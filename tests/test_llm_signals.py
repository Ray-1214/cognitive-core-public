"""S5–S8 的測試（fake client，不呼叫 API）。

§5 地雷 5：新指標必須有單元測試才可用來下結論。
S1–S4 在 `test_signals.py`。

這裡的重點不是「模型判得準不準」（那要靠 AUC），而是：
  - 統一介面 `signal(text) -> float in [0,1]` 在 S5–S8 上仍然成立
  - **解析失敗、API 錯誤時不得靜默回傳中間值**，必須回 0 並留痕
    （回 0.5 會讓失敗的題目看起來像「中等歧義」，直接污染 AUC）
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.router.signals import (  # noqa: E402
    LLMDirect,
    NReadings,
    RoundTripFidelity,
    SemanticEntropySignal,
    compute_all,
    llm_signals,
)


class FakeClient:
    """text() 依 role 回傳預設字串；embed() 給可控向量。"""

    def __init__(self, by_role: dict[str, str] | None = None, *,
                 vectors: list[list[float]] | None = None, raises: bool = False):
        self.by_role = by_role or {}
        self.vectors = vectors
        self.raises = raises
        self.calls: list[dict] = []

    def text(self, role, messages, **kw):
        self.calls.append({"role": role, **kw})
        if self.raises:
            raise RuntimeError("boom")
        return self.by_role.get(role, "")

    def texts(self, role, messages, **kw):
        self.calls.append({"role": role, **kw})
        if self.raises:
            raise RuntimeError("boom")
        return [self.by_role.get(role, "x")] * kw.get("n", 1)

    def embed(self, texts, role="embed"):
        self.calls.append({"role": role})
        if self.raises:
            raise RuntimeError("boom")
        if self.vectors is not None:
            return self.vectors[:len(texts)]
        return [[1.0, 0.0] for _ in texts]


def all_four(client):
    return llm_signals(client)


# ── 共同契約 ──

@pytest.mark.parametrize("idx", range(4))
def test_score_in_unit_interval(idx):
    c = FakeClient({"router": "0.7", "translate": "It rained.",
                    "backtrans": "下雨了。", "reflect": "{}"})
    v = all_four(c)[idx]("他昨天走了")
    assert 0.0 <= v <= 1.0


@pytest.mark.parametrize("idx", range(4))
def test_empty_string_returns_zero_without_calling_api(idx):
    c = FakeClient()
    assert all_four(c)[idx]("") == 0.0
    assert c.calls == [], "空字串不該浪費 API 呼叫"


@pytest.mark.parametrize("idx", range(4))
def test_api_error_returns_zero_and_leaves_trace(idx):
    """⚠️ 失敗不可回 0.5——那會讓失敗題看起來像「中等歧義」而污染 AUC。"""
    c = FakeClient({"router": "0.7"}, raises=True)
    r = all_four(c)[idx].compute("他昨天走了")
    assert r.score == 0.0
    assert r.detail.get("error") or r.detail.get("ok") is False


@pytest.mark.parametrize("idx", range(4))
def test_names_are_unique_and_prefixed(idx):
    names = [s.name for s in all_four(FakeClient())]
    assert len(set(names)) == 4
    assert names[idx].startswith(f"S{idx + 5}_")


# ── S5 LLM 直接判定 ──

@pytest.mark.parametrize("raw,expect", [
    ("0.7", 0.7), ("0.0", 0.0), ("1.0", 1.0), ("0", 0.0), ("1", 1.0),
    (".85", 0.85), ("分數：0.4", 0.4), ("0.55\n", 0.55),
])
def test_s5_parses_number(raw, expect):
    assert LLMDirect(FakeClient({"router": raw}))("句子") == pytest.approx(expect)


def test_s5_unparseable_returns_zero_and_flags():
    r = LLMDirect(FakeClient({"router": "我覺得有點歧義"})).compute("句子")
    assert r.score == 0.0 and r.detail["parsed"] is False
    assert r.detail["raw"] == "我覺得有點歧義"


def test_s5_out_of_range_is_clamped():
    assert LLMDirect(FakeClient({"router": "1.9"}))("句子") <= 1.0


def test_s5_uses_router_role():
    c = FakeClient({"router": "0.5"})
    LLMDirect(c)("句子")
    assert c.calls[0]["role"] == "router"


# ── S6 往返保真度 ──

def test_s6_identical_roundtrip_scores_zero():
    """回譯與原句完全同向 → cos=1 → 不保真程度 0。"""
    c = FakeClient({"translate": "en", "backtrans": "他昨天走了"},
                   vectors=[[1.0, 0.0], [1.0, 0.0]])
    r = RoundTripFidelity(c).compute("他昨天走了")
    assert r.score == pytest.approx(0.0)
    assert r.detail["cosine"] == pytest.approx(1.0)


def test_s6_orthogonal_roundtrip_scores_one():
    c = FakeClient({"translate": "en", "backtrans": "完全不同"},
                   vectors=[[1.0, 0.0], [0.0, 1.0]])
    assert RoundTripFidelity(c)("他昨天走了") == pytest.approx(1.0)


def test_s6_direction_matches_other_signals():
    """高分 = 比較可能出錯。相似度低的那個必須拿到比較高的分。"""
    same = RoundTripFidelity(FakeClient(
        {"translate": "e", "backtrans": "b"},
        vectors=[[1.0, 0.0], [1.0, 0.0]]))("句")
    diff = RoundTripFidelity(FakeClient(
        {"translate": "e", "backtrans": "b"},
        vectors=[[1.0, 0.0], [0.0, 1.0]]))("句")
    assert diff > same


def test_s6_keeps_intermediate_text_for_audit():
    c = FakeClient({"translate": "He left yesterday.", "backtrans": "他昨天離開了。"})
    d = RoundTripFidelity(c).compute("他昨天走了")
    assert d.detail["en"] == "He left yesterday."
    assert d.detail["back"] == "他昨天離開了。"


def test_s6_uses_three_distinct_roles():
    c = FakeClient({"translate": "e", "backtrans": "b"})
    RoundTripFidelity(c).compute("句")
    assert [x["role"] for x in c.calls] == ["translate", "backtrans", "embed"]


# ── S7 n_readings ──

def _reflect(n: int) -> str:
    return json.dumps({"uncertainty": {"alternative_readings": [
        {"reading": f"讀法{i}"} for i in range(n)]}}, ensure_ascii=False)


@pytest.mark.parametrize("n,expect", [(0, 0.0), (1, 0.0), (2, 0.25),
                                      (3, 0.5), (5, 1.0), (9, 1.0)])
def test_s7_normalization(n, expect):
    """0 或 1 個讀法 = 沒有歧義 → 0；之後遞增且有上界。"""
    assert NReadings(FakeClient({"reflect": _reflect(n)}))("句") == pytest.approx(expect)


def test_s7_is_monotone_nondecreasing():
    s = [NReadings(FakeClient({"reflect": _reflect(n)}))("句") for n in range(8)]
    assert all(b >= a for a, b in zip(s, s[1:]))


def test_s7_malformed_json_returns_zero():
    r = NReadings(FakeClient({"reflect": "不是 JSON"})).compute("句")
    assert r.score == 0.0 and r.detail["n_readings"] == 0


def test_s7_missing_uncertainty_key_returns_zero():
    r = NReadings(FakeClient({"reflect": '{"agent": "UNKNOWN"}'})).compute("句")
    assert r.score == 0.0


def test_s7_records_the_readings():
    r = NReadings(FakeClient({"reflect": _reflect(3)})).compute("句")
    assert r.detail["readings"] == ["讀法0", "讀法1", "讀法2"]


def test_s7_survives_readings_not_being_a_list():
    r = NReadings(FakeClient(
        {"reflect": '{"uncertainty": {"alternative_readings": "兩種"}}'})).compute("句")
    assert r.score == 0.0


# ── S8 語意熵 ──

def test_s8_all_identical_samples_score_zero():
    c = FakeClient({"translate": "same"})
    r = SemanticEntropySignal(c, n=4, threshold=0.5).compute("句")
    assert r.score == 0.0 and r.detail["n_clusters"] == 1


def test_s8_records_threshold_and_method():
    c = FakeClient({"translate": "same"})
    d = SemanticEntropySignal(c, n=4, threshold=0.83).compute("句").detail
    assert d["threshold"] == 0.83 and d["method"] == "embed"


def test_s8_samples_in_one_request():
    """⚠️ 與 test_semantic_entropy 的同名檢查對應——訊號這一層也要釘住。"""
    c = FakeClient({"translate": "same"})
    SemanticEntropySignal(c, n=8).compute("句")
    sampling = [x for x in c.calls if x["role"] == "translate"]
    assert len(sampling) == 1 and sampling[0]["n"] == 8


# ── compute_all 的兩種模式 ──

def test_compute_all_without_client_is_rule_only():
    r = compute_all("他昨天走了")
    assert len(r) == 4 and all(k.startswith(("S1", "S2", "S3", "S4")) for k in r)


def test_compute_all_with_client_returns_eight():
    c = FakeClient({"router": "0.5", "translate": "e", "backtrans": "b",
                    "reflect": _reflect(2)})
    r = compute_all("他昨天走了", client=c, n=2)
    assert len(r) == 8
    assert [k[:2] for k in sorted(r)] == [f"S{i}" for i in range(1, 9)]
