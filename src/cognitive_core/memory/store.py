"""記憶儲存與檢索（v3 架構書 §P7）。

嵌入函式可注入，測試用合成向量即可，不必呼叫 API。
ChromaDB 為選用後端——未安裝時退回純 Python 的記憶體實作，
兩者的檢索語意相同（餘弦相似度 top-k），測試對兩者跑同一套斷言。
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Sequence

Embedder = Callable[[list[str]], list[list[float]]]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


@dataclass
class MemoryEntry:
    id: str
    text: str
    role: str = "user"
    turn: int = 0
    anchor: dict | None = None
    summarised: bool = False        # 已被滾動摘要壓縮，原文不再保留
    ts: float = field(default_factory=time.time)

    @property
    def searchable(self) -> str:
        """檢索用文字。有錨點時把讀法與未知欄位一併納入——資訊密度較高。"""
        if not self.anchor:
            return self.text
        u = self.anchor.get("uncertainty") or {}
        readings = [r.get("reading", "") for r in
                    (u.get("alternative_readings") or []) if isinstance(r, dict)]
        unknowns = self.anchor.get("unknown_scalars") or []
        extra = "　".join([*readings, *unknowns])
        return f"{self.text}　{extra}".strip()


@dataclass
class SummaryConfig:
    window: int = 12          # 超過幾則就觸發滾動摘要
    keep_recent: int = 6      # 保留最近幾則不壓縮
    max_summary_chars: int = 120


class RollingSummary:
    """滾動摘要。有錨點者優先保留，沒有錨點的先被壓。

    ⚠️ 壓縮後原文以摘要取代且不可還原。若原文還在就沒有真的壓縮，
    Lost-in-the-Middle 的對照就不成立。
    """

    def __init__(self, cfg: SummaryConfig | None = None,
                 summariser: Callable[[list[str]], str] | None = None):
        self.cfg = cfg or SummaryConfig()
        self.summariser = summariser or self._default_summariser

    def _default_summariser(self, texts: list[str]) -> str:
        """不呼叫 API 的預設摘要：取各則首句並截斷。

        用 LLM 摘要會讓 Lost-in-the-Middle 的結果混進摘要模型的能力，
        那是另一個變因。預設用確定性規則，需要時再注入 LLM 版本。
        """
        heads = []
        for t in texts:
            head = t.strip().split("。")[0].strip()
            if head:
                heads.append(head[:24])
        s = "；".join(heads)
        return s[:self.cfg.max_summary_chars]

    def should_compress(self, entries: list[MemoryEntry]) -> bool:
        return len(entries) > self.cfg.window

    def compress(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        """回傳壓縮後的清單。輸入不被就地修改。"""
        if not self.should_compress(entries):
            return list(entries)
        keep = self.cfg.keep_recent
        old, recent = entries[:-keep], entries[-keep:]
        # 有錨點者不壓——它們是後續對話會回頭參照的
        anchored = [e for e in old if e.anchor]
        plain = [e for e in old if not e.anchor]
        out: list[MemoryEntry] = list(anchored)
        if plain:
            text = self.summariser([e.text for e in plain])
            out.append(MemoryEntry(
                id=f"sum-{uuid.uuid4().hex[:8]}", text=text, role="summary",
                turn=min(e.turn for e in plain), summarised=True))
        out.sort(key=lambda e: e.turn)
        return out + recent


class MemoryStore:
    """對話記憶。`backend="chroma"` 用 ChromaDB，否則用記憶體實作。

    ## ⚠️ 向量庫是長期儲存，滾動摘要只管脈絡

    第一版把兩者混在一起——`add()` 觸發滾動摘要，摘要順手把舊項目從
    向量庫刪掉。結果是檢索再也找不到被壓掉的內容，Lost-in-the-Middle
    的實驗組召回率跟對照組一樣是 0%。

    正確的分工：

        向量庫        存全部歷史，永不刪除 —— `search()` / `recall()` 走這裡
        滾動摘要      決定**送進模型脈絡**的是什麼 —— `context()` 走這裡

    兩者都需要：脈絡有長度上限所以要摘要，但摘要不該讓資訊永久消失，
    否則記憶模組就退化成一個比較貴的固定視窗。
    """

    def __init__(self, embedder: Embedder, *, backend: str = "memory",
                 summary: RollingSummary | None = None,
                 collection: str = "cognitive_core"):
        self.embed = embedder
        self.summary = summary or RollingSummary()
        self.entries: list[MemoryEntry] = []
        self._vecs: dict[str, list[float]] = {}
        self._turn = 0
        self.backend = backend
        self._col = None
        if backend == "chroma":
            import chromadb
            self._client = chromadb.EphemeralClient()
            self._col = self._client.get_or_create_collection(collection)

    # ── 寫入 ──

    def add(self, text: str, *, role: str = "user",
            anchor: dict | None = None) -> MemoryEntry:
        """存入長期記憶。**不觸發壓縮**——壓縮只影響脈絡，見 `context()`。"""
        self._turn += 1
        e = MemoryEntry(id=uuid.uuid4().hex[:12], text=text, role=role,
                        turn=self._turn, anchor=anchor)
        self.entries.append(e)
        self._index([e])
        return e

    def _index(self, items: list[MemoryEntry]) -> None:
        if not items:
            return
        vecs = self.embed([e.searchable for e in items])
        for e, v in zip(items, vecs):
            self._vecs[e.id] = v
        if self._col is not None:
            self._col.upsert(ids=[e.id for e in items],
                             embeddings=vecs,
                             documents=[e.text for e in items],
                             metadatas=[{"role": e.role, "turn": e.turn,
                                         "summarised": e.summarised}
                                        for e in items])

    # ── 脈絡（受滾動摘要壓縮）──

    def context(self) -> list[MemoryEntry]:
        """要送進模型脈絡的內容。長度受滾動摘要控制。

        ⚠️ 這裡的壓縮**不影響向量庫**——`search()` 仍看得到全部歷史。
        """
        return self.summary.compress(self.entries)

    def augmented_context(self, query: str, k: int = 3) -> list[MemoryEntry]:
        """脈絡 + 檢索補回來的舊項目。這才是「有記憶」的完整行為。

        滾動摘要壓掉的東西，若與當前查詢相關就由檢索補回，
        所以資訊不會像固定視窗那樣永久掉出。
        """
        ctx = self.context()
        have = {e.id for e in ctx}
        for e, _ in self.search(query, k):
            if e.id not in have:
                ctx.append(e)
                have.add(e.id)
        return ctx

    # ── 檢索（走全部歷史，不受摘要影響）──

    def search(self, query: str, k: int = 3) -> list[tuple[MemoryEntry, float]]:
        if not self.entries:
            return []
        qv = self.embed([query])[0]
        scored = [(e, cosine(qv, self._vecs.get(e.id, []))) for e in self.entries]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]

    def recall(self, query: str, k: int = 3) -> list[str]:
        return [e.text for e, _ in self.search(query, k)]

    def get(self, entry_id: str) -> MemoryEntry | None:
        return next((e for e in self.entries if e.id == entry_id), None)

    def __len__(self) -> int:
        return len(self.entries)
