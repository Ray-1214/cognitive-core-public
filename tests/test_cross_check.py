"""judge_cross 的行為檢查（2026-08-23 裁示 A-3）。

## ⚠️ 本檔有一支測試**目前是紅色的**，而且那是刻意的

`test_current_deployment_fails_behavioural_cross_check` 會失敗，因為校內端點的
`ithu/mistral-small-4` 與 `ithu/gpt-oss-120b` 在三個不同的 `max_tokens` 下
截斷點逐字相同——極可能由同一個後端提供服務。

**原始的字串檢查通過，行為檢查失敗。後者才是對的。**
此測試的紅色本身就是研究發現的一部分：一個用來防止球員兼裁判的機制，
通過了所有測試，卻在部署層面被架空，而且無法從 API 察覺。

不要為了讓測試綠掉而放寬它。要讓它變綠，唯一正當的作法是換一個
確實不同來源的 judge（例如 `judge_gemini`）。

跟 `test_gate.py` 把閘門測試改成「守住開閘的理由」是同一個做法。
"""

from __future__ import annotations

import inspect
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.eval import cross_check as cc  # noqa: E402
from cognitive_core.eval.cross_check import (  # noqa: E402
    MAX_TOKENS_LADDER,
    CrossCheckResult,
    SameBackend,
    assert_judge_is_cross,
    check_cross,
)


class FakeSpec:
    def __init__(self, provider, model):
        self.provider, self.model = provider, model


class FakeCfg:
    def __init__(self, mapping):
        self.mapping = mapping

    def resolve(self, role, profile=None):
        return FakeSpec(*self.mapping[role])


class FakeClient:
    """`cuts` 是 role → 各 max_tokens 下的截斷輸出。"""

    def __init__(self, mapping, cuts):
        self.cfg = FakeCfg(mapping)
        self.cuts = cuts
        self.calls = 0

    def call(self, role, messages, *, temperature=0.0, max_tokens=16, **kw):
        self.calls += 1
        idx = MAX_TOKENS_LADDER.index(max_tokens)
        txt = self.cuts[role][idx]

        class M:
            content = txt

        class C:
            message = M()

        class R:
            choices = [C()]
        return R()


SAME = ["人工智慧與", "人工智慧與機器學", "人工智慧與機器學習的差異在"]
DIFF = ["人工智慧", "人工智慧與機器", "人工智慧與機器學習的差"]


def client(a=("ithu", "mistral-small-4"), b=("ithu", "gpt-oss-120b"),
           cuts_a=SAME, cuts_b=SAME) -> FakeClient:
    return FakeClient({"translate": a, "judge": b},
                      {"translate": cuts_a, "judge": cuts_b})


# ── 名稱層 ──

def test_same_name_is_rejected():
    with pytest.raises(SameBackend, match="球員兼裁判"):
        assert_judge_is_cross(client(a=("ithu", "m"), b=("ithu", "m")))


def test_different_names_alone_are_not_enough():
    """⭐ 本專案的實際情形：名稱不同、行為相同。"""
    with pytest.raises(SameBackend, match="行為相同"):
        assert_judge_is_cross(client())


# ── 行為層 ──

def test_different_truncation_passes():
    r = assert_judge_is_cross(client(cuts_b=DIFF))
    assert r.is_cross is True


def test_one_differing_cut_is_enough():
    """只要有一個切點不同就不是同一個 tokenizer。"""
    cuts = list(SAME)
    cuts[1] = "人工智慧與機器"
    assert assert_judge_is_cross(client(cuts_b=cuts)).is_cross is True


def test_check_cross_measures_without_raising():
    r = check_cross(client())
    assert isinstance(r, CrossCheckResult)
    assert r.names_differ is True
    assert r.cuts_identical is True
    assert r.is_cross is False


def test_ladder_has_at_least_three_rungs():
    """單一切點可能碰巧相同；三個才有說服力。"""
    assert len(MAX_TOKENS_LADDER) >= 3


def test_probe_is_queried_once_per_rung_per_role():
    c = client()
    check_cross(c)
    assert c.calls == 2 * len(MAX_TOKENS_LADDER)


def test_explain_names_the_evidence():
    txt = check_cross(client()).explain()
    assert "逐字相同" in txt
    for mt in MAX_TOKENS_LADDER:
        assert f"max_tokens={mt}" in txt


# ── 不得退回字串比較 ⭐ ──

def test_behavioural_check_actually_calls_the_model():
    """釘住「不得改回只比字串」——那樣就不會有任何 API 呼叫。"""
    c = client(cuts_b=DIFF)
    assert_judge_is_cross(c)
    assert c.calls > 0, "行為檢查沒有實際呼叫模型，退化成字串比較了"


def test_source_still_uses_truncation():
    src = inspect.getsource(cc)
    assert "max_tokens" in src and "truncation_signature" in src


def test_config_method_documents_its_insufficiency():
    """`Config.assert_judge_is_cross` 保留為便宜的前置檢查，

    但它的 docstring 必須說清楚擋不住什麼，否則下一個人會以為它夠用。
    """
    from cognitive_core.config import Config
    doc = Config.assert_judge_is_cross.__doc__ or ""
    assert "不足" in doc and "行為" in doc


# ── 專案現況：這支目前是紅的 ⭐ ──

def test_current_deployment_fails_behavioural_cross_check():
    """🔴 **本測試目前失敗，那是研究發現本身，不是要修掉的 bug。**

    校內端點的兩個 model id 在三個 max_tokens 下截斷點逐字相同。
    字串檢查通過、行為檢查失敗——後者才是對的。

    不要放寬判準讓它變綠。唯一正當的修法是換一個確實不同來源的 judge。
    證據見 `data/results/endpoint_identity_check.md`。
    """
    import json
    f = (pathlib.Path(__file__).resolve().parents[1]
         / "data" / "results" / "judge_validation_r2.json")
    if not f.exists():
        pytest.skip("尚無驗證結果")
    d = json.loads(f.read_text(encoding="utf-8")).get("judge_cross_behavioural")
    if not d:
        pytest.skip("驗證結果尚未記錄行為檢查")
    assert d["is_cross"], (
        "judge_cross 的行為層檢查未通過："
        f"名稱不同={d['names_differ']}、截斷點逐字相同={d['cuts_identical']}。\n"
        "這是已知且刻意保留的失敗——見本檔 docstring。")
