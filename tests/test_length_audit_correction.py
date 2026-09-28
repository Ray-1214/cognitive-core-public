"""長度稽核的多重比較校正與退化處理。

兩個缺陷在 n=400 的實跑中才浮現，各自都會讓報告下錯結論：

  1. `熱` 這一層回報 `AUC=0.000, CI [0.000, 0.000]` ——
     Hanley–McNeil 在邊界 var=0，那不是「非常確定」，是公式失效。
  2. 一次跑上百格卻不校正 ——「9 格顯著」在 α=0.05 下與純機率相符。
"""

from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.data.length_audit import (  # noqa: E402
    AuditRow,
    audit_predicts_error,
    format_report,
)


def rec(span: str, wrong: bool, word: str = "甲") -> dict:
    return {"probe_span": span, "full_input": span,
            "context_length": len(span), "is_wrong": wrong,
            "target_word": word, "ambiguity_type": "LEXICAL"}


def perfectly_separated(word: str = "甲", n: int = 4) -> list[dict]:
    """選錯者一律較短 → AUC = 0.0，觸發退化。"""
    return ([rec("短" * 2, True, word) for _ in range(n)]
            + [rec("長" * 20, False, word) for _ in range(n)])


# ── 退化 ──

def test_degenerate_row_is_flagged_not_reported_as_certain():
    rows = audit_predicts_error(perfectly_separated(), strata=("target_word",))
    deg = [r for r in rows if r.degenerate]
    assert deg, "完美分離未被標成退化"
    for r in deg:
        assert r.auc in (0.0, 1.0)
        assert math.isnan(r.ci[0]) and math.isnan(r.ci[1]), \
            "退化時不得回報數值 CI——CI [0.000, 0.000] 是假確定性"
        assert r.p_perm is not None


def test_degenerate_ci_text_says_so():
    rows = audit_predicts_error(perfectly_separated(), strata=("target_word",))
    r = next(x for x in rows if x.degenerate)
    assert "退化" in r.ci_text() and "排列檢定" in r.ci_text()


def test_smallest_perfect_separation_is_not_significant():
    """n=3 vs 3：只有 C(6,3)=20 種切法，完美分離的雙尾 p = 2/20 = 0.1。

    天真實作會說「AUC=0.000，完美預測」。正確答案是「樣本太少，
    這種完美分離本來就常見」。
    """
    rows = audit_predicts_error(perfectly_separated(n=3), strata=("target_word",))
    deg = [x for x in rows if x.degenerate]
    assert deg
    for r in deg:
        assert r.p_perm > 0.05, f"n=3 的完美分離不該算顯著（p={r.p_perm}）"
        assert r.excludes_half is False


def test_perfect_separation_significance_tracks_sample_size():
    """n=4 起（C(8,4)=70，p≈0.029）排列檢定才給得出顯著——

    這是 n 依賴的判準，不是固定門檻。釘住它以免日後有人改成硬門檻。
    """
    p3 = next(r.p_perm for r in audit_predicts_error(
        perfectly_separated(n=3), strata=("target_word",)) if r.degenerate)
    p4 = next(r.p_perm for r in audit_predicts_error(
        perfectly_separated(n=4), strata=("target_word",)) if r.degenerate)
    assert p3 > 0.05 > p4


def test_holm_still_rescues_small_perfect_separation():
    """單看排列檢定 n=4 顯著，但它是上百格裡的一格——校正後應被擋下。"""
    rows = audit_predicts_error(perfectly_separated(n=4), strata=("target_word",))
    deg = [r for r in rows if r.degenerate]
    assert deg and not any(r.survives_correction for r in deg)


def test_report_does_not_print_fake_zero_ci():
    txt = format_report(audit_predicts_error(perfectly_separated(),
                                             strata=("target_word",)))
    assert "[0.000, 0.000]" not in txt


# ── Holm 校正 ──

def test_every_row_gets_an_adjusted_p():
    rows = audit_predicts_error(
        [rec("短" * (2 + i % 5), i % 3 == 0) for i in range(40)],
        strata=("target_word",))
    assert rows and all(r.p_adjusted is not None for r in rows)


def test_adjusted_p_is_never_smaller_than_raw_significance():
    """校正只會讓結論更保守，不會製造新的顯著。"""
    rows = audit_predicts_error(
        [rec("短" * (2 + (i * 7) % 9), i % 2 == 0, f"w{i % 6}") for i in range(90)],
        strata=("target_word",))
    for r in rows:
        if r.survives_correction:
            assert r.excludes_half, "校正後顯著但未校正時不顯著——不可能"


def test_holm_is_monotone_across_sorted_p():
    """Holm 的調整後 p 必須逐步遞增（step-down 的定義）。"""
    rows = audit_predicts_error(
        [rec("短" * (2 + (i * 3) % 11), i % 3 == 0, f"w{i % 5}") for i in range(100)],
        strata=("target_word",))
    got = sorted((r.p_adjusted for r in rows if r.p_adjusted is not None))
    assert got == sorted(got)
    assert all(0.0 <= p <= 1.0 for p in got)


def test_pure_noise_yields_no_surviving_row():
    """隨機標籤：未校正可能有幾格顯著，校正後應一格不剩。"""
    import random
    rng = random.Random(11)
    recs = [rec("字" * rng.randint(3, 30), rng.random() < 0.45, f"w{i % 12}")
            for i in range(600)]
    rows = audit_predicts_error(recs, strata=("target_word",))
    assert not [r for r in rows if r.survives_correction], \
        "純噪音卻有格通過 Holm 校正"


def test_report_states_both_counts():
    import random
    rng = random.Random(12)
    recs = [rec("字" * rng.randint(3, 30), rng.random() < 0.45, f"w{i % 10}")
            for i in range(400)]
    txt = format_report(audit_predicts_error(recs, strata=("target_word",)))
    assert "未校正" in txt and "Holm 校正後仍顯著" in txt


def test_report_warns_when_significant_but_none_survive():
    import random
    rng = random.Random(13)
    recs = [rec("字" * rng.randint(3, 30), rng.random() < 0.45, f"w{i % 14}")
            for i in range(700)]
    rows = audit_predicts_error(recs, strata=("target_word",))
    txt = format_report(rows)
    if [r for r in rows if r.excludes_half]:
        assert "沒有任何一格通過 Holm 校正" in txt


# ── AuditRow 的預設值 ──

def test_audit_row_defaults_are_conservative():
    r = AuditRow("x", "f", 5, 5, 0.6, 0.1, (0.4, 0.8))
    assert r.degenerate is False
    assert r.survives_correction is False, "沒算過校正就不算通過"
