"""SemanticAnchor 的四條約束必須由型別強制，不是靠自律（實作規格書 §A-1）。"""

from __future__ import annotations

import pathlib
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.models import (  # noqa: E402
    UNKNOWN,
    AlternativeReading,
    AnchorDraft,
    CulturalItem,
    SemanticAnchor,
    Uncertainty,
    anchor_json_schema,
)

SRC = "方便的話明天再說吧"


def make_draft(**kw) -> AnchorDraft:
    base = {
        "agent": UNKNOWN,
        "time": "明天",
        "register": "SEMI_FORMAL",
        "social_relation": UNKNOWN,
        "uncertainty": Uncertainty(
            text_determinable=False,
            alternative_readings=[
                AlternativeReading(reading="委婉推託", applicable_when="無先前約定",
                                   speaker_intent="SOFT_REFUSAL"),
                AlternativeReading(reading="字面詢問時間", applicable_when="已約定討論",
                                   speaker_intent="INQUIRY"),
            ]),
    }
    base.update(kw)
    return AnchorDraft(**base)


# ── 約束 1：source_text 不可修改 ──

def test_anchor_is_frozen():
    a = SemanticAnchor.from_draft(make_draft(), source_text=SRC)
    with pytest.raises(ValidationError):
        a.source_text = "改掉的原文"


def test_draft_cannot_carry_source_text():
    """LLM 產出的 draft 即使夾帶 source_text 也會被丟棄，結構上無從竄改。"""
    d = AnchorDraft.model_validate({"agent": "我", "source_text": "惡意覆寫"})
    assert not hasattr(d, "source_text")
    a = SemanticAnchor.from_draft(d, source_text=SRC)
    assert a.source_text == SRC


def test_revise_preserves_source_and_bumps_revision():
    a = SemanticAnchor.from_draft(make_draft(), source_text=SRC)
    b = a.revise(make_draft(agent="說話者"))
    assert b.source_text == SRC
    assert b.revisions == a.revisions + 1
    assert b.agent == "說話者"
    assert a.agent == UNKNOWN          # 原實例不受影響


# ── 約束 3：UNKNOWN 是合法值，且各種寫法要正規化 ──

@pytest.mark.parametrize("raw", ["unknown", "UNKNOWN", "  ", "", None,
                                 "未知", "不明", "無法判定", "n/a", "null"])
def test_unknown_normalisation(raw):
    d = AnchorDraft.model_validate({"agent": raw})
    assert d.agent == UNKNOWN, f"{raw!r} 未被正規化，UNKNOWN 統計會失真"


def test_unknown_scalars_uses_actual_values_not_self_report():
    """不採信模型自報的 unknown_fields —— §8.2 顯示該欄位與實際值不一致。"""
    d = make_draft(agent=UNKNOWN, social_relation=UNKNOWN)
    d.uncertainty.unknown_fields = ["time"]          # 模型亂報
    a = SemanticAnchor.from_draft(d, source_text=SRC)
    assert set(a.unknown_scalars()) == {"agent", "social_relation"}


# ── 約束 4：alternative_readings 不設上限 ──

def test_no_cap_on_alternative_readings():
    many = [AlternativeReading(reading=f"讀法{i}") for i in range(20)]
    u = Uncertainty(alternative_readings=many)
    assert len(u.alternative_readings) == 20, "不得設硬上限，改報 precision@k"


def test_speaker_intent_lives_inside_reading_not_top_level():
    """意圖不得是錨點頂層的單值欄位（§8.2 實測該問法會逼出過度自信的斷言）。"""
    assert "speaker_intent" not in AnchorDraft.model_fields
    assert "speaker_intent" in AlternativeReading.model_fields


# ── 不確定性狀態 ──

@pytest.mark.parametrize("kw,expected", [
    ({"text_determinable": False}, False),   # 自報不可決定，但只列 0 個讀法 → 以行為為準
    ({"unknown_fields": ["agent"]}, True),
    ({"alternative_readings": [AlternativeReading(reading="a"),
                               AlternativeReading(reading="b")]}, True),
    ({}, False),
])
def test_high_uncertainty_flag(kw, expected):
    assert Uncertainty(**kw).is_high is expected


def test_determinable_derived_from_behaviour_not_self_report():
    """實測模型會一邊回報 determinable=True、一邊列出三個讀法。

    §8.2 已證實自我回報不承載資訊，一律以列舉行為為準。
    """
    u = Uncertainty(text_determinable=True, alternative_readings=[
        AlternativeReading(reading="讀法一"),
        AlternativeReading(reading="讀法二"),
        AlternativeReading(reading="讀法三"),
    ])
    assert u.text_determinable is True          # 模型自報保留，供比對
    assert u.derived_text_determinable is False  # 行為推導才是採用值
    assert u.self_report_agrees is False
    assert u.is_high is True


def test_self_report_agrees_when_consistent():
    u = Uncertainty(text_determinable=True,
                    alternative_readings=[AlternativeReading(reading="唯一讀法")])
    assert u.self_report_agrees is True
    assert u.is_high is False


def test_ambiguity_score_clamped():
    assert Uncertainty(ambiguity_score=5.0).ambiguity_score == 1.0
    assert Uncertainty(ambiguity_score=-2.0).ambiguity_score == 0.0


# ── prompt 區塊 ──

def test_prompt_block_puts_source_first():
    """原文置頂：翻譯一律從錨點出發，不從上一輪譯文（約束 2 的前提）。"""
    a = SemanticAnchor.from_draft(make_draft(), source_text=SRC)
    block = a.to_prompt_block()
    assert block.startswith(f"【原文】{SRC}")
    assert "委婉推託" in block and "字面詢問時間" in block
    assert "agent" in block


def test_cultural_item_appears_in_block():
    d = make_draft(cultural_items=[CulturalItem(
        term="方便", literal="convenient", actual_sense="委婉推託",
        ambiguity_type="PRAGMATIC")])
    block = SemanticAnchor.from_draft(d, source_text=SRC).to_prompt_block()
    assert "方便" in block and "委婉推託" in block


# ── schema ──

def test_json_schema_excludes_source_text():
    s = anchor_json_schema()
    assert "source_text" not in s.get("properties", {})
    assert "uncertainty" in s["properties"]
