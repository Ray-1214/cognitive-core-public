"""MT 詞義錯誤基準：翻譯 → judge 判義項 → 比對 CWN gold。

DiBiMT / MuCoW 一系的範式。取代原本的 U/A/B 脈絡恆等設計——後者需要
「無脈絡時未定」的題目，而 WSD 資料集提供的是「有脈絡時已定」的題目。
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from ..assets import prompt
from ..llm import Client, LLMError

# 譯文中文字元比例超過此值即視為未翻譯。
# 粗跑時 81% 的譯文仍是中文，那是要報告的數字不是要藏的錯誤。
CJK_FAIL_RATIO = 0.30

TRANSLATE_SYS = ("Translate the Chinese sentence into English. "
                 "Output only the English translation. "
                 "No explanation, no notes, no Chinese characters.")

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "choice": {"type": "string", "enum": ["A", "B", "NONE"]},
        "confidence": {"type": "number"},
        "reasoning_summary": {"type": "string"},
    },
    "required": ["choice", "confidence", "reasoning_summary"],
    "additionalProperties": False,
}


def pick_distractor(item: dict) -> dict | None:
    """同 lemma 中**最高頻的非 gold 義項**——最易混淆的干擾項。

    ⚠️ 選法寫死在這裡：不由模型選，也不隨機。
    模型選會讓難度隨模型變動；隨機會讓每次跑的難度不一致，
    兩者都使跨次比較失去意義。

    tie-break 用 sense_id 遞增，確保與 yaml 的排序無關也可重現。
    """
    cands = [s for s in item["competing_senses"]
             if s["sense_id"] != item["gold_sense_id"]]
    if not cands:
        return None
    return sorted(cands, key=lambda s: (-s.get("corpus_count", 0), s["sense_id"]))[0]


def gold_goes_first(index_within_stratum: int) -> bool:
    """A/B 位置配平：分層內逐題交替。

    ⚠️ 不可用 hash 決定——雜湊是隨機不是配平，先前實測 60 筆分到 23/37。
    交替可保證任何前綴的失衡都 ≤1。
    """
    return index_within_stratum % 2 == 0


def judge_sense_binary(client: Client, word: str, translation: str,
                       def_a: str, def_b: str, *, role: str = "judge") -> dict:
    """二元強迫選擇。**本函式不知道哪個是 gold**——呼叫端負責配平與還原。"""
    body = prompt("sense_judge").render(
        target_word=word, translation=translation, def_a=def_a, def_b=def_b)

    def validator(obj: dict) -> dict:
        ch = str(obj.get("choice", "")).strip().upper()
        if ch not in ("A", "B", "NONE"):
            # 非法回覆降級為 NONE 並留痕，不可靜默當成某一邊
            obj = {**obj, "choice": "NONE", "invalid_choice_returned": ch}
        else:
            obj["choice"] = ch
        try:
            obj["confidence"] = min(max(float(obj.get("confidence", 0.0)), 0.0), 1.0)
        except (TypeError, ValueError):
            obj["confidence"] = 0.0
        return obj

    obj, tier = client.structured(role, [{"role": "user", "content": body}],
                                  JUDGE_SCHEMA, validator=validator, max_tokens=400)
    obj["_tier"] = tier
    return obj


def cjk_ratio(text: str) -> float:
    if not text:
        return 1.0
    cjk = sum(1 for c in text if "一" <= c <= "鿿")
    return cjk / len(text)


def translate(client: Client, sentence: str, *, role: str = "translate") -> str:
    return client.text(role, [{"role": "system", "content": TRANSLATE_SYS},
                              {"role": "user", "content": sentence}],
                       temperature=0.0, max_tokens=400)


def judge_sense(client: Client, word: str, translation: str,
                senses: list[dict], *, role: str = "judge") -> dict:
    sense_list = "\n".join(f"- `{s['sense_id']}` {s['definition']}" for s in senses)
    body = prompt("sense_judge").render(
        target_word=word, translation=translation, sense_list=sense_list)
    valid = {s["sense_id"] for s in senses} | {"NONE"}

    def validator(obj: dict) -> dict:
        sid = str(obj.get("chosen_sense_id", "")).strip()
        if sid not in valid:
            # 清單外的 id 一律降級為 NONE 並留痕，不可靜默接受
            obj = {**obj, "chosen_sense_id": "NONE", "invalid_id_returned": sid}
        try:
            obj["confidence"] = min(max(float(obj.get("confidence", 0.0)), 0.0), 1.0)
        except (TypeError, ValueError):
            obj["confidence"] = 0.0
        return obj

    obj, tier = client.structured(role, [{"role": "user", "content": body}],
                                  JUDGE_SCHEMA, validator=validator, max_tokens=400)
    obj["_tier"] = tier
    return obj


NONE_CAUSE_SYS = (
    "You judge whether an English translation renders a specific Chinese word.\n"
    'Answer with JSON only: {"rendered": true|false, "evidence": "<=20 chars"}\n'
    '"rendered" is true if ANY word or phrase in the English translation '
    "expresses the meaning of the Chinese word (not necessarily literally). "
    "It is false if the translation omits that word entirely or paraphrases the "
    "sentence in a way that drops it.")

NONE_CAUSE_SCHEMA = {
    "type": "object",
    "properties": {"rendered": {"type": "boolean"},
                   "evidence": {"type": "string"}},
    "required": ["rendered", "evidence"],
    "additionalProperties": False,
}


def classify_none(client: Client, word: str, sentence: str, translation: str,
                  *, role: str = "judge") -> dict:
    """判 NONE 的成因：譯文是否根本沒譯出該詞。

    30 筆時 NONE 佔 20%，但實例顯示 NONE 有時是對的
    （「皮皮掉到山谷後居然沒死」→ survived，譯文確實沒有「死」）。
    分兩類才知道 20% 是特性還是缺陷：
      rendered=False → 譯文沒譯出該詞，NONE 正確
      rendered=True  → 譯文有譯出但 judge 認不出來，NONE 是 judge 的問題
    """
    body = (f"Chinese word: {word}\n"
            f"Chinese sentence: {sentence}\n"
            f"English translation: {translation}")
    obj, _ = client.structured(role, [{"role": "system", "content": NONE_CAUSE_SYS},
                                      {"role": "user", "content": body}],
                               NONE_CAUSE_SCHEMA, max_tokens=200)
    return obj


@dataclass
class Outcome:
    probe_id: str
    stratum: str
    word: str
    sentence: str
    gold: str
    translation: str = ""
    chosen: str | None = None
    confidence: float = 0.0
    reasoning: str = ""
    translation_failed: bool = False
    error: str | None = None
    # NONE 成因（僅 NONE 案例）
    none_rendered: bool | None = None
    none_evidence: str = ""
    # 錯誤時模型選中的義項在語料庫中的頻率排名（1 = 最高頻）
    chosen_rank: int | None = None
    n_candidates: int = 0
    # 事後分層分析用（詞類、gold 的頻率排名）
    pos: str = ""
    gold_rank: int | None = None
    # 二元強迫選擇（v3 judge）
    distractor: str | None = None      # 干擾項的 sense_id
    distractor_rank: int | None = None
    gold_first: bool | None = None     # gold 是否被放在 A 位（配平用）
    raw_choice: str = ""               # judge 原始回覆 A / B / NONE

    @property
    def judgeable(self) -> bool:
        return (not self.translation_failed and self.error is None
                and self.chosen is not None)

    @property
    def is_none(self) -> bool:
        return self.chosen == "NONE"

    @property
    def correct(self) -> bool | None:
        """None 代表不可判定（翻譯失敗、錯誤、或 judge 回 NONE），不計入正確率。"""
        if not self.judgeable or self.is_none:
            return None
        return self.chosen == self.gold


def run_one(client: Client, item: dict, *, translate_only: bool = False,
            index_within_stratum: int = 0) -> Outcome:
    """跑一題。`translate_only` 只做翻譯（譯文會進快取，之後補 judge 不需重譯）。

    judge 走二元強迫選擇：gold vs 最高頻非 gold 干擾項。
    `index_within_stratum` 決定 gold 放 A 位還是 B 位（分層內交替配平）。
    """
    o = Outcome(probe_id=item["id"], stratum=item["stratum"],
                word=item["target_word"], sentence=item["sentence"],
                gold=item["gold_sense_id"],
                pos=item.get("target_pos", ""),
                gold_rank=item.get("gold_rank"))
    try:
        o.translation = translate(client, item["sentence"])
    except LLMError as e:
        o.error = f"translate: {str(e)[:160]}"
        return o
    if cjk_ratio(o.translation) > CJK_FAIL_RATIO:
        o.translation_failed = True
        return o          # 不送進 judge——判中文沒有意義
    if translate_only:
        o.error = "judge_skipped"
        return o
    senses = item["competing_senses"]
    o.n_candidates = 2                        # 二元強迫選擇
    dis = pick_distractor(item)
    if dis is None:
        o.error = "no_distractor"             # 該詞只有一個義項，題目無效
        return o
    o.distractor = dis["sense_id"]
    gold_def = item["gold_definition"]
    o.gold_first = gold_goes_first(index_within_stratum)
    def_a, def_b = ((gold_def, dis["definition"]) if o.gold_first
                    else (dis["definition"], gold_def))
    try:
        j = judge_sense_binary(client, item["target_word"], o.translation,
                               def_a, def_b)
        o.raw_choice = j["choice"]
        o.confidence = j["confidence"]
        o.reasoning = j.get("reasoning_summary", "")
    except LLMError as e:
        o.error = f"judge: {str(e)[:160]}"
        return o

    # 把 A/B 還原成 sense_id
    if o.raw_choice == "NONE":
        o.chosen = "NONE"
    elif (o.raw_choice == "A") == bool(o.gold_first):
        o.chosen = o.gold
    else:
        o.chosen = o.distractor

    # 選中義項的頻率排名（候選已依語料庫頻率遞減排序）
    if o.chosen and o.chosen != "NONE":
        for k, s in enumerate(senses, 1):
            if s["sense_id"] == o.chosen:
                o.chosen_rank = k
            if s["sense_id"] == o.distractor:
                o.distractor_rank = k
    if o.chosen == "NONE":
        try:
            c = classify_none(client, item["target_word"], item["sentence"],
                              o.translation)
            o.none_rendered = bool(c.get("rendered"))
            o.none_evidence = str(c.get("evidence", ""))[:40]
        except LLMError:
            pass          # 成因分類失敗不影響主結果
    return o


# ─────────────────── 統計 ───────────────────

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 區間。比常態近似在小 n 與極端比例下穩健。"""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    # 夾在 [0,1]：k=0 或 k=n 時浮點誤差會給出 -1e-17，報表會印成「-0%」
    return (min(max((c - s) / d, 0.0), 1.0), min(max((c + s) / d, 0.0), 1.0))


def paired_bootstrap_diff(a_flags: list[bool], b_flags: list[bool], *,
                          n_boot: int = 10000, seed: int = 20260818
                          ) -> tuple[float, tuple[float, float], float]:
    """兩組正確率之差的拔靴 CI 與雙尾 p。兩組為獨立樣本（不同題目），
    故對各組分別重抽——非配對，因為題目不重疊。"""
    import random

    if not a_flags or not b_flags:
        return (float("nan"), (float("nan"), float("nan")), float("nan"))
    rng = random.Random(seed)
    obs = sum(a_flags) / len(a_flags) - sum(b_flags) / len(b_flags)
    diffs = []
    for _ in range(n_boot):
        ra = [a_flags[rng.randrange(len(a_flags))] for _ in a_flags]
        rb = [b_flags[rng.randrange(len(b_flags))] for _ in b_flags]
        diffs.append(sum(ra) / len(ra) - sum(rb) / len(rb))
    diffs.sort()
    lo = diffs[int(0.025 * n_boot)]
    hi = diffs[int(0.975 * n_boot)]
    # 雙尾 p：以 0 為虛無，看有多少重抽差值落在觀測值的另一側
    n_cross = sum(1 for d in diffs if (d <= 0) if obs > 0) or \
        sum(1 for d in diffs if (d >= 0) if obs < 0)
    p = min(1.0, 2 * n_cross / n_boot) if obs != 0 else 1.0
    return obs, (lo, hi), p


@dataclass
class Summary:
    n_total: int
    n_translation_failed: int
    n_error: int
    n_none: int
    n_judgeable: int
    n_correct: int
    by_stratum: dict = field(default_factory=dict)

    @property
    def accuracy(self) -> float:
        return self.n_correct / self.n_judgeable if self.n_judgeable else float("nan")


def dominant_bias(outcomes: list[Outcome]) -> dict:
    """錯誤時模型是否偏向最高頻義項（與 CHA-Gen「偏好主流解讀」的銜接）。

    隨機基準：若模型隨機選，選中最高頻義項的機率是 1/候選數，
    對所有錯誤題目取平均即為期望值。實際比例顯著高於它，
    就是「偏好主流解讀」在脈絡層級的證據。

    ⚠️ **二元強迫選擇下這個指標會退化，本函式會拒絕計算。**

    二元設計中干擾項恆為「同 lemma 中最高頻的非 gold 義項」，於是：
      主流層（gold 是第 1 名）  → 干擾項是第 2 名，答錯 ≠ 選到最高頻
      非主流層（gold 非第 1 名）→ 干擾項就是第 1 名，答錯 = 選到最高頻
    「錯誤中選到最高頻的比例」因此等於「錯誤有多少落在非主流層」，
    是抽樣設計的產物而不是模型偏好。隨機基準也退化成 0.5。

    二元設計下同一個研究問題由**兩層正確率之差**回答：
    若模型偏好高頻義項，非主流層的錯誤率應系統性較高。
    """
    wrong = [o for o in outcomes if o.correct is False and o.chosen_rank]
    if not wrong:
        return {"n": 0}
    if all(o.n_candidates == 2 for o in wrong):
        return {"n": len(wrong), "not_applicable": True,
                "reason": "二元強迫選擇下本指標退化為「錯誤落在非主流層的比例」，"
                          "是抽樣設計的產物。該研究問題改由兩層正確率之差回答。",
                "see": "by_stratum / diff"}
    picked_top = sum(1 for o in wrong if o.chosen_rank == 1)
    expected = sum(1.0 / o.n_candidates for o in wrong if o.n_candidates) / len(wrong)
    lo, hi = wilson_ci(picked_top, len(wrong))
    return {"n": len(wrong), "picked_top": picked_top,
            "rate": picked_top / len(wrong), "ci": (lo, hi),
            "random_baseline": expected,
            "exceeds_random": lo > expected,
            "rank_hist": {k: sum(1 for o in wrong if o.chosen_rank == k)
                          for k in sorted({o.chosen_rank for o in wrong})}}


def position_effect(outcomes: list[Outcome]) -> dict:
    """A/B 位置對正確率的影響，並換算成它貢獻多少**標籤噪音**。

    二元強迫選擇會有位置啟發式。配平（分層內交替）讓**點估計**不受影響——
    gold 在 A 與在 B 的題數各半，偏誤相互抵銷。但它不會讓變異數消失：
    受位置驅動的那些判定與譯文內容無關，就是噪音。

    ## 換算模型

    設 judge 以機率 `q` 直接依位置作答（不看內容），其餘 `1−q` 依內容判斷：

        gold 在 A：正確率 = q·1 + (1−q)·a
        gold 在 B：正確率 = q·0 + (1−q)·a
        兩者之差 = q

    配平下位置驅動的判定有一半落在錯的那邊，故它對標籤錯誤率的貢獻是
    **q/2**。這是 judge 不可靠度的**下界**——內容判斷本身還會再錯。

    `implied_noise` 應餵給 `auc.required_auc(noise=…)`：
    在人工驗證回來之前，它是唯一有實證基礎的噪音估計。
    """
    ab = [o for o in outcomes if o.raw_choice in ("A", "B") and o.correct is not None]
    ga = [o for o in ab if o.gold_first]
    gb = [o for o in ab if not o.gold_first]
    if len(ga) < 2 or len(gb) < 2:
        return {"n": len(ab), "available": False}
    n1, n2 = len(ga), len(gb)
    p1 = sum(1 for o in ga if o.correct) / n1
    p2 = sum(1 for o in gb if o.correct) / n2
    diff = p1 - p2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z = diff / se if se > 0 else float("nan")
    p = (2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
         if se > 0 else float("nan"))
    n_a = sum(1 for o in ab if o.raw_choice == "A")
    alo, ahi = wilson_ci(n_a, len(ab))
    return {
        "n": len(ab), "available": True,
        "n_gold_a": n1, "n_gold_b": n2,
        "acc_gold_a": p1, "acc_gold_b": p2,
        "diff": diff, "se": se, "z": z, "p": p,
        "diff_ci": (diff - 1.96 * se, diff + 1.96 * se),
        "chose_a": n_a, "chose_a_rate": n_a / len(ab), "chose_a_ci": (alo, ahi),
        "chose_a_biased": not (alo <= 0.5 <= ahi),
        # 位置驅動的判定有一半落在錯的那邊
        "implied_noise": max(diff, 0.0) / 2,
        "implied_noise_ci": (max(diff - 1.96 * se, 0.0) / 2,
                             max(diff + 1.96 * se, 0.0) / 2),
    }


def none_breakdown(outcomes: list[Outcome]) -> dict:
    nones = [o for o in outcomes if o.is_none]
    classified = [o for o in nones if o.none_rendered is not None]
    not_rendered = [o for o in classified if o.none_rendered is False]
    rendered = [o for o in classified if o.none_rendered is True]
    return {"n_none": len(nones), "n_classified": len(classified),
            "not_rendered": len(not_rendered),   # NONE 正確
            "rendered": len(rendered),           # judge 的問題
            "unclassified": len(nones) - len(classified)}


def summarise(outcomes: list[Outcome]) -> Summary:
    judgeable = [o for o in outcomes if o.correct is not None]
    s = Summary(
        n_total=len(outcomes),
        n_translation_failed=sum(1 for o in outcomes if o.translation_failed),
        n_error=sum(1 for o in outcomes if o.error),
        n_none=sum(1 for o in outcomes if o.is_none),
        n_judgeable=len(judgeable),
        n_correct=sum(1 for o in judgeable if o.correct))
    for st in ("dominant", "non_dominant"):
        sub = [o for o in judgeable if o.stratum == st]
        k = sum(1 for o in sub if o.correct)
        s.by_stratum[st] = {"n": len(sub), "correct": k,
                            "acc": k / len(sub) if sub else float("nan"),
                            "ci": wilson_ci(k, len(sub))}
    return s
