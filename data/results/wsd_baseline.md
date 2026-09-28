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
| judge 回 NONE | 9/200（4%） |
| **可判定** | 191/200（96%） |
| **義項正確率** | **0.550**　[0.479, 0.619] |

## 分層 ⭐ 主結果

| 層 | n（可判定） | 正確 | 正確率 | 95% CI |
| --- | :-: | :-: | :-: | :-: |
| 主流（gold 為最高頻） | 98 | 57 | 0.582 | [0.483, 0.674] |
| 非主流 | 93 | 48 | 0.516 | [0.416, 0.615] |

**兩層之差（主流 − 非主流）**：+6.6pp　95% CI [-7.8, +20.8]pp　p≈0.350

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
| 譯文沒譯出該詞 | 4 | 44%　[0.189, 0.733] | **NONE 正確**，是翻譯的遺漏不是 judge 的錯 |
| 譯文有譯出但 judge 認不出 | 5 | 56%　[0.267, 0.811] | **judge 的問題**，計入 judge 錯誤率 |
| 未分類 | 0 | — | 成因分類呼叫失敗 |

NONE 總數 9／200，已分類 9

---

## (b) 錯誤時模型選了哪個義項 ⭐ 與 CHA-Gen 的銜接

> CHA-Gen 發現「模型偏好主流解讀」。若成立，本專案的錯誤應集中在
> 該詞的最高頻義項那一側。隨機基準為 1/候選數的加權平均。

- 錯誤題數：86
- 其中選到**最高頻義項**：17（19.8%，95% CI [12.7, 29.4]%）
- 隨機基準：13.8%
- **未超過隨機基準（CI 涵蓋之），尚不足以支持**

選中義項的頻率排名分布：第1名 17　第2名 23　第3名 12　第4名 8　第5名 8　第6名 14　第7名 3　第8名 1

---

## (c) 長度稽核

> 問「答錯的題目句子是否較長」。分層報告——聚合值會正負相消
> （CHA-Gen 18 組中 12 組顯著、方向相反，中位數卻是 0.490）。
> 此處 `ambiguity_type` 欄位承載的是 stratum。


| 分層 | 特徵 | n（錯／對） | AUC | SE | 95% CI | 效應量 | 方向 | 排除 0.5 |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 整體 | probe_span 字元數 | 86／105 | 0.540 | 0.042 | [0.458, 0.623] | 0.040 | 選錯者較長 | — |
| 整體 | full_input 字元數 | 86／105 | 0.540 | 0.042 | [0.458, 0.623] | 0.040 | 選錯者較長 | — |
| 整體 | probe_span 詞數估計 | 86／105 | 0.540 | 0.042 | [0.458, 0.623] | 0.040 | 選錯者較長 | — |
| 整體 | probe_span 標點數 | 86／105 | 0.487 | 0.042 | [0.405, 0.570] | 0.013 | 選對者較長 | — |
| 整體 | context 字元數 | 86／105 | 0.500 | 0.042 | [0.417, 0.583] | 0.000 | — | — |
| target_word=中 | probe_span 字元數 | 5／5 | 0.780 | 0.154 | [0.477, 1.000] | 0.280 | 選錯者較長 | — |
| target_word=中 | full_input 字元數 | 5／5 | 0.780 | 0.154 | [0.477, 1.000] | 0.280 | 選錯者較長 | — |
| target_word=中 | probe_span 詞數估計 | 5／5 | 0.780 | 0.154 | [0.477, 1.000] | 0.280 | 選錯者較長 | — |
| target_word=中 | probe_span 標點數 | 5／5 | 0.600 | 0.187 | [0.233, 0.967] | 0.100 | 選錯者較長 | — |
| target_word=去 | probe_span 標點數 | 5／5 | 0.400 | 0.187 | [0.033, 0.767] | 0.100 | 選對者較長 | — |
| ambiguity_type=non_dominant | probe_span 字元數 | 45／48 | 0.561 | 0.060 | [0.444, 0.678] | 0.061 | 選錯者較長 | — |
| ambiguity_type=non_dominant | full_input 字元數 | 45／48 | 0.561 | 0.060 | [0.444, 0.678] | 0.061 | 選錯者較長 | — |
| ambiguity_type=non_dominant | probe_span 詞數估計 | 45／48 | 0.561 | 0.060 | [0.444, 0.678] | 0.061 | 選錯者較長 | — |
| target_word=去 | probe_span 字元數 | 5／5 | 0.460 | 0.191 | [0.086, 0.834] | 0.040 | 選對者較長 | — |
| target_word=去 | full_input 字元數 | 5／5 | 0.460 | 0.191 | [0.086, 0.834] | 0.040 | 選對者較長 | — |
| target_word=去 | probe_span 詞數估計 | 5／5 | 0.460 | 0.191 | [0.086, 0.834] | 0.040 | 選對者較長 | — |
| ambiguity_type=dominant | probe_span 字元數 | 41／57 | 0.521 | 0.059 | [0.405, 0.638] | 0.021 | 選錯者較長 | — |
| ambiguity_type=dominant | full_input 字元數 | 41／57 | 0.521 | 0.059 | [0.405, 0.638] | 0.021 | 選錯者較長 | — |
| ambiguity_type=dominant | probe_span 詞數估計 | 41／57 | 0.521 | 0.059 | [0.405, 0.638] | 0.021 | 選錯者較長 | — |
| ambiguity_type=non_dominant | probe_span 標點數 | 45／48 | 0.481 | 0.060 | [0.363, 0.599] | 0.019 | 選對者較長 | — |
| ambiguity_type=dominant | probe_span 標點數 | 41／57 | 0.491 | 0.059 | [0.375, 0.608] | 0.009 | 選對者較長 | — |
| ambiguity_type=dominant | context 字元數 | 41／57 | 0.500 | 0.059 | [0.384, 0.616] | 0.000 | — | — |
| ambiguity_type=non_dominant | context 字元數 | 45／48 | 0.500 | 0.060 | [0.382, 0.618] | 0.000 | — | — |
| target_word=中 | context 字元數 | 5／5 | 0.500 | 0.191 | [0.125, 0.875] | 0.000 | — | — |
| target_word=去 | context 字元數 | 5／5 | 0.500 | 0.191 | [0.125, 0.875] | 0.000 | — | — |

**CI 排除 0.5 的項目：0 / 25**

沒有任何分層的長度特徵能顯著預測選錯。

---

## 逐筆（請掃一遍判斷 judge 合不合理）

| # | 詞 | 原句 | 譯文 | judge 選的 | gold | 對 |
| :-: | :-: | --- | --- | --- | --- | :-: |
| 1 | 收 | 我們不收支票。 | We do not accept checks. | `03039303` | `03039303` | ✅ |
| 2 | 上 | 街頭上到處也可以看到咖啡店． | You can see coffee shops everywhere on the streets. | `04081315` | `04081314` | ❌ |
| 3 | 心 | 以極為艱難的說話方式表達他心中的感想。 | He expressed his thoughts in an excruciatingly diffi | `05231612` | `05231612` | ✅ |
| 4 | 死 | 皮皮掉到山谷後居然沒死， | Pipi fell into the valley but surprisingly survived. | `05035202` | `05035202` | ✅ |
| 5 | 低 | 創下八十六年以來同季首度滑落千億元以下的最低紀錄。 | It marked the lowest record in over 86 years to fall | `06748407` | `06748406` | ❌ |
| 6 | 歲 | 今年整整滿一百歲了。 | This year marks exactly one hundred years. | `06559403` | `06559405` | ❌ |
| 7 | 掛 | 比如今八三歲父親至今還掛在牆上親自題著「音容宛在」的 | A portrait of a young woman with the inscription "音容 | `06701402` | `06701401` | ❌ |
| 8 | 坐 | 他習慣坐在客運公司走廊一角， | He is used to sitting in a corner of the corridor at | `05223901` | `05223901` | ✅ |
| 9 | 折 | 打七五折是四百六十五。 | It's NT$465 after a 25% discount. | `07033113` | `07033113` | ✅ |
| 10 | 季 | 亞洲出口成長仍於二○○一年第四季反彈回升。 | Asia's export growth rebounded in the fourth quarter | `07026505` | `07026505` | ✅ |
| 11 | 心 | 心裡很不是滋味。 | It leaves a bitter taste in my heart. | `05231612` | `05231612` | ✅ |
| 12 | 死 | 等我什麼時候也死了， | When I die someday. | `05035202` | `05035202` | ✅ |
| 13 | 頭 | 做出一個大小適中的頭， | Make a head of moderate size. | `03043001` | `03043001` | ✅ |
| 14 | 粗 | 英勇的消防隊員合力舉起又粗又大的水管， | Brave firefighters worked together to lift the thick | `06711801` | `06711801` | ✅ |
| 15 | 去 | 以及親手去使用這些資料。 | And personally use this data. | `06559208` | `06559205` | ❌ |
| 16 | 回 | 預計七月結婚的郭思宏利用寒假專程由美國回臺灣與女友拍 | Vicky and her fiancé, Kuo Szu-hung, who plans to get | `03019001` | `03019001` | ✅ |
| 17 | 回 | 每天晚上她回乘務隊的時候， | Every night when she returns to the duty team. | `03019001` | `03019001` | ✅ |
| 18 | 拍 | 一走紅大家都搶著找她拍， | Once she became popular, everyone scrambled to colla | `08028001` | `08028004` | ❌ |
| 19 | 去 | 你先去預備圖章， | Please go prepare the seal first. | `06559201` | `06559205` | ❌ |
| 20 | 頭 | 頭上還要綁布條， | You still have to tie a headband. | `03043001` | `03043001` | ✅ |
| 21 | 拍 | 希望能多拍些劇情片。 | I hope we can make more narrative films. | `08028003` | `08028004` | ❌ |
| 22 | 歲 | 一個在三十歲之前沒有成為社會主義信徒的人， | A person who hasn't become a socialist believer befo | `06559405` | `06559405` | ✅ |
| 23 | 支 | 而韓國隊卻只有七支。 | However, the South Korean team only has seven. | `03056204` | `03056210` | ❌ |
| 24 | 上 | 就把媽祖在海上顯靈的事蹟， | Mazu's miraculous manifestations at sea | `04081315` | `04081314` | ❌ |
| 25 | 坐 | 我坐在書桌前， | I am sitting at my desk. | `05223901` | `05223901` | ✅ |
| 26 | 行 | 我們演習一下就行了， | Let's just practice. | `06775706` | `06775711` | ❌ |
| 27 | 起 | 報名自即日起受理， | Registration is now open. | `04004828` | `04004801` | ❌ |
| 28 | 高 | 台大最高， | National Taiwan University is the best. | `06010615` | `06010610` | ❌ |
| 29 | 心 | 心中非常不甘願， | I am very reluctant. | `05231608` | `05231612` | ❌ |
| 30 | 說 | 陳總統說去年三一八事件今年可能重演； | President Tsai said that the March 18 incident last  | `05212401` | `05212401` | ✅ |
| 31 | 明 | 明起路邊停車巡場管理員將不再受理民眾繳交停車費， | Starting tomorrow, roadside parking patrol officers  | `07003401` | `07003401` | ✅ |
| 32 | 中 | 每家主婦都率領家中的婦女， | Every housewife leads the women in her household. | `04004603` | `04004605` | ❌ |
| 33 | 長 | 工作負荷必須花長時間來記錄， | Workload must be recorded over a long period of time | `06030810` | `06030803` | ❌ |
| 34 | 空 | 這是唯識講『空』的不同處。 | This is the unique approach of the Yogācāra school i | `06517331` | `06517331` | ✅ |
| 35 | 中 | 座中有人提到郝柏村現象， | Someone at the gathering mentioned the "Hao Bai-cun  | `04004605` | `04004605` | ✅ |
| 36 | 歲 | 四十五歲的臺北水準書局老闆曾大福搭朋友的車南下， | The 45-year-old owner of Taipei Shuei-shui Bookstore | `06559405` | `06559405` | ✅ |
| 37 | 回 | 黑派理應回座維持會務， | YUI should return to her seat to maintain the meetin | `03019001` | `03019001` | ✅ |
| 38 | 中 | 恍恍惚惚腦中忽然瞥過過去她那激憤壯烈的夢。 | A fleeting image of her passionate and heroic dream  | `04004604` | `04004605` | ❌ |
| 39 | 會 | 約在１０﹣１２天大時會出現銅離子負平衡， | Around 10 to 12 days old, copper ion negative balanc | `04143405` | `04143405` | ✅ |
| 40 | 字 | 因為我的所有最字， | All my best wishes. | `06584501` | `06584502` | ❌ |
| 41 | 就 | 就造成肥胖症。 | It can lead to obesity. | `05198301` | `05198301` | ✅ |
| 42 | 日 | 經驗上可能在三日內出現天價， | Experience shows that sky-high prices may appear wit | `03036209` | `03036209` | ✅ |
| 43 | 口 | 口吐白沫， | Foaming at the mouth. | `04084201` | `04084201` | ✅ |
| 44 | 股 | 首季每股稅後盈餘約○．八元。 | The after-tax earnings per share for the first quart | `03015702` | `03015710` | ❌ |
| 45 | 中 | 在上次吸吮一章中， | In the previous chapter titled "Sucking," | `04004604` | `04004605` | ❌ |
| 46 | 拿 | 我都拿體重計為小豬們檢查身體， | I always use the scale to check the health of the li | `04011209` | `04011201` | ❌ |
| 47 | 畫 | 每幅畫都很不錯， | All the paintings are excellent. | `06550302` | `06550302` | ✅ |
| 48 | 做 | 他也把我們的垃圾做分類， | He also sorts our trash for recycling. | `06664307` | `06664306` | ❌ |
| 49 | 上 | 多媒體在網路上的應用確實擁有無限發展潛力， | Multimedia applications on the internet indeed have  | `04081315` | `04081314` | ❌ |
| 50 | 行 | 父母就希望你只要書念好就行了。 | Parents just hope that you do well in your studies. | `06775706` | `06775711` | ❌ |
| 51 | 拉 | 連拖帶拉的把豪豪拖到公園去了。 | Dragged Hou Hou to the park, struggling all the way. | `05230801` | `05230801` | ✅ |
| 52 | 坐 | 坐在矮牆上望著大海抽菸， | Sitting on a low wall, smoking while gazing at the s | `05223901` | `05223901` | ✅ |
| 53 | 點 | 以佔指數較重之金融股搶攻４９００點， | Financial stocks, which carry significant weight in  | `04043808` | `04043808` | ✅ |
| 54 | 歲 | 都比薛蘋小幾歲， | Sue is a few years younger than Hsieh Pin. | `06559405` | `06559405` | ✅ |
| 55 | 帶 | 事後我帶他回南部老家見父母， | Afterward, I took him back to my hometown in souther | `06791406` | `06791407` | ❌ |
| 56 | 吃 | Ｗｉｎｓｔｏｎ告訴我們無論如何也要買隻大螃蟹吃才不虛 | Winston told us we absolutely have to buy a big crab | `05227001` | `05227001` | ✅ |
| 57 | 去 | 準備挑到城裡去賣。 | I'm going to take them to the city to sell. | `06559201` | `06559205` | ❌ |
| 58 | 錢 | 但偏偏卻有很多人願把錢送入虎口， | But for some reason, many people are still willing t | `06015102` | `06015105` | ❌ |
| 59 | 過 | 而且從未請過教練， | And I have never hired a coach. | `05206001` | `05206001` | ✅ |
| 60 | 度 | 在澳洲風景明媚的海灘度了兩天假之後， | After spending two days of vacation on Australia's s | `06785401` | `06785402` | ❌ |
| 61 | 畫 | 如果用來記錄美術館的畫， | The system is used to record paintings in an art mus | `06550302` | `06550302` | ✅ |
| 62 | 歲 | 因為我30歲， | Because I am 30 years old. | `06559405` | `06559405` | ✅ |
| 63 | 去 | 就可以去做事了。 | You can start working now. | `06559205` | `06559205` | ✅ |
| 64 | 中 | 讀者可由表中清楚看出， | Readers can clearly see from the table. | `04004603` | `04004605` | ❌ |
| 65 | 度 | 他們繼續在自己生活的地方和工作崗位度信仰的生活。 | They continued to live out their faith in their own  | `NONE` | `06785402` | — |
| 66 | 股 | 中華電週二公布今年每股純益目標為四．一六元， | Taiwan Mobile announced on Tuesday that its target f | `03015702` | `03015710` | ❌ |
| 67 | 季 | 第二季半導體景氣及公司業績可望觸底， | The semiconductor market outlook and company perform | `07026505` | `07026505` | ✅ |
| 68 | 中 | 在ＩＰ通訊協定中， | In IP communication protocols, | `04004605` | `04004605` | ✅ |
| 69 | 點 | 同時在四三００至四七００點間採行箱型操作， | Box operations are conducted between 4300 and 4700 p | `04043808` | `04043808` | ✅ |
| 70 | 吃 | 便和同學偷溜跑去吃刨冰， | We sneaked out with classmates to have shaved ice. | `05227001` | `05227001` | ✅ |
| 71 | 明 | 第四繼承時期是五代至明末。 | The fourth inheritance period spans from the Five Dy | `07003502` | `07003501` | ❌ |
| 72 | 叫 | 出現一個叫永窮的窮小子， | A poor young man named Yongqiong appeared. | `04010207` | `04010206` | ❌ |
| 73 | 條 | 他還是執意走上這條不歸路， | He still insisted on taking this irreversible path. | `06585924` | `06585924` | ✅ |
| 74 | 好 | 「下半場上來的那名後衛很好！ | The defender who came on in the second half is reall | `04157701` | `04157701` | ✅ |
| 75 | 吃 | 年年拼死吃， | I fight to eat every year. | `05227009` | `05227001` | ❌ |
| 76 | 日 | 以實品文物、各國服飾、鈔票特區及影像展呈現出日、韓、 | The exhibition showcases the charm of Japan, South K | `05239901` | `05239901` | ✅ |
| 77 | 吃 | 冰淇淋只好給弟弟吃啦！ | Ice cream can only be given to my little brother to  | `05227001` | `05227001` | ✅ |
| 78 | 場 | 國王明星大前鋒韋伯則攻下全隊最高的21分以及本季個人 | King star power forward Webber scored a team-high 21 | `06721705` | `06721709` | ❌ |
| 79 | 度 | 璩美鳳首先三度表示， | Feng Mei-feng first expressed it three times. | `05147620` | `05147620` | ✅ |
| 80 | 包 | 但依慣例只拿了幾包藥後回家養病。 | But as usual, he only took a few packs of medicine a | `05095701` | `05095711` | ❌ |
| 81 | 拉 | 還是每天拉著那輛三輪車沿街拾荒， | I still pull that tricycle around the streets scaven | `05230801` | `05230801` | ✅ |
| 82 | 帶 | 就能帶個女孩回來。 | You could even bring a girl back. | `06791406` | `06791407` | ❌ |
| 83 | 正 | 正準備開槍， | I was about to pull the trigger. | `NONE` | `07009821` | — |
| 84 | 大 | 年紀輕輕的就擔負這麼大的責任， | At such a young age, you're taking on such great res | `05227204` | `05227204` | ✅ |
| 85 | 分 | 顯示中共有意分階段解決問題， | The Chinese Communist Party has expressed its intent | `04146403` | `04146403` | ✅ |
| 86 | 拉 | 拉著大書包走下車， | I pulled my large backpack off the bus. | `05230801` | `05230801` | ✅ |
| 87 | 好 | 做個好女兒， | Be a good daughter. | `04157701` | `04157701` | ✅ |
| 88 | 上 | 林青霞也在記者會上感動的表示， | Yvonne Yeh also emotionally expressed at the press c | `04081315` | `04081314` | ❌ |
| 89 | 說 | 他已說過很多遍， | He has said it many times. | `05212401` | `05212401` | ✅ |
| 90 | 中 | 第一票不能改變各政黨在國會中的席次比。 | The first vote does not change the seat distribution | `04004605` | `04004605` | ✅ |
| 91 | 小 | 再把芒果切成一小片， | Then cut the mango into small pieces. | `05227101` | `05227101` | ✅ |
| 92 | 叫 | 阿眉叫我不要太擔心她身體。 | Mei asked me not to worry too much about her health. | `05013801` | `05013801` | ✅ |
| 93 | 折 | 軍警票改為八折優待， | Commissioned tickets for military and police personn | `07033113` | `07033113` | ✅ |
| 94 | 會 | 沒有一家銀行會故意違反央行規定， | No bank would deliberately violate the regulations s | `04143405` | `04143405` | ✅ |
| 95 | 去 | 不必去當兵， | You don't have to enlist in the military. | `06559205` | `06559205` | ✅ |
| 96 | 歲 | 看到一位七十幾歲的老先生， | I saw an elderly gentleman in his seventies. | `06559405` | `06559405` | ✅ |
| 97 | 去 | 我們要去旅行， | We are going to travel. | `06559201` | `06559205` | ❌ |
| 98 | 條 | 便可堆出一條筆直的高級公路。 | A straight, high-quality highway can be built this w | `06585906` | `06585924` | ❌ |
| 99 | 強 | 當海水清澈、陽光穿透力強的時候， | When the sea is clear and sunlight penetrates deeply | `09250308` | `09250303` | ❌ |
| 100 | 人 | 有些人批國安聯盟是太上決策機制， | Some people criticize the National Security Alliance | `05231105` | `05231101` | ❌ |
| 101 | 條 | 森林之家的每條街道， | Every street in Forest Home | `06585906` | `06585906` | ✅ |
| 102 | 下 | 在Ｃ目錄下打）ｐａｔｈ）。 | Create a path under the C drive. | `04081803` | `04081808` | ❌ |
| 103 | 高 | 照說素質都很高， | The quality is supposed to be very high. | `06010615` | `06010615` | ✅ |
| 104 | 場 | 除了在萬芳醫院的三場演出之外， | In addition to the three performances at Wanfang Hos | `06721701` | `06721707` | ❌ |
| 105 | 吃 | 「天生我才必有用」、「吃得苦中苦， | "Great minds have aims, petty minds have wishes."
"O | `NONE` | `05227009` | — |
| 106 | 拿 | 偶爾有幾個好心人拿東西給我吃， | Occasionally, a few kind people bring me something t | `04011205` | `04011205` | ✅ |
| 107 | 當 | 而在將高山當郊山玩的途中， | And along the way, while treating towering mountains | `04013907` | `04013901` | ❌ |
| 108 | 強 | 國男組也將進行四強交叉準決賽， | The men's team will also compete in the semifinals c | `09250303` | `09250305` | ❌ |
| 109 | 去 | 她去過多少美國市場， | How many U.S. markets has she visited? | `06559201` | `06559201` | ✅ |
| 110 | 面 | 面無表情地望著大家， | He stared at everyone with a blank expression. | `03028801` | `03028801` | ✅ |
| 111 | 深 | 自己深知道頭銜無用， | I know full well that titles are useless. | `06663313` | `06663313` | ✅ |
| 112 | 去 | 走到了最常去最熟悉的圖書館， | I arrived at the most frequently visited and familia | `06559201` | `06559201` | ✅ |
| 113 | 破 | 自己發球局反在第六局被破， | I was broken in my own serve game in the sixth set. | `06761401` | `06761422` | ❌ |
| 114 | 條 | 教育部在九月初以不符合師資培育法第七條及師範教育精神 | The Ministry of Education ruled in early September t | `06585929` | `06585929` | ✅ |
| 115 | 做 | 剝取牠們的毛皮做標本， | Extract their fur to make specimens. | `06664301` | `06664301` | ✅ |
| 116 | 度 | 那麼如何因應不同需求或在家庭結構變化時必須採行的「二 | Therefore, the "second-time redesign" required to ac | `05147605` | `05147617` | ❌ |
| 117 | 中 | 在車中， | In the car. | `04004603` | `04004603` | ✅ |
| 118 | 去 | 去幾天﹖ | How many days ago? | `06559218` | `06559201` | ❌ |
| 119 | 做 | 做個術德兼修、品學兼優的好學生， | Be a good student who excels in both moral character | `06664308` | `06664308` | ✅ |
| 120 | 粗 | 還有幾支粗簽字筆， | There are still a few thick felt-tip pens. | `06711801` | `06711803` | ❌ |
| 121 | 回 | 有一回他受命去孟家宅院取兩支手槍， | One time, he was ordered to go to the Meng family co | `03019001` | `03019008` | ❌ |
| 122 | 小 | 否則浪費金錢事小， | Otherwise, wasting money is the least of our concern | `05227104` | `05227104` | ✅ |
| 123 | 下 | 並在其下成立系統規格制訂和系統測試小組。 | And establish system specification formulation and s | `04081808` | `04081808` | ✅ |
| 124 | 破 | 也沒聽說過肚皮會破的。 | I've never heard of a belly bursting open either. | `06761402` | `06761404` | ❌ |
| 125 | 道 | 每一個性方面的需求可能有些人比較好此道， | Every individual may have varying levels of expertis | `06002401` | `06002402` | ❌ |
| 126 | 中 | 亦正發展中， | It is also developing in a positive direction. | `04004618` | `04004618` | ✅ |
| 127 | 條 | 一開始就把這條小河川整理一下， | Start by tidying up this small river. | `06585906` | `06585906` | ✅ |
| 128 | 條 | 可是他那兩條硬得像木棍的腿， | But those two legs of his were as stiff as wooden st | `06585910` | `06585910` | ✅ |
| 129 | 過 | 透著粉綠、粉紫、粉紅的金花鱸游曳而過， | A flash of golden perch, tinged with soft green, lav | `04005002` | `04005001` | ❌ |
| 130 | 熱 | 此外響韻、寶麗金也在一波波文藝復興熱， | In addition, Iris and PolyGram are also experiencing | `05228709` | `05228709` | ✅ |
| 131 | 去 | 我們能去嗎？ | Can we go? | `06559201` | `06559201` | ✅ |
| 132 | 條 | 只求挽回一條垂危的生命， | I only seek to save a life hanging by a thread. | `06585924` | `06585911` | ❌ |
| 133 | 就 | 要不然就是陰天。 | Otherwise, it will be overcast. | `05198301` | `05198307` | ❌ |
| 134 | 面 | 她曾在82年奪得區運5面金牌後因傷退出體操界， | She once won five gold medals at the District Games  | `NONE` | `03028807` | — |
| 135 | 部 | 包括二十部保時捷。 | Including twenty Porsche vehicles. | `05075709` | `05075709` | ✅ |
| 136 | 點 | 說得確實點， | Just put it bluntly. | `04043803` | `04043813` | ❌ |
| 137 | 分 | 分不清是夢是真。 | I can't tell if it's a dream or reality. | `04146408` | `04146401` | ❌ |
| 138 | 大 | 又在１９０６年建了更大的ＬａｎｇｄｅｌｌＨａｌｌ， | In 1906, an even larger Langdell Hall was built. | `05227201` | `05227202` | ❌ |
| 139 | 行 | 美國之行並非尋夢、也非淘金， | The trip to the United States was neither a quest fo | `06775704` | `06775704` | ✅ |
| 140 | 吃 | 所有出門的人一定要趕回家來吃年夜飯， | Everyone who goes out must rush home to have the New | `05227024` | `05227024` | ✅ |
| 141 | 片 | 他站在一片書牆前， | He stood in front of a wall of books. | `05195903` | `05195915` | ❌ |
| 142 | 破 | 再破三案。 | Three more cases have been cracked. | `06761412` | `06761412` | ✅ |
| 143 | 就 | 昏沉就是愛睡， | Drowsiness is just loving to sleep. | `05198313` | `05198313` | ✅ |
| 144 | 法 | 而非國民黨統治機器所貼下標籤的地域區分法‧人們習慣稱 | People are actually accustomed to calling the "ben s | `NONE` | `05045104` | — |
| 145 | 熱 | 如此對於賽程的控制和比賽氣氛熱都很有幫助， | This helps a lot in controlling the schedule and hea | `05228723` | `05228723` | ✅ |
| 146 | 代 | 由於本學期校方代學生聯合會向學生收取自治費， | The Student Union collected self-governance fees on  | `07104505` | `07104502` | ❌ |
| 147 | 大 | 大蛇竟然把嘴張開， | The serpent actually opened its mouth wide. | `NONE` | `05227201` | — |
| 148 | 用 | 吃穿用玩樣樣俱全， | Everything is available for eating, dressing, using, | `04017401` | `04017411` | ❌ |
| 149 | 叫 | 你學個貓叫， | Meow! | `04010202` | `04010202` | ✅ |
| 150 | 拉 | 你是說你們那時候連手都沒有拉！ | You said you didn't even hold hands back then! | `05230802` | `05230802` | ✅ |
| 151 | 拿 | 只開放特定場地供學生拿號碼牌寄物。 | Only specific areas are open for students to take nu | `04011201` | `04011202` | ❌ |
| 152 | 上 | 一切都只停留在勞作的程度上。 | Everything remains at the level of mere labor. | `04081315` | `04081317` | ❌ |
| 153 | 大 | 由於批購總額大， | The total procurement amount is large. | `05227203` | `05227203` | ✅ |
| 154 | 發 | 是很願意國內所有發卡機構能研擬出一套辦法來針對如果受 | I sincerely hope that all domestic card-issuing inst | `06724101` | `06724102` | ❌ |
| 155 | 就 | 就是彼此的特性。 | It is about each other's characteristics. | `NONE` | `05198313` | — |
| 156 | 作 | 或許這部小說也是明人所作的， | Perhaps this novel was also written by a Ming dynast | `05098103` | `05098103` | ✅ |
| 157 | 平 | 車子的把手為平把， | The car has flat handlebars. | `06025201` | `06025213` | ❌ |
| 158 | 高 | 配備精良的美國警方人員在攝影高台上嚴密監視觀眾動態， | Well-equipped U.S. police officers closely monitor t | `06010607` | `06010601` | ❌ |
| 159 | 掛 | 男孩要求掛急診。 | The boy requested emergency treatment. | `06701415` | `06701415` | ✅ |
| 160 | 破 | 大陸經過文化大革命及破四舊的浩劫， | The mainland experienced the catastrophe of the Cult | `06761405` | `06761415` | ❌ |
| 161 | 真 | 真希望可以永遠住在那裡。 | I truly wish I could live there forever. | `05100406` | `05100414` | ❌ |
| 162 | 行 | 聽取奎爾簡報他此行經過及與沙烏地阿拉伯國王法德和科威 | I listened to Kuier's briefing on his trip and the t | `06775704` | `06775704` | ✅ |
| 163 | 邊 | 調整的方法是手握雙筒鏡的兩邊， | Adjust the binoculars by holding both sides. | `06584404` | `06584406` | ❌ |
| 164 | 層 | 中間那層「主任」完全不在他眼裡。 | The middle-tier "Director" meant nothing to him. | `03005006` | `03005006` | ✅ |
| 165 | 中 | 這種哲學和傅蘭尼、孔恩等嘗試在科學的知識如何獲得的過 | This type of philosophy, like that of Foucault and K | `04004605` | `04004618` | ❌ |
| 166 | 行 | 西方國家行之已久的社會安全措施， | Western countries have long implemented social secur | `06775707` | `06775707` | ✅ |
| 167 | 季 | 所以這兩隊的競爭從這一季的第一場球就開始了， | So the rivalry between these two teams began with th | `07026504` | `07026504` | ✅ |
| 168 | 子 | 法華經長者窮子喻之中， | In the parable of the rich man and his poor son in t | `07027901` | `07027904` | ❌ |
| 169 | 明 | 而教練費區和球員之間不和的事實也由暗而明， | The rift between the coaching staff and players has  | `06685411` | `06685407` | ❌ |
| 170 | 叫 | 當頑皮的鬧鐘叫了以後， | After the mischievous alarm clock rang, | `04010201` | `04010205` | ❌ |
| 171 | 正 | 其謬誤正如同我們總習於率爾用一個人比擬另一個人。 | Just as we often hastily compare one person to anoth | `07009822` | `07009822` | ✅ |
| 172 | 拍 | 「原來拍古裝戲這麼辛苦！ | "Turns out filming period dramas is so exhausting!" | `08028003` | `08028003` | ✅ |
| 173 | 花 | 棘皮動物海百合像海中之花般地鮮艷綻放， | Echinoderms like sea lilies bloom brilliantly in the | `05229001` | `05229006` | ❌ |
| 174 | 就 | 心浮動就是道心不堅固， | A floating mind is an unsteady Dao mind. | `05198301` | `05198313` | ❌ |
| 175 | 支 | 由國內四支球隊選出的職棒明星隊負責把守第二關。 | The all-star team composed of four domestic teams wi | `03056204` | `03056204` | ✅ |
| 176 | 度 | 因此面前的視野交集區只有十度。 | Therefore, the overlapping field of view in front of | `05147607` | `05147607` | ✅ |
| 177 | 來 | 國外學生來台主要集中在台灣師大學中文， | The main concentration of international students com | `04086501` | `04086501` | ✅ |
| 178 | 正 | 後人乘涼正是本院圖書館自動化的最佳寫照， | Future generations benefit from the cool shade, whic | `07009822` | `07009822` | ✅ |
| 179 | 代 | 這些是發生在這一代華人身上比較新的事情。 | These are relatively new events that have happened t | `04016205` | `04016206` | ❌ |
| 180 | 好 | 好漂亮啊！ | That's so beautiful! | `04157710` | `04157710` | ✅ |
| 181 | 上 | 在個人資料和事件的處理上， | In the handling of personal data and incidents, | `04081315` | `04081317` | ❌ |
| 182 | 分 | 自家門口遭到三名蒙面歹徒分執鋁製球棒毆傷， | Three people in masks attacked me at my doorstep wit | `NONE` | `04146408` | — |
| 183 | 做 | 堂姊就做了一個洋娃娃給我。 | My cousin made a doll for me. | `06664301` | `06664301` | ✅ |
| 184 | 條 | 他的童年像一條浮根， | His childhood was like a floating root. | `NONE` | `06585903` | — |
| 185 | 發 | ∥我要靠意外之財我才能發啦我！ | I'm counting on a windfall to strike it rich! | `05193416` | `05193406` | ❌ |
| 186 | 大 | 竹葉上有一大群螞蟻， | There is a large group of ants on the bamboo leaf. | `05227203` | `05227203` | ✅ |
| 187 | 就 | 首先選擇茶葉就是一門學問。 | Choosing tea leaves is a subject of study in itself. | `05198301` | `05198313` | ❌ |
| 188 | 打 | 謝玄只用了五千人就把秦兵打得大敗， | Only five thousand of Xie Xuan's troops routed the Q | `05229126` | `05229126` | ✅ |
| 189 | 代 | 身為台塑的第二代， | As the second generation of the Formosa Plastics Gro | `04016203` | `04016201` | ❌ |
| 190 | 大 | 好大的一個螺殼！ | What a huge shell! | `05227201` | `05227201` | ✅ |
| 191 | 收 | 還捨不得收起來。 | I still can't bear to put it away. | `03039314` | `03039314` | ✅ |
| 192 | 對 | 但因氣氛及感覺不對， | But since the atmosphere and feeling were off. | `04017506` | `04017503` | ❌ |
| 193 | 人 | 高階積體電路設計公司至少雇用十人以上， | A high-end integrated circuit design company must em | `05231102` | `05231109` | ❌ |
| 194 | 道 | 相信透過教育這最後一道丹藥可以拯救！ | I believe that through education, this final elixir  | `04083505` | `04083512` | ❌ |
| 195 | 轉 | 他三個手指悠然轉著那只淡青色玉鐲。 | He leisurely twirled the light blue jade bracelet wi | `05228801` | `05228802` | ❌ |
| 196 | 重 | 拿起大包小包的行李也就不覺得重了。 | Picking up all the big and small pieces of luggage d | `05207602` | `05207602` | ✅ |
| 197 | 行 | 李總統康乃爾之行， | President Tsai's visit to Cornell University | `06775704` | `06775704` | ✅ |
| 198 | 畫 | 例如在畫建築時， | For example, when drawing buildings, | `06550303` | `06550301` | ❌ |
| 199 | 空 | 是非成敗轉頭空， | Only the translation is required:

Time turns all vi | `06517327` | `06517332` | ❌ |
| 200 | 條 | 或者手拉手走一條霪雨霏霏的街。 | Or hand in hand, we walk down a rain-soaked street. | `06585906` | `06585906` | ✅ |

### 錯誤與 NONE 的細節

**2. 上**　`wsd-上-10d2`　[dominant]
- 原句：街頭上到處也可以看到咖啡店．
- 譯文：You can see coffee shops everywhere on the streets.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：整句強調「街道」作為可見範圍的主題
- gold：`04081314` 事件的發生在前述事物的範圍內。

**5. 低**　`wsd-低-a891`　[dominant]
- 原句：創下八十六年以來同季首度滑落千億元以下的最低紀錄。
- 譯文：It marked the lowest record in over 86 years to fall below NT$100 billion for the same quarter.
- judge 選：`06748407` 形容數值變小。　信心 0.95　依據：譯文強調數值降至歷史新低
- gold：`06748406` 形容數值小於比較對象的。

**6. 歲**　`wsd-歲-5ae2`　[dominant]
- 原句：今年整整滿一百歲了。
- 譯文：This year marks exactly one hundred years.
- judge 選：`06559403` 計算時間的單位，一歲有十二個月。　信心 0.95　依據：整句強調時間長度的一百年
- gold：`06559405` 計算年齡的單位。

**7. 掛**　`wsd-掛-3cf0`　[dominant]
- 原句：比如今八三歲父親至今還掛在牆上親自題著「音容宛在」的少婦像，
- 譯文：A portrait of a young woman with the inscription "音容宛在" still hangs on the wall, painted by my 83-year-old father.
- judge 選：`06701402` 特定物體的一端被支撐而維持在特定高度。　信心 0.95　依據：整句在說畫像被懸掛於牆上
- gold：`06701401` 支撐特定物體的一端使其維持在特定高度。

**15. 去**　`wsd-去-6d5f`　[dominant]
- 原句：以及親手去使用這些資料。
- 譯文：And personally use this data.
- judge 選：`06559208` 表藉由前述工具、方法或範圍進行後述事件。　信心 0.95　依據：整句在說以此資料為工具或方法
- gold：`06559205` 表前述對象進行後述事件。

**18. 拍**　`wsd-拍-241f`　[dominant]
- 原句：一走紅大家都搶著找她拍，
- 譯文：Once she became popular, everyone scrambled to collaborate with her on photo shoots.
- judge 選：`08028001` 用攝影器材拍照片。　信心 0.95　依據：整句在說拍攝照片的合作行為
- gold：`08028004` 參與拍攝電影與製作。

**19. 去**　`wsd-去-9e53`　[dominant]
- 原句：你先去預備圖章，
- 譯文：Please go prepare the seal first.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說前往特定地點準備印章
- gold：`06559205` 表前述對象進行後述事件。

**21. 拍**　`wsd-拍-8759`　[dominant]
- 原句：希望能多拍些劇情片。
- 譯文：I hope we can make more narrative films.
- judge 選：`08028003` 用攝影器材紀錄動態影像。　信心 0.95　依據：整句在說製作敘事影片，強調動態影像紀錄
- gold：`08028004` 參與拍攝電影與製作。

**23. 支**　`wsd-支-1fe0`　[dominant]
- 原句：而韓國隊卻只有七支。
- 譯文：However, the South Korean team only has seven.
- judge 選：`03056204` 計算團隊的單位。　信心 0.95　依據：整句在說團隊人數
- gold：`03056210` 計算棒球賽中擊出的有效打擊數。

**24. 上**　`wsd-上-e2ba`　[dominant]
- 原句：就把媽祖在海上顯靈的事蹟，
- 譯文：Mazu's miraculous manifestations at sea
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：at sea 表示以海域為主題範圍
- gold：`04081314` 事件的發生在前述事物的範圍內。

**26. 行**　`wsd-行-45ab`　[dominant]
- 原句：我們演習一下就行了，
- 譯文：Let's just practice.
- judge 選：`06775706` 做，取代整個事件。　信心 0.95　依據：整句在說進行練習活動
- gold：`06775711` 形容表示同意或允許。

**27. 起**　`wsd-起-b672`　[dominant]
- 原句：報名自即日起受理，
- 譯文：Registration is now open.
- judge 選：`04004828` 開始或產生。　信心 0.95　依據：註冊程序開始啟動
- gold：`04004801` 表示事件時間範圍的開始參考點。

**28. 高**　`wsd-高-1f42`　[dominant]
- 原句：台大最高，
- 譯文：National Taiwan University is the best.
- judge 選：`06010615` 形容程度或標準高於比較對象。　信心 0.95　依據：整句強調優越程度而非實際高度
- gold：`06010610` 形容數值大於比較對象。

**29. 心**　`wsd-心-ce2d`　[dominant]
- 原句：心中非常不甘願，
- 譯文：I am very reluctant.
- judge 選：`05231608` 想做特定事件的念頭。　信心 0.95　依據：整句在說猶豫不決的念頭
- gold：`05231612` 人的感情或思想。

**32. 中**　`wsd-中-85bc`　[dominant]
- 原句：每家主婦都率領家中的婦女，
- 譯文：Every housewife leads the women in her household.
- judge 選：`04004603` 在前述對象所包含的空間範圍。　信心 0.95　依據：整句在說婦女在其家庭成員的空間範圍內
- gold：`04004605` 在前述的機構或領域範圍。

**33. 長**　`wsd-長-d38d`　[dominant]
- 原句：工作負荷必須花長時間來記錄，
- 譯文：Workload must be recorded over a long period of time.
- judge 選：`06030810` 時間的長度。　信心 0.95　依據：整句強調時間跨度的長度
- gold：`06030803` 形容事件持續的時間間隔大。

**38. 中**　`wsd-中-d396`　[dominant]
- 原句：恍恍惚惚腦中忽然瞥過過去她那激憤壯烈的夢。
- 譯文：A fleeting image of her passionate and heroic dream suddenly flashed through my hazy mind.
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：整句強調夢想在腦海中閃現的時間點
- gold：`04004605` 在前述的機構或領域範圍。

**40. 字**　`wsd-字-c8e1`　[dominant]
- 原句：因為我的所有最字，
- 譯文：All my best wishes.
- judge 選：`06584501` 記錄語言的書面符號。　信心 0.90　依據：整句在表達祝福的書面語言符號
- gold：`06584502` 中文書面書寫的最小單位。

**44. 股**　`wsd-股-32a8`　[dominant]
- 原句：首季每股稅後盈餘約○．八元。
- 譯文：The after-tax earnings per share for the first quarter were approximately NT$0.8.
- judge 選：`03015702` 上櫃或上市公司用來表示其公司股份的證券。　信心 0.95　依據：譯文提及「每股稅後盈餘」直接對應股票證券
- gold：`03015710` 計算股份的單位。

**45. 中**　`wsd-中-6473`　[dominant]
- 原句：在上次吸吮一章中，
- 譯文：In the previous chapter titled "Sucking,"
- judge 選：`04004604` 在前述的時間範圍內。　信心 0.95　依據：標題中的「中」指前一章節的時間範圍
- gold：`04004605` 在前述的機構或領域範圍。

**46. 拿**　`wsd-拿-b7ca`　[dominant]
- 原句：我都拿體重計為小豬們檢查身體，
- 譯文：I always use the scale to check the health of the little pigs.
- judge 選：`04011209` 引介事件所憑藉的方法或工具。　信心 0.95　依據：整句強調用工具（秤）來達成檢查目的
- gold：`04011201` 用手取物或持物。

**48. 做**　`wsd-做-8944`　[dominant]
- 原句：他也把我們的垃圾做分類，
- 譯文：He also sorts our trash for recycling.
- judge 選：`06664307` 進行特定正式活動。　信心 0.90　依據：整句在說進行垃圾分類的正式活動
- gold：`06664306` 做，取代整個事件。

**49. 上**　`wsd-上-e882`　[dominant]
- 原句：多媒體在網路上的應用確實擁有無限發展潛力，
- 譯文：Multimedia applications on the internet indeed have unlimited potential for development.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：「上」在此表示「網際網路」為主題範圍
- gold：`04081314` 事件的發生在前述事物的範圍內。

**50. 行**　`wsd-行-a94f`　[dominant]
- 原句：父母就希望你只要書念好就行了。
- 譯文：Parents just hope that you do well in your studies.
- judge 選：`06775706` 做，取代整個事件。　信心 0.90　依據：整句在說「做好學業」而非實際移動
- gold：`06775711` 形容表示同意或允許。

**55. 帶**　`wsd-帶-de6d`　[dominant]
- 原句：事後我帶他回南部老家見父母，
- 譯文：Afterward, I took him back to my hometown in southern Taiwan to meet my parents.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：整句在說「我」讓「他」跟著移動
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**57. 去**　`wsd-去-a508`　[dominant]
- 原句：準備挑到城裡去賣。
- 譯文：I'm going to take them to the city to sell.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說帶領他們前往城市
- gold：`06559205` 表前述對象進行後述事件。

**58. 錢**　`wsd-錢-f034`　[dominant]
- 原句：但偏偏卻有很多人願把錢送入虎口，
- 譯文：But for some reason, many people are still willing to throw their money into the tiger's den.
- judge 選：`06015102` 通指貨幣。　信心 0.95　依據：整句在談論人們投入貨幣到虎穴
- gold：`06015105` 經費、錢財。

**60. 度**　`wsd-度-334e`　[dominant]
- 原句：在澳洲風景明媚的海灘度了兩天假之後，
- 譯文：After spending two days of vacation on Australia's scenic beaches
- judge 選：`06785401` 從特定地理範圍的一邊到另一邊，通常為水體。　信心 0.90　依據：假期在海灘上度過，語義為跨越地理範圍
- gold：`06785402` 經過特定時段。

**64. 中**　`wsd-中-797e`　[dominant]
- 原句：讀者可由表中清楚看出，
- 譯文：Readers can clearly see from the table.
- judge 選：`04004603` 在前述對象所包含的空間範圍。　信心 0.90　依據：從表格的空間範圍內可見
- gold：`04004605` 在前述的機構或領域範圍。

**65. 度**　`wsd-度-4fa1`　[dominant]
- 原句：他們繼續在自己生活的地方和工作崗位度信仰的生活。
- 譯文：They continued to live out their faith in their own places of residence and work.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文未提及任何與「度」相關的時空或抽象概念
- gold：`06785402` 經過特定時段。

**66. 股**　`wsd-股-47e8`　[dominant]
- 原句：中華電週二公布今年每股純益目標為四．一六元，
- 譯文：Taiwan Mobile announced on Tuesday that its target for earnings per share this year is NT$4.16.
- judge 選：`03015702` 上櫃或上市公司用來表示其公司股份的證券。　信心 0.95　依據：譯文提及公司股份證券的目標價
- gold：`03015710` 計算股份的單位。

**71. 明**　`wsd-明-3724`　[dominant]
- 原句：第四繼承時期是五代至明末。
- 譯文：The fourth inheritance period spans from the Five Dynasties to the end of the Ming Dynasty.
- judge 選：`07003502` 明朝的國號或政權。　信心 0.95　依據：整句在說明朝政權的時間跨度
- gold：`07003501` 中國朝代名，西元1368至1644年，由朱元璋所建立。

**72. 叫**　`wsd-叫-2b66`　[dominant]
- 原句：出現一個叫永窮的窮小子，
- 譯文：A poor young man named Yongqiong appeared.
- judge 選：`04010207` 根據前述定義給予後述對象名稱。　信心 0.95　依據：整句在說命名為「永瓊」
- gold：`04010206` 叫特定對象的名字是後述對象。

**75. 吃**　`wsd-吃-8bc8`　[dominant]
- 原句：年年拼死吃，
- 譯文：I fight to eat every year.
- judge 選：`05227009` 比喻經歷後述負面事件。　信心 0.95　依據：整句在說為生存奮鬥，採比喻用法
- gold：`05227001` 使物體經過口中吞入體內。

**78. 場**　`wsd-場-50f3`　[dominant]
- 原句：國王明星大前鋒韋伯則攻下全隊最高的21分以及本季個人單場最多之12個籃板球。
- 譯文：King star power forward Webber scored a team-high 21 points and a season-high 12 rebounds.
- judge 選：`06721705` 特定表演或比賽的段落。　信心 0.90　依據：譯文提到球員得分與籃板，屬比賽段落
- gold：`06721709` 計算經過安排的活動的單位。

**80. 包**　`wsd-包-07f6`　[dominant]
- 原句：但依慣例只拿了幾包藥後回家養病。
- 譯文：But as usual, he only took a few packs of medicine and went home to recuperate.
- judge 選：`05095701` 折疊紙、布或其他薄片狀物以覆蓋物體所有的面。　信心 0.90　依據：整句在說用外皮包覆藥品
- gold：`05095711` 計算成包物品的單位。

**82. 帶**　`wsd-帶-b6cb`　[dominant]
- 原句：就能帶個女孩回來。
- 譯文：You could even bring a girl back.
- judge 選：`06791406` 有支配權的人使所支配的特定對象跟著自己移動。　信心 0.95　依據：整句在說讓女孩跟著自己移動
- gold：`06791407` 使特定對象跟著有支配權的人移動。

**83. 正**　`wsd-正-8b50`　[dominant]
- 原句：正準備開槍，
- 譯文：I was about to pull the trigger.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句在說扣扳機動作即將發生，未傳達「正」的語義
- gold：`07009821` 表動作進行中或狀態持續中。

**88. 上**　`wsd-上-2481`　[dominant]
- 原句：林青霞也在記者會上感動的表示，
- 譯文：Yvonne Yeh also emotionally expressed at the press conference,
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：press conference 是以 Yvonne Yeh 為主題的場合
- gold：`04081314` 事件的發生在前述事物的範圍內。

**97. 去**　`wsd-去-eeed`　[dominant]
- 原句：我們要去旅行，
- 譯文：We are going to travel.
- judge 選：`06559201` 向特定地點移動。　信心 0.95　依據：整句在說前往某處進行旅行
- gold：`06559205` 表前述對象進行後述事件。

**98. 條**　`wsd-條-a722`　[dominant]
- 原句：便可堆出一條筆直的高級公路。
- 譯文：A straight, high-quality highway can be built this way.
- judge 選：`06585906` 計算地面上長條型的建築物或自然景觀的單位。　信心 0.95　依據：highway為長條型地面建築景觀
- gold：`06585924` 計算行進的路線的單位。

**99. 強**　`wsd-強-95c5`　[dominant]
- 原句：當海水清澈、陽光穿透力強的時候，
- 譯文：When the sea is clear and sunlight penetrates deeply.
- judge 選：`09250308` 形容光線的強度大。　信心 0.95　依據：整句在說陽光穿透的強度高
- gold：`09250303` 形容能力或發展狀況好的。

**100. 人**　`wsd-人-9047`　[dominant]
- 原句：有些人批國安聯盟是太上決策機制，
- 譯文：Some people criticize the National Security Alliance as an extra-constitutional decision-making mechanism.
- judge 選：`05231105` 自己以外的人。　信心 0.95　依據：譯文強調批評者為他人而非自己
- gold：`05231101` 軀幹直立，用雙腳行走的高等動物，具備思考能力，有語言文字，能進行社交活動。

**102. 下**　`wsd-下-496b`　[non_dominant]
- 原句：在Ｃ目錄下打）ｐａｔｈ）。
- 譯文：Create a path under the C drive.
- judge 選：`04081803` 鄰近前述物體的底部或低於該物體位置。　信心 0.95　依據：整句在說磁碟機根目錄下方的路徑
- gold：`04081808` 比喻階級架構中低於前述階級的階級。

**104. 場**　`wsd-場-9bec`　[non_dominant]
- 原句：除了在萬芳醫院的三場演出之外，
- 譯文：In addition to the three performances at Wanfang Hospital,
- judge 選：`06721701` 具有特定用途且可開放給大眾使用的地方或建築物。　信心 0.95　依據：醫院為可開放使用的場所，語義明確
- gold：`06721707` 計算戲劇中較小段落的單位。

**105. 吃**　`wsd-吃-cf63`　[non_dominant]
- 原句：「天生我才必有用」、「吃得苦中苦，
- 譯文："Great minds have aims, petty minds have wishes."
"Only through hardship can one achieve greatness."
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文完全未涉及飲食或比喻語義
- gold：`05227009` 比喻經歷後述負面事件。

**107. 當**　`wsd-當-d0c0`　[non_dominant]
- 原句：而在將高山當郊山玩的途中，
- 譯文：And along the way, while treating towering mountains like mere hills for a casual outing,
- judge 選：`04013907` 引介背景事件作為時間的範圍。　信心 0.95　依據：while 引介背景事件作為時間範圍
- gold：`04013901` 前述對象的工作或身份是後述對象。

**108. 強**　`wsd-強-7c81`　[non_dominant]
- 原句：國男組也將進行四強交叉準決賽，
- 譯文：The men's team will also compete in the semifinals crossover.
- judge 選：`09250303` 形容能力或發展狀況好的。　信心 0.90　依據：整句強調團隊能力優秀而參賽
- gold：`09250305` 競賽中排名在前述範圍的特定對象。

**113. 破**　`wsd-破-6095`　[non_dominant]
- 原句：自己發球局反在第六局被破，
- 譯文：I was broken in my own serve game in the sixth set.
- judge 選：`06761401` 前述物體因受到外力影響使特定部位脫離，而影響外觀的完整性。　信心 0.90　依據：整句在說球員在發球局中失敗
- gold：`06761422` 比喻在球類運動中，在對方發球的局數中，將其擊敗。

**116. 度**　`wsd-度-378e`　[non_dominant]
- 原句：那麼如何因應不同需求或在家庭結構變化時必須採行的「二度設計」就是我們檢討萬年平面的參考方向。
- 譯文：Therefore, the "second-time redesign" required to accommodate different needs or changes in family structure serves as our reference direction for reviewing the "never-changing floor plan."
- judge 選：`05147605` 比喻前述特性的程度。　信心 0.95　依據：整句強調「程度」作為參考方向
- gold：`05147617` 計算空間維數的單位。

**118. 去**　`wsd-去-d84e`　[non_dominant]
- 原句：去幾天﹖
- 譯文：How many days ago?
- judge 選：`06559218` 比喻前述時段經過，成為特定時間點以前的時段。　信心 0.95　依據：整句在問過去的時間點，符合時間經過的比喻義
- gold：`06559201` 向特定地點移動。

**120. 粗**　`wsd-粗-704b`　[non_dominant]
- 原句：還有幾支粗簽字筆，
- 譯文：There are still a few thick felt-tip pens.
- judge 選：`06711801` 形容條狀物的橫切面的面積大。　信心 0.95　依據：felt-tip pens 的筆桿橫切面面積大
- gold：`06711803` 形容線條的寬度大。

**121. 回**　`wsd-回-1e59`　[non_dominant]
- 原句：有一回他受命去孟家宅院取兩支手槍，
- 譯文：One time, he was ordered to go to the Meng family compound to retrieve two pistols.
- judge 選：`03019001` 從其它地方到原來的地方或處所。　信心 0.95　依據：整句在說被命令前往某處取回物品
- gold：`03019008` 計算事件的單位。

**124. 破**　`wsd-破-f6ff`　[non_dominant]
- 原句：也沒聽說過肚皮會破的。
- 譯文：I've never heard of a belly bursting open either.
- judge 選：`06761402` 形容完整的物體因受到外力影響而裂成小塊的。　信心 0.90　依據：整句在說腹部因外力而裂開
- gold：`06761404` 特定物品產生缺口。

**125. 道**　`wsd-道-ef48`　[non_dominant]
- 原句：每一個性方面的需求可能有些人比較好此道，
- 譯文：Every individual may have varying levels of expertise or interest in matters related to intimacy.
- judge 選：`06002401` 思想或理論。　信心 0.90　依據：譯文中的 matters 承載「事物」語義，與思想或理論相關
- gold：`06002402` 含有哲理的技藝。

**129. 過**　`wsd-過-46a1`　[non_dominant]
- 原句：透著粉綠、粉紫、粉紅的金花鱸游曳而過，
- 譯文：A flash of golden perch, tinged with soft green, lavender, and pink, darted by.
- judge 選：`04005002` 穿越特定障礙或界線。　信心 0.95　依據：darted by 表快速穿越空間
- gold：`04005001` 由特定路徑通過。

**132. 條**　`wsd-條-7771`　[non_dominant]
- 原句：只求挽回一條垂危的生命，
- 譯文：I only seek to save a life hanging by a thread.
- judge 選：`06585924` 計算行進的路線的單位。　信心 0.90　依據：整句在說拯救一條垂死的生命
- gold：`06585911` 計算動物性命的單位。

**133. 就**　`wsd-就-fe97`　[non_dominant]
- 原句：要不然就是陰天。
- 譯文：Otherwise, it will be overcast.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.95　依據：Otherwise表條件假設，符合充分條件義
- gold：`05198307` 表強調說話者已知事實。

**134. 面**　`wsd-面-572d`　[non_dominant]
- 原句：她曾在82年奪得區運5面金牌後因傷退出體操界，
- 譯文：She once won five gold medals at the District Games in 1982 before retiring from gymnastics due to an injury.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文未提及任何與「面」相關之語義
- gold：`03028807` 計算牌狀物的單位。

**136. 點**　`wsd-點-b366`　[non_dominant]
- 原句：說得確實點，
- 譯文：Just put it bluntly.
- judge 選：`04043803` 書寫筆畫的一種，沒有線條或延伸。　信心 0.95　依據：bluntly 表達直接陳述，對應筆畫的點
- gold：`04043813` 表不確定的小數量。

**137. 分**　`wsd-分-1598`　[non_dominant]
- 原句：分不清是夢是真。
- 譯文：I can't tell if it's a dream or reality.
- judge 選：`04146408` 表分別。　信心 0.90　依據：整句在說區辨夢與現實的差異
- gold：`04146401` 特定對象分開。

**138. 大**　`wsd-大-6041`　[non_dominant]
- 原句：又在１９０６年建了更大的ＬａｎｇｄｅｌｌＨａｌｌ，
- 譯文：In 1906, an even larger Langdell Hall was built.
- judge 選：`05227201` 形容體積超過比較對象的。　信心 0.90　依據：larger 指建物體積大於原有
- gold：`05227202` 形容容量超過比較對象的。

**141. 片**　`wsd-片-add4`　[non_dominant]
- 原句：他站在一片書牆前，
- 譯文：He stood in front of a wall of books.
- judge 選：`05195903` 計算平而薄的物品的單位。　信心 0.90　依據：書籍為平薄物品，片在此作量詞
- gold：`05195915` 計算牆或窗戶的單位。

**144. 法**　`wsd-法-7bbd`　[non_dominant]
- 原句：而非國民黨統治機器所貼下標籤的地域區分法‧人們習慣稱呼的本省人其實也是外省移民的第七代，
- 譯文：People are actually accustomed to calling the "ben sheng ren" the seventh generation of waisheng immigrants.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句在談稱呼習慣，未涉法律或法術語義
- gold：`05045104` 做事的步驟或技巧。

**146. 代**　`wsd-代-5679`　[non_dominant]
- 原句：由於本學期校方代學生聯合會向學生收取自治費，
- 譯文：The Student Union collected self-governance fees on behalf of the school this semester.
- judge 選：`07104505` 表替他人處理或執行。　信心 0.95　依據：整句在說代表學校代收費用
- gold：`07104502` 排除後述事項，使前述事項佔有其位。

**147. 大**　`wsd-大-6481`　[non_dominant]
- 原句：大蛇竟然把嘴張開，
- 譯文：The serpent actually opened its mouth wide.
- judge 選：`NONE` （NONE）　信心 0.90　依據：整句在說張口的幅度，與「大」的比較義無關
- gold：`05227201` 形容體積超過比較對象的。

**148. 用**　`wsd-用-dfc4`　[non_dominant]
- 原句：吃穿用玩樣樣俱全，
- 譯文：Everything is available for eating, dressing, using, and playing.
- judge 選：`04017401` 利用特定對象的特定功能。　信心 0.90　依據：整句在說事物可被用於特定功能
- gold：`04017411` 特定事物所預期發揮的功能。

**151. 拿**　`wsd-拿-752a`　[non_dominant]
- 原句：只開放特定場地供學生拿號碼牌寄物。
- 譯文：Only specific areas are open for students to take numbered tickets for luggage storage.
- judge 選：`04011201` 用手取物或持物。　信心 0.95　依據：整句在說學生用手取得行李票
- gold：`04011202` 向特定對象取得主事者擁有或應該擁有的金錢或物品。

**152. 上**　`wsd-上-21f2`　[non_dominant]
- 原句：一切都只停留在勞作的程度上。
- 譯文：Everything remains at the level of mere labor.
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：譯文強調「層次」為主題範圍
- gold：`04081317` 按前述事物的觀點來陳述。

**154. 發**　`wsd-發-5680`　[non_dominant]
- 原句：是很願意國內所有發卡機構能研擬出一套辦法來針對如果受款行號未照約定履行交付等值之物品，
- 譯文：I sincerely hope that all domestic card-issuing institutions will develop a set of measures to address situations where the acquiring bank fails to fulfill its contractual obligation to deliver equivalent goods.
- judge 選：`06724101` 按特定的分配原則將物品給特定對象。　信心 0.90　依據：整句在說核准後將物品交付給對象
- gold：`06724102` 事先核准後將後述證件或執照給特定對象。

**155. 就**　`wsd-就-5f17`　[non_dominant]
- 原句：就是彼此的特性。
- 譯文：It is about each other's characteristics.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文無條件、轉折或強調語氣之語義
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**157. 平**　`wsd-平-cb19`　[non_dominant]
- 原句：車子的把手為平把，
- 譯文：The car has flat handlebars.
- judge 選：`06025201` 形容物體表面高度相同沒有凹凸起伏的。　信心 0.95　依據：handlebars 表面平整無凹凸
- gold：`06025213` 形容高度相同的。

**158. 高**　`wsd-高-1c47`　[non_dominant]
- 原句：配備精良的美國警方人員在攝影高台上嚴密監視觀眾動態，
- 譯文：Well-equipped U.S. police officers closely monitor the audience from elevated surveillance platforms.
- judge 選：`06010607` 形容有前述高度的。　信心 0.90　依據：elevated platforms 表達有高度的平台
- gold：`06010601` 形容物體從頂部到地面的距離大於比較對象的。

**160. 破**　`wsd-破-d556`　[non_dominant]
- 原句：大陸經過文化大革命及破四舊的浩劫，
- 譯文：The mainland experienced the catastrophe of the Cultural Revolution and the destruction of the Four Olds.
- judge 選：`06761405` 形容完整的物體有缺口或物品因長期使用而呈現損壞的樣子。　信心 0.95　依據：整句在說文物或傳統遭受嚴重損壞
- gold：`06761415` 比喻故意違反特定限制或拘束。

**161. 真**　`wsd-真-4c47`　[non_dominant]
- 原句：真希望可以永遠住在那裡。
- 譯文：I truly wish I could live there forever.
- judge 選：`05100406` 形容強調說話者對後述描述內容的肯定。　信心 0.95　依據：整句強調說話者對願望的真誠肯定
- gold：`05100414` 表說話者主觀評價程度高，帶有誇張語氣或情感。

**163. 邊**　`wsd-邊-fb5e`　[non_dominant]
- 原句：調整的方法是手握雙筒鏡的兩邊，
- 譯文：Adjust the binoculars by holding both sides.
- judge 選：`06584404` 特定對象與其他鄰界對象交界的地方。　信心 0.90　依據：整句在說雙筒望遠鏡的兩側邊緣
- gold：`06584406` 特定地區中位於前述方向邊緣的地點。

**165. 中**　`wsd-中-c90e`　[non_dominant]
- 原句：這種哲學和傅蘭尼、孔恩等嘗試在科學的知識如何獲得的過程中推論知識論的問題是同一類的，
- 譯文：This type of philosophy, like that of Foucault and Kuhn, attempts to infer epistemological issues in the process of how knowledge is acquired in science, and belongs to the same category.
- judge 選：`04004605` 在前述的機構或領域範圍。　信心 0.90　依據：屬於某個領域範疇（哲學流派）
- gold：`04004618` 在事件的過程中。

**168. 子**　`wsd-子-daed`　[non_dominant]
- 原句：法華經長者窮子喻之中，
- 譯文：In the parable of the rich man and his poor son in the Lotus Sutra,
- judge 選：`07027901` 兒子和女兒。　信心 0.95　依據：譯文中「son」直接對應「子」作為兒子之意
- gold：`07027904` 具有前述身份或從事前述工作的人。

**169. 明**　`wsd-明-2c5b`　[non_dominant]
- 原句：而教練費區和球員之間不和的事實也由暗而明，
- 譯文：The rift between the coaching staff and players has gradually become apparent.
- judge 選：`06685411` 形容比喻狀況變得明顯清楚。　信心 0.95　依據：整句在說狀況變得明顯清楚
- gold：`06685407` 形容比喻事件在公開的情況下進行的。

**170. 叫**　`wsd-叫-9a50`　[non_dominant]
- 原句：當頑皮的鬧鐘叫了以後，
- 譯文：After the mischievous alarm clock rang,
- judge 選：`04010201` 人以大聲量發聲。　信心 0.95　依據：整句在說鬧鐘發出聲響
- gold：`04010205` 比喻物體像人一樣發出聲響。

**173. 花**　`wsd-花-da24`　[non_dominant]
- 原句：棘皮動物海百合像海中之花般地鮮艷綻放，
- 譯文：Echinoderms like sea lilies bloom brilliantly in the sea like flowers.
- judge 選：`05229001` 植物的主要器官之一，主要用於繁殖，通常具有顏色鮮豔和形狀漂亮的花瓣。　信心 0.95　依據：整句以花比喻海百合的外觀
- gold：`05229006` 比喻事物的精華。

**174. 就**　`wsd-就-d690`　[non_dominant]
- 原句：心浮動就是道心不堅固，
- 譯文：A floating mind is an unsteady Dao mind.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：整句強調前提條件下的自然發展
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**179. 代**　`wsd-代-38c7`　[non_dominant]
- 原句：這些是發生在這一代華人身上比較新的事情。
- 譯文：These are relatively new events that have happened to this generation of Chinese people.
- judge 選：`04016205` 年齡大致相同的一群人。　信心 0.95　依據：譯文強調同一時代的華人世代
- gold：`04016206` 計算年齡大致相同的一群人的單位。

**181. 上**　`wsd-上-94b4`　[non_dominant]
- 原句：在個人資料和事件的處理上，
- 譯文：In the handling of personal data and incidents,
- judge 選：`04081315` 以前述事物為主題的範圍。　信心 0.90　依據：譯文強調以個人數據為主題範圍
- gold：`04081317` 按前述事物的觀點來陳述。

**182. 分**　`wsd-分-a4e1`　[non_dominant]
- 原句：自家門口遭到三名蒙面歹徒分執鋁製球棒毆傷，
- 譯文：Three people in masks attacked me at my doorstep with aluminum baseball bats and injured me.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文無任何與「分」相關之語義
- gold：`04146408` 表分別。

**184. 條**　`wsd-條-f9f4`　[non_dominant]
- 原句：他的童年像一條浮根，
- 譯文：His childhood was like a floating root.
- judge 選：`NONE` （NONE）　信心 0.90　依據：譯文無計量或條列語義
- gold：`06585903` 計算形狀細而長的物體的單位。

**185. 發**　`wsd-發-68d0`　[non_dominant]
- 原句：∥我要靠意外之財我才能發啦我！
- 譯文：I'm counting on a windfall to strike it rich!
- judge 選：`05193416` 產生特定心理狀態或思想特質。　信心 0.90　依據：整句在說期待意外之財
- gold：`05193406` 形容得到讓眾人羨慕的名利。

**187. 就**　`wsd-就-f48f`　[non_dominant]
- 原句：首先選擇茶葉就是一門學問。
- 譯文：Choosing tea leaves is a subject of study in itself.
- judge 選：`05198301` 表前述事件為後述事件的充分條件，表示在該條件或情況下自然發展。　信心 0.90　依據：整句強調選擇茶葉本身即為研究主題
- gold：`05198313` 表加強說話者對陳述內容的肯定。

**189. 代**　`wsd-代-2206`　[non_dominant]
- 原句：身為台塑的第二代，
- 譯文：As the second generation of the Formosa Plastics Group,
- judge 選：`04016203` 比喻有衍生關係的特定對象。　信心 0.90　依據：「第二代」指衍生的後續系列
- gold：`04016201` 生物血緣關係中所有與其始祖的距離相同的人所組成的團體。

**192. 對**　`wsd-對-85c8`　[non_dominant]
- 原句：但因氣氛及感覺不對，
- 譯文：But since the atmosphere and feeling were off.
- judge 選：`04017506` 引介事件所涉及的對象或範圍。　信心 0.90　依據：譯文中的 off 指向氣氛與感覺所涉及的對象
- gold：`04017503` 形容適合的。

**193. 人**　`wsd-人-64c0`　[non_dominant]
- 原句：高階積體電路設計公司至少雇用十人以上，
- 譯文：A high-end integrated circuit design company must employ at least ten or more people.
- judge 選：`05231102` 具有前述身份或從事前述工作的人。　信心 0.95　依據：整句在說公司須僱用特定工作的個體
- gold：`05231109` 符合特定需求、從事特定工作的人。

**194. 道**　`wsd-道-e472`　[non_dominant]
- 原句：相信透過教育這最後一道丹藥可以拯救！
- 譯文：I believe that through education, this final elixir can save us!
- judge 選：`04083505` 比喻處理事情或解決問題的方法。　信心 0.90　依據：elixir在此被譬喻為拯救方法
- gold：`04083512` 計算步驟的單位。

**195. 轉**　`wsd-轉-cbbd`　[non_dominant]
- 原句：他三個手指悠然轉著那只淡青色玉鐲。
- 譯文：He leisurely twirled the light blue jade bracelet with three fingers.
- judge 選：`05228801` 物體維持本身的軸心，做連續改變方向的運動。　信心 0.95　依據：整句在說手指讓玉鐲做連續方向改變
- gold：`05228802` 使物體維持本身的軸心，做連續改變方向的運動。

**198. 畫**　`wsd-畫-7d89`　[non_dominant]
- 原句：例如在畫建築時，
- 譯文：For example, when drawing buildings,
- judge 選：`06550303` 利用線條、色彩在平面上描出特定對象的形象的技巧或知識。　信心 0.95　依據：整句在說建築繪製技巧的行為
- gold：`06550301` 利用線條、色彩在平面上做出特定形象。

**199. 空**　`wsd-空-6f79`　[non_dominant]
- 原句：是非成敗轉頭空，
- 譯文：Only the translation is required:

Time turns all victories and defeats to nothing.
- judge 選：`06517327` 形容特定對象完全沒有剩下的。　信心 0.95　依據：譯文強調「一切化為烏有」表完全不剩
- gold：`06517332` 形容事物不具有實體概念的。

---

成本：409 次呼叫 / 631,753 tokens / 139.3s / 快取命中 229
run: `runs\20260821-044157-wsd-b8ab37.jsonl`