# Cognitive-Core 專案完整架構與技術規格書

> **專案名稱**：Cognitive-Core（基於代理人工作流與多視角語意驗證之自適應認知框架）  
> **版本**：v1.1（架構設計 + 分階段 Checklist + 骨架程式碼）  
> **目標**：讓開發者能直接拿這份文件在 VS Code 中與 AI 討論，並逐步實作完整系統。  
> **技術棧核心**：Python 3.10+ / Ollama (Llama-3-8B-GGUF) / LangGraph / ChromaDB / Streamlit  
> **硬體目標**：單張 RTX 4060 Ti 16GB 或同等級（4-bit 量化）  
> **更新**：新增 Phase 0～7 詳細 Checklist、完成定義（DoD）、各階段可複製骨架程式碼

---

## 目錄

1. [專案目標與核心問題](#1-專案目標與核心問題)
2. [系統整體架構總覽](#2-系統整體架構總覽)
3. [資料流與決策流程](#3-資料流與決策流程)
4. [核心模組詳細設計](#4-核心模組詳細設計)
5. [技術棧與依賴](#5-技術棧與依賴)
6. [推薦專案目錄結構](#6-推薦專案目錄結構)
7. [狀態機 (LangGraph) 設計](#7-狀態機-langgraph-設計)
8. [關鍵演算法與偽代碼](#8-關鍵演算法與偽代碼)
9. [Prompt 工程設計](#9-prompt-工程設計)
10. [評測與資料集](#10-評測與資料集)
11. [開發環境與部署](#11-開發環境與部署)
12. [風險與因應對策](#12-風險與因應對策)
13. [分階段實作 Checklist 與骨架程式碼](#13-分階段實作-checklist-與骨架程式碼)
14. [可參考的開源專案](#14-可參考的開源專案)
15. [附錄：重要公式與配置](#15-附錄重要公式與配置)

---

## 1. 專案目標與核心問題

### 1.1 核心目標
建立一套**具備後設認知（Metacognition）能力**的本地端 AI 系統，能在回答前先「停下來思考、比對、驗證」，特別針對高語境語言（如中文）的歧義與幻覺問題。

### 1.2 三個核心研究問題
1. **歧義性自動化偵測**：如何讓模型知道自己「沒聽懂」？利用日文敬語、英文時態等結構差異作為探針。
2. **算力與準確度平衡**：在有限 VRAM 下，簡單問題走快速通道，複雜問題才啟動多代理人驗證。
3. **長文本記憶優化**：結合 RAG + 滾動摘要，避免 Lost in the Middle。

### 1.3 成功指標（預期）
- 高歧義語句的語意一致性（BERTScore / Self-Consistency Score）顯著優於 Zero-shot 基準。
- 在 CAD-100 自建測試集上，語意保留度與文化適配性有明顯提升。
- 系統能在本地 RTX 4060 Ti 等級硬體上穩定運行。

---

## 2. 系統整體架構總覽

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Web UI (Streamlit)                              │
│  左側：原始對話視窗          │  右側：決策摘要 (Decision Summary) + 信心分數  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LangGraph 狀態機 (Orchestrator)                       │
│                                                                             │
│  User Input ──► Semantic Router ──┬── Fast Path (Simple) ──► Final Output   │
│                                   │                                         │
│                                   └── Slow Path (Complex)                   │
│                                           │                                 │
│                                           ▼                                 │
│                                   Multi-View Verifier                       │
│                                   (日文 + 英文三角測量)                      │
│                                           │                                 │
│                                           ▼                                 │
│                                   Uncertainty-Aware Decision                │
│                                   (Reflection / 多解釋 / 澄清提示)            │
│                                           │                                 │
│                                           ▼                                 │
│                                   Dynamic Memory (ChromaDB + Rolling Summary)│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           底層推論引擎                                       │
│  Ollama (Llama-3-8B-Instruct Q4_K_M GGUF)  +  Embeddings (nomic-embed-text) │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 三大核心模組
| 模組 | 職責 | 輸入 | 輸出 |
|------|------|------|------|
| **Semantic Router** | 判斷問題複雜度 / 歧義程度 | 原始文本 | Fast / Slow 路徑決策 + 歧義分數 |
| **Multi-View Verifier** | 多語言平行翻譯 + 回譯 + 餘弦相似度 + 反思 | 源文本 | 驗證後翻譯 / 歧義標記 / 修正建議 |
| **Dynamic Memory** | 長短期記憶管理 | 對話歷史 | 檢索結果 + 滾動摘要 |

### 2.2 不確定性感知決策機制
系統在以下任一條件成立時進入「高不確定性狀態」：
1. 多語言回譯後向量餘弦相似度 < τ
2. 不同語言版本語用推論衝突
3. 跨語言 PPL 變異數過高

進入高不確定性後可採取：
- 觸發 Reflection Agent
- 生成多個可能語意解釋並標示適用情境
- 回傳澄清提示給使用者

---

## 3. 資料流與決策流程

### 3.1 主流程（高階）
```
1. User Input (中文高語境文本)
2. Semantic Router 計算 Cross-Lingual PPL Variance + 其他歧義指標
3. if 簡單 → Fast Path：直接翻譯 / 回答 → 輸出
4. if 複雜 → Slow Path：
   a. 平行翻譯成 English + Japanese
   b. 回譯成中文
   c. 計算 Embed(Ven) 與 Embed(Vjp) 的 Cosine Similarity
   d. if Score < τ → 啟動 Reflection Agent
   e. 產出最終驗證結果 + 決策摘要
5. 更新 Dynamic Memory
6. 回傳給 Web UI（含思考過程摘要，但不暴露完整 CoT）
```

### 3.2 多視角語意三角測量詳細流程
```
Source Text (Tsrc)
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
  Translate to EN    Translate to JP    (可選第三語言)
       │                  │
       ▼                  ▼
  Back-Translate     Back-Translate
  to Chinese (Ven)   to Chinese (Vjp)
       │                  │
       └────────┬─────────┘
                ▼
     CosineSimilarity(Embed(Ven), Embed(Vjp))
                │
        ┌───────┴───────┐
        ▼               ▼
   Score ≥ τ        Score < τ
   (低歧義)          (高歧義)
        │               │
        ▼               ▼
   接受 Ten         IdentifyDiff + ReflectionAgent
        │               │
        └───────┬───────┘
                ▼
           Tfinal
```

---

## 4. 核心模組詳細設計

### 4.1 Semantic Router（自適應語意路由器）

**目標**：在有限算力下分流簡單/複雜問題。

**歧義指標設計（建議實作）**：
- **Cross-Lingual PPL Variance**：將源文本經不同路徑回譯後，計算各版本 Perplexity 的變異數。變異數高 → 模型對語意缺乏信心。
- 可選輔助指標：
  - 詞彙歧義密度（多義詞比例）
  - 省略主詞 / 指代不明程度（可用簡單規則或輕量 LLM 判斷）
  - 句子長度與複雜度

**實作建議**：
- 可用輕量模型或規則 + embedding 相似度快速判斷。
- 也可整合 `aurelio-labs/semantic-router` 作為路由層，再用自訂指標補強。
- 輸出應為結構化：`{"path": "fast"|"slow", "ambiguity_score": float, "reason": str}`

### 4.2 Multi-View Verifier（多視角驗證代理人）

**核心推論引擎**：`Meta-Llama-3-8B-Instruct`（透過 Ollama，4-bit GGUF）

**語言選擇原則（語法強制顯性化）**：
- **English**：強制時態與名詞單複數 → 消除時間與數量歧義
- **Japanese**：嚴謹敬語與社會關係標記 → 顯性化中文隱含語用資訊

**步驟**：
1. 平行翻譯：`Tsrc → Ten`、`Tsrc → Tjp`
2. 回譯：`Ten → Ven`、`Tjp → Vjp`
3. Embedding + Cosine Similarity
4. 若低於閾值 → 呼叫 Reflection Agent，輸出 JSON 結構化結果

**建議閾值 τ**：初期可設 0.75~0.85，後續用驗證集調參。

### 4.3 Dynamic Memory（動態記憶模組）

- **向量資料庫**：ChromaDB（本地持久化）
- **Embedding 模型**：建議 `nomic-embed-text`（Ollama）或 `bge-m3`
- **技術**：
  - 短期：對話歷史 sliding window
  - 長期：Rolling Summary（滾動摘要）
  - 檢索：Cosine Similarity top-k
- **解決問題**：Lost in the Middle

### 4.4 Uncertainty-Aware Decision Flow

當偵測到高不確定性時：
1. Reflection Agent 重新分析歧義來源
2. 生成多個可能解釋 + 適用情境
3. 互動場景下回傳澄清提示

此設計對齊 AI Safety 的「保守回應」與「可解釋不確定性」。

### 4.5 Web 介面（Streamlit）

- 左側：原始對話視窗
- 右側：Decision Summary（判斷依據、信心分數、路徑選擇）
- **安全考量**：不直接暴露完整 Chain-of-Thought，僅顯示摘要

---

## 5. 技術棧與依賴

### 5.1 硬體（計畫書規格）
| 項目 | 規格 |
|------|------|
| CPU | Intel Core i9-13900K 或同等 |
| GPU | NVIDIA RTX 4060 Ti 16GB |
| RAM | 128GB（可接受較低，但建議 ≥32GB） |

### 5.2 軟體環境
| 類別 | 項目 | 版本建議 |
|------|------|----------|
| OS | Ubuntu 22.04 LTS (WSL2 亦可) | - |
| 語言 | Python | 3.10 或 3.11 |
| 推論 | Ollama | 最新穩定版 |
| 模型 | Llama-3-8B-Instruct GGUF Q4_K_M | 透過 Ollama pull |
| 代理人框架 | LangGraph + LangChain | 最新 0.3.x / 1.x |
| 向量庫 | ChromaDB | 最新 |
| UI | Streamlit | 最新 |
| Embedding | nomic-embed-text 或 bge-m3 | Ollama / HuggingFace |

### 5.3 主要 Python 套件（建議 requirements.txt 起點）
```text
langgraph>=0.2.0
langchain>=0.3.0
langchain-ollama>=0.2.0
langchain-community
chromadb
streamlit
pydantic>=2.0
numpy
scikit-learn          # 計算 cosine similarity 等
sentence-transformers # 備選 embedding
tiktoken
python-dotenv
```

### 5.4 模型下載指令
```bash
ollama pull llama3.1:8b          # 或 llama3:8b
ollama pull nomic-embed-text
# 若要用量化 GGUF 直接跑，也可使用 llama.cpp 相關工具
```

---

## 6. 推薦專案目錄結構

```text
Cognitive-Core/
├── README.md
├── pyproject.toml / requirements.txt
├── .env.example
├── configs/
│   ├── models.yaml              # 模型名稱、溫度、τ 閾值等
│   ├── prompts.yaml             # 所有 System Prompt
│   └── router_thresholds.yaml
├── src/
│   ├── __init__.py
│   ├── main.py                  # 入口（或 api.py）
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py             # TypedDict / Pydantic State
│   │   ├── nodes.py             # 各節點函式
│   │   ├── edges.py             # 條件路由邏輯
│   │   └── builder.py           # 組裝 StateGraph
│   ├── agents/
│   │   ├── router.py            # Semantic Router
│   │   ├── translator.py        # 多語言翻譯
│   │   ├── verifier.py          # Multi-View Verifier
│   │   ├── reflection.py        # Reflection Agent
│   │   └── memory.py            # Dynamic Memory
│   ├── core/
│   │   ├── embeddings.py
│   │   ├── similarity.py        # Cosine + PPL variance
│   │   ├── llm.py               # ChatOllama 封裝
│   │   └── uncertainty.py
│   ├── ui/
│   │   └── streamlit_app.py
│   └── utils/
│       ├── prompts.py
│       └── logging.py
├── data/
│   ├── cad100/                  # 自建高歧義測試集
│   └── wmt23/                   # 基準資料
├── eval/
│   ├── metrics.py               # BERTScore, Self-Consistency
│   ├── human_eval_protocol.md
│   └── run_eval.py
├── tests/
│   ├── test_router.py
│   ├── test_triangulation.py
│   └── test_memory.py
├── notebooks/                   # 實驗用
└── scripts/
    ├── setup_ollama.sh
    └── build_cad100.py
```

---

## 7. 狀態機 (LangGraph) 設計

### 7.1 建議 State Schema（TypedDict 或 Pydantic）

```python
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph.message import add_messages
import operator

class GraphState(TypedDict):
    # 輸入
    source_text: str
    messages: Annotated[list, add_messages]
    
    # Router 輸出
    path: Literal["fast", "slow"]
    ambiguity_score: float
    router_reason: str
    
    # Multi-View
    trans_en: Optional[str]
    trans_jp: Optional[str]
    back_en: Optional[str]      # Ven
    back_jp: Optional[str]      # Vjp
    consistency_score: Optional[float]
    
    # Uncertainty & Reflection
    is_high_uncertainty: bool
    ambiguity_detected: bool
    reflection_details: Optional[str]
    suggested_refinement: Optional[str]
    
    # 最終輸出
    final_output: Optional[str]
    decision_summary: Optional[dict]
    
    # Memory
    retrieved_context: Optional[List[str]]
    rolling_summary: Optional[str]
```

### 7.2 節點建議
- `router_node`
- `fast_path_node`
- `translate_multi_view_node`
- `back_translate_node`
- `similarity_check_node`
- `reflection_node`
- `memory_update_node`
- `finalize_node`

### 7.3 條件邊邏輯
```python
def route_after_router(state: GraphState) -> str:
    if state["path"] == "fast":
        return "fast_path"
    return "multi_view"

def route_after_similarity(state: GraphState) -> str:
    if state["consistency_score"] < THRESHOLD:
        return "reflection"
    return "finalize"
```

---

## 8. 關鍵演算法與偽代碼

### 8.1 Semantic Triangulation（計畫書 Algorithm 1）

```text
Algorithm: Multi-View Semantic Triangulation
Input: Source Text Tsrc, Threshold τ
Output: Final Verified Translation Tfinal

1. Ten ← Translate(Tsrc, English)
2. Tjp ← Translate(Tsrc, Japanese)
3. Ven ← BackTranslate(Ten, Chinese)
4. Vjp ← BackTranslate(Tjp, Chinese)
5. Score ← CosineSimilarity(Embed(Ven), Embed(Vjp))
6. if Score < τ then
       Details ← IdentifyDiff(Ven, Vjp)
       Tfinal ← ReflectionAgent(Tsrc, Details)
   else
       Tfinal ← Ten   # 或根據任務選擇最適語言版本
7. return Tfinal
```

### 8.2 Cross-Lingual PPL Variance（Router 核心指標）
```text
1. 產生多個回譯版本
2. 對每個版本計算 Perplexity（可用模型本身或輕量模型）
3. Variance = Var({PPL1, PPL2, ...})
4. 若 Variance > 安全閾值 → 判定高歧義 → Slow Path
```

### 8.3 Self-Consistency Score
```text
Score_consistency = 1 - Var({Ven, Vjp, Ves})   # 向量空間變異數
```

### 8.4 Cosine Similarity
```text
Similarity(A, B) = (A · B) / (||A|| ||B||)
```

---

## 9. Prompt 工程設計

### 9.1 Verifier Agent System Prompt（計畫書 Table 2 擴充）

```text
Role: You are a senior linguistic expert proficient in English, Japanese, and Chinese.

Task: Compare the source text with its translations. Identify any semantic discrepancies based on cultural nuances (e.g., honorifics in Japanese, tense in English).

Input format (JSON):
{
  "source": "...",
  "trans_en": "...",
  "trans_jp": "..."
}

Output Format (JSON Only):
{
  "consistency_score": (float 0.0-1.0),
  "ambiguity_detected": (boolean),
  "reasoning": "Explain the difference in nuance...",
  "suggested_refinement": "..."
}
```

### 9.2 Reflection Agent 建議結構
- 明確指出歧義類型（Lexical / Referential / Pragmatic）
- 列出可能解釋
- 給出 refinement 建議
- 強制 JSON 輸出（可用 `with_structured_output`）

### 9.3 翻譯 Prompt 注意事項
- 要求保留文化語用資訊
- 日文版本特別要求正確使用敬語等級
- 英文版本要求明確時態與單複數

---

## 10. 評測與資料集

### 10.1 資料集
1. **WMT23 Chinese-English**：一般翻譯基準
2. **CAD-100**（自建）：100 句含雙關語、成語、省略主詞的高歧義中文句子（例：「意思意思」、「方便」）

### 10.2 自動化指標
- **BERTScore**
- **Self-Consistency Score**（多版本回譯向量變異數）
- 可選：BLEU、COMET

### 10.3 人類評測協定
- 評測人員：3 位中英日三語能力者
- 樣本：CAD-100 隨機抽 30 句
- 指標：Likert 1-5（語意精確度、文化得體性）
- 一致性：Fleiss’ Kappa

### 10.4 預備實驗參考（計畫書模擬數據）
| 測試項目     | Zero-shot | Multi-View | 改善幅度 |
|--------------|-----------|------------|----------|
| 語意保留度   | 45%       | 85%        | +40%     |
| 文化適配性   | 50%       | 80%        | +30%     |

---

## 11. 開發環境與部署

### 11.1 本地開發流程建議
```bash
# 1. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 確認 Ollama 運行
ollama serve
ollama list

# 4. 啟動 Streamlit
streamlit run src/ui/streamlit_app.py
```

### 11.2 量化與效能
- 使用 4-bit GGUF 降低 VRAM
- Semantic Router 必須夠快（避免每句都跑完整驗證）
- 可考慮將部分運算 offload 到 RAM（llama.cpp）

### 11.3 環境變數（.env）
```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
CONSISTENCY_THRESHOLD=0.80
CHROMA_PERSIST_DIR=./chroma_db
```

---

## 12. 風險與因應對策

| 風險 | 對策 |
|------|------|
| 推論延遲過高 | Semantic Router 分流 + 4-bit 量化 + 只對高歧義啟動完整驗證 |
| 模型在解釋歧義時產生新幻覺 | 引入 RAG（成語/流行語知識庫）強制 grounded |
| GPU 顯存不足 | GGUF + llama.cpp offload 到 RAM |
| 系統不保證絕對正確 | 明確目標是「提升語意穩定性與降低高歧義錯誤」，並提供不確定性提示 |

---

## 13. 分階段實作 Checklist 與骨架程式碼

> **使用方式**：每完成一個子項目就打勾 `[x]`。每個階段都有「完成定義（Definition of Done）」與對應骨架程式碼，可直接複製到 VS Code 再請 AI 幫你補完。

### 階段總覽（對應 8 個月甘特）

| 階段 | 名稱 | 預估時間 | 核心產出 |
|------|------|----------|----------|
| Phase 0 | 環境與專案骨架 | 3～7 天 | 可跑的空專案 + Ollama 通 |
| Phase 1 | 基本翻譯 Pipeline（MVP 核心） | 1～2 週 | 中→英/日 + 回譯 + similarity |
| Phase 2 | Multi-View Verifier + Reflection | 2～3 週 | Algorithm 1 完整可跑 |
| Phase 3 | Semantic Router | 1～2 週 | Fast/Slow 分流可用 |
| Phase 4 | Dynamic Memory | 1～2 週 | Chroma + Rolling Summary |
| Phase 5 | LangGraph 完整狀態機 | 2 週 | 閉環 Orchestrator |
| Phase 6 | Streamlit Web UI | 1～2 週 | 可演示介面 |
| Phase 7 | 評測、優化、開源與論文 | 3～4 週 | CAD-100 結果 + 套件 |

---

### Phase 0：環境與專案骨架

#### Checklist
- [ ] 安裝 Python 3.10 或 3.11
- [ ] 建立虛擬環境（`.venv`）並啟用
- [ ] 安裝 Ollama，確認 `ollama serve` 可運行
- [ ] `ollama pull llama3.1:8b`（或 llama3:8b）成功
- [ ] `ollama pull nomic-embed-text` 成功
- [ ] 建立專案目錄結構（見第 6 章）
- [ ] 寫好 `requirements.txt` 並 `pip install -r requirements.txt`
- [ ] 建立 `.env` 與 `.env.example`
- [ ] 寫一個最簡單的 `test_ollama.py`，能成功呼叫模型回傳文字
- [ ] Git init + 第一次 commit

#### 完成定義（DoD）
能在終端機執行一段 Python，成功呼叫本地 Llama 並印出回答。

#### 骨架程式碼

**`requirements.txt`**
```text
langgraph>=0.2.0
langchain>=0.3.0
langchain-ollama>=0.2.0
langchain-community
chromadb
streamlit
pydantic>=2.0
numpy
python-dotenv
scikit-learn
tiktoken
```

**`.env.example`**
```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
CONSISTENCY_THRESHOLD=0.80
CHROMA_PERSIST_DIR=./chroma_db
```

**`src/core/llm.py`（骨架）**
```python
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

def get_llm(temperature: float = 0.3, model: str | None = None) -> ChatOllama:
    return ChatOllama(
        model=model or os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=temperature,
    )

# 快速測試
if __name__ == "__main__":
    llm = get_llm()
    print(llm.invoke("用一句話介紹你自己").content)
```

**`scripts/setup_check.py`**
```python
from src.core.llm import get_llm

def main():
    llm = get_llm(temperature=0)
    resp = llm.invoke("Reply with exactly: OK")
    print("Ollama status:", resp.content)

if __name__ == "__main__":
    main()
```

---

### Phase 1：基本翻譯 Pipeline（MVP 核心）

#### Checklist
- [ ] 實作 `translate(text, target_lang)` 函式（支援 en / ja）
- [ ] 實作 `back_translate(text, source_lang="zh")`
- [ ] 實作 embedding 函式（用 Ollama nomic-embed-text 或 sentence-transformers）
- [ ] 實作 `cosine_similarity(vec1, vec2)`
- [ ] 寫一個 CLI 或 notebook：輸入一句中文 → 輸出 EN、JP、回譯、similarity 分數
- [ ] 用 5～10 句簡單中文測試，確認流程可跑通
- [ ] 把結果印成結構化 dict / JSON

#### 完成定義（DoD）
輸入「今天天氣真好」這類句子，能看到英文翻譯、日文翻譯、兩個回譯版本，以及一個 0～1 的相似度分數。

#### 骨架程式碼

**`src/core/embeddings.py`**
```python
import os
from langchain_ollama import OllamaEmbeddings
import numpy as np

def get_embeddings():
    return OllamaEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )

def embed_text(text: str) -> list[float]:
    emb = get_embeddings()
    return emb.embed_query(text)

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
```

**`src/agents/translator.py`**
```python
from src.core.llm import get_llm

TRANSLATE_PROMPT = """You are a professional translator.
Translate the following Chinese text into {target_lang}.
Keep cultural nuances and do not add explanations.
Only output the translation.

Text: {text}
"""

def translate(text: str, target_lang: str = "English") -> str:
    llm = get_llm(temperature=0.3)
    prompt = TRANSLATE_PROMPT.format(target_lang=target_lang, text=text)
    return llm.invoke(prompt).content.strip()

def back_translate(text: str, from_lang: str = "English") -> str:
    llm = get_llm(temperature=0.3)
    prompt = f"Translate the following {from_lang} text back into Chinese. Only output the Chinese translation.\n\nText: {text}"
    return llm.invoke(prompt).content.strip()
```

**`scripts/test_phase1.py`**
```python
from src.agents.translator import translate, back_translate
from src.core.embeddings import embed_text, cosine_similarity

def run(text: str):
    ten = translate(text, "English")
    tjp = translate(text, "Japanese")
    ven = back_translate(ten, "English")
    vjp = back_translate(tjp, "Japanese")
    score = cosine_similarity(embed_text(ven), embed_text(vjp))
    print({
        "source": text,
        "en": ten,
        "jp": tjp,
        "back_en": ven,
        "back_jp": vjp,
        "consistency_score": round(score, 4),
    })

if __name__ == "__main__":
    run("意思意思就好")
```

---

### Phase 2：Multi-View Verifier + Reflection

#### Checklist
- [ ] 把 Phase 1 流程包裝成 `multi_view_verify(source_text, threshold=0.80)` 函式
- [ ] 實作 `IdentifyDiff`（可用 LLM 比較 Ven 與 Vjp 的差異）
- [ ] 實作 Reflection Agent（輸入 source + details，輸出 refinement）
- [ ] 強制 JSON 結構化輸出（建議用 Pydantic + `with_structured_output` 或手動 parse）
- [ ] 撰寫 Verifier System Prompt（見第 9 章）
- [ ] 用 10 句高歧義句子（雙關、成語）測試
- [ ] 記錄「觸發 reflection 的比例」與耗時

#### 完成定義（DoD）
對「方便一下」這類句子，系統能偵測到低 consistency，並產出帶 reasoning 的修正建議。

#### 骨架程式碼

**`src/agents/verifier.py`**
```python
from pydantic import BaseModel, Field
from src.agents.translator import translate, back_translate
from src.core.embeddings import embed_text, cosine_similarity
from src.core.llm import get_llm
import os

class VerifierResult(BaseModel):
    consistency_score: float
    ambiguity_detected: bool
    reasoning: str
    suggested_refinement: str
    final_translation: str

def multi_view_verify(source: str, threshold: float | None = None) -> VerifierResult:
    threshold = threshold or float(os.getenv("CONSISTENCY_THRESHOLD", "0.80"))
    
    ten = translate(source, "English")
    tjp = translate(source, "Japanese")
    ven = back_translate(ten, "English")
    vjp = back_translate(tjp, "Japanese")
    score = cosine_similarity(embed_text(ven), embed_text(vjp))
    
    if score >= threshold:
        return VerifierResult(
            consistency_score=score,
            ambiguity_detected=False,
            reasoning="Back-translations are consistent.",
            suggested_refinement="",
            final_translation=ten,
        )
    
    # 高歧義 → Reflection
    details = f"EN back: {ven}\nJP back: {vjp}"
    reflection = run_reflection(source, details)
    return VerifierResult(
        consistency_score=score,
        ambiguity_detected=True,
        reasoning=reflection.get("reasoning", ""),
        suggested_refinement=reflection.get("suggested_refinement", ""),
        final_translation=reflection.get("refined", ten),
    )

def run_reflection(source: str, details: str) -> dict:
    llm = get_llm(temperature=0.2)
    prompt = f"""You are a senior linguistic expert.
Source (Chinese): {source}
Back-translation differences:
{details}

Identify semantic discrepancies and suggest a refined English translation.
Reply in JSON only:
{{"reasoning": "...", "suggested_refinement": "...", "refined": "..."}}
"""
    # 簡化版：實際可改用 structured output
    import json
    raw = llm.invoke(prompt).content
    try:
        return json.loads(raw)
    except Exception:
        return {"reasoning": raw, "suggested_refinement": "", "refined": source}
```

---

### Phase 3：Semantic Router

#### Checklist
- [ ] 定義 Router 輸出格式：`{"path": "fast"|"slow", "ambiguity_score": float, "reason": str}`
- [ ] 實作至少一種歧義指標（建議先做「規則 + LLM 輕量判斷」或簡單長度/多義詞）
- [ ] （進階）實作 Cross-Lingual PPL Variance 近似版本
- [ ] 設定閾值，讓簡單句走 fast、歧義句走 slow
- [ ] 寫單元測試：10 句簡單 + 10 句歧義，檢查分流正確率
- [ ] 記錄 fast/slow 比例與平均延遲

#### 完成定義（DoD）
輸入「你好」走 fast；輸入「意思意思」走 slow，且有合理的 ambiguity_score。

#### 骨架程式碼

**`src/agents/router.py`**
```python
from pydantic import BaseModel
from src.core.llm import get_llm
from typing import Literal

class RouterDecision(BaseModel):
    path: Literal["fast", "slow"]
    ambiguity_score: float
    reason: str

ROUTER_PROMPT = """Analyze the Chinese text for semantic ambiguity (pun, omitted subject, pragmatic nuance, multi-meaning words).
Reply JSON only:
{{"path": "fast" or "slow", "ambiguity_score": 0.0-1.0, "reason": "..."}}

Text: {text}
"""

def semantic_route(text: str) -> RouterDecision:
    # 簡單啟發式可先寫在這裡加速
    if len(text) < 8 and not any(w in text for w in ["意思", "方便", "隨便", "再說"]):
        return RouterDecision(path="fast", ambiguity_score=0.1, reason="Short and clear")
    
    llm = get_llm(temperature=0.0)
    raw = llm.invoke(ROUTER_PROMPT.format(text=text)).content
    import json
    try:
        data = json.loads(raw)
        return RouterDecision(**data)
    except Exception:
        return RouterDecision(path="slow", ambiguity_score=0.7, reason="Parse failed, default to slow")
```

---

### Phase 4：Dynamic Memory

#### Checklist
- [ ] 安裝並初始化 ChromaDB（本地 persist）
- [ ] 實作 `add_memory(text, metadata)`
- [ ] 實作 `retrieve(query, top_k=5)`
- [ ] 實作簡單 Rolling Summary（每隔 N 輪或 token 超過閾值就摘要）
- [ ] 把檢索結果接到翻譯/回答的 context
- [ ] 測試多輪對話後，系統仍能記得前面關鍵資訊

#### 完成定義（DoD）
進行 5 輪以上對話後，詢問稍早提到的專有名詞或約定，系統能正確檢索並回答。

#### 骨架程式碼

**`src/agents/memory.py`**
```python
import os
from chromadb import PersistentClient
from src.core.embeddings import get_embeddings

class DynamicMemory:
    def __init__(self, persist_dir: str | None = None):
        persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.client = PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection("dialogue")
        self.embeddings = get_embeddings()
        self.history: list[str] = []
        self.summary: str = ""

    def add(self, text: str, role: str = "user"):
        emb = self.embeddings.embed_query(text)
        self.collection.add(
            documents=[text],
            embeddings=[emb],
            ids=[f"{role}_{len(self.history)}"],
            metadatas=[{"role": role}],
        )
        self.history.append(f"{role}: {text}")

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        emb = self.embeddings.embed_query(query)
        results = self.collection.query(query_embeddings=[emb], n_results=top_k)
        return results["documents"][0] if results["documents"] else []

    def maybe_summarize(self, llm, max_turns: int = 8):
        if len(self.history) < max_turns:
            return
        # 簡化：把舊歷史摘要後清空部分
        prompt = "Summarize the following dialogue in Chinese, keep key facts:\n" + "\n".join(self.history[:-4])
        self.summary = llm.invoke(prompt).content
        self.history = self.history[-4:]
```

---

### Phase 5：LangGraph 完整狀態機

#### Checklist
- [ ] 定義 `GraphState`（見第 7 章）
- [ ] 實作所有 node 函式：`router_node`, `fast_path_node`, `multi_view_node`, `reflection_node`, `memory_node`, `finalize_node`
- [ ] 寫條件邊 `route_after_router`、`route_after_similarity`
- [ ] 用 `StateGraph` 組裝並 `compile()`
- [ ] 能用 `graph.invoke({"source_text": "..."})` 跑完整流程
- [ ] 加入簡單 logging / 每個 node 的耗時
- [ ] （可選）加上 MemorySaver checkpoint

#### 完成定義（DoD）
一句話輸入後，系統自動走完 Router → 對應路徑 → 最終輸出，且 state 中有完整中間結果。

#### 骨架程式碼

**`src/graph/state.py`**
```python
from typing import TypedDict, Annotated, Optional, Literal, List
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    source_text: str
    messages: Annotated[list, add_messages]
    path: Literal["fast", "slow"]
    ambiguity_score: float
    router_reason: str
    trans_en: Optional[str]
    trans_jp: Optional[str]
    back_en: Optional[str]
    back_jp: Optional[str]
    consistency_score: Optional[float]
    is_high_uncertainty: bool
    ambiguity_detected: bool
    reflection_details: Optional[str]
    suggested_refinement: Optional[str]
    final_output: Optional[str]
    decision_summary: Optional[dict]
    retrieved_context: Optional[List[str]]
```

**`src/graph/nodes.py`（部分）**
```python
from src.graph.state import GraphState
from src.agents.router import semantic_route
from src.agents.verifier import multi_view_verify

def router_node(state: GraphState) -> dict:
    decision = semantic_route(state["source_text"])
    return {
        "path": decision.path,
        "ambiguity_score": decision.ambiguity_score,
        "router_reason": decision.reason,
    }

def multi_view_node(state: GraphState) -> dict:
    result = multi_view_verify(state["source_text"])
    return {
        "consistency_score": result.consistency_score,
        "ambiguity_detected": result.ambiguity_detected,
        "suggested_refinement": result.suggested_refinement,
        "final_output": result.final_translation,
        "is_high_uncertainty": result.ambiguity_detected,
        "reflection_details": result.reasoning,
    }

def fast_path_node(state: GraphState) -> dict:
    from src.agents.translator import translate
    return {"final_output": translate(state["source_text"], "English")}

def finalize_node(state: GraphState) -> dict:
    summary = {
        "path": state.get("path"),
        "ambiguity_score": state.get("ambiguity_score"),
        "consistency_score": state.get("consistency_score"),
        "ambiguity_detected": state.get("ambiguity_detected"),
    }
    return {"decision_summary": summary}
```

**`src/graph/builder.py`**
```python
from langgraph.graph import StateGraph, START, END
from src.graph.state import GraphState
from src.graph.nodes import router_node, multi_view_node, fast_path_node, finalize_node

def route_after_router(state: GraphState) -> str:
    return "fast_path" if state["path"] == "fast" else "multi_view"

def build_graph():
    g = StateGraph(GraphState)
    g.add_node("router", router_node)
    g.add_node("fast_path", fast_path_node)
    g.add_node("multi_view", multi_view_node)
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", route_after_router, {
        "fast_path": "fast_path",
        "multi_view": "multi_view",
    })
    g.add_edge("fast_path", "finalize")
    g.add_edge("multi_view", "finalize")
    g.add_edge("finalize", END)
    return g.compile()
```

---

### Phase 6：Streamlit Web UI

#### Checklist
- [ ] 建立 `src/ui/streamlit_app.py`
- [ ] 左側：聊天輸入 + 歷史訊息
- [ ] 右側：Decision Summary（path、分數、是否觸發 reflection）
- [ ] 呼叫已 compile 的 graph，顯示最終結果
- [ ] 加入「清除對話」按鈕
- [ ] （可選）顯示中間步驟（但不暴露完整敏感 CoT）
- [ ] 介面在本地 `streamlit run` 可正常使用

#### 完成定義（DoD）
開啟瀏覽器後，輸入高歧義句子，左側看到回答、右側看到系統判斷依據。

#### 骨架程式碼

**`src/ui/streamlit_app.py`**
```python
import streamlit as st
from src.graph.builder import build_graph

st.set_page_config(page_title="Cognitive-Core", layout="wide")
st.title("Cognitive-Core Demo")

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
if "history" not in st.session_state:
    st.session_state.history = []

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("對話")
    user_input = st.chat_input("輸入中文句子...")
    if user_input:
        with st.spinner("思考中..."):
            result = st.session_state.graph.invoke({"source_text": user_input})
            st.session_state.history.append({
                "user": user_input,
                "assistant": result.get("final_output", ""),
                "summary": result.get("decision_summary", {}),
            })
    for turn in st.session_state.history:
        st.chat_message("user").write(turn["user"])
        st.chat_message("assistant").write(turn["assistant"])

with col_right:
    st.subheader("Decision Summary")
    if st.session_state.history:
        last = st.session_state.history[-1]["summary"]
        st.json(last)
    else:
        st.info("尚無結果")
```

---

### Phase 7：評測、優化、開源與論文

#### Checklist
- [ ] 建立 CAD-100 初版（至少 30～50 句，標註預期歧義類型）
- [ ] 實作自動化評測腳本（BERTScore 或簡單 embedding 相似度 baseline vs multi-view）
- [ ] 跑 Zero-shot vs Multi-View 對比實驗並記錄表格
- [ ] （可選）邀請 1～3 人做小規模 Likert 評分
- [ ] 優化延遲（Router 閾值、快取、批次）
- [ ] 整理 README、開源授權、使用說明
- [ ] 撰寫技術報告 / 論文草稿
- [ ] 打包成可 `pip install -e .` 的套件結構

#### 完成定義（DoD）
有一份可重現的評測結果表 + 可公開的程式碼與文件。

#### 骨架程式碼（評測）

**`eval/run_eval.py`**
```python
from src.agents.verifier import multi_view_verify
from src.agents.translator import translate
# 之後可接 bert_score

def evaluate_samples(samples: list[dict]):
    results = []
    for s in samples:
        baseline = translate(s["source"], "English")
        multi = multi_view_verify(s["source"])
        results.append({
            "source": s["source"],
            "baseline": baseline,
            "multi_view": multi.final_translation,
            "score": multi.consistency_score,
            "triggered_reflection": multi.ambiguity_detected,
        })
    return results
```

---

## 14. 可參考的開源專案

### 最接近核心邏輯
- **andrewyng/translation-agent**：Reflection workflow 經典實作
- **Dual-Reflect**：回譯 + 雙向反思
- **aurelio-labs/semantic-router**：成熟語意路由層
- **open-multi-agent translation-backtranslation 範例**

### 架構與技術棧對齊
- LangGraph + Ollama multi-agent RAG 專案（secureagentrag、multi_agent_rag、langgraph-ollama-tutorial 等）
- MultiAgentVerification (MAV)
- MARCH（多代理人幻覺檢查）

### 建議閱讀順序
1. andrewyng/translation-agent 的 prompt 與流程
2. semantic-router 文件
3. LangGraph 官方 multi-agent 與 StateGraph 文件
4. 本文件第 13 章對應階段的骨架程式碼，開始實作

---

## 15. 附錄：重要公式與配置

### 15.1 Attention（背景知識）
\[
Attention(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
\]

### 15.2 量化
\[
q = \text{round}\left(\frac{w}{s} + z\right)
\]

### 15.3 Cosine Similarity
\[
\text{Similarity}(A, B) = \frac{A \cdot B}{\|A\|\|B\|}
\]

### 15.4 BERTScore（簡化）
\[
R_{\text{BERT}} = \frac{1}{|x|} \sum_{x_i \in x} \max_{y_j \in y} (x_i \cdot y_j)
\]

### 15.5 建議初始超參數
```yaml
consistency_threshold: 0.80
ppl_variance_threshold: 2.5   # 需實驗調整
temperature_router: 0.0
temperature_translate: 0.3
temperature_reflection: 0.2
top_k_memory: 5
max_reflection_rounds: 2
```

---

## 結語與使用方式

這份文件現在包含：
- 完整系統架構與技術細節
- **Phase 0～7 的 Checklist**（可直接打勾追蹤進度）
- **每個階段的骨架程式碼**（可複製到 VS Code 再請 AI 補完）
- 完成定義（Definition of Done），避免「做到哪算哪」

**建議使用流程**：
1. 從 Phase 0 開始，逐項打勾。
2. 每完成一個 Phase，用該階段的測試腳本確認 DoD。
3. 在 VS Code 中對 AI 說：「根據架構規格書 Phase X 的骨架，幫我把 `xxx.py` 補完整並通過 Checklist」。
4. 文件可直接用 Pandoc 轉 Word：  
   `pandoc Cognitive-Core_專案完整架構與技術規格書.md -o 架構規格書.docx`

祝實作順利。若某個 Phase 的骨架需要更細（例如完整 error handling、logging、單元測試範本），再指定階段即可繼續擴充。

---

**文件結束**  
*本文件依據研究計畫摘要表 (C802) 整理與擴充，可作為實作藍圖與進度 Checklist 直接使用。*
