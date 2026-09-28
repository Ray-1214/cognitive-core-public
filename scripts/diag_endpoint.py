"""診斷 litellm 對校內端點的 URL 組法與 Gemini 回應結構。"""

from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import litellm  # noqa: E402

from cognitive_core.config import get_config  # noqa: E402

litellm.suppress_debug_info = True
litellm.drop_params = True

print("=== 環境變數（不印金鑰內容）===")
for k in ["ITHU_API_BASE", "ITHU_API_KEY", "GOOGLE_API_KEY"]:
    v = os.environ.get(k)
    print(f"  {k:16} {'(未設定)' if not v else (v if 'BASE' in k else f'已設定，{len(v)} 字元')}")

cfg = get_config()
spec = cfg.resolve("translate")
print(f"\n=== config 解析結果 ===")
print(f"  litellm_model  {spec.litellm_model}")
print(f"  api_base       {spec.api_base}")

print("\n=== 逐個 api_base 候選試打 ===")
base_env = (os.environ.get("ITHU_API_BASE") or "<your-llm-endpoint>").rstrip("/")
candidates = [base_env, base_env + "/v1"]
if base_env.endswith("/v1"):
    candidates.insert(0, base_env[:-3].rstrip("/"))
msg = [{"role": "user", "content": "只回 OK"}]
for base in dict.fromkeys(candidates):
    try:
        r = litellm.completion(model="openai/mistral-small-4", messages=msg,
                               api_base=base, api_key=os.environ["ITHU_API_KEY"],
                               max_tokens=10, temperature=0, timeout=60)
        print(f"  ✅ {base}  ->  {r.choices[0].message.content!r}")
    except Exception as e:  # noqa: BLE001
        print(f"  ❌ {base}  ->  {type(e).__name__}: {str(e)[:110]}")

print("\n=== Gemini 回應結構 ===")
try:
    r = litellm.completion(model="gemini/gemini-flash-latest", messages=msg,
                           api_key=os.environ.get("GOOGLE_API_KEY"),
                           max_tokens=20, temperature=0, timeout=60)
    ch = r.choices[0]
    print(f"  finish_reason  {ch.finish_reason}")
    print(f"  content        {getattr(ch.message, 'content', None)!r}")
    print(f"  reasoning      {getattr(ch.message, 'reasoning_content', None)!r}")
    print(f"  usage          {r.usage}")
except Exception as e:  # noqa: BLE001
    print(f"  ❌ {type(e).__name__}: {str(e)[:220]}")
