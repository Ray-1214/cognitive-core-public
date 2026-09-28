"""產生備審資料用的圖（2026-08-29）。

  figs/architecture.svg / .png   系統架構
  figs/auc_summary.png           RQ1 的 AUC 結果

⚠️ **架構圖不畫快速通道的分流。** P4 實測八個訊號的 AUC 為 0.463–0.532、
純句長基準 0.517，95% CI 全數涵蓋 0.5——訊號無法預測詞義錯誤，
分流的前提不成立（見 `docs/.../v3.md` 的 §P5 取消說明）。
畫成單一路徑，另加註記說明原規劃與實測結果。展示一個已被否證的分流會誤導人。

⚠️ AUC 圖的數字**一律從 `data/results/signals_all.md` 讀**，不手抄——
手抄的數字會在下次重跑後悄悄過期。

用法：
    python scripts/make_figures.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIGS = ROOT / "figs"
RESULTS = ROOT / "data" / "results"

# 中文標籤用的字型。找不到就退回預設並警告——不要靜默畫出一堆豆腐字。
CJK_CANDIDATES = ("Microsoft JhengHei", "Microsoft YaHei", "PMingLiU",
                  "Noto Sans CJK TC", "Heiti TC", "Arial Unicode MS")


def setup_font():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt

    have = {f.name for f in fm.fontManager.ttflist}
    for name in CJK_CANDIDATES:
        if name in have:
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return name
    print("⚠️ 找不到中文字型，中文標籤會變成方框", file=sys.stderr)
    return None


def missing_glyphs(font_name: str, texts) -> list[str]:
    """回傳字型缺少的字元。

    ⚠️ **缺字只會出 UserWarning，圖照樣產出但字變成豆腐方框。**
    備審資料印出來才發現就來不及了，所以在畫圖之前先擋。

    Microsoft JhengHei 實測缺 `✕ ✗ ⇒ ⚠ ≤` 與所有 emoji——
    這些在編輯器裡看起來完全正常，只有輸出的圖會壞。
    """
    try:
        import matplotlib.font_manager as fm
        from fontTools.ttLib import TTFont
    except ImportError:
        return []
    paths = [f.fname for f in fm.fontManager.ttflist if f.name == font_name]
    if not paths:
        return []
    cmap: set[int] = set()
    try:
        tt = TTFont(paths[0], fontNumber=0)
        for tbl in tt["cmap"].tables:
            cmap |= set(tbl.cmap)
    except Exception:  # noqa: BLE001
        return []
    bad = set()
    for s in texts:
        for ch in s:
            # ASCII 與 CJK 一定有；只查符號區
            if ord(ch) > 0x2000 and ord(ch) not in cmap:
                bad.add(ch)
    return sorted(bad)


def assert_glyphs(font_name: str | None, texts) -> None:
    if not font_name:
        return
    bad = missing_glyphs(font_name, texts)
    if bad:
        detail = "　".join(f"{c!r} U+{ord(c):04X}" for c in bad)
        raise SystemExit(
            f"🔴 {font_name} 缺少這些字元，圖上會變成豆腐方框：{detail}\n"
            f"   請改用該字型有的字元，或換一個字型。")


# ═══════════════ 【2】架構圖 ═══════════════

LABEL = {
    "in": "使用者輸入",
    "sig": "語意路由器\n（訊號量測 S1–S8）",
    "anchor": "語意錨點建構\nreflect",
    "multi": "多視角驗證\n平行翻譯 + 回譯比對",
    "reflect": "反思代理人\n差異定位 → 修正錨點",
    "mem": "動態記憶模組\nChromaDB + 滾動摘要",
    "out": "輸出\n譯文 + 決策時間軸 + 澄清提問",
}

LOOP_LABEL = "未通過\n則重試\n（最多 3 次）"

# ⚠️ 註記文字放在這裡讓 SVG 與 PNG 兩個分支共用。
#    先前兩邊各寫一份，那遲早會漂移成兩張說法不同的圖。
FASTPATH_TITLE = "× 原規劃：訊號導向的快速通道"
FASTPATH_NOTE = [
    "計畫書假設「簡單問題走快速通道、",
    "困難問題走完整驗證」，以此換取",
    "成本與準確度的平衡。",
    "",
    "實測否證：八個訊號的 AUC 落在",
    "0.463–0.532，未加權總和 0.477，",
    "純句長基準 0.517——十個量測的",
    "95% CI 全數涵蓋 0.5。",
    "",
    "→ 無法預測哪些題目需要驗證，",
    "　 任何分流都不優於隨機。",
    "　 故本系統走單一路徑。",
]
FOOTER = ("取消 P5／P6 的決定與理由見技術報告 §5.1；"
          "AUC 完整結果見 figs/auc_summary.png")


def architecture_svg() -> str:
    """手寫 SVG。用 matplotlib 畫流程圖會很醜，而且框線對不齊。"""
    W, H = 980, 720
    box = ("<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' "
           "fill='{fill}' stroke='{stroke}' stroke-width='2'/>")

    def text(x, y, s, *, size=15, weight="normal", fill="#1a1a1a", anchor="middle"):
        out = []
        for i, line in enumerate(s.split("\n")):
            dy = y + i * (size + 5)
            out.append(f"<text x='{x}' y='{dy}' font-size='{size}' "
                       f"font-weight='{weight}' fill='{fill}' "
                       f"text-anchor='{anchor}' "
                       f"font-family='Microsoft JhengHei, sans-serif'>"
                       f"{line}</text>")
        return "".join(out)

    def arrow(x1, y1, x2, y2, label=""):
        s = (f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' "
             f"stroke='#555' stroke-width='2' marker-end='url(#a)'/>")
        if label:
            s += text((x1 + x2) / 2 + 8, (y1 + y2) / 2 - 6, label,
                      size=12, fill="#666", anchor="start")
        return s

    cx = 330                      # 主流程的中心線
    bw, bh = 300, 62              # 方塊寬高
    # 7 個節點各一列。原本只給 6 個 y，輸出框與記憶模組畫在同一格而重疊。
    ys = [30, 118, 206, 294, 382, 470, 558]

    p = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' "
         f"viewBox='0 0 {W} {H}'>",
         "<defs><marker id='a' viewBox='0 0 10 10' refX='9' refY='5' "
         "markerWidth='7' markerHeight='7' orient='auto'>"
         "<path d='M 0 0 L 10 5 L 0 10 z' fill='#555'/></marker></defs>",
         f"<rect width='{W}' height='{H}' fill='#ffffff'/>"]

    nodes = [("in", "#eef2f7", "#7a8ba0"),
             ("sig", "#fff4e0", "#d9a441"),
             ("anchor", "#eaf3ea", "#6b9a6b"),
             ("multi", "#eaf3ea", "#6b9a6b"),
             ("reflect", "#eaf3ea", "#6b9a6b"),
             ("mem", "#efeaf5", "#8a7aa8")]
    for (key, fill, stroke), y in zip(nodes, ys):
        p.append(box.format(x=cx - bw // 2, y=y, w=bw, h=bh,
                            fill=fill, stroke=stroke))
        lines = LABEL[key].split("\n")
        p.append(text(cx, y + (bh // 2) - (len(lines) - 1) * 9 + 5,
                      LABEL[key], size=15 if len(lines) == 1 else 14,
                      weight="bold" if len(lines) == 1 else "normal"))
    # 輸出框
    y_out = ys[6]
    p.append(box.format(x=cx - bw // 2, y=y_out, w=bw, h=bh,
                        fill="#eef2f7", stroke="#7a8ba0"))
    p.append(text(cx, y_out + 26, LABEL["out"], size=13))

    for a, b in zip(ys, ys[1:]):
        p.append(arrow(cx, a + bh, cx, b - 4))

    # 反思迴圈：reflect → multi
    lx = cx - bw // 2 - 26
    p.append(f"<path d='M {cx - bw // 2} {ys[4] + bh // 2} H {lx} "
             f"V {ys[3] + bh // 2} H {cx - bw // 2 - 4}' fill='none' "
             f"stroke='#6b9a6b' stroke-width='2' stroke-dasharray='6 4' "
             f"marker-end='url(#a)'/>")
    p.append(text(lx - 8, ys[3] + bh + 26, LOOP_LABEL,
                  size=11, fill="#6b9a6b", anchor="end"))

    # ── 右側註記：原規劃的快速通道與實測結果 ──
    nx, nw = 660, 290
    p.append(f"<rect x='{nx}' y='{ys[1] - 10}' width='{nw}' height='300' rx='10' "
             f"fill='#fdf0f0' stroke='#c66' stroke-width='2' "
             f"stroke-dasharray='7 5'/>")
    p.append(text(nx + 16, ys[1] + 16, FASTPATH_TITLE,
                  size=14, weight="bold", fill="#a33", anchor="start"))
    note = FASTPATH_NOTE
    for i, line in enumerate(note):
        p.append(text(nx + 16, ys[1] + 44 + i * 17, line,
                      size=12, fill="#663", anchor="start"))

    # 底部說明
    p.append(text(W // 2, H - 18, FOOTER, size=11, fill="#888"))
    p.append("</svg>")
    return "\n".join(p)


def make_architecture() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    svg = architecture_svg()
    (FIGS / "architecture.svg").write_text(svg, encoding="utf-8")
    print(f"  {FIGS / 'architecture.svg'}")

    # SVG → PNG。cairosvg 最可靠；沒有就用 matplotlib 重畫一版。
    png = FIGS / "architecture.png"
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                         write_to=str(png), scale=2.5)
        print(f"  {png}　（cairosvg）")
        return
    except ImportError:
        pass
    _architecture_png_matplotlib(png)


def _architecture_png_matplotlib(png: pathlib.Path) -> None:
    """沒有 cairosvg 時的備援：用 matplotlib 畫同一張圖。

    ⚠️ 內容必須與 SVG 一致——包括那個「快速通道實測不可行」的註記。
    """
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9.8, 7.2), dpi=300)
    ax.set_xlim(0, 980)
    ax.set_ylim(720, 0)
    ax.axis("off")

    cx, bw, bh = 330, 300, 62
    # 7 個節點各一列。原本只給 6 個 y，輸出框與記憶模組畫在同一格而重疊。
    ys = [30, 118, 206, 294, 382, 470, 558]
    nodes = [("in", "#eef2f7", "#7a8ba0"), ("sig", "#fff4e0", "#d9a441"),
             ("anchor", "#eaf3ea", "#6b9a6b"), ("multi", "#eaf3ea", "#6b9a6b"),
             ("reflect", "#eaf3ea", "#6b9a6b"), ("mem", "#efeaf5", "#8a7aa8")]
    for (key, fill, stroke), y in zip(nodes, ys):
        ax.add_patch(mpatches.FancyBboxPatch(
            (cx - bw / 2, y), bw, bh, boxstyle="round,pad=0,rounding_size=10",
            facecolor=fill, edgecolor=stroke, linewidth=1.6))
        ax.text(cx, y + bh / 2, LABEL[key], ha="center", va="center",
                fontsize=9.5, linespacing=1.5)
    y_out = ys[6]
    ax.add_patch(mpatches.FancyBboxPatch(
        (cx - bw / 2, y_out), bw, bh, boxstyle="round,pad=0,rounding_size=10",
        facecolor="#eef2f7", edgecolor="#7a8ba0", linewidth=1.6))
    ax.text(cx, y_out + bh / 2, LABEL["out"], ha="center", va="center",
            fontsize=8.5, linespacing=1.5)

    for a, b in zip(ys, ys[1:]):
        ax.annotate("", xy=(cx, b - 2), xytext=(cx, a + bh),
                    arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.6))
    lx = cx - bw / 2 - 26
    ax.annotate("", xy=(cx - bw / 2 - 2, ys[3] + bh / 2),
                xytext=(lx, ys[3] + bh / 2),
                arrowprops=dict(arrowstyle="-|>", color="#6b9a6b", lw=1.6))
    ax.plot([cx - bw / 2, lx, lx], [ys[4] + bh / 2, ys[4] + bh / 2,
                                    ys[3] + bh / 2],
            color="#6b9a6b", lw=1.6, ls=(0, (6, 4)))
    ax.text(lx - 8, ys[3] + bh + 34, "未通過\n則重試\n（最多 3 次）",
            ha="right", va="top", fontsize=7.5, color="#6b9a6b",
            linespacing=1.5)

    nx = 660
    ax.add_patch(mpatches.FancyBboxPatch(
        (nx, ys[1] - 10), 290, 300, boxstyle="round,pad=0,rounding_size=10",
        facecolor="#fdf0f0", edgecolor="#cc6666", linewidth=1.6,
        linestyle=(0, (7, 5))))
    ax.text(nx + 16, ys[1] + 12, FASTPATH_TITLE,
            fontsize=9.5, fontweight="bold", color="#aa3333", va="top")
    note = "\n".join(FASTPATH_NOTE)
    ax.text(nx + 16, ys[1] + 44, note, fontsize=7.8, color="#665533",
            va="top", linespacing=1.6)
    ax.text(490, 704, FOOTER, ha="center", fontsize=7,
            color="#888888")

    fig.tight_layout(pad=0.2)
    fig.savefig(png, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  {png}　（matplotlib 備援）")


# ═══════════════ 【3】AUC 圖 ═══════════════

DISPLAY = {
    "S1_polysemy": "S1 多義詞詞表",
    "S2_subject_ellipsis": "S2 主詞省略",
    "S3_syntactic_complexity": "S3 句法複雜度",
    "S4_cultural": "S4 成語命中",
    "S5_llm_direct": "S5 LLM 自評歧義",
    "S6_roundtrip": "S6 往返保真度",
    "S7_n_readings": "S7 讀法數",
    "S8_semantic_entropy": "S8 語意熵",
    "未加權總和": "未加權總和",
    "純句長基準": "純句長基準",
}


def read_auc() -> tuple[list[dict], float]:
    """自 signals_all.md 讀 AUC 與 CI。**不手抄。**"""
    f = RESULTS / "signals_all.md"
    if not f.exists():
        raise SystemExit(f"🔴 缺少 {f}")
    t = f.read_text(encoding="utf-8")
    i, j = t.find("### 主表"), t.find("### vs 純句長")
    body = t[i:j]
    rows = []
    for line in body.splitlines():
        m = re.match(r"\|\s*(S\d_\w+)\s*\|\s*([\d.]+)\s*\|\s*[\d.—]+\s*\|"
                     r"\s*\[([\d.]+),\s*([\d.]+)\]", line)
        if m:
            rows.append({"name": m.group(1), "auc": float(m.group(2)),
                         "lo": float(m.group(3)), "hi": float(m.group(4)),
                         "control": False,
                         "untestable": "不可檢定" in line})
        m2 = re.match(r"\|\s*\*\*(未加權總和|純句長基準)\*\*\s*\|\s*([\d.]+)\s*\|"
                      r"\s*[\d.—]+\s*\|\s*\[([\d.]+),\s*([\d.]+)\]", line)
        if m2:
            rows.append({"name": m2.group(1), "auc": float(m2.group(2)),
                         "lo": float(m2.group(3)), "hi": float(m2.group(4)),
                         "control": True, "untestable": False})
    thr = re.search(r"required_auc = \*\*([\d.]+)\*\*", t)
    return rows, float(thr.group(1)) if thr else 0.626


def make_auc() -> None:
    import matplotlib.pyplot as plt

    rows, thr = read_auc()
    if not rows:
        raise SystemExit("🔴 從 signals_all.md 抽不到 AUC")
    rows.sort(key=lambda r: r["auc"])

    labels = [DISPLAY.get(r["name"], r["name"]) for r in rows]
    vals = [r["auc"] for r in rows]
    err = [[r["auc"] - r["lo"] for r in rows], [r["hi"] - r["auc"] for r in rows]]
    colors = ["#8a7aa8" if r["control"] else
              ("#bbbbbb" if r["untestable"] else "#4a7fb5") for r in rows]

    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=300)
    y = range(len(rows))
    # ⚠️ 長條從 **0.5** 起算，不是從軸的左端。
    #    從軸端起算的話，AUC 0.463 的長條看起來很長——那是軸截斷造成的錯覺，
    #    會讓「全部貼近隨機」這個結論在視覺上完全消失。
    #    以 0.5 為基準時，長條的長度直接就是「偏離隨機多少」。
    ax.barh(list(y), [v - 0.5 for v in vals], left=0.5, color=colors,
            height=0.62, zorder=3, edgecolor="white", linewidth=0.8)
    ax.errorbar(vals, list(y), xerr=err, fmt="none", ecolor="#333",
                elinewidth=1.3, capsize=4, zorder=4)

    ax.axvline(0.5, color="#c0392b", lw=1.8, zorder=5)
    ax.axvline(thr, color="#d9a441", lw=1.8, ls="--", zorder=5)
    ax.text(0.5, len(rows) - 0.25, " 隨機基準 0.5", color="#c0392b",
            fontsize=9, va="bottom")
    ax.text(thr, len(rows) - 0.25, f" 顯著門檻 {thr:.3f}", color="#b8860b",
            fontsize=9, va="bottom")

    for i, r in enumerate(rows):
        ax.text(r["hi"] + 0.008, i, f"{r['auc']:.3f}", va="center",
                fontsize=8.5, color="#333")

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0.38, 0.70)
    ax.set_ylim(-0.7, len(rows) - 0.05)
    ax.set_xlabel("AUC（預測「模型會選錯義項」）　長條以 0.5 為基準，"
                  "誤差線為 95% CI", fontsize=10)
    ax.set_title("RQ1：十個量測全部涵蓋 0.5，無一顯著",
                 fontsize=13, fontweight="bold", pad=14)
    ax.grid(axis="x", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor="#4a7fb5", label="候選訊號"),
        Patch(facecolor="#bbbbbb", label="不可檢定（並列上限低於門檻）"),
        Patch(facecolor="#8a7aa8", label="對照組"),
    ], loc="lower right", fontsize=8.5, framealpha=0.95)

    fig.text(0.012, 0.012,
             "n=399（錯 118／對 281）　門檻含實測 25% 標籤噪音　"
             "Holm 校正後無一顯著　數字自 data/results/signals_all.md 讀取",
             fontsize=7.2, color="#777")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = FIGS / "auc_summary.png"
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  {out}　{len(rows)} 列　300 dpi")


def figure_texts() -> list[str]:
    """圖上會出現的所有文字。字型檢查用。

    只收**真的會畫進圖裡**的字串——docstring 與註解裡的符號（例如 ⚠）
    不進圖，掃進來只會製造假警報。
    """
    return ([*LABEL.values(), *DISPLAY.values(), *FASTPATH_NOTE,
             LOOP_LABEL, FASTPATH_TITLE, FOOTER,
             "AUC（預測「模型會選錯義項」）　長條以 0.5 為基準，誤差線為 95% CI",
             "RQ1：十個量測全部涵蓋 0.5，無一顯著",
             " 隨機基準 0.5", " 顯著門檻 0.626",
             "候選訊號", "不可檢定（並列上限低於門檻）", "對照組",
             "n=399（錯 118／對 281）　門檻含實測 25% 標籤噪音　"
             "Holm 校正後無一顯著　數字自 data/results/signals_all.md 讀取"])


def main() -> int:
    import warnings
    # 缺字只會出 UserWarning，圖照樣產出但字變豆腐方框——升級成錯誤，
    # 免得備審資料印出來才發現。
    warnings.filterwarnings("error", message="Glyph .* missing from font",
                            category=UserWarning)
    font = setup_font()
    print(f"字型：{font or '（預設，中文會變方框）'}")
    assert_glyphs(font, figure_texts())
    print("字型檢查：圖上用到的字元都有\n")
    FIGS.mkdir(parents=True, exist_ok=True)
    print("【2】架構圖")
    make_architecture()
    print("\n【3】AUC 圖")
    make_auc()
    return 0


if __name__ == "__main__":
    sys.exit(main())
