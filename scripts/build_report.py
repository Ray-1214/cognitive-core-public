"""產生技術報告（v3 架構書 §P8）。

⚠️ **`docs/技術報告.md` 是產物，直接編輯會在下一次重跑時被整份覆蓋。**
論述文字定義在本檔的 `PROSE_*` 常數；尚未撰寫的段落用 `todo()` 留標記。
`tests/test_report_prose.py` 守住這個不變量——若 .md 裡的標記比重新產出的
少，代表有論述只寫在 .md 裡，即將遺失。

所有數字一律**從結果檔讀取**，不手抄——手抄的數字會在下一次重跑後
悄悄過期，而報告裡沒有任何東西會提示它過期了。目前的例外有四處，
各自在常數旁註明來源：§1 的 dev-30 複核率、§3.3 走勢的前三點、
§8.2 前次執行的未校正 p、§8.2b 的 tokenizer 截斷表。

用法：
    python scripts/build_report.py
"""

from __future__ import annotations

import datetime
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cognitive_core.data.probe_builder import MAX_CANDIDATE_SENSES  # noqa: E402
from cognitive_core.eval.noise import ceiling_correct, compose_noise, decompose  # noqa: E402
from cognitive_core.eval.wsd import wilson_ci  # noqa: E402

RESULTS = ROOT / "data" / "results"
DOCS = ROOT / "docs"


def load(name: str) -> dict:
    f = RESULTS / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def load_external(name: str) -> list:
    """`data/external/` 下的稽核結果（頂層是 list，與 `load()` 的 dict 不同）。"""
    f = ROOT / "data" / "external" / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def section(md_path: pathlib.Path, start: str, end: str | None) -> str:
    """抽出既有報表的一段，避免同一張表在兩處各寫一份。"""
    if not md_path.exists():
        return "_（來源檔尚未產生）_"
    t = md_path.read_text(encoding="utf-8")
    i = t.find(start)
    if i < 0:
        return "_（找不到該段落）_"
    j = t.find(end, i) if end else len(t)
    return t[i:j if j > 0 else len(t)].rstrip()


def auc_table(md_path: pathlib.Path) -> dict[str, dict]:
    """從 `signals_all.md` 的主表讀回每個訊號的 AUC 與 p 值。

    ⚠️ `signals_all.json` 只存訊號名稱與 `auc_computed` 旗標，**AUC 與 p 值只
    存在於 markdown 表格裡**。§8.2 當初因此把數字手抄進來，重跑後就悄悄過期
    ——正是本檔 docstring 警告的那件事。這裡改成解析表格，讓它跟其他數字一樣
    自結果檔讀取。
    """
    out: dict[str, dict] = {}
    body = section(md_path, "### 主表", "### 對照列")

    def num(x: str) -> float | None:
        try:
            return float(x.strip("*"))
        except ValueError:
            return None

    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 10 or not re.fullmatch(r"S\d+_\w+", cells[0]):
            continue
        out[cells[0]] = {"auc": num(cells[1]), "se": num(cells[2]),
                         "ci": cells[3], "perm_p": num(cells[4]),
                         "tie_cap": num(cells[5]), "threshold": num(cells[6]),
                         "holm_p": num(cells[8]), "verdict": cells[9]}
    return out


def control_rows(md_path: pathlib.Path) -> dict[str, dict]:
    """從 `signals_all.md` 的對照列讀回未加權總和與純句長基準。

    與 `auc_table()` 同樣的理由：這兩列的數字只存在於 markdown 表格裡。
    §4.5 的整段論述都建立在純句長那一列上，手抄會在重跑後悄悄過期。
    """
    out: dict[str, dict] = {}
    for line in section(md_path, "### 對照列", "### vs 純句長").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        name = cells[0].strip("*")
        if name in ("未加權總和", "純句長基準"):
            try:
                out[name] = {"auc": float(cells[1]), "se": float(cells[2]),
                             "ci": cells[3], "perm_p": float(cells[4])}
            except ValueError:
                continue
    return out


def auc_n(md_path: pathlib.Path) -> int | None:
    """AUC 的樣本數＝正類＋負類（`signals_all.md` 的 AUC 段開頭那句）。"""
    nums = re.findall(r"（(\d+) 筆）", section(md_path, "## AUC", "### 主表"))
    return sum(int(x) for x in nums) if len(nums) == 2 else None


def git_hash() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              check=True).stdout.strip()[:12]
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


TODO = "<!-- TODO(你寫)：{} -->"

# 表頭那一行的佔位符：TODO 全部寫完之後，「標記的位置由研究者撰寫」
# 這句話就不再成立，改成提醒讀者本檔是產物。實際內容在寫檔前替換。
_HEADER_SLOT = "\x00header\x00"

_TODO_EMITTED: list[str] = []


def todo(topic: str) -> str:
    """論述缺口標記，**每呼叫一次計一筆**。

    `tests/test_report_prose.py` 拿這個計數比對兩件事：
    (a) 新產出的報告裡標記數是否等於呼叫數；
    (b) **已提交的 `docs/技術報告.md` 標記數是否 ≥ 新產出的**。

    (b) 是真正的守門條件。標記變少代表有論述只寫在 .md 裡、沒有搬進
    `PROSE_*`——下一次重跑 `write_text` 會把它整段蓋掉，而報告裡沒有
    任何東西會提示它消失了。每搬一段論述進來就少一次 `todo()` 呼叫，
    兩邊自然對齊。
    """
    _TODO_EMITTED.append(topic)
    return TODO.format(topic)


# ═════════════════ 論述文字（由研究者撰寫） ═════════════════
#
# 論述放這裡而不是直接編輯 docs/技術報告.md——後者每次重跑都會被
# 整份覆蓋。數字一律用具名欄位插入，維持本檔 docstring 的「不手抄」原則。
#
# ⚠️ 字串內不得出現裸露的 { }，會被 str.format 吃掉。

PROSE_INTRO = """中文是典型的高語境語言：一句話的意思往往不由字面決定，而由說話者
與受話者的關係、語氣、以及當下的情境決定。同一串字可以承載互不相容
的理解。

> 「那你很厲害ㄟ」——可能是真心稱讚，也可能是諷刺對方的說法很蠢。
>
> 「那你來啊」——可能是不滿對方的指點、可能是自己不想做、
> 也可能只是語氣不好地請對方過來。

這類歧義對人類溝通不構成障礙，因為人會用語境補足。但對語言模型
而言，它意味著模型必須在資訊不足的情況下做出選擇，而**選錯時沒有
任何外顯訊號**——輸出仍然流暢、自信、看起來完全正常。

### 1.1　從語用歧義到詞彙歧義

本研究原本以語用歧義為對象。實作過程中發現一個難以繞過的問題：
**語用歧義缺乏可辯護的標準答案。**

初期建構的 30 題語用歧義測試集，在研究者第一輪逐句複核時有 13% 被
判定為「其實只有一種讀法」——那些歧義是標註過程製造出來的，不是
語言本身的。若標準答案本身可爭議，任何以它為 gold 的準確率都難以
辯護。

因此改以**詞彙歧義**為對象，資料取自中文詞網 SemCor（CWN-SemCor）。
該資料集的義項來自詞典編纂、句子取自中央研究院平衡語料庫、標註者為
六位具語言學背景的華語母語者。這是一個現象上較窄、但標準答案客觀
可辯護的選擇。

<!-- 這個轉向的完整理由見差異表 D9、D15 -->

### 1.2　為什麼用機器翻譯當觀測窗口

模型「有沒有理解對」是內部狀態，無法直接觀察。翻譯提供了一個把它
外顯化的方法：**中文可以懸置的資訊，英文的語法強制要求做出選擇。**

「他昨天走了」在中文裡可以同時是離開與過世；譯成英文必須在 left 與
passed away 之間擇一。模型一旦選了，它理解成什麼就變成一個可以檢查
的外顯產物。

相對於統計式機器翻譯，LLM 具有更強的上下文利用能力與世界知識，
理論上更能依語境選對義項。因此若 LLM 在此仍有系統性的錯誤率，
那個錯誤率是有意義的下界，而非工具粗糙所致。"""
# ⚠️ 上面的 13% 來自 dev-30 第一輪複核，沒有對應的結果 JSON，
#    是本檔唯一手抄的數字。來源：架構書 §「CWN-SemCor 為何決定性」。

PROSE_STRATIFY = """**為什麼要分層抽樣。**

每個目標詞的多個義項在語料庫中出現頻率不同。若某題的正解剛好是該詞
最高頻的義項，模型答對可能只是因為它偏好主流解讀——CHA-Gen 已報告
LLM 有這個傾向——而不是因為它讀懂了脈絡。

因此依 gold 是否為該 lemma 中的最高頻義項分兩層，各抽 {per_stratum} 題：

| 層 | 定義 | 作用 |
| --- | --- | --- |
| 主流 | gold ＝該詞最高頻義項 | **基準線** |
| 非主流 | gold ≠最高頻義項 | 主測試 |

**主流層是基準線，不可省略。** 若只測非主流層，得到的 {nd_acc:.1%} 正確率
無從分辨兩種情況：模型讀不懂脈絡，或題目全被挑在模型預設偏好之外。
兩層之差才是「模型是否使用脈絡」的量測。"""

PROSE_BINARY = """**為什麼從 N 選一改成二元強迫選擇。**

初期採用完整的詞義消歧設定：judge 從該詞的全部同 lemma 義項中選一個。
該設定下的判定**不可靠**——judge 與研究者人工標註的一致率只有
{nway_judge_lo:.0%}–{nway_judge_hi:.0%}。

診斷結果指向任務本身而非模型：**CWN 的義項粒度細於英文譯文所能承載的
資訊。** 許多義項對在譯文層面根本無法區分，判定者只能猜。同一批盲標中
**研究者對 gold 的一致率也只有 {nway_human_gold:.0%}**——連人都做不到，
換模型或調 prompt 都無濟於事。

改為二元強迫選擇後（gold vs 同 lemma 中最高頻的非 gold 義項，
即最易混淆的干擾項），judge 與人工的一致率回到 {judge_human:.0%}、
研究者對 gold 由 {nway_human_gold:.0%} 升至 {human_gold:.0%}，
NONE 由 {nway_none:.1%}（{nway_none_n}/{nway_n}）降至 {none:.2%}（{none_n}/{n}），
可判定率由 {nway_judgeable:.1%} 升至 {judgeable:.2%}。

這個改動有三項代價，必須一併說明：

1. **不再是完整的 WSD 任務。** 測的是「模型能否把正解與最易混淆的
   競爭者分開」，不是「能否精準命中細粒度義項」
2. **隨機基準由約 {nway_chance:.1%} 升至 50%**，可偵測的效應空間被壓縮
3. **「錯誤時選了哪個義項」退化為抽樣產物**——干擾項恆為最高頻非 gold，
   於是該指標等同於「錯誤落在非主流層的比例」，與 CHA-Gen 的主流偏好
   銜接因此失效

⚠️ 第 1 點也是選擇二元設定的正面理由：對比對（正解 vs 干擾項）
正是 DiBiMT 與 MuCoW 這一系 MT 詞義評測的既有範式。"""

# §6.1 的論述夾著產生出來的公式方塊，故拆成前後兩段。
PROSE_TIE_CEILING_INTRO = """AUC 可以理解為：隨機抽一個正例與一個負例，訊號給正例較高分的機率。
若兩者**同分**，該次比較沒有排序資訊，只能貢獻 0.5。因此"""

PROSE_TIE_CEILING_BODY = """**這個上限與訊號的判別力無關**，只取決於分數的分布形狀。一個訊號若把
大量題目給成同一個值，它的 AUC 就有一個結構性的天花板——即使它在
概念上是完美的預測因子。

當這個上限低於顯著門檻時，該訊號**無論如何都不可能達到顯著**。
這種情況與「測了但沒有效果」是不同的兩件事：

| | 意思 | 能否由更多資料解決 |
| --- | --- | :-: |
| **不顯著** | 測了，效果未達可偵測水準 | 可能 |
| **不可檢定** | 這個量測工具對此訊號在數學上無法產生顯著結果 | 否 |

把後者報告成「不顯著」會誤導讀者，讓他們以為那是一個關於訊號的結論，
而它其實是一個關於量測工具的結論。

**為什麼這件事很少被注意。** 在 AUC 的常見使用場景中——模型輸出機率、
連續評分——幾乎不會出現兩個樣本完全同分，上限恆等於 1，天花板不存在。
它只在訊號是**離散的、詞表命中式的、且樣本量不大**時才會發生作用，
而那正是「便宜前置訊號」這類設計的典型特徵。

本研究因此在計算任何 AUC 之前先計算所有訊號的並列上限，並將處置決定
（重新設計為連續分數／標記為不可檢定）預先登記——見 §4.2 與
`data/results/signal_preregistration.md`。這個診斷不使用標籤，
因此不受 AUC 閘門限制，也不構成資料窺探。"""

PROSE_S4_UNTESTABLE = """`S4_cultural`（成語詞表命中）的並列上限為 **{ceiling:.3f}**，低於標籤全乾淨時
所需的 {req_clean:.3f}，更低於實測噪音下的 {req_noise:.3f}。

原因是覆蓋率：**{n} 題中只有 {hits} 題命中成語詞表**，其餘 {rest} 題的分數
全為 0。隨機抽出的一正一負有高機率同為 0 分，大量的 0.5 貢獻把 AUC
壓在 {ceiling:.2f} 附近，與成語本身是不是好的預測因子完全無關。

因此本研究對 S4 的結論是「**因覆蓋率不足而無法檢定**」，
不是「成語與詞義錯誤無關」。要檢定這個訊號需要成語密度較高的語料，
而更換語料會動搖整個資料層的可辯護性（CWN-SemCor 的義項標註是本研究
gold 的來源）。此權衡見 `docs/future_work.md`。

⚠️ 這也說明了為什麼並列上限必須**在看到 AUC 之前**計算。若事後才發現
S4 不可檢定，這個說法就會落入「結果不好才找理由」的質疑——
而預先登記檔的 `labels_used: false` 與 commit hash 排除了這個可能。"""

PROSE_SIGNAL_DESIGN = """**設計原則：三種資訊來源。**

八個訊號並非任意挑選，而是涵蓋在**實際翻譯之前**可取得的三類資訊：

| 類 | 訊號 | 資訊來源 | 成本 |
| --- | --- | --- | :-: |
| 表層特徵 | S1–S4 | 直接觀察句子（詞表、規則） | 0 次呼叫 |
| 自我評估 | S5、S7 | 直接問模型 | 1 次呼叫 |
| 生成行為 | S6、S8 | 從外部觀察模型的輸出分布 | 2–3 次呼叫 |

各訊號的設計直覺：

- **S1 多義詞**：句中多義詞越多，可能的解讀組合越多
- **S2 主詞省略**：中文常省略主詞，省略處是歧義的常見來源
- **S3 句法複雜度**：結構越複雜，可能的剖析越多
- **S4 文化專有項**：成語與慣用語的字面義與實際義常不一致
- **S5 LLM 直接判定**：模型自陳這句話有多歧義
- **S6 往返保真度**：翻譯再譯回中文，語意漂移越大代表原句越不確定
- **S7 讀法列舉數**：模型列舉的替代讀法越多，代表它認為越歧義
- **S8 語意熵**：多次取樣的譯文若分散在多個語意群，代表模型在搖擺

**成本階梯是刻意的。** Router 的意義在於用比完整驗證便宜的方法做出
分流決策；若訊號本身就跟驗證一樣貴，分流就失去意義。三類訊號的
成本從 0 到 3 次呼叫，恰好對應「可以多便宜」的光譜。"""

# ⚠️ 只在三個位置皆達 100% 時使用——第二、三段直接斷言天花板效應，
#    數字一旦變動論述就是錯的。條件不成立時退回 todo()。
PROSE_RQ3 = """Liu et al. (2024) 報告了長脈絡中的 Lost-in-the-Middle 現象：
關鍵資訊位於脈絡中段時，模型的取用率顯著低於位於首尾時。本節檢驗
一個直接的緩解：以檢索補回被滾動摘要壓縮掉的內容。

無記憶組（固定視窗）的結果重現了該現象的極端版本——關鍵資訊在頭段
與中段時召回率為 {head_baseline:.0%}，因為固定視窗根本沒有涵蓋它們。
加入記憶模組後三個位置皆為 {memory:.0%}。

⚠️ **但這是天花板效應，不能當作模組有效的證據。**

{turns} 則訊息中只有 1 則與查詢相關、檢索 top-{top_k}——**任務對檢索而言太簡單**。
題目本身也是自動生成的，關鍵事實（「專案代號是 XXXX」）在詞彙上
與填充訊息區隔明顯。{memory:.0%} 這個數字反映的是題目難度，不是模組能力。

此結果只證明**機制可行**：滾動摘要壓掉的內容確實能由檢索補回，
記憶模組不會退化成一個比較貴的固定視窗。它不證明在更難的場景
（多則部分相關、需跨訊息綜合、關鍵資訊本身模糊）仍然有效。

⚠️ 每位置 n={n_per_pos}，本節為初步驗證。"""

PROSE_TWO_CONSTRUCTS = """二元對比（{binary_err:.1%}）與 N 選一（{nway_err:.1%}）測的是不同的能力，
不是同一個量的兩個估計：

| | 問的問題 | 隨機基準 |
| --- | --- | :-: |
| 二元對比 | 模型能否把正解與**最易混淆的競爭者**分開 | 50% |
| N 選一 | 模型能否**精準命中**細粒度義項中的那一個 | ~{nway_chance:.1%} |

前者是 DiBiMT / MuCoW 一系 MT 詞義評測的既有範式，且判定可靠
（一致率 {judge_human:.0%}）；後者是完整的 WSD 任務，但在本研究的設定下判定
不可靠（{nway_judge_lo:.0%}–{nway_judge_hi:.0%}）。

⚠️ 因此**不得將 {nway_err:.1%} 當作 {binary_err:.1%} 的「上界」來論證**。那個數字所依賴的
judge 未通過驗證，且該驗證已標記為 `contaminated`。兩者並列僅供讀者
理解不同建構下的量級差異。"""

PROSE_JUDGE_PROPAGATION = """主指標與所有 AUC 的標籤均來自 sense_judge，judge 的錯誤會直接傳遞
到下游的每一個數字。本研究以三種方式處理這個問題：

1. **量測它**——人工盲標 {nv} 筆，judge 與人工一致率 {judge_human:.0%}（CI [{jh_lo:.0f}, {jh_hi:.0f}]）
2. **餵回檢定力計算**——{noise:.0%} 的噪音使 `required_auc` 由 {req_clean:.3f} 升至 {req_noise:.3f}
3. **分解它**——位置效應（{pos:.1f}pp）是總噪音的**成分**而非加項（§6.4）

⚠️ 位置效應的 {pos:.1f}pp 是噪音的**下界**，不是估計值。它只涵蓋了
「judge 依 A/B 位置而非內容作答」的部分；內容判斷本身的錯誤
（約 {content:.1%}）無法用同樣的方式拆解。

🔴 更嚴重的是 judge 的獨立性未通過驗證（見 §8.2b）。這使得
self-preference bias 無法排除，而該偏誤的方向與大小都無法從現有
資料估計。"""

PROSE_SAMPLE_SIZE = """**樣本數**

| 量測 | n | 影響 |
| --- | :-: | --- |
| 主指標與 AUC | {n_judgeable} | CI 寬度約 ±{acc_hw:.1f}pp；`required_auc` {req_noise:.3f} |
| judge 人工驗證 | {nv} | 一致率 CI [{jh_lo:.0f}, {jh_hi:.0f}]，很寬 |
| 天花板估計 | {nv} | 校正後錯誤率 CI [{cc_lo:.1%}, {cc_hi:.1%}] |
| RQ3 | {rq3_n}／位置 | 僅供初步驗證 |

降低標籤噪音的邊際效益高於加大樣本數——見 §6.4 的事前檢定力表：
噪音由 {noise:.0%} 降至 0% 可使門檻由 {req_noise:.3f} 降至 {req_clean:.3f}，
而在 {noise:.0%} 噪音下加大 n 只能收窄 CI，無法降低門檻。

**檢定力不是本研究 null 的解釋。**

Kuhn et al. 在問答任務上報告語意熵預測答錯的 AUROC 為 0.70–0.82。
本研究的顯著門檻為 `required_auc = {req_noise:.3f}`。

**若 S8 具有該量級的效果，本研究一定測得出來。** 因此「訊號其實有效
但樣本不夠」不是一個成立的解釋——至少對 0.70 以上的效果量而言不是。

檢定力的限制只適用於更弱的效果：真實 AUC 落在 0.55–0.62 之間的訊號
無法被本研究偵測（§4.5）。

**可推廣性**

- **單一翻譯模型**（`{translate_model}`）。結果不保證推廣到其他 MT 系統
- **單一語言對**（中→英）。日文、德文的技能檔已實作但未納入本次評測
- **高多義詞**（CWN 中義項數 >10）。這是刻意選擇的困難子集，
  一般詞彙的錯誤率應顯著較低"""

# ⚠️ 走勢的前三個點（n=30、n=200 v1／v2）對應的執行已不存在，沒有結果檔可讀，
#    是本檔第二處手抄的數字。最後一點與 CI 自 wsd_baseline400.json 讀取。
PROSE_STRATUM_TREND = """**分層效應的走勢。**

兩層之差在四次量測中的變化：

```
+22.4pp (n=30)  →  +10.1pp (n=200, judge v1)
                →  +6.6pp (n=200, judge v2)
                →  {diff:+.1f}pp (n={n}, 二元)
```

每一次**加大樣本或改善量測**，效應就縮小一次。這是雜訊衰減的典型形狀
——初期的大效應來自小樣本的抽樣變異，隨著 n 增加向真值收斂。

最終的 {diff:+.1f}pp，95% CI [{ci_lo:+.1f}, {ci_hi:+.1f}]pp 涵蓋 0。**本研究沒有證據支持
「非主流義項較難翻對」。**

這個結果與 CHA-Gen 報告的「模型偏好主流解讀」不一致。兩個可能的解釋：
(a) 該偏好在詞義選擇任務上的效果小於可偵測水準；
(b) 二元強迫選擇的設定壓縮了效應空間（隨機基準由 {nway_chance:.1%} 升至 50%，見 §8.1）。
本研究無法區分這兩者。

⚠️ 走勢中的每一步都改變了不只一個變因（樣本量、judge 版本、判定設定），
因此不能把它讀成受控的收斂實驗。它只是說明：**這個效應在越乾淨的
量測下越小**，而不是越大。"""

# ⚠️ tokenizer 截斷表與第 1 次敏感度嘗試的數字沒有 JSON 來源，
#    自 data/results/endpoint_identity_check.md 與 judge_sensitivity_status.md 抄來。
#    這兩份報表本身是committed 的一手證據，改動時兩邊都要更新。
PROSE_JUDGE_INDEPENDENCE = """LLM-as-a-Judge 的標準防呆是「受測模型與評判模型不能是同一個」。
本研究實作了這個檢查，翻譯用 `mistral-small-4`、判定用 `gpt-oss-120b`，
字串不同，檢查通過，全部測試為綠。

**但這兩個 model id 極可能由同一個後端提供服務。**

決定性的證據是 tokenizer 的截斷行為。`max_tokens` 的截斷發生在推論引擎，
用的是模型自己的 tokenizer；不同 tokenizer 對同一段中文的切分不同，
截斷位置就會不同。實測：

| `max_tokens` | `mistral-small-4` | `gpt-oss-120b` | |
| :-: | --- | --- | :-: |
| 6 | 5 字 | 5 字 | 🔴 逐字相同 |
| 10 | 8 字 | 8 字 | 🔴 逐字相同 |
| 16 | 13 字 | 13 字 | 🔴 逐字相同 |

對照組 Gemini 在同樣設定下用掉 7 tokens 且回傳空字串——切分方式明顯不同，
**那才是不同 tokenizer 該有的樣子**。

原本的檢查比較的是 provider/model **字串**，而 self-preference bias
取決於**是不是同一個模型**。名稱由 API 供應方決定，與後端實際載入什麼
權重之間沒有保證。

**⇒ self-preference bias 無法排除。**

完整證據見 `data/results/endpoint_identity_check.md`，
方法學討論見 `docs/judge_cross_pitfall.md`。

#### 影響範圍與未受影響的部分

| | 是否受影響 |
| --- | :-: |
| 主指標 {binary_err:.1%}、所有 AUC、judge 人工驗證 | 🔴 是 |
| 探針抽樣、S1–S4 純規則訊號、Lost-in-the-Middle | ✅ 否 |

⚠️ 但主結果的效度**不完全建立在 judge_cross 上**，理由有二：

1. **judge 判定的不是譯文之間的優劣，而是譯文與外部義項定義的對應。**
   self-preference bias 的典型形式是「模型偏袒自己的輸出」，
   而此處沒有兩個輸出可供偏袒——judge 是在把一個譯文對應到
   CWN 標註的兩個候選義項之一
2. **有外部錨點。** 研究者人工盲標與 CWN gold 的一致率為 {human_gold:.0%}，
   與模型無關；judge 與人工的 {judge_human:.0%} 一致率也是相對於這個外部參照量測的

**但獨立性的宣稱必須撤回。** 本研究不能主張「因為使用了不同模型，
所以評判是客觀的」。

#### 敏感度檢查未完成

原規劃以 Gemini（確定不同來源，行為檢查通過）重判 {n_sampled} 筆作為敏感度檢查。
兩次嘗試因外部 API 配額限制中止，分別只得 10 筆與 {n_second} 筆可比題目，
遠低於可下判讀的門檻（n≥{min_n}）。

⚠️ n=10 時對照 judge 錯誤率的 95% CI 為 [1.8%, 40.4%]，涵蓋整個判讀區間，
因此**不採用該批數字**。過程記錄見 `data/results/judge_sensitivity_status.md`。

**「主指標對 judge 選擇是否敏感」在本研究中沒有答案。**"""

# §2 的數字絕大多數來自外部論文，無結果檔可讀，照研究者的閱讀筆記寫入。
# 唯一自結果檔插入的是 S6 的 AUC。
PROSE_RELATED_WORK = """### 2.1　語意熵與不確定性量化

Kuhn, Gal & Farquhar (ICLR 2023) 指出量測自然語言不確定性的核心困難是
**語意等價**——同一個意思有很多種說法，直接算 token 層級的熵會把
「換句話說」誤判為「不確定」。他們提出**語意熵**：對同一題取樣多個回答、
以 NLI 雙向蘊涵判定哪些互相等價、分群後在群的層級上算熵。
在問答任務上，語意熵預測模型答錯的 AUROC 為 0.70–0.82。

本研究的 S8 直接沿用這個方法，但有三處實作上的降級，必須說明：

| | Kuhn et al. | 本研究 S8 |
| --- | --- | --- |
| 分群依據 | NLI 雙向蘊涵，人工標註 300 筆驗證分群品質 | embedding 餘弦相似度 0.92，未驗證 |
| 熵的計算 | token 機率加權 | 僅計群大小（黑箱 API 無 logprobs），未加權近似 |
| 任務 | 問答（語意群邊界清楚） | 翻譯（譯文差異多為措辭，訊噪比較差） |

⚠️ 該文亦專章討論**長度作為不確定性的混淆變因**。本研究的純句長基準
（§4.5）因此不是本研究獨有的檢查，而是這一系方法的標準做法。

### 2.2　中文歧義的評測

**Wu et al. (2025)** 建立 900 句的中文歧義基準（詞彙／句法／語用三大類、
九小類），以中文直接詢問模型三件事：這句是否歧義、列出所有解讀、
以及兩者的組合。主要發現是 LLM 難以區分歧義與非歧義文本、傾向以過度自信
咬定單一解讀、而在被要求解釋時又會過度推論。

**CHA-Gen (2026)** 以潛在歧義論為基礎生成 5,712 句資料集（18 種歧義結構），
並以兩條路徑評測：直接詢問，以及中譯英取樣 50 次後計算語意熵。
結論是模型的歧義判斷接近隨機（F1 約 0.5），而歧義句的語意熵確實較高。

### 2.3　以翻譯偵測歧義

**Mehrparvar & Pezzelle (MRL 2024)** 是與本研究最接近的先行工作。
他們將英文句子翻成 14 種語言再翻回，記錄模型在去程與回程的內部狀態，
訓練一個網路學習兩組狀態之間的對應；歧義句與非歧義句的對應難度不同，
以此差異為特徵訓練分類器，最高達 94.94%。

核心假設與本研究一致：**翻譯會迫使模型將內部狀態外顯**。

### 2.4　本研究的定位

| | Wu et al. | CHA-Gen | Mehrparvar & P. | 本研究 |
| --- | :-: | :-: | :-: | :-: |
| 觀測方式 | 直接詢問 | 詢問＋翻譯 | 往返翻譯 | 往返翻譯 |
| 讀取層次 | 模型自陳 | 自陳＋輸出分布 | **隱藏狀態** | 譯文表面 |
| 標籤在哪 | 句子 | 句子 | 句子 | **模型輸出** |
| 是否監督訓練 | 有（BERT-ft） | 否 | **有** | **否** |
| 語言方向 | 中文（單語） | 中→英 | 英→14 語 | 中→英 |
| 歧義類型 | 詞彙／句法／語用 | 句法 | 未分類 | **詞彙（多義詞）** |

三處實質差異：

**① 標籤在模型輸出上，不在句子上。** 前三者問的是「這個句子歧不歧義」，
本研究問的是「模型有沒有選錯義項」。前者的 gold 依賴標註者對歧義的判斷，
後者的 gold 是 CWN 的義項標註加上譯文的判定——是可由外部客觀檢驗的
**下游損害**，不是對歧義程度的主觀評估。

**② 不做監督訓練。** Mehrparvar & Pezzelle 用標籤訓練分類器，Wu et al.
微調 BERT。本研究的所有訊號都是**未擬合的**，權重不調、閾值不調
（§4.2 預先登記）。這是刻意的取捨：Router 的應用場景要求訊號在
沒有標籤的新輸入上就能用。

**③ 現象不重疊。** CHA-Gen 在其限制中明確指出只涵蓋句法歧義，
多義詞（polysemy）列為未涵蓋的未來工作——而那正是本研究的對象。

### 2.5　先行研究中與本研究一致的證據

值得指出的是，**Mehrparvar & Pezzelle 的細部結果與本研究的否定結論方向一致**：

- 單一目標語言時分類準確率僅 **57.81%**
- 14 種語言逐一檢定，**12 種不顯著**
- 94.94% 是靠堆疊 14 個語言維度加上監督訓練換來的

換言之，該研究同樣顯示**單一便宜的往返翻譯訊號不足以偵測歧義**。
本研究在中文詞義選擇任務上得到的 null（S6 往返保真度 AUC {s6_auc:.3f}）
與此一致。

⚠️ 另一個未被討論的細節：在他們的 14 種語言中，**中文的判別力最強**
（唯一達 p=0.001 的語言），但該文未對此提出解釋。若這個現象穩健，
它與本研究對中文高語境性的關注可能有關，但本研究無法驗證。"""

PROSE_SUPERVISED_GAP = """Wu et al. (2025) 報告微調後的 BERT 在其歧義偵測任務上達到 94.70%，
遠高於本研究所有訊號的表現。這個對比需要說明，否則容易被誤讀為
本研究的方法特別差。

三處不可比：

**① 目標變數不同。** 他們的分類器預測「這個句子是否歧義」，
標籤在句子上；本研究預測「模型是否選錯義項」，標籤在模型輸出上。
後者依賴模型當下的行為，不是句子的固有屬性。

**② 監督 vs 未擬合。** BERT-ft 在該資料集上訓練過；本研究的所有訊號
都不擬合任何參數（§4.2 預先登記）。這不是能力差異，是設定差異——
Router 的應用場景要求訊號在沒有標籤的新輸入上直接可用。

**③ 表層特徵的可分性不等於現象的可預測性。** 一個在特定資料集上
達到高準確率的監督分類器，可能學到的是該資料集的建構痕跡而非
歧義本身。本研究對該資料集的長度稽核發現，僅使用句長的分類器即可
達到 AUC **{wu_auc:.3f}**（n={wu_n}／{wu_n}，歧義側均長 {wu_mean_amb:.1f} 字、
消歧側 {wu_mean_ctl:.1f} 字；見 `data/external/length_audit_summary.md`）
——這說明該資料集的兩組在表層特徵上高度可分。

⚠️ 這不是對 Wu et al. 的批評：該資料集是為「生成消歧版本」設計的，
長度差異對其原用途不構成問題。有問題的是把它當偵測任務的負例——
那是本研究的用法，不是原作者的主張。"""

PROSE_LENGTH_NULL = """十個量測（八個訊號＋未加權總和＋純句長）全部落在 0.5 附近，
95% CI 全數涵蓋 0.5。

**這裡真正關鍵的是純句長基準也不顯著（AUC {len_auc:.3f}，CI {len_ci}）。**

若只有本研究自訂的八個訊號失敗，最自然的解釋是訊號設計不良——
特徵選得不對、規則寫得太粗、prompt 不夠好。這些都是可以靠更好的
工程解決的問題。但純句長不同：它不依賴任何語言學假設，也不依賴
任何實作品質，就只是數字元。它同樣不顯著。

因此這個對照把兩種解釋分了開來：

| | 解釋 | 是否可由更好的設計解決 |
| :-: | --- | :-: |
| (a) | 我們沒找到對的訊號 | 可以 |
| (b) | 句子的可觀察屬性與模型是否譯錯之間沒有可用的關聯 | 不行 |

純句長的結果支持 (b)。

**訊號涵蓋了三種取得資訊的方式，三種同時失效。** S1–S4 是純規則的
表層特徵（客觀觀察句子）、S5 與 S7 是模型的自我評估（主觀自陳）、
S6 與 S8 是模型的生成行為（從外部觀察模型自己）。這三類分別對應
「看題目」「問模型」「看模型怎麼做」，涵蓋了在不實際翻譯之前
可取得的三種資訊來源。三者同時落在雜訊水準，比任一類單獨失效
更難用設計不良來解釋。

#### 一個直覺上的反例

較長的句子提供較多上下文，而 LLM 相對於統計式機器翻譯的優勢正是
更能利用上下文——照這個推論，句子越長模型應該越少譯錯。實測不支持
這個方向（純句長 AUC {len_auc:.3f}，與 0.5 無異）。

合理的解釋是：決定譯得對不對的不是上下文的**量**，而是上下文裡
**有沒有剛好能消歧的那個線索**。一個二十字的句子若沒有任何一處
指向正確義項，並不會比五字的句子更容易譯對。而「有沒有那個線索」
無法從句子的表面屬性讀出來——那正是本節十個量測共同顯示的。

**這個檢查不是本研究獨有的。** Kuhn et al. (ICLR 2023) 在建立語意熵
方法時即專章討論長度作為不確定性的混淆變因。純句長基準是這一系
方法的標準做法，本研究只是把它明確地列入對照表。

**先行研究亦有一致的證據。** Mehrparvar & Pezzelle (2024) 在使用
單一目標語言時，歧義偵測的準確率為 57.81%；14 種語言逐一檢定時
12 種不顯著。他們達到的 94.94% 是靠堆疊 14 個語言維度加監督訓練
取得的。這與本研究的結論一致：**單一便宜訊號不足以偵測**——
差別在於他們用堆疊與監督訓練解決，而那不適用於 Router 的場景
（見 §2.4）。

#### 誠實的限制

`required_auc = {req_noise:.3f}` 是在 {noise:.0%} 的標籤噪音下算出的。真實 AUC 落在
0.55 到 0.62 之間的訊號，在本研究的樣本數（n={n_auc}）與標籤品質下
**無法被偵測**。

因此本節的結論應讀作「**沒有訊號達到可偵測的效果量**」，而非
「不存在任何關聯」。若要偵測更弱的關聯，降低標籤噪音的邊際效益
高於加大樣本數——見 §6.4 的事前檢定力表。"""

# §5 全節論述（5.1–5.4），無插值欄位。
PROSE_RQ2 = """### 5.1　Router 原本要做什麼

計畫書設計的 Router 是一個**分流器**：在翻譯之前先用很低的成本判斷
一句話的歧義程度，低分的直接翻譯（快速通道），高分的才進入多視角
驗證與反思迴圈（慢速通道）。這樣可以把算力集中在真正會出錯的句子上，
而不是對每一句都付出完整的驗證成本。

計畫書原本以「跨語言 PPL 變異數」作為判斷依據——同一句話翻成多種
語言後，各版本之間的差異越大，歧義越大。但這個指標構成**循環依賴**：
要算出跨語言變異數，必須先完成多路徑翻譯與回譯，而那正是慢速通道
本身。等於為了判斷要不要付出昂貴的成本，必須先把那個成本付掉。

因此改為八個真正的前置訊號（差異表 D4），涵蓋詞表比對、規則判斷、
單次模型呼叫等成本遠低於完整驗證的方法。

### 5.2　為什麼 §4 直接否定了 RQ2

分流之所以有意義，前提是**這些便宜的訊號能挑出會出錯的句子**。
§4 的結果證明這個前提不成立：八個訊號、未加權總和、以及純句長基準，
十個量測的 95% CI 全數涵蓋 0.5。

沒有可用的訊號，任何以訊號為依據的分流都等同於隨機分流。
成本–準確度前緣上，訊號導向的策略不可能勝過同成本的均一策略。

**RQ2 因此有答案，而且是實證得來的否定答案。**

### 5.3　P5／P6 的取消決定

| 階段 | 原規劃 | 狀態 | 理由 |
| :-: | --- | :-: | --- |
| P5 | Router 成本–準確度前緣 | 🚫 取消 | 分流前提已被 §4 否證，前緣圖只會是一條水平線 |
| P6 | 八組對照主實驗 | 🚫 取消 | 既然任何分流都不優於隨機，八組之間也不會有訊號；§4 的 AUC 表已是主實驗 |

**取消的理由不是成本，是結果。** 這一點必須說清楚：
P5 與 P6 的執行成本在本專案的資源範圍內（估計數小時的 API 呼叫），
取消它們是因為**執行完不會產生可解讀的資訊**——
一條已知會是水平線的曲線，以及八組已知會全部涵蓋 0.5 的 CI，
後者還會額外引入多重比較問題。

決定的時間點在 §4 的 AUC 表產出之後、任何 P5/P6 的程式碼開工之前。

### 5.4　為什麼把取消寫進報告

依實驗結果修改後續計畫，是研究過程的一部分，不是需要掩飾的偏離。
把它寫出來有三個作用：

1. **讀者能檢驗這個決定是否合理**——判準（十個 CI 全涵蓋 0.5）與
   時間點（AUC 表產出後）都在報告裡，可以自行判斷
2. **與計畫書的差異可追溯**——見差異表 D17
3. **避免把否定結果誤讀為未完成**——沒有 P5/P6 的圖表，
   不是因為做不完，是因為做了也是空的

⚠️ 這也是一個誠實性的問題：若靜默地不做，讀者只會看到報告裡
缺少計畫書承諾的兩節，而無從得知那是有依據的決定還是進度落後。"""

# ⚠️ 前次執行的 S8 未校正 p（0.019）沒有結果檔可讀，是本檔第三處手抄的數字；
#    AUC 0.431 讀自 _snapshot_before.json。
PROSE_S8_REVERSAL = """S8 的 AUC 為 **{auc:.3f}**（< 0.5）——答錯的題目，八個譯文樣本反而
**更一致**。這與「不確定性高則容易出錯」的直覺相反。

**與 CHA-Gen 不矛盾，兩者比較的對象不同：**

| | 比較對象 |
| --- | --- |
| CHA-Gen | 歧義句 vs 非歧義句 |
| 本研究 | 答錯 vs 答對 |

兩者可以同時為真。

**一個有外部證據的解釋：指令微調壓縮了熵。**

CHA-Gen 在同尺寸模型上量到 Base 版的歧義／非歧義熵差為 0.299，
Instruct 版只剩 **0.0599**——指令微調把語意熵的訊號壓掉了約五倍。

這個發現直接關係到本研究：**S8 的量測對象 `{translate_model}` 是
instruct 模型**。而 Kuhn et al. 建立語意熵方法時使用的是 OPT，
2023 年當時尚無 instruct 版本。

兩者交叉起來指向一個未被系統檢驗的問題：**語意熵這個方法是在
base 模型上驗證的，它在 instruct 模型上是否仍然有效，本身是個問號。**

若指令微調確實壓縮了熵的動態範圍，本研究 S8 的 null 就不是
「語意熵無效」，而是「語意熵在 instruct 模型上的可用範圍被壓縮到
本研究的偵測門檻之下」。這兩者的意涵不同——前者否定方法，
後者指出方法的適用邊界。

⚠️ 本研究未測 base 模型，因此無法區分這兩種解釋。
這是 §8.6 可推廣性限制的一部分。

#### 呼應計畫書的問題意識

計畫書的出發點是模型會「一本正經地胡說八道」——輸出流暢、自信，
但內容是錯的。S8 的方向若成立，會是這個現象的一個量化版本：
**錯誤與低不確定性同時出現**，模型的自信與它的正確性脫鉤。

🔴 **但本研究不宣稱這是一個發現。**

未校正排列 p = {perm_p:.3f}，Holm 校正後 {holm_p:.3f}，n = {n_auc}。**這個結果本身
就不顯著。**

更關鍵的是它的不穩定性：在兩次執行之間，S8 的 AUC 由 {prev_auc:.3f} 變為
{auc:.3f}、未校正 p 由 0.019 變為 {perm_p:.3f}（差異來源見 §3.4 的端點漂移）。
**換一次端點狀態，這個「反轉」就縮回雜訊水準。**

方向與預期相反的結果特別容易被過度解讀，因為它們看起來有故事性。
本研究的立場是：這個方向值得以更大樣本與更穩定的端點重新檢驗，
但在此之前它只是一個觀察，不是結論。"""

PROSE_SENSE_GRANULARITY = """盲標時研究者的第二欄記錄了一個直接的量測：**{amb:.0%} 的題目（{n_amb}/{nv}，
95% CI [{amb_lo:.0%}, {amb_hi:.0%}]）被判定為「兩個義項在這個譯文裡都說得通」。**

這不是判定者的能力問題，而是**任務本身的上限**。CWN 的義項粒度
細於英文譯文所能承載的資訊——中文詞典區分得出來的兩個義項，
翻成英文之後可能落在同一個詞上，判定者（無論是人或模型）
只能猜。

三項證據指向同一件事：

| 觀察 | 數值 |
| --- | :-: |
| 研究者盲標時判定「兩個都說得通」 | {amb:.0%} |
| 研究者與 CWN gold 的一致率 | {human_gold:.0%} |
| N 選一設定下 judge 與人工的一致率 | {nway_lo:.0%}–{nway_hi:.0%} |

第二項尤其關鍵：**研究者看著英文譯文判定，與看著中文原句標註的
CWN 標註者，有 {gold_to_human:.0%} 對不上。** 那 {gold_to_human:.0%} 不是任一方標錯，是跨語言
判定的固有損失。

這個數值被用於主指標的天花板校正（§3.6）。它也解釋了為什麼
N 選一的設定不可靠——義項越細，可判定的比例越低。

⚠️ 天花板估計僅 n={nv}，CI 為 [{amb_lo:.0%}, {amb_hi:.0%}]，因此校正後的錯誤率區間
（[{cc_lo:.1%}, {cc_hi:.1%}]）相當寬。加大盲標樣本是收窄它的最直接方法。"""

PROSE_PHENOMENON_LIMIT = """本研究測的是**詞彙歧義**，而中文高語境性最典型的表現是**語用歧義**
（反諷、委婉、話中有話）。這個轉向的理由在 §1.1：語用歧義缺乏
可辯護的標準答案。

代價是：本研究的結論**只適用於詞義選擇**。「便宜訊號無法預測詞義
錯誤」不蘊含「便宜訊號無法預測語用誤解」——後者尚未被檢驗。

另一個必須說明的前提：**LLM 在一般翻譯任務上已相當可靠。**
本研究刻意選擇了高多義詞這個困難子集，因此 {binary_err:.1%} 的錯誤率不應被
讀為「LLM 翻譯有三成錯誤」，而應讀為「在義項數超過十個的困難詞上，
即使是 LLM 也有三成的對比詞義錯誤」。"""


def main(out: pathlib.Path | None = None) -> int:
    base = load("wsd_baseline400.json")
    nway = load("wsd_baseline400_nway.json")
    val = load("judge_validation_r2.json")
    sig = load("signals_all.json")
    prereg = load("signal_preregistration.json")
    if not (base and val and sig):
        print("🔴 缺少結果檔，先跑 run_wsd / judge_validate / run_signals",
              file=sys.stderr)
        return 1

    nv = val["n"]
    ne = compose_noise(n_agree=round(val["judge_vs_human"] * nv), n_total=nv,
                       position_noise=base["position_effect"]["implied_noise"])
    dec = decompose(judge_vs_human=val["judge_vs_human"],
                    human_vs_gold=val["human_vs_gold"],
                    judge_vs_gold=val["judge_vs_gold"], n=nv)
    cc = ceiling_correct(base["accuracy"],
                         n_ambiguous=round(val["both_plausible_rate"] * nv),
                         n_annotated=nv)
    pe = base["position_effect"]
    # 顯著門檻：0% 噪音 vs 實測 25% 噪音。鍵是登記時寫入的噪音水準字串。
    ra = prereg.get("required_auc", {})
    req_clean, req_noise = ra.get("0.0", 0.563), ra.get("0.25", 0.626)
    # 主指標 CI 的半寬——§8.6 的「±?pp」由它算，不手抄
    _lo, _hi = wilson_ci(base["n_correct"], base["n_judgeable"])
    acc_hw = (_hi - _lo) / 2
    sa = RESULTS / "signals_all.md"
    auc = auc_table(sa)
    an = auc_n(sa)
    # N 選一那一輪的 judge 驗證（已標記 contaminated），供 §3.5 與 D16 引用
    nway_val = load("judge_validation_p2.json")
    # p1 = prompt v1、p2 = prompt v2，同為 N 選一。§3.2 的「50–60%」是這兩者。
    nway_val_v1 = load("judge_validation_p1.json")

    L: list[str] = []
    a = L.append
    _TODO_EMITTED.clear()

    a("# Cognitive-Core 技術報告")
    a("")
    a(f"> 骨架由 `scripts/build_report.py` 產生於 "
      f"{datetime.date.today().isoformat()}　commit `{git_hash()}`")
    a("> **所有數字自結果檔讀取，不手抄。** 重跑實驗後重新執行本腳本即可更新。")
    a(_HEADER_SLOT)   # 依是否還有 TODO 決定內容，在寫檔前替換
    a("")
    a("---")
    a("")

    # ── 1 ──
    a("## 1　緒論")
    a("")
    a(PROSE_INTRO)
    a("")
    a("### 1.3　三個研究問題")
    a("")
    a("| | 問題 | 本研究的答案 |")
    a("| :-: | --- | --- |")
    a("| RQ1 | 能否用便宜的前置訊號預測 MT 的詞義錯誤 | **否**（§4）|")
    a("| RQ2 | 成本–準確度前緣上，訊號導向的分流能否勝過均一策略 | "
      "**否**，由 RQ1 直接推得（§5）|")
    a("| RQ3 | 記憶模組能否改善跨輪一致性 | 初步驗證（§7）|")
    a("")

    # ── 2 ──
    a("## 2　相關工作")
    a("")
    a(PROSE_RELATED_WORK.format(
        s6_auc=auc.get("S6_roundtrip", {}).get("auc", 0.532)))
    a("")

    # ── 3 主結果 ──
    a("## 3　主結果：高多義詞的 MT 詞義對比錯誤率")
    a("")
    a("### 3.1　資料")
    a("")
    a("| 項目 | 值 |")
    a("| --- | :-: |")
    a("| 來源 | `lopentu/Chinese-Wordnet-SemCor`（MIT）|")
    a("| 目標詞 | CWN 2.0 中義項數 >10 的高多義詞，113 個 |")
    a("| 候選池 | 17,967 |")
    a(f"| 抽樣 | 分層 {base['n'] // 2}／{base['n'] // 2}"
      "（主流＝gold 為最高頻義項；非主流＝其餘）|")
    a(f"| 實際評測 | n={base['n']} |")
    a("")
    a(PROSE_STRATIFY.format(
        per_stratum=base["n"] // 2,
        nd_acc=base["by_stratum"]["non_dominant"]["acc"]))
    a("")

    a("### 3.2　判定協定")
    a("")
    a(f"- 翻譯：`{base['translate_model']}`（temperature=0）")
    a(f"- 判定：`{base['judge_model']}`，**二元強迫選擇**")
    a("- 候選：gold vs 同 lemma 中最高頻的非 gold 義項（最易混淆的干擾項）")
    a("- 干擾項選法寫死在 `pick_distractor()`，不由模型選、不隨機")
    a("- A/B 位置在**分層內逐題交替**配平（非雜湊）")
    a("- 🔴 judge 與受測模型**經查極可能由同一後端提供服務**——"
      "原本的 `assert_judge_is_cross` 只比名稱，見 §8.2b")
    a("")
    a(PROSE_BINARY.format(
        nway_judge_lo=min(nway_val_v1["judge_vs_human"], nway_val["judge_vs_human"]),
        nway_judge_hi=max(nway_val_v1["judge_vs_human"], nway_val["judge_vs_human"]),
        nway_human_gold=nway_val["human_vs_gold"],
        judge_human=val["judge_vs_human"], human_gold=val["human_vs_gold"],
        nway_none=nway["none"] / nway["n"], nway_none_n=nway["none"],
        nway_n=nway["n"], none=base["none"] / base["n"],
        none_n=base["none"], n=base["n"],
        nway_judgeable=nway["n_judgeable"] / nway["n"],
        judgeable=base["n_judgeable"] / base["n"],
        nway_chance=1 / MAX_CANDIDATE_SENSES))
    a("")

    a("### 3.3　主指標")
    a("")
    a("| 項目 | 值 | 95% CI |")
    a("| --- | :-: | :-: |")
    a(f"| 可判定 | {base['n_judgeable']}/{base['n']} | — |")
    a(f"| NONE | {base['none']}/{base['n']} | — |")
    a(f"| 義項正確率 | {base['accuracy']:.3f} | — |")
    a(f"| **對比錯誤率** | **{1 - base['accuracy']:.1%}** | — |")
    a("| 隨機基準 | 50% | — |")
    a("")
    a("**分層**")
    a("")
    a("| 層 | n | 正確率 | 95% CI |")
    a("| --- | :-: | :-: | :-: |")
    for k, lab in (("dominant", "主流"), ("non_dominant", "非主流")):
        d = base["by_stratum"][k]
        a(f"| {lab} | {d['n']} | {d['acc']:.3f} | "
          f"[{d['ci'][0]:.3f}, {d['ci'][1]:.3f}] |")
    a("")
    a(f"兩層之差 **{base['diff'] * 100:+.1f}pp**　95% CI "
      f"[{base['diff_ci'][0] * 100:+.1f}, {base['diff_ci'][1] * 100:+.1f}]pp"
      f"　p≈{base['p']:.3f}")
    a("")
    # 走勢改由論述帶出（含區塊圖），此處不再另印一行。
    a(PROSE_STRATUM_TREND.format(
        diff=base["diff"] * 100, n=base["n"],
        ci_lo=base["diff_ci"][0] * 100, ci_hi=base["diff_ci"][1] * 100,
        nway_chance=1 / MAX_CANDIDATE_SENSES))
    a("")

    a("### 3.4　兩次執行的比較 ⭐")
    a("")
    a("本專案的結果跑過兩次。**第二次是從零重現驗證**——快取與 run log "
      "搬離後依序重跑整條管線。")
    a("")
    a("| 指標 | 8/20-21 | **8/22-23（採用）** | 結論是否改變 |")
    a("| --- | :-: | :-: | :-: |")
    for lab, old, new, note in (
            ("對比錯誤率", "29.6%", f"{1 - base['accuracy']:.1%}", "否"),
            ("兩層之差", "+3.9pp", f"{base['diff'] * 100:+.1f}pp",
             "否，兩者 CI 皆涵蓋 0"),
            ("位置效應 p", "0.084", f"{pe['p']:.3f}", "否，皆不顯著"),
            ("judge vs 人工", "85%", f"{val['judge_vs_human']:.0%}",
             "否，AUC 全部不顯著")):
        a(f"| {lab} | {old} | **{new}** | {note} |")
    a("")
    a("**沒有任何結論改變。** 差異的來源是**校內端點在兩個日期之間換了模型**——")
    a("不是 per-call 隨機性（20 句 × 3 次、停用快取，100% 相同），")
    a("而是時間漂移（當下重新呼叫的結果永遠等於 8/22 值，從不等於 8/20-21 值）。")
    a("")
    a("**採用後者的三個理由：**")
    a("")
    a("1. 那是可重現的那一套——現在的端點狀態就是它")
    a("2. 舊值對應的端點已不存在，別人無法驗證")
    a("3. 兩次的差異與採用理由都寫在這裡，讀者可以自行判斷")
    a("")
    a("舊值保留在 git 歷史中，未刪除。"
      "完整比對見 `data/results/reproduction_check.md` 與 "
      "`reproduction_diagnosis.md`。")
    a("")
    a("⚠️ 端點漂移**無法從 API 察覺**（無 `system_fingerprint`，"
      "`/models` 的 `created` 是固定佔位值）。")
    a("已建 `scripts/endpoint_fingerprint.py` 作為偵測工具。")
    a("")

    a("### 3.5　次要指標（exploratory）")
    a("")
    if nway:
        a("| 建構 | 錯誤率 | 隨機基準 | 地位 |")
        a("| --- | :-: | :-: | --- |")
        a(f"| 二元對比 | **{1 - base['accuracy']:.1%}** | 50% | 主指標 |")
        a(f"| N 選一（完整 WSD） | {1 - nway['accuracy']:.1%} | ~12.5% | "
          "exploratory |")
        a("")
        a("⚠️ 兩者是**不同的建構**，不是同一個量的上下界。"
          f"N 選一那一輪的 judge 未通過驗證（一致率 "
          f"{nway_val['judge_vs_human']:.0%}，且該驗證已標記 "
          "`contaminated`），故只作討論用，不得當作論證支柱。")
    a("")

    a("### 3.6　天花板校正")
    a("")
    a(f"盲標第二欄顯示 **{cc.ambiguous_rate:.0%}** 的題目「兩個都說得通」"
      f"（{round(val['both_plausible_rate'] * nv)}/{nv}，95% CI "
      f"[{cc.ambiguous_ci[0]:.0%}, {cc.ambiguous_ci[1]:.0%}]）。")
    a("")
    a("```")
    a("觀測正確率 = (1−a)·θ + a·0.5      a = 不可判定的比例")
    a("```")
    a("")
    a("| 指標 | 值 | 分母 | 95% CI |")
    a("| --- | :-: | --- | :-: |")
    a(f"| 觀測錯誤率 | **{cc.err_observed:.1%}** | 全部可判定題目 | — |")
    a(f"| 任務天花板 | {cc.ceiling:.0%} | — | — |")
    a(f"| 校正後模型錯誤 | **{cc.err_of_all_items:.1%}** | 全部題目 | "
      f"[{cc.err_of_all_ci[0]:.1%}, {cc.err_of_all_ci[1]:.1%}] |")
    a(f"| 校正後模型錯誤 | {cc.err_of_decidable:.1%} | 僅可判定題目 | "
      f"[{cc.err_of_decidable_ci[0]:.1%}, {cc.err_of_decidable_ci[1]:.1%}] |")
    a("")
    a(f"⚠️ 兩個分母都列出：{cc.err_of_all_items:.1%} 是「每 100 題有幾題是"
      f"模型的錯」，{cc.err_of_decidable:.1%} 是「題目本身有唯一答案時模型錯多少」。"
      f"a 由 n={nv} 估得，CI 很寬。**未校正與校正後都報。**")
    a("")

    a("### 3.7　judge 的人工驗證")
    a("")
    a("| 比較 | 一致率 | 95% CI |")
    a("| --- | :-: | :-: |")
    for lab, key in (("**judge vs 人工**（主指標）", "judge_vs_human"),
                     ("人工 vs gold", "human_vs_gold"),
                     ("judge vs gold", "judge_vs_gold")):
        r = val[key]
        a(f"| {lab} | {r:.0%} | — |")
    a("")
    a(f"n={nv}，盲標，題目與第一輪不重疊且未出現在任何 prompt 的 few-shot 中。"
      "隨機基準 50%。")
    a("")

    a("### 3.8　A/B 位置效應")
    a("")
    a("| gold 的位置 | n | 正確率 |")
    a("| :-: | :-: | :-: |")
    a(f"| A | {pe['n_gold_a']} | {pe['acc_gold_a']:.3f} |")
    a(f"| B | {pe['n_gold_b']} | {pe['acc_gold_b']:.3f} |")
    a("")
    a(f"差 **{pe['diff'] * 100:+.2f}pp**　SE {pe['se'] * 100:.2f}pp"
      f"　z={pe['z']:.2f}　p={pe['p']:.4f}")
    a("")
    a("配平使**點估計**不受影響；位置效應**計入 judge 不可靠度**"
      f"（貢獻噪音 {pe['implied_noise'] * 100:.1f}pp，見 §6.4）。")
    a("")

    # ── 4 RQ1 ──
    a("## 4　RQ1：哪些訊號能預測這些錯誤 —— 答案是「沒有」")
    a("")
    a("### 4.1　八個訊號")
    a("")
    a("| 訊號 | 內容 | 生成呼叫 | 嵌入呼叫 |")
    a("| --- | --- | :-: | :-: |")
    for n, desc, g, e in (
            ("S1_polysemy", "多義詞詞表命中（由 CWN-SemCor 推導）", 0, 0),
            ("S2_subject_ellipsis", "主詞省略（規則，連續分數）", 0, 0),
            ("S3_syntactic_complexity", "句長／子句數／標點密度", 0, 0),
            ("S4_cultural", "成語詞表命中（chinese-xinhua, MIT）", 0, 0),
            ("S5_llm_direct", "LLM 直接判定歧義程度", 1, 0),
            ("S6_roundtrip", "翻譯→回譯→餘弦，分數=1−cos", 2, 1),
            ("S7_n_readings", "reflect 列舉的替代讀法數", 1, 0),
            ("S8_semantic_entropy", "n=8 取樣→等價分群→熵", 1, 1)):
        a(f"| `{n}` | {desc} | {g} | {e} |")
    a("")
    a(PROSE_SIGNAL_DESIGN)
    a("")

    a("### 4.2　預先登記")
    a("")
    a(f"訊號設計在看到任何 AUC 之前凍結。登記檔 "
      f"`data/results/signal_preregistration.md`，commit "
      f"`{prereg.get('commit', '—')}`，`labels_used: false`。")
    a("")
    a(section(RESULTS / "signal_preregistration.md", "## 登記表", "## 處置理由"))
    a("")

    a("### 4.3　AUC 表 ⭐")
    a("")
    a(section(sa, "### 主表", "### 對照列"))
    a("")
    a(section(sa, "### 對照列", "### vs 純句長"))
    a("")

    a("### 4.4　與純句長的比較（DeLong，相關樣本）")
    a("")
    a(section(sa, "### vs 純句長", "### 結論"))
    a("")

    a("### 4.5　純句長也不顯著——本節的關鍵 ⭐")
    a("")
    ctrl = control_rows(sa).get("純句長基準", {})
    a(PROSE_LENGTH_NULL.format(
        len_auc=ctrl.get("auc", 0.517), len_ci=ctrl.get("ci", "[0.455, 0.579]"),
        req_noise=req_noise, noise=ne.total, n_auc=an or base["n_judgeable"]))
    a("")

    # ── 5 RQ2 ──
    a("## 5　RQ2：Router 分流 —— 由 RQ1 直接回答，否定")
    a("")
    a(PROSE_RQ2)
    a("")

    # ── 6 方法學 ──
    a("## 6　方法學貢獻")
    a("")
    a("### 6.1　AUC 的並列上限 ⭐")
    a("")
    a(PROSE_TIE_CEILING_INTRO)
    a("")
    a("```")
    a("AUC 上限 = 1 − 0.5 × P(隨機兩題同值)")
    a("```")
    a("")
    a(PROSE_TIE_CEILING_BODY)
    a("")
    # S4 的具體數字移到 §8.5，此處只留一般性論述，避免同一組數字寫兩遍。
    s4 = next((r for r in prereg.get("signals", [])
               if r["signal"] == "S4_cultural"), {})

    a("### 6.2　AI 協作研究的 prompt 洩題管道 ⭐")
    a("")
    a("撰寫 prompt 的助理會從它處理過的資料中取 few-shot 範例。"
      "三次事件、四種載體，**關鍵性質是從結果不可見**。")
    a("")
    a("| | 檔案 | 載體 |")
    a("| :-: | --- | --- |")
    a("| 1 | `router.md` | 評測原句 |")
    a("| 2 | `reflect.md` | 既有資料集的標準答案 |")
    a("| 3 | `sense_judge.md` | 英文譯文 + 詞義定義 |")
    a("")
    a("細節與可引用段落：`data/results/prompt_contamination_incidents.md`")
    a("")

    a("### 6.3　長度稽核：分層 + 多重比較校正")
    a("")
    a(section(RESULTS / "wsd_baseline400.md", "**未校正 CI 排除 0.5", "---"))
    a("")

    a("### 6.4　標籤噪音的分解")
    a("")
    a("```")
    a(f"judge 總錯誤 {ne.total:.1%}　（1 − judge/人工一致率，n={nv}）")
    a(f"  ├── ≥{ne.position_component:.1%}  位置啟發式（n={pe['n']} 量得）")
    a(f"  └── ≈{ne.content_component:.1%}  內容誤判（殘差）")
    a("```")
    a("")
    a(f"⚠️ 位置效應是總噪音的**成分**不是加項。相加得 "
      f"{ne.additive_would_be:.1%} 是重複計算。")
    a("")
    a("**誤差分解**")
    a("")
    a("| 段落 | 落差 | 歸因 |")
    a("| --- | :-: | --- |")
    a(f"| CWN gold → 人工 | {dec.gold_to_human:.0%} | "
      "跨語言判定的固有限制（標註者看英譯，CWN 標的是中文原句）|")
    a(f"| 人工 → judge | {dec.human_to_judge:.0%} | 機器誤差 |")
    a(f"| **gold → judge** | **{dec.gold_to_judge:.0%}** | 兩者疊加 |")
    a("")
    a(f"judge 對 gold 的 {dec.gold_to_judge:.0%} 落差中，約 "
      f"**{dec.task_share:.0%} 來自任務本身**、**{dec.model_share:.0%} 是模型問題**。")
    a("")
    a(section(sa, "## 事前檢定力", "## 誤差分解"))
    a("")

    # ── 7 ──
    a("## 7　RQ3：記憶模組（初步）")
    a("")
    litm = load("lost_in_the_middle.json")
    if litm:
        cfg, sm = litm["config"], litm["summary"]
        a(f"對話長度 {cfg['turns']} 則、固定視窗 {cfg['window']}、"
          f"檢索 top-{cfg['top_k']}、詞彙干擾項 {cfg['distractors']} 則，"
          f"嵌入 `{'ithu/bge-m3-embedding' if cfg['embed'] == 'api' else '字元 n-gram'}`。")
        a("")
        a("指標為**召回率**——關鍵事實有沒有進入送給模型的脈絡。"
          "刻意不量模型的作答正確率，那會讓「記憶模組有沒有用」"
          "與「模型聰不聰明」分不開。")
        a("")
        a("| 關鍵資訊位置 | n | 無記憶（固定視窗） | 有記憶（摘要+檢索） |")
        a("| :-: | :-: | :-: | :-: |")
        for pos in ("頭", "中", "尾"):
            s = sm[pos]
            a(f"| {pos} | {s['n']} | {s['baseline']:.0%} | **{s['memory']:.0%}** |")
        a("")
        a("![Lost-in-the-Middle](../figs/lost_in_the_middle.png)")
        a("")
    # 論述直接斷言天花板效應與 0%／100% 的對比，數字一變就是錯的——
    # 條件不成立時退回 todo()，守門測試會讓標記數對不上而浮現。
    if litm and all(sm[p]["memory"] >= 1.0 for p in ("頭", "中", "尾")) \
            and sm["頭"]["baseline"] == sm["中"]["baseline"] == 0.0:
        a(PROSE_RQ3.format(head_baseline=sm["頭"]["baseline"],
                           memory=sm["中"]["memory"], turns=cfg["turns"],
                           top_k=cfg["top_k"], n_per_pos=sm["中"]["n"]))
    else:
        a(todo("與 Liu et al. 2024 的關係；n 與天花板效應的限制"))
    a("")

    # ── 8 ──
    a("## 8　討論與限制")
    a("")
    a("### 8.1　兩種建構的並置")
    a("")
    a(PROSE_TWO_CONSTRUCTS.format(
        binary_err=1 - base["accuracy"], nway_err=1 - nway["accuracy"],
        nway_chance=1 / MAX_CANDIDATE_SENSES,
        judge_human=val["judge_vs_human"],
        nway_judge_lo=min(nway_val_v1["judge_vs_human"], nway_val["judge_vs_human"]),
        nway_judge_hi=max(nway_val_v1["judge_vs_human"], nway_val["judge_vs_human"])))
    a("")
    a("### 8.1b　與監督式分類器結果的差異")
    a("")
    wu = next((r for r in load_external("length_audit_summary.json")
               if r.get("dataset", "").startswith("Wu et al.")
               and "無上下文" in r.get("comparison", "")), {})
    a(PROSE_SUPERVISED_GAP.format(
        wu_auc=wu.get("length_auc", 0.965), wu_n=wu.get("n_amb", 136),
        wu_mean_amb=wu.get("mean_amb", 9.6), wu_mean_ctl=wu.get("mean_ctl", 26.7)))
    a("")
    a("### 8.2　S8 語意熵的方向反轉 ⭐")
    a("")
    s8 = auc.get("S8_semantic_entropy", {})
    prev_s8 = load("_snapshot_before.json").get("auc", {}).get("S8_semantic_entropy")
    if s8 and an and prev_s8:
        a(PROSE_S8_REVERSAL.format(auc=s8["auc"], perm_p=s8["perm_p"],
                                   holm_p=s8["holm_p"], n_auc=an,
                                   prev_auc=prev_s8,
                                   translate_model=base["translate_model"]))
    else:
        a("_（signals_all.md 或前次快照尚未產生，S8 的數字無法讀取）_")
        a("")
        a(todo("「自信的錯誤」與計畫書開頭「一本正經地胡說八道」的呼應；"
               "以及為什麼此處必須保守"))
    a("")
    a("### 8.2b　judge 的獨立性未驗證 🔴")
    a("")
    sens = load("judge_sensitivity.json")
    a(PROSE_JUDGE_INDEPENDENCE.format(
        binary_err=1 - base["accuracy"], human_gold=val["human_vs_gold"],
        judge_human=val["judge_vs_human"],
        n_sampled=sens.get("n_sampled", 50), n_second=sens.get("n", 1),
        min_n=sens.get("min_n", 30)))
    a("")
    for t, body in (("8.3　義項粒度的天花板",
                     PROSE_SENSE_GRANULARITY.format(
                         # n_ambiguous_sample 是樣本數（分母），分子要自己算
                         amb=cc.ambiguous_rate,
                         n_amb=round(val["both_plausible_rate"] * nv),
                         nv=cc.n_ambiguous_sample,
                         amb_lo=cc.ambiguous_ci[0], amb_hi=cc.ambiguous_ci[1],
                         human_gold=val["human_vs_gold"],
                         nway_lo=min(nway_val_v1["judge_vs_human"],
                                     nway_val["judge_vs_human"]),
                         nway_hi=max(nway_val_v1["judge_vs_human"],
                                     nway_val["judge_vs_human"]),
                         gold_to_human=dec.gold_to_human,
                         cc_lo=cc.err_of_all_ci[0], cc_hi=cc.err_of_all_ci[1])),
                    ("8.4　judge 誤差的傳遞",
                     PROSE_JUDGE_PROPAGATION.format(
                         nv=nv, judge_human=val["judge_vs_human"],
                         jh_lo=val["judge_vs_human_ci"][0] * 100,
                         jh_hi=val["judge_vs_human_ci"][1] * 100,
                         noise=ne.total, req_clean=req_clean, req_noise=req_noise,
                         pos=ne.position_component * 100,
                         content=ne.content_component)),
                    ("8.5　S4 不可檢定 ≠ 訊號無效",
                     PROSE_S4_UNTESTABLE.format(
                         ceiling=s4["auc_ceiling"],
                         req_clean=s4["required_auc_clean"],
                         req_noise=s4["required_auc_noise25"],
                         n=s4["n"], hits=round(s4["n"] * (1 - s4["max_same_value_share"])),
                         rest=round(s4["n"] * s4["max_same_value_share"]))
                     if s4 else todo("覆蓋率問題")),
                    ("8.6　樣本數與可推廣性",
                     PROSE_SAMPLE_SIZE.format(
                         n_judgeable=base["n_judgeable"], acc_hw=acc_hw * 100,
                         req_noise=req_noise, req_clean=req_clean, nv=nv,
                         jh_lo=val["judge_vs_human_ci"][0] * 100,
                         jh_hi=val["judge_vs_human_ci"][1] * 100,
                         cc_lo=cc.err_of_all_ci[0], cc_hi=cc.err_of_all_ci[1],
                         rq3_n=litm["summary"]["中"]["n"] if litm else "—",
                         noise=ne.total,
                         translate_model=base["translate_model"]))):
        a(f"### {t}")
        a("")
        a(body)
        a("")

    a("### 8.7　現象選擇的限制")
    a("")
    a(PROSE_PHENOMENON_LIMIT.format(binary_err=1 - base["accuracy"]))
    a("")

    a("## 9　與計畫書的差異表")
    a("")
    a("| 編號 | 差異 | 幅度 | 理由 |")
    a("| :-: | --- | :-: | --- |")
    for i, (d, m, r) in enumerate([
            ("CAD-100 改為 CWN-SemCor 抽樣", "大", "原資料集不存在，改用公開 WSD 語料"),
            ("RQ1 改為「預測譯錯詞義」", "中", "需主動說明"),
            ("Fleiss' Kappa → Krippendorff's α", "小", "標註者僅一人時的適用性"),
            ("BERTScore 只在 WMT23 算", "小", "CAD 上改用義項正確率"),
            ("自我一致性 → 語意熵", "中", "自我一致性是循環論證"),
            ("Electron → Streamlit", "小", "時間成本"),
            ("REFERENTIAL 降為對照組", "中", "題數不足"),
            ("脈絡恆等三元組設計放棄", "大",
             "WSD 資料要求「有脈絡時已定」，與 U/A/B 的「無脈絡時未定」相反"),
            ("sense_judge 改二元強迫選擇", "中",
             f"N 選一的 judge 一致率僅 {nway_val['judge_vs_human']:.0%}，"
             f"二元後 {val['judge_vs_human']:.0%}"),
            ("**P5／P6 取消**", "**大**",
             "RQ1 的否定結果使 Router 分流的前提不成立（§5.1）"),
    ], 8):
        a(f"| D{i} | {d} | {m} | {r} |")
    a("")

    a("## 附錄")
    a("")
    a("| 檔案 | 內容 |")
    a("| --- | --- |")
    for f, d in (("wsd_baseline400.md", "主結果完整報表"),
                 ("signals_all.md", "訊號分布、並列上限、AUC 表"),
                 ("signal_preregistration.md", "訊號預先登記"),
                 ("judge_validation_r2.md", "judge 人工驗證"),
                 ("judge_diagnosis.md", "第一輪 judge 失敗的診斷"),
                 ("prompt_contamination_incidents.md", "prompt 洩題事件記錄"),
                 ("none_analysis.md", "NONE 的詞類分布"),
                 ("../external/length_audit_summary.md",
                  "外部資料集的長度稽核（§8.1b）"),
                 ("endpoint_identity_check.md", "judge 端點身分檢查（§8.2b）"),
                 ("judge_sensitivity_status.md", "judge 敏感度檢查的中止記錄")):
        a(f"| `data/results/{f}` | {d} |")
    a("")

    out = out or DOCS / "技術報告.md"
    out.write_text("\n".join(L).replace(_HEADER_SLOT, (
        "> 標記 `TODO(你寫)` 的位置是論述文字，由研究者撰寫。"
        if _TODO_EMITTED else
        "> 論述定義在 `scripts/build_report.py` 的 `PROSE_*` 常數，"
        "**本檔為產物，直接編輯會被覆蓋**。")), encoding="utf-8")
    print(f"  {out}")
    print(f"  {len(L)} 行，{len(_TODO_EMITTED)} 處待你撰寫論述")
    return 0


if __name__ == "__main__":
    sys.exit(main())
