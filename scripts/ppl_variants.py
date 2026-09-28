"""PPL 的局部變體：span surprisal 與句內最大 token surprisal（§8.7 延伸）。

整句 PPL 是全 token 的平均對數機率，但歧義通常是**局部**的——「方便的話明天再說吧」
的歧義只在「方便」兩個字，在 9 個 token 上平均會被稀釋四五倍。§8.7 測得整句 PPL
AUC = 0.516，可能是問錯了問題而非訊號不存在。

兩個變體：
  span   標註歧義處的平均 surprisal   診斷用：訊號到底存不存在
  max    句內最大 token surprisal     可部署版：不需要標註

三種結果三種意義：
  都 ≈0.5      → PPL 家族可以寫死，不再考慮
  span 高 max 低 → 訊號存在但沒有標註就定位不到，這件事本身可寫
  都高          → 便宜偵測器找到了，RQ2 需重新定位

span 來源：dev-30 的 minimal_pair.edit 欄位形如「難說 → 難以評斷（等長替換）」，
箭號左側即為歧義處，不需額外標註。

用法：
    python scripts/ppl_variants.py
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import statistics
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEV = ROOT / "data" / "dev30"
DEFAULT_MODEL = "ckiplab/gpt2-base-chinese"


def auc(pos: list[float], neg: list[float]) -> float:
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def hm_se(a: float, n1: int, n2: int) -> float:
    q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
    return math.sqrt(max((a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2), 0))


def extract_spans(edit: str, amb: str, dis: str) -> tuple[str, str] | None:
    """由 minimal_pair.edit 取出「歧義處 → 替換處」這一對。

    ⚠️ 必須 span 對 span 比較。初版拿歧義句的 span surprisal 去比消歧句的
    **整句**平均，是子片段對整句平均，必然偏低（常見套語 vs 全句），
    得到虛假的 AUC 0.851。
    """
    m = re.match(r"\s*(.+?)\s*(?:→|->)\s*(.+?)\s*(?:（|\(|$)", edit)
    if not m:
        return None
    clean = lambda s: re.sub(r"^[「『]|[」』]$", "", s.strip())
    a, b = clean(m.group(1)), clean(m.group(2))
    return (a, b) if a and b and a in amb and b in dis else None


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

    @torch.no_grad()
    def surprisals(text: str) -> tuple[list[float], list[tuple[int, int]]] | None:
        """回傳每個 token 的 surprisal（-log p）與其字元區間。"""
        enc = tok(text, return_tensors="pt", return_offsets_mapping=True)
        ids = enc.input_ids
        if ids.shape[1] < 2:
            return None
        logits = model(ids).logits
        logp = torch.log_softmax(logits[0, :-1], dim=-1)
        tgt = ids[0, 1:]
        s = [-float(logp[i, tgt[i]]) for i in range(len(tgt))]
        offs = [tuple(x) for x in enc.offset_mapping[0].tolist()][1:]   # 對齊 target
        return s, offs

    data = yaml.safe_load((DEV / "sentences.yaml").read_text(encoding="utf-8"))
    items = data["items"]

    rows, no_span = [], []
    for it in items:
        pair = extract_spans(it["minimal_pair"]["edit"], it["text"], it["minimal_pair"]["text"])
        if pair is None:
            no_span.append(it["id"])
        for key, txt in (("amb", it["text"]), ("dis", it["minimal_pair"]["text"])):
            sp = pair[0 if key == "amb" else 1] if pair else None
            r = surprisals(txt)
            if r is None:
                continue
            s, offs = r
            rec = {"id": it["id"], "type": it["ambiguity_type"], "side": key,
                   "text": txt, "mean": statistics.mean(s), "max": max(s)}
            if sp:
                lo = txt.index(sp); hi = lo + len(sp)
                sel = [v for v, (a, b) in zip(s, offs) if a < hi and b > lo]
                rec["span"] = sp
                rec["span_mean"] = statistics.mean(sel) if sel else None
            rows.append(rec)

    A = {r["id"]: r for r in rows if r["side"] == "amb"}
    D = {r["id"]: r for r in rows if r["side"] == "dis"}
    ids = [i for i in A if i in D]
    n = len(ids)
    print(f"完成 {n} 對；無法取出 span 的句子 {len(no_span)} 句"
          + (f"（{', '.join(no_span)}）" if no_span else ""))

    print("\n" + "=" * 76)
    print("PPL 局部變體：歧義是否為局部訊號")
    print("=" * 76)

    results = {}
    for name, key in [("整句平均 surprisal", "mean"), ("句內最大 surprisal", "max")]:
        a = [A[i][key] for i in ids]
        d = [D[i][key] for i in ids]
        hi, lo = auc(a, d), auc(d, a)
        best = max(hi, lo)
        se = hm_se(best, n, n)
        results[key] = best
        print(f"\n  【{name}】(可部署，不需標註)")
        print(f"    歧義高 = {hi:.3f}   歧義低 = {lo:.3f}   取較佳 = {best:.3f}")
        print(f"    SE≈{se:.3f}   95% CI [{max(0,best-1.96*se):.2f}, {min(1,best+1.96*se):.2f}]")

    # span 必須對 span 比。拿歧義句的 span 去比消歧句的整句平均是子片段對整句，
    # 常見套語必然偏低，會得到虛假的高 AUC。
    sp = [i for i in ids
          if A[i].get("span_mean") is not None and D[i].get("span_mean") is not None]
    if sp:
        print(f"\n  【span 對 span 的 surprisal】(診斷用，需標註；n={len(sp)})")
        a_span = [A[i]["span_mean"] for i in sp]
        d_span = [D[i]["span_mean"] for i in sp]
        print(f"    歧義處 span 平均   {statistics.mean(a_span):7.3f}   （例：{A[sp[0]]['span']}）")
        print(f"    替換處 span 平均   {statistics.mean(d_span):7.3f}   （例：{D[sp[0]]['span']}）")
        hi, lo = auc(a_span, d_span), auc(d_span, a_span)
        best = max(hi, lo)
        se = hm_se(best, len(sp), len(sp))
        results["span"] = best
        print(f"    歧義處較高 = {hi:.3f}   歧義處較低 = {lo:.3f}   取較佳 = {best:.3f}")
        print(f"    CI [{max(0,best-1.96*se):.2f}, {min(1,best+1.96*se):.2f}]")
        # 句內對照：歧義處相對同句其餘部分是否突出，長度效應自然抵銷
        ratio = [A[i]["span_mean"] / A[i]["mean"] if A[i]["mean"] else 1.0 for i in sp]
        med = statistics.median(ratio)
        print(f"    句內比值 span/整句 中位數 = {med:.3f}  "
              + ("← 歧義處比句子其餘部分更難預測" if med > 1.2 else
                 "← 歧義處反而更好預測（高頻套語，與假設一致）" if med < 0.85 else
                 "← 未特別突出"))

    print("\n" + "=" * 76)
    best_deploy = results.get("max", 0)
    best_span = results.get("span", 0)
    print(f"  可部署變體（max）  = {best_deploy:.3f}")
    print(f"  診斷變體（span）   = {best_span:.3f}")
    print(f"  基準（整句平均）    = {results.get('mean', 0):.3f}")
    print()
    if best_deploy >= 0.75:
        print("  >>> 🔴 便宜偵測器找到了：句內最大 surprisal 單獨即可偵測，RQ2 需重新定位")
    elif best_span >= 0.70 > best_deploy:
        print("  >>> ⚠️ 訊號存在但需標註才定位得到——沒有標註就用不上。")
        print("      這個落差本身可寫：歧義是局部訊號，整句層級的量測會稀釋掉它。")
    elif max(best_deploy, best_span, results.get("mean", 0)) < 0.60:
        print("  >>> ✅ 三個變體皆無訊號，PPL 家族可以寫死，不再列入候選訊號")
    else:
        print("  >>> ⚠️ 介於之間，n=30 無法定案，須於 CAD-100（SE≈0.04）重測")
    print(f"\n  ⚠️ n={n}，SE≈0.07–0.09，CI 寬。所有結論須在 CAD-100 上重測。")

    (DEV / "ppl_variants.json").write_text(json.dumps(
        {"model": args.model, "n": n, "auc": results, "rows": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完整結果：{DEV / 'ppl_variants.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
