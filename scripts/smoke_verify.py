"""Phase A 驗收：錨點建構 + 四種 verify profile 走同一路徑。

⚠️ 測試句刻意使用已退役的 spike 句，不碰 dev-30（標註污染，地雷 3）。

用法：
    python scripts/smoke_verify.py
    python scripts/smoke_verify.py --text "他終於放下了"
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from cognitive_core.assets import asset_manifest  # noqa: E402
from cognitive_core.llm import Client  # noqa: E402
from cognitive_core.reflect import build_anchor, clarification_needed, revise_anchor  # noqa: E402
from cognitive_core.runlog import RunLog  # noqa: E402
from cognitive_core.verify import Verifier, VerifyConfig  # noqa: E402

# 已退役的 spike 句，非 dev-30
DEFAULT_TEXT = "方便的話明天再說吧"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=DEFAULT_TEXT)
    ap.add_argument("--profiles", nargs="*",
                    default=["cross_en_ja", "cross_en_de", "same_en", "single_ja"])
    ap.add_argument("--force-reflect", action="store_true",
                    help="把一致性閾值拉到 1.0 強制觸發反思迴圈，驗證該路徑")
    args = ap.parse_args()
    force_th = 1.0 if args.force_reflect else None

    run = RunLog("smoke_verify", meta={"purpose": "Phase A 驗收",
                                       "assets": asset_manifest(),
                                       "text": args.text})
    client = Client(run=run)
    vcfg = VerifyConfig()
    verifier = Verifier(client, vcfg)
    ok = fail = 0

    print(f"測試句：{args.text}")
    print(f"（已退役的 spike 句，非 dev-30）\n")

    # ── 1. 錨點建構 ──
    print("=== 1. 錨點建構（走降級階梯）===")
    try:
        anchor, tier = build_anchor(client, args.text)
        ok += 1
        print(f"  ✅ tier={tier}  built_by={anchor.built_by}")
        print(f"     UNKNOWN 欄位：{anchor.unknown_scalars() or '（無）'}")
        print(f"     可決定唯一讀法：{anchor.uncertainty.text_determinable}")
        print(f"     列舉讀法 {len(anchor.uncertainty.alternative_readings)} 個：")
        for r in anchor.uncertainty.alternative_readings:
            print(f"       - {r.reading}"
                  + (f"（{r.applicable_when}）" if r.applicable_when else "")
                  + f"  intent={r.speaker_intent}")
        q = clarification_needed(anchor)
        if q:
            print(f"     澄清提問：{q[0]}")
    except Exception as e:  # noqa: BLE001
        print(f"  ❌ {type(e).__name__}: {str(e)[:200]}")
        return 1

    # ── 2. 原文不可變 ──
    print("\n=== 2. 約束檢查 ===")
    assert anchor.source_text == args.text
    print(f"  ✅ source_text 未被更動")

    # ── 3. 四種 profile 走同一路徑 ──
    print("\n=== 3. 四種 verify profile（同一條程式碼路徑）===")
    print(f"  {'profile':14}{'mode':16}{'譯本':>4}{'偵測分數':>10}{'一致性':>9}"
          f"{'通過':>6}  差異點")
    print("  " + "-" * 76)
    reports = {}
    for name in args.profiles:
        try:
            rep = verifier.run(anchor, name, consistency_threshold=force_th)
            reports[name] = rep
            ok += 1
            cons = f"{rep.consistency:.4f}" if rep.consistency is not None else "  n/a"
            det = f"{rep.detector_score:.4f}" if rep.detector_score is not None else "  n/a"
            print(f"  {name:14}{rep.mode:16}{len(rep.back_translations):>4}"
                  f"{det:>10}{cons:>9}{'✓' if rep.passed else '✗':>6}  "
                  f"{len(rep.differences)} 項")
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"  {name:14}❌ {type(e).__name__}: {str(e)[:90]}")

    # ── 4. 單探針不做診斷 ──
    print("\n=== 4. 偵測／診斷分離（§4.2.1）===")
    sp = reports.get("single_ja")
    if sp is not None:
        assert sp.consistency is None, "單探針不該有樣本間一致性"
        assert sp.detector_score is not None, "單探針必須給得出偵測分數"
        assert sp.differences == [], "單探針給不出差異點"
        print("  ✅ 單探針：有偵測分數、無一致性、無差異點")
        ok += 1
    cl = reports.get("cross_en_ja")
    if cl is not None:
        assert cl.consistency is not None
        print(f"  ✅ 跨語言：有一致性（{cl.consistency:.4f}），可做 IdentifyDiff")
        ok += 1

    # ── 5. 反思迴圈 ──
    print("\n=== 5. 反思修訂（修錨點不修譯文）===")
    base = reports.get("cross_en_ja")
    if base and not base.passed:
        try:
            revised, tier2 = revise_anchor(client, anchor, base.differences)
            ok += 1
            print(f"  ✅ tier={tier2}  revisions {anchor.revisions} → {revised.revisions}")
            print(f"     source_text 保持不變：{revised.source_text == args.text}")
            print(f"     UNKNOWN 欄位：{anchor.unknown_scalars()} → {revised.unknown_scalars()}")
            print(f"     讀法數：{len(anchor.uncertainty.alternative_readings)} → "
                  f"{len(revised.uncertainty.alternative_readings)}")
            rep2 = verifier.run(revised, "cross_en_ja")
            c1 = base.consistency or 0
            c2 = rep2.consistency or 0
            print(f"     一致性：{c1:.4f} → {c2:.4f}（{'↑' if c2 > c1 else '↓'}）")
            print(f"     ⚠️ 一致性僅作收斂診斷，不得當勝負依據（地雷 2）")
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"  ❌ {type(e).__name__}: {str(e)[:200]}")
    else:
        print("  （首輪即通過，未觸發反思）")

    s = run.summary()
    print(f"\n=== run 記錄 ===")
    print(f"  呼叫 {s['calls']}｜快取命中 {s['cache_hits']}｜錯誤 {s['errors']}"
          f"｜token {s['total_tokens']}｜{s['wall_s']}s")
    print(f"  {s['path']}")
    print(f"\n{'=' * 60}\n通過 {ok}｜失敗 {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
