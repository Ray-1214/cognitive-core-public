"""產生 docs/Cognitive-Core_進度報告_20260817.pptx

所有數字取自 repo 內的實際產物（git log、pytest、data/ 下的結果檔），
不得手抄。改數字請改本檔的 FACTS 區塊並重跑。

    python scripts/make_progress_ppt.py
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Emu, Inches, Pt

OUT = Path(__file__).resolve().parents[1] / "docs" / "Cognitive-Core_進度報告_20260817.pptx"

# ─────────────────────────── 設計常數 ───────────────────────────

FONT = "微軟正黑體"
FONT_NUM = "Segoe UI Semibold"

INK = RGBColor(0x1A, 0x23, 0x32)
MUTED = RGBColor(0x5A, 0x6B, 0x7C)
FAINT = RGBColor(0x8E, 0x9E, 0xAB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

ACCENT = RGBColor(0x0E, 0x7C, 0x86)
ACCENT_DK = RGBColor(0x0A, 0x4F, 0x57)
NAVY = RGBColor(0x10, 0x21, 0x33)

GREEN = RGBColor(0x2F, 0x7D, 0x4F)
AMBER = RGBColor(0xB0, 0x72, 0x12)
RED = RGBColor(0xA8, 0x38, 0x2C)
GRAYD = RGBColor(0x8A, 0x9A, 0xA8)

CARD = RGBColor(0xF5, 0xF8, 0xF9)
CARD2 = RGBColor(0xEC, 0xF3, 0xF4)
BORDER = RGBColor(0xDA, 0xE3, 0xE7)
RULE = RGBColor(0xE4, 0xEA, 0xED)

SW, SH = 13.333, 7.5
ML = 0.72              # 左邊界
CW = SW - 2 * ML       # 內容寬
TOP = 1.62             # 內容起始 y

# ─────────────────────────── FACTS（取自 repo 實際產物）───────────────────────────

F = {
    "date": "2026-08-17",
    "span": "2026-08-09 – 08-17",
    "days": 9,
    "commits": 20,
    "tests": 141,
    "loc_src": 2097,
    "loc_tests": 1256,
    "loc_scripts": 4105,
    "papers": 4,
}

# ─────────────────────────── 基礎繪圖工具 ───────────────────────────


def _tf(shape, *, wrap=True, anchor=MSO_ANCHOR.TOP, margin=0.0):
    tf = shape.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    m = Inches(margin)
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = m
    return tf


def text(
    slide, x, y, w, h, body, *, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT,
    font=FONT, spacing=1.25, anchor=MSO_ANCHOR.TOP, space_after=0,
):
    """body 可為 str 或 [(文字, 覆寫dict), ...] 的 run 清單，或段落清單。"""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = _tf(box, anchor=anchor)
    paras = body if isinstance(body, list) else [body]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        runs = para if isinstance(para, list) else [(para, {})]
        for content, ov in runs:
            r = p.add_run()
            r.text = content
            f = r.font
            f.name = ov.get("font", font)
            f.size = Pt(ov.get("size", size))
            f.bold = ov.get("bold", bold)
            f.color.rgb = ov.get("color", color)
    return box


def box(slide, x, y, w, h, *, fill=CARD, line=BORDER, lw=1.0,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(lw)
    sp.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:  # 圓角半徑
            sp.adjustments[0] = radius
        except Exception:
            pass
    sp.text_frame.text = ""
    return sp


def rule(slide, x, y, w, *, color=RULE, thick=1.0):
    sp = box(slide, x, y, w, thick / 72.0, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    return sp


def chip(slide, x, y, w, h, label, *, fg=WHITE, bg=ACCENT, size=10.5, bold=True):
    sp = box(slide, x, y, w, h, fill=bg, line=None, radius=0.5)
    tf = _tf(sp, anchor=MSO_ANCHOR.MIDDLE, margin=0.02)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = fg
    return sp


def arrow(slide, x, y, w, h=0.16, *, color=RGBColor(0xB7, 0xC5, 0xCC)):
    sp = box(slide, x, y, w, h, fill=color, line=None, shape=MSO_SHAPE.RIGHT_ARROW)
    return sp


# ─────────────────────────── 表格 ───────────────────────────


def _plain_table_style(table):
    tbl = table._tbl
    tblPr = tbl.find(qn("a:tblPr"))
    if tblPr is None:
        tblPr = parse_xml("<a:tblPr %s/>" % nsdecls("a"))
        tbl.insert(0, tblPr)
    for el in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(el)
    tblPr.append(
        parse_xml(
            "<a:tableStyleId %s>{2D5ABB26-0587-4C30-8999-92F81FD0307C}</a:tableStyleId>"
            % nsdecls("a")
        )
    )
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")


def table(
    slide, x, y, w, rows, *, col_w=None, header=True, size=11.5, head_size=11,
    row_h=0.42, head_h=0.42, aligns=None, head_bg=ACCENT_DK, zebra=True,
    row_colors=None,
):
    """rows[0] 為表頭。cell 可為 str 或 (str, {覆寫}). """
    nrow, ncol = len(rows), len(rows[0])
    h = head_h + row_h * (nrow - 1)
    gf = slide.shapes.add_table(nrow, ncol, Inches(x), Inches(y), Inches(w), Inches(h))
    tb = gf.table
    _plain_table_style(tb)
    tb.first_row = False
    tb.horz_banding = False

    if col_w:
        total = sum(col_w)
        for i, cwv in enumerate(col_w):
            tb.columns[i].width = Emu(int(Inches(w) * cwv / total))
    tb.rows[0].height = Inches(head_h)
    for i in range(1, nrow):
        tb.rows[i].height = Inches(row_h)

    aligns = aligns or [PP_ALIGN.LEFT] * ncol

    for ri, row in enumerate(rows):
        is_head = header and ri == 0
        for ci, cell_v in enumerate(row):
            cell = tb.cell(ri, ci)
            content, ov = (cell_v, {}) if isinstance(cell_v, str) else cell_v
            cell.fill.solid()
            if is_head:
                cell.fill.fore_color.rgb = head_bg
            elif row_colors and row_colors.get(ri):
                cell.fill.fore_color.rgb = row_colors[ri]
            else:
                cell.fill.fore_color.rgb = (
                    CARD if (zebra and ri % 2 == 0) else WHITE
                )
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.11)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = ov.get("align", aligns[ci])
            p.line_spacing = 1.0
            r = p.add_run()
            r.text = content
            r.font.name = ov.get("font", FONT)
            r.font.size = Pt(ov.get("size", head_size if is_head else size))
            r.font.bold = ov.get("bold", is_head)
            r.font.color.rgb = ov.get("color", WHITE if is_head else INK)
    return tb


# ─────────────────────────── 版型 ───────────────────────────

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]
_n = [0]


def slide(title, kicker=None, *, sub=None):
    s = prs.slides.add_slide(BLANK)
    _n[0] += 1
    y = 0.42
    if kicker:
        text(s, ML, y, CW, 0.28, kicker, size=11.5, color=ACCENT, bold=True, spacing=1.0)
        y += 0.30
    text(s, ML, y, CW, 0.55, title, size=27, color=INK, bold=True, spacing=1.0)
    rule(s, ML, 1.26, 1.5, color=ACCENT, thick=2.6)
    if sub:
        text(s, ML, 1.32, CW, 0.26, sub, size=12, color=MUTED, spacing=1.0)
    footer(s)
    return s


def footer(s):
    text(s, ML, SH - 0.46, 6.0, 0.3, "Cognitive-Core ｜ 進度報告 " + F["date"],
         size=9.5, color=FAINT, spacing=1.0)
    text(s, SW - ML - 1.0, SH - 0.46, 1.0, 0.3, f"{_n[0]:02d}",
         size=9.5, color=FAINT, align=PP_ALIGN.RIGHT, spacing=1.0)


def stat(s, x, y, w, h, value, label, *, note=None, color=ACCENT, vsize=30):
    box(s, x, y, w, h, fill=CARD, line=BORDER)
    box(s, x, y, 0.055, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    text(s, x + 0.26, y + 0.16, w - 0.4, 0.55, value, size=vsize, color=color,
         bold=True, font=FONT_NUM, spacing=1.0)
    text(s, x + 0.28, y + 0.72, w - 0.44, 0.3, label, size=11.5, color=INK,
         bold=True, spacing=1.0)
    if note:
        text(s, x + 0.28, y + 1.0, w - 0.44, 0.4, note, size=9.5, color=MUTED, spacing=1.15)


def bullets(s, x, y, w, items, *, size=13, gap=0.44, marker="—", mcolor=ACCENT):
    """items: str 或 (粗體前綴, 說明)"""
    cy = y
    for it in items:
        text(s, x, cy, 0.3, 0.3, marker, size=size, color=mcolor, bold=True, spacing=1.0)
        if isinstance(it, tuple):
            head, tail = it
            runs = [(head, {"bold": True, "color": INK}), (tail, {"color": MUTED})]
        else:
            runs = [(it, {"color": INK})]
        text(s, x + 0.3, cy - 0.015, w - 0.3, gap, [runs], size=size, spacing=1.32)
        cy += gap
    return cy


# ═══════════════════════════ S1 封面 ═══════════════════════════

s = prs.slides.add_slide(BLANK)
box(s, 0, 0, SW, SH, fill=NAVY, line=None, shape=MSO_SHAPE.RECTANGLE)
box(s, 0, 0, 0.22, SH, fill=ACCENT, line=None, shape=MSO_SHAPE.RECTANGLE)
# 裝飾
box(s, SW - 4.6, -1.4, 6.0, 6.0, fill=RGBColor(0x16, 0x2C, 0x40), line=None,
    shape=MSO_SHAPE.OVAL)
box(s, SW - 2.9, 1.4, 3.4, 3.4, fill=RGBColor(0x1B, 0x3A, 0x4A), line=None,
    shape=MSO_SHAPE.OVAL)

text(s, 1.15, 1.62, 9.0, 0.35, "專題研究　期中進度報告", size=13,
     color=RGBColor(0x6F, 0xC5, 0xCC), bold=True, spacing=1.0)
text(s, 1.1, 2.05, 10.0, 1.0, "Cognitive-Core", size=54, color=WHITE, bold=True,
     spacing=1.0, font="Segoe UI Semibold")
text(s, 1.15, 3.08, 9.6, 0.9,
     "基於代理人工作流與多視角語意驗證之自適應認知框架",
     size=19, color=RGBColor(0xC8, 0xD8, 0xE0), spacing=1.3)
rule(s, 1.15, 4.12, 2.2, color=ACCENT, thick=2.6)

text(s, 1.15, 4.42, 10.0, 1.2,
     [[("開發期間　", {"color": RGBColor(0x7F, 0x93, 0xA2)}),
       (f"{F['span']}（{F['days']} 天）", {"color": WHITE, "bold": True})],
      [("報告日期　", {"color": RGBColor(0x7F, 0x93, 0xA2)}),
       (F["date"], {"color": WHITE, "bold": True})],
      [("報告人　　", {"color": RGBColor(0x7F, 0x93, 0xA2)}),
       ("（請填入姓名）", {"color": RGBColor(0xA8, 0xBA, 0xC6)})]],
     size=13, spacing=1.55)

for i, (v, l) in enumerate([(f"{F['commits']}", "commits"),
                            (f"{F['tests']}", "測試全通過"),
                            ("1.5 / 8", "階段完成")]):
    x = 1.15 + i * 2.15
    text(s, x, 6.05, 2.0, 0.5, v, size=26, color=RGBColor(0x6F, 0xC5, 0xCC),
         bold=True, font=FONT_NUM, spacing=1.0)
    text(s, x, 6.56, 2.0, 0.3, l, size=10.5, color=RGBColor(0x7F, 0x93, 0xA2), spacing=1.0)

# ═══════════════════════════ S2 一頁摘要 ═══════════════════════════

s = slide("一頁摘要", "EXECUTIVE SUMMARY")

stat(s, ML, TOP, 2.85, 1.5, f"{F['days']} 天", "實際開發時間",
     note=f"{F['commits']} 次 commit，08/09 起算", color=ACCENT)
stat(s, ML + 3.05, TOP, 2.85, 1.5, f"{F['tests']}", "項自動化測試全通過",
     note="全離線，不呼叫任何 API", color=GREEN)
stat(s, ML + 6.10, TOP, 2.85, 1.5, "7,458", "行程式碼",
     note=f"src {F['loc_src']}／tests {F['loc_tests']}／scripts {F['loc_scripts']}",
     color=ACCENT)
stat(s, ML + 9.15, TOP, 2.74, 1.5, "1.5 / 8", "階段完成",
     note="P1 完成、P2 前置驗證完成", color=AMBER)

y = TOP + 1.85
text(s, ML, y, CW, 0.34, "三句話總結", size=15, color=INK, bold=True, spacing=1.0)
y += 0.44
bullets(s, ML, y, CW, [
    ("系統骨架已可端到端執行。　",
     "LangGraph 狀態機、CLI 三個子命令（run／batch／golden）、四種驗證 profile 走同一條程式碼路徑，重跑結果一致。"),
    ("主資料來源已完成前置驗證。　",
     "CWN-SemCor（中研院平衡語料庫 + 中文詞網，六位語言學背景母語者標註）確認可用、授權為 MIT，21,098 句可篩。"),
    ("最有價值的產出是一項負面發現。　",
     "既有中文歧義資料集普遍受「長度混淆」污染——一個只數字數的分類器就能達到 AUC 0.965。此發現推翻了本專案前期的全部量測，也促成資料設計改版。"),
], size=13, gap=0.62)

box(s, ML, 6.28, CW, 0.62, fill=CARD2, line=BORDER)
text(s, ML + 0.24, 6.42, CW - 0.5, 0.4,
     [[("目前狀態　", {"bold": True, "color": ACCENT_DK}),
       ("基礎設施與方法學已就緒，尚未產出主實驗數據。距 10 月截止約 6 週，剩餘 6 個階段皆已有明確規格與完成定義。",
        {"color": INK})]],
     size=12, spacing=1.2)

# ═══════════════════════════ S3 研究問題 ═══════════════════════════

s = slide("研究問題與核心主張", "RESEARCH QUESTIONS")

box(s, ML, TOP, CW, 0.86, fill=CARD2, line=None)
box(s, ML, TOP, 0.055, 0.86, fill=ACCENT, line=None, shape=MSO_SHAPE.RECTANGLE)
text(s, ML + 0.3, TOP + 0.14, CW - 0.6, 0.6,
     "核心主張：用「系統架構」的設計（System 2 Thinking），而非單純堆疊模型算力，來提升 AI 的理解精確度。",
     size=15, color=ACCENT_DK, bold=True, spacing=1.25)

text(s, ML, TOP + 1.06, CW, 0.3,
     "作法：把中文的模糊處翻譯成語法上必須講清楚的語言（日文強制敬語階層、英文強制時態與單複數），"
     "再從多語言視角回譯比對。哪裡對不上，哪裡就是原文的歧義點。",
     size=12, color=MUTED, spacing=1.3)

table(s, ML, TOP + 1.72, CW, [
    ["RQ", "計畫書原文", "本階段確立的操作型定義", "狀態"],
    ["RQ1", "模型如何知道自己「沒聽懂」？",
     "能否預測模型在翻譯時會選錯詞義（客觀、可自動判定）", "方法已定案"],
    ["RQ2", "Router 如何讓簡單問題走快速通道？",
     "成本–準確度前緣曲線上，本系統是否位於等算力對照組上方", "待 P5"],
    ["RQ3", "RAG + 滑動視窗如何避免 Lost in the Middle？",
     "有無記憶模組的中段召回率對照（降級為初步驗證）", "待 P7"],
], col_w=[0.7, 3.2, 5.6, 1.5], row_h=0.62, head_h=0.44, size=11.5,
   aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER])

box(s, ML, 6.22, CW, 0.68, fill=RGBColor(0xFD, 0xF6, 0xE9), line=RGBColor(0xEB, 0xD9, 0xB4))
text(s, ML + 0.24, 6.34, CW - 0.5, 0.5,
     [[("RQ1 為何改寫　", {"bold": True, "color": AMBER}),
       ("「這句話歧不歧義」是主觀標籤，連 CHAmbi、Wu et al. 的原作者都聲明其標註目標是與人類判斷對齊，而非定義唯一正解；"
        "「模型有沒有選錯詞義」則是客觀的，且直接就是下游損害本身。",
        {"color": INK})]],
     size=11.5, spacing=1.25)

# ═══════════════════════════ S4 系統架構 ═══════════════════════════

s = slide("系統架構與各模組實作狀態", "SYSTEM ARCHITECTURE",
          sub="四個模組，兩條通道。慢速通道才付多視角驗證的成本。")

# 輸入
box(s, 0.72, 3.07, 1.30, 1.25, fill=WHITE, line=BORDER)
text(s, 0.80, 3.44, 1.14, 0.6, "使用者\n輸入", size=12, color=INK, bold=True,
     align=PP_ALIGN.CENTER, spacing=1.28)
arrow(s, 2.08, 3.615, 0.30)

# ① Router
box(s, 2.45, 2.77, 2.75, 1.85, fill=CARD, line=ACCENT, lw=1.5)
text(s, 2.61, 2.92, 2.45, 0.3, "① Semantic Router", size=12.5, color=ACCENT_DK,
     bold=True, spacing=1.0)
text(s, 2.61, 3.26, 2.48, 0.66, "S1–S7 訊號 → 歧義分數\n分數 < τ 走快速通道",
     size=10.5, color=MUTED, spacing=1.35)
chip(s, 2.61, 3.98, 2.42, 0.28, "目前為固定樁 · P5 實作", bg=AMBER, size=9.5)

arrow(s, 5.26, 2.34, 0.34, h=0.15)
arrow(s, 5.26, 4.22, 0.34, h=0.15)

# 快速 / 慢速
box(s, 5.66, 1.92, 3.95, 1.00, fill=WHITE, line=BORDER)
text(s, 5.86, 2.07, 3.6, 0.34,
     [[("快速通道　", {"bold": True, "color": GREEN}), ("直接翻譯，1× 推論", {"color": MUTED})]],
     size=11.5, spacing=1.2)
chip(s, 5.86, 2.44, 0.98, 0.28, "已實作", bg=GREEN, size=9.5)

box(s, 5.66, 3.14, 3.95, 2.32, fill=CARD, line=ACCENT, lw=1.5)
text(s, 5.86, 3.26, 3.6, 0.3, "慢速通道", size=11.5, color=ACCENT_DK, bold=True, spacing=1.0)
text(s, 5.86, 3.60, 3.66, 1.2,
     [[("② Multi-View Verifier", {"bold": True, "color": INK})],
      [("　　偵測：單探針往返保真度", {"color": MUTED, "size": 10})],
      [("③ Reflection Agent", {"bold": True, "color": INK})],
      [("　　診斷：多視角差異定位 → 修錨點，迴圈 ≤ R", {"color": MUTED, "size": 10})]],
     size=11, spacing=1.3)
chip(s, 5.86, 4.88, 0.98, 0.28, "已實作", bg=GREEN, size=9.5)
chip(s, 6.98, 4.88, 1.85, 0.28, "四 profile 走同一路徑", bg=ACCENT, size=9.5)

arrow(s, 9.67, 3.615, 0.30)

# ④ Memory
box(s, 10.04, 2.87, 2.57, 1.65, fill=WHITE, line=BORDER)
text(s, 10.22, 3.02, 2.3, 0.3, "④ Dynamic Memory", size=11.5, color=INK, bold=True,
     spacing=1.0)
text(s, 10.22, 3.36, 2.32, 0.66, "ChromaDB 向量檢索\n＋ 滾動摘要", size=10.5,
     color=MUTED, spacing=1.35)
chip(s, 10.22, 4.04, 1.5, 0.28, "未開始 · P7", bg=GRAYD, size=9.5)

text(s, ML, 5.64, CW, 0.34,
     "輸出：譯文　＋　結構化決策摘要　＋　不確定性報告（顯示決策記錄，不揭露模型原始推理文字）",
     size=11.5, color=MUTED, align=PP_ALIGN.CENTER, spacing=1.0)

box(s, ML, 6.24, CW, 0.66, fill=CARD2, line=BORDER)
text(s, ML + 0.24, 6.36, CW - 0.5, 0.48,
     [[("本階段的架構修正　", {"bold": True, "color": ACCENT_DK}),
       ("原設計把最貴的操作（多視角平行翻譯）放在偵測階段，等於每句都付診斷成本。"
        "改為「偵測／診斷分離」：偵測用單探針往返（1 翻 + 1 回譯），多視角只在慢速通道做診斷。",
        {"color": INK})]],
     size=11.5, spacing=1.22)

# ═══════════════════════════ S5 進度總覽 ═══════════════════════════

s = slide("八階段進度總覽", "PROGRESS OVERVIEW",
          sub="實作路徑於 08/14 定案（docs/完整架構與分階段實作路徑 v3），每階段皆有完成定義（DoD）。")

DONE = RGBColor(0xEC, 0xF6, 0xF0)
NOW = RGBColor(0xFD, 0xF6, 0xE9)

table(s, ML, TOP + 0.30, CW, [
    ["階段", "內容", "產出", "估時", "狀態"],
    ["P1", "管線收尾（狀態機、CLI、取樣自適應）", "CLI 可跑單句／批次／黃金案例", "半天",
     ("● 完成", {"bold": True, "color": GREEN, "align": PP_ALIGN.CENTER})],
    ["P2", "資料層：脈絡恆等 U/A/B 三元組", "≥40 筆通過快篩的三元組", "1.5 天",
     ("● 前置驗證完成", {"bold": True, "color": AMBER, "align": PP_ALIGN.CENTER})],
    ["P3", "判定層 sense_judge（主指標的基礎）", "與人工一致率 ≥ 85%", "半天",
     ("○ 未開始", {"color": GRAYD, "align": PP_ALIGN.CENTER})],
    ["P4", "訊號層：八個偵測訊號各自的 AUC", "RQ1 的答案", "1 天",
     ("○ 未開始", {"color": GRAYD, "align": PP_ALIGN.CENTER})],
    ["P5", "Router：成本–準確度前緣曲線", "RQ2 的答案", "半天",
     ("○ 未開始", {"color": GRAYD, "align": PP_ALIGN.CENTER})],
    ["P6", "主實驗：全對照組 B0/B1/B2/B3 vs E1", "主表 + 三張圖", "1 天",
     ("○ 未開始", {"color": GRAYD, "align": PP_ALIGN.CENTER})],
    ["P7", "Demo 介面 + 記憶模組（RQ3）", "Streamlit + 召回率曲線", "1 天",
     ("○ 未開始", {"color": GRAYD, "align": PP_ALIGN.CENTER})],
    ["P8", "技術報告與打包", "20–30 頁報告、可重現封包", "1 週",
     ("○ 未開始", {"color": GRAYD, "align": PP_ALIGN.CENTER})],
], col_w=[0.72, 4.9, 3.5, 0.85, 1.9], row_h=0.44, head_h=0.42, size=11.5,
   aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
   zebra=True, row_colors={1: DONE, 2: NOW})

text(s, ML, 6.36, CW, 0.5,
     [[("為什麼前八天沒有進到 P2 之後：", {"bold": True, "color": INK}),
       ("架構在 08/13–08/14 兩度被自己的實驗推翻——長度混淆推翻了跨語言訊號的全部數字，"
        "CWN-SemCor 的發現推翻了整個資料層設計。在那之前寫規格書等於白寫。兩件事定案後，"
        "剩餘六階段的規格才一次寫完。", {"color": MUTED})]],
     size=11.5, spacing=1.3)

# ═══════════════════════════ S6 已完成一：基礎設施 ═══════════════════════════

s = slide("已完成（一）：基礎設施與執行管線", "DELIVERED · P1",
          sub="M0 基礎設施 + Phase A 演算法骨架 + P1 離線測試，DoD 全數達成。")

lw = 6.5
text(s, ML, TOP + 0.1, lw, 0.3, "本階段交付的元件", size=14, color=INK, bold=True, spacing=1.0)
bullets(s, ML, TOP + 0.5, lw, [
    ("Provider 抽象層　", "改用 litellm 取代自寫的四家 SDK adapter；統一快取、重試、成本追蹤。"),
    ("LangGraph 狀態機　", "astream_events 可用（P7 的串流介面需要）；source_text 全程不可變。"),
    ("四種驗證 profile　", "跨語言 en+ja／換語言對 en+de／同語言重取樣／單探針，同一條程式碼路徑的不同設定，不是四份實作。"),
    ("反思代理人　", "結構化輸出走降級階梯（json_schema → json_object → 文字解析），依各模型實測能力自動選路。"),
    ("語意錨點資料模型　", "Pydantic 驗證，含 UNKNOWN 不確定性欄位與 alternative_readings。"),
    ("檔案化的 prompt 與語言技能檔　", "5 份 prompt、5 份語言技能檔（zh-TW/en/ja/de/範本），每筆 run log 記錄 prompt hash。"),
], size=12, gap=0.63)

rx2 = ML + lw + 0.4
rw = CW - lw - 0.4
box(s, rx2, TOP + 0.1, rw, 2.05, fill=NAVY, line=None)
text(s, rx2 + 0.24, TOP + 0.26, rw - 0.5, 0.3, "DoD：三個指令皆可執行", size=11.5,
     color=RGBColor(0x6F, 0xC5, 0xCC), bold=True, spacing=1.0)
text(s, rx2 + 0.24, TOP + 0.62, rw - 0.45, 1.4,
     "cli run  --text \"…\" --profile cross_en_ja\ncli batch --dataset data/dev30/sentences.yaml\ncli golden",
     size=10.5, color=RGBColor(0xC8, 0xD8, 0xE0), font="Consolas", spacing=1.55)
text(s, rx2 + 0.24, TOP + 1.72, rw - 0.5, 0.3, "✅ 三個都跑完，runs/*.jsonl 記錄完整，重跑結果一致",
     size=10, color=RGBColor(0x8F, 0xD6, 0xB4), spacing=1.15)

box(s, rx2, TOP + 2.32, rw, 2.0, fill=CARD, line=BORDER)
text(s, rx2 + 0.24, TOP + 2.46, rw - 0.5, 0.3, "可重現性設計", size=11.5, color=ACCENT_DK,
     bold=True, spacing=1.0)
text(s, rx2 + 0.24, TOP + 2.82, rw - 0.5, 1.4,
     ["· 每筆 run 記錄 commit hash ＋ dirty 旗標",
      "· prompt hash 隨每次呼叫寫入",
      "· 快取鍵含取樣參數（temperature／n／seed）",
      "· batch 支援斷點續跑，不重複計費"],
     size=10.5, color=INK, spacing=1.5)

# ═══════════════════════════ S7 已完成二：資料層驗證 ═══════════════════════════

s = slide("已完成（二）：主資料來源驗證", "DELIVERED · P2-D1",
          sub="原則：不驗證完，不寫任何 builder。08/17 完成，結果記於 data/cwn/D1_FINDINGS.md。")

text(s, ML, TOP + 0.28, 6.3, 0.3, "CWN-SemCor 實測結果", size=14, color=INK, bold=True,
     spacing=1.0)
table(s, ML, TOP + 0.66, 6.3, [
    ["查驗項目", "結果"],
    ["HuggingFace 可下載", ("● 可", {"color": GREEN, "bold": True})],
    ["實際授權（dataset card）", ("● MIT，與規格所述相符", {"color": GREEN, "bold": True})],
    ["還原展平後的唯一句子", "21,098 句"],
    ["唯一目標詞", "113 個（皆有 ≥2 個義項）"],
    ["目標詞標記完整性", "284,060 / 284,060 皆含 <目標詞> 標記"],
    ["目標詞在句中恰出現一次", "95.8%"],
    ["繁體純度", "疑似含簡體者 10 / 21,098"],
], col_w=[3.3, 3.0], row_h=0.44, head_h=0.4, size=11)

text(s, ML, TOP + 4.34, 6.3, 0.5,
     "為何決定性：義項來自中文詞網（CWN 2.0）詞典編纂，句子來自中央研究院平衡語料庫，"
     "六位語言學背景母語者標註——取代原本單人＋LLM 起草的 dev-30。",
     size=11, color=MUTED, spacing=1.3)

rx2 = ML + 6.6
rw = CW - 6.6
text(s, rx2, TOP + 0.28, rw, 0.3, "同時完成的四項數字查證", size=14, color=INK, bold=True,
     spacing=1.0)
table(s, rx2, TOP + 0.66, rw, [
    ["規格書中的主張", "查證結果"],
    ["Wu et al. BERT-ft 94.70% / 91.81 F1", ("● 完全吻合", {"color": GREEN, "bold": True})],
    ["中文零形式主詞 36%、英文 4%", ("● 為真", {"color": GREEN, "bold": True})],
    ["Qwen2.5 Base/Instruct 熵差", ("● 定性為真、數值待查", {"color": AMBER, "bold": True})],
    ["CHAmbi 893 歧義／1784 非歧義", ("● 與原文不符，須換掉", {"color": RED, "bold": True})],
], col_w=[3.4, 1.85], row_h=0.48, head_h=0.4, size=10.5)

box(s, rx2, TOP + 3.16, rw, 1.68, fill=RGBColor(0xFC, 0xEF, 0xED),
    line=RGBColor(0xE8, 0xC6, 0xC1))
text(s, rx2 + 0.22, TOP + 3.30, rw - 0.44, 1.4,
     [[("● 查證時發現一篇高度重疊的論文", {"bold": True, "color": RED})],
      [("arXiv:2605.15635（2026-05 投稿）以「翻譯 + 語意熵」偵測中文歧義，"
        "等於本專案演算法 1 的核心，且發表於本專案設計實驗的三個月前。",
        {"color": INK})],
      [("→ novelty 邊界需重新界定；PDF 已下載待研究者自行評估。", {"color": RED, "bold": True})]],
     size=10.5, spacing=1.28)

# ═══════════════════════════ S8 關鍵發現：長度混淆 ═══════════════════════════

s = slide("關鍵發現：中文歧義資料集的「長度混淆」", "KEY FINDING ★",
          sub="本階段最有價值的產出，且不依賴本專案的系統是否有效，可獨立成立。")

box(s, ML, TOP, CW, 0.78, fill=RGBColor(0xFC, 0xEF, 0xED), line=RGBColor(0xE8, 0xC6, 0xC1))
text(s, ML + 0.26, TOP + 0.12, CW - 0.55, 0.6,
     [[("機制　", {"bold": True, "color": RED}),
       ("歧義多半來自「省略」，省略就短；消歧要「寫明」，寫明就長。"
        "於是「歧義句 vs 消歧句」的資料集裡，句長本身就是標籤的代理變數——"
        "一個只數字數的分類器就能拿到高分，而那個分數看起來像模型能力。", {"color": INK})]],
     size=12.5, spacing=1.3)

text(s, ML, TOP + 1.0, CW, 0.3, "以同一支長度基準對所有資料集一視同仁（含本專案自己的 dev-30）",
     size=13, color=INK, bold=True, spacing=1.0)

table(s, ML, TOP + 1.4, CW, [
    ["資料集", "比較方式", "n", "長度 AUC", "95% CI", "判讀"],
    ["Wu et al. 2025", "歧義句（無上下文） vs 消歧句", "136／136",
     ("0.965", {"bold": True, "color": RED, "align": PP_ALIGN.CENTER}), "[0.94, 0.99]",
     ("● 嚴重", {"color": RED, "bold": True, "align": PP_ALIGN.CENTER})],
    ["Wu et al. 2025", "歧義句＋上下文 vs 消歧句", "136／136",
     ("0.712", {"bold": True, "color": AMBER, "align": PP_ALIGN.CENTER}), "[0.65, 0.77]",
     ("● 中度", {"color": AMBER, "bold": True, "align": PP_ALIGN.CENTER})],
    ["CHA-Gen", "歧義句 vs 配對的非歧義句", "2414／2414",
     ("0.503", {"align": PP_ALIGN.CENTER}), "[0.49, 0.52]",
     ("○ 可接受", {"color": GREEN, "align": PP_ALIGN.CENTER})],
    ["本專案 dev-30（修正後）", "歧義句 vs 等長替換消歧句", "30／30",
     ("0.511", {"align": PP_ALIGN.CENTER}), "[0.36, 0.66]",
     ("○ 可接受", {"color": GREEN, "align": PP_ALIGN.CENTER})],
], col_w=[2.5, 4.0, 1.15, 1.3, 1.5, 1.4], row_h=0.44, head_h=0.42, size=11,
   aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER,
           PP_ALIGN.CENTER, PP_ALIGN.CENTER])

y = TOP + 3.66
box(s, ML, y, 6.2, 1.16, fill=CARD, line=BORDER)
text(s, ML + 0.24, y + 0.13, 5.75, 1.0,
     [[("對本專案的代價（照實報告）", {"bold": True, "color": INK})],
      [("回頭套用到自己前期的 15 句 spike：只用句長的分類器 AUC = 0.900，"
        "高於整條多視角管線的最佳量測 0.840。", {"color": MUTED})],
      [("→ 前期八個 AUC、DeLong 檢定等結果全數作廢，該批句子退役。",
        {"color": RED, "bold": True})]],
     size=11, spacing=1.3)

box(s, ML + 6.4, y, CW - 6.4, 1.16, fill=CARD2, line=BORDER)
text(s, ML + 6.64, y + 0.13, CW - 6.9, 1.0,
     [[("對外的價值", {"bold": True, "color": ACCENT_DK})],
      [("一個已發表的中文歧義資料集，其成對消歧句可被「只數字數」的分類器以 AUC 0.965 分開。"
        "任何以此類資料做歧義偵測評測而未報告長度基準的研究，成績都可能主要來自長度。",
        {"color": INK})]],
     size=11, spacing=1.3)

text(s, ML, 6.50, CW, 0.44,
     "▲ 公平陳述：這些資料集是為各自的用途設計的（Wu et al. 是為「生成消歧版本」而設計）。"
     "有問題的是把它們當偵測任務的負例——那是本專案的用法，不是原作者的主張。",
     size=10, color=MUTED, spacing=1.22)

# ═══════════════════════════ S9 因應設計 ═══════════════════════════

s = slide("因應設計：脈絡恆等三元組", "DESIGN RESPONSE",
          sub="不是量測後揭露混淆，而是讓混淆不可能發生。")

box(s, ML, TOP, CW, 0.62, fill=CARD2, line=None)
box(s, ML, TOP, 0.055, 0.62, fill=ACCENT, line=None, shape=MSO_SHAPE.RECTANGLE)
text(s, ML + 0.3, TOP + 0.13, CW - 0.6, 0.4,
     "所有實驗條件下，被測子句的字元序列完全相同；只變動被測子句以外的脈絡。",
     size=14.5, color=ACCENT_DK, bold=True, spacing=1.2)

dy = TOP + 0.92
rows = [
    ("條件 U", "", "還不如死了算了", "效度檢查：確認這題真的需要脈絡", GRAYD),
    ("條件 A", "他生了重病，痛苦得受不了，", "還不如死了算了", "測試：譯文應表達「失去生命」", ACCENT),
    ("條件 B", "這場比賽輸得這麼難看，", "還不如死了算了", "測試：譯文應表達「競爭中被淘汰」", ACCENT),
]
for i, (lab, ctx, span, note, col) in enumerate(rows):
    yy = dy + i * 0.78
    text(s, ML, yy + 0.14, 0.85, 0.3, lab, size=12.5, color=col, bold=True, spacing=1.0)
    if ctx:
        cb = box(s, ML + 0.9, yy, 2.9, 0.56, fill=WHITE, line=BORDER)
        text(s, ML + 1.0, yy + 0.14, 2.7, 0.35, ctx, size=11.5, color=MUTED,
             align=PP_ALIGN.CENTER, spacing=1.0)
    sb = box(s, ML + 3.9, yy, 2.55, 0.56, fill=CARD2, line=ACCENT, lw=1.5)
    text(s, ML + 3.95, yy + 0.14, 2.45, 0.35, span, size=11.5, color=ACCENT_DK, bold=True,
         align=PP_ALIGN.CENTER, spacing=1.0)
    text(s, ML + 6.62, yy + 0.15, 5.2, 0.35, note, size=11, color=MUTED, spacing=1.0)

text(s, ML + 3.9, dy + 2.36, 2.55, 0.3, "▲ 三條件下逐字元相同", size=10, color=ACCENT,
     bold=True, align=PP_ALIGN.CENTER, spacing=1.0)

y = dy + 2.76
text(s, ML, y, CW, 0.3, "由此得到兩件事", size=14, color=INK, bold=True, spacing=1.0)
box(s, ML, y + 0.38, 6.2, 1.12, fill=CARD, line=BORDER)
text(s, ML + 0.24, y + 0.5, 5.75, 0.9,
     [[("① 訊號差異不可能來自表面特徵", {"bold": True, "color": INK})],
      [("被測子句在 U/A/B 完全相同，任何差異都只能來自脈絡。"
        "驗收條件：被測子句的長度 AUC 必須是 0.500——這個數字本身就是設計有效的證據。",
        {"color": MUTED})]], size=11, spacing=1.3)

box(s, ML + 6.4, y + 0.38, CW - 6.4, 1.12, fill=CARD, line=BORDER)
text(s, ML + 6.64, y + 0.5, CW - 6.9, 0.9,
     [[("② 錯誤分類變成客觀、零主觀標註", {"bold": True, "color": INK})],
      [("insensitive（A 與 B 選到同一義項）＝ 模型忽略脈絡，是最強的錯誤訊號——"
        "它不需要知道哪個義項才對，只需要知道兩個脈絡的答案應該不同。", {"color": MUTED})]],
     size=11, spacing=1.3)

# ═══════════════════════════ S10 其他負面發現 ═══════════════════════════

s = slide("其他三項負面發現", "NEGATIVE RESULTS",
          sub="負面結果照實報告。本階段最有價值的產出幾乎全部來自這裡。")

cards = [
    ("問法會讓模型退化", "0.500 → 0.660",
     "問模型「兩句話的意圖是不是相同」，它對所有句子一律回答「相同」，AUC 退化為 0.500，等於亂猜。"
     "改問「列出兩者的具體差異，完全相同則輸出『無差異』」，AUC 回到 0.660。",
     "→ 是／否的自我評估題會退化，強制生成題則保有訊號。此結論在專案內兩處獨立印證，已寫入系統設計。",
     AMBER),
    ("本地 PPL 沒有訊號", "0.484 / 0.516",
     "用中文 GPT-2 算困惑度，測試「歧義句是否比消歧句更難預測」。n=30 下兩個方向的 AUC 分別為 "
     "0.484 與 0.516，都等同亂猜。",
     "→ 排除了「本架構其實可被一個廉價的 PPL 指標取代」這個對架構存在理由的挑戰。負面結果，但有用。",
     ACCENT),
    ("快取讓重取樣靜默失效", "4 次呼叫 → 1 種回應",
     "校內端點自身有快取：相同請求即使把 temperature 設到 1.5，重送 4 次也只拿回同一份回應，"
     "自我一致性實驗因此全部無效而不自知。",
     "→ 改為單一請求的 n=k 取樣，並補上快取鍵回歸測試（tests/test_cache_key.py）避免再犯。",
     RED),
]
cw3 = (CW - 0.6) / 3
for i, (title, num, body, take, col) in enumerate(cards):
    x = ML + i * (cw3 + 0.3)
    box(s, x, TOP, cw3, 4.4, fill=WHITE, line=BORDER)
    box(s, x, TOP, cw3, 0.07, fill=col, line=None, shape=MSO_SHAPE.RECTANGLE)
    text(s, x + 0.26, TOP + 0.28, cw3 - 0.5, 0.3, f"0{i+1}", size=11, color=col, bold=True,
         font=FONT_NUM, spacing=1.0)
    text(s, x + 0.26, TOP + 0.56, cw3 - 0.5, 0.36, title, size=14.5, color=INK, bold=True,
         spacing=1.15)
    text(s, x + 0.26, TOP + 1.0, cw3 - 0.5, 0.42, num, size=19, color=col, bold=True,
         font=FONT_NUM, spacing=1.0)
    rule(s, x + 0.26, TOP + 1.52, cw3 - 0.52)
    text(s, x + 0.26, TOP + 1.66, cw3 - 0.5, 1.6, body, size=11, color=MUTED, spacing=1.35)
    box(s, x + 0.18, TOP + 3.28, cw3 - 0.36, 0.96, fill=CARD, line=None)
    text(s, x + 0.34, TOP + 3.38, cw3 - 0.66, 0.85, take, size=10.5, color=INK, spacing=1.3)

text(s, ML, 6.36, CW, 0.4,
     "研究誠信原則：對有利結果嚴格，對不利結果同樣嚴格。所有作廢的結果都逐項列在文件的「已作廢，不得引用」一節。",
     size=11, color=MUTED, spacing=1.2)

# ═══════════════════════════ S11 品質保證 ═══════════════════════════

s = slide("品質保證與工程紀律", "ENGINEERING DISCIPLINE")

stat(s, ML, TOP, 3.0, 1.4, f"{F['tests']}", "項測試全數通過",
     note="10 支測試檔，全離線執行", color=GREEN, vsize=32)
stat(s, ML + 3.2, TOP, 3.0, 1.4, "0", "次真實 API 呼叫",
     note="以 fake client 替換，測試不計費", color=ACCENT, vsize=32)
stat(s, ML + 6.4, TOP, 3.0, 1.4, "1", "處標註污染被測出",
     note="守門測試抓到自造的資料污染", color=AMBER, vsize=32)
stat(s, ML + 9.6, TOP, CW - 9.6, 1.4, f"{F['papers']}", "篇相關論文已查證",
     note="含一篇高度重疊的先行研究", color=ACCENT, vsize=32)

y = TOP + 1.75
text(s, ML, y, 6.2, 0.3, "測試涵蓋的不變量", size=14, color=INK, bold=True, spacing=1.0)
bullets(s, ML, y + 0.4, 6.2, [
    "狀態機：快速／慢速通道分流、反思迴圈上限不會無限迴圈",
    "source_text 在任何節點執行後皆未被修改",
    "決策時間軸不含模型原始推理文字（倫理界線）",
    "CLI：批次斷點續跑不重複呼叫、單句失敗不整體退出",
    "快取鍵含取樣參數（此測試即為前述快取 bug 的回歸測試）",
], size=11.5, gap=0.42, marker="✓", mcolor=GREEN)

text(s, ML + 6.6, y, CW - 6.6, 0.3, "全案自訂的五條紅線", size=14, color=INK, bold=True,
     spacing=1.0)
bullets(s, ML + 6.6, y + 0.4, CW - 6.6, [
    ("長度與表層混淆　", "任何組間比較先跑長度基準，訊號 AUC 與最強雜訊 AUC 並列呈現。"),
    ("循環論證　", "反思迴圈的終止條件就是一致性，故一致性只作收斂診斷，不當勝負依據。"),
    ("標註污染　", "題目標註在任何模型看過它之前凍結；模型輸出只能影響準則，不能影響個別答案。"),
    ("不對稱的證據標準　", "記錄總共試了幾個配置（研究者自由度）；AUC=1.000 時改用排列檢定。"),
    ("基礎設施債　", "每筆 run 記錄 commit hash 與 prompt hash；新指標必須有單元測試才可下結論。"),
], size=10.5, gap=0.52, marker="•", mcolor=ACCENT)

# ═══════════════════════════ S12 風險與待決 ═══════════════════════════

s = slide("風險與待決事項", "RISKS & OPEN DECISIONS",
          sub="下列四項需要研究者／指導教授裁定，其餘依規格執行即可。")

table(s, ML, TOP + 0.28, CW, [
    ["項目", "情況", "影響", "所需決定"],
    ["CwnGraph 授權為 GPL v3",
     "規格書原記為「學術免費、禁商用」，實測為 GPL v3（傳染性授權）。CWN 資料本身的授權另需向官方確認。",
     "若當程式庫連結進 repo，會觸發衍生作品條款",
     "只在資料建構階段使用／全案改 GPL／改用資料集自帶的定義欄位"],
    ["高度重疊的先行研究",
     "arXiv:2605.15635 以「翻譯 + 語意熵」偵測中文歧義，方法與本專案演算法 1 核心重疊，早三個月發表。",
     "novelty 論述與「語意熵取代成對餘弦」的採納範圍",
     "劃定 novelty 邊界；本專案的差異點在「用於路由」與「逼出承諾」"],
    ["dev-30 標註獨立性缺口",
     "第二輪複核時 30 句全部被三個模型看過並給了逐句改法，原本只有 2 句有此缺口。",
     "模型讀法已回流進標註，違反標註凍結原則",
     "三方意見只用於修準則、不逐句補；此事須寫進論文的資料集章節"],
    ["受測模型權限",
     "目前金鑰可存取的研究模型全數 403，僅三個模型可用，暫作基礎設施驗證。",
     "跨模型對比實驗（M8）無法執行",
     "向系上申請模型存取權限"],
], col_w=[2.15, 4.5, 2.9, 3.0], row_h=0.92, head_h=0.42, size=10.5)

box(s, ML, 6.26, CW, 0.62, fill=CARD2, line=None)
text(s, ML + 0.24, 6.38, CW - 0.5, 0.42,
     [[("硬性 timebox　", {"bold": True, "color": ACCENT_DK}),
       ("P2 的資料層若三天內未產出可用資料，即回頭沿用 dev-30 現有設計，不再投入。"
        "任一階段的完成定義卡住超過半天，視為設計問題而非實作問題，回頭討論。", {"color": INK})]],
     size=11, spacing=1.2)

# ═══════════════════════════ S13 後續時程 ═══════════════════════════

s = slide("後續時程", "NEXT STEPS",
          sub="距 10 月截止約 6 週，估計實際可用工時約 3 週。")

phases = [
    ("P2", "資料層：產出 ≥40 筆脈絡恆等三元組", 1.5, AMBER, "進行中"),
    ("P3", "判定層：sense_judge 與人工一致率 ≥85%", 0.5, ACCENT, ""),
    ("P4", "訊號層：八個訊號各自的 AUC（RQ1）", 1.0, ACCENT, ""),
    ("P5", "Router：成本–準確度前緣曲線（RQ2）", 0.5, ACCENT, ""),
    ("P6", "主實驗：全對照組與主表（關鍵檢查點）", 1.0, ACCENT_DK, "檢查點"),
    ("P7", "Demo 介面與記憶模組（RQ3）", 1.0, ACCENT, ""),
    ("P8", "技術報告 20–30 頁與可重現封包", 5.0, GRAYD, ""),
]
total = sum(p[2] for p in phases)
gx, gw = ML + 5.2, CW - 5.2 - 2.0
cy = TOP + 0.30
cursor = 0.0
for code, label, dur, col, tag in phases:
    text(s, ML, cy - 0.03, 0.6, 0.3, code, size=12.5, color=col, bold=True, spacing=1.0)
    text(s, ML + 0.62, cy - 0.03, 4.4, 0.3, label, size=11.5, color=INK, spacing=1.15)
    bx = gx + gw * (cursor / total)
    bwid = max(gw * (dur / total), 0.22)
    box(s, bx, cy, bwid, 0.24, fill=col, line=None, radius=0.35)
    text(s, gx + gw + 0.14, cy - 0.03, 0.62, 0.3, f"{dur:g} 天", size=10.5, color=MUTED,
         spacing=1.0)
    if tag:
        text(s, gx + gw + 0.86, cy - 0.03, 1.16, 0.3, tag, size=10.5, color=col, bold=True,
             spacing=1.0)
    cursor += dur
    cy += 0.46

rule(s, gx, cy + 0.04, gw)
text(s, gx, cy + 0.14, gw + 1.9, 0.3,
     f"合計約 {total:g} 個工作天（其中 P8 報告撰寫占 5 天）", size=10.5, color=MUTED,
     spacing=1.0)

y = cy + 0.60
box(s, ML, y, 6.2, 0.98, fill=CARD, line=BORDER)
text(s, ML + 0.24, y + 0.12, 5.7, 0.8,
     [[("最近的一步（P2-D2）", {"bold": True, "color": INK})],
      [("在 D1 的裁定完成後撰寫 cwn_loader 與 probe_builder，產出 60 筆候選供研究者快篩，"
        "並以 length_audit 驗證被測子句長度 AUC = 0.500。", {"color": MUTED})]],
     size=11, spacing=1.3)

box(s, ML + 6.4, y, CW - 6.4, 0.98, fill=RGBColor(0xFD, 0xF6, 0xE9),
    line=RGBColor(0xEB, 0xD9, 0xB4))
text(s, ML + 6.64, y + 0.12, CW - 6.9, 0.8,
     [[("關鍵檢查點：P6", {"bold": True, "color": AMBER})],
      [("若主實驗顯示本系統在等算力下沒有優於 self-consistency 對照組，"
        "即回頭重新設計，而不是繼續堆功能。", {"color": INK})]],
     size=11, spacing=1.3)

# ═══════════════════════════ S14 結語 ═══════════════════════════

s = prs.slides.add_slide(BLANK)
_n[0] += 1
box(s, 0, 0, SW, SH, fill=NAVY, line=None, shape=MSO_SHAPE.RECTANGLE)
box(s, 0, 0, 0.22, SH, fill=ACCENT, line=None, shape=MSO_SHAPE.RECTANGLE)

text(s, 1.15, 1.3, 9.0, 0.35, "小結", size=13, color=RGBColor(0x6F, 0xC5, 0xCC), bold=True,
     spacing=1.0)
text(s, 1.1, 1.72, 11.0, 1.6,
     "架構與方法學已定案，\n剩下的是照規格把數據跑出來。",
     size=33, color=WHITE, bold=True, spacing=1.32)

rule(s, 1.15, 3.62, 2.2, color=ACCENT, thick=2.6)

items = [
    ("已經站穩的", "端到端可執行的管線、141 項離線測試、經查證的主資料來源與授權。"),
    ("最有價值的產出", "長度混淆的量化揭露，以及據此設計的脈絡恆等三元組協定。這部分不依賴系統成敗，可獨立成立。"),
    ("尚未回答的", "三個 RQ 都還沒有主實驗數據；P6 是關鍵檢查點，結果不利就回頭重新設計。"),
]
cy = 3.95
for head, body in items:
    text(s, 1.15, cy, 2.5, 0.35, head, size=13, color=RGBColor(0x6F, 0xC5, 0xCC), bold=True,
         spacing=1.0)
    text(s, 3.75, cy, 8.3, 0.6, body, size=12.5, color=RGBColor(0xC8, 0xD8, 0xE0), spacing=1.35)
    cy += 0.82

text(s, 1.15, 6.72, 9.0, 0.3,
     "文件：docs/研究計畫書.md（合約）｜ docs/技術設計文件.md（施工圖）｜ docs/完整架構與分階段實作路徑 v3（執行規格）",
     size=9.5, color=RGBColor(0x6A, 0x7D, 0x8C), spacing=1.0)

# ─────────────────────────── 輸出 ───────────────────────────

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print(f"已產出：{OUT}")
print(f"投影片數：{len(prs.slides.__iter__.__self__._sldIdLst)}")
