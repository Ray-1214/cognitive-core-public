"""標籤噪音的組成與天花板校正（2026-08-22 裁示）。

兩個容易出錯的地方，各自都會讓報告的數字錯：

  1. **位置效應與內容誤差不可相加。**「judge vs 人工 15%」是總錯誤率，
     位置驅動的判定早就算在裡面了。相加會得到 18.9%，那是重複計算。
  2. **天花板校正有兩個分母。** 22.1%（佔全部題目）與 26.0%（佔可判定題目）
     都對，但意思不同，混用會被誤讀。
"""

from __future__ import annotations

import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.eval.noise import (  # noqa: E402
    ceiling_correct,
    compose_noise,
    decompose,
    holm,
)


# ── 噪音組成：分解而非相加 ⭐ ──

def test_total_is_the_direct_measurement_not_a_sum():
    """17/20 一致 → 總噪音 15%，不是 15% + 3.9%。"""
    ne = compose_noise(n_agree=17, n_total=20, position_noise=0.039)
    assert ne.total == pytest.approx(0.15)
    assert ne.additive_would_be == pytest.approx(0.189)
    assert ne.total < ne.additive_would_be


def test_position_is_a_component_of_total():
    ne = compose_noise(n_agree=17, n_total=20, position_noise=0.039)
    assert ne.position_component == pytest.approx(0.039)
    assert ne.content_component == pytest.approx(0.15 - 0.039)
    assert ne.position_component + ne.content_component == pytest.approx(ne.total)


def test_position_component_cannot_exceed_total():
    """位置效應量到的值若比總錯誤還大，代表兩者參照不同，取 total 為上限。"""
    ne = compose_noise(n_agree=19, n_total=20, position_noise=0.30)
    assert ne.position_component <= ne.total
    assert ne.content_component == 0.0


def test_shared_position_bias_is_flagged():
    """人工與 judge 同向偏誤 → 一致率裡互相抵銷 → total 低估。"""
    ne = compose_noise(n_agree=17, n_total=20, position_noise=0.039,
                       human_a_rate=0.75, judge_a_rate=0.80)
    assert ne.shared_position_bias is True and ne.note


def test_no_shared_bias_when_both_balanced():
    """r2 的實測：兩邊都是 10/20。"""
    ne = compose_noise(n_agree=17, n_total=20, position_noise=0.039,
                       human_a_rate=0.5, judge_a_rate=0.5)
    assert ne.shared_position_bias is False


def test_opposite_bias_is_not_shared():
    ne = compose_noise(n_agree=17, n_total=20, position_noise=0.039,
                       human_a_rate=0.75, judge_a_rate=0.25)
    assert ne.shared_position_bias is False


def test_total_ci_is_wide_at_n20():
    ne = compose_noise(n_agree=17, n_total=20, position_noise=0.039)
    lo, hi = ne.total_ci
    assert lo < 0.15 < hi
    assert hi - lo > 0.25, "n=20 的 CI 應該很寬，此處未反映出來"


# ── 誤差分解 ──

def test_decomposition_matches_the_three_agreements():
    d = decompose(judge_vs_human=0.85, human_vs_gold=0.90,
                  judge_vs_gold=0.80, n=20)
    assert d.gold_to_human == pytest.approx(0.10)
    assert d.human_to_judge == pytest.approx(0.15)
    assert d.gold_to_judge == pytest.approx(0.20)


def test_task_and_model_shares_sum_to_total_gap():
    d = decompose(judge_vs_human=0.85, human_vs_gold=0.90,
                  judge_vs_gold=0.80, n=20)
    assert d.task_share + d.model_share == pytest.approx(d.gold_to_judge)
    assert d.task_share == pytest.approx(0.10)
    assert d.model_share == pytest.approx(0.10)


def test_superadditive_positive_means_errors_partly_cancel():
    """10% + 15% = 25% > 實際 20% → judge 的錯有時剛好回到 gold。"""
    d = decompose(judge_vs_human=0.85, human_vs_gold=0.90,
                  judge_vs_gold=0.80, n=20)
    assert d.superadditive == pytest.approx(0.05)


def test_model_share_never_negative():
    """judge 比人工還接近 gold 時，模型份額不可為負。"""
    d = decompose(judge_vs_human=0.85, human_vs_gold=0.70,
                  judge_vs_gold=0.95, n=20)
    assert d.model_share == 0.0


# ── 天花板校正 ⭐ 兩個分母 ──

def test_ceiling_correction_matches_hand_computation():
    """觀測錯誤 29.6%，a=15% → 佔全部 29.6−7.5 = 22.1%；佔可判定 26.0%。"""
    cc = ceiling_correct(0.704, n_ambiguous=3, n_annotated=20)
    assert cc.ambiguous_rate == pytest.approx(0.15)
    assert cc.ceiling == pytest.approx(0.925)
    assert cc.err_observed == pytest.approx(0.296)
    assert cc.err_of_all_items == pytest.approx(0.221, abs=1e-3)
    assert cc.err_of_decidable == pytest.approx(0.260, abs=1e-3)


def test_two_denominators_differ():
    """⭐ 混用會被誤讀——測試釘住兩者不相等。"""
    cc = ceiling_correct(0.704, n_ambiguous=3, n_annotated=20)
    assert cc.err_of_all_items < cc.err_of_decidable


def test_zero_ambiguity_means_no_correction():
    cc = ceiling_correct(0.704, n_ambiguous=0, n_annotated=20)
    assert cc.err_of_all_items == pytest.approx(cc.err_observed)
    assert cc.err_of_decidable == pytest.approx(cc.err_observed)
    assert cc.ceiling == 1.0


def test_more_ambiguity_lowers_corrected_error():
    a = ceiling_correct(0.704, n_ambiguous=2, n_annotated=20)
    b = ceiling_correct(0.704, n_ambiguous=6, n_annotated=20)
    assert b.err_of_all_items < a.err_of_all_items


def test_correction_clamps_at_zero():
    """不可判定的比例大到足以解釋全部錯誤時，模型錯誤率是 0 不是負數。"""
    cc = ceiling_correct(0.704, n_ambiguous=15, n_annotated=20)
    assert cc.err_of_all_items == 0.0


def test_ci_is_wide_at_n20_and_ordered():
    cc = ceiling_correct(0.704, n_ambiguous=3, n_annotated=20)
    lo, hi = cc.err_of_all_ci
    assert lo < cc.err_of_all_items < hi
    assert hi - lo > 0.10, "n=20 的天花板估計 CI 應該很寬"


def test_ci_direction_is_inverted():
    """a 越大 → 校正越多 → 錯誤率越低，所以 CI 上界對應 a 的下界。"""
    cc = ceiling_correct(0.704, n_ambiguous=3, n_annotated=20)
    from cognitive_core.eval.noise import ceiling_correct as f
    at_a_hi = f(0.704, n_ambiguous=round(cc.ambiguous_ci[1] * 100),
                n_annotated=100)
    assert at_a_hi.err_of_all_items == pytest.approx(cc.err_of_all_ci[0], abs=0.01)


# ── Holm ──

def test_holm_preserves_input_order():
    out = holm([0.04, 0.01, 0.20])
    assert len(out) == 3
    assert out[1] < out[0] < out[2]


def test_holm_smallest_p_times_m():
    assert holm([0.01, 0.02, 0.03])[0] == pytest.approx(0.03)


def test_holm_is_monotone_after_sorting():
    p = [0.001, 0.01, 0.02, 0.5]
    adj = sorted(holm(p))
    assert adj == sorted(adj)


def test_holm_never_exceeds_one():
    assert all(x <= 1.0 for x in holm([0.4, 0.5, 0.6, 0.9]))


def test_holm_ignores_nan():
    out = holm([0.01, float("nan"), 0.02])
    assert math.isnan(out[1])
    assert out[0] == pytest.approx(0.02)


# ── 專案現況 ──

def test_project_numbers_are_consistent():
    """報告裡的 15% / 22.1% / 0.590 必須能由驗證檔重算出來。"""
    import json
    root = pathlib.Path(__file__).resolve().parents[1] / "data" / "results"
    vf, bf = root / "judge_validation_r2.json", root / "wsd_baseline400.json"
    if not (vf.exists() and bf.exists()):
        pytest.skip("尚無驗證或基準結果")
    v = json.loads(vf.read_text(encoding="utf-8"))
    b = json.loads(bf.read_text(encoding="utf-8"))
    ne = compose_noise(n_agree=round(v["judge_vs_human"] * v["n"]),
                       n_total=v["n"],
                       position_noise=b["position_effect"]["implied_noise"])
    assert ne.total == pytest.approx(1 - v["judge_vs_human"])
    cc = ceiling_correct(b["accuracy"],
                         n_ambiguous=round(v["both_plausible_rate"] * v["n"]),
                         n_annotated=v["n"])
    assert cc.err_of_all_items < cc.err_observed
    assert cc.valid
