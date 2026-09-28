"""A/B 位置效應與它對標籤噪音的貢獻（2026-08-21 裁示第 2 條）。

配平讓**點估計**不受位置影響，但受位置驅動的判定與譯文內容無關——那是雜訊。
本模組把它換算成標籤錯誤率的下界，餵給 `auc.required_auc(noise=…)`。

換算模型：judge 以機率 q 直接依位置作答，其餘依內容判斷
    gold 在 A：正確率 = q·1 + (1−q)·a
    gold 在 B：正確率 = q·0 + (1−q)·a
    差 = q，配平下位置驅動者一半落錯 → 噪音貢獻 q/2
"""

from __future__ import annotations

import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.eval.wsd import Outcome, position_effect  # noqa: E402


def make(gold_first: bool, correct: bool, *, letter: str | None = None) -> Outcome:
    """造一筆二元判定的結果。`letter` 未給時由 gold_first/correct 推出。"""
    if letter is None:
        letter = "A" if (gold_first == correct) else "B"
    gold, dis = "G", "D"
    o = Outcome(probe_id="x", stratum="dominant", word="詞", sentence="句",
                gold=gold, translation="t")
    o.distractor = dis
    o.gold_first = gold_first
    o.raw_choice = letter
    o.n_candidates = 2
    o.chosen = gold if (letter == "A") == gold_first else dis
    return o


def batch(n_a_correct, n_a_wrong, n_b_correct, n_b_wrong) -> list[Outcome]:
    return ([make(True, True) for _ in range(n_a_correct)]
            + [make(True, False) for _ in range(n_a_wrong)]
            + [make(False, True) for _ in range(n_b_correct)]
            + [make(False, False) for _ in range(n_b_wrong)])


# ── 基本 ──

def test_no_position_effect_gives_zero_noise():
    """兩個位置正確率相同 → q=0 → 不貢獻噪音。"""
    r = position_effect(batch(70, 30, 70, 30))
    assert r["available"] is True
    assert r["diff"] == pytest.approx(0.0)
    assert r["implied_noise"] == 0.0


def test_pure_position_heuristic_is_detected():
    """judge 完全依位置作答：gold 在 A 全對、在 B 全錯 → q=1。"""
    r = position_effect(batch(50, 0, 0, 50))
    assert r["diff"] == pytest.approx(1.0)
    assert r["implied_noise"] == pytest.approx(0.5)
    assert r["chose_a_rate"] == pytest.approx(1.0)
    assert r["chose_a_biased"] is True


def test_implied_noise_is_half_the_difference():
    r = position_effect(batch(60, 40, 40, 60))
    assert r["implied_noise"] == pytest.approx(r["diff"] / 2)


def test_negative_difference_clamps_to_zero_noise():
    """B 位反而較準時 q<0，噪音不可為負。"""
    r = position_effect(batch(40, 60, 60, 40))
    assert r["diff"] < 0
    assert r["implied_noise"] == 0.0


def test_counterbalancing_leaves_point_estimate_unbiased():
    """⭐ 配平的核心保證：位置效應再大，整體正確率仍是兩位置的平均。

    這正是「點估計不受影響、但變異數還是進來了」那句話的前半。
    """
    outs = batch(50, 0, 0, 50)          # 極端位置效應
    overall = sum(1 for o in outs if o.correct) / len(outs)
    assert overall == pytest.approx(0.5)


# ── 統計量 ──

def test_z_and_p_are_consistent():
    r = position_effect(batch(74, 26, 66, 34))
    assert r["z"] == pytest.approx(r["diff"] / r["se"])
    assert 0.0 <= r["p"] <= 1.0


def test_large_effect_is_significant():
    assert position_effect(batch(90, 10, 50, 50))["p"] < 0.001


def test_small_effect_is_not_significant():
    assert position_effect(batch(51, 49, 50, 50))["p"] > 0.05


def test_ci_brackets_the_difference():
    r = position_effect(batch(74, 26, 66, 34))
    assert r["diff_ci"][0] < r["diff"] < r["diff_ci"][1]


def test_noise_ci_is_half_the_diff_ci_clamped():
    r = position_effect(batch(74, 26, 66, 34))
    lo, hi = r["implied_noise_ci"]
    assert lo == pytest.approx(max(r["diff_ci"][0], 0.0) / 2)
    assert hi == pytest.approx(max(r["diff_ci"][1], 0.0) / 2)
    assert lo >= 0.0


# ── 邊界 ──

def test_too_few_items_reports_unavailable():
    assert position_effect(batch(1, 0, 1, 0))["available"] is False
    assert position_effect([])["available"] is False


def test_only_one_position_reports_unavailable():
    """全部 gold 都在 A → 沒有對照，不能算。"""
    assert position_effect(batch(10, 10, 0, 0))["available"] is False


def test_none_and_errors_are_excluded():
    outs = batch(50, 50, 50, 50)
    bad = Outcome(probe_id="y", stratum="dominant", word="詞", sentence="句",
                  gold="G", translation="t")
    bad.raw_choice = "NONE"
    bad.chosen = "NONE"
    bad.gold_first = True
    assert position_effect(outs + [bad])["n"] == len(outs)


def test_chose_a_rate_matches_raw_choices():
    outs = batch(30, 20, 20, 30)
    r = position_effect(outs)
    assert r["chose_a"] == sum(1 for o in outs if o.raw_choice == "A")


# ── 專案現況 ──

def test_project_position_effect_is_recorded():
    """400 筆基準必須把位置效應存進 JSON——它是噪音估計的唯一實證來源。"""
    import json
    f = (pathlib.Path(__file__).resolve().parents[1]
         / "data" / "results" / "wsd_baseline400.json")
    if not f.exists():
        pytest.skip("尚無 400 筆基準")
    pe = json.loads(f.read_text(encoding="utf-8")).get("position_effect")
    assert pe and pe.get("available"), "基準結果缺少 position_effect"
    assert pe["implied_noise"] >= 0.0
    assert abs(pe["n_gold_a"] - pe["n_gold_b"]) <= 2, \
        f"配平失效：A {pe['n_gold_a']}／B {pe['n_gold_b']}"


def test_project_noise_is_a_lower_bound_not_the_old_25pct():
    """⚠️ 不得再用第一輪推的 25%——那份驗證已標記 contaminated。"""
    import json
    root = pathlib.Path(__file__).resolve().parents[1]
    f = root / "data" / "results" / "signal_preregistration.json"
    if not f.exists():
        pytest.skip("尚未登記")
    d = json.loads(f.read_text(encoding="utf-8"))
    got = d["signals"][0].get("position_derived_noise")
    assert got is not None, "登記檔未記錄位置效應推得的噪音"
    assert not math.isclose(got, 0.25), "噪音仍寫死為 25%"
