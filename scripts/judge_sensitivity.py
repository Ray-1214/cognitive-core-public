"""judge 選擇的敏感度檢查（2026-08-23 裁示 A-2）。

## 問題

校內端點的 `mistral-small-4` 與 `gpt-oss-120b` 極可能由同一後端提供服務
（見 `data/results/endpoint_identity_check.md`），所以 judge 與受測模型
不是獨立的。**換一個確定不同來源的 judge，主指標會不會大幅偏移？**

## 設計

- 從 400 筆隨機抽 50（種子記錄於輸出）
- 用 `judge_gemini` profile 重判。**譯文走快取不重譯**——
  重譯會讓「換 judge」與「換翻譯」兩個變因混在一起
- 報告兩個 judge 各自判出的錯誤率與 CI，以及逐題一致率

判讀（裁示定的區間）：
  落在 27–33% → 主指標對 judge 的選擇不敏感
  差很多      → 那是更重要的發現

⚠️ Gemini 免費層有日配額。撞 429 就停，**不重試**——前幾輪曾因重試燒掉配額。

用法：
    python scripts/judge_sensitivity.py --n 50
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import yaml  # noqa: E402

from cognitive_core.eval.cross_check import check_cross  # noqa: E402
from cognitive_core.eval.wsd import (  # noqa: E402
    gold_goes_first,
    judge_sense_binary,
    pick_distractor,
    translate,
    wilson_ci,
)
from cognitive_core.llm import Client, LLMError  # noqa: E402
from cognitive_core.runlog import RunLog  # noqa: E402

RESULTS = ROOT / "data" / "results"
PROBES = ROOT / "data" / "probes" / "wsd_probes.yaml"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--profile", default="judge_gemini")
    ap.add_argument("--min-n", type=int, default=30,
                    help="低於此數不下判讀。n=10 時 CI 寬到 [6%%, 51%%]，"
                         "任何判讀都是雜訊")
    args = ap.parse_args()

    base = json.loads(
        (RESULTS / "wsd_baseline400.json").read_text(encoding="utf-8"))
    items_by_id = {p["id"]: p for p in yaml.safe_load(
        PROBES.read_text(encoding="utf-8"))["items"]}
    judgeable = [it for it in base["items"] if it.get("correct") is not None]

    rng = random.Random(args.seed)
    picked = rng.sample(judgeable, min(args.n, len(judgeable)))
    print(f"從 {len(judgeable)} 筆可判定題目隨機抽 {len(picked)}（seed={args.seed}）")

    run = RunLog("judge_sensitivity", meta={"n": len(picked), "seed": args.seed,
                                            "profile": args.profile})
    client = Client(run=run, profile=args.profile)
    client.cfg.defaults["max_retries"] = 0        # 撞 429 不重試燒配額
    jspec = client.cfg.resolve("judge", args.profile)
    tspec = client.cfg.resolve("translate", args.profile)
    print(f"對照 judge：{jspec.provider}/{jspec.model}")

    cross = check_cross(client, profile=args.profile)
    print(f"行為層 judge_cross：{'✅ 通過' if cross.is_cross else '🔴 未通過'}")
    if not cross.is_cross:
        print("🔴 對照 judge 與受測模型仍非獨立，敏感度檢查沒有意義。",
              file=sys.stderr)
        return 2

    rows, aborted = [], None
    for i, it in enumerate(picked, 1):
        print(f"\r  [{i}/{len(picked)}] {it['probe_id']:18}", end="", flush=True)
        p = items_by_id[it["probe_id"]]
        dis = pick_distractor(p)
        gf = bool(it["gold_first"])
        gd, dd = p["gold_definition"], dis["definition"]
        def_a, def_b = (gd, dd) if gf else (dd, gd)
        try:
            # 譯文走快取，不重譯——否則「換 judge」與「換翻譯」會混在一起
            tr = translate(client, p["sentence"], role="translate")
            j = judge_sense_binary(client, p["target_word"], tr, def_a, def_b)
        except LLMError as e:
            msg = str(e)
            if "RateLimit" in msg:
                # 日配額。依裁示不重試——前幾輪曾因重試燒掉整天的額度
                aborted = (f"第 {i} 筆撞到 RateLimit（研判為日配額），"
                           f"已停止且不重試。已完成 {len(rows)} 筆")
                print(f"\n🔴 {aborted}")
                break
            if "ServiceUnavailable" not in msg:
                rows.append({"probe_id": it["probe_id"], "error": msg[:120]})
                continue
            # 503「high demand」是暫時性的，與配額無關。等一次再試一次。
            # 首跑 50 筆中有 9 筆因此被丟掉，只剩 10 筆可比——那才是樣本不足的主因。
            time.sleep(20)
            try:
                tr = translate(client, p["sentence"], role="translate")
                j = judge_sense_binary(client, p["target_word"], tr,
                                       def_a, def_b)
            except LLMError as e2:
                rows.append({"probe_id": it["probe_id"], "error": str(e2)[:120]})
                continue
        letter = j["choice"]
        alt_correct = (None if letter == "NONE"
                       else ((letter == "A") == gf))
        rows.append({"probe_id": it["probe_id"], "stratum": it["stratum"],
                     "gold_first": gf,
                     "base_choice": it["raw_choice"], "base_correct": it["correct"],
                     "alt_choice": letter, "alt_correct": alt_correct,
                     "alt_conf": j["confidence"]})
    print()

    ok = [r for r in rows if r.get("alt_correct") is not None
          and r.get("base_correct") is not None]
    n = len(ok)
    if not n:
        print("🔴 沒有可比較的題目", file=sys.stderr)
        return 1
    b_err = sum(1 for r in ok if r["base_correct"] is False)
    a_err = sum(1 for r in ok if r["alt_correct"] is False)
    blo, bhi = wilson_ci(b_err, n)
    alo, ahi = wilson_ci(a_err, n)
    agree = sum(1 for r in ok if r["base_choice"] == r["alt_choice"])
    glo, ghi = wilson_ci(agree, n)
    a_rate = a_err / n

    # ⚠️ n 太小時不得下判讀。第一次跑在 n=10 就印出「偏移超出 27–33%」，
    # 但那時的 CI 是 [1.8%, 40.4%]，涵蓋了整個判讀區間——那是雜訊不是發現。
    if n < args.min_n:
        verdict = (f"🔴 **樣本不足（n={n} < {args.min_n}），不下判讀。**"
                   f"錯誤率的 95% CI 為 [{alo:.1%}, {ahi:.1%}]，"
                   "寬到涵蓋整個判讀區間。")
    elif 0.27 <= a_rate <= 0.33:
        verdict = "主指標對 judge 的選擇**不敏感**（落在 27–33%）"
    else:
        verdict = "🔴 **偏移超出 27–33%**——這是更重要的發現，需回報"

    L = [f"# judge 選擇的敏感度檢查　n={n}", "",
         "> 校內端點的兩個 model id 極可能由同一後端提供服務"
         "（`endpoint_identity_check.md`），",
         "> 所以 judge 與受測模型不獨立。此處換一個**確定不同來源**的 judge，",
         "> 看主指標會不會大幅偏移。", "",
         f"- 抽樣：從 400 筆可判定題目隨機抽 {len(picked)}，seed=`{args.seed}`",
         f"- 譯文：**走快取不重譯**（`{tspec.provider}/{tspec.model}`）"
         "——否則換 judge 與換翻譯兩個變因會混在一起",
         f"- 對照 judge：`{jspec.provider}/{jspec.model}`"
         f"　行為層 judge_cross ✅ 通過", ""]
    if aborted:
        L += [f"> 🔴 **{aborted}**", ""]
    L += ["## 錯誤率", "",
          "| judge | 錯誤 | 錯誤率 | 95% CI |", "| --- | :-: | :-: | :-: |",
          f"| `{base['judge_model']}`（原） | {b_err}/{n} | {b_err / n:.1%} | "
          f"[{blo:.1%}, {bhi:.1%}] |",
          f"| `{jspec.provider}/{jspec.model}`（對照） | {a_err}/{n} | "
          f"**{a_rate:.1%}** | [{alo:.1%}, {ahi:.1%}] |", "",
          f"400 筆全樣本的原始錯誤率為 {1 - base['accuracy']:.1%}。", "",
          f"**判讀：{verdict}**", "",
          "## 逐題一致率", "",
          f"兩個 judge 選到同一個選項：**{agree}/{n} = {agree / n:.0%}**"
          f"　95% CI [{glo:.0%}, {ghi:.0%}]", "",
          "⚠️ 一致率低於錯誤率的接近程度是正常的——"
          "兩個 judge 可以在不同題目上各自出錯，卻得到相近的總錯誤率。",
          "所以兩個數字都要看。", ""]

    dis = [r for r in ok if r["base_choice"] != r["alt_choice"]]
    if dis:
        L += ["## 不一致的題目", "",
              "| probe | 層 | 原 judge | 對照 judge | 原判對 | 對照判對 |",
              "| --- | :-: | :-: | :-: | :-: | :-: |"]
        for r in dis[:20]:
            L.append(f"| `{r['probe_id']}` | {r['stratum'][:3]} | "
                     f"{r['base_choice']} | {r['alt_choice']} | "
                     f"{'✅' if r['base_correct'] else '❌'} | "
                     f"{'✅' if r['alt_correct'] else '❌'} |")
        if len(dis) > 20:
            L.append(f"\n（另有 {len(dis) - 20} 筆未列）")
        L.append("")

    out = RESULTS / "judge_sensitivity.md"
    out.write_text("\n".join(L), encoding="utf-8")
    (RESULTS / "judge_sensitivity.json").write_text(json.dumps(
        {"n": n, "n_sampled": len(picked), "seed": args.seed,
         "aborted": aborted,
         "base_judge": base["judge_model"],
         "alt_judge": f"{jspec.provider}/{jspec.model}",
         "base_error_rate": b_err / n, "base_ci": [blo, bhi],
         "alt_error_rate": a_rate, "alt_ci": [alo, ahi],
         "agreement": agree / n, "agreement_ci": [glo, ghi],
         "conclusive": bool(n >= args.min_n),
         "min_n": args.min_n,
         "insensitive": (bool(0.27 <= a_rate <= 0.33)
                         if n >= args.min_n else None),
         "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 62)
    print(f"  原 judge   錯誤率 {b_err / n:.1%}　[{blo:.1%}, {bhi:.1%}]")
    print(f"  對照 judge 錯誤率 {a_rate:.1%}　[{alo:.1%}, {ahi:.1%}]")
    print(f"  逐題一致率 {agree}/{n} = {agree / n:.0%}")
    print(f"\n  {verdict}")
    print(f"  {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
