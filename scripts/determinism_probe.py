"""量化端點在 temperature=0 下的非確定性（2026-08-22 重現驗證的後續）。

## 為什麼要量這個

從零重現時發現：**186/400 的譯文與原跑不同**，judge 判定 27/400 不同，
而所有呼叫都是 `temperature=0`。這不是程式的隨機性——探針檔逐位元相同、
抽樣種子固定——而是端點本身。

推測原因：vLLM 一類的推論服務用連續批次（continuous batching），
同一個請求落在不同批次時，GPU 上的浮點運算順序不同，
再加上 MoE 路由，即使 temperature=0 也會給出不同結果。

這支腳本把它量成一個數字，好寫進報告的限制章。

⚠️ **本腳本停用快取**——量的就是端點的重複性，命中快取會量到 100%。

用法：
    python scripts/determinism_probe.py --n 20 --repeats 3
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import yaml  # noqa: E402

from cognitive_core.eval.wsd import (  # noqa: E402
    TRANSLATE_SYS,
    gold_goes_first,
    judge_sense_binary,
    pick_distractor,
    wilson_ci,
)
from cognitive_core.llm import Client  # noqa: E402

RESULTS = ROOT / "data" / "results"
PROBES = ROOT / "data" / "probes" / "wsd_probes.yaml"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="取幾句")
    ap.add_argument("--repeats", type=int, default=3, help="每句重複幾次")
    args = ap.parse_args()

    import litellm
    litellm.cache = None
    litellm.disable_cache()
    print("⚠️ 已停用快取——量的是端點本身的重複性\n")

    items = yaml.safe_load(PROBES.read_text(encoding="utf-8"))["items"][:args.n]
    client = Client()
    tspec = client.cfg.resolve("translate")
    jspec = client.cfg.resolve("judge")
    print(f"翻譯 {tspec.provider}/{tspec.model}　judge {jspec.provider}/{jspec.model}")
    print(f"{len(items)} 句 × {args.repeats} 次，temperature=0\n")

    rows = []
    for i, it in enumerate(items, 1):
        print(f"\r  [{i}/{len(items)}]", end="", flush=True)
        trs, chs = [], []
        dis = pick_distractor(it)
        gf = gold_goes_first(i)
        gd, dd = it["gold_definition"], dis["definition"]
        def_a, def_b = (gd, dd) if gf else (dd, gd)
        for _ in range(args.repeats):
            t = client.text("translate",
                            [{"role": "system", "content": TRANSLATE_SYS},
                             {"role": "user", "content": it["sentence"]}],
                            temperature=0.0, max_tokens=400)
            trs.append(t.strip())
            j = judge_sense_binary(client, it["target_word"], trs[0],
                                   def_a, def_b)
            chs.append(j["choice"])
        rows.append({"probe_id": it["id"],
                     "translations": trs, "choices": chs,
                     "translation_stable": len(set(trs)) == 1,
                     "judge_stable": len(set(chs)) == 1})
    print()

    n = len(rows)
    ts = sum(r["translation_stable"] for r in rows)
    js = sum(r["judge_stable"] for r in rows)
    tlo, thi = wilson_ci(ts, n)
    jlo, jhi = wilson_ci(js, n)

    L = [f"# 端點在 temperature=0 下的重複性　n={n} 句 × {args.repeats} 次", "",
         "> ⚠️ 本測試**停用快取**。量的是端點本身，不是快取命中率。", "",
         f"翻譯 `{tspec.provider}/{tspec.model}`　"
         f"judge `{jspec.provider}/{jspec.model}`", "",
         "| 階段 | 重複 n 次結果完全相同 | 比例 | 95% CI |",
         "| --- | :-: | :-: | :-: |",
         f"| 翻譯 | {ts}/{n} | {ts / n:.0%} | [{tlo:.0%}, {thi:.0%}] |",
         f"| judge（固定譯文） | {js}/{n} | {js / n:.0%} | [{jlo:.0%}, {jhi:.0%}] |",
         "", "## 判讀", "",
         "`temperature=0` 只保證取樣時選機率最高的 token，"
         "**不保證兩次前向傳播算出同一組機率**。",
         "推論服務用連續批次時，同一個請求落在不同批次會改變 GPU 上的",
         "浮點運算順序；MoE 模型的路由也可能因此不同。", "",
         "⇒ 本專案的數字**不是位元級可重現**的。",
         "報告與 README 必須說明這一點，並改以「結論穩健」而非「數字相同」",
         "作為可重現性的主張。", ""]
    unstable = [r for r in rows if not r["translation_stable"]]
    if unstable:
        L += ["## 譯文不穩定的例子", ""]
        for r in unstable[:3]:
            L.append(f"**`{r['probe_id']}`**")
            for k, t in enumerate(dict.fromkeys(r["translations"]), 1):
                L.append(f"{k}. {t}")
            L.append("")
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "determinism_probe.md"
    out.write_text("\n".join(L), encoding="utf-8")
    (RESULTS / "determinism_probe.json").write_text(json.dumps(
        {"n": n, "repeats": args.repeats,
         "translate_model": f"{tspec.provider}/{tspec.model}",
         "judge_model": f"{jspec.provider}/{jspec.model}",
         "translation_stable": ts, "judge_stable": js, "rows": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  翻譯完全相同 {ts}/{n} = {ts / n:.0%}　CI [{tlo:.0%}, {thi:.0%}]")
    print(f"  judge 完全相同 {js}/{n} = {js / n:.0%}　CI [{jlo:.0%}, {jhi:.0%}]")
    print(f"\n  {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
