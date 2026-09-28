# 詞表來源

⚠️ **未使用 LLM 生成任何詞表。** 兩份來源皆為既有公開資源。

| 詞表 | 來源 | 授權 | 處理 |
| --- | --- | --- | --- |
| `idioms.json` | [pwxcoo/chinese-xinhua](https://github.com/pwxcoo/chinese-xinhua) `data/idiom.json` | MIT | OpenCC `s2twp` 簡轉繁後去重 |
| `polysemous.json` | `lopentu/Chinese-Wordnet-SemCor`（由資料集推導） | MIT | 以 `sense_id` 前 6 碼分 lemma 後計算同讀音義項數 |

上游授權全文與著作權聲明見根目錄 [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)（CWN-SemCor 上游未附 LICENSE 檔，缺漏項目一併列於該檔）。

## 已知限制

- 成語表原始為簡體，OpenCC 轉換可能引入誤差（一簡對多繁的情況）
- 多義詞表僅涵蓋 CWN-SemCor 的 113 個目標詞，不是完整的中文多義詞表；
  用於 S1 訊號時，未收錄的詞一律計為 0，這是保守方向
- 缺委婉語與流行語詞表。S4 目前只有成語，未涵蓋流行語
