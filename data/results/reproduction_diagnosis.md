# 從零重現驗證的診斷

> 2026-08-22 至 08-23。自動產出的比對表在
> [`reproduction_check.md`](reproduction_check.md)，本文是解讀。

## 摘要

| | 結果 |
| --- | --- |
| 管線可跑完 | 🟡 10 步中 9 步成功，第 7 步被 AUC 閘門擋下 |
| 從零總耗時 | **26.6 分鐘** |
| 關鍵數字一致 | **20/52** |
| 不一致的原因 | 端點在 8/21 與 8/22 之間**換了模型**（非 per-call 隨機） |
| 附帶發現 | 🔴 `judge_cross` 可能一直是假的（見 [`endpoint_identity_check.md`](endpoint_identity_check.md)）|

---

## 1　乾淨 clone 跑不起來（已修）

`build_lexicons.py` 需要 `data/lexicons/idiom_xinhua_raw.json`（10MB），
而該檔被 `.gitignore` 排除。**乾淨 clone 會在第 2 步直接失敗。**

`.gitignore` 當時的註解還寫成「可由 build_lexicons.py 重建」——方向剛好相反，
是那支腳本**消費**它。

已修：`fetch_idiom_source()` 在缺檔時自動由上游下載。
驗證：下載得到的檔與本地檔**位元組完全相同**（10.3 MB，30,895 條）。

---

## 2　不一致的分界完全乾淨 ⭐

52 個比對項的分界不是隨機的：

| | 項目 | 一致 |
| --- | --- | :-: |
| **不依賴生成式 LLM** | 探針檔 sha、S1–S4 與 raw_length 的並列上限、Lost-in-the-Middle 全部、`human_vs_gold`、題數 | **20/20 ✅** |
| **依賴生成式 LLM** | 正確率、兩層之差、位置效應、`judge_vs_human`、S5/S7/S8 的並列上限、各結果檔 sha | **0/32 🔴** |

抽樣是確定性的（`build_probes.py` 逐位元重現），統計也是。
非確定性**只**來自端點的生成模型。

---

## 3　原因：端點換了模型，不是 per-call 隨機

這兩者的處置方式完全不同，所以必須分辨清楚。

**證據一：連續呼叫是穩定的。**
20 句 × 3 次、**停用快取**、`temperature=0`：

| 階段 | 三次結果完全相同 |
| --- | :-: |
| 翻譯 | 20/20（100%） |
| judge | 20/20（100%） |

**證據二：現在的呼叫等於重現值，從不等於原值。**
挑 5 筆譯文有差異的題目重新呼叫 3 次：

| 題目 | 8/20-21 原值 | 8/22-23 重現值 | 現在 3 次 |
| --- | --- | --- | --- |
| `wsd-帶-b6cb` | You could even bring a girl back. | You can bring a girl back. | 1 種，＝重現值 |
| `wsd-熱-842c` | …overheated during operation and caught fire. | …overheated and caught fire. | 1 種，＝重現值 |
| `wsd-叫-7a40` | Keep watch over the hostage. | YUI ordered the guards to watch over the hostages. | 1 種，＝重現值 |

⇒ **管線在端點狀態固定時是確定性的；端點本身是會動的。**

**證據三：無法從 API 察覺。**
沒有 `system_fingerprint`；`/models` 的 `created` 是固定佔位值 `1677610602`；
model id 仍叫 `mistral-small-4`。

已建 `scripts/endpoint_fingerprint.py`：送一組固定長句、雜湊輸出。
指紋變了就代表端點變了。基準已記錄於 `endpoint_fingerprint.json`。

⚠️ 第一版的探測句是八個簡單直述句，兩個 model id 給出**逐字相同**的譯文，
指紋形同虛設。已換成有子句嵌套、省略主詞、量詞的長句。
（而「兩個 model id 輸出高度一致」這件事本身，導向了第 5 節。）

---

## 4　對結論的影響

| 指標 | 原值 | 重現值 | 判讀 |
| --- | :-: | :-: | --- |
| 對比錯誤率 | 29.6% | 30.1% | 差 0.5pp，遠小於 CI 寬度 |
| 兩層之差 | +3.9pp | +7.2pp | 兩者的 CI 都涵蓋 0，結論同為「無效果」 |
| 位置效應 p | 0.084 | 0.201 | 兩者皆不顯著 |
| 主流／非主流 | 0.724／0.685 | 0.735／0.663 | 方向一致 |
| **judge vs 人工** | **85%** | **75%** | 🔴 **翻過門檻，AUC 閘門關閉** |

**方向性結論全部穩健，點估計會動。** 但有一個例外：

🔴 **judge 一致率跨過了 85% 的門檻**，AUC 閘門因此關閉，第 7 步無法執行。
20 筆中差 2 筆就翻盤——**n=20 的驗證集太小，不足以當作閘門的判準**。
這是設計缺陷，不是運氣不好。

---

## 5　附帶發現：`judge_cross` 可能一直是假的 🔴

建端點指紋時發現兩個 model id 的輸出高度一致，追查後得到：
**`mistral-small-4` 與 `gpt-oss-120b` 的 tokenizer 截斷點在三個不同的
`max_tokens` 下逐字相同。**

完整證據與影響範圍見 [`endpoint_identity_check.md`](endpoint_identity_check.md)。

---

## 6　「可重現」該怎麼講

**不能講「數字相同」。** 依賴生成式 LLM 的數字都不相同，
而且原因不在我們能控制的範圍內。

可以講的是：

1. **給定端點狀態，管線是確定性的**（20 句 × 3 次驗證，100% 相同）
2. **抽樣與統計完全可重現**（探針檔逐位元相同）
3. **方向性結論穩健**（§4，唯一例外是被閘門放大的 judge 一致率）
4. **端點漂移可被偵測**（`endpoint_fingerprint.py`）

README 應以此為主張，並附上 26.6 分鐘的成本估計與漂移警語。
