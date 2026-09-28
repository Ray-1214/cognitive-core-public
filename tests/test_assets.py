"""Prompt 與 skill 載入的回歸測試（實作規格書 §A-4、§A-5）。

重點在兩件事：
  1. hash 必須隨內容改變 —— prompt 改了而數據沒重跑，是先前事故的根因之一
  2. 缺變數必須報錯 —— 未填的佔位符會直接進 prompt，讓數據無聲失真
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core import assets  # noqa: E402

REQUIRED_PROMPTS = ["translate", "backtrans", "reflect", "verify", "router"]
REQUIRED_SKILLS = ["zh-TW", "en", "ja", "de"]


@pytest.mark.parametrize("name", REQUIRED_PROMPTS)
def test_required_prompt_exists(name):
    p = assets.prompt(name)
    assert p.body, f"{name} 內容為空"
    assert len(p.sha256_16) == 16


@pytest.mark.parametrize("code", REQUIRED_SKILLS)
def test_required_skill_exists(code):
    s = assets.skill(code)
    assert s.body
    assert s.meta.get("code") == code, f"{code} 的 frontmatter code 欄位不符"


def test_missing_asset_lists_available():
    with pytest.raises(FileNotFoundError) as e:
        assets.prompt("no_such_prompt")
    assert "可用" in str(e.value)


def test_template_not_listed_as_available_skill():
    assert "_template" not in assets.available_skills()


# ── render ──

def test_render_fills_placeholders():
    out = assets.prompt("translate").render(target_name="英文", skill="（測試）")
    assert "英文" in out
    assert "{target_name}" not in out and "{skill}" not in out


def test_render_missing_var_raises():
    """缺值必須報錯。靜默留下 {skill} 會讓 prompt 帶著佔位符送出去。"""
    with pytest.raises(KeyError) as e:
        assets.prompt("translate").render(target_name="英文")
    assert "skill" in str(e.value)


def test_render_is_idempotent():
    a = assets.prompt("backtrans").render(source_name="日文")
    b = assets.prompt("backtrans").render(source_name="日文")
    assert a == b


# ── hash ──

def test_hash_changes_with_content(tmp_path, monkeypatch):
    d = tmp_path / "prompts"
    d.mkdir()
    f = d / "tmp.md"
    f.write_text("---\nname: tmp\n---\n第一版", encoding="utf-8")
    monkeypatch.setattr(assets, "PROMPT_DIR", d)
    assets.clear_cache()
    h1 = assets.prompt("tmp").sha256_16
    f.write_text("---\nname: tmp\n---\n第二版", encoding="utf-8")
    assets.clear_cache()
    h2 = assets.prompt("tmp").sha256_16
    assert h1 != h2, "prompt 改了 hash 卻沒變，數據批次無法區分"
    assets.clear_cache()


def test_manifest_covers_all():
    m = assets.asset_manifest()
    for n in REQUIRED_PROMPTS:
        assert f"prompt:{n}" in m
    for c in REQUIRED_SKILLS:
        assert f"skill:{c}" in m


# ── 內容約束 ──

def test_de_is_marked_holdout():
    """德文是留出語言，不得進反思迴圈（地雷 2：循環論證）。"""
    assert assets.skill("de").meta.get("holdout") is True


def test_verify_prompt_uses_forced_enumeration():
    """verify 必須是強制列舉，不可退回是／否問法（AUC 0.500 的教訓）。"""
    body = assets.prompt("verify").body
    assert "列出" in body
    assert "是否相同" not in body.split("⚠️")[0]
