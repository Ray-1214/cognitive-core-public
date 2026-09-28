"""MT 詞義錯誤基準：翻譯 → judge → 比對 gold。

⚠️ **撞到 429 立刻中止，不重試。** Gemini 免費層的日配額前幾輪已被重試燒掉一次。
本腳本把 max_retries 設為 0，並在偵測到 RateLimitError 時停止整批並回報進度。

用法：
    python scripts/run_wsd.py --n 30
    python scripts/run_wsd.py --n 200 --out data/results/wsd_baseline.md
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from cognitive_core.assets import asset_manifest  # noqa: E402
from cognitive_core.data.length_audit import (  # noqa: E402
    audit_predicts_error,
    format_report,
)
from cognitive_core.eval.cross_check import (  # noqa: E402
    SameBackend,
    assert_judge_is_cross as assert_judge_is_cross_behaviour,
    check_cross,
)
from cognitive_core.eval.wsd import (  # noqa: E402
    Outcome,
    dominant_bias,
    none_breakdown,
    paired_bootstrap_diff,
    position_effect,
    run_one,
    summarise,
    wilson_ci,
)
from cognitive_core.llm import Client  # noqa: E402
from cognitive_core.runlog import RunLog  # noqa: E402

PROBES = ROOT / "data" / "probes" / "wsd_probes.yaml"
RESULTS = ROOT / "data" / "results"


class RateLimitAbort(RuntimeError):
    pass


def pct(k: int, n: int) -> str:
    return f"{k}/{n}（{k / n * 100:.0f}%）" if n else f"{k}/0"


def ci_str(lo: float, hi: float) -> str:
    return f"[{lo:.3f}, {hi:.3f}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--out", default=None)
    ap.add_argument("--translate-only", action="store_true",
                    help="只跑翻譯（校內 API），不呼叫 judge。"
                         "譯文會進快取，之後補跑 judge 不需重譯")
    ap.add_argument("--allow-same-backend", action="store_true",
                    help="行為層 judge_cross 未通過時仍繼續。"
                         "此事實會寫進報表標頭——這是知情下的選擇，不是繞過")
    ap.add_argument("--judge-profile", default=None,
                    help="切換評審：judge_cross（預設，gpt-oss-120b）／"
                         "judge_gemini（評審間一致性檢驗用）")
    args = ap.parse_args()
    n_each = args.n // 2

    data = yaml.safe_load(PROBES.read_text(encoding="utf-8"))
    items = data["items"]
    dom = [i for i in items if i["stratum"] == "dominant"][:n_each]
    non = [i for i in items if i["stratum"] == "non_dominant"][:args.n - n_each]
    picked = dom + non
    print(f"抽 {len(picked)} 筆（主流 {len(dom)}／非主流 {len(non)}）")

    run = RunLog("wsd", meta={"assets": asset_manifest(), "n_items": len(picked),
                              "judge_profile": args.judge_profile or "(default)",
                              "task": "MT word-sense error benchmark"})
    client = Client(run=run, profile=args.judge_profile)
    client.cfg.defaults["max_retries"] = 0      # 撞 429 不讓 litellm 內部重試燒配額

    # 球員兼裁判會讓 self-preference bias 無法排除，且事後從結果看不出來。
    # 名稱層檢查（便宜，但擋不住「不同 id 同一後端」）
    client.cfg.assert_judge_is_cross(args.judge_profile)
    # 行為層檢查（截斷點）。本專案現行設定通不過——那是研究發現本身，
    # 不是要修掉的 bug。必須明示 --allow-same-backend 才放行，
    # 讓「知情下繼續」留在指令列與報表裡。
    cross = None
    try:
        cross = assert_judge_is_cross_behaviour(
            client, profile=args.judge_profile)
        print("✅ 行為層 judge_cross 通過（截斷行為不同）")
    except SameBackend as e:
        cross = check_cross(client, profile=args.judge_profile)
        print(f"\n🔴 行為層 judge_cross 未通過\n{e}\n")
        if not args.allow_same_backend:
            print("要在知情下繼續，請加 --allow-same-backend。", file=sys.stderr)
            return 3
        print("⚠️ 已加 --allow-same-backend，在知情下繼續。"
              "此事實會寫進報表標頭。\n")

    tspec = client.cfg.resolve("translate", args.judge_profile)
    jspec = client.cfg.resolve("judge", args.judge_profile)
    print(f"翻譯：{tspec.provider}/{tspec.model}　"
          f"judge：{jspec.provider}/{jspec.model}　"
          f"{'✅ 確為不同後端' if (cross and cross.is_cross) else '🔴 名稱不同但行為相同'}")
    if jspec.rpm and jspec.rpm < 60:
        print(f"judge 控速 rpm={jspec.rpm}，"
              f"預估純等待 {len(picked) * 60 / jspec.rpm:.0f}s")
    print()

    outcomes: list[Outcome] = []
    aborted = None
    n_429 = 0
    # A/B 位置配平：分層內逐題交替，任何前綴的失衡都 ≤1。
    # 用雜湊決定不是配平——先前實測 60 筆分到 23/37。
    seen_in_stratum: dict[str, int] = {}
    for n, it in enumerate(picked, 1):
        print(f"\r[{n}/{len(picked)}] {it['id']:18}", end="", flush=True)
        k = seen_in_stratum.get(it["stratum"], 0)
        seen_in_stratum[it["stratum"]] = k + 1
        o = run_one(client, it, translate_only=args.translate_only,
                    index_within_stratum=k)
        # 429 在此為**每分鐘限流**而非日配額耗盡（實測 15s 後重試即成功）。
        # 給一次長退避重試以區分兩者：連續兩次 429 才視為配額耗盡並中止整批。
        if o.error and "RateLimit" in o.error:
            n_429 += 1
            print(f"\n  ⏳ 第 {n} 筆 429（累計 {n_429} 次），等 25s 後重試一次 …",
                  flush=True)
            time.sleep(25)
            o = run_one(client, it, index_within_stratum=k)
            if o.error and "RateLimit" in o.error:
                aborted = (f"第 {n} 筆連續兩次 429（間隔 25s），研判為日配額耗盡，"
                           f"已中止。累計 429 {n_429} 次")
                outcomes.append(o)
                print(f"\n🔴 {aborted}")
                break
        outcomes.append(o)
    print()
    if n_429:
        print(f"  （過程中 429 共 {n_429} 次，皆以單次 25s 退避化解）")

    s = summarise(outcomes)
    dom_f = [o.correct for o in outcomes
             if o.stratum == "dominant" and o.correct is not None]
    non_f = [o.correct for o in outcomes
             if o.stratum == "non_dominant" and o.correct is not None]
    diff, dci, dp = paired_bootstrap_diff(dom_f, non_f)

    # 停止判準
    stops: list[str] = []
    n = len(outcomes)
    if n and s.n_translation_failed / n > 0.20:
        stops.append(f"🔴 translation_failed {pct(s.n_translation_failed, n)} > 20%")
    if n and s.n_none / n > 0.30:
        stops.append(f"🔴 NONE {pct(s.n_none, n)} > 30%")
    chosen = [o.chosen for o in outcomes if o.chosen and o.chosen != "NONE"]
    if chosen:
        # ⚠️ tie-break 用 sense_id，不要只用 count。
        # `max(set(...), key=count)` 在並列時回傳**迭代順序**的第一個，
        # 而 set 的順序隨 PYTHONHASHSEED 變動——判定的布林值不受影響
        # （次數相同），但報表印出來的 sense_id 每次跑會不一樣。
        top = max(set(chosen), key=lambda s: (chosen.count(s), s))
        if chosen.count(top) / len(chosen) > 0.5:
            stops.append(f"🔴 judge 有 {pct(chosen.count(top), len(chosen))} "
                         f"回同一個 sense_id `{top}`，可能在猜")
    if not (isinstance(diff, float) and diff != diff) and abs(diff) < 0.03:
        stops.append(f"⚠️ 兩層差 {diff * 100:+.1f}pp < 3pp，可能沒訊號"
                     f"（n={len(dom_f)}／{len(non_f)}，先不下結論）")

    # ── 報告 ──
    L = [f"# MT 詞義錯誤基準　n={len(outcomes)}", "",
         "> ⚠️ **judge 未經人工驗證前，所有數字標為 preliminary。**",
         f"> 翻譯：`{tspec.provider}/{tspec.model}`　"
         f"judge：`{jspec.provider}/{jspec.model}`"
         f"（judge_cross：**名稱**不同）",
         "> 任務：CWN-SemCor 句子 → 翻成英文 → judge 判譯文表達哪個義項 → 比對 CWN gold",
         ""]
    if cross is not None and not cross.is_cross:
        L += ["> 🔴 **judge_cross 的行為層檢查未通過。**"
              "兩個 model id 的 tokenizer 截斷點逐字相同，",
              "> 極可能由同一個後端提供服務，"
              "self-preference bias 無法排除。",
              "> 本次以 `--allow-same-backend` 在知情下執行。",
              "> 證據見 `data/results/endpoint_identity_check.md`。", ""]
    if aborted:
        L += [f"> 🔴 **{aborted}**", ""]
    L += ["## 停止判準", ""]
    L += ([f"- {x}" for x in stops] if stops else ["- ✅ 全部未觸發"])
    L += ["", "## 整體", "",
          "| 項目 | 值 |", "| --- | :-: |",
          f"| 總題數 | {n} |",
          f"| translation_failed | {pct(s.n_translation_failed, n)} |",
          f"| error | {pct(s.n_error, n)} |",
          f"| judge 回 NONE | {pct(s.n_none, n)} |",
          f"| **可判定** | {pct(s.n_judgeable, n)} |",
          f"| **義項正確率** | **{s.accuracy:.3f}**"
          f"　{ci_str(*wilson_ci(s.n_correct, s.n_judgeable))} |",
          "", "## 分層 ⭐ 主結果", "",
          "| 層 | n（可判定） | 正確 | 正確率 | 95% CI |",
          "| --- | :-: | :-: | :-: | :-: |"]
    for st, label in (("dominant", "主流（gold 為最高頻）"),
                      ("non_dominant", "非主流")):
        d = s.by_stratum[st]
        L.append(f"| {label} | {d['n']} | {d['correct']} | {d['acc']:.3f} | "
                 f"{ci_str(*d['ci'])} |")
    L += ["",
          f"**兩層之差（主流 − 非主流）**：{diff * 100:+.1f}pp"
          f"　95% CI [{dci[0] * 100:+.1f}, {dci[1] * 100:+.1f}]pp　p≈{dp:.3f}",
          "",
          "| 觀察 | 判讀 |", "| --- | --- |",
          "| 主流高、非主流低 | 走頻率捷徑，沒讀脈絡 |",
          "| 兩層相近 | 真的在讀脈絡 |",
          "| 兩層都低 | 任務太難或 judge 有問題 |",
          ""]

    # ── (a) NONE 的成因分類 ──
    nb = none_breakdown(outcomes)
    L += ["---", "", "## (a) NONE 的成因", "",
          "> NONE 有時是正確的：譯文若根本沒譯出該詞，任何義項都不符。",
          "> 分兩類才知道 NONE 比例是特性還是缺陷。", "",
          "| 類別 | n | 比例 | 判讀 |", "| --- | :-: | :-: | --- |"]
    if nb["n_classified"]:
        for key, label, note in (
                ("not_rendered", "譯文沒譯出該詞", "**NONE 正確**，是翻譯的遺漏不是 judge 的錯"),
                ("rendered", "譯文有譯出但 judge 認不出", "**judge 的問題**，計入 judge 錯誤率")):
            k = nb[key]
            lo, hi = wilson_ci(k, nb["n_classified"])
            L.append(f"| {label} | {k} | {k / nb['n_classified'] * 100:.0f}%"
                     f"　{ci_str(lo, hi)} | {note} |")
    L.append(f"| 未分類 | {nb['unclassified']} | — | 成因分類呼叫失敗 |")
    L += ["", f"NONE 總數 {nb['n_none']}／{n}，已分類 {nb['n_classified']}", ""]

    # ── (b) 錯誤時是否偏向最高頻義項 ──
    db = dominant_bias(outcomes)
    L += ["---", "", "## (b) 錯誤時模型選了哪個義項 ⭐ 與 CHA-Gen 的銜接", "",
          "> CHA-Gen 發現「模型偏好主流解讀」。若成立，本專案的錯誤應集中在",
          "> 該詞的最高頻義項那一側。隨機基準為 1/候選數的加權平均。", ""]
    if db.get("not_applicable"):
        L += [f"🔴 **本設計下不適用**（錯誤題數 {db['n']}）", "",
              db["reason"], "",
              "二元設計中干擾項恆為「同 lemma 中最高頻的非 gold 義項」，於是",
              "「錯誤中選到最高頻的比例」等於「錯誤有多少落在非主流層」——",
              "那是抽樣設計的產物，不是模型偏好。隨機基準也退化成 0.5。", "",
              "**該研究問題改由上方的兩層正確率之差回答**："
              "若模型偏好高頻義項，非主流層的錯誤率應系統性較高。", ""]
    elif db.get("n"):
        L += [f"- 錯誤題數：{db['n']}",
              f"- 其中選到**最高頻義項**：{db['picked_top']}"
              f"（{db['rate'] * 100:.1f}%，95% CI "
              f"[{db['ci'][0] * 100:.1f}, {db['ci'][1] * 100:.1f}]%）",
              f"- 隨機基準：{db['random_baseline'] * 100:.1f}%",
              f"- **{'✅ CI 下界高於隨機基準 → 偏好主流解讀成立' if db['exceeds_random'] else '未超過隨機基準（CI 涵蓋之），尚不足以支持'}**",
              "",
              "選中義項的頻率排名分布：" +
              "　".join(f"第{k}名 {v}" for k, v in db["rank_hist"].items()), ""]
    else:
        L += ["（無可分析的錯誤題目）", ""]

    # ── (b2) A/B 位置效應 ──
    pe = position_effect(outcomes)
    if pe.get("available"):
        la, ha = wilson_ci(sum(1 for o in outcomes
                               if o.gold_first and o.correct), pe["n_gold_a"])
        lb, hb = wilson_ci(sum(1 for o in outcomes
                               if o.gold_first is False and o.correct),
                           pe["n_gold_b"])
        L += ["---", "", "## (b2) A/B 位置效應 ⭐ 折進噪音估計", "",
              "> 二元強迫選擇會有位置啟發式。gold 的位置在**分層內逐題交替**"
              "（不是雜湊），",
              "> 所以**點估計不受影響**——但變異數還是進來了：受位置驅動的判定",
              "> 與譯文內容無關，那就是雜訊。", "",
              f"- judge 選 A：{pe['chose_a']}/{pe['n']} = {pe['chose_a_rate']:.3f}"
              f"　95% CI [{pe['chose_a_ci'][0]:.3f}, {pe['chose_a_ci'][1]:.3f}]"
              f"　{'🔴 有偏誤' if pe['chose_a_biased'] else '✅ 涵蓋 0.5'}", "",
              "| gold 的位置 | n | 正確率 | 95% CI |",
              "| :-: | :-: | :-: | :-: |",
              f"| A | {pe['n_gold_a']} | {pe['acc_gold_a']:.3f} | "
              f"[{la:.3f}, {ha:.3f}] |",
              f"| B | {pe['n_gold_b']} | {pe['acc_gold_b']:.3f} | "
              f"[{lb:.3f}, {hb:.3f}] |", "",
              f"兩位置之差 **{pe['diff'] * 100:+.2f}pp**"
              f"　SE {pe['se'] * 100:.2f}pp　z={pe['z']:.2f}　p={pe['p']:.4f}"
              f"　95% CI [{pe['diff_ci'][0] * 100:+.1f}, "
              f"{pe['diff_ci'][1] * 100:+.1f}]pp", "",
              f"**{'邊緣顯著' if 0.05 <= pe['p'] < 0.10 else ('顯著' if pe['p'] < 0.05 else '不顯著')}"
              "——報告但不過度解讀。**", "",
              "### 換算成標籤噪音", "",
              "設 judge 以機率 *q* 直接依位置作答（不看內容），其餘依內容判斷：", "",
              "```",
              "gold 在 A：正確率 = q·1 + (1−q)·a",
              "gold 在 B：正確率 = q·0 + (1−q)·a",
              "兩者之差 = q",
              "```", "",
              f"配平下位置驅動的判定有一半落在錯的那邊，故它對標籤錯誤率的貢獻是 "
              f"**q/2 = {pe['implied_noise'] * 100:.1f}pp**"
              f"（95% CI [{pe['implied_noise_ci'][0] * 100:.1f}, "
              f"{pe['implied_noise_ci'][1] * 100:.1f}]pp）。", "",
              "⚠️ 配平使**點估計**不受影響，但位置效應**計入 judge 不可靠度**。",
              "這是 judge 噪音的**下界**——內容判斷本身還會再錯。",
              "在人工驗證回來之前，它是唯一有實證基礎的噪音估計，",
              "已餵給 `auc.required_auc(noise=…)`（見 `signals_all.md`）。", ""]

    # ── (c) 長度稽核 ──
    recs = [{"probe_span": o.sentence, "context_length": 0,
             "full_input": o.sentence, "is_wrong": o.correct is False,
             "ambiguity_type": o.stratum, "target_word": o.word}
            for o in outcomes if o.correct is not None]
    L += ["---", "", "## (c) 長度稽核", "",
          "> 問「答錯的題目句子是否較長」。分層報告——聚合值會正負相消",
          "> （CHA-Gen 18 組中 12 組顯著、方向相反，中位數卻是 0.490）。",
          "> 此處 `ambiguity_type` 欄位承載的是 stratum。", ""]
    audit_rows = audit_predicts_error(recs, strata=("ambiguity_type", "target_word"))
    L += [format_report(audit_rows).split("\n", 5)[-1] if audit_rows
          else "（樣本不足，無法計算）", ""]

    L += ["---", "", "## 逐筆（請掃一遍判斷 judge 合不合理）", "",
          "| # | 詞 | 原句 | 譯文 | judge 選的 | gold | 對 |",
          "| :-: | :-: | --- | --- | --- | --- | :-: |"]
    defs_all: dict[str, str] = {}
    for it in picked:
        for sn in it["competing_senses"]:
            defs_all[sn["sense_id"]] = sn["definition"]
    for i, o in enumerate(outcomes, 1):
        if o.translation_failed:
            mark, tr, ch = "🔴譯", o.translation[:40] + "…", "—"
        elif o.error:
            mark, tr, ch = "🔴錯", o.error[:40], "—"
        else:
            mark = "✅" if o.correct else ("—" if o.is_none else "❌")
            tr = o.translation[:52]
            ch = f"`{o.chosen}`"
        L.append(f"| {i} | {o.word} | {o.sentence[:26]} | {tr} | {ch} | "
                 f"`{o.gold}` | {mark} |")

    L += ["", "### 錯誤與 NONE 的細節", ""]
    for i, o in enumerate(outcomes, 1):
        if o.correct is False or o.is_none:
            L += [f"**{i}. {o.word}**　`{o.probe_id}`　[{o.stratum}]",
                  f"- 原句：{o.sentence}",
                  f"- 譯文：{o.translation}",
                  f"- judge 選：`{o.chosen}` {defs_all.get(o.chosen, '（NONE）')}"
                  f"　信心 {o.confidence:.2f}　依據：{o.reasoning}",
                  f"- gold：`{o.gold}` {defs_all.get(o.gold, '')}", ""]

    rs = run.summary()
    L += ["---", "",
          f"成本：{rs['calls']} 次呼叫 / {rs['total_tokens']:,} tokens / "
          f"{rs['wall_s']}s / 快取命中 {rs['cache_hits']}",
          f"run: `{rs['path']}`"]

    RESULTS.mkdir(parents=True, exist_ok=True)
    suffix = f"_{args.judge_profile}" if args.judge_profile else ""
    out = (pathlib.Path(args.out) if args.out
           else RESULTS / f"wsd_pilot{len(outcomes)}{suffix}.md")
    out.write_text("\n".join(L), encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(
        {"n": n, "accuracy": s.accuracy, "n_correct": s.n_correct,
         "n_judgeable": s.n_judgeable, "translation_failed": s.n_translation_failed,
         "none": s.n_none, "error": s.n_error, "by_stratum": s.by_stratum,
         "diff": diff, "diff_ci": list(dci), "p": dp, "aborted": aborted,
         "judge_model": f"{jspec.provider}/{jspec.model}",
         "translate_model": f"{tspec.provider}/{tspec.model}",
         "judge_profile": args.judge_profile or "(default)",
         "judge_cross_behavioural": (
             None if cross is None else
             {"is_cross": cross.is_cross, "names_differ": cross.names_differ,
              "cuts_identical": cross.cuts_identical,
              "subject_cuts": list(cross.subject_cuts),
              "judge_cuts": list(cross.judge_cuts)}),
         "none_breakdown": nb, "dominant_bias": db,
         "position_effect": pe,
         # 逐筆結果必須持久化——否則任何事後分析都得重跑，而重跑的
         # 快取命中不保證（模型端可能改版）。
         "items": [
             {"probe_id": o.probe_id, "word": o.word, "pos": o.pos,
              "stratum": o.stratum, "sentence": o.sentence,
              "translation": o.translation, "chosen": o.chosen, "gold": o.gold,
              "correct": o.correct, "is_none": o.is_none,
              "none_rendered": o.none_rendered, "none_evidence": o.none_evidence,
              "confidence": o.confidence, "reasoning": o.reasoning,
              "chosen_rank": o.chosen_rank, "n_candidates": o.n_candidates,
              "gold_rank": o.gold_rank,
              "distractor": o.distractor, "distractor_rank": o.distractor_rank,
              "gold_first": o.gold_first, "raw_choice": o.raw_choice,
              "translation_failed": o.translation_failed, "error": o.error}
             for o in outcomes],
         "length_audit_significant": [
             {"stratum": r.stratum, "feature": r.feature, "auc": r.auc,
              "ci": list(r.ci), "direction": r.direction}
             for r in audit_rows if r.excludes_half]},
        ensure_ascii=False, indent=2, default=float), encoding="utf-8")

    print("=" * 62)
    print(f"translation_failed {pct(s.n_translation_failed, n)}　"
          f"NONE {pct(s.n_none, n)}　error {pct(s.n_error, n)}")
    print(f"可判定 {pct(s.n_judgeable, n)}　正確率 {s.accuracy:.3f} "
          f"{ci_str(*wilson_ci(s.n_correct, s.n_judgeable))}")
    for st in ("dominant", "non_dominant"):
        d = s.by_stratum[st]
        print(f"  {st:14} n={d['n']:3} 正確率 {d['acc']:.3f} {ci_str(*d['ci'])}")
    print(f"兩層之差 {diff * 100:+.1f}pp  CI [{dci[0]*100:+.1f}, {dci[1]*100:+.1f}]pp")
    print("\n停止判準：" + ("；".join(stops) if stops else "✅ 全部未觸發"))
    print(f"\n{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
