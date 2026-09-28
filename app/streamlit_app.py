"""Cognitive-Core 展示介面（v3 架構書 §P7）。

    streamlit run app/streamlit_app.py

## 兩條界線

**① 不揭露原始 CoT**（計畫書 §4.9）
右欄顯示的是**結構化決策記錄**——哪個訊號量到多少、哪個欄位缺失、
相似度多少——不是模型的推理文字。這條界線由 `timeline.assert_no_cot()`
在渲染前強制檢查，違規時畫面直接報錯而不是靜默過濾。

**② 不展示分流決策**（2026-08-22 裁示）
P4 實測八個訊號的 AUC 為 0.431–0.527、純句長基準 0.514，95% CI 全數涵蓋 0.5。
訊號**無法**預測詞義錯誤，所以介面不呈現快慢通道，也不把訊號值說成分流依據。
訊號照樣量、照樣顯示，但明確標為**診斷資訊**並附上實測結果。

展示一個實際上無效的分流，會讓觀眾以為系統靠訊號挑出了難句。
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st  # noqa: E402

from cognitive_core.timeline import (  # noqa: E402
    SIGNAL_DISCLAIMER,
    TimelineNode,
    build_timeline,
    summarise_cost,
)

RECORDED = ROOT / "data" / "demo" / "recorded.json"

DEMO_SENTENCES = [
    "這個人很有意思",
    "報告我下週一交給你",
    "那位客人的東西還沒拿走",
    "小王把整鍋湯都端上來了",
    "他的話裡有話",
]

PROFILES = ["cross_en_ja", "same_en", "single_ja"]


def _lazy_env() -> None:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")


# ══════════════ 離線模式 ══════════════
#
# 教授要能**不用 API key** 就把 demo 跑起來看。
#
# ⚠️ 刻意**不做**「在 UI 裡填 key」的設定頁：key 存 session state 會掉、
#    存檔案會不小心進版控，而且每次點擊都在燒別人的額度。
#    沒有 key 的人要的是「不用 key 就能看到東西」，不是一個填表流程。


def has_api_key() -> bool:
    """有沒有校內端點的 key。沒有就走離線模式。"""
    _lazy_env()
    return bool((os.environ.get("ITHU_API_KEY") or "").strip())


def load_recorded() -> dict | None:
    if not RECORDED.exists():
        return None
    try:
        return json.loads(RECORDED.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def play_recorded(rec: dict, text: str, profile: str):
    """播放預錄結果。回傳 (timeline, final, cost)，與 `run_pipeline` 同形。

    ⚠️ 這是**播放錄影**不是執行。介面必須明示，不得讓人以為系統在跑。
    """
    e = (rec.get("entries") or {}).get(f"{profile}|{text}")
    if e is None:
        return None
    tl = [TimelineNode(**n) for n in e["timeline"]]
    final = {"translations": e.get("translations") or {},
             "clarifications": e.get("clarifications") or [],
             "readings": e.get("readings") or [],
             "unknown_scalars": e.get("unknown_scalars") or [],
             "high_uncertainty": e.get("high_uncertainty")}
    return tl, final, e.get("cost") or {}


def run_pipeline(text: str, profile: str) -> tuple[list, dict, dict]:
    """跑一次完整流程。回傳 (timeline, final, cost)。

    ⚠️ 匯入放在函式內——`streamlit_app` 必須可以被 import 而不觸發副作用
    （建 Client、讀 .env、連線），否則測試無法載入它。
    """
    _lazy_env()
    from cognitive_core.graph import build_graph, initial_state, stub_router
    from cognitive_core.llm import Client
    from cognitive_core.router.signals import compute_all
    from cognitive_core.runlog import RunLog

    run = RunLog("demo", meta={"profile": profile})
    client = Client(run=run)

    # 訊號：純規則的四個先算（免費），標為診斷資訊。
    # ⚠️ 經由 router 注入讓 graph 的 route 節點自己記錄，**不要另外塞 timeline**——
    #    手動塞一筆、route 節點再記一筆，時間軸就會出現兩個「訊號量測」。
    #    timeline 只由 graph 產生，這裡不碰。
    sigs = {k: round(v.score, 3) for k, v in compute_all(text).items()}

    def demo_router(state) -> dict:
        return {**stub_router(state), "signals": sigs}

    graph = build_graph(client, profile=profile, router=demo_router)

    targets = {"cross_en_ja": ["en", "ja"], "same_en": ["en"],
               "single_ja": ["ja"]}[profile]
    state = initial_state(text, targets, profile)

    t0 = time.monotonic()
    out = graph.invoke(state)
    wall = time.monotonic() - t0

    cost = run.summary()
    cost["wall_s"] = round(wall, 1)
    return build_timeline(out), out.get("final") or {}, cost


# 預設展開的節點：錨點建構（UNKNOWN 欄位、列舉的讀法）與回譯比對（相似度分數）
# 是最能說明系統在做什麼的兩格，其餘維持摺疊以免畫面太長。
EXPANDED_NODES = ("build_anchor", "verify")


def render_node(n) -> None:
    with st.expander(f"**{n.step}. {n.label}**　`{n.node}`",
                     expanded=n.node in EXPANDED_NODES):
        if n.node == "route":
            st.warning(f"⚠️ {SIGNAL_DISCLAIMER}")
            sig = n.detail.get("signals") or {}
            if sig:
                st.bar_chart(sig, horizontal=True)
        for k, v in n.detail.items():
            if k in ("signals", "note"):
                continue
            if isinstance(v, float):
                st.metric(k, f"{v:.3f}")
            elif isinstance(v, (list, tuple)):
                st.write(f"**{k}**：{'、'.join(map(str, v)) if v else '（無）'}")
            elif v is not None:
                st.write(f"**{k}**：{v}")
        if n.cost:
            st.caption(str(n.cost))


def main() -> None:
    st.set_page_config(page_title="Cognitive-Core", layout="wide")
    st.title("Cognitive-Core　中文高語境歧義的偵測與診斷")

    live = has_api_key()
    rec = None if live else load_recorded()
    offline = not live and rec is not None

    if not live and rec is None:
        st.error("離線模式需要 `data/demo/recorded.json`，但找不到該檔。"
                 "請設定 `ITHU_API_KEY` 走即時模式，"
                 "或執行 `python scripts/record_demo.py` 產生預錄結果。")
        return

    if offline:
        st.warning(
            "**離線模式——顯示預錄結果。**　"
            "設定 API key 後可即時執行任意句子（見 `.env.example`）。",
            icon="📼")

    with st.sidebar:
        st.header("設定")
        st.caption("🟢 即時模式" if live else "📼 離線模式（播放預錄結果）")
        profile = st.selectbox("Profile（消融）", PROFILES,
                               help="cross_en_ja 跨語言／same_en 同語言／"
                                    "single_ja 單探針")
        st.divider()
        st.subheader("展示句")
        for s in DEMO_SENTENCES:
            if st.button(s, use_container_width=True):
                st.session_state["pending"] = s
        st.divider()
        if st.button("清除對話", type="secondary", use_container_width=True):
            st.session_state["history"] = []
            st.rerun()
        if offline:
            st.divider()
            st.caption(f"錄製於 `{rec.get('recorded_at', '—')}`")
            st.caption(f"commit `{rec.get('commit', '—')}`")

    st.session_state.setdefault("history", [])

    left, right = st.columns([1, 1])

    with left:
        st.subheader("對話")
        for h in st.session_state["history"]:
            with st.chat_message("user"):
                st.write(h["text"])
            with st.chat_message("assistant"):
                for lang, t in (h["final"].get("translations") or {}).items():
                    st.write(f"**{lang}**　{t}")
                cl = h["final"].get("clarifications") or []
                if cl:
                    st.info("澄清提問：" + "；".join(cl))
        typed = st.chat_input(
            "離線模式僅能播放展示句" if offline else "輸入一句中文…",
            disabled=offline)

    pending = typed or st.session_state.pop("pending", None)
    if pending:
        if offline:
            got = play_recorded(rec, pending, profile)
            if got is None:
                st.warning(f"離線模式沒有「{pending}」在 `{profile}` 下的預錄結果。"
                           "請改點側邊欄的展示句。")
                return
            tl, final, cost = got
        else:
            with st.spinner("跑流程中…"):
                try:
                    tl, final, cost = run_pipeline(pending, profile)
                except Exception as e:  # noqa: BLE001
                    st.error(f"流程失敗：{type(e).__name__}: {e}")
                    return
        st.session_state["history"].append(
            {"text": pending, "timeline": tl, "final": final, "cost": cost,
             "recorded": offline})
        st.rerun()

    with right:
        st.subheader("決策時間軸")
        if not st.session_state["history"]:
            st.info("左欄輸入一句中文，或從側邊欄挑一句展示句。")
        else:
            last = st.session_state["history"][-1]
            if last.get("recorded"):
                st.caption("📼 以下為預錄結果，非本次即時執行。")
            for n in last["timeline"]:
                render_node(n)
            st.divider()
            st.caption(("錄製時的成本　" if last.get("recorded") else "成本　")
                       + summarise_cost(last["cost"]))
            st.caption("⚠️ 本欄顯示結構化決策記錄，不含模型的原始推理文字"
                       "（計畫書 §4.9）。")
            # 原本放在側邊欄，但被展示句與按鈕擠到摺疊線以下、實際看不到。
            # 訊號值就顯示在上方的時間軸裡，免責說明貼著它才有意義。
            st.caption(f"⚠️ **RQ1 實測結果**　{SIGNAL_DISCLAIMER}")


if __name__ == "__main__":
    main()
