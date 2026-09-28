"""決策時間軸與倫理界線（v3 架構書 §P7 測試提示詞第 2 項）。

⚠️ **這是 P7 最重要的測試。** 計畫書 §4.9 明文要求介面不揭露模型的原始
推理文字。這條界線若只寫在文件上，任何一次「順手把 reason 欄位塞滿」
就會破功，而且從畫面上看起來完全正常。

防兩件事：
  直接洩漏——payload 裡有 reasoning_content
  間接洩漏——CoT 從別的欄位混進來（所以還限制自由文本長度）
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.timeline import (  # noqa: E402
    CONTENT_KEYS,
    MAX_TEXT,
    CoTLeak,
    TimelineNode,
    assert_no_cot,
    build_timeline,
    render_lines,
    summarise_cost,
    to_json,
)


def state(*recs) -> dict:
    return {"timeline": [{"step": i, **r} for i, r in enumerate(recs, 1)]}


REAL = state(
    {"node": "route", "path": "slow", "ambiguity_score": 0.72,
     "triggered": ["S1_polysemy", "S2_subject_ellipsis"]},
    {"node": "build_anchor", "tier": 1, "n_readings": 2,
     "unknown_scalars": ["agent", "social_relation"]},
    {"node": "translate_multi", "languages": ["en", "ja"], "n_samples": 2},
    {"node": "verify", "detector_score": 0.851, "consistency": 0.804,
     "passed": False, "n_differences": 1},
    {"node": "reflect", "tier": 1, "revision": 1,
     "unknown_before": ["agent", "social_relation"], "unknown_after": ["agent"]},
    {"node": "write_memory", "high_uncertainty": True},
)


# ── 結構契約 ──

def test_every_node_has_the_four_fields():
    for n in build_timeline(REAL):
        assert isinstance(n.step, int)
        assert n.node and n.label
        assert isinstance(n.detail, dict)
        assert isinstance(n.cost, dict)


def test_order_matches_execution_order():
    tl = build_timeline(REAL)
    assert [n.step for n in tl] == list(range(1, len(REAL["timeline"]) + 1))
    assert [n.node for n in tl] == [r["node"] for r in REAL["timeline"]]


def test_labels_are_human_readable():
    tl = build_timeline(REAL)
    assert tl[0].label == "訊號量測"
    assert tl[3].label == "回譯比對"


def test_unknown_node_falls_back_to_its_name():
    assert build_timeline(state({"node": "新節點"}))[0].label == "新節點"


def test_costs_are_attached_by_step():
    tl = build_timeline(REAL, costs={2: {"calls": 1, "tokens": 300}})
    assert tl[1].cost == {"calls": 1, "tokens": 300}
    assert tl[0].cost == {}


def test_empty_state_yields_empty_timeline():
    assert build_timeline({}) == []


# ── 倫理界線：直接洩漏 ⭐ ──

@pytest.mark.parametrize("key", [
    "reasoning_content", "reasoning_detail", "cot", "chain_of_thought",
    "raw_reasoning", "thinking", "REASONING_CONTENT", "model_cot",
])
def test_forbidden_keys_are_rejected(key):
    with pytest.raises(CoTLeak):
        build_timeline(state({"node": "verify", key: "先想一下……"}))


def test_forbidden_key_nested_in_list_is_caught():
    with pytest.raises(CoTLeak):
        build_timeline(state({"node": "verify",
                              "samples": [{"reasoning_content": "…"}]}))


def test_forbidden_key_deeply_nested_is_caught():
    with pytest.raises(CoTLeak):
        build_timeline(state({"node": "x", "a": {"b": {"c": {"cot": "…"}}}}))


# ── 倫理界線：間接洩漏 ⭐ ──

def test_long_free_text_is_rejected():
    """CoT 可以從任何欄位混進來，不只是叫 reasoning_content 的那個。"""
    with pytest.raises(CoTLeak):
        build_timeline(state({"node": "reflect", "reason": "很長的推理" * 60}))


def test_text_at_the_limit_passes():
    build_timeline(state({"node": "reflect", "reason": "字" * MAX_TEXT}))


def test_text_one_over_the_limit_fails():
    with pytest.raises(CoTLeak):
        build_timeline(state({"node": "reflect", "reason": "字" * (MAX_TEXT + 1)}))


@pytest.mark.parametrize("key", CONTENT_KEYS)
def test_content_keys_are_exempt_from_length_limit(key):
    """譯文本身可以很長——那是內容不是推理。"""
    build_timeline(state({"node": "translate_multi", key: "word " * 200}))


def test_long_text_inside_a_list_is_caught():
    with pytest.raises(CoTLeak):
        build_timeline(state({"node": "reflect",
                              "notes": ["短", "長" * (MAX_TEXT + 1)]}))


def test_error_message_names_the_offending_path():
    with pytest.raises(CoTLeak) as e:
        build_timeline(state({"node": "v", "deep": {"reasoning_content": "x"}}))
    assert "deep.reasoning_content" in str(e.value)


# ── 不靜默過濾 ⭐ ──

def test_violation_raises_rather_than_being_stripped():
    """靜默過濾比報錯危險——它會讓洩漏在下一次改動後悄悄復活。"""
    bad = state({"node": "verify", "reasoning_content": "……"})
    with pytest.raises(CoTLeak):
        build_timeline(bad)
    # 原始資料未被就地修改
    assert "reasoning_content" in bad["timeline"][0]


def test_to_json_also_guards():
    tl = [TimelineNode(1, "v", "驗證", {"reasoning_content": "x"})]
    with pytest.raises(CoTLeak):
        to_json(tl)


def test_assert_no_cot_accepts_plain_dicts():
    assert_no_cot([{"step": 1, "node": "v", "detail": {"score": 0.9}}])


# ── 序列化 ──

def test_serialised_timeline_has_no_forbidden_substring():
    """⭐ 最終防線：整份 JSON 掃一遍。"""
    s = to_json(build_timeline(REAL))
    for bad in ("reasoning_content", "chain_of_thought", "raw_reasoning"):
        assert bad not in s


def test_json_round_trips():
    d = json.loads(to_json(build_timeline(REAL)))
    assert len(d) == len(REAL["timeline"])
    assert all({"step", "node", "label", "detail", "cost"} <= set(x) for x in d)


# ── 展示 ──

def test_render_includes_signal_disclaimer():
    """⚠️ 訊號值必須標為診斷資訊——展示無效的分流會誤導觀眾。"""
    lines = render_lines(build_timeline(REAL))
    joined = "\n".join(lines)
    assert "診斷資訊，非分流依據" in joined
    assert "0.5" in joined, "未附上 CI 涵蓋 0.5 的實測結果"


def test_render_has_one_line_per_node():
    tl = build_timeline(REAL)
    lines = render_lines(tl)
    # route 節點多一行免責說明
    assert len(lines) == len(tl) + 1


def test_render_formats_floats():
    assert "0.851" in "\n".join(render_lines(build_timeline(REAL)))


def test_summarise_cost_handles_missing_keys():
    assert "0 次呼叫" in summarise_cost({})
