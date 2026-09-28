# MT 詞義錯誤基準　n=200

> ⚠️ **judge 未經人工驗證前，所有數字標為 preliminary。**
> 翻譯：`ithu/mistral-small-4`　judge：`ithu/gpt-oss-120b`（judge_cross：不同訓練來源，非同一模型）
> 任務：CWN-SemCor 句子 → 翻成英文 → judge 判譯文表達哪個義項 → 比對 CWN gold

## 停止判準

- ✅ 全部未觸發

## 整體

| 項目 | 值 |
| --- | :-: |
| 總題數 | 200 |
| translation_failed | 0/200（0%） |
| error | 0/200（0%） |
| judge 回 NONE | 56/200（28%） |
| **可判定** | 144/200（72%） |
| **義項正確率** | **0.618**　[0.537, 0.693] |

## 分層 ⭐ 主結果

| 層 | n（可判定） | 正確 | 正確率 | 95% CI |
| --- | :-: | :-: | :-: | :-: |
| 主流（gold 為最高頻） | 75 | 50 | 0.667 | [0.554, 0.763] |
| 非主流 | 69 | 39 | 0.565 | [0.448, 0.676] |

**兩層之差（主流 − 非主流）**：+10.1pp　95% CI [-6.0, +25.6]pp　p≈0.205

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
| 譯文沒譯出該詞 | 18 | 32%　[0.214, 0.452] | **NONE 正確**，是翻譯的遺漏不是 judge 的錯 |
| 譯文有譯出但 judge 認不出 | 38 | 68%　[0.548, 0.786] | **judge 的問題**，計入 judge 錯誤率 |
| 未分類 | 0 | — | 成因分類呼叫失敗 |

NONE 總數 56／200，已分類 56

---

## (b) 錯誤時模型選了哪個義項 ⭐ 與 CHA-Gen 的銜接

> CHA-Gen 發現「模型偏好主流解讀」。若成立，本專案的錯誤應集中在
> 該詞的最高頻義項那一側。隨機基準為 1/候選數的加權平均。

- 錯誤題數：55
- 其中選到**最高頻義項**：12（21.8%，95% CI [12.9, 34.4]%）
- 隨機基準：13.4%
- **未超過隨機基準（CI 涵蓋之），尚不足以支持**

選中義項的頻率排名分布：第1名 12　第2名 12　第3名 8　第4名 4　第5名 6　第6名 5　第7名 5　第8名 3

---

## (c) 長度稽核

> 問「答錯的題目句子是否較長」。分層報告——聚合值會正負相消
> （CHA-Gen 18 組中 12 組顯著、方向相反，中位數卻是 0.490）。
> 此處 `ambiguity_type` 欄位承載的是 stratum。


| 分層 | 特徵 | n（錯／對） | AUC | SE | 95% CI | 效應量 | 方向 | 排除 0.5 |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 整體 | probe_span 標點數 | 55／89 | 0.478 | 0.049 | [0.381, 0.575] | 0.022 | 選對者較長 | — |
| 整體 | probe_span 字元數 | 55／89 | 0.501 | 0.050 | [0.403, 0.598] | 0.001 | 選錯者較長 | — |
| 整體 | full_input 字元數 | 55／89 | 0.501 | 0.050 | [0.403, 0.598] | 0.001 | 選錯者較長 | — |
| 整體 | probe_span 詞數估計 | 55／89 | 0.501 | 0.050 | [0.403, 0.598] | 0.001 | 選錯者較長 | — |
| 整體 | context 字元數 | 55／89 | 0.500 | 0.050 | [0.403, 0.597] | 0.000 | — | — |
| target_word=去 | probe_span 字元數 | 5／4 | 0.250 | 0.176 | [0.000, 0.595] | 0.250 | 選對者較長 | — |
| target_word=去 | full_input 字元數 | 5／4 | 0.250 | 0.176 | [0.000, 0.595] | 0.250 | 選對者較長 | — |
| target_word=去 | probe_span 詞數估計 | 5／4 | 0.250 | 0.176 | [0.000, 0.595] | 0.250 | 選對者較長 | — |
| ambiguity_type=dominant | probe_span 字元數 | 25／50 | 0.398 | 0.068 | [0.265, 0.530] | 0.102 | 選對者較長 | — |
| ambiguity_type=dominant | full_input 字元數 | 25／50 | 0.398 | 0.068 | [0.265, 0.530] | 0.102 | 選對者較長 | — |
| ambiguity_type=dominant | probe_span 詞數估計 | 25／50 | 0.398 | 0.068 | [0.265, 0.530] | 0.102 | 選對者較長 | — |
| target_word=去 | probe_span 標點數 | 5／4 | 0.400 | 0.201 | [0.007, 0.793] | 0.100 | 選對者較長 | — |
| ambiguity_type=non_dominant | probe_span 字元數 | 30／39 | 0.594 | 0.070 | [0.458, 0.731] | 0.094 | 選錯者較長 | — |
| ambiguity_type=non_dominant | full_input 字元數 | 30／39 | 0.594 | 0.070 | [0.458, 0.731] | 0.094 | 選錯者較長 | — |
| ambiguity_type=non_dominant | probe_span 詞數估計 | 30／39 | 0.594 | 0.070 | [0.458, 0.731] | 0.094 | 選錯者較長 | — |
| ambiguity_type=non_dominant | probe_span 標點數 | 30／39 | 0.463 | 0.070 | [0.325, 0.600] | 0.037 | 選對者較長 | — |
| ambiguity_type=dominant | probe_span 標點數 | 25／50 | 0.490 | 0.071 | [0.351, 0.629] | 0.010 | 選對者較長 | — |
| ambiguity_type=dominant | context 字元數 | 25／50 | 0.500 | 0.071 | [0.360, 0.640] | 0.000 | — | — |
| ambiguity_type=non_dominant | context 字元數 | 30／39 | 0.500 | 0.071 | [0.362, 0.638] | 0.000 | — | — |
| target_word=去 | context 字元數 | 5／4 | 0.500 | 0.204 | [0.100, 0.900] | 0.000 | — | — |

**CI 排除 0.5 的項目：0 / 20**

沒有任何分層的長度特徵能顯著預測選錯。

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
| 16 | 回 | 預計七月結婚的郭思宏利用寒假專程由美國回臺灣與女友拍 | Vicky and her fiancé, Kuo Szu-hung, who plans to get | `03019001` | `03019001` | ✅ |
| 17 | 回 | 每天晚上她回乘務隊的時候， | Every night when she returns to the duty team. | `03019001` | `03019001` | ✅ |
| 18 | 拍 | 一走紅大家都搶著找她拍， | Once she became popular, everyone scrambled to colla | `08028001` | `08028004` | ❌ |
| 19 | 去 | 你先去預備圖章， | Please go prepare the seal first. | `06559201` | `06559205` | ❌ |
| 20 | 頭 | 頭上還要綁布條， | You still have to tie a headband. | `03043001` | `03043001` | ✅ |
| 21 | 拍 | 希望能多拍些劇情片。 | I hope we can make more narrative films. | `08028003` | `08028004` | ❌ |
| 22 | 歲 | 一個在三十歲之前沒有成為社會主義信徒的人， | A person who hasn't become a socialist believer befo | `06559405` | `06559405` | ✅ |
| 23 | 支 | 而韓國隊卻只有七支。 | However, the South Korean team only has seven. | `NONE` | `03056210` | — |
| 24 | 上 | 就把媽祖在海上顯靈的事蹟， | Mazu's miraculous manifestations at sea | `NONE` | `04081314` | — |
| 25 | 坐 | 我坐在書桌前， | I am sitting at my desk. | `05223901` | `05223901` | ✅ |
| 26 | 行 | 我們演習一下就行了， | Let's just practice. | `06775707` | `06775711` | ❌ |
| 27 | 起 | 報名自即日起受理， | Registration is now open. | `04004828` | `04004801` | ❌ |
| 28 | 高 | 台大最高， | National Taiwan University is the best. | `06010615` | `06010610` | ❌ |
| 29 | 心 | 心中非常不甘願， | I am very reluctant. | `05231612` | `05231612` | ✅ |
| 30 | 說 | 陳總統說去年三一八事件今年可能重演； | President Tsai said that the March 18 incident last  | `05212401` | `05212401` | ✅ |
| 31 | 明 | 明起路邊停車巡場管理員將不再受理民眾繳交停車費， | Starting tomorrow, roadside parking patrol officers  | `07003401` | `07003401` | ✅ |
| 32 | 中 | 每家主婦都率領家中的婦女， | Every housewife leads the women in her household. | `04004603` | `04004605` | ❌ |
| 33 | 長 | 工作負荷必須花長時間來記錄， | Workload must be recorded over a long period of time | `06030810` | `06030803` | ❌ |
| 34 | 空 | 這是唯識講『空』的不同處。 | This is the unique approach of the Yogācāra school i | `06517331` | `06517331` | ✅ |
| 35 | 中 | 座中有人提到郝柏村現象， | Someone at the gathering mentioned the "Hao Bai-cun  | `NONE` | `04004605` | — |
| 36 | 歲 | 四十五歲的臺北水準書局老闆曾大福搭朋友的車南下， | The 45-year-old owner of Taipei Shuei-shui Bookstore | `06559405` | `06559405` | ✅ |
| 37 | 回 | 黑派理應回座維持會務， | YUI should return to her seat to maintain the meetin | `03019001` | `03019001` | ✅ |
| 38 | 中 | 恍恍惚惚腦中忽然瞥過過去她那激憤壯烈的夢。 | A fleeting image of her passionate and heroic dream  | `NONE` | `04004605` | — |
| 39 | 會 | 約在１０﹣１２天大時會出現銅離子負平衡， | Around 10 to 12 days old, copper ion negative balanc | `04143405` | `04143405` | ✅ |
| 40 | 字 | 因為我的所有最字， | All my best wishes. | `NONE` | `06584502` | — |
| 41 | 就 | 就造成肥胖症。 | It can lead to obesity. | `NONE` | `05198301` | — |
| 42 | 日 | 經驗上可能在三日內出現天價， | Experience shows that sky-high prices may appear wit | `03036209` | `03036209` | ✅ |
| 43 | 口 | 口吐白沫， | Foaming at the mouth. | `04084201` | `04084201` | ✅ |
| 44 | 股 | 首季每股稅後盈餘約○．八元。 | The after-tax earnings per share for the first quart | `03015702` | `03015710` | ❌ |
| 45 | 中 | 在上次吸吮一章中， | In the previous chapter titled "Sucking," | `NONE` | `04004605` | — |
| 46 | 拿 | 我都拿體重計為小豬們檢查身體， | I always use the scale to check the health of the li | `04011201` | `04011201` | ✅ |
| 47 | 畫 | 每幅畫都很不錯， | All the paintings are excellent. | `06550302` | `06550302` | ✅ |
| 48 | 做 | 他也把我們的垃圾做分類， | He also sorts our trash for recycling. | `NONE` | `06664306` | — |
| 49 | 上 | 多媒體在網路上的應用確實擁有無限發展潛力， | Multimedia applications on the internet indeed have  | `NONE` | `04081314` | — |
| 50 | 行 | 父母就希望你只要書念好就行了。 | Parents just hope that you do well in your studies. | `06775706` | `06775711` | ❌ |
| 51 | 拉 | 連拖帶拉的把豪豪拖到公園去了。 | Dragged Hou Hou to the park, struggling all the way. | `05230801` | `05230801` | ✅ |
| 52 | 坐 | 坐在矮牆上望著大海抽菸， | Sitting on a low wall, smoking while gazing at the s | `05223901` | `05223901` | ✅ |
| 53 | 點 | 以佔指數較重之金融股搶攻４９００點， | Financial stocks, which carry significant weight in  | `04043808` | `04043808` | ✅ |
| 54 | 歲 | 都比薛蘋小幾歲， | Sue is a few years younger than Hsieh Pin. | `06559405` | `06559405` | ✅ |
| 55 | 帶 | 事後我帶他回南部老家見父母， | Afterward, I took him back to my hometown in souther | `06791406` | `06791407` | ❌ |
| 56 | 吃 | Ｗｉｎｓｔｏｎ告訴我們無論如何也要買隻大螃蟹吃才不虛 | Winston told us we absolutely have to buy a big crab | `05227001` | `05227001` | ✅ |
| 57 | 去 | 準備挑到城裡去賣。 | I'm going to take them to the city to sell. | `06559201` | `06559205` | ❌ |
| 58 | 錢 | 但偏偏卻有很多人願把錢送入虎口， | But for some reason, many people are still willing t | `06015102` | `06015105` | ❌ |
| 59 | 過 | 而且從未請過教練， | And I have never hired a coach. | `NONE` | `05206001` | — |
| 60 | 度 | 在澳洲風景明媚的海灘度了兩天假之後， | After spending two days of vacation on Australia's s | `NONE` | `06785402` | — |
| 61 | 畫 | 如果用來記錄美術館的畫， | The system is used to record paintings in an art mus | `06550302` | `06550302` | ✅ |
| 62 | 歲 | 因為我30歲， | Because I am 30 years old. | `06559405` | `06559405` | ✅ |
| 63 | 去 | 就可以去做事了。 | You can start working now. | `06559205` | `06559205` | ✅ |
| 64 | 中 | 讀者可由表中清楚看出， | Readers can clearly see from the table. | `NONE` | `04004605` | — |
| 65 | 度 | 他們繼續在自己生活的地方和工作崗位度信仰的生活。 | They continued to live out their faith in their own  | `NONE` | `06785402` | — |
| 66 | 股 | 中華電週二公布今年每股純益目標為四．一六元， | Taiwan Mobile announced on Tuesday that its target f | `03015710` | `03015710` | ✅ |
| 67 | 季 | 第二季半導體景氣及公司業績可望觸底， | The semiconductor market outlook and company perform | `07026501` | `07026505` | ❌ |
| 68 | 中 | 在ＩＰ通訊協定中， | In IP communication protocols, | `NONE` | `04004605` | — |
| 69 | 點 | 同時在四三００至四七００點間採行箱型操作， | Box operations are conducted between 4300 and 4700 p | `04043808` | `04043808` | ✅ |
| 70 | 吃 | 便和同學偷溜跑去吃刨冰， | We sneaked out with classmates to have shaved ice. | `05227024` | `05227001` | ❌ |
| 71 | 明 | 第四繼承時期是五代至明末。 | The fourth inheritance period spans from the Five Dy | `07003501` | `07003501` | ✅ |
| 72 | 叫 | 出現一個叫永窮的窮小子， | A poor young man named Yongqiong appeared. | `04010207` | `04010206` | ❌ |
| 73 | 條 | 他還是執意走上這條不歸路， | He still insisted on taking this irreversible path. | `NONE` | `06585924` | — |
| 74 | 好 | 「下半場上來的那名後衛很好！ | The defender who came on in the second half is reall | `04157701` | `04157701` | ✅ |
| 75 | 吃 | 年年拼死吃， | I fight to eat every year. | `05227001` | `05227001` | ✅ |
| 76 | 日 | 以實品文物、各國服飾、鈔票特區及影像展呈現出日、韓、 | The exhibition showcases the charm of Japan, South K | `05239901` | `05239901` | ✅ |
| 77 | 吃 | 冰淇淋只好給弟弟吃啦！ | Ice cream can only be given to my little brother to  | `05227001` | `05227001` | ✅ |
| 78 | 場 | 國王明星大前鋒韋伯則攻下全隊最高的21分以及本季個人 | King star power forward Webber scored a team-high 21 | `NONE` | `06721709` | — |
| 79 | 度 | 璩美鳳首先三度表示， | Feng Mei-feng first expressed it three times. | `NONE` | `05147620` | — |
| 80 | 包 | 但依慣例只拿了幾包藥後回家養病。 | But as usual, he only took a few packs of medicine a | `05095709` | `05095711` | ❌ |
| 81 | 拉 | 還是每天拉著那輛三輪車沿街拾荒， | I still pull that tricycle around the streets scaven | `05230801` | `05230801` | ✅ |
| 82 | 帶 | 就能帶個女孩回來。 | You could even bring a girl back. | `06791406` | `06791407` | ❌ |
| 83 | 正 | 正準備開槍， | I was about to pull the trigger. | `NONE` | `07009821` | — |
| 84 | 大 | 年紀輕輕的就擔負這麼大的責任， | At such a young age, you're taking on such great res | `NONE` | `05227204` | — |
| 85 | 分 | 顯示中共有意分階段解決問題， | The Chinese Communist Party has expressed its intent | `04146403` | `04146403` | ✅ |
| 86 | 拉 | 拉著大書包走下車， | I pulled my large backpack off the bus. | `05230801` | `05230801` | ✅ |
| 87 | 好 | 做個好女兒， | Be a good daughter. | `04157701` | `04157701` | ✅ |
| 88 | 上 | 林青霞也在記者會上感動的表示， | Yvonne Yeh also emotionally expressed at the press c | `NONE` | `04081314` | — |
| 89 | 說 | 他已說過很多遍， | He has said it many times. | `05212401` | `05212401` | ✅ |
| 90 | 中 | 第一票不能改變各政黨在國會中的席次比。 | The first vote does not change the seat distribution | `NONE` | `04004605` | — |
| 91 | 小 | 再把芒果切成一小片， | Then cut the mango into small pieces. | `05227101` | `05227101` | ✅ |
| 92 | 叫 | 阿眉叫我不要太擔心她身體。 | Mei asked me not to worry too much about her health. | `NONE` | `05013801` | — |
| 93 | 折 | 軍警票改為八折優待， | Commissioned tickets for military and police personn | `07033113` | `07033113` | ✅ |
| 94 | 會 | 沒有一家銀行會故意違反央行規定， | No bank would deliberately violate the regulations s | `04143405` | `04143405` | ✅ |
| 95 | 去 | 不必去當兵， | You don't have to enlist in the military. | `06559214` | `06559205` | ❌ |
| 96 | 歲 | 看到一位七十幾歲的老先生， | I saw an elderly gentleman in his seventies. | `06559405` | `06559405` | ✅ |
| 97 | 去 | 我們要去旅行， | We are going to travel. | `06559201` | `06559205` | ❌ |
| 98 | 條 | 便可堆出一條筆直的高級公路。 | A straight, high-quality highway can be built this w | `NONE` | `06585924` | — |
| 99 | 強 | 當海水清澈、陽光穿透力強的時候， | When the sea is clear and sunlight penetrates deeply | `09250308` | `09250303` | ❌ |
| 100 | 人 | 有些人批國安聯盟是太上決策機制， | Some people criticize the National Security Alliance | `05231105` | `05231101` | ❌ |
| 101 | 條 | 森林之家的每條街道， | Every street in Forest Home | `NONE` | `06585906` | — |
| 102 | 下 | 在Ｃ目錄下打）ｐａｔｈ）。 | Create a path under the C drive. | `04081803` | `04081808` | ❌ |
| 103 | 高 | 照說素質都很高， | The quality is supposed to be very high. | `06010615` | `06010615` | ✅ |
| 104 | 場 | 除了在萬芳醫院的三場演出之外， | In addition to the three performances at Wanfang Hos | `NONE` | `06721707` | — |
| 105 | 吃 | 「天生我才必有用」、「吃得苦中苦， | "Great minds have aims, petty minds have wishes."
"O | `NONE` | `05227009` | — |
| 106 | 拿 | 偶爾有幾個好心人拿東西給我吃， | Occasionally, a few kind people bring me something t | `04011201` | `04011205` | ❌ |
| 107 | 當 | 而在將高山當郊山玩的途中， | And along the way, while treating towering mountains | `04013907` | `04013901` | ❌ |
| 108 | 強 | 國男組也將進行四強交叉準決賽， | The men's team will also compete in the semifinals c | `NONE` | `09250305` | — |
| 109 | 去 | 她去過多少美國市場， | How many U.S. markets has she visited? | `06559201` | `06559201` | ✅ |
| 110 | 面 | 面無表情地望著大家， | He stared at everyone with a blank expression. | `03028803` | `03028801` | ❌ |
| 111 | 深 | 自己深知道頭銜無用， | I know full well that titles are useless. | `06663316` | `06663313` | ❌ |
| 112 | 去 | 走到了最常去最熟悉的圖書館， | I arrived at the most frequently visited and familia | `06559201` | `06559201` | ✅ |
| 113 | 破 | 自己發球局反在第六局被破， | I was broken in my own serve game in the sixth set. | `06761422` | `06761422` | ✅ |
| 114 | 條 | 教育部在九月初以不符合師資培育法第七條及師範教育精神 | The Ministry of Education ruled in early September t | `06585929` | `06585929` | ✅ |
| 115 | 做 | 剝取牠們的毛皮做標本， | Extract their fur to make specimens. | `06664301` | `06664301` | ✅ |
| 116 | 度 | 那麼如何因應不同需求或在家庭結構變化時必須採行的「二 | Therefore, the "second-time redesign" required to ac | `05147605` | `05147617` | ❌ |
| 117 | 中 | 在車中， | In the car. | `04004603` | `04004603` | ✅ |
| 118 | 去 | 去幾天﹖ | How many days ago? | `06559218` | `06559201` | ❌ |
| 119 | 做 | 做個術德兼修、品學兼優的好學生， | Be a good student who excels in both moral character | `06664308` | `06664308` | ✅ |
| 120 | 粗 | 還有幾支粗簽字筆， | There are still a few thick felt-tip pens. | `06711801` | `06711803` | ❌ |
| 121 | 回 | 有一回他受命去孟家宅院取兩支手槍， | One time, he was ordered to go to the Meng family co | `03019001` | `03019008` | ❌ |
| 122 | 小 | 否則浪費金錢事小， | Otherwise, wasting money is the least of our concern | `05227104` | `05227104` | ✅ |
| 123 | 下 | 並在其下成立系統規格制訂和系統測試小組。 | And establish system specification formulation and s | `NONE` | `04081808` | — |
| 124 | 破 | 也沒聽說過肚皮會破的。 | I've never heard of a belly bursting open either. | `06761402` | `06761404` | ❌ |
| 125 | 道 | 每一個性方面的需求可能有些人比較好此道， | Every individual may have varying levels of expertis | `NONE` | `06002402` | — |
| 126 | 中 | 亦正發展中， | It is also developing in a positive direction. | `NONE` | `04004618` | — |
| 127 | 條 | 一開始就把這條小河川整理一下， | Start by tidying up this small river. | `NONE` | `06585906` | — |
| 128 | 條 | 可是他那兩條硬得像木棍的腿， | But those two legs of his were as stiff as wooden st | `06585903` | `06585910` | ❌ |
| 129 | 過 | 透著粉綠、粉紫、粉紅的金花鱸游曳而過， | A flash of golden perch, tinged with soft green, lav | `NONE` | `04005001` | — |
| 130 | 熱 | 此外響韻、寶麗金也在一波波文藝復興熱， | In addition, Iris and PolyGram are also experiencing | `05228709` | `05228709` | ✅ |
| 131 | 去 | 我們能去嗎？ | Can we go? | `06559201` | `06559201` | ✅ |
| 132 | 條 | 只求挽回一條垂危的生命， | I only seek to save a life hanging by a thread. | `NONE` | `06585911` | — |
| 133 | 就 | 要不然就是陰天。 | Otherwise, it will be overcast. | `NONE` | `05198307` | — |
| 134 | 面 | 她曾在82年奪得區運5面金牌後因傷退出體操界， | She once won five gold medals at the District Games  | `NONE` | `03028807` | — |
| 135 | 部 | 包括二十部保時捷。 | Including twenty Porsche vehicles. | `NONE` | `05075709` | — |
| 136 | 點 | 說得確實點， | Just put it bluntly. | `NONE` | `04043813` | — |
| 137 | 分 | 分不清是夢是真。 | I can't tell if it's a dream or reality. | `NONE` | `04146401` | — |
| 138 | 大 | 又在１９０６年建了更大的ＬａｎｇｄｅｌｌＨａｌｌ， | In 1906, an even larger Langdell Hall was built. | `05227201` | `05227202` | ❌ |
| 139 | 行 | 美國之行並非尋夢、也非淘金， | The trip to the United States was neither a quest fo | `06775704` | `06775704` | ✅ |
| 140 | 吃 | 所有出門的人一定要趕回家來吃年夜飯， | Everyone who goes out must rush home to have the New | `05227024` | `05227024` | ✅ |
| 141 | 片 | 他站在一片書牆前， | He stood in front of a wall of books. | `NONE` | `05195915` | — |
| 142 | 破 | 再破三案。 | Three more cases have been cracked. | `06761412` | `06761412` | ✅ |
| 143 | 就 | 昏沉就是愛睡， | Drowsiness is just loving to sleep. | `05198313` | `05198313` | ✅ |
| 144 | 法 | 而非國民黨統治機器所貼下標籤的地域區分法‧人們習慣稱 | People are actually accustomed to calling the "ben s | `NONE` | `05045104` | — |
| 145 | 熱 | 如此對於賽程的控制和比賽氣氛熱都很有幫助， | This helps a lot in controlling the schedule and hea | `05228723` | `05228723` | ✅ |
| 146 | 代 | 由於本學期校方代學生聯合會向學生收取自治費， | The Student Union collected self-governance fees on  | `07104505` | `07104502` | ❌ |
| 147 | 大 | 大蛇竟然把嘴張開， | The serpent actually opened its mouth wide. | `NONE` | `05227201` | — |
| 148 | 用 | 吃穿用玩樣樣俱全， | Everything is available for eating, dressing, using, | `04017411` | `04017411` | ✅ |
| 149 | 叫 | 你學個貓叫， | Meow! | `04010202` | `04010202` | ✅ |
| 150 | 拉 | 你是說你們那時候連手都沒有拉！ | You said you didn't even hold hands back then! | `05230802` | `05230802` | ✅ |
| 151 | 拿 | 只開放特定場地供學生拿號碼牌寄物。 | Only specific areas are open for students to take nu | `04011201` | `04011202` | ❌ |
| 152 | 上 | 一切都只停留在勞作的程度上。 | Everything remains at the level of mere labor. | `NONE` | `04081317` | — |
| 153 | 大 | 由於批購總額大， | The total procurement amount is large. | `05227203` | `05227203` | ✅ |
| 154 | 發 | 是很願意國內所有發卡機構能研擬出一套辦法來針對如果受 | I sincerely hope that all domestic card-issuing inst | `06724101` | `06724102` | ❌ |
| 155 | 就 | 就是彼此的特性。 | It is about each other's characteristics. | `NONE` | `05198313` | — |
| 156 | 作 | 或許這部小說也是明人所作的， | Perhaps this novel was also written by a Ming dynast | `05098103` | `05098103` | ✅ |
| 157 | 平 | 車子的把手為平把， | The car has flat handlebars. | `06025201` | `06025213` | ❌ |
| 158 | 高 | 配備精良的美國警方人員在攝影高台上嚴密監視觀眾動態， | Well-equipped U.S. police officers closely monitor t | `06010603` | `06010601` | ❌ |
| 159 | 掛 | 男孩要求掛急診。 | The boy requested emergency treatment. | `NONE` | `06701415` | — |
| 160 | 破 | 大陸經過文化大革命及破四舊的浩劫， | The mainland experienced the catastrophe of the Cult | `06761405` | `06761415` | ❌ |
| 161 | 真 | 真希望可以永遠住在那裡。 | I truly wish I could live there forever. | `05100406` | `05100414` | ❌ |
| 162 | 行 | 聽取奎爾簡報他此行經過及與沙烏地阿拉伯國王法德和科威 | I listened to Kuier's briefing on his trip and the t | `06775704` | `06775704` | ✅ |
| 163 | 邊 | 調整的方法是手握雙筒鏡的兩邊， | Adjust the binoculars by holding both sides. | `06584404` | `06584406` | ❌ |
| 164 | 層 | 中間那層「主任」完全不在他眼裡。 | The middle-tier "Director" meant nothing to him. | `03005008` | `03005006` | ❌ |
| 165 | 中 | 這種哲學和傅蘭尼、孔恩等嘗試在科學的知識如何獲得的過 | This type of philosophy, like that of Foucault and K | `04004605` | `04004618` | ❌ |
| 166 | 行 | 西方國家行之已久的社會安全措施， | Western countries have long implemented social secur | `NONE` | `06775707` | — |
| 167 | 季 | 所以這兩隊的競爭從這一季的第一場球就開始了， | So the rivalry between these two teams began with th | `07026504` | `07026504` | ✅ |
| 168 | 子 | 法華經長者窮子喻之中， | In the parable of the rich man and his poor son in t | `07027902` | `07027904` | ❌ |
| 169 | 明 | 而教練費區和球員之間不和的事實也由暗而明， | The rift between the coaching staff and players has  | `06685411` | `06685407` | ❌ |
| 170 | 叫 | 當頑皮的鬧鐘叫了以後， | After the mischievous alarm clock rang, | `NONE` | `04010205` | — |
| 171 | 正 | 其謬誤正如同我們總習於率爾用一個人比擬另一個人。 | Just as we often hastily compare one person to anoth | `NONE` | `07009822` | — |
| 172 | 拍 | 「原來拍古裝戲這麼辛苦！ | "Turns out filming period dramas is so exhausting!" | `08028003` | `08028003` | ✅ |
| 173 | 花 | 棘皮動物海百合像海中之花般地鮮艷綻放， | Echinoderms like sea lilies bloom brilliantly in the | `05229001` | `05229006` | ❌ |
| 174 | 就 | 心浮動就是道心不堅固， | A floating mind is an unsteady Dao mind. | `NONE` | `05198313` | — |
| 175 | 支 | 由國內四支球隊選出的職棒明星隊負責把守第二關。 | The all-star team composed of four domestic teams wi | `03056204` | `03056204` | ✅ |
| 176 | 度 | 因此面前的視野交集區只有十度。 | Therefore, the overlapping field of view in front of | `05147607` | `05147607` | ✅ |
| 177 | 來 | 國外學生來台主要集中在台灣師大學中文， | The main concentration of international students com | `04086501` | `04086501` | ✅ |
| 178 | 正 | 後人乘涼正是本院圖書館自動化的最佳寫照， | Future generations benefit from the cool shade, whic | `07009822` | `07009822` | ✅ |
| 179 | 代 | 這些是發生在這一代華人身上比較新的事情。 | These are relatively new events that have happened t | `04016205` | `04016206` | ❌ |
| 180 | 好 | 好漂亮啊！ | That's so beautiful! | `04157710` | `04157710` | ✅ |
| 181 | 上 | 在個人資料和事件的處理上， | In the handling of personal data and incidents, | `NONE` | `04081317` | — |
| 182 | 分 | 自家門口遭到三名蒙面歹徒分執鋁製球棒毆傷， | Three people in masks attacked me at my doorstep wit | `NONE` | `04146408` | — |
| 183 | 做 | 堂姊就做了一個洋娃娃給我。 | My cousin made a doll for me. | `06664301` | `06664301` | ✅ |
| 184 | 條 | 他的童年像一條浮根， | His childhood was like a floating root. | `NONE` | `06585903` | — |
| 185 | 發 | ∥我要靠意外之財我才能發啦我！ | I'm counting on a windfall to strike it rich! | `05193406` | `05193406` | ✅ |
| 186 | 大 | 竹葉上有一大群螞蟻， | There is a large group of ants on the bamboo leaf. | `05227203` | `05227203` | ✅ |
| 187 | 就 | 首先選擇茶葉就是一門學問。 | Choosing tea leaves is a subject of study in itself. | `NONE` | `05198313` | — |
| 188 | 打 | 謝玄只用了五千人就把秦兵打得大敗， | Only five thousand of Xie Xuan's troops routed the Q | `05229126` | `05229126` | ✅ |
| 189 | 代 | 身為台塑的第二代， | As the second generation of the Formosa Plastics Gro | `04016203` | `04016201` | ❌ |
| 190 | 大 | 好大的一個螺殼！ | What a huge shell! | `05227201` | `05227201` | ✅ |
| 191 | 收 | 還捨不得收起來。 | I still can't bear to put it away. | `03039314` | `03039314` | ✅ |
| 192 | 對 | 但因氣氛及感覺不對， | But since the atmosphere and feeling were off. | `NONE` | `04017503` | — |
| 193 | 人 | 高階積體電路設計公司至少雇用十人以上， | A high-end integrated circuit design company must em | `05231109` | `05231109` | ✅ |
| 194 | 道 | 相信透過教育這最後一道丹藥可以拯救！ | I believe that through education, this final elixir  | `NONE` | `04083512` | — |
| 195 | 轉 | 他三個手指悠然轉著那只淡青色玉鐲。 | He leisurely twirled the light blue jade bracelet wi | `05228801` | `05228802` | ❌ |
| 196 | 重 | 拿起大包小包的行李也就不覺得重了。 | Picking up all the big and small pieces of luggage d | `05207602` | `05207602` | ✅ |
| 197 | 行 | 李總統康乃爾之行， | President Tsai's visit to Cornell University | `06775704` | `06775704` | ✅ |
| 198 | 畫 | 例如在畫建築時， | For example, when drawing buildings, | `06550303` | `06550301` | ❌ |
| 199 | 空 | 是非成敗轉頭空， | Only the translation is required:

Time turns all vi | `06517327` | `06517332` | ❌ |
| 200 | 條 | 或者手拉手走一條霪雨霏霏的街。 | Or hand in hand, we walk down a rain-soaked street. | `06585906` | `06585906` | ✅ |

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

**18. 拍**　`wsd-拍-241f`　[dominant]
- 原句：一走紅大家都搶著找她拍，
- 譯文：Once she became popular, everyone scrambled to collaborate with her on photo shoots.
- judge 選：`08028001` 用攝影器材拍照片。　信心 0.98　依據：photo shoots 指拍照的過程，對應用器材紀錄影像
- gold：`08028004` 參與拍攝電影與製作。

**19. 去**　`wsd-去-9e53`　[dominant]
- 原句：你先去預備圖章，
- 譯文：Please go prepare the seal first.
- judge 選：`06559201` 向特定地點移動。　信心 0.98　依據：go 表向特定地點移動
- gold：`06559205` 表前述對象進行後述事件。

**21. 拍**　`wsd-拍-8759`　[dominant]
- 原句：希望能多拍些劇情片。
- 譯文：I hope we can make more narrative films.
- judge 選：`08028003` 用攝影器材紀錄動態影像。　信心 0.95　依據：narrative films 指電影拍攝，對應用器材紀錄影像
- gold：`08028004` 參與拍攝電影與製作。

**23. 支**　`wsd-支-1fe0`　[dominant]
- 原句：而韓國隊卻只有七支。
- 譯文：However, the South Korean team only has seven.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「支」相關的計量單位意涵
- gold：`03056210` 計算棒球賽中擊出的有效打擊數。

**24. 上**　`wsd-上-e2ba`　[dominant]
- 原句：就把媽祖在海上顯靈的事蹟，
- 譯文：Mazu's miraculous manifestations at sea
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文中的 at sea 未對應任何候選義項
- gold：`04081314` 事件的發生在前述事物的範圍內。

**26. 行**　`wsd-行-45ab`　[dominant]
- 原句：我們演習一下就行了，
- 譯文：Let's just practice.
- judge 選：`06775707` 依照特定方法實際施行特定事件。　信心 0.90　依據：practice 為實際施行特定事件
- gold：`06775711` 形容表示同意或允許。

**27. 起**　`wsd-起-b672`　[dominant]
- 原句：報名自即日起受理，
- 譯文：Registration is now open.
- judge 選：`04004828` 開始或產生。　信心 0.90　依據：open 表開始或啟動註冊流程
- gold：`04004801` 表示事件時間範圍的開始參考點。

**28. 高**　`wsd-高-1f42`　[dominant]
- 原句：台大最高，
- 譯文：National Taiwan University is the best.
- judge 選：`06010615` 形容程度或標準高於比較對象。　信心 0.90　依據：best 表程度或標準高於比較對象
- gold：`06010610` 形容數值大於比較對象。

**32. 中**　`wsd-中-85bc`　[dominant]
- 原句：每家主婦都率領家中的婦女，
- 譯文：Every housewife leads the women in her household.
- judge 選：`04004603` 在前述對象所包含的空間範圍。　信心 0.95　依據：household 指家庭成員所在的空間範圍
- gold：`04004605` 在前述的機構或領域範圍。

**33. 長**　`wsd-長-d38d`　[dominant]
- 原句：工作負荷必須花長時間來記錄，
- 譯文：Workload must be recorded over a long period of time.
- judge 選：`06030810` 時間的長度。　信心 0.98　依據：long period of time 直接對應時間的長度
- gold：`06030803` 形容事件持續的時間間隔大。

**35. 中**　`wsd-中-90d9`　[dominant]
- 原句：座中有人提到郝柏村現象，
- 譯文：Someone at the gathering mentioned the "Hao Bai-cun phenomenon."
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與中文「中」相關的意涵
- gold：`04004605` 在前述的機構或領域範圍。

**38. 中**　`wsd-中-d396`　[dominant]
- 原句：恍恍惚惚腦中忽然瞥過過去她那激憤壯烈的夢。
- 譯文：A fleeting image of her passionate and heroic dream suddenly flashed through my hazy mind.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「中」相關的空間或時間標記
- gold：`04004605` 在前述的機構或領域範圍。

**40. 字**　`wsd-字-c8e1`　[dominant]
- 原句：因為我的所有最字，
- 譯文：All my best wishes.
- judge 選：`NONE` （NONE）　信心 0.95　依據：wishes 未對應任何字義義項
- gold：`06584502` 中文書面書寫的最小單位。

**41. 就**　`wsd-就-6f06`　[dominant]
- 原句：就造成肥胖症。
- 譯文：It can lead to obesity.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現「就」的對應詞，無義項符合
- gold：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。

**44. 股**　`wsd-股-32a8`　[dominant]
- 原句：首季每股稅後盈餘約○．八元。
- 譯文：The after-tax earnings per share for the first quarter were approximately NT$0.8.
- judge 選：`03015702` 上櫃或上市公司用來表示其公司股份的證券。　信心 0.98　依據：earnings per share 譯為每股盈餘，指證券
- gold：`03015710` 計算股份的單位。

**45. 中**　`wsd-中-6473`　[dominant]
- 原句：在上次吸吮一章中，
- 譯文：In the previous chapter titled "Sucking,"
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現中文詞，僅為章節標題標記
- gold：`04004605` 在前述的機構或領域範圍。

**48. 做**　`wsd-做-8944`　[dominant]
- 原句：他也把我們的垃圾做分類，
- 譯文：He also sorts our trash for recycling.
- judge 選：`NONE` （NONE）　信心 0.95　依據：sorts 為分類處理，與候選義項無關
- gold：`06664306` 做，取代整個事件。

**49. 上**　`wsd-上-e882`　[dominant]
- 原句：多媒體在網路上的應用確實擁有無限發展潛力，
- 譯文：Multimedia applications on the internet indeed have unlimited potential for development.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未直接對應任何上列義項
- gold：`04081314` 事件的發生在前述事物的範圍內。

**50. 行**　`wsd-行-a94f`　[dominant]
- 原句：父母就希望你只要書念好就行了。
- 譯文：Parents just hope that you do well in your studies.
- judge 選：`06775706` 做，取代整個事件。　信心 0.90　依據：do well in studies 對應「做」的義項
- gold：`06775711` 形容表示同意或允許。

**55. 帶**　`wsd-帶-de6d`　[dominant]
- 原句：事後我帶他回南部老家見父母，
- 譯文：Afterward, I took him back to my hometown in southern Taiwan to meet my parents.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.90　依據：took him back 使他跟著自己移動
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**57. 去**　`wsd-去-a508`　[dominant]
- 原句：準備挑到城裡去賣。
- 譯文：I'm going to take them to the city to sell.
- judge 選：`06559201` 向特定地點移動。　信心 0.98　依據：譯文用 going to，指向特定地點移動
- gold：`06559205` 表前述對象進行後述事件。

**58. 錢**　`wsd-錢-f034`　[dominant]
- 原句：但偏偏卻有很多人願把錢送入虎口，
- 譯文：But for some reason, many people are still willing to throw their money into the tiger's den.
- judge 選：`06015102` 通指貨幣。　信心 0.98　依據：money 譯為貨幣，對應通指貨幣的義項
- gold：`06015105` 經費、錢財。

**59. 過**　`wsd-過-2e45`　[dominant]
- 原句：而且從未請過教練，
- 譯文：And I have never hired a coach.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「過」相關的時態或狀態標記
- gold：`05206001` 時態標記。表事件在參考時點前曾經發生。

**60. 度**　`wsd-度-334e`　[dominant]
- 原句：在澳洲風景明媚的海灘度了兩天假之後，
- 譯文：After spending two days of vacation on Australia's scenic beaches
- judge 選：`NONE` （NONE）　信心 0.95　依據：vacation 譯文未涉及「度」的任何義項
- gold：`06785402` 經過特定時段。

**64. 中**　`wsd-中-797e`　[dominant]
- 原句：讀者可由表中清楚看出，
- 譯文：Readers can clearly see from the table.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現中文「中」字或其對應概念
- gold：`04004605` 在前述的機構或領域範圍。

**65. 度**　`wsd-度-4fa1`　[dominant]
- 原句：他們繼續在自己生活的地方和工作崗位度信仰的生活。
- 譯文：They continued to live out their faith in their own places of residence and work.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「度」相關的意涵
- gold：`06785402` 經過特定時段。

**67. 季**　`wsd-季-58ca`　[dominant]
- 原句：第二季半導體景氣及公司業績可望觸底，
- 譯文：The semiconductor market outlook and company performance in the second half of the year are expected to bottom out.
- judge 選：`07026501` 一年中依氣候變化以三個月為一等分的固定時段。　信心 0.98　依據：second half of the year 指一年分為兩個時段
- gold：`07026505` 依照特定活動將一年以三個月為一等分的固定時段。

**68. 中**　`wsd-中-cde3`　[dominant]
- 原句：在ＩＰ通訊協定中，
- 譯文：In IP communication protocols,
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文為片語未單獨譯出「中」字
- gold：`04004605` 在前述的機構或領域範圍。

**70. 吃**　`wsd-吃-c740`　[dominant]
- 原句：便和同學偷溜跑去吃刨冰，
- 譯文：We sneaked out with classmates to have shaved ice.
- judge 選：`05227024` 經歷後述包括飲食的社交聚會。　信心 0.95　依據：have shaved ice 指經歷吃冰的社交活動
- gold：`05227001` 使物體經過口中吞入體內。

**72. 叫**　`wsd-叫-2b66`　[dominant]
- 原句：出現一個叫永窮的窮小子，
- 譯文：A poor young man named Yongqiong appeared.
- judge 選：`04010207` 根據前述定義給予後述對象名稱。　信心 0.98　依據：named 譯為「命名」，對應「給予後述對象名稱」
- gold：`04010206` 叫特定對象的名字是後述對象。

**73. 條**　`wsd-條-5afb`　[dominant]
- 原句：他還是執意走上這條不歸路，
- 譯文：He still insisted on taking this irreversible path.
- judge 選：`NONE` （NONE）　信心 0.95　依據：irreversible path 未對應任何條的義項
- gold：`06585924` 計算行進的路線的單位。

**78. 場**　`wsd-場-50f3`　[dominant]
- 原句：國王明星大前鋒韋伯則攻下全隊最高的21分以及本季個人單場最多之12個籃板球。
- 譯文：King star power forward Webber scored a team-high 21 points and a season-high 12 rebounds.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「場」相關的詞彙
- gold：`06721709` 計算經過安排的活動的單位。

**79. 度**　`wsd-度-c33f`　[dominant]
- 原句：璩美鳳首先三度表示，
- 譯文：Feng Mei-feng first expressed it three times.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「度」相關的單位或概念
- gold：`05147620` 計算事件發生的次數的單位。

**80. 包**　`wsd-包-07f6`　[dominant]
- 原句：但依慣例只拿了幾包藥後回家養病。
- 譯文：But as usual, he only took a few packs of medicine and went home to recuperate.
- judge 選：`05095709` 成包的物品。　信心 0.98　依據：packs of medicine 指成包的藥品
- gold：`05095711` 計算成包物品的單位。

**82. 帶**　`wsd-帶-b6cb`　[dominant]
- 原句：就能帶個女孩回來。
- 譯文：You could even bring a girl back.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.98　依據：bring 使某人跟著移動，符合支配者帶動被支配者
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**83. 正**　`wsd-正-8b50`　[dominant]
- 原句：正準備開槍，
- 譯文：I was about to pull the trigger.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現正面對應該詞的意涵
- gold：`07009821` 表動作進行中或狀態持續中。

**84. 大**　`wsd-大-7fac`　[dominant]
- 原句：年紀輕輕的就擔負這麼大的責任，
- 譯文：At such a young age, you're taking on such great responsibility.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未直接對應「大」的任何義項
- gold：`05227204` 形容程度超過比較對象的。

**88. 上**　`wsd-上-2481`　[dominant]
- 原句：林青霞也在記者會上感動的表示，
- 譯文：Yvonne Yeh also emotionally expressed at the press conference,
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「上」相關的意義或用法
- gold：`04081314` 事件的發生在前述事物的範圍內。

**90. 中**　`wsd-中-b982`　[dominant]
- 原句：第一票不能改變各政黨在國會中的席次比。
- 譯文：The first vote does not change the seat distribution of each political party in the legislature.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未直接表達「中」的任何義項
- gold：`04004605` 在前述的機構或領域範圍。

**92. 叫**　`wsd-叫-7924`　[dominant]
- 原句：阿眉叫我不要太擔心她身體。
- 譯文：Mei asked me not to worry too much about her health.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未直接表達「叫」的語意
- gold：`05013801` 指示後述對象做事。

**95. 去**　`wsd-去-44b6`　[dominant]
- 原句：不必去當兵，
- 譯文：You don't have to enlist in the military.
- judge 選：`06559214` 比喻消除後述對象使其不存在。　信心 0.90　依據：enlist 可理解為「去除、消除」的比喻用法
- gold：`06559205` 表前述對象進行後述事件。

**97. 去**　`wsd-去-eeed`　[dominant]
- 原句：我們要去旅行，
- 譯文：We are going to travel.
- judge 選：`06559201` 向特定地點移動。　信心 0.98　依據：going to 表移動方向，符合向特定地點移動
- gold：`06559205` 表前述對象進行後述事件。

**98. 條**　`wsd-條-a722`　[dominant]
- 原句：便可堆出一條筆直的高級公路。
- 譯文：A straight, high-quality highway can be built this way.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「條」相關的量詞或概念
- gold：`06585924` 計算行進的路線的單位。

**99. 強**　`wsd-強-95c5`　[dominant]
- 原句：當海水清澈、陽光穿透力強的時候，
- 譯文：When the sea is clear and sunlight penetrates deeply.
- judge 選：`09250308` 形容光線的強度大。　信心 0.98　依據：sunlight penetrates deeply 對應光線強度大
- gold：`09250303` 形容能力或發展狀況好的。

**100. 人**　`wsd-人-9047`　[dominant]
- 原句：有些人批國安聯盟是太上決策機制，
- 譯文：Some people criticize the National Security Alliance as an extra-constitutional decision-making mechanism.
- judge 選：`05231105` 自己以外的人。　信心 0.90　依據：criticize 指向他人，people 為自己以外的人
- gold：`05231101` 軀幹直立，用雙腳行走的高等動物，具備思考能力，有語言文字，能進行社交活動。

**101. 條**　`wsd-條-63fe`　[non_dominant]
- 原句：森林之家的每條街道，
- 譯文：Every street in Forest Home
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「條」相關的量詞或概念
- gold：`06585906` 計算地面上長條型的建築物或自然景觀的單位。

**102. 下**　`wsd-下-496b`　[non_dominant]
- 原句：在Ｃ目錄下打）ｐａｔｈ）。
- 譯文：Create a path under the C drive.
- judge 選：`04081803` 鄰近前述物體的底部或低於該物體位置。　信心 0.95　依據：under 譯為「在...下方」，指位置低於參考點
- gold：`04081808` 比喻階級架構中低於前述階級的階級。

**104. 場**　`wsd-場-9bec`　[non_dominant]
- 原句：除了在萬芳醫院的三場演出之外，
- 譯文：In addition to the three performances at Wanfang Hospital,
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「場」相關的詞彙
- gold：`06721707` 計算戲劇中較小段落的單位。

**105. 吃**　`wsd-吃-cf63`　[non_dominant]
- 原句：「天生我才必有用」、「吃得苦中苦，
- 譯文："Great minds have aims, petty minds have wishes."
"Only through hardship can one achieve greatness."
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「吃」相關的意涵
- gold：`05227009` 比喻經歷後述負面事件。

**106. 拿**　`wsd-拿-7496`　[non_dominant]
- 原句：偶爾有幾個好心人拿東西給我吃，
- 譯文：Occasionally, a few kind people bring me something to eat.
- judge 選：`04011201` 用手取物或持物。　信心 0.95　依據：bring 表用手取物或持物
- gold：`04011205` 提供金錢或其他有價值物給後述對象。

**107. 當**　`wsd-當-d0c0`　[non_dominant]
- 原句：而在將高山當郊山玩的途中，
- 譯文：And along the way, while treating towering mountains like mere hills for a casual outing,
- judge 選：`04013907` 引介背景事件作為時間的範圍。　信心 0.90　依據：while 表達背景事件作為時間範圍
- gold：`04013901` 前述對象的工作或身份是後述對象。

**108. 強**　`wsd-強-7c81`　[non_dominant]
- 原句：國男組也將進行四強交叉準決賽，
- 譯文：The men's team will also compete in the semifinals crossover.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「強」相關的意涵
- gold：`09250305` 競賽中排名在前述範圍的特定對象。

**110. 面**　`wsd-面-43d6`　[non_dominant]
- 原句：面無表情地望著大家，
- 譯文：He stared at everyone with a blank expression.
- judge 選：`03028803` 面對觀察者的方向。　信心 0.95　依據：expression 指臉部表情，對應面的方向義
- gold：`03028801` 動物頭從額頭到下巴的部分。

**111. 深**　`wsd-深-55e4`　[non_dominant]
- 原句：自己深知道頭銜無用，
- 譯文：I know full well that titles are useless.
- judge 選：`06663316` 形容前述狀態的程度高，通常是負面。　信心 0.85　依據：full well 中的 well 表程度高且負面
- gold：`06663313` 表超過平常的程度。

**116. 度**　`wsd-度-378e`　[non_dominant]
- 原句：那麼如何因應不同需求或在家庭結構變化時必須採行的「二度設計」就是我們檢討萬年平面的參考方向。
- 譯文：Therefore, the "second-time redesign" required to accommodate different needs or changes in family structure serves as our reference direction for reviewing the "never-changing floor plan."
- judge 選：`05147605` 比喻前述特性的程度。　信心 0.90　依據：reference direction 表程度上的參考基準
- gold：`05147617` 計算空間維數的單位。

**118. 去**　`wsd-去-d84e`　[non_dominant]
- 原句：去幾天﹖
- 譯文：How many days ago?
- judge 選：`06559218` 比喻前述時段經過，成為特定時間點以前的時段。　信心 0.95　依據：ago 表示時間已過去，對應「經過」的時段義
- gold：`06559201` 向特定地點移動。

**120. 粗**　`wsd-粗-704b`　[non_dominant]
- 原句：還有幾支粗簽字筆，
- 譯文：There are still a few thick felt-tip pens.
- judge 選：`06711801` 形容條狀物的橫切面的面積大。　信心 0.98　依據：thick 譯為條狀物橫切面面積大
- gold：`06711803` 形容線條的寬度大。

**121. 回**　`wsd-回-1e59`　[non_dominant]
- 原句：有一回他受命去孟家宅院取兩支手槍，
- 譯文：One time, he was ordered to go to the Meng family compound to retrieve two pistols.
- judge 選：`03019001` 從其它地方到原來的地方或處所。　信心 0.98　依據：retrieve 為「取回、拿回」意指前往他處後返回原處
- gold：`03019008` 計算事件的單位。

**123. 下**　`wsd-下-4f94`　[non_dominant]
- 原句：並在其下成立系統規格制訂和系統測試小組。
- 譯文：And establish system specification formulation and system testing teams under it.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「下」相關的意涵
- gold：`04081808` 比喻階級架構中低於前述階級的階級。

**124. 破**　`wsd-破-f6ff`　[non_dominant]
- 原句：也沒聽說過肚皮會破的。
- 譯文：I've never heard of a belly bursting open either.
- judge 選：`06761402` 形容完整的物體因受到外力影響而裂成小塊的。　信心 0.90　依據：burst open 指物體因外力而裂成碎塊
- gold：`06761404` 特定物品產生缺口。

**125. 道**　`wsd-道-ef48`　[non_dominant]
- 原句：每一個性方面的需求可能有些人比較好此道，
- 譯文：Every individual may have varying levels of expertise or interest in matters related to intimacy.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「道」相關的概念
- gold：`06002402` 含有哲理的技藝。

**126. 中**　`wsd-中-3be9`　[non_dominant]
- 原句：亦正發展中，
- 譯文：It is also developing in a positive direction.
- judge 選：`NONE` （NONE）　信心 0.95　依據：direction 表方向而非中文的「中」義項
- gold：`04004618` 在事件的過程中。

**127. 條**　`wsd-條-50d4`　[non_dominant]
- 原句：一開始就把這條小河川整理一下，
- 譯文：Start by tidying up this small river.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「條」相關的量詞或概念
- gold：`06585906` 計算地面上長條型的建築物或自然景觀的單位。

**128. 條**　`wsd-條-fb09`　[non_dominant]
- 原句：可是他那兩條硬得像木棍的腿，
- 譯文：But those two legs of his were as stiff as wooden sticks.
- judge 選：`06585903` 計算形狀細而長的物體的單位。　信心 0.98　依據：sticks 指細長的木棍，對應「形狀細而長的物體」
- gold：`06585910` 計算身體部位的單位。

**129. 過**　`wsd-過-46a1`　[non_dominant]
- 原句：透著粉綠、粉紫、粉紅的金花鱸游曳而過，
- 譯文：A flash of golden perch, tinged with soft green, lavender, and pink, darted by.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「過」相關的意涵
- gold：`04005001` 由特定路徑通過。

**132. 條**　`wsd-條-7771`　[non_dominant]
- 原句：只求挽回一條垂危的生命，
- 譯文：I only seek to save a life hanging by a thread.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「條」相關的量詞或概念
- gold：`06585911` 計算動物性命的單位。

**133. 就**　`wsd-就-fe97`　[non_dominant]
- 原句：要不然就是陰天。
- 譯文：Otherwise, it will be overcast.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「就」相關的語意或詞彙
- gold：`05198307` 表強調說話者已知事實。

**134. 面**　`wsd-面-572d`　[non_dominant]
- 原句：她曾在82年奪得區運5面金牌後因傷退出體操界，
- 譯文：She once won five gold medals at the District Games in 1982 before retiring from gymnastics due to an injury.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「面」相關的詞彙
- gold：`03028807` 計算牌狀物的單位。

**135. 部**　`wsd-部-8828`　[non_dominant]
- 原句：包括二十部保時捷。
- 譯文：Including twenty Porsche vehicles.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現部字，且Porsche vehicles非機械裝置單位
- gold：`05075709` 計算有輪子的機械裝置的單位。

**136. 點**　`wsd-點-b366`　[non_dominant]
- 原句：說得確實點，
- 譯文：Just put it bluntly.
- judge 選：`NONE` （NONE）　信心 0.95　依據：bluntly 指直率表達，未對應任何義項
- gold：`04043813` 表不確定的小數量。

**137. 分**　`wsd-分-1598`　[non_dominant]
- 原句：分不清是夢是真。
- 譯文：I can't tell if it's a dream or reality.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「分」相關的意涵
- gold：`04146401` 特定對象分開。

**138. 大**　`wsd-大-6041`　[non_dominant]
- 原句：又在１９０６年建了更大的ＬａｎｇｄｅｌｌＨａｌｌ，
- 譯文：In 1906, an even larger Langdell Hall was built.
- judge 選：`05227201` 形容體積超過比較對象的。　信心 0.95　依據：larger 指體積或規模超過比較對象
- gold：`05227202` 形容容量超過比較對象的。

**141. 片**　`wsd-片-add4`　[non_dominant]
- 原句：他站在一片書牆前，
- 譯文：He stood in front of a wall of books.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與片相關的單位或概念
- gold：`05195915` 計算牆或窗戶的單位。

**144. 法**　`wsd-法-7bbd`　[non_dominant]
- 原句：而非國民黨統治機器所貼下標籤的地域區分法‧人們習慣稱呼的本省人其實也是外省移民的第七代，
- 譯文：People are actually accustomed to calling the "ben sheng ren" the seventh generation of waisheng immigrants.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文中的 legal 指法律制度而非法規本身
- gold：`05045104` 做事的步驟或技巧。

**146. 代**　`wsd-代-5679`　[non_dominant]
- 原句：由於本學期校方代學生聯合會向學生收取自治費，
- 譯文：The Student Union collected self-governance fees on behalf of the school this semester.
- judge 選：`07104505` 表替他人處理或執行。　信心 0.98　依據：on behalf of 表示代表他人處理或執行
- gold：`07104502` 排除後述事項，使前述事項佔有其位。

**147. 大**　`wsd-大-6481`　[non_dominant]
- 原句：大蛇竟然把嘴張開，
- 譯文：The serpent actually opened its mouth wide.
- judge 選：`NONE` （NONE）　信心 0.95　依據：wide 形容開口的寬度，與候選義項無關
- gold：`05227201` 形容體積超過比較對象的。

**151. 拿**　`wsd-拿-752a`　[non_dominant]
- 原句：只開放特定場地供學生拿號碼牌寄物。
- 譯文：Only specific areas are open for students to take numbered tickets for luggage storage.
- judge 選：`04011201` 用手取物或持物。　信心 0.95　依據：take tickets 指用手取得編號票券
- gold：`04011202` 向特定對象取得主事者擁有或應該擁有的金錢或物品。

**152. 上**　`wsd-上-21f2`　[non_dominant]
- 原句：一切都只停留在勞作的程度上。
- 譯文：Everything remains at the level of mere labor.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未直接對應任何候選義項
- gold：`04081317` 按前述事物的觀點來陳述。

**154. 發**　`wsd-發-5680`　[non_dominant]
- 原句：是很願意國內所有發卡機構能研擬出一套辦法來針對如果受款行號未照約定履行交付等值之物品，
- 譯文：I sincerely hope that all domestic card-issuing institutions will develop a set of measures to address situations where the acquiring bank fails to fulfill its contractual obligation to deliver equivalent goods.
- judge 選：`06724101` 按特定的分配原則將物品給特定對象。　信心 0.90　依據：deliver 為將物品交付，符合「按分配原則給予」義
- gold：`06724102` 事先核准後將後述證件或執照給特定對象。

**155. 就**　`wsd-就-5f17`　[non_dominant]
- 原句：就是彼此的特性。
- 譯文：It is about each other's characteristics.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未呈現「就」的任何義項功能
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**157. 平**　`wsd-平-cb19`　[non_dominant]
- 原句：車子的把手為平把，
- 譯文：The car has flat handlebars.
- judge 選：`06025201` 形容物體表面高度相同沒有凹凸起伏的。　信心 0.98　依據：flat handlebars 指車把平坦無凹凸
- gold：`06025213` 形容高度相同的。

**158. 高**　`wsd-高-1c47`　[non_dominant]
- 原句：配備精良的美國警方人員在攝影高台上嚴密監視觀眾動態，
- 譯文：Well-equipped U.S. police officers closely monitor the audience from elevated surveillance platforms.
- judge 選：`06010603` 形容物體所處的位置離地面的距離大於比較對象。　信心 0.95　依據：elevated 指位置高於地面
- gold：`06010601` 形容物體從頂部到地面的距離大於比較對象的。

**159. 掛**　`wsd-掛-c83e`　[non_dominant]
- 原句：男孩要求掛急診。
- 譯文：The boy requested emergency treatment.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與掛相關的意涵
- gold：`06701415` 登記並留下紀錄以獲得特定服務。

**160. 破**　`wsd-破-d556`　[non_dominant]
- 原句：大陸經過文化大革命及破四舊的浩劫，
- 譯文：The mainland experienced the catastrophe of the Cultural Revolution and the destruction of the Four Olds.
- judge 選：`06761405` 形容完整的物體有缺口或物品因長期使用而呈現損壞的樣子。　信心 0.90　依據：destruction 指物品因損壞而呈現損壞樣子
- gold：`06761415` 比喻故意違反特定限制或拘束。

**161. 真**　`wsd-真-4c47`　[non_dominant]
- 原句：真希望可以永遠住在那裡。
- 譯文：I truly wish I could live there forever.
- judge 選：`05100406` 形容強調說話者對後述描述內容的肯定。　信心 0.98　依據：truly 表肯定語氣，對後述內容強調
- gold：`05100414` 表說話者主觀評價程度高，帶有誇張語氣或情感。

**163. 邊**　`wsd-邊-fb5e`　[non_dominant]
- 原句：調整的方法是手握雙筒鏡的兩邊，
- 譯文：Adjust the binoculars by holding both sides.
- judge 選：`06584404` 特定對象與其他鄰界對象交界的地方。　信心 0.90　依據：sides 指雙筒望遠鏡的兩側邊緣
- gold：`06584406` 特定地區中位於前述方向邊緣的地點。

**164. 層**　`wsd-層-8006`　[non_dominant]
- 原句：中間那層「主任」完全不在他眼裡。
- 譯文：The middle-tier "Director" meant nothing to him.
- judge 選：`03005008` 計算可以分階層的概念的單位，主要是表達思想、含義、理由等。　信心 0.95　依據：middle-tier 指概念上的分層架構
- gold：`03005006` 根據某種標準而加以分類的同一類人群。

**165. 中**　`wsd-中-c90e`　[non_dominant]
- 原句：這種哲學和傅蘭尼、孔恩等嘗試在科學的知識如何獲得的過程中推論知識論的問題是同一類的，
- 譯文：This type of philosophy, like that of Foucault and Kuhn, attempts to infer epistemological issues in the process of how knowledge is acquired in science, and belongs to the same category.
- judge 選：`04004605` 在前述的機構或領域範圍。　信心 0.90　依據：in the process 譯為「在過程中」，屬機構或領域範圍
- gold：`04004618` 在事件的過程中。

**166. 行**　`wsd-行-8bb0`　[non_dominant]
- 原句：西方國家行之已久的社會安全措施，
- 譯文：Western countries have long implemented social security measures.
- judge 選：`NONE` （NONE）　信心 0.95　依據：implemented 表實施政策，未對應行的任何義項
- gold：`06775707` 依照特定方法實際施行特定事件。

**168. 子**　`wsd-子-daed`　[non_dominant]
- 原句：法華經長者窮子喻之中，
- 譯文：In the parable of the rich man and his poor son in the Lotus Sutra,
- judge 選：`07027902` 父母對自己所生育的男性後代的指稱。　信心 0.98　依據：son 指父母所生的男性後代
- gold：`07027904` 具有前述身份或從事前述工作的人。

**169. 明**　`wsd-明-2c5b`　[non_dominant]
- 原句：而教練費區和球員之間不和的事實也由暗而明，
- 譯文：The rift between the coaching staff and players has gradually become apparent.
- judge 選：`06685411` 形容比喻狀況變得明顯清楚。　信心 0.95　依據：became apparent 指狀況變得明顯清楚
- gold：`06685407` 形容比喻事件在公開的情況下進行的。

**170. 叫**　`wsd-叫-9a50`　[non_dominant]
- 原句：當頑皮的鬧鐘叫了以後，
- 譯文：After the mischievous alarm clock rang,
- judge 選：`NONE` （NONE）　信心 0.95　依據：ring 譯為鈴響，未涉及「叫」的義項
- gold：`04010205` 比喻物體像人一樣發出聲響。

**171. 正**　`wsd-正-e48f`　[non_dominant]
- 原句：其謬誤正如同我們總習於率爾用一個人比擬另一個人。
- 譯文：Just as we often hastily compare one person to another.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「正」相關的意義
- gold：`07009822` 表前述對象不經刻意安排而完全符合後述描述。

**173. 花**　`wsd-花-da24`　[non_dominant]
- 原句：棘皮動物海百合像海中之花般地鮮艷綻放，
- 譯文：Echinoderms like sea lilies bloom brilliantly in the sea like flowers.
- judge 選：`05229001` 植物的主要器官之一，主要用於繁殖，通常具有顏色鮮豔和形狀漂亮的花瓣。　信心 0.98　依據：bloom 直接對應花的開放義項
- gold：`05229006` 比喻事物的精華。

**174. 就**　`wsd-就-d690`　[non_dominant]
- 原句：心浮動就是道心不堅固，
- 譯文：A floating mind is an unsteady Dao mind.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未直接對應任何「就」的義項
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**179. 代**　`wsd-代-38c7`　[non_dominant]
- 原句：這些是發生在這一代華人身上比較新的事情。
- 譯文：These are relatively new events that have happened to this generation of Chinese people.
- judge 選：`04016205` 年齡大致相同的一群人。　信心 0.90　依據：generation 指年齡大致相同的一群人
- gold：`04016206` 計算年齡大致相同的一群人的單位。

**181. 上**　`wsd-上-94b4`　[non_dominant]
- 原句：在個人資料和事件的處理上，
- 譯文：In the handling of personal data and incidents,
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文中「incidents」為獨立名詞，未與「上」形成對應義項
- gold：`04081317` 按前述事物的觀點來陳述。

**182. 分**　`wsd-分-a4e1`　[non_dominant]
- 原句：自家門口遭到三名蒙面歹徒分執鋁製球棒毆傷，
- 譯文：Three people in masks attacked me at my doorstep with aluminum baseball bats and injured me.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文未出現與「分」相關的概念
- gold：`04146408` 表分別。

**184. 條**　`wsd-條-f9f4`　[non_dominant]
- 原句：他的童年像一條浮根，
- 譯文：His childhood was like a floating root.
- judge 選：`NONE` （NONE）　信心 0.95　依據：floating root 未對應任何候選義項
- gold：`06585903` 計算形狀細而長的物體的單位。

**187. 就**　`wsd-就-f48f`　[non_dominant]
- 原句：首先選擇茶葉就是一門學問。
- 譯文：Choosing tea leaves is a subject of study in itself.
- judge 選：`NONE` （NONE）　信心 0.95　依據：譯文中的 Choosing 未對應任何候選義項
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**189. 代**　`wsd-代-2206`　[non_dominant]
- 原句：身為台塑的第二代，
- 譯文：As the second generation of the Formosa Plastics Group,
- judge 選：`04016203` 比喻有衍生關係的特定對象。　信心 0.98　依據：second generation 指衍生的後代系列
- gold：`04016201` 生物血緣關係中所有與其始祖的距離相同的人所組成的團體。

**192. 對**　`wsd-對-85c8`　[non_dominant]
- 原句：但因氣氛及感覺不對，
- 譯文：But since the atmosphere and feeling were off.
- judge 選：`NONE` （NONE）　信心 0.95　依據：off 在此非介詞，譯文未對應任何義項
- gold：`04017503` 形容適合的。

**194. 道**　`wsd-道-e472`　[non_dominant]
- 原句：相信透過教育這最後一道丹藥可以拯救！
- 譯文：I believe that through education, this final elixir can save us!
- judge 選：`NONE` （NONE）　信心 0.95　依據：elixir 未對應任何候選義項
- gold：`04083512` 計算步驟的單位。

**195. 轉**　`wsd-轉-cbbd`　[non_dominant]
- 原句：他三個手指悠然轉著那只淡青色玉鐲。
- 譯文：He leisurely twirled the light blue jade bracelet with three fingers.
- judge 選：`05228801` 物體維持本身的軸心，做連續改變方向的運動。　信心 0.98　依據：twirled 指手指讓玉鐲繞軸心持續轉動
- gold：`05228802` 使物體維持本身的軸心，做連續改變方向的運動。

**198. 畫**　`wsd-畫-7d89`　[non_dominant]
- 原句：例如在畫建築時，
- 譯文：For example, when drawing buildings,
- judge 選：`06550303` 利用線條、色彩在平面上描出特定對象的形象的技巧或知識。　信心 0.98　依據：drawing buildings 指描繪建築的技巧或知識
- gold：`06550301` 利用線條、色彩在平面上做出特定形象。

**199. 空**　`wsd-空-6f79`　[non_dominant]
- 原句：是非成敗轉頭空，
- 譯文：Only the translation is required:

Time turns all victories and defeats to nothing.
- judge 選：`06517327` 形容特定對象完全沒有剩下的。　信心 0.90　依據：nothing 譯為完全沒有剩下的
- gold：`06517332` 形容事物不具有實體概念的。

---

成本：456 次呼叫 / 539,027 tokens / 113.1s / 快取命中 456
run: `runs\20260821-043518-wsd-5d122e.jsonl`