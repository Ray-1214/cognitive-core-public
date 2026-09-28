"""從歷史 run 記錄推估成本與取樣次數（實作規格書 §4-5、§4-6）。

兩個用途：
  成本預估    批次開跑前告訴使用者會燒多少，避免按下去才發現
  取樣自適應  same_language 的 n 依該模型的觀測變異決定，不用固定值

⚠️ 沒有歷史時一律回傳保守估計並標明來源為 fallback，
不得印得像實測值。
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from .similarity import suggest_n_samples, variance_of

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / "runs"

# 無歷史時的保守估計。刻意偏高——低估比高估糟。
FALLBACK_TOKENS_PER_CALL = 1500
FALLBACK_CALLS_PER_ITEM = 6


@dataclass(frozen=True)
class CostEstimate:
    n_items: int
    n_profiles: int
    calls_per_item: float
    tokens_per_call: float
    source: str                     # "history" | "fallback" | "mixed"
    n_history_runs: int = 0

    @property
    def total_calls(self) -> int:
        return round(self.n_items * self.n_profiles * self.calls_per_item)

    @property
    def total_tokens(self) -> int:
        return round(self.total_calls * self.tokens_per_call)

    def describe(self) -> str:
        tag = {"history": f"依 {self.n_history_runs} 筆歷史 run 推估",
               "fallback": "⚠️ 無歷史紀錄，使用保守預設值",
               "mixed": f"部分依 {self.n_history_runs} 筆歷史推估"}[self.source]
        return (f"預估：{self.n_items} 句 × {self.n_profiles} 個 profile"
                f" ≈ {self.total_calls:,} 次呼叫，約 {self.total_tokens:,} tokens\n"
                f"（{tag}；**這是估計值不是實測**，"
                f"每句 {self.calls_per_item:.1f} 次呼叫 × 每次 {self.tokens_per_call:,.0f} tokens）")


def _iter_calls(limit_runs: int = 20):
    """讀最近的 run 記錄。舊格式缺欄位就跳過，不讓解析失敗中斷估算。"""
    if not RUNS_DIR.exists():
        return
    files = sorted(RUNS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime,
                   reverse=True)[:limit_runs]
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield f.name, o


def estimate_cost(n_items: int, n_profiles: int = 1, *,
                  limit_runs: int = 20) -> CostEstimate:
    tokens: list[int] = []
    runs: set[str] = set()
    for fname, o in _iter_calls(limit_runs):
        if o.get("_type") != "call" or o.get("cached"):
            continue
        u = o.get("usage") or {}
        t = u.get("total_tokens")
        if t:
            tokens.append(int(t))
            runs.add(fname)

    if not tokens:
        return CostEstimate(n_items, n_profiles, FALLBACK_CALLS_PER_ITEM,
                            FALLBACK_TOKENS_PER_CALL, "fallback")

    tokens_per_call = sum(tokens) / len(tokens)
    # 每句呼叫數：優先用 batch run 的實際比值，否則用保守預設
    per_item = _calls_per_item(limit_runs) or FALLBACK_CALLS_PER_ITEM
    source = "history" if per_item != FALLBACK_CALLS_PER_ITEM else "mixed"
    return CostEstimate(n_items, n_profiles, per_item, tokens_per_call,
                        source, len(runs))


def _calls_per_item(limit_runs: int) -> float | None:
    """由 batch run 的 header 中的 n_items 與該 run 的呼叫數推算。"""
    per_run: dict[str, dict] = {}
    for fname, o in _iter_calls(limit_runs):
        d = per_run.setdefault(fname, {"calls": 0, "items": None, "profiles": 1})
        if o.get("_type") == "call":
            d["calls"] += 1
        elif o.get("_type") == "run_header":
            meta = o.get("meta") or {}
            if meta.get("n_items"):
                d["items"] = int(meta["n_items"])
                d["profiles"] = int(meta.get("n_profiles", 1))
    ratios = [d["calls"] / (d["items"] * d["profiles"])
              for d in per_run.values()
              if d["items"] and d["calls"] and d["items"] * d["profiles"] > 0]
    return sum(ratios) / len(ratios) if ratios else None


def observed_consistency(model: str | None = None, *,
                         limit_runs: int = 20) -> list[float]:
    """歷史上的一致性分數，用於估計該模型的輸出變異。"""
    out: list[float] = []
    for _, o in _iter_calls(limit_runs):
        if o.get("_type") == "event" and o.get("kind") == "verify":
            c = o.get("consistency")
            if c is not None:
                out.append(float(c))
    return out


def adaptive_n(config_n: int, *, model: str | None = None,
               limit_runs: int = 20) -> tuple[int, str]:
    """依觀測變異決定取樣次數，config 值當上限。

    固定 n=3 對所有模型是錯的——實測 mistral 11/15 句三次全同（近乎確定性，
    跑三次等於跑一次），diffusiongemma 0/15 全同（n=3 完全不足），差 15 倍。
    """
    obs = observed_consistency(model, limit_runs=limit_runs)
    if len(obs) < 2:
        return config_n, f"無足夠歷史（{len(obs)} 筆），沿用 config 值 {config_n}"
    n = suggest_n_samples(obs, floor=2, cap=config_n)
    return n, (f"依 {len(obs)} 筆歷史一致性（變異數 {variance_of(obs):.5f}）"
               f"建議 n={n}，config 上限 {config_n}")
