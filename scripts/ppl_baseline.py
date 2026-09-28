"""原文 PPL 雜訊基準（技術設計文件 §8.7）。

**這是可能讓多視角在偵測階段失去存在理由的實驗。**

若單次前向的原文 PPL 就能達到 AUC ≈ 0.75，那 RQ2 的答案就是「用 PPL 就好」——
不必翻譯、不必回譯、不必多視角。在 M5 才發現等於白做半年，所以現在做。

它有明確理由會有訊號，但**方向可能相反**：間接表達多為高頻套語（「時間不早了」、
「我盡量」），PPL 應該偏低；改寫後的直接表達反而可能較高。因此 AUC 顯著低於 0.5
時翻轉後仍是強訊號，兩個方向都要報。

為何不用校內 API：`/v1/completions` + `echo=true` + `logprobs` 回 500（LiteLLM proxy
不支援 legacy endpoint），chat 端的 logprobs 只有生成 token 而非 prompt token，
拿不到原文 PPL。原文 PPL 不必與主實驗同模型，故改用本地小模型。

用法：
    python scripts/ppl_baseline.py
    python scripts/ppl_baseline.py --model uer/gpt2-chinese-cluecorpussmall
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEV = ROOT / "data" / "dev30"

# 預設用 CKIP（中研院）的繁中 GPT-2，與本專案的台灣繁中資料最貼合
DEFAULT_MODEL = "ckiplab/gpt2-base-chinese"


def auc(pos: list[float], neg: list[float]) -> float:
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def hm_se(a: float, n1: int, n2: int) -> float:
    q1 = a / (2 - a)
    q2 = 2 * a * a / (1 + a)
    return math.sqrt(max((a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2), 0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"載入 {args.model} …", flush=True)
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model)
    model.eval()
    print(f"  參數量 {sum(p.numel() for p in model.parameters())/1e6:.0f}M", flush=True)

    @torch.no_grad()
    def ppl(text: str) -> float | None:
        """單次前向的原文 perplexity。"""
        ids = tok(text, return_tensors="pt").input_ids
        if ids.shape[1] < 2:
            return None
        out = model(ids, labels=ids)
        return float(torch.exp(out.loss))

    data = yaml.safe_load((DEV / "sentences.yaml").read_text(encoding="utf-8"))
    items = data["items"]

    rows = []
    for it in items:
        pa, pd = ppl(it["text"]), ppl(it["minimal_pair"]["text"])
        if pa is None or pd is None:
            continue
        rows.append({"id": it["id"], "type": it["ambiguity_type"],
                     "amb_text": it["text"], "dis_text": it["minimal_pair"]["text"],
                     "amb_ppl": pa, "dis_ppl": pd,
                     "amb_len": len(it["text"]), "dis_len": len(it["minimal_pair"]["text"])})
    print(f"完成 {len(rows)}/{len(items)} 對", flush=True)

    A = [r["amb_ppl"] for r in rows]
    D = [r["dis_ppl"] for r in rows]
    n = len(rows)

    # 兩個方向都算：高 PPL=歧義，以及低 PPL=歧義（間接套語頻率高）
    a_hi = auc(A, D)          # 歧義句 PPL 較高
    a_lo = auc(D, A)          # 歧義句 PPL 較低
    best = max(a_hi, a_lo)
    se = hm_se(best, n, n)

    print("\n" + "=" * 74)
    print("原文 PPL 作為歧義偵測訊號（單次前向，不翻譯、不回譯）")
    print("=" * 74)
    print(f"  歧義句 PPL  中位數 {statistics.median(A):8.1f}  平均 {statistics.mean(A):8.1f}")
    print(f"  消歧句 PPL  中位數 {statistics.median(D):8.1f}  平均 {statistics.mean(D):8.1f}")
    print()
    print(f"  AUC（假設 歧義=高 PPL）= {a_hi:.3f}")
    print(f"  AUC（假設 歧義=低 PPL）= {a_lo:.3f}   ← 間接套語頻率高，此方向可能才對")
    print(f"  取較佳方向 = {best:.3f}   SE≈{se:.3f}   95% CI [{max(0,best-1.96*se):.2f}, {min(1,best+1.96*se):.2f}]")
    print()
    print("  判準：")
    print("    ≥0.75  🔴 PPL 單獨即可偵測 → 多視角在偵測階段沒有存在理由，RQ2 需重新定位")
    print("    0.6–0.75 ⚠️ PPL 為有效訊號 → 納入 §4.1 成為第六個候選訊號 S6，")
    print("             且多視角必須證明其增益超過 PPL 才有價值")
    print("    <0.6   ✅ PPL 訊號弱 → 多視角的存在理由不受挑戰")
    print("  >>> " + ("🔴 PPL 單獨即足" if best >= 0.75 else
                      "⚠️ PPL 為有效訊號，須納入基準" if best >= 0.6 else
                      "✅ PPL 訊號弱"))

    print("\n  分型（n=9–12，SE≈0.13–0.15，只能說有無明顯異常，不可解讀型間差異）：")
    for t in ["LEXICAL", "REFERENTIAL", "PRAGMATIC"]:
        rs = [r for r in rows if r["type"] == t]
        if len(rs) < 2:
            continue
        a2 = [r["amb_ppl"] for r in rs]
        d2 = [r["dis_ppl"] for r in rs]
        print(f"    {t:12} 高={auc(a2,d2):.3f}  低={auc(d2,a2):.3f}  n={len(rs)}")

    # PPL 與長度的相關 —— 確認 PPL 不是長度的代理
    def pearson(x, y):
        mx, my = statistics.mean(x), statistics.mean(y)
        num = sum((a - mx) * (b - my) for a, b in zip(x, y))
        den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
        return num / den if den else 0.0

    L = [r["amb_len"] for r in rows] + [r["dis_len"] for r in rows]
    P = A + D
    print(f"\n  r(句長, PPL) = {pearson(L, P):+.3f}"
          f"   {'⚠️ PPL 與長度高度相關，可能只是長度的代理' if abs(pearson(L,P))>0.5 else '（相關不高，PPL 非長度代理）'}")

    (DEV / "ppl_baseline.json").write_text(json.dumps(
        {"model": args.model, "auc_high": a_hi, "auc_low": a_lo, "n": n, "rows": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完整結果：{DEV / 'ppl_baseline.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
