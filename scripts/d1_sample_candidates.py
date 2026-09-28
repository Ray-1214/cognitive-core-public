"""D1 2-3：抽 20 筆候選給研究者快篩。

⚠️ **只呈現，不判斷。** 不預先排除、不推薦、不標「這筆可用」——
篩選是研究者的工作（地雷 3）。

每筆呈現：
  目標詞與詞類
  最小完整子句（依標點切分，含 <> 標記的那一段）
  原句（供判斷子句是否為合法句子）
  CWN 給的競爭義項清單與定義

「最小完整子句」用標點切分產生。切出來是不是合法句子由研究者判斷——
研究者的修正 1-1 明確要求它必須是合法句子，本腳本無從代為認定。
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cwn"

MARK = re.compile(r"<([^<>]+)>")
CLAUSE_SPLIT = re.compile(r"[，。；！？、：]")
FUNC_PREFIX = ("P", "Nes", "DE", "Caa", "Cab", "Cba", "Cbb", "T", "I", "Neu", "Nep")


def minimal_clause(marked_sentence: str) -> tuple[str, int, int]:
    """含 <> 標記的最小子句，回傳 (子句含標記, 目標詞在子句中的起, 訖)。"""
    parts = CLAUSE_SPLIT.split(marked_sentence)
    clause = next((p for p in parts if MARK.search(p)), marked_sentence)
    clause = clause.strip()
    m = MARK.search(clause)
    if not m:
        return clause, -1, -1
    bare = clause[:m.start()] + m.group(1) + clause[m.end():]
    return bare, m.start(), m.start() + len(m.group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20260817)
    args = ap.parse_args()

    from datasets import load_dataset
    rows = list(load_dataset("lopentu/Chinese-Wordnet-SemCor")["train"])

    # 每個 (句子, 目標詞) 收斂為一筆，並蒐集該詞在資料集中的義項清單
    by_key: dict[tuple[str, str], dict] = {}
    senses_of: dict[str, dict[str, str]] = collections.defaultdict(dict)
    pos_of: dict[str, set[str]] = collections.defaultdict(set)
    for r in rows:
        key = (r["test_sentence"], r["test_word"])
        by_key.setdefault(key, {"word": r["test_word"], "pos": r["test_pos"],
                                "marked": r["test_sentence"],
                                "gold_sense": r["test_sense_id"],
                                "gold_def": r["test_definition"]})
        senses_of[r["test_word"]][r["test_sense_id"]] = r["test_definition"]
        senses_of[r["test_word"]][r["cwn_sense_id"]] = r["cwn_definition"]
        pos_of[r["test_word"]].add(r["test_pos"])

    items = list(by_key.values())
    rng = random.Random(args.seed)
    rng.shuffle(items)

    # 只做一項機械過濾：目標詞在句中恰出現一次（§3.1 明列的條件，非內容判斷）
    picked = []
    for it in items:
        bare_full = MARK.sub(it["word"], it["marked"])
        if bare_full.count(it["word"]) != 1:
            continue
        clause, lo, hi = minimal_clause(it["marked"])
        if lo < 0:
            continue
        it |= {"clause": clause, "span_start": lo, "span_end": hi,
               "clause_len": len(clause), "full_len": len(bare_full)}
        picked.append(it)
        if len(picked) >= args.n:
            break

    lines: list[str] = []
    lines.append("# CWN-SemCor 候選快篩（D1 2-3）")
    lines.append("")
    lines.append(f"> 隨機種子 {args.seed}，抽 {len(picked)} 筆。")
    lines.append("> 唯一的機械過濾：目標詞在原句中恰出現一次（§3.1 明列條件）。")
    lines.append("> **未做任何內容判斷**，沒有預先排除或推薦。")
    lines.append(">")
    lines.append("> 研究者的修正 1-1 要求「最小完整子句單獨呈現時必須是合法句子」，")
    lines.append("> 且「競爭義項在該子句下真的都可能」。兩者都需人工認定。")
    lines.append("")
    lines.append("每筆請填 `usable`：`y` / `n` / `?`，並可註明原因。")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, it in enumerate(picked, 1):
        func = "　⚠️ 該詞另有功能詞詞類" if any(
            p.startswith(FUNC_PREFIX) for p in pos_of[it["word"]]) else ""
        lines.append(f"## {i:02d}　目標詞「{it['word']}」（{it['pos']}）{func}")
        lines.append("")
        lines.append(f"**最小子句**（{it['clause_len']} 字）：{it['clause']}")
        lines.append(f"**目標詞位置**：字元 [{it['span_start']}, {it['span_end']})")
        lines.append("")
        lines.append(f"**原句**（{it['full_len']} 字）：{MARK.sub(lambda m: f'〔{m.group(1)}〕', it['marked'])}")
        lines.append("")
        sl = senses_of[it["word"]]
        lines.append(f"**CWN 義項清單**（該詞在資料集中共 {len(sl)} 個義項）：")
        for sid, d in sorted(sl.items()):
            star = " ★資料集標為本句正解" if sid == it["gold_sense"] else ""
            lines.append(f"- `{sid}` {d}{star}")
        lines.append("")
        lines.append("**usable**: <!-- y / n / ? -->")
        lines.append("**why**:")
        lines.append("")
        lines.append("---")
        lines.append("")

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "d1_candidates.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    print(f"已產出 {p}（{len(picked)} 筆）")
    cl = [it["clause_len"] for it in picked]
    fl = [it["full_len"] for it in picked]
    print(f"  最小子句長度：平均 {sum(cl) / len(cl):.1f}　範圍 {min(cl)}–{max(cl)}")
    print(f"  原句長度：    平均 {sum(fl) / len(fl):.1f}　範圍 {min(fl)}–{max(fl)}")
    nsen = [len(senses_of[it["word"]]) for it in picked]
    print(f"  義項數：      平均 {sum(nsen) / len(nsen):.1f}　範圍 {min(nsen)}–{max(nsen)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
