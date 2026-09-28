---
code: de
name: 德文
script: latin
direction: ltr
holdout: true
---
> ⚠️ 德文是**留出語言**（technical design §7.3）。只用於量測，不進反思迴圈。
> 選它的理由：格位標記強制顯性化語法角色，正打中文指代歧義的弱項；
> 且 Sie/du 是獨立於日文敬語的第二條敬體軸。

## 強制顯性化欄位

- `agent` → 德文的格位（Nominativ/Akkusativ/Dativ）強制標出誰對誰做了什麼。
  UNKNOWN 時用 man 或被動態，不得擅自指定人稱
- `social_relation` → 決定 Sie / du。**UNKNOWN 時一律用 Sie**，這是承諾最少的選擇
- `time` → 德文須選時態。UNKNOWN 時用 Präsens
- 名詞性別與冠詞 → 中文無此範疇，依德語本身規則處理即可，
  但不要用冠詞暗示原文沒有的特指

## 翻譯陷阱

- 中文的無主句在德文須補主詞或改被動，容易在此偷渡原文沒有的施事者
- 中文的「還可以」對應 ganz gut 或 akzeptabel，不是 gut
- 分離動詞的語序會把語意重心移到句尾，注意不要改變焦點

## 回譯檢查點

回譯成中文時確認：

- [ ] 德文格位標出的施事／受事關係，是否在回譯中變成原文沒有的明確主詞
- [ ] Sie / du 的選擇是否在回譯中變成「您」而原文並無敬稱
- [ ] 冠詞帶來的特指是否在回譯中變成「那個」「這個」

## Few-shot

| 錨點摘要 | 正確譯法 | 常見錯譯 | 錯在哪 |
| --- | --- | --- | --- |
| 原文「方便的話明天再說吧」，social_relation=UNKNOWN | Wenn es Ihnen passt, verschieben wir es auf morgen. | Wenn du Zeit hast, reden wir morgen. | 用 du 等於擅自指定為熟人關係 |

## 輸出格式約束

- 不得附加英文對照
- 不得用括號補充說明
