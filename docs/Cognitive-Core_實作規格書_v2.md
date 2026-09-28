# Cognitive-Core 實作規格書 v2

> **產出日期**：2026-08-14
> **截止目標**：2026 年 10 月（推甄用；同期另有畢業專題，實際可用工時約 3 週）
> **這份文件的角色**：執行文件。回答「十月前要做完什麼、怎麼做、什麼不做」。

---

## 0. 這份文件取代什麼、不取代什麼

| 文件 | 狀態 |
| --- | --- |
| `研究計畫書.md` | **合約，不動。** 已通過評審 |
| `docs/技術設計文件.md` | **完整設計，仍有效。** 本文件是它的執行子集 |
| Grok 版《專案完整架構與技術規格書》 | **作廢。** 結構可用，內容基於原計畫書假設，不知道 8/11–8/14 的實驗結果 |
| **本文件** | 十月前的執行計畫 |

### Grok 版哪裡過時

| 它寫的 | 實際狀況 |
| --- | --- |
| Ollama + 本地 Llama-3-8B GGUF | 已改用校內 LiteLLM proxy（6 模型）+ Gemini。差異表 D1/D2/D3 |
| Router 用 Cross-Lingual PPL Variance | **循環依賴**（要算變異數就得先做多路徑回譯，那就是慢速通道本身）。已改五種前置訊號。差異表 D4 |
| τ 閾值固定 0.75–0.85 | 訊號分布重疊，單一 τ 必然誤判。改報 ROC/AUC |
| BERTScore 為主指標 | CAD-100 不做標準譯文，BERTScore 算不出來。改用「正確義項命中率」 |
| Self-Consistency Score 為勝負依據 | **循環論證**（E1 的迴圈終止條件就是一致性 ≥ τ）。已降級為收斂診斷指標 |
| 三大模組平行推進 | 偵測與診斷已分離（§4.2.1），架構不同 |
| 未提長度混淆 | **最重要的遺漏。** 見 §5 地雷 1 |

Grok 版的 Phase Checklist + DoD + 骨架程式碼形式是對的，本文件沿用該形式。

---

## 1. 現況（2026-08-14）

### 已完成

| 項目 | 狀態 | commit |
| --- | --- | --- |
| litellm 基礎設施（provider / 快取 / run 記錄 / 降級階梯） | ✅ 煙霧測試 7/7 過 | `1b96e03` |
| 快取鍵回歸測試（9 項） | ✅ | `1b96e03` |
| dev-30 草稿（30 句 + 30 配對消歧版，長度平衡） | 🟡 待研究者複核凍結 | `81f0b26` |
| 外部資料集長度基準 | ✅ **本專案目前最強的結果** | `64394b2` |
| 標註污染記錄與隔離 | ✅ | `83c2e94` |

### 已作廢（不得引用）

- T3 全家：V1–V4、S0c 八個 AUC、ja+ja 的 1.000、DeLong 比較 → spike 15 句的長度 AUC = 0.900，比任何量測都高
- T2 的**數值**（方向性結論「UNKNOWN 判別力 ≤ 0」保留，因偏誤方向對結論不利，屬保守估計）
- 表 3 的「模擬數據」→ 期中報告前必須換掉，之後任何場合不得引用

### 未定

- §4.4 的兩條主張：(a) 類型學強制顯性化 🟢 未受挑戰；(b) 三角測量必要性 🟡 待驗
- PPL 局部變體（整句 0.509 → 句內最大 0.610 → span 0.679），三個 CI 皆涵蓋 0.5

### 已知可用資源

```
校內 LLM 端點（LiteLLM proxy）
  ✅ mistral-small-4 / gpt-oss-120b / llama4scout / nemotron-3-ultra / ornith-35b
  ✅ bge-m3-embedding (dim=1024) / bge-m3-reranker
  ❌ diffusiongemma-26b（伺服器端 500，與金鑰無關）
Gemini free tier：日配額易耗盡，只用於 judge 角色
本地：torch 2.13.0+cpu / transformers 5.15.0 / ckiplab/gpt2-base-chinese
```

---

## 2. 十月前的範圍決定

### 2.1 交付物定義

推甄要看的是**可展示的作品 + 一個站得住的結果 + 說得清楚的思考過程**，不是可投稿的論文。因此：

| # | 交付物 | 用途 |
| --- | --- | --- |
| D1 | 可跑的 Cognitive-Core 系統 + Streamlit demo | 主要展示品 |
| D2 | 技術報告（20–30 頁） | 書面材料 |
| D3 | GitHub repo（README、可 `pip install -e .`、可重現） | 作品連結 |
| D4 | CAD-60 標註資料集 | 可引用的產出 |

### 2.2 報告的主結果 ⭐ 這個決定去風險

**不要**把「本系統優於 baseline」當主結果——它依賴實驗贏，而現在沒有任何證據保證會贏。

改成：

> **主結果**：中文歧義偵測的評測資料集普遍存在長度混淆。在已發表的中文歧義資料集上，一個只使用句長的分類器可達 AUC 0.965。本研究提出等長最小對立對協定，並釋出長度平衡的 CAD-60。
>
> **應用**：在該乾淨基準上，比較多視角回譯、模型自我評估、原文 PPL 三類偵測訊號。
>
> **系統**：Cognitive-Core 實作了完整的偵測—診斷—反思流程，並提供決策過程可視化介面。

好處：
1. 主結果已經成立（n=136、SE=0.012），不依賴後續實驗
2. 系統贏了是加分，沒贏也有話講（「在乾淨基準上多視角無顯著優勢」是有價值的負面結果）
3. 對 RQ1 是正面回答——「模型如何知道自己沒聽懂」這個問題，現有的量測方式本身是被污染的

### 2.3 砍掉什麼

| 原規劃 | 決定 | 理由 |
| --- | --- | --- |
| M10 人類評測（3 人 × 30 句 × Fleiss' Kappa） | **砍到 pilot**：1–2 人 × 15 句，報告為初步 | 三人協調是以週計的，時間買不起 |
| M8 跨模型對比（7 模型 × 4 profile） | **降為 3 模型**：mistral / gpt-oss / gemini | 邊際資訊量低 |
| CAD-100（100 句） | **降為 CAD-60**：dev-30 + 新增 30 | 標註是研究者本人的時間，不可壓縮 |
| M7 記憶模組（RQ3） | **降為最小可展示**：ChromaDB + 滾動摘要實作 + 10 組 Lost-in-the-Middle 測試 | 保住 RQ3 有交代，不投入完整實驗 |
| 排列檢定、DeLong、拔靴法全套 | **只對主結果做** | 其餘報點估計 + CI 即可 |
| Electron 桌面應用 | **砍，改 Streamlit** | 計畫書原本就寫 Streamlit，差異表 D6 可刪，且快 |
| RouteLLM / semantic-entropy-probes clone | **砍** | 那是為投稿級 baseline 準備的，此規模不需要 |

### 2.4 時程

| 週 | 日期 | 內容 | 並行（研究者） |
| --- | --- | --- | --- |
| W1 | 8/15–8/21 | Phase A：系統核心（M1+M2+M3） | 複核凍結 dev-30 |
| W2 | 8/22–8/28 | Phase B：Router + Phase C：評測管線 | CAD-60 新增 30 句 |
| W3 | 8/29–9/4 | Phase D：主實驗 + 圖表 | — |
| W4 | 9/5–9/11 | Phase E：Streamlit + Phase F：記憶模組最小版 | 人類評測 pilot |
| W5–6 | 9/12–9/25 | Phase G：報告、README、打包 | 報告撰寫 |
| 緩衝 | 9/26–10/初 | — | — |

---

## 3. 技術棧（已定案，不再討論）

```
Python 3.14.5（Windows，非 WSL）
litellm 1.96.2      ← provider 抽象 / 快取 / 重試 / 成本追蹤
  + diskcache, tenacity, python-dotenv
langgraph           ← 狀態機
chromadb            ← 記憶模組
streamlit           ← 展示介面
pydantic v2         ← 結構化輸出驗證
pytest              ← 回歸測試
torch 2.13.0+cpu / transformers  ← 本地 PPL（僅雜訊基準用）
```

**不用**：Ollama、Electron、自寫 provider adapter、自寫節流。

### 專案結構（現況 + 待補）

```
cognitive-core/
├── config/
│   ├── providers.yaml          ✅ litellm 格式，角色綁定，experiment_profiles
│   └── router.yaml             ⬜ Phase B
├── prompts/                    ⬜ Phase A：所有 prompt 存檔，run 記錄存 hash
│   ├── translate.md  backtrans.md  reflect.md  verify.md  router.md
├── skills/                     ⬜ Phase A
│   ├── _template.md  zh-TW.md  en.md  ja.md  de.md
├── data/
│   ├── dev30/sentences.yaml    🟡 待凍結
│   ├── cad60/                  ⬜ Phase C 並行
│   ├── external/               ✅ wu2025_task2_test.tsv
│   └── lexicons/               ⬜ Phase B：歧義詞典、成語表
├── src/cognitive_core/
│   ├── config.py               ✅
│   ├── llm.py                  ✅
│   ├── runlog.py               ✅
│   ├── models.py               ⬜ Phase A：SemanticAnchor 等 Pydantic
│   ├── graph.py                ⬜ Phase A：LangGraph 狀態機
│   ├── verify/                 ⬜ Phase A：演算法 1
│   ├── reflect/                ⬜ Phase A：錨點建構
│   ├── router/                 ⬜ Phase B
│   ├── memory/                 ⬜ Phase F
│   ├── eval/                   ⬜ Phase C
│   └── cli.py                  ⬜ Phase A：批次入口
├── app/streamlit_app.py        ⬜ Phase E
├── tests/                      ✅ test_cache_key.py
└── scripts/
```

---

## 4. Phase 計畫

每個 Phase 有 Checklist、完成定義（DoD）、骨架。**DoD 未達成不進下一個 Phase。**

---

### Phase A：系統核心（M1 + M2 + M3）

**目標**：一句中文進去，跑完 Router→翻譯→回譯→比對→（必要時）反思→輸出，全程有 run 記錄。

#### A-1 Pydantic 資料模型

```python
# src/cognitive_core/models.py
from typing import Literal
from pydantic import BaseModel, Field

UNKNOWN = "UNKNOWN"

class AlternativeReading(BaseModel):
    reading: str
    applicable_when: str
    speaker_intent: str = UNKNOWN     # 降層：intent 內嵌在每個讀法裡

class CulturalItem(BaseModel):
    term: str
    literal: str
    actual_sense: str
    ambiguity_type: Literal["LEXICAL", "SYNTACTIC", "REFERENTIAL", "PRAGMATIC"]

class Uncertainty(BaseModel):
    unknown_fields: list[str] = Field(default_factory=list)
    ambiguity_score: float = 0.0
    alternative_readings: list[AlternativeReading]   # 必填，不設數量上限
    clarification_questions: list[str] = Field(default_factory=list)

class SemanticAnchor(BaseModel):
    source_text: str          # 不可變
    source_language: str = "zh-TW"
    agent: str = UNKNOWN
    time: str = UNKNOWN
    register: Literal["FORMAL", "SEMI_FORMAL", "CASUAL", "UNKNOWN"] = UNKNOWN
    social_relation: str = UNKNOWN
    cultural_items: list[CulturalItem] = Field(default_factory=list)
    uncertainty: Uncertainty
    revisions: int = 0
```

**約束（不可違反）**：
1. `source_text` 任何階段不得修改
2. 反思後重譯只讀錨點，**不讀上一輪譯文**
3. `UNKNOWN` 是合法且被鼓勵的值
4. `alternative_readings` **不設硬上限**，改報 precision@k（k=1,2,3,5）

#### A-2 驗證配置（§4.2.1 偵測／診斷分離）

```yaml
# config/verify.yaml
profiles:
  cross_en_ja:   { mode: cross_lingual, languages: [en, ja] }   # 預設
  cross_en_de:   { mode: cross_lingual, languages: [en, de] }
  same_en:       { mode: same_language, language: en, n: 4 }    # 同語言重取樣對照
  single_ja:     { mode: single_probe,  language: ja }          # E1-d 消融

detector: single_probe        # 便宜偵測：單探針往返保真度
diagnoser: cross_lingual      # 昂貴診斷：多視角 IdentifyDiff，只在慢速通道
holdout_languages: [de, fr]   # 只用於量測，不進迴圈（避免循環論證）
```

**四種 profile 必須是同一條程式碼路徑的不同設定**，不是四份實作。

#### A-3 LangGraph 狀態機

```python
# src/cognitive_core/graph.py
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

class GraphState(TypedDict):
    source_text: str
    targets: list[str]
    route: Optional[dict]              # {path, ambiguity_score, signals}
    anchor: Optional[dict]             # SemanticAnchor.model_dump()
    translations: dict[str, str]
    back_translations: dict[str, str]
    consistency_score: Optional[float]
    detector_score: Optional[float]    # 單探針往返保真度
    revision_count: int
    memory_context: list[str]
    timeline: list[dict]               # 給 UI 的決策記錄（非原始 CoT）
    final: Optional[dict]

# START → route ─┬─(fast)─→ translate_direct ─────────────┐
#                └─(slow)─→ build_anchor → translate_multi │
#                               ▲              │           │
#                           reflect ◀── verify ─(pass)─────┤
#                               ▲         │                │
#                               └─(fail, revision<R)───────┘
#                                         │                │
#                                    (revision≥R)          │
#                                         └────────────────┤
#                                                          ▼
#                                               write_memory → END
```

用 `astream_events` 把節點進出推給前端（Phase E 要用）。

#### A-4 Prompt 檔案化

所有 prompt 放 `prompts/*.md`，載入時取 SHA-256，寫進 run 記錄。
**prompt 改一個字，之前的數據就視為不同批次。**

#### A-5 語言技能檔

`skills/<code>.md` 每語言一檔，內容：強制顯性化欄位、翻譯陷阱、回譯檢查點、few-shot、輸出格式約束。
新增語言零程式碼改動。先做 zh-TW / en / ja / de。

#### Checklist

- [ ] `models.py`：SemanticAnchor 等 Pydantic 定義，附 `tests/test_models.py`
- [ ] `verify/`：演算法 1，四種 profile 走同一路徑
- [ ] `reflect/`：錨點建構，走 `Client.structured()` 降級階梯
- [ ] `graph.py`：LangGraph 節點與條件邊，`astream_events` 可用
- [ ] `prompts/`：五支 prompt 檔案化，hash 進 run 記錄
- [ ] `skills/`：zh-TW / en / ja / de
- [ ] `cli.py`：`cognitive-core run --input X --profile Y`，支援批次、斷點續跑
- [ ] 取樣重複次數**依模型觀測變異決定**，不固定 n=3

#### DoD

```bash
# 單句
python -m cognitive_core.cli run --text "方便的話明天再說吧" --profile cross_en_ja
# 批次
python -m cognitive_core.cli batch --dataset data/dev30/sentences.yaml --profile cross_en_ja
```
兩者都跑完，`runs/*.jsonl` 有完整記錄，重跑結果一致（快取命中）。
四種 verify profile 都能跑，且**不需改任何程式碼**。

---

### Phase B：Semantic Router（M6，RQ2）

#### 五種前置訊號

| 訊號 | 實作 | 成本 |
| --- | --- | --- |
| S1 歧義詞典命中 | 自建多義詞／成語／委婉語詞表 | 極低 |
| S2 主詞省略偵測 | 規則 + 依存句法 | 低 |
| S3 句法複雜度 | 句長、從句數、標點密度 | 極低 |
| S4 文化專有項 | 成語／流行語／典故詞表 | 極低 |
| S5 LLM 快速判定 | 單次小模型呼叫 | 中 |
| S6 單探針往返保真度 | 一次翻譯 + 一次回譯 | 中 |

#### ⚠️ 權重不擬合

**不要**在 dev-30 上擬合 $w_i$。改為：
- 報告**每個訊號各自的 AUC**（資訊量高於合成分數，且直接說明哪種訊號有用）
- 加報**未加權總和的 AUC** 當合成基準
- dev/test 洩漏風險降到零

#### Checklist

- [ ] `data/lexicons/`：多義詞、成語、委婉語詞表（可從既有中文資源起手）
- [ ] S1–S6 各自實作，各自輸出 0–1 分數
- [ ] 每個訊號的個別 AUC + 未加權總和 AUC，附 SE 與 95% CI
- [ ] **每個訊號都要跑長度基準對照**（見 §5 地雷 1）
- [ ] 成本記錄：每個訊號的呼叫次數與 token

#### DoD

一張表：六個訊號 × (AUC, SE, CI, 平均成本)，加一列未加權總和，加一列長度基準。

---

### Phase C：評測管線 + 主實驗（M5）

#### 對照組

| 組別 | 說明 | 推論次數 |
| --- | --- | --- |
| B0 | 單次直翻（計畫書指定 Zero-shot） | 1× |
| B1 | 鏈式往返翻譯（漂移對照） | K× |
| B2 | 等算力 self-consistency，取 medoid | N× |
| B3 | 模型自我評估（強制列舉差異版，非是／否） | 1× |
| **E1** | 本系統 | ~N× |
| E1-a | 消融：關閉反思 | |
| E1-b | 消融：關閉 Router（全走慢速） | |
| E1-d | **消融：單探針**（§4.2.1） | |

#### B2 的兩個實作細節

1. **「取多數」在自由文本上無定義** → 取 medoid（跟其他 N−1 個平均相似度最高的那一版）
2. **等算力對齊** → 不對齊，改讓 B2 掃 N = 1,2,3,5,8,10 畫**成本–準確度前緣曲線**，E1 當一個點畫上去。E1 在曲線上方就是贏。
   **這張圖同時就是 RQ2 的散點圖，兩張圖合成一張。**

#### 主指標

| 指標 | 用途 | 需標註 |
| --- | --- | --- |
| **正確義項命中率** | 主指標（取代 BERTScore） | 是 |
| 歧義偵測 AUC | RQ1 | 是（正負例） |
| Router 分流準確率 + 成本下降 | RQ2 | 是（`expected_route`） |
| precision@k（k=1,2,3,5） | alternative_readings 過度生成 | 是（`spurious_readings`） |
| 成本（calls / tokens / 秒） | 誠實揭露 | 否 |
| Schema 通過率 | G6 | 否 |
| 自我一致性分數 | **僅作收斂診斷，不當勝負依據** | 否 |

**BERTScore 只在 WMT23 子集上算**，宣稱方向改為「加了驗證機制不傷害一般翻譯品質」，不宣稱更好。

#### Checklist

- [ ] `eval/`：指標實作，每個指標有單元測試
- [ ] 雜訊基準面板：句長、標點數、相異字元數、字元重複率、原文 PPL
- [ ] **訊號 AUC 與最強雜訊 AUC 並列呈現**
- [ ] B0/B1/B2/B3/E1 + 三組消融，全部在 dev-30 上跑通
- [ ] 成本–準確度前緣圖
- [ ] 結果表自動產生（不要手抄）

#### DoD

`python -m cognitive_core.cli eval --dataset dev30 --all` 一鍵產出主表 + 三張圖。

---

### Phase D：CAD-60（研究者並行）

#### 標註 schema（已定案）

```yaml
- id: cad-001
  text: "方便的話明天再說吧"
  ambiguity_type: PRAGMATIC
  expected_route: slow              # Router 的 ground truth
  minimal_pair:                     # 等長消歧版（負例）
    text: "有空的話明天再談這件事"
    edit: "方便 → 有空（等長替換，非補語境）"
  ambiguity_points:
    - span: "方便"
      licensed_readings:            # 原文允許的所有讀法
        - reading: "委婉推託"
          licensed_when: "對方為平輩或下屬"
        - reading: "字面詢問時間"
          licensed_when: "先前已約定討論此事"
      text_determinable: false
      preferred_reading: null       # 僅 determinable=true 時填
      spurious_readings:            # 原文不允許、模型可能生成的
        - "詢問對方身體是否方便"
    - span: "(省略主詞)"
      field_determinable:           # 逐欄位可判定性
        agent: false
        social_relation: false
        time: true
  required_clarifications: [social_relation]
```

#### 分層配比

| 類型 | dev-30 | 新增 | 合計 |
| --- | --- | --- | --- |
| 詞彙 LEXICAL | 9 | 9 | 18 |
| 指代 REFERENTIAL | 9 | 9 | 18 |
| 語用 PRAGMATIC | 12 | 12 | 24 |
| **合計** | 30 | 30 | 60（+60 配對消歧版） |

#### 標註整規則（不可違反）

1. **某句的標註在任何模型看過它之前凍結**
2. 模型輸出只能用來判斷**準則是否涵蓋不足**，不可逐句補
3. 要改就改準則 → 從準則重標全部 → 重新凍結取 hash
4. 已知污染：`dev-lex-01`（助理看過）、`dev-prg-05`（雙方皆看過）→ 報告須逐句揭露

#### Checklist

- [ ] 研究者複核 dev-30 → 凍結 v1 → 記錄 SHA-256
- [ ] 7 模型跑 dev-30 收集讀法聯集 → 只判斷準則完備性
- [ ] 若改準則 → 從準則重標 30 句 → 凍結 v2 → v1↔v2 diff 存證
- [ ] 新增 30 句（自造為主，外部資料集需授權後才可收錄）
- [ ] 每次凍結都跑一次雜訊基準面板
- [ ] 授權詢問信寄出（Wu et al. / DEBATE / CHAmbi）

---

### Phase E：Streamlit 介面（M9）

計畫書 §4.9 的三項實質要求全保留：左側對話、右側決策摘要、**不揭露原始 CoT**。

#### 決策時間軸（右欄）

```
① Router      歧義分數 0.72 → 慢速通道
              觸發訊號：S1 詞彙「方便」命中委婉語詞表、S2 主詞省略
② 平行翻譯     日文 ✓  英文 ✓
③ 回譯比對     餘弦相似度 0.61 ＜ 閾值 0.75  ⚠ 不一致
④ 反思 (1/3)   差異定位：social_relation 欄位缺失
⑤ 重新翻譯     日文 ✓  英文 ✓
⑥ 回譯比對     餘弦相似度 0.88  ✓ 通過
⑦ 不確定性     ⚠ agent 欄位仍為 UNKNOWN
              → 澄清提問：「這句是對上司還是朋友說的？」
─────────────────────────────────
成本：6 次呼叫 / 3,240 tokens / 4.2 秒
```

**倫理界線的實作**：顯示的是**結構化決策記錄**（哪個訊號觸發、哪個欄位缺失、相似度多少），不是模型的原始推理文字。這既符合計畫書要求，也比揭露 CoT 更好懂。**Demo 時這個時間軸是最有說服力的畫面。**

推理模型的 `reasoning_content` 一律不外流。

#### Checklist

- [ ] 左欄：`st.chat_input` + 歷史
- [ ] 右欄：決策時間軸，每節點可展開
- [ ] 成本列：呼叫次數 / token / 秒
- [ ] Profile 切換器（跨語言 / 同語言 / 單探針），現場展示消融
- [ ] 「清除對話」
- [ ] 錄一段 60–90 秒的 demo 影片

#### DoD

`streamlit run app/streamlit_app.py`，輸入「方便的話明天再說吧」，右欄出現完整時間軸。

---

### Phase F：記憶模組最小版（M7，RQ3）

**降級目標**：讓 RQ3 有交代，不做完整實驗。

- ChromaDB 存對話歷史；有錨點時錨點一併存（資訊密度高於原始訊息）
- 滾動摘要：超過視窗長度時舊訊息壓縮，有錨點者優先摘要 `explicit` 區塊
- 檢索：bge-m3 embedding + 餘弦相似度 top-k

#### Checklist

- [ ] ChromaDB 存取
- [ ] 滾動摘要
- [ ] **10 組** Lost-in-the-Middle 測試（關鍵資訊放頭／中／尾），有無記憶模組的對照曲線
- [ ] 一張圖，寫進報告

#### DoD

一張召回率曲線圖，說明「有記憶模組時中段召回率不塌」。n=10 不足以下定論，報告中如實說明為初步驗證。

---

### Phase G：報告、README、打包

#### 報告骨架

```
1. 緒論：高語境語言的歧義問題、三個 RQ
2. 相關工作
   2.1 LLM 的不確定性表達（Xiong et al. ICLR 2024、Kadavath 2022、Geng 2024 綜述）
   2.2 中文歧義（Wu et al. 2025、CHAmbi EMNLP 2024）
   2.3 consistency-based 不確定性量化（semantic entropy, Farquhar et al. Nature 2024）
   ← 我們的方法是 consistency-based 的跨語言變體，不是新類別。必須這樣定位
3. ⭐ 評測方法學問題（主結果）
   3.1 長度混淆的機制：歧義多來自省略，省略就短；消歧要寫明，寫明就長
   3.2 外部資料集實測：Wu et al. 2025 長度 AUC = 0.965 (n=136, CI [0.94,0.99])
       ※ 須寫明該資料集為「生成消歧版本」而設計，非為偵測而設計。
         有問題的是把它當偵測負例——那是我們的用法，不是原作者的主張
   3.3 等長最小對立對協定
   3.4 CAD-60：長度平衡的中文歧義偵測基準
4. 系統設計
   4.1 偵測／診斷分離
   4.2 語意錨點與 alternative_readings
   4.3 引出格式的發現：是／否自評題退化（AUC 0.500），
       強制生成題保有訊號（0.660）。兩處獨立印證
5. 實驗
   5.1 各偵測訊號在乾淨基準上的 AUC（含雜訊基準面板並列）
   5.2 成本–準確度前緣曲線（RQ2）
   5.3 消融
   5.4 Lost-in-the-Middle 初步（RQ3）
6. 討論與限制
   - n 小、CI 寬，多數結論待更大樣本
   - 標註獨立性的兩處缺口（逐句揭露）
   - 主張範圍：偵測「間接言語行為」比「語用歧義」窄
7. 與計畫書的差異表（技術設計文件 §9）
```

#### Checklist

- [ ] 報告 20–30 頁
- [ ] README：一句話說明、架構圖、快速開始、重現實驗指令
- [ ] `pip install -e .` 可用
- [ ] 可重現性封包：config + 資料 + 結果 + 版本，一鍵匯出
- [ ] 計畫書差異表更新（D1、D3、D4 須主動說明變更理由）
- [ ] 表 3 的「模擬數據」換成真實數據

---

## 5. 不可重犯的地雷

這五條是 8/11–8/14 用實際事故換來的。**每個 Phase 開始前重讀一次。**

### 地雷 1：長度混淆 🔴 最嚴重

**任何**歧義／非歧義的組間比較，都必須先跑「只用句長的分類器」。

- spike 15 句：長度 AUC = **0.900**，高於最佳量測 0.840 → 全部作廢
- Wu et al. 2025：長度 AUC = **0.965**
- 機制：歧義多來自省略，省略就短；對照要語意明確，明確就要寫出來，寫出來就長

**規則**：
- 消歧一律用**等長替換**，不用補語境
- 每個新資料集、每個新訊號，都跑雜訊基準面板（句長、標點、相異字元、字元重複率、原文 PPL）
- 訊號 AUC 與**最強雜訊 AUC 並列**呈現
- 表層特徵無限，**不要逐個修到 0.5**——量化並揭露殘留即可。過度約束的對立對會變成沒人會講的句子，那時你量的是「偵測怪句子」

### 地雷 2：循環論證

- **自我一致性分數不可當勝負依據**：E1 的迴圈終止條件就是「一致性 ≥ τ」，拿它比 E1 vs B0 是套套邏輯
- 降級為收斂診斷指標；要量非循環的一致性，用**留出語言**（de/fr，全程不進迴圈）

### 地雷 3：標註污染

- 某句的標註在任何模型看過它之前凍結
- 模型輸出只能影響**準則完備性**，不能影響**個別句子的答案**
- 已知缺口：`dev-lex-01`、`dev-prg-05` → 報告逐句揭露

### 地雷 4：不對稱的證據標準

對有利結果嚴格，對不利結果要**同樣**嚴格。

- 不能一邊說「n=15 撐不起顯著性」撤回有利結論，一邊用同一批 n=15 否定 §4.4
- 多重比較要記錄**總共試了幾個配置**（研究者自由度不只表面那幾個：哪個 embedding、min 還是 mean、哪種聚合）
- AUC = 1.000 時**拔靴法也退化**（完美分離的資料，每個重抽樣本仍完美分離）→ 用排列檢定

### 地雷 5：基礎設施債會偽裝成研究問題

四天五個事故，五個都是基礎設施：

| 事故 | 根因 |
| --- | --- |
| 快取讓 temp=1.5 失效 | 快取鍵沒含取樣參數 |
| span AUC 0.851 是蘋果比橘子 | 指標邏輯寫在 heredoc，沒測試 |
| patch 沒套用卻拿舊結果當新結果 | heredoc 跳脫 |
| collect 三輪失敗查不出原因 | 沒有錯誤記錄 |
| 金鑰硬寫在指令列 | 沒有統一呼叫入口 |

**規則**：
- 不用 heredoc 內嵌 Python 做多步驟編輯。寫成檔案、跑、確認
- 不用 `git add -A`。明確列檔
- 每筆 run 記錄含 commit hash + dirty 旗標 + prompt hash
- 新指標必須有單元測試才可用來下結論

---

## 6. 每輪回報格式

給編碼代理的固定要求：

```
1. 這輪做了什麼（Checklist 打勾）
2. DoD 是否達成（是／否／部分，附證據）
3. 遇到的問題與處理
4. 數字（如有）：點估計 + n + SE + CI，不可只給百分比
5. 下一步建議 + 需要研究者處理的事項
```

**負面結果照實報。** 過去四天最有價值的三件事都是負面發現：快取 bug、長度混淆、PPL 無訊號。

---

## 附錄：可直接貼給編碼代理的啟動提示詞

```
讀 docs/Cognitive-Core_實作規格書_v2.md，執行 Phase A。

背景：截止是十月，實際可用工時約三週。範圍已在 §2.3 砍定，不要擴充。
Grok 版規格書已作廢（§0），以本文件為準。

執行前先讀 §5「不可重犯的地雷」五條。

Phase A 的 Checklist 逐項做，每完成 2–3 項回報一次（格式見 §6）。
DoD 未達成不進 Phase B。

不要做的事：
- 不要跑 §3 步驟 1（讀法聯集），等研究者凍結 dev-30 v1 給出 hash
- 不要動 dev-30 的句子
- 不要 clone RouteLLM 或 semantic-entropy-probes（§2.3 已砍）
- 不要用 heredoc 內嵌 Python 做多步驟編輯
- 不要用 git add -A
```
