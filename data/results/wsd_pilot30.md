# MT 詞義錯誤基準　n=30

> ⚠️ **judge 未經人工驗證前，所有數字標為 preliminary。**
> 翻譯：`ithu/mistral-small-4`　judge：`ithu/gpt-oss-120b`（judge_cross：不同訓練來源，非同一模型）
> 任務：CWN-SemCor 句子 → 翻成英文 → judge 判譯文表達哪個義項 → 比對 CWN gold

## 停止判準

- ✅ 全部未觸發

## 整體

| 項目 | 值 |
| --- | :-: |
| 總題數 | 30 |
| translation_failed | 0/30（0%） |
| error | 0/30（0%） |
| judge 回 NONE | 6/30（20%） |
| **可判定** | 24/30（80%） |
| **義項正確率** | **0.667**　[0.467, 0.820] |

## 分層 ⭐ 主結果

| 層 | n（可判定） | 正確 | 正確率 | 95% CI |
| --- | :-: | :-: | :-: | :-: |
| 主流（gold 為最高頻） | 13 | 10 | 0.769 | [0.497, 0.918] |
| 非主流 | 11 | 6 | 0.545 | [0.280, 0.787] |

**兩層之差（主流 − 非主流）**：+22.4pp　95% CI [-14.0, +57.3]pp　p≈0.259

| 觀察 | 判讀 |
| --- | --- |
| 主流高、非主流低 | 走頻率捷徑，沒讀脈絡 |
| 兩層相近 | 真的在讀脈絡 |
| 兩層都低 | 任務太難或 judge 有問題 |

---

## 逐筆（請掃一遍判斷 judge 合不合理）

| # | 詞 | 原句 | 譯文 | judge 選的 | gold | 對 |
| :-: | :-: | --- | --- | --- | --- | :-: |
| 1 | 收 | 我們不收支票。 | We do not accept checks. | `03039301` | `03039303` | ❌ |
| 2 | 上 | 街頭上到處也可以看到咖啡店． | You can see coffee shops everywhere on the streets. | `04081315` | `04081314` | ❌ |
| 3 | 心 | 以極為艱難的說話方式表達他心中的感想。 | He expressed his thoughts in an excruciatingly diffi | `05231612` | `05231612` | ✅ |
| 4 | 死 | 皮皮掉到山谷後居然沒死， | Pipi fell into the valley but surprisingly survived. | `NONE` | `05035202` | — |
| 5 | 低 | 創下八十六年以來同季首度滑落千億元以下的最低紀錄。 | It marked the lowest record in over 86 years to fall | `06748406` | `06748406` | ✅ |
| 6 | 歲 | 今年整整滿一百歲了。 | This year marks exactly one hundred years. | `06559403` | `06559405` | ❌ |
| 7 | 掛 | 比如今八三歲父親至今還掛在牆上親自題著「音容宛在」的 | A portrait of a young woman with the inscription "音容 | `06701401` | `06701401` | ✅ |
| 8 | 坐 | 他習慣坐在客運公司走廊一角， | He is used to sitting in a corner of the corridor at | `05223901` | `05223901` | ✅ |
| 9 | 折 | 打七五折是四百六十五。 | It's NT$465 after a 25% discount. | `07033113` | `07033113` | ✅ |
| 10 | 季 | 亞洲出口成長仍於二○○一年第四季反彈回升。 | Asia's export growth rebounded in the fourth quarter | `07026505` | `07026505` | ✅ |
| 11 | 心 | 心裡很不是滋味。 | It leaves a bitter taste in my heart. | `05231612` | `05231612` | ✅ |
| 12 | 死 | 等我什麼時候也死了， | When I die someday. | `05035202` | `05035202` | ✅ |
| 13 | 頭 | 做出一個大小適中的頭， | Make a head of moderate size. | `03043001` | `03043001` | ✅ |
| 14 | 粗 | 英勇的消防隊員合力舉起又粗又大的水管， | Brave firefighters worked together to lift the thick | `06711801` | `06711801` | ✅ |
| 15 | 去 | 以及親手去使用這些資料。 | And personally use this data. | `NONE` | `06559205` | — |
| 16 | 條 | 森林之家的每條街道， | Every street in Forest Home | `NONE` | `06585906` | — |
| 17 | 下 | 在Ｃ目錄下打）ｐａｔｈ）。 | Create a path under the C drive. | `04081803` | `04081808` | ❌ |
| 18 | 高 | 照說素質都很高， | The quality is supposed to be very high. | `06010615` | `06010615` | ✅ |
| 19 | 場 | 除了在萬芳醫院的三場演出之外， | In addition to the three performances at Wanfang Hos | `NONE` | `06721707` | — |
| 20 | 吃 | 「天生我才必有用」、「吃得苦中苦， | "Great minds have aims, petty minds have wishes."
"O | `NONE` | `05227009` | — |
| 21 | 拿 | 偶爾有幾個好心人拿東西給我吃， | Occasionally, a few kind people bring me something t | `04011201` | `04011205` | ❌ |
| 22 | 當 | 而在將高山當郊山玩的途中， | And along the way, while treating towering mountains | `04013907` | `04013901` | ❌ |
| 23 | 強 | 國男組也將進行四強交叉準決賽， | The men's team will also compete in the semifinals c | `NONE` | `09250305` | — |
| 24 | 去 | 她去過多少美國市場， | How many U.S. markets has she visited? | `06559201` | `06559201` | ✅ |
| 25 | 面 | 面無表情地望著大家， | He stared at everyone with a blank expression. | `03028803` | `03028801` | ❌ |
| 26 | 深 | 自己深知道頭銜無用， | I know full well that titles are useless. | `06663316` | `06663313` | ❌ |
| 27 | 去 | 走到了最常去最熟悉的圖書館， | I arrived at the most frequently visited and familia | `06559201` | `06559201` | ✅ |
| 28 | 破 | 自己發球局反在第六局被破， | I was broken in my own serve game in the sixth set. | `06761422` | `06761422` | ✅ |
| 29 | 條 | 教育部在九月初以不符合師資培育法第七條及師範教育精神 | The Ministry of Education ruled in early September t | `06585929` | `06585929` | ✅ |
| 30 | 做 | 剝取牠們的毛皮做標本， | Extract their fur to make specimens. | `06664301` | `06664301` | ✅ |

### 錯誤與 NONE 的細節

**1. 收**　`wsd-收-ea9a`　[dominant]
- 原句：我們不收支票。
- 譯文：We do not accept checks.
- judge 選：`03039301` 接到。　信心 0.95　依據：accept checks 為接到支票
- gold：`03039303` 收取金錢。

**2. 上**　`wsd-上-10d2`　[dominant]
- 原句：街頭上到處也可以看到咖啡店．
- 譯文：You can see coffee shops everywhere on the streets.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：on the streets 表達以街道為範圍主題
- gold：`04081314` 事件的發生在前述事物的範圍內。

**4. 死**　`wsd-死-fa11`　[dominant]
- 原句：皮皮掉到山谷後居然沒死，
- 譯文：Pipi fell into the valley but surprisingly survived.
- judge 選：`NONE` （NONE）　信心 0.95　依據：survived 指未失去生命，未直接對應義項
- gold：`05035202` 形容生物失去生命。

**6. 歲**　`wsd-歲-5ae2`　[dominant]
- 原句：今年整整滿一百歲了。
- 譯文：This year marks exactly one hundred years.
- judge 選：`06559403` 計算時間的單位，一歲有十二個月。　信心 0.95　依據：year 為計算時間的單位，對應「歲」的時間單位義
- gold：`06559405` 計算年齡的單位。

**15. 去**　`wsd-去-6d5f`　[dominant]
- 原句：以及親手去使用這些資料。
- 譯文：And personally use this data.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「去」相關的動作或方向義
- gold：`06559205` 表前述對象進行後述事件。

**16. 條**　`wsd-條-63fe`　[non_dominant]
- 原句：森林之家的每條街道，
- 譯文：Every street in Forest Home
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「條」相關的量詞或概念
- gold：`06585906` 計算地面上長條型的建築物或自然景觀的單位。

**17. 下**　`wsd-下-496b`　[non_dominant]
- 原句：在Ｃ目錄下打）ｐａｔｈ）。
- 譯文：Create a path under the C drive.
- judge 選：`04081803` 鄰近前述物體的底部或低於該物體位置。　信心 0.95　依據：under 譯為「在...下方」，指位置低於參考點
- gold：`04081808` 比喻階級架構中低於前述階級的階級。

**19. 場**　`wsd-場-9bec`　[non_dominant]
- 原句：除了在萬芳醫院的三場演出之外，
- 譯文：In addition to the three performances at Wanfang Hospital,
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「場」相關的詞彙
- gold：`06721707` 計算戲劇中較小段落的單位。

**20. 吃**　`wsd-吃-cf63`　[non_dominant]
- 原句：「天生我才必有用」、「吃得苦中苦，
- 譯文："Great minds have aims, petty minds have wishes."
"Only through hardship can one achieve greatness."
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「吃」相關的意涵
- gold：`05227009` 比喻經歷後述負面事件。

**21. 拿**　`wsd-拿-7496`　[non_dominant]
- 原句：偶爾有幾個好心人拿東西給我吃，
- 譯文：Occasionally, a few kind people bring me something to eat.
- judge 選：`04011201` 用手取物或持物。　信心 0.95　依據：bring 表用手取物或持物
- gold：`04011205` 提供金錢或其他有價值物給後述對象。

**22. 當**　`wsd-當-d0c0`　[non_dominant]
- 原句：而在將高山當郊山玩的途中，
- 譯文：And along the way, while treating towering mountains like mere hills for a casual outing,
- judge 選：`04013907` 引介背景事件作為時間的範圍。　信心 0.90　依據：while 表達背景事件作為時間範圍
- gold：`04013901` 前述對象的工作或身份是後述對象。

**23. 強**　`wsd-強-7c81`　[non_dominant]
- 原句：國男組也將進行四強交叉準決賽，
- 譯文：The men's team will also compete in the semifinals crossover.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「強」相關的意涵
- gold：`09250305` 競賽中排名在前述範圍的特定對象。

**25. 面**　`wsd-面-43d6`　[non_dominant]
- 原句：面無表情地望著大家，
- 譯文：He stared at everyone with a blank expression.
- judge 選：`03028803` 面對觀察者的方向。　信心 0.95　依據：expression 指臉部表情，對應面的方向義
- gold：`03028801` 動物頭從額頭到下巴的部分。

**26. 深**　`wsd-深-55e4`　[non_dominant]
- 原句：自己深知道頭銜無用，
- 譯文：I know full well that titles are useless.
- judge 選：`06663316` 形容前述狀態的程度高，通常是負面。　信心 0.85　依據：full well 中的 well 表程度高且負面
- gold：`06663313` 表超過平常的程度。

---

成本：60 次呼叫 / 37,542 tokens / 22.4s / 快取命中 30
run: `runs\20260818-153842-wsd-96576b.jsonl`