# 用不同模型當 judge，不代表 judge 是獨立的

> 一個部署層的陷阱，以及一個五分鐘就能做完的檢查。
> 本文源自 Cognitive-Core 專案 2026-08-23 的一次除錯。

## 問題

LLM-as-a-Judge 的標準防呆是「受測模型與評判模型不能是同一個」，
否則 self-preference bias 無法排除。實作上通常寫成這樣：

```python
if (subject.provider, subject.model) == (judge.provider, judge.model):
    raise RuntimeError("球員兼裁判")
```

本專案就是這樣寫的。受測 `mistral-small-4`、judge `gpt-oss-120b`，
字串不同，檢查一路通過，測試全綠。

**但兩個 model id 由同一個後端提供服務。**

檢查的是**名稱**，而 self-preference bias 取決於**是不是同一個模型**。
名稱由 API 供應方決定，與後端實際載入什麼權重之間沒有保證。

## 為什麼難以察覺

| 想查的東西 | 實際情況 |
| --- | --- |
| 回應的 `system_fingerprint` | `None` |
| `/models` 端點的版本資訊 | `created` 是固定佔位值 `1677610602` |
| 模型 id | 兩個確實不同 |
| 自我描述（「你是哪個模型？」） | 兩者都回答服務方注入的統一身分 |

沒有任何一個欄位會告訴你這件事。而且結果看起來完全正常——
judge 會給出合理的判定、合理的信心分數、合理的理由。

## 檢查方法：截斷點

`max_tokens` 的截斷發生在推論引擎，用的是**模型自己的 tokenizer**。
不同的 tokenizer 對同一段文字的切分方式不同，截斷位置就會不同。

送同一個「請原樣輸出以下文字」的指令，在數個 `max_tokens` 下比較截斷位置：

```python
PROBE = "Output exactly this and nothing else: 人工智慧與機器學習的差異在於前者涵蓋範圍更廣，機器學習只是其中一個子領域。"

for mt in (6, 10, 16):
    for role in ("subject", "judge"):
        r = call(role, PROBE, max_tokens=mt, temperature=0)
        print(mt, role, repr(r.strip()))
```

本專案量到的結果：

| `max_tokens` | `mistral-small-4` | `gpt-oss-120b` | |
| :-: | --- | --- | :-: |
| 6 | `人工智慧與`（5 字） | `人工智慧與`（5 字） | 🔴 同 |
| 10 | `人工智慧與機器學`（8 字） | `人工智慧與機器學`（8 字） | 🔴 同 |
| 16 | `人工智慧與機器學習的差異在`（13 字） | `人工智慧與機器學習的差異在`（13 字） | 🔴 同 |

對照組（Gemini `gemini-flash-latest`）在 `max_tokens=10` 下用掉 7 tokens
且回傳空字串——切分方式明顯不同。**這才是不同 tokenizer 該有的樣子。**

Mistral 的 Tekken 與 GPT-OSS 的 o200k 系 tokenizer 對中文的切分不同，
在三個不同切點上完全一致的機率極低。

### 佐證（單獨看都不決定性，合起來很難解釋）

- 同一段輸入的 `prompt_tokens` 完全相同（906 與 915，兩組不同輸入）
- 八個複雜長句的英譯 **7/8 逐字相同**
- 同一個自由生成指令，兩者的**前 45 字逐字相同**後才分歧

## 這個檢查的界線

**必要條件，不是充分條件。**

- 截斷點不同 → 一定是不同的 tokenizer → 幾乎確定是不同模型
- 截斷點相同 → 同一個 tokenizer。可能是同一個模型，
  也可能是「兩個不同模型共用一份 tokenizer 設定」的部署錯誤

但兩種情況下，**judge 獨立性的宣稱都不成立**——後者表示至少有一個
model id 名不副實，你無法確定 judge 是什麼。所以兩種都該擋。

## 建議

1. **名稱檢查保留**，它擋得住「換設定時不小心設成同一個」，很便宜。
2. **加上行為檢查**，作為真正的判準。實作見
   [`src/cognitive_core/eval/cross_check.py`](../src/cognitive_core/eval/cross_check.py)。
3. **檢查失敗時不要放寬它。** 本專案的作法是：
   - 主流程未通過即拒絕執行，必須明示 `--allow-same-backend` 才放行，
     且該事實寫進報表標頭
   - 測試留紅，docstring 寫明「這支測試的紅色本身就是研究發現的一部分」
4. **在報告中撤回獨立性宣稱**，而不是宣稱「我們用了不同模型所以客觀」。

## 對誰有用

任何以「我們用了不同的模型當 judge」來主張評判客觀性的研究——
特別是使用共用推論閘道、學術單位自建 proxy、
或任何一個 API 端點同時提供多個 model id 的情況。

字串檢查通過、測試全綠、結果看起來正常，
而那個防呆機制在部署層面已經被架空了。

---

*相關檔案：[`endpoint_identity_check.md`](../data/results/endpoint_identity_check.md)（完整證據）、
[`cross_check.py`](../src/cognitive_core/eval/cross_check.py)（實作）、
[`test_cross_check.py`](../tests/test_cross_check.py)（含刻意保留的紅燈）*
