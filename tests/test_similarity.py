"""相似度與聚合的單元測試（§5 地雷 5：新指標必須有測試才可用來下結論）。"""

from __future__ import annotations

import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.similarity import (  # noqa: E402
    cosine,
    mean_pairwise,
    mean_vs_source,
    medoid_index,
    min_vs_source,
    suggest_n_samples,
    variance_of,
)


# ── cosine ──

def test_cosine_identical_is_one():
    assert cosine([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_orthogonal_is_zero():
    assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_opposite_is_minus_one():
    assert cosine([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_scale_invariant():
    assert cosine([1.0, 2.0], [2.0, 4.0]) == pytest.approx(1.0)


def test_cosine_zero_vector_is_zero_not_nan():
    v = cosine([0.0, 0.0], [1.0, 1.0])
    assert v == 0.0 and not math.isnan(v)


def test_cosine_dimension_mismatch_raises():
    with pytest.raises(ValueError):
        cosine([1.0], [1.0, 2.0])


# ── 聚合 ──

def test_mean_pairwise_needs_two():
    assert mean_pairwise([[1.0, 0.0]]) is None
    assert mean_pairwise([]) is None


def test_mean_pairwise_all_identical():
    v = [1.0, 1.0]
    assert mean_pairwise([v, v, v]) == pytest.approx(1.0)


def test_mean_pairwise_counts_each_pair_once():
    """三個向量有三對，不是九對——重複計數會讓一致性虛高。"""
    a, b, c = [1.0, 0.0], [0.0, 1.0], [1.0, 0.0]
    expected = (cosine(a, b) + cosine(a, c) + cosine(b, c)) / 3
    assert mean_pairwise([a, b, c]) == pytest.approx(expected)


def test_min_vs_source_takes_worst_case():
    """取最小而非平均：只要有一條路徑掉了資訊就該被偵測到。"""
    src = [1.0, 0.0]
    others = [[1.0, 0.0], [0.0, 1.0]]
    assert min_vs_source(src, others) == pytest.approx(0.0)
    assert mean_vs_source(src, others) == pytest.approx(0.5)


def test_min_vs_source_empty_is_none():
    assert min_vs_source([1.0, 0.0], []) is None


# ── medoid ──

def test_medoid_picks_central_member():
    """自由文本沒有『取多數』，B2 的 self-consistency 用 medoid 定義。"""
    vecs = [[1.0, 0.0], [0.99, 0.14], [0.0, 1.0]]
    assert medoid_index(vecs) in (0, 1)      # 第三個是離群值


def test_medoid_single_and_empty():
    assert medoid_index([[1.0]]) == 0
    with pytest.raises(ValueError):
        medoid_index([])


def test_medoid_is_an_index_not_a_vector():
    idx = medoid_index([[1.0, 0.0], [0.0, 1.0]])
    assert isinstance(idx, int) and 0 <= idx < 2


# ── 取樣次數自適應 ──

def test_variance_of_constant_is_zero():
    assert variance_of([0.5] * 5) == 0.0


def test_suggest_n_deterministic_model_gets_floor():
    """mistral 實測 11/15 句三次全同，近乎確定性——多跑無益。"""
    assert suggest_n_samples([0.9, 0.9, 0.9]) == 2


def test_suggest_n_high_variance_model_gets_more():
    """diffusiongemma 實測 0/15 全同，n=3 完全不足。"""
    n = suggest_n_samples([0.2, 0.9, 0.5, 0.8])
    assert n > 2


def test_suggest_n_respects_cap():
    assert suggest_n_samples([0.0, 1.0, 0.0, 1.0], cap=5) <= 5


def test_suggest_n_insufficient_observations_returns_floor():
    assert suggest_n_samples([]) == 2
    assert suggest_n_samples([0.5]) == 2


def test_suggest_n_is_monotone_in_variance():
    lo = suggest_n_samples([0.50, 0.52, 0.51, 0.49])
    hi = suggest_n_samples([0.10, 0.90, 0.30, 0.70])
    assert hi >= lo
