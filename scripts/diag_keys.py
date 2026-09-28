"""確認金鑰的模型存取權限，以及 Gemini 的 thinking token 行為。"""

from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import litellm  # noqa: E402

litellm.suppress_debug_info = True
litellm.drop_params = True

BASE = (os.environ.get("ITHU_API_BASE") or "<your-llm-endpoint>").rstrip("/")
if not BASE.endswith("/v1"):
    BASE += "/v1"
KEY = os.environ.get("ITHU_API_KEY")

print("=== 校內金鑰可存取哪些模型 ===")
MODELS = ["mistral-small-4", "gpt-oss-120b", "llama4scout", "nemotron-3-ultra",
          "ornith-35b", "diffusiongemma-26b", "vibe", "vibecode", "office"]
allowed, denied = [], []
for m in MODELS:
    try:
        litellm.completion(model=f"openai/{m}", messages=[{"role": "user", "content": "OK"}],
                           api_base=BASE, api_key=KEY, max_tokens=5, timeout=60)
        allowed.append(m)
        print(f"  ✅ {m}")
    except Exception as e:  # noqa: BLE001
        s = str(e)
        if "not allowed to access" in s:
            denied.append(m)
            print(f"  🔒 {m}  權限不足")
        else:
            print(f"  ❌ {m}  {type(e).__name__}: {s[:80]}")
print(f"\n  可用 {len(allowed)}｜權限不足 {len(denied)}")
if denied:
    print(f"  🔴 研究模型被拒：{', '.join(denied)}")

print("\n=== embedding 端點 ===")
try:
    r = litellm.embedding(model="openai/bge-m3-embedding",
                          input=["測試"], api_base=BASE, api_key=KEY, timeout=60)
    print(f"  ✅ dim={len(r.data[0]['embedding'])}")
except Exception as e:  # noqa: BLE001
    print(f"  ❌ {type(e).__name__}: {str(e)[:150]}")

print("\n=== Gemini：thinking token 行為 ===")
gk = os.environ.get("GOOGLE_API_KEY")
for mt in [20, 200, 2000]:
    try:
        r = litellm.completion(model="gemini/gemini-flash-latest",
                               messages=[{"role": "user", "content": "只回覆 OK 兩個字"}],
                               api_key=gk, max_tokens=mt, temperature=0, timeout=90)
        ch = r.choices[0]
        rt = getattr(r.usage, "completion_tokens_details", None)
        rt = getattr(rt, "reasoning_tokens", None) if rt else None
        print(f"  max_tokens={mt:<5} finish={ch.finish_reason:<8} "
              f"content={str(getattr(ch.message,'content',None))[:24]!r} reasoning_tokens={rt}")
    except Exception as e:  # noqa: BLE001
        print(f"  max_tokens={mt:<5} ❌ {type(e).__name__}: {str(e)[:90]}")

print("\n=== Gemini：關閉 thinking ===")
try:
    r = litellm.completion(model="gemini/gemini-flash-latest",
                           messages=[{"role": "user", "content": "只回覆 OK 兩個字"}],
                           api_key=gk, max_tokens=50, temperature=0, timeout=90,
                           thinking={"type": "disabled"})
    print(f"  ✅ content={r.choices[0].message.content!r}")
except Exception as e:  # noqa: BLE001
    print(f"  ❌ {type(e).__name__}: {str(e)[:150]}")
