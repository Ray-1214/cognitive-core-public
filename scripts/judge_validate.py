"""比對研究者的盲標與 judge 的判定，算一致率（v3 架構書 §P3）。

## v2：二元強迫選擇

judge 與盲標表都改為「gold vs 同 lemma 最高頻的非 gold 干擾項」二選一。
第一輪的 N 選一版本留在 git 歷史。

三個一致率要分開看，混在一起看不出問題出在哪：

  judge vs 人工   ← **主指標**。judge 判得準不準
  人工  vs gold   ← gold 本身可不可信（CWN 標註 vs 母語者對譯文的判斷）
  judge vs gold   ← 即 400 筆基準所用的正確率，此處為子樣本

另加兩個二元設計特有的量：

  A/B 位置偏誤    ← 配平的用意就是讓它可被量出來
  「兩個都說得通」的比例 ← **義項粒度的天花板，直接量測**
                          第一輪的 25% 標籤噪音是間接推估的

用法：
    python scripts/judge_validate.py _r2
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import yaml  # noqa: E402

from cognitive_core.eval.cross_check import (  # noqa: E402
    SameBackend,
    assert_judge_is_cross as assert_judge_is_cross_behaviour,
    check_cross,
)
from cognitive_core.eval.wsd import (  # noqa: E402
    judge_sense_binary,
    pick_distractor,
    translate,
    wilson_ci,
)
from cognitive_core.llm import Client  # noqa: E402
from cognitive_core.runlog import RunLog  # noqa: E402

RESULTS = ROOT / "data" / "results"


def parse_field(text: str, label: str) -> list[str]:
    out = []
    for raw in re.findall(rf"\*\*{label}\*\*:\s*(.*)", text):
        out.append(re.sub(r"<!--.*?-->", "", raw).strip())
    return out


def main() -> int:
    tag = sys.argv[1] if len(sys.argv) > 1 else "_r2"
    md = RESULTS / f"judge_manual{tag}.md"
    keyf = RESULTS / f"judge_manual{tag}_KEY_do_not_open.json"
    if not md.exists() or not keyf.exists():
        print(f"🔴 找不到 {md.name} 或 {keyf.name}", file=sys.stderr)
        return 1

    text = md.read_text(encoding="utf-8")
    manual = parse_field(text, "你的判定")
    both_ok = parse_field(text, "兩個都說得通嗎")
    key = json.loads(keyf.read_text(encoding="utf-8"))
    items_key = key["items"]
    if key.get("design") != "binary_forced_choice":
        print("🔴 答案鍵不是二元設計——請用對應版本的腳本", file=sys.stderr)
        return 1
    if len(manual) != len(items_key):
        print(f"🔴 標註 {len(manual)} 筆與答案鍵 {len(items_key)} 筆不符", file=sys.stderr)
        return 1
    blank = [i for i, m in enumerate(manual, 1) if not m]
    if blank:
        print(f"🔴 第 {blank} 筆的「你的判定」未填", file=sys.stderr)
        return 1
    bad = [i for i, m in enumerate(manual, 1) if m.upper() not in ("A", "B", "NONE")]
    if bad:
        print(f"🔴 第 {bad} 筆的判定不是 A/B/NONE", file=sys.stderr)
        return 1

    probes = {p["id"]: p for p in yaml.safe_load(
        (ROOT / "data" / "probes" / "wsd_probes.yaml").read_text(encoding="utf-8"))["items"]}

    run = RunLog("judge_validate", meta={"n": len(manual), "design": "binary"})
    client = Client(run=run)
    client.cfg.assert_judge_is_cross()
    try:
        cross = assert_judge_is_cross_behaviour(client)
    except SameBackend as e:
        cross = check_cross(client)
        print(f"\n🔴 行為層 judge_cross 未通過\n{e}\n")
        print("⚠️ 驗證仍會進行——一致率本身不受影響（人工標註是外部錨點），")
        print("   但 judge 的獨立性宣稱不成立。此事實會寫進報表。\n")
    jspec = client.cfg.resolve("judge")
    print(f"judge：{jspec.provider}/{jspec.model}（重跑 {len(manual)} 筆）")

    rows = []
    for idx, (k, m) in enumerate(zip(items_key, manual)):
        p = probes[k["probe_id"]]
        dis = pick_distractor(p)
        gf = bool(k["gold_first"])
        gd, dd = p["gold_definition"], dis["definition"]
        def_a, def_b = (gd, dd) if gf else (dd, gd)
        tr = translate(client, p["sentence"])
        j = judge_sense_binary(client, p["target_word"], tr, def_a, def_b)

        def to_sense(letter: str) -> str:
            if letter == "NONE":
                return "NONE"
            return k["gold_sense_id"] if (letter == "A") == gf else k["distractor_sense_id"]

        rows.append({
            "n": k["n"], "probe_id": k["probe_id"], "stratum": k["stratum"],
            "word": p["target_word"], "sentence": p["sentence"], "translation": tr,
            "gold_first": gf, "def_a": def_a, "def_b": def_b,
            "human_letter": m.upper(), "human": to_sense(m.upper()),
            "judge_letter": j["choice"], "judge": to_sense(j["choice"]),
            "judge_conf": j["confidence"], "judge_reason": j.get("reasoning_summary", ""),
            "gold": k["gold_sense_id"], "distractor": k["distractor_sense_id"],
            "both_plausible": (both_ok[idx].strip() if idx < len(both_ok) else ""),
        })
    print(f"  完成 {len(rows)} 筆\n")

    n = len(rows)
    jh = [r for r in rows if r["judge"] == r["human"]]
    hg = [r for r in rows if r["human"] == r["gold"]]
    jg = [r for r in rows if r["judge"] == r["gold"]]
    r_jh = len(jh) / n

    def line(label: str, sub: list, note: str) -> str:
        lo, hi = wilson_ci(len(sub), n)
        return (f"| {label} | {len(sub)}/{n} | {len(sub) / n * 100:.0f}% | "
                f"[{lo * 100:.0f}, {hi * 100:.0f}]% | {note} |")

    L = [f"# judge 驗證（二元強迫選擇）　n={n}", "",
         f"> judge：`{jspec.provider}/{jspec.model}`　"
         f"人工標註為盲標（未見 gold、未見 sense_id、未見 judge 判定）。",
         "> 題目與第一輪完全不重疊，且未出現在任何 prompt 的 few-shot 中。", ""]
    if not cross.is_cross:
        L += ["> 🔴 **judge_cross 的行為層檢查未通過**——"
              "兩個 model id 的 tokenizer 截斷點逐字相同。",
              "> 一致率本身不受影響（人工標註是外部錨點），"
              "但 judge 的獨立性宣稱不成立。",
              "> 見 `data/results/endpoint_identity_check.md`。", ""]
    L += [
         "## 三個一致率", "",
         "| 比較 | 一致 | 比例 | 95% CI | 意義 |",
         "| --- | :-: | :-: | :-: | --- |",
         line("**judge vs 人工**", jh, "**主指標**：judge 判得準不準"),
         line("人工 vs gold", hg, "gold 本身可不可信"),
         line("judge vs gold", jg, "即 400 筆基準所用的正確率，此為子樣本"),
         "", "### 判準（v3 架構書 §P3）", "", "| 門檻 | 狀態 |", "| --- | --- |",
         f"| <60% judge 明顯亂判 → 停 | {'🔴 觸發' if r_jh < 0.60 else '未觸發'} |",
         f"| 60–85% 大致對 → 繼續 | {'✅ 落在此區' if 0.60 <= r_jh < 0.85 else '—'} |",
         f"| ≥85% 正式驗證門檻（可解 AUC 閘門） | "
         f"{'✅ 達成' if r_jh >= 0.85 else '未達成'} |", "",
         "⚠️ 二元設計的隨機基準是 **50%**，不是 N 選一時的 ~12.5%。"
         "判準門檻沿用原設定，但解讀時要記得這件事。", ""]

    # ── 義項粒度的天花板：直接量測 ──
    yes = [r for r in rows if r["both_plausible"].startswith("是")]
    answered = [r for r in rows if r["both_plausible"]]
    L += ["---", "", "## 義項粒度的天花板 ⭐ 直接量測", "",
          "第一輪的「25% 標籤噪音」是從「人工 vs gold 只有 75%」間接推的。",
          "本輪直接問「兩個都說得通嗎」。", ""]
    if answered:
        lo, hi = wilson_ci(len(yes), len(answered))
        L += [f"- 回答「是」：{len(yes)}/{len(answered)} = "
              f"**{len(yes) / len(answered) * 100:.0f}%**"
              f"　95% CI [{lo * 100:.0f}, {hi * 100:.0f}]%",
              "",
              "這些題目的譯文無法區分兩個義項，任何評判者（人或模型）都只能猜。",
              f"若比例為 *p*，本基準的準確度天花板約為 1 − *p*/2 = "
              f"**{1 - len(yes) / len(answered) / 2:.0%}**"
              "（都說得通時猜對的機率是一半）。", ""]
        gy = [r for r in yes if r["judge"] == r["human"]]
        gn = [r for r in answered if r not in yes and r["judge"] == r["human"]]
        nn = len(answered) - len(yes)
        L += ["| 題目類型 | n | judge 與人工一致 |", "| --- | :-: | :-: |",
              f"| 兩個都說得通 | {len(yes)} | "
              f"{len(gy)}（{len(gy) / len(yes) * 100:.0f}%）|" if yes else
              "| 兩個都說得通 | 0 | — |",
              f"| 只有一個說得通 | {nn} | "
              f"{len(gn)}（{len(gn) / nn * 100:.0f}%）|" if nn else
              "| 只有一個說得通 | 0 | — |", ""]
    else:
        L += ["（第二欄未填）", ""]

    # ── A/B 位置偏誤 ──
    ab = [r for r in rows if r["judge_letter"] in ("A", "B")]
    L += ["---", "", "## A/B 位置偏誤", ""]
    if ab:
        na = sum(1 for r in ab if r["judge_letter"] == "A")
        lo, hi = wilson_ci(na, len(ab))
        ha = sum(1 for r in rows if r["human_letter"] == "A")
        L += [f"- judge 選 A：{na}/{len(ab)} = {na / len(ab):.2f}"
              f"　95% CI [{lo:.2f}, {hi:.2f}]"
              f"　{'✅ 無顯著偏誤' if lo <= 0.5 <= hi else '🔴 有偏誤'}",
              f"- 人工選 A：{ha}/{n} = {ha / n:.2f}",
              f"- gold 在 A 位：{sum(1 for r in rows if r['gold_first'])}/{n}"
              "（分層內交替配平）", ""]

    # ── NONE ──
    L += ["---", "", "## NONE 的使用", "",
          f"| | judge | 人工 |", "| --- | :-: | :-: |",
          f"| 判為 NONE | {sum(1 for r in rows if r['judge_letter'] == 'NONE')} | "
          f"{sum(1 for r in rows if r['human_letter'] == 'NONE')} |", ""]

    # ── 不一致案例 ──
    dis_rows = [r for r in rows if r["judge"] != r["human"]]
    L += ["---", "", f"## 不一致的案例（judge ≠ 人工）　{len(dis_rows)} 筆", ""]
    for r in dis_rows:
        L += [f"### {r['n']:02d}　**{r['word']}**　`{r['probe_id']}`　[{r['stratum']}]",
              f"- 原句：{r['sentence']}",
              f"- 譯文：{r['translation']}",
              f"- A：{r['def_a']}",
              f"- B：{r['def_b']}",
              f"- **人工**：{r['human_letter']}"
              f"　（兩個都說得通：{r['both_plausible'] or '未填'}）",
              f"- **judge**：{r['judge_letter']}　信心 {r['judge_conf']:.2f}"
              f"　依據：{r['judge_reason']}",
              f"- gold 在 {'A' if r['gold_first'] else 'B'} 位"
              + ("　← 人工同 gold" if r["human"] == r["gold"] else "")
              + ("　← judge 同 gold" if r["judge"] == r["gold"] else ""),
              ""]

    L += ["---", "", "## 逐筆", "",
          "| # | 詞 | 人工 | judge | gold 位 | 都說得通 | j=h | h=g | j=g |",
          "| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |"]
    for r in rows:
        L.append(f"| {r['n']} | {r['word']} | {r['human_letter']} | "
                 f"{r['judge_letter']} | {'A' if r['gold_first'] else 'B'} | "
                 f"{r['both_plausible'] or '—'} | "
                 f"{'✅' if r['judge'] == r['human'] else '❌'} | "
                 f"{'✅' if r['human'] == r['gold'] else '❌'} | "
                 f"{'✅' if r['judge'] == r['gold'] else '❌'} |")

    out = RESULTS / f"judge_validation{tag}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    (RESULTS / f"judge_validation{tag}.json").write_text(json.dumps(
        {"n": n, "design": "binary_forced_choice",
         # 一旦這批題目被用來診斷 judge 或調 prompt，就要手動改成 true。
         # eval/gate.py 的 AUC 閘門會拒絕 contaminated 的驗證檔。
         "contaminated": False,
         "judge_cross_behavioural": {
             "is_cross": cross.is_cross, "names_differ": cross.names_differ,
             "cuts_identical": cross.cuts_identical},
         "judge_vs_human": r_jh, "human_vs_gold": len(hg) / n,
         "judge_vs_gold": len(jg) / n,
         "judge_vs_human_ci": list(wilson_ci(len(jh), n)),
         "both_plausible_rate": (len(yes) / len(answered)) if answered else None,
         "judge_model": f"{jspec.provider}/{jspec.model}",
         "disagreements": [{"n": r["n"], "probe_id": r["probe_id"],
                            "word": r["word"], "human": r["human_letter"],
                            "judge": r["judge_letter"]} for r in dis_rows]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 62)
    for label, sub in (("judge vs 人工 ⭐", jh), ("人工 vs gold", hg),
                       ("judge vs gold", jg)):
        lo, hi = wilson_ci(len(sub), n)
        print(f"  {label:16} {len(sub)}/{n} = {len(sub) / n * 100:5.1f}%"
              f"  95% CI [{lo * 100:.0f}, {hi * 100:.0f}]%　（隨機基準 50%）")
    if answered:
        print(f"\n  兩個都說得通：{len(yes)}/{len(answered)} = "
              f"{len(yes) / len(answered) * 100:.0f}%"
              f"　→ 天花板約 {1 - len(yes) / len(answered) / 2:.0%}")
    print(f"  不一致 {len(dis_rows)} 筆，逐筆列於 {out}")
    verdict = ("🔴 <60%，judge 明顯亂判" if r_jh < 0.60
               else "✅ ≥85%，達正式驗證門檻，可解 AUC 閘門" if r_jh >= 0.85
               else "⚠️ 60–85%，粗跑可繼續，AUC 閘門仍關閉")
    print(f"\n  判準：{verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
