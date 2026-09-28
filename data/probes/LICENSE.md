# 資料來源與授權

> P2 DoD 第 4 條。**會隨本專案資料一起散布的授權，與建構工具的授權是兩件事**，
> 以下分開記錄。

## 隨資料散布（重要）

### CWN-SemCor

| 項目 | 內容 |
| --- | --- |
| 來源 | HuggingFace `lopentu/Chinese-Wordnet-SemCor` |
| **授權** | **MIT**（dataset card 的 `license: mit`，2026-08-17 實測確認） |
| 語言標籤 | `zh`，tags 含 `traditional chinese` |
| 上游來源 | Chinese Wordnet (CWN) 2.0 的義項；句子來自中央研究院平衡語料庫 |
| 原始論文 | dataset card 引述 "Resolving Regular Polysemy in Named Entities" §3.1 |
| 原始規模 | card 自述 28,836 例句；展平後 train 284,060 列 |
| 標註者 | 六位語言學背景母語者（依 v3 架構書 §1.3） |
| repo 最後更新 | 2025-05-05 |

**MIT 允許再散布與修改，需保留授權聲明。** 本專案由此資料衍生的 probe 三元組
可隨專案散布，須在 `data/probes/` 附上本檔與 MIT 聲明。
MIT 聲明與上游著作權資訊集中於根目錄 [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)；上游未附 LICENSE 檔，缺漏的著作權人與年份亦列於該檔。

⚠️ **上游 CWN 2.0 本身的授權未在 HF card 或 CwnGraph 套件內找到。**
CWN-SemCor 標為 MIT，但那是該 HF repo 的宣告；若要嚴格追溯義項定義的授權，
需向 CWN 官方（<https://lopentu.github.io/CwnWeb/>）確認。
目前依 HF card 的 MIT 宣告使用。

## 僅用於建構、不隨資料散布

### CwnGraph

| 項目 | 內容 |
| --- | --- |
| 套件授權 | **GPL v3**（`METADATA: License: GPL GNUv3`） |
| 版本 | 0.4.0；CWN image `v.2022.08.01` |
| **本專案是否依賴** | ❌ **不依賴** |

**已確認不需要**（2026-08-17）：CWN-SemCor 的展平結構每列都帶
`cwn_sense_id` / `cwn_definition`，`groupby(test_sentence, test_word)` 即可還原
某目標詞的完整義項清單。實測抽 5 個詞對照，資料集的義項集合皆為 CwnGraph 的
子集（死 18/19、中 34/36、行 24/25、長 25/28、空 43/43），差額是語料庫中
從未出現的義項，對本專案無用。

因此：
- `src/cognitive_core/` **完全不 import CwnGraph**（已 grep 確認）
- 僅 `scripts/d1_verify_cwn*.py`、`scripts/d15_verify_criteria.py` 用它做一次性驗證
- 散布的套件不依賴 GPL 程式庫，**GPL 傳染問題不成立**

## 僅用於方法學稽核、不併入本專案資料集

以下資料集**只用來計算長度基準統計**（標準的方法學再分析，不需授權），
**未收錄任何句子進本專案資料集**。若日後要收錄，須先取得作者同意。

| 資料集 | 來源 | 授權 | 用途 |
| --- | --- | --- | --- |
| CHA-Gen | `github.com/SpaJune/CHA-Gen`（arXiv 2605.15635） | **無 LICENSE 檔**（預設保留所有權利） | 長度稽核 |
| CHAmbi | Findings of EMNLP 2024 | 未取得資料 | — |
| Wu et al. 2025 | `github.com/ictup/LLM-Chinese-Textual-Disambiguation` | **無 LICENSE 檔** | 長度稽核 |

⚠️ CHA-Gen 為**簡體中文**，本專案為台灣繁體。即使取得授權，字集轉換本身會引入
新的表層差異，須重跑長度與字元基準。

## 授權詢問狀態

| 對象 | 狀態 |
| --- | --- |
| Wu et al. | 未寄 |
| DEBATE（Zenodo records/15609922） | 未寄 |
| CHAmbi | 未寄 |
| CHA-Gen | 未寄 |
