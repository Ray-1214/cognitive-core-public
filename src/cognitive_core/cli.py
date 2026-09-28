"""批次與單句入口（實作規格書 §4）。

三個子命令：
    run     單句，輸出像 Phase E 的決策時間軸，終端機就看得懂
    batch   走資料集，支援斷點續跑
    golden  黃金案例回歸，觀測工具（不符預期標紅但不失敗退出）

評測一律走 CLI，不靠點 GUI（§5.5）。
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
from typing import Any

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:  # pragma: no cover
    pass

from .assets import asset_manifest  # noqa: E402
from .graph import build_graph, initial_state  # noqa: E402
from .history import adaptive_n, estimate_cost  # noqa: E402
from .llm import Client  # noqa: E402
from .runlog import RunLog  # noqa: E402
from .verify import VerifyConfig  # noqa: E402

RED = "\033[31m"
YEL = "\033[33m"
GRN = "\033[32m"
DIM = "\033[2m"
RST = "\033[0m"


# ────────────────────────── 輸出 ──────────────────────────

def render_timeline(state: dict) -> str:
    """把 state.timeline 攤成人類可讀的決策時間軸。

    ⚠️ 只顯示結構化決策記錄，不顯示模型的原始推理文字（計畫書 §4.9）。
    """
    L: list[str] = [f"原文：{state['source_text']}"]
    circled = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
    for i, ev in enumerate(state.get("timeline", [])):
        mark = circled[i] if i < len(circled) else f"({i + 1})"
        node = ev["node"]
        if node == "route":
            L.append(f"{mark} Router      [stub] → {'快速' if ev.get('path') == 'fast' else '慢速'}通道")
        elif node == "build_anchor":
            L.append(f"{mark} 錨點建構     tier={ev['tier']}")
            unk = ev.get("unknown_scalars") or []
            L.append(f"{'':12} UNKNOWN: {', '.join(unk) if unk else '（無）'}")
            L.append(f"{'':12} 讀法 {ev['n_readings']} 個"
                     f"　可決定唯一讀法={ev.get('text_determinable')}")
            if not ev.get("self_report_agrees", True):
                L.append(f"{'':12} {YEL}⚠ 自報與列舉行為不一致{RST}")
            nv = ev.get("n_format_violations", 0)
            if nv:
                L.append(f"{'':12} {YEL}⚠ 格式違規 {nv} 項{RST}")
        elif node == "translate_multi":
            L.append(f"{mark} 平行翻譯     "
                     + "  ".join(f"{k} ✓" for k in ev.get("languages", [])))
        elif node == "translate_direct":
            L.append(f"{mark} 直接翻譯     "
                     + "  ".join(f"{k} ✓" for k in ev.get("languages", [])))
        elif node == "verify":
            det = ev.get("detector_score")
            con = ev.get("consistency")
            ds = f"{det:.3f}" if det is not None else "n/a"
            cs = f"{con:.3f}" if con is not None else "n/a"
            flag = f"{GRN}✓ 通過{RST}" if ev.get("passed") else f"{YEL}✗ 未通過{RST}"
            L.append(f"{mark} 回譯比對     偵測 {ds}　一致性 {cs}　{flag}"
                     f"　差異 {ev.get('n_differences', 0)} 項")
        elif node == "reflect":
            L.append(f"{mark} 反思 ({ev['revision']})   tier={ev['tier']}"
                     f"　讀法 {ev.get('n_readings')} 個")
            b, a = ev.get("unknown_before") or [], ev.get("unknown_after") or []
            if b != a:
                L.append(f"{'':12} UNKNOWN: {b} → {a}")
        elif node == "write_memory":
            if ev.get("high_uncertainty"):
                L.append(f"{mark} 不確定性     {YEL}⚠ 高不確定性{RST}")

    fin = state.get("final") or {}
    unk = fin.get("unknown_scalars") or []
    if unk:
        L.append(f"{'':12} 仍為 UNKNOWN：{', '.join(unk)}")
    for q in (fin.get("clarifications") or [])[:2]:
        L.append(f"{'':12} → 澄清提問：{q}")
    fv = fin.get("format_violations") or []
    L.append("─" * 45)
    if fv:
        L.append(f"{YEL}格式違規 {len(fv)} 項{RST}：" + "；".join(fv[:3]))
    else:
        L.append("格式違規 0 項")
    if fin.get("readings"):
        L.append("讀法：" + " / ".join(fin["readings"]))
    return "\n".join(L)


def cost_line(run: RunLog) -> str:
    s = run.summary()
    return (f"成本：{s['calls']} 次呼叫 / {s['total_tokens']:,} tokens"
            f" / {s['wall_s']}s / 快取命中 {s['cache_hits']}")


# ────────────────────────── run ──────────────────────────

def cmd_run(args) -> int:
    run = RunLog("cli_run", meta={"assets": asset_manifest(), "text": args.text,
                                  "profile": args.profile})
    client = Client(run=run)
    graph = build_graph(client, profile=args.profile)
    state = graph.invoke(initial_state(args.text, args.targets, args.profile))
    if args.json:
        out = {k: v for k, v in state.items() if not k.startswith("_")}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render_timeline(state))
        print(cost_line(run))
        print(f"{DIM}run: {run.path}{RST}")
    return 0


# ────────────────────────── batch ──────────────────────────

def _load_dataset(path: pathlib.Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        items = data.get("items") or data.get("cases") or []
    else:
        items = data
    return [{"id": it.get("id", f"item-{i}"), "text": it["text"]}
            for i, it in enumerate(items) if it.get("text")]


def _done_ids(out_path: pathlib.Path) -> set[str]:
    if not out_path.exists():
        return set()
    done = set()
    for line in out_path.read_text(encoding="utf-8").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("ok"):
            done.add(f"{o['id']}|{o['profile']}")
    return done


def cmd_batch(args) -> int:
    ds = pathlib.Path(args.dataset)
    items = _load_dataset(ds)
    profiles = [p.strip() for p in args.profile.split(",") if p.strip()]
    out_path = pathlib.Path(args.out or (ROOT / "runs" / f"batch-{ds.stem}.jsonl"))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    done = _done_ids(out_path) if args.resume else set()
    todo = [(it, p) for it in items for p in profiles
            if f"{it['id']}|{p}" not in done]

    est = estimate_cost(len({t[0]['id'] for t in todo}), len(profiles))
    print(est.describe())
    if done:
        print(f"斷點續跑：已完成 {len(done)} 筆，本次待跑 {len(todo)} 筆")
    if not todo:
        print("沒有待跑項目。")
        return 0
    if not args.yes:
        try:
            ans = input("繼續？(y/N) ").strip().lower()
        except EOFError:
            ans = "n"
        if ans != "y":
            print("已取消。")
            return 1

    run = RunLog("cli_batch", meta={"assets": asset_manifest(), "dataset": str(ds),
                                    "profiles": profiles, "n_items": len(items),
                                    "n_profiles": len(profiles),
                                    "estimate": {"calls": est.total_calls,
                                                 "tokens": est.total_tokens,
                                                 "source": est.source}})
    client = Client(run=run)
    graphs = {p: build_graph(client, profile=p) for p in profiles}

    ok = fail = 0
    with out_path.open("a", encoding="utf-8") as fh:
        for n, (it, prof) in enumerate(todo, 1):
            print(f"\r[{n}/{len(todo)}] {it['id']:14} {prof:14}", end="", flush=True)
            rec: dict[str, Any] = {"id": it["id"], "profile": prof, "text": it["text"]}
            for attempt in range(args.retries + 1):
                try:
                    st = graphs[prof].invoke(
                        initial_state(it["text"], args.targets, prof))
                    rec |= {"ok": True, "final": st.get("final"),
                            "timeline": st.get("timeline")}
                    ok += 1
                    break
                except Exception as e:  # noqa: BLE001
                    if attempt == args.retries:
                        rec |= {"ok": False,
                                "error": f"{type(e).__name__}: {str(e)[:200]}"}
                        fail += 1
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()          # 逐筆寫入，中途中斷不會全丟

    s = run.summary()
    print(f"\n\n完成 {ok}｜失敗 {fail}｜輸出 {out_path}")
    print("─" * 55)
    print(f"{'':10}{'估計':>12}{'實際':>12}{'誤差':>10}")
    for label, e, a in [("呼叫次數", est.total_calls, s["calls"]),
                        ("tokens", est.total_tokens, s["total_tokens"])]:
        err = f"{(a - e) / e * 100:+.0f}%" if e else "n/a"
        print(f"{label:10}{e:>12,}{a:>12,}{err:>10}")
    print(f"{DIM}（快取命中 {s['cache_hits']} 次，實際值因此可能低於估計）{RST}")
    return 0 if fail == 0 else 1


# ────────────────────────── golden ──────────────────────────

def cmd_golden(args) -> int:
    path = pathlib.Path(args.cases)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = data["cases"]
    profiles = [p.strip() for p in args.profile.split(",") if p.strip()]

    est = estimate_cost(len(cases), len(profiles))
    print(est.describe())
    if not args.yes:
        try:
            ans = input("繼續？(y/N) ").strip().lower()
        except EOFError:
            ans = "n"
        if ans != "y":
            print("已取消。")
            return 1

    run = RunLog("cli_golden", meta={"assets": asset_manifest(),
                                     "n_items": len(cases),
                                     "n_profiles": len(profiles)})
    client = Client(run=run)
    rows: list[dict] = []
    for prof in profiles:
        graph = build_graph(client, profile=prof)
        for c in cases:
            try:
                st = graph.invoke(initial_state(c["text"], args.targets, prof))
                fin = st.get("final") or {}
                rows.append({"id": c["id"], "profile": prof, "text": c["text"],
                             "expect": c.get("expect", {}), "final": fin,
                             "issues": _check_expect(c.get("expect", {}), fin)})
            except Exception as e:  # noqa: BLE001
                rows.append({"id": c["id"], "profile": prof, "text": c["text"],
                             "expect": c.get("expect", {}), "final": {},
                             "issues": [f"執行失敗：{type(e).__name__}"]})

    print(f"\n{'id':11}{'profile':13}{'讀法':>4}{'UNKNOWN':>26}"
          f"{'偵測':>8}{'違規':>5}  符合預期")
    print("─" * 88)
    for r in rows:
        fin = r["final"]
        unk = ",".join(fin.get("unknown_scalars") or []) or "-"
        det = fin.get("detector_score")
        ds = f"{det:.3f}" if det is not None else "  n/a"
        nv = len(fin.get("format_violations") or [])
        mark = f"{GRN}✓{RST}" if not r["issues"] else f"{RED}✗ {'; '.join(r['issues'])}{RST}"
        print(f"{r['id']:11}{r['profile']:13}{fin.get('n_readings', 0):>4}"
              f"{unk[:25]:>26}{ds:>8}{nv:>5}  {mark}")

    bad = sum(1 for r in rows if r["issues"])
    print("─" * 88)
    print(f"{len(rows)} 項中 {bad} 項不符預期"
          f"{'（觀測工具，不視為失敗）' if bad else ''}")
    print(cost_line(run))
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0        # 永遠回 0：這是觀測工具不是斷言


def _check_expect(expect: dict, final: dict) -> list[str]:
    issues: list[str] = []
    n = final.get("n_readings", 0)
    if "min_readings" in expect and n < expect["min_readings"]:
        issues.append(f"讀法 {n} < 預期 {expect['min_readings']}")
    if "max_readings" in expect and n > expect["max_readings"]:
        issues.append(f"讀法 {n} > 預期 {expect['max_readings']}（過度生成）")
    unk = set(final.get("unknown_scalars") or [])
    for f in expect.get("unknown_contains") or []:
        if f not in unk:
            issues.append(f"{f} 未標為 UNKNOWN")
    for f in expect.get("unknown_not_contains") or []:
        if f in unk:
            issues.append(f"{f} 不該是 UNKNOWN")
    return issues


# ────────────────────────── 進入點 ──────────────────────────

def cmd_export(args) -> int:
    """可重現性封包：config + prompts + 資料 + 結果 + commit + 套件版本。

    ⚠️ **不含 .env、不含 .cache、不含 runs/。** 前者是金鑰，
    後兩者是執行期產物且動輒數十 MB。

    ⚠️ 封包**不保證數字可重現**——端點會漂移（見 README 的漂移警語）。
    它保證的是「跑出這些數字時，程式碼與資料長這樣」。
    因此一併收錄端點指紋：讀者可以比對自己面對的端點是否與當時相同。
    """
    import platform
    import subprocess
    import zipfile

    out = pathlib.Path(args.out)
    include_dirs = ["config", "prompts", "skills", "src", "scripts", "tests",
                    "data/probes", "data/results", "data/lexicons",
                    "data/golden", "docs", "app", "figs"]
    include_files = ["README.md", "pyproject.toml", ".env.example", ".gitignore"]
    # 大檔與執行期產物一律排除
    skip_suffix = (".pyc", ".zip")
    skip_parts = ("__pycache__", ".cache", "runs", ".git")

    def freeze() -> str:
        try:
            return subprocess.run([sys.executable, "-m", "pip", "freeze"],
                                  capture_output=True, text=True,
                                  check=True).stdout
        except (subprocess.CalledProcessError, OSError) as e:
            return f"(pip freeze 失敗：{type(e).__name__})"

    def git(*a: str) -> str:
        try:
            r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8", errors="replace",
                               check=True)
        except (subprocess.CalledProcessError, OSError):
            return "unknown"
        return (r.stdout or "").strip()

    fp = ROOT / "data" / "results" / "endpoint_fingerprint.json"
    manifest = {
        "exported_at": datetime.datetime.now().astimezone().isoformat(
            timespec="seconds"),
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "endpoint_fingerprint": (
            json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None),
        "note": ("封包不保證數字可重現——端點會漂移。它保證的是"
                 "「跑出這些數字時，程式碼與資料長這樣」。"
                 "endpoint_fingerprint 供比對端點是否仍相同。"),
        "excluded": [".env（金鑰）", ".cache/（快取）", "runs/（執行日誌）"],
    }

    n = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for d in include_dirs:
            base = ROOT / d
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if not p.is_file() or p.suffix in skip_suffix:
                    continue
                if any(part in skip_parts for part in p.parts):
                    continue
                z.write(p, p.relative_to(ROOT).as_posix())
                n += 1
        for f in include_files:
            p = ROOT / f
            if p.exists():
                z.write(p, f)
                n += 1
        z.writestr("MANIFEST.json",
                   json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr("requirements-frozen.txt", freeze())

    size = out.stat().st_size / 1e6
    print(f"  {out}　{n + 2} 個檔案　{size:.1f} MB")
    print(f"  commit {manifest['git_commit'][:12]}"
          + ("　⚠️ 工作目錄有未提交的變更" if manifest["git_dirty"] else ""))
    print("  已排除：.env（金鑰）／.cache／runs")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cognitive-core")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = dict(targets=["en", "ja"])

    p_run = sub.add_parser("run", help="單句")
    p_run.add_argument("--text", required=True)
    p_run.add_argument("--profile", default="cross_en_ja")
    p_run.add_argument("--targets", nargs="*", default=common["targets"])
    p_run.add_argument("--json", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_b = sub.add_parser("batch", help="批次")
    p_b.add_argument("--dataset", required=True)
    p_b.add_argument("--profile", default="cross_en_ja", help="逗號分隔可多個")
    p_b.add_argument("--targets", nargs="*", default=common["targets"])
    p_b.add_argument("--out", default=None)
    p_b.add_argument("--resume", action="store_true", default=True)
    p_b.add_argument("--no-resume", dest="resume", action="store_false")
    p_b.add_argument("--retries", type=int, default=1)
    p_b.add_argument("--yes", "-y", action="store_true")
    p_b.set_defaults(func=cmd_batch)

    p_g = sub.add_parser("golden", help="黃金案例回歸（觀測工具）")
    p_g.add_argument("--cases", default=str(ROOT / "data" / "golden" / "cases.yaml"))
    p_g.add_argument("--profile", default="cross_en_ja", help="逗號分隔可多個")
    p_g.add_argument("--targets", nargs="*", default=common["targets"])
    p_g.add_argument("--yes", "-y", action="store_true")
    p_g.add_argument("--json", action="store_true")
    p_g.set_defaults(func=cmd_golden)

    p_n = sub.add_parser("adaptive-n", help="顯示取樣次數建議（§4-6）")
    p_n.add_argument("--profile", default="same_en")
    p_n.set_defaults(func=cmd_adaptive_n)

    p_e = sub.add_parser("export", help="可重現性封包")
    p_e.add_argument("--out", default="repro.zip")
    p_e.set_defaults(func=cmd_export)

    args = ap.parse_args(argv)
    return args.func(args)


def cmd_adaptive_n(args) -> int:
    vcfg = VerifyConfig()
    p = vcfg.profile(args.profile)
    n, why = adaptive_n(p.n)
    print(f"profile {args.profile}（mode={p.mode}，config n={p.n}）")
    print(f"  建議 n = {n}")
    print(f"  依據：{why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
