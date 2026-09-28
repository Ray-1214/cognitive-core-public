"""統計程式碼規模（備審資料用）。

分開列出總行數、程式碼行、註解行、docstring 行、空行——
只報一個「行數」會讓人不知道那是不是灌水。

註解與 docstring 分開算，因為本專案的 docstring 承載了大量設計決策記錄，
把它算成「程式碼」不誠實，算成「註解」又低估了它的份量。

用法：
    python scripts/count_lines.py
"""

from __future__ import annotations

import ast
import io
import pathlib
import sys
import tokenize

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = ["src", "scripts", "app", "tests"]
SKIP_PARTS = ("__pycache__", ".venv", "venv", "build", "dist")


def classify(path: pathlib.Path) -> dict:
    """回傳該檔的行數分類。每一行只歸一類。"""
    src = path.read_text(encoding="utf-8", errors="replace")
    lines = src.splitlines()
    total = len(lines)
    kind = ["code"] * total          # 預設全是程式碼，之後覆寫

    for i, ln in enumerate(lines):
        if not ln.strip():
            kind[i] = "blank"

    # 註解：用 tokenize 找 COMMENT，避免把字串裡的 # 誤判
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                row = tok.start[0] - 1
                if 0 <= row < total and kind[row] != "blank":
                    # 整行註解才算註解行；行尾註解仍算程式碼行
                    kind[row] = ("comment" if lines[row].lstrip().startswith("#")
                                 else kind[row])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass

    # docstring：模組／類別／函式的第一個字串常數
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Module, ast.ClassDef,
                                     ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if (isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                for row in range(first.lineno - 1, (first.end_lineno or 0)):
                    if 0 <= row < total and kind[row] == "code":
                        kind[row] = "docstring"
    except (SyntaxError, ValueError):
        pass

    out = {"total": total, "code": 0, "comment": 0, "docstring": 0, "blank": 0}
    for k in kind:
        out[k] += 1
    return out


def main() -> int:
    grand = {"files": 0, "total": 0, "code": 0, "comment": 0,
             "docstring": 0, "blank": 0}
    rows = []
    for name in TARGETS:
        base = ROOT / name
        agg = {"files": 0, "total": 0, "code": 0, "comment": 0,
               "docstring": 0, "blank": 0}
        if base.exists():
            for p in sorted(base.rglob("*.py")):
                if any(part in SKIP_PARTS for part in p.parts):
                    continue
                c = classify(p)
                agg["files"] += 1
                for k in ("total", "code", "comment", "docstring", "blank"):
                    agg[k] += c[k]
        rows.append((name, agg))
        for k in agg:
            grand[k] += agg[k]

    w = 10
    print(f"{'目錄':<10}{'檔案':>6}{'總行':>{w}}{'程式碼':>{w}}"
          f"{'註解':>{w}}{'docstring':>{w + 2}}{'空行':>{w}}")
    print("  " + "─" * 62)
    for name, a in rows:
        print(f"  {name:<8}{a['files']:>6}{a['total']:>{w}}{a['code']:>{w}}"
              f"{a['comment']:>{w}}{a['docstring']:>{w + 2}}{a['blank']:>{w}}")
    print("  " + "─" * 62)
    print(f"  {'合計':<8}{grand['files']:>6}{grand['total']:>{w}}"
          f"{grand['code']:>{w}}{grand['comment']:>{w}}"
          f"{grand['docstring']:>{w + 2}}{grand['blank']:>{w}}")
    print()
    doc = grand["comment"] + grand["docstring"]
    print(f"  程式碼行（不含空行、註解、docstring）：{grand['code']:,}")
    print(f"  說明性文字（註解 + docstring）：{doc:,}"
          f"　佔非空行的 {doc / (grand['total'] - grand['blank']) * 100:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
