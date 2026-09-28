---
code: en
name: 英文
script: latin
direction: ltr
---
## 強制顯性化欄位

英文的語法強制標記出中文可以懸置的資訊。以下欄位為 UNKNOWN 時，必須採取
語意承諾最少的表達，不得憑空補值：

- `agent` → 英文句子幾乎必須有主詞。UNKNOWN 時優先用被動語態、
  祈使句或 it 結構，避免擅自指定 I / you / he
- `time` → 英文必須選一個時態。UNKNOWN 時用現在式或不定式，
  不要擅自用過去式或完成式暗示原文沒有的時間關係
- 名詞單複數 → 中文無標記。數量不明時優先用不可數或泛指複數，
  不要擅自用 a / one 暗示單一

## 翻譯陷阱

- 中文的「了」不等於過去式。「他走了」可能是完成、也可能是狀態改變
- 中文的「你」在正式場合常對應 one / people 而非 you
- 中文無冠詞。加 the 會暗示「特指」，原文未必有這層意思
- 「還可以」「不錯」的評價強度低於英文 good，較接近 acceptable / decent

## 回譯檢查點

回譯成中文時確認：

- [ ] 英文時態帶來的時間資訊，是否在中文回譯中被憑空保留成明確時間詞
- [ ] 英文主詞是否在回譯中被寫死，而原文其實是省略的
- [ ] 單複數是否在回譯中變成明確的數量詞

## Few-shot

| 錨點摘要 | 正確譯法 | 常見錯譯 | 錯在哪 |
| --- | --- | --- | --- |
| 原文「方便的話明天再說吧」，agent=UNKNOWN，intent=SOFT_REFUSAL | Let's leave it until tomorrow, if that works. | I'll tell you tomorrow if it's convenient. | 擅自指定主詞為 I，且把推託讀成承諾 |
| 原文「他昨天走了」，讀法未定 | He left yesterday. | He passed away yesterday. | 擅自選了委婉義，原文兩讀皆可 |

## 輸出格式約束

- 不得附加原文、拼音或註解
- 不得用括號補充說明
- 不得輸出多個候選譯文
