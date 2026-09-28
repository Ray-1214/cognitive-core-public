"""產生 judge 人工驗證表（盲標）。

⚠️ **不附 gold、不附 judge 的判定。** 研究者要獨立標，看到任何一個都會失去獨立性。
驗證的對象是「judge 判得準不準」，與 judge 用哪個模型無關。

## v3：對齊二元強迫選擇的 judge

judge 已改為二元強迫選擇（gold vs 同 lemma 最高頻的非 gold 干擾項），
盲標表必須是**同一個任務**才能算一致率——拿 8 選 1 的人工標註去比
2 選 1 的 judge，量到的是任務差異不是 judge 品質。

表中呈現與 judge 完全相同的兩個選項，位置同樣在分層內交替配平，
且**不標示哪個是 gold**。

第二欄「兩個都說得通嗎」直接量出義項粒度的天花板——
第一輪推估的 25% 標籤噪音是從「人工 vs gold 只有 75%」間接推的。

## 產出前的守門檢查（2026-08-21 裁示 2-5）

  1. 表中不含任何 sense_id
  2. 表中不含 gold 的任何標記
  3. 該批題目未出現在任何 prompt 的 few-shot 中
  4. 該批題目未被先前的驗證用過（--exclude）
  5. 答案鍵另存於 *_KEY_do_not_open.json

任一項不過就不產表——這些檢查失敗時產出的表看起來完全正常，
但算出來的一致率沒有意義。

用法：
    python scripts/make_judge_manual.py --n 20 --out-suffix _r2 \\
        --exclude data/results/judge_manual_KEY_do_not_open.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "data" / "results"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(RESULTS / "wsd_pilot30.json"))
    ap.add_argument("--run", default=None,
                    help="run log（jsonl），用於取回譯文；預設取最近的 wsd run")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20260818)
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="先前的 KEY 檔；其中的 probe_id 一律排除，"
                         "避免拿已經看過的題目當驗證集")
    ap.add_argument("--out-suffix", default="",
                    help="輸出檔名後綴，例如 _r2")
    args = ap.parse_args()

    used: set[str] = set()
    for p in args.exclude:
        f = pathlib.Path(p)
        if not f.exists():
            print(f"🔴 找不到排除檔 {f}", file=sys.stderr)
            return 1
        used |= {x["probe_id"] for x in json.loads(f.read_text(encoding="utf-8"))["items"]}
    if used:
        print(f"排除先前用過的 {len(used)} 筆")

    # 譯文與候選義項從 md 報告反推較脆弱，改從 probes + 快取重跑取得
    sys.path.insert(0, str(ROOT / "src"))
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    import yaml

    from cognitive_core.eval.wsd import gold_goes_first, pick_distractor, translate
    from cognitive_core.llm import Client

    probes = yaml.safe_load(
        (ROOT / "data" / "probes" / "wsd_probes.yaml").read_text(encoding="utf-8"))
    items = [i for i in probes["items"] if i["id"] not in used]

    # 守門檢查 3：題目不得出現在任何 prompt 的 few-shot 中
    in_prompts = []
    for pf in sorted((ROOT / "prompts").glob("*.md")):
        body = pf.read_text(encoding="utf-8")
        body = re.sub(r"^---\n.*?\n---\n", "", body, flags=re.DOTALL)
        for it in items:
            if it["sentence"] in body or it["gold_definition"] in body:
                in_prompts.append((it["id"], pf.name))
    if in_prompts:
        blocked = {i for i, _ in in_prompts}
        print(f"⚠️ {len(blocked)} 筆出現在 prompt 的 few-shot 中，已排除："
              f"{sorted(blocked)[:5]}")
        items = [i for i in items if i["id"] not in blocked]
    n_each = args.n // 2
    dom = [i for i in items if i["stratum"] == "dominant"]
    non = [i for i in items if i["stratum"] == "non_dominant"]
    if len(dom) < n_each or len(non) < args.n - n_each:
        print(f"🔴 排除後題目不足：主流 {len(dom)}／非主流 {len(non)}", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    rng.shuffle(dom)
    rng.shuffle(non)
    picked = dom[:n_each] + non[:args.n - n_each]
    rng.shuffle(picked)          # 打散分層，避免研究者從順序推出分層

    client = Client()
    print(f"取 {len(picked)} 筆的譯文（應全數快取命中）…", flush=True)
    rows = []
    seen: dict[str, int] = {}
    for n, it in enumerate(picked, 1):
        print(f"\r  [{n}/{len(picked)}]", end="", flush=True)
        dis = pick_distractor(it)
        if dis is None:
            continue
        k = seen.get(it["stratum"], 0)
        seen[it["stratum"]] = k + 1
        gold_first = gold_goes_first(k)
        rows.append({"item": it, "translation": translate(client, it["sentence"]),
                     "distractor": dis, "gold_first": gold_first})
    print()

    L = ["# judge 人工驗證表（盲標）　二元強迫選擇", "",
         f"> {len(rows)} 筆，隨機種子 {args.seed}。",
         "> ⚠️ **本表刻意不含 gold、不含 sense_id、不含 judge 的判定**"
         "——看到任一個都會讓標註失去獨立性。",
         "> A/B 哪個是正解已在分層內交替打散，從順序看不出來。",
         "> 標完後由助理比對一致率。", "",
         "## 每題兩個問題", "",
         "**① 你的判定**　讀英文譯文，判斷這個中文詞在譯文裡的意思比較接近 A 還是 B。",
         "填 `A` 或 `B`。**兩個都說得通時，選比較貼切的那一個**（這是強迫選擇）。",
         "只有在**譯文的整體意思完全沒有傳達該詞的語義**時才填 `NONE`——",
         "量詞、虛化動詞在英文中常沒有對應詞，但意思仍在句子裡，那不算 NONE。", "",
         "**② 兩個都說得通嗎**　填 `是` 或 `否`。", "",
         "> 第二題的用意：中文詞網的義項切得比英文細，"
         "有些區分譯成英文之後資訊就不在了",
         "> （`the lowest record` 是「數值小於比較對象」還是「數值變小」？）。",
         "> 這一欄直接量出這類題目佔多少——它就是本基準的準確度天花板。",
         "> **不要因為第二題而改第一題**。",
         "", "=" * 59, ""]

    for i, r in enumerate(rows, 1):
        it = r["item"]
        gd, dd = it["gold_definition"], r["distractor"]["definition"]
        da, db = (gd, dd) if r["gold_first"] else (dd, gd)
        L += [f"## {i:02d}　目標詞：**{it['target_word']}**（{it['target_pos']}）", "",
              f"**中文原句**：{it['sentence']}",
              f"**英文譯文**：{r['translation']}", "",
              f"**A**：{da}",
              f"**B**：{db}", "",
              "**你的判定**: <!-- ① A / B / NONE -->",
              "**兩個都說得通嗎**: <!-- ② 是 / 否 -->",
              "**note**:", "", "=" * 59, ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    sfx = args.out_suffix
    md = RESULTS / f"judge_manual{sfx}.md"
    if md.exists() and "你的判定**: " in md.read_text(encoding="utf-8").replace(
            "你的判定**: <!--", "×"):
        print(f"🔴 {md.name} 已有填寫內容，不覆蓋。請用 --out-suffix 指定新檔名。",
              file=sys.stderr)
        return 1

    # ── 產出前的守門檢查（2026-08-21 裁示 2-5）──
    text = "\n".join(L)
    # 關鍵字只掃題目區。說明文字本來就會提到「本表不含 gold」，
    # 那不是洩漏；掃進去會讓檢查永遠失敗而被繞過，反而更危險。
    sep = "=" * 59
    items_text = text.split(sep, 1)[1] if sep in text else text
    problems = []
    sense_ids = {s["sense_id"] for r in rows for s in r["item"]["competing_senses"]}
    leaked_ids = sorted(i for i in sense_ids if i in text)
    if leaked_ids:
        problems.append(f"表中出現 sense_id：{leaked_ids[:5]}")
    for kw in ("gold", "GOLD", "正解", "正確答案", "correct"):
        if kw in items_text:
            problems.append(f"題目區出現疑似洩漏 gold 的字樣：{kw!r}")
    # gold 位置必須在分層內交替，不得全在同一側
    for st in {r["item"]["stratum"] for r in rows}:
        v = [r["gold_first"] for r in rows if r["item"]["stratum"] == st]
        if abs(sum(v) - (len(v) - sum(v))) > 1:
            problems.append(f"{st} 的 gold 位置未配平：A {sum(v)}／B {len(v) - sum(v)}")
    dup = sorted({r["item"]["id"] for r in rows} & used)
    if dup:
        problems.append(f"含先前驗證用過的題目：{dup[:5]}")
    if problems:
        print("🔴 守門檢查未通過，不產表：", file=sys.stderr)
        for p in problems:
            print(f"   - {p}", file=sys.stderr)
        return 2
    print("✅ 守門檢查通過：無 sense_id、無 gold 標記、位置已配平、"
          "未用過的題目、未出現在任何 prompt")

    md.write_text(text, encoding="utf-8")

    # 答案鍵另存，研究者標完後用它比對。檔名明示不要打開。
    key = RESULTS / f"judge_manual{sfx}_KEY_do_not_open.json"
    key.write_text(json.dumps(
        {"seed": args.seed, "excluded_probe_ids": sorted(used),
         "note": "研究者標完 judge_manual.md 之前不要開啟本檔",
         "design": "binary_forced_choice",
         "items": [{"n": i, "probe_id": r["item"]["id"],
                    "stratum": r["item"]["stratum"],
                    "gold_sense_id": r["item"]["gold_sense_id"],
                    "distractor_sense_id": r["distractor"]["sense_id"],
                    "gold_first": r["gold_first"],
                    "gold_letter": "A" if r["gold_first"] else "B",
                    "translation_sha": hashlib.sha256(
                        r["translation"].encode()).hexdigest()[:12]}
                   for i, r in enumerate(rows, 1)]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  {md}   ← 標這個")
    print(f"  {key}   ← 標完前不要開")
    print(f"\n  分層：主流 {sum(1 for r in rows if r['item']['stratum'] == 'dominant')}／"
          f"非主流 {sum(1 for r in rows if r['item']['stratum'] == 'non_dominant')}"
          f"（順序已打散，看不出來）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
