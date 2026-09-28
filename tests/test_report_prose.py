"""守門：論述不得只存在於 `docs/技術報告.md`。

`build_report.py` 用 `write_text` **整份覆蓋**報告。任何直接寫進 .md 的
論述，都會在下一次重跑時無聲消失——報告裡沒有任何東西會提示它不見了。

唯一安全的位置是腳本上方的 `PROSE_*` 常數。本檔守三件事：

1. 每個 `PROSE_*` 常數都真的被寫進報告（有定義沒接線＝論述遺失）
2. 新產出的報告裡標記數 == `todo()` 呼叫數（計數本身可信）
3. **已提交的報告標記數 <= 新產出的**（少掉的那些是只寫在 .md 的論述）

第 3 條是真正的守門條件。搬一段論述進 `PROSE_*` 就少一次 `todo()` 呼叫，
兩邊自然對齊；對不上就是有東西即將被洗掉。
"""

from __future__ import annotations

import importlib.util
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "技術報告.md"

# 只認完整的標記，不認報告表頭那句「標記 `TODO(你寫)` 的位置是…」
MARK = "<!-- TODO(你寫)："


def _load_build_report():
    """以檔案路徑載入——`scripts/` 不是套件，不能用 import。"""
    spec = importlib.util.spec_from_file_location(
        "build_report", ROOT / "scripts" / "build_report.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def generated(tmp_path_factory) -> tuple[object, str]:
    """產到 tmp，**不動已提交的報告**。"""
    mod = _load_build_report()
    out = tmp_path_factory.mktemp("report") / "技術報告.md"
    if mod.main(out=out) != 0:
        pytest.skip("結果檔不齊，無法產出報告")
    return mod, out.read_text(encoding="utf-8")


def _fingerprint(template: str) -> str:
    """取模板中最長的一段不含插值欄位的文字。

    整串比對會因插值而失敗，取首行又會被 `**樣本數**` 這種短標題卡住，
    所以改取最長的字面片段——它必定原樣出現在產出的報告裡。
    """
    return max((p.strip() for p in re.split(r"\{[^}]*\}", template)), key=len)


def test_每個_prose_常數都有接線(generated):
    mod, text = generated
    names = [n for n in dir(mod) if n.startswith("PROSE_")]
    assert names, "沒有任何 PROSE_* 常數——論述應該搬進腳本而非留在 .md"
    for name in names:
        fingerprint = _fingerprint(getattr(mod, name))
        assert len(fingerprint) >= 12, f"{name} 沒有夠長的字面片段可當指紋"
        assert fingerprint in text, (
            f"{name} 有定義但沒被寫進報告——論述遺失，"
            f"檢查是否漏了對應的 a({name}) 呼叫")


def test_標記數等於_todo_呼叫數(generated):
    mod, text = generated
    assert text.count(MARK) == len(mod._TODO_EMITTED), (
        f"報告裡 {text.count(MARK)} 個標記，todo() 呼叫 "
        f"{len(mod._TODO_EMITTED)} 次——計數不可信，第三條檢查會失效")


def test_已提交的報告沒有只存在於_md_的論述(generated):
    """已提交的報告若標記比新產出的少，代表有人直接編輯了 .md。"""
    mod, text = generated
    if not REPORT.exists():
        pytest.skip("報告尚未產出")
    committed = REPORT.read_text(encoding="utf-8").count(MARK)
    fresh = text.count(MARK)
    assert committed >= fresh, (
        f"已提交的報告只剩 {committed} 個 TODO 標記，重新產出卻有 {fresh} 個。\n"
        f"少掉的 {fresh - committed} 段論述只寫在 docs/技術報告.md 裡，"
        f"下次執行 build_report.py 會被覆蓋。\n"
        f"修法：把那幾段搬進 build_report.py 的 PROSE_* 常數，"
        f"並把對應的 todo(...) 換成 a(PROSE_XXX)。")
