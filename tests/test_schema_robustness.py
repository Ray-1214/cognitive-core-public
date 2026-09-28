"""schema 與驗證的健壯性（本輪實跑抓到的三個 bug）。

三個 bug 都是「形式合法但語意錯誤」，降級階梯若只看型別會靜默接受：

1. tier1 strict 模式處理 $defs/$ref 失敗，把讀法陣列攤平成布林旗標
2. 模型把 cultural_items 寫成 dict 而非 list，害整份作廢
3. 模型回報 text_determinable=false 卻不列任何讀法
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.models import (  # noqa: E402
    AnchorDraft,
    anchor_json_schema,
    anchor_semantics_ok,
)


# ── Bug 1：schema 不得含 $ref / $defs ──

def test_schema_has_no_refs():
    """gpt-oss-120b 在 strict 模式下遇到 $ref 會把物件陣列攤平成布林旗標，
    且形式上仍合法，降級階梯察覺不到。
    """
    s = anchor_json_schema()
    dumped = json.dumps(s)
    assert "$ref" not in dumped, "schema 仍含 $ref，strict 模式會失敗"
    assert "$defs" not in dumped


def test_schema_readings_is_array_of_objects():
    s = anchor_json_schema()
    u = s["properties"]["uncertainty"]
    ar = u["properties"]["alternative_readings"]
    assert ar["type"] == "array"
    assert ar["items"]["type"] == "object"
    assert "reading" in ar["items"]["properties"]


# ── Bug 2：cultural_items 形狀容錯 ──

@pytest.mark.parametrize("raw,expected_terms", [
    (None, []),
    ([], []),
    ([{"term": "走了"}], ["走了"]),
    ({"term": "走了", "literal": "left"}, ["走了"]),
    ({"ambiguity_type": "LEXICAL", "items": ["走"]}, ["走"]),
    ({"items": [{"term": "方便"}, {"term": "意思"}]}, ["方便", "意思"]),
    ({"沒有可辨識的鍵": 1}, []),
])
def test_cultural_items_coercion(raw, expected_terms):
    """形狀錯不該讓整份作廢——真正要驗的是讀法有沒有填對。"""
    d = AnchorDraft.model_validate({"cultural_items": raw})
    assert [c.term for c in d.cultural_items] == expected_terms


def test_cultural_items_dict_form_preserves_sibling_fields():
    d = AnchorDraft.model_validate({
        "cultural_items": {"ambiguity_type": "LEXICAL", "items": ["走"]}})
    assert d.cultural_items[0].ambiguity_type == "LEXICAL"


# ── Bug 3：語意層級健全性 ──

def test_determinable_false_without_readings_is_rejected():
    """宣稱有歧義就必須列出是哪些讀法，否則 precision@k 算不出來。"""
    bad = {"uncertainty": {"text_determinable": False, "alternative_readings": []}}
    msg = anchor_semantics_ok(bad)
    assert msg is not None and "讀法" in msg


def test_determinable_false_with_one_reading_is_rejected():
    bad = {"uncertainty": {"text_determinable": False,
                           "alternative_readings": [{"reading": "只有一個"}]}}
    assert anchor_semantics_ok(bad) is not None


def test_determinable_false_with_two_readings_is_ok():
    good = {"uncertainty": {"text_determinable": False,
                            "alternative_readings": [{"reading": "離開"},
                                                     {"reading": "過世"}]}}
    assert anchor_semantics_ok(good) is None


def test_determinable_true_without_readings_is_ok():
    """明確句不列讀法是正確行為，不得誤判為失敗。"""
    good = {"uncertainty": {"text_determinable": True, "alternative_readings": []}}
    assert anchor_semantics_ok(good) is None


def test_missing_uncertainty_is_ok():
    assert anchor_semantics_ok({}) is None


def test_flattened_boolean_flags_are_caught():
    """tier1 實際產出的退化形式：讀法變成布林旗標。"""
    degenerate = {"uncertainty": {
        "text_determinable": False,
        "alternative_readings_are_exhaustive": True,
        "alternative_readings_are_short": True,
    }}
    assert anchor_semantics_ok(degenerate) is not None
