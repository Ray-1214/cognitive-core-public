# 參考文獻

存放本專案引用的論文 PDF 與書目資料。

## 規則

- **PDF 本身不進 Git**（`.gitignore` 已排除 `papers/*.pdf`）——出版社論文有著作權，公開散布有風險。PDF 請自行下載到本機。
- **書目資料進 Git**：統一維護在 `references.bib`，供 LaTeX 與計畫書引用使用。
- 檔名慣例：`作者年份-關鍵詞.pdf`，例如 `bender2021-stochastic-parrots.pdf`，與 BibTeX 的 citation key 對應。

## 待建立

- [ ] `references.bib`（從研究計畫書文末的 BibTeX 附錄整併過來）

## 已下載（2026-08-17，D1 查證）

| 檔案 | 出處 | 為何在此 |
| --- | --- | --- |
| `2024.mrl-1.26.pdf` | ACL Anthology, MRL 2024 | 研究者指定。與演算法 1 高度重疊（用多語 LLM 翻譯偵測歧義），novelty 邊界由研究者劃定 |
| `2605.15635_Evaluating_Chinese_Ambiguity_Understanding.pdf` | arXiv, 2026-05-15 | 🔴 D1 查證時發現。翻譯 + 語意熵偵測中文歧義、base vs instruct 熵差、CHA-Gen 資料集。**比 Wu et al. 更貼近本專案方法** |
| `2024.findings-emnlp.875_CHAmbi.pdf` | Findings of EMNLP 2024 | 查證規格書引用的 CHAmbi 統計。原文為 4,991 NLI 對 / 824 歧義，與規格書所稱 893/1784 不符 |
| `2507.23121_Wu2025_Chinese_Textual_Ambiguity.pdf` | arXiv | 查證 BERT-ft 94.70/91.81（確認吻合）。其資料集 900 句 / 9 類 |

⚠️ 以上 PDF 內文**未經助理閱讀或摘要**。D1_FINDINGS.md 中的描述全部取自公開摘要與 landing page。
