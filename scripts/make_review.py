"""把 dev-30 的 YAML 攤平成人類可讀的審查表。

⚠️ **本腳本只做機械轉換，不做任何內容判斷。**
任何「這句應該改成…」的建議都會讓研究者的複核失去獨立性（地雷 3）。
輸出的每個欄位都直接取自 sentences.yaml，不推論、不補充、不排序評價。

用法：
    python scripts/make_review.py
    python scripts/make_review.py --out data/dev30/REVIEW.md
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEV = ROOT / "data" / "dev30"

# 已知的標註獨立性缺口。事實記錄，來自 _quarantine/README.md，非內容判斷。
CONTAMINATED = {
    "dev-lex-01": "助理曾看過 mistral-small-4 對本句提議的讀法（草稿早於此，之後未改動本句）",
    "dev-prg-05": "助理曾看過 Gemini 對本句提議的意圖，且已轉述給研究者。雙方皆已看過",
}

CRITERIA = """## 判準清單

橫掃時對照用：

1. 歧義句真的能講出兩個互不相容的解讀嗎
2. 消歧句真的沒有第二讀了嗎
3. 兩句都像人話嗎（消歧句是否寫成教科書例句）
4. 最小對立對真的最小嗎（字數差 ≤2、沒順便改語域或稱謂）
5. 每個 `licensed_reading` 都真的被原文允許嗎（不是合理猜測）
6. 每個 `spurious_reading` 都真的不被允許嗎（這是 precision 的分母）
7. `field_determinable` 誠實嗎（標準是「原文本身」不是「我猜得出來」）

**verdict 可填**：`keep` / `fix: 具體改法` / `drop` / `uncertain`
"""


def block(item: dict) -> str:
    amb = item["text"]
    mp = item.get("minimal_pair", {}) or {}
    dis = mp.get("text", "")
    diff = len(dis) - len(amb)

    L: list[str] = []
    L.append(f"## {item['id']}  ({item['ambiguity_type']})")
    if item["id"] in CONTAMINATED:
        L.append("")
        L.append(f"> 🔴 **標註獨立性缺口**：{CONTAMINATED[item['id']]}")
    L.append("")
    L.append("| | 句子 | 字數 |")
    L.append("|---|---|---|")
    L.append(f"| 歧義 | {amb} | {len(amb)} |")
    L.append(f"| 消歧 | {dis} | {len(dis)} |")
    L.append("")
    L.append(f"改動：{mp.get('edit', '（未填）')}　　字數差：{diff:+d}")
    if mp.get("resolves_to"):
        L.append(f"消歧後鎖定：{mp['resolves_to']}")
    L.append("")

    L.append("**licensed_readings**")
    lr = item.get("licensed_readings") or []
    if lr:
        for i, r in enumerate(lr, 1):
            when = r.get("licensed_when") or r.get("applicable_when") or ""
            intent = r.get("speaker_intent")
            tail = f"　　適用：{when}" if when else ""
            tail += f"　　intent={intent}" if intent else ""
            L.append(f"{i}. {r.get('reading', '')}{tail}")
    else:
        L.append("（無）")
    L.append("")

    L.append("**spurious_readings**")
    sr = item.get("spurious_readings") or []
    for s in sr:
        L.append(f"- {s}")
    if not sr:
        L.append("（無）")
    L.append("")

    L.append(f"**text_determinable**: {str(item.get('text_determinable')).lower()}")
    fd = item.get("field_determinable") or {}
    if fd:
        parts = " / ".join(f"{k}={str(v).lower()}" for k, v in fd.items())
        L.append(f"**field_determinable**: {parts}")
    else:
        L.append("**field_determinable**: （未填）")
    L.append(f"**expected_route**: {item.get('expected_route', '（未填）')}")
    rc = item.get("required_clarifications") or []
    L.append(f"**required_clarifications**: {rc if rc else '[]'}")
    L.append("")
    L.append("---")
    L.append("**verdict**: <!-- keep / fix: 具體改法 / drop / uncertain -->")
    L.append("**note**:")
    L.append("")
    L.append("=" * 59)
    L.append("")
    return "\n".join(L)


def summary_table(items: list[dict]) -> str:
    L = ["## 總表", "",
         "| id | 類型 | 字數差 | licensed | spurious | text_determinable |",
         "| --- | --- | ---: | ---: | ---: | :-: |"]
    for it in items:
        amb = it["text"]
        dis = (it.get("minimal_pair") or {}).get("text", "")
        mark = " 🔴" if it["id"] in CONTAMINATED else ""
        L.append(f"| {it['id']}{mark} | {it['ambiguity_type'][:4]} | "
                 f"{len(dis) - len(amb):+d} | "
                 f"{len(it.get('licensed_readings') or [])} | "
                 f"{len(it.get('spurious_readings') or [])} | "
                 f"{str(it.get('text_determinable')).lower()} |")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEV / "REVIEW.md"))
    args = ap.parse_args()

    src = DEV / "sentences.yaml"
    raw = src.read_bytes()
    data = yaml.safe_load(raw.decode("utf-8"))
    items = data["items"]
    sha = hashlib.sha256(raw).hexdigest()

    out: list[str] = []
    out.append("# dev-30 複核表")
    out.append("")
    out.append(f"> 來源：`data/dev30/sentences.yaml`")
    out.append(f"> SHA-256：`{sha}`")
    dist = data["meta"]["distribution"]
    dist_s = "、".join(f"{k} {v}" for k, v in dist.items())
    out.append(f"> 句數：{len(items)}（{dist_s}）")
    out.append("> ")
    out.append("> 本檔由 `scripts/make_review.py` 機械產生，內容全部取自 YAML，"
               "不含任何助理的判斷或建議。")
    out.append("> 複核完成後請把 `meta.reviewed` 改為 true 並重新記錄 SHA-256。")
    out.append("")
    out.append(CRITERIA)
    out.append("")
    out.append("=" * 59)
    out.append("")
    for it in items:
        out.append(block(it))
    out.append(summary_table(items))
    out.append("")

    p = pathlib.Path(args.out)
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"已產出 {p}")
    print(f"  句數 {len(items)}｜來源 SHA-256 {sha[:16]}…")
    print(f"  標註獨立性缺口 {len(CONTAMINATED)} 句："
          f"{', '.join(sorted(CONTAMINATED))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
