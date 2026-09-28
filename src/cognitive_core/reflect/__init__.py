"""反思代理人：建構與修訂語意錨點（技術設計文件 §4.3）。

📌 這是計畫書 `ReflectionAgent()` 的實作，不是新主軸。
計畫書 §4.3 承諾「重新分析歧義來源」「生成多個可能的語意解釋並標示其適用情境」
「回傳澄清提示」——本模組就是那三件事。

修法的依據（§8.2 + §8.3 兩次獨立實證）：
承認 UNKNOWN 是**自我評估**任務，模型抗拒（意圖欄位僅 7.4% 標對，判別力為負）；
列舉讀法是**生成**任務，模型樂意（強制列舉版 AUC 0.660 vs 是否版 0.500）。
修法不是說服模型誠實，而是改變輸出結構，讓誠實不需要自我否定。
"""

from __future__ import annotations

from ..assets import prompt
from ..llm import Client, LLMError
from ..models import (
    AnchorDraft,
    SemanticAnchor,
    anchor_json_schema,
    anchor_semantics_ok,
)


def _draft_validator(obj: dict) -> dict:
    """交給 Client.structured 的驗證器：以 Pydantic 為最終把關。

    不論降級階梯走到第幾級都要過這一關——tier1 能過不代表欄位語意正確。
    實測 tier1 會把讀法陣列攤平成布林旗標，形式上合法但語意上空，
    故除了型別驗證還要過 anchor_semantics_ok。
    """
    bad = anchor_semantics_ok(obj)
    if bad:
        raise ValueError(bad)
    return AnchorDraft.model_validate(obj).model_dump()


def build_anchor(client: Client, text: str, *, source_language: str = "zh-TW",
                 role: str = "reflect") -> tuple[SemanticAnchor, int]:
    """由原文建構錨點。回傳 (錨點, 降級階梯用到的 tier)。"""
    msgs = [{"role": "system", "content": prompt("reflect").body},
            {"role": "user", "content": f"分析這句話：{text}"}]
    obj, tier = client.structured(role, msgs, anchor_json_schema(),
                                  validator=_draft_validator, max_tokens=1500)
    draft = AnchorDraft.model_validate(obj)
    spec = client.cfg.resolve(role, client.profile)
    anchor = SemanticAnchor.from_draft(
        draft, source_text=text, source_language=source_language,
        built_by=f"{spec.provider}/{spec.model}")
    _record_anchor_stats(client, anchor, tier, stage="build")
    return anchor, tier


def _record_anchor_stats(client: Client, anchor: SemanticAnchor, tier: int, *,
                         stage: str) -> None:
    """把錨點的可觀測量寫進 run 記錄。

    三項都是後續要統計的：
      n_readings           第七個候選訊號 S7（最便宜：一次呼叫、不翻譯）
      self_report_agrees   模型自評與其自身生成行為的落差率
      format_violations    模型多常不遵守格式規範
    """
    if client.run is None:
        return
    u = anchor.uncertainty
    client.run.record_event("anchor", {
        "stage": stage,
        "tier": tier,
        "revisions": anchor.revisions,
        "n_readings": u.n_readings,
        "unknown_scalars": anchor.unknown_scalars(),
        "text_determinable_self_report": u.text_determinable,
        "text_determinable_derived": u.derived_text_determinable,
        "self_report_agrees": u.self_report_agrees,
        "format_violations": u.format_violations,
        "n_format_violations": len(u.format_violations),
    })


def revise_anchor(client: Client, anchor: SemanticAnchor, differences: list[str], *,
                  role: str = "reflect") -> tuple[SemanticAnchor, int]:
    """依 IdentifyDiff 的結果修訂錨點。

    ⚠️ 修的是**錨點**，不是譯文。譯文只是錨點的投影，源頭修好投影自然對。
    ⚠️ 只讀原文與差異描述，**不讀上一輪譯文**（約束 2）。
    """
    diff_block = "\n".join(f"- {d}" for d in differences) or "（未提供具體差異）"
    user = (
        f"分析這句話：{anchor.source_text}\n\n"
        "先前的分析在轉譯後出現了以下不一致，代表下列欄位可能填錯或不該填：\n"
        f"{diff_block}\n\n"
        "請重新分析。若某欄位確實無從由原文判定，改填 UNKNOWN；"
        "若是讀法本身有分歧，把各個讀法都列進 alternative_readings。"
    )
    msgs = [{"role": "system", "content": prompt("reflect").body},
            {"role": "user", "content": user}]
    obj, tier = client.structured(role, msgs, anchor_json_schema(),
                                  validator=_draft_validator, max_tokens=1500)
    draft = AnchorDraft.model_validate(obj)
    spec = client.cfg.resolve(role, client.profile)
    revised = anchor.revise(draft, built_by=f"{spec.provider}/{spec.model}")
    _record_anchor_stats(client, revised, tier, stage="revise")
    return revised, tier


def clarification_needed(anchor: SemanticAnchor) -> list[str]:
    """高不確定性時該問使用者什麼（計畫書 §4.3「回傳澄清提示」）。

    模型自己給的問題優先；沒給就依實際為 UNKNOWN 的欄位生成。
    """
    if anchor.uncertainty.clarification_questions:
        return list(anchor.uncertainty.clarification_questions)
    tmpl = {
        "agent": "這句話的動作是誰做的？",
        "time": "這件事發生在什麼時候？",
        "register": "這句話用在正式場合還是日常對話？",
        "social_relation": "這句話是對上司、同事還是朋友說的？",
    }
    return [tmpl[f] for f in anchor.unknown_scalars() if f in tmpl]


__all__ = ["build_anchor", "revise_anchor", "clarification_needed", "LLMError"]
