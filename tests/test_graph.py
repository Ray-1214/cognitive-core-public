"""狀態機邏輯的測試（P1 測試提示詞第 1 條）。

目標：**不呼叫 API 也能驗證狀態機正確**。全部走 FakeClient。
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.graph import build_graph, initial_state, stub_router  # noqa: E402
from cognitive_core.verify import VerifyConfig  # noqa: E402

TEXT = "他昨天走了"


def fast_router(state):
    return {"path": "fast", "ambiguity_score": 0.1, "signals": {},
            "reason": "test_fast"}


def run_graph(client, *, router=None, profile="cross_en_ja"):
    g = build_graph(client, profile=profile, router=router)
    return g.invoke(initial_state(TEXT, ["en", "ja"], profile))


# ── 快速通道 ──

def test_fast_path_skips_anchor(fake_client):
    """route=fast 時只呼叫 translate_direct，不建錨點。"""
    st = run_graph(fake_client, router=fast_router)
    nodes = [e["node"] for e in st["timeline"]]
    assert "translate_direct" in nodes
    assert "build_anchor" not in nodes
    assert "verify" not in nodes
    assert st.get("anchor") is None
    assert "reflect" not in fake_client.roles_called()


def test_fast_path_still_produces_translations(fake_client):
    st = run_graph(fake_client, router=fast_router)
    assert set(st["translations"]) == {"en", "ja"}


# ── 慢速通道 ──

def test_slow_path_node_order(consistent_client):
    """route=slow 時 build_anchor → translate_multi → verify。"""
    st = run_graph(consistent_client)
    nodes = [e["node"] for e in st["timeline"]]
    assert nodes[:4] == ["route", "build_anchor", "translate_multi", "verify"]
    assert nodes[-1] == "write_memory"


def test_stub_router_always_slow():
    assert stub_router({})["path"] == "slow"
    assert stub_router({})["reason"] == "router_stub"


def test_slow_path_builds_anchor(consistent_client):
    st = run_graph(consistent_client)
    assert st["anchor"] is not None
    assert st["anchor"]["source_text"] == TEXT
    assert st["final"]["n_readings"] == 2


# ── 反思迴圈 ──

def test_reflection_triggered_on_low_consistency(fake_client):
    """verify 失敗時進 reflect，revision_count 遞增。"""
    st = run_graph(fake_client)
    nodes = [e["node"] for e in st["timeline"]]
    assert "reflect" in nodes
    assert st["revision_count"] >= 1


def test_reflection_not_triggered_when_consistent(consistent_client):
    st = run_graph(consistent_client)
    assert "reflect" not in [e["node"] for e in st["timeline"]]
    assert st["revision_count"] == 0


def test_reflection_loop_capped(fake_client):
    """revision 達 max_revisions 時強制離開，不無限迴圈。"""
    max_rev = int(VerifyConfig().thresholds.get("max_revisions", 3))
    st = run_graph(fake_client)
    assert st["revision_count"] <= max_rev, "反思迴圈未受上限約束"
    n_reflect = sum(1 for e in st["timeline"] if e["node"] == "reflect")
    assert n_reflect == max_rev, f"預期恰好反思 {max_rev} 次，實際 {n_reflect}"
    assert st["final"] is not None, "撞上限後仍須輸出結果，不可卡住"


def test_reflection_increments_monotonically(fake_client):
    st = run_graph(fake_client)
    revs = [e["revision"] for e in st["timeline"] if e["node"] == "reflect"]
    assert revs == sorted(revs) and len(set(revs)) == len(revs)


# ── 不變量 ──

@pytest.mark.parametrize("router", [None, fast_router])
def test_source_text_never_modified(router):
    """source_text 在任何節點後都未被修改。"""
    from tests.conftest import FakeClient
    c = FakeClient()
    st = run_graph(c, router=router)
    assert st["source_text"] == TEXT
    if st.get("anchor"):
        assert st["anchor"]["source_text"] == TEXT
    assert st["final"]["source_text"] == TEXT


def test_timeline_has_no_reasoning_content(fake_client):
    """timeline 不含任何 reasoning_content 欄位（計畫書 §4.9 倫理界線）。"""
    st = run_graph(fake_client)
    dumped = json.dumps(st["timeline"], ensure_ascii=False)
    assert "reasoning_content" not in dumped
    for ev in st["timeline"]:
        assert "reasoning_content" not in ev


def test_timeline_carries_no_long_free_text(fake_client):
    """防止原始 CoT 從別的欄位洩漏：timeline 不該有超長自由文本。"""
    st = run_graph(fake_client)
    for ev in st["timeline"]:
        for k, v in ev.items():
            if isinstance(v, str):
                assert len(v) <= 200, f"timeline.{ev['node']}.{k} 長度 {len(v)}"


def test_timeline_steps_are_sequential(fake_client):
    st = run_graph(fake_client)
    assert [e["step"] for e in st["timeline"]] == list(
        range(1, len(st["timeline"]) + 1))


def test_final_contains_required_fields(consistent_client):
    st = run_graph(consistent_client)
    fin = st["final"]
    for k in ["source_text", "path", "translations", "detector_score",
              "consistency_score", "revisions", "n_readings", "readings",
              "unknown_scalars", "high_uncertainty", "clarifications"]:
        assert k in fin, f"final 缺欄位 {k}"


def test_graph_does_not_call_real_api(fake_client):
    """所有呼叫都經過 FakeClient，沒有漏網的真實請求。"""
    run_graph(fake_client)
    assert fake_client.calls, "FakeClient 完全沒被呼叫，代表有別的路徑"
    assert set(fake_client.roles_called()) <= {
        "reflect", "translate", "backtrans", "verify", "embed"}
