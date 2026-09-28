"""LangGraph 狀態機（實作規格書 §A-3、技術設計文件 §3.2）。

    START → route ─┬─(fast)─→ translate_direct ─────────────┐
                   └─(slow)─→ build_anchor → translate_multi │
                                  ▲              │           │
                              reflect ◀── verify ─(pass)─────┤
                                  ▲         │                │
                                  └─(fail, revision<R)───────┘
                                            │                │
                                       (revision≥R)          │
                                            └────────────────┤
                                                             ▼
                                                  write_memory → END

⚠️ `timeline` 存的是**結構化決策記錄**（哪個訊號觸發、哪個欄位缺失、相似度多少），
不是模型的原始推理文字。推理模型的 `reasoning_content` 一律不外流
（計畫書 §4.9 的倫理界線）。Phase E 的時間軸直接吃這個欄位。
"""

from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .llm import Client
from .models import SemanticAnchor
from .reflect import build_anchor, clarification_needed, revise_anchor
from .translate import translate_direct
from .verify import Verifier, VerifyConfig


class GraphState(TypedDict, total=False):
    source_text: str
    targets: list[str]
    profile: str
    route: Optional[dict]              # {path, ambiguity_score, signals, reason}
    anchor: Optional[dict]             # SemanticAnchor.model_dump()
    translations: dict[str, str]
    back_translations: dict[str, str]
    consistency_score: Optional[float]
    detector_score: Optional[float]
    differences: list[str]
    revision_count: int
    memory_context: list[str]
    timeline: list[dict]
    final: Optional[dict]


def _step(state: GraphState, node: str, **payload: Any) -> dict:
    """產生一筆結構化決策記錄。刻意只收數值與欄位名，不收模型輸出的推理文字。"""
    tl = list(state.get("timeline", []))
    tl.append({"step": len(tl) + 1, "node": node, **payload})
    return {"timeline": tl}


def stub_router(state: GraphState) -> dict:
    """⚠️ P1 的固定樁：一律走慢速通道。真正的 Router 是 P5。

    提前實作 Router 會讓 P4 的訊號評估失去對照基準，
    且 RQ2 需要的是「各訊號各自的 AUC」而非一個已調好的合成分數。
    """
    return {"path": "slow", "ambiguity_score": None, "signals": {},
            "reason": "router_stub"}


def build_graph(client: Client, vcfg: VerifyConfig | None = None,
                *, profile: str = "cross_en_ja", router=None):
    """`router` 可注入：P5 換成真的 Router，測試用來驗快速通道。"""
    vcfg = vcfg or VerifyConfig()
    verifier = Verifier(client, vcfg)
    max_rev = int(vcfg.thresholds.get("max_revisions", 3))
    router_fn = router or stub_router

    # ── 節點 ──

    def route(state: GraphState) -> dict:
        decision = router_fn(state)
        return {"route": decision,
                **_step(state, "route", path=decision.get("path"),
                        ambiguity_score=decision.get("ambiguity_score"),
                        reason=decision.get("reason"),
                        signals=decision.get("signals") or {},
                        triggered=sorted((decision.get("signals") or {}).keys()))}

    def translate_direct_node(state: GraphState) -> dict:
        """快速通道：不建錨點，直翻。同時是 B0 baseline 的實作。"""
        outs = {}
        for lang in state["targets"]:
            outs[lang] = translate_direct(client, state["source_text"], lang).text
        return {"translations": outs,
                **_step(state, "translate_direct", languages=list(outs))}

    def build_anchor_node(state: GraphState) -> dict:
        anchor, tier = build_anchor(client, state["source_text"])
        u = anchor.uncertainty
        return {"anchor": anchor.model_dump(), "revision_count": 0,
                **_step(state, "build_anchor", tier=tier,
                        n_readings=u.n_readings,
                        unknown_scalars=anchor.unknown_scalars(),
                        text_determinable=u.derived_text_determinable,
                        self_report_agrees=u.self_report_agrees,
                        n_format_violations=len(u.format_violations))}

    def translate_multi(state: GraphState) -> dict:
        anchor = SemanticAnchor.model_validate(state["anchor"])
        trans = verifier.gather(anchor, state.get("profile", profile))
        outs: dict[str, str] = {}
        for i, t in enumerate(trans):
            key = t.language if len([x for x in trans if x.language == t.language]) == 1 \
                else f"{t.language}#{i + 1}"
            outs[key] = t.text
        return {"translations": outs, "_translations_obj": trans,
                **_step(state, "translate_multi", languages=list(outs),
                        n_samples=len(trans))}

    def verify_node(state: GraphState) -> dict:
        anchor = SemanticAnchor.model_validate(state["anchor"])
        trans = state.get("_translations_obj") or verifier.gather(
            anchor, state.get("profile", profile))
        rep = verifier.evaluate(anchor, trans, state.get("profile", profile))
        return {"back_translations": rep.back_translations,
                "consistency_score": rep.consistency,
                "detector_score": rep.detector_score,
                "differences": rep.differences,
                **_step(state, "verify", profile=rep.profile, mode=rep.mode,
                        detector_score=rep.detector_score,
                        consistency=rep.consistency, passed=rep.passed,
                        n_differences=rep.n_differences)}

    def reflect_node(state: GraphState) -> dict:
        anchor = SemanticAnchor.model_validate(state["anchor"])
        before = anchor.unknown_scalars()
        revised, tier = revise_anchor(client, anchor, state.get("differences", []))
        u = revised.uncertainty
        return {"anchor": revised.model_dump(),
                "revision_count": revised.revisions,
                **_step(state, "reflect", tier=tier, revision=revised.revisions,
                        unknown_before=before, unknown_after=revised.unknown_scalars(),
                        n_readings=u.n_readings,
                        n_format_violations=len(u.format_violations))}

    def write_memory(state: GraphState) -> dict:
        """⚠️ Phase F 才實作 ChromaDB。此處只組裝輸出。"""
        anchor_d = state.get("anchor")
        final: dict[str, Any] = {
            "source_text": state["source_text"],
            "path": (state.get("route") or {}).get("path"),
            "translations": state.get("translations", {}),
            "detector_score": state.get("detector_score"),
            "consistency_score": state.get("consistency_score"),
            "revisions": state.get("revision_count", 0),
        }
        if anchor_d:
            anchor = SemanticAnchor.model_validate(anchor_d)
            u = anchor.uncertainty
            final |= {
                "n_readings": u.n_readings,
                "readings": [r.reading for r in u.alternative_readings],
                "unknown_scalars": anchor.unknown_scalars(),
                "high_uncertainty": u.is_high,
                "clarifications": clarification_needed(anchor),
                "format_violations": u.format_violations,
            }
        return {"final": final,
                **_step(state, "write_memory", stub=True,
                        high_uncertainty=final.get("high_uncertainty"))}

    # ── 條件邊 ──

    def route_branch(state: GraphState) -> Literal["fast", "slow"]:
        return "fast" if (state.get("route") or {}).get("path") == "fast" else "slow"

    def verify_branch(state: GraphState) -> Literal["pass", "reflect", "exhausted"]:
        cons = state.get("consistency_score")
        det = state.get("detector_score")
        th = vcfg.thresholds
        if cons is not None:
            passed = cons >= float(th.get("consistency_pass", 0.75))
        else:
            passed = (det or 0.0) >= float(th.get("detector_slow_path", 0.85))
        if passed:
            return "pass"
        return "reflect" if state.get("revision_count", 0) < max_rev else "exhausted"

    # ── 組裝 ──

    g = StateGraph(GraphState)
    g.add_node("route", route)
    g.add_node("translate_direct", translate_direct_node)
    g.add_node("build_anchor", build_anchor_node)
    g.add_node("translate_multi", translate_multi)
    g.add_node("verify", verify_node)
    g.add_node("reflect", reflect_node)
    g.add_node("write_memory", write_memory)

    g.add_edge(START, "route")
    g.add_conditional_edges("route", route_branch,
                            {"fast": "translate_direct", "slow": "build_anchor"})
    g.add_edge("translate_direct", "write_memory")
    g.add_edge("build_anchor", "translate_multi")
    g.add_edge("translate_multi", "verify")
    g.add_conditional_edges("verify", verify_branch,
                            {"pass": "write_memory", "reflect": "reflect",
                             "exhausted": "write_memory"})
    g.add_edge("reflect", "translate_multi")
    g.add_edge("write_memory", END)
    return g.compile()


def initial_state(text: str, targets: list[str], profile: str) -> GraphState:
    return GraphState(source_text=text, targets=targets, profile=profile,
                      translations={}, back_translations={}, differences=[],
                      revision_count=0, memory_context=[], timeline=[])
