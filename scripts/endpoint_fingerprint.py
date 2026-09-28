"""端點的行為指紋——偵測模型在不知情的情況下被換掉。

## 為什麼需要

2026-08-22 的從零重現驗證發現：**186/400 的譯文與三天前不同**，
而所有呼叫都是 `temperature=0`。

診斷結果不是 per-call 隨機性（20 句 × 3 次、停用快取，100% 相同），
而是**校內端點在 8/21 與 8/22 之間換了模型**：
當下重新呼叫得到的結果，永遠等於 8/22 的重現值、從不等於 8/20-21 的原值。

問題在於**這件事無法從 API 察覺**：

  - 回應沒有 `system_fingerprint`
  - `/models` 的 `created` 是固定佔位值 1677610602
  - 模型 id 仍是 `mistral-small-4`

於是唯一的辦法是自己量：送一組固定的探測提示，把輸出雜湊起來。
指紋變了就代表端點變了，該重跑受影響的實驗。

⚠️ 探測句刻意不取自評測資料或 dev-30（同 prompt 洩題的理由）。

用法：
    python scripts/endpoint_fingerprint.py            # 量並比對既有記錄
    python scripts/endpoint_fingerprint.py --record   # 覆寫記錄
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

RESULTS = ROOT / "data" / "results"
FP = RESULTS / "endpoint_fingerprint.json"

# 固定探測提示。刻意不取自評測資料也不取自 dev-30。
#
# ⚠️ **句子要夠長夠複雜。** 第一版用了八句簡單直述句，結果 mistral-small-4
# 與 gpt-oss-120b 給出**逐字相同**的譯文（指紋也相同）——那種句子只有一種
# 自然譯法，對模型換版自然也不敏感，指紋就形同虛設。
# 現在用有子句嵌套、省略主詞、量詞、成語的長句，模型之間才會分開。
PROBE_PROMPTS = [
    "由於昨天下了整晚的雨，原訂在河堤舉行的園遊會臨時改到活動中心，"
    "但通知發得太晚，仍有不少人白跑一趟。",
    "他把那筆錢分成三份，一份繳房租，一份寄回老家，剩下的自己留著周轉。",
    "會議上大家都不表態，主管只好點名，被點到的人才勉強說了幾句場面話。",
    "這款相機的鏡頭雖然不是最頂級的，但在同價位裡已經算是相當夠用了。",
    "她一邊收拾行李一邊叮嚀，說到後來自己反而先紅了眼眶。",
    "那家店開了三十幾年，老闆退休後由女兒接手，口味多少還是變了一點。",
    "報告寫得再漂亮，資料如果站不住腳，審查的時候還是會被問倒。",
    "他們兩個從小一起長大，後來因為一件小事鬧翻，現在見面連招呼都不打。",
]


def measure(roles: tuple[str, ...] = ("translate", "judge")) -> dict:
    import litellm
    litellm.cache = None
    litellm.disable_cache()

    from cognitive_core.eval.wsd import TRANSLATE_SYS
    from cognitive_core.llm import Client

    client = Client()
    out = {}
    for role in roles:
        spec = client.cfg.resolve(role)
        outs = []
        for p in PROBE_PROMPTS:
            outs.append(client.text(
                role,
                [{"role": "system", "content": TRANSLATE_SYS},
                 {"role": "user", "content": p}],
                temperature=0.0, max_tokens=200).strip())
        blob = "\n".join(outs)
        out[role] = {
            "model": f"{spec.provider}/{spec.model}",
            "fingerprint": hashlib.sha256(blob.encode()).hexdigest()[:16],
            "samples": outs,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true", help="覆寫記錄")
    args = ap.parse_args()

    print(f"探測 {len(PROBE_PROMPTS)} 句（停用快取，temperature=0）…", flush=True)
    now = measure()
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    old = json.loads(FP.read_text(encoding="utf-8")) if FP.exists() else None
    drift = []
    if old:
        print(f"\n對照記錄　{old.get('measured_at', '—')}")
        for role, cur in now.items():
            prev = (old.get("roles") or {}).get(role)
            if not prev:
                continue
            same = prev["fingerprint"] == cur["fingerprint"]
            print(f"  {role:<10} {cur['model']:<24} "
                  f"{prev['fingerprint']} → {cur['fingerprint']}　"
                  f"{'✅ 未變' if same else '🔴 已變'}")
            if not same:
                n_diff = sum(1 for a, b in zip(prev["samples"], cur["samples"])
                             if a != b)
                drift.append((role, n_diff, len(cur["samples"])))
    else:
        print("\n（無既有記錄）")
        for role, cur in now.items():
            print(f"  {role:<10} {cur['model']:<24} {cur['fingerprint']}")

    if drift:
        print("\n🔴 端點已變動：")
        for role, k, n in drift:
            print(f"   {role}：{k}/{n} 句輸出不同")
        print("   受影響的實驗需要重跑。舊結果不可與新結果混用。")

    if args.record or not FP.exists():
        FP.write_text(json.dumps(
            {"measured_at": stamp, "n_prompts": len(PROBE_PROMPTS),
             "note": "行為指紋。端點不提供 system_fingerprint，"
                     "模型換版無法從 API 察覺，只能自己量。",
             "roles": now}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  已寫入 {FP}")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
