"""M0 端到端煙霧測試：確認 litellm 這條路整條會動。

驗證項目：
  1. 基本呼叫（校內 + Gemini）
  2. 結構化輸出的降級階梯 —— mistral 應走 tier2、gpt-oss 應走 tier1
  3. embedding
  4. 快取命中，且不同 temperature 不命中（線上版回歸測試）
  5. run 記錄含 commit hash / prompt hash / token / 耗時

用法：
    python scripts/smoke_llm.py
    python scripts/smoke_llm.py --skip-gemini      # 日配額用盡時
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from cognitive_core.config import get_config  # noqa: E402
from cognitive_core.llm import Client, LLMError  # noqa: E402
from cognitive_core.runlog import RunLog  # noqa: E402

ANCHOR_SCHEMA = {
    "type": "object",
    "properties": {
        "agent": {"type": "string"},
        "tense": {"type": "string", "enum": ["PAST", "PRESENT", "FUTURE", "UNKNOWN"]},
        "register": {"type": "string", "enum": ["FORMAL", "SEMI_FORMAL", "CASUAL", "UNKNOWN"]},
    },
    "required": ["agent", "tense", "register"],
    "additionalProperties": False,
}
SYS = ("你是語言學分析助手。分析中文句子並輸出 JSON。無法從句子本身確定的欄位填 "
       '"UNKNOWN"，不得猜測。只輸出 JSON，不要 markdown 圍欄。')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-gemini", action="store_true")
    ap.add_argument("--profile", default=None,
                    help="experiment_profile，例如 smoke（金鑰權限受限時用）")
    args = ap.parse_args()

    cfg = get_config()
    run = RunLog("smoke", meta={"purpose": "M0 端到端驗證", "profile": args.profile})
    cli = Client(cfg, run=run, profile=args.profile)
    ok, fail = 0, 0

    def check(label: str, fn):
        nonlocal ok, fail
        try:
            r = fn()
            print(f"  ✅ {label}: {r}")
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ {label}: {type(e).__name__}: {str(e)[:150]}")
            fail += 1

    print("=== 1. 基本呼叫 ===")
    msg = [{"role": "user", "content": "只回覆 OK 兩個字"}]
    check(f"role=translate → {cfg.resolve('translate', args.profile).model}",
          lambda: cli.text("translate", msg, max_tokens=20)[:20])
    check(f"role=reflect → {cfg.resolve('reflect', args.profile).model}",
          lambda: cli.text("reflect", msg, max_tokens=20)[:20])
    if not args.skip_gemini:
        check("gemini (role=judge)", lambda: cli.text("judge", msg, max_tokens=20)[:20])

    print("\n=== 2. 結構化輸出降級階梯（§5.2）===")
    smsg = [{"role": "system", "content": SYS},
            {"role": "user", "content": "分析這句話：方便的話明天再說吧"}]
    for role, expect in [("translate", "tier2 (mistral 的 json_schema 實測失效)"),
                         ("reflect", "tier1 (gpt-oss 支援嚴格模式)")]:
        def f(role=role):
            obj, tier = cli.structured(role, smsg, ANCHOR_SCHEMA, max_tokens=300)
            return f"tier={tier}  keys={sorted(obj)}"
        check(f"{role} → 預期 {expect}", f)

    print("\n=== 3. embedding ===")
    check("bge-m3-embedding",
          lambda: f"dim={len(cli.embed(['方便的話明天再說吧', '如果有空明天再談'])[0])}")

    print("\n=== 4. 快取行為（線上回歸測試）===")
    cmsg = [{"role": "user", "content": "把「今天天氣很好」翻成英文，只輸出譯文"}]

    def cache_same():
        a = cli.text("translate", cmsg, temperature=0.0, max_tokens=60)
        b = cli.text("translate", cmsg, temperature=0.0, max_tokens=60)
        return f"相同參數兩次呼叫 → {'一致（快取生效）' if a == b else '不一致'}"

    def cache_diff_temp():
        cli.text("translate", cmsg, temperature=0.0, max_tokens=60)
        cli.text("translate", cmsg, temperature=1.5, max_tokens=60)
        lines = [json.loads(x) for x in run.path.read_text(encoding="utf-8").splitlines()]
        calls = [c for c in lines if c.get("_type") == "call"][-2:]
        t = [c["params"].get("temperature") for c in calls]
        hit = [c["cached"] for c in calls]
        return f"temperature={t} → cached={hit}（第二筆必須為 False）"

    check("相同參數應命中快取", cache_same)
    check("不同 temperature 不得命中同一份快取", cache_diff_temp)

    print("\n=== 5. run 記錄 ===")
    s = run.summary()
    lines = [json.loads(x) for x in run.path.read_text(encoding="utf-8").splitlines()]
    hdr = lines[0]
    print(f"  run_id      {s['run_id']}")
    print(f"  git         {hdr['git']['commit'][:8]} ({hdr['git']['branch']})"
          f"{' [dirty]' if hdr['git']['dirty'] else ''}")
    print(f"  呼叫 {s['calls']} 次｜快取命中 {s['cache_hits']}｜錯誤 {s['errors']}"
          f"｜token {s['total_tokens']}｜累計 {s['wall_s']}s")
    sample = next((c for c in lines if c.get("_type") == "call"), None)
    if sample:
        print(f"  首筆欄位    {sorted(sample)}")
    print(f"  檔案        {s['path']}")

    print(f"\n{'=' * 60}\n通過 {ok}｜失敗 {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
