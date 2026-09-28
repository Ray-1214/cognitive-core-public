"""語意熵 S8（v3 架構書 §P4）。

取樣 N 個譯文 → 判定哪些在語意上等價 → 分群 → 算群的熵。
直覺：同一個中文句子若有多種互不相容的讀法，取樣出來的譯文會分裂成
好幾群；若只有一種讀法，N 個譯文只是措辭不同，會併成一群。

Kuhn et al. (2023)、Farquhar et al. (2024) 的離散版本。

## 兩個實作陷阱

1. **必須用單一請求的 `n=k` 取樣，不可重複呼叫。**（§P4）
   本專案的端點會對相同請求回傳快取，重複呼叫 k 次會拿到 k 個一模一樣的
   譯文，熵恆為 0。這個 bug 在 S0c 已經發生過一次。

2. **分群門檻要可調且記錄。**
   提供兩種等價判定：
     - `llm`   雙向蘊涵，由 judge 判（門檻是 `mode`：雙向 or 單向）
     - `embed` 餘弦相似度 ≥ threshold（門檻是連續值，可做敏感度分析）
   兩者都走 union-find 取連通分量（等價於單連結聚合分群）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..llm import Client
from ..similarity import cosine

DEFAULT_N = 8
DEFAULT_TEMPERATURE = 1.0
DEFAULT_EMBED_THRESHOLD = 0.92

EQUIV_SYS = (
    "You judge whether two English sentences convey the same meaning.\n"
    'Answer with JSON only: {"same": true|false}\n'
    "They are the same if a reader would draw the same conclusions about who did "
    "what to whom. Differences in wording, register, or word order do not matter. "
    "Differences in who acts, what is referred to, or which sense a word carries "
    "do matter.")


# ─────────────── 取樣 ───────────────

def sample_translations(client: Client, sentence: str, *, n: int = DEFAULT_N,
                        temperature: float = DEFAULT_TEMPERATURE,
                        role: str = "translate") -> list[str]:
    """單一請求取 n 個樣本。⚠️ 不可改成呼叫 n 次——會撞快取，熵恆為 0。"""
    from .wsd import TRANSLATE_SYS

    out = client.texts(role,
                       [{"role": "system", "content": TRANSLATE_SYS},
                        {"role": "user", "content": sentence}],
                       temperature=temperature, n=n, max_tokens=200)
    return [t.strip() for t in out if t and t.strip()]


# ─────────────── 等價矩陣 ───────────────

def equivalence_matrix_embed(vectors: list[list[float]],
                             threshold: float = DEFAULT_EMBED_THRESHOLD) -> list[list[bool]]:
    """餘弦相似度 ≥ threshold 即視為等價。threshold 越高群越多、熵越高。"""
    k = len(vectors)
    return [[i == j or cosine(vectors[i], vectors[j]) >= threshold
             for j in range(k)] for i in range(k)]


def equivalence_matrix_llm(client: Client, texts: list[str], *,
                           role: str = "judge",
                           mode: str = "bidirectional") -> list[list[bool]]:
    """兩兩問 judge 是否語意相同。

    `mode="bidirectional"` 兩個方向都說 same 才算等價（嚴格，群較多）；
    `mode="unidirectional"` 任一方向說 same 即算（寬鬆，群較少）。
    """
    if mode not in ("bidirectional", "unidirectional"):
        raise ValueError(f"未知的 mode：{mode}")
    k = len(texts)
    eq = [[i == j for j in range(k)] for i in range(k)]
    schema = {"type": "object", "properties": {"same": {"type": "boolean"}},
              "required": ["same"]}
    for i in range(k):
        for j in range(i + 1, k):
            def ask(a: str, b: str) -> bool:
                obj, _ = client.structured(
                    role,
                    [{"role": "system", "content": EQUIV_SYS},
                     {"role": "user", "content": f"A: {a}\nB: {b}"}],
                    schema, max_tokens=60)
                return bool(obj.get("same"))
            ab = ask(texts[i], texts[j])
            ba = ask(texts[j], texts[i])
            same = (ab and ba) if mode == "bidirectional" else (ab or ba)
            eq[i][j] = eq[j][i] = same
    return eq


# ─────────────── 分群與熵 ───────────────

def cluster(eq: list[list[bool]]) -> list[int]:
    """union-find 取連通分量。回傳每個樣本的群編號（0 起，依首次出現排序）。"""
    k = len(eq)
    parent = list(range(k))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(k):
        for j in range(i + 1, k):
            if eq[i][j]:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)
    seen: dict[int, int] = {}
    out = []
    for i in range(k):
        r = find(i)
        if r not in seen:
            seen[r] = len(seen)
        out.append(seen[r])
    return out


def entropy(labels: list[int]) -> float:
    """群大小分布的夏農熵（nats）。全部同群 → 0；各自成群 → log(N)。"""
    n = len(labels)
    if n <= 1:
        return 0.0
    counts: dict[int, int] = {}
    for x in labels:
        counts[x] = counts.get(x, 0) + 1
    # +0.0 消掉全同群時的 -0.0——報表印 "-0.000" 會被誤讀成負熵
    return -sum((c / n) * math.log(c / n) for c in counts.values()) + 0.0


def normalized_entropy(labels: list[int]) -> float:
    """除以 log(N) 正規化到 [0,1]，供訊號介面使用。N≤1 時回 0。"""
    n = len(labels)
    if n <= 1:
        return 0.0
    return min(entropy(labels) / math.log(n), 1.0)


@dataclass(frozen=True)
class EntropyResult:
    entropy: float            # nats
    normalized: float         # [0,1]
    n_samples: int
    n_clusters: int
    labels: list[int]
    samples: list[str]
    method: str               # "llm" / "embed"
    threshold: float | str    # 門檻，必須記錄（§P4）


def semantic_entropy(client: Client, sentence: str, *, n: int = DEFAULT_N,
                     method: str = "embed",
                     threshold: float = DEFAULT_EMBED_THRESHOLD,
                     mode: str = "bidirectional",
                     temperature: float = DEFAULT_TEMPERATURE) -> EntropyResult:
    samples = sample_translations(client, sentence, n=n, temperature=temperature)
    if len(samples) <= 1:
        return EntropyResult(0.0, 0.0, len(samples), len(samples),
                             [0] * len(samples), samples, method,
                             threshold if method == "embed" else mode)
    if method == "embed":
        vecs = client.embed(samples)
        eq = equivalence_matrix_embed(vecs, threshold)
        thr: float | str = threshold
    elif method == "llm":
        eq = equivalence_matrix_llm(client, samples, mode=mode)
        thr = mode
    else:
        raise ValueError(f"未知的 method：{method}")
    labels = cluster(eq)
    return EntropyResult(entropy(labels), normalized_entropy(labels),
                         len(samples), len(set(labels)), labels, samples,
                         method, thr)
