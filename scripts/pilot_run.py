"""U/A 端到端粗跑（丟棄性質的探測，非正式實驗）。

⚠️ **所有數字都是煙霧測試，n=10，不得引用。**
目的是在研究者花 1.5 小時快篩之前，排除三個會讓整個設計白費的失敗模式：

  1. 脈絡沒做工 —— U 與 A 選到同一義項的比例過高
  2. judge 判不準 —— 主指標的基礎不可靠
  3. 兩層方向相反 —— 分層設計有問題

不需要研究者參與、不需要 C_B。只用條件 U 與條件 A（語料庫原句，免費）。

**量測位置的實作選擇**（須記錄）：
訊號必須量在 probe_span 的譯文上，不是整個輸入的譯文上。兩種取得方式：
  (a) 翻整句，再抽出 probe_span 對應的片段 —— 多一個抽取步驟與誤差來源
  (b) 只翻 probe_span，脈絡另外以背景提供 —— 輸出直接就是待測量的東西
本粗跑採 (b)。這是妥協：真實使用情境下模型會翻整句，而 (b) 改變了任務形狀。
正式版須評估 (a) 是否可行。

用法：
    python scripts/pilot_run.py
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from cognitive_core.assets import asset_manifest, prompt  # noqa: E402
from cognitive_core.llm import Client, LLMError  # noqa: E402
from cognitive_core.runlog import RunLog  # noqa: E402

OUT = ROOT / "data" / "probes"

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "chosen_sense_id": {"type": "string"},
        "confidence": {"type": "number"},
        "reasoning_summary": {"type": "string"},
    },
    "required": ["chosen_sense_id", "confidence", "reasoning_summary"],
    "additionalProperties": False,
}

TRANSLATE_SYS = (
    "You are a professional Chinese-to-English translator.\n"
    "Translate ONLY the target sentence. The context, if given, is background for "
    "disambiguation — do NOT translate it and do NOT include it in your output.\n"
    "Output only the English translation of the target sentence. "
    "No explanation, no quotes, no notes.")


def translate(client: Client, context: str, span: str) -> str:
    user = (f"【Context】{context}\n【Target sentence】{span}" if context
            else f"【Target sentence】{span}")
    return client.text("translate", [{"role": "system", "content": TRANSLATE_SYS},
                                     {"role": "user", "content": user}],
                       temperature=0.0, max_tokens=300)


def judge(client: Client, word: str, translation: str, senses: list[dict]) -> dict:
    sense_list = "\n".join(f"- `{s['sense_id']}` {s['definition']}" for s in senses)
    body = prompt("sense_judge").render(
        target_word=word, translation=translation, sense_list=sense_list)
    valid = {s["sense_id"] for s in senses} | {"NONE"}

    def validator(obj: dict) -> dict:
        sid = str(obj.get("chosen_sense_id", "")).strip()
        if sid not in valid:
            # 模型回傳清單外的 id 一律降級為 NONE 並記錄，不可靜默接受
            obj = {**obj, "chosen_sense_id": "NONE",
                   "invalid_id_returned": sid}
        c = obj.get("confidence", 0.0)
        try:
            obj["confidence"] = min(max(float(c), 0.0), 1.0)
        except (TypeError, ValueError):
            obj["confidence"] = 0.0
        return obj

    obj, tier = client.structured("judge", [{"role": "user", "content": body}],
                                  JUDGE_SCHEMA, validator=validator, max_tokens=400)
    obj["_tier"] = tier
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-dominant", type=int, default=3)
    ap.add_argument("--n-non", type=int, default=7)
    args = ap.parse_args()

    data = yaml.safe_load((OUT / "lexical_candidates.yaml").read_text(encoding="utf-8"))
    items = data["items"]
    dom = [i for i in items if i["stratum"] == "dominant"][:args.n_dominant]
    non = [i for i in items if i["stratum"] == "non_dominant"][:args.n_non]
    picked = dom + non
    print(f"抽 {len(picked)} 筆（主流 {len(dom)}／非主流 {len(non)}），未快篩、未挑選")

    run = RunLog("pilot_uab", meta={"assets": asset_manifest(),
                                    "purpose": "U/A 端到端粗跑（煙霧測試）",
                                    "n_items": len(picked),
                                    "measurement": "只翻 probe_span，脈絡作背景"})
    client = Client(run=run)
    judge_spec = client.cfg.resolve("judge")
    print(f"judge 模型：{judge_spec.provider}/{judge_spec.model}（judge_cross）")

    rows = []
    for n, it in enumerate(picked, 1):
        att = it["attested_condition"]
        cond_a = it["conditions"][att]
        span = it["probe_span"]
        ctx = cond_a["context_before"] + cond_a["context_after"]
        gold = cond_a["gold_sense_id"]
        senses = it["competing_senses"]
        print(f"\r[{n}/{len(picked)}] {it['id']:16}", end="", flush=True)
        rec: dict = {"id": it["id"], "stratum": it["stratum"],
                     "word": it["target_word"], "span": span,
                     "context": ctx, "gold": gold,
                     "gold_def": cond_a["gold_definition"],
                     "attested": att, "senses": senses}
        try:
            rec["trans_U"] = translate(client, "", span)
            rec["trans_A"] = translate(client, ctx, span)
            rec["judge_U"] = judge(client, it["target_word"], rec["trans_U"], senses)
            rec["judge_A"] = judge(client, it["target_word"], rec["trans_A"], senses)
        except LLMError as e:
            rec["error"] = str(e)[:200]
        rows.append(rec)
    print()

    ok = [r for r in rows if "error" not in r]
    same = [r for r in ok if r["judge_U"]["chosen_sense_id"]
            == r["judge_A"]["chosen_sense_id"]]
    a_correct = [r for r in ok if r["judge_A"]["chosen_sense_id"] == r["gold"]]
    u_correct = [r for r in ok if r["judge_U"]["chosen_sense_id"] == r["gold"]]
    none_a = [r for r in ok if r["judge_A"]["chosen_sense_id"] == "NONE"]

    def rate(sub, tot):
        return f"{len(sub)}/{len(tot)}" + (f"（{len(sub)/len(tot)*100:.0f}%）" if tot else "")

    # ── 報告 ──
    L = ["# U/A 端到端粗跑（煙霧測試）", "",
         "> ⚠️ **n=10，所有數字皆為煙霧測試，不得引用為實驗數據。**",
         "> 目的是在快篩前排除三個會讓設計白費的失敗模式，不是估計效應量。",
         ">",
         f"> judge 模型：`{judge_spec.provider}/{judge_spec.model}`（judge_cross，非受測模型）",
         "> 受測翻譯模型：校內 `mistral-small-4`",
         ">",
         "> **量測位置的實作妥協**：只翻 probe_span、脈絡另外以背景提供，",
         "> 而非翻整句再抽片段。這直接給出待測量的東西，但改變了任務形狀——",
         "> 真實情境下模型會翻整句。正式版須評估「翻整句再抽片段」是否可行。",
         "", "---", "",
         "## 2-1 脈絡有沒有做工？⭐", "",
         f"**U 與 A 選到同一義項：{rate(same, ok)}**", "",
         "| 判準 | 結果 |", "| --- | --- |",
         f"| >70% → 🔴 停，脈絡沒做工 | {'🔴 觸發' if ok and len(same)/len(ok) > 0.7 else '未觸發'} |",
         "",
         f"條件 A 選中 gold：{rate(a_correct, ok)}　"
         f"條件 U 選中 gold：{rate(u_correct, ok)}",
         f"條件 A 判為 NONE：{rate(none_a, ok)}",
         "", "---", "",
         "## 2-3 分層有沒有差？", "",
         "| 分層 | n | A 選中 gold | U/A 同義項 |", "| --- | :-: | :-: | :-: |"]
    for s in ["dominant", "non_dominant"]:
        sub = [r for r in ok if r["stratum"] == s]
        if not sub:
            continue
        c = [r for r in sub if r["judge_A"]["chosen_sense_id"] == r["gold"]]
        sm = [r for r in sub if r["judge_U"]["chosen_sense_id"]
              == r["judge_A"]["chosen_sense_id"]]
        L.append(f"| {s} | {len(sub)} | {rate(c, sub)} | {rate(sm, sub)} |")
    L += ["", "⚠️ n=3／n=7，方向明顯相反才有意義，數值不可解讀。", "",
          "---", "", "## 2-2 judge 判得準嗎？（請掃一遍）", ""]

    for i, r in enumerate(rows, 1):
        L.append(f"### {i:02d}　`{r['id']}`　［{r['stratum']}］　詞：**{r['word']}**")
        L.append("")
        if "error" in r:
            L.append(f"🔴 執行失敗：{r['error']}")
            L.append("")
            continue
        L.append(f"- **probe_span**：{r['span']}")
        L.append(f"- **脈絡（條件 {r['attested']}）**：{r['context'] or '（無）'}")
        L.append(f"- **U 譯文**：{r['trans_U']}")
        L.append(f"- **A 譯文**：{r['trans_A']}")
        L.append("")
        L.append("| | judge 選的義項 | 定義 | 信心 | 依據 |")
        L.append("| --- | --- | --- | :-: | --- |")
        defs = {s["sense_id"]: s["definition"] for s in r["senses"]}
        for cond in ("U", "A"):
            j = r[f"judge_{cond}"]
            sid = j["chosen_sense_id"]
            d = defs.get(sid, "—")
            L.append(f"| {cond} | `{sid}` | {d} | {j['confidence']:.2f} | "
                     f"{j['reasoning_summary']} |")
        L.append(f"| **gold** | `{r['gold']}` | {r['gold_def']} | — | 語料庫標註 |")
        flags = []
        if r["judge_U"]["chosen_sense_id"] == r["judge_A"]["chosen_sense_id"]:
            flags.append("U/A 同義項（脈絡未改變判定）")
        if r["judge_A"]["chosen_sense_id"] == r["gold"]:
            flags.append("A 選中 gold ✅")
        if r["judge_A"]["chosen_sense_id"] == "NONE":
            flags.append("A 判為 NONE")
        if flags:
            L.append("")
            L.append("　".join(f"`{f}`" for f in flags))
        L.append("")
        L.append("**你的判定是否同意 judge？** <!-- U: y/n　A: y/n -->")
        L.append("")

    s = run.summary()
    L += ["---", "", f"成本：{s['calls']} 次呼叫 / {s['total_tokens']:,} tokens / "
          f"{s['wall_s']}s / 快取命中 {s['cache_hits']}", f"run: `{s['path']}`"]

    p = OUT / "PILOT_RUN.md"
    p.write_text("\n".join(L), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"2-1 脈絡做工：U/A 同義項 {rate(same, ok)}"
          + ("　🔴 >70%，脈絡沒做工" if ok and len(same) / len(ok) > 0.7 else "　✅ 未觸發停止判準"))
    print(f"    A 選中 gold {rate(a_correct, ok)}　U 選中 gold {rate(u_correct, ok)}")
    print(f"2-3 分層：", end="")
    for st in ["dominant", "non_dominant"]:
        sub = [r for r in ok if r["stratum"] == st]
        c = [r for r in sub if r["judge_A"]["chosen_sense_id"] == r["gold"]]
        print(f"{st} {rate(c, sub)}　", end="")
    print(f"\n2-2 judge 逐筆列於 {p}（請掃一遍）")
    print(f"\n失敗 {len(rows) - len(ok)} 筆｜{s['calls']} 次呼叫｜{s['total_tokens']:,} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
