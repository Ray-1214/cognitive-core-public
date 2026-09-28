"""外部歧義資料集的長度稽核（D1.5）。

動機：CHA-Gen（arXiv 2605.15635）以語意熵區分「歧義句 vs 非歧義句」，
Wu et al. 2025 用「歧義句 vs 消歧版」，兩者都是組間比較。若兩組在句長上
系統性不同，一個只數字數的分類器就能達到相當的 AUC——那訊號的來源就無從歸因。

⚠️ **公平陳述**：這些資料集是為各自的用途設計的（CHA-Gen 為歧義偵測與
翻譯分析、Wu et al. 為生成消歧版本）。有問題的是把它們當**偵測任務的
負例**——那是本專案的用法，不是原作者的主張。
本腳本的輸出不得寫成「該資料集有瑕疵」。

用法：
    python scripts/external_length_audit.py
"""

from __future__ import annotations

import csv
import json
import math
import pathlib
import statistics
import sys
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXT = ROOT / "external"
OUT = ROOT / "data" / "external"

PUNCT = "，。、！？；：「」『』（）…—,.!?;:()"


def auc(pos: list[float], neg: list[float]) -> float:
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def hanley_mcneil(a: float, n1: int, n2: int) -> tuple[float, float, float]:
    q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
    var = (a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2)
    se = math.sqrt(max(var, 0.0))
    return se, max(0.0, a - 1.96 * se), min(1.0, a + 1.96 * se)


FEATURES = {
    "字元長度": lambda s: float(len(s)),
    "標點總數": lambda s: float(sum(c in PUNCT for c in s)),
    "相異字元數": lambda s: float(len(set(s))),
}


@dataclass
class GroupStat:
    name: str
    n_amb: int
    n_ctl: int
    auc: float
    se: float
    ci: tuple[float, float]

    @property
    def excludes_half(self) -> bool:
        """CI 是否排除 0.5 —— 統計上是否可分。"""
        return self.ci[0] > 0.5 or self.ci[1] < 0.5

    @property
    def effect(self) -> float:
        """效應量。統計顯著與實務重要是兩回事，必須分開報。"""
        return abs(self.auc - 0.5)

    @property
    def direction(self) -> str:
        return "對照較長" if self.auc > 0.5 else ("歧義較長" if self.auc < 0.5 else "—")


@dataclass
class AuditResult:
    dataset: str
    comparison: str
    n_amb: int
    n_ctl: int
    mean_amb: float
    mean_ctl: float
    length_auc: float
    se: float
    ci: tuple[float, float]
    strategy: str
    per_group: dict[str, GroupStat] = field(default_factory=dict)
    other_features: dict[str, float] = field(default_factory=dict)

    @property
    def excludes_half(self) -> bool:
        return self.ci[0] > 0.5 or self.ci[1] < 0.5

    @property
    def effect(self) -> float:
        return abs(self.length_auc - 0.5)


def audit(dataset: str, comparison: str, amb: list[str], ctl: list[str],
          strategy: str, groups: dict[str, tuple[list[str], list[str]]] | None = None
          ) -> AuditResult:
    """對照側為正例（多數資料集的對照側較長，故正向 AUC 代表長度可分）。"""
    A = [float(len(s)) for s in amb]
    C = [float(len(s)) for s in ctl]
    a = auc(C, A)
    se, lo, hi = hanley_mcneil(a, len(A), len(C))
    other = {}
    for name, f in FEATURES.items():
        if name == "字元長度":
            continue
        other[name] = auc([f(s) for s in ctl], [f(s) for s in amb])
    per_group: dict[str, GroupStat] = {}
    for g, (ga, gc) in (groups or {}).items():
        if len(ga) >= 3 and len(gc) >= 3:
            ga_l = [float(len(s)) for s in ga]
            gc_l = [float(len(s)) for s in gc]
            gauc = auc(gc_l, ga_l)
            gse, glo, ghi = hanley_mcneil(gauc, len(ga), len(gc))
            per_group[g] = GroupStat(g, len(ga), len(gc), gauc, gse, (glo, ghi))
    return AuditResult(dataset, comparison, len(A), len(C),
                       statistics.mean(A), statistics.mean(C),
                       a, se, (lo, hi), strategy, per_group, other)


# ─────────────────── 各資料集的載入 ───────────────────

def load_chagen() -> list[AuditResult]:
    base = EXT / "CHA-Gen" / "dataset" / "CHA-Gen"
    out: list[AuditResult] = []
    corpus = base / "corpus.csv"
    if corpus.exists():
        with corpus.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        amb = [r["sent"] for r in rows if str(r["ambiguity"]).strip() == "1"]
        ctl = [r["sent"] for r in rows if str(r["ambiguity"]).strip() == "0"]
        groups: dict[str, tuple[list[str], list[str]]] = {}
        for r in rows:
            t = r["type"]
            ga, gc = groups.setdefault(t, ([], []))
            (ga if str(r["ambiguity"]).strip() == "1" else gc).append(r["sent"])
        out.append(audit("CHA-Gen corpus", "歧義句 vs 非歧義句（同結構池）",
                         amb, ctl,
                         "非歧義句為另行生成的同結構句，非同句消歧版", groups))
    pair = base / "sentence_pair.csv"
    if pair.exists():
        with pair.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        out.append(audit("CHA-Gen sentence_pair", "歧義句 vs 配對的非歧義句",
                         [r["ambiguous"] for r in rows],
                         [r["unambiguous"] for r in rows],
                         "配對句為同結構的另一句，非同句的最小對立消歧版"))
    return out


# 該資料集無授權聲明（預設保留所有權利），不隨本專案散布
WU_TSV = OUT / "wu2025_task2_test.tsv"
WU_MISSING = (f"略過 Wu et al. 2025：找不到 {WU_TSV.relative_to(ROOT).as_posix()}。"
              "此資料需自行向原作者取得（ictup/LLM-Chinese-Textual-Disambiguation"
              " 的 task2_test.tsv），取得後放到上述路徑。")


def load_wu2025() -> list[AuditResult]:
    p = WU_TSV
    if not p.exists():
        print(WU_MISSING, file=sys.stderr)
        return []
    with p.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    def clean(s):
        return (s or "").strip().strip('"')

    bare, ctx, dis = [], [], []
    for r in rows:
        a = clean(r.get("歧义句"))
        c = clean(r.get("歧义句及上下文"))
        d = [clean(r.get(f"歧义句消岐{i}")) for i in (1, 2, 3, 4)]
        d = [x for x in d if x and x != "无"]
        if a and d:
            bare.append(a)
            ctx.append(c or a)
            dis.append(d[0])
    out = []
    if bare:
        out.append(audit("Wu et al. 2025", "歧義句（無上下文） vs 消歧句",
                         bare, dis, "消歧策略為補上下文，必然拉長"))
        out.append(audit("Wu et al. 2025", "歧義句＋上下文 vs 消歧句",
                         ctx, dis, "同上，但歧義側也含上下文"))
    return out


def load_dev30() -> list[AuditResult]:
    import yaml
    p = ROOT / "data" / "dev30" / "sentences.yaml"
    if not p.exists():
        return []
    items = yaml.safe_load(p.read_text(encoding="utf-8"))["items"]
    amb = [i["text"] for i in items if i.get("minimal_pair")]
    ctl = [i["minimal_pair"]["text"] for i in items if i.get("minimal_pair")]
    groups: dict[str, tuple[list[str], list[str]]] = {}
    for i in items:
        if not i.get("minimal_pair"):
            continue
        ga, gc = groups.setdefault(i["ambiguity_type"], ([], []))
        ga.append(i["text"])
        gc.append(i["minimal_pair"]["text"])
    return [audit("本專案 dev-30（修正後）", "歧義句 vs 等長替換消歧句",
                  amb, ctl, "等長替換，不補語境", groups)]


# ─────────────────── 報告 ───────────────────

def verdict(auc_v: float, ci: tuple[float, float]) -> str:
    """判讀必須依 n 而定 —— 固定門檻是錯的。

    先前版本用 ≥0.6 當門檻，那是為 n=30（SE≈0.075）設計的。
    套在 n=5712（SE≈0.0075）上會把「決定性排除 0.5 但效應微弱」誤判為「無混淆」。

    正確做法：統計顯著性（CI 是否排除 0.5）與效應量（|AUC−0.5|）分開報。
    """
    sig = ci[0] > 0.5 or ci[1] < 0.5
    eff = abs(auc_v - 0.5)
    if not sig:
        return "無法排除 0.5"
    size = "🔴 大" if eff >= 0.25 else ("⚠️ 中" if eff >= 0.10 else "微弱")
    return f"顯著／效應{size}"


def main() -> int:
    # 已 commit 的 length_audit_summary.* 含 Wu et al. 的列；缺資料時重寫會把它們弄丟
    if not WU_TSV.exists():
        print(WU_MISSING + "既有的 length_audit_summary.* 不覆寫。", file=sys.stderr)
        return 0
    results = load_chagen() + load_wu2025() + load_dev30()
    if not results:
        print("沒有可稽核的資料集", file=sys.stderr)
        return 1

    L: list[str] = []
    L.append("# 外部歧義資料集的長度稽核")
    L.append("")
    L.append("> 由 `scripts/external_length_audit.py` 產生。**只用同一支長度基準**，")
    L.append("> 對所有資料集一視同仁，包含本專案自己的 dev-30。")
    L.append(">")
    L.append("> ⚠️ **公平陳述**：這些資料集是為各自的用途設計的（CHA-Gen 為歧義偵測與")
    L.append("> 翻譯分析、Wu et al. 為生成消歧版本）。有問題的是把它們當**偵測任務的")
    L.append("> 負例**——那是本專案的用法，不是原作者的主張。")
    L.append("> 本表**不得**被寫成「該資料集有瑕疵」。")
    L.append("")
    L.append("> ⚠️ **判讀依 n 而定，不用固定門檻。** 統計顯著性（CI 是否排除 0.5）與")
    L.append("> 效應量（|AUC−0.5|）分開報——n 大時微弱效應也會顯著，n 小時大效應也可能不顯著。")
    L.append("")
    L.append("## 主表")
    L.append("")
    L.append("| 資料集 | 比較方式 | n（歧義／對照） | 歧義側均長 | 對照側均長 | 長度 AUC | SE | 95% CI | 效應量 | 方向 | 判讀 | 消歧策略 |")
    L.append("| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | --- |")
    for r in results:
        direction = "對照較長" if r.length_auc > 0.5 else "歧義較長"
        L.append(f"| {r.dataset} | {r.comparison} | {r.n_amb}／{r.n_ctl} | "
                 f"{r.mean_amb:.1f} | {r.mean_ctl:.1f} | **{r.length_auc:.3f}** | "
                 f"{r.se:.4f} | [{r.ci[0]:.3f}, {r.ci[1]:.3f}] | {r.effect:.3f} | "
                 f"{direction} | {verdict(r.length_auc, r.ci)} | {r.strategy} |")
    L.append("")

    L.append("## 其他表層特徵")
    L.append("")
    L.append("| 資料集 | 比較方式 | 標點總數 AUC | 相異字元數 AUC |")
    L.append("| --- | --- | :-: | :-: |")
    for r in results:
        L.append(f"| {r.dataset} | {r.comparison} | "
                 f"{r.other_features.get('標點總數', float('nan')):.3f} | "
                 f"{r.other_features.get('相異字元數', float('nan')):.3f} |")
    L.append("")

    for r in results:
        if not r.per_group:
            continue
        L.append(f"## 分組長度 AUC — {r.dataset}")
        L.append("")
        L.append("⭐ **這張表才是重點。** 聚合層級的 AUC 會因正負相消而看似乾淨，")
        L.append("但分組後可能有多個組別各自顯著且方向相反。")
        L.append("")
        L.append("| 組別 | n（歧義／對照） | 長度 AUC | SE | 95% CI | 效應量 | 方向 | CI 排除 0.5 |")
        L.append("| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |")
        for g in sorted(r.per_group.values(), key=lambda s: -s.auc):
            L.append(f"| {g.name} | {g.n_amb}／{g.n_ctl} | **{g.auc:.3f}** | "
                     f"{g.se:.3f} | [{g.ci[0]:.3f}, {g.ci[1]:.3f}] | {g.effect:.3f} | "
                     f"{g.direction} | {'✅' if g.excludes_half else '—'} |")
        L.append("")
        gs = list(r.per_group.values())
        sig = [g for g in gs if g.excludes_half]
        up = [g for g in sig if g.auc > 0.5]
        dn = [g for g in sig if g.auc < 0.5]
        vals = [g.auc for g in gs]
        L.append(f"分組數 {len(gs)}，AUC 範圍 {min(vals):.3f}–{max(vals):.3f}，"
                 f"中位數 {statistics.median(vals):.3f}")
        L.append("")
        L.append(f"**CI 排除 0.5 的組別：{len(sig)} / {len(gs)}**"
                 f"（對照較長 {len(up)} 組、歧義較長 {len(dn)} 組）")
        if len(up) and len(dn):
            L.append("")
            L.append(f"⚠️ **兩個方向都有顯著組別 → 聚合中位數 {statistics.median(vals):.3f} "
                     f"是正負相消的結果，不是「乾淨」。**")
            L.append(f"最極端的兩組：`{max(gs, key=lambda g: g.auc).name}` "
                     f"{max(vals):.3f} 與 `{min(gs, key=lambda g: g.auc).name}` {min(vals):.3f}")
        L.append("")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "length_audit_summary.md").write_text("\n".join(L), encoding="utf-8")
    (OUT / "length_audit_summary.json").write_text(json.dumps(
        [{"dataset": r.dataset, "comparison": r.comparison,
          "n_amb": r.n_amb, "n_ctl": r.n_ctl,
          "mean_amb": r.mean_amb, "mean_ctl": r.mean_ctl,
          "length_auc": r.length_auc, "se": r.se, "ci": list(r.ci),
          "effect": r.effect, "excludes_half": r.excludes_half,
          "strategy": r.strategy,
          "per_group": {k: {"n_amb": g.n_amb, "n_ctl": g.n_ctl, "auc": g.auc,
                            "se": g.se, "ci": list(g.ci), "effect": g.effect,
                            "direction": g.direction,
                            "excludes_half": g.excludes_half}
                        for k, g in r.per_group.items()},
          "other_features": r.other_features} for r in results],
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{'資料集':24}{'n':>12}{'AUC':>8}{'SE':>8}{'95% CI':>18}{'效應':>7}  判讀")
    print("-" * 100)
    for r in results:
        print(f"{r.dataset:24}{f'{r.n_amb}/{r.n_ctl}':>12}{r.length_auc:8.3f}"
              f"{r.se:8.4f}{f'[{r.ci[0]:.3f},{r.ci[1]:.3f}]':>18}{r.effect:7.3f}  "
              f"{verdict(r.length_auc, r.ci)}")
        if r.per_group:
            gs = list(r.per_group.values())
            sig = [g for g in gs if g.excludes_half]
            up = sum(1 for g in sig if g.auc > 0.5)
            dn = len(sig) - up
            print(f"{'':24}└ 分組 {len(gs)} 個，CI 排除 0.5 者 {len(sig)} 個"
                  f"（對照較長 {up}／歧義較長 {dn}）")
    print(f"\n已產出 {OUT / 'length_audit_summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
