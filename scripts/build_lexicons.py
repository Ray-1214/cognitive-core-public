"""建立 S1／S4 用的詞表（v3 架構書 §P4）。

⚠️ **不用 LLM 生成詞表。** 兩份來源都是既有的公開資源，授權與處理方式全部記錄。

  S1 多義詞：由 CWN-SemCor 自身推導——該資料集收錄的就是「難詞」
             （CWN 2.0 中義項數 >10 者），義項數直接可算，不需外部詞表
  S4 成語：  pwxcoo/chinese-xinhua 的 idiom.json（MIT），30,895 條，
             簡體，以 OpenCC s2twp 轉台灣正體

用法：
    python scripts/build_lexicons.py
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
LEX = ROOT / "data" / "lexicons"


IDIOM_URL = ("https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/"
             "master/data/idiom.json")


def fetch_idiom_source() -> pathlib.Path:
    """取得原始成語檔，缺少時自動下載。

    ⚠️ 這個檔（10MB）刻意不進版控，但**一定要能自動取得**——
    2026-08-22 的從零重現驗證抓到：乾淨 clone 沒有這個檔，
    本腳本會直接失敗，於是整條管線第 2 步就斷了。
    當時 .gitignore 的註解還寫成「可由 build_lexicons.py 重建」，
    方向剛好相反：是本腳本**消費**它。
    """
    p = LEX / "idiom_xinhua_raw.json"
    if p.exists():
        return p
    import urllib.request

    LEX.mkdir(parents=True, exist_ok=True)
    print(f"  缺少 {p.name}，自下載 …\n    {IDIOM_URL}", flush=True)
    with urllib.request.urlopen(IDIOM_URL, timeout=120) as r:
        data = r.read()
    p.write_bytes(data)
    print(f"    下載完成 {len(data) / 1e6:.1f} MB")
    return p


def build_idioms() -> dict:
    from opencc import OpenCC

    raw = json.loads(fetch_idiom_source().read_text(encoding="utf-8"))
    cc = OpenCC("s2twp")
    seen: dict[str, str] = {}
    for d in raw:
        w = (d.get("word") or "").strip()
        if len(w) < 2:
            continue
        t = cc.convert(w)
        seen.setdefault(t, w)
    out = {
        "name": "idioms",
        "source": "pwxcoo/chinese-xinhua data/idiom.json",
        "license": "MIT",
        "url": "https://github.com/pwxcoo/chinese-xinhua",
        "n_raw": len(raw),
        "conversion": "OpenCC s2twp（簡體 → 台灣正體，含慣用詞轉換）",
        "note": "原始資料為簡體。轉換後去重，故條數少於原始。"
                "轉換可能引入誤差，屬已知限制。",
        "entries": sorted(seen),
    }
    (LEX / "idioms.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  成語：{len(raw)} → 轉繁去重後 {len(seen)} 條")
    return out


def build_polysemous() -> dict:
    """多義詞表由 CWN-SemCor 推導，不需外部詞表。

    該資料集收錄的目標詞即為 CWN 2.0 中義項數 >10 的「難詞」，
    每個詞的義項數可由資料集直接算出，來源可追且與評測資料同源。
    """
    from cognitive_core.data.cwn_loader import load_corpus

    corpus = load_corpus()
    entries = {}
    for w, senses in corpus.senses_by_word.items():
        by_lemma: dict[str, int] = {}
        for sid in senses:
            by_lemma[sid[:6]] = by_lemma.get(sid[:6], 0) + 1
        entries[w] = {"n_senses": len(senses),
                      "n_lemmas": len(by_lemma),
                      "max_senses_in_one_lemma": max(by_lemma.values())}
    out = {
        "name": "polysemous",
        "source": "lopentu/Chinese-Wordnet-SemCor（由資料集推導，非外部詞表）",
        "license": "MIT",
        "note": "該資料集收錄的目標詞即為 CWN 2.0 中義項數 >10 的「難詞」。"
                "max_senses_in_one_lemma 為同讀音下的義項數，"
                "跨 lemma 的多義是同形異音詞，讀出來就消歧，不計入。",
        "n_words": len(entries),
        "entries": entries,
    }
    (LEX / "polysemous.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  多義詞：{len(entries)} 個，"
          f"同 lemma 義項數中位數 "
          f"{sorted(e['max_senses_in_one_lemma'] for e in entries.values())[len(entries) // 2]}")
    return out


def main() -> int:
    LEX.mkdir(parents=True, exist_ok=True)
    print("建立詞表 …")
    build_idioms()
    build_polysemous()

    readme = LEX / "README.md"
    readme.write_text(
        "# 詞表來源\n\n"
        "⚠️ **未使用 LLM 生成任何詞表。** 兩份來源皆為既有公開資源。\n\n"
        "| 詞表 | 來源 | 授權 | 處理 |\n"
        "| --- | --- | --- | --- |\n"
        "| `idioms.json` | [pwxcoo/chinese-xinhua]"
        "(https://github.com/pwxcoo/chinese-xinhua) `data/idiom.json` | MIT | "
        "OpenCC `s2twp` 簡轉繁後去重 |\n"
        "| `polysemous.json` | `lopentu/Chinese-Wordnet-SemCor`（由資料集推導） | MIT | "
        "以 `sense_id` 前 6 碼分 lemma 後計算同讀音義項數 |\n\n"
        "## 已知限制\n\n"
        "- 成語表原始為簡體，OpenCC 轉換可能引入誤差（一簡對多繁的情況）\n"
        "- 多義詞表僅涵蓋 CWN-SemCor 的 113 個目標詞，不是完整的中文多義詞表；\n"
        "  用於 S1 訊號時，未收錄的詞一律計為 0，這是保守方向\n"
        "- 缺委婉語與流行語詞表。S4 目前只有成語，未涵蓋流行語\n",
        encoding="utf-8")
    print(f"\n  {readme}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
