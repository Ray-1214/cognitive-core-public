"""記錄實驗溯源：prompt hash + 腳本 hash + git 狀態（技術設計文件 §5.4）。

Prompt 改一個字，所有實驗數據就失效。本工具把每次實驗的 prompt 內容雜湊下來，
之後看到兩批數據不一致，能立刻判斷是不是 prompt 變了，而不必憑記憶猜。

用法：
    python scripts/record_provenance.py                 # 寫入 data/spike/provenance.json
    python scripts/record_provenance.py --check         # 比對現有記錄，有變動則非零退出
"""

from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "spike" / "provenance.json"

# 要追蹤的腳本，以及其中屬於 prompt 的模組級字串常數
TRACKED = {
    "scripts/spike_s0.py": ["ANCHOR_SYSTEM"],
    "scripts/spike_s0b.py": [],   # prompt 為行內字串，改以整檔 hash 追蹤
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def module_constants(path: pathlib.Path, names: list[str]) -> dict[str, str]:
    """靜態解析出模組級字串常數，不執行該檔（避免匯入時觸發 API 呼叫）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in names and isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str):
                        found[t.id] = node.value.value
    return found


def inline_prompts(path: pathlib.Path) -> list[str]:
    """抓出所有含中文且長度 >30 的字串字面值，視為 prompt 候選。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if len(s) > 30 and any("一" <= c <= "鿿" for c in s):
                out.append(s)
    return sorted(set(out))


def git(*args: str) -> str:
    try:
        # Windows 預設 cp950 會在中文檔名上炸掉，必須明指 utf-8
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=15).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def build() -> dict:
    rec: dict = {
        "recorded_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "git": {
            "commit": git("rev-parse", "HEAD") or "(uncommitted)",
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
        },
        "scripts": {},
    }
    for rel, const_names in TRACKED.items():
        p = ROOT / rel
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        entry: dict = {"file_sha256_16": sha(src), "lines": src.count("\n") + 1, "prompts": {}}
        for name, val in module_constants(p, const_names).items():
            entry["prompts"][name] = {"sha256_16": sha(val), "chars": len(val),
                                      "preview": val[:70].replace("\n", " ")}
        for i, s in enumerate(inline_prompts(p)):
            entry["prompts"][f"inline_{i:02d}"] = {"sha256_16": sha(s), "chars": len(s),
                                                   "preview": s[:70].replace("\n", " ")}
        rec["scripts"][rel] = entry

    for rel in ["data/spike/sentences.json"]:
        p = ROOT / rel
        if p.exists():
            rec.setdefault("data", {})[rel] = {"sha256_16": sha(p.read_text(encoding="utf-8"))}
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="比對既有記錄，有變動則以 1 退出")
    args = ap.parse_args()

    rec = build()
    if args.check:
        if not OUT.exists():
            print("尚無 provenance.json，先執行一次不帶 --check 的版本", file=sys.stderr)
            return 1
        old = json.loads(OUT.read_text(encoding="utf-8"))
        changed = []
        for rel, e in rec["scripts"].items():
            oe = old.get("scripts", {}).get(rel, {})
            for k, v in e["prompts"].items():
                ov = oe.get("prompts", {}).get(k)
                if ov is None:
                    changed.append(f"{rel}:{k} 新增")
                elif ov["sha256_16"] != v["sha256_16"]:
                    changed.append(f"{rel}:{k} 已變更（{ov['sha256_16']} → {v['sha256_16']}）")
        if changed:
            print("⚠️ prompt 有變動，既有實驗數據可能已失效：")
            for c in changed:
                print("   " + c)
            return 1
        print("✅ prompt 未變動")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    n = sum(len(e["prompts"]) for e in rec["scripts"].values())
    print(f"已記錄 {len(rec['scripts'])} 個腳本、{n} 段 prompt → {OUT}")
    print(f"  git: {rec['git']['commit'][:8]} ({rec['git']['branch']}){' [dirty]' if rec['git']['dirty'] else ''}")
    for rel, e in rec["scripts"].items():
        print(f"  {rel:26} file={e['file_sha256_16']}  prompts={len(e['prompts'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
