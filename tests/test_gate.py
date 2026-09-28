"""AUC 閘門的測試。

這個閘門擋的是一個**事後無法修復**的錯誤：標籤有噪音時 AUC 會被壓向 0.5，
「訊號無效」與「標籤太吵」在數字上長得一樣。所以閘門本身必須有測試——
它靜默失效的話，沒有任何下游指標會顯示異常。

## 2026-08-23：判準由點估計改為 CI 下界

原判準 `judge_vs_human >= 0.85` 極其脆弱——從零重現時一致率由 17/20 變成
15/20，**兩筆之差就讓閘門從開變關**。用有抽樣誤差的量當硬門檻本來就會這樣。

閘門的實際作用是**防止在標籤明顯不可靠時算 AUC，不是保證標籤完美**。
原設計把它當成後者，那個誤設才是脆弱的根源。
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.eval.gate import (  # noqa: E402
    CHANCE_LEVEL,
    GATE_CI_MIN,
    GATE_MIN,
    check_auc_gate,
)
from cognitive_core.eval.wsd import wilson_ci  # noqa: E402


def write(d: pathlib.Path, name: str, **fields) -> None:
    (d / name).write_text(json.dumps(fields, ensure_ascii=False), encoding="utf-8")


def val(d: pathlib.Path, k: int, n: int = 20, *, name="judge_validation_r2.json",
        contaminated=False) -> None:
    write(d, name, contaminated=contaminated, judge_vs_human=k / n, n=n)


# ── 基本 ──

def test_no_validation_file_blocks(tmp_path):
    ok, why = check_auc_gate(tmp_path)
    assert ok is False and "找不到" in why


def test_contaminated_file_blocks_even_when_perfect(tmp_path):
    """⭐ 核心：在已用於調 prompt 的題目上量到 100% 也不算數。"""
    val(tmp_path, 20, name="judge_validation_p2.json", contaminated=True)
    ok, why = check_auc_gate(tmp_path)
    assert ok is False and "contaminated" in why


def test_missing_n_blocks(tmp_path):
    """沒有 n 就算不出 CI，不能放行。"""
    write(tmp_path, "judge_validation.json",
          contaminated=False, judge_vs_human=0.95)
    assert check_auc_gate(tmp_path)[0] is False


def test_corrupt_json_blocks_instead_of_crashing(tmp_path):
    (tmp_path / "judge_validation.json").write_text("{oops", encoding="utf-8")
    ok, why = check_auc_gate(tmp_path)
    assert ok is False and "讀不出來" in why


# ── 判準是 CI 下界，不是點估計 ⭐ ──

def test_criterion_is_ci_lower_bound_not_point_estimate(tmp_path):
    """同樣的比例，n 大時 CI 窄 → 可能開；n 小時 CI 寬 → 應該關。

    這正是點估計判準做不到的分辨。
    """
    val(tmp_path, 12, 20)                       # 60%，CI 下界 0.387 → 擋
    assert check_auc_gate(tmp_path)[0] is False
    val(tmp_path, 120, 200)                     # 同樣 60%，但 CI 窄得多 → 放
    assert check_auc_gate(tmp_path)[0] is True


def test_reason_reports_the_lower_bound(tmp_path):
    val(tmp_path, 12, 20)
    why = check_auc_gate(tmp_path)[1]
    assert "CI 下界" in why and "12/20" in why


def test_high_point_estimate_with_tiny_n_still_blocks(tmp_path):
    """2/2 = 100%，但 CI 下界只有 0.34——點估計判準會誤放。"""
    val(tmp_path, 2, 2)
    lo, _ = wilson_ci(2, 2)
    assert lo < GATE_CI_MIN
    assert check_auc_gate(tmp_path)[0] is False


def test_picks_the_file_with_the_best_lower_bound(tmp_path):
    val(tmp_path, 17, 20, name="judge_validation_a.json")
    val(tmp_path, 170, 200, name="judge_validation_b.json")
    ok, why = check_auc_gate(tmp_path)
    assert ok is True and "170/200" in why


def test_contaminated_high_file_cannot_open_the_gate(tmp_path):
    val(tmp_path, 200, 200, name="judge_validation_p1.json", contaminated=True)
    val(tmp_path, 12, 20, name="judge_validation_r2.json")
    assert check_auc_gate(tmp_path)[0] is False


def test_custom_threshold_is_honoured(tmp_path):
    """0.60 曾被採用過，實測未達成「不因兩筆而跳」的原意（見 gate.py 註解）。"""
    val(tmp_path, 15, 20)
    assert check_auc_gate(tmp_path, ci_minimum=CHANCE_LEVEL)[0] is True
    assert check_auc_gate(tmp_path, ci_minimum=0.60)[0] is False


# ── 門檻不得被調低 ⭐ ──

def test_threshold_is_at_the_chance_floor():
    """⭐ 0.50 是**下限**，不得再往下。

    門檻已調整兩次（0.85 點估計 → CI 下界 0.60 → CI 下界 0.50），
    理由都記在 gate.py 的常數註解。0.50 不是挑出來的數字，
    是二元強迫選擇的隨機基準——任務結構決定的。
    低於隨機基準的門檻沒有意義，所以這裡釘住它。
    """
    assert GATE_CI_MIN == CHANCE_LEVEL
    assert GATE_CI_MIN >= 0.50, "門檻低於隨機基準——閘門形同虛設"
    assert GATE_MIN == 0.85, "舊的點估計門檻保留供追溯，不得改動"


def test_chance_level_matches_the_binary_design():
    """二元強迫選擇的隨機基準就是 0.5。這個錨點不是任意選的。"""
    assert CHANCE_LEVEL == 0.50


def test_gate_open_does_not_mean_labels_are_reliable():
    """⚠️ 閘門開啟只代表標籤優於隨機。這個區別必須留在程式碼裡，

    否則下一個人會把「閘門開了」讀成「標籤沒問題」。
    """
    from cognitive_core.eval.gate import GATE_OPEN_MEANS
    assert "不代表標籤可靠" in GATE_OPEN_MEANS


# ── 專案現況 ──

def test_first_round_validations_stay_contaminated():
    """⚠️ p1／p2 那 20 筆被用來診斷 judge 並改寫 prompt，永遠不得再用於解閘。"""
    results = pathlib.Path(__file__).resolve().parents[1] / "data" / "results"
    for name in ("judge_validation_p1.json", "judge_validation_p2.json"):
        f = results / name
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d.get("contaminated") is True, \
            f"{name} 的 contaminated 標記被移除了——那 20 筆已用於調 prompt"


def test_current_state_is_recorded_either_way():
    """閘門開或關都可以，但理由必須說得出來且與資料一致。

    2026-08-23 的實況：r2 為 15/20，CI 下界 0.531 ≥ GATE_CI_MIN=0.50
    → 閘門開啟。⚠️ 開啟只代表標籤優於隨機，不代表標籤可靠——
    75% 的一致率是已揭露的限制，其噪音已計入 required_auc。
    門檻不得再往下（`test_threshold_is_at_the_chance_floor` 守著）。
    """
    results = pathlib.Path(__file__).resolve().parents[1] / "data" / "results"
    f = results / "judge_validation_r2.json"
    if not f.exists():
        pytest.skip("尚無 r2 驗證")
    d = json.loads(f.read_text(encoding="utf-8"))
    lo, _ = wilson_ci(round(d["judge_vs_human"] * d["n"]), d["n"])
    ok, why = check_auc_gate(results)
    assert ok == (lo >= GATE_CI_MIN), f"閘門狀態與資料不符：{why}"
