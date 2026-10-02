# Cognitive-Core

**中文高語境歧義的偵測與診斷** — 大專生專題研究計畫

## 計畫資訊

- 國科會大專學生研究計畫「基於代理人工作流與多視角語意驗證之自適應認知框架實作」（115-2813-C-029-063-E）
- 指導教授：劉榮春

---

## 結果

在中文詞網（CWN）標定的**高多義詞**上，LLM 翻譯的**對比詞義錯誤率為 30.1%**
（義項粒度天花板校正後約 **22.6%**，n=400，隨機基準 50%）。

**八個候選訊號沒有一個能預測這些錯誤——包含純句長基準在內。**
十個量測全部落在 0.5 附近，95% CI 全數涵蓋 0.5。
因此**訊號導向的 Router 分流在此任務上不可行**。

| 量測 | AUC | 95% CI |
| --- | :-: | :-: |
| S6 往返保真度 | 0.532 | [0.470, 0.595] |
| S2 主詞省略 | 0.521 | [0.459, 0.583] |
| **純句長基準** | **0.517** | [0.455, 0.579] |
| S4 成語 | 0.498 | 🚫 不可檢定（並列上限 0.520） |
| S3 句法複雜度 | 0.497 | [0.436, 0.559] |
| S7 讀法數 | 0.483 | [0.421, 0.544] |
| S5 LLM 自評 | 0.477 | [0.416, 0.539] |
| **未加權總和** | 0.477 | [0.416, 0.538] |
| S8 語意熵 | 0.465 | [0.404, 0.526] |
| S1 多義詞 | 0.463 | [0.402, 0.524] |

顯著門檻 `required_auc = 0.626`（含實測的 25% 標籤噪音）。Holm 校正後無一顯著。

### 為什麼這個負面結果站得住

**因為純句長也不顯著。** 如果只有自訂訊號失敗，那可能是訊號設計不好；
連句長這種最粗暴的表層特徵都沒有訊號，指向的是**任務本身**：

> 模型的詞義錯誤不是由句子的可觀察屬性決定的。錯誤幾乎隨機散布，
> 與句長、多義程度、成語密度、模型自評、乃至譯文取樣的一致性都無關。

而且我們**知道**那是真的 null 而不是搞砸了，因為：

- **訊號設計在首次計算訊號 AUC 之前凍結**（登記於 2026-08-21，首次 AUC 於 2026-08-22）；
  純句長與標籤的關係在登記前已於長度稽核中看過（[預先登記檔](data/results/signal_preregistration.md)）
- **並列上限分析**事先算出哪些訊號在數學上不可能顯著（S4 上限 0.520 < 門檻）
- **純句長基準**與 DeLong 相關樣本檢定全程並列

RQ2 因此由 RQ1 直接回答，且是**實證得來的否定答案**，不是未完成的工作。
原規劃的 P5（成本–準確度前緣）與 P6（八組對照）據此取消，
[取消決定與理由](docs/Cognitive-Core_完整架構與分階段實作路徑_v3.md)本身寫進報告方法章。

---

## 五分鐘試跑

```bash
git clone <repo>
cd cognitive-core
./run_demo.sh          # Windows: run_demo.bat
```

→ 瀏覽器開啟，點側邊欄任一展示句，右欄出現決策時間軸。

**不需要 API key。** 沒有 key 時自動走離線模式，播放 15 筆預錄結果
（五個展示句 × 三個 profile）。要即時執行任意句子才需要 key，見
[`.env.example`](.env.example)。

離線模式會在頁面頂端明示「顯示預錄結果」，輸入框停用，
側邊欄顯示錄製時間與 commit——**不會假裝是即時執行的**。

腳本會自己建 `.venv` 並安裝 `pip install -e ".[app]"`；
偵測到環境已就緒就跳過安裝。

> **所有實驗結果檔都已在版控中，不需要執行任何東西即可閱讀**——見下方
> 「看結果」。跑 demo 是為了看**流程**長什麼樣，不是為了產生結果。

---

## 五項方法學貢獻

| | 內容 | 檔案 |
| :-: | --- | --- |
| 1 | **AUC 的並列上限**——離散化訊號存在與判別力無關的硬上限 `1 − 0.5 × P(隨機兩題同值)`；上限低於門檻者「不可檢定」，與「不顯著」意義完全不同 | [`signal_preregistration.md`](data/results/signal_preregistration.md) |
| 2 | **AI 協作研究的 prompt 洩題管道**——撰寫 prompt 的助理會從它處理過的資料中取 few-shot 範例。三次事件、四種載體，關鍵性質是**從結果不可見** | [`prompt_contamination_incidents.md`](data/results/prompt_contamination_incidents.md) |
| 3 | **標籤噪音的分解**——位置效應是總噪音的**成分**不是加項，相加會重複計算；並把噪音餵回 `required_auc` | [`noise.py`](src/cognitive_core/eval/noise.py) |
| 4 | **把研究誠信寫進 CI**——AUC 閘門要求一份未污染的 judge 驗證；測試守的是**開閘的理由**，調低門檻或移除污染標記都會讓測試立刻失敗 | [`test_gate.py`](tests/test_gate.py) |
| 5 | ⭐ **`judge_cross` 在部署層被架空**——用不同模型當 judge，不代表 judge 是獨立的 | [`judge_cross_pitfall.md`](docs/judge_cross_pitfall.md) |

第 5 項值得單獨看：一個用來防止球員兼裁判的機制，通過了所有測試，
卻在部署層面失效——校內端點的 `mistral-small-4` 與 `gpt-oss-120b`
在三個不同的 `max_tokens` 下 **tokenizer 截斷點逐字相同**，
極可能由同一後端提供服務。原本的檢查比較的是 provider/model **字串**。

`tests/test_cross_check.py` 目前有**一支刻意保留的紅燈**，
docstring 寫明「這支測試的紅色本身就是研究發現的一部分」。

---

## 怎麼跑

### 看結果（不需要 API key）

**所有實驗結果檔都已進版控，不需要執行任何東西即可閱讀：**

| 檔案 | 內容 |
| --- | --- |
| [`data/results/wsd_baseline400.md`](data/results/wsd_baseline400.md) | 主結果完整報表 |
| [`data/results/signals_all.md`](data/results/signals_all.md) | 訊號分布、並列上限、**AUC 表** |
| [`data/results/judge_validation_r2.md`](data/results/judge_validation_r2.md) | judge 人工驗證 |
| [`data/results/reproduction_check.md`](data/results/reproduction_check.md) | 從零重現的逐項比對 |
| [`docs/技術報告.md`](docs/技術報告.md) | 技術報告（骨架 + 數據） |

### 環境安裝（conda）

```bash
conda create -n cognitive-core -c conda-forge -y python=3.12 pip \
        numpy matplotlib pyyaml pytest python-dotenv
conda activate cognitive-core
pip install -e ".[dev,app]"
```

conda 負責 Python 與科學運算基底，其餘走 pip——`litellm`、`langgraph`、`chromadb`、
`streamlit` 在 conda-forge 上沒有可靠的版本，混裝反而容易解不出來。
要精確重現某次執行的環境，用釘死版本的
[`requirements.txt`](requirements.txt)（實測凍結於 Python 3.12.14 / win-64）。

> #### ⚠️ PowerShell 裡 `conda activate` 可能安靜地無作用
>
> `conda activate` 要改得動當前 shell 的 PATH，得靠 `$PROFILE` 裡的 hook 定義出
> 一個 **PowerShell 函式**。沒跑過 `conda init powershell` 的話 `conda` 只解析到
> `conda.bat`／`conda.exe`——批次檔跑在**子行程**，改完 PATH 隨子行程一起消失，
> 父 shell 毫無感覺。於是它**不報錯、也不生效**，接著 `streamlit`、`pytest`
> 全是 `CommandNotFoundException`。
>
> **提示字元有沒有 `(cognitive-core)` 前綴，就是活化成功與否的憑據。**
>
> 本專案附了一支繞開整個 profile 機制的腳本，開頭那個點是 dot-source、不能省：
>
> ```powershell
> . .\scripts\activate.ps1
> ```
>
> 它只對當前 session 載入 conda hook，並順手驗證 BLAS 真的活著（見下一則警告）。
>
> 想要一勞永逸就跑 `conda init powershell` 再重開 shell。
> 但**它在開了 Defender「受控資料夾存取」的機器上會失敗**：該功能預設保護
> Documents，會擋掉 conda 寫 `%userprofile%\Documents\WindowsPowerShell\profile.ps1`,
> 而 conda 把這個攔截**誤報成 `needs sudo`**——用系統管理員身分重跑一樣失敗，
> 因為根本不是權限問題。要確認是不是這個原因：
>
> ```powershell
> Get-MpPreference | Select-Object EnableControlledFolderAccess   # 1 = 開啟
> Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Windows Defender/Operational'; Id=1123} -MaxEvents 5
> ```
>
> 事件 1123 會直接指名是哪個執行檔被擋。
> 把 `python.exe` 加進 CFA 放行清單可以解，但那等於替**任何** Python 腳本
> 打開防勒索軟體保護的破口，不建議；用上面的 `activate.ps1` 沒有這個代價。
>
> ℹ️ `scripts/activate.ps1` **存成帶 BOM 的 UTF-8**。Windows PowerShell 5.1
> 讀 `.ps1` 時沒 BOM 就會套系統 ANSI 碼頁（繁中機器是 cp950），
> 中文註解會被解成亂碼並炸出 parser error。編輯它的工具若會去掉 BOM，記得補回去。

> #### ⚠️ Windows：一定要 `conda activate` 之後再跑，別直接指到 exe
>
> conda-forge 的 numpy 不自帶 BLAS，而是延遲載入 `%CONDA_PREFIX%\Library\bin`
> 底下的 MKL；那個目錄**只有 activate 之後才在 PATH 上**。
> 若直接呼叫 `envs\cognitive-core\python.exe`，程式會在第一個進到 BLAS 的呼叫
> ——例如 `numpy.cov`，`eval/auc.py` 的 `delong_test()` 就會用到——
> **整個行程當掉**，錯誤碼 `0xc06d007f`（DLL 找不到）。
> 那是 OS 層的 fatal exception 不是 Python 例外，`try/except` 攔不到，
> 症狀是 pytest 跑到一半無訊息中斷、Streamlit 顯示連線中斷而查不出原因。
> 用 `Scripts\streamlit.exe`、`Scripts\pytest.exe` 的絕對路徑繞過活化也一樣會踩到。
> VS Code 請選這個 conda 環境當直譯器，不要用絕對路徑指到 `python.exe`。

安裝內容分四組，定義在 [`pyproject.toml`](pyproject.toml)：

| 組 | 用途 | 內容 |
| --- | --- | --- |
| core | 跑實驗與產報表 | litellm[caching] · langgraph · pydantic · pyyaml · python-dotenv · numpy · datasets · huggingface-hub · opencc |
| `dev` | 測試 · 作圖 · 報告 | pytest · matplotlib · python-pptx |
| `app` | Streamlit demo 與記憶模組（RQ3） | streamlit · chromadb |
| `ppl` | dev30 階段的本地 PPL 基準 | torch · transformers |

`litellm` 的 `[caching]` extra 不能省——它帶的 `diskcache` 是快取層的實作，
少了它 `tests/test_cache_key.py` 會整組 error。

`ppl` 只有 `scripts/ppl_baseline.py` 與 `ppl_variants.py` 需要，
**不在 `reproduce.py` 主流程內**，重現主結果不必裝。它約 2.5 GB，故獨立成檔：

```bash
pip install -r requirements-ppl.txt \
        --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple
```

**`CwnGraph` 不在任何一組裡，而且是刻意的**——`CwnGraph` 套件是 GPL v3，
裝了會有授權傳染問題；CWN 2.0 本體的授權則待向官方確認（見下方「資料與授權」）。
`scripts/d1_verify_cwn.py`、`d1_verify_cwn2.py`、`d15_verify_criteria.py`
裡的 `CwnGraph` 匯入都包在 `try/except` 中——那三支正是當初**用來確認不需要它**的驗證腳本；
缺它只會少印一段對照表，不影響任何結果。

### 重現實驗（需要 API key）

```bash
conda activate cognitive-core   # PowerShell 沒 init 過的話：. .\scripts\activate.ps1
cp .env.example .env            # 填入你的 key

python scripts/build_probes.py --total 400
python scripts/build_lexicons.py          # 缺檔時自動下載成語表
python scripts/run_wsd.py --n 400 --out data/results/wsd_baseline400.md
python scripts/judge_validate.py _r2
python scripts/run_signals.py --n 400
python scripts/preregister_signals.py
python scripts/run_signals.py --n 400 --auc --reuse
python scripts/lost_in_the_middle.py --n 10
python scripts/build_report.py
```

**成本（實測，空快取從零跑完）：26.6 分鐘 / 2,841 次 API 呼叫 / 4,007,818 tokens。**

一鍵版本：`python scripts/reproduce.py`，比對用 `--compare`。

可重現性封包（含 config、prompts、資料、結果、commit、套件版本、端點指紋；
**不含金鑰與快取**）：

```bash
python -m cognitive_core.cli export --out repro.zip
```

（`pip install -e .` 後也可用 `cognitive-core export`，
若 Windows 的 Scripts 目錄不在 PATH 上，用上面的 `python -m` 形式。）

### ⚠️ 端點漂移警語

**數字不是位元級可重現的。** 本專案的 API 端點在 8/21 與 8/22 之間
換過模型，導致 **186/400 的譯文改變**——而所有呼叫都是 `temperature=0`。

那不是 per-call 隨機性（20 句 × 3 次、停用快取，100% 相同），
是**時間漂移**，而且**無法從 API 察覺**
（無 `system_fingerprint`，`/models` 的 `created` 是固定佔位值）。

```bash
python scripts/endpoint_fingerprint.py            # 比對既有記錄
python scripts/endpoint_fingerprint.py --record   # 建立基準
```

指紋變了就代表端點變了，受影響的實驗需要重跑。

**可重現性的正確主張是「結論穩健」而非「數字相同」**：
兩次執行的錯誤率 29.6% → 30.1%、兩層之差 +3.9 → +7.2pp（兩者 CI 皆涵蓋 0）、
位置效應 p 0.084 → 0.201（皆不顯著）。沒有任何結論改變。

### Demo

```bash
./run_demo.sh          # Windows: run_demo.bat
# 已有環境時： streamlit run app/streamlit_app.py
```

沒有 `ITHU_API_KEY` 時自動走**離線模式**，播放
[`data/demo/recorded.json`](data/demo/recorded.json) 的 15 筆預錄結果
（`python scripts/record_demo.py` 可重錄）。

右欄是**可稽核的決策時間軸**——結構化決策記錄，不含模型的原始推理文字
（由 `timeline.assert_no_cot()` 強制檢查）。
訊號值標為**診斷資訊**並附上 AUC 實測結果，介面**不呈現快慢通道分流**
——那個分流實測無效，展示它會誤導觀眾。

---

## 限制

- **n=400，CI 仍寬。** 多數結論待更大樣本
- **單一翻譯模型**（`mistral-small-4`）。結果不保證推廣到其他 MT 系統
- 🔴 **judge 的獨立性未通過驗證**——見上方第 5 項。self-preference bias 無法排除
- 🔴 **judge 獨立性的敏感度檢查未完成**——換 Gemini 重判的嘗試因外部 API
  配額限制中止，兩次分別只得 10 筆與 1 筆可比題目
  （[過程記錄](data/results/judge_sensitivity_status.md)）
- **judge 一致率 75%（CI [53, 89]，n=20）。** AUC 閘門開啟只代表
  **標籤優於隨機**，不代表標籤可靠。該噪音已計入 `required_auc = 0.626`
- **義項粒度天花板估計僅 n=20**（15% 的題目「兩個都說得通」，CI [5%, 36%]）
- **RQ3 有天花板效應**——記憶模組在三個位置皆 100% 召回，
  30 則訊息中只有 1 則相關，任務對檢索而言不難
- **`dev-lex-09` 的既有結果不可採用**（曾被 `reflect.md` v2 的 few-shot 曝光）

---

## 資料與授權

| 來源 | 授權 | 用途 |
| --- | :-: | --- |
| [`lopentu/Chinese-Wordnet-SemCor`](https://huggingface.co/datasets/lopentu/Chinese-Wordnet-SemCor) | MIT | 探針（21,098 筆 → 池 17,967 → 抽 400） |
| [`pwxcoo/chinese-xinhua`](https://github.com/pwxcoo/chinese-xinhua) | MIT | S4 成語表（30,813 條，OpenCC `s2twp`） |
| `CwnGraph` 套件 | GPL v3 | **刻意不使用**，避免授權傳染 |
| CWN 2.0 本體 | 待向[官方](https://lopentu.github.io/CwnWeb/)確認 | 未直接使用；義項定義經由 CWN-SemCor 取得 |

**未使用 LLM 生成任何詞表。** 上游授權全文與著作權聲明見 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

Wu et al. 2025 的 `task2_test.tsv`（僅用於長度稽核）沒有授權聲明，**不隨本 repo 散布**，需自行向原作者取得（[`ictup/LLM-Chinese-Textual-Disambiguation`](https://github.com/ictup/LLM-Chinese-Textual-Disambiguation)）並放到 `data/external/wu2025_task2_test.tsv`；缺檔時 `scripts/external_length_audit.py` 會跳過並提示，[`length_audit_summary.md`](data/external/length_audit_summary.md) 保留的是既有統計結果、不含原句。

---

## 專案結構

```
src/cognitive_core/
  eval/        wsd（基準）· auc · noise · gate（AUC 閘門）· cross_check
  data/        cwn_loader · probe_builder · length_audit
  router/      signals（S1–S8）
  memory/      ChromaDB + 滾動摘要（向量庫是長期儲存，摘要只管脈絡）
  timeline.py  決策時間軸 + CoT 洩漏防護
scripts/       建資料 · 跑實驗 · 重現驗證 · 產報告
app/           Streamlit demo
docs/          架構書 · 技術報告 · judge_cross 陷阱 · 交接文件
```

測試共 **2,946 項，2,945 通過**；1 項為刻意保留的已知失敗
`tests/test_cross_check.py::test_current_deployment_fails_behavioural_cross_check`
（`judge_cross` 行為檢查，見上方第 5 項）。

---

*大專生專題研究計畫。所有數字自結果檔讀取，重跑實驗後執行
`python scripts/build_report.py` 即可更新。*
