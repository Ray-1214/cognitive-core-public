# dev-30 複核表（第二輪：三方交叉複核合議）

> 來源：`data/dev30/sentences.yaml`
> SHA-256：`9e46cf8b9d0c7d58ad1c396d3af7402d6ecffec063db0f799fe2e4f41fec8e3d`
> 句數：30（LEXICAL 9、REFERENTIAL 9、PRAGMATIC 12）
> 第一輪結果：keep 19／applied 2／deferred 9（已寫回 YAML 的 `review_r1`）
> 
> 本檔由 `scripts/make_review_r2.py` 產生。機械欄位取自 YAML；
> 三方意見取自 `data/dev30/review_r2_inputs.yaml`；**「合議建議」是助理的判斷，**
> **在你逐句確認之前一律不算數**，`meta.reviewed` 維持 false。

## ⚠️ 先讀這段：標註獨立性已經改變

標註鐵則 1 是「某句的標註在任何模型看過它之前凍結」，鐵則 2 是「模型輸出只能
用來判斷準則是否涵蓋不足，不可逐句補」。本輪之後：

- 30 句**全部**被 grok / gpt / claude 看過，而且三方都給了逐句改法。
  原本只有 `dev-lex-01`、`dev-prg-05` 兩句有缺口。
- 直接影響 Phase D 的「7 模型跑 dev-30 收集讀法聯集 → 判斷準則完備性」——
  其中三個模型的讀法已經回流進標註。
- 依鐵則 2 的用法：三方意見只拿來改**準則**（§2 的 D1–D8），
  逐句改動由你自己下判斷。這件事必須寫進論文的資料集章節。

另一件同樣要記住的事：三份複核都看過現行的 licensed/spurious 標註（不是盲標），
所以「三方一致 keep」只代表沒有人反對，不是獨立驗證通過。實際上在
`ref-03`／`ref-06`／`prg-06` 三題，你第一輪的母語判斷與三方**全體**相反。

## §0 這張表怎麼用

1. **先答 §1 的 11 個母語問題**（只有你能答，其中 Q1 一題連動三句的去留）。
2. **再裁定 §2 的 8 個準則決策**（D1–D8）。這些一旦定案，多數逐句 verdict 就自動確定，
   不必一句一句重想。
3. §3 的 4 項機械修正**不需要等 1 和 2**，可以現在就做。
4. 最後回到 §4 逐句填 `**verdict**:`。

> 填 verdict 時請用 `keep` / `fix: 具體改法` / `drop` / `uncertain` 當開頭，
> `scripts/apply_review.py` 是用冒號前的第一個 token 判斷種類的；
> 說明文字寫在下一行的 `**note**:`。

## §1 只有母語者能回答的問題

這些是本表唯一真正卡住的地方 —— 助理與三個模型都給不出可信答案，
因為它們全都是台灣華語的語感問題。

### Q1　（`dev-ref-03`、`dev-ref-06`、`dev-prg-06`）

你在第一輪對這三句都說「只有一個讀法」，但 grok / gpt / claude 三方全部說兩讀成立。
逐句確認你的判斷是否維持：

- `ref-03` 媽媽罵妹妹，因為她把杯子打破了 —— 「她」能不能指媽媽（自己打破而遷怒）？
- `ref-06` 老闆同意了小張的提案，這是他第一次成功 —— 「他」能不能指老闆？
- `prg-06` 這樣也可以啦 —— 有沒有真心認可的讀法，還是「也…啦」一定帶勉強？

確認為單讀的，走 D4 選項 B（回收成單讀對照組），不是丟掉。

### Q2　（`dev-lex-07`）

依你第一輪的原話，「他手上有東西」的第二讀是不是「手邊有事情占著、不方便做事或幫忙」？
若是，licensed 2「握有把柄或籌碼」直接刪（你判定那是英譯直譯的產物），改寫成這個讀法。

### Q3　（`dev-lex-09`）

台灣華語的「他昨天走了」能不能表「離職」？現在「辭職」被列在 spurious，
若可得就要移到 licensed，否則會直接罰掉答對的模型。

### Q4　（`dev-lex-01`）

「這個人很難說」能不能表「這個人講不通道理、不好溝通」（現行 licensed 2）？
還是只有「難以評斷其為人」一讀？

### Q5　（`dev-lex-03`）

「我們研究研究」的官場推託義，在台灣的公務／職場語境自然嗎？
（被質疑是中國大陸語感；台灣較常說「再研究一下」「再看看」。）

### Q6　（`dev-lex-04`）

「那家店歇業了」能不能只表「今天沒開」（招牌上的「本日歇業」）？
若能，這個消歧句就沒有鎖住永久義，要換。

### Q7　（`dev-ref-02`）

「經理跟助理說自己要出差」的「自己」是否唯一指經理？
（若是，這是比重複職稱更自然的消歧手段；ref-08 因為「自己」在賓語位置可長距離綁定，不適用。）

### Q8　（`dev-prg-12`）

「我知道了」能不能表「我早就知道了」？現在「我早就知道了」被列為 spurious。

### Q9　（`dev-prg-10`）

「這件衣服很適合你」的兩讀差在說話者身分（朋友／店員），句子裡沒有任何線索。
有沒有任何長度差 ≤2 的改寫能鎖住其中一讀？若沒有，本題改列「文本層不可消歧」案例。

### Q10　（`dev-prg-07`）

你第一輪說「能換掉是最好」—— 確定換掉嗎？
換掉會讓 PRAGMATIC 只剩 11 句，9/9/12 配比要補一句。

### Q11　（`dev-lex-01`、`dev-lex-02`、`dev-lex-05`）

下面五條 spurious 你已經表態過「離譜／不會有人這樣說」：

- `lex-01`「此人說話有口吃」「此人的名字很難念」
- `lex-02`「他降價了」
- `lex-05`「他很會生小孩」「他很會製作人偶」

確認全部刪除嗎？（依 D2，這類荒謬項會讓 precision 虛高。）
`lex-02`「他放棄了生命」另計 —— 你說「感覺是拔管，但也不太會有人這樣說」，
要刪，還是移到 licensed？

## §2 準則層決策

先定這些，逐句 verdict 才不會互相打架。每一項都附「現象 / 證據 / 選項 / 建議」，
建議欄是助理的判斷，可以直接否決。

### D1　篇章外（第三人）讀法政策

**現象**

同一種結構，第三人讀法在 ref-04 / 07 / 08 是 licensed，在 ref-01 / 03 / 05 / 09 是 spurious。
模型若一致輸出第三人讀法，會在一半題目得分、另一半被罰 —— precision 與 recall 同時被
標籤不一致污染，而不是被模型能力決定。

**涉及**：`dev-ref-01`、`dev-ref-03`、`dev-ref-04`、`dev-ref-05`、`dev-ref-07`、`dev-ref-08`、`dev-ref-09`

**選項**

- A 全面 license 第三人讀法（成本：ref-01/03/05/09 移除 4 條第三人 spurious）
- B 只認句內候選（成本：ref-04/07/08 移除 3 條 licensed，且推翻你第一輪已套用的 ref-04 決定）
- C 中性化，新增 discourse_external 標記，評分時不計分子也不計分母（成本：schema + eval 都要改）

**建議**

A。與你第一輪在 ref-04 已作的裁決（「有可能是第三者帶的」）一致，改動最小，
也符合中文代詞可跨句指涉的事實。副作用是 licensed 變寬鬆，要在論文的評分規則裡寫明。

**裁定**：<!-- 填 A / B / C / 其他 -->

### D2　spurious_reading 的準入標準

**現象**

現行 spurious 混了三種東西：

1. **語法／形態上不可得** —— `ref-08`（約束原則 B）、`ref-02/04/09`「兩人都…」（無複數標記）
2. **語境上不太可能** —— 多數
3. **荒謬到沒有鑑別力** —— `lex-01`「口吃」「名字難念」、`lex-05`「製作人偶」

規格書把 spurious_readings 當 precision@k 的分母，所以第 3 類讓 precision 虛高；
而第 2 類裡面其實可得的那幾條（`lex-06`「沒有任何想法」、`lex-09`「辭職」、
`prg-11`「命令對方去工作」）讓 precision 虛低。兩個方向的偏誤都不是模型造成的。

**涉及**：`dev-lex-01`、`dev-lex-02`、`dev-lex-05`、`dev-lex-06`、`dev-lex-07`、`dev-lex-09`、`dev-prg-04`、`dev-prg-09`、`dev-prg-11`

**選項**

- A 兩個必要條件（i）任何合理前文下都不可得（ii）是模型真的可能生成的過度推論；不合格者刪
- B 加 spurious_level 欄位（grammatical / contextual），precision 分兩張表報
- C 維持現狀

**建議**

A，並順手做 B（多一個欄位、多一張表，成本很低）。範本是 ref-08 —— 全表唯一
由語法保證不可得的 spurious。預估要動的約 12 條，逐條列在各題的合議欄。

**裁定**：<!-- 填 A / B / C / 其他 -->

### D3　PRAGMATIC 的「消歧」門檻與最小對立對約束

**現象**

判準 2（消歧句沒有第二讀）對語用題結構上不可能滿足 —— 反諷可以附著在任何讚美上，
「你看起來很健康」照樣說得酸。判準 4（不順便改語域）也不可能 ——
語用消歧本來就是把言外之意直說，語域必然變。等於用一組自我否定的判準在驗收 12 句。

**涉及**：`dev-prg-01`、`dev-prg-03`、`dev-prg-04`、`dev-prg-07`、`dev-prg-09`、`dev-prg-10`、`dev-prg-11`

**選項**

- A 改成「預設讀法唯一」，最小對立對約束改為長度差 ≤2 + 保留說話者與受話者角色（不要求語域不變）
- B PRAG 不做最小對立對，AUC 負例另造中性句
- C 維持現狀

**建議**

A。這也順便把 prg-07 / prg-11「消歧句把主語從『你』換成『我』」判成違規（本來就該修）。
長度平衡仍要守 —— §8 已經證明長度單獨就能撐出 0.965 的 AUC。

**裁定**：<!-- 填 A / B / C / 其他 -->

### D4　母語者判定為單讀的題目怎麼處理

**現象**

ref-03、ref-06、prg-06 你第一輪都說只有一讀，三個模型全說兩讀成立。
這三題是三方一致答錯的題目。

**涉及**：`dev-ref-03`、`dev-ref-06`、`dev-prg-06`、`dev-prg-07`

**選項**

- A drop（9/9/12 配比破掉，要補句）
- B 回收成單讀對照組 —— text_determinable=true、licensed 留一讀、被否決的讀法移到 spurious
- C 保留兩讀（等於推翻你的母語判斷）

**建議**

B。理由：這三題正好是「模型會不會硬造第二讀」的直接測點，而三個模型都上鉤了，
當成正例比丟掉有價值得多；而且順便補上 dev-30 完全沒有的 fast 正例（見 D8）。
prg-07 你已經說「能換掉是最好」，那題走 A，另補一句 PRAG。

**裁定**：<!-- 填 A / B / C / 其他 -->

### D5　類別歸屬 —— LEXICAL 裡的語用題

**現象**

lex-03（推託）、lex-05（褒貶）、lex-06（是否表態）、lex-08（指令內容）的歧義軸
其實是言語行為或評價極性，不是詞義。規格書要用 by-type 檢定「日文優勢是否集中在
語用／社會關係類、在詞彙歧義上消失」—— 類別被污染，這個檢定就不可解釋。

**涉及**：`dev-lex-03`、`dev-lex-05`、`dev-lex-06`、`dev-lex-08`

**選項**

- A 改類別（配比要重排，牽動最多）
- B 保留 ambiguity_type，新增次級欄位 ambiguity_axis（詞義／指涉／言語行為／評價極性），分析時用次級欄位
- C 維持現狀

**建議**

B。成本最低，而且 §4.4 的分型檢定真的做得下去。

**裁定**：<!-- 填 A / B / C / 其他 -->

### D6　標註 codebook（field_determinable / required_clarifications）

**現象**

這兩個欄位的判定規則沒有寫在任何檔案裡，只能從 30 句反推，而反推出來的規則已經打架：

- `required_clarifications` 用了 coreference，但 `field_determinable` 沒有這一欄（取值域不對齊）
- `lex-02` / `lex-04` / `lex-09` 是空集合卻有 2–3 個讀法（五個欄位撐不起省略賓語、時間範圍、委婉語）
- `ref-07` 把與讀法選擇無關的 tense 也列進去
- social_relation 在 `ref-03`（罵）判 true、`ref-09`（吵架）判 false

規格書 Phase D 寫「要改就改準則 → 從準則重標全部」，但準則目前不存在於任何檔案。

**涉及**：`dev-lex-02`、`dev-lex-04`、`dev-lex-09`、`dev-ref-07`、`dev-ref-09`

**選項**

- A 凍結 v1 前先寫一頁 codebook（每欄一行判定規則 + 一正一反例），再照它重掃 30 句的欄位
- B 先凍結，codebook 等 CAD-60 再寫

**建議**

A。CAD-60 要「照同一準則標 60 句」，沒有 codebook 就辦不到；而且第二標註者信度
（若要報 kappa）也需要它。這件事不做，dev-30 凍不了 v1。

**裁定**：<!-- 填 A / B / C / 其他 -->

### D7　標註獨立性 —— 本輪之後 30 句全部曝光

**現象**

標註鐵則 1「某句的標註在任何模型看過它之前凍結」、鐵則 2「模型輸出只能用來判斷
準則是否涵蓋不足，不可逐句補」。本輪之後，30 句全部被 grok / gpt / claude 看過，
而且三方都給了逐句改法。原本只有 lex-01、prg-05 有缺口。
直接影響 Phase D checklist 的「7 模型跑 dev-30 收集讀法聯集 → 判斷準則完備性」——
其中三個模型的讀法已經回流進標註了。

**涉及**：`dev-lex-01`、`dev-prg-05`

**選項**

- A 三方意見只用於準則層（D1–D6），逐句改動一律由你自己下判斷，論文逐句揭露
- B 依技術設計文件的資料集表，dev-30 本來就標「✅ 隨便看」，獨立性宣稱只對 CAD-60 提出
- C 換掉 lex-01 與 prg-05（現在收益已低，因為 30 句都曝光了）

**建議**

A + B 併行，並在論文資料集章節照實寫。C 只有在你還要對 dev-30 宣稱
「標註未受模型影響」時才值得做。

**裁定**：<!-- 填 A / B / C / 其他 -->

### D8　fast 正例 —— 30 題全是 slow

**現象**

expected_route 全 30 題都是 slow、text_determinable 全 30 題都是 false。
RQ2 的「Router 分流準確率」在這份資料上只量得到 recall，量不到 false-slow 率
（把簡單句誤送慢速通道的成本，正好是 RQ2 要辯護的東西）。

**選項**

- A 把 30 個消歧句正式列為 items（expected_route=fast, text_determinable=true），dev-30 變 30+30
- B 只把 D4 回收的單讀句轉成 fast 正例（3–4 句，太少）
- C 另造 15 句無歧義句

**建議**

A。消歧句本來就是為此造的，AUC 也已經拿它們當負例，只是沒有正式進 items。
但要注意一個維度混淆：prg-06「這樣也可以啦」若只有勉強義，它是「無歧義但有語用負載」——
走 fast 會翻壞。這類句子需要單獨標（例如 pragmatic_load: true），不要跟「簡單句」混在一起。

**裁定**：<!-- 填 A / B / C / 其他 -->

## §3 機械修正（不涉及語言判斷，可立刻做）

### M1　中文 enum 兩處

lex-08 reading 3 的 speaker_intent 是「指示」、ref-04 reading 3 是「敘述」，
其餘 22 個值都是英文常數。來源是 scripts/apply_review.py 的 APPLY 表寫死了中文
（照抄你的原話），不是原始標註的問題。
做法：改成 INSTRUCT / NARRATE，同時修 APPLY 表避免下次再引入，
並加一個凍結前的 enum 檢查。

**涉及**：`dev-lex-08`、`dev-ref-04`

**採用**：<!-- 是 / 否 -->

### M2　edit 欄宣稱「等長替換」但字數差不是 0（6 題）

prg-04 −1、prg-07 −2、prg-08 +1、prg-10 −1、prg-11 +1、prg-12 +1。
只改描述字串，不動句子。（長度平衡的實際約束是 ≤2，這 6 題都沒違規，
違規的是描述本身不誠實。）

**涉及**：`dev-prg-04`、`dev-prg-07`、`dev-prg-08`、`dev-prg-10`、`dev-prg-11`、`dev-prg-12`

**採用**：<!-- 是 / 否 -->

### M3　required_clarifications 的取值域沒對齊 field_determinable

required_clarifications 用到 coreference，但 field_determinable 只有
agent / tense / register / social_relation / speaker_intent 五欄。
指代題（9 題）全部靠這個對不上的鍵。併入 D6 的 codebook 一起定。

**涉及**：`dev-ref-01`、`dev-ref-02`、`dev-ref-03`、`dev-ref-04`、`dev-ref-05`、`dev-ref-06`、`dev-ref-07`、`dev-ref-08`、`dev-ref-09`

**採用**：<!-- 是 / 否 -->

### M4　verdict 欄請用可解析的前綴

scripts/apply_review.py 用 `冒號前的第一個 token` 當 verdict 種類。
你在 lex-01 寫的「不會有:"…"的說法」會被解析成 verdict=「不會有」。
第二輪請寫成 `fix: 不會有「口吃」這種說法` 這種格式，註解留給 note 欄。

**涉及**：`dev-lex-01`

**採用**：<!-- 是 / 否 -->

## §4 逐句

每題的欄位來源：事實取自 YAML；「第一輪（你）」取自 `review_r1`；
三方表格取自 `review_r2_inputs.yaml`；「合議建議」是助理判斷。

===========================================================

## dev-lex-01  (LEXICAL)　［連動 D2、D7；待答 Q4、Q11］

> 🔴 **標註獨立性缺口**：助理曾看過 mistral-small-4 對本句提議的讀法（草稿早於此，之後未改動本句）

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 這個人很難說 | 6 |
| 消歧 | 此人難以評斷 | 6 |

改動：難說 → 難以評斷（等長替換）　　字數差：+0
消歧後鎖定：此人的為人難以評斷

**licensed_readings**
1. 此人的為人難以評斷　　適用：討論對象是第三者的人格特質　　intent=EVALUATE
2. 此人不好溝通、講不通道理　　適用：先前提及與此人交涉受阻　　intent=COMPLAIN

**spurious_readings**
- 此人說話有口吃或發音困難
- 此人的名字很難念

**text_determinable**: false
**field_determinable**: agent=false / tense=true / register=true / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 歧義確實存在，消歧句自然鎖定第一讀；spurious 可留作對照。 |
| gpt | `keep` | 兩讀都能由「很難說」自然觸發，兩個 spurious 也確實不是常規語義。 |
| claude | `fix` | 消歧句「此人難以評斷」還能讀成「此人難以評斷別人」；兩個 spurious 荒謬到沒有鑑別力；質疑 licensed 2 在台灣華語是否可得。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

你在檔案裡已經對 spurious 1 表態，方向與 claude 一致 —— 依 D2 兩條 spurious 都刪。
消歧句另有主／賓兩讀（誰評斷誰），候選：「這個人不好評價」（6 字，+0，語域不變）。
licensed 2 是否成立看 Q4。本句已在污染清單內，見 D7。

**卡在**：Q4、Q11（見 §1）

---
**verdict**: 不會有:"此人說話有口吃或發音困難"的說法<!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-lex-02  (LEXICAL)　［連動 D2、D6；待答 Q11］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 他終於放下了 | 6 |
| 消歧 | 他終於釋懷了 | 6 |

改動：放下 → 釋懷（同長度替換）　　字數差：+0
消歧後鎖定：他終於釋懷、不再執著

**licensed_readings**
1. 他終於釋懷、不再執著　　適用：先前提及情感或心結　　intent=NARRATE
2. 他終於把手上的東西放下　　適用：先前提及他拿著某物　　intent=NARRATE
3. 他終於卸下職務　　適用：先前提及職位或責任　　intent=NARRATE

**spurious_readings**
- 他放棄了生命
- 他降價了

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: []

**第一輪（你）**：`fix`（deferred）　—　放棄生命感覺是拔管 但是也不太會有人這樣說 降價是最不可能的

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 三讀（釋懷、物理放下、卸職）皆合理且互不相容。 |
| gpt | `keep` | 三讀成立；「卸下職務」稍偏語境化，可改寫成「放下這份工作／責任」。 |
| claude | `fix` | spurious 1 在安寧療護／佛教語境可作「安詳離世」的委婉語，不乾淨；三讀靠零形賓語，其實接近 REFERENTIAL。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

你第一輪已說「降價是最不可能的」（＝荒謬型，依 D2 刪）、「放棄生命感覺是拔管，
但也不太會有人這樣說」（＝介於可得與不可得之間，見 Q11 下半）。
另 required_clarifications 是空集合卻有三讀 —— 五個欄位問不出「省略的賓語是什麼」，
慢速通道在這題收斂不了，併 D6 處理。

**卡在**：Q11（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-lex-03  (LEXICAL)　［連動 D5；待答 Q5］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 我們研究研究 | 6 |
| 消歧 | 我們實際研議 | 6 |

改動：研究研究 → 實際研議（等長替換）　　字數差：+0
消歧後鎖定：我們實際進行研議

**licensed_readings**
1. 我們實際進行研議　　適用：說話者具決策權且情境正式　　intent=COMMIT
2. 拖延推託的官場套語，實則不打算處理　　適用：對方提出請託，說話者無意應允　　intent=SOFT_REFUSAL

**spurious_readings**
- 我們去做學術研究
- 我們互相研究對方

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent', 'social_relation']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 官場語境的真研議／推託兩讀成立；消歧句稍正式但仍自然。 |
| gpt | `fix` | 第 2 讀是語用推論不是詞義，不宜當 lexical reading；「互相研究對方」也不自然。 |
| claude | `fix` | 「我們實際研議」不像人話；推託義偏中國大陸語感；spurious 1「學術研究」在實驗室語境其實可得，與 licensed 用同一種挑選機制卻被判不可得。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

你第一輪判 keep（母語者認可兩讀），所以讀法本身保留，先答 Q5 確認地域語感。
要動的是消歧句 —— 候選「我們正式研議」「我們排入議程」（6 字，+0）。
重疊動詞「研究研究」的推託義已高度構式化，可以辯護留在 LEXICAL，但請在 D5 的
ambiguity_axis 標成「言語行為」。

**卡在**：Q5（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-lex-04  (LEXICAL)　［連動 D2、D6；待答 Q6］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 那家店關門了 | 6 |
| 消歧 | 那家店歇業了 | 6 |

改動：關門 → 歇業（同長度替換，鎖定永久義）　　字數差：+0
消歧後鎖定：該店已永久歇業

**licensed_readings**
1. 該店今日已打烊　　適用：談論當下營業時間　　intent=INFORM
2. 該店已永久歇業　　適用：談論店家經營狀況　　intent=INFORM

**spurious_readings**
- 店員把門關上了
- 那家店被查封

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: []

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 今日打烊 vs 永久歇業是經典最小對立，消歧句鎖定永久義。 |
| gpt | `keep` | 兩讀都是中文常規用法，spurious 兩項都不是本句直接表達的內容。 |
| claude | `fix` | 「本日歇業」是常見招牌用語，消歧句鎖不住永久義；spurious 1「店員把門關上」與 licensed 1「今日打烊」語意幾乎重疊，評分時無法判定命中或誤報。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

三方兩票 keep，但 claude 的兩點是硬的，先答 Q6。
若「歇業」確實鎖不住，候選消歧句「那家店收掉了」（6 字，+0，口語）。
spurious 1 與 licensed 1 重疊 → 依 D2 換掉；spurious 2「被查封」是好的干擾項，留。
required_clarifications 是空集合卻有兩讀（時間範圍不在五欄內）→ D6。

**卡在**：Q6（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-lex-05  (LEXICAL)　［連動 D2、D5；待答 Q11］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 他很會做人 | 5 |
| 消歧 | 他人際圓融 | 5 |

改動：很會做人 → 人際圓融（鎖定褒義）　　字數差：+0
消歧後鎖定：他善於處世、人際圓融

**licensed_readings**
1. 他善於處世、人際圓融（褒義）　　適用：說話者對其持正面評價　　intent=PRAISE
2. 他八面玲瓏、只顧經營關係（貶義）　　適用：說話者對其持負面評價　　intent=CRITICIZE

**spurious_readings**
- 他很會生小孩
- 他很會製作人偶

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent']

**第一輪（你）**：`fix`（deferred）　—　不會有生小孩的說法 有點離譜

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 褒貶兩讀清晰，spurious 完全不相關。 |
| gpt | `keep` | 「很會做人」本身帶正負皆可的評價空間，消歧句能鎖到正面。 |
| claude | `fix` | 「他人際圓融」是考評用語，語域從口語漂到書面；spurious 2 荒謬；spurious 1 因為台灣有「做人成功」的說法反而有張力。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

你第一輪說「生小孩有點離譜」—— 這一點你和 claude 相反（claude 認為它有張力），
以你為準：兩條 spurious 依 D2 都刪。
消歧句語域問題三方只有 claude 提，候選「他待人周到」（5 字，+0，口語）。
歧義軸是評價極性 → D5 標 ambiguity_axis。

**卡在**：Q11（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-lex-06  (LEXICAL)　［連動 D2、D5］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 我沒有意見 | 5 |
| 消歧 | 我完全同意 | 5 |

改動：沒有意見 → 完全同意（等長替換）　　字數差：+0
消歧後鎖定：我同意此提案

**licensed_readings**
1. 我同意此提案　　適用：在表決或徵詢同意的場合　　intent=AGREE
2. 我不願表態　　適用：議題敏感或說話者處於不利位置　　intent=WITHHOLD

**spurious_readings**
- 我沒有任何想法
- 我沒有抱怨

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent', 'social_relation']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 同意 vs 不願表態是真實歧義，消歧句乾淨。 |
| gpt | `fix` | 「我沒有意見」不等於「我完全同意」，licensed 1 過度強化成 AGREE。 |
| claude | `fix` | 消歧句鎖過頭；兩個 spurious 其實都可得（「沒有任何想法」是字面義，「沒有抱怨」對應「我對他沒意見」的怨懟義），precision 分母是壞的；歧義軸屬 PRAGMATIC。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

gpt 與 claude 獨立指出同一件事（消歧句比 licensed 1 強），證據較硬，你第一輪判 keep。
建議：licensed 1 改為「不反對、無異議」；消歧句候選「我贊成此案」（5 字，+0）。
兩條 spurious 依 D2 重判 —— 若判定可得就移到 licensed，不要留在分母。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-lex-07  (LEXICAL)　［連動 D2；待答 Q2］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 他手上有東西 | 6 |
| 消歧 | 他手裡拿著書 | 6 |

改動：有東西 → 拿著書（等長替換，鎖定物理義）　　字數差：+0
消歧後鎖定：他手中拿著物品

**licensed_readings**
1. 他手中拿著物品　　適用：描述當下物理場景　　intent=INFORM
2. 他握有某人的把柄或籌碼　　適用：談論博弈、談判或衝突情境　　intent=WARN

**spurious_readings**
- 他手上長了東西（腫瘤）
- 他持有武器

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent']

**第一輪（你）**：`fix`（deferred）　—　不會有人替換成書 在中文也不會有把柄或武器啥的 就純粹是有東西占用到他的手了 例如我要求他做事情 就有人可以說他手上有東西 表達不方便做事或幫忙 這部分可能是英文翻譯所造成的問題吧

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 物理「有東西」vs 把柄／籌碼兩讀成立。 |
| gpt | `fix` | 限定成「某人的把柄或籌碼」太窄；「持有武器」是持有某物的下位，列 spurious 不成立。 |
| claude | `fix` | 消歧句不該引入原文沒有的「書」（ref 組明訂不引入新名，lex 組應同標準）；spurious 2 是 licensed 1 的下位讀法；質疑「有東西」撐不撐得起把柄義。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

這題四方（含你）指向同一結論：licensed 2「把柄／籌碼」是英譯直譯的產物，刪。
你的原話已經給出真正的第二讀 —— 「手邊有事情占著、不方便做事或幫忙」，見 Q2。
消歧句候選「他手上拿著東西」（7 字，+1，不引入新名）。
spurious 2「持有武器」是 licensed 1 的下位 → 依 D2 刪。

**卡在**：Q2（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-lex-08  (LEXICAL)　［連動 D2、D5］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 把那份文件處理一下 | 9 |
| 消歧 | 把那份文件辦理完成 | 9 |

改動：處理一下 → 辦理完成（等長替換）　　字數差：+0
消歧後鎖定：把文件辦理完成

**licensed_readings**
1. 把文件辦理完成　　適用：一般行政流程　　intent=INSTRUCT
2. 把文件銷毀　　適用：涉及需湮滅的內容　　intent=INSTRUCT
3. 整理文件　　適用：文件雜亂需歸檔時　　intent=指示

**spurious_readings**
- 把文件影印
- 把文件翻譯

**text_determinable**: false
**field_determinable**: agent=false / tense=true / register=false / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['social_relation']

**第一輪（你）**：`fix`（applied）　—　可以加上整理

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `fix` | reading 3 的 intent 寫成中文「指示」，應統一為 INSTRUCT；其餘可保留。 |
| gpt | `fix` | 「影印」「翻譯」在職場語境同樣可得，spurious 判得太嚴；「辦理完成」語域比「處理一下」正式，最小對立不乾淨。 |
| claude | `fix` | 同 enum 問題；「辦理」搭「文件」不自然；required_clarifications 只有 social_relation，區分不了辦理／銷毀／整理（真正的變因不在五欄內）；祈使句標 tense=true 可疑。 |

一致度：3 fix

**合議建議**：`fix`　（助理判斷，待你確認）

三方一致 fix，其中 enum 是純機械修正（M1，可立刻做）。
消歧句候選「把那份文件簽完送出」（9 字，+0）。
spurious「影印／翻譯」依 D2 重判：它們跟 licensed 用的是同一種語境挑選機制，
標準要一致。欄位問題併 D6。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-lex-09  (LEXICAL)　［連動 D2、D6；待答 Q3］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 他昨天走了 | 5 |
| 消歧 | 他昨天離開 | 5 |

改動：走 → 離開（等長替換）　　字數差：+0
消歧後鎖定：他昨天離開（此地／某處）

**licensed_readings**
1. 他昨天離開（此地／某處）　　適用：談論行程或去向　　intent=INFORM
2. 他昨天過世　　適用：談論健康或喪事，屬委婉語　　intent=INFORM

**spurious_readings**
- 他昨天走路去的
- 他昨天辭職

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: []

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 離開 vs 過世是經典委婉歧義，消歧句自然。 |
| gpt | `keep` | 典型的詞義／委婉義歧義，其餘兩項需要額外語境。 |
| claude | `fix` | 職場的「他走了」＝離職在台灣常用，列 spurious 會直接罰掉答對的模型；「他昨天離開」句末缺「了」偏不自然，且「離開」本身也能當委婉語。 |

一致度：2 keep／1 fix

**合議建議**：`uncertain`　（助理判斷，待你確認）

卡在 Q3 這個純母語問題。若「走了」可表離職 → spurious 2 移到 licensed；
若不可 → 維持，並在 codebook 記下判定理由（D2 的分級用得上）。
消歧句若要鎖「離開此地」，候選「他昨天出發」（5 字，+0）。
required_clarifications 空集合但兩讀 → D6。

**卡在**：Q3（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-01  (REFERENTIAL)　［連動 D1］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 小明告訴小華他考上了 | 10 |
| 消歧 | 小明告訴小華，小華考上了 | 12 |

改動：他 → 小華（代名詞換專名）　　字數差：+2
消歧後鎖定：「他」指小華

**licensed_readings**
1. 「他」指小明，小明報告自己的好消息　　適用：先前提及小明應考　　intent=NARRATE
2. 「他」指小華，小明通知小華錄取　　適用：先前提及小華應考　　intent=NARRATE

**spurious_readings**
- 「他」指第三個未提及的人

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=true / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['coreference']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 經典代詞歧義，消歧字數差 +2 在允許範圍內且只換專名。 |
| gpt | `keep` | 不列第三人是可接受的資料設計，消歧句確實把指涉鎖到小華。 |
| claude | `fix` | 第三人讀法的標籤與 ref-04/07/08 矛盾，precision 與 recall 會同時被標籤不一致污染。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

句子本身沒有人有意見，要動的只有 D1 政策（若選 A，刪掉第三人 spurious）。
另外這題字數差 +2，是全表長度風險最高的兩題之一（與 ref-04 並列）；
若想更保險，消歧句候選「小明通知小華錄取了」（9 字，−1）。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-02  (REFERENTIAL)　［連動 D2；待答 Q7］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 經理跟助理說他要出差 | 10 |
| 消歧 | 經理跟助理說經理要出差 | 11 |

改動：他 → 經理　　字數差：+1
消歧後鎖定：「他」指經理

**licensed_readings**
1. 「他」指經理，經理告知自己將出差　　適用：談論經理行程　　intent=INFORM
2. 「他」指助理，經理指派助理出差　　適用：談論工作分派　　intent=INSTRUCT

**spurious_readings**
- 經理與助理兩人都要出差

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=true / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['coreference']

**第一輪（你）**：`fix`（deferred）　—　不會有兩人都出差的情況 因為沒有複數

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 經理 vs 助理兩讀清晰，spurious「兩人都出差」不被允許。 |
| gpt | `fix` | reading 2「指派助理出差」比原句更強 —— 原句可以只是告知，是否構成指派無法由文本確定。 |
| claude | `fix` | 重複職稱比重複人名更不像中文，建議用「自己」；required_clarifications 用 coreference 但 field_determinable 沒這一欄。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

你第一輪的「不會有兩人都出差，因為沒有複數」在第一輪被判為方向不明而擱置 ——
現在解消了：那句話是在說「這條 spurious 之所以不可得，理由是缺複數標記」，
所以保留 spurious，並把理由寫進 D2 的 grammatical 分級。
reading 2 依 gpt 改為「經理告知助理將出差（是否為指派無法由文本判定）」，
intent 由 INSTRUCT 改 INFORM。消歧句改用「自己」與否看 Q7。

**卡在**：Q7（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-03  (REFERENTIAL)　［連動 D1、D4；待答 Q1］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 媽媽罵妹妹，因為她把杯子打破了 | 15 |
| 消歧 | 媽媽罵妹妹，因為妹妹把杯子打破了 | 16 |

改動：她 → 妹妹　　字數差：+1
消歧後鎖定：「她」指妹妹

**licensed_readings**
1. 「她」指妹妹，妹妹打破杯子而被罵　　適用：預設語境（因果最自然）　　intent=NARRATE
2. 「她」指媽媽，媽媽自己打破杯子而遷怒　　適用：描述遷怒行為　　intent=NARRATE

**spurious_readings**
- 「她」指第三人

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=true / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['coreference']

**第一輪（你）**：`fix`（deferred）　—　只有一個結果就是妹妹把杯子打破 畢竟沒理由自己打破還要罵人

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 妹妹（預設）vs 媽媽（遷怒）兩讀皆可能。 |
| gpt | `keep` | 兩種因果敘述都語法與語義成立。 |
| claude | `fix` | 兩句都自然、遷怒讀法可得，是 ref 組品質最好的幾題之一；問題只在第三人標籤一致性。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

三方全體認為兩讀成立，你第一輪說「沒理由自己打破還要罵人」＝ 只有一讀。
這是本輪最有價值的分歧：遷怒讀法語法上可得、語用上被排除，三個模型都只看到前者。
建議走 D4-B：把遷怒讀法從 licensed 移到 spurious（並在 D2 標成 contextual 級），
本題轉成 text_determinable=true 的單讀對照組。先答 Q1。

**卡在**：Q1（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-04  (REFERENTIAL)　［連動 D1、M1］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 王先生和李先生見面時，他帶了資料 | 16 |
| 消歧 | 王先生和李先生見面時，王先生帶了資料 | 18 |

改動：他 → 王先生　　字數差：+2
消歧後鎖定：「他」指王先生

**licensed_readings**
1. 「他」指王先生　　適用：王先生為敘述主體　　intent=NARRATE
2. 「他」指李先生　　適用：李先生為敘述主體　　intent=NARRATE
3. 「他」指第三者　　適用：在場另有他人　　intent=敘述

**spurious_readings**
- 兩人都帶了資料

**text_determinable**: false
**field_determinable**: agent=false / tense=true / register=true / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['coreference']

**第一輪（你）**：`fix`（applied）　—　不會有兩人都帶資料的情況 因為沒有複數 但是有可能是第三者帶的

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `fix` | reading 3 的 intent 寫成中文「敘述」，應統一為 NARRATE。 |
| gpt | `keep` | 主句本身無法唯一決定指涉，符合測試目的。 |
| claude | `fix` | 中文 enum 在 lex-08 與 ref-04 都出現在各自「第 3 個」licensed reading，很可能是後補讀法時漏轉；第三人讀法在此列 licensed，與 ref-01/03/09 矛盾。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

enum 是 M1（機械，立刻可做，且源頭在 apply_review.py 的 APPLY 表）。
第三人讀法是你第一輪親自加的 —— 這正是 D1 建議選 A（全面 license）的理由。
spurious「兩人都帶了資料」同 ref-02，保留並標成 grammatical 級。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-05  (REFERENTIAL)　［連動 D1］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 醫生看了病人一眼，他嘆了口氣 | 14 |
| 消歧 | 醫生看了病人一眼，醫生嘆了口氣 | 15 |

改動：他 → 醫生　　字數差：+1
消歧後鎖定：「他」指醫生

**licensed_readings**
1. 「他」指醫生，醫生對病情感到無奈　　適用：描述醫生反應　　intent=NARRATE
2. 「他」指病人，病人感到沮喪　　適用：描述病人反應　　intent=NARRATE

**spurious_readings**
- 旁邊的家屬嘆氣

**text_determinable**: false
**field_determinable**: agent=false / tense=true / register=true / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['coreference']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 醫生 vs 病人嘆氣兩讀成立，消歧自然。 |
| gpt | `keep` | 兩者都能自然承擔「嘆了口氣」，第三者家屬需要額外語境。 |
| claude | `fix` | 中文預設的消歧手段是零形主語而非重複專名 —— 「醫生看了病人一眼，嘆了口氣」更自然且短 1 字；spurious 的家屬同屬第三人讀法，標籤與 04/07/08 矛盾。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

零形主語的建議值得採用（13 字，−1，比重複「醫生」自然，且長度平衡更好），
但要先確認它是否真的唯一指醫生 —— 中文主語延續在這個句式相當穩，仍請你覆核。
第三人 spurious 依 D1。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-06  (REFERENTIAL)　［連動 D4；待答 Q1］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 老闆同意了小張的提案，這是他第一次成功 | 19 |
| 消歧 | 老闆同意了小張的提案，這是小張第一次成功 | 20 |

改動：他 → 小張（重複原文既有專名，不引入新名）　　字數差：+1
消歧後鎖定：「他」指小張

**licensed_readings**
1. 「他」指小張，敘述小張的成就　　適用：敘述提案人的成就　　intent=NARRATE
2. 「他」指老闆，老闆首度採納他人提案　　適用：敘述老闆的轉變　　intent=NARRATE

**spurious_readings**
- 「這」指老闆本人而非同意一事

**text_determinable**: false
**field_determinable**: agent=false / tense=true / register=true / social_relation=true / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['coreference']

**第一輪（你）**：`fix`（deferred）　—　看起來只能是小張成功 老闆是上位者 成不成功不是同意小張的提案就有的

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 「他」指小張 vs 老闆兩讀合理，spurious 針對「這」的另解正確排除。 |
| gpt | `keep` | 「這」通常指前述『同意提案』這件事，spurious 可以排除。 |
| claude | `fix` | 若「他」＝老闆，原文說的是「老闆第一次成功」，不等於現寫的「老闆首度採納他人提案」—— 採納≠成功，釋義超出原文；唯一的 spurious 針對「這」，與本題歧義軸（「他」）不同。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

你第一輪的理由（「成不成功不是同意小張的提案就有的」）與 claude 完全同一件事，
兩邊獨立得出：licensed 2 的釋義站不住。
若你維持單讀 → 走 D4-B 轉單讀對照組；若保留兩讀 → licensed 2 必須改寫成
「這是老闆第一次做成某事」，並補一個針對「他」的 spurious。

**卡在**：Q1（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-07  (REFERENTIAL)　［連動 D1、D6］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 我跟阿明去他家 | 7 |
| 消歧 | 我跟阿明去阿明家 | 8 |

改動：他 → 阿明（重複原文既有專名，不引入新名）　　字數差：+1
消歧後鎖定：「他家」指阿明家

**licensed_readings**
1. 「他家」指阿明家　　適用：預設語境　　intent=NARRATE
2. 「他家」指第三人的家　　適用：先前提及兩位男性　　intent=NARRATE

**spurious_readings**
- 「他家」指店家或機構

**text_determinable**: false
**field_determinable**: agent=true / tense=false / register=true / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['coreference', 'tense']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 阿明 vs 第三人皆可能，field_determinable 的 tense=false 誠實。 |
| gpt | `keep` | 默認讀法是阿明家，更大語境裡也可能回指第三位男性。 |
| claude | `fix` | 「我跟阿明去阿明家」不像人話；required_clarifications 含與讀法選擇無關的 tense，與其他題「只收消歧所需最小集合」的做法不一致。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

tense 的問題明確（依 D6 移除，或把 required_clarifications 的定義改成
「所有未定欄位」並全表統一 —— 二選一，不能兩套）。
消歧句確實不自然，但 claude 提的「我陪阿明回家」換掉了動詞與命題，違反最小對立，
不建議採用；這題需要你給一個新的消歧句（第一輪的 needs_text 仍未解）。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-08  (REFERENTIAL)　［連動 D1、D2］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 張三認為李四不該相信他 | 11 |
| 消歧 | 張三認為李四不該相信張三 | 12 |

改動：他 → 張三　　字數差：+1
消歧後鎖定：「他」指張三

**licensed_readings**
1. 「他」指張三，張三認為李四不該信任自己　　適用：張三自陳不可信或自謙　　intent=NARRATE
2. 「他」指某第三人　　適用：先前提及第三方　　intent=NARRATE

**spurious_readings**
- 「他」指李四自己

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['coreference']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 張三 vs 第三人兩讀成立，spurious「指李四自己」不被允許。 |
| gpt | `keep` | 中文通常會用「自己」表達此類照應，把李四列 spurious 合理。 |
| claude | `keep` | 全表唯一由語法保證不可得的 spurious（約束原則 B），建議當成 spurious 的撰寫標準；此處不能改用「自己」消歧，因為賓語位置的「自己」可長距離綁定。 |

一致度：3 keep

**合議建議**：`keep`　（助理判斷，待你確認）

四方（含你第一輪）唯一全體 keep 的一題。建議把它當 D2 的範本題寫進 codebook，
並把「ref-02 用『自己』可以、ref-08 不行」這組對比一併寫進去 ——
那是指代消歧手法的判定規則，CAD-60 會一直用到。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-ref-09  (REFERENTIAL)　［連動 D1、D6］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 小陳和小林吵架後，他就再也沒來過 | 16 |
| 消歧 | 小陳和小林吵架後，小陳就再也沒來過 | 17 |

改動：他 → 小陳（重複原文既有專名，不引入新名）　　字數差：+1
消歧後鎖定：「他」指小陳

**licensed_readings**
1. 「他」指小陳　　適用：前文已指明主體　　intent=NARRATE
2. 「他」指小林　　適用：前文以另一人為主體　　intent=NARRATE

**spurious_readings**
- 「他」指第三人
- 兩人都沒再來

**text_determinable**: false
**field_determinable**: agent=false / tense=true / register=true / social_relation=false / speaker_intent=true
**expected_route**: slow
**required_clarifications**: ['coreference']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 小陳 vs 小林兩讀清晰，spurious 正確。 |
| gpt | `keep` | 「兩人都沒再來」不是單一代詞句的合法指涉，可列 spurious。 |
| claude | `fix` | 第三人標籤一致性；social_relation=false 與其他題有出入 —— 「吵架」是相互言說事件，照 ref-03「罵」判 true 的標準，這題應為 true。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

句子與讀法沒有爭議，要動的是兩個一致性問題（D1 的第三人、D6 的 social_relation）。
spurious 2「兩人都沒來」同 ref-02/04，保留並標 grammatical 級。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-01  (PRAGMATIC)　［連動 D2、D3］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 你今天氣色不錯 | 7 |
| 消歧 | 你看起來很健康 | 7 |

改動：間接讚美 → 直接陳述健康（等長替換）　　字數差：+0
消歧後鎖定：真誠關心與讚美

**licensed_readings**
1. 真誠關心與讚美　　適用：雙方關係友好　　intent=PRAISE
2. 反諷，實則對方看來疲憊　　適用：熟識者間的玩笑　　intent=TEASE
3. 暗示先前狀況不佳　　適用：對方近日抱恙　　intent=IMPLY

**spurious_readings**
- 評論對方的化妝技術
- 詢問對方健康狀況

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['social_relation', 'speaker_intent']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 真誠讚美／反諷／暗示先前不佳三讀皆合理。 |
| gpt | `fix` | 在對方有不適傳聞時，本句也可作委婉的健康試探，「詢問對方健康狀況」不能列 spurious。 |
| claude | `fix` | 反諷幾乎能附著在任何讚美上，「你看起來很健康」照樣說得酸 —— 判準 2 對 PRAG 結構上不可能滿足；licensed 3 需要病史知識，也不在五欄內。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

兩件事分開處理：spurious 2 依 D2 重判（gpt 的理由成立，傾向刪）；
消歧句的「鎖不住」是 D3 的結構問題，不是本題的問題 —— D3 定案後這題句子可留。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-02  (PRAGMATIC)　［連動 D3］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 這報告我看過了 | 7 |
| 消歧 | 這報告沒有問題 | 7 |

改動：「我看過了」→ 直接給結論（等長替換）　　字數差：+0
消歧後鎖定：單純陳述已閱畢

**licensed_readings**
1. 單純陳述已閱畢　　適用：例行回報　　intent=INFORM
2. 暗示報告有問題，接下來要指正　　適用：上對下的審閱場合　　intent=IMPLY

**spurious_readings**
- 我看過類似的報告
- 我拒絕再看

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['social_relation', 'speaker_intent']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 單純告知已看 vs 暗示有問題兩讀真實，消歧乾淨。 |
| gpt | `keep` | 兩個 spurious 都比原句允許的 reading 更遠。 |
| claude | `fix` | 消歧句「這報告沒有問題」既不是 licensed 1 也不是 licensed 2，而是第三個命題；但 resolves_to 寫的是 licensed 1，消歧句與所鎖定的讀法對不上。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

這是機械可查的不一致（消歧句表達的命題 ≠ resolves_to），兩票 keep 但 claude 對。
候選消歧句「這報告我讀完了」（7 字，+0），與 resolves_to「單純陳述已閱畢」對齊。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-03  (PRAGMATIC)　［連動 D3］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 時間不早了 | 5 |
| 消歧 | 你們該走了 | 5 |

改動：「時間不早了」→ 直接逐客（等長替換）　　字數差：+0
消歧後鎖定：委婉的逐客令

**licensed_readings**
1. 單純陳述時間已晚　　適用：無社交壓力的場合　　intent=INFORM
2. 委婉的逐客令　　適用：說話者為主人且客人久留　　intent=SOFT_REFUSAL
3. 催促對方一同離開　　適用：雙方同為訪客　　intent=SUGGEST

**spurious_readings**
- 抱怨事情進度落後
- 提醒對方遲到

**text_determinable**: false
**field_determinable**: agent=false / tense=true / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['social_relation', 'speaker_intent']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 陳述時間晚／逐客／催促離開三讀成立。 |
| gpt | `keep` | 典型的語用歧義，三讀都成立。 |
| claude | `fix` | 「你們該走了」把中性語域換成直接甚至失禮的說法，違反判準 4。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

句子與三讀沒有爭議。claude 指的語域問題其實是 D3 —— 語用消歧必然改語域，
所以要改的是判準不是句子。D3 選 A 之後，本題可直接 keep。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-04  (PRAGMATIC)　［連動 D2、D3、M2］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 你的想法很特別 | 7 |
| 消歧 | 你的想法很好 | 6 |

改動：「很特別」→ 直接褒義（等長替換）　　字數差：-1
消歧後鎖定：真心讚賞其創意

**licensed_readings**
1. 真心讚賞其創意　　適用：說話者確實認同　　intent=PRAISE
2. 委婉否定，實則不認同　　適用：正式場合需保留顏面　　intent=SOFT_REFUSAL

**spurious_readings**
- 你的想法很奇怪且不可行
- 你的想法與眾人相同

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent', 'social_relation']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 讚賞 vs 委婉否定經典，消歧字數差 −1 可接受。 |
| gpt | `fix` | spurious 1「很奇怪且不可行」在負面語境下正是實際意圖，與 licensed 2 重疊。 |
| claude | `fix` | edit 欄寫「等長替換」但字數差 −1；「你的想法很好」在正式場合一樣能當委婉否定；spurious 1 接近 licensed 2 的言下之意，評分時會互相吃分。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

gpt 與 claude 獨立指出 spurious 1 與 licensed 2 重疊 —— 依 D2 刪或改寫。
edit 欄是 M2（機械）。消歧句鎖不住是 D3 的結構問題。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-05  (PRAGMATIC)　［連動 D2、D7］

> 🔴 **標註獨立性缺口**：助理曾看過 Gemini 對本句提議的意圖，且已轉述給研究者。雙方皆已看過

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 我盡量 | 3 |
| 消歧 | 我會做 | 3 |

改動：「盡量」→ 直接承諾（等長替換）　　字數差：+0
消歧後鎖定：真誠承諾會努力達成

**licensed_readings**
1. 真誠承諾會努力達成　　適用：說話者有意願且有能力　　intent=COMMIT
2. 委婉推託，實則不打算做　　適用：難以直接拒絕的場合　　intent=SOFT_REFUSAL

**spurious_readings**
- 我已經盡力了
- 我拒絕

**text_determinable**: false
**field_determinable**: agent=true / tense=false / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent', 'social_relation']

**第一輪（你）**：`fix`（deferred）　—　不會有我拒絕的情況 最多只有假裝有做 但是最後啥成果都沒有

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 承諾 vs 推託真實歧義，消歧「我會做」乾淨。 |
| gpt | `fix` | 「我盡量」是降低承諾強度的 hedge，直接標成「實則不打算做」過強。 |
| claude | `fix` | 最小對本身是好的；「我會做」偏生硬，建議「我一定做」；本題雙方皆已看過模型意見，建議排除在獨立性統計外或據實揭露。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

你第一輪的原話正好落在 gpt 的批評與現行標註之間 ——
「不會有我拒絕的情況，最多只有假裝有做，但是最後啥成果都沒有」：
licensed 2 建議改寫成「降低承諾強度的推託，不保證做到」（保留 SOFT_REFUSAL），
spurious「我拒絕」你已確認不可得 → 保留，是好的干擾項。
消歧句候選「我一定做」（3 字，+0）。污染見 D7。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-06  (PRAGMATIC)　［連動 D4、D8；待答 Q1］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 這樣也可以啦 | 6 |
| 消歧 | 這樣我很滿意 | 6 |

改動：「也可以啦」→ 直接肯定（等長替換）　　字數差：+0
消歧後鎖定：認可此做法

**licensed_readings**
1. 認可此做法　　適用：說話者確實接受　　intent=AGREE
2. 勉強接受，實則不滿意　　適用：語氣詞「啦」帶保留意味　　intent=RELUCTANT_AGREE

**spurious_readings**
- 這樣是最好的方式
- 我完全反對

**text_determinable**: false
**field_determinable**: agent=false / tense=true / register=true / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent']

**第一輪（你）**：`fix`（deferred）　—　這樣通常只有很勉強的選項 因為"也...啦" 例如也不是不行啦 也行啦 也是啦

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 認可 vs 勉強接受兩讀清楚。 |
| gpt | `keep` | 兩者都是自然的語用 reading。 |
| claude | `fix` | 消歧句「我很滿意」比 resolves_to 的「認可此做法」強，與 lex-06 同一類問題。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

你第一輪的理由很具體（「也…啦」這個構式本身就帶勉強），三方都沒看到這一層。
若確認單讀 → D4-B 轉對照組，但注意這句是「無歧義但有語用負載」，
直接標 expected_route=fast 會讓系統翻掉它的勉強語氣（見 D8 的維度混淆）。

**卡在**：Q1（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-07  (PRAGMATIC)　［連動 D3、D4、M2；待答 Q10］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 你要不要再考慮一下 | 9 |
| 消歧 | 我不贊成這決定 | 7 |

改動：反問 → 直接反對（等長替換）　　字數差：-2
消歧後鎖定：委婉表達反對

**licensed_readings**
1. 中性建議對方多思考　　適用：說話者無立場偏好　　intent=SUGGEST
2. 委婉表達反對　　適用：說話者不贊同該決定　　intent=SOFT_REFUSAL

**spurious_readings**
- 你必須改變決定
- 詢問對方是否已考慮完

**text_determinable**: false
**field_determinable**: agent=true / tense=false / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent', 'social_relation']

**第一輪（你）**：`fix`（deferred）　—　這跟也許吧差不多就是委婉地不想要但是也不是不行 就是感覺很勉強但能接受這個決定 能換掉是最好

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 中性建議 vs 委婉反對兩讀成立，字數差 −2 剛好在邊界。 |
| gpt | `keep` | 兩個 spurious 都把語氣推得過強或改變了言語行為。 |
| claude | `fix` | edit 欄寫「等長替換」但字數差 −2；消歧句換了主語（你→我）與句式（疑問→陳述），最小對立在這裡已無實質意義。 |

一致度：2 keep／1 fix

**合議建議**：`drop`　（助理判斷，待你確認）

你第一輪已經說「能換掉是最好」，而且理由與 claude 指出的問題一致
（這句更接近單一的委婉推託，不是兩個對等讀法）。
drop 會讓 PRAG 剩 11 句，需補一句才維持 9/9/12 —— 見 Q10。
若決定保留，至少要依 D3 重寫消歧句（保留主語與句式）。

**卡在**：Q10（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-08  (PRAGMATIC)　［連動 D2、D3］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 我沒說你錯 | 5 |
| 消歧 | 你的做法沒錯 | 6 |

改動：雙重否定 → 直接肯定（等長替換）　　字數差：+1
消歧後鎖定：澄清自己並未指責對方

**licensed_readings**
1. 澄清自己並未指責對方　　適用：對方誤會了說話者立場　　intent=CLARIFY
2. 暗示對方確實有錯，只是未明說　　適用：重音落在「說」上　　intent=IMPLY

**spurious_readings**
- 我認為你完全正確
- 我要指責你

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=true / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 澄清未指責 vs 暗示有錯（重音在「說」）兩讀真實。 |
| gpt | `keep` | 形式與語用意圖之間的歧義，兩讀都成立。 |
| claude | `fix` | 全表最明確的自我矛盾 —— 消歧句「你的做法沒錯」正是本題自己列的 spurious 1「我認為你完全正確」；且 licensed 1 是後設層次的澄清（我沒說過那句話），與「你是對的」是不同命題。另 licensed 2 靠重音，純文字取不到。 |

一致度：2 keep／1 fix

**合議建議**：`fix`　（助理判斷，待你確認）

消歧句 = 自己的 spurious，這是硬矛盾（兩票 keep 沒看到）。
候選消歧句「我沒有指責你」（6 字，+1），與 resolves_to 對齊。
licensed 2 的 licensed_when 從「重音落在說上」改成語境條件
（例如「對方正在辯解、先前已有爭議」）—— 重音是文本取不到的線索，
但這個言下之意不必靠重音也成立。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-09  (PRAGMATIC)　［連動 D2、D3］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 大家都很努力 | 6 |
| 消歧 | 每個人都達標 | 6 |

改動：全稱讚美 → 客觀陳述（等長替換）　　字數差：+0
消歧後鎖定：真心肯定全體表現

**licensed_readings**
1. 真心肯定全體表現　　適用：總結性場合　　intent=PRAISE
2. 暗示某人未盡力（以全體之名點名）　　適用：先前有人表現不佳　　intent=IMPLY

**spurious_readings**
- 只有部分人努力
- 抱怨工作量過大

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent', 'social_relation']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 真心肯定全體 vs 暗示有人未盡力兩讀合理。 |
| gpt | `fix` | 若是反諷，「其實只有部分人努力」正是言下之意，與 licensed 2 直接重疊，不能列 spurious。 |
| claude | `fix` | 消歧句「每個人都達標」把述謂從努力（過程）換成達標（結果），不只是消歧，還換了命題。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

兩件獨立的問題，兩票分別抓到一個，都成立：
spurious 1 依 D2 刪（與 licensed 2 重疊）；消歧句換了命題 → 候選「大家表現都很好」（7 字，+1）。
但要注意這個候選一樣可以反諷 —— 這題可能跟 prg-10 一樣屬於文本層難以消歧，D3 定案後再看。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-10  (PRAGMATIC)　［連動 D3；待答 Q9］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 這件衣服很適合你 | 8 |
| 消歧 | 我覺得這件好看 | 7 |

改動：「適合你」→ 標明為個人意見（等長替換）　　字數差：-1
消歧後鎖定：真心讚美

**licensed_readings**
1. 真心讚美　　適用：朋友間的意見徵詢　　intent=PRAISE
2. 店員的推銷客套話　　適用：商業銷售情境　　intent=PERSUADE

**spurious_readings**
- 這件衣服尺寸正確
- 你應該買下它

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['social_relation', 'speaker_intent']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 真心讚美 vs 店員客套兩讀成立，字數差 −1 可接受。 |
| gpt | `keep` | 合理的 utterance-intent ambiguity，兩個 spurious 都不是句子必然推出的內容。 |
| claude | `drop` | 店員一樣會說「我覺得這件好看」，消歧句完全沒排除 licensed 2；兩讀差在說話者身分，句子裡沒有任何線索。若保留，就明確標成不可消歧的極端案例。 |

一致度：2 keep／1 drop

**合議建議**：`fix`　（助理判斷，待你確認）

不建議 drop。claude 的診斷對（沒有任何文本手段能鎖住說話者身分），
但這正好是有價值的案例：required_clarifications 已經正確標了 social_relation，
它可以測「系統會不會硬猜，還是會發出澄清請求」。
建議加一個欄位標明「文本層不可消歧」，minimal_pair 保留但註明它只鎖命題內容、
不鎖說話意圖（AUC 的負例才不會少一句）。先答 Q9。

**卡在**：Q9（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-11  (PRAGMATIC)　［連動 D2、D3、M2］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 你先忙 | 3 |
| 消歧 | 我先走了 | 4 |

改動：「你先忙」→ 直接告辭（等長替換）　　字數差：+1
消歧後鎖定：體貼地讓對方繼續手邊工作

**licensed_readings**
1. 體貼地讓對方繼續手邊工作　　適用：對方明顯忙碌　　intent=CONSIDERATE
2. 結束對話的客套語　　適用：說話者想結束交談　　intent=END_CONVERSATION

**spurious_readings**
- 命令對方去工作
- 我比你晚開始工作

**text_determinable**: false
**field_determinable**: agent=false / tense=false / register=true / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent', 'social_relation']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 體貼讓對方忙 vs 結束對話客套兩讀真實。 |
| gpt | `fix` | 在上下級或同事情境中，「你先忙」也可帶明確的『你先去處理工作』指令色彩，不宜列 spurious。 |
| claude | `fix` | resolves_to 寫的是 licensed 1（體貼），但「我先走了」鎖的是 licensed 2（結束對話），而且主語從「你」換成「我」、命題整個換掉。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

兩票分別抓到 spurious 與 resolves_to 兩個獨立問題。
最省事的修法是把 resolves_to 改成 licensed 2（不動句子）；
若要鎖 licensed 1，候選「你忙你的沒關係」，但它同樣能當告辭套語，不乾淨。
spurious 1「命令對方去工作」依 D2 重判（gpt 的理由成立，傾向移到 licensed）。

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## dev-prg-12  (PRAGMATIC)　［連動 D2、M2；待答 Q8］

| | 句子 | 字數 |
|---|---|---|
| 歧義 | 我知道了 | 4 |
| 消歧 | 我完全理解 | 5 |

改動：「知道了」→ 直接表達理解（等長替換）　　字數差：+1
消歧後鎖定：理解並接受

**licensed_readings**
1. 理解並接受　　適用：中性的資訊接收　　intent=ACKNOWLEDGE
2. 帶不悅的敷衍，不想再談　　適用：對方反覆叮囑或說教　　intent=DISMISS

**spurious_readings**
- 我早就知道了
- 我同意你的看法

**text_determinable**: false
**field_determinable**: agent=true / tense=true / register=false / social_relation=false / speaker_intent=false
**expected_route**: slow
**required_clarifications**: ['speaker_intent', 'social_relation']

**第一輪（你）**：`keep`（keep）

**第二輪三方複核**

| 複核者 | verdict | 要點 |
| --- | --- | --- |
| grok | `keep` | 理解接受 vs 不悅敷衍兩讀清楚。 |
| gpt | `fix` | 「我早就知道了」不是 spurious 而是可能的語境化解讀；licensed 1 把「理解並接受」綁太緊，知道不等於接受。 |
| claude | `fix` | 「我完全理解」強度超過 licensed 1；兩個 spurious 都乾淨，尤其「我同意你的看法」抓到知悉 vs 接受的分野；edit 欄誤標為等長（實際 +1）。 |

一致度：2 fix／1 keep

**合議建議**：`fix`　（助理判斷，待你確認）

gpt 與 claude 在 licensed 1 上一致（「接受」是多出來的），建議改成「知悉、收到」。
消歧句候選「我明白了」（4 字，+0）。
兩人對 spurious 1 的判斷相反（gpt 說可得、claude 說乾淨）—— 見 Q8。
edit 欄是 M2。

**卡在**：Q8（見 §1）

---
**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->
**note**:

===========================================================

## §5 總表

| id | 型 | 字數差 | 第一輪(你) | grok | gpt | claude | 合議 | 連動 | 待答 |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| dev-lex-01 🔴 | LEXI | +0 | keep | keep | keep | fix | **fix** | D2、D7 | Q4、Q11 |
| dev-lex-02 | LEXI | +0 | fix | keep | keep | fix | **fix** | D2、D6 | Q11 |
| dev-lex-03 | LEXI | +0 | keep | keep | fix | fix | **fix** | D5 | Q5 |
| dev-lex-04 | LEXI | +0 | keep | keep | keep | fix | **fix** | D2、D6 | Q6 |
| dev-lex-05 | LEXI | +0 | fix | keep | keep | fix | **fix** | D2、D5 | Q11 |
| dev-lex-06 | LEXI | +0 | keep | keep | fix | fix | **fix** | D2、D5 | — |
| dev-lex-07 | LEXI | +0 | fix | keep | fix | fix | **fix** | D2 | Q2 |
| dev-lex-08 | LEXI | +0 | fix | fix | fix | fix | **fix** | D2、D5 | — |
| dev-lex-09 | LEXI | +0 | keep | keep | keep | fix | **uncertain** | D2、D6 | Q3 |
| dev-ref-01 | REFE | +2 | keep | keep | keep | fix | **fix** | D1 | — |
| dev-ref-02 | REFE | +1 | fix | keep | fix | fix | **fix** | D2 | Q7 |
| dev-ref-03 | REFE | +1 | fix | keep | keep | fix | **fix** | D1、D4 | Q1 |
| dev-ref-04 | REFE | +2 | fix | fix | keep | fix | **fix** | D1、M1 | — |
| dev-ref-05 | REFE | +1 | keep | keep | keep | fix | **fix** | D1 | — |
| dev-ref-06 | REFE | +1 | fix | keep | keep | fix | **fix** | D4 | Q1 |
| dev-ref-07 | REFE | +1 | keep | keep | keep | fix | **fix** | D1、D6 | — |
| dev-ref-08 | REFE | +1 | keep | keep | keep | keep | **keep** | D1、D2 | — |
| dev-ref-09 | REFE | +1 | keep | keep | keep | fix | **fix** | D1、D6 | — |
| dev-prg-01 | PRAG | +0 | keep | keep | fix | fix | **fix** | D2、D3 | — |
| dev-prg-02 | PRAG | +0 | keep | keep | keep | fix | **fix** | D3 | — |
| dev-prg-03 | PRAG | +0 | keep | keep | keep | fix | **fix** | D3 | — |
| dev-prg-04 | PRAG | -1 | keep | keep | fix | fix | **fix** | D2、D3、M2 | — |
| dev-prg-05 🔴 | PRAG | +0 | fix | keep | fix | fix | **fix** | D2、D7 | — |
| dev-prg-06 | PRAG | +0 | fix | keep | keep | fix | **fix** | D4、D8 | Q1 |
| dev-prg-07 | PRAG | -2 | fix | keep | keep | fix | **drop** | D3、D4、M2 | Q10 |
| dev-prg-08 | PRAG | +1 | keep | keep | keep | fix | **fix** | D2、D3 | — |
| dev-prg-09 | PRAG | +0 | keep | keep | fix | fix | **fix** | D2、D3 | — |
| dev-prg-10 | PRAG | -1 | keep | keep | keep | drop | **fix** | D3 | Q9 |
| dev-prg-11 | PRAG | +1 | keep | keep | fix | fix | **fix** | D2、D3、M2 | — |
| dev-prg-12 | PRAG | +1 | keep | keep | fix | fix | **fix** | D2、M2 | Q8 |

- 四方（你 + 三個模型）全體 keep：**1 題**
- 合議分布：27 fix／1 uncertain／1 keep／1 drop
- 需要母語裁決才動得了的題目：**14 題**
- grok：28 keep／2 fix
- gpt：19 keep／11 fix
- claude：28 fix／1 keep／1 drop

**不要被「27 題 fix」嚇到。** 那個數字裡真正壞掉的句子沒有那麼多，拆開來是：

- **純準則連動、句子與讀法都不必動**（D 一裁定就自動結案）：`ref-01`、`ref-04`（enum 除外）、
  `ref-09`、`prg-03` —— 4 題。
- **只要刪／改一條 spurious**：`lex-01`、`lex-02`、`lex-05`、`prg-01`、`prg-04`、`prg-09`、`prg-11` ——
  7 題，全部由 D2 一條準則決定，不必逐句重想。
- **消歧句要換**：`lex-03`、`lex-04`、`lex-05`、`lex-06`、`lex-07`、`lex-08`、`prg-02`、`prg-08`、
  `prg-12` —— 9 題（多數已附長度差 ≤2 的候選，等你判自然度）。
- **licensed reading 的釋義要改**：`lex-06`、`lex-07`、`ref-02`、`ref-06`、`prg-05`、`prg-12` —— 6 題。
- **整題結構要變**：`ref-03`、`ref-06`、`prg-06`（轉單讀對照組）、`prg-07`（drop）、
  `prg-10`（改列不可消歧案例）—— 5 題。
- **完全不必動**：`ref-08` —— 1 題，四方全體 keep，建議當 codebook 的範本題。

另外值得記一筆：三個模型的 keep 率（見上一行統計）是 28／19／1，差異大到不能當「投票」用 ——
少數意見在 `prg-08`（消歧句等於自己的 spurious）
這種硬矛盾上是對的，多數意見在 `ref-03`／`ref-06`／`prg-06` 上是錯的。
這張表只能當清單用，不能當表決用。

## §6 凍結前檢查清單

- [ ] 回答 Q1–Q11（只有你能答；其中 Q1 連動三題的去留）
- [ ] 裁定 D1–D8，寫進 codebook（D6 的一頁 codebook 是凍結的前提）
- [ ] 套用 M1–M4（不需等 Q/D，可立刻做）
- [ ] 照裁定結果逐句填 verdict（格式用 keep / fix / drop / uncertain 前綴）
- [ ] 重跑 apply_review（或第二輪版本）→ 更新 sentences.yaml
- [ ] 跑一次 schema 檢查：enum、required_clarifications 取值域、edit 欄字數差描述
- [ ] 跑一次雜訊基準面板（句長、標點數、相異字元數、字元重複率、PPL）
- [ ] meta.reviewed = true、meta.reviewer 填名、記錄新的 SHA-256 → 凍結 v1
- [ ] 在論文資料集章節揭露 D7（30 句全部被三個模型看過並提議過改法）
- [ ] v1 凍結後刪除 data/dev30/_quarantine/ 並重跑讀法聯集
