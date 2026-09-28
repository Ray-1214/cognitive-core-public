# MT 詞義錯誤基準　n=400

> ⚠️ **judge 未經人工驗證前，所有數字標為 preliminary。**
> 翻譯：`ithu/mistral-small-4`　judge：`ithu/gpt-oss-120b`（judge_cross：不同訓練來源，非同一模型）
> 任務：CWN-SemCor 句子 → 翻成英文 → judge 判譯文表達哪個義項 → 比對 CWN gold

## 停止判準

- ✅ 全部未觸發

## 整體

| 項目 | 值 |
| --- | :-: |
| 總題數 | 400 |
| translation_failed | 0/400（0%） |
| error | 0/400（0%） |
| judge 回 NONE | 22/400（6%） |
| **可判定** | 378/400（94%） |
| **義項正確率** | **0.508**　[0.458, 0.558] |

## 分層 ⭐ 主結果

| 層 | n（可判定） | 正確 | 正確率 | 95% CI |
| --- | :-: | :-: | :-: | :-: |
| 主流（gold 為最高頻） | 189 | 99 | 0.524 | [0.453, 0.594] |
| 非主流 | 189 | 93 | 0.492 | [0.422, 0.563] |

**兩層之差（主流 − 非主流）**：+3.2pp　95% CI [-6.9, +13.2]pp　p≈0.559

| 觀察 | 判讀 |
| --- | --- |
| 主流高、非主流低 | 走頻率捷徑，沒讀脈絡 |
| 兩層相近 | 真的在讀脈絡 |
| 兩層都低 | 任務太難或 judge 有問題 |

---

## (a) NONE 的成因

> NONE 有時是正確的：譯文若根本沒譯出該詞，任何義項都不符。
> 分兩類才知道 NONE 比例是特性還是缺陷。

| 類別 | n | 比例 | 判讀 |
| --- | :-: | :-: | --- |
| 譯文沒譯出該詞 | 10 | 45%　[0.269, 0.653] | **NONE 正確**，是翻譯的遺漏不是 judge 的錯 |
| 譯文有譯出但 judge 認不出 | 12 | 55%　[0.347, 0.731] | **judge 的問題**，計入 judge 錯誤率 |
| 未分類 | 0 | — | 成因分類呼叫失敗 |

NONE 總數 22／400，已分類 22

---

## (b) 錯誤時模型選了哪個義項 ⭐ 與 CHA-Gen 的銜接

> CHA-Gen 發現「模型偏好主流解讀」。若成立，本專案的錯誤應集中在
> 該詞的最高頻義項那一側。隨機基準為 1/候選數的加權平均。

- 錯誤題數：186
- 其中選到**最高頻義項**：27（14.5%，95% CI [10.2, 20.3]%）
- 隨機基準：13.7%
- **未超過隨機基準（CI 涵蓋之），尚不足以支持**

選中義項的頻率排名分布：第1名 27　第2名 51　第3名 21　第4名 24　第5名 19　第6名 27　第7名 9　第8名 8

---

## (c) 長度稽核

> 問「答錯的題目句子是否較長」。分層報告——聚合值會正負相消
> （CHA-Gen 18 組中 12 組顯著、方向相反，中位數卻是 0.490）。
> 此處 `ambiguity_type` 欄位承載的是 stratum。


> 一次跑 80 格，α=0.05 之下光靠運氣就會有 4 格顯著，故並列 Holm 校正後的 p。
> 五個長度特徵彼此高度相關（單句探針上 probe_span == full_input，且「詞數估計」是字元數的單調函數，
> AUC 只看排序故三者必然同值），所以要看的是有幾個**分層**出現效果，不是有幾格。

| 分層 | 特徵 | n（錯／對） | AUC | SE | 95% CI | 效應量 | 方向 | 排除 0.5 | Holm p |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 整體 | probe_span 字元數 | 186／192 | 0.554 | 0.030 | [0.496, 0.612] | 0.054 | 選錯者較長 | — | 1.000 |
| 整體 | full_input 字元數 | 186／192 | 0.554 | 0.030 | [0.496, 0.612] | 0.054 | 選錯者較長 | — | 1.000 |
| 整體 | probe_span 詞數估計 | 186／192 | 0.554 | 0.030 | [0.496, 0.612] | 0.054 | 選錯者較長 | — | 1.000 |
| 整體 | probe_span 標點數 | 186／192 | 0.496 | 0.030 | [0.437, 0.554] | 0.004 | 選對者較長 | — | 1.000 |
| 整體 | context 字元數 | 186／192 | 0.500 | 0.030 | [0.442, 0.558] | 0.000 | — | — | 1.000 |
| target_word=熱 | probe_span 字元數 | 3／3 | 0.000 | nan | 退化（排列檢定 p=0.0965） | 0.500 | 選對者較長 | — | 1.000 |
| target_word=熱 | full_input 字元數 | 3／3 | 0.000 | nan | 退化（排列檢定 p=0.0965） | 0.500 | 選對者較長 | — | 1.000 |
| target_word=熱 | probe_span 詞數估計 | 3／3 | 0.000 | nan | 退化（排列檢定 p=0.0965） | 0.500 | 選對者較長 | — | 1.000 |
| target_word=就 | probe_span 字元數 | 5／4 | 0.850 | 0.136 | [0.583, 1.000] | 0.350 | 選錯者較長 | ✅ | 0.804 |
| target_word=就 | full_input 字元數 | 5／4 | 0.850 | 0.136 | [0.583, 1.000] | 0.350 | 選錯者較長 | ✅ | 0.804 |
| target_word=就 | probe_span 詞數估計 | 5／4 | 0.850 | 0.136 | [0.583, 1.000] | 0.350 | 選錯者較長 | ✅ | 0.804 |
| target_word=度 | probe_span 字元數 | 4／7 | 0.750 | 0.167 | [0.422, 1.000] | 0.250 | 選錯者較長 | — | 1.000 |
| target_word=度 | full_input 字元數 | 4／7 | 0.750 | 0.167 | [0.422, 1.000] | 0.250 | 選錯者較長 | — | 1.000 |
| target_word=度 | probe_span 詞數估計 | 4／7 | 0.750 | 0.167 | [0.422, 1.000] | 0.250 | 選錯者較長 | — | 1.000 |
| target_word=發 | probe_span 字元數 | 3／4 | 0.750 | 0.205 | [0.348, 1.000] | 0.250 | 選錯者較長 | — | 1.000 |
| target_word=發 | full_input 字元數 | 3／4 | 0.750 | 0.205 | [0.348, 1.000] | 0.250 | 選錯者較長 | — | 1.000 |
| target_word=發 | probe_span 詞數估計 | 3／4 | 0.750 | 0.205 | [0.348, 1.000] | 0.250 | 選錯者較長 | — | 1.000 |
| target_word=空 | probe_span 字元數 | 4／3 | 0.250 | 0.205 | [0.000, 0.652] | 0.250 | 選對者較長 | — | 1.000 |
| target_word=空 | full_input 字元數 | 4／3 | 0.250 | 0.205 | [0.000, 0.652] | 0.250 | 選對者較長 | — | 1.000 |
| target_word=空 | probe_span 詞數估計 | 4／3 | 0.250 | 0.205 | [0.000, 0.652] | 0.250 | 選對者較長 | — | 1.000 |
| target_word=中 | probe_span 字元數 | 12／12 | 0.747 | 0.102 | [0.546, 0.947] | 0.247 | 選錯者較長 | ✅ | 1.000 |
| target_word=中 | full_input 字元數 | 12／12 | 0.747 | 0.102 | [0.546, 0.947] | 0.247 | 選錯者較長 | ✅ | 1.000 |
| target_word=中 | probe_span 詞數估計 | 12／12 | 0.747 | 0.102 | [0.546, 0.947] | 0.247 | 選錯者較長 | ✅ | 1.000 |
| target_word=熱 | probe_span 標點數 | 3／3 | 0.333 | 0.238 | [0.000, 0.800] | 0.167 | 選對者較長 | — | 1.000 |
| target_word=做 | probe_span 字元數 | 4／4 | 0.625 | 0.209 | [0.216, 1.000] | 0.125 | 選錯者較長 | — | 1.000 |
| target_word=做 | full_input 字元數 | 4／4 | 0.625 | 0.209 | [0.216, 1.000] | 0.125 | 選錯者較長 | — | 1.000 |
| target_word=做 | probe_span 詞數估計 | 4／4 | 0.625 | 0.209 | [0.216, 1.000] | 0.125 | 選錯者較長 | — | 1.000 |
| target_word=拍 | probe_span 字元數 | 4／3 | 0.375 | 0.230 | [0.000, 0.825] | 0.125 | 選對者較長 | — | 1.000 |
| target_word=拍 | full_input 字元數 | 4／3 | 0.375 | 0.230 | [0.000, 0.825] | 0.125 | 選對者較長 | — | 1.000 |
| target_word=拍 | probe_span 詞數估計 | 4／3 | 0.375 | 0.230 | [0.000, 0.825] | 0.125 | 選對者較長 | — | 1.000 |
| target_word=發 | probe_span 標點數 | 3／4 | 0.375 | 0.225 | [0.000, 0.816] | 0.125 | 選對者較長 | — | 1.000 |
| target_word=空 | probe_span 標點數 | 4／3 | 0.625 | 0.225 | [0.184, 1.000] | 0.125 | 選錯者較長 | — | 1.000 |
| target_word=吃 | probe_span 字元數 | 4／6 | 0.604 | 0.193 | [0.226, 0.982] | 0.104 | 選錯者較長 | — | 1.000 |
| target_word=吃 | full_input 字元數 | 4／6 | 0.604 | 0.193 | [0.226, 0.982] | 0.104 | 選錯者較長 | — | 1.000 |
| target_word=吃 | probe_span 詞數估計 | 4／6 | 0.604 | 0.193 | [0.226, 0.982] | 0.104 | 選錯者較長 | — | 1.000 |
| target_word=中 | probe_span 標點數 | 12／12 | 0.583 | 0.118 | [0.352, 0.815] | 0.083 | 選錯者較長 | — | 1.000 |
| target_word=條 | probe_span 字元數 | 4／9 | 0.417 | 0.173 | [0.077, 0.757] | 0.083 | 選對者較長 | — | 1.000 |
| target_word=條 | full_input 字元數 | 4／9 | 0.417 | 0.173 | [0.077, 0.757] | 0.083 | 選對者較長 | — | 1.000 |
| target_word=條 | probe_span 詞數估計 | 4／9 | 0.417 | 0.173 | [0.077, 0.757] | 0.083 | 選對者較長 | — | 1.000 |
| target_word=分 | probe_span 字元數 | 4／4 | 0.438 | 0.215 | [0.017, 0.858] | 0.062 | 選對者較長 | — | 1.000 |
| target_word=分 | full_input 字元數 | 4／4 | 0.438 | 0.215 | [0.017, 0.858] | 0.062 | 選對者較長 | — | 1.000 |
| target_word=分 | probe_span 詞數估計 | 4／4 | 0.438 | 0.215 | [0.017, 0.858] | 0.062 | 選對者較長 | — | 1.000 |
| target_word=吃 | probe_span 標點數 | 4／6 | 0.562 | 0.195 | [0.180, 0.945] | 0.062 | 選錯者較長 | — | 1.000 |
| target_word=條 | probe_span 標點數 | 4／9 | 0.444 | 0.176 | [0.099, 0.790] | 0.056 | 選對者較長 | — | 1.000 |
| ambiguity_type=non_dominant | probe_span 字元數 | 96／93 | 0.555 | 0.042 | [0.473, 0.637] | 0.055 | 選錯者較長 | — | 1.000 |
| ambiguity_type=non_dominant | full_input 字元數 | 96／93 | 0.555 | 0.042 | [0.473, 0.637] | 0.055 | 選錯者較長 | — | 1.000 |
| ambiguity_type=non_dominant | probe_span 詞數估計 | 96／93 | 0.555 | 0.042 | [0.473, 0.637] | 0.055 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | probe_span 字元數 | 90／99 | 0.552 | 0.042 | [0.470, 0.635] | 0.052 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | full_input 字元數 | 90／99 | 0.552 | 0.042 | [0.470, 0.635] | 0.052 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | probe_span 詞數估計 | 90／99 | 0.552 | 0.042 | [0.470, 0.635] | 0.052 | 選錯者較長 | — | 1.000 |
| target_word=去 | probe_span 標點數 | 11／8 | 0.455 | 0.138 | [0.185, 0.724] | 0.045 | 選對者較長 | — | 1.000 |
| target_word=去 | probe_span 字元數 | 11／8 | 0.540 | 0.137 | [0.272, 0.807] | 0.040 | 選錯者較長 | — | 1.000 |
| target_word=去 | full_input 字元數 | 11／8 | 0.540 | 0.137 | [0.272, 0.807] | 0.040 | 選錯者較長 | — | 1.000 |
| target_word=去 | probe_span 詞數估計 | 11／8 | 0.540 | 0.137 | [0.272, 0.807] | 0.040 | 選錯者較長 | — | 1.000 |
| target_word=行 | probe_span 字元數 | 4／9 | 0.472 | 0.179 | [0.122, 0.822] | 0.028 | 選對者較長 | — | 1.000 |
| target_word=行 | full_input 字元數 | 4／9 | 0.472 | 0.179 | [0.122, 0.822] | 0.028 | 選對者較長 | — | 1.000 |
| target_word=行 | probe_span 詞數估計 | 4／9 | 0.472 | 0.179 | [0.122, 0.822] | 0.028 | 選對者較長 | — | 1.000 |
| ambiguity_type=non_dominant | probe_span 標點數 | 96／93 | 0.489 | 0.042 | [0.407, 0.572] | 0.011 | 選對者較長 | — | 1.000 |
| ambiguity_type=dominant | probe_span 標點數 | 90／99 | 0.501 | 0.042 | [0.419, 0.584] | 0.001 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | context 字元數 | 90／99 | 0.500 | 0.042 | [0.417, 0.583] | 0.000 | — | — | 1.000 |
| ambiguity_type=non_dominant | context 字元數 | 96／93 | 0.500 | 0.042 | [0.417, 0.583] | 0.000 | — | — | 1.000 |
| target_word=中 | context 字元數 | 12／12 | 0.500 | 0.120 | [0.264, 0.736] | 0.000 | — | — | 1.000 |
| target_word=做 | context 字元數 | 4／4 | 0.500 | 0.217 | [0.076, 0.924] | 0.000 | — | — | 1.000 |
| target_word=做 | probe_span 標點數 | 4／4 | 0.500 | 0.217 | [0.076, 0.924] | 0.000 | — | — | 1.000 |
| target_word=分 | context 字元數 | 4／4 | 0.500 | 0.217 | [0.076, 0.924] | 0.000 | — | — | 1.000 |
| target_word=分 | probe_span 標點數 | 4／4 | 0.500 | 0.217 | [0.076, 0.924] | 0.000 | — | — | 1.000 |
| target_word=去 | context 字元數 | 11／8 | 0.500 | 0.138 | [0.230, 0.770] | 0.000 | — | — | 1.000 |
| target_word=吃 | context 字元數 | 4／6 | 0.500 | 0.195 | [0.117, 0.883] | 0.000 | — | — | 1.000 |
| target_word=就 | context 字元數 | 5／4 | 0.500 | 0.204 | [0.100, 0.900] | 0.000 | — | — | 1.000 |
| target_word=就 | probe_span 標點數 | 5／4 | 0.500 | 0.204 | [0.100, 0.900] | 0.000 | — | — | 1.000 |
| target_word=度 | context 字元數 | 4／7 | 0.500 | 0.189 | [0.130, 0.870] | 0.000 | — | — | 1.000 |
| target_word=度 | probe_span 標點數 | 4／7 | 0.500 | 0.189 | [0.130, 0.870] | 0.000 | — | — | 1.000 |
| target_word=拍 | context 字元數 | 4／3 | 0.500 | 0.236 | [0.038, 0.962] | 0.000 | — | — | 1.000 |
| target_word=拍 | probe_span 標點數 | 4／3 | 0.500 | 0.236 | [0.038, 0.962] | 0.000 | — | — | 1.000 |
| target_word=條 | context 字元數 | 4／9 | 0.500 | 0.180 | [0.147, 0.853] | 0.000 | — | — | 1.000 |
| target_word=熱 | context 字元數 | 3／3 | 0.500 | 0.255 | [0.001, 0.999] | 0.000 | — | — | 1.000 |
| target_word=發 | context 字元數 | 3／4 | 0.500 | 0.236 | [0.038, 0.962] | 0.000 | — | — | 1.000 |
| target_word=空 | context 字元數 | 4／3 | 0.500 | 0.236 | [0.038, 0.962] | 0.000 | — | — | 1.000 |
| target_word=行 | context 字元數 | 4／9 | 0.500 | 0.180 | [0.147, 0.853] | 0.000 | — | — | 1.000 |
| target_word=行 | probe_span 標點數 | 4／9 | 0.500 | 0.180 | [0.147, 0.853] | 0.000 | — | — | 1.000 |

**未校正 CI 排除 0.5：6 / 80 格，落在 2 個分層**
**Holm 校正後仍顯著：0 格**

⚠️ 未校正時有 6 格顯著（分層：target_word=中、target_word=就），但**沒有任何一格通過 Holm 校正**。
在這個格數下這個數量與純機率相符，不足以支持「有長度混淆」。

---

## 逐筆（請掃一遍判斷 judge 合不合理）

| # | 詞 | 原句 | 譯文 | judge 選的 | gold | 對 |
| :-: | :-: | --- | --- | --- | --- | :-: |
| 1 | 包 | 以一包Ａ４大小、內含20張的相片紙建議售價為從240 | A pack of A4-sized photo paper containing 20 sheets  | `05095701` | `05095711` | ❌ |
| 2 | 歲 | 今年才五十歲， | He's only fifty this year. | `06559405` | `06559405` | ✅ |
| 3 | 帶 | 就能帶個女孩回來。 | You could even bring a girl back. | `06791406` | `06791407` | ❌ |
| 4 | 死 | 可能這是你對我抱的至死不變的看法， | Perhaps this is the unchanging view you hold of me. | `NONE` | `05035202` | — |
| 5 | 熱 | 疑似運作過熱起火燃燒， | It appears to have overheated during operation and c | `05228702` | `05228701` | ❌ |
| 6 | 回 | 每天晚上她回乘務隊的時候， | Every night when she returns to the duty team. | `03019001` | `03019001` | ✅ |
| 7 | 空 | 這是唯識講『空』的不同處。 | This is the unique approach of the Yogācāra school i | `06517331` | `06517331` | ✅ |
| 8 | 叫 | 鍾木郎叫人看守人質， | Keep watch over the hostage. | `NONE` | `05013801` | — |
| 9 | 道 | 卻聽得其中白眉和尚哈哈一笑道： | Then the white-browed monk burst into laughter and s | `05239501` | `05239501` | ✅ |
| 10 | 拍 | 希望能多拍些劇情片。 | I hope we can make more narrative films. | `08028003` | `08028004` | ❌ |
| 11 | 中 | 讀者可由表中清楚看出， | Readers can clearly see from the table. | `04004603` | `04004605` | ❌ |
| 12 | 頭 | 頭上還要綁布條， | You still have to tie a headband. | `03043001` | `03043001` | ✅ |
| 13 | 分 | 三分天下。 | A tripartite division of the world. | `04146403` | `04146403` | ✅ |
| 14 | 畫 | 每幅畫都很不錯， | All the paintings are excellent. | `06550302` | `06550302` | ✅ |
| 15 | 包 | 但依慣例只拿了幾包藥後回家養病。 | But as usual, he only took a few packs of medicine a | `05095701` | `05095711` | ❌ |
| 16 | 心 | 只有母親能真正了解我心中的感受， | Only a mother can truly understand the feelings in m | `05231612` | `05231612` | ✅ |
| 17 | 小 | 再把芒果切成一小片， | Then cut the mango into small pieces. | `05227101` | `05227101` | ✅ |
| 18 | 分 | 顯示中共有意分階段解決問題， | The Chinese Communist Party has expressed its intent | `04146403` | `04146403` | ✅ |
| 19 | 去 | 本來要下樓去買幾包速食麵， | I was about to go downstairs to buy a few packs of i | `06559201` | `06559205` | ❌ |
| 20 | 口 | 口吐白沫， | Foaming at the mouth. | `04084201` | `04084201` | ✅ |
| 21 | 掛 | 比如今八三歲父親至今還掛在牆上親自題著「音容宛在」的 | A portrait of a young woman with the inscription "音容 | `06701402` | `06701401` | ❌ |
| 22 | 投 | 並非自己投了自己的。 | I did not vote for myself. | `06685709` | `06685709` | ✅ |
| 23 | 下 | 在共黨獨裁政權下產生的文學作品， | Literary works produced under a communist dictatorsh | `04081808` | `04081817` | ❌ |
| 24 | 心 | 心中非常不甘願， | I am very reluctant. | `05231608` | `05231612` | ❌ |
| 25 | 歲 | 不具高所得或高不動產的六十五歲以上老人， | Elderly individuals aged 65 or above who do not poss | `06559405` | `06559405` | ✅ |
| 26 | 歲 | 前總統李登輝七十八歲高齡， | Taiwan's former President Lee Teng-hui passed away a | `06559405` | `06559405` | ✅ |
| 27 | 去 | 你先去預備圖章， | Please go prepare the seal first. | `06559201` | `06559205` | ❌ |
| 28 | 發 | 象、獅隊球團發獎金也不手軟， | The Lions and Elephants team's management generously | `06724101` | `06724101` | ✅ |
| 29 | 吃 | Ｗｉｎｓｔｏｎ告訴我們無論如何也要買隻大螃蟹吃才不虛 | Winston told us we absolutely have to buy a big crab | `05227001` | `05227001` | ✅ |
| 30 | 歲 | 是我那個七十一歲的外婆和小外公吵著要離婚， | My seventy-one-year-old grandmother and grandfather  | `06559405` | `06559405` | ✅ |
| 31 | 低 | 創下八十六年以來同季首度滑落千億元以下的最低紀錄。 | It marked the lowest record in over 86 years to fall | `06748407` | `06748406` | ❌ |
| 32 | 歲 | 你不能要求兩歲的小孩， | You cannot expect a two-year-old child to do that. | `06559405` | `06559405` | ✅ |
| 33 | 拉 | 拉著大書包走下車， | I pulled my large backpack off the bus. | `05230801` | `05230801` | ✅ |
| 34 | 中 | Ｂｏｙｅｒ－Ｍｏｏｒｅ的方法是所有已知的字串比對方法 | Boyer-Moore method is the fastest among all known st | `04004605` | `04004605` | ✅ |
| 35 | 回 | 黑派理應回座維持會務， | YUI should return to her seat to maintain the meetin | `03019001` | `03019001` | ✅ |
| 36 | 邊 | 眼見一群男孩子就守在河邊， | A group of boys was seen standing by the river. | `06584405` | `06584404` | ❌ |
| 37 | 明 | 第四繼承時期是五代至明末。 | The fourth inheritance period spans from the Five Dy | `07003502` | `07003501` | ❌ |
| 38 | 層 | 表演者自十層樓一躍而下， | The performer leapt to his death from the tenth floo | `03005001` | `03005002` | ❌ |
| 39 | 前 | 三年前因為突然呼吸困難及全身不舒服， | Three years ago, I suddenly experienced difficulty b | `03033712` | `03033712` | ✅ |
| 40 | 點 | 同時在四三００至四七００點間採行箱型操作， | Box operations are conducted between 4300 and 4700 p | `04043808` | `04043808` | ✅ |
| 41 | 歲 | 今年整整滿一百歲了。 | This year marks exactly one hundred years. | `06559403` | `06559405` | ❌ |
| 42 | 好 | 「下半場上來的那名後衛很好！ | The defender who came on in the second half is reall | `04157701` | `04157701` | ✅ |
| 43 | 坐 | 反不若坐在家中，等待政黨比例代表制下的提名， | Just stay home and wait for a nomination under the p | `05223901` | `05223901` | ✅ |
| 44 | 去 | 以及親手去使用這些資料。 | And personally use this data. | `06559208` | `06559205` | ❌ |
| 45 | 坐 | 他習慣坐在客運公司走廊一角， | He is used to sitting in a corner of the corridor at | `05223901` | `05223901` | ✅ |
| 46 | 上 | 多媒體在網路上的應用確實擁有無限發展潛力， | Multimedia applications on the internet indeed have  | `04081315` | `04081314` | ❌ |
| 47 | 場 | 國王明星大前鋒韋伯則攻下全隊最高的21分以及本季個人 | King star power forward Webber scored a team-high 21 | `06721705` | `06721709` | ❌ |
| 48 | 歲 | 四十五歲的臺北水準書局老闆曾大福搭朋友的車南下， | The 45-year-old owner of Taipei Shuei-shui Bookstore | `06559405` | `06559405` | ✅ |
| 49 | 折 | 打七五折是四百六十五。 | It's NT$465 after a 25% discount. | `07033113` | `07033113` | ✅ |
| 50 | 面 | 難道那不是人生真實的一面？ | Isn't that just one aspect of real life? | `03028804` | `03028804` | ✅ |
| 51 | 拉 | 他整天拉著鞋， | He drags his shoes all day. | `05230801` | `05230801` | ✅ |
| 52 | 歲 | 看到一位七十幾歲的老先生， | I saw an elderly gentleman in his seventies. | `06559405` | `06559405` | ✅ |
| 53 | 拉 | 是將台灣拉向一個被強勢文化（好萊塢）同質化的下場， | It would lead Taiwan down the path of homogenization | `05230804` | `05230801` | ❌ |
| 54 | 中 | 但是這並不代表婦女在家中的責任減輕了。 | But this does not mean that women's responsibilities | `04004604` | `04004605` | ❌ |
| 55 | 會 | 約在１０﹣１２天大時會出現銅離子負平衡， | Around 10 to 12 days old, copper ion negative balanc | `04143405` | `04143405` | ✅ |
| 56 | 頭 | 做出一個大小適中的頭， | Make a head of moderate size. | `03043001` | `03043001` | ✅ |
| 57 | 畫 | 如果用來記錄美術館的畫， | The system is used to record paintings in an art mus | `06550302` | `06550302` | ✅ |
| 58 | 歲 | 共有兩百位八十歲以上的壽星在家人的陪同下， | A total of two hundred centenarians, accompanied by  | `06559405` | `06559405` | ✅ |
| 59 | 心 | 心裡很不是滋味。 | It leaves a bitter taste in my heart. | `05231612` | `05231612` | ✅ |
| 60 | 去 | 準備挑到城裡去賣。 | I'm going to take them to the city to sell. | `06559201` | `06559205` | ❌ |
| 61 | 新 | 與近千位新舊政府團隊和工商界的共同見證下， | Under the joint witness of nearly a thousand members | `05237901` | `05237904` | ❌ |
| 62 | 空 | 最後一幕『菩提』代表著『空』， | The final scene "Bodhi" represents "Emptiness." | `06517331` | `06517331` | ✅ |
| 63 | 坐 | 凱洛琳在一個油鍋前坐著， | Caroline was sitting in front of a deep fryer. | `05223901` | `05223901` | ✅ |
| 64 | 拉 | 還是每天拉著那輛三輪車沿街拾荒， | I still pull that tricycle around the streets scaven | `05230801` | `05230801` | ✅ |
| 65 | 言 | 就前者而言， | In this regard, | `NONE` | `06008204` | — |
| 66 | 歲 | 一個在三十歲之前沒有成為社會主義信徒的人， | A person who hasn't become a socialist believer befo | `06559405` | `06559405` | ✅ |
| 67 | 帶 | 事後我帶他回南部老家見父母， | Afterward, I took him back to my hometown in souther | `06791406` | `06791407` | ❌ |
| 68 | 抽 | 又抽大麻睡著了， | I smoked weed again and fell asleep. | `06598613` | `06598614` | ❌ |
| 69 | 歲 | 今年八十歲的王自牧， | Eighty-year-old Wang Tzu-mu | `06559405` | `06559405` | ✅ |
| 70 | 股 | 首季每股稅後盈餘約○．八元。 | The after-tax earnings per share for the first quart | `03015702` | `03015710` | ❌ |
| 71 | 做 | 也乾脆放下生意不做， | Just quit the business altogether. | `06664306` | `06664306` | ✅ |
| 72 | 來 | 但嚴格來說銀行業的壞帳比票券業更難計算， | But strictly speaking, bad debts in the banking indu | `04086501` | `04086509` | ❌ |
| 73 | 明 | 就好像在濃霧中遇到一盞明燈一樣。 | It was like encountering a bright beacon in the thic | `06685411` | `06685401` | ❌ |
| 74 | 中 | 在ＩＰ通訊協定中， | In IP communication protocols, | `04004605` | `04004605` | ✅ |
| 75 | 強 | 當海水清澈、陽光穿透力強的時候， | When the sea is clear and sunlight penetrates deeply | `09250308` | `09250303` | ❌ |
| 76 | 吃 | 有純樸簡單碼頭、熱鬧大船小舟、傳統市集、酒吧各式吃喝 | There are simple and rustic docks, bustling large an | `05227024` | `05227001` | ❌ |
| 77 | 吃 | 便和同學偷溜跑去吃刨冰， | We sneaked out with classmates to have shaved ice. | `05227001` | `05227001` | ✅ |
| 78 | 中 | 不必再侷限於那三類網路位址結構中， | There is no need to be limited to those three types  | `04004605` | `04004605` | ✅ |
| 79 | 上 | 就把媽祖在海上顯靈的事蹟， | Mazu's miraculous manifestations at sea | `04081315` | `04081314` | ❌ |
| 80 | 叫 | 出現一個叫永窮的窮小子， | A poor young man named Yongqiong appeared. | `04010207` | `04010206` | ❌ |
| 81 | 吃 | 知了喜歡吃樹葉、露水， | Cicadas like to eat tree leaves and dew. | `05227001` | `05227001` | ✅ |
| 82 | 股 | 中華電週二公布今年每股純益目標為四．一六元， | Taiwan Mobile announced on Tuesday that its target f | `03015702` | `03015710` | ❌ |
| 83 | 間 | 省能產品也成為未來國際間的最大商機， | Energy-efficient products are also becoming the bigg | `04084102` | `04084104` | ❌ |
| 84 | 歲 | 當場查獲釣蝦場女會計蔡雅惠（廿歲， | A female accountant at a crayfish farm, Tsai Ya-hui  | `06559405` | `06559405` | ✅ |
| 85 | 歲 | 因為我30歲， | Because I am 30 years old. | `06559405` | `06559405` | ✅ |
| 86 | 中 | 中菲國會議員友好協會會長。 | Chairman of the China-Philippines Parliamentary Frie | `08011201` | `08011203` | ❌ |
| 87 | 做 | 為什麼日本人要這麼做？ | Why do the Japanese do this? | `06664308` | `06664306` | ❌ |
| 88 | 去 | 並非去抗議。 | It's not about going to protest. | `06559201` | `06559205` | ❌ |
| 89 | 去 | 試著去接近森林， | Try to approach the forest. | `06559201` | `06559205` | ❌ |
| 90 | 日 | 以實品文物、各國服飾、鈔票特區及影像展呈現出日、韓、 | The exhibition showcases the charm of Japan, South K | `05239901` | `05239901` | ✅ |
| 91 | 低 | 我國以女性為戶長的單親家庭比例（７１７６％）較歐美低 | The proportion of single-parent households headed by | `06748406` | `06748406` | ✅ |
| 92 | 拍 | 一走紅大家都搶著找她拍， | Once she became popular, everyone scrambled to colla | `08028001` | `08028004` | ❌ |
| 93 | 度 | 在澳洲風景明媚的海灘度了兩天假之後， | After spending two days of vacation on Australia's s | `06785401` | `06785402` | ❌ |
| 94 | 吃 | 只要有一餐吃得太放肆， | If you eat too extravagantly at one meal, | `05227001` | `05227001` | ✅ |
| 95 | 真 | 真是惡名昭彰的傢伙。 | What a notoriously infamous guy. | `05100414` | `05100413` | ❌ |
| 96 | 新 | 並同時實施新的審查制度； | At the same time, a new censorship system was implem | `05237901` | `05237904` | ❌ |
| 97 | 包 | 臨走時帶包來自天津１８街桂發祥的麻花， | I'll bring some twisted crullers from Tianjin's 18th | `05095702` | `05095711` | ❌ |
| 98 | 去 | 去住旅館好了！ | Let's just stay at a hotel! | `06559201` | `06559205` | ❌ |
| 99 | 約 | 約她一起去附近的商店買下星期的吃食。 | Invite her to go to a nearby store to buy food for n | `NONE` | `05052303` | — |
| 100 | 季 | 亞洲出口成長仍於二○○一年第四季反彈回升。 | Asia's export growth rebounded in the fourth quarter | `07026505` | `07026505` | ✅ |
| 101 | 分 | 還讓他發現自己真有幾分語言天份。 | It also allowed him to discover that he had some tal | `05007209` | `05007209` | ✅ |
| 102 | 小 | 以小動物來作試驗， | Animal testing is conducted. | `NONE` | `05227101` | — |
| 103 | 發 | 每位候選人總是發一大堆傳單， | Every candidate always distributes a large number of | `06724101` | `06724101` | ✅ |
| 104 | 大 | 年紀輕輕的就擔負這麼大的責任， | At such a young age, you're taking on such great res | `05227204` | `05227204` | ✅ |
| 105 | 帶 | 或帶小孩郊遊。 | Go for an outing with children. | `06791406` | `06791407` | ❌ |
| 106 | 部 | 那是漫長的一部曲折而辛酸的歷史。 | That was a long, convoluted, and bitter history. | `05075701` | `05075710` | ❌ |
| 107 | 高 | 台大最高， | National Taiwan University is the best. | `06010615` | `06010610` | ❌ |
| 108 | 上 | 街頭上到處也可以看到咖啡店． | You can see coffee shops everywhere on the streets. | `04081315` | `04081314` | ❌ |
| 109 | 折 | 軍警票改為八折優待， | Commissioned tickets for military and police personn | `07033113` | `07033113` | ✅ |
| 110 | 起 | 報名自即日起受理， | Registration is now open. | `04004828` | `04004801` | ❌ |
| 111 | 中 | 恍恍惚惚腦中忽然瞥過過去她那激憤壯烈的夢。 | A fleeting image of her passionate and heroic dream  | `04004604` | `04004605` | ❌ |
| 112 | 說 | 他已說過很多遍， | He has said it many times. | `05212401` | `05212401` | ✅ |
| 113 | 大 | 小問題大煩惱資料漏失時的處理．何鴻毅問： | When minor issues cause major troubles: Handling dat | `05227205` | `05227204` | ❌ |
| 114 | 條 | 他還是執意走上這條不歸路， | He still insisted on taking this irreversible path. | `06585924` | `06585924` | ✅ |
| 115 | 做 | 他也把我們的垃圾做分類， | He also sorts our trash for recycling. | `06664307` | `06664306` | ❌ |
| 116 | 好 | 做個好女兒， | Be a good daughter. | `04157701` | `04157701` | ✅ |
| 117 | 說 | 陳總統說去年三一八事件今年可能重演； | President Tsai said that the March 18 incident last  | `05212401` | `05212401` | ✅ |
| 118 | 中 | 第一票不能改變各政黨在國會中的席次比。 | The first vote does not change the seat distribution | `04004605` | `04004605` | ✅ |
| 119 | 言 | 而所謂的新指甲可能也是指在老指甲下方的油脂指床而言。 | The so-called new nail may also refer to the fat nai | `06008211` | `06008204` | ❌ |
| 120 | 吃 | 年年拼死吃， | I fight to eat every year. | `05227009` | `05227001` | ❌ |
| 121 | 小 | 微細世界．小貓咪和貓熊一樣， | The tiny world is such that kittens are just like pa | `05227101` | `05227101` | ✅ |
| 122 | 條 | 要走哪條路呢？ | Which path should we take? | `06585924` | `06585924` | ✅ |
| 123 | 條 | 便可堆出一條筆直的高級公路。 | A straight, high-quality highway can be built this w | `06585906` | `06585924` | ❌ |
| 124 | 去 | 不必去當兵， | You don't have to enlist in the military. | `06559205` | `06559205` | ✅ |
| 125 | 季 | 第二季半導體景氣及公司業績可望觸底， | The semiconductor market outlook and company perform | `07026505` | `07026505` | ✅ |
| 126 | 層 | 地下三層）與緊鄰也將接著完工的資訊大樓， | The basement third floor and the adjacent Informatio | `03005001` | `03005002` | ❌ |
| 127 | 吃 | 冰淇淋只好給弟弟吃啦！ | Ice cream can only be given to my little brother to  | `05227001` | `05227001` | ✅ |
| 128 | 拿 | 我都拿體重計為小豬們檢查身體， | I always use the scale to check the health of the li | `04011209` | `04011201` | ❌ |
| 129 | 明 | 明起路邊停車巡場管理員將不再受理民眾繳交停車費， | Starting tomorrow, roadside parking patrol officers  | `07003401` | `07003401` | ✅ |
| 130 | 度 | 第四度獲奧斯卡提名。 | He received his fourth Oscar nomination. | `05147620` | `05147620` | ✅ |
| 131 | 中 | 每家主婦都率領家中的婦女， | Every housewife leads the women in her household. | `04004603` | `04004605` | ❌ |
| 132 | 使 | 使我們變得很有禮貌。 | Let us be very polite. | `06560201` | `06560202` | ❌ |
| 133 | 中 | 在佛法中所謂的經濟， | In Buddhism, what is referred to as "economy" | `04004605` | `04004605` | ✅ |
| 134 | 上 | 林青霞也在記者會上感動的表示， | Yvonne Yeh also emotionally expressed at the press c | `04081315` | `04081314` | ❌ |
| 135 | 行 | 父母就希望你只要書念好就行了。 | Parents just hope that you do well in your studies. | `06775706` | `06775711` | ❌ |
| 136 | 點 | 以佔指數較重之金融股搶攻４９００點， | Financial stocks, which carry significant weight in  | `04043808` | `04043808` | ✅ |
| 137 | 拍 | 拍那個終極保鏢的時候。 | When they were filming that ultimate bodyguard. | `08028003` | `08028004` | ❌ |
| 138 | 小 | 身長卻還只是２公分那麼小呢！ | It's still only 2 centimeters tall! | `05227101` | `05227101` | ✅ |
| 139 | 還 | 但應該還會再等幾個月， | But we should still wait for a few more months. | `05002705` | `05002703` | ❌ |
| 140 | 畫 | 在絹布上做畫。 | Painting on silk fabric. | `06550301` | `06550302` | ❌ |
| 141 | 拍 | 輕輕拍了他一下， | He gave him a gentle pat. | `08027901` | `08027901` | ✅ |
| 142 | 大 | 合成一股大力量呢？ | What powerful force can we create together? | `NONE` | `05227204` | — |
| 143 | 場 | 往年常常因為某一場球賽的比賽地點、時間無法達成共識， | In past years, consensus was often difficult to reac | `06721701` | `06721709` | ❌ |
| 144 | 水 | 而且若長期飲用淡化水， | And if you drink desalinated water for a long time, | `05233801` | `05233801` | ✅ |
| 145 | 坐 | 坐在矮牆上望著大海抽菸， | Sitting on a low wall, smoking while gazing at the s | `05223901` | `05223901` | ✅ |
| 146 | 回 | 預計七月結婚的郭思宏利用寒假專程由美國回臺灣與女友拍 | Vicky and her fiancé, Kuo Szu-hung, who plans to get | `03019001` | `03019001` | ✅ |
| 147 | 錢 | 但偏偏卻有很多人願把錢送入虎口， | But for some reason, many people are still willing t | `06015102` | `06015105` | ❌ |
| 148 | 中 | 多位教授昨天在澄社主辦的座談會中， | Several professors attended a symposium hosted by th | `04004604` | `04004605` | ❌ |
| 149 | 收 | 我們不收支票。 | We do not accept checks. | `03039303` | `03039303` | ✅ |
| 150 | 粗 | 英勇的消防隊員合力舉起又粗又大的水管， | Brave firefighters worked together to lift the thick | `06711801` | `06711801` | ✅ |
| 151 | 小 | 甚至滿園成千上萬的小花， | Even the entire garden is filled with thousands upon | `05227103` | `05227101` | ❌ |
| 152 | 中 | 在上次吸吮一章中， | In the previous chapter titled "Sucking," | `04004604` | `04004605` | ❌ |
| 153 | 度 | 他們繼續在自己生活的地方和工作崗位度信仰的生活。 | They continued to live out their faith in their own  | `NONE` | `06785402` | — |
| 154 | 日 | 經驗上可能在三日內出現天價， | Experience shows that sky-high prices may appear wit | `03036209` | `03036209` | ✅ |
| 155 | 中 | 主要乃因在如此萎縮的成交量中， | Amid such shrinking transaction volumes, | `04004604` | `04004605` | ❌ |
| 156 | 空 | 在紅樓二樓右側空教室成立的「網咖」昨日開幕。 | A "net café" was inaugurated yesterday in the vacant | `07114601` | `07114607` | ❌ |
| 157 | 字 | 因為我的所有最字， | All my best wishes. | `06584501` | `06584502` | ❌ |
| 158 | 強 | 她的港裔美籍夫婿區永禧親和力強， | Her Hong Kong-born American husband Au Wing Hei has  | `09250306` | `09250303` | ❌ |
| 159 | 中 | 混合工作負荷中的「自然工作負荷」是在控制條件之下以較 | In mixed workloads, "natural workload" is executed u | `04004604` | `04004605` | ❌ |
| 160 | 會 | 學校通常會開放兩個教室， | Schools usually open two classrooms. | `04143405` | `04143405` | ✅ |
| 161 | 吃 | 家裡吃的麵都是自己做的， | We always make noodles at home ourselves. | `NONE` | `05227001` | — |
| 162 | 拉 | 連拖帶拉的把豪豪拖到公園去了。 | Dragged Hou Hou to the park, struggling all the way. | `05230801` | `05230801` | ✅ |
| 163 | 度 | 蔣介石總統曾兩度提出亡黨亡國的話， | President Chiang Kai-shek once warned twice about th | `05147620` | `05147620` | ✅ |
| 164 | 正 | 警方正擴大追查中。 | The police are expanding their investigation. | `NONE` | `07009821` | — |
| 165 | 支 | 而韓國隊卻只有七支。 | However, the South Korean team only has seven. | `03056204` | `03056210` | ❌ |
| 166 | 中 | 六年國建計畫中處處可見為人癌細胞架設的舞台， | Throughout the Six-Year National Construction Plan,  | `04004604` | `04004605` | ❌ |
| 167 | 分 | 布朗也只有八點一分， | Brown only has 8.1 points. | `05007101` | `05007102` | ❌ |
| 168 | 帶 | 秋天你帶我來歐洲好嗎？ | Would you like me to take you to Europe in the fall? | `06791406` | `06791407` | ❌ |
| 169 | 死 | 皮皮掉到山谷後居然沒死， | Pipi fell into the valley but surprisingly survived. | `05035202` | `05035202` | ✅ |
| 170 | 去 | 就可以去做事了。 | You can start working now. | `06559205` | `06559205` | ✅ |
| 171 | 吃 | 其實吃茶去並無深意。 | Actually, there is no deep meaning to drinking tea. | `NONE` | `05227001` | — |
| 172 | 做 | 程一駿也曾前往東沙群島做綠蠵龜分布調查， | Cheng I-chun also once went to the Dongsha Islands t | `06664307` | `06664306` | ❌ |
| 173 | 度 | 璩美鳳首先三度表示， | Feng Mei-feng first expressed it three times. | `05147620` | `05147620` | ✅ |
| 174 | 正 | 但樓下爸媽正興趣盎然的替她編織未來。 | But the parents downstairs are enthusiastically weav | `07009822` | `07009821` | ❌ |
| 175 | 強 | 她就有很強的自主意識， | She has a strong sense of independence. | `09250306` | `09250303` | ❌ |
| 176 | 坐 | 我坐在書桌前， | I am sitting at my desk. | `05223901` | `05223901` | ✅ |
| 177 | 坐 | 最喜歡坐在岩石上， | I love sitting on rocks. | `05223901` | `05223901` | ✅ |
| 178 | 行 | 當初是怎麼走上這行的﹖ | How did I end up in this line of work? | `05145006` | `05145006` | ✅ |
| 179 | 行 | 我們演習一下就行了， | Let's just practice. | `06775706` | `06775711` | ❌ |
| 180 | 歲 | 趁被害人黃文助（二十九歲， | The victim, Huang Wen-zhu (29 years old), | `06559405` | `06559405` | ✅ |
| 181 | 起 | 台北羽球名人邀請賽八日起在台北勝光羽球館開打， | The Taipei Badminton Invitational Tournament kicks o | `04004828` | `04004801` | ❌ |
| 182 | 深 | 而且更深一層的智慧的發揮。 | And the deeper manifestation of wisdom. | `06663315` | `06663314` | ❌ |
| 183 | 歲 | 都比薛蘋小幾歲， | Sue is a few years younger than Hsieh Pin. | `06559405` | `06559405` | ✅ |
| 184 | 中 | 致潘雙全腹部中一槍。 | A shot to the abdomen of Pan Shuangquan. | `05007601` | `05007601` | ✅ |
| 185 | 長 | 工作負荷必須花長時間來記錄， | Workload must be recorded over a long period of time | `06030810` | `06030803` | ❌ |
| 186 | 死 | 等我什麼時候也死了， | When I die someday. | `05035202` | `05035202` | ✅ |
| 187 | 人 | 有些人批國安聯盟是太上決策機制， | Some people criticize the National Security Alliance | `05231105` | `05231101` | ❌ |
| 188 | 頭 | 他說獅子的頭又大又圓， | He said the lion's head is big and round. | `03043001` | `03043001` | ✅ |
| 189 | 叫 | 阿眉叫我不要太擔心她身體。 | Mei asked me not to worry too much about her health. | `05013801` | `05013801` | ✅ |
| 190 | 就 | 就造成肥胖症。 | It can lead to obesity. | `05198301` | `05198301` | ✅ |
| 191 | 心 | 以極為艱難的說話方式表達他心中的感想。 | He expressed his thoughts in an excruciatingly diffi | `05231612` | `05231612` | ✅ |
| 192 | 過 | 而且從未請過教練， | And I have never hired a coach. | `05206001` | `05206001` | ✅ |
| 193 | 吃 | 晚上在北京飯店新樓吃羊肉， | I had lamb at the Beijing Hotel New Building in the  | `05227007` | `05227001` | ❌ |
| 194 | 會 | 沒有一家銀行會故意違反央行規定， | No bank would deliberately violate the regulations s | `04143405` | `04143405` | ✅ |
| 195 | 正 | 正準備開槍， | I was about to pull the trigger. | `NONE` | `07009821` | — |
| 196 | 去 | 我們要去旅行， | We are going to travel. | `06559201` | `06559205` | ❌ |
| 197 | 拍 | 「這部電影是誰拍的？ | Who directed this movie? | `08028003` | `08028004` | ❌ |
| 198 | 畫 | 畫裡人物竟是她夢境中的書生。 | The figure in the painting turned out to be the scho | `06550301` | `06550302` | ❌ |
| 199 | 要 | 沒想到原始人居然要睡到中午才會起來， | Primitive people actually sleep until noon before ge | `06636905` | `06636905` | ✅ |
| 200 | 中 | 座中有人提到郝柏村現象， | Someone at the gathering mentioned the "Hao Bai-cun  | `04004605` | `04004605` | ✅ |
| 201 | 就 | 這就是「相」很少印在我的心上。 | That's why the "phase" rarely leaves an impression o | `05198301` | `05198313` | ❌ |
| 202 | 度 | 亦足供七種樣本可將組織保存於液態氮或零下七十度中， | Samples can also be preserved in liquid nitrogen or  | `05147610` | `05147610` | ✅ |
| 203 | 好 | 好漂亮啊！ | That's so beautiful! | `04157710` | `04157710` | ✅ |
| 204 | 作 | 或許這部小說也是明人所作的， | Perhaps this novel was also written by a Ming dynast | `05098103` | `05098103` | ✅ |
| 205 | 小 | 小野豬叫著： | A wild boar is grunting. | `NONE` | `05227107` | — |
| 206 | 小 | 否則浪費金錢事小， | Otherwise, wasting money is the least of our concern | `05227104` | `05227104` | ✅ |
| 207 | 下 | 地球上正下著大雨， | It's raining heavily on Earth right now. | `04081830` | `04081830` | ✅ |
| 208 | 點 | 說得確實點， | Just put it bluntly. | `04043803` | `04043813` | ❌ |
| 209 | 行 | 往北漸行漸遠， | As we head north, we gradually move farther away. | `06775702` | `06775702` | ✅ |
| 210 | 吃 | 「天生我才必有用」、「吃得苦中苦， | "Great minds have aims, petty minds have wishes."
"O | `NONE` | `05227009` | — |
| 211 | 深 | 於圖書事業深有研究或經驗並有專門著作者之規定， | Persons with in-depth research or experience in libr | `06663314` | `06663313` | ❌ |
| 212 | 破 | 當年城破家亡， | The city fell, and our home was lost. | `06761406` | `06761401` | ❌ |
| 213 | 空 | 世俗諦都是假的、該空的； | All worldly truths are false and should be seen as e | `06517316` | `06517332` | ❌ |
| 214 | 花 | 棘皮動物海百合像海中之花般地鮮艷綻放， | Echinoderms like sea lilies bloom brilliantly in the | `05229001` | `05229006` | ❌ |
| 215 | 大 | 竹葉上有一大群螞蟻， | There is a large group of ants on the bamboo leaf. | `05227203` | `05227203` | ✅ |
| 216 | 去 | 走到了最常去最熟悉的圖書館， | I arrived at the most frequently visited and familia | `06559201` | `06559201` | ✅ |
| 217 | 支 | 由國內四支球隊選出的職棒明星隊負責把守第二關。 | The all-star team composed of four domestic teams wi | `03056204` | `03056204` | ✅ |
| 218 | 強 | 國男組也將進行四強交叉準決賽， | The men's team will also compete in the semifinals c | `09250303` | `09250305` | ❌ |
| 219 | 空 | 是非成敗轉頭空， | Only the translation is required:

Time turns all vi | `06517327` | `06517332` | ❌ |
| 220 | 條 | 森林之家的每條街道， | Every street in Forest Home | `06585906` | `06585906` | ✅ |
| 221 | 平 | 形成追漲殺跌皆乏力的平低震盪盤， | A flat, low-oscillation trading range where both cha | `06025219` | `06025219` | ✅ |
| 222 | 條 | 這條等於不存在， | This statement is equivalent to non-existence. | `NONE` | `06585929` | — |
| 223 | 高 | 配備精良的美國警方人員在攝影高台上嚴密監視觀眾動態， | Well-equipped U.S. police officers closely monitor t | `06010607` | `06010601` | ❌ |
| 224 | 子 | 而是要人以社會為妻為子， | But instead, people should take society as their wif | `07027901` | `07027901` | ✅ |
| 225 | 部 | 包括二十部保時捷。 | Including twenty Porsche vehicles. | `05075709` | `05075709` | ✅ |
| 226 | 行 | 有兩行特別醒目的大字， | Two lines of particularly eye-catching large charact | `05145003` | `05145004` | ❌ |
| 227 | 吃 | 所有出門的人一定要趕回家來吃年夜飯， | Everyone who goes out must rush home to have the New | `05227024` | `05227024` | ✅ |
| 228 | 格 | 由於十五格圖的四個構面恰好反應出價值鏈不同階段的特性 | The four dimensions of the 15-box matrix precisely r | `06730804` | `06730802` | ❌ |
| 229 | 對 | 但因氣氛及感覺不對， | But since the atmosphere and feeling were off. | `04017506` | `04017503` | ❌ |
| 230 | 破 | 自己發球局反在第六局被破， | I was broken in my own serve game in the sixth set. | `06761401` | `06761422` | ❌ |
| 231 | 法 | 而非國民黨統治機器所貼下標籤的地域區分法‧人們習慣稱 | People are actually accustomed to calling the "ben s | `NONE` | `05045104` | — |
| 232 | 道 | 每一個性方面的需求可能有些人比較好此道， | Every individual may have varying levels of expertis | `06002401` | `06002402` | ❌ |
| 233 | 收 | 我們音樂收起來， | Let's put the music away. | `03039313` | `03039313` | ✅ |
| 234 | 邊 | 步道一邊是長著爬籐的花架， | A path is lined with a trellis covered in climbing v | `06584401` | `06584406` | ❌ |
| 235 | 叫 | 吃飯時那張木椅便被女人寬軟的臀部撫摸得舒服地輕叫。 | As she sat on the wooden chair during the meal, it c | `NONE` | `04010205` | — |
| 236 | 發 | 並在各大專院校及教育機構發公函， | And send official letters to major universities and  | `06724108` | `06724108` | ✅ |
| 237 | 層 | 中間那層「主任」完全不在他眼裡。 | The middle-tier "Director" meant nothing to him. | `03005006` | `03005006` | ✅ |
| 238 | 過 | 透著粉綠、粉紫、粉紅的金花鱸游曳而過， | A flash of golden perch, tinged with soft green, lav | `04005002` | `04005001` | ❌ |
| 239 | 熱 | 他也是較常跳流行熱舞， | He also often performs popular hot dances. | `05228710` | `05228715` | ❌ |
| 240 | 條 | 斷肢逃生的情形很像一個人被巨石壓住一條腿， | A case of escaping with a severed limb is much like  | `06585903` | `06585910` | ❌ |
| 241 | 抽 | 爸爸想再抽一次， | Dad wants to smoke again. | `06598613` | `06598603` | ❌ |
| 242 | 死 | 只要文化不死我在美國柏克萊一住就是十五年。 | I've been living in Berkeley, USA for fifteen years, | `05035203` | `05035209` | ❌ |
| 243 | 行 | 聽取奎爾簡報他此行經過及與沙烏地阿拉伯國王法德和科威 | I listened to Kuier's briefing on his trip and the t | `06775704` | `06775704` | ✅ |
| 244 | 間 | 但至今年三月間， | But as of this past March, | `04084105` | `04084103` | ❌ |
| 245 | 分 | 自家門口遭到三名蒙面歹徒分執鋁製球棒毆傷， | Three people in masks attacked me at my doorstep wit | `NONE` | `04146408` | — |
| 246 | 大 | 又在１９０６年建了更大的ＬａｎｇｄｅｌｌＨａｌｌ， | In 1906, an even larger Langdell Hall was built. | `05227201` | `05227202` | ❌ |
| 247 | 下 | 下表中列示ＧＡＴＥ現有實用軟體的名稱及其功能， | The table below lists the names and functions of the | `04081815` | `04081803` | ❌ |
| 248 | 做 | 哥哥做蘇武牧羊、天女散花。 | Brother did "Su Wu Tending Sheep" and "Fairy Scatter | `06664307` | `06664308` | ❌ |
| 249 | 度 | 自從釋迦牟尼佛轉法輪度眾生， | Since the Buddha began turning the Dharma wheel to d | `06785402` | `06785404` | ❌ |
| 250 | 拿 | 只開放特定場地供學生拿號碼牌寄物。 | Only specific areas are open for students to take nu | `04011201` | `04011202` | ❌ |
| 251 | 上 | 在歷史上曾經被滅亡過好幾次， | It has been conquered and destroyed multiple times t | `04081315` | `04081317` | ❌ |
| 252 | 抽 | 在大型的教學醫院皆有辦法抽血檢查。 | Large teaching hospitals are all capable of drawing  | `06598612` | `06598611` | ❌ |
| 253 | 還 | 我還以為他們會為身體的殘障痛苦呢！ | I thought they would suffer from physical disabiliti | `05002704` | `05002707` | ❌ |
| 254 | 行 | 美國之行並非尋夢、也非淘金， | The trip to the United States was neither a quest fo | `06775704` | `06775704` | ✅ |
| 255 | 就 | 就是所謂修行的智慧。 | The so-called wisdom of spiritual cultivation. | `05198313` | `05198313` | ✅ |
| 256 | 條 | 一開始就把這條小河川整理一下， | Start by tidying up this small river. | `06585906` | `06585906` | ✅ |
| 257 | 層 | 小敏住在二層。 | Xiao Min lives on the second floor. | `03005001` | `03005001` | ✅ |
| 258 | 去 | 就得去哪。 | Wherever you need to go. | `06559201` | `06559201` | ✅ |
| 259 | 做 | 堂姊就做了一個洋娃娃給我。 | My cousin made a doll for me. | `06664301` | `06664301` | ✅ |
| 260 | 季 | 所以這兩隊的競爭從這一季的第一場球就開始了， | So the rivalry between these two teams began with th | `07026504` | `07026504` | ✅ |
| 261 | 去 | 去幾天﹖ | How many days ago? | `06559218` | `06559201` | ❌ |
| 262 | 平 | 車子的把手為平把， | The car has flat handlebars. | `06025201` | `06025213` | ❌ |
| 263 | 吃 | 他們不像某些臺灣移民過的是「吃老本」的日子， | They don't live off their past like some Taiwanese i | `05227009` | `05227012` | ❌ |
| 264 | 代 | 這些是發生在這一代華人身上比較新的事情。 | These are relatively new events that have happened t | `04016205` | `04016206` | ❌ |
| 265 | 度 | 毛高文也常以他高八度的音調嚷嚷兩人歌路不同， | May also shout about their different musical paths i | `05147605` | `05147619` | ❌ |
| 266 | 去 | 她去過多少美國市場， | How many U.S. markets has she visited? | `06559201` | `06559201` | ✅ |
| 267 | 叫 | 你學個貓叫， | Meow! | `04010202` | `04010202` | ✅ |
| 268 | 道 | 相信透過教育這最後一道丹藥可以拯救！ | I believe that through education, this final elixir  | `04083505` | `04083512` | ❌ |
| 269 | 發 | 並於台北地區騎乘使用滿一年者（以電動機車行車執照之原 | Riders in the Taipei area who have used an electric  | `06724102` | `06724102` | ✅ |
| 270 | 行 | 西方國家行之已久的社會安全措施， | Western countries have long implemented social secur | `06775707` | `06775707` | ✅ |
| 271 | 投 | 他投７局、送出８次三振， | He pitched seven innings and struck out eight batter | `06685703` | `06685703` | ✅ |
| 272 | 大 | 好大的一個螺殼！ | What a huge shell! | `05227201` | `05227201` | ✅ |
| 273 | 回 | 有一回他受命去孟家宅院取兩支手槍， | One time, he was ordered to go to the Meng family co | `03019001` | `03019008` | ❌ |
| 274 | 就 | 要不然就是陰天。 | Otherwise, it will be overcast. | `05198301` | `05198307` | ❌ |
| 275 | 高 | 照說素質都很高， | The quality is supposed to be very high. | `06010615` | `06010615` | ✅ |
| 276 | 做 | 剝取牠們的毛皮做標本， | Extract their fur to make specimens. | `06664301` | `06664301` | ✅ |
| 277 | 深 | 自己深知道頭銜無用， | I know full well that titles are useless. | `06663313` | `06663313` | ✅ |
| 278 | 就 | 小美聽見這個話就下去了。 | Xiao Mei heard this and then went downstairs. | `05198303` | `05198303` | ✅ |
| 279 | 就 | 就是彼此的特性。 | It is about each other's characteristics. | `NONE` | `05198313` | — |
| 280 | 點 | 就這點來說， | In this regard, | `NONE` | `04043812` | — |
| 281 | 中 | 亦正發展中， | It is also developing in a positive direction. | `04004618` | `04004618` | ✅ |
| 282 | 帶 | 幾乎帶一點哽咽， | Almost choked up a little. | `06791413` | `06791420` | ❌ |
| 283 | 去 | 起身要去。 | I'm about to leave. | `06559201` | `06559201` | ✅ |
| 284 | 中 | 這種哲學和傅蘭尼、孔恩等嘗試在科學的知識如何獲得的過 | This type of philosophy, like that of Foucault and K | `04004605` | `04004618` | ❌ |
| 285 | 去 | 後來就坐飛機到東京去了。 | Later, I took a plane to Tokyo. | `06559201` | `06559204` | ❌ |
| 286 | 拉 | 你是說你們那時候連手都沒有拉！ | You said you didn't even hold hands back then! | `05230802` | `05230802` | ✅ |
| 287 | 當 | 而在將高山當郊山玩的途中， | And along the way, while treating towering mountains | `04013907` | `04013901` | ❌ |
| 288 | 支 | 為這支陌生且新鮮的球隊加油， | Cheer for this unfamiliar yet fresh team! | `03056204` | `03056204` | ✅ |
| 289 | 帶 | 所以視障生必須要仰賴別人帶他過馬路。 | Therefore, visually impaired students must rely on o | `06791407` | `06791413` | ❌ |
| 290 | 畫 | 例如在畫建築時， | For example, when drawing buildings, | `06550303` | `06550301` | ❌ |
| 291 | 去 | ∥我們到紐約去。 | We are going to New York. | `06559201` | `06559204` | ❌ |
| 292 | 中 | 最後在呂尚叡小姐（ＩＩＩ服務部人員）、童敏惠小姐（台 | Finally, Ms. Lü Shang-rui (staff member of the III S | `04004604` | `04004618` | ❌ |
| 293 | 代 | 由於本學期校方代學生聯合會向學生收取自治費， | The Student Union collected self-governance fees on  | `07104505` | `07104502` | ❌ |
| 294 | 空 | 誰好意思有一隻手是空的呢！ | Who would dare to have one hand empty? | `06517316` | `06517316` | ✅ |
| 295 | 度 | 因此面前的視野交集區只有十度。 | Therefore, the overlapping field of view in front of | `05147607` | `05147607` | ✅ |
| 296 | 發 | ∥我要靠意外之財我才能發啦我！ | I'm counting on a windfall to strike it rich! | `05193416` | `05193406` | ❌ |
| 297 | 破 | 也沒聽說過肚皮會破的。 | I've never heard of a belly bursting open either. | `06761402` | `06761404` | ❌ |
| 298 | 上 | 餐飲業上的自動點菜系統； | Automated ordering systems in the catering industry | `04081315` | `04081316` | ❌ |
| 299 | 上 | 在時間上適逢阿爾巴尼亞已故共黨首領霍查的遺孀妮克絲吉 | At the time, it coincided with Nexhmije Hoxha, the w | `04081315` | `04081317` | ❌ |
| 300 | 條 | 只求挽回一條垂危的生命， | I only seek to save a life hanging by a thread. | `06585924` | `06585911` | ❌ |
| 301 | 分 | 分不清是夢是真。 | I can't tell if it's a dream or reality. | `04146408` | `04146401` | ❌ |
| 302 | 破 | 大陸經過文化大革命及破四舊的浩劫， | The mainland experienced the catastrophe of the Cult | `06761405` | `06761415` | ❌ |
| 303 | 子 | 法華經長者窮子喻之中， | In the parable of the rich man and his poor son in t | `07027901` | `07027904` | ❌ |
| 304 | 條 | 那是一條繁華的商業街道。 | That is a bustling commercial street. | `06585906` | `06585906` | ✅ |
| 305 | 打 | 不是靠打殺就可以一手遮天的， | It's not something that can be swept under the rug j | `05229154` | `05229126` | ❌ |
| 306 | 用 | 依照戒急用忍檢討執行計畫， | In accordance with the "Review and Implementation Pl | `04017401` | `04017405` | ❌ |
| 307 | 中 | 祥雲的鼓樓中所感到的隆起是完全不同的， | The uplift felt in Xiangyun's Drum Tower is entirely | `04004603` | `04004603` | ✅ |
| 308 | 長 | 長鼻尖探入牛奶瓶。 | The trunk tip dips into the milk bottle. | `06030801` | `06030801` | ✅ |
| 309 | 代 | 身為台塑的第二代， | As the second generation of the Formosa Plastics Gro | `04016203` | `04016201` | ❌ |
| 310 | 面 | 她曾在82年奪得區運5面金牌後因傷退出體操界， | She once won five gold medals at the District Games  | `NONE` | `03028807` | — |
| 311 | 就 | 首先選擇茶葉就是一門學問。 | Choosing tea leaves is a subject of study in itself. | `05198301` | `05198313` | ❌ |
| 312 | 分 | 分由七十一至七十七會計年度逐年編列預算， | The budget shall be allocated annually from fiscal y | `04146406` | `04146408` | ❌ |
| 313 | 條 | 每次烤鴨都一條腿， | Every time I roast a duck, it's on one leg. | `06585908` | `06585910` | ❌ |
| 314 | 中 | 耳朵以下全埋在衣服中， | The entire area below the ears is buried in the clot | `04004603` | `04004603` | ✅ |
| 315 | 叫 | 當頑皮的鬧鐘叫了以後， | After the mischievous alarm clock rang, | `04010201` | `04010205` | ❌ |
| 316 | 點 | 就某一點而言， | In a certain sense, | `04043808` | `04043812` | ❌ |
| 317 | 打開 | 打開這個知識的寶庫。 | Open this treasure trove of knowledge. | `06548116` | `06548102` | ❌ |
| 318 | 行 | 李總統康乃爾之行， | President Tsai's visit to Cornell University | `06775704` | `06775704` | ✅ |
| 319 | 中 | 在車中， | In the car. | `04004603` | `04004603` | ✅ |
| 320 | 還 | 還在服役的吳昌達， | Wu Chang-ta is still on active duty. | `05002701` | `05002701` | ✅ |
| 321 | 打 | 有牌打就好， | As long as you have a license to play, that's all th | `05229179` | `05229133` | ❌ |
| 322 | 回 | 這回換野狼的屁股卡在洞口了， | This time, it's the wolf's butt that's stuck in the  | `03019007` | `03019008` | ❌ |
| 323 | 上 | 在個人資料和事件的處理上， | In the handling of personal data and incidents, | `04081315` | `04081317` | ❌ |
| 324 | 低 | 故包括大部份的自營商及散戶投資人普遍都有預期回檔後再 | Most self-employed traders and retail investors gene | `06748407` | `06748412` | ❌ |
| 325 | 行 | 所以要出門是必須繞過公園而行的。 | Therefore, you have to go around the park to get out | `06775702` | `06775701` | ❌ |
| 326 | 度 | 一百八十度不一樣。 | It's a hundred and eighty degrees different. | `05147607` | `05147607` | ✅ |
| 327 | 帶 | 帶著滿腹心得與球經比以前更成熟。 | I'm carrying a wealth of experience and insights, ma | `06791406` | `06791420` | ❌ |
| 328 | 用 | 是取之於消費者、用之於消費者。 | It is taken from consumers and used for consumers. | `04017401` | `04017401` | ✅ |
| 329 | 邊 | 調整的方法是手握雙筒鏡的兩邊， | Adjust the binoculars by holding both sides. | `06584404` | `06584406` | ❌ |
| 330 | 拍 | 「原來拍古裝戲這麼辛苦！ | "Turns out filming period dramas is so exhausting!" | `08028003` | `08028003` | ✅ |
| 331 | 打 | 可見學生不但喜歡打保齡球， | Students not only enjoy playing bowling. | `05229131` | `05229131` | ✅ |
| 332 | 正 | 後人乘涼正是本院圖書館自動化的最佳寫照， | Future generations benefit from the cool shade, whic | `07009822` | `07009822` | ✅ |
| 333 | 清 | 水乃天下至清之物， | Water is the purest substance in the world. | `06539501` | `06539501` | ✅ |
| 334 | 收 | 還捨不得收起來。 | I still can't bear to put it away. | `03039314` | `03039314` | ✅ |
| 335 | 場 | 除了在萬芳醫院的三場演出之外， | In addition to the three performances at Wanfang Hos | `06721701` | `06721707` | ❌ |
| 336 | 條 | 他的童年像一條浮根， | His childhood was like a floating root. | `NONE` | `06585903` | — |
| 337 | 下 | 在Ｃ目錄下打）ｐａｔｈ）。 | Create a path under the C drive. | `04081803` | `04081808` | ❌ |
| 338 | 新 | 馬英九重申暫緩設立新的公立高中， | Ma Ying-jeou reiterated the postponement of establis | `05237904` | `05237901` | ❌ |
| 339 | 拍 | 這部片子裡的留鳥還滿容易拍的， | The birds in this film are quite easy to photograph. | `08028003` | `08028003` | ✅ |
| 340 | 高 | 也較查詢系統為高； | The query system is also more advanced. | `06010615` | `06010615` | ✅ |
| 341 | 大 | 那條大蛇卻朝他點了點頭， | That giant serpent nodded at him. | `05227201` | `05227201` | ✅ |
| 342 | 就 | 昏沉就是愛睡， | Drowsiness is just loving to sleep. | `05198313` | `05198313` | ✅ |
| 343 | 人 | 高階積體電路設計公司至少雇用十人以上， | A high-end integrated circuit design company must em | `05231102` | `05231109` | ❌ |
| 344 | 去 | 煩請猛師兄與無蹤師父以及貴寺四大弟子去那邊坐鎮， | Please dispatch Master Meng, Master Wu, and the four | `06559201` | `06559201` | ✅ |
| 345 | 中 | 在這次選戰中佔了有利地位。 | They gained an advantageous position in this electio | `04004618` | `04004618` | ✅ |
| 346 | 去 | 我們能去嗎？ | Can we go? | `06559201` | `06559201` | ✅ |
| 347 | 錢 | 而讀書人則是最沒有錢的。 | The scholar is often the poorest. | `06015107` | `06015107` | ✅ |
| 348 | 熱 | 無形的過熱， | Invisible overheating. | `05228701` | `05228707` | ❌ |
| 349 | 說 | 可說毫不遜色。 | It can be said to be no less impressive. | `05212407` | `05212406` | ❌ |
| 350 | 起 | 其中七名船員劉憲助（上圖右起）。 | Among them, seven crew members, including Liu Xianzu | `04004803` | `04004803` | ✅ |
| 351 | 打 | 謝玄只用了五千人就把秦兵打得大敗， | Only five thousand of Xie Xuan's troops routed the Q | `05229126` | `05229126` | ✅ |
| 352 | 條 | 可是他那兩條硬得像木棍的腿， | But those two legs of his were as stiff as wooden st | `06585910` | `06585910` | ✅ |
| 353 | 新 | 然後沖進新燒滾水， | Then rush into freshly boiled water. | `05237901` | `05237905` | ❌ |
| 354 | 度 | 那麼如何因應不同需求或在家庭結構變化時必須採行的「二 | Therefore, the "second-time redesign" required to ac | `05147605` | `05147617` | ❌ |
| 355 | 度 | 而南極的最低氣溫紀錄則有攝氏零下８８度。 | The lowest temperature record in Antarctica is minus | `05147610` | `05147610` | ✅ |
| 356 | 上 | 準備幾個乾淨的塑膠容器放在轉盤上， | Prepare a few clean plastic containers and place the | `04081301` | `04081301` | ✅ |
| 357 | 熱 | 如此對於賽程的控制和比賽氣氛熱都很有幫助， | This helps a lot in controlling the schedule and hea | `05228723` | `05228723` | ✅ |
| 358 | 下 | 並在其下成立系統規格制訂和系統測試小組。 | And establish system specification formulation and s | `04081808` | `04081808` | ✅ |
| 359 | 行 | 一定偕母同行， | I will definitely go with my mother. | `06775704` | `06775704` | ✅ |
| 360 | 轉 | 他三個手指悠然轉著那只淡青色玉鐲。 | He leisurely twirled the light blue jade bracelet wi | `05228801` | `05228802` | ❌ |
| 361 | 活 | 活的天然檜木林已全面禁採， | The living natural cypress forest has been completel | `06725001` | `06725001` | ✅ |
| 362 | 明 | 法燈滅又明。 | The light goes out and then shines again. | `06685403` | `06685403` | ✅ |
| 363 | 片 | 他家後院就是一片竹林， | His backyard is a bamboo grove. | `05195912` | `05195912` | ✅ |
| 364 | 帶 | 「每個眾生都帶著自己的業而來， | Every being comes with their own karma. | `06791418` | `06791418` | ✅ |
| 365 | 就 | 心浮動就是道心不堅固， | A floating mind is an unsteady Dao mind. | `05198301` | `05198313` | ❌ |
| 366 | 上 | 也把墳地上那些白花和紅花稱為杜鵑花。 | Also refer to those white and red flowers on the gra | `04081315` | `04081301` | ❌ |
| 367 | 重 | 拿起大包小包的行李也就不覺得重了。 | Picking up all the big and small pieces of luggage d | `05207602` | `05207602` | ✅ |
| 368 | 大 | 大蛇竟然把嘴張開， | The serpent actually opened its mouth wide. | `NONE` | `05227201` | — |
| 369 | 拿 | 偶爾有幾個好心人拿東西給我吃， | Occasionally, a few kind people bring me something t | `04011205` | `04011205` | ✅ |
| 370 | 分 | 數十年不分寒暑， | For decades, regardless of the heat or cold, | `04146408` | `04146405` | ❌ |
| 371 | 發 | 是很願意國內所有發卡機構能研擬出一套辦法來針對如果受 | I sincerely hope that all domestic card-issuing inst | `06724101` | `06724102` | ❌ |
| 372 | 明 | 而教練費區和球員之間不和的事實也由暗而明， | The rift between the coaching staff and players has  | `06685411` | `06685407` | ❌ |
| 373 | 拿 | 有些人因「太紅」怕整個晚上因不停拿宵夜而無法念書， | Some people are so busy taking late-night snacks tha | `04011201` | `04011202` | ❌ |
| 374 | 面 | 面無表情地望著大家， | He stared at everyone with a blank expression. | `03028801` | `03028801` | ✅ |
| 375 | 真 | 真希望可以永遠住在那裡。 | I truly wish I could live there forever. | `05100406` | `05100414` | ❌ |
| 376 | 上 | 一切都只停留在勞作的程度上。 | Everything remains at the level of mere labor. | `04081315` | `04081317` | ❌ |
| 377 | 熱 | 此外響韻、寶麗金也在一波波文藝復興熱， | In addition, Iris and PolyGram are also experiencing | `05228709` | `05228709` | ✅ |
| 378 | 要 | 要完成還早得很呢！ | It's going to take a long time to finish! | `06636901` | `06636907` | ❌ |
| 379 | 條 | 美國的Ｆ１１１戰鬥轟炸機，廿六日晚精確炸毀科威特境內 | On the evening of the 26th, the U.S. F-111 fighter-b | `06585903` | `06585903` | ✅ |
| 380 | 發 | 因此也在同時明令停止所有稻田轉用的審核與發照。 | Therefore, it also simultaneously issued a formal or | `06724112` | `06724102` | ❌ |
| 381 | 行 | 唱片公司特別為曾慶瑜安排了一趟美國之行， | The record company specially arranged a trip to the  | `06775704` | `06775704` | ✅ |
| 382 | 做 | 做個術德兼修、品學兼優的好學生， | Be a good student who excels in both moral character | `06664308` | `06664308` | ✅ |
| 383 | 片 | 他站在一片書牆前， | He stood in front of a wall of books. | `05195903` | `05195915` | ❌ |
| 384 | 行 | （３）電池組每隔適當時期應行均衡充電一次。 | The battery pack should be given an equalizing charg | `06775706` | `06775706` | ✅ |
| 385 | 用 | 吃穿用玩樣樣俱全， | Everything is available for eating, dressing, using, | `04017401` | `04017411` | ❌ |
| 386 | 正 | 其謬誤正如同我們總習於率爾用一個人比擬另一個人。 | Just as we often hastily compare one person to anoth | `07009822` | `07009822` | ✅ |
| 387 | 前 | 廿五日清晨在林口鄉中山路五十四號前發現曾忠義座車， | In the early morning of the 25th, a car belonging to | `03033701` | `03033701` | ✅ |
| 388 | 大 | 由於批購總額大， | The total procurement amount is large. | `05227203` | `05227203` | ✅ |
| 389 | 就 | 夜市裡最吸引人的地方就是商品的價錢比一般商店或百貨公 | The most attractive thing about night markets is tha | `05198301` | `05198313` | ❌ |
| 390 | 條 | 或者手拉手走一條霪雨霏霏的街。 | Or hand in hand, we walk down a rain-soaked street. | `06585906` | `06585906` | ✅ |
| 391 | 破 | 再破三案。 | Three more cases have been cracked. | `06761412` | `06761412` | ✅ |
| 392 | 掛 | 男孩要求掛急診。 | The boy requested emergency treatment. | `06701415` | `06701415` | ✅ |
| 393 | 來 | 國外學生來台主要集中在台灣師大學中文， | The main concentration of international students com | `04086501` | `04086501` | ✅ |
| 394 | 空 | ２．胃酸排空時間檢查。 | Gastric emptying time examination. | `06517306` | `06517312` | ❌ |
| 395 | 帶 | 集合是以不帶正負號的整數構成陣列型式， | A set is an array of non-negative integers. | `06791413` | `06791418` | ❌ |
| 396 | 熱 | 這不過是近年來臺灣明式家具熱的兩個浪頭。 | These are just two waves of the recent surge in inte | `05228709` | `05228709` | ✅ |
| 397 | 粗 | 還有幾支粗簽字筆， | There are still a few thick felt-tip pens. | `06711801` | `06711803` | ❌ |
| 398 | 條 | 教育部在九月初以不符合師資培育法第七條及師範教育精神 | The Ministry of Education ruled in early September t | `06585929` | `06585929` | ✅ |
| 399 | 邊 | 現在井邊圍上了欄杆， | A railing has been installed around the well. | `06584404` | `06584405` | ❌ |
| 400 | 分 | 向行政院院長連戰提出的第一分報告書中， | The first interim report submitted to Premier Vincen | `04108107` | `04108107` | ✅ |

### 錯誤與 NONE 的細節

**1. 包**　`wsd-包-3321`　[dominant]
- 原句：以一包Ａ４大小、內含20張的相片紙建議售價為從240元降為190元，
- 譯文：A pack of A4-sized photo paper containing 20 sheets is suggested to have its price reduced from NT$240 to NT$190.
- judge 選：`05095701` 折疊紙、布或其他薄片狀物以覆蓋物體所有的面。　信心 0.90　依據：A pack of 紙張被外皮包覆
- gold：`05095711` 計算成包物品的單位。

**3. 帶**　`wsd-帶-b6cb`　[dominant]
- 原句：就能帶個女孩回來。
- 譯文：You could even bring a girl back.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：整句在說讓女孩跟著自己移動
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**4. 死**　`wsd-死-ab87`　[dominant]
- 原句：可能這是你對我抱的至死不變的看法，
- 譯文：Perhaps this is the unchanging view you hold of me.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句無關生命或終止語義
- gold：`05035202` 形容生物失去生命。

**5. 熱**　`wsd-熱-842c`　[dominant]
- 原句：疑似運作過熱起火燃燒，
- 譯文：It appears to have overheated during operation and caught fire.
- judge 選：`05228702` 形容溫度升高或感覺溫度升高的。　信心 0.95　依據：整句在說溫度升高至起火
- gold：`05228701` 形容溫度高或感覺溫度高的。

**8. 叫**　`wsd-叫-7a40`　[dominant]
- 原句：鍾木郎叫人看守人質，
- 譯文：Keep watch over the hostage.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句無指示或導致語義
- gold：`05013801` 指示後述對象做事。

**10. 拍**　`wsd-拍-8759`　[dominant]
- 原句：希望能多拍些劇情片。
- 譯文：I hope we can make more narrative films.
- judge 選：`08028003` 用攝影器材紀錄動態影像。　信心 0.95　依據：整句在說製作敘事影片，強調動態影像紀錄
- gold：`08028004` 參與拍攝電影與製作。

**11. 中**　`wsd-中-797e`　[dominant]
- 原句：讀者可由表中清楚看出，
- 譯文：Readers can clearly see from the table.
- judge 選：`04004603` 在前述對象所包含的空間範圍。　信心 0.90　依據：從表格的空間範圍內可見
- gold：`04004605` 在前述的機構或領域範圍。

**15. 包**　`wsd-包-07f6`　[dominant]
- 原句：但依慣例只拿了幾包藥後回家養病。
- 譯文：But as usual, he only took a few packs of medicine and went home to recuperate.
- judge 選：`05095701` 折疊紙、布或其他薄片狀物以覆蓋物體所有的面。　信心 0.90　依據：整句在說用外皮包覆藥品
- gold：`05095711` 計算成包物品的單位。

**19. 去**　`wsd-去-9cd9`　[dominant]
- 原句：本來要下樓去買幾包速食麵，
- 譯文：I was about to go downstairs to buy a few packs of instant noodles.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說前往樓下購物
- gold：`06559205` 表前述對象進行後述事件。

**21. 掛**　`wsd-掛-3cf0`　[dominant]
- 原句：比如今八三歲父親至今還掛在牆上親自題著「音容宛在」的少婦像，
- 譯文：A portrait of a young woman with the inscription "音容宛在" still hangs on the wall, painted by my 83-year-old father.
- judge 選：`06701402` 特定物體的一端被支撐而維持在特定高度。　信心 0.95　依據：整句在說畫像被懸掛於牆上
- gold：`06701401` 支撐特定物體的一端使其維持在特定高度。

**23. 下**　`wsd-下-0a1f`　[dominant]
- 原句：在共黨獨裁政權下產生的文學作品，
- 譯文：Literary works produced under a communist dictatorship
- judge 選：`04081808` 比喻階級架構中低於前述階級的階級。　信心 0.90　依據：譯文指稱共產黨專政體制下的文學作品
- gold：`04081817` 表處在前述事件的情況或條件中。

**24. 心**　`wsd-心-ce2d`　[dominant]
- 原句：心中非常不甘願，
- 譯文：I am very reluctant.
- judge 選：`05231608` 想做特定事件的念頭。　信心 0.95　依據：整句在說猶豫不決的念頭
- gold：`05231612` 人的感情或思想。

**27. 去**　`wsd-去-9e53`　[dominant]
- 原句：你先去預備圖章，
- 譯文：Please go prepare the seal first.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說前往特定地點準備印章
- gold：`06559205` 表前述對象進行後述事件。

**31. 低**　`wsd-低-a891`　[dominant]
- 原句：創下八十六年以來同季首度滑落千億元以下的最低紀錄。
- 譯文：It marked the lowest record in over 86 years to fall below NT$100 billion for the same quarter.
- judge 選：`06748407` 形容數值變小。　信心 0.95　依據：譯文強調數值降至歷史新低
- gold：`06748406` 形容數值小於比較對象的。

**36. 邊**　`wsd-邊-d206`　[dominant]
- 原句：眼見一群男孩子就守在河邊，
- 譯文：A group of boys was seen standing by the river.
- judge 選：`06584405` 表靠近參考點的地方。　信心 0.95　依據：整句在說位置鄰近河流
- gold：`06584404` 特定對象與其他鄰界對象交界的地方。

**37. 明**　`wsd-明-3724`　[dominant]
- 原句：第四繼承時期是五代至明末。
- 譯文：The fourth inheritance period spans from the Five Dynasties to the end of the Ming Dynasty.
- judge 選：`07003502` 明朝的國號或政權。　信心 0.95　依據：整句在說明朝政權的時間跨度
- gold：`07003501` 中國朝代名，西元1368至1644年，由朱元璋所建立。

**38. 層**　`wsd-層-fa2c`　[dominant]
- 原句：表演者自十層樓一躍而下，
- 譯文：The performer leapt to his death from the tenth floor.
- judge 選：`03005001` 兩層以上的房屋其中的一層。　信心 0.95　依據：整句在說從第十層樓跳下
- gold：`03005002` 計算房屋樓面的單位。

**41. 歲**　`wsd-歲-5ae2`　[dominant]
- 原句：今年整整滿一百歲了。
- 譯文：This year marks exactly one hundred years.
- judge 選：`06559403` 計算時間的單位，一歲有十二個月。　信心 0.95　依據：整句強調時間長度的一百年
- gold：`06559405` 計算年齡的單位。

**44. 去**　`wsd-去-6d5f`　[dominant]
- 原句：以及親手去使用這些資料。
- 譯文：And personally use this data.
- judge 選：`06559208` 表藉由前述工具、方法或範圍進行後述事件。　信心 0.95　依據：整句在說以此資料為工具或方法
- gold：`06559205` 表前述對象進行後述事件。

**46. 上**　`wsd-上-e882`　[dominant]
- 原句：多媒體在網路上的應用確實擁有無限發展潛力，
- 譯文：Multimedia applications on the internet indeed have unlimited potential for development.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：「上」在此表示「網際網路」為主題範圍
- gold：`04081314` 事件的發生在前述事物的範圍內。

**47. 場**　`wsd-場-50f3`　[dominant]
- 原句：國王明星大前鋒韋伯則攻下全隊最高的21分以及本季個人單場最多之12個籃板球。
- 譯文：King star power forward Webber scored a team-high 21 points and a season-high 12 rebounds.
- judge 選：`06721705` 特定表演或比賽的段落。　信心 0.90　依據：譯文提到球員得分與籃板，屬比賽段落
- gold：`06721709` 計算經過安排的活動的單位。

**53. 拉**　`wsd-拉-72ff`　[dominant]
- 原句：是將台灣拉向一個被強勢文化（好萊塢）同質化的下場，
- 譯文：It would lead Taiwan down the path of homogenization under the dominance of a strong culture (Hollywood).
- judge 選：`05230804` 比喻將後述對象引到自己這邊來。　信心 0.90　依據：lead 表引導他人走向某路徑，符合比喻引導語義
- gold：`05230801` 向主事者身體的方向施力而使後述對象順著施力方向移動。

**54. 中**　`wsd-中-5c4c`　[dominant]
- 原句：但是這並不代表婦女在家中的責任減輕了。
- 譯文：But this does not mean that women's responsibilities at home have lessened.
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：整句強調職責在時間上的持續
- gold：`04004605` 在前述的機構或領域範圍。

**60. 去**　`wsd-去-a508`　[dominant]
- 原句：準備挑到城裡去賣。
- 譯文：I'm going to take them to the city to sell.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說帶領他們前往城市
- gold：`06559205` 表前述對象進行後述事件。

**61. 新**　`wsd-新-d569`　[dominant]
- 原句：與近千位新舊政府團隊和工商界的共同見證下，
- 譯文：Under the joint witness of nearly a thousand members from the old and new government teams and the business community,
- judge 選：`05237901` 形容特定對象剛產生不久。　信心 0.90　依據：新政府團隊剛成立不久的語義
- gold：`05237904` 形容和原來不一樣的。

**65. 言**　`wsd-言-3d36`　[dominant]
- 原句：就前者而言，
- 譯文：In this regard,
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文為片語，未傳達「言」的任何語義
- gold：`06008204` 評價後述對象。

**67. 帶**　`wsd-帶-de6d`　[dominant]
- 原句：事後我帶他回南部老家見父母，
- 譯文：Afterward, I took him back to my hometown in southern Taiwan to meet my parents.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：整句在說「我」讓「他」跟著移動
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**68. 抽**　`wsd-抽-8360`　[dominant]
- 原句：又抽大麻睡著了，
- 譯文：I smoked weed again and fell asleep.
- judge 選：`06598613` 動物用口或鼻攝取後述氣體。　信心 0.95　依據：整句在說吸入大麻煙氣後睡著
- gold：`06598614` 使用口攝入會令人上癮的物品。

**70. 股**　`wsd-股-32a8`　[dominant]
- 原句：首季每股稅後盈餘約○．八元。
- 譯文：The after-tax earnings per share for the first quarter were approximately NT$0.8.
- judge 選：`03015702` 上櫃或上市公司用來表示其公司股份的證券。　信心 0.95　依據：譯文提及「每股稅後盈餘」直接對應股票證券
- gold：`03015710` 計算股份的單位。

**72. 來**　`wsd-來-cead`　[dominant]
- 原句：但嚴格來說銀行業的壞帳比票券業更難計算，
- 譯文：But strictly speaking, bad debts in the banking industry are harder to calculate than in the securities industry.
- judge 選：`04086501` 向參考點的位置移動或到達參考點的位置。　信心 0.90　依據：整句在說壞帳計算難度的比較，來表移動到計算的狀態
- gold：`04086509` 表藉由前述工具、方法或範圍進行後述事件。

**73. 明**　`wsd-明-9c84`　[dominant]
- 原句：就好像在濃霧中遇到一盞明燈一樣。
- 譯文：It was like encountering a bright beacon in the thick fog.
- judge 選：`06685411` 形容比喻狀況變得明顯清楚。　信心 0.95　依據：整句以光源比喻狀況變得明顯清楚
- gold：`06685401` 形容光源的光線充足。

**75. 強**　`wsd-強-95c5`　[dominant]
- 原句：當海水清澈、陽光穿透力強的時候，
- 譯文：When the sea is clear and sunlight penetrates deeply.
- judge 選：`09250308` 形容光線的強度大。　信心 0.95　依據：整句在說陽光穿透的強度高
- gold：`09250303` 形容能力或發展狀況好的。

**76. 吃**　`wsd-吃-1fc3`　[dominant]
- 原句：有純樸簡單碼頭、熱鬧大船小舟、傳統市集、酒吧各式吃喝餐廳，
- 譯文：There are simple and rustic docks, bustling large and small boats, traditional markets, and various bars and restaurants for eating and drinking.
- judge 選：`05227024` 經歷後述包括飲食的社交聚會。　信心 0.90　依據：整句在說飲食相關的社交活動
- gold：`05227001` 使物體經過口中吞入體內。

**79. 上**　`wsd-上-e2ba`　[dominant]
- 原句：就把媽祖在海上顯靈的事蹟，
- 譯文：Mazu's miraculous manifestations at sea
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：at sea 表示以海域為主題範圍
- gold：`04081314` 事件的發生在前述事物的範圍內。

**80. 叫**　`wsd-叫-2b66`　[dominant]
- 原句：出現一個叫永窮的窮小子，
- 譯文：A poor young man named Yongqiong appeared.
- judge 選：`04010207` 根據前述定義給予後述對象名稱。　信心 0.95　依據：整句在說命名為「永瓊」
- gold：`04010206` 叫特定對象的名字是後述對象。

**82. 股**　`wsd-股-47e8`　[dominant]
- 原句：中華電週二公布今年每股純益目標為四．一六元，
- 譯文：Taiwan Mobile announced on Tuesday that its target for earnings per share this year is NT$4.16.
- judge 選：`03015702` 上櫃或上市公司用來表示其公司股份的證券。　信心 0.95　依據：譯文提及公司股份證券的目標價
- gold：`03015710` 計算股份的單位。

**83. 間**　`wsd-間-41a8`　[dominant]
- 原句：省能產品也成為未來國際間的最大商機，
- 譯文：Energy-efficient products are also becoming the biggest business opportunity in the international market in the future.
- judge 選：`04084102` 引介事情或狀態發生的範圍。　信心 0.90　依據：「在國際市場」引介未來商機的範圍
- gold：`04084104` 引介事件與事件的關係。

**86. 中**　`wsd-中-937d`　[dominant]
- 原句：中菲國會議員友好協會會長。
- 譯文：Chairman of the China-Philippines Parliamentary Friendship Association.
- judge 選：`08011201` 國名，位於亞洲東部的國家，東瀕太平洋，北臨俄國，是世界上人口最多的國家。　信心 0.95　依據：譯文中的國家指稱對應中華人民共和國
- gold：`08011203` 位於臺灣島的國家，建立於西元1912年的民主共和國，轄區包含臺灣、澎湖、金門、馬祖。

**87. 做**　`wsd-做-b317`　[dominant]
- 原句：為什麼日本人要這麼做？
- 譯文：Why do the Japanese do this?
- judge 選：`06664308` 前述對象的工作或身份是後述對象。　信心 0.95　依據：整句在詢問日本人從事的職業或角色
- gold：`06664306` 做，取代整個事件。

**88. 去**　`wsd-去-0a4c`　[dominant]
- 原句：並非去抗議。
- 譯文：It's not about going to protest.
- judge 選：`06559201` 向特定地點移動。　信心 0.90　依據：整句在說前往特定地點（抗議）
- gold：`06559205` 表前述對象進行後述事件。

**89. 去**　`wsd-去-1625`　[dominant]
- 原句：試著去接近森林，
- 譯文：Try to approach the forest.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說朝向森林移動
- gold：`06559205` 表前述對象進行後述事件。

**92. 拍**　`wsd-拍-241f`　[dominant]
- 原句：一走紅大家都搶著找她拍，
- 譯文：Once she became popular, everyone scrambled to collaborate with her on photo shoots.
- judge 選：`08028001` 用攝影器材拍照片。　信心 0.95　依據：整句在說拍攝照片的合作行為
- gold：`08028004` 參與拍攝電影與製作。

**93. 度**　`wsd-度-334e`　[dominant]
- 原句：在澳洲風景明媚的海灘度了兩天假之後，
- 譯文：After spending two days of vacation on Australia's scenic beaches
- judge 選：`06785401` 從特定地理範圍的一邊到另一邊，通常為水體。　信心 0.90　依據：假期在海灘上度過，語義為跨越地理範圍
- gold：`06785402` 經過特定時段。

**95. 真**　`wsd-真-a3cf`　[dominant]
- 原句：真是惡名昭彰的傢伙。
- 譯文：What a notoriously infamous guy.
- judge 選：`05100414` 表說話者主觀評價程度高，帶有誇張語氣或情感。　信心 0.90　依據：notoriously infamous 強調主觀評價且帶有誇張語氣
- gold：`05100413` 表對客觀情況的真實性給予評價。

**96. 新**　`wsd-新-c4ba`　[dominant]
- 原句：並同時實施新的審查制度；
- 譯文：At the same time, a new censorship system was implemented.
- judge 選：`05237901` 形容特定對象剛產生不久。　信心 0.95　依據：整句強調系統剛被實施，表新生成不久
- gold：`05237904` 形容和原來不一樣的。

**97. 包**　`wsd-包-32b3`　[dominant]
- 原句：臨走時帶包來自天津１８街桂發祥的麻花，
- 譯文：I'll bring some twisted crullers from Tianjin's 18th Street Gui Faxiang when I leave.
- judge 選：`05095702` 以外皮包住內餡，製成後述食物。　信心 0.95　依據：整句在說用外皮包裹內餡的食物
- gold：`05095711` 計算成包物品的單位。

**98. 去**　`wsd-去-fada`　[dominant]
- 原句：去住旅館好了！
- 譯文：Let's just stay at a hotel!
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說前往特定地點（飯店）
- gold：`06559205` 表前述對象進行後述事件。

**99. 約**　`wsd-約-c8c8`　[dominant]
- 原句：約她一起去附近的商店買下星期的吃食。
- 譯文：Invite her to go to a nearby store to buy food for next week.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句在說邀請做某事而非共同約定
- gold：`05052303` 請特定對象在事先共同決定的時間或地點見面。

**102. 小**　`wsd-小-8d9a`　[dominant]
- 原句：以小動物來作試驗，
- 譯文：Animal testing is conducted.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句無關體積、年紀、數量或地位比較
- gold：`05227101` 形容體積少於比較對象的。

**105. 帶**　`wsd-帶-dc7d`　[dominant]
- 原句：或帶小孩郊遊。
- 譯文：Go for an outing with children.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：整句在說成人帶領兒童外出
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**106. 部**　`wsd-部-7f83`　[dominant]
- 原句：那是漫長的一部曲折而辛酸的歷史。
- 譯文：That was a long, convoluted, and bitter history.
- judge 選：`05075701` 整體中可區分的組成單位。　信心 0.90　依據：整句在說歷史的組成部分
- gold：`05075710` 計算編寫而成的作品的單位，包括書籍、戲劇、音樂等。

**107. 高**　`wsd-高-1f42`　[dominant]
- 原句：台大最高，
- 譯文：National Taiwan University is the best.
- judge 選：`06010615` 形容程度或標準高於比較對象。　信心 0.95　依據：整句強調優越程度而非實際高度
- gold：`06010610` 形容數值大於比較對象。

**108. 上**　`wsd-上-10d2`　[dominant]
- 原句：街頭上到處也可以看到咖啡店．
- 譯文：You can see coffee shops everywhere on the streets.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：整句強調「街道」作為可見範圍的主題
- gold：`04081314` 事件的發生在前述事物的範圍內。

**110. 起**　`wsd-起-b672`　[dominant]
- 原句：報名自即日起受理，
- 譯文：Registration is now open.
- judge 選：`04004828` 開始或產生。　信心 0.95　依據：註冊程序開始啟動
- gold：`04004801` 表示事件時間範圍的開始參考點。

**111. 中**　`wsd-中-d396`　[dominant]
- 原句：恍恍惚惚腦中忽然瞥過過去她那激憤壯烈的夢。
- 譯文：A fleeting image of her passionate and heroic dream suddenly flashed through my hazy mind.
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：整句強調夢想在腦海中閃現的時間點
- gold：`04004605` 在前述的機構或領域範圍。

**113. 大**　`wsd-大-224c`　[dominant]
- 原句：小問題大煩惱資料漏失時的處理．何鴻毅問：
- 譯文：When minor issues cause major troubles: Handling data loss. What does Ho Hung-yi ask?
- judge 選：`05227205` 形容在相關對象中最重要的。　信心 0.90　依據：整句在說重要議題（Ho Hung-yi的詢問）
- gold：`05227204` 形容程度超過比較對象的。

**115. 做**　`wsd-做-8944`　[dominant]
- 原句：他也把我們的垃圾做分類，
- 譯文：He also sorts our trash for recycling.
- judge 選：`06664307` 進行特定正式活動。　信心 0.90　依據：整句在說進行垃圾分類的正式活動
- gold：`06664306` 做，取代整個事件。

**119. 言**　`wsd-言-7e8e`　[dominant]
- 原句：而所謂的新指甲可能也是指在老指甲下方的油脂指床而言。
- 譯文：The so-called new nail may also refer to the fat nail bed beneath the old nail.
- judge 選：`06008211` 根據前述定義給予後述對象名稱。　信心 0.95　依據：so-called 表示根據定義命名
- gold：`06008204` 評價後述對象。

**120. 吃**　`wsd-吃-8bc8`　[dominant]
- 原句：年年拼死吃，
- 譯文：I fight to eat every year.
- judge 選：`05227009` 比喻經歷後述負面事件。　信心 0.95　依據：整句在說為生存奮鬥，採比喻用法
- gold：`05227001` 使物體經過口中吞入體內。

**123. 條**　`wsd-條-a722`　[dominant]
- 原句：便可堆出一條筆直的高級公路。
- 譯文：A straight, high-quality highway can be built this way.
- judge 選：`06585906` 計算地面上長條型的建築物或自然景觀的單位。　信心 0.95　依據：highway為長條型地面建築景觀
- gold：`06585924` 計算行進的路線的單位。

**126. 層**　`wsd-層-602f`　[dominant]
- 原句：地下三層）與緊鄰也將接著完工的資訊大樓，
- 譯文：The basement third floor and the adjacent Information Building will soon be completed.
- judge 選：`03005001` 兩層以上的房屋其中的一層。　信心 0.95　依據：樓層數在句中直接對應建物的樓層
- gold：`03005002` 計算房屋樓面的單位。

**128. 拿**　`wsd-拿-b7ca`　[dominant]
- 原句：我都拿體重計為小豬們檢查身體，
- 譯文：I always use the scale to check the health of the little pigs.
- judge 選：`04011209` 引介事件所憑藉的方法或工具。　信心 0.95　依據：整句強調用工具（秤）來達成檢查目的
- gold：`04011201` 用手取物或持物。

**131. 中**　`wsd-中-85bc`　[dominant]
- 原句：每家主婦都率領家中的婦女，
- 譯文：Every housewife leads the women in her household.
- judge 選：`04004603` 在前述對象所包含的空間範圍。　信心 0.95　依據：整句在說婦女在其家庭成員的空間範圍內
- gold：`04004605` 在前述的機構或領域範圍。

**132. 使**　`wsd-使-61bb`　[dominant]
- 原句：使我們變得很有禮貌。
- 譯文：Let us be very polite.
- judge 選：`06560201` 較有權力的人或機構要求他人去做後述事件。　信心 0.90　依據：整句在表達「讓我們表現得有禮貌」
- gold：`06560202` 導致後述對象涉入後述事件。

**134. 上**　`wsd-上-2481`　[dominant]
- 原句：林青霞也在記者會上感動的表示，
- 譯文：Yvonne Yeh also emotionally expressed at the press conference,
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：press conference 是以 Yvonne Yeh 為主題的場合
- gold：`04081314` 事件的發生在前述事物的範圍內。

**135. 行**　`wsd-行-a94f`　[dominant]
- 原句：父母就希望你只要書念好就行了。
- 譯文：Parents just hope that you do well in your studies.
- judge 選：`06775706` 做，取代整個事件。　信心 0.90　依據：整句在說「做好學業」而非實際移動
- gold：`06775711` 形容表示同意或允許。

**137. 拍**　`wsd-拍-8f3e`　[dominant]
- 原句：拍那個終極保鏢的時候。
- 譯文：When they were filming that ultimate bodyguard.
- judge 選：`08028003` 用攝影器材紀錄動態影像。　信心 0.95　依據：整句在說用器材紀錄動態影像
- gold：`08028004` 參與拍攝電影與製作。

**139. 還**　`wsd-還-f9cb`　[dominant]
- 原句：但應該還會再等幾個月，
- 譯文：But we should still wait for a few more months.
- judge 選：`05002705` 表預期發生的改變在時間參考點之後。　信心 0.95　依據：still 表預期改變在時間參考點之後
- gold：`05002703` 表前述範圍之外有所補充。

**140. 畫**　`wsd-畫-8a7f`　[dominant]
- 原句：在絹布上做畫。
- 譯文：Painting on silk fabric.
- judge 選：`06550301` 利用線條、色彩在平面上做出特定形象。　信心 0.95　依據：整句在說在絲織品上進行繪畫行為
- gold：`06550302` 利用線條、色彩在平面上做出特定形象的藝術作品。

**142. 大**　`wsd-大-5c2e`　[dominant]
- 原句：合成一股大力量呢？
- 譯文：What powerful force can we create together?
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文未表達「大」的任何比較或程度語義
- gold：`05227204` 形容程度超過比較對象的。

**143. 場**　`wsd-場-5dfe`　[dominant]
- 原句：往年常常因為某一場球賽的比賽地點、時間無法達成共識，
- 譯文：In past years, consensus was often difficult to reach regarding the venue and timing of certain games.
- judge 選：`06721701` 具有特定用途且可開放給大眾使用的地方或建築物。　信心 0.95　依據：譯文中的 venue 指舉辦比賽的場所
- gold：`06721709` 計算經過安排的活動的單位。

**147. 錢**　`wsd-錢-f034`　[dominant]
- 原句：但偏偏卻有很多人願把錢送入虎口，
- 譯文：But for some reason, many people are still willing to throw their money into the tiger's den.
- judge 選：`06015102` 通指貨幣。　信心 0.95　依據：整句在談論人們投入貨幣到虎穴
- gold：`06015105` 經費、錢財。

**148. 中**　`wsd-中-b105`　[dominant]
- 原句：多位教授昨天在澄社主辦的座談會中，
- 譯文：Several professors attended a symposium hosted by the Cheng She Society yesterday.
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：整句強調活動發生的時間點
- gold：`04004605` 在前述的機構或領域範圍。

**151. 小**　`wsd-小-7024`　[dominant]
- 原句：甚至滿園成千上萬的小花，
- 譯文：Even the entire garden is filled with thousands upon thousands of little flowers.
- judge 選：`05227103` 形容數目或數量少於比較對象的。　信心 0.95　依據：little flowers 表數量少於一般預期
- gold：`05227101` 形容體積少於比較對象的。

**152. 中**　`wsd-中-6473`　[dominant]
- 原句：在上次吸吮一章中，
- 譯文：In the previous chapter titled "Sucking,"
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：標題中的「中」指前一章節的時間範圍
- gold：`04004605` 在前述的機構或領域範圍。

**153. 度**　`wsd-度-4fa1`　[dominant]
- 原句：他們繼續在自己生活的地方和工作崗位度信仰的生活。
- 譯文：They continued to live out their faith in their own places of residence and work.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文未提及任何與「度」相關的時空或抽象概念
- gold：`06785402` 經過特定時段。

**155. 中**　`wsd-中-103c`　[dominant]
- 原句：主要乃因在如此萎縮的成交量中，
- 譯文：Amid such shrinking transaction volumes,
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：交易量萎縮發生在時間範圍內
- gold：`04004605` 在前述的機構或領域範圍。

**156. 空**　`wsd-空-43b7`　[dominant]
- 原句：在紅樓二樓右側空教室成立的「網咖」昨日開幕。
- 譯文：A "net café" was inaugurated yesterday in the vacant classroom on the second floor to the right of Honglou.
- judge 選：`07114601` 比喻在版面上特別留下空白。　信心 0.90　依據：空教室意指未被使用的教室，符合版面留白的比喻義
- gold：`07114607` 形容可使用的空間還沒有被完全利用。

**157. 字**　`wsd-字-c8e1`　[dominant]
- 原句：因為我的所有最字，
- 譯文：All my best wishes.
- judge 選：`06584501` 記錄語言的書面符號。　信心 0.90　依據：整句在表達祝福的書面語言符號
- gold：`06584502` 中文書面書寫的最小單位。

**158. 強**　`wsd-強-ee11`　[dominant]
- 原句：她的港裔美籍夫婿區永禧親和力強，
- 譯文：Her Hong Kong-born American husband Au Wing Hei has a strong affinity.
- judge 選：`09250306` 形容特定特性的程度高。　信心 0.95　依據：整句在說對某事物的親和力程度高
- gold：`09250303` 形容能力或發展狀況好的。

**159. 中**　`wsd-中-8b41`　[dominant]
- 原句：混合工作負荷中的「自然工作負荷」是在控制條件之下以較少變化的方式執行。
- 譯文：In mixed workloads, "natural workload" is executed under controlled conditions with less variation.
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.90　依據：controlled conditions with less variation 表時間範圍
- gold：`04004605` 在前述的機構或領域範圍。

**161. 吃**　`wsd-吃-5f46`　[dominant]
- 原句：家裡吃的麵都是自己做的，
- 譯文：We always make noodles at home ourselves.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句在說製作麵條而非食用
- gold：`05227001` 使物體經過口中吞入體內。

**164. 正**　`wsd-正-71ae`　[dominant]
- 原句：警方正擴大追查中。
- 譯文：The police are expanding their investigation.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句無關於「正」的語義傳達
- gold：`07009821` 表動作進行中或狀態持續中。

**165. 支**　`wsd-支-1fe0`　[dominant]
- 原句：而韓國隊卻只有七支。
- 譯文：However, the South Korean team only has seven.
- judge 選：`03056204` 計算團隊的單位。　信心 0.95　依據：整句在說團隊人數
- gold：`03056210` 計算棒球賽中擊出的有效打擊數。

**166. 中**　`wsd-中-32fc`　[dominant]
- 原句：六年國建計畫中處處可見為人癌細胞架設的舞台，
- 譯文：Throughout the Six-Year National Construction Plan, stages were set up everywhere for human cancer cells.
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：譯文強調計畫執行期間設有階段
- gold：`04004605` 在前述的機構或領域範圍。

**167. 分**　`wsd-分-1315`　[dominant]
- 原句：布朗也只有八點一分，
- 譯文：Brown only has 8.1 points.
- judge 選：`05007101` 用於紀錄成績或競賽結果的數目。　信心 0.95　依據：整句在說紀錄競賽成績的數值
- gold：`05007102` 計算分數的單位。

**168. 帶**　`wsd-帶-170d`　[dominant]
- 原句：秋天你帶我來歐洲好嗎？
- 譯文：Would you like me to take you to Europe in the fall?
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：整句在說支配者使被支配者跟著移動
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**171. 吃**　`wsd-吃-dac3`　[dominant]
- 原句：其實吃茶去並無深意。
- 譯文：Actually, there is no deep meaning to drinking tea.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文談論喝茶而非吃東西
- gold：`05227001` 使物體經過口中吞入體內。

**172. 做**　`wsd-做-f190`　[dominant]
- 原句：程一駿也曾前往東沙群島做綠蠵龜分布調查，
- 譯文：Cheng I-chun also once went to the Dongsha Islands to conduct a survey on the distribution of green sea turtles.
- judge 選：`06664307` 進行特定正式活動。　信心 0.95　依據：整句在說進行正式調查活動
- gold：`06664306` 做，取代整個事件。

**174. 正**　`wsd-正-5121`　[dominant]
- 原句：但樓下爸媽正興趣盎然的替她編織未來。
- 譯文：But the parents downstairs are enthusiastically weaving a future for her.
- judge 選：`07009822` 表前述對象不經刻意安排而完全符合後述描述。　信心 0.90　依據：整句在說父母主動為她編織未來
- gold：`07009821` 表動作進行中或狀態持續中。

**175. 強**　`wsd-強-cf66`　[dominant]
- 原句：她就有很強的自主意識，
- 譯文：She has a strong sense of independence.
- judge 選：`09250306` 形容特定特性的程度高。　信心 0.95　依據：整句強調「獨立特性的程度高」
- gold：`09250303` 形容能力或發展狀況好的。

**179. 行**　`wsd-行-45ab`　[dominant]
- 原句：我們演習一下就行了，
- 譯文：Let's just practice.
- judge 選：`06775706` 做，取代整個事件。　信心 0.95　依據：整句在說進行練習活動
- gold：`06775711` 形容表示同意或允許。

**181. 起**　`wsd-起-f55c`　[dominant]
- 原句：台北羽球名人邀請賽八日起在台北勝光羽球館開打，
- 譯文：The Taipei Badminton Invitational Tournament kicks off on the 8th at the Shenguang Badminton Hall in Taipei.
- judge 選：`04004828` 開始或產生。　信心 0.95　依據：kicks off 表示賽事開始，符合「開始或產生」義
- gold：`04004801` 表示事件時間範圍的開始參考點。

**182. 深**　`wsd-深-9292`　[dominant]
- 原句：而且更深一層的智慧的發揮。
- 譯文：And the deeper manifestation of wisdom.
- judge 選：`06663315` 形容比喻接近事物最基本概念而不易由表面現象理解的。　信心 0.90　依據：manifestation of wisdom 對應最深層概念
- gold：`06663314` 形容比喻牽涉事件的程度高。

**185. 長**　`wsd-長-d38d`　[dominant]
- 原句：工作負荷必須花長時間來記錄，
- 譯文：Workload must be recorded over a long period of time.
- judge 選：`06030810` 時間的長度。　信心 0.95　依據：整句強調時間跨度的長度
- gold：`06030803` 形容事件持續的時間間隔大。

**187. 人**　`wsd-人-9047`　[dominant]
- 原句：有些人批國安聯盟是太上決策機制，
- 譯文：Some people criticize the National Security Alliance as an extra-constitutional decision-making mechanism.
- judge 選：`05231105` 自己以外的人。　信心 0.95　依據：譯文強調批評者為他人而非自己
- gold：`05231101` 軀幹直立，用雙腳行走的高等動物，具備思考能力，有語言文字，能進行社交活動。

**193. 吃**　`wsd-吃-c09d`　[dominant]
- 原句：晚上在北京飯店新樓吃羊肉，
- 譯文：I had lamb at the Beijing Hotel New Building in the evening.
- judge 選：`05227007` 在後述地點用餐。　信心 0.95　依據：整句在說在特定地點用餐
- gold：`05227001` 使物體經過口中吞入體內。

**195. 正**　`wsd-正-8b50`　[dominant]
- 原句：正準備開槍，
- 譯文：I was about to pull the trigger.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句在說扣扳機動作即將發生，未傳達「正」的語義
- gold：`07009821` 表動作進行中或狀態持續中。

**196. 去**　`wsd-去-eeed`　[dominant]
- 原句：我們要去旅行，
- 譯文：We are going to travel.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說前往某處進行旅行
- gold：`06559205` 表前述對象進行後述事件。

**197. 拍**　`wsd-拍-c888`　[dominant]
- 原句：「這部電影是誰拍的？
- 譯文：Who directed this movie?
- judge 選：`08028003` 用攝影器材紀錄動態影像。　信心 0.95　依據：整句在說電影製作的導演職責
- gold：`08028004` 參與拍攝電影與製作。

**198. 畫**　`wsd-畫-fa24`　[dominant]
- 原句：畫裡人物竟是她夢境中的書生。
- 譯文：The figure in the painting turned out to be the scholar from her dream.
- judge 選：`06550301` 利用線條、色彩在平面上做出特定形象。　信心 0.95　依據：整句在說繪製的形象作品
- gold：`06550302` 利用線條、色彩在平面上做出特定形象的藝術作品。

**201. 就**　`wsd-就-d8a6`　[non_dominant]
- 原句：這就是「相」很少印在我的心上。
- 譯文：That's why the "phase" rarely leaves an impression on my mind.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：整句強調前因後果的自然發展
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**205. 小**　`wsd-小-2e7b`　[non_dominant]
- 原句：小野豬叫著：
- 譯文：A wild boar is grunting.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文僅描述野豬發出聲音，未涉及「小」的語義
- gold：`05227107` 形容年紀比特定對象小。

**208. 點**　`wsd-點-b366`　[non_dominant]
- 原句：說得確實點，
- 譯文：Just put it bluntly.
- judge 選：`04043803` 書寫筆畫的一種，沒有線條或延伸。　信心 0.95　依據：bluntly 表達直接陳述，對應筆畫的點
- gold：`04043813` 表不確定的小數量。

**210. 吃**　`wsd-吃-cf63`　[non_dominant]
- 原句：「天生我才必有用」、「吃得苦中苦，
- 譯文："Great minds have aims, petty minds have wishes."
"Only through hardship can one achieve greatness."
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文完全未涉及飲食或比喻語義
- gold：`05227009` 比喻經歷後述負面事件。

**211. 深**　`wsd-深-b431`　[non_dominant]
- 原句：於圖書事業深有研究或經驗並有專門著作者之規定，
- 譯文：Persons with in-depth research or experience in library affairs and who have published specialized works are eligible.
- judge 選：`06663314` 形容比喻牽涉事件的程度高。　信心 0.90　依據：in-depth research 對應牽涉事件程度高
- gold：`06663313` 表超過平常的程度。

**212. 破**　`wsd-破-8932`　[non_dominant]
- 原句：當年城破家亡，
- 譯文：The city fell, and our home was lost.
- judge 選：`06761406` 形容比喻品質或功能低於說話者預期的標準。　信心 0.90　依據：整句在說城市淪陷且家園毀損
- gold：`06761401` 前述物體因受到外力影響使特定部位脫離，而影響外觀的完整性。

**213. 空**　`wsd-空-2f0b`　[non_dominant]
- 原句：世俗諦都是假的、該空的；
- 譯文：All worldly truths are false and should be seen as empty.
- judge 選：`06517316` 形容比喻特定對象沒有被使用。　信心 0.90　依據：譯文強調「空」的虛假與未被使用
- gold：`06517332` 形容事物不具有實體概念的。

**214. 花**　`wsd-花-da24`　[non_dominant]
- 原句：棘皮動物海百合像海中之花般地鮮艷綻放，
- 譯文：Echinoderms like sea lilies bloom brilliantly in the sea like flowers.
- judge 選：`05229001` 植物的主要器官之一，主要用於繁殖，通常具有顏色鮮豔和形狀漂亮的花瓣。　信心 0.95　依據：整句以花比喻海百合的外觀
- gold：`05229006` 比喻事物的精華。

**218. 強**　`wsd-強-7c81`　[non_dominant]
- 原句：國男組也將進行四強交叉準決賽，
- 譯文：The men's team will also compete in the semifinals crossover.
- judge 選：`09250303` 形容能力或發展狀況好的。　信心 0.90　依據：整句強調團隊能力優秀而參賽
- gold：`09250305` 競賽中排名在前述範圍的特定對象。

**219. 空**　`wsd-空-6f79`　[non_dominant]
- 原句：是非成敗轉頭空，
- 譯文：Only the translation is required:

Time turns all victories and defeats to nothing.
- judge 選：`06517327` 形容特定對象完全沒有剩下的。　信心 0.95　依據：譯文強調「一切化為烏有」表完全不剩
- gold：`06517332` 形容事物不具有實體概念的。

**222. 條**　`wsd-條-499c`　[non_dominant]
- 原句：這條等於不存在，
- 譯文：This statement is equivalent to non-existence.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文無計量或條列語義
- gold：`06585929` 法規結構分類的一種，在「節」之下、「項」之上。

**223. 高**　`wsd-高-1c47`　[non_dominant]
- 原句：配備精良的美國警方人員在攝影高台上嚴密監視觀眾動態，
- 譯文：Well-equipped U.S. police officers closely monitor the audience from elevated surveillance platforms.
- judge 選：`06010607` 形容有前述高度的。　信心 0.90　依據：elevated platforms 表達有高度的平台
- gold：`06010601` 形容物體從頂部到地面的距離大於比較對象的。

**226. 行**　`wsd-行-59db`　[non_dominant]
- 原句：有兩行特別醒目的大字，
- 譯文：Two lines of particularly eye-catching large characters are displayed.
- judge 選：`05145003` 文字書寫或排版時的單位，在同一方向書寫或排版到轉變方向前為止為一行。　信心 0.95　依據：譯文提到書寫或排版的單位
- gold：`05145004` 計算文字書寫或排版時的單位，在同一方向書寫或排版到轉變方向前為止為一行。

**228. 格**　`wsd-格-2292`　[non_dominant]
- 原句：由於十五格圖的四個構面恰好反應出價值鏈不同階段的特性，
- 譯文：The four dimensions of the 15-box matrix precisely reflect the characteristics of different stages in the value chain.
- judge 選：`06730804` 用來放置物品的結構體內部空間所區隔出的較小的空間。　信心 0.90　依據：矩陣中的每個小格子是被區隔的空間
- gold：`06730802` 兩對近似平行線相交所圍成的空間。

**229. 對**　`wsd-對-85c8`　[non_dominant]
- 原句：但因氣氛及感覺不對，
- 譯文：But since the atmosphere and feeling were off.
- judge 選：`04017506` 引介事件所涉及的對象或範圍。　信心 0.90　依據：譯文中的 off 指向氣氛與感覺所涉及的對象
- gold：`04017503` 形容適合的。

**230. 破**　`wsd-破-6095`　[non_dominant]
- 原句：自己發球局反在第六局被破，
- 譯文：I was broken in my own serve game in the sixth set.
- judge 選：`06761401` 前述物體因受到外力影響使特定部位脫離，而影響外觀的完整性。　信心 0.90　依據：整句在說球員在發球局中失敗
- gold：`06761422` 比喻在球類運動中，在對方發球的局數中，將其擊敗。

**231. 法**　`wsd-法-7bbd`　[non_dominant]
- 原句：而非國民黨統治機器所貼下標籤的地域區分法‧人們習慣稱呼的本省人其實也是外省移民的第七代，
- 譯文：People are actually accustomed to calling the "ben sheng ren" the seventh generation of waisheng immigrants.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句在談稱呼習慣，未涉法律或法術語義
- gold：`05045104` 做事的步驟或技巧。

**232. 道**　`wsd-道-ef48`　[non_dominant]
- 原句：每一個性方面的需求可能有些人比較好此道，
- 譯文：Every individual may have varying levels of expertise or interest in matters related to intimacy.
- judge 選：`06002401` 思想或理論。　信心 0.90　依據：譯文中的 matters 承載「事物」語義，與思想或理論相關
- gold：`06002402` 含有哲理的技藝。

**234. 邊**　`wsd-邊-0c87`　[non_dominant]
- 原句：步道一邊是長著爬籐的花架，
- 譯文：A path is lined with a trellis covered in climbing vines.
- judge 選：`06584401` 幾何圖形中相夾成角的線條。　信心 0.90　依據：trellis 與 vines 的交界線為幾何邊緣
- gold：`06584406` 特定地區中位於前述方向邊緣的地點。

**235. 叫**　`wsd-叫-6eac`　[non_dominant]
- 原句：吃飯時那張木椅便被女人寬軟的臀部撫摸得舒服地輕叫。
- 譯文：As she sat on the wooden chair during the meal, it creaked softly under the gentle pressure of her soft, pliant buttocks.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句未提及任何發聲或稱呼行為
- gold：`04010205` 比喻物體像人一樣發出聲響。

**238. 過**　`wsd-過-46a1`　[non_dominant]
- 原句：透著粉綠、粉紫、粉紅的金花鱸游曳而過，
- 譯文：A flash of golden perch, tinged with soft green, lavender, and pink, darted by.
- judge 選：`04005002` 穿越特定障礙或界線。　信心 0.95　依據：darted by 表快速穿越空間
- gold：`04005001` 由特定路徑通過。

**239. 熱**　`wsd-熱-5dad`　[non_dominant]
- 原句：他也是較常跳流行熱舞，
- 譯文：He also often performs popular hot dances.
- judge 選：`05228710` 形容比喻全心投入的。　信心 0.90　依據：整句在說熱情投入的舞蹈
- gold：`05228715` 表動作劇烈。

**240. 條**　`wsd-條-5dab`　[non_dominant]
- 原句：斷肢逃生的情形很像一個人被巨石壓住一條腿，
- 譯文：A case of escaping with a severed limb is much like a person having a boulder pinning down one leg.
- judge 選：`06585903` 計算形狀細而長的物體的單位。　信心 0.90　依據：boulder 為細長形物體，語義由名詞片語承載
- gold：`06585910` 計算身體部位的單位。

**241. 抽**　`wsd-抽-b0a2`　[non_dominant]
- 原句：爸爸想再抽一次，
- 譯文：Dad wants to smoke again.
- judge 選：`06598613` 動物用口或鼻攝取後述氣體。　信心 0.95　依據：整句在說吸入煙草氣體
- gold：`06598603` 伸出的肢體或頭部往身體的方向退。

**242. 死**　`wsd-死-9b5f`　[non_dominant]
- 原句：只要文化不死我在美國柏克萊一住就是十五年。
- 譯文：I've been living in Berkeley, USA for fifteen years, and as long as culture survives, I'll stay.
- judge 選：`05035203` 形容比喻事件終止不再存在。　信心 0.90　依據：整句在說文化持續存在而不終止
- gold：`05035209` 形容不再使用的。

**244. 間**　`wsd-間-f76e`　[non_dominant]
- 原句：但至今年三月間，
- 譯文：But as of this past March,
- judge 選：`04084105` 引介特定時段。　信心 0.95　依據：as of March 引介特定時間點
- gold：`04084103` 引介時間的範圍。

**245. 分**　`wsd-分-a4e1`　[non_dominant]
- 原句：自家門口遭到三名蒙面歹徒分執鋁製球棒毆傷，
- 譯文：Three people in masks attacked me at my doorstep with aluminum baseball bats and injured me.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文無任何與「分」相關之語義
- gold：`04146408` 表分別。

**246. 大**　`wsd-大-6041`　[non_dominant]
- 原句：又在１９０６年建了更大的ＬａｎｇｄｅｌｌＨａｌｌ，
- 譯文：In 1906, an even larger Langdell Hall was built.
- judge 選：`05227201` 形容體積超過比較對象的。　信心 0.90　依據：larger 指建物體積大於原有
- gold：`05227202` 形容容量超過比較對象的。

**247. 下**　`wsd-下-7715`　[non_dominant]
- 原句：下表中列示ＧＡＴＥ現有實用軟體的名稱及其功能，
- 譯文：The table below lists the names and functions of the existing practical software available for GATE.
- judge 選：`04081815` 比喻在參考點之後的文本順序。　信心 0.90　依據：below 在此比喻表格在文本中的位置順序
- gold：`04081803` 鄰近前述物體的底部或低於該物體位置。

**248. 做**　`wsd-做-88b9`　[non_dominant]
- 原句：哥哥做蘇武牧羊、天女散花。
- 譯文：Brother did "Su Wu Tending Sheep" and "Fairy Scattering Flowers."
- judge 選：`06664307` 進行特定正式活動。　信心 0.95　依據：整句在說進行戲劇或表演活動
- gold：`06664308` 前述對象的工作或身份是後述對象。

**249. 度**　`wsd-度-9c03`　[non_dominant]
- 原句：自從釋迦牟尼佛轉法輪度眾生，
- 譯文：Since the Buddha began turning the Dharma wheel to deliver sentient beings.
- judge 選：`06785402` 經過特定時段。　信心 0.90　依據：整句在說佛陀開始傳法的時段
- gold：`06785404` 助人得到佛法。

**250. 拿**　`wsd-拿-752a`　[non_dominant]
- 原句：只開放特定場地供學生拿號碼牌寄物。
- 譯文：Only specific areas are open for students to take numbered tickets for luggage storage.
- judge 選：`04011201` 用手取物或持物。　信心 0.95　依據：整句在說學生用手取得行李票
- gold：`04011202` 向特定對象取得主事者擁有或應該擁有的金錢或物品。

**251. 上**　`wsd-上-9cab`　[non_dominant]
- 原句：在歷史上曾經被滅亡過好幾次，
- 譯文：It has been conquered and destroyed multiple times throughout history.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：throughout history 表示以歷史為範圍主題
- gold：`04081317` 按前述事物的觀點來陳述。

**252. 抽**　`wsd-抽-4625`　[non_dominant]
- 原句：在大型的教學醫院皆有辦法抽血檢查。
- 譯文：Large teaching hospitals are all capable of drawing blood for testing.
- judge 選：`06598612` 以壓力或吸力移動後述流體到其他地方。　信心 0.95　依據：整句在說醫院用吸力移動血液
- gold：`06598611` 利用真空造成吸力將後述流體由動物體內取出。

**253. 還**　`wsd-還-796e`　[non_dominant]
- 原句：我還以為他們會為身體的殘障痛苦呢！
- 譯文：I thought they would suffer from physical disabilities!
- judge 選：`05002704` 表超出預料。　信心 0.95　依據：整句表達超出預期的殘疾結果
- gold：`05002707` 表前述對象符合讓步後的條件。

**261. 去**　`wsd-去-d84e`　[non_dominant]
- 原句：去幾天﹖
- 譯文：How many days ago?
- judge 選：`06559218` 比喻前述時段經過，成為特定時間點以前的時段。　信心 0.95　依據：整句在問過去的時間點，符合時間經過的比喻義
- gold：`06559201` 向特定地點移動。

**262. 平**　`wsd-平-cb19`　[non_dominant]
- 原句：車子的把手為平把，
- 譯文：The car has flat handlebars.
- judge 選：`06025201` 形容物體表面高度相同沒有凹凸起伏的。　信心 0.95　依據：handlebars 表面平整無凹凸
- gold：`06025213` 形容高度相同的。

**263. 吃**　`wsd-吃-7df1`　[non_dominant]
- 原句：他們不像某些臺灣移民過的是「吃老本」的日子，
- 譯文：They don't live off their past like some Taiwanese immigrants do.
- judge 選：`05227009` 比喻經歷後述負面事件。　信心 0.95　依據：整句比喻經歷過去生活
- gold：`05227012` 比喻物品或能量因使用而漸漸減少。

**264. 代**　`wsd-代-38c7`　[non_dominant]
- 原句：這些是發生在這一代華人身上比較新的事情。
- 譯文：These are relatively new events that have happened to this generation of Chinese people.
- judge 選：`04016205` 年齡大致相同的一群人。　信心 0.95　依據：譯文強調同一時代的華人世代
- gold：`04016206` 計算年齡大致相同的一群人的單位。

**265. 度**　`wsd-度-85ca`　[non_dominant]
- 原句：毛高文也常以他高八度的音調嚷嚷兩人歌路不同，
- 譯文：May also shout about their different musical paths in his high-pitched voice.
- judge 選：`05147605` 比喻前述特性的程度。　信心 0.95　依據：high-pitched voice 表達聲音的高低程度
- gold：`05147619` 計算音程的單位。

**268. 道**　`wsd-道-e472`　[non_dominant]
- 原句：相信透過教育這最後一道丹藥可以拯救！
- 譯文：I believe that through education, this final elixir can save us!
- judge 選：`04083505` 比喻處理事情或解決問題的方法。　信心 0.90　依據：elixir在此被譬喻為拯救方法
- gold：`04083512` 計算步驟的單位。

**273. 回**　`wsd-回-1e59`　[non_dominant]
- 原句：有一回他受命去孟家宅院取兩支手槍，
- 譯文：One time, he was ordered to go to the Meng family compound to retrieve two pistols.
- judge 選：`03019001` 從其它地方到原來的地方或處所。　信心 0.95　依據：整句在說被命令前往某處取回物品
- gold：`03019008` 計算事件的單位。

**274. 就**　`wsd-就-fe97`　[non_dominant]
- 原句：要不然就是陰天。
- 譯文：Otherwise, it will be overcast.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.95　依據：Otherwise表條件假設，符合充分條件義
- gold：`05198307` 表強調說話者已知事實。

**279. 就**　`wsd-就-5f17`　[non_dominant]
- 原句：就是彼此的特性。
- 譯文：It is about each other's characteristics.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文無條件、轉折或強調語氣之語義
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**280. 點**　`wsd-點-9076`　[non_dominant]
- 原句：就這點來說，
- 譯文：In this regard,
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文為片語且無明顯語義承載
- gold：`04043812` 指所陳述事件的部份或方面。

**282. 帶**　`wsd-帶-6ba6`　[non_dominant]
- 原句：幾乎帶一點哽咽，
- 譯文：Almost choked up a little.
- judge 選：`06791413` 走在前面，引導前進方向。　信心 0.90　依據：整句在說被某物阻塞而難以前進
- gold：`06791420` 比喻具有後述意義或情感。

**284. 中**　`wsd-中-c90e`　[non_dominant]
- 原句：這種哲學和傅蘭尼、孔恩等嘗試在科學的知識如何獲得的過程中推論知識論的問題是同一類的，
- 譯文：This type of philosophy, like that of Foucault and Kuhn, attempts to infer epistemological issues in the process of how knowledge is acquired in science, and belongs to the same category.
- judge 選：`04004605` 在前述的機構或領域範圍。　信心 0.90　依據：屬於某個領域範疇（哲學流派）
- gold：`04004618` 在事件的過程中。

**285. 去**　`wsd-去-aba8`　[non_dominant]
- 原句：後來就坐飛機到東京去了。
- 譯文：Later, I took a plane to Tokyo.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說移動至特定地點東京
- gold：`06559204` 隨動作到達前述地點。

**287. 當**　`wsd-當-d0c0`　[non_dominant]
- 原句：而在將高山當郊山玩的途中，
- 譯文：And along the way, while treating towering mountains like mere hills for a casual outing,
- judge 選：`04013907` 引介背景事件作為時間的範圍。　信心 0.95　依據：while 引介背景事件作為時間範圍
- gold：`04013901` 前述對象的工作或身份是後述對象。

**289. 帶**　`wsd-帶-f9d9`　[non_dominant]
- 原句：所以視障生必須要仰賴別人帶他過馬路。
- 譯文：Therefore, visually impaired students must rely on others to help them cross the road.
- judge 選：`06791407` 使特定對象跟著有支配權的人移動。　信心 0.95　依據：整句在說他人協助引導視障學生過馬路
- gold：`06791413` 走在前面，引導前進方向。

**290. 畫**　`wsd-畫-7d89`　[non_dominant]
- 原句：例如在畫建築時，
- 譯文：For example, when drawing buildings,
- judge 選：`06550303` 利用線條、色彩在平面上描出特定對象的形象的技巧或知識。　信心 0.95　依據：整句在說建築繪製技巧的行為
- gold：`06550301` 利用線條、色彩在平面上做出特定形象。

**291. 去**　`wsd-去-aee9`　[non_dominant]
- 原句：∥我們到紐約去。
- 譯文：We are going to New York.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說前往特定地點
- gold：`06559204` 隨動作到達前述地點。

**292. 中**　`wsd-中-4054`　[non_dominant]
- 原句：最後在呂尚叡小姐（ＩＩＩ服務部人員）、童敏惠小姐（台灣大學圖書館系統組主任）說明「填寫ＧｅｔｔｉｎｇＳｔａｒｔｅｄＷｉｔｈＩＮＮＯＰＡＣ」中圓滿結束了此次會議。
- 譯文：Finally, Ms. Lü Shang-rui (staff member of the III Service Department) and Ms. Tong Min-hui (Director of the System Division at the National Taiwan University Library) explained "Filling out 'Getting Started with INNOPAC'" before the meeting concluded successfully.
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：譯文中「before the meeting concluded」明確表達時間範圍
- gold：`04004618` 在事件的過程中。

**293. 代**　`wsd-代-5679`　[non_dominant]
- 原句：由於本學期校方代學生聯合會向學生收取自治費，
- 譯文：The Student Union collected self-governance fees on behalf of the school this semester.
- judge 選：`07104505` 表替他人處理或執行。　信心 0.95　依據：整句在說代表學校代收費用
- gold：`07104502` 排除後述事項，使前述事項佔有其位。

**296. 發**　`wsd-發-68d0`　[non_dominant]
- 原句：∥我要靠意外之財我才能發啦我！
- 譯文：I'm counting on a windfall to strike it rich!
- judge 選：`05193416` 產生特定心理狀態或思想特質。　信心 0.90　依據：整句在說期待意外之財
- gold：`05193406` 形容得到讓眾人羨慕的名利。

**297. 破**　`wsd-破-f6ff`　[non_dominant]
- 原句：也沒聽說過肚皮會破的。
- 譯文：I've never heard of a belly bursting open either.
- judge 選：`06761402` 形容完整的物體因受到外力影響而裂成小塊的。　信心 0.90　依據：整句在說腹部因外力而裂開
- gold：`06761404` 特定物品產生缺口。

**298. 上**　`wsd-上-8d16`　[non_dominant]
- 原句：餐飲業上的自動點菜系統；
- 譯文：Automated ordering systems in the catering industry
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：整句強調自動化訂單系統在餐飲業中的應用範圍
- gold：`04081316` 以前述事物為對象。

**299. 上**　`wsd-上-34ff`　[non_dominant]
- 原句：在時間上適逢阿爾巴尼亞已故共黨首領霍查的遺孀妮克絲吉美。
- 譯文：At the time, it coincided with Nexhmije Hoxha, the widow of Albania's late communist leader Enver Hoxha.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：整句以「當時」為時間主題範圍
- gold：`04081317` 按前述事物的觀點來陳述。

**300. 條**　`wsd-條-7771`　[non_dominant]
- 原句：只求挽回一條垂危的生命，
- 譯文：I only seek to save a life hanging by a thread.
- judge 選：`06585924` 計算行進的路線的單位。　信心 0.90　依據：整句在說拯救一條垂死的生命
- gold：`06585911` 計算動物性命的單位。

**301. 分**　`wsd-分-1598`　[non_dominant]
- 原句：分不清是夢是真。
- 譯文：I can't tell if it's a dream or reality.
- judge 選：`04146408` 表分別。　信心 0.90　依據：整句在說區辨夢與現實的差異
- gold：`04146401` 特定對象分開。

**302. 破**　`wsd-破-d556`　[non_dominant]
- 原句：大陸經過文化大革命及破四舊的浩劫，
- 譯文：The mainland experienced the catastrophe of the Cultural Revolution and the destruction of the Four Olds.
- judge 選：`06761405` 形容完整的物體有缺口或物品因長期使用而呈現損壞的樣子。　信心 0.95　依據：整句在說文物或傳統遭受嚴重損壞
- gold：`06761415` 比喻故意違反特定限制或拘束。

**303. 子**　`wsd-子-daed`　[non_dominant]
- 原句：法華經長者窮子喻之中，
- 譯文：In the parable of the rich man and his poor son in the Lotus Sutra,
- judge 選：`07027901` 兒子和女兒。　信心 0.95　依據：譯文中「son」直接對應「子」作為兒子之意
- gold：`07027904` 具有前述身份或從事前述工作的人。

**305. 打**　`wsd-打-6cc8`　[non_dominant]
- 原句：不是靠打殺就可以一手遮天的，
- 譯文：It's not something that can be swept under the rug just by force.
- judge 選：`05229154` 比喻以後述理由為藉口，進行特定事件。　信心 0.90　依據：整句以比喻方式用力壓制問題
- gold：`05229126` 兩對立團體之間起武力衝突。

**306. 用**　`wsd-用-ad93`　[non_dominant]
- 原句：依照戒急用忍檢討執行計畫，
- 譯文：In accordance with the "Review and Implementation Plan for Curbing Impatience,"
- judge 選：`04017401` 利用特定對象的特定功能。　信心 0.90　依據：依據計畫內容採取行動
- gold：`04017405` 比喻選擇後述有系統性的態度或方式。

**309. 代**　`wsd-代-2206`　[non_dominant]
- 原句：身為台塑的第二代，
- 譯文：As the second generation of the Formosa Plastics Group,
- judge 選：`04016203` 比喻有衍生關係的特定對象。　信心 0.90　依據：「第二代」指衍生的後續系列
- gold：`04016201` 生物血緣關係中所有與其始祖的距離相同的人所組成的團體。

**310. 面**　`wsd-面-572d`　[non_dominant]
- 原句：她曾在82年奪得區運5面金牌後因傷退出體操界，
- 譯文：She once won five gold medals at the District Games in 1982 before retiring from gymnastics due to an injury.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文未提及任何與「面」相關之語義
- gold：`03028807` 計算牌狀物的單位。

**311. 就**　`wsd-就-f48f`　[non_dominant]
- 原句：首先選擇茶葉就是一門學問。
- 譯文：Choosing tea leaves is a subject of study in itself.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：整句強調選擇茶葉本身即為研究主題
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**312. 分**　`wsd-分-1a74`　[non_dominant]
- 原句：分由七十一至七十七會計年度逐年編列預算，
- 譯文：The budget shall be allocated annually from fiscal years 71 to 77.
- judge 選：`04146406` 將事物分享或分配給人。　信心 0.95　依據：整句在說將預算分配給特定期間
- gold：`04146408` 表分別。

**313. 條**　`wsd-條-8075`　[non_dominant]
- 原句：每次烤鴨都一條腿，
- 譯文：Every time I roast a duck, it's on one leg.
- judge 選：`06585908` 計算動物的單位。　信心 0.95　依據：整句在說烤鴨時以單腿支撐
- gold：`06585910` 計算身體部位的單位。

**315. 叫**　`wsd-叫-9a50`　[non_dominant]
- 原句：當頑皮的鬧鐘叫了以後，
- 譯文：After the mischievous alarm clock rang,
- judge 選：`04010201` 人以大聲量發聲。　信心 0.95　依據：整句在說鬧鐘發出聲響
- gold：`04010205` 比喻物體像人一樣發出聲響。

**316. 點**　`wsd-點-87e4`　[non_dominant]
- 原句：就某一點而言，
- 譯文：In a certain sense,
- judge 選：`04043808` 事件或過程中具顯著的指標。　信心 0.90　依據：in a certain sense 表達顯著指標或觀察角度
- gold：`04043812` 指所陳述事件的部份或方面。

**317. 打開**　`wsd-打開-c078`　[non_dominant]
- 原句：打開這個知識的寶庫。
- 譯文：Open this treasure trove of knowledge.
- judge 選：`06548116` 比喻拓展後述知識領域或經驗。　信心 0.95　依據：整句在說開啟知識領域的機會
- gold：`06548102` 將控制特定對象使其無法被打開或使用的裝置解除。

**321. 打**　`wsd-打-f6dd`　[non_dominant]
- 原句：有牌打就好，
- 譯文：As long as you have a license to play, that's all that matters.
- judge 選：`05229179` 利用電話裝置與人通話。　信心 0.95　依據：整句在說擁有許可即可通話
- gold：`05229133` 進行後述賽局，通常從過程中得到樂趣。

**322. 回**　`wsd-回-27ca`　[non_dominant]
- 原句：這回換野狼的屁股卡在洞口了，
- 譯文：This time, it's the wolf's butt that's stuck in the hole.
- judge 選：`03019007` 身體面向的改變，掉轉身體至背面的方向。　信心 0.95　依據：整句在說身體面向改變至背面方向
- gold：`03019008` 計算事件的單位。

**323. 上**　`wsd-上-94b4`　[non_dominant]
- 原句：在個人資料和事件的處理上，
- 譯文：In the handling of personal data and incidents,
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：譯文強調以個人數據為主題範圍
- gold：`04081317` 按前述事物的觀點來陳述。

**324. 低**　`wsd-低-0818`　[non_dominant]
- 原句：故包括大部份的自營商及散戶投資人普遍都有預期回檔後再行逢低承接的打算，
- 譯文：Most self-employed traders and retail investors generally plan to expect a pullback before buying the dip again.
- judge 選：`06748407` 形容數值變小。　信心 0.90　依據：整句在說價格或數值變小
- gold：`06748412` 形容程度或標準低於比較對象的。

**325. 行**　`wsd-行-907c`　[non_dominant]
- 原句：所以要出門是必須繞過公園而行的。
- 譯文：Therefore, you have to go around the park to get out.
- judge 選：`06775702` 比喻交通工具移動。　信心 0.90　依據：整句在說交通工具移動繞行公園
- gold：`06775701` 以兩腿交互向前移動，雙腳不同時離開地面。

**327. 帶**　`wsd-帶-3497`　[non_dominant]
- 原句：帶著滿腹心得與球經比以前更成熟。
- 譯文：I'm carrying a wealth of experience and insights, making me more mature than before.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.90　依據：整句在說經驗與見解隨自身移動
- gold：`06791420` 比喻具有後述意義或情感。

**329. 邊**　`wsd-邊-fb5e`　[non_dominant]
- 原句：調整的方法是手握雙筒鏡的兩邊，
- 譯文：Adjust the binoculars by holding both sides.
- judge 選：`06584404` 特定對象與其他鄰界對象交界的地方。　信心 0.90　依據：整句在說雙筒望遠鏡的兩側邊緣
- gold：`06584406` 特定地區中位於前述方向邊緣的地點。

**335. 場**　`wsd-場-9bec`　[non_dominant]
- 原句：除了在萬芳醫院的三場演出之外，
- 譯文：In addition to the three performances at Wanfang Hospital,
- judge 選：`06721701` 具有特定用途且可開放給大眾使用的地方或建築物。　信心 0.95　依據：醫院為可開放使用的場所，語義明確
- gold：`06721707` 計算戲劇中較小段落的單位。

**336. 條**　`wsd-條-f9f4`　[non_dominant]
- 原句：他的童年像一條浮根，
- 譯文：His childhood was like a floating root.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文無計量或條列語義
- gold：`06585903` 計算形狀細而長的物體的單位。

**337. 下**　`wsd-下-496b`　[non_dominant]
- 原句：在Ｃ目錄下打）ｐａｔｈ）。
- 譯文：Create a path under the C drive.
- judge 選：`04081803` 鄰近前述物體的底部或低於該物體位置。　信心 0.95　依據：整句在說磁碟機根目錄下方的路徑
- gold：`04081808` 比喻階級架構中低於前述階級的階級。

**338. 新**　`wsd-新-32cb`　[non_dominant]
- 原句：馬英九重申暫緩設立新的公立高中，
- 譯文：Ma Ying-jeou reiterated the postponement of establishing new public senior high schools.
- judge 選：`05237904` 形容和原來不一樣的。　信心 0.95　依據：整句強調與原先狀態不同的新設學校
- gold：`05237901` 形容特定對象剛產生不久。

**343. 人**　`wsd-人-64c0`　[non_dominant]
- 原句：高階積體電路設計公司至少雇用十人以上，
- 譯文：A high-end integrated circuit design company must employ at least ten or more people.
- judge 選：`05231102` 具有前述身份或從事前述工作的人。　信心 0.95　依據：整句在說公司須僱用特定工作的個體
- gold：`05231109` 符合特定需求、從事特定工作的人。

**348. 熱**　`wsd-熱-3583`　[non_dominant]
- 原句：無形的過熱，
- 譯文：Invisible overheating.
- judge 選：`05228701` 形容溫度高或感覺溫度高的。　信心 0.95　依據：overheating 直接表達溫度過高
- gold：`05228707` 形容身體陽氣亢盛。

**349. 說**　`wsd-說-9e57`　[non_dominant]
- 原句：可說毫不遜色。
- 譯文：It can be said to be no less impressive.
- judge 選：`05212407` 前述對象具有後述評價的屬性。　信心 0.90　依據：整句在評價後述對象具有「impressive」屬性
- gold：`05212406` 評價後述對象。

**353. 新**　`wsd-新-e875`　[non_dominant]
- 原句：然後沖進新燒滾水，
- 譯文：Then rush into freshly boiled water.
- judge 選：`05237901` 形容特定對象剛產生不久。　信心 0.95　依據：freshly boiled water 表煮沸不久的水
- gold：`05237905` 表過去不久的時間。

**354. 度**　`wsd-度-378e`　[non_dominant]
- 原句：那麼如何因應不同需求或在家庭結構變化時必須採行的「二度設計」就是我們檢討萬年平面的參考方向。
- 譯文：Therefore, the "second-time redesign" required to accommodate different needs or changes in family structure serves as our reference direction for reviewing the "never-changing floor plan."
- judge 選：`05147605` 比喻前述特性的程度。　信心 0.95　依據：整句強調「程度」作為參考方向
- gold：`05147617` 計算空間維數的單位。

**360. 轉**　`wsd-轉-cbbd`　[non_dominant]
- 原句：他三個手指悠然轉著那只淡青色玉鐲。
- 譯文：He leisurely twirled the light blue jade bracelet with three fingers.
- judge 選：`05228801` 物體維持本身的軸心，做連續改變方向的運動。　信心 0.95　依據：整句在說手指讓玉鐲做連續方向改變
- gold：`05228802` 使物體維持本身的軸心，做連續改變方向的運動。

**365. 就**　`wsd-就-d690`　[non_dominant]
- 原句：心浮動就是道心不堅固，
- 譯文：A floating mind is an unsteady Dao mind.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：整句強調前提條件下的自然發展
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**366. 上**　`wsd-上-568c`　[non_dominant]
- 原句：也把墳地上那些白花和紅花稱為杜鵑花。
- 譯文：Also refer to those white and red flowers on the grave as azaleas.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：整句以墳墓為主題範圍稱呼其上的花
- gold：`04081301` 前述物體的表面。

**368. 大**　`wsd-大-6481`　[non_dominant]
- 原句：大蛇竟然把嘴張開，
- 譯文：The serpent actually opened its mouth wide.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句在說張口的幅度，與「大」的比較義無關
- gold：`05227201` 形容體積超過比較對象的。

**370. 分**　`wsd-分-ea80`　[non_dominant]
- 原句：數十年不分寒暑，
- 譯文：For decades, regardless of the heat or cold,
- judge 選：`04146408` 表分別。　信心 0.90　依據：regardless of 表不受冷熱影響，語義為分別對待
- gold：`04146405` 依特性做分類。

**371. 發**　`wsd-發-5680`　[non_dominant]
- 原句：是很願意國內所有發卡機構能研擬出一套辦法來針對如果受款行號未照約定履行交付等值之物品，
- 譯文：I sincerely hope that all domestic card-issuing institutions will develop a set of measures to address situations where the acquiring bank fails to fulfill its contractual obligation to deliver equivalent goods.
- judge 選：`06724101` 按特定的分配原則將物品給特定對象。　信心 0.90　依據：整句在說核准後將物品交付給對象
- gold：`06724102` 事先核准後將後述證件或執照給特定對象。

**372. 明**　`wsd-明-2c5b`　[non_dominant]
- 原句：而教練費區和球員之間不和的事實也由暗而明，
- 譯文：The rift between the coaching staff and players has gradually become apparent.
- judge 選：`06685411` 形容比喻狀況變得明顯清楚。　信心 0.95　依據：整句在說狀況變得明顯清楚
- gold：`06685407` 形容比喻事件在公開的情況下進行的。

**373. 拿**　`wsd-拿-fe6f`　[non_dominant]
- 原句：有些人因「太紅」怕整個晚上因不停拿宵夜而無法念書，
- 譯文：Some people are so busy taking late-night snacks that they can't study all night out of fear of being "too popular."
- judge 選：`04011201` 用手取物或持物。　信心 0.90　依據：late-night snacks 為用手取用的食物
- gold：`04011202` 向特定對象取得主事者擁有或應該擁有的金錢或物品。

**375. 真**　`wsd-真-4c47`　[non_dominant]
- 原句：真希望可以永遠住在那裡。
- 譯文：I truly wish I could live there forever.
- judge 選：`05100406` 形容強調說話者對後述描述內容的肯定。　信心 0.95　依據：整句強調說話者對願望的真誠肯定
- gold：`05100414` 表說話者主觀評價程度高，帶有誇張語氣或情感。

**376. 上**　`wsd-上-21f2`　[non_dominant]
- 原句：一切都只停留在勞作的程度上。
- 譯文：Everything remains at the level of mere labor.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：譯文強調「層次」為主題範圍
- gold：`04081317` 按前述事物的觀點來陳述。

**378. 要**　`wsd-要-f6e4`　[non_dominant]
- 原句：要完成還早得很呢！
- 譯文：It's going to take a long time to finish!
- judge 選：`06636901` 表心中存有完成後述事件的願望。　信心 0.90　依據：整句在說預期完成某事的願望
- gold：`06636907` 表預期後述事件會在很短的時間內發生。

**380. 發**　`wsd-發-d72a`　[non_dominant]
- 原句：因此也在同時明令停止所有稻田轉用的審核與發照。
- 譯文：Therefore, it also simultaneously issued a formal order to halt all reviews and license issuances for converting rice fields to other uses.
- judge 選：`06724112` 公佈消息或新聞。　信心 0.95　依據：整句在說公佈正式命令
- gold：`06724102` 事先核准後將後述證件或執照給特定對象。

**383. 片**　`wsd-片-add4`　[non_dominant]
- 原句：他站在一片書牆前，
- 譯文：He stood in front of a wall of books.
- judge 選：`05195903` 計算平而薄的物品的單位。　信心 0.90　依據：書籍為平薄物品，片在此作量詞
- gold：`05195915` 計算牆或窗戶的單位。

**385. 用**　`wsd-用-dfc4`　[non_dominant]
- 原句：吃穿用玩樣樣俱全，
- 譯文：Everything is available for eating, dressing, using, and playing.
- judge 選：`04017401` 利用特定對象的特定功能。　信心 0.90　依據：整句在說事物可被用於特定功能
- gold：`04017411` 特定事物所預期發揮的功能。

**389. 就**　`wsd-就-57f9`　[non_dominant]
- 原句：夜市裡最吸引人的地方就是商品的價錢比一般商店或百貨公司的東西便宜的多，
- 譯文：The most attractive thing about night markets is that the prices of goods are much cheaper than those in general stores or department stores.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：「就」在此表「在夜市的情況下」為價格便宜的充分條件
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**394. 空**　`wsd-空-3ec9`　[non_dominant]
- 原句：２．胃酸排空時間檢查。
- 譯文：Gastric emptying time examination.
- judge 選：`06517306` 形容可被填充的空間不具有填充物。　信心 0.95　依據：空在此指胃中未被食物填充的空間
- gold：`06517312` 形容比喻特定時段沒有排滿活動。

**395. 帶**　`wsd-帶-d5b9`　[non_dominant]
- 原句：集合是以不帶正負號的整數構成陣列型式，
- 譯文：A set is an array of non-negative integers.
- judge 選：`06791413` 走在前面，引導前進方向。　信心 0.90　依據：整句在說集合由整數陣列構成，帶表引導或構成
- gold：`06791418` 前述對象本身有後述成分存在。

**397. 粗**　`wsd-粗-704b`　[non_dominant]
- 原句：還有幾支粗簽字筆，
- 譯文：There are still a few thick felt-tip pens.
- judge 選：`06711801` 形容條狀物的橫切面的面積大。　信心 0.95　依據：felt-tip pens 的筆桿橫切面面積大
- gold：`06711803` 形容線條的寬度大。

**399. 邊**　`wsd-邊-81c8`　[non_dominant]
- 原句：現在井邊圍上了欄杆，
- 譯文：A railing has been installed around the well.
- judge 選：`06584404` 特定對象與其他鄰界對象交界的地方。　信心 0.95　依據：圍欄圍繞水井，指交界處
- gold：`06584405` 表靠近參考點的地方。

---

成本：822 次呼叫 / 1,288,183 tokens / 201.9s / 快取命中 822
run: `runs\20260821-051506-wsd-e198c1.jsonl`