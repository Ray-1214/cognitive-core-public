"""D1 續：詞類分布、義項數、目標詞標記結構、CWN 2.0 授權。

前一支腳本的欄位偵測寫錯（欄位名為 test_pos，偵測器只找 pos），此處修正。
另外發現 test_sentence 用 <目標詞> 標記位置——這正好給了 probe_span 的
字元起訖，直接對應研究者修正 1-2 的要求。

⚠️ 只呈現事實，不判斷哪些可用。
"""

from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cwn"

# CWN／中研院詞類標記中的功能詞前綴
FUNC_PREFIX = ("P", "Nes", "DE", "Caa", "Cab", "Cba", "Cbb", "T", "I", "Neu", "Nep")
MARK = re.compile(r"<([^<>]+)>")


def sep(t: str) -> None:
    print(f"\n{'=' * 74}\n{t}\n{'=' * 74}")


def main() -> int:
    from datasets import load_dataset
    ds = load_dataset("lopentu/Chinese-Wordnet-SemCor")
    rows = list(ds["train"])

    sep("目標詞標記結構（test_sentence 用 <詞> 標位置）")
    n_marked = sum(1 for r in rows if MARK.search(r["test_sentence"]))
    n_multi = sum(1 for r in rows if len(MARK.findall(r["test_sentence"])) > 1)
    print(f"  含 <> 標記的列 {n_marked}/{len(rows)}")
    print(f"  含多於一個 <> 標記的列 {n_multi}")
    mismatch = sum(1 for r in rows
                   if (m := MARK.search(r["test_sentence"]))
                   and m.group(1) != r["test_word"])
    print(f"  標記內容與 test_word 不一致的列 {mismatch}")
    print("  ⇒ probe_span 的字元起訖可由 <> 位置直接取得（修正 1-2 所需）")

    sep("詞類分布與功能詞")
    by_word_pos: dict[str, set[str]] = collections.defaultdict(set)
    for r in rows:
        by_word_pos[r["test_word"]].add(r["test_pos"])
    pos_counter = collections.Counter(r["test_pos"] for r in rows)
    print(f"  詞類標記共 {len(pos_counter)} 種：")
    for p, n in pos_counter.most_common():
        print(f"    {p:8} {n:>7}")
    func_words = sorted(w for w, ps in by_word_pos.items()
                        if any(p.startswith(FUNC_PREFIX) for p in ps))
    print(f"\n  目標詞總數 {len(by_word_pos)}")
    print(f"  含功能詞詞類者 {len(func_words)}：{func_words}")
    print(f"  扣掉後剩 {len(by_word_pos) - len(func_words)}")

    sep("每個目標詞的義項數（§3.1 篩選條件：義項數 ≥2）")
    senses: dict[str, set[str]] = collections.defaultdict(set)
    for r in rows:
        senses[r["test_word"]].add(r["test_sense_id"])
        senses[r["test_word"]].add(r["cwn_sense_id"])
    dist = collections.Counter(len(v) for v in senses.values())
    print(f"  義項數分布（詞數）：{dict(sorted(dist.items()))}")
    ge2 = [w for w, v in senses.items() if len(v) >= 2]
    print(f"  義項數 ≥2 的目標詞 {len(ge2)} / {len(senses)}")
    top = sorted(senses.items(), key=lambda kv: -len(kv[1]))[:12]
    print("  義項最多的 12 個：" + "　".join(f"{w}({len(v)})" for w, v in top))

    sep("句子中目標詞出現次數（§3.1：恰一次）")
    exactly_once = 0
    for r in rows:
        bare = MARK.sub(r["test_word"], r["test_sentence"])
        if bare.count(r["test_word"]) == 1:
            exactly_once += 1
    print(f"  目標詞在句中恰出現一次的列 {exactly_once}/{len(rows)}"
          f"（{exactly_once / len(rows) * 100:.1f}%）")

    sep("2-2  CWN 2.0 授權與版本")
    try:
        from CwnGraph import CwnImage
        cwn = CwnImage.latest()
        meta = getattr(cwn, "meta", None)
        print(f"  meta 型別 {type(meta).__name__}")
        if isinstance(meta, dict):
            for k, v in meta.items():
                print(f"    {k:16} {str(v)[:150]}")
        else:
            print(f"    {str(meta)[:400]}")
        # 授權字串常放在 meta 或套件的 __doc__
        import CwnGraph
        doc = (CwnGraph.__doc__ or "")[:300]
        print(f"  CwnGraph.__doc__ {doc!r}")
        pkg = pathlib.Path(CwnGraph.__file__).parent
        lic = [p.name for p in pkg.parent.glob("CwnGraph*") if "dist-info" in p.name]
        print(f"  dist-info: {lic}")
        for d in lic:
            for cand in ("LICENSE", "LICENSE.txt", "METADATA"):
                f = pkg.parent / d / cand
                if f.exists():
                    txt = f.read_text(encoding="utf-8", errors="replace")
                    if cand == "METADATA":
                        for line in txt.splitlines():
                            if line.lower().startswith(("license", "classifier: license")):
                                print(f"    METADATA {line[:120]}")
                    else:
                        print(f"    {cand} 前 200 字：{txt[:200]!r}")
    except Exception as e:  # noqa: BLE001
        print(f"  ❌ {type(e).__name__}: {str(e)[:200]}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "d1_stats2.json").write_text(json.dumps({
        "pos_distribution": dict(pos_counter),
        "n_target_words": len(by_word_pos),
        "function_words": func_words,
        "n_after_removing_function": len(by_word_pos) - len(func_words),
        "sense_count_distribution": {str(k): v for k, v in sorted(dist.items())},
        "n_words_ge2_senses": len(ge2),
        "exactly_once_ratio": exactly_once / len(rows),
        "marker_ok": {"n_marked": n_marked, "n_multi": n_multi, "mismatch": mismatch},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  已存 {OUT / 'd1_stats2.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
