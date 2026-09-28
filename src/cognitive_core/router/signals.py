"""偵測訊號 S1–S4：純規則，不呼叫 API（v3 架構書 §P4）。

統一介面 `signal(text) -> float in [0,1]`。

⚠️ **S3 與長度基準幾乎是同一個東西**（見 `SyntacticComplexity` 的說明）。
報告時必須把 S3 與純句長基準並列——若兩者 AUC 相近，S3 就不是獨立訊號，
而是長度的代理。這不是可選的補充分析，是 S3 能否被當作訊號的前提。

詞表來源見 `data/lexicons/README.md`。未使用 LLM 生成任何詞表。
"""

from __future__ import annotations

import functools
import json
import pathlib
import re
from dataclasses import dataclass

LEX = pathlib.Path(__file__).resolve().parents[3] / "data" / "lexicons"

CLAUSE_PUNCT = "，。；！？、：．﹒‧﹖…"
ALL_PUNCT = CLAUSE_PUNCT + "「」『』（）《》〔〕—－／％"

# 中文常見的主詞省略脈絡：句首直接是動詞或副詞＋動詞，且無人稱代名詞／專名
PRONOUNS = "我你他她它我們你們他們她們牠祂咱您諸位大家"
# 常見的話題標記與連詞，出現在句首時後方常省略主詞
TOPIC_MARKERS = ("因為", "所以", "但是", "可是", "然而", "而且", "並且",
                 "如果", "雖然", "既然", "為了", "由於", "於是", "接著",
                 "後來", "然後", "不過", "只要", "只是", "此外")

# 常接在主詞之後的功能詞與謂語標記。用途：估計前置名詞組的長度——
# 標記出現得越晚，主詞越可能是顯性的名詞組而非被省略。
# ⚠️ 這是無斷詞、無句法的粗略近似，只用來排序不用來斷言句法結構。
PRED_MARKERS = "是在有會將被把也都就已正可要能不沒於為和與對向從使讓等所以"


@dataclass(frozen=True)
class SignalResult:
    name: str
    score: float
    detail: dict


class Signal:
    name = "base"

    def __call__(self, text: str) -> float:
        return self.compute(text).score

    def compute(self, text: str) -> SignalResult:  # pragma: no cover
        raise NotImplementedError

    @staticmethod
    def _clamp(v: float) -> float:
        return min(max(float(v), 0.0), 1.0)


# ─────────────────── S1 歧義詞典命中 ───────────────────

@functools.lru_cache(maxsize=1)
def _polysemous() -> dict[str, dict]:
    p = LEX / "polysemous.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))["entries"]


class PolysemyHit(Signal):
    """S1：句中出現多義詞的程度。

    以同 lemma（同讀音）的義項數為權重——跨 lemma 的多義是同形異音詞，
    讀出來就消歧，不構成翻譯時的歧義。

    正規化：取句中最高的義項數，除以 SAT（飽和點）。

    ⚠️ **兩個已知弱點，都會壓低這個訊號的判別力，報告時須揭露**：

    1. **覆蓋率只有 113 個詞**（CWN-SemCor 的目標詞）。未收錄者計為 0，
       是保守方向（低估歧義）。
    2. **單字比對會誤命中詞素**。詞表中多為單字詞，而字串比對無法區分
       「橘子」的「子」（後綴詞素）與作為多義content word 的「子」。
       實測「蘋果橘子香蕉」得 0.533，高於「他昨天走了」的 0.333——
       兩者都是假命中。要修需要斷詞，而斷詞本身會引入新的誤差來源，
       故此處保留並揭露，不做工程修補。
    """

    name = "S1_polysemy"
    SAT = 30.0        # CWN-SemCor 中同 lemma 義項數的高分位

    def compute(self, text: str) -> SignalResult:
        tbl = _polysemous()
        hits = {w: tbl[w]["max_senses_in_one_lemma"] for w in tbl if w in text}
        if not hits:
            return SignalResult(self.name, 0.0, {"hits": {}, "max": 0})
        mx = max(hits.values())
        return SignalResult(self.name, self._clamp(mx / self.SAT),
                            {"hits": hits, "max": mx})


# ─────────────────── S2 主詞省略偵測 ───────────────────

class SubjectEllipsis(Signal):
    """S2：主詞省略的可能性（規則，不用依存句法）。

    中文零主詞在 OntoNotes V5.0 上佔 36%（英文 4%），是高語境特性的核心。

    ## v2：改為連續分數（2026-08-21）

    v1 對每個子句做二元判定（句首六字內有人稱 → 0，否則 → 1）再取比例。
    400 筆實測有 **79% 的題目拿到同一個值 1.0**，隨機兩題同值的機率 66%，
    使 AUC 的硬上限只有 **0.669**——與判別力無關，純粹是離散化造成的。

    但單純把「人稱的位置」連續化只把上限推到 0.687，因為問題不在離散化，
    而在規則本身錯了：**它把「沒有人稱代名詞」等同於「省略主詞」**。
    中文的主詞多半是名詞組不是代名詞，新聞語體尤其
    （「教育部在九月初以不符合師資培育法為由…」的主詞是「教育部」）。

    v2 因此加了第二個線索：**謂語標記出現的位置**。
    子句開頭到第一個常見謂語標記（是／在／有／會／將／被／把／也／都／就…）
    之間的字數，就是前置名詞組的長度估計；標記出現得越晚，越可能有顯性主詞。

    | 線索 | 對「有顯性主詞」的證據 |
    | --- | --- |
    | 句首即人稱代名詞 | 最強，隨位置遞減 |
    | 謂語標記出現得晚 | 前置名詞組長 → 有主詞 |
    | 兩者都沒有 | **0.5（無證據）**，見下 |
    | 句首是話題標記／連詞 | 反向證據，把上述打到 0.25 倍 |

    效果：相異值 5 → 24，最大同值 79% → 29%，**AUC 上限 0.669 → 0.924**。

    ⚠️ 「兩者都沒有」刻意給 0.5 而**不依子句長度分級**。用長度分級可以把
    上限再推高，但那會讓 S2 變成句長的代理，正是 §4 地雷 1 要避免的事。
    寧可留一塊 29% 的無資訊區。

    ⚠️ 改動時間點在**計算任何 AUC 之前**（AUC 閘門關閉中，見 `eval/gate.py`），
    且所依據的並列上限分析不使用標籤，因此不存在 outcome-dependent 的洩漏。
    這不是 p-hacking，但時間點與理由必須留在此處與
    `data/results/signal_preregistration.md`。

    ⚠️ 仍是粗略近似：沒有依存句法，會把無主句（天氣句、存現句）一併算進去。
    """

    name = "S2_subject_ellipsis"
    HEAD = 8               # 只看子句前 8 字——之後出現的線索多半與主詞無關
    PRED_SAT = 5.0         # 謂語標記出現在第 5 字之後即視為「前置名詞組夠長」
    MARKER_PENALTY = 0.25  # 句首話題標記使「有主詞」的證據再打折
    NO_EVIDENCE = 0.5      # 既無人稱也無謂語標記——誠實地給不確定值

    def _clause_score(self, c: str) -> float:
        """回傳該子句「省略主詞」的程度，0（明顯有主詞）到 1（明顯沒有）。"""
        head = c[:self.HEAD]
        pron = next((i for i, ch in enumerate(head) if ch in PRONOUNS), None)
        evidence = 0.0 if pron is None else 1.0 - pron / self.HEAD
        pred = next((i for i, ch in enumerate(head) if ch in PRED_MARKERS), None)
        if pred is not None:
            evidence = max(evidence, min(pred / self.PRED_SAT, 1.0))
        elif pron is None and len(c) >= 4:
            evidence = max(evidence, 1.0 - self.NO_EVIDENCE)
        if any(head.startswith(m) for m in TOPIC_MARKERS):
            evidence *= self.MARKER_PENALTY
        return 1.0 - evidence

    def compute(self, text: str) -> SignalResult:
        clauses = [c.strip() for c in re.split(f"[{CLAUSE_PUNCT}]", text) if c.strip()]
        if not clauses:
            return SignalResult(self.name, 0.0, {"clauses": 0})
        scores = [self._clause_score(c) for c in clauses]
        return SignalResult(self.name, self._clamp(sum(scores) / len(scores)),
                            {"clauses": len(clauses),
                             "clause_scores": [round(s, 3) for s in scores],
                             "no_evidence_clauses":
                                 sum(1 for s in scores
                                     if abs(s - self.NO_EVIDENCE) < 1e-9)})


# ─────────────────── S3 句法複雜度 ───────────────────

class SyntacticComplexity(Signal):
    """S3：句長、子句數、標點密度的合成。

    🔴 **這個訊號與純句長基準高度重疊。** 三個成分中句長直接是長度，
    子句數與標點密度也隨長度成長。報告時**必須**把 S3 的 AUC 與
    「只用句長」的 AUC 並列；若兩者相近，S3 就不是獨立訊號而是長度的代理，
    不得當作「本系統偵測到句法複雜度」的證據。

    `compute()` 的 detail 一併回傳純句長，方便並列比較。
    """

    name = "S3_syntactic_complexity"
    LEN_SAT = 40.0
    CLAUSE_SAT = 5.0

    def compute(self, text: str) -> SignalResult:
        n = len(text)
        clauses = [c for c in re.split(f"[{CLAUSE_PUNCT}]", text) if c.strip()]
        n_punct = sum(1 for c in text if c in ALL_PUNCT)
        len_s = min(n / self.LEN_SAT, 1.0)
        clause_s = min(len(clauses) / self.CLAUSE_SAT, 1.0)
        dens_s = min(n_punct / max(n, 1) * 10, 1.0)
        score = (len_s + clause_s + dens_s) / 3
        return SignalResult(self.name, self._clamp(score),
                            {"chars": n, "clauses": len(clauses),
                             "punct": n_punct,
                             "raw_length": n,          # 供與長度基準並列
                             "components": {"len": len_s, "clause": clause_s,
                                            "density": dens_s}})


# ─────────────────── S4 文化專有項 ───────────────────

@functools.lru_cache(maxsize=1)
def _idioms() -> frozenset[str]:
    p = LEX / "idioms.json"
    if not p.exists():
        return frozenset()
    return frozenset(json.loads(p.read_text(encoding="utf-8"))["entries"])


class CulturalItem(Signal):
    """S4：成語命中。

    ⚠️ 目前只有成語，**沒有流行語與委婉語詞表**——那兩類缺乏可引用的公開來源，
    自建又會變成 LLM 生成。這是覆蓋率上的已知缺口，未收錄者計為 0（保守）。

    只比對長度 3–8 的連續子字串，避免對長句做 O(n²) 的全掃描。
    """

    name = "S4_cultural"
    MIN, MAX = 3, 8

    def compute(self, text: str) -> SignalResult:
        idi = _idioms()
        if not idi:
            return SignalResult(self.name, 0.0, {"hits": []})
        found: list[str] = []
        for size in range(self.MIN, self.MAX + 1):
            for i in range(len(text) - size + 1):
                sub = text[i:i + size]
                if sub in idi:
                    found.append(sub)
        found = sorted(set(found), key=len, reverse=True)
        # 一句話有一個成語就已經是強訊號，兩個以上飽和
        return SignalResult(self.name, self._clamp(min(len(found), 2) / 2),
                            {"hits": found})


# ═══════════════ S5–S8：需要 API 的訊號 ═══════════════
#
# 統一介面仍是 `signal(text) -> float`——client 在建構時綁定，不進呼叫簽章。
# 這樣 S1–S8 可以放進同一個列表、跑同一套 AUC 流程。


class LLMSignal(Signal):
    """需要 API 的訊號。⚠️ 成本要記錄——§P4 的 DoD 要求每個訊號附平均成本。"""

    def __init__(self, client, role: str = "router"):
        self.client = client
        self.role = role

    def compute(self, text: str) -> SignalResult:  # pragma: no cover
        raise NotImplementedError


class LLMDirect(LLMSignal):
    """S5：直接問 LLM 這句話有多歧義（`prompts/router.md`）。

    ⚠️ 這同時是評測中的對照組。自我評估的判別力先前實測只有 AUC≈0.55，
    接近亂猜——它是否優於 S1–S4 的機械量測，是 RQ1 要回答的事情之一，
    不可預設它比較強。
    """

    name = "S5_llm_direct"

    def compute(self, text: str) -> SignalResult:
        from ..assets import prompt

        if not text.strip():
            return SignalResult(self.name, 0.0, {"raw": "", "parsed": False})
        sys_p = prompt("router").render()
        try:
            raw = self.client.text(
                self.role,
                [{"role": "system", "content": sys_p},
                 {"role": "user", "content": text}],
                max_tokens=16).strip()
        except Exception as e:  # noqa: BLE001
            return SignalResult(self.name, 0.0,
                                {"raw": "", "parsed": False, "error": str(e)[:120]})
        m = re.search(r"[01](?:\.\d+)?|\.\d+", raw)
        if not m:
            # 解析失敗計 0 並留痕，不可靜默當成 0.5
            return SignalResult(self.name, 0.0, {"raw": raw, "parsed": False})
        return SignalResult(self.name, self._clamp(float(m.group())),
                            {"raw": raw, "parsed": True})


class RoundTripFidelity(LLMSignal):
    """S6：單探針往返保真度——翻成英文再回譯，與原句比。

    分數 = 1 − cos(原句, 回譯)，即**不保真的程度**。
    方向要與其他訊號一致：分數高 = 比較可能出錯。

    ⚠️ 回譯不一致有兩個來源，這個訊號分不開：真的有歧義、或翻譯本身就爛。
    這是它的已知限制，報告時要寫。
    """

    name = "S6_roundtrip"

    def __init__(self, client, role: str = "translate",
                 back_role: str = "backtrans", embed_role: str = "embed"):
        super().__init__(client, role)
        self.back_role = back_role
        self.embed_role = embed_role

    def compute(self, text: str) -> SignalResult:
        from ..assets import prompt
        from ..eval.wsd import TRANSLATE_SYS
        from ..similarity import cosine

        if not text.strip():
            return SignalResult(self.name, 0.0, {"ok": False})
        try:
            en = self.client.text(
                self.role,
                [{"role": "system", "content": TRANSLATE_SYS},
                 {"role": "user", "content": text}], max_tokens=200).strip()
            back = self.client.text(
                self.back_role,
                [{"role": "system",
                  "content": prompt("backtrans").render(source_name="英文")},
                 {"role": "user", "content": en}], max_tokens=200).strip()
            va, vb = self.client.embed([text, back], role=self.embed_role)
        except Exception as e:  # noqa: BLE001
            return SignalResult(self.name, 0.0, {"ok": False, "error": str(e)[:120]})
        sim = cosine(va, vb)
        return SignalResult(self.name, self._clamp(1.0 - sim),
                            {"ok": True, "en": en, "back": back, "cosine": sim})


class NReadings(LLMSignal):
    """S7：reflect 列舉出的替代讀法數，正規化。

    0 或 1 個讀法 → 0（沒有歧義）；讀法越多分數越高，SAT 之後飽和。
    """

    name = "S7_n_readings"
    SAT = 4.0

    def __init__(self, client, role: str = "reflect"):
        super().__init__(client, role)

    def compute(self, text: str) -> SignalResult:
        from ..assets import prompt
        from ..llm import parse_json_loose

        if not text.strip():
            return SignalResult(self.name, 0.0, {"n_readings": 0, "ok": False})
        try:
            raw = self.client.text(
                self.role,
                [{"role": "system", "content": prompt("reflect").render()},
                 {"role": "user", "content": text}], max_tokens=900)
        except Exception as e:  # noqa: BLE001
            return SignalResult(self.name, 0.0,
                                {"n_readings": 0, "ok": False, "error": str(e)[:120]})
        obj = parse_json_loose(raw) or {}
        readings = (obj.get("uncertainty") or {}).get("alternative_readings") or []
        k = len(readings) if isinstance(readings, list) else 0
        # 一個讀法等於沒有歧義，從 1 開始算
        return SignalResult(self.name, self._clamp(max(k - 1, 0) / self.SAT),
                            {"n_readings": k, "ok": True,
                             "readings": [r.get("reading") for r in readings
                                          if isinstance(r, dict)][:8]})


class SemanticEntropySignal(LLMSignal):
    """S8：語意熵。取樣 N 個譯文，看它們分裂成幾群。

    ⚠️ 必須用單一請求的 `n=k` 取樣。重複呼叫會撞快取，熵恆為 0（§P4）。
    分群門檻記在 `detail["threshold"]`。
    """

    name = "S8_semantic_entropy"

    def __init__(self, client, *, n: int = 8, method: str = "embed",
                 threshold: float = 0.92, mode: str = "bidirectional"):
        super().__init__(client, "translate")
        self.n, self.method, self.threshold, self.mode = n, method, threshold, mode

    def compute(self, text: str) -> SignalResult:
        from ..eval.semantic_entropy import semantic_entropy

        if not text.strip():
            return SignalResult(self.name, 0.0, {"ok": False, "n_clusters": 0})
        try:
            r = semantic_entropy(self.client, text, n=self.n, method=self.method,
                                 threshold=self.threshold, mode=self.mode)
        except Exception as e:  # noqa: BLE001
            return SignalResult(self.name, 0.0,
                                {"ok": False, "error": str(e)[:120]})
        return SignalResult(self.name, self._clamp(r.normalized),
                            {"ok": True, "entropy_nats": r.entropy,
                             "n_samples": r.n_samples, "n_clusters": r.n_clusters,
                             "method": r.method, "threshold": r.threshold})


RULE_SIGNALS: list[Signal] = [PolysemyHit(), SubjectEllipsis(),
                              SyntacticComplexity(), CulturalItem()]
ALL_SIGNALS = RULE_SIGNALS      # 向後相容：純規則、不需 client


def llm_signals(client, **kw) -> list[LLMSignal]:
    """建立 S5–S8。client 在此綁定，之後仍是 `signal(text) -> float`。"""
    return [LLMDirect(client), RoundTripFidelity(client),
            NReadings(client), SemanticEntropySignal(client, **kw)]


def compute_all(text: str, client=None, **kw) -> dict[str, SignalResult]:
    """client 為 None 時只算 S1–S4（不呼叫 API）。"""
    sigs: list[Signal] = list(RULE_SIGNALS)
    if client is not None:
        sigs += llm_signals(client, **kw)
    return {s.name: s.compute(text) for s in sigs}


def raw_length(text: str) -> float:
    """純句長基準。S3 必須與它並列報告。"""
    return float(len(text))
