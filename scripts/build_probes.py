"""產生 MT 詞義錯誤基準的題目集。

⚠️ 2026-08-18 重寫：U/A/B 脈絡恆等設計已移除（不適用於 WSD 資料源，
理由見 `src/cognitive_core/data/probe_builder.py` 的模組說明）。
不需要研究者快篩——gold 來自 CWN-SemCor 的既有標註。

用法：
    python scripts/build_probes.py --total 200
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cognitive_core.data.cwn_loader import load_corpus  # noqa: E402
from cognitive_core.data.probe_builder import (  # noqa: E402
    length_distribution,
    select_candidates,
)

OUT = ROOT / "data" / "probes"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260818)
    args = ap.parse_args()
    n_dom = args.total // 2

    print("載入 CWN-SemCor …", flush=True)
    corpus = load_corpus()
    print(f"  題目 {len(corpus.items)}，目標詞 {len(corpus.senses_by_word)}")

    probes, stats = select_candidates(
        corpus, stratify=(n_dom, args.total - n_dom), seed=args.seed)
    print(f"\n  候選池 {stats['pool_total']}"
          f"（主流 {stats['pool_dominant']}／非主流 {stats['pool_non_dominant']}）")
    print(f"  要求 {stats['requested']}　達成 {stats['achieved']}")

    bad = [(p.id, e) for p in probes for e in p.check_invariants()]
    if bad:
        print(f"🔴 不變量檢查失敗 {len(bad)} 項：", file=sys.stderr)
        for pid, e in bad[:5]:
            print(f"    {pid}: {e}", file=sys.stderr)
        return 1
    print("  ✅ 全數通過不變量檢查")

    dist = length_distribution(probes)
    lens = [len(p.sentence) for p in probes]
    print(f"\n  句長分布：" + "　".join(f"{k} {v}" for k, v in dist.items()))
    print(f"  句長 平均 {sum(lens) / len(lens):.1f}，範圍 {min(lens)}–{max(lens)}")
    ranks = [p.gold_rank for p in probes if p.stratum == "non_dominant"]
    if ranks:
        print(f"  非主流層的 gold_rank：中位數 {sorted(ranks)[len(ranks) // 2]}，"
              f"範圍 {min(ranks)}–{max(ranks)}")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "wsd_probes.yaml"
    path.write_text(yaml.safe_dump(
        {"meta": {"task": "MT word-sense error benchmark",
                  "source": "CWN-SemCor", "license": "MIT", "seed": args.seed,
                  "stratify": stats["requested"], "achieved": stats["achieved"],
                  "pool": stats["pool_total"],
                  "length_distribution": dist,
                  "note": "gold 來自 CWN-SemCor 既有標註，不需人工快篩。"
                          "U/A/B 設計不適用於 WSD 資料源，已移除"},
         "items": [p.to_dict() for p in probes]},
        allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    print(f"\n  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
