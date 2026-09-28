"""決策時間軸：把 `GraphState["timeline"]` 轉成可展示的結構（v3 架構書 §P7）。

## 倫理界線（計畫書 §4.9）

介面顯示的是**結構化決策記錄**——哪個訊號觸發、哪個欄位缺失、相似度多少——
**不是模型的原始推理文字**。推理模型的 `reasoning_content` 一律不得出現。

這條界線在 `assert_no_cot()` 裡強制執行，而不只是寫在文件上。防的有兩件事：

1. 直接洩漏：某個節點把 `reasoning_content` 放進 payload
2. **間接洩漏**：CoT 從別的欄位混進來——例如某個 `reason` 欄位塞了整段推理。
   所以除了鍵名黑名單，還限制任何自由文本欄位的長度上限。

## ⚠️ 不展示分流決策

P4 的結果是：八個訊號的 AUC 落在 0.431–0.527，95% CI 全數涵蓋 0.5，
**純句長基準（0.514）也不顯著**。訊號無法預測詞義錯誤。

因此時間軸把訊號值標為**診斷資訊**，不標為分流依據，也不呈現快慢通道。
展示一個實際上無效的分流會讓觀眾以為系統靠訊號挑出了難句。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

# 任何鍵名含這些片段者一律視為 CoT 洩漏
FORBIDDEN_KEYS = ("reasoning_content", "reasoning_detail", "cot",
                  "chain_of_thought", "raw_reasoning", "thinking")
# 自由文本欄位的長度上限。超過就不是「結構化決策記錄」了。
MAX_TEXT = 200
# 這些鍵是內容本身（譯文、原句），不受 MAX_TEXT 限制
CONTENT_KEYS = ("source_text", "translation", "translations",
                "back_translation", "back_translations", "text")

NODE_LABELS = {
    "route": "訊號量測",
    "translate_direct": "直接翻譯",
    "build_anchor": "錨點建構",
    "translate_multi": "平行翻譯",
    "verify": "回譯比對",
    "reflect": "反思修正",
    "write_memory": "輸出組裝",
}

# 訊號實測結果，顯示在時間軸上避免誤導（見模組 docstring）
SIGNAL_DISCLAIMER = (
    "診斷資訊，非分流依據。本研究實測八個訊號 AUC 0.463–0.532，"
    "純句長基準 0.517，95% CI 全數涵蓋 0.5。")


class CoTLeak(RuntimeError):
    """時間軸含有模型的原始推理文字。"""


@dataclass(frozen=True)
class TimelineNode:
    step: int
    node: str
    label: str
    detail: dict
    cost: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"step": self.step, "node": self.node, "label": self.label,
                "detail": self.detail, "cost": self.cost}


def _offending(obj, path: str = "") -> list[str]:
    """回傳所有違規的位置。空清單代表乾淨。"""
    bad: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else str(k)
            if any(f in str(k).lower() for f in FORBIDDEN_KEYS):
                bad.append(f"{here}（鍵名黑名單）")
                continue
            bad += _offending(v, here)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            bad += _offending(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        leaf = path.rsplit(".", 1)[-1].split("[")[0]
        if leaf not in CONTENT_KEYS and len(obj) > MAX_TEXT:
            bad.append(f"{path}（自由文本 {len(obj)} 字 > {MAX_TEXT}）")
    return bad


def assert_no_cot(timeline) -> None:
    """時間軸不得含原始推理文字。違規即 raise，不靜默過濾。

    靜默過濾比報錯更危險——它會讓洩漏在下一次改動後悄悄復活。
    """
    payload = [n.as_dict() if isinstance(n, TimelineNode) else n for n in timeline]
    bad = _offending(payload)
    if bad:
        raise CoTLeak("時間軸含疑似原始推理文字：" + "；".join(bad[:5]))


def build_timeline(state: dict, *, costs: dict[int, dict] | None = None
                   ) -> list[TimelineNode]:
    """把 GraphState 的 timeline 轉成展示結構。順序即執行順序。"""
    costs = costs or {}
    out: list[TimelineNode] = []
    for rec in state.get("timeline", []):
        step = rec.get("step", len(out) + 1)
        node = rec.get("node", "?")
        detail = {k: v for k, v in rec.items() if k not in ("step", "node")}
        out.append(TimelineNode(step=step, node=node,
                                label=NODE_LABELS.get(node, node),
                                detail=detail, cost=costs.get(step, {})))
    assert_no_cot(out)
    return out


def render_lines(timeline: list[TimelineNode]) -> list[str]:
    """終端／純文字用的時間軸。Streamlit 走自己的元件。"""
    lines = []
    for n in timeline:
        bits = []
        for k, v in n.detail.items():
            if isinstance(v, float):
                bits.append(f"{k}={v:.3f}")
            elif isinstance(v, (list, tuple)):
                bits.append(f"{k}={len(v)}")
            elif v is not None:
                bits.append(f"{k}={v}")
        lines.append(f"{n.step}. {n.label:<8} " + "　".join(bits))
        if n.node == "route":
            lines.append(f"   ⚠️ {SIGNAL_DISCLAIMER}")
    return lines


def summarise_cost(run_summary: dict) -> str:
    return (f"{run_summary.get('calls', 0)} 次呼叫 / "
            f"{run_summary.get('total_tokens', 0):,} tokens / "
            f"{run_summary.get('wall_s', 0)}s / "
            f"快取命中 {run_summary.get('cache_hits', 0)}")


def to_json(timeline: list[TimelineNode]) -> str:
    assert_no_cot(timeline)
    return json.dumps([n.as_dict() for n in timeline],
                      ensure_ascii=False, indent=2, default=str)
