"""S1–S4 純規則訊號的單元測試（不呼叫 API）。

§5 地雷 5：新指標必須有單元測試才可用來下結論。
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.router.signals import (  # noqa: E402
    ALL_SIGNALS,
    CulturalItem,
    PolysemyHit,
    SubjectEllipsis,
    SyntacticComplexity,
    compute_all,
    raw_length,
)


# ── 共同契約 ──

@pytest.mark.parametrize("sig", ALL_SIGNALS, ids=[s.name for s in ALL_SIGNALS])
@pytest.mark.parametrize("text", [
    "", "。", "他昨天走了", "我們不收支票。",
    "如此對於賽程的控制和比賽氣氛熱都很有幫助，這是一個很長的句子用來測試邊界情況",
])
def test_output_in_unit_interval(sig, text):
    v = sig(text)
    assert 0.0 <= v <= 1.0, f"{sig.name}({text!r}) = {v} 超出 [0,1]"


@pytest.mark.parametrize("sig", ALL_SIGNALS, ids=[s.name for s in ALL_SIGNALS])
def test_empty_string_does_not_crash(sig):
    assert sig("") == 0.0


@pytest.mark.parametrize("sig", ALL_SIGNALS, ids=[s.name for s in ALL_SIGNALS])
def test_deterministic(sig):
    t = "他終於放下了，心裡很不是滋味。"
    assert sig(t) == sig(t)


def test_compute_all_returns_every_signal():
    r = compute_all("他昨天走了")
    assert {s.name for s in ALL_SIGNALS} == set(r)
    for name, res in r.items():
        assert res.name == name
        assert isinstance(res.detail, dict)


# ── S1 多義詞 ──

def test_s1_hits_polysemous_word():
    s = PolysemyHit()
    assert s.compute("我們不收支票。").score > 0, "「收」在 113 詞表中，應命中"
    assert s.compute("ＡＢＣＤＥＦ").score == 0.0


def test_s1_reports_which_words_hit():
    r = PolysemyHit().compute("我們不收支票。")
    assert isinstance(r.detail["hits"], dict)
    assert "收" in r.detail["hits"]


def test_s1_unknown_words_score_zero_conservatively():
    """詞表未收錄者計為 0——低估歧義是保守方向。"""
    assert PolysemyHit().compute("ＸＹＺ").score == 0.0


def test_s1_substring_false_positive_is_documented():
    """⚠️ 已知弱點：單字比對會誤命中詞素。

    「橘子」的「子」是後綴詞素，不是多義的 content word，但字串比對分不出來。
    這支測試把弱點釘住——若日後加了斷詞使它消失，應同步更新文件與報告的揭露。
    """
    r = PolysemyHit().compute("蘋果橘子香蕉")
    assert r.score > 0 and "子" in r.detail["hits"], \
        "假命中已消失（可能加了斷詞），請同步更新 signals.py 的限制說明與報告"


# ── S2 主詞省略（v2 連續分數）──

def test_s2_pronoun_lowers_score():
    s = SubjectEllipsis()
    assert s("我昨天去了公園") < s("昨天去了公園")


def test_s2_topic_marker_raises_score():
    s = SubjectEllipsis()
    assert s("因為下雨所以取消") >= s("我因為下雨取消行程")


def test_s2_counts_clauses():
    r = SubjectEllipsis().compute("甲來了，乙走了，丙留下")
    assert r.detail["clauses"] == 3


def test_s2_overt_np_subject_scores_low():
    """v1 的核心錯誤：把「沒有人稱代名詞」等同於「省略主詞」。

    「教育部在九月初…」的主詞是名詞組「教育部」，不是省略。
    v2 由謂語標記「在」的位置推斷前置名詞組存在。
    """
    s = SubjectEllipsis()
    assert s("教育部在九月初宣布新制") < s("因為下雨所以取消")


def test_s2_predicate_marker_position_is_graded():
    """謂語標記出現得越晚 → 前置名詞組越長 → 省略分數越低。"""
    s = SubjectEllipsis()
    early = s("是他做的")          # 標記在第 0 字
    late = s("教育部長官是他")      # 標記在第 5 字
    assert early > late


def test_s2_is_continuous_not_binary():
    """v1 只產出 5 個相異值，AUC 上限被壓到 0.669。"""
    s = SubjectEllipsis()
    vals = {s(t) for t in (
        "我去", "他昨天去了公園", "昨天去了公園", "因為下雨所以取消",
        "教育部在九月初宣布", "甲來了，乙走了", "是他做的", "這件事我知道")}
    assert len(vals) >= 5, f"只產出 {len(vals)} 個相異值，仍過於離散"


def test_s2_no_evidence_clause_gets_half():
    """既無人稱也無謂語標記時給 0.5——誠實的不確定值。

    ⚠️ 刻意不依子句長度分級。用長度分級能把 AUC 上限再推高，
    但那會讓 S2 變成句長的代理（§4 地雷 1）。
    """
    s = SubjectEllipsis()
    r = s.compute("昨天去了公園")
    assert r.score == pytest.approx(0.5)
    assert r.detail["no_evidence_clauses"] == 1


def test_s2_not_a_length_proxy():
    """同結構下加長不應單調推高分數——那是 S3 的職責，不是 S2 的。"""
    s = SubjectEllipsis()
    short = s("昨天去了公園")
    longer = s("昨天去了公園" + "又去了圖書館")
    assert abs(longer - short) < 0.5, "S2 對純粹加長過度敏感，可能已變成長度代理"


# ── S3 句法複雜度 ⭐ 與長度基準的關係 ──

def test_s3_long_sentence_scores_higher():
    s = SyntacticComplexity()
    assert s("這是一個非常長的句子，包含很多子句，而且標點也不少。") > s("短句")


def test_s3_exposes_raw_length_for_side_by_side():
    """S3 必須把純句長一併回傳——報告時要與長度基準並列。

    若 S3 的 AUC 與純句長的 AUC 相近，S3 就不是獨立訊號而是長度的代理。
    """
    t = "他昨天走了"
    r = SyntacticComplexity().compute(t)
    assert r.detail["raw_length"] == raw_length(t) == float(len(t))


def test_s3_is_monotone_in_length_for_same_structure():
    """同結構下 S3 隨長度單調——這正是它與長度高度重疊的來源。"""
    s = SyntacticComplexity()
    assert s("啊" * 5) <= s("啊" * 20) <= s("啊" * 40)


def test_s3_components_are_reported():
    d = SyntacticComplexity().compute("甲，乙，丙。").detail
    assert set(d["components"]) == {"len", "clause", "density"}


# ── S4 成語 ──

def test_s4_hits_known_idiom():
    s = CulturalItem()
    r = s.compute("這件事真是畫蛇添足。")
    assert r.score > 0, f"未命中成語，detail={r.detail}"
    assert any("畫蛇添足" in h for h in r.detail["hits"])


def test_s4_no_idiom_scores_zero():
    assert CulturalItem().compute("我們不收支票。").score == 0.0


def test_s4_saturates_at_two():
    s = CulturalItem()
    one = s("這件事真是畫蛇添足。")
    two = s("他對牛彈琴，真是畫蛇添足。")
    assert two >= one
    assert two <= 1.0


def test_s4_lexicon_is_traditional_chinese():
    """詞表已用 OpenCC 轉台灣正體——原始資料是簡體。"""
    from cognitive_core.router.signals import _idioms
    idi = _idioms()
    if not idi:
        pytest.skip("詞表尚未建立")
    assert "畫蛇添足" in idi
    assert "画蛇添足" not in idi, "詞表仍含簡體，轉換未生效"


def test_s4_long_text_does_not_hang():
    """避免對長句做 O(n²) 全掃描。"""
    CulturalItem().compute("啊" * 2000)
