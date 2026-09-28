# MT 詞義錯誤基準　n=1

> ⚠️ **judge 未經人工驗證前，所有數字標為 preliminary。**
> 翻譯：`ithu/mistral-small-4`　judge：`gemini/gemini-flash-latest`（judge_cross，非受測模型）
> 任務：CWN-SemCor 句子 → 翻成英文 → judge 判譯文表達哪個義項 → 比對 CWN gold

> 🔴 **第 1 筆連續兩次 429（間隔 25s），研判為日配額耗盡，已中止。累計 429 1 次**

## 停止判準

- ✅ 全部未觸發

## 整體

| 項目 | 值 |
| --- | :-: |
| 總題數 | 1 |
| translation_failed | 0/1（0%） |
| error | 1/1（100%） |
| judge 回 NONE | 0/1（0%） |
| **可判定** | 0/1（0%） |
| **義項正確率** | **nan**　[nan, nan] |

## 分層 ⭐ 主結果

| 層 | n（可判定） | 正確 | 正確率 | 95% CI |
| --- | :-: | :-: | :-: | :-: |
| 主流（gold 為最高頻） | 0 | 0 | nan | [nan, nan] |
| 非主流 | 0 | 0 | nan | [nan, nan] |

**兩層之差（主流 − 非主流）**：+nanpp　95% CI [+nan, +nan]pp　p≈nan

| 觀察 | 判讀 |
| --- | --- |
| 主流高、非主流低 | 走頻率捷徑，沒讀脈絡 |
| 兩層相近 | 真的在讀脈絡 |
| 兩層都低 | 任務太難或 judge 有問題 |

---

## 逐筆（請掃一遍判斷 judge 合不合理）

| # | 詞 | 原句 | 譯文 | judge 選的 | gold | 對 |
| :-: | :-: | --- | --- | --- | --- | :-: |
| 1 | 收 | 我們不收支票。 | judge: 結構化輸出全數失敗（gemini-flash-latest）：ge | — | `03039303` | 🔴錯 |

### 錯誤與 NONE 的細節

---

成本：8 次呼叫 / 314 tokens / 48.4s / 快取命中 2
run: `runs\20260818-144803-wsd-2946f1.jsonl`