"""prompt 裡的例子不得取自評測資料或 dev-30（v3 架構書 §4 地雷 3）。

這支測試是我自己犯過兩次之後補的，而且**第一版還漏抓了第三次**：

  1. `router.md` v2 的例句用了「我們不收支票。」——那句就在 400 筆探針裡
  2. `reflect.md` v2 的 few-shot 用「他昨天走了」＋完整 licensed_readings
     ——那是 dev-30 的 dev-lex-09，等於把答案寫進 prompt
  3. `sense_judge_binary.md` v1 的 few-shot 用了探針的**英文譯文**與
     **CWN 義項定義**（`bring me something to eat` / 「用手取物或持物。」）
     ——第一版測試只掃引號內的中文，完全沒看到

洩題的共同特徵是**從結果看不出來**：該題的分數照樣產生，只是不再有意義。
所以四種載體都要掃：原句、譯文、義項定義、dev-30 文本。
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"
PROBES = ROOT / "data" / "probes" / "wsd_probes.yaml"
DEV30 = ROOT / "data" / "dev30" / "sentences.yaml"
BASELINE = ROOT / "data" / "results" / "wsd_baseline400.json"

# 中文片段：連續 5 個以上的漢字。太短會撞到通用詞而全是偽陽性。
CJK_RUN = re.compile(r"[一-鿿]{5,}")
# 英文片段：連續 4 個以上的英文詞。譯文比對用。
EN_RUN = re.compile(r"[A-Za-z][A-Za-z'’,\- ]{18,}")


def prompt_files() -> list[pathlib.Path]:
    return sorted(PROMPTS.glob("*.md"))


def prompt_body(path: pathlib.Path) -> str:
    """只取送給模型的部分。

    frontmatter（含 changelog / design）不會進 `render()`，所以在那裡
    提到某個句子不構成洩題——修正記錄本來就得寫出被換掉的是哪一句。
    """
    t = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n.*?\n---\n", t, re.DOTALL)
    return t[m.end():] if m else t


def probes() -> list[dict]:
    if not PROBES.exists():
        return []
    return yaml.safe_load(PROBES.read_text(encoding="utf-8"))["items"]


def probe_sentences() -> set[str]:
    return {p["sentence"] for p in probes()}


def probe_definitions() -> set[str]:
    """gold 與所有競爭義項的定義。這些是 judge prompt 最容易誤用的素材。"""
    out = set()
    for p in probes():
        out.add(p["gold_definition"])
        for s in p.get("competing_senses", []):
            out.add(s["definition"])
    return {d.strip() for d in out if d and len(d.strip()) >= 6}


def probe_translations() -> set[str]:
    if not BASELINE.exists():
        return set()
    d = json.loads(BASELINE.read_text(encoding="utf-8"))
    return {it["translation"].strip() for it in d.get("items", [])
            if it.get("translation") and len(it["translation"].strip()) >= 20}


def dev30_text() -> str:
    return DEV30.read_text(encoding="utf-8") if DEV30.exists() else ""


def cjk_fragments(text: str) -> list[str]:
    """引號／反引號內的中文片段——那些才是例句。"""
    quoted = re.findall(r"`([^`\n]+)`|「([^」\n]+)」", text)
    out = []
    for a, b in quoted:
        for m in CJK_RUN.findall((a or b).strip()):
            out.append(m)
    return out


# ── 原句 ──

@pytest.mark.parametrize("path", prompt_files(), ids=lambda p: p.name)
def test_prompt_examples_not_in_probe_set(path):
    sents = probe_sentences()
    if not sents:
        pytest.skip("尚無探針資料")
    bad = [(f, s) for f in cjk_fragments(prompt_body(path))
           for s in sents if f in s]
    assert not bad, (
        f"{path.name} 的例句出現在評測資料裡（洩題）：\n"
        + "\n".join(f"  「{f}」 ⊂ 探針「{s}」" for f, s in bad[:5]))


# ── 義項定義 ⭐ 第一版漏掉的 ──

@pytest.mark.parametrize("path", prompt_files(), ids=lambda p: p.name)
def test_prompt_does_not_quote_probe_definitions(path):
    """few-shot 用真實的 CWN 義項定義，等於示範該義項的正確答案。

    judge prompt 特別容易犯——寫例子時最順手的素材就是資料集裡的定義。
    """
    defs = probe_definitions()
    if not defs:
        pytest.skip("尚無探針資料")
    body = prompt_body(path)
    bad = [d for d in defs if d in body]
    assert not bad, (
        f"{path.name} 直接引用了探針集的義項定義（洩題）：{bad[:5]}\n"
        "  改用未被抽樣到的目標詞的義項。")


# ── 譯文 ⭐ 第一版漏掉的 ──

@pytest.mark.parametrize("path", prompt_files(), ids=lambda p: p.name)
def test_prompt_does_not_quote_probe_translations(path):
    trs = probe_translations()
    if not trs:
        pytest.skip("尚無基準結果")
    body = prompt_body(path)
    bad = [t for t in trs if t in body]
    assert not bad, (
        f"{path.name} 直接引用了探針的英文譯文（洩題）：{bad[:3]}")


# ── dev-30 ──

@pytest.mark.parametrize("path", prompt_files(), ids=lambda p: p.name)
def test_prompt_examples_not_in_dev30(path):
    t = dev30_text()
    if not t:
        pytest.skip("尚無 dev-30")
    bad = [f for f in cjk_fragments(prompt_body(path)) if f in t]
    assert not bad, (
        f"{path.name} 的例句取自 dev-30（研究者已人工複核的資料）：{bad[:5]}")


# ── 偵測器自己要能抓到違規 ──
#
# ⚠️ **一律從 `sorted(...)` 取樣本，不要 `next(iter(set))`。**
# set 的迭代順序隨 `PYTHONHASHSEED` 變動，每次跑挑到不同句子——
# 挑到「他投７局、送出８次三振，」這種全形數字打斷漢字連續的句子，
# `cjk_fragments()` 抽不出片段，測試就失敗。
# 症狀是**隨機紅燈**，看起來像專案不穩，其實是取樣不確定。
# 實測 400 筆探針中有 4 筆長度 ≥6 卻抽不出 5 連漢字。


def pick(items: set[str], *, ok=lambda s: True) -> str:
    """從集合取一個**確定的**樣本。順序固定，且必須滿足前提條件。"""
    for s in sorted(items):
        if ok(s):
            return s
    pytest.skip("沒有滿足前提的樣本")


def test_detector_catches_sentence_leak():
    sents = probe_sentences()
    if not sents:
        pytest.skip("尚無探針資料")
    # 前提：句子要抽得出 5 連漢字（偵測器的門檻），且不含反引號免得破壞包裹
    victim = pick(sents, ok=lambda s: CJK_RUN.search(s) and "`" not in s)
    frags = cjk_fragments(f"範例：`{victim}` → 0.5")
    assert any(any(fr in s for s in sents) for fr in frags), \
        "偵測器抓不到明顯的洩題，門檻或正則需要調整"


def test_detector_catches_definition_leak():
    defs = probe_definitions()
    if not defs:
        pytest.skip("尚無探針資料")
    victim = pick(defs)
    body = f"A：{victim}　B：其他"
    assert [d for d in defs if d in body], "偵測器抓不到義項定義的洩題"


def test_detector_catches_translation_leak():
    trs = probe_translations()
    if not trs:
        pytest.skip("尚無基準結果")
    victim = pick(trs, ok=lambda s: "`" not in s)
    body = f"譯文：`{victim}`"
    assert [t for t in trs if t in body], "偵測器抓不到譯文的洩題"
