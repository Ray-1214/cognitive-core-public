"""抽出所有關鍵數字成一份 JSON，供重現驗證逐項比對。

肉眼比對會漏掉小數點後第三位的差異，而那正是非確定性最先顯現的地方。

用法：
    python scripts/snapshot_results.py --out data/results/_snapshot_before.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "data" / "results"
PROBES = ROOT / "data" / "probes" / "wsd_probes.yaml"


def sha(p: pathlib.Path) -> str | None:
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load(name: str) -> dict:
    f = RESULTS / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def auc_table() -> dict:
    """從 signals_all.md 的 AUC 主表與對照列抽數字。JSON 沒存表格。

    ⚠️ 必須限定在 `### 主表` … `### vs 純句長` 之間。整份掃會撈到
    後面「每題成本」表的 `| S5_llm_direct | 1 | 0 |`，把 AUC 覆蓋成 1.0。
    """
    f = RESULTS / "signals_all.md"
    if not f.exists():
        return {}
    t = f.read_text(encoding="utf-8")
    i, j = t.find("### 主表"), t.find("### vs 純句長")
    if i < 0:
        return {}
    body = t[i:j if j > i else len(t)]
    out = {}
    for line in body.splitlines():
        m = re.match(r"\|\s*(S\d_\w+)\s*\|\s*([\d.]+)\s*\|", line)
        if m:
            out[m.group(1)] = float(m.group(2))
        m2 = re.match(r"\|\s*\*\*(未加權總和|純句長基準)\*\*\s*\|\s*([\d.]+)\s*\|", line)
        if m2:
            out[m2.group(1)] = float(m2.group(2))
    return out


def required_auc_used() -> float | None:
    f = RESULTS / "signals_all.md"
    if not f.exists():
        return None
    m = re.search(r"required_auc = \*\*([\d.]+)\*\*", f.read_text(encoding="utf-8"))
    return float(m.group(1)) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = load("wsd_baseline400.json")
    val = load("judge_validation_r2.json")
    litm = load("lost_in_the_middle.json")
    prereg = load("signal_preregistration.json")

    snap = {
        "probes_sha": sha(PROBES),
        "baseline": {
            "n": base.get("n"),
            "accuracy": base.get("accuracy"),
            "error_rate": (1 - base["accuracy"]) if base.get("accuracy") else None,
            "n_judgeable": base.get("n_judgeable"),
            "none": base.get("none"),
            "diff": base.get("diff"),
            "by_stratum": {k: v.get("acc") for k, v in
                           (base.get("by_stratum") or {}).items()},
            "position_effect": {
                k: base.get("position_effect", {}).get(k)
                for k in ("diff", "se", "p", "implied_noise",
                          "acc_gold_a", "acc_gold_b")},
        },
        "judge_validation": {
            "n": val.get("n"),
            "judge_vs_human": val.get("judge_vs_human"),
            "human_vs_gold": val.get("human_vs_gold"),
            "judge_vs_gold": val.get("judge_vs_gold"),
            "both_plausible_rate": val.get("both_plausible_rate"),
            "contaminated": val.get("contaminated"),
        },
        "auc": auc_table(),
        "required_auc": required_auc_used(),
        "ceilings": {r["signal"]: r["auc_ceiling"]
                     for r in prereg.get("signals", [])},
        "lost_in_the_middle": {
            pos: {"baseline": v["baseline"], "memory": v["memory"]}
            for pos, v in (litm.get("summary") or {}).items()},
        "file_sha": {n: sha(RESULTS / n) for n in (
            "wsd_baseline400.json", "signals_all.json",
            "judge_validation_r2.json", "signal_preregistration.json",
            "lost_in_the_middle.json")},
    }
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"  {out}")
    print(f"  探針檔 sha {snap['probes_sha']}")
    print(f"  錯誤率 {snap['baseline']['error_rate']}")
    print(f"  AUC 抓到 {len(snap['auc'])} 項")
    return 0


if __name__ == "__main__":
    sys.exit(main())
