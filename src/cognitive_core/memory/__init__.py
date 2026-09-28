"""記憶模組（v3 架構書 §P7，RQ3）。

ChromaDB 存對話歷史 + 滾動摘要 + 餘弦檢索。

## 三個設計決定

**有錨點時錨點一併存。** 錨點的資訊密度高於原始訊息——它已經把讀法、
未知欄位、文化專有項顯性化了。檢索時命中錨點比命中原句更有用。

**滾動摘要優先壓縮沒有錨點的訊息。** 有錨點的訊息是後續對話會回頭參照的，
壓掉它們等於把最有用的東西丟了。

**摘要後原始訊息不可再被完整取回。** 這不是缺陷是定義——若原文還在，
就沒有真的壓縮，Lost-in-the-Middle 的對照組就不成立。
`test_memory.py` 有一支測試釘住這件事。

⚠️ RQ3 只有 n=10 組長對話，**不足以下定論**，圖說與報告都要標為初步驗證。
"""

from .store import (
    MemoryEntry,
    MemoryStore,
    RollingSummary,
    SummaryConfig,
)

__all__ = ["MemoryEntry", "MemoryStore", "RollingSummary", "SummaryConfig"]
