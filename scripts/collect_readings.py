"""§3 步驟 1：收集全模型在 dev-30 上提出的讀法聯集（準則完備性檢查）。

**目的是檢查準則涵蓋是否不足，不是逐句補模型講對的東西。**

規則（技術設計文件 §7.6）：
  - 某句的標註在任何模型看過它之前為草稿；本步驟之後只能改**準則**，
    改準則就從準則重標全部 30 句，不可逐句挑模型答對的補進去
  - 準則凍結 → 標註凍結 → 取 hash 進 run 記錄
  - 之後任何改動 = 全部重跑 + 記錄理由

輸出 data/dev30/readings_union.json 與一份給人看的 markdown 報告，
報告以**跨句型樣**為主（哪一類讀法被系統性遺漏），而非逐句清單。

用法：
    python scripts/collect_readings.py
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import yaml

from _throttle import GEMINI, GEMINI_BREAKER, ITHU, ITHU_BREAKER, CircuitOpen

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEV = ROOT / "data" / "dev30"
ITHU_BASE = os.environ.get("ITHU_API_BASE", "<your-llm-endpoint>").rstrip("/") + "/v1"
ITHU_KEY = os.environ.get("ITHU_API_KEY")
G_KEY = os.environ.get("GOOGLE_API_KEY")

ITHU_MODELS = ["mistral-small-4", "gpt-oss-120b", "llama4scout",
               "nemotron-3-ultra", "ornith-35b", "diffusiongemma-26b"]
GEMINI_MODEL = "gemini-flash-latest"
GEMINI_DELAY = 6.0        # 免費層 RPM 低，序列執行時的間隔秒數

SYSTEM = """你是語言學分析助手。使用者會給一個中文句子。

列出這個句子在**沒有任何上下文**的情況下，所有合理的解讀。
每個解讀一行，格式為：
解讀內容 | 在什麼情境下成立

規則：
- 只列原文本身允許的解讀，不要加入原文不支持的臆測
- 有幾個列幾個，不要湊數也不要保留
- 不要編號、不要標題、不要任何解釋文字"""


def _ithu(model: str, text: str) -> tuple[str | None, str | None]:
    payload = {"model": model, "max_tokens": 1200,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": text}]}
    if model != "diffusiongemma-26b":       # 該模型不接受取樣參數（§5.0）
        payload["temperature"] = 0
    body = json.dumps(payload).encode()
    last = "未知"
    for attempt in range(3):
        try:
            ITHU_BREAKER.check()
        except CircuitOpen as e:
            return None, f"熔斷：{e}"
        ITHU.acquire()
        req = urllib.request.Request(ITHU_BASE + "/chat/completions", data=body,
            headers={"Authorization": f"Bearer {ITHU_KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.loads(r.read())
                ITHU_BREAKER.record(ok=True)
                return d["choices"][0]["message"].get("content"), None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:120]}"
            ITHU_BREAKER.record(ok=False)
            if e.code == 429 and attempt < 2:
                time.sleep(2 ** attempt * 2)
                continue
            return None, last
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:120]}"
            ITHU_BREAKER.record(ok=False)
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return None, last
    return None, last


def _gemini(text: str) -> tuple[str | None, str | None]:
    """免費層 RPM 很低，需較長的退避重試（初版無重試，30 句只成功 9 句）。"""
    body = {"contents": [{"parts": [{"text": SYSTEM + "\n\n句子：" + text}]}],
            "generationConfig": {"temperature": 0}}
    data = json.dumps(body).encode()
    last = "未知"
    for attempt in range(5):
        try:
            GEMINI_BREAKER.check()
        except CircuitOpen as e:
            return None, f"熔斷：{e}"
        GEMINI.acquire()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            data=data, headers={"Content-Type": "application/json", "X-goog-api-key": G_KEY})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
                GEMINI_BREAKER.record(ok=True)
                return d["candidates"][0]["content"]["parts"][0]["text"], None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:120]}"
            GEMINI_BREAKER.record(ok=False)
            if e.code in (429, 503) and attempt < 4:
                time.sleep(5 * (attempt + 1))
                continue
            return None, last
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:120]}"
            GEMINI_BREAKER.record(ok=False)
            if attempt < 4:
                time.sleep(5 * (attempt + 1))
                continue
            return None, last
    return None, last


def parse_readings(raw: str | None) -> list[dict]:
    if not raw:
        return []
    out = []
    for ln in raw.strip().splitlines():
        s = re.sub(r"^[\s\-*•]*\d*[.、)]?\s*", "", ln).strip()
        if not s or s.startswith("#"):
            continue
        if "|" in s:
            a, b = s.split("|", 1)
            out.append({"reading": a.strip(), "when": b.strip()})
        elif len(s) > 4:
            out.append({"reading": s, "when": ""})
    return out[:8]


def main() -> int:
    if not ITHU_KEY or not G_KEY:
        print("錯誤：需要 ITHU_API_KEY 與 GOOGLE_API_KEY", file=sys.stderr)
        return 1
    data = yaml.safe_load((DEV / "sentences.yaml").read_text(encoding="utf-8"))
    items = data["items"]
    print(f"dev-30：{len(items)} 句 × {len(ITHU_MODELS) + 1} 模型")

    # 兩段式：校內模型並行；Gemini 序列且限速。
    # 混在同一個 thread pool 會讓 Gemini 的退避 sleep 佔住 worker，拖垮整批。
    results = []

    ithu_jobs = [(it, m) for it in items for m in ITHU_MODELS]
    with ThreadPoolExecutor(max_workers=8) as ex:
        def _one(j):
            raw, err = _ithu(j[1], j[0]["text"])
            return {"id": j[0]["id"], "model": j[1], "raw": raw,
                    "error": err, "readings": parse_readings(raw)}
        results += list(ex.map(_one, ithu_jobs))
    ok = sum(1 for r in results if r["readings"])
    print(f"校內模型：{ok}/{len(ithu_jobs)} 次取得讀法", flush=True)

    print(f"Gemini：序列執行 {len(items)} 句（免費層 RPM 低，每次間隔 {GEMINI_DELAY}s）", flush=True)
    for n, it in enumerate(items, 1):
        raw, err = _gemini(it["text"])
        results.append({"id": it["id"], "model": GEMINI_MODEL, "raw": raw,
                        "error": err, "readings": parse_readings(raw)})
        if n % 10 == 0:
            print(f"  {n}/{len(items)}", flush=True)

    # 失敗清單必須留痕，不能靜默消失
    failures = [{"id": r["id"], "model": r["model"],
                 "reason": r.get("error") or ("呼叫失敗" if r["raw"] is None
                                              else "有回應但解析不出讀法")}
                for r in results if not r["readings"]]
    print(f"總計 {sum(1 for r in results if r['readings'])}/{len(results)} 次取得讀法"
          f"，失敗 {len(failures)}")

    by_id: dict[str, list] = {}
    for r in results:
        by_id.setdefault(r["id"], []).append(r)

    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "models": ITHU_MODELS + [GEMINI_MODEL],
           "failures": failures, "per_sentence": {}}
    lines = ["# dev-30 讀法聯集 — 準則完備性檢查",
             "",
             "> **用途限定**：只用來判斷「準則是否涵蓋不足」。",
             "> **不得**逐句把模型講對的讀法補進標註——那會讓 spurious_readings 失去意義、",
             "> precision@k 不可計算，並使「AI 初稿 + 研究者複核」的揭露變成半真。",
             "> 要改就改準則，然後從準則重標全部 30 句。",
             "", "---", ""]

    for it in items:
        rs = by_id.get(it["id"], [])
        drafted = [r["reading"] for r in it["licensed_readings"]]
        spurious = it["spurious_readings"]
        proposed = []
        for r in rs:
            for x in r["readings"]:
                proposed.append({"model": r["model"], **x})
        out["per_sentence"][it["id"]] = {
            "text": it["text"], "type": it["ambiguity_type"],
            "drafted_licensed": drafted, "drafted_spurious": spurious,
            "model_proposed": proposed,
            "n_proposed_per_model": {r["model"]: len(r["readings"]) for r in rs},
        }
        lines += [f"## {it['id']}　`{it['text']}`　({it['ambiguity_type']})", "",
                  f"**草稿 licensed（{len(drafted)}）**：" + "；".join(drafted), "",
                  f"**草稿 spurious（{len(spurious)}）**：" + "；".join(spurious), "",
                  f"**模型提出（各家數量：**" +
                  "，".join(f"{m.split('-')[0]}={n}" for m, n in
                            out["per_sentence"][it["id"]]["n_proposed_per_model"].items()) + "**）**", ""]
        seen = set()
        for p in proposed:
            k = p["reading"][:24]
            if k in seen:
                continue
            seen.add(k)
            lines.append(f"- {p['reading']}" + (f"　*（{p['when']}）*" if p["when"] else "")
                         + f"　<sub>{p['model']}</sub>")
        lines += ["", "---", ""]

    # 跨句型樣：列舉數量分布（§8.4 的 overthinking 可直接量化）
    lines += ["## 跨句型樣（準則層級判讀用）", "",
              "### 各模型平均列舉讀法數", ""]
    for m in ITHU_MODELS + [GEMINI_MODEL]:
        ns = [len(r["readings"]) for r in results if r["model"] == m]
        ok = [n for n in ns if n]
        lines.append(f"- `{m}`：平均 {sum(ok)/len(ok):.2f} 項"
                     f"（n={len(ok)}，失敗 {len(ns)-len(ok)}）" if ok else f"- `{m}`：全數失敗")
    lines += ["", "### 草稿讀法數 vs 模型列舉數", "",
              "| 類型 | 草稿平均 | 模型平均 | 差 |", "| --- | :-: | :-: | :-: |"]
    for t in ["LEXICAL", "REFERENTIAL", "PRAGMATIC"]:
        its = [i for i in items if i["ambiguity_type"] == t]
        dn = sum(len(i["licensed_readings"]) for i in its) / len(its)
        mn = [len(r["readings"]) for r in results
              if r["id"] in {i["id"] for i in its} and r["readings"]]
        mm = sum(mn) / len(mn) if mn else 0
        lines.append(f"| {t} | {dn:.2f} | {mm:.2f} | {mm-dn:+.2f} |")
    lines += ["", "> 模型平均顯著高於草稿 → 可能為 §8.4 的過度生成，",
              "> 也可能為草稿涵蓋不足。**這正是要人判斷的準則層級問題。**", ""]

    (DEV / "readings_union.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (DEV / "readings_union.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"已輸出 {DEV / 'readings_union.md'}")
    print(f"        {DEV / 'readings_union.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
