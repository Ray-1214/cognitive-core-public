"""長度稽核（v3 架構書 §P2、修正版 DoD 第 2 條）。

⚠️ **DoD 第 2 條已拆成兩件事**，因為原本的講法搞混了兩個層次：

1-1 **實作斷言**（進 tests/，不進報告）
    probe_span 在 U/A/B 是**同一個字串**，比較同一字串的長度 AUC 必然是 0.500——
    那是恆等式，證明的是「程式沒把字串弄壞」，不是「設計有效」。
    這類檢查屬於守門測試，見 `tests/test_probe_invariants.py`。

1-2 **真正的長度稽核**（進報告）
    問的不是「兩組長度一不一樣」，而是：
      - 在**模型選錯**的題目上，probe_span 是不是系統性比較長？
      - context 長度能不能預測選錯？
    兩者都是非平凡的。context 尤其要查——C_A 與 C_B 是不同字串，
    配平只做到 ≤10%，殘差仍可能與答案相關。

    且照 CHA-Gen 的教訓必須**分層跑**：聚合值會正負相消
    （該資料集 18 組中 12 組顯著，7 組一個方向、5 組另一個方向，
    中位數卻是 0.490）。
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass


# AUC 的正典實作在 eval/auc.py（含 AUC==1.0 的退化處理與 DeLong）。
# 這裡只轉出名字，避免兩份實作各自演化——§4 地雷 5「基礎設施債」。
from ..eval.auc import auc_score as auc  # noqa: E402
from ..eval.auc import evaluate, hanley_mcneil  # noqa: E402

__all__ = ["auc", "hanley_mcneil", "evaluate", "AuditRow",
           "audit_predicts_error", "format_report"]


@dataclass
class AuditRow:
    stratum: str
    feature: str
    n_wrong: int
    n_correct: int
    auc: float
    se: float
    ci: tuple[float, float]
    degenerate: bool = False
    p_perm: float | None = None
    p_adjusted: float | None = None      # Holm 校正後的 p

    @property
    def excludes_half(self) -> bool:
        """未校正的顯著性。⚠️ 一次跑上百格，這個欄位一定會有偽陽性，

        判斷實際結論請看 `survives_correction`。
        """
        if self.degenerate:
            return self.p_perm is not None and self.p_perm < 0.05
        if math.isnan(self.auc):
            return False
        return self.ci[0] > 0.5 or self.ci[1] < 0.5

    @property
    def survives_correction(self) -> bool:
        """Holm 校正後仍顯著。"""
        return self.p_adjusted is not None and self.p_adjusted < 0.05

    def ci_text(self) -> str:
        if self.degenerate:
            p = "—" if self.p_perm is None else f"{self.p_perm:.4f}"
            return f"退化（排列檢定 p={p}）"
        if math.isnan(self.auc):
            return "—"
        return f"[{self.ci[0]:.3f}, {self.ci[1]:.3f}]"

    @property
    def effect(self) -> float:
        return abs(self.auc - 0.5)

    @property
    def direction(self) -> str:
        if math.isnan(self.auc):
            return "—"
        return "選錯者較長" if self.auc > 0.5 else ("選對者較長" if self.auc < 0.5 else "—")


# 要稽核的長度定義。不同定義可能給出不同結論，故各算一次。
#
# ⚠️ 這幾個特徵**彼此高度相關**，在單句探針上有幾個甚至完全等價
# （probe_span == full_input，且「詞數估計」是字元數的單調函數，AUC 只看排序
# 所以三者的 AUC 必然相同）。因此「N 格顯著」不等於「N 個獨立發現」——
# 報告時要看的是有幾個**分層**出現效果，不是有幾格。
LENGTH_FEATURES = {
    "probe_span 字元數": lambda r: float(len(r["probe_span"])),
    "context 字元數": lambda r: float(r["context_length"]),
    "full_input 字元數": lambda r: float(len(r["full_input"])),
    "probe_span 標點數": lambda r: float(sum(c in "，。、！？；：" for c in r["probe_span"])),
    "probe_span 詞數估計": lambda r: float(len([c for c in r["probe_span"] if c.strip()])),
}


def _holm(rows: list[AuditRow]) -> None:
    """Holm–Bonferroni 逐步校正，就地寫回 `p_adjusted`。

    為什麼一定要做：本函式一次跑「整體 + 每個分層 × 5 個特徵」，
    在 400 筆、40 個目標詞的規模下是上百格。α=0.05 之下光靠運氣就會有
    5–10 格顯著。不校正就會把雜訊讀成「某些詞有長度混淆」。

    用 Holm 而非 Bonferroni：Holm 一致地較不保守，且同樣控制族錯誤率。
    """
    idx = [i for i, r in enumerate(rows) if not math.isnan(r.auc)]
    pv = []
    for i in idx:
        r = rows[i]
        if r.degenerate:
            p = 1.0 if r.p_perm is None else r.p_perm
        else:
            # 由 AUC 與 SE 反推雙尾 p（H0: AUC = 0.5）
            p = (1.0 if r.se == 0 or math.isnan(r.se)
                 else 2 * (1 - _phi(abs(r.auc - 0.5) / r.se)))
        pv.append((p, i))
    pv.sort()
    m = len(pv)
    prev = 0.0
    for k, (p, i) in enumerate(pv):
        adj = min(1.0, max(prev, (m - k) * p))
        prev = adj
        rows[i].p_adjusted = adj


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def audit_predicts_error(records: list[dict], *,
                         strata: tuple[str, ...] = ("ambiguity_type", "target_word")
                         ) -> list[AuditRow]:
    """長度特徵能否預測「模型選錯」。

    `records` 每筆需含：
        probe_span, context_length, full_input, is_wrong(bool)
        以及 strata 指定的分層欄位

    正例＝選錯者。AUC > 0.5 代表選錯的題目長度較長。
    """
    rows: list[AuditRow] = []

    def one(name: str, subset: list[dict]) -> None:
        wrong = [r for r in subset if r.get("is_wrong")]
        right = [r for r in subset if not r.get("is_wrong")]
        if len(wrong) < 3 or len(right) < 3:
            return
        for feat, fn in LENGTH_FEATURES.items():
            res = evaluate([fn(r) for r in wrong], [fn(r) for r in right],
                           name=feat, n_perm=2000)
            rows.append(AuditRow(name, feat, len(wrong), len(right),
                                 res.auc, res.se, res.ci,
                                 degenerate=res.degenerate, p_perm=res.p_perm))

    one("整體", records)
    for key in strata:
        buckets: dict[str, list[dict]] = {}
        for r in records:
            v = str(r.get(key, "—"))
            buckets.setdefault(v, []).append(r)
        for v, subset in sorted(buckets.items()):
            one(f"{key}={v}", subset)
    _holm(rows)
    return rows


def format_report(rows: list[AuditRow]) -> str:
    """報告用的 markdown。CI 排除 0.5 者必須逐一列出（DoD 第 2 條 b）。"""
    L = ["# 長度稽核：長度特徵能否預測「模型選錯」", "",
         "> 問的不是「兩組長度一不一樣」，而是**在模型選錯的題目上長度是否系統性不同**。",
         "> 分層報告——聚合值會正負相消（CHA-Gen 18 組中 12 組顯著、方向相反，",
         "> 中位數卻是 0.490）。", "",
         f"> 一次跑 {len(rows)} 格，α=0.05 之下光靠運氣就會有 "
         f"{len(rows) * 0.05:.0f} 格顯著，故並列 Holm 校正後的 p。",
         "> 五個長度特徵彼此高度相關（單句探針上 probe_span == full_input，"
         "且「詞數估計」是字元數的單調函數，",
         "> AUC 只看排序故三者必然同值），所以要看的是有幾個**分層**出現效果，"
         "不是有幾格。", "",
         "| 分層 | 特徵 | n（錯／對） | AUC | SE | 95% CI | 效應量 | 方向 "
         "| 排除 0.5 | Holm p |",
         "| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |"]
    for r in sorted(rows, key=lambda x: (x.stratum != "整體", -x.effect)):
        adj = "—" if r.p_adjusted is None else f"{r.p_adjusted:.3f}"
        L.append(f"| {r.stratum} | {r.feature} | {r.n_wrong}／{r.n_correct} | "
                 f"{r.auc:.3f} | {r.se:.3f} | {r.ci_text()} | "
                 f"{r.effect:.3f} | {r.direction} | "
                 f"{'✅' if r.excludes_half else '—'} | "
                 f"{adj}{' ✅' if r.survives_correction else ''} |")
    sig = [r for r in rows if r.excludes_half]
    survived = [r for r in rows if r.survives_correction]
    strata_sig = sorted({r.stratum for r in sig})
    L += ["", f"**未校正 CI 排除 0.5：{len(sig)} / {len(rows)} 格，"
              f"落在 {len(strata_sig)} 個分層**",
          f"**Holm 校正後仍顯著：{len(survived)} 格**"]
    if survived:
        L += ["", "校正後仍顯著者（這些才是結論）："]
        for r in survived:
            L.append(f"- `{r.stratum}` / {r.feature}：AUC {r.auc:.3f} "
                     f"{r.ci_text()}，{r.direction}，Holm p={r.p_adjusted:.4f}")
    elif sig:
        L += ["", f"⚠️ 未校正時有 {len(sig)} 格顯著（分層：{'、'.join(strata_sig)}），"
                  "但**沒有任何一格通過 Holm 校正**。",
              "在這個格數下這個數量與純機率相符，不足以支持「有長度混淆」。"]
    else:
        L += ["", "沒有任何分層的長度特徵能顯著預測選錯。"]
    return "\n".join(L)


def context_balance_report(probes: list[dict]) -> str:
    """脈絡長度配平的達成率（DoD 第 3 條）。"""
    deltas, ratios = [], []
    for p in probes:
        conds = p.get("conditions", {})
        a, b = conds.get("A"), conds.get("B")
        if not a or not b:
            continue
        la = len(a.get("context_before", "")) + len(a.get("context_after", ""))
        lb = len(b.get("context_before", "")) + len(b.get("context_after", ""))
        longer = max(la, lb)
        if longer == 0:
            continue
        deltas.append(abs(la - lb))
        ratios.append(abs(la - lb) / longer)
    if not ratios:
        return "（尚無 A/B 皆備的題目，無法計算脈絡配平）"
    ok = sum(1 for r in ratios if r <= 0.10)
    return (f"脈絡長度配平：{ok}/{len(ratios)}（{ok / len(ratios) * 100:.1f}%）"
            f"達成 ≤10%；差值中位數 {statistics.median(deltas):.1f} 字元，"
            f"最大 {max(deltas)}")
