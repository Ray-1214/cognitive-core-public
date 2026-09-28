"""Run 記錄（技術設計文件 §5.4）。

每筆呼叫留下足以還原當時狀態的資訊：model、prompt hash、參數、
git commit hash 與 dirty 旗標、token、耗時、快取是否命中。

寫成 JSONL，一個 run 一個檔，append-only。
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import threading
import uuid
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNS_DIR = pathlib.Path(os.environ.get("RUNS_DIR", ROOT / "runs"))


def _git(*args: str) -> str:
    try:
        # Windows 預設 cp950 會在中文檔名上炸掉，必須明指 utf-8
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=15).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


_GIT_STATE: dict[str, Any] | None = None


def git_state() -> dict[str, Any]:
    """整個行程取一次即可，commit 不會在執行中改變。"""
    global _GIT_STATE
    if _GIT_STATE is None:
        _GIT_STATE = {
            "commit": _git("rev-parse", "HEAD") or "(uncommitted)",
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(_git("status", "--porcelain")),
        }
    return _GIT_STATE


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def prompt_hash(messages: list[dict]) -> str:
    """對訊息內容取雜湊。prompt 改一個字，數據就該視為失效。"""
    canon = json.dumps(
        [{"role": m.get("role"), "content": m.get("content")} for m in messages],
        ensure_ascii=False, sort_keys=True)
    return sha16(canon)


class RunLog:
    """一次實驗執行的記錄。thread-safe append。"""

    def __init__(self, name: str, meta: dict | None = None):
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_id = f"{stamp}-{name}-{uuid.uuid4().hex[:6]}"
        self.path = RUNS_DIR / f"{self.run_id}.jsonl"
        self._lock = threading.Lock()
        self._n = 0
        header = {
            "_type": "run_header",
            "run_id": self.run_id,
            "name": name,
            "started_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "git": git_state(),
            "meta": meta or {},
        }
        self._write(header)

    def _write(self, obj: dict) -> None:
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def record_call(self, *, role: str, spec, messages: list[dict], params: dict,
                    usage: dict | None, elapsed: float, cached: bool,
                    error: str | None = None, extra: dict | None = None) -> None:
        self._n += 1
        self._write({
            "_type": "call",
            "seq": self._n,
            "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "role": role,
            "provider": spec.provider,
            "model": spec.model,
            "prompt_hash": prompt_hash(messages),
            "params": params,
            "usage": usage,
            "elapsed_s": round(elapsed, 3),
            "cached": cached,
            "error": error,
            **({"extra": extra} if extra else {}),
        })

    def record_event(self, kind: str, payload: dict) -> None:
        self._write({"_type": "event", "kind": kind,
                     "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                     **payload})

    def summary(self) -> dict:
        calls, cached, err, tok, secs = 0, 0, 0, 0, 0.0
        for line in self.path.read_text(encoding="utf-8").splitlines():
            o = json.loads(line)
            if o.get("_type") != "call":
                continue
            calls += 1
            cached += bool(o.get("cached"))
            err += bool(o.get("error"))
            secs += o.get("elapsed_s") or 0
            u = o.get("usage") or {}
            tok += (u.get("total_tokens") or 0)
        return {"run_id": self.run_id, "calls": calls, "cache_hits": cached,
                "errors": err, "total_tokens": tok, "wall_s": round(secs, 1),
                "path": str(self.path)}
