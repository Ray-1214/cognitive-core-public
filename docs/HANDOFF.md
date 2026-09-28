# Cognitive-Core 交接狀態　2026-08-21

這份文件的用途有二：接手的人快速進入狀況；以及**直接貼進新對話當開場提示詞**。
內容以事實與已定案的裁示為主，不重述推理過程。

---

## 1　這是什麼專案

大專生專題計畫（截止 2026 年 10 月），研究**中文高語境歧義的偵測與路由**。
使用者是主持人，所有研究設計由他裁示；助理負責實作與回報。

治理文件：`docs/Cognitive-Core_完整架構與分階段實作路徑_v3.md`（P1–P8）。

### 三個 RQ

| | 問題 | 現況 |
| :-: | --- | --- |
| RQ1 | 能否用訊號預測機器翻譯會譯錯詞義 | **主線**，卡在標籤品質 |
| RQ2 | 成本–準確度前緣（Router） | 未開始（P5） |
| RQ3 | 記憶模組能否改善跨輪一致性 | 未開始（P7） |

---

## 2　進度

| | 階段 | 狀態 |
| :-: | --- | --- |
| P1 | 管線收尾 | ✅ |
| P2 | 資料層（400 筆探針） | ✅ |
| P3 | 判定層 sense_judge | 🔴 **卡住**：一致率 60%，門檻 85% |
| P4 | 訊號層 S1–S8 | 🟡 訊號值全算完；**AUC 被閘門擋著** |
| P5–P8 | Router／主實驗／Demo／報告 | ⬜ |

實作部分（P1–P7）約 55%。測試 2751 passed。

### 目前的主要數字（`data/results/wsd_baseline400.md`）

翻譯 `ithu/mistral-small-4`　judge `ithu/gpt-oss-120b`（不同訓練血統，judge_cross）

```
n=400   NONE 22(6%)   可判定 378(94%)
義項正確率 0.508  95% CI [0.458, 0.558]
主流   n=189  0.524      非主流 n=189  0.492
兩層之差 +3.2pp  CI [-6.9, +13.2]pp
```

**兩層之差的走勢**：`+22.4pp (n=30) → +10.1pp (n=200,judge v1) →
+6.6pp (n=200,judge v2) → +3.2pp (n=400,judge v2)`
每次把樣本加大或把測量做乾淨，效果就縮一次。目前**沒有證據**支持
「非主流義項較難翻對」。

**主流偏好（CHA-Gen 的預測）在三個樣本數下都不支持**：
n=400 時錯誤 186 筆中選到最高頻義項者 27（14.5%，CI [10.2, 20.3]%），
隨機基準 13.7%。

**長度稽核**：未校正 6/80 格顯著，Holm 校正後 **0 格**。沒有長度混淆。

---

## 3　現在卡在哪

### 3.1　judge 一致率不足（P3 的 DoD）

研究者盲標 20 筆的結果：

| | judge vs 人工 | 人工 vs gold |
| --- | :-: | :-: |
| prompt v1 | 50% | 75% |
| prompt v2 | 60% | 75% |

v1 的兩個具名 bug 已修好（誤判 NONE 3/3、對英文單字做義項匹配 3/3），
NONE 率因此 28% → 4%。但：

- **那 20 筆已成為 dev set**（被用來診斷並改 prompt），不能再當驗證集
- **真正的瓶頸是義項粒度**：人工對著 gold 也只有 75%。剩餘不一致多是
  英文譯文無法區分的義項對（`the lowest record` 是「數值小於比較對象」
  還是「數值變小」？）。這不受 prompt 影響，v1 v2 完全相同。

### 3.2　待研究者裁示的兩件事

**決策 1　judge 任務的形式**

| | 作法 | 風險 |
| --- | --- | --- |
| A（助理建議） | 改 DiBiMT 式二元判定「譯文與 gold 相容嗎」+ 反向對照 | 相容判定偏向「相容」，可能低估錯誤率 |
| B | 維持 N 選一，合併英譯不可區分的義項 | 合併準則難定 |
| C | 不改，把 75% 當天花板寫進限制 | RQ1 很可能全部 CI 涵蓋 0.5 |

**決策 2　新的 20 筆盲標**（研究者的時間）
`scripts/make_judge_manual.py --exclude <舊 KEY>` 已支援排除舊題，
並加了第二欄「也說得通的」，使同一批標註可同時驗證 A 與 C 兩種設計，
並直接量出粒度天花板（目前 25% 是間接推估）。

---

## 4　關鍵數字：這個實驗測得到多小的效果

`required_auc(186, 192, noise)`

| 標籤噪音 | 需要的真實 AUC |
| :-: | :-: |
| 0% | 0.558 |
| 10% | 0.573 |
| 25% | **0.616** |

一般難度預測訊號的 AUC 落在 0.60–0.70，所以**標籤噪音直接決定 RQ1 有沒有答案**。
降噪音比加資料有效得多：噪音 25%→10% 約等於資料量 ×5。

---

## 5　不可違反的規則（研究者已裁示，不要重新討論）

1. **judge_cross**：受測模型與評審模型必須不同訓練血統。
   `config.assert_judge_is_cross()` 在每次 run 開頭檢查。
2. **不擬合權重**：訊號各自報 AUC + 未加權總和。`eval/auc.py` 刻意
   沒有任何 fit/train 介面，且有測試釘住這件事。
3. **每個訊號都要與純句長基準並列**，用 `delong_test`（相關樣本）比較。
   S3 句法複雜度尤其——它的三個成分都隨長度成長。
4. **prompt 例句不得取自探針集或 dev-30**。守門測試
   `tests/test_prompt_contamination.py`。已抓到兩次違規。
5. **不得對 `data/dev30/sentences.yaml` 或 `REVIEW.md` 做內容判斷或修改。**
6. **語意熵必須用單一請求的 `n=k` 取樣**，重複呼叫會撞快取使熵恆為 0。
7. **不要用 heredoc 內嵌 Python 做多步驟編輯**（曾靜默失敗三次）。
8. **不要 `git add -A`**。
9. 新指標必須有單元測試才可用來下結論。
10. **AUC 閘門**：`eval/gate.py`。judge 一致率未達 85% 或驗證檔標記
    `contaminated` 時拒絕計算 AUC。目前關閉。

---

## 6　程式碼地圖

```
src/cognitive_core/
  config.py              角色→provider/model；assert_judge_is_cross()
  llm.py                 Client（litellm）、ProviderPacer、structured() 降級階梯
  similarity.py          cosine 等
  data/
    cwn_loader.py        CWN-SemCor 載入（不用 CwnGraph，避開 GPL）
    probe_builder.py     分層抽樣（dominant / non_dominant）
    length_audit.py      長度混淆稽核 + Holm 校正
  eval/
    wsd.py               MT 詞義錯誤基準的核心
    auc.py               AUC / Hanley-McNeil / 排列檢定 / DeLong / required_auc
    semantic_entropy.py  S8
    gate.py              AUC 閘門
  router/
    signals.py           S1–S8
prompts/                 translate, backtrans, reflect(v3), router(v2),
                         sense_judge(v2), verify
scripts/
  build_probes.py        產生探針（--total 400）
  build_lexicons.py      S1/S4 詞表
  run_wsd.py             主基準（--n 400）
  run_signals.py         S1–S8 + AUC 表（--auc 有閘門）
  judge_validate.py      比對盲標與 judge
  make_judge_manual.py   產生盲標表（--exclude）
  analyze_none.py        NONE 的詞類分布
data/results/
  wsd_baseline400.md     主結果
  judge_diagnosis.md     judge 驗證的完整診斷 ⭐ 先讀這份
  signals_all.md         八個訊號的分布 + AUC 上限
  none_analysis.md
```

---

## 7　資料與授權

| 來源 | 授權 | 用途 |
| --- | :-: | --- |
| `lopentu/Chinese-Wordnet-SemCor` | MIT | 探針（21,098 筆 → 池 17,967 → 抽 400） |
| `pwxcoo/chinese-xinhua` idiom.json | MIT | S4 成語表（30,813 條，OpenCC s2twp） |
| `CwnGraph` 套件 | GPL v3 | **刻意不用**，避免授權傳染 |
| CWN 2.0 本體 | 待向官方確認 | 未直接使用；義項定義經由 CWN-SemCor 取得 |

校內 LLM 端點是 LiteLLM proxy，免費，1200 rpm。
Gemini 免費層日配額曾耗盡，現僅列為備援 profile（`judge_gemini`）。

---

## 8　新對話的開場提示詞

> 我在做 Cognitive-Core（大專生專題，截止 2026/10）。
> 請先讀 `docs/HANDOFF.md`、`docs/Cognitive-Core_完整架構與分階段實作路徑_v3.md`
> 與 `data/results/judge_diagnosis.md`，然後告訴我你理解的現況與下一步。
>
> 重點：P3 的 judge 一致率只有 60%（門檻 85%），而且那 20 筆已經是 dev set。
> 真正的瓶頸是 CWN 義項粒度比英文細，我自己對著 gold 也只有 75%。
> 我要先決定 judge 任務要不要從「N 選一」改成「與 gold 相容嗎」的二元判定。
>
> 規則：不要算任何訊號的 AUC（程式裡有閘門擋著，不要繞過）；
> 不要動 dev-30；不要用 heredoc 內嵌 Python 做多步驟編輯；不要 git add -A。
