"""S0b — T3 訊號追查（技術設計文件 §8.3）。

S0 發現多視角回譯一致性訊號 separable=False，威脅演算法 1 的地基。
本腳本先確認那是「訊號不存在」還是「尺規太鈍」，再談改設計。

設計原則：**翻譯固定，只換量測工具**——同一批回譯結果套四種量測，
變因就只剩尺規本身。另加一個關鍵對照組：

  V1  雙編碼器 cos(V_en, V_ja)          ← S0 用的，基準線
  V2  雙編碼器 min(cos(src,V_en), cos(src,V_ja))   ← 跟原文比而非互比
  V3  交叉編碼器 rerank(V_en, V_ja)     ← cross-encoder，對細粒度語意較敏銳
  V4  LLM 判「兩句回譯的說話者意圖是否相同」  ← 直接打語用層
  S5  LLM 直接問「這句歧不歧義」         ← §4.1 的便宜訊號，RQ2 的存亡對照

若 S5 的判別力 >= V1..V4，RQ2 失去立論基礎：既然直接問更準，
為什麼要走多視角慢速通道。這是全篇最關鍵的數字。

判別力用 AUC（Mann-Whitney U）：1.0 完全分離，0.5 等於亂猜。
n=10 vs 5 檢定力極低，dev-30 完成後必須重跑。

用法：
    python scripts/spike_s0b.py --repeats 3
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

GEN_MODEL = "mistral-small-4"       # 翻譯／回譯，固定不變
JUDGE_MODELS = ["mistral-small-4", "gpt-oss-120b"]
EMBED_MODEL = "bge-m3-embedding"
RERANK_MODEL = "bge-m3-reranker"

LANG_NAME = {"en": "英文", "ja": "日文", "de": "德文", "fr": "法文"}


def _post(path: str, payload: dict, retries: int = 3) -> dict:
    body = json.dumps(payload).encode()
    for attempt in range(retries):
        req = urllib.request.Request(
            BASE + path, data=body,
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


def chat(model: str, system: str, user: str, max_tokens: int = 500) -> str | None:
    r = _post("/chat/completions", {
        "model": model, "temperature": 0, "max_tokens": max_tokens,
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


def rerank(query: str, doc: str) -> float | None:
    r = _post("/rerank", {"model": RERANK_MODEL, "query": query, "documents": [doc]})
    if "__error__" in r:
        return None
    try:
        return float(r["results"][0]["relevance_score"])
    except (KeyError, IndexError, ValueError):
        return None


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def parse_score(text: str | None) -> float | None:
    if not text:
        return None
    buf = ""
    for ch in text.strip():
        if ch.isdigit() or ch == ".":
            buf += ch
        elif buf:
            break
    try:
        v = float(buf)
    except ValueError:
        return None
    return min(max(v, 0.0), 1.0)


def auc(pos: list[float], neg: list[float]) -> float | None:
    """P(隨機 pos 分數 > 隨機 neg 分數)，同分算 0.5。1.0=完全分離，0.5=無訊號。"""
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


# ─────────────────────────── 主流程 ───────────────────────────

def pipeline(sent: dict) -> dict:
    """翻譯 → 回譯 → 四種量測。翻譯只做一次，四種尺規套同一批結果。"""
    text = sent["text"]
    out: dict = {"id": sent["id"], "group": sent["_group"], "text": text}

    def tr(lang: str) -> str | None:
        c = chat(GEN_MODEL, f"你是專業翻譯。把使用者的中文翻成{LANG_NAME[lang]}。"
                            "只輸出譯文，不要解釋、不要附註、不要引號。", text)
        return c.strip() if c else None

    def back(t: str, lang: str) -> str | None:
        c = chat(GEN_MODEL, f"你是專業翻譯。把使用者的{LANG_NAME[lang]}翻成繁體中文。"
                            "只輸出譯文，不要解釋、不要附註、不要引號。", t)
        return c.strip() if c else None

    t_en, t_ja = tr("en"), tr("ja")
    if not (t_en and t_ja):
        return {**out, "error": "translate failed"}
    v_en, v_ja = back(t_en, "en"), back(t_ja, "ja")
    if not (v_en and v_ja):
        return {**out, "error": "backtranslate failed"}
    out |= {"trans_en": t_en, "trans_ja": t_ja, "back_en": v_en, "back_ja": v_ja}

    vecs = embed([text, v_en, v_ja])
    if vecs:
        src, e, j = vecs
        out["V1_biencoder_pair"] = cosine(e, j)
        out["V2_biencoder_vs_src"] = min(cosine(src, e), cosine(src, j))

    s = rerank(v_en, v_ja)
    if s is not None:
        out["V3_crossencoder"] = s

    j4 = chat(GEN_MODEL,
              "以下兩句都是同一句中文經由不同語言轉譯後再譯回中文的結果。"
              "判斷它們所表達的「說話者意圖」是否相同。"
              "只輸出一個 0 到 1 的數字，1 表示意圖完全相同，0 表示意圖完全不同。不要解釋。",
              f"A：{v_en}\nB：{v_ja}")
    v = parse_score(j4)
    if v is not None:
        out["V4_llm_intent_same"] = v
    return out


def s5_direct(sent: dict, model: str) -> dict:
    c = chat(model,
             "判斷使用者提供的中文句子是否存在語意歧義（同一句話可能有多種互不相容的解讀）。"
             "只輸出一個 0 到 1 的數字，1 表示高度歧義，0 表示完全無歧義。不要解釋。",
             sent["text"])
    return {"id": sent["id"], "group": sent["_group"], "model": model, "score": parse_score(c)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    if not KEY:
        print("錯誤：未設定 ITHU_API_KEY", file=sys.stderr)
        return 1

    data = json.loads((DATA / "sentences.json").read_text(encoding="utf-8"))
    sents = ([dict(s, _group="ambiguous") for s in data["ambiguous"]]
             + [dict(s, _group="control") for s in data["control"]])

    print(f"句子 {len(sents)}（歧義 {len(data['ambiguous'])} / 對照 {len(data['control'])}）"
          f"，重複 {args.repeats} 次，生成模型 {GEN_MODEL}")

    runs, s5_runs = [], []
    for rep in range(args.repeats):
        print(f"\n--- 第 {rep + 1}/{args.repeats} 次 ---", flush=True)
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            rs = list(ex.map(pipeline, sents))
        runs.append(rs)
        print(f"  多視角管線完成（失敗 {sum('error' in r for r in rs)}）", flush=True)

        for m in JUDGE_MODELS:
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                s5_runs.append({"model": m, "repeat": rep,
                                "rows": list(ex.map(lambda s: s5_direct(s, m), sents))})
        print("  S5 直接詢問完成", flush=True)

    # ── AUC 計算 ──
    # 一致性訊號：對照組應較高 → AUC = P(control > ambiguous)
    # S5 歧義分數：歧義組應較高 → AUC = P(ambiguous > control)
    variants = ["V1_biencoder_pair", "V2_biencoder_vs_src", "V3_crossencoder", "V4_llm_intent_same"]
    table: dict[str, list[float]] = {}
    detail: dict[str, dict] = {}

    for v in variants:
        aucs = []
        for rs in runs:
            amb = [r[v] for r in rs if r.get("group") == "ambiguous" and v in r]
            ctl = [r[v] for r in rs if r.get("group") == "control" and v in r]
            a = auc(ctl, amb)
            if a is not None:
                aucs.append(a)
                detail.setdefault(v, {"amb": [], "ctl": []})
                detail[v]["amb"] += amb
                detail[v]["ctl"] += ctl
        if aucs:
            table[v] = aucs

    for m in JUDGE_MODELS:
        aucs = []
        for run in [r for r in s5_runs if r["model"] == m]:
            amb = [x["score"] for x in run["rows"] if x["group"] == "ambiguous" and x["score"] is not None]
            ctl = [x["score"] for x in run["rows"] if x["group"] == "control" and x["score"] is not None]
            a = auc(amb, ctl)
            if a is not None:
                aucs.append(a)
                key = f"S5_direct_{m}"
                detail.setdefault(key, {"amb": [], "ctl": []})
                detail[key]["amb"] += amb
                detail[key]["ctl"] += ctl
        if aucs:
            table[f"S5_direct_{m}"] = aucs

    (DATA / "results_s0b.json").write_text(json.dumps(
        {"runs": runs, "s5": s5_runs, "auc": table}, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 88)
    print(f"{'量測方式':30} {'AUC 平均':>9} {'標準差':>8} {'各次':>22}  判讀")
    print("-" * 88)
    for k, v in sorted(table.items(), key=lambda kv: -statistics.mean(kv[1])):
        mean = statistics.mean(v)
        sd = statistics.stdev(v) if len(v) > 1 else 0.0
        each = " ".join(f"{x:.2f}" for x in v)
        verdict = "完全分離" if mean >= 0.99 else "強" if mean >= 0.9 else "中" if mean >= 0.75 else "弱" if mean >= 0.6 else "近乎無訊號"
        print(f"{k:30} {mean:9.3f} {sd:8.3f} {each:>22}  {verdict}")
    print("=" * 88)

    print("\n分組平均（合併各次執行）：")
    for k, d in detail.items():
        if d["amb"] and d["ctl"]:
            print(f"  {k:30} 歧義 {statistics.mean(d['amb']):.4f}  對照 {statistics.mean(d['ctl']):.4f}")

    best_mv = max((k for k in table if k.startswith("V")), key=lambda k: statistics.mean(table[k]), default=None)
    best_s5 = max((k for k in table if k.startswith("S5")), key=lambda k: statistics.mean(table[k]), default=None)
    if best_mv and best_s5:
        mv, s5 = statistics.mean(table[best_mv]), statistics.mean(table[best_s5])
        print(f"\n最佳多視角量測 {best_mv} = {mv:.3f}")
        print(f"最佳直接詢問   {best_s5} = {s5:.3f}")
        print("\n>>> " + ("多視角勝出，RQ2 的慢速通道有立論基礎" if mv > s5 + 0.05
                          else "直接詢問勝出或持平 —— RQ2 立論動搖，需重新檢視" if s5 >= mv
                          else "兩者接近，n 太小無法判定，需 dev-30 重跑"))
    print(f"\n⚠️ n=10 vs 5，檢定力極低；dev-30 完成後必須重跑。完整結果：{DATA / 'results_s0b.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
