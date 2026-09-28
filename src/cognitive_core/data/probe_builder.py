"""機器翻譯的詞義錯誤基準（DiBiMT / MuCoW 一系的範式）。

    CWN-SemCor 句子 → 翻成英文 → judge 判譯文表達哪個義項 → 比對 CWN gold

⚠️ **本檔於 2026-08-18 全面重寫，U/A/B 脈絡恆等設計已從此處移除。**

原因不是實作 bug，是資料源與設計的需求相反：

  CWN-SemCor 是 WSD 的 gold standard——六位標註者看句子標出正確義項。
  要標得出來，義項就必須**可由該句決定**。實測 60 筆候選中 59 筆（98%）的
  句子只有一個子句，決定義項的線索全在該子句內。因此：
      條件 U（子句單獨）  → 已經決定了
      條件 A（加脈絡）    → 加了也沒差
      條件 B（鎖另一義項）→ 不是鎖定，是推翻
  粗跑測得 U/A 選同一義項 88%，那可能就是正確答案：這些題目本來就不歧義。

  U/A/B 需要「無脈絡時未定」的題目；WSD 資料集提供「有脈絡時已定」的題目。

U/A/B 設計未廢棄，降為**次要實驗**，僅適用於語用歧義（dev-30 的 12 句），
理由見技術設計文件。「為什麼 WSD 資料源不適用於脈絡恆等設計」本身可寫進方法章。

保留的篩選條件（前輪已驗證）：
  - 同 lemma 競爭義項 ≥2（跨 lemma 是同形異音詞，讀出來就消歧）
  - 出現層級排除功能詞（詞層級會誤殺 21 個混合詞）
  - 目標詞在句中恰出現一次
  - gold 必在候選清單中（本專案刻意選 gold 非最高頻的題目）
  - 依 gold 頻率排名分層抽樣（主流層是基準線，不可省略）
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

from .cwn_loader import Corpus, Item, Sense

MAX_CANDIDATE_SENSES = 8


@dataclass
class Probe:
    """一題：一個句子、一個目標詞、一個 gold 義項、一組同 lemma 競爭義項。"""

    id: str
    target_word: str
    target_pos: str
    sentence: str                   # 完整原句，不切子句
    target_offset: tuple[int, int]  # 目標詞在 sentence 中的字元起訖
    gold_sense_id: str
    gold_definition: str
    competing_senses: list[Sense]   # 同 lemma，依語料庫頻率遞減
    gold_rank: int                  # gold 在同 lemma 中的頻率排名
    n_lemma_senses: int
    stratum: str                    # dominant | non_dominant
    source: str = "CWN-SemCor"

    def check_invariants(self) -> list[str]:
        errs: list[str] = []
        lo, hi = self.target_offset
        if not (0 <= lo < hi <= len(self.sentence)):
            errs.append("target_offset 超出句子範圍")
        elif self.sentence[lo:hi] != self.target_word:
            errs.append("target_offset 切出的不是目標詞")
        if self.sentence.count(self.target_word) != 1:
            errs.append(f"目標詞出現 {self.sentence.count(self.target_word)} 次")
        ids = {s.sense_id for s in self.competing_senses}
        if self.gold_sense_id not in ids:
            errs.append("gold 不在候選義項清單中")
        lemmas = {s.sense_id[:6] for s in self.competing_senses}
        if len(lemmas) != 1:
            errs.append(f"候選義項跨 {len(lemmas)} 個 lemma")
        if len(self.competing_senses) < 2:
            errs.append("候選義項少於 2 個")
        return errs

    def to_dict(self) -> dict:
        d = asdict(self)
        d["competing_senses"] = [asdict(s) for s in self.competing_senses]
        d["target_offset"] = list(self.target_offset)
        return d


def build_probe(item: Item, corpus: Corpus) -> Probe | None:
    lemma = item.gold_sense_id[:6]
    ranked = corpus.same_lemma_senses(item.word, lemma)
    if len(ranked) < 2:
        return None
    rank, n_lemma = corpus.sense_rank(item.word, item.gold_sense_id)

    # 取前 N 高頻，但 gold 一律納入——本專案刻意選 gold 非最高頻的題目，
    # 只取前 N 會讓 gold 落在清單外。
    cands = ranked[:MAX_CANDIDATE_SENSES]
    if all(s.sense_id != item.gold_sense_id for s in cands):
        gold = next((s for s in ranked if s.sense_id == item.gold_sense_id), None)
        if gold is None:
            return None
        cands = cands[:MAX_CANDIDATE_SENSES - 1] + [gold]

    sentence = item.sentence
    lo, hi = item.target_offset
    if lo < 0 or sentence[lo:hi] != item.word:
        return None

    return Probe(
        id=f"wsd-{item.word}-{hashlib.sha256(sentence.encode()).hexdigest()[:4]}",
        target_word=item.word, target_pos=item.pos,
        sentence=sentence, target_offset=(lo, hi),
        gold_sense_id=item.gold_sense_id, gold_definition=item.gold_definition,
        competing_senses=cands, gold_rank=rank, n_lemma_senses=n_lemma,
        stratum="dominant" if rank == 1 else "non_dominant")


def select_candidates(corpus: Corpus, *, stratify: tuple[int, int] = (100, 100),
                      seed: int = 20260818) -> tuple[list[Probe], dict]:
    """分層抽樣。`stratify = (n_dominant, n_non_dominant)`。

    ⭐ 主流層是**基準線**，不可省略。若全選非主流，正確率低下無從分辨是
    「模型不理解脈絡」還是「題目全設計成答案剛好不是模型的預設偏好」。
    CHA-Gen 已發表「模型偏好主流解讀」，缺主流層就無法回應這個質疑。

    主指標因此是**兩層之差**，不是單一正確率。
    """
    import random

    pool: list[Probe] = []
    for it in corpus.items:
        if it.is_function_word_occurrence:
            continue
        if not it.target_occurs_once:
            continue
        p = build_probe(it, corpus)
        if p is not None:
            pool.append(p)

    rng = random.Random(seed)
    rng.shuffle(pool)

    n_dom, n_non = stratify
    dom = [p for p in pool if p.stratum == "dominant"][:n_dom]
    non = [p for p in pool if p.stratum == "non_dominant"][:n_non]
    out = dom + non
    rng.shuffle(out)

    stats = {
        "pool_total": len(pool),
        "pool_dominant": sum(1 for p in pool if p.stratum == "dominant"),
        "pool_non_dominant": sum(1 for p in pool if p.stratum == "non_dominant"),
        "requested": {"dominant": n_dom, "non_dominant": n_non},
        "achieved": {"dominant": len(dom), "non_dominant": len(non)},
    }
    return out, stats


def length_bucket(n: int) -> str:
    return "≤10" if n <= 10 else ("11-20" if n <= 20 else
                                  ("21-30" if n <= 30 else ">30"))


def length_distribution(probes: list[Probe]) -> dict[str, int]:
    buckets = {"≤10": 0, "11-20": 0, "21-30": 0, ">30": 0}
    for p in probes:
        buckets[length_bucket(len(p.sentence))] += 1
    return buckets
