"""測試共用的假 client —— **測試不得呼叫真實 API**（P1 測試提示詞第 3 條）。

FakeClient 實作 Client 的公開介面，行為由建構參數控制，
所以狀態機的每條路徑都能被決定性地驅動。
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))


@dataclass
class FakeSpec:
    provider: str = "fake"
    model: str = "fake-model"
    litellm_model: str = "fake/fake-model"
    api_base: str | None = None
    api_key: str | None = None
    capabilities: dict = field(default_factory=lambda: {"json_schema": True,
                                                        "json_object": True})
    reasoning: bool = False
    max_tokens_floor: int | None = None
    rpm: int | None = None
    kind: str = "chat"

    def supports(self, cap: str) -> bool:
        return bool(self.capabilities.get(cap, False))


class FakeCfg:
    max_concurrency = 2
    defaults: dict = {"timeout": 10, "max_retries": 0}
    cache: dict = {"enabled": False}

    def resolve(self, role: str, profile: str | None = None) -> FakeSpec:
        return FakeSpec()


DEFAULT_ANCHOR = {
    "agent": "UNKNOWN",
    "time": "昨天",
    "register": "CASUAL",
    "social_relation": "UNKNOWN",
    "cultural_items": [],
    "uncertainty": {
        "text_determinable": False,
        "ambiguity_score": 0.7,
        "unknown_fields": ["agent", "social_relation"],
        "alternative_readings": [
            {"reading": "離開", "applicable_when": "談論行程",
             "speaker_intent": "陳述"},
            {"reading": "過世", "applicable_when": "談論喪事",
             "speaker_intent": "委婉告知"},
        ],
        "clarification_questions": ["談論的是行程還是喪事？"],
    },
}


class FakeClient:
    """可控行為的假 client。

    embed_map 決定回傳的向量，用來精準控制一致性分數：
    預設所有回譯向量彼此正交（一致性低 → 觸發反思），
    設 consistent=True 則全部相同（一致性 1.0 → 直接通過）。
    """

    def __init__(self, *, consistent: bool = False, anchor: dict | None = None,
                 run=None, profile: str | None = None,
                 fail_on: set[str] | None = None):
        self.cfg = FakeCfg()
        self.run = run
        self.profile = profile
        self.consistent = consistent
        self.anchor = anchor or DEFAULT_ANCHOR
        self.fail_on = fail_on or set()
        self.calls: list[tuple[str, str]] = []      # (role, kind)

    # ── Client 介面 ──
    def texts(self, role, messages, *, n: int = 1, **kw) -> list[str]:
        self.calls.append((role, "texts"))
        if role in self.fail_on:
            raise RuntimeError(f"fake failure on {role}")
        return [f"[{role}#{i}]" for i in range(max(1, n))]

    def text(self, role, messages, **kw) -> str:
        self.calls.append((role, "text"))
        if role in self.fail_on:
            raise RuntimeError(f"fake failure on {role}")
        if role == "verify":
            return "施事者不同 | agent\n時態不同 | time"
        return f"[{role}]"

    def structured(self, role, messages, schema, validator=None, **kw):
        self.calls.append((role, "structured"))
        if role in self.fail_on:
            raise RuntimeError(f"fake failure on {role}")
        obj = dict(self.anchor)
        if validator is not None:
            obj = validator(obj)
        return obj, 1

    def embed(self, texts, role: str = "embed") -> list[list[float]]:
        self.calls.append((role, "embed"))
        if self.consistent:
            return [[1.0, 0.0, 0.0] for _ in texts]
        # 原文一個方向，回譯彼此正交 → 一致性低
        out = [[1.0, 0.0, 0.0]]
        basis = [[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.7, 0.7, 0.0]]
        for i in range(len(texts) - 1):
            out.append(basis[i % len(basis)])
        return out

    # ── 測試輔助 ──
    def roles_called(self) -> list[str]:
        return [r for r, _ in self.calls]


@pytest.fixture
def fake_client():
    return FakeClient()


@pytest.fixture
def consistent_client():
    return FakeClient(consistent=True)
