"""judge 不得與受測模型相同（§7.5 避免球員兼裁判）。

換 profile 時很容易不小心讓兩者變成同一個模型，而那會讓 self-preference bias
無法排除，且事後從結果看不出來。故在啟動時檢查並拒絕執行。
"""

from __future__ import annotations

import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.config import Config  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def cfg(monkeypatch_session=None):
    return Config()


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ITHU_API_BASE", "https://example.invalid")
    monkeypatch.setenv("ITHU_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")


def test_default_judge_differs_from_translate(cfg):
    t = cfg.resolve("translate")
    j = cfg.resolve("judge")
    assert (t.provider, t.model) != (j.provider, j.model)
    cfg.assert_judge_is_cross()


def test_judge_cross_profile_is_actually_cross(cfg):
    cfg.assert_judge_is_cross("judge_cross")


def test_judge_gemini_profile_is_actually_cross(cfg):
    """評審間一致性檢驗用的 profile 也必須是 cross。"""
    cfg.assert_judge_is_cross("judge_gemini")


@pytest.mark.parametrize("profile", ["all_mistral", "all_gptoss", "all_scout"])
def test_all_same_profiles_are_rejected(cfg, profile):
    """_all profile 會讓 judge 與受測模型相同，必須被擋下。

    這些 profile 是給跨模型對比用的，不該拿來跑需要 judge 的評測。
    """
    with pytest.raises(RuntimeError, match="球員兼裁判"):
        cfg.assert_judge_is_cross(profile)


def test_error_message_names_both_roles(cfg):
    with pytest.raises(RuntimeError) as e:
        cfg.assert_judge_is_cross("all_mistral")
    msg = str(e.value)
    assert "translate" in msg and "judge" in msg
    assert "all_mistral" in msg


def test_judge_and_translate_have_different_training_sources():
    """judge_cross 的實質是**不同訓練來源**，不只是不同字串。

    翻譯 mistral-small-4（Mistral）vs judge gpt-oss-120b（OpenAI 血統）。
    兩者部署於同一機構端點，但模型權重與訓練資料獨立。
    """
    raw = yaml.safe_load((ROOT / "config" / "providers.yaml").read_text(encoding="utf-8"))
    roles = raw["roles"]
    fam = {"mistral-small-4": "mistral", "gpt-oss-120b": "openai",
           "llama4scout": "meta", "nemotron-3-ultra": "nvidia",
           "ornith-35b": "other", "gemini-flash-latest": "google"}
    t = fam.get(roles["translate"]["model"])
    j = fam.get(roles["judge"]["model"])
    assert t and j, "模型未登記訓練來源，無法確認 judge_cross 成立"
    assert t != j, f"translate 與 judge 同為 {t} 血統，judge_cross 不成立"


def test_judge_supports_strict_structured_output():
    """judge 需要穩定的結構化輸出——降級到 tier3 靠寬鬆解析不可靠。"""
    raw = yaml.safe_load((ROOT / "config" / "providers.yaml").read_text(encoding="utf-8"))
    m = raw["roles"]["judge"]["model"]
    prov = raw["roles"]["judge"]["provider"]
    caps = raw["providers"][prov]["models"][m]["capabilities"]
    assert caps.get("json_schema") is True, \
        f"judge 模型 {m} 不支援 tier1 嚴格 json_schema"
