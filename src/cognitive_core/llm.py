"""以 litellm 為底的呼叫入口（技術設計文件 §5.1、§5.2、§5.4）。

取代先前自寫的四家 adapter、_throttle.py、呼叫快取與成本追蹤——
校內端點本身就是 LiteLLM proxy，client 端用同一套即可。

保留自寫的部分只有三項，litellm 不提供：
  1. 結構化輸出的降級階梯（§5.2）——需依 per-model capabilities 決定走哪一級，
     且最終一律以 Pydantic 驗證。litellm 只轉發 response_format，不做降級。
  2. 推理模型的 reasoning_content 擷取與 max_tokens 下限。
  3. Run 記錄的 commit hash / prompt hash（runlog.py）。
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Any

import litellm
from litellm import completion
from litellm.caching.caching import Cache

from .config import Config, ModelSpec, get_config
from .runlog import RunLog

litellm.suppress_debug_info = True
litellm.drop_params = True          # 模型不支援的參數自動剔除，取代自寫的 capability 分支


class LLMError(RuntimeError):
    pass


def _init_cache(cfg: Config) -> None:
    c = cfg.cache
    if not c.get("enabled", True):
        return
    path = c.get("path", ".cache/litellm")
    os.makedirs(path, exist_ok=True)
    litellm.cache = Cache(type="disk", disk_cache_dir=path)
    litellm.enable_cache()


class Semaphore:
    """併發上限。RateLimiter 控速率不控併發，而佔住後端推論槽的是併發。"""

    def __init__(self, n: int):
        self._sem = threading.Semaphore(n)

    def __enter__(self):
        self._sem.acquire()
        return self

    def __exit__(self, *exc):
        self._sem.release()
        return False


class ProviderPacer:
    """依 providers.yaml 的 rate_limit.rpm 控速。

    litellm 會重試但不會控速；Gemini 免費層的 RPM 很低，粗跑時 10 筆有 6 筆
    因 RateLimitError 失敗。速率限制屬於 provider 的屬性，寫在 config 裡就該生效。
    """

    def __init__(self, cfg: Config):
        self._lock = threading.Lock()
        self._next: dict[str, float] = {}
        self._interval: dict[str, float] = {}
        for name, pconf in (cfg.raw.get("providers") or {}).items():
            rpm = (pconf.get("rate_limit") or {}).get("rpm")
            if rpm:
                self._interval[name] = 60.0 / float(rpm)

    def wait(self, provider: str) -> None:
        iv = self._interval.get(provider)
        if not iv:
            return
        with self._lock:
            now = time.monotonic()
            due = max(now, self._next.get(provider, 0.0))
            self._next[provider] = due + iv
        delay = due - time.monotonic()
        if delay > 0:
            time.sleep(delay)


class Client:
    def __init__(self, cfg: Config | None = None, run: RunLog | None = None,
                 profile: str | None = None):
        self.cfg = cfg or get_config()
        self.run = run
        self.profile = profile
        _init_cache(self.cfg)
        self._sem = Semaphore(self.cfg.max_concurrency)
        self._pacer = ProviderPacer(self.cfg)

    # ─────────────── 基本呼叫 ───────────────

    def call(self, role: str, messages: list[dict], *, temperature: float | None = 0.0,
             max_tokens: int = 800, n: int = 1, seed: int | None = None,
             response_format: dict | None = None,
             spec: ModelSpec | None = None, **kw) -> Any:
        spec = spec or self.cfg.resolve(role, self.profile)
        if spec.max_tokens_floor:
            max_tokens = max(max_tokens, spec.max_tokens_floor)

        params: dict[str, Any] = {"max_tokens": max_tokens, "n": n}
        if temperature is not None:
            params["temperature"] = temperature
        if seed is not None:
            params["seed"] = seed
        if response_format is not None:
            params["response_format"] = response_format
        params.update(kw)

        t0 = time.monotonic()
        err = None
        resp = None
        try:
            self._pacer.wait(spec.provider)
            with self._sem:
                resp = completion(
                    model=spec.litellm_model, messages=messages,
                    api_base=spec.api_base, api_key=spec.api_key,
                    timeout=self.cfg.defaults.get("timeout", 180),
                    num_retries=self.cfg.defaults.get("max_retries", 3),
                    **params)
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {str(e)[:300]}"
        elapsed = time.monotonic() - t0

        cached = bool(getattr(resp, "_hidden_params", {}).get("cache_hit")) if resp else False
        usage = None
        if resp is not None and getattr(resp, "usage", None) is not None:
            u = resp.usage
            usage = {"prompt_tokens": getattr(u, "prompt_tokens", None),
                     "completion_tokens": getattr(u, "completion_tokens", None),
                     "total_tokens": getattr(u, "total_tokens", None)}
        if self.run:
            self.run.record_call(role=role, spec=spec, messages=messages, params=params,
                                 usage=usage, elapsed=elapsed, cached=cached, error=err)
        if err:
            raise LLMError(f"{spec.provider}/{spec.model}: {err}")
        return resp

    def texts(self, role: str, messages: list[dict], **kw) -> list[str]:
        """回傳所有 choice 的文字。推理模型的 reasoning_content 一律不外流（§6.1）。"""
        resp = self.call(role, messages, **kw)
        out = []
        for ch in resp.choices:
            c = getattr(ch.message, "content", None)
            out.append((c or "").strip())
        return out

    def text(self, role: str, messages: list[dict], **kw) -> str:
        t = self.texts(role, messages, **kw)
        if not t or not t[0]:
            raise LLMError("回應為空（推理模型可能只填了 reasoning_content）")
        return t[0]

    # ─────────────── 結構化輸出的降級階梯（§5.2）───────────────

    def structured(self, role: str, messages: list[dict], schema: dict,
                   validator=None, *, max_tokens: int = 800, **kw) -> tuple[dict, int]:
        """依降級階梯取得符合 schema 的物件。回傳 (物件, 使用的 tier)。

        litellm 只負責轉發 response_format，不做降級。主力模型 mistral-small-4 的
        json_schema 嚴格模式實測失效（卡在輸出空白直到耗盡 token），故必須有階梯。
        """
        spec = self.cfg.resolve(role, self.profile)
        tiers: list[tuple[int, dict | None]] = []
        if spec.supports("json_schema"):
            tiers.append((1, {"type": "json_schema",
                              "json_schema": {"name": "out", "strict": True, "schema": schema}}))
        if spec.supports("json_object"):
            tiers.append((2, {"type": "json_object"}))
        tiers.append((3, None))

        last_err = "未嘗試"
        for tier, rf in tiers:
            # tier1 由 API 強制欄位；降級後模型不知道要產哪些欄位，
            # 必須把 schema 描述進 prompt，否則會自由發揮出一堆無關欄位。
            msgs = messages if tier == 1 else _with_schema_hint(messages, schema)
            try:
                txt = self.text(role, msgs, response_format=rf,
                                max_tokens=max_tokens, spec=spec, **kw)
            except LLMError as e:
                last_err = str(e)
                continue
            obj = parse_json_loose(txt)
            if obj is None:
                last_err = f"tier{tier} 解析失敗：{txt[:120]!r}"
                continue
            if validator is not None:
                try:
                    obj = validator(obj)
                except Exception as e:  # noqa: BLE001
                    last_err = f"tier{tier} 驗證失敗：{type(e).__name__}: {str(e)[:120]}"
                    continue
            elif not all(k in obj for k in schema.get("required", [])):
                last_err = f"tier{tier} 缺必填欄位，得到 {sorted(obj)}"
                continue
            if self.run:
                self.run.record_event("structured_ok", {"role": role, "tier": tier})
            return obj, tier

        if self.run:
            self.run.record_event("structured_fail", {"role": role, "reason": last_err})
        raise LLMError(f"結構化輸出全數失敗（{spec.model}）：{last_err}")

    # ─────────────── embedding / rerank ───────────────

    def embed(self, texts: list[str], role: str = "embed") -> list[list[float]]:
        spec = self.cfg.resolve(role, self.profile)
        self._pacer.wait(spec.provider)
        with self._sem:
            r = litellm.embedding(model=spec.litellm_model, input=texts,
                                  api_base=spec.api_base, api_key=spec.api_key)
        return [d["embedding"] for d in r.data]


def _schema_hint(schema: dict) -> str:
    """把 JSON Schema 壓成一行給模型看的欄位規格。"""
    props = schema.get("properties", {})
    req = set(schema.get("required", []))
    parts = []
    for name, spec in props.items():
        t = spec.get("type", "any")
        if "enum" in spec:
            t = "|".join(str(x) for x in spec["enum"])
        parts.append(f'"{name}": {t}' + ("" if name in req else "  (選填)"))
    body = ",\n  ".join(parts)
    extra = "不得加入其他欄位。" if schema.get("additionalProperties") is False else ""
    return (f"只輸出符合下列格式的 JSON，不要 markdown 圍欄、不要解釋：\n"
            f"{{\n  {body}\n}}\n"
            f"必填欄位：{', '.join(sorted(req)) or '（無）'}。{extra}")


def _with_schema_hint(messages: list[dict], schema: dict) -> list[dict]:
    hint = _schema_hint(schema)
    out = [dict(m) for m in messages]
    for m in out:
        if m.get("role") == "system":
            m["content"] = f"{m['content']}\n\n{hint}"
            return out
    return [{"role": "system", "content": hint}, *out]


def parse_json_loose(text: str) -> dict | None:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        v = json.loads(t)
        return v if isinstance(v, dict) else None
    except json.JSONDecodeError:
        pass
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j > i:
        try:
            v = json.loads(t[i:j + 1])
            return v if isinstance(v, dict) else None
        except json.JSONDecodeError:
            return None
    return None
