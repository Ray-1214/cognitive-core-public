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
| judge 回 NONE | 1/400（0%） |
| **可判定** | 399/400（100%） |
| **義項正確率** | **0.699**　[0.653, 0.742] |

## 分層 ⭐ 主結果

| 層 | n（可判定） | 正確 | 正確率 | 95% CI |
| --- | :-: | :-: | :-: | :-: |
| 主流（gold 為最高頻） | 200 | 147 | 0.735 | [0.670, 0.791] |
| 非主流 | 199 | 132 | 0.663 | [0.595, 0.725] |

**兩層之差（主流 − 非主流）**：+7.2pp　95% CI [-1.9, +16.2]pp　p≈0.112

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
| 譯文沒譯出該詞 | 1 | 100%　[0.207, 1.000] | **NONE 正確**，是翻譯的遺漏不是 judge 的錯 |
| 譯文有譯出但 judge 認不出 | 0 | 0%　[0.000, 0.793] | **judge 的問題**，計入 judge 錯誤率 |
| 未分類 | 0 | — | 成因分類呼叫失敗 |

NONE 總數 1／400，已分類 1

---

## (b) 錯誤時模型選了哪個義項 ⭐ 與 CHA-Gen 的銜接

> CHA-Gen 發現「模型偏好主流解讀」。若成立，本專案的錯誤應集中在
> 該詞的最高頻義項那一側。隨機基準為 1/候選數的加權平均。

🔴 **本設計下不適用**（錯誤題數 120）

二元強迫選擇下本指標退化為「錯誤落在非主流層的比例」，是抽樣設計的產物。該研究問題改由兩層正確率之差回答。

二元設計中干擾項恆為「同 lemma 中最高頻的非 gold 義項」，於是
「錯誤中選到最高頻的比例」等於「錯誤有多少落在非主流層」——
那是抽樣設計的產物，不是模型偏好。隨機基準也退化成 0.5。

**該研究問題改由上方的兩層正確率之差回答**：若模型偏好高頻義項，非主流層的錯誤率應系統性較高。

---

## (b2) A/B 位置效應 ⭐ 折進噪音估計

> 二元強迫選擇會有位置啟發式。gold 的位置在**分層內逐題交替**（不是雜湊），
> 所以**點估計不受影響**——但變異數還是進來了：受位置驅動的判定
> 與譯文內容無關，那就是雜訊。

- judge 選 A：211/399 = 0.529　95% CI [0.480, 0.577]　✅ 涵蓋 0.5

| gold 的位置 | n | 正確率 | 95% CI |
| :-: | :-: | :-: | :-: |
| A | 199 | 0.729 | [0.663, 0.786] |
| B | 200 | 0.670 | [0.602, 0.731] |

兩位置之差 **+5.86pp**　SE 4.58pp　z=1.28　p=0.2006　95% CI [-3.1, +14.8]pp

**不顯著——報告但不過度解讀。**

### 換算成標籤噪音

設 judge 以機率 *q* 直接依位置作答（不看內容），其餘依內容判斷：

```
gold 在 A：正確率 = q·1 + (1−q)·a
gold 在 B：正確率 = q·0 + (1−q)·a
兩者之差 = q
```

配平下位置驅動的判定有一半落在錯的那邊，故它對標籤錯誤率的貢獻是 **q/2 = 2.9pp**（95% CI [0.0, 7.4]pp）。

⚠️ 配平使**點估計**不受影響，但位置效應**計入 judge 不可靠度**。
這是 judge 噪音的**下界**——內容判斷本身還會再錯。
在人工驗證回來之前，它是唯一有實證基礎的噪音估計，
已餵給 `auc.required_auc(noise=…)`（見 `signals_all.md`）。

---

## (c) 長度稽核

> 問「答錯的題目句子是否較長」。分層報告——聚合值會正負相消
> （CHA-Gen 18 組中 12 組顯著、方向相反，中位數卻是 0.490）。
> 此處 `ambiguity_type` 欄位承載的是 stratum。


> 一次跑 65 格，α=0.05 之下光靠運氣就會有 3 格顯著，故並列 Holm 校正後的 p。
> 五個長度特徵彼此高度相關（單句探針上 probe_span == full_input，且「詞數估計」是字元數的單調函數，
> AUC 只看排序故三者必然同值），所以要看的是有幾個**分層**出現效果，不是有幾格。

| 分層 | 特徵 | n（錯／對） | AUC | SE | 95% CI | 效應量 | 方向 | 排除 0.5 | Holm p |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 整體 | probe_span 字元數 | 120／279 | 0.517 | 0.032 | [0.455, 0.579] | 0.017 | 選錯者較長 | — | 1.000 |
| 整體 | full_input 字元數 | 120／279 | 0.517 | 0.032 | [0.455, 0.579] | 0.017 | 選錯者較長 | — | 1.000 |
| 整體 | probe_span 詞數估計 | 120／279 | 0.517 | 0.032 | [0.455, 0.579] | 0.017 | 選錯者較長 | — | 1.000 |
| 整體 | probe_span 標點數 | 120／279 | 0.505 | 0.032 | [0.443, 0.567] | 0.005 | 選錯者較長 | — | 1.000 |
| 整體 | context 字元數 | 120／279 | 0.500 | 0.032 | [0.438, 0.562] | 0.000 | — | — | 1.000 |
| target_word=歲 | probe_span 字元數 | 7／8 | 0.705 | 0.140 | [0.431, 0.979] | 0.205 | 選錯者較長 | — | 1.000 |
| target_word=歲 | full_input 字元數 | 7／8 | 0.705 | 0.140 | [0.431, 0.979] | 0.205 | 選錯者較長 | — | 1.000 |
| target_word=歲 | probe_span 詞數估計 | 7／8 | 0.705 | 0.140 | [0.431, 0.979] | 0.205 | 選錯者較長 | — | 1.000 |
| target_word=條 | probe_span 字元數 | 6／9 | 0.694 | 0.146 | [0.408, 0.981] | 0.194 | 選錯者較長 | — | 1.000 |
| target_word=條 | full_input 字元數 | 6／9 | 0.694 | 0.146 | [0.408, 0.981] | 0.194 | 選錯者較長 | — | 1.000 |
| target_word=條 | probe_span 詞數估計 | 6／9 | 0.694 | 0.146 | [0.408, 0.981] | 0.194 | 選錯者較長 | — | 1.000 |
| target_word=空 | probe_span 標點數 | 3／4 | 0.375 | 0.225 | [0.000, 0.816] | 0.125 | 選對者較長 | — | 1.000 |
| target_word=帶 | probe_span 字元數 | 4／5 | 0.400 | 0.198 | [0.012, 0.788] | 0.100 | 選對者較長 | — | 1.000 |
| target_word=帶 | full_input 字元數 | 4／5 | 0.400 | 0.198 | [0.012, 0.788] | 0.100 | 選對者較長 | — | 1.000 |
| target_word=帶 | probe_span 詞數估計 | 4／5 | 0.400 | 0.198 | [0.012, 0.788] | 0.100 | 選對者較長 | — | 1.000 |
| target_word=上 | probe_span 標點數 | 5／6 | 0.583 | 0.180 | [0.230, 0.937] | 0.083 | 選錯者較長 | — | 1.000 |
| target_word=條 | probe_span 標點數 | 6／9 | 0.583 | 0.156 | [0.277, 0.889] | 0.083 | 選錯者較長 | — | 1.000 |
| target_word=就 | probe_span 字元數 | 4／6 | 0.417 | 0.190 | [0.044, 0.790] | 0.083 | 選對者較長 | — | 1.000 |
| target_word=就 | full_input 字元數 | 4／6 | 0.417 | 0.190 | [0.044, 0.790] | 0.083 | 選對者較長 | — | 1.000 |
| target_word=就 | probe_span 詞數估計 | 4／6 | 0.417 | 0.190 | [0.044, 0.790] | 0.083 | 選對者較長 | — | 1.000 |
| target_word=中 | probe_span 字元數 | 7／17 | 0.576 | 0.133 | [0.315, 0.837] | 0.076 | 選錯者較長 | — | 1.000 |
| target_word=中 | full_input 字元數 | 7／17 | 0.576 | 0.133 | [0.315, 0.837] | 0.076 | 選錯者較長 | — | 1.000 |
| target_word=中 | probe_span 詞數估計 | 7／17 | 0.576 | 0.133 | [0.315, 0.837] | 0.076 | 選錯者較長 | — | 1.000 |
| target_word=大 | probe_span 字元數 | 3／6 | 0.444 | 0.211 | [0.030, 0.858] | 0.056 | 選對者較長 | — | 1.000 |
| target_word=大 | full_input 字元數 | 3／6 | 0.444 | 0.211 | [0.030, 0.858] | 0.056 | 選對者較長 | — | 1.000 |
| target_word=大 | probe_span 詞數估計 | 3／6 | 0.444 | 0.211 | [0.030, 0.858] | 0.056 | 選對者較長 | — | 1.000 |
| target_word=去 | probe_span 字元數 | 7／12 | 0.446 | 0.139 | [0.175, 0.718] | 0.054 | 選對者較長 | — | 1.000 |
| target_word=去 | full_input 字元數 | 7／12 | 0.446 | 0.139 | [0.175, 0.718] | 0.054 | 選對者較長 | — | 1.000 |
| target_word=去 | probe_span 詞數估計 | 7／12 | 0.446 | 0.139 | [0.175, 0.718] | 0.054 | 選對者較長 | — | 1.000 |
| target_word=分 | probe_span 字元數 | 5／4 | 0.550 | 0.202 | [0.154, 0.946] | 0.050 | 選錯者較長 | — | 1.000 |
| target_word=分 | full_input 字元數 | 5／4 | 0.550 | 0.202 | [0.154, 0.946] | 0.050 | 選錯者較長 | — | 1.000 |
| target_word=分 | probe_span 詞數估計 | 5／4 | 0.550 | 0.202 | [0.154, 0.946] | 0.050 | 選錯者較長 | — | 1.000 |
| target_word=中 | probe_span 標點數 | 7／17 | 0.542 | 0.133 | [0.281, 0.803] | 0.042 | 選錯者較長 | — | 1.000 |
| target_word=去 | probe_span 標點數 | 7／12 | 0.542 | 0.141 | [0.265, 0.819] | 0.042 | 選錯者較長 | — | 1.000 |
| target_word=空 | probe_span 字元數 | 3／4 | 0.542 | 0.236 | [0.080, 1.000] | 0.042 | 選錯者較長 | — | 1.000 |
| target_word=空 | full_input 字元數 | 3／4 | 0.542 | 0.236 | [0.080, 1.000] | 0.042 | 選錯者較長 | — | 1.000 |
| target_word=空 | probe_span 詞數估計 | 3／4 | 0.542 | 0.236 | [0.080, 1.000] | 0.042 | 選錯者較長 | — | 1.000 |
| ambiguity_type=non_dominant | probe_span 字元數 | 67／132 | 0.525 | 0.044 | [0.440, 0.611] | 0.025 | 選錯者較長 | — | 1.000 |
| ambiguity_type=non_dominant | full_input 字元數 | 67／132 | 0.525 | 0.044 | [0.440, 0.611] | 0.025 | 選錯者較長 | — | 1.000 |
| ambiguity_type=non_dominant | probe_span 詞數估計 | 67／132 | 0.525 | 0.044 | [0.440, 0.611] | 0.025 | 選錯者較長 | — | 1.000 |
| target_word=上 | probe_span 字元數 | 5／6 | 0.517 | 0.183 | [0.159, 0.875] | 0.017 | 選錯者較長 | — | 1.000 |
| target_word=上 | full_input 字元數 | 5／6 | 0.517 | 0.183 | [0.159, 0.875] | 0.017 | 選錯者較長 | — | 1.000 |
| target_word=上 | probe_span 詞數估計 | 5／6 | 0.517 | 0.183 | [0.159, 0.875] | 0.017 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | probe_span 字元數 | 53／147 | 0.506 | 0.046 | [0.415, 0.597] | 0.006 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | full_input 字元數 | 53／147 | 0.506 | 0.046 | [0.415, 0.597] | 0.006 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | probe_span 詞數估計 | 53／147 | 0.506 | 0.046 | [0.415, 0.597] | 0.006 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | probe_span 標點數 | 53／147 | 0.505 | 0.046 | [0.414, 0.596] | 0.005 | 選錯者較長 | — | 1.000 |
| ambiguity_type=non_dominant | probe_span 標點數 | 67／132 | 0.503 | 0.043 | [0.418, 0.588] | 0.003 | 選錯者較長 | — | 1.000 |
| ambiguity_type=dominant | context 字元數 | 53／147 | 0.500 | 0.046 | [0.409, 0.591] | 0.000 | — | — | 1.000 |
| ambiguity_type=non_dominant | context 字元數 | 67／132 | 0.500 | 0.043 | [0.415, 0.585] | 0.000 | — | — | 1.000 |
| target_word=上 | context 字元數 | 5／6 | 0.500 | 0.183 | [0.142, 0.858] | 0.000 | — | — | 1.000 |
| target_word=中 | context 字元數 | 7／17 | 0.500 | 0.132 | [0.241, 0.759] | 0.000 | — | — | 1.000 |
| target_word=分 | context 字元數 | 5／4 | 0.500 | 0.204 | [0.100, 0.900] | 0.000 | — | — | 1.000 |
| target_word=分 | probe_span 標點數 | 5／4 | 0.500 | 0.204 | [0.100, 0.900] | 0.000 | — | — | 1.000 |
| target_word=去 | context 字元數 | 7／12 | 0.500 | 0.141 | [0.224, 0.776] | 0.000 | — | — | 1.000 |
| target_word=大 | context 字元數 | 3／6 | 0.500 | 0.215 | [0.078, 0.922] | 0.000 | — | — | 1.000 |
| target_word=大 | probe_span 標點數 | 3／6 | 0.500 | 0.215 | [0.078, 0.922] | 0.000 | — | — | 1.000 |
| target_word=就 | context 字元數 | 4／6 | 0.500 | 0.195 | [0.117, 0.883] | 0.000 | — | — | 1.000 |
| target_word=就 | probe_span 標點數 | 4／6 | 0.500 | 0.195 | [0.117, 0.883] | 0.000 | — | — | 1.000 |
| target_word=帶 | context 字元數 | 4／5 | 0.500 | 0.204 | [0.100, 0.900] | 0.000 | — | — | 1.000 |
| target_word=帶 | probe_span 標點數 | 4／5 | 0.500 | 0.204 | [0.100, 0.900] | 0.000 | — | — | 1.000 |
| target_word=條 | context 字元數 | 6／9 | 0.500 | 0.157 | [0.192, 0.808] | 0.000 | — | — | 1.000 |
| target_word=歲 | context 字元數 | 7／8 | 0.500 | 0.154 | [0.198, 0.802] | 0.000 | — | — | 1.000 |
| target_word=歲 | probe_span 標點數 | 7／8 | 0.500 | 0.154 | [0.198, 0.802] | 0.000 | — | — | 1.000 |
| target_word=空 | context 字元數 | 3／4 | 0.500 | 0.236 | [0.038, 0.962] | 0.000 | — | — | 1.000 |

**未校正 CI 排除 0.5：0 / 65 格，落在 0 個分層**
**Holm 校正後仍顯著：0 格**

沒有任何分層的長度特徵能顯著預測選錯。

---

## 逐筆（請掃一遍判斷 judge 合不合理）

| # | 詞 | 原句 | 譯文 | judge 選的 | gold | 對 |
| :-: | :-: | --- | --- | --- | --- | :-: |
| 1 | 包 | 以一包Ａ４大小、內含20張的相片紙建議售價為從240 | A pack of A4-sized photo paper containing 20 sheets  | `05095711` | `05095711` | ✅ |
| 2 | 歲 | 今年才五十歲， | He's only fifty this year. | `06559405` | `06559405` | ✅ |
| 3 | 帶 | 就能帶個女孩回來。 | You can bring a girl back. | `06791407` | `06791407` | ✅ |
| 4 | 死 | 可能這是你對我抱的至死不變的看法， | Perhaps this is the unchanging view you hold of me. | `05035201` | `05035202` | ❌ |
| 5 | 熱 | 疑似運作過熱起火燃燒， | It appears to have overheated and caught fire. | `05228701` | `05228701` | ✅ |
| 6 | 回 | 每天晚上她回乘務隊的時候， | Every night when she returns to the duty team. | `03019001` | `03019001` | ✅ |
| 7 | 空 | 這是唯識講『空』的不同處。 | This is the unique approach of the Yogācāra school i | `06517331` | `06517331` | ✅ |
| 8 | 叫 | 鍾木郎叫人看守人質， | YUI ordered the guards to watch over the hostages. | `05013801` | `05013801` | ✅ |
| 9 | 道 | 卻聽得其中白眉和尚哈哈一笑道： | Then the white-browed monk burst into laughter and s | `05239501` | `05239501` | ✅ |
| 10 | 拍 | 希望能多拍些劇情片。 | I hope we can make more narrative films. | `08028004` | `08028004` | ✅ |
| 11 | 中 | 讀者可由表中清楚看出， | Readers can clearly see from the table. | `04004605` | `04004605` | ✅ |
| 12 | 頭 | 頭上還要綁布條， | You still have to tie a headband. | `03043001` | `03043001` | ✅ |
| 13 | 分 | 三分天下。 | A tripartite division of the world. | `04146403` | `04146403` | ✅ |
| 14 | 畫 | 每幅畫都很不錯， | Every painting is excellent. | `06550302` | `06550302` | ✅ |
| 15 | 包 | 但依慣例只拿了幾包藥後回家養病。 | But as usual, he only took a few packs of medicine a | `05095711` | `05095711` | ✅ |
| 16 | 心 | 只有母親能真正了解我心中的感受， | Only a mother can truly understand the feelings in m | `05231612` | `05231612` | ✅ |
| 17 | 小 | 再把芒果切成一小片， | Then cut the mango into small pieces. | `05227101` | `05227101` | ✅ |
| 18 | 分 | 顯示中共有意分階段解決問題， | The Chinese government has indicated its intention t | `04146403` | `04146403` | ✅ |
| 19 | 去 | 本來要下樓去買幾包速食麵， | I was about to go downstairs to buy a few packs of i | `06559201` | `06559205` | ❌ |
| 20 | 口 | 口吐白沫， | Foaming at the mouth. | `04084201` | `04084201` | ✅ |
| 21 | 掛 | 比如今八三歲父親至今還掛在牆上親自題著「音容宛在」的 | An elderly father, now eighty-three years old, still | `06701401` | `06701401` | ✅ |
| 22 | 投 | 並非自己投了自己的。 | I didn't vote for myself. | `06685709` | `06685709` | ✅ |
| 23 | 下 | 在共黨獨裁政權下產生的文學作品， | Literary works produced under a communist dictatorsh | `04081817` | `04081817` | ✅ |
| 24 | 心 | 心中非常不甘願， | I am very reluctant. | `05231612` | `05231612` | ✅ |
| 25 | 歲 | 不具高所得或高不動產的六十五歲以上老人， | Elderly individuals aged 65 or above who do not poss | `06559405` | `06559405` | ✅ |
| 26 | 歲 | 前總統李登輝七十八歲高齡， | Taiwan's former President Lee Teng-hui passed away a | `06559404` | `06559405` | ❌ |
| 27 | 去 | 你先去預備圖章， | Please prepare the seal first. | `06559205` | `06559205` | ✅ |
| 28 | 發 | 象、獅隊球團發獎金也不手軟， | The Elephants and Lions team's management is generou | `06724101` | `06724101` | ✅ |
| 29 | 吃 | Ｗｉｎｓｔｏｎ告訴我們無論如何也要買隻大螃蟹吃才不虛 | Winston told us we absolutely have to buy a big crab | `05227001` | `05227001` | ✅ |
| 30 | 歲 | 是我那個七十一歲的外婆和小外公吵著要離婚， | My seventy-one-year-old grandmother and grandfather  | `06559404` | `06559405` | ❌ |
| 31 | 低 | 創下八十六年以來同季首度滑落千億元以下的最低紀錄。 | For the first time in 86 years, it has fallen below  | `06748406` | `06748406` | ✅ |
| 32 | 歲 | 你不能要求兩歲的小孩， | You cannot expect a two-year-old child to do that. | `06559405` | `06559405` | ✅ |
| 33 | 拉 | 拉著大書包走下車， | I pulled my large backpack off the bus. | `05230801` | `05230801` | ✅ |
| 34 | 中 | Ｂｏｙｅｒ－Ｍｏｏｒｅ的方法是所有已知的字串比對方法 | The Boyer-Moore method is the fastest among all know | `04004605` | `04004605` | ✅ |
| 35 | 回 | 黑派理應回座維持會務， | Black factions should return to their seats to maint | `03019001` | `03019001` | ✅ |
| 36 | 邊 | 眼見一群男孩子就守在河邊， | A group of boys was seen standing by the river. | `06584406` | `06584404` | ❌ |
| 37 | 明 | 第四繼承時期是五代至明末。 | The Fourth Inheritance Period spans from the Five Dy | `07003502` | `07003501` | ❌ |
| 38 | 層 | 表演者自十層樓一躍而下， | The performer leapt to his death from the tenth floo | `03005002` | `03005002` | ✅ |
| 39 | 前 | 三年前因為突然呼吸困難及全身不舒服， | Three years ago, I suddenly experienced difficulty b | `03033712` | `03033712` | ✅ |
| 40 | 點 | 同時在四三００至四七００點間採行箱型操作， | Box operations are conducted between 4300 and 4700 p | `04043808` | `04043808` | ✅ |
| 41 | 歲 | 今年整整滿一百歲了。 | This year marks exactly one hundred years old. | `06559405` | `06559405` | ✅ |
| 42 | 好 | 「下半場上來的那名後衛很好！ | The defender who came on in the second half played r | `04157701` | `04157701` | ✅ |
| 43 | 坐 | 反不若坐在家中，等待政黨比例代表制下的提名， | It would be better to stay at home and wait for a no | `05223903` | `05223901` | ❌ |
| 44 | 去 | 以及親手去使用這些資料。 | And personally use this data. | `06559205` | `06559205` | ✅ |
| 45 | 坐 | 他習慣坐在客運公司走廊一角， | He was used to sitting in a corner of the corridor a | `05223901` | `05223901` | ✅ |
| 46 | 上 | 多媒體在網路上的應用確實擁有無限發展潛力， | Multimedia applications on the internet indeed have  | `04081314` | `04081314` | ✅ |
| 47 | 場 | 國王明星大前鋒韋伯則攻下全隊最高的21分以及本季個人 | King star power forward Webber scored a team-high 21 | `06721710` | `06721709` | ❌ |
| 48 | 歲 | 四十五歲的臺北水準書局老闆曾大福搭朋友的車南下， | The 45-year-old owner of Taipei Shuei-shui Bookstore | `06559405` | `06559405` | ✅ |
| 49 | 折 | 打七五折是四百六十五。 | The 25% discount makes it four hundred sixty-five. | `07033113` | `07033113` | ✅ |
| 50 | 面 | 難道那不是人生真實的一面？ | Isn't that just one aspect of life's reality? | `03028804` | `03028804` | ✅ |
| 51 | 拉 | 他整天拉著鞋， | He drags his shoes all day. | `05230801` | `05230801` | ✅ |
| 52 | 歲 | 看到一位七十幾歲的老先生， | I saw an elderly gentleman in his seventies. | `06559404` | `06559405` | ❌ |
| 53 | 拉 | 是將台灣拉向一個被強勢文化（好萊塢）同質化的下場， | It would lead Taiwan down the path of being homogeni | `05230801` | `05230801` | ✅ |
| 54 | 中 | 但是這並不代表婦女在家中的責任減輕了。 | But this does not mean that women's responsibilities | `04004605` | `04004605` | ✅ |
| 55 | 會 | 約在１０﹣１２天大時會出現銅離子負平衡， | Around 10–12 days old, copper ion negative balance m | `04143405` | `04143405` | ✅ |
| 56 | 頭 | 做出一個大小適中的頭， | Make a head of moderate size. | `03043001` | `03043001` | ✅ |
| 57 | 畫 | 如果用來記錄美術館的畫， | The system is used to record paintings in an art mus | `06550302` | `06550302` | ✅ |
| 58 | 歲 | 共有兩百位八十歲以上的壽星在家人的陪同下， | A total of two hundred centenarians, accompanied by  | `06559404` | `06559405` | ❌ |
| 59 | 心 | 心裡很不是滋味。 | I feel a bit upset inside. | `05231612` | `05231612` | ✅ |
| 60 | 去 | 準備挑到城裡去賣。 | I'm going to take them to town to sell. | `06559201` | `06559205` | ❌ |
| 61 | 新 | 與近千位新舊政府團隊和工商界的共同見證下， | Under the joint witness of nearly a thousand members | `05237904` | `05237904` | ✅ |
| 62 | 空 | 最後一幕『菩提』代表著『空』， | The final scene "Bodhi" represents "Emptiness." | `06517332` | `06517331` | ❌ |
| 63 | 坐 | 凱洛琳在一個油鍋前坐著， | Caroline was sitting in front of a vat of boiling oi | `05223901` | `05223901` | ✅ |
| 64 | 拉 | 還是每天拉著那輛三輪車沿街拾荒， | I still pull that tricycle around the streets every  | `05230801` | `05230801` | ✅ |
| 65 | 言 | 就前者而言， | In this regard, | `06008201` | `06008204` | ❌ |
| 66 | 歲 | 一個在三十歲之前沒有成為社會主義信徒的人， | A person who hasn't become a socialist before the ag | `06559404` | `06559405` | ❌ |
| 67 | 帶 | 事後我帶他回南部老家見父母， | Afterward, I took him back to my hometown in souther | `06791406` | `06791407` | ❌ |
| 68 | 抽 | 又抽大麻睡著了， | I smoked weed and fell asleep again. | `06598612` | `06598614` | ❌ |
| 69 | 歲 | 今年八十歲的王自牧， | Eighty-year-old Wang Tzu-mu this year | `06559404` | `06559405` | ❌ |
| 70 | 股 | 首季每股稅後盈餘約○．八元。 | The after-tax earnings per share for the first quart | `03015702` | `03015710` | ❌ |
| 71 | 做 | 也乾脆放下生意不做， | Just give up on the business altogether. | `06664306` | `06664306` | ✅ |
| 72 | 來 | 但嚴格來說銀行業的壞帳比票券業更難計算， | But strictly speaking, bad debts in the banking indu | `04086501` | `04086509` | ❌ |
| 73 | 明 | 就好像在濃霧中遇到一盞明燈一樣。 | It was like encountering a bright beacon in the thic | `06685411` | `06685401` | ❌ |
| 74 | 中 | 在ＩＰ通訊協定中， | In IP communication protocols, | `04004605` | `04004605` | ✅ |
| 75 | 強 | 當海水清澈、陽光穿透力強的時候， | When the sea is clear and the sunlight penetrates st | `09250306` | `09250303` | ❌ |
| 76 | 吃 | 有純樸簡單碼頭、熱鬧大船小舟、傳統市集、酒吧各式吃喝 | A quaint and simple dock, bustling with boats of all | `05227001` | `05227001` | ✅ |
| 77 | 吃 | 便和同學偷溜跑去吃刨冰， | My friends and I sneaked out to have shaved ice. | `05227001` | `05227001` | ✅ |
| 78 | 中 | 不必再侷限於那三類網路位址結構中， | You no longer need to be confined to those three typ | `04004605` | `04004605` | ✅ |
| 79 | 上 | 就把媽祖在海上顯靈的事蹟， | Mazu's miraculous manifestations at sea | `04081314` | `04081314` | ✅ |
| 80 | 叫 | 出現一個叫永窮的窮小子， | A poor young man named Yongqiong appeared. | `04010206` | `04010206` | ✅ |
| 81 | 吃 | 知了喜歡吃樹葉、露水， | Cicadas like to eat tree leaves and dew. | `05227001` | `05227001` | ✅ |
| 82 | 股 | 中華電週二公布今年每股純益目標為四．一六元， | Taiwan Mobile announced on Tuesday that its target f | `03015702` | `03015710` | ❌ |
| 83 | 間 | 省能產品也成為未來國際間的最大商機， | Energy-efficient products are also becoming the bigg | `04084103` | `04084104` | ❌ |
| 84 | 歲 | 當場查獲釣蝦場女會計蔡雅惠（廿歲， | A female accountant, Tsai Ya-hui (20 years old), was | `06559405` | `06559405` | ✅ |
| 85 | 歲 | 因為我30歲， | Because I'm 30 years old. | `06559405` | `06559405` | ✅ |
| 86 | 中 | 中菲國會議員友好協會會長。 | The Chairperson of the Philippines-Taiwan Inter-Parl | `08011203` | `08011203` | ✅ |
| 87 | 做 | 為什麼日本人要這麼做？ | Why do the Japanese do this? | `06664306` | `06664306` | ✅ |
| 88 | 去 | 並非去抗議。 | It's not about going to protest. | `06559201` | `06559205` | ❌ |
| 89 | 去 | 試著去接近森林， | Try to approach the forest. | `06559201` | `06559205` | ❌ |
| 90 | 日 | 以實品文物、各國服飾、鈔票特區及影像展呈現出日、韓、 | The exhibition showcases the charm of Japan, South K | `05239901` | `05239901` | ✅ |
| 91 | 低 | 我國以女性為戶長的單親家庭比例（７１７６％）較歐美低 | The proportion of single-parent households headed by | `06748406` | `06748406` | ✅ |
| 92 | 拍 | 一走紅大家都搶著找她拍， | Once she became popular, everyone scrambled to colla | `08028003` | `08028004` | ❌ |
| 93 | 度 | 在澳洲風景明媚的海灘度了兩天假之後， | After spending two days of vacation at the scenic be | `06785402` | `06785402` | ✅ |
| 94 | 吃 | 只要有一餐吃得太放肆， | You can only indulge in one meal too extravagantly. | `05227001` | `05227001` | ✅ |
| 95 | 真 | 真是惡名昭彰的傢伙。 | What a notorious guy. | `05100414` | `05100413` | ❌ |
| 96 | 新 | 並同時實施新的審查制度； | At the same time, a new censorship system was implem | `05237901` | `05237904` | ❌ |
| 97 | 包 | 臨走時帶包來自天津１８街桂發祥的麻花， | Bring some twisted crullers from Tianjin's 18th Stre | `05095711` | `05095711` | ✅ |
| 98 | 去 | 去住旅館好了！ | Let's just stay at a hotel! | `06559201` | `06559205` | ❌ |
| 99 | 約 | 約她一起去附近的商店買下星期的吃食。 | Invite her to go to a nearby store to buy food for n | `05052303` | `05052303` | ✅ |
| 100 | 季 | 亞洲出口成長仍於二○○一年第四季反彈回升。 | Asia's export growth rebounded in the fourth quarter | `07026505` | `07026505` | ✅ |
| 101 | 分 | 還讓他發現自己真有幾分語言天份。 | It also allowed him to discover that he actually had | `05007209` | `05007209` | ✅ |
| 102 | 小 | 以小動物來作試驗， | Animal testing should be conducted. | `05227101` | `05227101` | ✅ |
| 103 | 發 | 每位候選人總是發一大堆傳單， | Every candidate always distributes a large number of | `06724101` | `06724101` | ✅ |
| 104 | 大 | 年紀輕輕的就擔負這麼大的責任， | At such a young age, you're taking on such great res | `05227204` | `05227204` | ✅ |
| 105 | 帶 | 或帶小孩郊遊。 | Go on a picnic with children. | `06791406` | `06791407` | ❌ |
| 106 | 部 | 那是漫長的一部曲折而辛酸的歷史。 | That was a long, convoluted, and bitter history. | `05075710` | `05075710` | ✅ |
| 107 | 高 | 台大最高， | National Taiwan University is the best. | `06010615` | `06010610` | ❌ |
| 108 | 上 | 街頭上到處也可以看到咖啡店． | You can see coffee shops everywhere on the streets. | `04081314` | `04081314` | ✅ |
| 109 | 折 | 軍警票改為八折優待， | Military and police tickets are now discounted to 80 | `07033113` | `07033113` | ✅ |
| 110 | 起 | 報名自即日起受理， | Registration is now open. | `04004806` | `04004801` | ❌ |
| 111 | 中 | 恍恍惚惚腦中忽然瞥過過去她那激憤壯烈的夢。 | A fleeting image of her passionate and heroic dream  | `04004618` | `04004605` | ❌ |
| 112 | 說 | 他已說過很多遍， | He has said it many times. | `05212401` | `05212401` | ✅ |
| 113 | 大 | 小問題大煩惱資料漏失時的處理．何鴻毅問： | When data is lost, how should it be handled? Mr. He  | `05227204` | `05227204` | ✅ |
| 114 | 條 | 他還是執意走上這條不歸路， | He is still determined to take this irreversible pat | `06585924` | `06585924` | ✅ |
| 115 | 做 | 他也把我們的垃圾做分類， | He also sorts our trash for recycling. | `06664306` | `06664306` | ✅ |
| 116 | 好 | 做個好女兒， | Be a good daughter. | `04157701` | `04157701` | ✅ |
| 117 | 說 | 陳總統說去年三一八事件今年可能重演； | President Chen said that the March 18 incident last  | `05212401` | `05212401` | ✅ |
| 118 | 中 | 第一票不能改變各政黨在國會中的席次比。 | The first vote does not change the seat distribution | `04004605` | `04004605` | ✅ |
| 119 | 言 | 而所謂的新指甲可能也是指在老指甲下方的油脂指床而言。 | The so-called new nail may also refer to the fatty n | `06008201` | `06008204` | ❌ |
| 120 | 吃 | 年年拼死吃， | I make it a point to savor every moment of life to t | `05227001` | `05227001` | ✅ |
| 121 | 小 | 微細世界．小貓咪和貓熊一樣， | The tiny world is such that even a kitten is as ador | `05227101` | `05227101` | ✅ |
| 122 | 條 | 要走哪條路呢？ | Which path should we take? | `06585924` | `06585924` | ✅ |
| 123 | 條 | 便可堆出一條筆直的高級公路。 | A straight, high-quality highway can be built this w | `06585906` | `06585924` | ❌ |
| 124 | 去 | 不必去當兵， | You don't have to enlist in the military. | `06559205` | `06559205` | ✅ |
| 125 | 季 | 第二季半導體景氣及公司業績可望觸底， | The semiconductor market outlook and company perform | `07026505` | `07026505` | ✅ |
| 126 | 層 | 地下三層）與緊鄰也將接著完工的資訊大樓， | The basement level three and the adjacent Informatio | `03005002` | `03005002` | ✅ |
| 127 | 吃 | 冰淇淋只好給弟弟吃啦！ | Ice cream can only be given to little brother to eat | `05227001` | `05227001` | ✅ |
| 128 | 拿 | 我都拿體重計為小豬們檢查身體， | I always use the scale to check the little pigs' wei | `04011201` | `04011201` | ✅ |
| 129 | 明 | 明起路邊停車巡場管理員將不再受理民眾繳交停車費， | Starting tomorrow, roadside parking patrol officers  | `07003401` | `07003401` | ✅ |
| 130 | 度 | 第四度獲奧斯卡提名。 | He received his fourth Oscar nomination. | `05147620` | `05147620` | ✅ |
| 131 | 中 | 每家主婦都率領家中的婦女， | Every housewife leads the women in her household. | `04004605` | `04004605` | ✅ |
| 132 | 使 | 使我們變得很有禮貌。 | Let us become very polite. | `06560201` | `06560202` | ❌ |
| 133 | 中 | 在佛法中所謂的經濟， | In Buddhist teachings, what is referred to as "econo | `04004605` | `04004605` | ✅ |
| 134 | 上 | 林青霞也在記者會上感動的表示， | Yvonne Yung also emotionally expressed at the press  | `04081317` | `04081314` | ❌ |
| 135 | 行 | 父母就希望你只要書念好就行了。 | Parents just hope that you do well in your studies. | `06775704` | `06775711` | ❌ |
| 136 | 點 | 以佔指數較重之金融股搶攻４９００點， | Financial stocks, which carry significant weight in  | `04043808` | `04043808` | ✅ |
| 137 | 拍 | 拍那個終極保鏢的時候。 | When they were filming that ultimate bodyguard. | `08028003` | `08028004` | ❌ |
| 138 | 小 | 身長卻還只是２公分那麼小呢！ | It's still only 2 centimeters tall! | `05227101` | `05227101` | ✅ |
| 139 | 還 | 但應該還會再等幾個月， | But we should still wait for a few more months. | `05002703` | `05002703` | ✅ |
| 140 | 畫 | 在絹布上做畫。 | Painting on silk fabric. | `06550302` | `06550302` | ✅ |
| 141 | 拍 | 輕輕拍了他一下， | He gave him a gentle pat. | `08027901` | `08027901` | ✅ |
| 142 | 大 | 合成一股大力量呢？ | What if we combine into one great force? | `05227204` | `05227204` | ✅ |
| 143 | 場 | 往年常常因為某一場球賽的比賽地點、時間無法達成共識， | In previous years, it was often difficult to reach a | `06721709` | `06721709` | ✅ |
| 144 | 水 | 而且若長期飲用淡化水， | And if you drink desalinated water for a long time, | `05233801` | `05233801` | ✅ |
| 145 | 坐 | 坐在矮牆上望著大海抽菸， | Sitting on a low wall, smoking while gazing at the s | `05223901` | `05223901` | ✅ |
| 146 | 回 | 預計七月結婚的郭思宏利用寒假專程由美國回臺灣與女友拍 | Edward Kuo, who plans to get married in July, specia | `03019001` | `03019001` | ✅ |
| 147 | 錢 | 但偏偏卻有很多人願把錢送入虎口， | But for some reason, many people are still willing t | `06015105` | `06015105` | ✅ |
| 148 | 中 | 多位教授昨天在澄社主辦的座談會中， | Several professors attended a symposium hosted by th | `04004605` | `04004605` | ✅ |
| 149 | 收 | 我們不收支票。 | We do not accept checks. | `03039303` | `03039303` | ✅ |
| 150 | 粗 | 英勇的消防隊員合力舉起又粗又大的水管， | Brave firefighters worked together to lift the thick | `06711803` | `06711801` | ❌ |
| 151 | 小 | 甚至滿園成千上萬的小花， | Even the entire garden is filled with thousands upon | `05227101` | `05227101` | ✅ |
| 152 | 中 | 在上次吸吮一章中， | In the previous "Sucking" chapter, | `04004605` | `04004605` | ✅ |
| 153 | 度 | 他們繼續在自己生活的地方和工作崗位度信仰的生活。 | They continued to live out their faith in their own  | `06785402` | `06785402` | ✅ |
| 154 | 日 | 經驗上可能在三日內出現天價， | Experience-wise, it's possible that exorbitant price | `03036209` | `03036209` | ✅ |
| 155 | 中 | 主要乃因在如此萎縮的成交量中， | Amid such shrinking transaction volumes, | `04004618` | `04004605` | ❌ |
| 156 | 空 | 在紅樓二樓右側空教室成立的「網咖」昨日開幕。 | A "net café" was inaugurated yesterday in the vacant | `07114607` | `07114607` | ✅ |
| 157 | 字 | 因為我的所有最字， | All my words. | `06584501` | `06584502` | ❌ |
| 158 | 強 | 她的港裔美籍夫婿區永禧親和力強， | Her Hong Kong-born American husband Au Wing Hei has  | `09250306` | `09250303` | ❌ |
| 159 | 中 | 混合工作負荷中的「自然工作負荷」是在控制條件之下以較 | In mixed workloads, "natural workload" is executed u | `04004618` | `04004605` | ❌ |
| 160 | 會 | 學校通常會開放兩個教室， | Schools usually open two classrooms. | `04143405` | `04143405` | ✅ |
| 161 | 吃 | 家裡吃的麵都是自己做的， | We make all the noodles we eat at home ourselves. | `05227001` | `05227001` | ✅ |
| 162 | 拉 | 連拖帶拉的把豪豪拖到公園去了。 | Dragged Hou Hou to the park, struggling all the way. | `05230801` | `05230801` | ✅ |
| 163 | 度 | 蔣介石總統曾兩度提出亡黨亡國的話， | President Chiang Kai-shek once warned twice of the p | `05147620` | `05147620` | ✅ |
| 164 | 正 | 警方正擴大追查中。 | The police are expanding their investigation. | `07009821` | `07009821` | ✅ |
| 165 | 支 | 而韓國隊卻只有七支。 | However, the South Korean team only has seven. | `03056204` | `03056210` | ❌ |
| 166 | 中 | 六年國建計畫中處處可見為人癌細胞架設的舞台， | In the Six-Year National Construction Plan, stages w | `04004605` | `04004605` | ✅ |
| 167 | 分 | 布朗也只有八點一分， | Brown only has 8.1 points. | `05007101` | `05007102` | ❌ |
| 168 | 帶 | 秋天你帶我來歐洲好嗎？ | Would you like me to take you to Europe in the fall? | `06791406` | `06791407` | ❌ |
| 169 | 死 | 皮皮掉到山谷後居然沒死， | Pipi fell into the valley but surprisingly didn't di | `05035202` | `05035202` | ✅ |
| 170 | 去 | 就可以去做事了。 | You can start working now. | `06559205` | `06559205` | ✅ |
| 171 | 吃 | 其實吃茶去並無深意。 | There is no deep meaning to "Let's go drink tea." | `05227001` | `05227001` | ✅ |
| 172 | 做 | 程一駿也曾前往東沙群島做綠蠵龜分布調查， | Yi-jun Cheng also once traveled to the Dongsha Islan | `06664306` | `06664306` | ✅ |
| 173 | 度 | 璩美鳳首先三度表示， | Fang Mei-Feng first expressed this three times. | `05147620` | `05147620` | ✅ |
| 174 | 正 | 但樓下爸媽正興趣盎然的替她編織未來。 | But the parents downstairs are enthusiastically weav | `07009821` | `07009821` | ✅ |
| 175 | 強 | 她就有很強的自主意識， | She has a strong sense of independence. | `09250306` | `09250303` | ❌ |
| 176 | 坐 | 我坐在書桌前， | I am sitting at my desk. | `05223901` | `05223901` | ✅ |
| 177 | 坐 | 最喜歡坐在岩石上， | I love sitting on rocks. | `05223901` | `05223901` | ✅ |
| 178 | 行 | 當初是怎麼走上這行的﹖ | How did you first get into this line of work? | `05145006` | `05145006` | ✅ |
| 179 | 行 | 我們演習一下就行了， | Let's just practice. | `06775711` | `06775711` | ✅ |
| 180 | 歲 | 趁被害人黃文助（二十九歲， | The victim, Huang Wen-zhu (29 years old), | `06559404` | `06559405` | ❌ |
| 181 | 起 | 台北羽球名人邀請賽八日起在台北勝光羽球館開打， | The Taipei Badminton Invitational Tournament kicks o | `04004801` | `04004801` | ✅ |
| 182 | 深 | 而且更深一層的智慧的發揮。 | And the deeper manifestation of wisdom. | `06663313` | `06663314` | ❌ |
| 183 | 歲 | 都比薛蘋小幾歲， | Sue is a few years younger than Hsieh Pin. | `06559405` | `06559405` | ✅ |
| 184 | 中 | 致潘雙全腹部中一槍。 | A gunshot wound to the abdomen was inflicted on Pan  | `05007603` | `05007601` | ❌ |
| 185 | 長 | 工作負荷必須花長時間來記錄， | Recording workload requires a long time. | `06030803` | `06030803` | ✅ |
| 186 | 死 | 等我什麼時候也死了， | When I die someday. | `05035202` | `05035202` | ✅ |
| 187 | 人 | 有些人批國安聯盟是太上決策機制， | Some people criticize the National Security Council  | `05231101` | `05231101` | ✅ |
| 188 | 頭 | 他說獅子的頭又大又圓， | He said the lion's head is big and round. | `03043001` | `03043001` | ✅ |
| 189 | 叫 | 阿眉叫我不要太擔心她身體。 | A-mei told me not to worry too much about her health | `05013801` | `05013801` | ✅ |
| 190 | 就 | 就造成肥胖症。 | It can lead to obesity. | `05198301` | `05198301` | ✅ |
| 191 | 心 | 以極為艱難的說話方式表達他心中的感想。 | He expressed his thoughts in an extremely difficult  | `05231612` | `05231612` | ✅ |
| 192 | 過 | 而且從未請過教練， | And I have never hired a coach. | `05206001` | `05206001` | ✅ |
| 193 | 吃 | 晚上在北京飯店新樓吃羊肉， | I had lamb at the Beijing Hotel New Building in the  | `05227001` | `05227001` | ✅ |
| 194 | 會 | 沒有一家銀行會故意違反央行規定， | No bank would deliberately violate the central bank' | `04143406` | `04143405` | ❌ |
| 195 | 正 | 正準備開槍， | I was about to pull the trigger. | `07009821` | `07009821` | ✅ |
| 196 | 去 | 我們要去旅行， | We are going to travel. | `06559201` | `06559205` | ❌ |
| 197 | 拍 | 「這部電影是誰拍的？ | Who directed this movie? | `08028004` | `08028004` | ✅ |
| 198 | 畫 | 畫裡人物竟是她夢境中的書生。 | The figure in the painting turned out to be the scho | `06550302` | `06550302` | ✅ |
| 199 | 要 | 沒想到原始人居然要睡到中午才會起來， | Even cavemen had to sleep until noon before getting  | `06636905` | `06636905` | ✅ |
| 200 | 中 | 座中有人提到郝柏村現象， | Someone at the table mentioned the "Hao Bai-cun phen | `04004605` | `04004605` | ✅ |
| 201 | 就 | 這就是「相」很少印在我的心上。 | That is why the "phase" rarely imprints on my heart. | `05198301` | `05198313` | ❌ |
| 202 | 度 | 亦足供七種樣本可將組織保存於液態氮或零下七十度中， | Samples can also be preserved in liquid nitrogen or  | `05147610` | `05147610` | ✅ |
| 203 | 好 | 好漂亮啊！ | That's so beautiful! | `04157710` | `04157710` | ✅ |
| 204 | 作 | 或許這部小說也是明人所作的， | Perhaps this novel was also written by someone from  | `05098103` | `05098103` | ✅ |
| 205 | 小 | 小野豬叫著： | A wild boar is grunting. | `NONE` | `05227107` | — |
| 206 | 小 | 否則浪費金錢事小， | Otherwise, wasting money is a minor issue. | `05227104` | `05227104` | ✅ |
| 207 | 下 | 地球上正下著大雨， | It is raining heavily on Earth right now. | `04081830` | `04081830` | ✅ |
| 208 | 點 | 說得確實點， | Just put it bluntly. | `04043808` | `04043813` | ❌ |
| 209 | 行 | 往北漸行漸遠， | As we head north, we gradually move farther away. | `06775702` | `06775702` | ✅ |
| 210 | 吃 | 「天生我才必有用」、「吃得苦中苦， | "Every person has their own unique value in life."
" | `05227009` | `05227009` | ✅ |
| 211 | 深 | 於圖書事業深有研究或經驗並有專門著作者之規定， | Persons with in-depth research or experience in the  | `06663313` | `06663313` | ✅ |
| 212 | 破 | 當年城破家亡， | The city fell, and our home was lost. | `06761401` | `06761401` | ✅ |
| 213 | 空 | 世俗諦都是假的、該空的； | Secular truths are all false and should be seen as e | `06517332` | `06517332` | ✅ |
| 214 | 花 | 棘皮動物海百合像海中之花般地鮮艷綻放， | Echinoderms like sea lilies bloom brilliantly in the | `05229001` | `05229006` | ❌ |
| 215 | 大 | 竹葉上有一大群螞蟻， | There is a large group of ants on the bamboo leaf. | `05227203` | `05227203` | ✅ |
| 216 | 去 | 走到了最常去最熟悉的圖書館， | I arrived at the library I frequent the most, the on | `06559201` | `06559201` | ✅ |
| 217 | 支 | 由國內四支球隊選出的職棒明星隊負責把守第二關。 | The all-star team composed of four domestic teams wi | `03056204` | `03056204` | ✅ |
| 218 | 強 | 國男組也將進行四強交叉準決賽， | The men's team will also compete in the semifinals w | `09250305` | `09250305` | ✅ |
| 219 | 空 | 是非成敗轉頭空， | Empty are the tides of success and failure when view | `06517332` | `06517332` | ✅ |
| 220 | 條 | 森林之家的每條街道， | Every street in Forest House | `06585924` | `06585906` | ❌ |
| 221 | 平 | 形成追漲殺跌皆乏力的平低震盪盤， | A formation of a flat, low oscillation pattern where | `06025219` | `06025219` | ✅ |
| 222 | 條 | 這條等於不存在， | This statement is equivalent to nonexistence. | `06585929` | `06585929` | ✅ |
| 223 | 高 | 配備精良的美國警方人員在攝影高台上嚴密監視觀眾動態， | Well-equipped U.S. police officers closely monitor t | `06010601` | `06010601` | ✅ |
| 224 | 子 | 而是要人以社會為妻為子， | But instead, people should take society as their wif | `07027901` | `07027901` | ✅ |
| 225 | 部 | 包括二十部保時捷。 | Including twenty Porsche vehicles. | `05075709` | `05075709` | ✅ |
| 226 | 行 | 有兩行特別醒目的大字， | Two lines of particularly eye-catching large charact | `05145004` | `05145004` | ✅ |
| 227 | 吃 | 所有出門的人一定要趕回家來吃年夜飯， | Everyone who goes out must rush home to have the New | `05227024` | `05227024` | ✅ |
| 228 | 格 | 由於十五格圖的四個構面恰好反應出價值鏈不同階段的特性 | The four dimensions of the fifteen-box grid precisel | `06730802` | `06730802` | ✅ |
| 229 | 對 | 但因氣氛及感覺不對， | But since the atmosphere and feeling were off. | `04017503` | `04017503` | ✅ |
| 230 | 破 | 自己發球局反在第六局被破， | I was broken in my own serve game in the sixth set. | `06761422` | `06761422` | ✅ |
| 231 | 法 | 而非國民黨統治機器所貼下標籤的地域區分法‧人們習慣稱 | People are actually accustomed to calling the "ben s | `05045101` | `05045104` | ❌ |
| 232 | 道 | 每一個性方面的需求可能有些人比較好此道， | Everyone has different levels of interest or experti | `06002401` | `06002402` | ❌ |
| 233 | 收 | 我們音樂收起來， | Let's put the music away. | `03039313` | `03039313` | ✅ |
| 234 | 邊 | 步道一邊是長著爬籐的花架， | A path is lined with a trellis covered in climbing v | `06584404` | `06584406` | ❌ |
| 235 | 叫 | 吃飯時那張木椅便被女人寬軟的臀部撫摸得舒服地輕叫。 | As she sat on the wooden chair during the meal, the  | `04010205` | `04010205` | ✅ |
| 236 | 發 | 並在各大專院校及教育機構發公函， | And send official letters to major universities and  | `06724108` | `06724108` | ✅ |
| 237 | 層 | 中間那層「主任」完全不在他眼裡。 | The middle-tier "Director" meant nothing to him. | `03005006` | `03005006` | ✅ |
| 238 | 過 | 透著粉綠、粉紫、粉紅的金花鱸游曳而過， | A school of golden perch, shimmering in shades of pi | `04005001` | `04005001` | ✅ |
| 239 | 熱 | 他也是較常跳流行熱舞， | He also often dances to popular hot dance moves. | `05228701` | `05228715` | ❌ |
| 240 | 條 | 斷肢逃生的情形很像一個人被巨石壓住一條腿， | A case of escaping with a severed limb is much like  | `06585910` | `06585910` | ✅ |
| 241 | 抽 | 爸爸想再抽一次， | Dad wants to smoke again. | `06598614` | `06598603` | ❌ |
| 242 | 死 | 只要文化不死我在美國柏克萊一住就是十五年。 | I've been living in Berkeley, California for fifteen | `05035202` | `05035209` | ❌ |
| 243 | 行 | 聽取奎爾簡報他此行經過及與沙烏地阿拉伯國王法德和科威 | I listened to Kuier's briefing on his trip and the t | `06775704` | `06775704` | ✅ |
| 244 | 間 | 但至今年三月間， | But up until March of this year, | `04084103` | `04084103` | ✅ |
| 245 | 分 | 自家門口遭到三名蒙面歹徒分執鋁製球棒毆傷， | Three people wearing masks attacked me in front of m | `04146403` | `04146408` | ❌ |
| 246 | 大 | 又在１９０６年建了更大的ＬａｎｇｄｅｌｌＨａｌｌ， | In 1906, an even larger Langdell Hall was built. | `05227204` | `05227202` | ❌ |
| 247 | 下 | 下表中列示ＧＡＴＥ現有實用軟體的名稱及其功能， | The table below lists the names and functions of GAT | `04081803` | `04081803` | ✅ |
| 248 | 做 | 哥哥做蘇武牧羊、天女散花。 | Brother did "Su Wu Tending Sheep" and "Fairy Scatter | `06664306` | `06664308` | ❌ |
| 249 | 度 | 自從釋迦牟尼佛轉法輪度眾生， | Since the time when Sakyamuni Buddha turned the Dhar | `06785402` | `06785404` | ❌ |
| 250 | 拿 | 只開放特定場地供學生拿號碼牌寄物。 | Only specific areas are open for students to take nu | `04011201` | `04011202` | ❌ |
| 251 | 上 | 在歷史上曾經被滅亡過好幾次， | It has been conquered multiple times throughout hist | `04081314` | `04081317` | ❌ |
| 252 | 抽 | 在大型的教學醫院皆有辦法抽血檢查。 | Large teaching hospitals are all capable of drawing  | `06598611` | `06598611` | ✅ |
| 253 | 還 | 我還以為他們會為身體的殘障痛苦呢！ | I thought they would suffer from physical disabiliti | `05002707` | `05002707` | ✅ |
| 254 | 行 | 美國之行並非尋夢、也非淘金， | The trip to the United States was neither a quest fo | `06775704` | `06775704` | ✅ |
| 255 | 就 | 就是所謂修行的智慧。 | The so-called wisdom of spiritual cultivation. | `05198313` | `05198313` | ✅ |
| 256 | 條 | 一開始就把這條小河川整理一下， | Start by tidying up this small river. | `06585924` | `06585906` | ❌ |
| 257 | 層 | 小敏住在二層。 | Xiao Min lives on the second floor. | `03005001` | `03005001` | ✅ |
| 258 | 去 | 就得去哪。 | Where do you have to go? | `06559201` | `06559201` | ✅ |
| 259 | 做 | 堂姊就做了一個洋娃娃給我。 | My cousin just made a doll for me. | `06664301` | `06664301` | ✅ |
| 260 | 季 | 所以這兩隊的競爭從這一季的第一場球就開始了， | Therefore, the competition between these two teams b | `07026504` | `07026504` | ✅ |
| 261 | 去 | 去幾天﹖ | How many days ago? | `06559201` | `06559201` | ✅ |
| 262 | 平 | 車子的把手為平把， | The car has flat handlebars. | `06025201` | `06025213` | ❌ |
| 263 | 吃 | 他們不像某些臺灣移民過的是「吃老本」的日子， | They don't live off their past like some Taiwanese i | `05227001` | `05227012` | ❌ |
| 264 | 代 | 這些是發生在這一代華人身上比較新的事情。 | These are relatively new events that have happened t | `04016205` | `04016206` | ❌ |
| 265 | 度 | 毛高文也常以他高八度的音調嚷嚷兩人歌路不同， | Edgar Miles Bronfman Jr. also often shouted about th | `05147620` | `05147619` | ❌ |
| 266 | 去 | 她去過多少美國市場， | How many U.S. markets has she visited? | `06559201` | `06559201` | ✅ |
| 267 | 叫 | 你學個貓叫， | Meow! | `04010202` | `04010202` | ✅ |
| 268 | 道 | 相信透過教育這最後一道丹藥可以拯救！ | I believe that through education, this final elixir  | `04083505` | `04083512` | ❌ |
| 269 | 發 | 並於台北地區騎乘使用滿一年者（以電動機車行車執照之原 | Riders in the Taipei area who have used an electric  | `06724102` | `06724102` | ✅ |
| 270 | 行 | 西方國家行之已久的社會安全措施， | Western countries have long implemented social secur | `06775707` | `06775707` | ✅ |
| 271 | 投 | 他投７局、送出８次三振， | He pitched seven innings and struck out eight batter | `06685703` | `06685703` | ✅ |
| 272 | 大 | 好大的一個螺殼！ | What a huge shell! | `05227204` | `05227201` | ❌ |
| 273 | 回 | 有一回他受命去孟家宅院取兩支手槍， | One time, he was ordered to go to the Meng family co | `03019001` | `03019008` | ❌ |
| 274 | 就 | 要不然就是陰天。 | Otherwise, it will be overcast. | `05198301` | `05198307` | ❌ |
| 275 | 高 | 照說素質都很高， | The quality is generally very high. | `06010615` | `06010615` | ✅ |
| 276 | 做 | 剝取牠們的毛皮做標本， | They strip their fur to make specimens. | `06664301` | `06664301` | ✅ |
| 277 | 深 | 自己深知道頭銜無用， | I know full well that titles are useless. | `06663313` | `06663313` | ✅ |
| 278 | 就 | 小美聽見這個話就下去了。 | Xiao Mei heard this and went downstairs. | `05198303` | `05198303` | ✅ |
| 279 | 就 | 就是彼此的特性。 | The characteristics of each other. | `05198313` | `05198313` | ✅ |
| 280 | 點 | 就這點來說， | In this regard, | `04043808` | `04043812` | ❌ |
| 281 | 中 | 亦正發展中， | It is also under development. | `04004605` | `04004618` | ❌ |
| 282 | 帶 | 幾乎帶一點哽咽， | Almost choked up a little. | `06791420` | `06791420` | ✅ |
| 283 | 去 | 起身要去。 | I'm about to leave. | `06559201` | `06559201` | ✅ |
| 284 | 中 | 這種哲學和傅蘭尼、孔恩等嘗試在科學的知識如何獲得的過 | This type of philosophy is in the same category as t | `04004618` | `04004618` | ✅ |
| 285 | 去 | 後來就坐飛機到東京去了。 | Later, I took a plane to Tokyo. | `06559204` | `06559204` | ✅ |
| 286 | 拉 | 你是說你們那時候連手都沒有拉！ | You said you didn't even hold hands at that time! | `05230801` | `05230802` | ❌ |
| 287 | 當 | 而在將高山當郊山玩的途中， | While hiking in the mountains, | `04013907` | `04013901` | ❌ |
| 288 | 支 | 為這支陌生且新鮮的球隊加油， | Cheer for this unfamiliar yet fresh team! | `03056204` | `03056204` | ✅ |
| 289 | 帶 | 所以視障生必須要仰賴別人帶他過馬路。 | So visually impaired students have to rely on others | `06791407` | `06791413` | ❌ |
| 290 | 畫 | 例如在畫建築時， | For example, when drawing architecture, | `06550301` | `06550301` | ✅ |
| 291 | 去 | ∥我們到紐約去。 | We're going to New York. | `06559204` | `06559204` | ✅ |
| 292 | 中 | 最後在呂尚叡小姐（ＩＩＩ服務部人員）、童敏惠小姐（台 | Finally, the meeting concluded successfully with exp | `04004605` | `04004618` | ❌ |
| 293 | 代 | 由於本學期校方代學生聯合會向學生收取自治費， | The university collects self-governance fees on beha | `07104504` | `07104502` | ❌ |
| 294 | 空 | 誰好意思有一隻手是空的呢！ | Who would be shameless enough to have one hand empty | `06517331` | `06517316` | ❌ |
| 295 | 度 | 因此面前的視野交集區只有十度。 | Therefore, the overlapping field of view in front of | `05147607` | `05147607` | ✅ |
| 296 | 發 | ∥我要靠意外之財我才能發啦我！ | I need a stroke of luck to strike it rich! | `05193406` | `05193406` | ✅ |
| 297 | 破 | 也沒聽說過肚皮會破的。 | I've never heard of a stomach bursting open either. | `06761404` | `06761404` | ✅ |
| 298 | 上 | 餐飲業上的自動點菜系統； | Automated ordering systems in the catering industry | `04081316` | `04081316` | ✅ |
| 299 | 上 | 在時間上適逢阿爾巴尼亞已故共黨首領霍查的遺孀妮克絲吉 | At the time, it coincided with Nexhmije Hoxha, the w | `04081314` | `04081317` | ❌ |
| 300 | 條 | 只求挽回一條垂危的生命， | I only seek to save a life hanging by a thread. | `06585924` | `06585911` | ❌ |
| 301 | 分 | 分不清是夢是真。 | I can't tell if it's a dream or reality. | `04146403` | `04146401` | ❌ |
| 302 | 破 | 大陸經過文化大革命及破四舊的浩劫， | After the mainland China went through the Cultural R | `06761415` | `06761415` | ✅ |
| 303 | 子 | 法華經長者窮子喻之中， | In the parable of the rich man and his poor son in t | `07027902` | `07027904` | ❌ |
| 304 | 條 | 那是一條繁華的商業街道。 | That is a bustling commercial street. | `06585906` | `06585906` | ✅ |
| 305 | 打 | 不是靠打殺就可以一手遮天的， | It's not something that can be swept under the rug j | `05229126` | `05229126` | ✅ |
| 306 | 用 | 依照戒急用忍檢討執行計畫， | In accordance with the "Refrain from Rashness, Empha | `04017407` | `04017405` | ❌ |
| 307 | 中 | 祥雲的鼓樓中所感到的隆起是完全不同的， | The uplift felt in the drum tower of Xiangyun is ent | `04004603` | `04004603` | ✅ |
| 308 | 長 | 長鼻尖探入牛奶瓶。 | The trunk tip dips into the milk bottle. | `06030801` | `06030801` | ✅ |
| 309 | 代 | 身為台塑的第二代， | As the second generation of the Formosa Plastics Gro | `04016205` | `04016201` | ❌ |
| 310 | 面 | 她曾在82年奪得區運5面金牌後因傷退出體操界， | She retired from gymnastics after winning five gold  | `03028804` | `03028807` | ❌ |
| 311 | 就 | 首先選擇茶葉就是一門學問。 | Choosing tea leaves is a subject of study in itself. | `05198313` | `05198313` | ✅ |
| 312 | 分 | 分由七十一至七十七會計年度逐年編列預算， | The budget shall be allocated annually from fiscal y | `04146403` | `04146408` | ❌ |
| 313 | 條 | 每次烤鴨都一條腿， | Every time I roast a duck, it's on one leg. | `06585910` | `06585910` | ✅ |
| 314 | 中 | 耳朵以下全埋在衣服中， | The entire area below the ears is buried in the clot | `04004603` | `04004603` | ✅ |
| 315 | 叫 | 當頑皮的鬧鐘叫了以後， | After the mischievous alarm clock went off, | `04010205` | `04010205` | ✅ |
| 316 | 點 | 就某一點而言， | In a certain sense, | `04043808` | `04043812` | ❌ |
| 317 | 打開 | 打開這個知識的寶庫。 | Open this treasure trove of knowledge. | `06548101` | `06548102` | ❌ |
| 318 | 行 | 李總統康乃爾之行， | President Tsai's visit to Cornell. | `06775704` | `06775704` | ✅ |
| 319 | 中 | 在車中， | In the car | `04004603` | `04004603` | ✅ |
| 320 | 還 | 還在服役的吳昌達， | Wu Chang-ta is still on active duty. | `05002701` | `05002701` | ✅ |
| 321 | 打 | 有牌打就好， | As long as you have a license to play, that's all th | `05229133` | `05229133` | ✅ |
| 322 | 回 | 這回換野狼的屁股卡在洞口了， | The wolf's butt got stuck in the hole this time. | `03019001` | `03019008` | ❌ |
| 323 | 上 | 在個人資料和事件的處理上， | In the handling of personal data and incidents, | `04081314` | `04081317` | ❌ |
| 324 | 低 | 故包括大部份的自營商及散戶投資人普遍都有預期回檔後再 | Most self-employed traders and retail investors gene | `06748412` | `06748412` | ✅ |
| 325 | 行 | 所以要出門是必須繞過公園而行的。 | Therefore, you have to go around the park to go out. | `06775701` | `06775701` | ✅ |
| 326 | 度 | 一百八十度不一樣。 | It's a hundred and eighty degrees different. | `05147607` | `05147607` | ✅ |
| 327 | 帶 | 帶著滿腹心得與球經比以前更成熟。 | I return with a wealth of experience and a deeper un | `06791420` | `06791420` | ✅ |
| 328 | 用 | 是取之於消費者、用之於消費者。 | It is taken from consumers and used for consumers. | `04017407` | `04017401` | ❌ |
| 329 | 邊 | 調整的方法是手握雙筒鏡的兩邊， | Adjust the method by holding both sides of the binoc | `06584404` | `06584406` | ❌ |
| 330 | 拍 | 「原來拍古裝戲這麼辛苦！ | "Turns out filming period dramas is so exhausting!" | `08028003` | `08028003` | ✅ |
| 331 | 打 | 可見學生不但喜歡打保齡球， | Students not only enjoy playing bowling. | `05229131` | `05229131` | ✅ |
| 332 | 正 | 後人乘涼正是本院圖書館自動化的最佳寫照， | Future generations benefit from the cool shade, whic | `07009822` | `07009822` | ✅ |
| 333 | 清 | 水乃天下至清之物， | Water is the purest substance in the world. | `06539501` | `06539501` | ✅ |
| 334 | 收 | 還捨不得收起來。 | I still can't bear to put it away. | `03039314` | `03039314` | ✅ |
| 335 | 場 | 除了在萬芳醫院的三場演出之外， | In addition to the three performances at Wanfang Hos | `06721709` | `06721707` | ❌ |
| 336 | 條 | 他的童年像一條浮根， | His childhood was like a floating root. | `06585903` | `06585903` | ✅ |
| 337 | 下 | 在Ｃ目錄下打）ｐａｔｈ）。 | Create a path under the C directory. | `04081808` | `04081808` | ✅ |
| 338 | 新 | 馬英九重申暫緩設立新的公立高中， | Ma Ying-jeou reiterated the postponement of establis | `05237901` | `05237901` | ✅ |
| 339 | 拍 | 這部片子裡的留鳥還滿容易拍的， | The resident birds in this film are quite easy to ph | `08028003` | `08028003` | ✅ |
| 340 | 高 | 也較查詢系統為高； | The query system is also more advanced. | `06010615` | `06010615` | ✅ |
| 341 | 大 | 那條大蛇卻朝他點了點頭， | That giant serpent nodded at him. | `05227201` | `05227201` | ✅ |
| 342 | 就 | 昏沉就是愛睡， | Drowsiness is just loving to sleep. | `05198301` | `05198313` | ❌ |
| 343 | 人 | 高階積體電路設計公司至少雇用十人以上， | At least ten people are employed by advanced integra | `05231109` | `05231109` | ✅ |
| 344 | 去 | 煩請猛師兄與無蹤師父以及貴寺四大弟子去那邊坐鎮， | Please send Master Meng, Master Wu Zong, and the fou | `06559201` | `06559201` | ✅ |
| 345 | 中 | 在這次選戰中佔了有利地位。 | They have an advantageous position in this election  | `04004605` | `04004618` | ❌ |
| 346 | 去 | 我們能去嗎？ | Are we able to go? | `06559205` | `06559201` | ❌ |
| 347 | 錢 | 而讀書人則是最沒有錢的。 | Scholars are often the poorest. | `06015105` | `06015107` | ❌ |
| 348 | 熱 | 無形的過熱， | Invisible overheating. | `05228701` | `05228707` | ❌ |
| 349 | 說 | 可說毫不遜色。 | It can be said to be no less impressive. | `05212406` | `05212406` | ✅ |
| 350 | 起 | 其中七名船員劉憲助（上圖右起）。 | Among them, seven crew members, including Liu Xianzh | `04004803` | `04004803` | ✅ |
| 351 | 打 | 謝玄只用了五千人就把秦兵打得大敗， | Yue Xuan defeated the Qin army with only five thousa | `05229126` | `05229126` | ✅ |
| 352 | 條 | 可是他那兩條硬得像木棍的腿， | But those two legs of his were as stiff as wooden st | `06585910` | `06585910` | ✅ |
| 353 | 新 | 然後沖進新燒滾水， | Then rush into freshly boiled water. | `05237905` | `05237905` | ✅ |
| 354 | 度 | 那麼如何因應不同需求或在家庭結構變化時必須採行的「二 | Therefore, the "second-time redesign" required to ad | `05147617` | `05147617` | ✅ |
| 355 | 度 | 而南極的最低氣溫紀錄則有攝氏零下８８度。 | The lowest temperature record in Antarctica is minus | `05147610` | `05147610` | ✅ |
| 356 | 上 | 準備幾個乾淨的塑膠容器放在轉盤上， | Prepare a few clean plastic containers and place the | `04081301` | `04081301` | ✅ |
| 357 | 熱 | 如此對於賽程的控制和比賽氣氛熱都很有幫助， | This helps a lot in controlling the schedule and hea | `05228723` | `05228723` | ✅ |
| 358 | 下 | 並在其下成立系統規格制訂和系統測試小組。 | And establish a system specification development and | `04081808` | `04081808` | ✅ |
| 359 | 行 | 一定偕母同行， | I will definitely go with my mother. | `06775704` | `06775704` | ✅ |
| 360 | 轉 | 他三個手指悠然轉著那只淡青色玉鐲。 | He leisurely twirled the light blue jade bracelet wi | `05228803` | `05228802` | ❌ |
| 361 | 活 | 活的天然檜木林已全面禁採， | The living natural cypress forest has been completel | `06725001` | `06725001` | ✅ |
| 362 | 明 | 法燈滅又明。 | The light goes out and then shines again. | `06685403` | `06685403` | ✅ |
| 363 | 片 | 他家後院就是一片竹林， | There is a bamboo grove right in the backyard of his | `05195912` | `05195912` | ✅ |
| 364 | 帶 | 「每個眾生都帶著自己的業而來， | Every being comes with their own karma. | `06791418` | `06791418` | ✅ |
| 365 | 就 | 心浮動就是道心不堅固， | A restless mind is one that lacks a firm spiritual f | `05198301` | `05198313` | ❌ |
| 366 | 上 | 也把墳地上那些白花和紅花稱為杜鵑花。 | They also call the white and red flowers on the grav | `04081301` | `04081301` | ✅ |
| 367 | 重 | 拿起大包小包的行李也就不覺得重了。 | Picking up large and small pieces of luggage doesn't | `05207602` | `05207602` | ✅ |
| 368 | 大 | 大蛇竟然把嘴張開， | The serpent actually opened its mouth wide. | `05227204` | `05227201` | ❌ |
| 369 | 拿 | 偶爾有幾個好心人拿東西給我吃， | Occasionally, some kind people give me things to eat | `04011205` | `04011205` | ✅ |
| 370 | 分 | 數十年不分寒暑， | For decades, summer and winter have not been disting | `04146403` | `04146405` | ❌ |
| 371 | 發 | 是很願意國內所有發卡機構能研擬出一套辦法來針對如果受 | I sincerely hope that all domestic card-issuing inst | `06724101` | `06724102` | ❌ |
| 372 | 明 | 而教練費區和球員之間不和的事實也由暗而明， | The rift between the coaching staff and the players  | `06685407` | `06685407` | ✅ |
| 373 | 拿 | 有些人因「太紅」怕整個晚上因不停拿宵夜而無法念書， | Some people avoid eating late-night snacks because t | `04011201` | `04011202` | ❌ |
| 374 | 面 | 面無表情地望著大家， | He stared blankly at everyone. | `03028804` | `03028801` | ❌ |
| 375 | 真 | 真希望可以永遠住在那裡。 | I really wish I could live there forever. | `05100414` | `05100414` | ✅ |
| 376 | 上 | 一切都只停留在勞作的程度上。 | Everything remains at the level of mere labor. | `04081314` | `04081317` | ❌ |
| 377 | 熱 | 此外響韻、寶麗金也在一波波文藝復興熱， | In addition, Decca and PolyGram are also experiencin | `05228709` | `05228709` | ✅ |
| 378 | 要 | 要完成還早得很呢！ | It's going to take a long time to finish! | `06636905` | `06636907` | ❌ |
| 379 | 條 | 美國的Ｆ１１１戰鬥轟炸機，廿六日晚精確炸毀科威特境內 | The U.S. F-111 fighter-bomber precisely destroyed tw | `06585924` | `06585903` | ❌ |
| 380 | 發 | 因此也在同時明令停止所有稻田轉用的審核與發照。 | Therefore, it also simultaneously issued a formal or | `06724102` | `06724102` | ✅ |
| 381 | 行 | 唱片公司特別為曾慶瑜安排了一趟美國之行， | A record company specially arranged a trip to the Un | `06775704` | `06775704` | ✅ |
| 382 | 做 | 做個術德兼修、品學兼優的好學生， | Strive to be a student who excels in both moral char | `06664308` | `06664308` | ✅ |
| 383 | 片 | 他站在一片書牆前， | He stood in front of a wall of books. | `05195915` | `05195915` | ✅ |
| 384 | 行 | （３）電池組每隔適當時期應行均衡充電一次。 | The battery pack should be given an equalizing charg | `06775706` | `06775706` | ✅ |
| 385 | 用 | 吃穿用玩樣樣俱全， | Everything needed for eating, dressing, using, and p | `04017411` | `04017411` | ✅ |
| 386 | 正 | 其謬誤正如同我們總習於率爾用一個人比擬另一個人。 | Just as we often hastily compare one person to anoth | `07009821` | `07009822` | ❌ |
| 387 | 前 | 廿五日清晨在林口鄉中山路五十四號前發現曾忠義座車， | At dawn on the 25th, a car belonging to Zeng Zhongyi | `03033701` | `03033701` | ✅ |
| 388 | 大 | 由於批購總額大， | The total procurement amount is large. | `05227203` | `05227203` | ✅ |
| 389 | 就 | 夜市裡最吸引人的地方就是商品的價錢比一般商店或百貨公 | The most attractive thing about night markets is tha | `05198313` | `05198313` | ✅ |
| 390 | 條 | 或者手拉手走一條霪雨霏霏的街。 | Or hand in hand, stroll down a rain-soaked street. | `06585924` | `06585906` | ❌ |
| 391 | 破 | 再破三案。 | Three more cases have been cracked. | `06761412` | `06761412` | ✅ |
| 392 | 掛 | 男孩要求掛急診。 | The boy requests emergency treatment. | `06701415` | `06701415` | ✅ |
| 393 | 來 | 國外學生來台主要集中在台灣師大學中文， | International students in Taiwan are mainly concentr | `04086501` | `04086501` | ✅ |
| 394 | 空 | ２．胃酸排空時間檢查。 | Gastric emptying time examination. | `06517331` | `06517312` | ❌ |
| 395 | 帶 | 集合是以不帶正負號的整數構成陣列型式， | A set is an array formed by unsigned integers. | `06791418` | `06791418` | ✅ |
| 396 | 熱 | 這不過是近年來臺灣明式家具熱的兩個浪頭。 | These are merely two waves of the recent surge in in | `05228709` | `05228709` | ✅ |
| 397 | 粗 | 還有幾支粗簽字筆， | There are still a few thick felt-tip pens left. | `06711803` | `06711803` | ✅ |
| 398 | 條 | 教育部在九月初以不符合師資培育法第七條及師範教育精神 | The Ministry of Education rejected in early Septembe | `06585929` | `06585929` | ✅ |
| 399 | 邊 | 現在井邊圍上了欄杆， | A railing has been installed around the well. | `06584404` | `06584405` | ❌ |
| 400 | 分 | 向行政院院長連戰提出的第一分報告書中， | The first interim report submitted to Premier Vincen | `04108107` | `04108107` | ✅ |

### 錯誤與 NONE 的細節

**4. 死**　`wsd-死-ab87`　[dominant]
- 原句：可能這是你對我抱的至死不變的看法，
- 譯文：Perhaps this is the unchanging view you hold of me.
- judge 選：`05035201` 形容沒有生命的。　信心 0.90　依據：整句強調「不變的觀點」而非生死狀態
- gold：`05035202` 形容生物失去生命。

**19. 去**　`wsd-去-9cd9`　[dominant]
- 原句：本來要下樓去買幾包速食麵，
- 譯文：I was about to go downstairs to buy a few packs of instant noodles.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說「下樓去買泡麵」的移動行為
- gold：`06559205` 表前述對象進行後述事件。

**26. 歲**　`wsd-歲-03a2`　[dominant]
- 原句：前總統李登輝七十八歲高齡，
- 譯文：Taiwan's former President Lee Teng-hui passed away at the age of 97.
- judge 選：`06559404` 生物存活的時間長度。　信心 0.95　依據：整句強調逝世時的年紀長度
- gold：`06559405` 計算年齡的單位。

**30. 歲**　`wsd-歲-3561`　[dominant]
- 原句：是我那個七十一歲的外婆和小外公吵著要離婚，
- 譯文：My seventy-one-year-old grandmother and grandfather are arguing about getting a divorce.
- judge 選：`06559404` 生物存活的時間長度。　信心 0.95　依據：seventy-one-year-old 直接表達年齡長度
- gold：`06559405` 計算年齡的單位。

**36. 邊**　`wsd-邊-d206`　[dominant]
- 原句：眼見一群男孩子就守在河邊，
- 譯文：A group of boys was seen standing by the river.
- judge 選：`06584406` 特定地區中位於前述方向邊緣的地點。　信心 0.90　依據：by the river 表達河流邊緣位置
- gold：`06584404` 特定對象與其他鄰界對象交界的地方。

**37. 明**　`wsd-明-3724`　[dominant]
- 原句：第四繼承時期是五代至明末。
- 譯文：The Fourth Inheritance Period spans from the Five Dynasties to the late Ming Dynasty.
- judge 選：`07003502` 明朝的國號或政權。　信心 0.95　依據：譯文明確提到明朝政權的時間範圍
- gold：`07003501` 中國朝代名，西元1368至1644年，由朱元璋所建立。

**43. 坐**　`wsd-坐-03d2`　[dominant]
- 原句：反不若坐在家中，等待政黨比例代表制下的提名，
- 譯文：It would be better to stay at home and wait for a nomination under the proportional representation system of the political party.
- judge 選：`05223903` 搭乘有座位的交通工具。　信心 0.90　依據：整句在說待在家等政黨比例代表制提名
- gold：`05223901` 維持上身直立，臀部放在椅子或其它物體上支撐身體重量的姿勢。

**47. 場**　`wsd-場-50f3`　[dominant]
- 原句：國王明星大前鋒韋伯則攻下全隊最高的21分以及本季個人單場最多之12個籃板球。
- 譯文：King star power forward Webber scored a team-high 21 points and a season-high 12 rebounds.
- judge 選：`06721710` 計算完整歷程的事件的單位。　信心 0.90　依據：譯文提到球季最高紀錄，強調完整歷程
- gold：`06721709` 計算經過安排的活動的單位。

**52. 歲**　`wsd-歲-ec31`　[dominant]
- 原句：看到一位七十幾歲的老先生，
- 譯文：I saw an elderly gentleman in his seventies.
- judge 選：`06559404` 生物存活的時間長度。　信心 0.95　依據：elderly 直接對應「歲」在此指年齡長度
- gold：`06559405` 計算年齡的單位。

**58. 歲**　`wsd-歲-f168`　[dominant]
- 原句：共有兩百位八十歲以上的壽星在家人的陪同下，
- 譯文：A total of two hundred centenarians, accompanied by their family members,
- judge 選：`06559404` 生物存活的時間長度。　信心 0.95　依據：整句在說百歲人瑞的存活時間長度
- gold：`06559405` 計算年齡的單位。

**60. 去**　`wsd-去-a508`　[dominant]
- 原句：準備挑到城裡去賣。
- 譯文：I'm going to take them to town to sell.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說帶他們去城裡賣東西
- gold：`06559205` 表前述對象進行後述事件。

**62. 空**　`wsd-空-9844`　[dominant]
- 原句：最後一幕『菩提』代表著『空』，
- 譯文：The final scene "Bodhi" represents "Emptiness."
- judge 選：`06517332` 形容事物不具有實體概念的。　信心 0.90　依據：譯文中的Emptiness對應空的語義
- gold：`06517331` 事物不具有實體的概念。

**65. 言**　`wsd-言-3d36`　[dominant]
- 原句：就前者而言，
- 譯文：In this regard,
- judge 選：`06008201` 以口語媒介引述或陳述後述訊息。　信心 0.95　依據：譯文用介系詞片語引介後述訊息
- gold：`06008204` 評價後述對象。

**66. 歲**　`wsd-歲-b893`　[dominant]
- 原句：一個在三十歲之前沒有成為社會主義信徒的人，
- 譯文：A person who hasn't become a socialist before the age of thirty
- judge 選：`06559404` 生物存活的時間長度。　信心 0.95　依據：譯文強調「未滿三十歲」即存活時間長度
- gold：`06559405` 計算年齡的單位。

**67. 帶**　`wsd-帶-de6d`　[dominant]
- 原句：事後我帶他回南部老家見父母，
- 譯文：Afterward, I took him back to my hometown in southern Taiwan to meet my parents.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：整句強調「我」帶他回家見父母
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**68. 抽**　`wsd-抽-8360`　[dominant]
- 原句：又抽大麻睡著了，
- 譯文：I smoked weed and fell asleep again.
- judge 選：`06598612` 以壓力或吸力移動後述流體到其他地方。　信心 0.90　依據：整句在說吸菸後睡著，smoked在此表吸入動作
- gold：`06598614` 使用口攝入會令人上癮的物品。

**69. 歲**　`wsd-歲-42b7`　[dominant]
- 原句：今年八十歲的王自牧，
- 譯文：Eighty-year-old Wang Tzu-mu this year
- judge 選：`06559404` 生物存活的時間長度。　信心 0.95　依據：譯文強調「80歲」即存活時間長度
- gold：`06559405` 計算年齡的單位。

**70. 股**　`wsd-股-32a8`　[dominant]
- 原句：首季每股稅後盈餘約○．八元。
- 譯文：The after-tax earnings per share for the first quarter were approximately NT$0.8.
- judge 選：`03015702` 上櫃或上市公司用來表示其公司股份的證券。　信心 0.95　依據：譯文提到每股稅後盈餘，明確指向股份證券
- gold：`03015710` 計算股份的單位。

**72. 來**　`wsd-來-cead`　[dominant]
- 原句：但嚴格來說銀行業的壞帳比票券業更難計算，
- 譯文：But strictly speaking, bad debts in the banking industry are harder to calculate than in the securities industry.
- judge 選：`04086501` 向參考點的位置移動或到達參考點的位置。　信心 0.90　依據：譯文強調「計算難度」需移動到某參考點
- gold：`04086509` 表藉由前述工具、方法或範圍進行後述事件。

**73. 明**　`wsd-明-9c84`　[dominant]
- 原句：就好像在濃霧中遇到一盞明燈一樣。
- 譯文：It was like encountering a bright beacon in the thick fog.
- judge 選：`06685411` 形容比喻狀況變得明顯清楚。　信心 0.90　依據：like 後的比喻強調狀況變得明顯清楚
- gold：`06685401` 形容光源的光線充足。

**75. 強**　`wsd-強-95c5`　[dominant]
- 原句：當海水清澈、陽光穿透力強的時候，
- 譯文：When the sea is clear and the sunlight penetrates strongly.
- judge 選：`09250306` 形容特定特性的程度高。　信心 0.95　依據：譯文強調陽光穿透的程度高
- gold：`09250303` 形容能力或發展狀況好的。

**82. 股**　`wsd-股-47e8`　[dominant]
- 原句：中華電週二公布今年每股純益目標為四．一六元，
- 譯文：Taiwan Mobile announced on Tuesday that its target for earnings per share this year is NT$4.16.
- judge 選：`03015702` 上櫃或上市公司用來表示其公司股份的證券。　信心 0.95　依據：譯文提到 earnings per share（每股盈餘）與股份證券直接相關
- gold：`03015710` 計算股份的單位。

**83. 間**　`wsd-間-41a8`　[dominant]
- 原句：省能產品也成為未來國際間的最大商機，
- 譯文：Energy-efficient products are also becoming the biggest business opportunity in the international market in the future.
- judge 選：`04084103` 引介時間的範圍。　信心 0.95　依據：「間」在此引介未來的時間範圍
- gold：`04084104` 引介事件與事件的關係。

**88. 去**　`wsd-去-0a4c`　[dominant]
- 原句：並非去抗議。
- 譯文：It's not about going to protest.
- judge 選：`06559201` 向特定地點移動。　信心 0.90　依據：譯文強調「去抗議」的移動行為
- gold：`06559205` 表前述對象進行後述事件。

**89. 去**　`wsd-去-1625`　[dominant]
- 原句：試著去接近森林，
- 譯文：Try to approach the forest.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：譯文整句在說接近森林
- gold：`06559205` 表前述對象進行後述事件。

**92. 拍**　`wsd-拍-241f`　[dominant]
- 原句：一走紅大家都搶著找她拍，
- 譯文：Once she became popular, everyone scrambled to collaborate with her on photo shoots.
- judge 選：`08028003` 用攝影器材紀錄動態影像。　信心 0.95　依據：譯文提到 photo shoots，即拍照行為
- gold：`08028004` 參與拍攝電影與製作。

**95. 真**　`wsd-真-a3cf`　[dominant]
- 原句：真是惡名昭彰的傢伙。
- 譯文：What a notorious guy.
- judge 選：`05100414` 表說話者主觀評價程度高，帶有誇張語氣或情感。　信心 0.95　依據：notorious 表主觀負面評價且語氣誇張
- gold：`05100413` 表對客觀情況的真實性給予評價。

**96. 新**　`wsd-新-c4ba`　[dominant]
- 原句：並同時實施新的審查制度；
- 譯文：At the same time, a new censorship system was implemented.
- judge 選：`05237901` 形容特定對象剛產生不久。　信心 0.95　依據：譯文強調系統剛被實施，意指「新」產生不久
- gold：`05237904` 形容和原來不一樣的。

**98. 去**　`wsd-去-fada`　[dominant]
- 原句：去住旅館好了！
- 譯文：Let's just stay at a hotel!
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說待在旅館而非移動
- gold：`06559205` 表前述對象進行後述事件。

**105. 帶**　`wsd-帶-dc7d`　[dominant]
- 原句：或帶小孩郊遊。
- 譯文：Go on a picnic with children.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：「帶」在此指帶領孩子一起去野餐
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**107. 高**　`wsd-高-1f42`　[dominant]
- 原句：台大最高，
- 譯文：National Taiwan University is the best.
- judge 選：`06010615` 形容程度或標準高於比較對象。　信心 0.95　依據：best 在句中表示程度或標準高於他者
- gold：`06010610` 形容數值大於比較對象。

**110. 起**　`wsd-起-b672`　[dominant]
- 原句：報名自即日起受理，
- 譯文：Registration is now open.
- judge 選：`04004806` 時態標記。表事件開始。　信心 0.90　依據：Registration 開始即表註冊活動啟動
- gold：`04004801` 表示事件時間範圍的開始參考點。

**111. 中**　`wsd-中-d396`　[dominant]
- 原句：恍恍惚惚腦中忽然瞥過過去她那激憤壯烈的夢。
- 譯文：A fleeting image of her passionate and heroic dream suddenly flashed through my mind.
- judge 選：`04004618` 在事件的過程中。　信心 0.90　依據：中在此指事件過程中的某個瞬間
- gold：`04004605` 在前述的機構或領域範圍。

**119. 言**　`wsd-言-7e8e`　[dominant]
- 原句：而所謂的新指甲可能也是指在老指甲下方的油脂指床而言。
- 譯文：The so-called new nail may also refer to the fatty nail bed beneath the old nail.
- judge 選：`06008201` 以口語媒介引述或陳述後述訊息。　信心 0.90　依據：譯文中refer to即為以言語引述訊息
- gold：`06008204` 評價後述對象。

**123. 條**　`wsd-條-a722`　[dominant]
- 原句：便可堆出一條筆直的高級公路。
- 譯文：A straight, high-quality highway can be built this way.
- judge 選：`06585906` 計算地面上長條型的建築物或自然景觀的單位。　信心 0.90　依據：譯文提到高速公路為長條型建築
- gold：`06585924` 計算行進的路線的單位。

**132. 使**　`wsd-使-61bb`　[dominant]
- 原句：使我們變得很有禮貌。
- 譯文：Let us become very polite.
- judge 選：`06560201` 較有權力的人或機構要求他人去做後述事件。　信心 0.95　依據：整句為「讓我們變得有禮貌」
- gold：`06560202` 導致後述對象涉入後述事件。

**134. 上**　`wsd-上-2481`　[dominant]
- 原句：林青霞也在記者會上感動的表示，
- 譯文：Yvonne Yung also emotionally expressed at the press conference that
- judge 選：`04081317` 按前述事物的觀點來陳述。　信心 0.90　依據：「上」在此表示「依據前述事物的觀點」
- gold：`04081314` 事件的發生在前述事物的範圍內。

**135. 行**　`wsd-行-a94f`　[dominant]
- 原句：父母就希望你只要書念好就行了。
- 譯文：Parents just hope that you do well in your studies.
- judge 選：`06775704` 前往特定地點參觀或訪問的活動。　信心 0.90　依據：譯文強調「在學業上表現良好」隱含實際行動
- gold：`06775711` 形容表示同意或允許。

**137. 拍**　`wsd-拍-8f3e`　[dominant]
- 原句：拍那個終極保鏢的時候。
- 譯文：When they were filming that ultimate bodyguard.
- judge 選：`08028003` 用攝影器材紀錄動態影像。　信心 0.95　依據：譯文強調用器材紀錄動態影像
- gold：`08028004` 參與拍攝電影與製作。

**150. 粗**　`wsd-粗-a2fc`　[dominant]
- 原句：英勇的消防隊員合力舉起又粗又大的水管，
- 譯文：Brave firefighters worked together to lift the thick and heavy hose.
- judge 選：`06711803` 形容線條的寬度大。　信心 0.90　依據：譯文中的 thick 描述水管的寬度而非橫切面面積
- gold：`06711801` 形容條狀物的橫切面的面積大。

**155. 中**　`wsd-中-103c`　[dominant]
- 原句：主要乃因在如此萎縮的成交量中，
- 譯文：Amid such shrinking transaction volumes,
- judge 選：`04004618` 在事件的過程中。　信心 0.95　依據：譯文強調交易量縮減的過程
- gold：`04004605` 在前述的機構或領域範圍。

**157. 字**　`wsd-字-c8e1`　[dominant]
- 原句：因為我的所有最字，
- 譯文：All my words.
- judge 選：`06584501` 記錄語言的書面符號。　信心 0.95　依據：譯文中的 words 即為書面語言符號
- gold：`06584502` 中文書面書寫的最小單位。

**158. 強**　`wsd-強-ee11`　[dominant]
- 原句：她的港裔美籍夫婿區永禧親和力強，
- 譯文：Her Hong Kong-born American husband Au Wing Hei has a strong affinity.
- judge 選：`09250306` 形容特定特性的程度高。　信心 0.95　依據：譯文強調丈夫與生俱來的親近感
- gold：`09250303` 形容能力或發展狀況好的。

**159. 中**　`wsd-中-8b41`　[dominant]
- 原句：混合工作負荷中的「自然工作負荷」是在控制條件之下以較少變化的方式執行。
- 譯文：In mixed workloads, "natural workload" is executed under controlled conditions with less variation.
- judge 選：`04004618` 在事件的過程中。　信心 0.90　依據：譯文強調執行過程中的條件控制
- gold：`04004605` 在前述的機構或領域範圍。

**165. 支**　`wsd-支-1fe0`　[dominant]
- 原句：而韓國隊卻只有七支。
- 譯文：However, the South Korean team only has seven.
- judge 選：`03056204` 計算團隊的單位。　信心 0.95　依據：整句在說團隊人數而非棒球術語
- gold：`03056210` 計算棒球賽中擊出的有效打擊數。

**167. 分**　`wsd-分-1315`　[dominant]
- 原句：布朗也只有八點一分，
- 譯文：Brown only has 8.1 points.
- judge 選：`05007101` 用於紀錄成績或競賽結果的數目。　信心 0.95　依據：整句在說布朗的得分數值
- gold：`05007102` 計算分數的單位。

**168. 帶**　`wsd-帶-170d`　[dominant]
- 原句：秋天你帶我來歐洲好嗎？
- 譯文：Would you like me to take you to Europe in the fall?
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：整句在說帶領某人前往歐洲
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**175. 強**　`wsd-強-cf66`　[dominant]
- 原句：她就有很強的自主意識，
- 譯文：She has a strong sense of independence.
- judge 選：`09250306` 形容特定特性的程度高。　信心 0.95　依據：譯文強調「獨立特性的程度高」
- gold：`09250303` 形容能力或發展狀況好的。

**180. 歲**　`wsd-歲-edb8`　[dominant]
- 原句：趁被害人黃文助（二十九歲，
- 譯文：The victim, Huang Wen-zhu (29 years old),
- judge 選：`06559404` 生物存活的時間長度。　信心 0.95　依據：「歲」在此表示年齡長度而非單位
- gold：`06559405` 計算年齡的單位。

**182. 深**　`wsd-深-9292`　[dominant]
- 原句：而且更深一層的智慧的發揮。
- 譯文：And the deeper manifestation of wisdom.
- judge 選：`06663313` 表超過平常的程度。　信心 0.90　依據：deeper 直接對應「深」的程度義
- gold：`06663314` 形容比喻牽涉事件的程度高。

**184. 中**　`wsd-中-993b`　[dominant]
- 原句：致潘雙全腹部中一槍。
- 譯文：A gunshot wound to the abdomen was inflicted on Pan Shuangquan.
- judge 選：`05007603` 因他人的惡意設計而受到負面影響。　信心 0.90　依據：槍傷是他人惡意行為造成的負面影響
- gold：`05007601` 從施力來源使投擲物經過運動路徑到達目標。

**194. 會**　`wsd-會-9ba2`　[dominant]
- 原句：沒有一家銀行會故意違反央行規定，
- 譯文：No bank would deliberately violate the central bank's regulations.
- judge 選：`04143406` 表條件符合，就一定實現。　信心 0.95　依據：「會」在此表示「必然實現」的條件語義
- gold：`04143405` 表在通常狀況下，有可能實現。

**196. 去**　`wsd-去-eeed`　[dominant]
- 原句：我們要去旅行，
- 譯文：We are going to travel.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說前往旅行的地點
- gold：`06559205` 表前述對象進行後述事件。

**201. 就**　`wsd-就-d8a6`　[non_dominant]
- 原句：這就是「相」很少印在我的心上。
- 譯文：That is why the "phase" rarely imprints on my heart.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：「就」在此表示「在這種情況下自然發生」
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**205. 小**　`wsd-小-2e7b`　[non_dominant]
- 原句：小野豬叫著：
- 譯文：A wild boar is grunting.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文未表達年紀或體積的比較
- gold：`05227107` 形容年紀比特定對象小。

**208. 點**　`wsd-點-b366`　[non_dominant]
- 原句：說得確實點，
- 譯文：Just put it bluntly.
- judge 選：`04043808` 事件或過程中具顯著的指標。　信心 0.90　依據：bluntly 表示直接陳述重點，符合指標意涵
- gold：`04043813` 表不確定的小數量。

**214. 花**　`wsd-花-da24`　[non_dominant]
- 原句：棘皮動物海百合像海中之花般地鮮艷綻放，
- 譯文：Echinoderms like sea lilies bloom brilliantly in the ocean like flowers.
- judge 選：`05229001` 植物的主要器官之一，主要用於繁殖，通常具有顏色鮮豔和形狀漂亮的花瓣。　信心 0.90　依據：譯文用 bloom 和 flowers 比喻海百合的外觀
- gold：`05229006` 比喻事物的精華。

**220. 條**　`wsd-條-63fe`　[non_dominant]
- 原句：森林之家的每條街道，
- 譯文：Every street in Forest House
- judge 選：`06585924` 計算行進的路線的單位。　信心 0.95　依據：street 指的是街道的路線單位
- gold：`06585906` 計算地面上長條型的建築物或自然景觀的單位。

**231. 法**　`wsd-法-7bbd`　[non_dominant]
- 原句：而非國民黨統治機器所貼下標籤的地域區分法‧人們習慣稱呼的本省人其實也是外省移民的第七代，
- 譯文：People are actually accustomed to calling the "ben sheng ren" (locally born people) the seventh generation of Waishengren immigrants.
- judge 選：`05045101` 由立法機關制定，有強制效力的行為規範。　信心 0.90　依據：「法」在此指稱具有強制效力的行為規範
- gold：`05045104` 做事的步驟或技巧。

**232. 道**　`wsd-道-ef48`　[non_dominant]
- 原句：每一個性方面的需求可能有些人比較好此道，
- 譯文：Everyone has different levels of interest or expertise when it comes to matters of intimacy.
- judge 選：`06002401` 思想或理論。　信心 0.85　依據：譯文中的matters of intimacy涉及個人知識或經驗層次
- gold：`06002402` 含有哲理的技藝。

**234. 邊**　`wsd-邊-0c87`　[non_dominant]
- 原句：步道一邊是長著爬籐的花架，
- 譯文：A path is lined with a trellis covered in climbing vines.
- judge 選：`06584404` 特定對象與其他鄰界對象交界的地方。　信心 0.90　依據：譯文中的 'lined with' 表達路徑與柵架的交界
- gold：`06584406` 特定地區中位於前述方向邊緣的地點。

**239. 熱**　`wsd-熱-5dad`　[non_dominant]
- 原句：他也是較常跳流行熱舞，
- 譯文：He also often dances to popular hot dance moves.
- judge 選：`05228701` 形容溫度高或感覺溫度高的。　信心 0.90　依據：hot dance moves 指流行且熱門的舞步
- gold：`05228715` 表動作劇烈。

**241. 抽**　`wsd-抽-b0a2`　[non_dominant]
- 原句：爸爸想再抽一次，
- 譯文：Dad wants to smoke again.
- judge 選：`06598614` 使用口攝入會令人上癮的物品。　信心 0.95　依據：整句在說父親想再吸菸
- gold：`06598603` 伸出的肢體或頭部往身體的方向退。

**242. 死**　`wsd-死-9b5f`　[non_dominant]
- 原句：只要文化不死我在美國柏克萊一住就是十五年。
- 譯文：I've been living in Berkeley, California for fifteen years, and as long as our culture survives, I'll stay.
- judge 選：`05035202` 形容生物失去生命。　信心 0.95　依據：整句強調文化存續而「我」會留下，非指物品廢棄
- gold：`05035209` 形容不再使用的。

**245. 分**　`wsd-分-a4e1`　[non_dominant]
- 原句：自家門口遭到三名蒙面歹徒分執鋁製球棒毆傷，
- 譯文：Three people wearing masks attacked me in front of my house with aluminum baseball bats and injured me.
- judge 選：`04146403` 將整體事物區隔成幾部份。　信心 0.95　依據：整句在說三人分別攻擊
- gold：`04146408` 表分別。

**246. 大**　`wsd-大-6041`　[non_dominant]
- 原句：又在１９０６年建了更大的ＬａｎｇｄｅｌｌＨａｌｌ，
- 譯文：In 1906, an even larger Langdell Hall was built.
- judge 選：`05227204` 形容程度超過比較對象的。　信心 0.95　依據：larger 直接對應「大」的比較義
- gold：`05227202` 形容容量超過比較對象的。

**248. 做**　`wsd-做-88b9`　[non_dominant]
- 原句：哥哥做蘇武牧羊、天女散花。
- 譯文：Brother did "Su Wu Tending Sheep" and "Fairy Scattering Flowers."
- judge 選：`06664306` 做，取代整個事件。　信心 0.90　依據：整句在說弟弟表演了兩個節目
- gold：`06664308` 前述對象的工作或身份是後述對象。

**249. 度**　`wsd-度-9c03`　[non_dominant]
- 原句：自從釋迦牟尼佛轉法輪度眾生，
- 譯文：Since the time when Sakyamuni Buddha turned the Dharma wheel to deliver sentient beings,
- judge 選：`06785402` 經過特定時段。　信心 0.95　依據：譯文強調時間起點而非助人語義
- gold：`06785404` 助人得到佛法。

**250. 拿**　`wsd-拿-752a`　[non_dominant]
- 原句：只開放特定場地供學生拿號碼牌寄物。
- 譯文：Only specific areas are open for students to take numbered tickets for luggage storage.
- judge 選：`04011201` 用手取物或持物。　信心 0.90　依據：譯文中 take 承擔「拿取」語義
- gold：`04011202` 向特定對象取得主事者擁有或應該擁有的金錢或物品。

**251. 上**　`wsd-上-9cab`　[non_dominant]
- 原句：在歷史上曾經被滅亡過好幾次，
- 譯文：It has been conquered multiple times throughout history.
- judge 選：`04081314` 事件的發生在前述事物的範圍內。　信心 0.95　依據：譯文強調事件在歷史範圍內發生
- gold：`04081317` 按前述事物的觀點來陳述。

**256. 條**　`wsd-條-50d4`　[non_dominant]
- 原句：一開始就把這條小河川整理一下，
- 譯文：Start by tidying up this small river.
- judge 選：`06585924` 計算行進的路線的單位。　信心 0.90　依據：整句在說清理河流，強調路徑的單位
- gold：`06585906` 計算地面上長條型的建築物或自然景觀的單位。

**262. 平**　`wsd-平-cb19`　[non_dominant]
- 原句：車子的把手為平把，
- 譯文：The car has flat handlebars.
- judge 選：`06025201` 形容物體表面高度相同沒有凹凸起伏的。　信心 0.95　依據：flat handlebars 指車把手平坦無起伏的表面
- gold：`06025213` 形容高度相同的。

**263. 吃**　`wsd-吃-7df1`　[non_dominant]
- 原句：他們不像某些臺灣移民過的是「吃老本」的日子，
- 譯文：They don't live off their past like some Taiwanese immigrants do.
- judge 選：`05227001` 使物體經過口中吞入體內。　信心 0.95　依據：整句在說移民依賴過去經驗維生
- gold：`05227012` 比喻物品或能量因使用而漸漸減少。

**264. 代**　`wsd-代-38c7`　[non_dominant]
- 原句：這些是發生在這一代華人身上比較新的事情。
- 譯文：These are relatively new events that have happened to this generation of Chinese people.
- judge 選：`04016205` 年齡大致相同的一群人。　信心 0.95　依據：譯文中的 generation 指同一時代的人
- gold：`04016206` 計算年齡大致相同的一群人的單位。

**265. 度**　`wsd-度-85ca`　[non_dominant]
- 原句：毛高文也常以他高八度的音調嚷嚷兩人歌路不同，
- 譯文：Edgar Miles Bronfman Jr. also often shouted about their different musical paths in his high-pitched voice.
- judge 選：`05147620` 計算事件發生的次數的單位。　信心 0.90　依據：shouted about 表示強調或多次提及，對應計數單位
- gold：`05147619` 計算音程的單位。

**268. 道**　`wsd-道-e472`　[non_dominant]
- 原句：相信透過教育這最後一道丹藥可以拯救！
- 譯文：I believe that through education, this final elixir can bring salvation!
- judge 選：`04083505` 比喻處理事情或解決問題的方法。　信心 0.90　依據：elixir在此被譬喻為終極解方
- gold：`04083512` 計算步驟的單位。

**272. 大**　`wsd-大-dc2c`　[non_dominant]
- 原句：好大的一個螺殼！
- 譯文：What a huge shell!
- judge 選：`05227204` 形容程度超過比較對象的。　信心 0.90　依據：整句強調「巨大」的程度而非實際體積
- gold：`05227201` 形容體積超過比較對象的。

**273. 回**　`wsd-回-1e59`　[non_dominant]
- 原句：有一回他受命去孟家宅院取兩支手槍，
- 譯文：One time, he was ordered to go to the Meng family compound to retrieve two pistols.
- judge 選：`03019001` 從其它地方到原來的地方或處所。　信心 0.95　依據：譯文中「retrieve」表示取回原處
- gold：`03019008` 計算事件的單位。

**274. 就**　`wsd-就-fe97`　[non_dominant]
- 原句：要不然就是陰天。
- 譯文：Otherwise, it will be overcast.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.95　依據：otherwise 表示「若非如此則會」的充分條件
- gold：`05198307` 表強調說話者已知事實。

**280. 點**　`wsd-點-9076`　[non_dominant]
- 原句：就這點來說，
- 譯文：In this regard,
- judge 選：`04043808` 事件或過程中具顯著的指標。　信心 0.85　依據：In this regard 表示「在此方面」或「就此點而言」
- gold：`04043812` 指所陳述事件的部份或方面。

**281. 中**　`wsd-中-3be9`　[non_dominant]
- 原句：亦正發展中，
- 譯文：It is also under development.
- judge 選：`04004605` 在前述的機構或領域範圍。　信心 0.90　依據：under development 在前述領域或機構中進行
- gold：`04004618` 在事件的過程中。

**286. 拉**　`wsd-拉-4697`　[non_dominant]
- 原句：你是說你們那時候連手都沒有拉！
- 譯文：You said you didn't even hold hands at that time!
- judge 選：`05230801` 向主事者身體的方向施力而使後述對象順著施力方向移動。　信心 0.95　依據：譯文強調「沒有牽手」而非動作本身
- gold：`05230802` 兩手握在一起。

**287. 當**　`wsd-當-d0c0`　[non_dominant]
- 原句：而在將高山當郊山玩的途中，
- 譯文：While hiking in the mountains,
- judge 選：`04013907` 引介背景事件作為時間的範圍。　信心 0.95　依據：While hiking 表示在背景事件期間
- gold：`04013901` 前述對象的工作或身份是後述對象。

**289. 帶**　`wsd-帶-f9d9`　[non_dominant]
- 原句：所以視障生必須要仰賴別人帶他過馬路。
- 譯文：So visually impaired students have to rely on others to help them cross the road.
- judge 選：`06791407` 使特定對象跟著有支配權的人移動。　信心 0.90　依據：整句在說視障學生需他人協助移動
- gold：`06791413` 走在前面，引導前進方向。

**292. 中**　`wsd-中-4054`　[non_dominant]
- 原句：最後在呂尚叡小姐（ＩＩＩ服務部人員）、童敏惠小姐（台灣大學圖書館系統組主任）說明「填寫ＧｅｔｔｉｎｇＳｔａｒｔｅｄＷｉｔｈＩＮＮＯＰＡＣ」中圓滿結束了此次會議。
- 譯文：Finally, the meeting concluded successfully with explanations from Ms. Lü Shàng-ruì (staff member of the III Service Department) and Ms. Tóng Mǐn-huì (Director of the System Division at the National Taiwan University Library) on "Filling Out 'Getting Started with INNOPAC'."
- judge 選：`04004605` 在前述的機構或領域範圍。　信心 0.90　依據：譯文中「with explanations from...」指稱機構成員的職務範疇
- gold：`04004618` 在事件的過程中。

**293. 代**　`wsd-代-5679`　[non_dominant]
- 原句：由於本學期校方代學生聯合會向學生收取自治費，
- 譯文：The university collects self-governance fees on behalf of the student union this semester.
- judge 選：`07104504` 引介被代替的對象。　信心 0.95　依據：譯文中的 on behalf of 即為「代」在此承擔的語意
- gold：`07104502` 排除後述事項，使前述事項佔有其位。

**294. 空**　`wsd-空-94a8`　[non_dominant]
- 原句：誰好意思有一隻手是空的呢！
- 譯文：Who would be shameless enough to have one hand empty?
- judge 選：`06517331` 事物不具有實體的概念。　信心 0.90　依據：譯文強調「空手」即手中無實體物品
- gold：`06517316` 形容比喻特定對象沒有被使用。

**299. 上**　`wsd-上-34ff`　[non_dominant]
- 原句：在時間上適逢阿爾巴尼亞已故共黨首領霍查的遺孀妮克絲吉美。
- 譯文：At the time, it coincided with Nexhmije Hoxha, the widow of Albania's late communist leader Enver Hoxha.
- judge 選：`04081314` 事件的發生在前述事物的範圍內。　信心 0.90　依據：整句在說事件發生在某時期且與某人重疊
- gold：`04081317` 按前述事物的觀點來陳述。

**300. 條**　`wsd-條-7771`　[non_dominant]
- 原句：只求挽回一條垂危的生命，
- 譯文：I only seek to save a life hanging by a thread.
- judge 選：`06585924` 計算行進的路線的單位。　信心 0.90　依據：整句強調「一線生機」的「線」為路徑單位
- gold：`06585911` 計算動物性命的單位。

**301. 分**　`wsd-分-1598`　[non_dominant]
- 原句：分不清是夢是真。
- 譯文：I can't tell if it's a dream or reality.
- judge 選：`04146403` 將整體事物區隔成幾部份。　信心 0.90　依據：譯文強調夢與現實的區隔
- gold：`04146401` 特定對象分開。

**303. 子**　`wsd-子-daed`　[non_dominant]
- 原句：法華經長者窮子喻之中，
- 譯文：In the parable of the rich man and his poor son in the Lotus Sutra,
- judge 選：`07027902` 父母對自己所生育的男性後代的指稱。　信心 0.95　依據：譯文中「son」直接對應「子」的親屬稱謂
- gold：`07027904` 具有前述身份或從事前述工作的人。

**306. 用**　`wsd-用-ad93`　[non_dominant]
- 原句：依照戒急用忍檢討執行計畫，
- 譯文：In accordance with the "Refrain from Rashness, Emphasize Pragmatism" review and implementation plan,
- judge 選：`04017407` 引介事件所憑藉的方法或工具。　信心 0.90　依據：譯文中的 in accordance with 直接對應「用」的方法或工具義
- gold：`04017405` 比喻選擇後述有系統性的態度或方式。

**309. 代**　`wsd-代-2206`　[non_dominant]
- 原句：身為台塑的第二代，
- 譯文：As the second generation of the Formosa Plastics Group,
- judge 選：`04016205` 年齡大致相同的一群人。　信心 0.90　依據：「第二代」指年齡相近的一群人
- gold：`04016201` 生物血緣關係中所有與其始祖的距離相同的人所組成的團體。

**310. 面**　`wsd-面-572d`　[non_dominant]
- 原句：她曾在82年奪得區運5面金牌後因傷退出體操界，
- 譯文：She retired from gymnastics after winning five gold medals at the District Games in 1982 due to an injury.
- judge 選：`03028804` 事件被觀察到的情況或範圍。　信心 0.90　依據：整句在說她因傷退役，強調受傷後的狀態
- gold：`03028807` 計算牌狀物的單位。

**312. 分**　`wsd-分-1a74`　[non_dominant]
- 原句：分由七十一至七十七會計年度逐年編列預算，
- 譯文：The budget shall be allocated annually from fiscal years 71 to 77.
- judge 選：`04146403` 將整體事物區隔成幾部份。　信心 0.95　依據：譯文中的 allocated 表將預算分配到各年度
- gold：`04146408` 表分別。

**316. 點**　`wsd-點-87e4`　[non_dominant]
- 原句：就某一點而言，
- 譯文：In a certain sense,
- judge 選：`04043808` 事件或過程中具顯著的指標。　信心 0.90　依據：in a certain sense 指特定意義上的指標
- gold：`04043812` 指所陳述事件的部份或方面。

**317. 打開**　`wsd-打開-c078`　[non_dominant]
- 原句：打開這個知識的寶庫。
- 譯文：Open this treasure trove of knowledge.
- judge 選：`06548101` 移動封閉門窗的裝置物，使其空間的出入口不被封閉。　信心 0.95　依據：整句在說開啟知識寶庫的入口
- gold：`06548102` 將控制特定對象使其無法被打開或使用的裝置解除。

**322. 回**　`wsd-回-27ca`　[non_dominant]
- 原句：這回換野狼的屁股卡在洞口了，
- 譯文：The wolf's butt got stuck in the hole this time.
- judge 選：`03019001` 從其它地方到原來的地方或處所。　信心 0.95　依據：譯文中的 got stuck in 表達「回到」原處被困
- gold：`03019008` 計算事件的單位。

**323. 上**　`wsd-上-94b4`　[non_dominant]
- 原句：在個人資料和事件的處理上，
- 譯文：In the handling of personal data and incidents,
- judge 選：`04081314` 事件的發生在前述事物的範圍內。　信心 0.90　依據：譯文中「incidents」對應「上」的範圍語義
- gold：`04081317` 按前述事物的觀點來陳述。

**328. 用**　`wsd-用-cc15`　[non_dominant]
- 原句：是取之於消費者、用之於消費者。
- 譯文：It is taken from consumers and used for consumers.
- judge 選：`04017407` 引介事件所憑藉的方法或工具。　信心 0.90　依據：譯文強調「被取自消費者後用於消費者」的方法或工具
- gold：`04017401` 利用特定對象的特定功能。

**329. 邊**　`wsd-邊-fb5e`　[non_dominant]
- 原句：調整的方法是手握雙筒鏡的兩邊，
- 譯文：Adjust the method by holding both sides of the binoculars.
- judge 選：`06584404` 特定對象與其他鄰界對象交界的地方。　信心 0.90　依據：sides 對應邊界交界處
- gold：`06584406` 特定地區中位於前述方向邊緣的地點。

**335. 場**　`wsd-場-9bec`　[non_dominant]
- 原句：除了在萬芳醫院的三場演出之外，
- 譯文：In addition to the three performances at Wanfang Hospital,
- judge 選：`06721709` 計算經過安排的活動的單位。　信心 0.95　依據：「場」在此指經安排的活動單位
- gold：`06721707` 計算戲劇中較小段落的單位。

**342. 就**　`wsd-就-0a6d`　[non_dominant]
- 原句：昏沉就是愛睡，
- 譯文：Drowsiness is just loving to sleep.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：整句強調「昏睏就是愛睡」的充分條件關係
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**345. 中**　`wsd-中-d613`　[non_dominant]
- 原句：在這次選戰中佔了有利地位。
- 譯文：They have an advantageous position in this election campaign.
- judge 選：`04004605` 在前述的機構或領域範圍。　信心 0.95　依據：in this election campaign 表達「在選舉這個領域/範圍」
- gold：`04004618` 在事件的過程中。

**346. 去**　`wsd-去-3d3f`　[non_dominant]
- 原句：我們能去嗎？
- 譯文：Are we able to go?
- judge 選：`06559205` 表前述對象進行後述事件。　信心 0.95　依據：整句在詢問能否進行某事
- gold：`06559201` 向特定地點移動。

**347. 錢**　`wsd-錢-0083`　[non_dominant]
- 原句：而讀書人則是最沒有錢的。
- 譯文：Scholars are often the poorest.
- judge 選：`06015105` 經費、錢財。　信心 0.95　依據：整句在說學者通常缺乏經費
- gold：`06015107` 比喻財富。

**348. 熱**　`wsd-熱-3583`　[non_dominant]
- 原句：無形的過熱，
- 譯文：Invisible overheating.
- judge 選：`05228701` 形容溫度高或感覺溫度高的。　信心 0.95　依據：overheating 直接對應溫度過高
- gold：`05228707` 形容身體陽氣亢盛。

**360. 轉**　`wsd-轉-cbbd`　[non_dominant]
- 原句：他三個手指悠然轉著那只淡青色玉鐲。
- 譯文：He leisurely twirled the light blue jade bracelet with three fingers.
- judge 選：`05228803` 物體繞著軸心，作圓周運動。　信心 0.95　依據：整句在說手指頭讓玉鐲做圓周運動
- gold：`05228802` 使物體維持本身的軸心，做連續改變方向的運動。

**365. 就**　`wsd-就-d690`　[non_dominant]
- 原句：心浮動就是道心不堅固，
- 譯文：A restless mind is one that lacks a firm spiritual foundation.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：整句強調缺乏基礎導致不安
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**368. 大**　`wsd-大-6481`　[non_dominant]
- 原句：大蛇竟然把嘴張開，
- 譯文：The serpent actually opened its mouth wide.
- judge 選：`05227204` 形容程度超過比較對象的。　信心 0.90　依據：wide 在此形容嘴巴張開的程度
- gold：`05227201` 形容體積超過比較對象的。

**370. 分**　`wsd-分-ea80`　[non_dominant]
- 原句：數十年不分寒暑，
- 譯文：For decades, summer and winter have not been distinguished.
- judge 選：`04146403` 將整體事物區隔成幾部份。　信心 0.95　依據：譯文強調夏冬未被區隔，符合將整體分開之意
- gold：`04146405` 依特性做分類。

**371. 發**　`wsd-發-5680`　[non_dominant]
- 原句：是很願意國內所有發卡機構能研擬出一套辦法來針對如果受款行號未照約定履行交付等值之物品，
- 譯文：I sincerely hope that all domestic card-issuing institutions can develop a solution to address situations where the acquiring bank fails to fulfill its contractual obligation to deliver equivalent goods.
- judge 選：`06724101` 按特定的分配原則將物品給特定對象。　信心 0.85　依據：譯文強調銀行需履行交付商品的義務
- gold：`06724102` 事先核准後將後述證件或執照給特定對象。

**373. 拿**　`wsd-拿-fe6f`　[non_dominant]
- 原句：有些人因「太紅」怕整個晚上因不停拿宵夜而無法念書，
- 譯文：Some people avoid eating late-night snacks because they're afraid of being "too engaged" in studying all night.
- judge 選：`04011201` 用手取物或持物。　信心 0.95　依據：譯文中用手拿東西的動作被「avoid eating」隱含
- gold：`04011202` 向特定對象取得主事者擁有或應該擁有的金錢或物品。

**374. 面**　`wsd-面-43d6`　[non_dominant]
- 原句：面無表情地望著大家，
- 譯文：He stared blankly at everyone.
- judge 選：`03028804` 事件被觀察到的情況或範圍。　信心 0.90　依據：stared blankly 表達「注視的情況」而非身體部位
- gold：`03028801` 動物頭從額頭到下巴的部分。

**376. 上**　`wsd-上-21f2`　[non_dominant]
- 原句：一切都只停留在勞作的程度上。
- 譯文：Everything remains at the level of mere labor.
- judge 選：`04081314` 事件的發生在前述事物的範圍內。　信心 0.90　依據：譯文強調「保持在某層級」即範圍內
- gold：`04081317` 按前述事物的觀點來陳述。

**378. 要**　`wsd-要-f6e4`　[non_dominant]
- 原句：要完成還早得很呢！
- 譯文：It's going to take a long time to finish!
- judge 選：`06636905` 表按照道理必須做後述事件。　信心 0.95　依據：譯文強調「需要很長時間」符合「按道理必須」的語義
- gold：`06636907` 表預期後述事件會在很短的時間內發生。

**379. 條**　`wsd-條-65cd`　[non_dominant]
- 原句：美國的Ｆ１１１戰鬥轟炸機，廿六日晚精確炸毀科威特境內阿馬迪貯油區的兩條輸油控制管，
- 譯文：The U.S. F-111 fighter-bomber precisely destroyed two oil control pipelines at the Al-Ahmadi storage facility in Kuwait on the night of the 26th.
- judge 選：`06585924` 計算行進的路線的單位。　信心 0.95　依據：譯文提到摧毀兩條輸油管線，強調路線而非單位
- gold：`06585903` 計算形狀細而長的物體的單位。

**386. 正**　`wsd-正-e48f`　[non_dominant]
- 原句：其謬誤正如同我們總習於率爾用一個人比擬另一個人。
- 譯文：Just as we often hastily compare one person to another.
- judge 選：`07009821` 表動作進行中或狀態持續中。　信心 0.90　依據：譯文中的 compare 顯示動作正在進行
- gold：`07009822` 表前述對象不經刻意安排而完全符合後述描述。

**390. 條**　`wsd-條-6af3`　[non_dominant]
- 原句：或者手拉手走一條霪雨霏霏的街。
- 譯文：Or hand in hand, stroll down a rain-soaked street.
- judge 選：`06585924` 計算行進的路線的單位。　信心 0.90　依據：street 在譯文中代表行進路線
- gold：`06585906` 計算地面上長條型的建築物或自然景觀的單位。

**394. 空**　`wsd-空-3ec9`　[non_dominant]
- 原句：２．胃酸排空時間檢查。
- 譯文：Gastric emptying time examination.
- judge 選：`06517331` 事物不具有實體的概念。　信心 0.90　依據：empty在此指胃部排空，為抽象概念
- gold：`06517312` 形容比喻特定時段沒有排滿活動。

**399. 邊**　`wsd-邊-81c8`　[non_dominant]
- 原句：現在井邊圍上了欄杆，
- 譯文：A railing has been installed around the well.
- judge 選：`06584404` 特定對象與其他鄰界對象交界的地方。　信心 0.95　依據：整句在說圍繞水井安裝護欄
- gold：`06584405` 表靠近參考點的地方。

---

成本：801 次呼叫 / 1,234,141 tokens / 244.9s / 快取命中 0
run: `runs\20260822-235029-wsd-674ed1.jsonl`