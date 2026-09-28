"""產出 dev-30 第二輪（三方交叉複核）的合議表。

與 `make_review.py` 的差別，先講清楚以免日後誤讀：

* `make_review.py` 是**純機械攤平**，刻意不含任何判斷，目的是保護第一輪複核的
  獨立性（地雷 3）。第一輪已完成（19 keep / 2 applied / 9 deferred，見 YAML 的
  `review_r1`），那個目的已經達成。
* 本腳本產出的是**第二輪**：研究者已經把三份模型複核（grok / gpt / claude）貼進
  專案，30 句全部曝光。獨立性已不可逆地耗用（見 review_r2_inputs.yaml 的 D7），
  所以這一輪的表**明確含有判斷**，但每一行的來源都標出來：

      事實欄位          → data/dev30/sentences.yaml
      第一輪 verdict    → sentences.yaml 的 review_r1（研究者本人，母語判斷）
      grok / gpt / claude → review_r2_inputs.yaml 的 items.*.reviews（摘錄）
      合議建議          → review_r2_inputs.yaml 的 items.*.consensus（助理判斷，待確認）

輸出保持與 `scripts/apply_review.py` 相容：每個 `## dev-xxx` 區塊只有一行
`**verdict**:`，其餘意見一律用表格或別的欄位名，不會被解析器誤抓。

用法：
    python scripts/make_review_r2.py
    python scripts/make_review_r2.py --out data/dev30/REVIEW.md
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
from collections import Counter

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEV = ROOT / "data" / "dev30"

# 已知的標註獨立性缺口。事實記錄，來自 _quarantine/README.md。
CONTAMINATED = {
    "dev-lex-01": "助理曾看過 mistral-small-4 對本句提議的讀法（草稿早於此，之後未改動本句）",
    "dev-prg-05": "助理曾看過 Gemini 對本句提議的意圖，且已轉述給研究者。雙方皆已看過",
}

REVIEWERS = ["grok", "gpt", "claude"]
SEP = "=" * 59


def kind(v: str) -> str:
    """取 verdict 的種類（冒號前那一段）。"""
    return (v or "").split(":", 1)[0].split("：", 1)[0].strip().lower()


def wrap(text: str | None) -> str:
    return (text or "").strip()


def indent_block(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + ln if ln.strip() else "" for ln in wrap(text).splitlines())


def render_header(data: dict, inputs: dict, sha: str, n: int) -> list[str]:
    dist = "、".join(f"{k} {v}" for k, v in data["meta"]["distribution"].items())
    r1 = data["meta"].get("review_r1_summary", {})
    L = [
        "# dev-30 複核表（第二輪：三方交叉複核合議）",
        "",
        "> 來源：`data/dev30/sentences.yaml`",
        f"> SHA-256：`{sha}`",
        f"> 句數：{n}（{dist}）",
        f"> 第一輪結果：keep {r1.get('keep', '?')}／applied {r1.get('applied', '?')}"
        f"／deferred {r1.get('deferred', '?')}（已寫回 YAML 的 `review_r1`）",
        "> ",
        "> 本檔由 `scripts/make_review_r2.py` 產生。機械欄位取自 YAML；",
        "> 三方意見取自 `data/dev30/review_r2_inputs.yaml`；**「合議建議」是助理的判斷，**",
        "> **在你逐句確認之前一律不算數**，`meta.reviewed` 維持 false。",
        "",
        "## ⚠️ 先讀這段：標註獨立性已經改變",
        "",
        "標註鐵則 1 是「某句的標註在任何模型看過它之前凍結」，鐵則 2 是「模型輸出只能",
        "用來判斷準則是否涵蓋不足，不可逐句補」。本輪之後：",
        "",
        "- 30 句**全部**被 grok / gpt / claude 看過，而且三方都給了逐句改法。",
        "  原本只有 `dev-lex-01`、`dev-prg-05` 兩句有缺口。",
        "- 直接影響 Phase D 的「7 模型跑 dev-30 收集讀法聯集 → 判斷準則完備性」——",
        "  其中三個模型的讀法已經回流進標註。",
        "- 依鐵則 2 的用法：三方意見只拿來改**準則**（§2 的 D1–D8），",
        "  逐句改動由你自己下判斷。這件事必須寫進論文的資料集章節。",
        "",
        "另一件同樣要記住的事：三份複核都看過現行的 licensed/spurious 標註（不是盲標），",
        "所以「三方一致 keep」只代表沒有人反對，不是獨立驗證通過。實際上在",
        "`ref-03`／`ref-06`／`prg-06` 三題，你第一輪的母語判斷與三方**全體**相反。",
        "",
    ]
    return L


def render_howto(inputs: dict) -> list[str]:
    n_q = len(inputs.get("questions") or [])
    n_d = len(inputs.get("decisions") or [])
    n_m = len(inputs.get("mech") or [])
    return [
        "## §0 這張表怎麼用",
        "",
        f"1. **先答 §1 的 {n_q} 個母語問題**（只有你能答，其中 Q1 一題連動三句的去留）。",
        f"2. **再裁定 §2 的 {n_d} 個準則決策**（D1–D8）。這些一旦定案，多數逐句 verdict 就自動確定，",
        "   不必一句一句重想。",
        f"3. §3 的 {n_m} 項機械修正**不需要等 1 和 2**，可以現在就做。",
        "4. 最後回到 §4 逐句填 `**verdict**:`。",
        "",
        "> 填 verdict 時請用 `keep` / `fix: 具體改法` / `drop` / `uncertain` 當開頭，",
        "> `scripts/apply_review.py` 是用冒號前的第一個 token 判斷種類的；",
        "> 說明文字寫在下一行的 `**note**:`。",
        "",
    ]


def render_questions(inputs: dict) -> list[str]:
    L = ["## §1 只有母語者能回答的問題", "",
         "這些是本表唯一真正卡住的地方 —— 助理與三個模型都給不出可信答案，",
         "因為它們全都是台灣華語的語感問題。", ""]
    for q in inputs.get("questions") or []:
        ids = "、".join(f"`{i}`" for i in q["items"])
        L.append(f"### {q['id']}　（{ids}）")
        L.append("")
        L.append(wrap(q["q"]))
        L.append("")
    return L


def render_decisions(inputs: dict) -> list[str]:
    L = ["## §2 準則層決策", "",
         "先定這些，逐句 verdict 才不會互相打架。每一項都附「現象 / 證據 / 選項 / 建議」，",
         "建議欄是助理的判斷，可以直接否決。", ""]
    for d in inputs.get("decisions") or []:
        L.append(f"### {d['id']}　{d['title']}")
        L.append("")
        L.append("**現象**")
        L.append("")
        L.append(wrap(d["problem"]))
        L.append("")
        ev = d.get("evidence") or []
        if ev:
            L.append("**涉及**：" + "、".join(f"`{e}`" for e in ev))
            L.append("")
        L.append("**選項**")
        L.append("")
        for o in d.get("options") or []:
            L.append(f"- {o}")
        L.append("")
        L.append("**建議**")
        L.append("")
        L.append(wrap(d["recommend"]))
        L.append("")
        L.append("**裁定**：<!-- 填 A / B / C / 其他 -->")
        L.append("")
    return L


def render_mech(inputs: dict) -> list[str]:
    L = ["## §3 機械修正（不涉及語言判斷，可立刻做）", ""]
    for m in inputs.get("mech") or []:
        L.append(f"### {m['id']}　{m['title']}")
        L.append("")
        L.append(wrap(m["detail"]))
        L.append("")
        ev = m.get("evidence") or []
        if ev:
            L.append("**涉及**：" + "、".join(f"`{e}`" for e in ev))
            L.append("")
        L.append("**採用**：<!-- 是 / 否 -->")
        L.append("")
    return L


def render_item(item: dict, spec: dict) -> list[str]:
    sid = item["id"]
    amb = item["text"]
    mp = item.get("minimal_pair") or {}
    dis = mp.get("text", "")
    diff = len(dis) - len(amb)

    links = spec.get("links") or []
    ask = spec.get("ask") or []
    tag = ""
    if links or ask:
        bits = [f"連動 {'、'.join(links)}"] if links else []
        if ask:
            bits.append(f"待答 {'、'.join(ask)}")
        tag = "　［" + "；".join(bits) + "］"

    L = [f"## {sid}  ({item['ambiguity_type']}){tag}"]
    if sid in CONTAMINATED:
        L += ["", f"> 🔴 **標註獨立性缺口**：{CONTAMINATED[sid]}"]
    L += ["",
          "| | 句子 | 字數 |",
          "|---|---|---|",
          f"| 歧義 | {amb} | {len(amb)} |",
          f"| 消歧 | {dis} | {len(dis)} |",
          "",
          f"改動：{mp.get('edit', '（未填）')}　　字數差：{diff:+d}"]
    if mp.get("resolves_to"):
        L.append(f"消歧後鎖定：{mp['resolves_to']}")
    L.append("")

    L.append("**licensed_readings**")
    for i, r in enumerate(item.get("licensed_readings") or [], 1):
        when = r.get("licensed_when") or r.get("applicable_when") or ""
        intent = r.get("speaker_intent")
        tail = f"　　適用：{when}" if when else ""
        tail += f"　　intent={intent}" if intent else ""
        L.append(f"{i}. {r.get('reading', '')}{tail}")
    L.append("")

    L.append("**spurious_readings**")
    for s in item.get("spurious_readings") or []:
        L.append(f"- {s}")
    L.append("")

    L.append(f"**text_determinable**: {str(item.get('text_determinable')).lower()}")
    fd = item.get("field_determinable") or {}
    if fd:
        L.append("**field_determinable**: " +
                 " / ".join(f"{k}={str(v).lower()}" for k, v in fd.items()))
    L.append(f"**expected_route**: {item.get('expected_route', '（未填）')}")
    rc = item.get("required_clarifications") or []
    L.append(f"**required_clarifications**: {rc if rc else '[]'}")
    L.append("")

    # 第一輪：研究者本人的判斷
    r1 = item.get("review_r1") or {}
    if r1:
        note = f"　—　{r1['note']}" if r1.get("note") else ""
        L.append(f"**第一輪（你）**：`{r1.get('verdict', '—')}`"
                 f"（{r1.get('status', '—')}）{note}")
        L.append("")

    # 第二輪：三方
    L.append("**第二輪三方複核**")
    L.append("")
    L.append("| 複核者 | verdict | 要點 |")
    L.append("| --- | --- | --- |")
    rv = spec.get("reviews") or {}
    for name in REVIEWERS:
        r = rv.get(name) or {}
        L.append(f"| {name} | `{r.get('v', '—')}` | {wrap(r.get('note'))} |")
    tally = Counter(kind((rv.get(n) or {}).get("v", "")) for n in REVIEWERS)
    tally.pop("", None)
    L.append("")
    L.append("一致度：" + "／".join(f"{v} {k}" for k, v in tally.most_common()))
    L.append("")

    con = spec.get("consensus") or {}
    L.append(f"**合議建議**：`{con.get('v', '—')}`　（助理判斷，待你確認）")
    L.append("")
    L.append(wrap(con.get("note")))
    L.append("")
    if ask:
        L.append(f"**卡在**：{'、'.join(ask)}（見 §1）")
        L.append("")

    L.append("---")
    L.append(f"**verdict**: {spec.get('prefilled_verdict', '')}"
             "<!-- keep / fix: 具體改法 / drop / uncertain -->")
    L.append("**note**:")
    L.append("")
    L.append(SEP)
    L.append("")
    return L


def render_summary(items: list[dict], inputs: dict) -> list[str]:
    specs = inputs["items"]
    L = ["## §5 總表", "",
         "| id | 型 | 字數差 | 第一輪(你) | grok | gpt | claude | 合議 | 連動 | 待答 |",
         "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |"]
    agree_all_keep = 0
    con_tally: Counter = Counter()
    for it in items:
        sid = it["id"]
        sp = specs.get(sid, {})
        rv = sp.get("reviews") or {}
        mp = it.get("minimal_pair") or {}
        diff = len(mp.get("text", "")) - len(it["text"])
        r1 = (it.get("review_r1") or {}).get("verdict", "—")
        cols = [kind((rv.get(n) or {}).get("v", "")) or "—" for n in REVIEWERS]
        con = kind((sp.get("consensus") or {}).get("v", "")) or "—"
        con_tally[con] += 1
        if r1 == "keep" and all(c == "keep" for c in cols):
            agree_all_keep += 1
        mark = " 🔴" if sid in CONTAMINATED else ""
        L.append(
            f"| {sid}{mark} | {it['ambiguity_type'][:4]} | {diff:+d} | {r1} | "
            + " | ".join(cols)
            + f" | **{con}** | {'、'.join(sp.get('links') or []) or '—'}"
            + f" | {'、'.join(sp.get('ask') or []) or '—'} |")
    L += ["",
          f"- 四方（你 + 三個模型）全體 keep：**{agree_all_keep} 題**",
          "- 合議分布：" + "／".join(f"{v} {k}" for k, v in con_tally.most_common()),
          f"- 需要母語裁決才動得了的題目：**{sum(1 for s in specs.values() if s.get('ask'))} 題**"]
    for name in REVIEWERS:
        t = Counter(kind(((specs.get(it["id"], {}).get("reviews") or {})
                          .get(name) or {}).get("v", "")) for it in items)
        t.pop("", None)
        L.append(f"- {name}：" + "／".join(f"{v} {k}" for k, v in t.most_common()))
    L.append("")
    if inputs.get("summary_note"):
        L.append(wrap(inputs["summary_note"]))
        L.append("")
    return L


def render_checklist(inputs: dict) -> list[str]:
    L = ["## §6 凍結前檢查清單", ""]
    for c in inputs.get("checklist") or []:
        L.append(f"- [ ] {c}")
    L.append("")
    return L


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEV / "REVIEW.md"))
    args = ap.parse_args()

    raw = (DEV / "sentences.yaml").read_bytes()
    data = yaml.safe_load(raw.decode("utf-8"))
    items = data["items"]
    sha = hashlib.sha256(raw).hexdigest()

    inputs = yaml.safe_load((DEV / "review_r2_inputs.yaml").read_text(encoding="utf-8"))
    specs = inputs["items"]

    missing = [it["id"] for it in items if it["id"] not in specs]
    if missing:
        print(f"⚠️ review_r2_inputs.yaml 缺少：{missing}", file=sys.stderr)
        return 1
    if inputs["meta"]["source_sha256"] != sha:
        print("⚠️ review_r2_inputs.yaml 記錄的 SHA-256 與現在的 sentences.yaml 不符。\n"
              f"   記錄：{inputs['meta']['source_sha256']}\n   實際：{sha}\n"
              "   三方意見是對舊版做的，請先確認差異再重跑。", file=sys.stderr)
        return 1

    out: list[str] = []
    out += render_header(data, inputs, sha, len(items))
    out += render_howto(inputs)
    out += render_questions(inputs)
    out += render_decisions(inputs)
    out += render_mech(inputs)
    out += ["## §4 逐句", "",
            "每題的欄位來源：事實取自 YAML；「第一輪（你）」取自 `review_r1`；",
            "三方表格取自 `review_r2_inputs.yaml`；「合議建議」是助理判斷。", "", SEP, ""]
    for it in items:
        out += render_item(it, specs[it["id"]])
    out += render_summary(items, inputs)
    out += render_checklist(inputs)

    p = pathlib.Path(args.out)
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"已產出 {p}")
    print(f"  句數 {len(items)}｜來源 SHA-256 {sha[:16]}…")
    print(f"  母語待答 {len(inputs['questions'])} 題｜準則決策 {len(inputs['decisions'])} 項"
          f"｜機械修正 {len(inputs['mech'])} 項")
    return 0


if __name__ == "__main__":
    sys.exit(main())
