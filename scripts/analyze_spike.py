"""spike 數據的統計重算（技術設計文件 §8.6）。

補上先前缺的東西：
  1. 三個欄位的 2×2 列聯表與原始次數 —— 百分比不附分母無法判讀
  2. per-repeat AUC 的 mean ± range —— 不必重跑就能給變異
  3. Hanley–McNeil 95% CI —— n=15 下 AUC 0.84 的區間有多寬
  4. DeLong 配對檢定 —— 0.840 vs 0.550 是同一批句子上的相關比較，不能用獨立檢定

用法：
    python scripts/analyze_spike.py
"""

from __future__ import annotations

import collections
import json
import math
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "spike"
FIELDS = ["agent", "tense", "register", "social_relation", "speaker_intent"]


# ─────────────────── 統計工具 ───────────────────

def auc_from(pos: list[float], neg: list[float]) -> float:
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def hanley_mcneil(a: float, n1: int, n2: int) -> tuple[float, float, float]:
    q1 = a / (2 - a)
    q2 = 2 * a * a / (1 + a)
    var = (a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2)
    se = math.sqrt(max(var, 0.0))
    return se, max(0.0, a - 1.96 * se), min(1.0, a + 1.96 * se)


def _placements(pos: list[float], neg: list[float]) -> tuple[list[float], list[float]]:
    v10 = [sum((p > n) + 0.5 * (p == n) for n in neg) / len(neg) for p in pos]
    v01 = [sum((p > n) + 0.5 * (p == n) for p in pos) / len(pos) for n in neg]
    return v10, v01


def _cov(x: list[float], y: list[float]) -> float:
    if len(x) < 2:
        return 0.0
    mx, my = statistics.mean(x), statistics.mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (len(x) - 1)


def delong(pos_a, neg_a, pos_b, neg_b) -> dict:
    """兩個相關 AUC 的 DeLong 檢定。兩者須來自同一批樣本（順序一致）。"""
    a1, a2 = auc_from(pos_a, neg_a), auc_from(pos_b, neg_b)
    v10_1, v01_1 = _placements(pos_a, neg_a)
    v10_2, v01_2 = _placements(pos_b, neg_b)
    n1, n2 = len(pos_a), len(neg_a)
    s10 = [[_cov(v10_1, v10_1), _cov(v10_1, v10_2)], [_cov(v10_2, v10_1), _cov(v10_2, v10_2)]]
    s01 = [[_cov(v01_1, v01_1), _cov(v01_1, v01_2)], [_cov(v01_2, v01_1), _cov(v01_2, v01_2)]]
    s = [[s10[i][j] / n1 + s01[i][j] / n2 for j in range(2)] for i in range(2)]
    var = s[0][0] + s[1][1] - 2 * s[0][1]
    if var <= 0:
        return {"auc_a": a1, "auc_b": a2, "diff": a1 - a2, "z": None, "p": None,
                "note": "變異數非正，樣本過小"}
    z = (a1 - a2) / math.sqrt(var)
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return {"auc_a": a1, "auc_b": a2, "diff": a1 - a2, "z": z, "p": p}


# ─────────────────── 1. 列聯表 ───────────────────

def contingency() -> None:
    d = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    rec = collections.defaultdict(lambda: [0, 0])
    fp = collections.defaultdict(lambda: [0, 0])
    for r in d["raw"]:
        for x in r["t1_t2"]:
            if not x.get("schema_ok"):
                continue
            if x["group"] == "ambiguous" and "marked_unknown" in x:
                f = x["undeterminable_field"]
                rec[f][0] += x["marked_unknown"]
                rec[f][1] += 1
            if x["group"] == "control":
                m = set(x.get("unknown_marks", []))
                for f in FIELDS:
                    fp[f][0] += f in m
                    fp[f][1] += 1

    print("=" * 78)
    print("1. UNKNOWN 標記的 2×2 列聯表（六模型 × 3 重複合計，原始次數）")
    print("=" * 78)
    for f in FIELDS:
        tp, n_und = rec[f]
        fpn, n_det = fp[f]
        if n_und == 0 and n_det == 0:
            continue
        fn, tn = n_und - tp, n_det - fpn
        print(f"\n  【{f}】")
        print(f"    {'':22}{'標 UNKNOWN':>12}{'未標':>10}{'合計':>8}")
        if n_und:
            print(f"    {'真的無從判定':22}{tp:>12}{fn:>10}{n_und:>8}   ← recall = {tp}/{n_und} = {tp/n_und*100:.1f}%")
        else:
            print(f"    {'真的無從判定':22}{'—':>12}{'—':>10}{0:>8}   ← spike 句集無此類")
        print(f"    {'原文可判定（對照句）':22}{fpn:>12}{tn:>10}{n_det:>8}   ← FP = {fpn}/{n_det} = {fpn/n_det*100:.1f}%")
        if n_und:
            disc = tp / n_und - fpn / n_det
            prec = tp / (tp + fpn) if (tp + fpn) else 0
            print(f"    判別力 = {disc*100:+.1f}pp    precision = {tp}/{tp+fpn} = {prec*100:.1f}%")
            if n_und < 30 or tp < 5:
                print(f"    ⚠️ 樣本過小（tp={tp}），結論不穩固")
    print("\n  ⚠️ 對照句按「語意不歧義」挑選，未逐欄位標註可判定性。")
    print("     social_relation 在無受話者的句子中本就無從判定 → 其 FP 列無效。")
    print("     須以新 schema 的 field_determinable 重標後才能定論。")


# ─────────────────── 2–4. S0b 的 AUC ───────────────────

def s0b_auc() -> None:
    p = DATA / "results_s0b.json"
    if not p.exists():
        print("\n（找不到 results_s0b.json，略過）")
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    runs, s5 = d["runs"], d["s5"]
    variants = ["V1_biencoder_pair", "V2_biencoder_vs_src", "V3_crossencoder", "V4_llm_intent_same"]

    print("\n" + "=" * 78)
    print("2–3. per-repeat AUC 與 Hanley–McNeil 95% CI")
    print("=" * 78)
    print(f"{'量測':28}{'AUC':>7}{'range':>14}{'SE':>7}{'95% CI':>18}")
    print("-" * 78)

    def oriented(rs, v):
        """統一方向：分數愈高愈歧義。一致性類需取負號。"""
        amb = [-r[v] for r in rs if r["group"] == "ambiguous" and v in r]
        ctl = [-r[v] for r in rs if r["group"] == "control" and v in r]
        return amb, ctl

    rows = {}
    for v in variants:
        aucs = []
        for rs in runs:
            amb, ctl = oriented(rs, v)
            if amb and ctl:
                aucs.append(auc_from(amb, ctl))
        if not aucs:
            continue
        m = statistics.mean(aucs)
        se, lo, hi = hanley_mcneil(m, 10, 5)
        rows[v] = m
        rng = f"{min(aucs):.2f}–{max(aucs):.2f}"
        print(f"{v:28}{m:7.3f}{rng:>14}{se:7.3f}{f'[{lo:.2f}, {hi:.2f}]':>18}")

    for model in sorted({r["model"] for r in s5}):
        aucs = []
        for run in [r for r in s5 if r["model"] == model]:
            amb = [x["score"] for x in run["rows"] if x["group"] == "ambiguous" and x["score"] is not None]
            ctl = [x["score"] for x in run["rows"] if x["group"] == "control" and x["score"] is not None]
            if amb and ctl:
                aucs.append(auc_from(amb, ctl))
        if not aucs:
            continue
        m = statistics.mean(aucs)
        se, lo, hi = hanley_mcneil(m, 10, 5)
        rows[f"S5_{model}"] = m
        rng = f"{min(aucs):.2f}–{max(aucs):.2f}"
        print(f"{'S5_direct_' + model:28}{m:7.3f}{rng:>14}{se:7.3f}{f'[{lo:.2f}, {hi:.2f}]':>18}")

    print("\n  ⚠️ n=10 vs 5，CI 寬達 ±0.15 以上。AUC 0.84 與 0.55 的區間可能重疊，")
    print("     單看點估計會高估證據強度。")

    # DeLong：V2 vs S5，同一批句子
    print("\n" + "=" * 78)
    print("4. DeLong 配對檢定：V2（跨語言回譯）vs S5（直接詢問）")
    print("=" * 78)
    rs = runs[0]
    ids = [r["id"] for r in rs if "V2_biencoder_vs_src" in r]
    s5_first = [r for r in s5 if r["repeat"] == 0 and r["model"] == "mistral-small-4"]
    if not s5_first:
        print("  找不到對應的 S5 執行，略過")
        return
    s5_map = {x["id"]: x["score"] for x in s5_first[0]["rows"]}
    v2_map = {r["id"]: -r["V2_biencoder_vs_src"] for r in rs if "V2_biencoder_vs_src" in r}
    grp = {r["id"]: r["group"] for r in rs}
    common = [i for i in ids if i in s5_map and s5_map[i] is not None]
    pa = [v2_map[i] for i in common if grp[i] == "ambiguous"]
    na = [v2_map[i] for i in common if grp[i] == "control"]
    pb = [s5_map[i] for i in common if grp[i] == "ambiguous"]
    nb = [s5_map[i] for i in common if grp[i] == "control"]
    res = delong(pa, na, pb, nb)
    print(f"  V2 AUC = {res['auc_a']:.3f}   S5 AUC = {res['auc_b']:.3f}   差 = {res['diff']:+.3f}")
    if res["z"] is None:
        print(f"  {res['note']}")
    else:
        print(f"  z = {res['z']:.3f}   p = {res['p']:.4f}   "
              f"{'✅ 達 0.05 顯著' if res['p'] < 0.05 else '❌ 未達顯著 —— 目前不能宣稱行為訊號優於自陳訊號'}")
    print(f"  （n={len(pa)} vs {len(na)}，僅第 1 次執行；正式數據須在 dev-30 上重跑）")


if __name__ == "__main__":
    contingency()
    s0b_auc()
