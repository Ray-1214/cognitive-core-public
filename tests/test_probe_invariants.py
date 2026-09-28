"""probe 資料集的不變量（守門測試——失敗代表資料集壞了）。

⚠️ **2026-08-18 大幅簡化。** 原本的 U/A/B 脈絡恆等不變量已全數刪除
（不是註解掉），因為那個設計不適用於 WSD 資料源：CWN-SemCor 的義項
必須可由該句決定，否則標註者標不出來，而 U/A/B 需要的是「無脈絡時未定」。
刪除的檢查包含：probe_span 三條件逐字元相同、offset 三條件各驗、
U 條件無脈絡、U 是最小完整子句、脈絡長度配平、對調平衡。

保留的是與新任務（MT 詞義錯誤基準）仍相關的四項。
"""

from __future__ import annotations

import collections
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.data.probe_builder import MAX_CANDIDATE_SENSES  # noqa: E402

PROBE_DIR = pathlib.Path(__file__).resolve().parents[1] / "data" / "probes"


def _all_probe_items() -> list[tuple[str, dict]]:
    out = []
    for p in sorted(PROBE_DIR.glob("*.yaml")):
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for it in data.get("items", []):
            out.append((f"{p.name}:{it['id']}", it))
    return out


ITEMS = _all_probe_items()
pytestmark = pytest.mark.skipif(not ITEMS, reason="data/probes/ 尚無資料")


@pytest.mark.parametrize("label,item", ITEMS, ids=[x[0] for x in ITEMS])
def test_target_offset_points_at_target_word(label, item):
    lo, hi = item["target_offset"]
    s = item["sentence"]
    assert 0 <= lo < hi <= len(s), f"{label}：offset 超出句子範圍"
    assert s[lo:hi] == item["target_word"], f"{label}：offset 切出的不是目標詞"


@pytest.mark.parametrize("label,item", ITEMS, ids=[x[0] for x in ITEMS])
def test_target_occurs_exactly_once(label, item):
    """目標詞恰出現一次——否則譯文中的詞義無從歸因到哪一次出現。"""
    n = item["sentence"].count(item["target_word"])
    assert n == 1, f"{label}：目標詞出現 {n} 次"


@pytest.mark.parametrize("label,item", ITEMS, ids=[x[0] for x in ITEMS])
def test_gold_is_in_candidate_list(label, item):
    """gold 必須在候選清單中，否則 judge 不可能選對。

    本專案刻意選 gold 非最高頻的題目，只取前 N 高頻會讓 gold 落在清單外。
    """
    ids = {s["sense_id"] for s in item["competing_senses"]}
    assert item["gold_sense_id"] in ids, f"{label}：gold 不在候選清單中"


@pytest.mark.parametrize("label,item", ITEMS, ids=[x[0] for x in ITEMS])
def test_competing_senses_same_lemma(label, item):
    """競爭義項必須同 lemma（同讀音）——跨 lemma 的多義讀出來就消歧了。"""
    lemmas = {s["sense_id"][:6] for s in item["competing_senses"]}
    assert len(lemmas) == 1, f"{label}：候選義項跨 {len(lemmas)} 個 lemma：{lemmas}"


@pytest.mark.parametrize("label,item", ITEMS, ids=[x[0] for x in ITEMS])
def test_candidate_count_bounded(label, item):
    n = len(item["competing_senses"])
    assert 2 <= n <= MAX_CANDIDATE_SENSES, f"{label}：候選義項 {n} 個"


@pytest.mark.parametrize("label,item", ITEMS, ids=[x[0] for x in ITEMS])
def test_stratum_matches_gold_rank(label, item):
    """分層標籤必須與實際的 gold_rank 一致，否則分層分析會錯。"""
    expected = "dominant" if item["gold_rank"] == 1 else "non_dominant"
    assert item["stratum"] == expected, \
        f"{label}：stratum={item['stratum']} 但 gold_rank={item['gold_rank']}"


def test_stratification_is_balanced():
    """兩層題數應大致相等——主流層是基準線，太少就撐不起比較。"""
    c = collections.Counter(it["stratum"] for _, it in ITEMS)
    dom, non = c["dominant"], c["non_dominant"]
    assert dom > 0 and non > 0, f"分層缺一：dominant={dom} non_dominant={non}"
    assert abs(dom - non) <= max(5, 0.2 * len(ITEMS)), \
        f"分層失衡：dominant={dom} non_dominant={non}"
