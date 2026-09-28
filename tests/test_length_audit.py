"""長度稽核的單元測試（v3 架構書 §P2 測試提示詞第 2 條）。

用合成資料，不需真資料集。重點是「分層必須被分別計算」——
CHA-Gen 的教訓：18 組中 12 組顯著、方向相反，聚合中位數卻是 0.490。
若只看整體，那 12 組全部被相消掉。
"""

from __future__ import annotations

import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.data.length_audit import (  # noqa: E402
    auc,
    audit_predicts_error,
    context_balance_report,
    hanley_mcneil,
)


def rec(span: str, ctx_len: int, wrong: bool, atype: str = "LEXICAL",
        word: str = "死") -> dict:
    return {"probe_span": span, "context_length": ctx_len,
            "full_input": "x" * ctx_len + span, "is_wrong": wrong,
            "ambiguity_type": atype, "target_word": word}


# ── auc 基本性質 ──

def test_auc_identical_groups_is_half():
    assert auc([1.0] * 5, [1.0] * 5) == 0.5


def test_auc_perfect_separation_is_one():
    assert auc([10.0, 11.0, 12.0], [1.0, 2.0, 3.0]) == 1.0


def test_auc_reverse_separation_is_zero():
    assert auc([1.0, 2.0], [10.0, 11.0]) == 0.0


def test_auc_empty_is_nan():
    assert math.isnan(auc([], [1.0]))


# ── Hanley–McNeil ──

def test_se_shrinks_with_n():
    se_small, _, _ = hanley_mcneil(0.7, 10, 10)
    se_large, _, _ = hanley_mcneil(0.7, 1000, 1000)
    assert se_large < se_small / 5, "SE 未隨 n 縮小，判讀門檻就無法依 n 調整"


def test_ci_at_large_n_excludes_half_for_small_effect():
    """n 大時微弱效應也會顯著——這正是先前用固定門檻誤判 CHA-Gen 的原因。"""
    _, lo, hi = hanley_mcneil(0.418, 2414, 3298)
    assert hi < 0.5, f"CI [{lo:.3f}, {hi:.3f}] 應排除 0.5"


def test_ci_at_small_n_includes_half_for_same_effect():
    _, lo, hi = hanley_mcneil(0.418, 15, 15)
    assert lo < 0.5 < hi, "n 小時同樣的效應不該顯著"


# ── 預測選錯 ──

def test_no_length_difference_gives_half():
    recs = [rec("同樣長度", 10, i % 2 == 0) for i in range(20)]
    rows = [r for r in audit_predicts_error(recs) if r.stratum == "整體"]
    span_rows = [r for r in rows if "probe_span 字元數" in r.feature]
    assert span_rows and span_rows[0].auc == 0.5


def test_wrong_items_longer_gives_high_auc():
    recs = ([rec("很長很長很長很長的句子", 10, True) for _ in range(10)]
            + [rec("短句", 10, False) for _ in range(10)])
    rows = [r for r in audit_predicts_error(recs)
            if r.stratum == "整體" and "probe_span 字元數" in r.feature]
    assert rows[0].auc == 1.0
    assert rows[0].direction == "選錯者較長"


def test_context_length_predicting_error_is_detected():
    """C_A 與 C_B 是不同字串，配平只到 ≤10%，殘差仍可能與答案相關。"""
    recs = ([rec("固定跨度", 100, True) for _ in range(10)]
            + [rec("固定跨度", 10, False) for _ in range(10)])
    rows = [r for r in audit_predicts_error(recs)
            if r.stratum == "整體" and "context 字元數" in r.feature]
    assert rows[0].auc == 1.0
    assert rows[0].excludes_half


# ── 分層 ⭐ ──

def test_strata_are_computed_separately():
    recs = []
    for _ in range(15):
        recs.append(rec("很長很長很長很長", 10, True, atype="LEXICAL"))
        recs.append(rec("短", 10, False, atype="LEXICAL"))
        recs.append(rec("短", 10, True, atype="PRAGMATIC"))
        recs.append(rec("很長很長很長很長", 10, False, atype="PRAGMATIC"))
    rows = audit_predicts_error(recs, strata=("ambiguity_type",))
    by = {r.stratum: r for r in rows if "probe_span 字元數" in r.feature}
    assert by["ambiguity_type=LEXICAL"].auc == 1.0
    assert by["ambiguity_type=PRAGMATIC"].auc == 0.0


def test_aggregate_cancels_but_strata_reveal():
    """⭐ CHA-Gen 的教訓：整體 ≈0.5 但子類 1.0／0.0 必須被抓出來。"""
    recs = []
    for _ in range(15):
        recs.append(rec("很長很長很長很長", 10, True, atype="A"))
        recs.append(rec("短", 10, False, atype="A"))
        recs.append(rec("短", 10, True, atype="B"))
        recs.append(rec("很長很長很長很長", 10, False, atype="B"))
    rows = audit_predicts_error(recs, strata=("ambiguity_type",))
    overall = next(r for r in rows
                   if r.stratum == "整體" and "probe_span 字元數" in r.feature)
    strata = [r for r in rows
              if r.stratum.startswith("ambiguity_type=") and "probe_span 字元數" in r.feature]
    assert abs(overall.auc - 0.5) < 0.01, "整體應因正負相消而接近 0.5"
    assert any(r.excludes_half for r in strata), \
        "分層後必須抓到顯著組別，否則稽核形同虛設"
    assert {r.direction for r in strata} == {"選錯者較長", "選對者較長"}, \
        "兩個方向都要出現，才證明是相消不是乾淨"


def test_small_strata_are_skipped_not_reported_as_clean():
    """樣本不足的分層應略過，不可回報為「無異常」。"""
    recs = [rec("x", 10, True, word="甲"), rec("y", 10, False, word="甲")]
    rows = audit_predicts_error(recs, strata=("target_word",))
    assert not any(r.stratum == "target_word=甲" for r in rows)


# ── 多種長度定義 ──

def test_all_length_definitions_are_computed():
    recs = ([rec("長句，有標點。", 10, True) for _ in range(5)]
            + [rec("短", 10, False) for _ in range(5)])
    feats = {r.feature for r in audit_predicts_error(recs) if r.stratum == "整體"}
    assert len(feats) >= 3, "字元數／標點數／詞數應各算一次"


# ── 脈絡配平報告 ──

def test_context_balance_counts_within_tolerance():
    probes = [{"conditions": {
        "A": {"context_before": "x" * 100, "context_after": ""},
        "B": {"context_before": "y" * 105, "context_after": ""}}},
        {"conditions": {
            "A": {"context_before": "x" * 100, "context_after": ""},
            "B": {"context_before": "y" * 200, "context_after": ""}}}]
    out = context_balance_report(probes)
    assert "1/2" in out


def test_context_balance_skips_incomplete():
    probes = [{"conditions": {"U": {"context_before": "", "context_after": ""}}}]
    assert "尚無" in context_balance_report(probes)
