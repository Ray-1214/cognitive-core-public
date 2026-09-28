"""標籤噪音的估計與天花板校正（2026-08-22 裁示）。

## ⚠️ 位置效應與內容誤差不可相加

「judge vs 人工 = 85%」量的是 judge 的**總**錯誤率（相對人工這個參照）。
位置驅動的判定與人工不一致時就已經算在那 15% 裡了——
把 3.9pp 再加上去是重複計算。

正確關係是**分解**而非相加：

    judge 總錯誤 15%
      ├── ≥3.9pp  位置啟發式（n=399 量得，精度高）
      └── ≈11pp   內容誤判（殘差）

`compose_noise()` 因此回傳 total = 直接量測值，並附上分解。

一個例外要留意：若人工**也**有同向的位置偏誤，兩邊的偏誤會在一致率裡
互相抵銷，15% 就低估了。r2 實測人工選 A 為 10/20、judge 亦 10/20，
沒有共同偏誤，故此處不做上修。`shared_position_bias` 記錄這件事。

## 天花板校正

盲標的第二欄直接量出「兩個都說得通」的比例 a。那些題目上任何評判者
（人或模型）都只能猜，期望正確率 0.5。故

    觀測正確率 = (1−a)·θ + a·0.5

θ 是模型在**可判定題目**上的真實正確率。兩個分母都要報：

    模型錯誤（佔全部題目） = 觀測錯誤 − a/2
    模型錯誤（佔可判定題目）= (觀測錯誤 − a/2) / (1−a)

⚠️ a 由 n=20 估得，CI 很寬。校正後的數字必須連同 CI 一起報。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .wsd import wilson_ci


@dataclass(frozen=True)
class NoiseEstimate:
    total: float                     # 直接量測：1 − judge/人工一致率
    total_ci: tuple[float, float]
    position_component: float        # 位置啟發式貢獻的下界
    content_component: float         # 殘差
    n_agreement: int
    shared_position_bias: bool       # 人工是否也有同向位置偏誤
    note: str = ""

    @property
    def additive_would_be(self) -> float:
        """若誤把兩者相加會得到的（錯誤）數字。留著供報告說明用。"""
        return self.total + self.position_component


def compose_noise(*, n_agree: int, n_total: int, position_noise: float,
                  human_a_rate: float | None = None,
                  judge_a_rate: float | None = None) -> NoiseEstimate:
    """把一致率與位置效應組成標籤噪音估計。

    `position_noise` 來自 `wsd.position_effect()["implied_noise"]`。
    它是 total 的**成分**，不是加項。
    """
    total = 1.0 - n_agree / n_total if n_total else float("nan")
    lo, hi = wilson_ci(n_total - n_agree, n_total)
    shared = False
    note = ""
    if human_a_rate is not None and judge_a_rate is not None:
        # 兩邊都明顯偏 A（或都偏 B）→ 偏誤會在一致率裡抵銷，total 低估
        shared = (human_a_rate - 0.5) * (judge_a_rate - 0.5) > 0 and \
                 min(abs(human_a_rate - 0.5), abs(judge_a_rate - 0.5)) > 0.1
        if shared:
            note = ("人工與 judge 有同向位置偏誤，兩者在一致率中互相抵銷，"
                    "total 為低估。")
    return NoiseEstimate(
        total=total, total_ci=(lo, hi),
        position_component=min(position_noise, total) if total == total else position_noise,
        content_component=max(total - position_noise, 0.0) if total == total else float("nan"),
        n_agreement=n_total, shared_position_bias=shared, note=note)


@dataclass(frozen=True)
class ErrorDecomposition:
    """三個一致率的分解。讓 judge 的可靠度有可辯護的說明。"""
    gold_to_human: float      # CWN gold → 人工　跨語言判定的固有限制
    human_to_judge: float     # 人工 → judge　　機器誤差
    gold_to_judge: float      # gold → judge　　兩者疊加
    n: int

    @property
    def task_share(self) -> float:
        """judge 對 gold 的落差中，可歸因於任務本身的部分。"""
        return self.gold_to_human

    @property
    def model_share(self) -> float:
        """殘差——歸因於模型的部分。"""
        return max(self.gold_to_judge - self.gold_to_human, 0.0)

    @property
    def superadditive(self) -> float:
        """兩段落差相加與實際落差的差。

        >0 代表兩段誤差部分抵銷（judge 的錯剛好回到 gold），
        <0 代表誤差疊加得比獨立假設更嚴重。
        """
        return self.gold_to_human + self.human_to_judge - self.gold_to_judge


def decompose(*, judge_vs_human: float, human_vs_gold: float,
              judge_vs_gold: float, n: int) -> ErrorDecomposition:
    return ErrorDecomposition(gold_to_human=1 - human_vs_gold,
                              human_to_judge=1 - judge_vs_human,
                              gold_to_judge=1 - judge_vs_gold, n=n)


@dataclass(frozen=True)
class CeilingCorrection:
    observed_acc: float
    ambiguous_rate: float
    ambiguous_ci: tuple[float, float]
    n_ambiguous_sample: int
    ceiling: float                       # 任何評判者能達到的最高正確率
    err_observed: float
    err_of_all_items: float              # 模型錯誤佔**全部**題目
    err_of_decidable: float              # 模型錯誤佔**可判定**題目
    err_of_all_ci: tuple[float, float]
    err_of_decidable_ci: tuple[float, float]

    @property
    def valid(self) -> bool:
        return 0.0 <= self.ambiguous_rate < 1.0 and self.err_of_all_items >= 0


def ceiling_correct(observed_acc: float, *, n_ambiguous: int,
                    n_annotated: int) -> CeilingCorrection:
    """依「兩個都說得通」的比例做天花板校正。

    模型：不可判定的題目上結果是擲硬幣（期望正確率 0.5）。

        觀測正確率 = (1−a)·θ + a·0.5

    ⚠️ 兩個分母都要報，混用會讓數字被誤讀：
      `err_of_all_items`  = 觀測錯誤 − a/2          （分母＝全部題目）
      `err_of_decidable`  = 上式 / (1−a)            （分母＝可判定題目）
    """
    a = n_ambiguous / n_annotated if n_annotated else float("nan")
    alo, ahi = wilson_ci(n_ambiguous, n_annotated)
    err_obs = 1.0 - observed_acc

    def of_all(x: float) -> float:
        return max(err_obs - x / 2, 0.0)

    def of_dec(x: float) -> float:
        return of_all(x) / (1 - x) if x < 1 else float("nan")

    # a 越大 → 校正越多 → 錯誤率越低，故 CI 方向相反
    return CeilingCorrection(
        observed_acc=observed_acc, ambiguous_rate=a, ambiguous_ci=(alo, ahi),
        n_ambiguous_sample=n_annotated,
        ceiling=1 - a / 2,
        err_observed=err_obs,
        err_of_all_items=of_all(a), err_of_decidable=of_dec(a),
        err_of_all_ci=(of_all(ahi), of_all(alo)),
        err_of_decidable_ci=(of_dec(ahi), of_dec(alo)))


def holm(pvalues: list[float]) -> list[float]:
    """Holm–Bonferroni 逐步校正。回傳與輸入同順序的調整後 p。"""
    idx = [i for i, p in enumerate(pvalues) if not math.isnan(p)]
    order = sorted(idx, key=lambda i: pvalues[i])
    out = [float("nan")] * len(pvalues)
    m = len(order)
    prev = 0.0
    for k, i in enumerate(order):
        adj = min(1.0, max(prev, (m - k) * pvalues[i]))
        prev = adj
        out[i] = adj
    return out
