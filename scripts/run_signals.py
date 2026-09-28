"""計算 S1–S8 全部訊號，並（在閘門開啟後）產出 AUC 表。

v3 架構書 §P4 的 DoD：一張表 = 八個訊號 × (AUC, SE, 95% CI, 平均成本)，
加一列未加權總和，**加一列長度基準對照**。

## ⚠️ AUC 閘門

`--auc` 需要一份**未受污染**的 judge 驗證（`contaminated: false` 且
`judge_vs_human >= 0.85`），條件寫在 `eval/gate.py` 的 `check_auc_gate()`。
理由：AUC 的標籤來自 sense_judge，標籤有噪音時 AUC 會被壓向 0.5，
「訊號無效」與「標籤太吵」在數字上長得一模一樣，事後分不開。

2026-08-22 起閘門開啟——`judge_validation_r2.json` 的一致率 85%（n=20，
題目與第一輪不重疊、未出現在任何 prompt 的 few-shot 中）。
第一輪的 p1／p2 兩份維持 `contaminated: true`，不採用。

用法：
    python scripts/run_signals.py --n 400              # 只算訊號值
    python scripts/run_signals.py --n 400 --rules-only # 不呼叫 API
    python scripts/run_signals.py --auc                # 閘門開啟後
"""

from __future__ import annotations

import argparse
import json
import pathlib
import math
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import yaml  # noqa: E402

from cognitive_core.eval.auc import (  # noqa: E402
    delong_test,
    evaluate,
    permutation_p,
    required_auc,
    unweighted_sum,
)
from cognitive_core.eval.gate import (  # noqa: E402
    GATE_EXPLANATION,
    check_auc_gate,
)
from cognitive_core.eval.noise import (  # noqa: E402
    ceiling_correct,
    compose_noise,
    decompose,
    holm,
)
from cognitive_core.llm import Client  # noqa: E402
from cognitive_core.router.signals import (  # noqa: E402
    RULE_SIGNALS,
    llm_signals,
    raw_length,
)
from cognitive_core.runlog import RunLog  # noqa: E402

RESULTS = ROOT / "data" / "results"
PROBES = ROOT / "data" / "probes" / "wsd_probes.yaml"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--rules-only", action="store_true", help="只算 S1–S4，不呼叫 API")
    ap.add_argument("--auc", action="store_true", help="產出 AUC 表（有閘門）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--reuse", action="store_true",
                    help="直接讀既有的 signals_all.json，不重算訊號值。"
                         "只改表格排版或統計時用，省下 12 分鐘的 API 往返")
    args = ap.parse_args()

    if args.auc:
        ok, why = check_auc_gate(RESULTS)
        if not ok:
            print(f"🔴 AUC 閘門未開：{why}\n", file=sys.stderr)
            print(GATE_EXPLANATION, file=sys.stderr)
            return 2
        print(f"✅ AUC 閘門開啟：{why}")

    items = yaml.safe_load(PROBES.read_text(encoding="utf-8"))["items"][:args.n]
    print(f"{len(items)} 筆探針")

    run = RunLog("signals", meta={"n": len(items), "rules_only": args.rules_only})
    client = None if args.rules_only else Client(run=run)
    sigs = list(RULE_SIGNALS) + ([] if client is None else llm_signals(client))
    print("訊號：" + "　".join(s.name for s in sigs) + "\n")

    rows = []
    if args.reuse:
        cached = json.loads((RESULTS / "signals_all.json").read_text(encoding="utf-8"))
        rows = cached["items"]
        names_cached = cached["signals"]
        if names_cached != [s.name for s in sigs]:
            print(f"🔴 快取的訊號組合與現在不同：{names_cached}", file=sys.stderr)
            return 1
        print(f"  重用既有訊號值 {len(rows)} 筆（未重算）")
    t0 = time.monotonic()
    for i, it in enumerate([] if args.reuse else items, 1):
        text = it["sentence"]
        rec = {"probe_id": it["id"], "word": it["target_word"],
               "stratum": it["stratum"], "sentence": text,
               "raw_length": raw_length(text), "signals": {}}
        for s in sigs:
            r = s.compute(text)
            rec["signals"][s.name] = {"score": r.score, "detail": r.detail}
        rows.append(rec)
        if i % 20 == 0 or i == len(items):
            print(f"  [{i}/{len(items)}] {time.monotonic() - t0:.0f}s", flush=True)

    names = [s.name for s in sigs]
    vals = {n: [r["signals"][n]["score"] for r in rows] for n in names}
    lens = [r["raw_length"] for r in rows]

    L = [f"# 訊號值　n={len(rows)}", "",
         "> ⚠️ 這份只有訊號的**分布**，沒有 AUC。AUC 的閘門見 "
         "`scripts/run_signals.py` 的 `check_auc_gate()`。", "",
         "| 訊號 | 平均 | 中位數 | 標準差 | 非零 | 與純句長的 r |",
         "| --- | :-: | :-: | :-: | :-: | :-: |"]
    for n in names:
        v = vals[n]
        nz = sum(1 for x in v if x > 0)
        sd = statistics.pstdev(v) if len(v) > 1 else 0.0
        try:
            r = statistics.correlation(v, lens) if sd > 0 else float("nan")
        except statistics.StatisticsError:
            r = float("nan")
        flag = "　🔴 與句長高度重疊" if r == r and abs(r) > 0.7 else ""
        L.append(f"| {n} | {statistics.mean(v):.3f} | {statistics.median(v):.3f} | "
                 f"{sd:.3f} | {nz}/{len(v)} | {r:+.3f}{flag} |")

    need, L2 = _power_section(len(rows))
    L += L2

    # ── 並列造成的 AUC 上限 ⭐ ──
    L += ["## 並列造成的 AUC 上限", "",
          "AUC 只看排序，**分數相同的兩題只能貢獻 0.5**。",
          "所以一個訊號若把大量題目給成同一個值，它的 AUC 就有一個",
          "與判別力無關的天花板：`上限 = 1 − 0.5 × P(隨機兩題同值)`。", "",
          "這個診斷不需要標籤，因此不受 AUC 閘門限制——而且**必須先看**：",
          "上限低於上表門檻的訊號，再怎麼有效也測不出顯著，",
          "報告時不能寫成「該訊號無預測力」。", "",
          "| 訊號 | 相異值 | 最大同值佔比 | 隨機兩題同值 | AUC 上限 | vs 門檻 |",
          "| --- | :-: | :-: | :-: | :-: | :-: |"]

    def ceiling(v: list[float]) -> tuple[int, float, float, float]:
        import collections
        c = collections.Counter(round(x, 9) for x in v)
        m = len(v)
        tie = (sum(k * (k - 1) for k in c.values()) / (m * (m - 1))) if m > 1 else 0.0
        return len(c), max(c.values()) / m, tie, 1 - 0.5 * tie

    thr = need["primary"]
    clean = need.get(0.0, thr)
    dead = []
    for n, v in list(vals.items()) + [("raw_length（基準）", lens)]:
        k, mx, tie, cap = ceiling(v)
        if cap < clean:
            verdict, tag = "🔴 即使標籤全乾淨也不可能顯著", "dead"
        elif cap < thr:
            verdict, tag = "🚫 低於現行門檻 → **不可檢定**", "untestable"
        else:
            verdict, tag = "—", "ok"
        if tag != "ok" and not n.startswith("raw"):
            dead.append((n, cap, tag))
        L.append(f"| {n} | {k} | {mx:.0%} | {tie:.0%} | **{cap:.3f}** | {verdict} |")
    L += ["", f"（現行門檻 required_auc = {thr:.3f}，噪音 "
              f"{need['primary_noise']:.1%}；標籤全乾淨時為 {clean:.3f}）"]
    if dead:
        L += ["", "**受並列拖累的訊號**——這些標為「不可檢定」，"
                  "與「不顯著」意義完全不同："]
        for n, cap, tag in dead:
            L.append(f"- `{n}`：上限 {cap:.3f} < 門檻 {thr:.3f}"
                     + ("　🔴 即使標籤完全乾淨也不可能顯著" if tag == "dead" else ""))
    L.append("")

    if args.auc:
        prereg = json.loads(
            (RESULTS / "signal_preregistration.json").read_text(encoding="utf-8")
        )["signals"]
        sec, entries, base_res, sum_res = _auc_section(
            rows, names, vals, lens, need, prereg)
        L += sec
    else:
        ok, why = check_auc_gate(RESULTS)
        L += ["---", "", "## AUC", "",
              f"🔴 **未計算**（未加 `--auc`）。閘門狀態："
              f"{'✅ 可開啟' if ok else '關閉'}——{why}", ""]

    # 每題成本（§P4 DoD 要求）。RunLog 只有角色不分訊號，S6 與 S8 都走
    # translate 角色無法從日誌切開，故以呼叫結構分析式列出。
    L += ["## 每題成本", "",
          "| 訊號 | 生成呼叫 | 嵌入呼叫 | 備註 |", "| --- | :-: | :-: | --- |",
          "| S1–S4 | 0 | 0 | 純規則 |",
          "| S5_llm_direct | 1 | 0 | 單次，輸出 1 個數字 |",
          "| S6_roundtrip | 2 | 1（2 段文字） | 翻譯 + 回譯 |",
          "| S7_n_readings | 1 | 0 | reflect，輸出較長 |",
          "| S8_semantic_entropy | 1（`n=8`） | 1（8 段文字） | 取樣成本在補全端 |", ""]

    rs = run.summary() if client else {"calls": 0, "total_tokens": 0, "cache_hits": 0}
    L += ["---", ""]
    if args.reuse:
        L += ["本次以 `--reuse` 執行——訊號值取自既有的 `signals_all.json`，"
              "未重新呼叫 API。",
              "成本數字請見未加 `--reuse` 的那一次執行。"]
    else:
        L += [f"實測：{rs['calls']} 次呼叫 / {rs['total_tokens']:,} tokens / "
              f"快取命中 {rs['cache_hits']}",
              f"每題平均 {rs['calls'] / max(len(rows), 1):.1f} 次生成呼叫、"
              f"{rs['total_tokens'] / max(len(rows), 1):,.0f} tokens"]

    out = pathlib.Path(args.out) if args.out else RESULTS / "signals_all.md"
    out.write_text("\n".join(L), encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(
        {"n": len(rows), "signals": names, "auc_computed": bool(args.auc),
         "items": rows}, ensure_ascii=False, indent=1, default=float),
        encoding="utf-8")

    print("\n" + "=" * 62)
    for n in names:
        v = vals[n]
        print(f"  {n:<26} 平均 {statistics.mean(v):.3f}　"
              f"非零 {sum(1 for x in v if x > 0)}/{len(v)}")
    print(f"\n  {out}")
    return 0


def _power_section(n_items: int) -> tuple[dict, list[str]]:
    """事前檢定力 + 誤差分解 + 天花板校正。全部改用實測值。"""
    pe, val = {}, {}
    base = RESULTS / "wsd_baseline400.json"
    if base.exists():
        b = json.loads(base.read_text(encoding="utf-8"))
        pe = b.get("position_effect") or {}
    vf = RESULTS / "judge_validation_r2.json"
    if vf.exists():
        val = json.loads(vf.read_text(encoding="utf-8"))

    pos_noise = pe.get("implied_noise") or 0.0
    nv = val.get("n", 0)
    jh = val.get("judge_vs_human")
    ne = compose_noise(n_agree=round((jh or 0) * nv), n_total=nv,
                       position_noise=pos_noise) if nv else None

    n_pos = round(n_items * 0.296)
    n_neg = n_items - n_pos
    primary = ne.total if ne else 0.10

    L = ["", "## 標籤噪音　實測", "",
         "⚠️ **位置效應與內容誤差不是相加的。**",
         f"「judge vs 人工 = {(1 - primary):.0%}」量的是 judge 的**總**錯誤率——",
         f"位置驅動的判定與人工不一致時，早就算在那 {primary:.0%} 裡了。",
         f"把 {pos_noise * 100:.1f}pp 再加上去是重複計算。正確關係是**分解**：", ""]
    if ne:
        L += ["```",
              f"judge 總錯誤 {ne.total:.1%}"
              f"　（1 − judge/人工一致率，n={ne.n_agreement}）",
              f"  ├── ≥{ne.position_component:.1%}  位置啟發式（n=399 量得，精度高）",
              f"  └── ≈{ne.content_component:.1%}  內容誤判（殘差）",
              "```", "",
              f"若誤把兩者相加會得到 {ne.additive_would_be:.1%}——那是重複計算。", ""]
        if ne.shared_position_bias:
            L += [f"🔴 {ne.note}", ""]
        else:
            L += ["✅ 人工與 judge 的選 A 率皆為 10/20，無共同位置偏誤，"
                  "故 total 未低估。", ""]

    L += ["## 事前檢定力", "",
          "在目前的樣本數下，訊號的**真實** AUC 要多大才能讓 95% CI 排除 0.5：", "",
          "| 標籤噪音 | 來源 | 需要的真實 AUC |", "| :-: | --- | :-: |"]
    cand = [(0.0, "假想的完美標籤（不成立，僅作對照）"),
            (pos_noise, "位置效應（噪音的下界）")]
    if ne:
        cand += [(ne.total, "**judge vs 人工，實測點估計**"),
                 (ne.total_ci[1], "同上的 CI 上界（保守）")]
    need = {}
    for noise, src in cand:
        if noise is None or noise >= 0.5:
            continue
        v = required_auc(n_pos, n_neg, noise=noise)
        need[round(noise, 4)] = v
        shown = "**無法偵測**（噪音已高到任何真實 AUC 都測不出）" if v != v             else f"{v:.3f}"
        L.append(f"| {noise:.1%} | {src} | {shown} |")
    need["primary"] = required_auc(n_pos, n_neg, noise=primary)
    need["primary_noise"] = primary
    L += ["", f"（正類 {n_pos} 筆／負類 {n_neg} 筆，依 400 筆二元基準的錯誤率 29.6%。）",
          "", f"**採用 {primary:.1%} 為主要門檻 → required_auc = "
              f"{need['primary']:.3f}**", ""]

    # ── 誤差分解 ──
    if val.get("human_vs_gold") is not None:
        dec = decompose(judge_vs_human=val["judge_vs_human"],
                        human_vs_gold=val["human_vs_gold"],
                        judge_vs_gold=val["judge_vs_gold"], n=nv)
        L += ["## 誤差分解　報告材料", "",
              "| 段落 | 落差 | 歸因 |", "| --- | :-: | --- |",
              f"| CWN gold → 人工 | {dec.gold_to_human:.0%} | "
              "跨語言判定的固有限制（標註者看英譯，CWN 標的是中文原句）|",
              f"| 人工 → judge | {dec.human_to_judge:.0%} | 機器誤差 |",
              f"| **gold → judge** | **{dec.gold_to_judge:.0%}** | 兩者疊加 |", "",
              f"judge 對 gold 的 {dec.gold_to_judge:.0%} 落差中，"
              f"約 **{dec.task_share:.0%} 來自任務本身**、"
              f"**{dec.model_share:.0%} 是模型問題**。", "",
              f"（兩段相加 {dec.gold_to_human + dec.human_to_judge:.0%} "
              f"高於實際的 {dec.gold_to_judge:.0%}，差 {dec.superadditive:+.0%}"
              "——部分誤差互相抵銷，judge 的錯有時剛好回到 gold。"
              f"n={nv}，此差值不可過度解讀。）", ""]

    # ── 天花板校正 ──
    amb = val.get("both_plausible_rate")
    if amb is not None and base.exists():
        acc = json.loads(base.read_text(encoding="utf-8"))["accuracy"]
        cc = ceiling_correct(acc, n_ambiguous=round(amb * nv), n_annotated=nv)
        L += ["## 主指標的天花板校正 ⭐", "",
              f"盲標第二欄顯示 **{cc.ambiguous_rate:.0%}** 的題目"
              f"「兩個都說得通」（{round(amb * nv)}/{nv}，"
              f"95% CI [{cc.ambiguous_ci[0]:.0%}, {cc.ambiguous_ci[1]:.0%}]）。",
              "那些題目上任何評判者都只能猜，期望正確率 0.5，故", "",
              "```",
              "觀測正確率 = (1−a)·θ + a·0.5      a = 不可判定的比例",
              "```", "",
              "| 指標 | 值 | 分母 |", "| --- | :-: | --- |",
              f"| 觀測錯誤率 | **{cc.err_observed:.1%}** | 全部可判定題目 |",
              f"| 任務天花板 | {cc.ceiling:.0%} | — |",
              f"| 校正後模型錯誤 | **{cc.err_of_all_items:.1%}** | 全部題目 |",
              f"| 校正後模型錯誤 | {cc.err_of_decidable:.1%} | 僅可判定題目 |", "",
              "⚠️ **兩個分母都列出來，因為兩個都對但意思不同。**",
              f"{cc.err_of_all_items:.1%} 是「每 100 題有幾題是模型的錯」；",
              f"{cc.err_of_decidable:.1%} 是「在題目本身有唯一答案時模型錯多少」。", "",
              f"⚠️ **a 由 n={nv} 估得，CI 很寬**，校正後的區間是：",
              f"- 佔全部題目：[{cc.err_of_all_ci[0]:.1%}, {cc.err_of_all_ci[1]:.1%}]",
              f"- 佔可判定題目：[{cc.err_of_decidable_ci[0]:.1%}, "
              f"{cc.err_of_decidable_ci[1]:.1%}]", "",
              "**未校正與校正後的數字都要報，不可只報校正後的。**", ""]
    return need, L


N_PERM = 4000

COST = {"S1_polysemy": "0", "S2_subject_ellipsis": "0",
        "S3_syntactic_complexity": "0", "S4_cultural": "0",
        "S5_llm_direct": "1 生成", "S6_roundtrip": "2 生成 + 1 嵌入",
        "S7_n_readings": "1 生成", "S8_semantic_entropy": "1 生成(n=8) + 1 嵌入"}


def _load_labels() -> dict[str, bool]:
    """probe_id → 模型是否選錯義項（正類）。來自 400 筆二元基準。"""
    f = RESULTS / "wsd_baseline400.json"
    if not f.exists():
        return {}
    d = json.loads(f.read_text(encoding="utf-8"))
    return {it["probe_id"]: (it["correct"] is False)
            for it in d.get("items", []) if it.get("correct") is not None}


def _auc_section(rows, names, vals, lens, need, prereg) -> list[str]:
    """只有閘門開啟時才會走到這裡。RQ1 的答案。"""
    labels_by_id = _load_labels()
    keep = [i for i, r in enumerate(rows) if r["probe_id"] in labels_by_id]
    if not keep:
        return ["", "🔴 找不到可對應的標籤，無法算 AUC。", ""]
    y = [labels_by_id[rows[i]["probe_id"]] for i in keep]
    pos_idx = [k for k, v in zip(keep, y) if v]
    neg_idx = [k for k, v in zip(keep, y) if not v]

    def split(v):
        return [v[i] for i in pos_idx], [v[i] for i in neg_idx]

    n_pos, n_neg = len(pos_idx), len(neg_idx)
    thr = need["primary"]
    ceil_by = {r["signal"]: r["auc_ceiling"] for r in prereg}
    act_by = {r["signal"]: r.get("action") for r in prereg}

    L = ["---", "", "## AUC ⭐ RQ1 的答案", "",
         f"> 正類＝模型選錯義項（{n_pos} 筆），負類＝選對（{n_neg} 筆）。",
         f"> 標籤來自二元強迫選擇的 judge，一致率 85%（n=20，未受污染）。",
         f"> 顯著門檻 required_auc = **{thr:.3f}**（噪音 {need['primary_noise']:.1%}）。",
         "> 訊號設計在看到本表之前已凍結，見 `signal_preregistration.md`。", ""]

    lp, ln = split(lens)
    base = evaluate(lp, ln, name="raw_length", n_perm=N_PERM)
    base_pperm = (base.p_perm if base.p_perm is not None
                  else permutation_p(lp, ln, n_perm=N_PERM, seed=17))

    entries = []
    for n in names:
        p, q = split(vals[n])
        r = evaluate(p, q, name=n, n_perm=N_PERM)
        pperm = (r.p_perm if r.p_perm is not None
                 else permutation_p(p, q, n_perm=N_PERM, seed=17))
        d = delong_test(p, q, lp, ln)
        cap = ceil_by.get(n, 1.0)
        testable = cap >= thr
        entries.append({"name": n, "res": r, "delong": d, "ceiling": cap,
                        "p_perm": pperm, "testable": testable,
                        "action": act_by.get(n)})

    # p 值：非退化用 Hanley–McNeil 反推，退化用排列檢定
    def raw_p(r) -> float:
        if r.degenerate:
            return r.p_perm if r.p_perm is not None else float("nan")
        if r.se == 0 or math.isnan(r.se):
            return float("nan")
        z = abs(r.auc - 0.5) / r.se
        return 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))

    # Holm 只在**可檢定**的訊號之間校正——不可檢定者不參與比較
    testable = [e for e in entries if e["testable"]]
    praw = [raw_p(e["res"]) for e in testable]
    padj = holm(praw)
    for e, pr, pa in zip(testable, praw, padj):
        e["p_raw"], e["p_adj"] = pr, pa
    for e in entries:
        e.setdefault("p_raw", float("nan"))
        e.setdefault("p_adj", float("nan"))

    L += [f"### 主表　（Holm 校正在 {len(testable)} 個可檢定訊號之間進行）", "",
          "| 訊號 | AUC | SE | 95% CI | 排列 p | 並列上限 | 門檻 | 未校正 | Holm p | 判定 | 成本 |",
          "| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |"]
    for e in sorted(entries, key=lambda x: -x["res"].auc):
        r = e["res"]
        if not e["testable"]:
            verdict = f"🚫 **不可檢定**（{e['action'] or '上限不足'}）"
        elif not math.isnan(e["p_adj"]) and e["p_adj"] < 0.05:
            verdict = "✅ **顯著**"
        elif r.excludes_half:
            verdict = "⚠️ 未校正顯著，校正後不顯著"
        else:
            verdict = "— 不顯著"
        pp = f"{e['p_perm']:.4f}" if e["p_perm"] == e["p_perm"] else "—"
        se_s = "—" if math.isnan(r.se) else f"{r.se:.3f}"
        adj_s = "—" if math.isnan(e["p_adj"]) else f"{e['p_adj']:.4f}"
        L.append(f"| {e['name']} | {r.auc:.3f} | {se_s} | {r.ci_text()} | "
                 f"{pp} | {e['ceiling']:.3f} | {thr:.3f} | "
                 f"{'✅' if r.excludes_half else '—'} | {adj_s} | "
                 f"{verdict} | {COST.get(e['name'], '—')} |")

    us = split(unweighted_sum(vals))
    rus = evaluate(*us, name="unweighted_sum", n_perm=N_PERM)
    rus_pperm = (rus.p_perm if rus.p_perm is not None
                 else permutation_p(*us, n_perm=N_PERM, seed=17))
    L += ["", "### 對照列 ⭐ 缺一不可", "",
          "| 對照 | AUC | SE | 95% CI | 排列 p | 說明 |",
          "| --- | :-: | :-: | :-: | :-: | --- |",
          f"| **未加權總和** | {rus.auc:.3f} | "
          f"{'—' if math.isnan(rus.se) else f'{rus.se:.3f}'} | {rus.ci_text()} | "
          f"{rus_pperm:.4f} | 合成基準。**不擬合權重**（§P4）|",
          f"| **純句長基準** | {base.auc:.3f} | "
          f"{'—' if math.isnan(base.se) else f'{base.se:.3f}'} | {base.ci_text()} | "
          f"{base_pperm:.4f} | 地雷 1：任何訊號都要跟它比 |", ""]

    # DeLong：每個訊號 vs 純句長（相關樣本）
    L += ["### vs 純句長　DeLong 檢定（相關樣本）", "",
          "> 兩個 AUC 算在同一批題目上，高度相關。用獨立雙樣本檢定會低估標準誤。",
          "> **S3 句法複雜度尤其要看這一列**——它的三個成分都隨長度成長。", "",
          "| 訊號 | AUC | 純句長 AUC | 差 | SE | z | p | 判讀 |",
          "| --- | :-: | :-: | :-: | :-: | :-: | :-: | --- |"]
    for e in sorted(entries, key=lambda x: -x["res"].auc):
        d = e["delong"]
        if math.isnan(d.p):
            note = "無法檢定"
        elif d.significant:
            note = "**優於句長**" if d.diff > 0 else "**劣於句長**"
        else:
            note = "與句長無異——不能算獨立訊號"
        L.append(f"| {e['name']} | {d.auc_a:.3f} | {d.auc_b:.3f} | "
                 f"{d.diff:+.3f} | "
                 f"{'—' if math.isnan(d.se_diff) else f'{d.se_diff:.3f}'} | "
                 f"{'—' if math.isnan(d.z) else f'{d.z:+.2f}'} | "
                 f"{'—' if math.isnan(d.p) else f'{d.p:.4f}'} | {note} |")
    L.append("")

    sig = [e for e in entries if e["testable"] and not math.isnan(e["p_adj"])
           and e["p_adj"] < 0.05]
    untestable = [e for e in entries if not e["testable"]]
    L += ["### 結論", ""]
    if sig:
        L.append(f"**Holm 校正後顯著的訊號（{len(sig)} 個）**：")
        for e in sorted(sig, key=lambda x: -x["res"].auc):
            d = e["delong"]
            extra = ("，且 DeLong 顯示優於純句長" if d.significant and d.diff > 0
                     else "，但 DeLong 顯示與純句長無異")
            L.append(f"- `{e['name']}`　AUC {e['res'].auc:.3f} "
                     f"{e['res'].ci_text()}　Holm p={e['p_adj']:.4f}{extra}")
    else:
        L.append("**沒有任何訊號在 Holm 校正後顯著。**")
    if untestable:
        L += ["", f"**不可檢定的訊號（{len(untestable)} 個）**"
                  "——並列上限低於門檻，與「不顯著」意義完全不同：", ""]
        for e in untestable:
            L.append(f"- `{e['name']}`　上限 {e['ceiling']:.3f} < 門檻 {thr:.3f}"
                     f"　（預先登記處置：{e['action'] or '未指定'}）")
    L.append("")
    return L, entries, base, rus


if __name__ == "__main__":
    sys.exit(main())
