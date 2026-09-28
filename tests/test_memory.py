"""記憶模組（v3 架構書 §P7 測試提示詞第 1 項）。

嵌入函式注入合成向量，不呼叫 API。ChromaDB 後端與純記憶體後端跑同一套斷言——
兩者的檢索語意必須相同，否則 RQ3 的結果會依後端而變。
"""

from __future__ import annotations

import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.memory import (  # noqa: E402
    MemoryEntry,
    MemoryStore,
    RollingSummary,
    SummaryConfig,
)
from cognitive_core.memory.store import cosine  # noqa: E402


def fake_embed(texts: list[str]) -> list[list[float]]:
    """依字元集合給方向。同字多的文字向量相近。"""
    out = []
    for t in texts:
        a = sum(ord(c) for c in t) * 0.017
        b = len(set(t)) * 0.11
        out.append([math.cos(a), math.sin(a), math.cos(b), math.sin(b)])
    return out


def has_chroma() -> bool:
    try:
        import chromadb  # noqa: F401
        return True
    except ImportError:
        return False


BACKENDS = ["memory"] + (["chroma"] if has_chroma() else [])


def store(backend="memory", **kw) -> MemoryStore:
    return MemoryStore(fake_embed, backend=backend, **kw)


# ── 存取 ──

@pytest.mark.parametrize("backend", BACKENDS)
def test_added_entry_is_retrievable(backend):
    s = store(backend)
    s.add("他昨天離開了公司")
    assert len(s) == 1
    assert s.recall("離開公司") == ["他昨天離開了公司"]


@pytest.mark.parametrize("backend", BACKENDS)
def test_search_returns_k_results(backend):
    s = store(backend)
    for i in range(5):
        s.add(f"第 {i} 則訊息")
    assert len(s.search("訊息", k=3)) == 3


@pytest.mark.parametrize("backend", BACKENDS)
def test_empty_store_search_does_not_crash(backend):
    assert store(backend).search("任何東西") == []
    assert store(backend).recall("任何東西") == []


def test_search_is_ordered_by_similarity():
    s = store()
    s.add("完全一樣的句子")
    s.add("毫不相干的內容")
    res = s.search("完全一樣的句子", k=2)
    assert res[0][0].text == "完全一樣的句子"
    assert res[0][1] >= res[1][1]


def test_get_by_id():
    s = store()
    e = s.add("找我")
    assert s.get(e.id) is e
    assert s.get("不存在") is None


# ── 錨點提高檢索的資訊密度 ──

def test_anchor_enters_the_search_text():
    e = MemoryEntry(id="x", text="他昨天走了", anchor={
        "uncertainty": {"alternative_readings": [
            {"reading": "離開"}, {"reading": "過世"}]},
        "unknown_scalars": ["agent"]})
    st = e.searchable
    assert "離開" in st and "過世" in st and "agent" in st
    assert e.text in st


def test_entry_without_anchor_searches_on_text_only():
    assert MemoryEntry(id="x", text="純文字").searchable == "純文字"


def test_malformed_anchor_does_not_crash():
    e = MemoryEntry(id="x", text="t", anchor={"uncertainty": {
        "alternative_readings": ["不是 dict"]}})
    assert e.searchable.startswith("t")


# ── 滾動摘要 ⭐ ──

def make(n: int, *, anchored: set[int] = frozenset()) -> list[MemoryEntry]:
    return [MemoryEntry(id=f"e{i}", text=f"第{i}則。內容內容內容", turn=i,
                        anchor={"unknown_scalars": []} if i in anchored else None)
            for i in range(n)]


def test_compression_triggers_only_above_window():
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4))
    assert rs.should_compress(make(10)) is False
    assert rs.should_compress(make(11)) is True


def test_compression_shortens_the_list():
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4))
    out = rs.compress(make(20))
    assert len(out) < 20


def test_recent_entries_are_kept_verbatim():
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4))
    out = rs.compress(make(20))
    assert [e.text for e in out[-4:]] == [f"第{i}則。內容內容內容" for i in range(16, 20)]


def test_anchored_entries_survive_compression():
    """有錨點的訊息是後續對話會回頭參照的，壓掉它們等於丟掉最有用的東西。"""
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4))
    out = rs.compress(make(20, anchored={2, 5}))
    kept = {e.id for e in out}
    assert "e2" in kept and "e5" in kept


def test_original_text_cannot_be_recovered_after_summarising():
    """⭐ 摘要後原文不可再被完整取回——否則沒有真的壓縮。"""
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4))
    out = rs.compress(make(20))
    joined = "".join(e.text for e in out)
    # 被壓掉的那些（0..15，非 anchored）不得完整出現
    assert "第0則。內容內容內容" not in joined
    assert "第7則。內容內容內容" not in joined


def test_summary_entry_is_flagged():
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4))
    out = rs.compress(make(20))
    s = [e for e in out if e.summarised]
    assert s and s[0].role == "summary"


def test_summary_respects_length_cap():
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4,
                                      max_summary_chars=40))
    out = rs.compress(make(30))
    for e in out:
        if e.summarised:
            assert len(e.text) <= 40


def test_compress_does_not_mutate_input():
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4))
    src = make(20)
    rs.compress(src)
    assert len(src) == 20


def test_compress_preserves_turn_order():
    rs = RollingSummary(SummaryConfig(window=10, keep_recent=4))
    out = rs.compress(make(20, anchored={3, 9}))
    turns = [e.turn for e in out]
    assert turns == sorted(turns)


def test_injected_summariser_is_used():
    rs = RollingSummary(SummaryConfig(window=6, keep_recent=2),
                        summariser=lambda ts: f"共 {len(ts)} 則")
    out = rs.compress(make(12))
    assert any(e.text.startswith("共 ") for e in out)


# ── 摘要與 store 的整合 ──

def filled(n=20, **kw) -> MemoryStore:
    s = store(summary=RollingSummary(SummaryConfig(window=8, keep_recent=3)), **kw)
    for i in range(n):
        s.add(f"訊息 {i}。這是一段內容")
    return s


@pytest.mark.parametrize("backend", BACKENDS)
def test_add_never_deletes_from_the_store(backend):
    """⭐ 向量庫是長期儲存。第一版讓 add() 觸發破壞性壓縮，

    結果檢索再也找不到被壓掉的內容，Lost-in-the-Middle 的實驗組
    召回率跟對照組一樣是 0%。
    """
    s = filled(20, backend=backend)
    assert len(s) == 20


def test_context_is_compressed_but_store_is_not():
    s = filled(20)
    assert len(s.context()) < len(s.entries)


def test_every_entry_keeps_its_vector():
    s = filled(20)
    assert set(s._vecs) == {e.id for e in s.entries}


def test_search_reaches_entries_the_summary_dropped():
    """⭐ 滾動摘要壓掉的內容，檢索仍找得到——這是記憶模組的全部意義。"""
    s = filled(20)
    ctx_ids = {e.id for e in s.context()}
    dropped = [e for e in s.entries if e.id not in ctx_ids]
    assert dropped, "測試設定有問題：沒有任何項目被摘要壓掉"
    target = dropped[0]
    assert any(e.id == target.id for e, _ in s.search(target.text, k=1))


def test_augmented_context_pulls_back_relevant_old_entries():
    s = filled(20)
    ctx_ids = {e.id for e in s.context()}
    dropped = [e for e in s.entries if e.id not in ctx_ids]
    target = dropped[0]
    aug = s.augmented_context(target.text, k=3)
    assert any(e.id == target.id for e in aug)
    assert len(aug) >= len(s.context())


def test_augmented_context_has_no_duplicates():
    s = filled(20)
    aug = s.augmented_context("訊息 19。這是一段內容", k=5)
    assert len({e.id for e in aug}) == len(aug)


# ── cosine ──

def test_cosine_identical_is_one():
    assert cosine([1.0, 2.0], [1.0, 2.0]) == pytest.approx(1.0)


def test_cosine_orthogonal_is_zero():
    assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_zero_vector_does_not_divide_by_zero():
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0
