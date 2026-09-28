# 第三方授權聲明（Third-Party Notices）

本專案自有的程式碼與文件依根目錄 [`LICENSE`](LICENSE)（MIT）授權。
下列第三方資料**不**適用該授權，各自依其上游授權散布；上游原文取得日為 2026-09-29。

| 上游 | 本 repo 內的檔案 | 上游授權 | 授權全文與著作權聲明 |
| --- | --- | :-: | --- |
| [pwxcoo/chinese-xinhua](https://github.com/pwxcoo/chinese-xinhua) | `data/lexicons/idioms.json` | MIT | ✅ 取自上游 `LICENSE`，全文見下 |
| [lopentu/Chinese-Wordnet-SemCor](https://huggingface.co/datasets/lopentu/Chinese-Wordnet-SemCor) | `data/probes/wsd_probes.yaml` 及其衍生檔 | MIT（dataset card 宣告） | 標準 MIT 條文見下；⚠️ 上游未載明著作權人 |

---

## 1. chinese-xinhua

- 來源：<https://github.com/pwxcoo/chinese-xinhua> 的 `data/idiom.json`
- 本 repo 使用方式：以 OpenCC `s2twp` 簡轉繁、去重後存為 `data/lexicons/idioms.json`
  （處理方式見 [`data/lexicons/README.md`](data/lexicons/README.md)）
- 授權原文取自：<https://github.com/pwxcoo/chinese-xinhua/blob/master/LICENSE>
  （`master` 分支 commit `fe6d6c2e8baa82187f4c96bbe042e43f96c05666`；
  `LICENSE` blob `8fc37c07672d51ca6d042221786641d4c8fe6d04`）

```text
MIT License

Copyright (c) 2018 PWXCOO

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 2. Chinese Wordnet SemCor（CWN-SemCor）

- 來源：<https://huggingface.co/datasets/lopentu/Chinese-Wordnet-SemCor>
  （revision `65d08163152c87d707feefaade195d71f751d9b1`，上游最後更新 2025-05-05）
- 本 repo 使用方式：抽樣建構探針 `data/probes/wsd_probes.yaml`（含原句、目標詞、CWN 義項編號與定義）；
  由資料集推導 `data/lexicons/polysemous.json`；原句與義項定義亦出現在 `data/cwn/d1_candidates.md`
  與 `data/results/` 下的報表。來源與處理見 [`data/probes/LICENSE.md`](data/probes/LICENSE.md)。

### 上游的授權宣告（原文）

dataset card 的 YAML metadata：

```yaml
license: mit
```

dataset card 的「Licensing Information」一節全文：

```text
MIT
```

### 授權全文

上游 repo 沒有 `LICENSE` 檔，dataset card 只宣告了授權名稱 MIT。以下為標準 MIT 授權條文
（與 [SPDX License List](https://spdx.org/licenses/MIT.html) 的 MIT 文字逐字相同）；
著作權行依上游現況註明，**未自行填入著作權人**。

```text
MIT License

Copyright: 上游未載明著作權人，授權依 Hugging Face dataset card
(https://huggingface.co/datasets/lopentu/Chinese-Wordnet-SemCor, revision 65d0816)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 仍缺的授權資訊

上游 repo 的檔案只有 `.gitattributes`、`README.md` 與 `data/*.parquet`，**沒有 `LICENSE` 檔**；
dataset card 只寫了授權名稱。因此下列資訊無法從上游取得，本檔**不自行補寫**：

- 著作權聲明：著作權人與年份（上游未提供）

補齊方式：向資料集維護者（Hugging Face 組織 `lopentu`）確認著作權人與年份後，替換上方的著作權行。

### 上游資料的來源（依 dataset card，授權未查證）

- 義項體系：[Chinese Wordnet (CWN) 2.0](https://lopentu.github.io/CwnWeb/)——授權待向官方確認
- 例句：主要取自[中央研究院現代漢語平衡語料庫（ASBC）](https://asbc.iis.sinica.edu.tw/)——其使用條款未查證

### 引用

dataset card 要求使用者引用下列論文（BibTeX 取自 dataset card）：

```bibtex
@misc{hsieh2024resolvingregularpolysemynamed,
      title={Resolving Regular Polysemy in Named Entities},
      author={Shu-Kai Hsieh and Yu-Hsiang Tseng and Hsin-Yu Chou and Ching-Wen Yang and Yu-Yun Chang},
      year={2024},
      eprint={2401.09758},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2401.09758},
}
```
