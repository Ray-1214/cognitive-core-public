"""把 REVIEW.md 的第一輪 verdict 套回 sentences.yaml。

⚠️ **只套用明確的編輯指令，不做任何詮釋。**
verdict 寫「fix: 不會有兩人都出差的情況」是**觀察**不是**指令**——
可以理解成刪除該 spurious、也可以理解成它正因不可能才是好的 spurious，
兩種處理相反。這類一律標為待議，留給第二輪。

APPLY 表是本腳本唯一會改動內容的地方，刻意寫死在原始碼裡以便稽核。
每一筆都附上研究者的原話與我採取的動作，任何過度詮釋都看得出來。
"""

from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEV = ROOT / "data" / "dev30"

# ─────────────────────────────────────────────────────────────
# 明確的編輯指令。只有「加上 X」「換成 Y」這種可直接執行的才列入。
# 格式：id -> (動作, 參數, 研究者原話)
# ─────────────────────────────────────────────────────────────
APPLY: dict[str, dict] = {
    "dev-lex-08": {
        "action": "add_licensed_reading",
        "reading": "整理文件",
        "licensed_when": "文件雜亂需歸檔時",
        "speaker_intent": "指示",
        "verbatim": "可以加上整理",
    },
    "dev-ref-04": {
        "action": "add_licensed_reading",
        "reading": "「他」指第三者",
        "licensed_when": "在場另有他人",
        "speaker_intent": "敘述",
        "verbatim": "但是有可能是第三者帶的",
    },
}

# 需要研究者再給具體指示才能動的。這裡只記錄，不猜。
DEFER_REASONS = {
    "spurious_ambiguous": "指出某 spurious_reading 不合理，但「刪除」與「其實是合法讀法」兩種處理相反",
    "not_ambiguous": "指出本句其實只有一個讀法，若照做則不再是歧義正例，會改變資料集結構",
    "needs_text": "需要研究者提供新的讀法文字或新的消歧句",
    "conflict": "同時被標為污染待換，若換句則本 fix 失效",
}
DEFER: dict[str, str] = {
    "dev-lex-02": "spurious_ambiguous",
    "dev-lex-05": "spurious_ambiguous",
    "dev-lex-07": "needs_text",
    "dev-ref-02": "spurious_ambiguous",
    "dev-ref-03": "not_ambiguous",
    "dev-ref-06": "not_ambiguous",
    "dev-prg-05": "conflict",
    "dev-prg-06": "not_ambiguous",
    "dev-prg-07": "not_ambiguous",
}


def parse_verdicts(md: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    blocks = re.split(r"^## (dev-\S+)", md, flags=re.M)
    for i in range(1, len(blocks), 2):
        sid, body = blocks[i], blocks[i + 1]
        m = re.search(r"\*\*verdict\*\*:[ \t]*(.*)", body)
        raw = (m.group(1) if m else "").strip()
        raw = re.sub(r"<!--.*?-->", "", raw).strip()
        if not raw:
            continue
        kind = raw.split(":", 1)[0].strip().lower()
        detail = raw.split(":", 1)[1].strip() if ":" in raw else ""
        out[sid] = {"verdict": kind, "detail": detail, "raw": raw}
    return out


def main() -> int:
    md = (DEV / "REVIEW.md").read_text(encoding="utf-8")
    verdicts = parse_verdicts(md)
    path = DEV / "sentences.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    applied, deferred, kept = [], [], []
    for it in data["items"]:
        sid = it["id"]
        v = verdicts.get(sid)
        if not v:
            continue
        # 逐條寫進 YAML 留痕，第二輪直接看得到
        it["review_r1"] = {"verdict": v["verdict"], "note": v["detail"] or None,
                           "status": "applied" if sid in APPLY else
                                     ("deferred" if sid in DEFER else "none")}
        if v["verdict"] == "keep":
            kept.append(sid)
            it["review_r1"]["status"] = "keep"
            continue
        if sid in APPLY:
            spec = APPLY[sid]
            if spec["action"] == "add_licensed_reading":
                it["licensed_readings"].append({
                    "reading": spec["reading"],
                    "licensed_when": spec["licensed_when"],
                    "speaker_intent": spec["speaker_intent"]})
                applied.append((sid, spec["reading"], spec["verbatim"]))
        elif sid in DEFER:
            it["review_r1"]["defer_reason"] = DEFER_REASONS[DEFER[sid]]
            deferred.append((sid, DEFER[sid], v["detail"]))

    data["meta"]["review_round"] = 1
    data["meta"]["review_r1_summary"] = {
        "keep": len(kept), "applied": len(applied), "deferred": len(deferred)}

    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8")

    print(f"keep {len(kept)}｜已套用 {len(applied)}｜待議 {len(deferred)}\n")
    print("=== 已套用（明確編輯指令）===")
    for sid, what, verbatim in applied:
        print(f"  {sid}  新增讀法「{what}」")
        print(f"{'':14}依據原話：{verbatim}")
    print("\n=== 待議（觀察意見，需具體指示）===")
    for sid, reason, detail in deferred:
        print(f"  {sid}  [{reason}]")
        print(f"{'':14}{detail[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
