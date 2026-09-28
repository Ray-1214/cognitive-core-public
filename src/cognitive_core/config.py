"""設定載入與角色解析（技術設計文件 §5.1）。"""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field
from typing import Any

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


@dataclass(frozen=True)
class ModelSpec:
    """一個可呼叫的模型。`litellm_model` 是傳給 litellm.completion 的字串。"""

    provider: str
    model: str
    litellm_model: str
    api_base: str | None
    api_key: str | None
    capabilities: dict[str, Any] = field(default_factory=dict)
    reasoning: bool = False
    max_tokens_floor: int | None = None
    rpm: int | None = None
    kind: str = "chat"

    def supports(self, cap: str) -> bool:
        return bool(self.capabilities.get(cap, False))


class Config:
    def __init__(self, path: pathlib.Path | None = None):
        p = path or (CONFIG_DIR / "providers.yaml")
        self.raw: dict = yaml.safe_load(p.read_text(encoding="utf-8"))
        self.path = p

    # ── 基本存取 ──
    @property
    def defaults(self) -> dict:
        return self.raw.get("defaults", {})

    @property
    def cache(self) -> dict:
        return self.raw.get("cache", {})

    @property
    def max_concurrency(self) -> int:
        return int(self.defaults.get("max_concurrency", 3))

    def profile_roles(self, profile: str | None) -> dict[str, dict]:
        """套用 experiment_profile 後的角色綁定。`_all` 覆蓋全部角色。"""
        roles = {k: dict(v) for k, v in self.raw.get("roles", {}).items()}
        if not profile:
            return roles
        prof = self.raw.get("experiment_profiles", {}).get(profile)
        if prof is None:
            raise KeyError(f"未知的 experiment_profile：{profile}")
        if "_all" in prof:
            base = prof["_all"]
            # embedding / rerank 是特定模型，不可被 _all 覆蓋
            roles = {k: (dict(base) if k not in ("embed", "rerank") else v)
                     for k, v in roles.items()}
        for k, v in prof.items():
            if k == "_all":
                continue
            roles[k] = {**roles.get(k, {}), **v}
        return roles

    # ── 解析 ──
    def resolve(self, role: str, profile: str | None = None) -> ModelSpec:
        roles = self.profile_roles(profile)
        if role not in roles:
            raise KeyError(f"未知角色：{role}（可用：{', '.join(sorted(roles))}）")
        binding = roles[role]
        return self.spec(binding["provider"], binding["model"])

    def spec(self, provider: str, model: str) -> ModelSpec:
        pconf = self.raw["providers"].get(provider)
        if pconf is None:
            raise KeyError(f"未知 provider：{provider}")
        mconf = pconf.get("models", {}).get(model)
        if mconf is None:
            raise KeyError(f"provider {provider} 沒有模型 {model}")

        api_base = None
        if "api_base_env" in pconf:
            base = os.environ.get(pconf["api_base_env"])
            if not base:
                raise RuntimeError(
                    f"環境變數 {pconf['api_base_env']} 未設定（provider={provider}）")
            base = base.rstrip("/")
            suffix = pconf.get("api_base_suffix", "")
            # .env 可能已含 suffix（實測 ITHU_API_BASE 就寫成 .../v1），
            # 無條件串接會得到 /v1/v1 並回 404。
            api_base = base if (suffix and base.endswith(suffix)) else base + suffix

        api_key = os.environ.get(pconf["api_key_env"]) if "api_key_env" in pconf else None
        if "api_key_env" in pconf and not api_key:
            raise RuntimeError(
                f"環境變數 {pconf['api_key_env']} 未設定（provider={provider}）。"
                "金鑰一律由 .env 提供，不得寫在指令列或程式碼中。")

        return ModelSpec(
            provider=provider,
            model=model,
            litellm_model=f"{pconf['litellm_prefix']}/{model}",
            api_base=api_base,
            api_key=api_key,
            capabilities=mconf.get("capabilities", {}),
            reasoning=bool(mconf.get("reasoning", False)),
            max_tokens_floor=mconf.get("max_tokens_floor"),
            rpm=(pconf.get("rate_limit") or {}).get("rpm"),
            kind=mconf.get("kind", "chat"),
        )

    def assert_judge_is_cross(self, profile: str | None = None,
                              subject_role: str = "translate") -> None:
        """⚠️ **名稱層的檢查，不足以保證 judge_cross。**

        只比較 provider/model **字串**。它擋得住「換 profile 時不小心把兩者
        設成同一個 id」，擋不住「不同 id 由同一個後端提供服務」——
        而後者正是本專案實際發生的事：`ithu/mistral-small-4` 與
        `ithu/gpt-oss-120b` 字串不同、本檢查一路通過，但 tokenizer 截斷點
        逐字相同，極可能是同一個模型在評判自己的輸出。

        真正的檢查在 `eval/cross_check.assert_judge_is_cross()`——它比較
        **行為**（截斷位置）而非名稱。本方法保留為便宜的前置檢查。

        發現經過見 `data/results/endpoint_identity_check.md`。
        """
        subj = self.resolve(subject_role, profile)
        judge = self.resolve("judge", profile)
        if (subj.provider, subj.model) == (judge.provider, judge.model):
            raise RuntimeError(
                f"球員兼裁判：{subject_role} 與 judge 都是 "
                f"{judge.provider}/{judge.model}"
                + (f"（profile={profile}）" if profile else "")
                + "。judge 必須是不同模型，否則 self-preference bias 無法排除。")

    def all_chat_models(self) -> list[tuple[str, str]]:
        out = []
        for prov, pconf in self.raw["providers"].items():
            for m, mconf in pconf.get("models", {}).items():
                if mconf.get("kind", "chat") == "chat":
                    out.append((prov, m))
        return out


_default: Config | None = None


def get_config() -> Config:
    global _default
    if _default is None:
        _default = Config()
    return _default
