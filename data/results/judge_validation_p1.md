# judge 驗證　n=20

> judge：`ithu/gpt-oss-120b`　人工標註為盲標（未見 gold、未見 judge 判定）。

## 三個一致率

| 比較 | 一致 | 比例 | 95% CI | 意義 |
| --- | :-: | :-: | :-: | --- |
| **judge vs 人工** | 10/20 | 50% | [30, 70]% | **主指標**：judge 判得準不準 |
| 人工 vs gold | 15/20 | 75% | [53, 89]% | gold 本身可不可信（CWN 標註 vs 母語者對譯文的判斷） |
| judge vs gold | 13/20 | 65% | [43, 82]% | 即 200 筆基準所用的正確率，此為子樣本 |

### 判準（v3 架構書 §P3）

| 門檻 | 狀態 |
| --- | --- |
| <60% judge 明顯亂判 → 停 | 🔴 觸發 |
| 60–85% 大致對 → 繼續 | — |
| ≥85% 正式驗證門檻 | 未達成 |

## NONE 的使用

| | judge | 人工 |
| --- | :-: | :-: |
| 判為 NONE | 3 | 2 |

雙方皆 NONE 0　僅 judge 判 NONE 3　僅人工判 NONE 2

⚠️ judge 多判了 3 筆 NONE——200 筆基準中 NONE 佔 28%，其中 68% 經分類為「譯文有譯出但 judge 認不出」，與此一致。

## 混淆矩陣（judge × 人工，以是否等於 gold 表示）

| | 人工=gold | 人工≠gold | 人工=NONE |
| --- | :-: | :-: | :-: |
| judge=gold | 10 | 2 | 1 |
| judge≠gold | 3 | 0 | 1 |
| judge=NONE | 2 | 1 | 0 |

---

## 不一致的案例（judge ≠ 人工）

### 03　**強**　`wsd-強-7c81`　[non_dominant]
- 原句：國男組也將進行四強交叉準決賽，
- 譯文：The men's team will also compete in the semifinals crossover.
- **人工**：`09250305` 競賽中排名在前述範圍的特定對象。
- **judge**：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「強」相關的意涵
- gold：`09250305` 競賽中排名在前述範圍的特定對象。　← 人工同 gold

### 04　**收**　`wsd-收-ea9a`　[dominant]
- 原句：我們不收支票。
- 譯文：We do not accept checks.
- **人工**：`03039303` 收取金錢。
- **judge**：`03039301` 接到。　信心 0.95　依據：accept checks 為接到支票
- gold：`03039303` 收取金錢。　← 人工同 gold

### 08　**掛**　`wsd-掛-3cf0`　[dominant]
- 原句：比如今八三歲父親至今還掛在牆上親自題著「音容宛在」的少婦像，
- 譯文：A portrait of a young woman with the inscription "音容宛在" still hangs on the wall, painted by my 83-year-old father.
- **人工**：`06701402` 特定物體的一端被支撐而維持在特定高度。
- **judge**：`06701401` 支撐特定物體的一端使其維持在特定高度。　信心 0.98　依據：hangs on the wall 指畫像被支撐懸掛
- gold：`06701401` 支撐特定物體的一端使其維持在特定高度。　← judge 同 gold

### 10　**去**　`wsd-去-bdaa`　[non_dominant]
- 原句：走到了最常去最熟悉的圖書館，
- 譯文：I arrived at the most frequently visited and familiar library.
- **人工**：`06559204` 隨動作到達前述地點。
- **judge**：`06559201` 向特定地點移動。　信心 0.90　依據：arrived at 表向特定地點移動，對應去的方向義
- gold：`06559201` 向特定地點移動。　← judge 同 gold

### 12　**條**　`wsd-條-2146`　[non_dominant]
- 原句：教育部在九月初以不符合師資培育法第七條及師範教育精神為由，
- 譯文：The Ministry of Education ruled in early September that it did not comply with Article 7 of the Teacher Education Act and the spirit of normal education.
- **人工**：`NONE` （NONE）
- **judge**：`06585929` 法規結構分類的一種，在「節」之下、「項」之上。　信心 0.95　依據：Article 7 指法律條文，符合法規結構分類義項
- gold：`06585929` 法規結構分類的一種，在「節」之下、「項」之上。　← judge 同 gold

### 16　**拿**　`wsd-拿-7496`　[non_dominant]
- 原句：偶爾有幾個好心人拿東西給我吃，
- 譯文：Occasionally, a few kind people bring me something to eat.
- **人工**：`04011205` 提供金錢或其他有價值物給後述對象。
- **judge**：`04011201` 用手取物或持物。　信心 0.95　依據：bring 表用手取物或持物
- gold：`04011205` 提供金錢或其他有價值物給後述對象。　← 人工同 gold

### 17　**深**　`wsd-深-55e4`　[non_dominant]
- 原句：自己深知道頭銜無用，
- 譯文：I know full well that titles are useless.
- **人工**：`06663313` 表超過平常的程度。
- **judge**：`06663316` 形容前述狀態的程度高，通常是負面。　信心 0.85　依據：full well 中的 well 表程度高且負面
- gold：`06663313` 表超過平常的程度。　← 人工同 gold

### 18　**去**　`wsd-去-6d5f`　[dominant]
- 原句：以及親手去使用這些資料。
- 譯文：And personally use this data.
- **人工**：`06559205` 表前述對象進行後述事件。
- **judge**：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「去」相關的動作或方向義
- gold：`06559205` 表前述對象進行後述事件。　← 人工同 gold

### 19　**當**　`wsd-當-d0c0`　[non_dominant]
- 原句：而在將高山當郊山玩的途中，
- 譯文：And along the way, while treating towering mountains like mere hills for a casual outing,
- **人工**：`NONE` （NONE）
- **judge**：`04013907` 引介背景事件作為時間的範圍。　信心 0.90　依據：while 表達背景事件作為時間範圍
- gold：`04013901` 前述對象的工作或身份是後述對象。

### 20　**條**　`wsd-條-63fe`　[non_dominant]
- 原句：森林之家的每條街道，
- 譯文：Every street in Forest Home
- **人工**：`06585924` 計算行進的路線的單位。
- **judge**：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「條」相關的量詞或概念
- gold：`06585906` 計算地面上長條型的建築物或自然景觀的單位。

---

## 逐筆

| # | 詞 | 人工 | judge | gold | j=h | h=g | j=g |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | 死 | 5202 | 5202 | 5202 | ✅ | ✅ | ✅ |
| 2 | 頭 | 3001 | 3001 | 3001 | ✅ | ✅ | ✅ |
| 3 | 強 | 0305 | NONE | 0305 | ❌ | ✅ | ❌ |
| 4 | 收 | 9303 | 9301 | 9303 | ❌ | ✅ | ❌ |
| 5 | 低 | 8406 | 8406 | 8406 | ✅ | ✅ | ✅ |
| 6 | 心 | 1612 | 1612 | 1612 | ✅ | ✅ | ✅ |
| 7 | 折 | 3113 | 3113 | 3113 | ✅ | ✅ | ✅ |
| 8 | 掛 | 1402 | 1401 | 1401 | ❌ | ❌ | ✅ |
| 9 | 做 | 4301 | 4301 | 4301 | ✅ | ✅ | ✅ |
| 10 | 去 | 9204 | 9201 | 9201 | ❌ | ❌ | ✅ |
| 11 | 破 | 1422 | 1422 | 1422 | ✅ | ✅ | ✅ |
| 12 | 條 | NONE | 5929 | 5929 | ❌ | ❌ | ✅ |
| 13 | 心 | 1612 | 1612 | 1612 | ✅ | ✅ | ✅ |
| 14 | 粗 | 1801 | 1801 | 1801 | ✅ | ✅ | ✅ |
| 15 | 高 | 0615 | 0615 | 0615 | ✅ | ✅ | ✅ |
| 16 | 拿 | 1205 | 1201 | 1205 | ❌ | ✅ | ❌ |
| 17 | 深 | 3313 | 3316 | 3313 | ❌ | ✅ | ❌ |
| 18 | 去 | 9205 | NONE | 9205 | ❌ | ✅ | ❌ |
| 19 | 當 | NONE | 3907 | 3901 | ❌ | ❌ | ❌ |
| 20 | 條 | 5924 | NONE | 5906 | ❌ | ❌ | ❌ |