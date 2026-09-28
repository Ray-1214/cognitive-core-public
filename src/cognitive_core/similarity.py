"""相似度與聚合（實作規格書 §A-2 similarity 區塊）。

純函式，不碰 API，因此可完整單元測試——§5 地雷 5：新指標必須有單元測試
才可用來下結論。先前的 span AUC 0.851 就是因為指標邏輯寫在 heredoc 裡沒有測試，
拿子片段比整句平均而未被發現。
"""

from __future__ import annotations

import math
from itertools import combinations

Vector = list[float]


def cosine(a: Vector, b: Vector) -> float:
    if len(a) != len(b):
        raise ValueError(f"維度不一致：{len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def mean_pairwise(vectors: list[Vector]) -> float | None:
    """樣本間一致性：平均成對餘弦。

    ⚠️ 僅作**收斂診斷**（迴圈跑了幾輪才穩），不得當作 E1 vs baseline 的勝負依據。
    反思迴圈的終止條件就是「一致性 ≥ τ」，拿它比較是套套邏輯（地雷 2）。
    """
    if len(vectors) < 2:
        return None
    pairs = list(combinations(vectors, 2))
    return sum(cosine(a, b) for a, b in pairs) / len(pairs)


def min_vs_source(source: Vector, others: list[Vector]) -> float | None:
    """單探針偵測分數：各回譯與**原文**的相似度取最小值。

    取最小而非平均：只要有一條路徑掉了資訊就該被偵測到。
    這是 S0b 實測中判別力最好的比法（V2）。
    """
    if not others:
        return None
    return min(cosine(source, v) for v in others)


def mean_vs_source(source: Vector, others: list[Vector]) -> float | None:
    if not others:
        return None
    return sum(cosine(source, v) for v in others) / len(others)


def medoid_index(vectors: list[Vector]) -> int:
    """回傳 medoid 的索引：到其他所有樣本距離總和最小者。

    自由文本沒有「取多數」這種操作，B2 的 self-consistency 用這個定義
    （實作規格書 §Phase C）。
    """
    if not vectors:
        raise ValueError("空集合")
    if len(vectors) == 1:
        return 0
    best_i, best_cost = 0, float("inf")
    for i, v in enumerate(vectors):
        cost = sum(1.0 - cosine(v, u) for j, u in enumerate(vectors) if j != i)
        if cost < best_cost:
            best_i, best_cost = i, cost
    return best_i


def variance_of(values: list[float]) -> float:
    """母體變異數。用於「取樣重複次數依觀測變異決定」。"""
    if len(values) < 2:
        return 0.0
    m = sum(values) / len(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def suggest_n_samples(observed: list[float], *, target_sem: float = 0.02,
                      floor: int = 2, cap: int = 8) -> int:
    """依觀測變異決定取樣次數（Phase A checklist 第 8 項）。

    固定 n=3 對所有模型是錯的——實測 mistral 11/15 句三次全同（近乎確定性，
    跑三次等於跑一次），diffusiongemma 0/15 全同（n=3 完全不足），差 15 倍。

    以「平均值標準誤達到 target_sem」反推 n = var / target_sem²，
    夾在 [floor, cap] 之間。observed 不足兩筆時回傳 floor。
    """
    if len(observed) < 2:
        return floor
    var = variance_of(observed)
    if var <= 0:
        return floor                      # 完全確定性的模型，多跑無益
    need = math.ceil(var / (target_sem ** 2))
    return max(floor, min(cap, need))
