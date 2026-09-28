"""Lost-in-the-Middle 初步驗證（v3 架構書 §P7，RQ3）。

問題：長對話中，關鍵資訊放在**中段**時特別容易被遺忘（Liu et al. 2024）。
記憶模組（檢索 + 滾動摘要）能否把中段的召回率拉回來？

## 設計

造 N 組長對話，每組把一則「關鍵事實」分別放在頭／中／尾三個位置，
其餘為填充訊息。然後問一個只有靠那則事實才答得出的問題。

  對照組  無記憶：只把最近 `window` 則塞進脈絡（模擬固定視窗）
  實驗組  有記憶：檢索 top-k + 滾動摘要

指標是**召回率**——關鍵事實有沒有進入送給模型的脈絡。
量的是檢索機制，不是模型的回答能力：把模型的作答能力混進來會讓
「記憶模組有沒有用」與「模型聰不聰明」分不開。

⚠️ **n=10 不足以下定論。** 圖說與報告都標為初步驗證。

用法：
    python scripts/lost_in_the_middle.py --n 10
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cognitive_core.eval.wsd import wilson_ci  # noqa: E402
from cognitive_core.memory import MemoryStore, RollingSummary, SummaryConfig  # noqa: E402

RESULTS = ROOT / "data" / "results"
FIGS = ROOT / "figs"

POSITIONS = ("頭", "中", "尾")

FILLER = [
    "今天天氣還不錯，適合出門走走。",
    "剛剛那份文件我已經看過了。",
    "會議室好像被別的部門借走了。",
    "午餐要不要一起吃？",
    "系統昨晚更新過，速度快了一些。",
    "那本書我上週還回圖書館了。",
    "印表機的碳粉快用完了。",
    "下午的訓練課程改成線上舉行。",
    "停車場今天在施工。",
    "我把資料夾放在櫃子第二層。",
]


# ⚠️ 詞彙干擾項。沒有這些，關鍵事實在詞彙上與填充訊息完全不重疊，
# 檢索任務是 trivial 的——第一版實測三個位置全是 100%，那個數字只反映
# 「關鍵句用了查詢裡的詞而別人沒有」，不反映檢索是否穩健。
DISTRACTORS = [
    "上一個專案的代號我忘記了，要問一下。",
    "負責人好像換過人，現在不確定是誰。",
    "那個專案的代號跟這個很像，別搞混了。",
    "代號的編碼規則去年改過一次。",
    "負責人清單放在共用資料夾裡。",
]


def make_dialogue(seed: int, n_turns: int, position: str, *,
                  n_distractors: int = 0) -> tuple[list[str], str, str]:
    """回傳 (訊息串, 關鍵事實, 查詢)。

    `n_distractors` 插入幾則與查詢共享詞彙但不含答案的訊息。
    """
    rng = random.Random(seed)
    key_id = rng.randint(1000, 9999)
    fact = f"專案代號是 {key_id}，負責人是林小姐。"
    query = "專案代號是多少？負責人是誰？"
    msgs = [rng.choice(FILLER) for _ in range(n_turns - 1)]
    for d in rng.sample(DISTRACTORS, min(n_distractors, len(DISTRACTORS))):
        msgs[rng.randrange(len(msgs))] = d
    idx = {"頭": 0, "中": len(msgs) // 2, "尾": len(msgs)}[position]
    msgs.insert(idx, fact)
    return msgs, fact, query


def char_embed(texts: list[str]) -> list[list[float]]:
    """字元 n-gram 的雜湊向量。不呼叫 API——RQ3 要量的是檢索機制。

    用 LLM 嵌入會把嵌入模型的品質混進結果，那是另一個變因；
    且本實驗只需要「含關鍵詞的句子相似度較高」這個性質。

    ⚠️ 用 `zlib.crc32` 而非內建 `hash()`——後者對字串是每個行程隨機化的，
    結果無法重現。
    """
    dim = 64
    out = []
    for t in texts:
        v = [0.0] * dim
        for i in range(len(t)):
            for k in (1, 2):
                if i + k <= len(t):
                    v[zlib.crc32(t[i:i + k].encode()) % dim] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        out.append([x / norm for x in v])
    return out


def api_embed_factory():
    """真實的 bge-m3 嵌入（校內端點，免費）。

    字元 n-gram 版本的問題：關鍵句字面上就含查詢的「專案代號」「負責人」，
    等於在做子字串比對，三個位置都是 100%——那個數字不反映語意檢索的能力。
    """
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    from cognitive_core.llm import Client
    client = Client()
    cache: dict[str, list[float]] = {}

    def embed(texts: list[str]) -> list[list[float]]:
        todo = [x for x in texts if x not in cache]
        if todo:
            for x, v in zip(todo, client.embed(todo)):
                cache[x] = v
        return [cache[x] for x in texts]
    return embed


def run_group(seed: int, n_turns: int, position: str, *,
              window: int, top_k: int, n_distractors: int = 0,
              embedder=None) -> dict:
    msgs, fact, query = make_dialogue(seed, n_turns, position,
                                      n_distractors=n_distractors)

    # 對照組：固定視窗，只留最近 window 則
    baseline_ctx = msgs[-window:]
    baseline_hit = fact in baseline_ctx

    # 實驗組：滾動摘要後的脈絡 + 檢索補回相關的舊項目
    store = MemoryStore(embedder or char_embed, summary=RollingSummary(
        SummaryConfig(window=window, keep_recent=max(window // 2, 2))))
    for m in msgs:
        store.add(m)
    ctx = store.augmented_context(query, k=top_k)
    memory_hit = any(e.text == fact for e in ctx)

    return {"seed": seed, "position": position, "n_turns": n_turns,
            "baseline_hit": baseline_hit, "memory_hit": memory_hit,
            "n_context": len(ctx), "n_stored": len(store)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="每個位置幾組對話")
    ap.add_argument("--turns", type=int, default=30)
    ap.add_argument("--window", type=int, default=8)
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--embed", choices=("api", "char"), default="api",
                    help="api = 真實 bge-m3（校內端點，免費）；"
                         "char = 字元 n-gram（離線，但等於子字串比對）")
    ap.add_argument("--distractors", type=int, default=4,
                    help="插入幾則與查詢共享詞彙但不含答案的訊息。"
                         "設 0 會讓任務變得 trivial（實測三個位置全 100%%）")
    args = ap.parse_args()

    embedder = None
    if args.embed == "api":
        try:
            embedder = api_embed_factory()
            print("嵌入：ithu/bge-m3-embedding")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 無法建立 API 嵌入（{type(e).__name__}），退回字元 n-gram")
            args.embed = "char"
    if embedder is None:
        print("嵌入：字元 n-gram（離線）")

    rows = [run_group(1000 + i, args.turns, pos, window=args.window,
                      top_k=args.top_k, n_distractors=args.distractors,
                      embedder=embedder)
            for pos in POSITIONS for i in range(args.n)]

    summary = {}
    for pos in POSITIONS:
        g = [r for r in rows if r["position"] == pos]
        b = sum(r["baseline_hit"] for r in g)
        m = sum(r["memory_hit"] for r in g)
        summary[pos] = {
            "n": len(g),
            "baseline": b / len(g), "baseline_ci": list(wilson_ci(b, len(g))),
            "memory": m / len(g), "memory_ci": list(wilson_ci(m, len(g))),
        }

    L = [f"# Lost-in-the-Middle 初步驗證　每位置 n={args.n}", "",
         "> ⚠️ **n 過小，不足以下定論。本節為初步驗證。**", "",
         f"對話長度 {args.turns} 則，固定視窗 {args.window}，檢索 top-{args.top_k}，"
         f"詞彙干擾項 {args.distractors} 則，"
         f"嵌入 {'ithu/bge-m3-embedding' if args.embed == 'api' else '字元 n-gram'}。",
         "",
         "⚠️ **干擾項是必要的。** 沒有它們時關鍵事實與填充訊息在詞彙上"
         "完全不重疊，檢索任務 trivial——",
         "實測三個位置全是 100%，那個數字只反映「關鍵句用了查詢裡的詞"
         "而別人沒有」，不反映檢索是否穩健。",
         "指標為**召回率**：關鍵事實有沒有進入送給模型的脈絡。",
         "刻意不量模型的作答正確率——那會讓「記憶模組有沒有用」",
         "與「模型聰不聰明」分不開。", "",
         "| 關鍵資訊位置 | n | 無記憶（固定視窗） | 95% CI | 有記憶（檢索+摘要） | 95% CI |",
         "| :-: | :-: | :-: | :-: | :-: | :-: |"]
    for pos in POSITIONS:
        s = summary[pos]
        L.append(f"| {pos} | {s['n']} | {s['baseline']:.0%} | "
                 f"[{s['baseline_ci'][0]:.0%}, {s['baseline_ci'][1]:.0%}] | "
                 f"**{s['memory']:.0%}** | "
                 f"[{s['memory_ci'][0]:.0%}, {s['memory_ci'][1]:.0%}] |")
    mid = summary["中"]
    ceiling = all(summary[p]["memory"] >= 1.0 for p in POSITIONS)
    L += ["", f"**中段的落差**：無記憶 {mid['baseline']:.0%} → "
              f"有記憶 {mid['memory']:.0%}", ""]
    if ceiling:
        L += ["⚠️ **有記憶組三個位置都是 100%，這是天花板效應。**", "",
              f"{args.turns} 則訊息中只有 1 則與查詢相關，檢索 top-{args.top_k}——"
              "任務對檢索而言不難。",
              "這個結果證明**機制可行**（滾動摘要壓掉的內容能由檢索補回），",
              "不證明它在更難的場景仍然有效：多則部分相關、"
              "需要跨訊息綜合、或關鍵資訊本身就模糊時，結果會不同。",
              "要看出區別需要更難的資料集，那超出本專案的範圍。", ""]
    L += ["<!-- TODO(你寫)：與 Liu et al. 2024 的關係；"
          "n=10 與天花板效應的限制 -->", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "lost_in_the_middle.md"
    out.write_text("\n".join(L), encoding="utf-8")
    (RESULTS / "lost_in_the_middle.json").write_text(
        json.dumps({"config": vars(args), "summary": summary, "rows": rows},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    _plot(summary, args)
    print(f"{'位置':<6}{'無記憶':>10}{'有記憶':>10}")
    for pos in POSITIONS:
        s = summary[pos]
        print(f"  {pos:<6}{s['baseline']:>9.0%}{s['memory']:>10.0%}")
    print(f"\n  {out}")
    return 0


def _plot(summary: dict, args) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  （未安裝 matplotlib，略過作圖）")
        return
    FIGS.mkdir(parents=True, exist_ok=True)
    x = range(len(POSITIONS))
    b = [summary[p]["baseline"] for p in POSITIONS]
    m = [summary[p]["memory"] for p in POSITIONS]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, b, "o--", label="no memory (fixed window)")
    ax.plot(x, m, "s-", label="with memory (retrieval + summary)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["start", "middle", "end"])
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("recall of key fact")
    ax.set_xlabel("position of key fact in dialogue")
    ax.set_title(f"Lost-in-the-Middle (preliminary, n={args.n} per position)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    p = FIGS / "lost_in_the_middle.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print(f"  {p}")


if __name__ == "__main__":
    sys.exit(main())
