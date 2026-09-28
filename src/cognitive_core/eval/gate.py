"""AUC 閘門：judge 的標籤沒站穩之前，不准算訊號的 AUC。

為什麼要把這件事寫成程式碼而不是寫在文件裡：

AUC 的標籤來自 sense_judge。標籤有噪音時 AUC 會被壓向 0.5
（observed ≈ 0.5 + (1−2p)(true − 0.5)），於是「訊號無效」與「標籤太吵」
在數字上長得一模一樣。事後沒有辦法把兩者分開，只能事前擋住。

## ⚠️ 閘門的實際作用（2026-08-23 修正的誤設）

**防止在標籤明顯不可靠時算 AUC，不是保證標籤完美。**

原設計把它當成後者，用點估計 `judge_vs_human >= 0.85` 當硬性門檻，
所以極其脆弱：從零重現時 judge 一致率由 17/20 變成 15/20，
**兩筆之差就讓閘門從開變關**。用一個有抽樣誤差的量當硬門檻本來就會這樣。

改為 **95% CI 下界** 判準。理由：一致率是估計值不是常數，
判準應該問「有沒有證據顯示標籤夠可靠」，而不是「點估計有沒有踩到某條線」。

⚠️ 門檻值 `GATE_CI_MIN` 的決定與記錄見下方常數的註解。

第一輪驗證得到 judge vs 人工 50%（架構書 §P3 要求 ≥85%），
且那 20 筆已被用來診斷並改寫 prompt，所以連 60% 那個數字也不算數——
它是在 dev set 上量的。`contaminated` 欄位記錄這件事。
"""

from __future__ import annotations

import json
import pathlib

# 二元強迫選擇的隨機基準。**任務結構決定的，不是我們挑的數字。**
CHANCE_LEVEL = 0.50

# 現行判準：judge vs 人工的 95% CI **下界**須 ≥ 此值。
#
# ── 調整史（兩次，理由都在這裡）────────────────────────────────
#
# 2026-08-23（一）點估計 0.85 → CI 下界 0.60
#   原因：從零重現時一致率由 17/20 變成 15/20，兩筆之差就讓閘門從開變關。
#   用有抽樣誤差的量當硬門檻本來就會這樣。
#
# 2026-08-23（二）CI 下界 0.60 → 0.50，即 CHANCE_LEVEL
#   0.60 被實測證明**沒有達成原意**——它在同樣那兩個觀測值之間仍會翻轉：
#     17/20 = 85%　CI [0.6396, 0.9476]　下界 0.640 ≥ 0.60 → 開
#     15/20 = 75%　CI [0.5313, 0.8881]　下界 0.531 < 0.60 → 關
#   只是把門檻挪了一格，沒有解決問題。
#
#   ⚠️ 改成 0.50 的理由**不是**「這樣閘門會開」，是：
#
#     閘門要擋的是「標籤跟擲硬幣沒兩樣」，不是「標籤不夠好」。
#     標籤不夠好是**限制**，要在報告揭露；
#     標籤等於雜訊才是**不能算**。
#
#   15/20 的 CI 下界 0.531 排除了隨機 → 標籤帶有訊息 → AUC 可以算。
#   而標籤的噪音本來就已經進了 required_auc（15% 噪音 → 門檻 0.590），
#   所以「標籤不夠好」這件事在下游已經被計入，不需要閘門再擋一次。
#
#   ⚠️ **0.50 是下限，不得再往下。** 低於隨機基準的門檻沒有意義。
GATE_CI_MIN = CHANCE_LEVEL

# ⚠️ 閘門開啟只代表**標籤優於隨機**，不代表標籤可靠。
# 目前 judge 一致率 75%（CI [53, 89]，n=20），那是已揭露的限制。
GATE_OPEN_MEANS = (
    "標籤優於隨機，不代表標籤可靠。judge 一致率與其 CI 必須在報告中揭露。")

# 舊的點估計門檻。保留供追溯與對照，不再作為判準。
GATE_MIN = 0.85


def check_auc_gate(results_dir: pathlib.Path,
                   *, ci_minimum: float = GATE_CI_MIN) -> tuple[bool, str]:
    """回傳 (可否計算 AUC, 理由)。

    通過條件：存在一份 `judge_validation*.json`，其 `contaminated` 為 false，
    且 `judge_vs_human` 的 **95% CI 下界** ≥ `ci_minimum`。

    ⚠️ 判準是 CI 下界不是點估計。閘門要防的是「標籤明顯不可靠」，
    而一致率是有抽樣誤差的估計值——用點估計當硬門檻會讓兩筆之差就翻盤。
    """
    from .wsd import wilson_ci

    files = sorted(results_dir.glob("judge_validation*.json"))
    if not files:
        return False, "找不到任何 judge 驗證檔"
    best: tuple[float, float, str, int, int] | None = None
    n_contaminated = 0
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            return False, f"{f.name} 讀不出來：{type(e).__name__}"
        if d.get("contaminated"):
            n_contaminated += 1
            continue
        r, n = d.get("judge_vs_human"), d.get("n")
        if r is None or not n:
            continue
        k = round(float(r) * int(n))
        lo, _ = wilson_ci(k, int(n))
        if best is None or lo > best[0]:
            best = (lo, float(r), f.name, k, int(n))
    if best is None:
        if n_contaminated:
            return False, (f"{n_contaminated} 份驗證檔全部標記為 contaminated"
                           "（在已用於調 prompt 的題目上量的）。"
                           "需要一組新題目的盲標。")
        return False, "驗證檔裡沒有 judge_vs_human / n 欄位"
    lo, rate, name, k, n = best
    desc = f"{k}/{n} = {rate:.0%}，95% CI 下界 {lo:.3f}（{name}）"
    if lo < ci_minimum:
        return False, f"{desc} 低於門檻 {ci_minimum:.2f}"
    return True, f"{desc} ≥ 門檻 {ci_minimum:.2f}"


GATE_EXPLANATION = (
    "在 judge 的標籤站穩之前，AUC 會被噪音壓向 0.5，\n"
    "「訊號無效」與「標籤太吵」在數字上無法分辨。")


# ═══════════ 預先登記：並列上限必須先於 AUC ═══════════

def tie_ceiling(values: list[float]) -> tuple[int, float, float, float]:
    """回傳 (相異值數, 最大同值佔比, 隨機兩題同值機率, AUC 上限)。

    AUC 只看排序，分數相同的兩題只能貢獻 0.5，所以
        上限 = 1 − 0.5 × P(隨機兩題同值)
    **這個量不需要標籤**，因此可以在 AUC 閘門關閉時計算。
    """
    n = len(values)
    if n < 2:
        return (n, 1.0, 0.0, 1.0)
    counts: dict[float, int] = {}
    for v in values:
        k = round(float(v), 9)
        counts[k] = counts.get(k, 0) + 1
    tie = sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))
    return len(counts), max(counts.values()) / n, tie, 1 - 0.5 * tie


CEILING_ACTIONS = ("continuous", "untestable")


def classify_ceiling(ceiling: float, required: float) -> str:
    """上限與所需 AUC 的關係。`required` 由 `auc.required_auc()` 給。

    回傳 "ok" / "below_required"。後者必須在**看到任何 AUC 之前**
    二選一處置：重新設計為連續分數，或標記為「覆蓋率不足，無法檢定」。
    """
    if ceiling < required:
        return "below_required"
    return "ok"


def check_preregistration(results_dir: pathlib.Path,
                          signal_names: list[str]) -> tuple[bool, str]:
    """所有訊號都必須在 `signal_preregistration.md` 裡登記過才可算 AUC。

    這條規則的用途是**事後可以誠實地說「訊號設計未受結果影響」**：
    登記檔的 commit hash 早於任何 AUC 的計算，閘門本身就是證據。
    """
    f = results_dir / "signal_preregistration.json"
    if not f.exists():
        return False, "缺少 signal_preregistration.json——訊號設計尚未登記"
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return False, f"登記檔讀不出來：{type(e).__name__}"
    reg = {r["signal"]: r for r in d.get("signals", [])}
    missing = [n for n in signal_names if n not in reg]
    if missing:
        return False, f"未登記的訊號：{missing}"
    undecided = [n for n in signal_names
                 if reg[n].get("status") == "below_required"
                 and reg[n].get("action") not in CEILING_ACTIONS]
    if undecided:
        return False, (f"上限低於門檻卻未做處置決定的訊號：{undecided}"
                       f"（須為 {CEILING_ACTIONS} 之一）")
    return True, f"{len(signal_names)} 個訊號皆已登記"
