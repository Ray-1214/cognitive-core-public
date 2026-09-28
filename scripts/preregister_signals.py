"""訊號的並列上限預先登記（v3 架構書 §P4，2026-08-21 裁示第 4 條）。

## 規則

    所有訊號在計算 AUC 之前，先算並列上限。
    上限 < required_auc 者，二選一：
      (a) 重新設計為連續分數  action="continuous"
      (b) 標記為「覆蓋率不足，無法檢定」  action="untestable"
    決定必須在看到任何 AUC 之前做完並記錄。

## 為什麼要有這個檔

AUC 只看排序，分數相同的兩題只能貢獻 0.5，所以訊號有一個
**與判別力無關**的硬上限：`1 − 0.5 × P(隨機兩題同值)`。
上限低於顯著門檻的訊號，再怎麼有效也測不出來——這時若在看到 AUC 之後
才回頭改訊號設計，就分不清是修正缺陷還是配合結果。

登記檔的 commit hash 早於任何 AUC 的計算，閘門（`eval/gate.py`）拒絕
未登記的訊號，兩者合起來就是「訊號設計未受結果影響」的證據。

⚠️ 本腳本**不使用任何標籤**。並列上限只依賴訊號值的分布。

用法：
    python scripts/preregister_signals.py            # 由 signals_all.json 讀值
"""

from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cognitive_core.eval.auc import required_auc  # noqa: E402
from cognitive_core.eval.gate import (  # noqa: E402
    check_auc_gate,
    classify_ceiling,
    tie_ceiling,
)

RESULTS = ROOT / "data" / "results"

# 處置決定。上限低於門檻者必須在此明列，且理由要寫得起。
DECISIONS = {
    "S4_cultural": {
        "action": "untestable",
        "reason": "400 筆 ASBC 新聞／學術語料只有 8 筆命中成語（2%）。"
                  "擴詞表會變成 LLM 生成（違反詞表來源原則），"
                  "換語料會動搖資料層。照實報「因覆蓋率不足無法檢定」，"
                  "與「訊號無效」明確區分。",
    },
    "S2_subject_ellipsis": {
        "action": "continuous",
        "reason": "v1 對每個子句做二元判定，79% 的題目同值 1.0，上限 0.669。"
                  "v2 加入謂語標記位置作為前置名詞組長度的估計"
                  "（修正 v1 把「沒有人稱代名詞」等同於「省略主詞」的錯誤），"
                  "上限 0.669 → 0.925。"
                  "無證據的子句刻意給 0.5 而不依長度分級，避免變成句長代理。",
    },
    "S5_llm_direct": {
        "action": "continuous",
        "reason": "prompts/router.md v1 用 0.0/0.5/1.0 當說明錨點，"
                  "模型只輸出那三個值，上限 0.753。"
                  "v2 要求兩位小數、量表改為連續帶、錨點改用非整數，"
                  "上限 0.753 → 0.890。",
    },
}


def git_hash() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              check=True).stdout.strip()[:12]
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def main() -> int:
    src = RESULTS / "signals_all.json"
    if not src.exists():
        print(f"🔴 缺少 {src}，先跑 scripts/run_signals.py", file=sys.stderr)
        return 1
    d = json.loads(src.read_text(encoding="utf-8"))
    rows_in = d["items"]
    names = d["signals"]
    n = len(rows_in)

    # 目標變數的類別數依 400 筆**二元**基準的錯誤率（118/399 = 29.6%）估。
    # required_auc 只需要兩類的筆數，不需要標籤本身。
    #
    # ⚠️ 二元設計的錯誤率低於 N 選一（29.6% vs 49.2%），類別因此較不平衡
    # （118/282 vs 186/192），所需 AUC 由 0.557 升到 0.563——代價可忽略，
    # 換到的是 NONE 由 6% 降到 0.25%。
    #
    # 噪音的下界取自 A/B 位置效應的實測（wsd.position_effect），
    # 不用第一輪那個已標記 contaminated 的驗證所推的 25%。
    n_pos = round(n * 0.296)
    pos_noise = 0.0
    base = RESULTS / "wsd_baseline400.json"
    if base.exists():
        pe = json.loads(base.read_text(encoding="utf-8")).get("position_effect") or {}
        pos_noise = pe.get("implied_noise") or 0.0
    need = {p: required_auc(n_pos, n - n_pos, noise=p)
            for p in sorted({0.0, round(pos_noise, 4), 0.10, 0.25})}

    ok, why = check_auc_gate(RESULTS)
    if ok:
        print("🔴 AUC 閘門已開啟——預先登記必須在看到 AUC 之前完成。", file=sys.stderr)
        print(f"   {why}", file=sys.stderr)
        return 2
    print(f"AUC 閘門狀態：關閉（{why}）")
    print("→ 可以進行預先登記\n")

    out = []
    for name in list(names) + ["raw_length"]:
        vals = ([r["raw_length"] for r in rows_in] if name == "raw_length"
                else [r["signals"][name]["score"] for r in rows_in])
        k, mx, tie, cap = tie_ceiling(vals)
        status = classify_ceiling(cap, need[0.0])
        dec = DECISIONS.get(name, {})
        out.append({
            "signal": name, "n": n, "distinct_values": k,
            "max_same_value_share": round(mx, 4),
            "p_tie": round(tie, 4), "auc_ceiling": round(cap, 4),
            "required_auc_clean": need[0.0],
            "required_auc_noise25": need[0.25],
            "position_derived_noise": round(pos_noise, 4),
            "status": status,
            "action": dec.get("action"),
            "reason": dec.get("reason"),
        })

    undecided = [r["signal"] for r in out
                 if r["status"] == "below_required" and not r["action"]]
    if undecided:
        print(f"🔴 上限低於門檻卻沒有處置決定：{undecided}", file=sys.stderr)
        print("   請在 DECISIONS 中補上 action 與理由後再跑。", file=sys.stderr)
        return 3

    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    commit = git_hash()
    payload = {"registered_at": stamp, "commit": commit, "n": n,
               "labels_used": False,
               "note": "並列上限只依賴訊號值的分布，不使用任何標籤。",
               "required_auc": need, "signals": out}
    (RESULTS / "signal_preregistration.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    L = ["# 訊號預先登記　並列上限與處置決定", "",
         f"> 登記時間 `{stamp}`　commit `{commit}`　n={n}", "",
         "**本檔在計算任何 AUC 之前產生。** 並列上限只依賴訊號值的分布，",
         "不使用任何標籤——`labels_used: false`。",
         "AUC 閘門（`eval/gate.py`）拒絕未登記的訊號，",
         "兩者合起來就是「訊號設計未受結果影響」的證據。", "",
         "## 規則", "",
         "```",
         "所有訊號在計算 AUC 之前，先算並列上限。",
         "上限 < required_auc 者，二選一：",
         "  (a) 重新設計為連續分數        action=continuous",
         "  (b) 標記為覆蓋率不足無法檢定  action=untestable",
         "決定必須在看到任何 AUC 之前做完並記錄。",
         "```", "",
         "## 顯著門檻", "",
         f"正類 {n_pos} 筆／負類 {n - n_pos} 筆"
         f"（依 400 筆**二元**基準的錯誤率 29.6%）", "",
         "| 標籤噪音 | 需要的真實 AUC |", "| :-: | :-: |"]
    for p, v in need.items():
        L.append(f"| {p:.0%} | {v:.3f} |")
    L += ["", "## 登記表", "",
          "| 訊號 | 相異值 | 最大同值 | AUC 上限 | 狀態 | 處置 |",
          "| --- | :-: | :-: | :-: | :-: | :-: |"]
    for r in out:
        mark = "🔴 低於門檻" if r["status"] == "below_required" else "✅"
        L.append(f"| {r['signal']} | {r['distinct_values']} | "
                 f"{r['max_same_value_share']:.0%} | **{r['auc_ceiling']:.3f}** | "
                 f"{mark} | {r['action'] or '—'} |")
    L += ["", "## 處置理由", ""]
    for r in out:
        if r["action"]:
            L += [f"### {r['signal']}　→　`{r['action']}`", "", r["reason"], ""]
    L += ["---", "",
          "## 未做處置的訊號", "",
          "上限高於門檻，維持原設計，不因後續 AUC 結果調整：", ""]
    for r in out:
        if not r["action"]:
            L.append(f"- `{r['signal']}`　上限 {r['auc_ceiling']:.3f}")
    L.append("")

    md = RESULTS / "signal_preregistration.md"
    md.write_text("\n".join(L), encoding="utf-8")

    print(f"{'訊號':<26}{'相異值':>7}{'最大同值':>10}{'上限':>8}  處置")
    for r in out:
        print(f"  {r['signal']:<24}{r['distinct_values']:>7}"
              f"{r['max_same_value_share']:>9.0%}{r['auc_ceiling']:>8.3f}"
              f"  {r['action'] or ''}")
    print(f"\n  {md}\n  commit {commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
