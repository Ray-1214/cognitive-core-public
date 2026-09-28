"""AUC 與其信賴區間（v3 架構書 §P4 DoD、§4 地雷 1）。

這是 RQ1 的核心統計。三件事必須做對，否則結論不成立：

1. **AUC == 1.0 或 0.0 時 Hanley–McNeil 退化。**
   代入 A=1 得 Q1=Q2=1、var=0，會回報 CI [1.00, 1.00]——那不是
   「我們非常確定 AUC 是 1」，而是這個近似公式在邊界失效。
   本模組偵測到退化時改用**排列檢定**給 p 值，並把 `degenerate` 標成 True。

2. **每個訊號都要與純句長基準並列。**（§4 地雷 1）
   S3 句法複雜度尤其——它的三個成分都隨長度成長。
   單看 S3 的 AUC 顯著不能證明它有獨立資訊，必須用 `delong_test`
   比較「S3」與「純句長」這兩個**相關**的 AUC。

3. **不要在資料上擬合權重。**（§P4）
   本模組只提供「各訊號各自的 AUC」與「未加權總和」兩種算法，
   刻意不提供任何擬合介面。

Hanley & McNeil (1982)；DeLong et al. (1988)。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import numpy as np


def _phi(z: float) -> float:
    """標準常態 CDF。專案未安裝 scipy，用 erf 自己算。"""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def auc_score(pos: list[float], neg: list[float]) -> float:
    """pos = 正類（例：模型答錯）的訊號值，neg = 負類。並列計 0.5。"""
    if not pos or not neg:
        return float("nan")
    p = np.asarray(pos, dtype=float)
    n = np.asarray(neg, dtype=float)
    gt = (p[:, None] > n[None, :]).sum()
    eq = (p[:, None] == n[None, :]).sum()
    return float((gt + 0.5 * eq) / (p.size * n.size))


def hanley_mcneil(a: float, n1: int, n2: int) -> tuple[float, float, float]:
    """回傳 (SE, CI 下界, CI 上界)。a 為 0 或 1 時 var=0，呼叫端須自行處理。"""
    if n1 < 1 or n2 < 1 or math.isnan(a):
        return (float("nan"),) * 3
    q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
    var = (a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2)
    se = math.sqrt(max(var, 0.0))
    return se, max(0.0, a - 1.96 * se), min(1.0, a + 1.96 * se)


def permutation_p(pos: list[float], neg: list[float], *,
                  n_perm: int = 10000, seed: int = 0) -> float:
    """雙尾排列檢定：|AUC - 0.5| 在標籤隨機重排下有多常見。

    AUC 退化（0 或 1）時 Hanley–McNeil 給不出有意義的 CI，改用這個。
    回傳的 p 值用 (r+1)/(n+1) 的保守估計，不會出現 p=0。
    """
    if not pos or not neg:
        return float("nan")
    obs = abs(auc_score(pos, neg) - 0.5)
    allv = np.asarray(list(pos) + list(neg), dtype=float)
    n1 = len(pos)
    rng = np.random.default_rng(seed)
    hit = 0
    for _ in range(n_perm):
        rng.shuffle(allv)
        a = auc_score(allv[:n1].tolist(), allv[n1:].tolist())
        if abs(a - 0.5) >= obs - 1e-12:
            hit += 1
    return (hit + 1) / (n_perm + 1)


@dataclass(frozen=True)
class AucResult:
    name: str
    auc: float
    se: float
    ci: tuple[float, float]
    n_pos: int
    n_neg: int
    degenerate: bool = False
    p_perm: float | None = None
    note: str = ""

    @property
    def excludes_half(self) -> bool:
        """CI 排除 0.5（退化時改看排列檢定的 p）。"""
        if self.degenerate:
            return self.p_perm is not None and self.p_perm < 0.05
        if math.isnan(self.auc):
            return False
        return self.ci[0] > 0.5 or self.ci[1] < 0.5

    def ci_text(self) -> str:
        if self.degenerate:
            return f"退化（排列檢定 p={self.p_perm:.4f}）"
        if math.isnan(self.auc):
            return "—"
        return f"[{self.ci[0]:.3f}, {self.ci[1]:.3f}]"


DEGENERATE_NOTE = (
    "AUC 落在邊界，Hanley–McNeil 的 var=0，CI 無意義。已改用排列檢定。")


def evaluate(pos: list[float], neg: list[float], *, name: str = "",
             n_perm: int = 10000, seed: int = 0) -> AucResult:
    """算 AUC + CI；退化時自動改用排列檢定。"""
    a = auc_score(pos, neg)
    n1, n2 = len(pos), len(neg)
    if math.isnan(a):
        return AucResult(name, a, float("nan"), (float("nan"),) * 2, n1, n2,
                         note="正類或負類為空")
    if a <= 0.0 or a >= 1.0:
        return AucResult(name, a, float("nan"), (float("nan"),) * 2, n1, n2,
                         degenerate=True,
                         p_perm=permutation_p(pos, neg, n_perm=n_perm, seed=seed),
                         note=DEGENERATE_NOTE)
    se, lo, hi = hanley_mcneil(a, n1, n2)
    return AucResult(name, a, se, (lo, hi), n1, n2)


# ─────────────── DeLong：比較兩個「相關」的 AUC ───────────────

def _structural_components(scores: np.ndarray, n1: int) -> tuple[np.ndarray, np.ndarray]:
    """回傳 (V10, V01)。scores 前 n1 筆是正類。"""
    p, n = scores[:n1], scores[n1:]
    m = (p[:, None] > n[None, :]).astype(float) + 0.5 * (p[:, None] == n[None, :])
    return m.mean(axis=1), m.mean(axis=0)


@dataclass(frozen=True)
class DeLongResult:
    auc_a: float
    auc_b: float
    diff: float
    se_diff: float
    z: float
    p: float
    ci: tuple[float, float] = field(default=(float("nan"), float("nan")))

    @property
    def significant(self) -> bool:
        return not math.isnan(self.p) and self.p < 0.05


def delong_test(pos_a: list[float], neg_a: list[float],
                pos_b: list[float], neg_b: list[float]) -> DeLongResult:
    """比較同一批樣本上兩個訊號的 AUC（相關樣本，不可用獨立雙樣本檢定）。

    ⚠️ 兩組必須是**同一批題目、同樣的排序**——A 的第 i 個正類與 B 的第 i 個
    正類要是同一題。這正是「S3 vs 純句長」該用的檢定：兩者在同一批句子上
    高度相關，用獨立檢定會低估標準誤、高估顯著性。
    """
    n1, n2 = len(pos_a), len(neg_a)
    if (n1, n2) != (len(pos_b), len(neg_b)) or n1 < 2 or n2 < 2:
        return DeLongResult(float("nan"), float("nan"), float("nan"),
                            float("nan"), float("nan"), float("nan"))
    sa = np.asarray(list(pos_a) + list(neg_a), dtype=float)
    sb = np.asarray(list(pos_b) + list(neg_b), dtype=float)
    v10a, v01a = _structural_components(sa, n1)
    v10b, v01b = _structural_components(sb, n1)
    a_a, a_b = float(v10a.mean()), float(v10b.mean())

    s10 = np.cov(np.vstack([v10a, v10b]), ddof=1)
    s01 = np.cov(np.vstack([v01a, v01b]), ddof=1)
    s = s10 / n1 + s01 / n2
    var = float(s[0, 0] - 2 * s[0, 1] + s[1, 1])
    diff = a_a - a_b
    if var <= 0:
        # 兩個訊號給出完全相同的排序 → 差為 0 且無變異，不是「顯著相同」
        return DeLongResult(a_a, a_b, diff, 0.0, float("nan"), float("nan"))
    se = math.sqrt(var)
    z = diff / se
    return DeLongResult(a_a, a_b, diff, se, z, 2 * (1 - _phi(abs(z))),
                        (diff - 1.96 * se, diff + 1.96 * se))


# ─────────────── 未加權總和（§P4 的合成基準，不擬合權重） ───────────────

def unweighted_sum(signal_values: dict[str, list[float]]) -> list[float]:
    """把各訊號的分數直接相加當合成基準。

    ⚠️ 刻意不提供加權介面。在資料上擬合 w_i 會製造 dev/test 洩漏，
    而本專案沒有獨立的 test set 可以吸收那個風險（§P4）。
    """
    names = sorted(signal_values)
    if not names:
        return []
    n = len(signal_values[names[0]])
    if any(len(signal_values[k]) != n for k in names):
        raise ValueError("各訊號的長度必須一致")
    return [sum(signal_values[k][i] for k in names) for i in range(n)]


def required_auc(n_pos: int, n_neg: int, *, noise: float = 0.0,
                 step: float = 0.001) -> float:
    """在給定樣本數與標籤噪音下，「真實 AUC」要多大才能讓 95% CI 排除 0.5。

    標籤噪音的衰減用 observed ≈ 0.5 + (1-2p)(true-0.5)。
    這個函式的用途是**在跑實驗之前**就知道測不測得到，避免事後才發現
    所有訊號的 CI 都涵蓋 0.5 卻不知道是訊號無效還是樣本不足。
    """
    if n_pos < 1 or n_neg < 1 or noise >= 0.5:
        return float("nan")
    t = 0.5
    while t < 1.0:
        obs = 0.5 + (1 - 2 * noise) * (t - 0.5)
        _, lo, _ = hanley_mcneil(obs, n_pos, n_neg)
        if lo > 0.5:
            return round(t, 4)
        t += step
    return float("nan")
