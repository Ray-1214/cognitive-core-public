"""AUC 與其信賴區間的測試（v3 架構書 §P4 測試提示詞第 3 項）。

⚠️ 重點是 **AUC==1.0 的退化行為**。天真實作會回報 CI [1.00, 1.00]，
那不是「非常確定」，是公式在邊界失效。這種假確定性一旦進了報告，
就會變成「某訊號完美預測」的錯誤結論。
"""

from __future__ import annotations

import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.eval.auc import (  # noqa: E402
    AucResult,
    auc_score,
    delong_test,
    evaluate,
    hanley_mcneil,
    permutation_p,
    required_auc,
    unweighted_sum,
)


# ── auc_score ──

def test_perfect_separation_is_one():
    assert auc_score([3.0, 4.0, 5.0], [0.0, 1.0, 2.0]) == 1.0


def test_perfect_inversion_is_zero():
    assert auc_score([0.0, 1.0, 2.0], [3.0, 4.0, 5.0]) == 0.0


def test_all_ties_is_half():
    """全部並列 → 0.5。並列必須計 0.5，不可計 0 或 1。"""
    assert auc_score([1.0] * 5, [1.0] * 5) == 0.5


def test_random_labels_near_half():
    import random
    rng = random.Random(0)
    vals = [rng.random() for _ in range(400)]
    a = auc_score(vals[:200], vals[200:])
    assert abs(a - 0.5) < 0.08, f"隨機標籤的 AUC = {a}，離 0.5 太遠"


def test_empty_class_is_nan():
    assert math.isnan(auc_score([], [1.0]))
    assert math.isnan(auc_score([1.0], []))


def test_auc_is_rank_based_not_scale_based():
    """AUC 只看排序。訊號做單調轉換不應改變 AUC——這是它比閾值指標可靠的原因。"""
    pos, neg = [0.9, 0.8], [0.2, 0.1]
    assert auc_score(pos, neg) == auc_score([p ** 3 for p in pos],
                                            [n ** 3 for n in neg])


# ── Hanley–McNeil 的退化 ⭐ ──

def test_hanley_mcneil_variance_collapses_at_one():
    """證實退化確實存在——這正是 evaluate() 要繞開的東西。"""
    se, lo, hi = hanley_mcneil(1.0, 10, 10)
    assert se == 0.0 and (lo, hi) == (1.0, 1.0)


def test_evaluate_flags_degenerate_and_does_not_report_fake_ci():
    r = evaluate([3.0, 4.0, 5.0], [0.0, 1.0, 2.0], n_perm=2000)
    assert r.auc == 1.0
    assert r.degenerate is True
    assert math.isnan(r.ci[0]) and math.isnan(r.ci[1]), "退化時不得回報數值 CI"
    assert r.p_perm is not None
    assert "退化" in r.ci_text()


def test_evaluate_flags_degenerate_at_zero_too():
    r = evaluate([0.0, 1.0], [3.0, 4.0], n_perm=500)
    assert r.auc == 0.0 and r.degenerate is True


def test_tiny_perfect_separation_is_not_significant():
    """n=3 vs 3 的完美分離只有 1/20 的排列可能，p 不可能 <0.05。

    這是退化處理最重要的一題：天真實作會說「AUC=1.0, CI[1,1]，完美預測」，
    正確答案是「樣本太少，這個完美分離本來就常見」。
    """
    r = evaluate([3.0, 4.0, 5.0], [0.0, 1.0, 2.0], n_perm=5000)
    assert r.p_perm > 0.05
    assert r.excludes_half is False


def test_large_perfect_separation_is_significant():
    r = evaluate([float(i) for i in range(20, 40)],
                 [float(i) for i in range(20)], n_perm=2000)
    assert r.p_perm < 0.05 and r.excludes_half is True


def test_normal_case_reports_real_ci():
    r = evaluate([float(i) for i in range(30, 60)], [float(i) for i in range(40)])
    assert r.degenerate is False
    assert 0.5 < r.ci[0] < r.auc < r.ci[1] <= 1.0
    assert r.excludes_half is True


def test_excludes_half_false_when_ci_covers_half():
    import random
    rng = random.Random(1)
    v = [rng.random() for _ in range(60)]
    assert evaluate(v[:30], v[30:]).excludes_half is False


# ── 排列檢定 ──

def test_permutation_p_never_zero():
    """(r+1)/(n+1) 的保守估計。p=0 是不可能被觀測到的斷言。"""
    p = permutation_p([float(i) for i in range(50, 100)],
                      [float(i) for i in range(50)], n_perm=200)
    assert p > 0.0


def test_permutation_p_near_one_for_identical_distributions():
    p = permutation_p([1.0] * 20, [1.0] * 20, n_perm=200)
    assert p > 0.9


def test_permutation_p_is_deterministic_given_seed():
    a = permutation_p([3.0, 4.0], [1.0, 2.0], n_perm=500, seed=7)
    b = permutation_p([3.0, 4.0], [1.0, 2.0], n_perm=500, seed=7)
    assert a == b


# ── DeLong ⭐ S3 vs 純句長要用這個 ──

def test_delong_identical_signals_gives_zero_diff():
    pos, neg = [3.0, 4.0, 5.0, 6.0], [1.0, 2.0, 2.5, 0.5]
    r = delong_test(pos, neg, pos, neg)
    assert r.diff == 0.0


def test_delong_detects_a_real_difference():
    """A 完美分離、B 亂猜，且 n 夠大 → 應顯著。"""
    pos_a = [float(i) for i in range(40, 80)]
    neg_a = [float(i) for i in range(40)]
    import random
    rng = random.Random(2)
    pos_b = [rng.random() for _ in range(40)]
    neg_b = [rng.random() for _ in range(40)]
    r = delong_test(pos_a, neg_a, pos_b, neg_b)
    assert r.auc_a > r.auc_b
    assert r.significant, f"z={r.z}, p={r.p}"


def test_delong_correlated_signals_not_significant():
    """B 是 A 加一點噪音——高度相關，差異不該顯著。

    這正是 S3 與純句長的關係。用獨立雙樣本檢定會誤判為顯著。
    """
    import random
    rng = random.Random(3)
    pos_a = [rng.gauss(1.0, 1.0) for _ in range(50)]
    neg_a = [rng.gauss(0.0, 1.0) for _ in range(50)]
    pos_b = [x + rng.gauss(0, 0.05) for x in pos_a]
    neg_b = [x + rng.gauss(0, 0.05) for x in neg_a]
    assert delong_test(pos_a, neg_a, pos_b, neg_b).significant is False


def test_delong_rejects_mismatched_sample_sizes():
    r = delong_test([1.0, 2.0], [3.0, 4.0], [1.0], [3.0, 4.0])
    assert math.isnan(r.p)


def test_delong_p_is_two_sided():
    """交換 A B 只改變 z 的正負，p 不變。"""
    pos_a = [float(i) for i in range(30, 60)]
    neg_a = [float(i) for i in range(30)]
    import random
    rng = random.Random(4)
    pos_b = [rng.random() for _ in range(30)]
    neg_b = [rng.random() for _ in range(30)]
    r1 = delong_test(pos_a, neg_a, pos_b, neg_b)
    r2 = delong_test(pos_b, neg_b, pos_a, neg_a)
    assert r1.p == pytest.approx(r2.p, abs=1e-12)
    assert r1.z == pytest.approx(-r2.z, abs=1e-9)


# ── 未加權總和（不擬合權重）──

def test_unweighted_sum_adds_signals():
    assert unweighted_sum({"a": [1.0, 2.0], "b": [0.5, 0.5]}) == [1.5, 2.5]


def test_unweighted_sum_rejects_ragged_input():
    with pytest.raises(ValueError):
        unweighted_sum({"a": [1.0, 2.0], "b": [1.0]})


def test_unweighted_sum_is_order_independent():
    assert (unweighted_sum({"a": [1.0], "b": [2.0]})
            == unweighted_sum({"b": [2.0], "a": [1.0]}))


def test_no_weight_fitting_interface_exists():
    """§P4：不得在資料上擬合權重。這支測試釘住「沒有那個介面」。"""
    import cognitive_core.eval.auc as m
    banned = [n for n in dir(m)
              if any(k in n.lower() for k in ("fit", "train", "optimi", "weight"))
              and n != "unweighted_sum"]
    assert not banned, f"出現了疑似擬合介面：{banned}"


# ── 事前檢定力 ──

def test_required_auc_rises_with_noise():
    clean = required_auc(90, 110, noise=0.0)
    noisy = required_auc(90, 110, noise=0.25)
    assert noisy > clean


def test_required_auc_falls_with_more_data():
    assert required_auc(450, 550, noise=0.25) < required_auc(90, 110, noise=0.25)


def test_required_auc_matches_hanley_mcneil():
    """回代驗證：在臨界值上 CI 下界確實剛好越過 0.5。"""
    t = required_auc(90, 110, noise=0.0)
    _, lo, _ = hanley_mcneil(t, 90, 110)
    assert lo > 0.5
    _, lo2, _ = hanley_mcneil(t - 0.002, 90, 110)
    assert lo2 <= 0.5


def test_required_auc_nan_when_noise_destroys_signal():
    assert math.isnan(required_auc(90, 110, noise=0.5))


def test_auc_result_ci_text_for_nan():
    r = AucResult("x", float("nan"), float("nan"), (float("nan"),) * 2, 0, 0)
    assert r.ci_text() == "—" and r.excludes_half is False
