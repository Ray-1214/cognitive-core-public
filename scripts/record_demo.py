"""錄製 demo 的預錄結果，供離線模式播放（2026-08-23 裁示 §1-1）。

## 為什麼

教授要能**不用 API key** 就把 demo 跑起來看。做「在 UI 裡填 key」不行：
key 存 session state 會掉、存檔案會不小心進版控、而且每次點擊都在燒額度。

所以改成：有 key 走即時模式，沒有 key 就播這份錄好的結果。

## 錄什麼

五個展示句 × 三個 profile。**不是只錄一個 profile**——
profile 切換器是既有的 UI，只錄一個的話離線模式下切換就會開天窗，
那是把功能弄壞不是精簡。

每筆含：完整 timeline（節點與 detail）、譯文、澄清提問、成本、
以及錄製時間與 commit hash。

⚠️ 錄製也是一條**輸出通道**，所以一樣要過 `assert_no_cot()`——
模型的原始推理文字不得經由這個檔案外流（計畫書 §4.9）。

用法：
    python scripts/record_demo.py
"""

from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from cognitive_core.timeline import assert_no_cot  # noqa: E402

OUT = ROOT / "data" / "demo" / "recorded.json"


def git_hash() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", check=True)
        return (r.stdout or "").strip()[:12]
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def run_once(app, text: str, profile: str):
    """跑一次；遇到驗證失敗就繞過快取重試一次。

    ⚠️ **快取會毒化特定輸入。** 端點偶爾回傳 HTTP 200 但欄位不全的 JSON，
    那個回應照樣進快取，之後每次重播都在同一個地方失敗——重試沒有用，
    因為根本沒有再送出請求。

    實例：「他的話裡有話」的 `build_anchor` 在快取開啟時 100% 失敗
    （`cultural_items.0.term` 缺欄位），停用快取後 3/3 成功。

    這裡只在錄製時繞過。真正的修法屬於快取層，不在本次範圍內。
    """
    import litellm

    from cognitive_core import llm as llm_mod

    try:
        return app.run_pipeline(text, profile)
    except Exception:  # noqa: BLE001
        pass

    # ⚠️ 光是 `litellm.disable_cache()` 沒有用——`run_pipeline` 每次都建新的
    #    `Client`，而 `Client.__init__` 會呼叫 `_init_cache()` 把快取重新開啟。
    #    所以要連那個函式一起暫時換成 no-op。
    saved_init, saved_cache = llm_mod._init_cache, litellm.cache
    llm_mod._init_cache = lambda cfg: None
    litellm.cache = None
    litellm.disable_cache()
    try:
        out = app.run_pipeline(text, profile)
    finally:
        llm_mod._init_cache = saved_init
        litellm.cache = saved_cache
        if saved_cache is not None:
            litellm.enable_cache()
    print("  ⚠️ 快取毒化，已繞過快取重錄", flush=True)
    return out


def main() -> int:
    import streamlit_app as app

    n_total = len(app.DEMO_SENTENCES) * len(app.PROFILES)
    print(f"錄製 {len(app.DEMO_SENTENCES)} 句 × {len(app.PROFILES)} profile "
          f"= {n_total} 次\n")

    entries: dict[str, dict] = {}
    t0 = time.monotonic()
    i = 0
    for profile in app.PROFILES:
        for text in app.DEMO_SENTENCES:
            i += 1
            print(f"\r  [{i}/{n_total}] {profile:12} {text}", end="", flush=True)
            try:
                tl, final, cost = run_once(app, text, profile)
            except Exception as e:  # noqa: BLE001
                print(f"\n🔴 {profile} / {text} 失敗：{type(e).__name__}: {e}")
                return 1
            # 錄製是一條輸出通道，一樣要擋 CoT 外流
            assert_no_cot(tl)
            entries[f"{profile}|{text}"] = {
                "text": text, "profile": profile,
                "timeline": [n.as_dict() for n in tl],
                "translations": final.get("translations") or {},
                "clarifications": final.get("clarifications") or [],
                "readings": final.get("readings") or [],
                "unknown_scalars": final.get("unknown_scalars") or [],
                "high_uncertainty": final.get("high_uncertainty"),
                "cost": cost,
            }
    print(f"\n  完成，耗時 {time.monotonic() - t0:.0f}s")

    payload = {
        "recorded_at": datetime.datetime.now().astimezone().isoformat(
            timespec="seconds"),
        "commit": git_hash(),
        "sentences": list(app.DEMO_SENTENCES),
        "profiles": list(app.PROFILES),
        "note": ("離線模式播放用的預錄結果。"
                 "⚠️ 這是錄影不是即時執行——介面必須明示這一點。"),
        "entries": entries,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    size = OUT.stat().st_size / 1024
    print(f"\n  {OUT}　{len(entries)} 筆　{size:.0f} KB")
    print(f"  commit {payload['commit']}　{payload['recorded_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
