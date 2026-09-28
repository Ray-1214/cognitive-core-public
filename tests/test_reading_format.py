"""讀法格式規範與 S7 訊號的測試（本輪 §1-3、§2-1）。

v1 prompt 實測產出的是整句改寫（「方便的話，我們明天再談這件事。」），
而標註 schema 用的是短標籤（「委婉推託」）。兩邊對不起來，
主指標（正確義項命中率、precision@k）就算不出來。

格式違規**只記 warning 不拒絕**：直接拒絕會讓 schema 通過率失真，
而「模型多常不遵守格式」本身是要統計的數據。
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.models import (  # noqa: E402
    MAX_APPLICABLE_CHARS,
    MAX_INTENT_CHARS,
    MAX_READING_CHARS,
    AlternativeReading,
    Uncertainty,
)

GOOD = AlternativeReading(reading="委婉推託", applicable_when="無先前約定",
                          speaker_intent="婉拒")
# 取自 v1 prompt 的實際輸出（reading 與 speaker_intent 為原樣，
# applicable_when 加長以確保三個欄位都跨過各自上限，測到偵測器本身）
SENTENCE_REWRITE = AlternativeReading(
    reading="方便的話，我們明天再談這件事。（說話者委婉地表達希望延後討論某事）",
    applicable_when="說話者委婉地表達希望延後討論某事，但並未明確指定受話者是誰，需要更多語境",
    speaker_intent="延遲決策或討論，尋求對方的配合或理解。")


# ── 格式違規偵測 ──

def test_good_label_has_no_violations():
    assert Uncertainty(alternative_readings=[GOOD]).format_violations == []


def test_sentence_rewrite_is_flagged():
    """整句改寫必須被抓到——這正是 v1 的失敗模式。"""
    v = Uncertainty(alternative_readings=[SENTENCE_REWRITE]).format_violations
    assert any("reading[0]" in x for x in v)
    assert any("speaker_intent[0]" in x for x in v)
    assert any("applicable_when[0]" in x for x in v)


def test_violation_does_not_reject():
    """只記 warning 不拒絕，否則 schema 通過率失真。"""
    u = Uncertainty(alternative_readings=[SENTENCE_REWRITE])
    assert u.n_readings == 1
    assert u.alternative_readings[0].reading  # 內容仍在，未被清空


def test_boundary_exactly_at_limit_is_ok():
    r = AlternativeReading(reading="字" * MAX_READING_CHARS,
                           applicable_when="字" * MAX_APPLICABLE_CHARS,
                           speaker_intent="字" * MAX_INTENT_CHARS)
    assert Uncertainty(alternative_readings=[r]).format_violations == []


def test_one_char_over_limit_is_flagged():
    r = AlternativeReading(reading="字" * (MAX_READING_CHARS + 1))
    assert Uncertainty(alternative_readings=[r]).format_violations


def test_violations_report_index_for_multiple_readings():
    u = Uncertainty(alternative_readings=[GOOD, SENTENCE_REWRITE, GOOD])
    v = u.format_violations
    assert any("[1]" in x for x in v)
    assert not any("[0]" in x for x in v)
    assert not any("[2]" in x for x in v)


# ── S7：n_readings ──

def test_n_readings_counts_enumerated_readings():
    """S7 候選訊號：最便宜的偵測訊號（一次呼叫、不翻譯、不回譯）。"""
    assert Uncertainty().n_readings == 0
    assert Uncertainty(alternative_readings=[GOOD]).n_readings == 1
    assert Uncertainty(alternative_readings=[GOOD] * 5).n_readings == 5


def test_n_readings_is_not_capped():
    """不設硬上限（會製造截斷假象），改報 precision@k。"""
    u = Uncertainty(alternative_readings=[GOOD] * 30)
    assert u.n_readings == 30


@pytest.mark.parametrize("n,expected_high", [(0, False), (1, False), (2, True), (7, True)])
def test_n_readings_drives_derived_determinable(n, expected_high):
    u = Uncertainty(text_determinable=True,
                    alternative_readings=[GOOD] * n)
    assert u.is_high is expected_high
    assert u.derived_text_determinable is (n <= 1)


# ── prompt 內容 ──

def test_reflect_prompt_has_fewshot_for_three_ambiguity_types():
    from cognitive_core import assets
    body = assets.prompt("reflect").body
    assert "詞彙歧義" in body and "指代歧義" in body and "語用歧義" in body
    assert "錯誤寫法" in body, "必須示範常見錯誤（整句改寫），光講規則壓不住"
    assert str(MAX_READING_CHARS) in body, "prompt 須寫明長度上限"


def test_reflect_prompt_version_bumped():
    """v1 的整句改寫問題修過之後不得退回。

    改成 >= 2：釘死在特定版本會讓每次正當的改版都要動測試，
    久了就變成無腦改數字。這裡真正要守的是「不回到 v1」。
    """
    from cognitive_core import assets
    assert assets.prompt("reflect").meta.get("version", 0) >= 2
