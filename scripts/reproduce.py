"""從零重現整條管線，記錄每步的指令與耗時（2026-08-22 裁示 §1）。

## 為什麼需要這個

所有結果都是在**已有快取**的環境裡產生的。拿到 repo 的人是空快取開始跑。
若有腳本依賴未 commit 的中間檔、執行順序有隱含依賴、或某個數字來自
手動修過的檔案——在跑過這支腳本之前，這些都不會被發現。

「可重現」這個宣稱能不能講，取決於這支腳本的結果。

## 用法

    # 1. 先搬走快取（不要刪，比對要用）
    mv .cache <備份位置>/.cache ;  mv runs <備份位置>/runs
    # 2. 記下現有數字
    python scripts/snapshot_results.py --out data/results/_snapshot_before.json
    # 3. 從零重跑
    python scripts/reproduce.py
    # 4. 比對
    python scripts/reproduce.py --compare
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "data" / "results"
LOG = RESULTS / "_repro_steps.json"

STEPS: list[tuple[str, list[str]]] = [
    ("建立探針", ["scripts/build_probes.py", "--total", "400"]),
    ("建立詞表", ["scripts/build_lexicons.py"]),
    ("主基準 400 筆", ["scripts/run_wsd.py", "--n", "400",
                        "--out", "data/results/wsd_baseline400.md"]),
    ("judge 驗證", ["scripts/judge_validate.py", "_r2"]),
    ("訊號值", ["scripts/run_signals.py", "--n", "400"]),
    ("訊號預先登記", ["scripts/preregister_signals.py"]),
    ("AUC 表", ["scripts/run_signals.py", "--n", "400", "--auc", "--reuse"]),
    ("Lost-in-the-Middle", ["scripts/lost_in_the_middle.py", "--n", "10"]),
    ("NONE 分布", ["scripts/analyze_none.py"]),
    ("技術報告", ["scripts/build_report.py"]),
]


def run_all() -> int:
    recs = []
    t_all = time.monotonic()
    for i, (label, argv) in enumerate(STEPS, 1):
        cmd = [sys.executable, *argv]
        print(f"\n[{i}/{len(STEPS)}] {label}\n    $ python {' '.join(argv)}",
              flush=True)
        t0 = time.monotonic()
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env={**__import__("os").environ,
                                "PYTHONIOENCODING": "utf-8"})
        dt = time.monotonic() - t0
        ok = p.returncode == 0
        print(f"    {'✅' if ok else '🔴'} {dt:.0f}s"
              + ("" if ok else f"　exit={p.returncode}"))
        if not ok:
            print("    ── stderr ──")
            print("\n".join(f"    {x}" for x in
                            (p.stderr or "").strip().splitlines()[-15:]))
        recs.append({"step": i, "label": label,
                     "cmd": "python " + " ".join(argv),
                     "seconds": round(dt, 1), "returncode": p.returncode,
                     "stdout_tail": (p.stdout or "").strip().splitlines()[-6:],
                     "stderr_tail": (p.stderr or "").strip().splitlines()[-6:]})
        LOG.write_text(json.dumps(recs, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        if not ok:
            print(f"\n🔴 第 {i} 步失敗，中止。這本身就是重現驗證的結果。")
            return 1
    total = time.monotonic() - t_all
    print(f"\n全部完成，總耗時 {total / 60:.1f} 分鐘")
    return 0


# ── 比對 ──

TOL = 1e-9


def walk(d, prefix="") -> dict:
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            out |= walk(v, key)
        else:
            out[key] = v
    return out


def same(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return abs(a - b) <= TOL
    return a == b


def compare() -> int:
    before_f = RESULTS / "_snapshot_before.json"
    after_f = RESULTS / "_snapshot_after.json"
    if not before_f.exists():
        print("🔴 缺少 _snapshot_before.json", file=sys.stderr)
        return 1
    subprocess.run([sys.executable, "scripts/snapshot_results.py",
                    "--out", str(after_f)], cwd=ROOT, check=True,
                   capture_output=True)
    before = walk(json.loads(before_f.read_text(encoding="utf-8")))
    after = walk(json.loads(after_f.read_text(encoding="utf-8")))

    keys = sorted(set(before) | set(after))
    rows = []
    for k in keys:
        b, a = before.get(k), after.get(k)
        rows.append({"key": k, "before": b, "after": a, "same": same(b, a)})
    bad = [r for r in rows if not r["same"]]

    steps = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    total_s = sum(s["seconds"] for s in steps)

    L = ["# 從零重現驗證", "",
         "> 快取（`.cache/litellm`）與 `runs/` 已搬離工作目錄後，"
         "依序重跑整條管線。", "",
         "## 指令序列與耗時", "",
         "| # | 步驟 | 指令 | 耗時 | 結果 |",
         "| :-: | --- | --- | :-: | :-: |"]
    for s in steps:
        L.append(f"| {s['step']} | {s['label']} | `{s['cmd']}` | "
                 f"{s['seconds']:.0f}s | "
                 f"{'✅' if s['returncode'] == 0 else '🔴 exit=' + str(s['returncode'])} |")
    L += ["", f"**總耗時 {total_s / 60:.1f} 分鐘**", "",
          "## 關鍵數字比對", "",
          f"共 {len(rows)} 項，**{len(rows) - len(bad)} 項一致、"
          f"{len(bad)} 項不一致**。", "",
          "| 項目 | 原值 | 重現值 | 一致 |", "| --- | :-: | :-: | :-: |"]

    def fmt(v):
        if isinstance(v, float):
            return f"{v:.6g}"
        return "—" if v is None else str(v)

    for r in rows:
        L.append(f"| `{r['key']}` | {fmt(r['before'])} | {fmt(r['after'])} | "
                 f"{'✅' if r['same'] else '🔴'} |")
    if bad:
        L += ["", "## 🔴 不一致項目", "",
              "temperature=0 的管線在空快取重跑後仍應完全一致。"
              "不一致代表有非確定性未被控制住，逐項查明原因：", ""]
        for r in bad:
            L.append(f"- `{r['key']}`：{fmt(r['before'])} → {fmt(r['after'])}"
                     "　<!-- 原因： -->")
    else:
        L += ["", "## ✅ 全部一致", "",
              "空快取從零重跑後所有關鍵數字與原值完全相同。"]
    L.append("")

    out = RESULTS / "reproduction_check.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"  一致 {len(rows) - len(bad)}／{len(rows)}")
    for r in bad:
        print(f"  🔴 {r['key']}: {fmt(r['before'])} → {fmt(r['after'])}")
    print(f"\n  {out}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compare", action="store_true", help="只做比對，不重跑")
    args = ap.parse_args()
    return compare() if args.compare else run_all()


if __name__ == "__main__":
    sys.exit(main())
