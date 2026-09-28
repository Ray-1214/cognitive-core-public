"""S0 能力 spike — 技術設計文件 §8.1。

在蓋 provider 抽象層之前，先確認校內各模型撐不撐得住反思任務。測三件事：

  T1 Schema 通過率      走到降級階梯第幾級、各級成功率（對應 G6）
  T2 UNKNOWN 亂猜率     該留白的欄位，模型是填 UNKNOWN 還是編一個值
  T3 回譯相似度判別力    高歧義句 vs 低歧義對照句的一致性分數能否分開

腳本本身是丟棄式的；產出的 results.json 併入 M8 跨模型對比。

用法：
    python scripts/spike_s0.py                       # 跑全部模型
    python scripts/spike_s0.py --models mistral-small-4 gpt-oss-120b
    python scripts/spike_s0.py --repeats 3 --workers 8
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
EMBED_MODEL = "bge-m3-embedding"

# §5.0 實測能力矩陣
MODELS = {
    "mistral-small-4":    {"json_schema": False, "temperature": True,  "max_tokens": 600},
    "gpt-oss-120b":       {"json_schema": True,  "temperature": True,  "max_tokens": 600},
    "llama4scout":        {"json_schema": True,  "temperature": True,  "max_tokens": 600},
    "nemotron-3-ultra":   {"json_schema": False, "temperature": True,  "max_tokens": 4000, "reasoning": True},
    "ornith-35b":         {"json_schema": False, "temperature": True,  "max_tokens": 4000, "reasoning": True},
    "diffusiongemma-26b": {"json_schema": False, "temperature": False, "max_tokens": 600},
}

ANCHOR_SCHEMA = {
    "type": "object",
    "properties": {
        "agent": {"type": "string"},
        "tense": {"type": "string", "enum": ["PAST", "PRESENT", "FUTURE", "UNKNOWN"]},
        "register": {"type": "string", "enum": ["FORMAL", "SEMI_FORMAL", "CASUAL", "UNKNOWN"]},
        "social_relation": {"type": "string", "enum": ["SUPERIOR", "PEER", "SUBORDINATE", "UNKNOWN"]},
        "speaker_intent": {"type": "string"},
        "unknown_fields": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["agent", "tense", "register", "social_relation", "speaker_intent", "unknown_fields"],
    "additionalProperties": False,
}

ANCHOR_SYSTEM = """你是語言學分析助手。分析使用者提供的中文句子，輸出語意錨點 JSON。

最重要的規則：
- 若某欄位無法從句子本身確定，必須填 "UNKNOWN"，並把欄位名列入 unknown_fields。
- 不得憑常識、機率或最可能的情況猜測。留白比猜錯更有價值。
- speaker_intent 若無法判定，填 "UNKNOWN"。

只輸出 JSON，不要 markdown 圍欄，不要任何解釋文字。格式：
{"agent": string, "tense": "PAST"|"PRESENT"|"FUTURE"|"UNKNOWN",
 "register": "FORMAL"|"SEMI_FORMAL"|"CASUAL"|"UNKNOWN",
 "social_relation": "SUPERIOR"|"PEER"|"SUBORDINATE"|"UNKNOWN",
 "speaker_intent": string, "unknown_fields": [string]}"""

LANG_NAME = {"en": "英文", "ja": "日文"}


# ─────────────────────────── HTTP ───────────────────────────

def _post(path: str, payload: dict, retries: int = 3) -> dict:
    body = json.dumps(payload).encode()
    for attempt in range(retries):
        req = urllib.request.Request(
            BASE + path, data=body,
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:200]
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            return {"__error__": f"HTTP {e.code}", "__body__": detail}
        except Exception as e:  # noqa: BLE001
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error__": type(e).__name__, "__body__": str(e)[:200]}
    return {"__error__": "exhausted"}


def chat(model: str, system: str, user: str, *, response_format: dict | None = None) -> tuple[str | None, dict]:
    """回傳 (content, meta)。meta 含 tokens / finish_reason / error。"""
    cap = MODELS[model]
    payload: dict = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": cap["max_tokens"],
    }
    if cap["temperature"]:
        payload["temperature"] = 0
    if response_format:
        payload["response_format"] = response_format

    r = _post("/chat/completions", payload)
    if "__error__" in r:
        return None, {"error": f"{r['__error__']}: {r.get('__body__', '')}"}
    try:
        ch = r["choices"][0]
        return ch["message"].get("content"), {
            "finish_reason": ch["finish_reason"],
            "completion_tokens": r.get("usage", {}).get("completion_tokens"),
        }
    except (KeyError, IndexError) as e:
        return None, {"error": f"malformed response: {e}"}


def embed(texts: list[str]) -> list[list[float]] | None:
    r = _post("/embeddings", {"model": EMBED_MODEL, "input": texts})
    if "__error__" in r:
        return None
    return [d["embedding"] for d in r["data"]]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# ──────────────────── 降級階梯（§5.2）────────────────────

def parse_json_loose(text: str) -> dict | None:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1].rsplit("```", 1)[0]
    t = t.strip()
    try:
        v = json.loads(t)
        return v if isinstance(v, dict) else None
    except json.JSONDecodeError:
        pass
    # 退一步：抓第一個 {...} 區塊
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j > i:
        try:
            v = json.loads(t[i:j + 1])
            return v if isinstance(v, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def valid_anchor(obj: dict) -> bool:
    return all(k in obj for k in ANCHOR_SCHEMA["required"])


def get_anchor(model: str, text: str) -> dict:
    """依降級階梯取得錨點。回傳 {tier, ok, anchor, raw, meta}。"""
    cap = MODELS[model]
    attempts: list[dict] = []

    tiers: list[tuple[int, dict | None]] = []
    if cap["json_schema"]:
        tiers.append((1, {"type": "json_schema",
                          "json_schema": {"name": "anchor", "strict": True, "schema": ANCHOR_SCHEMA}}))
    tiers.append((2, {"type": "json_object"}))
    tiers.append((3, None))

    for tier, rf in tiers:
        content, meta = chat(model, ANCHOR_SYSTEM, f"分析這句話：{text}", response_format=rf)
        attempts.append({"tier": tier, "meta": meta, "raw": (content or "")[:300]})
        if content is None:
            continue
        obj = parse_json_loose(content)
        if obj and valid_anchor(obj):
            return {"tier": tier, "ok": True, "anchor": obj, "attempts": attempts}
    return {"tier": None, "ok": False, "anchor": None, "attempts": attempts}


# ──────────────────── T3 翻譯 / 回譯 ────────────────────

def translate(model: str, text: str, lang: str) -> str | None:
    sys_p = f"你是專業翻譯。把使用者的中文翻成{LANG_NAME[lang]}。只輸出譯文，不要解釋、不要附註、不要引號。"
    c, _ = chat(model, sys_p, text)
    return c.strip() if c else None


def back_translate(model: str, text: str, lang: str) -> str | None:
    sys_p = f"你是專業翻譯。把使用者的{LANG_NAME[lang]}翻成繁體中文。只輸出譯文，不要解釋、不要附註、不要引號。"
    c, _ = chat(model, sys_p, text)
    return c.strip() if c else None


# ─────────────────────────── 主流程 ───────────────────────────

def run_model(model: str, sentences: list[dict], repeats: int, workers: int) -> dict:
    print(f"\n=== {model} ===", flush=True)
    out: dict = {"model": model, "t1_t2": [], "t3": []}

    # --- T1 / T2：錨點抽取，每句重複 repeats 次 ---
    jobs = [(s, r) for s in sentences for r in range(repeats)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(lambda j: (j[0], j[1], get_anchor(model, j[0]["text"])), jobs))

    SCALAR_FIELDS = ["agent", "tense", "register", "social_relation", "speaker_intent"]

    for sent, rep, res in results:
        rec = {
            "id": sent["id"], "repeat": rep, "group": sent["_group"],
            "tier": res["tier"], "schema_ok": res["ok"],
        }
        if res["ok"]:
            anchor = res["anchor"]
            listed = {str(x) for x in anchor.get("unknown_fields", [])}

            def is_unknown(f: str) -> bool:
                return str(anchor.get(f, "")).strip().upper() == "UNKNOWN" or f in listed

            # 全欄位的 UNKNOWN 標記狀態 —— precision 分母
            rec["unknown_marks"] = [f for f in SCALAR_FIELDS if is_unknown(f)]
            rec["anchor"] = {f: str(anchor.get(f, ""))[:80] for f in SCALAR_FIELDS}

            if sent["_group"] == "ambiguous":
                field = sent["undeterminable_field"]
                rec["undeterminable_field"] = field
                rec["marked_unknown"] = is_unknown(field)      # ← recall
                rec["actual_value"] = str(anchor.get(field, ""))[:80]
            else:
                # 對照句所有欄位皆可由原文判定 → 任何 UNKNOWN 標記都是偽陽性
                rec["false_unknowns"] = rec["unknown_marks"]
        out["t1_t2"].append(rec)
        if not res["ok"]:
            out.setdefault("failures", []).append({"id": sent["id"], "attempts": res["attempts"]})
    print(f"  T1/T2 完成：{len(out['t1_t2'])} 筆", flush=True)

    # --- T3：翻譯 → 回譯 → 一致性 ---
    def one(sent: dict) -> dict | None:
        t_en = translate(model, sent["text"], "en")
        t_ja = translate(model, sent["text"], "ja")
        if not t_en or not t_ja:
            return {"id": sent["id"], "group": sent["_group"], "error": "translate failed"}
        v_en = back_translate(model, t_en, "en")
        v_ja = back_translate(model, t_ja, "ja")
        if not v_en or not v_ja:
            return {"id": sent["id"], "group": sent["_group"], "error": "backtranslate failed"}
        vecs = embed([sent["text"], v_en, v_ja])
        if not vecs:
            return {"id": sent["id"], "group": sent["_group"], "error": "embed failed"}
        src, e, j = vecs
        return {
            "id": sent["id"], "group": sent["_group"],
            "consistency": cosine(e, j),          # 演算法 1 的 Score
            "sim_src_en": cosine(src, e),
            "sim_src_ja": cosine(src, j),
            "trans_en": t_en[:150], "trans_ja": t_ja[:150],
            "back_en": v_en[:150], "back_ja": v_ja[:150],
        }

    with ThreadPoolExecutor(max_workers=workers) as ex:
        out["t3"] = [r for r in ex.map(one, sentences) if r]
    print(f"  T3 完成：{len(out['t3'])} 筆", flush=True)
    return out


def summarize(res: dict) -> dict:
    rows = res["t1_t2"]
    n = len(rows)
    ok = [r for r in rows if r["schema_ok"]]
    tier_counts: dict[str, int] = {}
    for r in ok:
        tier_counts[f"tier{r['tier']}"] = tier_counts.get(f"tier{r['tier']}", 0) + 1

    judged = [r for r in rows if "marked_unknown" in r]
    t3_amb = [r["consistency"] for r in res["t3"] if r.get("group") == "ambiguous" and "consistency" in r]
    t3_ctl = [r["consistency"] for r in res["t3"] if r.get("group") == "control" and "consistency" in r]

    # precision：對照句所有欄位皆可判定，故任何 UNKNOWN 標記皆為偽陽性
    ctl_ok = [r for r in rows if r["group"] == "control" and "false_unknowns" in r]
    n_fields = 5
    fp = sum(len(r["false_unknowns"]) for r in ctl_ok)
    tp = sum(r["marked_unknown"] for r in judged)

    s = {
        "model": res["model"],
        "T1_schema_pass_rate": round(len(ok) / n, 4) if n else None,
        "T1_tier_distribution": tier_counts,
        "T2_unknown_recall": round(tp / len(judged), 4) if judged else None,
        "T2_n_judged": len(judged),
        "T2_ctl_false_unknown_rate": round(fp / (len(ctl_ok) * n_fields), 4) if ctl_ok else None,
        "T2_ctl_n_fields": len(ctl_ok) * n_fields,
        "T2_precision_proxy": round(tp / (tp + fp), 4) if (tp + fp) else None,
        "T3_ambiguous_mean": round(statistics.mean(t3_amb), 4) if t3_amb else None,
        "T3_control_mean": round(statistics.mean(t3_ctl), 4) if t3_ctl else None,
    }
    if t3_amb and t3_ctl:
        s["T3_gap"] = round(s["T3_control_mean"] - s["T3_ambiguous_mean"], 4)
        s["T3_ambiguous_max"] = round(max(t3_amb), 4)
        s["T3_control_min"] = round(min(t3_ctl), 4)
        # 兩組是否可分：對照組最低分 > 歧義組最高分 才算完全分離
        s["T3_separable"] = s["T3_control_min"] > s["T3_ambiguous_max"]
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=list(MODELS))
    ap.add_argument("--repeats", type=int, default=3, help="T1/T2 每句重複次數")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    if not KEY:
        print("錯誤：未設定 ITHU_API_KEY（請放入 .env 或環境變數）", file=sys.stderr)
        return 1

    data = json.loads((DATA / "sentences.json").read_text(encoding="utf-8"))
    sentences = ([dict(s, _group="ambiguous") for s in data["ambiguous"]]
                 + [dict(s, _group="control") for s in data["control"]])
    print(f"句子：{len(sentences)} 句（歧義 {len(data['ambiguous'])} / 對照 {len(data['control'])}）")
    print(f"模型：{', '.join(args.models)}")

    # 沿用既有結果，依模型名合併——分批跑不同模型時不會覆寫先前的數據
    out_path = DATA / "results.json"
    by_model: dict[str, dict] = {}
    if out_path.exists():
        prev = json.loads(out_path.read_text(encoding="utf-8"))
        by_model = {r["model"]: r for r in prev.get("raw", [])}
        print(f"沿用既有結果：{', '.join(by_model) or '（無）'}")

    for m in args.models:
        if m not in MODELS:
            print(f"跳過未知模型 {m}", file=sys.stderr)
            continue
        try:
            by_model[m] = run_model(m, sentences, args.repeats, args.workers)
        except Exception as e:  # noqa: BLE001
            print(f"  {m} 失敗：{e}", file=sys.stderr)
            continue
        # 逐模型落盤，中途掛掉不會全丟
        all_results = [by_model[k] for k in by_model]
        out_path.write_text(
            json.dumps({"summaries": [summarize(r) for r in all_results], "raw": all_results},
                       ensure_ascii=False, indent=2),
            encoding="utf-8")

    all_results = [by_model[k] for k in by_model]
    summaries = [summarize(r) for r in all_results]

    print("\n" + "=" * 104)
    print(f"{'模型':22} {'T1通過':>8} {'T2recall':>9} {'對照誤標':>9} {'T2precis':>9} "
          f"{'T3歧義':>8} {'T3對照':>8} {'落差':>7}")
    print("-" * 104)
    for s in summaries:
        def f(v, pct=False):
            if v is None:
                return "  n/a"
            return f"{v * 100:7.1f}%" if pct else f"{v:7.4f}"
        print(f"{s['model']:22} {f(s['T1_schema_pass_rate'], True):>8} {f(s['T2_unknown_recall'], True):>9} "
              f"{f(s.get('T2_ctl_false_unknown_rate'), True):>9} {f(s.get('T2_precision_proxy'), True):>9} "
              f"{f(s['T3_ambiguous_mean']):>8} {f(s['T3_control_mean']):>8} {f(s.get('T3_gap')):>7}")
    print("=" * 104)
    print(f"\n完整結果：{DATA / 'results.json'}")
    print("\n判讀：")
    print("  T1 通過   → G6 目標 ≥99%；tier 分布看降級階梯實際走到第幾級")
    print("  T2 recall → 該欄位確實無從判定，填 UNKNOWN 才對；低代表模型會亂猜")
    print("  對照誤標  → 對照句全欄位皆可判定，標 UNKNOWN 即偽陽性；高代表濫用 UNKNOWN")
    print("  T2 precis → tp/(tp+fp)，同時看誠實與節制；只看 recall 會被『全標 UNKNOWN』騙過")
    print("  T3 落差   → 判別力請看 spike_s0b 的 AUC，落差大不等於可分離")
    return 0


if __name__ == "__main__":
    sys.exit(main())
