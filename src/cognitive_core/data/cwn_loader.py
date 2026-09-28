"""CWN-SemCor 載入與展平結構還原（v3 架構書 §P2-D2 2-1）。

**不依賴 CwnGraph**（GPL v3）。已驗證資料集自帶完整義項清單：
每列都帶 `cwn_sense_id` / `cwn_definition`，groupby 即可還原某目標詞的義項全集。
實測抽 5 詞對照皆為 CwnGraph 的子集，差額是語料庫中從未出現的義項，對本專案無用。
詳見 `data/probes/LICENSE.md`。

資料集為 MIT 授權。
"""

from __future__ import annotations

import collections
import functools
import re
from dataclasses import dataclass, field

# `test_sentence` 用 <目標詞> 標位置。實測 284,060/284,060 皆恰一個標記、
# 0 筆與 test_word 不符，故 probe_span 的字元起訖可由此直接取得。
MARK = re.compile(r"<([^<>]+)>")

# 中研院詞類標記中的功能詞前綴。
# ⚠️ 排除必須在**出現層級**：只有「於」的全部出現皆為功能詞，另 21 個詞
#    （上/下/打/用…）是混合的，詞層級排除會誤殺它們的全部出現。
FUNC_PREFIX = ("P", "Nes", "DE", "Caa", "Cab", "Cba", "Cbb", "T", "I", "Neu", "Nep")

DATASET_ID = "lopentu/Chinese-Wordnet-SemCor"


@dataclass(frozen=True)
class Sense:
    sense_id: str
    definition: str
    corpus_count: int = 0

    @property
    def lemma_id(self) -> str:
        """sense_id 前 6 碼 = lemma id。

        已驗證：「中」分為 040046(zhōng)／050076(zhòng)／080112(中國)／080113(台中)，
        「行」5 群、「長」3 群。同 lemma 即同讀音，跨 lemma 的「多義」是同形異音詞，
        讀出來就消歧了，不是本專案要測的現象。
        """
        return self.sense_id[:6]


@dataclass
class Item:
    """一個 (句子, 目標詞) 題目。"""

    sentence_marked: str          # 含 <目標詞> 標記的原句
    word: str
    pos: str
    gold_sense_id: str
    gold_definition: str

    @property
    def sentence(self) -> str:
        return MARK.sub(lambda m: m.group(1), self.sentence_marked)

    @property
    def target_offset(self) -> tuple[int, int]:
        m = MARK.search(self.sentence_marked)
        if not m:
            return (-1, -1)
        return (m.start(), m.start() + len(m.group(1)))

    @property
    def is_function_word_occurrence(self) -> bool:
        """出現層級判斷：看**這一次**出現被標成什麼詞類。"""
        return self.pos.startswith(FUNC_PREFIX)

    @property
    def target_occurs_once(self) -> bool:
        return self.sentence.count(self.word) == 1


@dataclass
class Corpus:
    items: list[Item]
    senses_by_word: dict[str, dict[str, Sense]] = field(default_factory=dict)

    def senses_of(self, word: str) -> list[Sense]:
        return list(self.senses_by_word.get(word, {}).values())

    def same_lemma_senses(self, word: str, lemma_id: str) -> list[Sense]:
        """同 lemma（同讀音）的義項，依語料庫出現頻率遞減。"""
        out = [s for s in self.senses_of(word) if s.lemma_id == lemma_id]
        return sorted(out, key=lambda s: (-s.corpus_count, s.sense_id))

    def sense_rank(self, word: str, sense_id: str) -> tuple[int, int]:
        """(gold 在同 lemma 中的頻率排名, 該 lemma 的義項數)。排名自 1 起。"""
        lemma = sense_id[:6]
        ranked = self.same_lemma_senses(word, lemma)
        for i, s in enumerate(ranked, 1):
            if s.sense_id == sense_id:
                return i, len(ranked)
        return (-1, len(ranked))

    def is_dominant(self, word: str, sense_id: str) -> bool:
        """gold 是否為同 lemma 中的最高頻義項。

        CHA-Gen 發現模型偏好主流解讀：若 gold 就是最高頻義項，
        模型答對可能是猜對而非理解脈絡，該題缺乏鑑別力。
        """
        return self.sense_rank(word, sense_id)[0] == 1


@functools.lru_cache(maxsize=1)
def load_corpus(split: str = "train") -> Corpus:
    """載入並還原展平結構。整個行程載入一次即可。"""
    from datasets import load_dataset

    rows = list(load_dataset(DATASET_ID)[split])

    # 每個 (句子, 詞) 只保留一筆 —— 展平的多列是同一題對不同候選義項的比較
    by_key: dict[tuple[str, str], Item] = {}
    senses: dict[str, dict[str, Sense]] = collections.defaultdict(dict)
    gold_counter: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)

    for r in rows:
        key = (r["test_sentence"], r["test_word"])
        if key not in by_key:
            by_key[key] = Item(
                sentence_marked=r["test_sentence"], word=r["test_word"],
                pos=r["test_pos"], gold_sense_id=r["test_sense_id"],
                gold_definition=r["test_definition"])
        w = r["test_word"]
        for sid, d in ((r["test_sense_id"], r["test_definition"]),
                       (r["cwn_sense_id"], r["cwn_definition"])):
            if sid not in senses[w]:
                senses[w][sid] = Sense(sid, d)

    # 語料庫頻率：每題的 gold 各算一次
    for it in by_key.values():
        gold_counter[it.word][it.gold_sense_id] += 1
    for w, cnt in gold_counter.items():
        for sid, n in cnt.items():
            if sid in senses[w]:
                senses[w][sid] = Sense(sid, senses[w][sid].definition, n)

    return Corpus(items=list(by_key.values()), senses_by_word=dict(senses))
