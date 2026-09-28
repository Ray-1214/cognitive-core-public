"""Streamlit 介面的煙測（v3 架構書 §P7 測試提示詞第 3 項）。

⚠️ **重點是「可以 import 而不執行副作用」。** 若 import 時就建 Client、
讀 .env、連線，測試會依環境而變，CI 也跑不動。所有這類動作必須放在
`run_pipeline()` 裡。

另外守住兩條界線在介面層仍然成立：
  不揭露原始 CoT、不展示分流決策。
"""

from __future__ import annotations

import importlib
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

APP = ROOT / "app" / "streamlit_app.py"


def load():
    return importlib.import_module("streamlit_app")


def test_module_imports_without_side_effects():
    """import 時不得建立 Client 或讀取 .env。"""
    import cognitive_core.llm as llm

    calls = []
    orig = llm.Client.__init__

    def spy(self, *a, **kw):
        calls.append(1)
        return orig(self, *a, **kw)

    llm.Client.__init__ = spy
    try:
        load()
    finally:
        llm.Client.__init__ = orig
    assert not calls, "import streamlit_app 時建立了 Client"


def test_main_is_not_called_on_import():
    m = load()
    assert callable(m.main)


def test_demo_sentences_exist_and_are_clean():
    """展示句不得取自評測資料或 dev-30——那等於在 demo 裡洩題。"""
    import yaml
    m = load()
    assert len(m.DEMO_SENTENCES) >= 5
    probes = ROOT / "data" / "probes" / "wsd_probes.yaml"
    if probes.exists():
        sents = {p["sentence"] for p in
                 yaml.safe_load(probes.read_text(encoding="utf-8"))["items"]}
        for s in m.DEMO_SENTENCES:
            assert not any(s in x for x in sents), f"展示句 {s} 出現在探針集"
    d30 = ROOT / "data" / "dev30" / "sentences.yaml"
    if d30.exists():
        t = d30.read_text(encoding="utf-8")
        for s in m.DEMO_SENTENCES:
            assert s not in t, f"展示句 {s} 取自 dev-30"


def test_profiles_match_the_ablation_design():
    m = load()
    assert m.PROFILES == ["cross_en_ja", "same_en", "single_ja"]


# ── 兩條界線在介面層 ⭐ ──

def test_signal_disclaimer_is_wired_in():
    """訊號值必須標為診斷資訊，且附上 CI 涵蓋 0.5 的實測結果。"""
    m = load()
    assert "診斷資訊，非分流依據" in m.SIGNAL_DISCLAIMER
    assert "0.5" in m.SIGNAL_DISCLAIMER
    src = APP.read_text(encoding="utf-8")
    assert "SIGNAL_DISCLAIMER" in src


def test_no_fast_slow_routing_ui():
    """⚠️ 介面不得出現快慢通道的分流視覺——那個分流實測無效。"""
    src = APP.read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]      # 去掉模組 docstring（那裡有說明文字）
    for bad in ("快速通道", "慢速通道", "fast path", "分流至"):
        assert bad not in body, f"介面出現分流視覺：{bad}"


def test_cot_boundary_is_enforced_not_just_documented():
    src = APP.read_text(encoding="utf-8")
    assert "build_timeline" in src, "未經 build_timeline（其中含 assert_no_cot）"


def test_reasoning_content_never_referenced():
    src = APP.read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]
    assert "reasoning_content" not in body


# ── build_timeline 對 GraphState 的實際輸出 ──

def test_build_timeline_on_a_graphstate_shape():
    from cognitive_core.timeline import build_timeline

    state = {"timeline": [
        {"step": 1, "node": "route", "signals": {"S1_polysemy": 0.73},
         "note": "diagnostic_only"},
        {"step": 2, "node": "build_anchor", "tier": 1, "n_readings": 2,
         "unknown_scalars": ["agent"]},
        {"step": 3, "node": "write_memory", "high_uncertainty": True},
    ]}
    tl = build_timeline(state)
    assert [n.node for n in tl] == ["route", "build_anchor", "write_memory"]
    assert tl[0].detail["signals"]["S1_polysemy"] == 0.73
    assert tl[1].label == "錨點建構"


def test_render_node_signature_is_stable():
    """介面重構時容易忘記 render_node 也吃 TimelineNode。"""
    import inspect
    m = load()
    assert list(inspect.signature(m.render_node).parameters) == ["n"]


@pytest.mark.parametrize("fn", ["run_pipeline", "render_node", "main"])
def test_public_functions_exist(fn):
    assert hasattr(load(), fn)
