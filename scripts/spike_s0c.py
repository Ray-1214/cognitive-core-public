"""S0c — 跨語言 vs 同語言：類型學差異到底貢獻了什麼（技術設計文件 §8.5）。

S0b 證明「行為訊號（AUC 0.84）優於自陳訊號（0.55）」，但**沒有**證明訊號來自
計畫書 §4.4 主張的「日英語法強制顯性化」。若同語言重取樣也能拿到 0.84，
則類型學差異貢獻為零，多視角驗證退化成「比較貴的 self-consistency」，§4.4 落空。

本腳本做完全配對的對照——同溫度、同樣本數、同量測方式，
**唯一變因是第二個樣本換語言還是換一次取樣**：

  A  cross_en_ja   en(T) + ja(T)     ← 跨語言（計畫書主張）
  B  same_en_en    en(T) + en(T)     ← 同語言重取樣（虛無假設）
  C  same_ja_ja    ja(T) + ja(T)     ← 同上，確認非英文特有
  D  cross_en_de   en(T) + de(T)     ← 換一組語言對，檢驗是否日英專屬

附帶兩項：
  E  V4 改問法      強制指出差異而非是／否 —— S0b 的 AUC 0.500 可能是退化輸出
  F  de / fr 品質   確認校內模型的德法譯文堪用（Open Q F 前置）

用法：
    python scripts/spike_s0c.py --repeats 3 --temp 0.7
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "spike"
BASE = os.environ.get("ITHU_API_BASE", "<your-llm-endpoint>").rstrip("/") + "/v1"
KEY = os.environ.get("ITHU_API_KEY")

GEN_MODEL = "mistral-small-4"
EMBED_MODEL = "bge-m3-embedding"
LANG_NAME = {"en": "英文", "ja": "日文", "de": "德文", "fr": "法文"}


def _post(path: str, payload: dict, retries: int = 3) -> dict:
    body = json.dumps(payload).encode()
    for attempt in range(retries):
        req = urllib.request.Request(BASE + path, data=body,
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            return {"__error__": f"HTTP {e.code}", "__body__": e.read().decode()[:200]}
        except Exception as e:  # noqa: BLE001
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error__": type(e).__name__, "__body__": str(e)[:200]}
    return {"__error__": "exhausted"}


def chat(system: str, user: str, temp: float = 0.0, max_tokens: int = 500) -> str | None:
    r = _post("/chat/completions", {"model": GEN_MODEL, "temperature": temp,
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    if "__error__" in r:
        return None
    try:
        return r["choices"][0]["message"].get("content")
    except (KeyError, IndexError):
        return None


def embed(texts: list[str]) -> list[list[float]] | None:
    r = _post("/embeddings", {"model": EMBED_MODEL, "input": texts})
    return None if "__error__" in r else [d["embedding"] for d in r["data"]]


def cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def auc_ci(a: float, n1: int, n2: int) -> tuple[float, float, float]:
    """Hanley–McNeil 標準誤與 95% CI。"""
    q1 = a / (2 - a)
    q2 = 2 * a * a / (1 + a)
    var = (a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2)
    se = math.sqrt(max(var, 0.0))
    return se, max(0.0, a - 1.96 * se), min(1.0, a + 1.96 * se)


def translate_n(text: str, lang: str, temp: float, k: int = 1) -> list[str]:
    """取 k 個獨立譯本。

    ⚠️ 端點會快取相同請求：同一組 (model, messages, temperature) 重送會拿到
    完全相同的回應，即使 temperature > 0（實測 temp=1.5 重送 4 次仍為 1 種）。
    因此同語言重取樣**必須**用單一請求的 n=k 參數，不能靠重複呼叫。
    """
    r = _post("/chat/completions", {
        "model": GEN_MODEL, "temperature": temp, "max_tokens": 500, "n": k,
        "messages": [
            {"role": "system", "content": f"你是專業翻譯。把使用者的中文翻成{LANG_NAME[lang]}。"
                                          "只輸出譯文，不要解釋、不要附註、不要引號。"},
            {"role": "user", "content": text}]})
    if "__error__" in r:
        return []
    try:
        return [c["message"]["content"].strip() for c in r["choices"]
                if c["message"].get("content")]
    except (KeyError, IndexError):
        return []


def translate(text: str, lang: str, temp: float) -> str | None:
    out = translate_n(text, lang, temp, 1)
    return out[0] if out else None


def back(t: str, lang: str) -> str | None:
    # 回譯一律 temp=0，把變異來源限制在正向翻譯，避免混入額外雜訊
    c = chat(f"你是專業翻譯。把使用者的{LANG_NAME[lang]}翻成繁體中文。"
             "只輸出譯文，不要解釋、不要附註、不要引號。", t, temp=0.0)
    return c.strip() if c else None


CONDITIONS = {
    "A_cross_en_ja": ("en", "ja"),
    "B_same_en_en":  ("en", "en"),
    "C_same_ja_ja":  ("ja", "ja"),
    "D_cross_en_de": ("en", "de"),
}


def run_sentence(sent: dict, temp: float) -> dict:
    """四種條件，每種產兩個譯本 → 回譯 → 量離散度。"""
    text = sent["text"]
    out: dict = {"id": sent["id"], "group": sent["_group"], "text": text, "cond": {}}

    for name, (l1, l2) in CONDITIONS.items():
        if l1 == l2:
            # 同語言：單一請求取 n=2，否則快取會回傳兩個相同譯本（見 translate_n）
            samples = translate_n(text, l1, temp, 2)
            t1, t2 = (samples + [None, None])[:2]
        else:
            t1 = translate(text, l1, temp)
            t2 = translate(text, l2, temp)
        if not (t1 and t2):
            out["cond"][name] = {"error": "translate failed"}
            continue
        v1, v2 = back(t1, l1), back(t2, l2)
        if not (v1 and v2):
            out["cond"][name] = {"error": "backtranslate failed"}
            continue
        vecs = embed([text, v1, v2])
        if not vecs:
            out["cond"][name] = {"error": "embed failed"}
            continue
        src, e1, e2 = vecs
        out["cond"][name] = {
            "V1_pair": cosine(e1, e2),                        # 兩回譯互比
            "V2_vs_src": min(cosine(src, e1), cosine(src, e2)),  # 各自與原文比取最小
            "identical_surface": t1.strip() == t2.strip(),    # 同語言條件下譯文是否根本沒變
            "t1": t1[:120], "t2": t2[:120], "v1": v1[:120], "v2": v2[:120],
        }
    return out


def v4_rephrase(sent: dict, pair: tuple[str, str]) -> dict:
    """E：強制指出差異（生成任務），取代 S0b 的是／否自我評估。"""
    v1, v2 = pair
    c = chat("以下 A、B 兩句是同一句中文經不同路徑轉譯後譯回的結果。"
             "列出兩者在「說話者意圖」上的具體差異，每行一項，最多三項。"
             "若確實完全相同，只輸出「無差異」四個字。不要其他說明。",
             f"A：{v1}\nB：{v2}")
    # sent 為 run_sentence 的輸出，其分組鍵為 "group"（非原始句集的 "_group"）
    grp = sent.get("group") or sent.get("_group")
    if c is None:
        return {"id": sent["id"], "group": grp, "score": None}
    txt = c.strip()
    n = 0 if "無差異" in txt else sum(1 for ln in txt.splitlines() if ln.strip())
    return {"id": sent["id"], "group": grp,
            "n_diffs": n, "score": min(n / 3.0, 1.0), "raw": txt[:200]}


def lang_quality(sent: dict, lang: str) -> dict:
    """F：某語言的往返品質 —— 回譯與原文的相似度。"""
    t = translate(sent["text"], lang, 0.0)
    if not t:
        return {"id": sent["id"], "lang": lang, "sim": None}
    v = back(t, lang)
    if not v:
        return {"id": sent["id"], "lang": lang, "sim": None}
    vecs = embed([sent["text"], v])
    return {"id": sent["id"], "group": sent["_group"], "lang": lang,
            "sim": cosine(vecs[0], vecs[1]) if vecs else None,
            "trans": t[:100], "back": v[:100]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--temp", type=float, default=0.7)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    if not KEY:
        print("錯誤：未設定 ITHU_API_KEY", file=sys.stderr)
        return 1

    data = json.loads((DATA / "sentences.json").read_text(encoding="utf-8"))
    sents = ([dict(s, _group="ambiguous") for s in data["ambiguous"]]
             + [dict(s, _group="control") for s in data["control"]])
    n_amb = len(data["ambiguous"])
    n_ctl = len(data["control"])
    print(f"句子 {len(sents)}（歧義 {n_amb} / 對照 {n_ctl}），重複 {args.repeats}，temp={args.temp}")
    print("條件：" + "  ".join(f"{k}={v[0]}+{v[1]}" for k, v in CONDITIONS.items()))

    runs, v4_rows, qual_rows = [], [], []
    for rep in range(args.repeats):
        print(f"\n--- 第 {rep + 1}/{args.repeats} 次 ---", flush=True)
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            rs = list(ex.map(lambda s: run_sentence(s, args.temp), sents))
        runs.append(rs)
        print("  四條件完成", flush=True)

        # E：拿 A 條件的回譯對做改良問法
        pairs = [(r, (r["cond"]["A_cross_en_ja"].get("v1"), r["cond"]["A_cross_en_ja"].get("v2")))
                 for r in rs if "v1" in r["cond"].get("A_cross_en_ja", {})]
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            v4_rows.append(list(ex.map(lambda p: v4_rephrase(p[0], p[1]), pairs)))
        print("  V4 改良問法完成", flush=True)

        # 逐次落盤：翻譯階段最貴，中途失敗不該全丟
        (DATA / "results_s0c.json").write_text(json.dumps(
            {"runs": runs, "v4_rephrase": v4_rows, "lang_quality": [],
             "config": {"temp": args.temp, "repeats": args.repeats, "model": GEN_MODEL,
                        "partial": True}},
            ensure_ascii=False, indent=2), encoding="utf-8")

    # F：德法品質只跑一次
    for lang in ["de", "fr", "en", "ja"]:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            qual_rows += list(ex.map(lambda s: lang_quality(s, lang), sents))
    print("  語言品質檢查完成", flush=True)

    (DATA / "results_s0c.json").write_text(json.dumps(
        {"runs": runs, "v4_rephrase": v4_rows, "lang_quality": qual_rows,
         "config": {"temp": args.temp, "repeats": args.repeats, "model": GEN_MODEL}},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 條件比較 ──
    print("\n" + "=" * 98)
    print("【核心對照】跨語言 vs 同語言 —— 決定計畫書 §4.4 是否成立")
    print("=" * 98)
    print(f"{'條件':16} {'量測':11} {'AUC 平均':>9} {'各次':>18} {'95% CI':>16} {'譯文全同':>9}")
    print("-" * 98)
    summary = {}
    for cond in CONDITIONS:
        for metric in ["V1_pair", "V2_vs_src"]:
            aucs = []
            for rs in runs:
                amb = [r["cond"][cond][metric] for r in rs
                       if r["group"] == "ambiguous" and metric in r["cond"].get(cond, {})]
                ctl = [r["cond"][cond][metric] for r in rs
                       if r["group"] == "control" and metric in r["cond"].get(cond, {})]
                a = auc(ctl, amb)
                if a is not None:
                    aucs.append(a)
            if not aucs:
                continue
            m = statistics.mean(aucs)
            _, lo, hi = auc_ci(m, n_amb, n_ctl)
            ident = sum(r["cond"].get(cond, {}).get("identical_surface", False)
                        for rs in runs for r in rs)
            tot = sum(1 for rs in runs for r in rs if "identical_surface" in r["cond"].get(cond, {}))
            summary[f"{cond}|{metric}"] = {"auc_mean": m, "aucs": aucs, "ci": [lo, hi]}
            print(f"{cond:16} {metric:11} {m:9.3f} {' '.join(f'{x:.2f}' for x in aucs):>18} "
                  f"{f'[{lo:.2f}, {hi:.2f}]':>16} {f'{ident}/{tot}':>9}")
    print("=" * 98)

    best_cross = max((k for k in summary if "cross" in k), key=lambda k: summary[k]["auc_mean"], default=None)
    best_same = max((k for k in summary if "same" in k), key=lambda k: summary[k]["auc_mean"], default=None)
    if best_cross and best_same:
        c, s = summary[best_cross]["auc_mean"], summary[best_same]["auc_mean"]
        print(f"\n最佳跨語言 {best_cross} = {c:.3f}")
        print(f"最佳同語言 {best_same} = {s:.3f}")
        print(f"差距 = {c - s:+.3f}")
        print("\n>>> " + (
            "跨語言明顯勝出 → §4.4 類型學主張獲實證支持，是全篇最有價值的一張表" if c - s > 0.10 else
            "跨語言略勝，但 CI 重疊 → 尚不足以支持 §4.4，需 dev-30 加大樣本" if c - s > 0.03 else
            "🔴 兩者相當 → 類型學差異貢獻近零，多視角退化為昂貴版 self-consistency，§4.4 需重寫"))

    # ── E ──
    print("\n【V4 改良問法】強制指出差異，取代是／否自我評估")
    aucs = []
    for rows in v4_rows:
        amb = [r["score"] for r in rows if r["group"] == "ambiguous" and r["score"] is not None]
        ctl = [r["score"] for r in rows if r["group"] == "control" and r["score"] is not None]
        a = auc(amb, ctl)
        if a is not None:
            aucs.append(a)
    if aucs:
        m = statistics.mean(aucs)
        _, lo, hi = auc_ci(m, n_amb, n_ctl)
        alln = [r["n_diffs"] for rows in v4_rows for r in rows if r.get("n_diffs") is not None]
        print(f"  AUC = {m:.3f}  各次 {' '.join(f'{x:.2f}' for x in aucs)}  95% CI [{lo:.2f}, {hi:.2f}]")
        print(f"  列舉差異數分布：{statistics.mean(alln):.2f} 平均，"
              f"全零比例 {sum(1 for x in alln if x == 0) / len(alln) * 100:.0f}%")
        print(f"  對照 S0b 原問法 AUC = 0.500（退化為一律『相同』）")
        print("  >>> " + ("改良問法救回訊號 → S0b 的 0.500 是問法造成的退化輸出，非能力不足"
                          if m > 0.65 else
                          "改良問法仍無訊號 → 自我評估失效為能力問題，可寫入論文"))

    # ── F ──
    print("\n【語言往返品質】回譯與原文相似度（判斷德法是否堪用為留出語言）")
    for lang in ["en", "ja", "de", "fr"]:
        sims = [r["sim"] for r in qual_rows if r["lang"] == lang and r["sim"] is not None]
        if sims:
            print(f"  {lang}: 平均 {statistics.mean(sims):.4f}  最低 {min(sims):.4f}  n={len(sims)}")
    print("  >>> 德法若與英日同級即堪用；明顯偏低則該語言的譯文品質會混淆量測")

    print(f"\n⚠️ n={n_amb} vs {n_ctl}，CI 極寬；spike 句子為自選，0.84 類數字是樂觀上界。")
    print(f"完整結果：{DATA / 'results_s0c.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
