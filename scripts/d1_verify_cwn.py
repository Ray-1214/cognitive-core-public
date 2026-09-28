"""D1 驗證：CWN-SemCor 與 CwnGraph 能不能用（不驗證完不寫 builder）。

回答的問題：
  2-1  HF 能否下載、實際授權、展平結構還原後的唯一組合數、
       目標詞清單與功能詞占比、句長、繁簡
  2-2  CwnGraph 安裝與 CwnImage.latest() 是否可用、CWN 2.0 授權

⚠️ 本腳本只呈現事實，不判斷哪些資料可用（地雷 3：篩選是研究者的工作）。

用法：
    python scripts/d1_verify_cwn.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cwn"

# CWN 詞類標記中屬於功能詞的前綴（規格書提到 P / Nes / DE）
FUNCTION_POS_PREFIXES = ("P", "Nes", "DE", "Caa", "Cab", "Cba", "Cbb", "T", "I")


def sep(title: str) -> None:
    print(f"\n{'=' * 74}\n{title}\n{'=' * 74}")


def is_simplified_hint(text: str) -> bool:
    """粗略偵測簡體殘留。只查幾個高頻簡繁差異字，不做完整判定。"""
    return any(c in text for c in "对说这没经过实现时问题机后进关点样发内学")


def main() -> int:
    sep("2-2  CwnGraph 與 CWN 2.0")
    cwn = None
    try:
        from CwnGraph import CwnImage
        print("  import CwnGraph            ✅")
        try:
            cwn = CwnImage.latest()
            print(f"  CwnImage.latest()         ✅ {type(cwn).__name__}")
            for attr in ("meta", "V"):
                if hasattr(cwn, attr):
                    v = getattr(cwn, attr)
                    print(f"    .{attr}: {str(v)[:120]}")
        except Exception as e:  # noqa: BLE001
            print(f"  CwnImage.latest()         ❌ {type(e).__name__}: {str(e)[:200]}")
    except Exception as e:  # noqa: BLE001
        print(f"  import CwnGraph            ❌ {type(e).__name__}: {str(e)[:200]}")

    sep("2-1  CWN-SemCor 載入與結構")
    ds = None
    card_license = "（未取得）"
    try:
        from datasets import load_dataset
        ds = load_dataset("lopentu/Chinese-Wordnet-SemCor")
        print(f"  load_dataset              ✅")
        print(f"  splits: { {k: len(v) for k, v in ds.items()} }")
        split = next(iter(ds.values()))
        print(f"  欄位: {split.column_names}")
        print(f"\n  第一筆（截斷顯示）：")
        row = split[0]
        for k, v in row.items():
            print(f"    {k:22} {str(v)[:110]}")
    except Exception as e:  # noqa: BLE001
        print(f"  load_dataset              ❌ {type(e).__name__}: {str(e)[:250]}")

    # 授權：從 dataset card 抓
    try:
        from huggingface_hub import DatasetCard
        card = DatasetCard.load("lopentu/Chinese-Wordnet-SemCor")
        cd = card.data.to_dict() if hasattr(card.data, "to_dict") else {}
        card_license = cd.get("license") or "（card 未標示 license）"
        print(f"\n  dataset card license      {card_license}")
        print(f"  card 其他欄位              {sorted(cd)}")
    except Exception as e:  # noqa: BLE001
        print(f"\n  dataset card              ❌ {type(e).__name__}: {str(e)[:160]}")

    if ds is None:
        print("\n🔴 資料集無法載入，後續統計略過。")
        return 1

    sep("2-1  展平結構還原後的唯一組合")
    split = next(iter(ds.values()))
    rows = list(split)
    print(f"  原始列數 {len(rows)}")

    # 找出句子欄與目標詞欄的實際名稱
    cols = split.column_names
    sent_col = next((c for c in cols if "sentence" in c.lower()), None)
    word_col = next((c for c in cols if "word" in c.lower() or "lemma" in c.lower()), None)
    pos_col = next((c for c in cols if c.lower() in ("pos", "tag", "postag")), None)
    print(f"  推定欄位：句子={sent_col}　目標詞={word_col}　詞類={pos_col}")

    if sent_col and word_col:
        combos = {(str(r[sent_col]), str(r[word_col])) for r in rows}
        print(f"  (句子, 目標詞) 唯一組合 {len(combos)}")
        print(f"  唯一句子 {len({c[0] for c in combos})}")
        print(f"  唯一目標詞 {len({c[1] for c in combos})}")

        wc = collections.Counter(c[1] for c in combos)
        print(f"\n  目標詞清單（{len(wc)} 個，依出現次數排序）：")
        for i, (w, n) in enumerate(wc.most_common()):
            end = "\n" if (i + 1) % 8 == 0 else "  "
            print(f"{w}({n})", end=end)
        print()

        if pos_col:
            pos_by_word: dict[str, set] = collections.defaultdict(set)
            for r in rows:
                pos_by_word[str(r[word_col])].add(str(r[pos_col]))
            func = {w for w, ps in pos_by_word.items()
                    if any(str(p).startswith(FUNCTION_POS_PREFIXES) for p in ps)}
            print(f"\n  詞類標記樣本：{sorted({str(r[pos_col]) for r in rows})[:20]}")
            print(f"  功能詞（前綴 {FUNCTION_POS_PREFIXES}）：{len(func)} 個")
            print(f"    {sorted(func)}")
            print(f"  扣掉功能詞後剩 {len(wc) - len(func)} 個目標詞")
        else:
            print("\n  ⚠️ 找不到詞類欄位，功能詞占比無法直接計算")

        lens = [len(c[0]) for c in combos]
        simp = [c[0] for c in combos if is_simplified_hint(c[0])]
        print(f"\n  句長（字元）：平均 {sum(lens) / len(lens):.1f}"
              f"　中位數 {sorted(lens)[len(lens) // 2]}"
              f"　範圍 {min(lens)}–{max(lens)}")
        print(f"  疑似含簡體字的句子：{len(simp)} / {len(combos)}")
        for s in simp[:3]:
            print(f"    {s[:70]}")

        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "d1_stats.json").write_text(json.dumps({
            "n_rows": len(rows), "n_combos": len(combos),
            "n_unique_sentences": len({c[0] for c in combos}),
            "n_target_words": len(wc),
            "target_words": dict(wc.most_common()),
            "columns": cols, "card_license": card_license,
            "sent_len_mean": sum(lens) / len(lens),
            "n_simplified_hint": len(simp),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  統計已存 {OUT / 'd1_stats.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
