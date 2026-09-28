"""語意熵的測試（v3 架構書 §P4 測試提示詞第 2 項）。

分群與熵的部分用合成向量／固定等價矩陣，不呼叫 API。
取樣的部分用 fake client，重點是釘住 **`n=k` 單一請求**——
改成呼叫 n 次會撞快取，熵恆為 0，而那個 bug 在 S0c 已經發生過一次。
"""

from __future__ import annotations

import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.eval.semantic_entropy import (  # noqa: E402
    cluster,
    entropy,
    equivalence_matrix_embed,
    equivalence_matrix_llm,
    normalized_entropy,
    sample_translations,
    semantic_entropy,
)


def eye(k: int) -> list[list[bool]]:
    return [[i == j for j in range(k)] for i in range(k)]


def ones(k: int) -> list[list[bool]]:
    return [[True] * k for _ in range(k)]


# ── 熵的兩個端點 ⭐ ──

def test_all_equivalent_gives_zero_entropy():
    labels = cluster(ones(8))
    assert len(set(labels)) == 1
    assert entropy(labels) == 0.0
    assert normalized_entropy(labels) == 0.0


def test_all_distinct_gives_log_n():
    n = 8
    labels = cluster(eye(n))
    assert len(set(labels)) == n
    assert entropy(labels) == pytest.approx(math.log(n))
    assert normalized_entropy(labels) == pytest.approx(1.0)


def test_two_equal_clusters_gives_log_two():
    labels = [0, 0, 1, 1]
    assert entropy(labels) == pytest.approx(math.log(2))


def test_unbalanced_clusters_below_max():
    """7:1 的分裂熵應遠低於 2:2 的均分。"""
    assert entropy([0] * 7 + [1]) < entropy([0] * 4 + [1] * 4)


def test_normalized_entropy_in_unit_interval():
    for labels in ([0] * 8, [0, 1, 2, 3, 4, 5, 6, 7], [0, 0, 1, 1, 2, 2, 3, 3]):
        assert 0.0 <= normalized_entropy(labels) <= 1.0


# ── N=1 與空輸入不炸 ──

def test_single_sample_returns_zero():
    assert entropy([0]) == 0.0
    assert normalized_entropy([0]) == 0.0


def test_empty_returns_zero():
    assert entropy([]) == 0.0
    assert normalized_entropy([]) == 0.0


# ── 分群 ──

def test_cluster_is_transitive():
    """A≡B、B≡C 但 A≢C → 單連結仍應併成一群（連通分量）。"""
    eq = eye(3)
    eq[0][1] = eq[1][0] = True
    eq[1][2] = eq[2][1] = True
    assert len(set(cluster(eq))) == 1


def test_cluster_labels_are_dense_and_ordered():
    eq = eye(4)
    eq[0][3] = eq[3][0] = True
    labels = cluster(eq)
    assert labels[0] == labels[3] == 0
    assert sorted(set(labels)) == list(range(len(set(labels))))


# ── 門檻的單調性 ⭐ ──

def _spread_vectors() -> list[list[float]]:
    """六個逐漸分開的單位向量，餘弦相似度隨距離遞減。"""
    return [[math.cos(t), math.sin(t)]
            for t in (0.0, 0.05, 0.10, 0.60, 0.65, 1.20)]


def test_entropy_is_monotone_in_threshold():
    """門檻越高 → 越難判等價 → 群越多 → 熵越高。單調不遞減。"""
    v = _spread_vectors()
    prev = -1.0
    for thr in (0.0, 0.5, 0.9, 0.98, 0.999, 1.01):
        e = entropy(cluster(equivalence_matrix_embed(v, thr)))
        assert e >= prev - 1e-12, f"門檻 {thr} 時熵下降了（{e} < {prev}）"
        prev = e


def test_threshold_extremes():
    v = _spread_vectors()
    assert entropy(cluster(equivalence_matrix_embed(v, -1.1))) == 0.0
    assert normalized_entropy(cluster(
        equivalence_matrix_embed(v, 1.01))) == pytest.approx(1.0)


def test_equivalence_matrix_is_symmetric_with_true_diagonal():
    m = equivalence_matrix_embed(_spread_vectors(), 0.9)
    for i, row in enumerate(m):
        assert row[i] is True
        for j, x in enumerate(row):
            assert x == m[j][i]


# ── 取樣：必須是單一請求的 n=k ⭐ ──

class FakeClient:
    """記錄呼叫次數與參數。"""

    def __init__(self, outputs: list[str]):
        self.outputs = outputs
        self.calls: list[dict] = []

    def texts(self, role, messages, **kw):
        self.calls.append({"role": role, **kw})
        return list(self.outputs)

    def embed(self, texts, role="embed"):
        # 依首字元給**方向**（不是長度）——用長度做會讓所有向量幾乎同向，
        # 餘弦全部趨近 1，門檻再高也分不開。
        out = []
        for t in texts:
            a = (ord(t[0]) if t else 0) * 0.7
            out.append([math.cos(a), math.sin(a)])
        return out

    def structured(self, role, messages, schema, **kw):
        self.calls.append({"role": role, **kw})
        return {"same": False}, 1


def test_sampling_uses_single_request_with_n_k():
    """⚠️ 這是本檔最重要的一題。改成迴圈呼叫 n 次會撞快取，熵恆為 0。"""
    c = FakeClient(["a", "b", "c", "d", "e", "f", "g", "h"])
    sample_translations(c, "他昨天走了", n=8)
    assert len(c.calls) == 1, f"取樣呼叫了 {len(c.calls)} 次，必須是 1 次 n=8"
    assert c.calls[0]["n"] == 8


def test_sampling_uses_nonzero_temperature():
    """temp=0 時 n=k 會回傳 k 個相同結果，熵恆為 0。"""
    c = FakeClient(["a"] * 4)
    sample_translations(c, "x", n=4)
    assert c.calls[0]["temperature"] > 0


def test_sampling_drops_empty_strings():
    c = FakeClient(["a", "", "b", "   "])
    assert sample_translations(c, "x", n=4) == ["a", "b"]


# ── 端到端（fake client）──

def test_semantic_entropy_all_same_is_zero():
    c = FakeClient(["same one", "same two", "same three", "same four"])
    r = semantic_entropy(c, "x", n=4, method="embed", threshold=0.5)
    assert r.n_clusters == 1 and r.entropy == 0.0 and r.normalized == 0.0


def test_semantic_entropy_all_different_is_one():
    c = FakeClient(["alpha", "beta", "gamma", "delta"])
    r = semantic_entropy(c, "x", n=4, method="embed", threshold=0.999999)
    assert r.n_clusters == 4 and r.normalized == pytest.approx(1.0)


def test_semantic_entropy_records_threshold():
    """§P4：分群門檻必須記錄。"""
    c = FakeClient(["a", "b"])
    assert semantic_entropy(c, "x", n=2, threshold=0.77).threshold == 0.77
    c2 = FakeClient(["a", "b"])
    r = semantic_entropy(c2, "x", n=2, method="llm", mode="unidirectional")
    assert r.threshold == "unidirectional"


def test_semantic_entropy_with_one_sample_does_not_crash():
    c = FakeClient(["only"])
    r = semantic_entropy(c, "x", n=1)
    assert r.entropy == 0.0 and r.normalized == 0.0 and r.n_clusters == 1


def test_semantic_entropy_with_zero_samples_does_not_crash():
    r = semantic_entropy(FakeClient([]), "x", n=8)
    assert r.entropy == 0.0 and r.n_samples == 0


def test_semantic_entropy_rejects_unknown_method():
    with pytest.raises(ValueError):
        semantic_entropy(FakeClient(["a", "b"]), "x", n=2, method="nope")


# ── LLM 等價判定的兩個 mode ──

class FakeJudge:
    """A→B 說 same，B→A 說 not same。用來分辨雙向與單向。"""

    def __init__(self):
        self.n = 0

    def structured(self, role, messages, schema, **kw):
        self.n += 1
        body = messages[-1]["content"]
        a = body.split("\n")[0][3:]
        return {"same": a == "x"}, 1


def test_llm_mode_bidirectional_is_stricter_than_unidirectional():
    texts = ["x", "y"]
    bi = equivalence_matrix_llm(FakeJudge(), texts, mode="bidirectional")
    uni = equivalence_matrix_llm(FakeJudge(), texts, mode="unidirectional")
    assert bi[0][1] is False, "雙向：只有一個方向說 same，不該算等價"
    assert uni[0][1] is True, "單向：任一方向說 same 即算等價"


def test_llm_equivalence_asks_both_directions():
    j = FakeJudge()
    equivalence_matrix_llm(j, ["a", "b", "c"])
    assert j.n == 6, f"3 個樣本應問 3 對 × 2 方向 = 6 次，實際 {j.n}"


def test_llm_equivalence_rejects_unknown_mode():
    with pytest.raises(ValueError):
        equivalence_matrix_llm(FakeJudge(), ["a", "b"], mode="whatever")
