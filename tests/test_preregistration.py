"""並列上限與預先登記閘門（2026-08-21 裁示第 4 條）。

規則：所有訊號在計算 AUC 之前先算並列上限；上限 < required_auc 者必須
二選一（改連續／標記無法檢定），且決定要在看到任何 AUC 之前做完。

這條規則的價值全在**時序**上，所以測試要守的是「未登記就擋下」，
而不是「登記檔長得對不對」。
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.eval.auc import required_auc  # noqa: E402
from cognitive_core.eval.gate import (  # noqa: E402
    check_preregistration,
    classify_ceiling,
    tie_ceiling,
)


# ── tie_ceiling ──

def test_all_distinct_gives_ceiling_one():
    k, mx, tie, cap = tie_ceiling([float(i) for i in range(50)])
    assert k == 50 and tie == 0.0 and cap == 1.0


def test_all_identical_gives_ceiling_half():
    """全部同值 → 每一對都是並列 → AUC 恆為 0.5，上限就是 0.5。"""
    k, mx, tie, cap = tie_ceiling([0.0] * 20)
    assert k == 1 and mx == 1.0 and tie == pytest.approx(1.0)
    assert cap == pytest.approx(0.5)


def test_half_tied_ceiling_between():
    vals = [0.0] * 10 + [float(i) for i in range(1, 11)]
    _, _, tie, cap = tie_ceiling(vals)
    assert 0.0 < tie < 1.0 and 0.5 < cap < 1.0


def test_ceiling_matches_hand_computation():
    """4 個值中有 2 個同值：C(2,2) 的有序對 2 / 全部 12 = 1/6。"""
    _, _, tie, cap = tie_ceiling([1.0, 1.0, 2.0, 3.0])
    assert tie == pytest.approx(2 / 12)
    assert cap == pytest.approx(1 - 0.5 * 2 / 12)


def test_ceiling_ignores_float_noise():
    """1e-12 的差不該被當成不同值——否則上限會被浮點誤差灌成 1.0。"""
    k, _, _, _ = tie_ceiling([0.3, 0.3 + 1e-12, 0.3 - 1e-12])
    assert k == 1


def test_ceiling_handles_tiny_input():
    assert tie_ceiling([])[3] == 1.0
    assert tie_ceiling([0.5])[3] == 1.0


def test_sparse_binary_signal_is_near_floor():
    """S4 的形狀：400 筆中只有 8 筆非零。"""
    vals = [0.0] * 392 + [1.0] * 8
    _, _, _, cap = tie_ceiling(vals)
    assert cap < 0.53, f"上限 {cap} 不該高於 0.53"
    assert cap < required_auc(196, 204, noise=0.0), "應被判為低於門檻"


# ── classify_ceiling ──

def test_classify_below_and_ok():
    assert classify_ceiling(0.52, 0.557) == "below_required"
    assert classify_ceiling(0.92, 0.557) == "ok"


def test_classify_boundary_is_inclusive_upward():
    assert classify_ceiling(0.557, 0.557) == "ok"


# ── check_preregistration ──

def write_reg(d: pathlib.Path, signals: list[dict]) -> None:
    (d / "signal_preregistration.json").write_text(
        json.dumps({"signals": signals}, ensure_ascii=False), encoding="utf-8")


def test_missing_file_blocks(tmp_path):
    ok, why = check_preregistration(tmp_path, ["S1"])
    assert ok is False and "尚未登記" in why


def test_unregistered_signal_blocks(tmp_path):
    write_reg(tmp_path, [{"signal": "S1", "status": "ok"}])
    ok, why = check_preregistration(tmp_path, ["S1", "S9_new"])
    assert ok is False and "S9_new" in why


def test_below_required_without_action_blocks(tmp_path):
    """⭐ 核心：上限低於門檻卻沒做決定，就是還沒完成預先登記。"""
    write_reg(tmp_path, [{"signal": "S4", "status": "below_required"}])
    ok, why = check_preregistration(tmp_path, ["S4"])
    assert ok is False and "未做處置決定" in why


def test_below_required_with_invalid_action_blocks(tmp_path):
    write_reg(tmp_path, [{"signal": "S4", "status": "below_required",
                          "action": "ignore"}])
    assert check_preregistration(tmp_path, ["S4"])[0] is False


@pytest.mark.parametrize("action", ["continuous", "untestable"])
def test_below_required_with_valid_action_passes(tmp_path, action):
    write_reg(tmp_path, [{"signal": "S4", "status": "below_required",
                          "action": action, "reason": "…"}])
    assert check_preregistration(tmp_path, ["S4"])[0] is True


def test_all_ok_passes(tmp_path):
    write_reg(tmp_path, [{"signal": "S1", "status": "ok"},
                         {"signal": "S3", "status": "ok"}])
    ok, why = check_preregistration(tmp_path, ["S1", "S3"])
    assert ok is True and "2 個訊號" in why


def test_corrupt_file_blocks(tmp_path):
    (tmp_path / "signal_preregistration.json").write_text("{oops", encoding="utf-8")
    assert check_preregistration(tmp_path, ["S1"])[0] is False


# ── 專案現況 ──

def test_project_registration_records_no_labels_used():
    """登記檔必須自證沒有用到標籤——這是整條規則的立足點。"""
    f = (pathlib.Path(__file__).resolve().parents[1]
         / "data" / "results" / "signal_preregistration.json")
    if not f.exists():
        pytest.skip("尚未登記")
    d = json.loads(f.read_text(encoding="utf-8"))
    assert d.get("labels_used") is False
    assert d.get("commit") and d.get("registered_at")


def test_project_registration_covers_current_signals():
    root = pathlib.Path(__file__).resolve().parents[1]
    f = root / "data" / "results" / "signal_preregistration.json"
    sig = root / "data" / "results" / "signals_all.json"
    if not (f.exists() and sig.exists()):
        pytest.skip("尚未登記")
    names = json.loads(sig.read_text(encoding="utf-8"))["signals"]
    ok, why = check_preregistration(f.parent, names)
    assert ok, why
