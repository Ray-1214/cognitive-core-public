"""D1.5 §1 §2：CwnGraph 是否必要、三項新篩選判準是否可行。

§1-1  CWN-SemCor 展平結構是否已含完整義項清單（若是則不需 CwnGraph → GPL 問題消失）
§2-1  功能詞改為出現層級判斷
§2-2  「同音競爭義項 ≥2」——驗證 sense_id 前綴是否可用來分讀音／lemma
§2-3  義項出現頻率統計，供「優先選 gold ≠ 最高頻」使用
"""

from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cwn"
MARK = re.compile(r"<([^<>]+)>")
FUNC_PREFIX = ("P", "Nes", "DE", "Caa", "Cab", "Cba", "Cbb", "T", "I", "Neu", "Nep")


def sep(t: str) -> None:
    print(f"\n{'=' * 74}\n{t}\n{'=' * 74}")


def main() -> int:
    from datasets import load_dataset
    rows = list(load_dataset("lopentu/Chinese-Wordnet-SemCor")["train"])

    # ── §1-1 資料集自帶的義項清單是否完整 ──
    sep("§1-1  CWN-SemCor 是否自帶完整義項清單（決定要不要 CwnGraph）")
    from_data: dict[str, dict[str, str]] = collections.defaultdict(dict)
    for r in rows:
        from_data[r["test_word"]][r["test_sense_id"]] = r["test_definition"]
        from_data[r["test_word"]][r["cwn_sense_id"]] = r["cwn_definition"]
    print(f"  由資料集還原：{len(from_data)} 個目標詞")
    print(f"  義項數合計 {sum(len(v) for v in from_data.values())}")
    print(f"  定義全部非空：{all(all(d for d in v.values()) for v in from_data.values())}")

    # 與 CwnGraph 對照
    try:
        from CwnGraph import CwnImage
        cwn = CwnImage.latest()
        sample = ["死", "中", "行", "長", "空"]
        print(f"\n  與 CwnGraph 對照（抽 {len(sample)} 詞）：")
        print(f"  {'詞':4}{'資料集義項數':>12}{'CwnGraph 義項數':>16}{'資料集⊆CwnGraph':>16}")
        for w in sample:
            if w not in from_data:
                continue
            try:
                lemmas = cwn.find_lemma(f"^{w}$")
                cwn_ids = set()
                for lm in lemmas:
                    for sense in lm.senses:
                        cwn_ids.add(sense.id)
                ds_ids = set(from_data[w])
                subset = ds_ids <= cwn_ids
                print(f"  {w:4}{len(ds_ids):>12}{len(cwn_ids):>16}{str(subset):>16}")
            except Exception as e:  # noqa: BLE001
                print(f"  {w:4}  CwnGraph 查詢失敗：{type(e).__name__}")
    except Exception as e:  # noqa: BLE001
        print(f"  CwnGraph 不可用：{type(e).__name__}")

    # ── §2-2 sense_id 前綴是否能分 lemma／讀音 ──
    sep("§2-2  sense_id 前綴能否用來分讀音／lemma")
    print("  假設：sense_id 前 6 碼 = lemma id，後 2 碼 = 該 lemma 內的義項序號")
    for w in ["中", "行", "長", "死"]:
        if w not in from_data:
            continue
        groups: dict[str, list[str]] = collections.defaultdict(list)
        for sid in sorted(from_data[w]):
            groups[sid[:6]].append(sid)
        print(f"\n  「{w}」共 {len(from_data[w])} 義項，分成 {len(groups)} 個 lemma 群：")
        for lid, sids in sorted(groups.items()):
            d0 = from_data[w][sids[0]]
            print(f"    lemma {lid}  {len(sids):>3} 義項  例：{d0[:38]}")

    # 全體：依 lemma 分群後，同群義項數 ≥2 的詞有多少
    ge2_same_lemma = []
    for w, senses in from_data.items():
        g: dict[str, int] = collections.Counter(s[:6] for s in senses)
        if any(n >= 2 for n in g.values()):
            ge2_same_lemma.append(w)
    print(f"\n  依 lemma 分群後仍有『同群義項 ≥2』的目標詞："
          f"{len(ge2_same_lemma)} / {len(from_data)}")

    # ── §2-1 功能詞出現層級 ──
    sep("§2-1  功能詞改為出現層級判斷")
    n_func_rows = sum(1 for r in rows if str(r["test_pos"]).startswith(FUNC_PREFIX))
    print(f"  以列（出現）為單位：{n_func_rows} / {len(rows)}"
          f"（{n_func_rows / len(rows) * 100:.1f}%）被標為功能詞詞類")
    words_all_func = []
    words_mixed = []
    by_word_pos: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in rows:
        by_word_pos[r["test_word"]][r["test_pos"]] += 1
    for w, pc in by_word_pos.items():
        fn = sum(n for p, n in pc.items() if p.startswith(FUNC_PREFIX))
        if fn == sum(pc.values()):
            words_all_func.append(w)
        elif fn:
            words_mixed.append(w)
    print(f"  全部出現皆為功能詞的詞：{len(words_all_func)}　{words_all_func}")
    print(f"  混合的詞：{len(words_mixed)}")
    print(f"  ⇒ 出現層級排除只砍掉 {n_func_rows} 列；"
          f"詞層級排除會誤殺 {len(words_mixed)} 個詞的全部出現")

    # ── §2-3 義項頻率 ──
    sep("§2-3  義項出現頻率（供「優先選 gold ≠ 最高頻」使用）")
    # 每個 (句子,詞) 只算一次 gold
    gold_by_key: dict[tuple[str, str], str] = {}
    for r in rows:
        gold_by_key[(r["test_sentence"], r["test_word"])] = r["test_sense_id"]
    freq: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for (sent, w), sid in gold_by_key.items():
        freq[w][sid] += 1
    n_gold_is_top = 0
    n_total = 0
    for (sent, w), sid in gold_by_key.items():
        top = freq[w].most_common(1)[0][0]
        n_total += 1
        if sid == top:
            n_gold_is_top += 1
    print(f"  題目總數（唯一 句子×詞）：{n_total}")
    print(f"  gold 即該詞最高頻義項者：{n_gold_is_top}"
          f"（{n_gold_is_top / n_total * 100:.1f}%）")
    print(f"  gold ≠ 最高頻者：{n_total - n_gold_is_top}"
          f"（{(n_total - n_gold_is_top) / n_total * 100:.1f}%）← 有鑑別力的題庫")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "d15_criteria.json").write_text(json.dumps({
        "sense_inventory_from_dataset": {w: len(v) for w, v in from_data.items()},
        "n_words_ge2_same_lemma": len(ge2_same_lemma),
        "words_ge2_same_lemma": sorted(ge2_same_lemma),
        "func_rows": n_func_rows, "total_rows": len(rows),
        "words_all_function": sorted(words_all_func),
        "words_mixed_function": sorted(words_mixed),
        "n_items": n_total, "n_gold_is_top_sense": n_gold_is_top,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已存 {OUT / 'd15_criteria.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
