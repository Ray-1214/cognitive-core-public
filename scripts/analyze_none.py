"""事後分析：NONE 與錯誤集中在哪一類目標詞。

動機——judge 驗證的 20 筆中，judge 誤判 NONE 的 3 筆全部是
「中文虛詞／量詞在英文中沒有詞彙對應，但語義由結構傳達」的情況
（四強→semifinals、親手去使用→personally use、每條街道→every street）。
若這類詞在 200 筆中佔比高，28% 的 NONE 率就不是 judge 的隨機噪音，
而是評測設計把「無詞彙對應的功能詞」也放進來所致。

用法：
    python scripts/analyze_none.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cognitive_core.eval.wsd import wilson_ci  # noqa: E402

RESULTS = ROOT / "data" / "results"

# CWN 詞類粗分。功能／量詞類在英譯中常無詞彙對應。
FUNCTION_LIKE = ("Nf", "Ng", "P", "D", "Cb", "Caa", "Cbb", "T", "DE", "SHI")


def bucket(pos: str) -> str:
    if pos.startswith("Nf"):
        return "量詞 Nf"
    if any(pos.startswith(p) for p in ("P", "C", "T", "D")):
        return "功能詞 P/C/T/D"
    if pos.startswith("V"):
        return "動詞 V*"
    if pos.startswith("N"):
        return "名詞 N*"
    return f"其他 {pos[:3]}"


def main() -> int:
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS / "wsd_baseline.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    items = d["items"]
    n = len(items)
    L = [f"# NONE 與錯誤的分布　n={n}", "",
         "> 事後分析。動機見 `scripts/analyze_none.py` 的 docstring。", ""]

    # ── 依詞類 ──
    by = collections.defaultdict(list)
    for it in items:
        by[bucket(it["pos"])].append(it)
    L += ["## 依詞類", "",
          "| 詞類 | n | NONE | NONE 率 | 95% CI | 可判定 | 正確率 |",
          "| --- | :-: | :-: | :-: | :-: | :-: | :-: |"]
    print(f"{'詞類':<18}{'n':>4}{'NONE率':>9}{'正確率':>10}")
    for k in sorted(by, key=lambda x: -len(by[x])):
        g = by[k]
        nn = sum(1 for it in g if it["is_none"])
        lo, hi = wilson_ci(nn, len(g))
        jg = [it for it in g if it["correct"] is not None]
        acc = f"{sum(it['correct'] for it in jg) / len(jg):.3f}" if jg else "—"
        L.append(f"| {k} | {len(g)} | {nn} | {nn / len(g) * 100:.0f}% | "
                 f"[{lo * 100:.0f}, {hi * 100:.0f}]% | {len(jg)} | {acc} |")
        print(f"  {k:<16}{len(g):>4}{nn / len(g) * 100:>8.0f}%{acc:>10}")

    # ── 功能詞 vs 實詞 的二分對照 ──
    fn = [it for it in items if bucket(it["pos"]) in ("量詞 Nf", "功能詞 P/C/T/D")]
    ct = [it for it in items if it not in fn]
    L += ["", "### 二分對照", "",
          "| | n | NONE | NONE 率 | 95% CI |", "| --- | :-: | :-: | :-: | :-: |"]
    for lab, g in (("功能詞／量詞", fn), ("實詞（動詞、名詞等）", ct)):
        if not g:
            continue
        nn = sum(1 for it in g if it["is_none"])
        lo, hi = wilson_ci(nn, len(g))
        L.append(f"| {lab} | {len(g)} | {nn} | {nn / len(g) * 100:.0f}% | "
                 f"[{lo * 100:.0f}, {hi * 100:.0f}]% |")
    if fn and ct:
        a = sum(1 for it in fn if it["is_none"]) / len(fn)
        b = sum(1 for it in ct if it["is_none"]) / len(ct)
        L += ["", f"差距 **{(a - b) * 100:+.0f}pp**"]
        print(f"\n  功能詞／量詞 NONE 率 {a * 100:.0f}%  vs  實詞 {b * 100:.0f}%"
              f"　差 {(a - b) * 100:+.0f}pp")

    # ── 依目標詞（只列 NONE 最集中的） ──
    byw = collections.defaultdict(list)
    for it in items:
        byw[it["word"]].append(it)
    ranked = sorted(byw.items(),
                    key=lambda kv: -sum(1 for it in kv[1] if it["is_none"]))
    L += ["", "## NONE 最集中的目標詞", "",
          "| 詞 | n | NONE | NONE 率 |", "| :-: | :-: | :-: | :-: |"]
    tot = 0
    for w, g in ranked[:12]:
        nn = sum(1 for it in g if it["is_none"])
        if nn == 0:
            break
        tot += nn
        L.append(f"| {w} | {len(g)} | {nn} | {nn / len(g) * 100:.0f}% |")
    n_none = sum(1 for it in items if it["is_none"])
    L += ["", f"前列這些詞佔全部 NONE 的 {tot}/{n_none}"
              f"（{tot / n_none * 100:.0f}%）"]

    # ── NONE 成因 × 詞類 ──
    L += ["", "## NONE 成因 × 是否功能詞／量詞", "",
          "「譯文有譯出但 judge 認不出」若集中在功能詞，即為設計問題而非 judge 隨機失誤。", "",
          "| | 譯文沒譯出 | 譯文有譯出（judge 認不出） |",
          "| --- | :-: | :-: |"]
    for lab, g in (("功能詞／量詞", fn), ("實詞", ct)):
        nones = [it for it in g if it["is_none"]]
        nr = sum(1 for it in nones if it["none_rendered"] is False)
        rd = sum(1 for it in nones if it["none_rendered"] is True)
        L.append(f"| {lab} | {nr} | {rd} |")

    out = RESULTS / f"none_analysis{'_p2' if 'p2' in src.name else ''}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"\n  {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
