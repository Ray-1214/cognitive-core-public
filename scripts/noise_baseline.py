"""雜訊基準面板（§5 地雷 1）。

**任何**歧義／非歧義的組間比較，都必須先跑「只用句長的分類器」。
- spike 15 句：長度 AUC = 0.900，高於最佳量測 0.840 → 全部作廢
- Wu et al. 2025：長度 AUC = 0.965
- dev-30 初稿：0.758（語用類 1.000）→ 改等長替換後降至 0.520

**每次新增或改寫句子後都要重跑。** 表層特徵無限，不可能每個都工程到 0.5——
量化並揭露殘留即可，不要進入無止境修補。

用法：
    python scripts/noise_baseline.py
    python scripts/noise_baseline.py --dataset data/dev30/sentences.yaml
"""

from __future__ import annotations

import argparse
import math
import pathlib
import statistics
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent

PUNCT = "，。、！？；：「」『』（）…—,.!?;:()"


def auc(pos: list[float], neg: list[float]) -> float:
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def hanley_mcneil(a: float, n1: int, n2: int) -> tuple[float, float, float]:
    q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
    var = (a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2)
    se = math.sqrt(max(var, 0.0))
    return se, max(0.0, a - 1.96 * se), min(1.0, a + 1.96 * se)


FEATURES = {
    "句長": lambda s: float(len(s)),
    "標點總數": lambda s: float(sum(c in PUNCT for c in s)),
    "相異字元數": lambda s: float(len(set(s))),
    "字元重複率": lambda s: 1.0 - len(set(s)) / len(s) if s else 0.0,
}

THRESHOLD = 0.6      # 句長 AUC ≥ 此值須指出是哪幾句拉高的


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(ROOT / "data" / "dev30" / "sentences.yaml"))
    args = ap.parse_args()

    data = yaml.safe_load(pathlib.Path(args.dataset).read_text(encoding="utf-8"))
    items = data["items"]
    pairs = [(it["ambiguity_type"], it["id"], it["text"], it["minimal_pair"]["text"])
             for it in items if it.get("minimal_pair")]
    n = len(pairs)
    print(f"資料集：{args.dataset}")
    print(f"成對數：{n}（消歧句為正例）\n")

    print(f"{'特徵':12}{'全體 AUC':>10}{'SE':>7}{'95% CI':>16}   分型（僅報有無明顯異常）")
    print("-" * 86)
    length_auc = None
    for name, f in FEATURES.items():
        A = [f(a) for _, _, a, _ in pairs]
        D = [f(b) for _, _, _, b in pairs]
        a = auc(D, A)
        se, lo, hi = hanley_mcneil(a, n, n)
        if name == "句長":
            length_auc = a
        flags = []
        for t in ["LEXICAL", "REFERENTIAL", "PRAGMATIC"]:
            ps = [p for p in pairs if p[0] == t]
            if len(ps) < 3:
                continue
            ta = auc([f(b) for _, _, _, b in ps], [f(a2) for _, _, a2, _ in ps])
            # 分型 n=9–12，SE≈0.13–0.15，只報是否偏離 0.5 超過兩個 SE
            if abs(ta - 0.5) > 0.30:
                flags.append(f"{t[:4]}異常({ta:.2f})")
        note = "、".join(flags) if flags else "無明顯異常"
        print(f"{name:12}{a:10.3f}{se:7.3f}{f'[{lo:.2f}, {hi:.2f}]':>16}   {note}")

    print()
    print(f"判準：句長 AUC ≥ {THRESHOLD} 須指出是哪幾句拉高的")
    if length_auc is not None and length_auc >= THRESHOLD:
        print(f"🔴 句長 AUC = {length_auc:.3f} 超標，字數差最大的句子：")
        ranked = sorted(pairs, key=lambda p: -abs(len(p[3]) - len(p[2])))
        for t, sid, a, b in ranked[:8]:
            print(f"    {sid:12} {len(b) - len(a):+3d}  {a}  →  {b}")
    else:
        print(f"✅ 句長 AUC = {length_auc:.3f}，未超標")
        ranked = sorted(pairs, key=lambda p: -abs(len(p[3]) - len(p[2])))
        print("   字數差最大的三句（供參考，未超標）：")
        for t, sid, a, b in ranked[:3]:
            print(f"    {sid:12} {len(b) - len(a):+3d}  {a}  →  {b}")

    diffs = [len(b) - len(a) for _, _, a, b in pairs]
    print(f"\n字數差：平均 {statistics.mean(diffs):+.2f}，"
          f"範圍 {min(diffs):+d}～{max(diffs):+d}，"
          f"|差|>2 的有 {sum(1 for d in diffs if abs(d) > 2)} 句")
    print("\n⚠️ 表層特徵無限，不可能每個都工程到 0.5。量化並揭露殘留即可——")
    print("   過度約束的對立對會變成沒人會講的句子，那時量的是「偵測怪句子」。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
