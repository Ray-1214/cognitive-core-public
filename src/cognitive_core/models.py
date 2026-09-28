"""語意錨點的資料模型（實作規格書 §A-1、技術設計文件 §4.3）。

四條不可違反的約束，用型別結構強制而非靠自律：

1. `source_text` 任何階段不得修改
   → `SemanticAnchor` 為 frozen；修訂走 `revise()` 產生新實例並保留原文。
   → LLM 產出的是 `AnchorDraft`（不含 source_text），結構上就不可能改到原文。
2. 反思後重譯只讀錨點，不讀上一輪譯文
   → 由 graph 的節點介面保證（translate 只吃 anchor）。
3. `UNKNOWN` 是合法且被鼓勵的值
   → 所有純量欄位預設為 UNKNOWN。
4. `alternative_readings` 必填、不設數量上限
   → 改報 precision@k。硬上限會製造截斷假象，分不出是模型克制還是上限咬到。

⚠️ 意圖類資訊一律走 `alternative_readings` 列舉，不設單值欄位。
依據：§8.2 實測模型對 `speaker_intent` 僅 7.4% 標對 UNKNOWN（且判別力為負），
§8.3 的 V4 自評題 AUC 0.500。承認 UNKNOWN 是自我評估（模型抗拒），
列舉讀法是生成（模型樂意）。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

UNKNOWN = "UNKNOWN"

AmbiguityType = Literal["LEXICAL", "SYNTACTIC", "REFERENTIAL", "PRAGMATIC"]
Register = Literal["FORMAL", "SEMI_FORMAL", "CASUAL", "UNKNOWN"]

# 錨點的純量欄位，供逐欄位可判定性統計使用
SCALAR_FIELDS = ("agent", "time", "register", "social_relation")


class AlternativeReading(BaseModel):
    """一個原文允許的讀法。speaker_intent 降層於此，不在錨點頂層。"""

    model_config = ConfigDict(extra="ignore")

    reading: str
    applicable_when: str = ""
    speaker_intent: str = UNKNOWN


class CulturalItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    term: str
    literal: str = ""
    actual_sense: str = ""
    ambiguity_type: AmbiguityType = "PRAGMATIC"


# 格式上限。超過即記 warning，但**不拒絕**——直接拒絕會讓 schema 通過率失真，
# 而「模型多常不遵守格式」本身是要統計的數據。
MAX_READING_CHARS = 20
MAX_APPLICABLE_CHARS = 30
MAX_INTENT_CHARS = 12


class Uncertainty(BaseModel):
    model_config = ConfigDict(extra="ignore")

    unknown_fields: list[str] = Field(default_factory=list)
    ambiguity_score: float = 0.0
    text_determinable: bool = True
    alternative_readings: list[AlternativeReading] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)

    @field_validator("ambiguity_score")
    @classmethod
    def _clamp(cls, v: float) -> float:
        return min(max(float(v), 0.0), 1.0)

    @property
    def n_readings(self) -> int:
        """列舉的讀法數。這是第七個候選偵測訊號（S7）——最便宜的一個：
        一次呼叫、不翻譯、不回譯。Phase B 須跑長度基準對照（地雷 1），
        長句可能自然引出更多讀法。
        """
        return len(self.alternative_readings)

    @property
    def format_violations(self) -> list[str]:
        """不符長度規範的欄位。計算屬性而非欄位，避免污染送給模型的 schema。

        v1 prompt 實測產出的是整句改寫而非短標籤，與標註 schema 對不起來，
        主指標（正確義項命中率、precision@k）因此無法計算。
        """
        out: list[str] = []
        for i, r in enumerate(self.alternative_readings):
            if len(r.reading) > MAX_READING_CHARS:
                out.append(f"reading[{i}] {len(r.reading)}字>{MAX_READING_CHARS}"
                           f"：{r.reading[:24]}…")
            if len(r.applicable_when) > MAX_APPLICABLE_CHARS:
                out.append(f"applicable_when[{i}] {len(r.applicable_when)}字"
                           f">{MAX_APPLICABLE_CHARS}")
            if len(r.speaker_intent) > MAX_INTENT_CHARS:
                out.append(f"speaker_intent[{i}] {len(r.speaker_intent)}字"
                           f">{MAX_INTENT_CHARS}：{r.speaker_intent[:16]}…")
        return out

    @property
    def derived_text_determinable(self) -> bool:
        """由**列舉行為**推導，而非採信模型自報的 `text_determinable`。

        §8.2 已證實模型的自我回報不承載資訊（`unknown_fields` 與實際值不符）。
        實測同一次呼叫中模型會一邊回報 determinable=True、一邊列出三個讀法。
        列了多個讀法就是不可決定——以行為為準。
        """
        return len(self.alternative_readings) <= 1

    @property
    def self_report_agrees(self) -> bool:
        """模型自報的 determinable 是否與其列舉行為一致。

        兩者不一致的比率本身是可報告的數據：自我評估 vs 生成行為的落差。
        """
        return self.text_determinable == self.derived_text_determinable

    @property
    def is_high(self) -> bool:
        """高不確定性狀態（技術設計文件 §4.3）。一律以行為為準。"""
        return (not self.derived_text_determinable
                or bool(self.unknown_fields)
                or len(self.alternative_readings) > 1)


class AnchorDraft(BaseModel):
    """LLM 產出的部分。**刻意不含 source_text**，結構上排除竄改原文的可能。"""

    model_config = ConfigDict(extra="ignore")

    agent: str = UNKNOWN
    time: str = UNKNOWN
    register: Register = UNKNOWN
    social_relation: str = UNKNOWN
    cultural_items: list[CulturalItem] = Field(default_factory=list)
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)

    @field_validator("cultural_items", mode="before")
    @classmethod
    def _coerce_items(cls, v: Any) -> Any:
        """模型常把陣列寫成 {"items": [...]} 或單一物件。形狀錯不該讓整份作廢——
        真正要驗的是讀法有沒有填對。

        ⚠️ **缺 `term` 的項目一律丟掉，而不是讓整份 draft 作廢。**
        實例：「他的話裡有話」的 `revise_anchor` 100% 失敗，因為模型回了一個
        沒有 `term` 的 cultural item，於是三個 tier 全數驗證失敗、整條管線中斷。
        這與本檔上方「格式違規記 warning 但不拒絕」的原則一致——
        沒有任何實驗指標消費 `cultural_items`，為了它讓錨點整份作廢不划算。
        """
        if v is None:
            return []
        if isinstance(v, dict):
            for key in ("items", "cultural_items", "list"):
                inner = v.get(key)
                if isinstance(inner, list):
                    base = {k: x for k, x in v.items() if k != key}
                    v = [({**base, "term": i} if isinstance(i, str) else {**base, **i})
                         for i in inner]
                    break
            else:
                v = [v] if "term" in v else []
        if not isinstance(v, list):
            return v
        out = []
        for item in v:
            if isinstance(item, str):
                out.append({"term": item})
            elif isinstance(item, dict) and str(item.get("term", "")).strip():
                out.append(item)
            # 其餘（缺 term、或非 dict）靜默丟棄——見上方說明
        return out

    @field_validator("agent", "time", "social_relation", mode="before")
    @classmethod
    def _normalise_unknown(cls, v: Any) -> Any:
        """模型常寫成 unknown / 未知 / null，一律正規化，否則 UNKNOWN 統計會失真。"""
        if v is None:
            return UNKNOWN
        s = str(v).strip()
        if not s or s.lower() in {"unknown", "n/a", "na", "none", "null"}:
            return UNKNOWN
        if s in {"未知", "不明", "無法判定", "無法確定"}:
            return UNKNOWN
        return s


class SemanticAnchor(BaseModel):
    """完整錨點。frozen —— 修訂一律產生新實例，原文永遠保留。"""

    model_config = ConfigDict(frozen=True, extra="ignore")

    source_text: str
    source_language: str = "zh-TW"
    agent: str = UNKNOWN
    time: str = UNKNOWN
    register: Register = UNKNOWN
    social_relation: str = UNKNOWN
    cultural_items: list[CulturalItem] = Field(default_factory=list)
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    revisions: int = 0
    built_by: str = ""

    # ── 建構 ──
    @classmethod
    def from_draft(cls, draft: AnchorDraft, *, source_text: str,
                   source_language: str = "zh-TW", built_by: str = "",
                   revisions: int = 0) -> "SemanticAnchor":
        return cls(source_text=source_text, source_language=source_language,
                   built_by=built_by, revisions=revisions,
                   **draft.model_dump())

    def revise(self, draft: AnchorDraft, *, built_by: str = "") -> "SemanticAnchor":
        """以新的 draft 修訂。source_text 由本方法保留，呼叫端無從覆寫。"""
        return SemanticAnchor.from_draft(
            draft, source_text=self.source_text,
            source_language=self.source_language,
            built_by=built_by or self.built_by,
            revisions=self.revisions + 1)

    # ── 查詢 ──
    def unknown_scalars(self) -> list[str]:
        """實際為 UNKNOWN 的純量欄位。不採信模型自報的 unknown_fields。"""
        return [f for f in SCALAR_FIELDS
                if str(getattr(self, f)).strip().upper() == UNKNOWN]

    def to_prompt_block(self) -> str:
        """給翻譯階段看的錨點文字。原文置頂，符合『每輪都從錨點翻』的設計。"""
        lines = [f"【原文】{self.source_text}", ""]
        lines.append("【顯性化】")
        for f in SCALAR_FIELDS:
            lines.append(f"  {f}: {getattr(self, f)}")
        if self.cultural_items:
            lines.append("【文化專有項】")
            for c in self.cultural_items:
                lines.append(f"  {c.term}（字面：{c.literal}）→ {c.actual_sense}"
                             f" [{c.ambiguity_type}]")
        u = self.uncertainty
        lines.append("【不確定性】")
        lines.append(f"  原文可否決定唯一讀法: {'否' if not u.text_determinable else '是'}")
        if u.alternative_readings:
            lines.append("  可能讀法：")
            for i, r in enumerate(u.alternative_readings, 1):
                extra = f"（{r.applicable_when}）" if r.applicable_when else ""
                lines.append(f"    {i}. {r.reading}{extra} [intent={r.speaker_intent}]")
        unk = self.unknown_scalars()
        if unk:
            lines.append(f"  無從判定的欄位：{', '.join(unk)}")
        return "\n".join(lines)


class Translation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    language: str
    text: str
    from_anchor: bool = True     # False 代表直翻（快速通道），非從錨點產生


class VerifyReport(BaseModel):
    """演算法 1 的輸出。"""

    model_config = ConfigDict(extra="ignore")

    profile: str = ""
    mode: str                                  # cross_lingual / same_language / single_probe
    languages: list[str] = Field(default_factory=list)
    back_translations: dict[str, str] = Field(default_factory=dict)
    consistency: float | None = None           # 樣本間一致性；僅作收斂診斷（地雷 2）
    detector_score: float | None = None        # 單探針往返保真度，與原文比
    passed: bool = False
    differences: list[str] = Field(default_factory=list)   # IdentifyDiff 的結果
    n_readings: int = 0                        # S7 候選訊號，來自錨點
    n_samples: int = 0                         # 實際取得的譯本數

    @property
    def n_differences(self) -> int:
        """診斷產出率。單探針結構上為 0；同語言重取樣實測也可能為 0
        （回譯近乎相同）。分 profile 報告，本身是可觀測指標，不下結論。
        """
        return len(self.differences)


def _inline_refs(node: Any, defs: dict) -> Any:
    """把 $ref 就地展開。

    ⚠️ 實測 `gpt-oss-120b` 在 strict json_schema 模式下處理 $defs/$ref 會失敗：
    它把 `alternative_readings`（物件陣列）攤平成
    `alternative_readings_are_short: true` 之類的布林旗標，
    而且解析得過、必填欄位也齊，降級階梯因此靜默接受了語意上空的結果。
    """
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].rsplit("/", 1)[-1]
            target = defs.get(name, {})
            merged = {k: v for k, v in node.items() if k != "$ref"}
            return {**_inline_refs(target, defs), **merged}
        return {k: _inline_refs(v, defs) for k, v in node.items() if k != "$defs"}
    if isinstance(node, list):
        return [_inline_refs(x, defs) for x in node]
    return node


def anchor_json_schema() -> dict:
    """給 Client.structured() 用的 schema。以 AnchorDraft 為準，不含 source_text。"""
    raw = AnchorDraft.model_json_schema()
    defs = raw.get("$defs", {})
    return _inline_refs(raw, defs)


def anchor_semantics_ok(obj: dict) -> str | None:
    """語意層級的健全性檢查，回傳錯誤描述或 None。

    schema 通過不代表內容有意義。實測模型會回報 text_determinable=false
    卻不列任何讀法——那等於說「這句有歧義但我不告訴你是哪些」，
    後續的 precision@k 與正確義項命中率都算不出來。
    """
    u = obj.get("uncertainty") or {}
    readings = u.get("alternative_readings") or []
    if u.get("text_determinable") is False and len(readings) < 2:
        return (f"text_determinable=false 卻只列了 {len(readings)} 個讀法；"
                "宣稱有歧義就必須列出是哪些讀法")
    return None
