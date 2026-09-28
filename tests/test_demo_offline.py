"""離線模式：沒有 API key 也要能把 demo 跑起來（2026-08-23 裁示 §1-4）。

教授拿到 repo 時不會有 key。離線模式播放 `data/demo/recorded.json` 的預錄結果。

⚠️ 本檔守的三件事：
  1. 沒有 key 時 import 與初始化不炸
  2. 預錄的句子與 profile 與 `DEMO_SENTENCES`／`PROFILES` 一致
     ——不一致的話側邊欄按下去會開天窗
  3. **離線模式下不得建立 `Client`**——建了就是在燒別人的額度
"""

from __future__ import annotations

import importlib
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

RECORDED = ROOT / "data" / "demo" / "recorded.json"


def load():
    return importlib.import_module("streamlit_app")


def rec() -> dict:
    if not RECORDED.exists():
        pytest.skip("尚無 data/demo/recorded.json")
    return json.loads(RECORDED.read_text(encoding="utf-8"))


# ── 1. 沒有 key 時不炸 ──

def test_import_without_api_key(monkeypatch):
    monkeypatch.delenv("ITHU_API_KEY", raising=False)
    m = load()
    assert callable(m.main)


def test_has_api_key_false_when_unset(monkeypatch):
    m = load()
    monkeypatch.setattr(m, "_lazy_env", lambda: None)   # 不要讀本機 .env
    monkeypatch.delenv("ITHU_API_KEY", raising=False)
    assert m.has_api_key() is False


def test_blank_key_counts_as_absent(monkeypatch):
    """`.env` 裡留 `ITHU_API_KEY=` 是常態，那不算有 key。"""
    m = load()
    monkeypatch.setattr(m, "_lazy_env", lambda: None)
    monkeypatch.setenv("ITHU_API_KEY", "   ")
    assert m.has_api_key() is False


def test_real_key_is_detected(monkeypatch):
    m = load()
    monkeypatch.setattr(m, "_lazy_env", lambda: None)
    monkeypatch.setenv("ITHU_API_KEY", "sk-test")
    assert m.has_api_key() is True


def test_missing_recording_returns_none(monkeypatch):
    m = load()
    monkeypatch.setattr(m, "RECORDED", ROOT / "data" / "demo" / "_nope.json")
    assert m.load_recorded() is None


def test_corrupt_recording_returns_none(tmp_path, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    m = load()
    monkeypatch.setattr(m, "RECORDED", bad)
    assert m.load_recorded() is None


# ── 2. 錄的內容與 UI 一致 ──

def test_recorded_sentences_match_demo_sentences():
    m, d = load(), rec()
    assert d["sentences"] == list(m.DEMO_SENTENCES)


def test_recorded_profiles_match_ui_profiles():
    """只錄一個 profile 的話，離線模式下切換就會開天窗。"""
    m, d = load(), rec()
    assert d["profiles"] == list(m.PROFILES)


def test_every_sentence_profile_pair_is_recorded():
    m, d = load(), rec()
    missing = [f"{p}|{s}" for p in m.PROFILES for s in m.DEMO_SENTENCES
               if f"{p}|{s}" not in d["entries"]]
    assert not missing, f"缺少預錄：{missing}"


def test_recording_carries_provenance():
    d = rec()
    assert d.get("recorded_at") and d.get("commit")
    assert d["commit"] != "unknown"


def test_every_entry_has_a_timeline_and_translations():
    d = rec()
    for key, e in d["entries"].items():
        assert e["timeline"], f"{key} 沒有 timeline"
        assert e["translations"], f"{key} 沒有譯文"


def test_recorded_timeline_has_no_cot():
    """⚠️ 錄製是一條輸出通道，一樣不得夾帶模型的原始推理文字。"""
    from cognitive_core.timeline import assert_no_cot
    for e in rec()["entries"].values():
        assert_no_cot(e["timeline"])


# ── 3. 播放不建 Client ⭐ ──

def test_playback_rebuilds_timeline_nodes():
    from cognitive_core.timeline import TimelineNode
    m, d = load(), rec()
    tl, final, cost = m.play_recorded(d, m.DEMO_SENTENCES[0], m.PROFILES[0])
    assert tl and all(isinstance(n, TimelineNode) for n in tl)
    assert [n.step for n in tl] == list(range(1, len(tl) + 1))
    assert final["translations"]


def test_playback_never_constructs_a_client(monkeypatch):
    """⭐ 離線模式建 Client 就是在燒別人的額度。"""
    import cognitive_core.llm as llm

    def boom(*a, **kw):
        raise AssertionError("離線模式不得建立 Client")

    monkeypatch.setattr(llm.Client, "__init__", boom)
    m, d = load(), rec()
    for p in m.PROFILES:
        for s in m.DEMO_SENTENCES:
            assert m.play_recorded(d, s, p) is not None


def test_playback_of_unknown_pair_returns_none():
    m, d = load(), rec()
    assert m.play_recorded(d, "這句沒有錄過", m.PROFILES[0]) is None
    assert m.play_recorded(d, m.DEMO_SENTENCES[0], "no_such_profile") is None


# ── 4. 介面不得假裝是即時的 ──

def test_ui_states_offline_explicitly():
    src = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]
    assert "離線模式——顯示預錄結果" in body
    assert "僅能播放展示句" in body
    assert "recorded_at" in body and "commit" in body, "側邊欄未顯示錄製來源"


def test_input_is_disabled_offline():
    src = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    assert "disabled=offline" in src


def test_no_api_key_input_widget():
    """⚠️ 刻意不做「在 UI 裡填 key」——key 存 session state 會掉、

    存檔案會不小心進版控，而且每次點擊都在燒別人的額度。
    """
    src = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]
    for bad in ("text_input", "password"):
        assert bad not in body, f"介面出現疑似填 key 的元件：{bad}"
