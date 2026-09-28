# 從零重現驗證

> 快取（`.cache/litellm`）與 `runs/` 已搬離工作目錄後，依序重跑整條管線。

## 指令序列與耗時

| # | 步驟 | 指令 | 耗時 | 結果 |
| :-: | --- | --- | :-: | :-: |
| 1 | 建立探針 | `python scripts/build_probes.py --total 400` | 35s | ✅ |
| 2 | 建立詞表 | `python scripts/build_lexicons.py` | 29s | ✅ |
| 3 | 主基準 400 筆 | `python scripts/run_wsd.py --n 400 --out data/results/wsd_baseline400.md` | 259s | ✅ |
| 4 | judge 驗證 | `python scripts/judge_validate.py _r2` | 21s | ✅ |
| 5 | 訊號值 | `python scripts/run_signals.py --n 400` | 1194s | ✅ |
| 6 | 訊號預先登記 | `python scripts/preregister_signals.py` | 1s | ✅ |
| 7 | AUC 表 | `python scripts/run_signals.py --n 400 --auc --reuse` | 11s | 🔴 exit=2 |
| 8 | Lost-in-the-Middle | `python scripts/lost_in_the_middle.py --n 10` | 23s | ✅ |
| 9 | NONE 分布 | `python scripts/analyze_none.py` | 10s | ✅ |
| 10 | 技術報告 | `python scripts/build_report.py` | 11s | ✅ |

**總耗時 26.6 分鐘**

## 關鍵數字比對

共 52 項，**20 項一致、32 項不一致**。

| 項目 | 原值 | 重現值 | 一致 |
| --- | :-: | :-: | :-: |
| `auc.S1_polysemy` | 0.452 | — | 🔴 |
| `auc.S2_subject_ellipsis` | 0.488 | — | 🔴 |
| `auc.S3_syntactic_complexity` | 0.489 | — | 🔴 |
| `auc.S4_cultural` | 0.498 | — | 🔴 |
| `auc.S5_llm_direct` | 0.493 | — | 🔴 |
| `auc.S6_roundtrip` | 0.527 | — | 🔴 |
| `auc.S7_n_readings` | 0.481 | — | 🔴 |
| `auc.S8_semantic_entropy` | 0.431 | — | 🔴 |
| `auc.未加權總和` | 0.44 | — | 🔴 |
| `auc.純句長基準` | 0.514 | — | 🔴 |
| `baseline.accuracy` | 0.704261 | 0.699248 | 🔴 |
| `baseline.by_stratum.dominant` | 0.723618 | 0.735 | 🔴 |
| `baseline.by_stratum.non_dominant` | 0.685 | 0.663317 | 🔴 |
| `baseline.diff` | 0.0386181 | 0.0716834 | 🔴 |
| `baseline.error_rate` | 0.295739 | 0.300752 | 🔴 |
| `baseline.n` | 400 | 400 | ✅ |
| `baseline.n_judgeable` | 399 | 399 | ✅ |
| `baseline.none` | 1 | 1 | ✅ |
| `baseline.position_effect.acc_gold_a` | 0.743719 | 0.728643 | 🔴 |
| `baseline.position_effect.acc_gold_b` | 0.665 | 0.67 | 🔴 |
| `baseline.position_effect.diff` | 0.0787186 | 0.0586432 | 🔴 |
| `baseline.position_effect.implied_noise` | 0.0393593 | 0.0293216 | 🔴 |
| `baseline.position_effect.p` | 0.0837222 | 0.200552 | 🔴 |
| `baseline.position_effect.se` | 0.0455156 | 0.0458157 | 🔴 |
| `ceilings.S1_polysemy` | 0.9435 | 0.9435 | ✅ |
| `ceilings.S2_subject_ellipsis` | 0.9254 | 0.9254 | ✅ |
| `ceilings.S3_syntactic_complexity` | 0.9787 | 0.9787 | ✅ |
| `ceilings.S4_cultural` | 0.5197 | 0.5197 | ✅ |
| `ceilings.S5_llm_direct` | 0.8901 | 0.9097 | 🔴 |
| `ceilings.S6_roundtrip` | 1 | 1 | ✅ |
| `ceilings.S7_n_readings` | 0.7672 | 0.7645 | 🔴 |
| `ceilings.S8_semantic_entropy` | 0.9024 | 0.9009 | 🔴 |
| `ceilings.raw_length` | 0.9758 | 0.9758 | ✅ |
| `file_sha.judge_validation_r2.json` | 0926d158fbe2ff13 | 2cc90556c0e8d124 | 🔴 |
| `file_sha.lost_in_the_middle.json` | 222ecc7c65b38b79 | 207f012f06181c59 | 🔴 |
| `file_sha.signal_preregistration.json` | aaeb81f7ef604888 | b53de178ad5afa23 | 🔴 |
| `file_sha.signals_all.json` | fe011d039f6a926e | 33c83ef6c025b94a | 🔴 |
| `file_sha.wsd_baseline400.json` | 7a231293a0763b23 | 45cc78d07042dc28 | 🔴 |
| `judge_validation.both_plausible_rate` | 0.15 | 0.15 | ✅ |
| `judge_validation.contaminated` | False | False | ✅ |
| `judge_validation.human_vs_gold` | 0.9 | 0.9 | ✅ |
| `judge_validation.judge_vs_gold` | 0.8 | 0.7 | 🔴 |
| `judge_validation.judge_vs_human` | 0.85 | 0.75 | 🔴 |
| `judge_validation.n` | 20 | 20 | ✅ |
| `lost_in_the_middle.中.baseline` | 0 | 0 | ✅ |
| `lost_in_the_middle.中.memory` | 1 | 1 | ✅ |
| `lost_in_the_middle.尾.baseline` | 1 | 1 | ✅ |
| `lost_in_the_middle.尾.memory` | 1 | 1 | ✅ |
| `lost_in_the_middle.頭.baseline` | 0 | 0 | ✅ |
| `lost_in_the_middle.頭.memory` | 1 | 1 | ✅ |
| `probes_sha` | b152c8802f304fdf | b152c8802f304fdf | ✅ |
| `required_auc` | 0.59 | — | 🔴 |

## 🔴 不一致項目

temperature=0 的管線在空快取重跑後仍應完全一致。不一致代表有非確定性未被控制住，逐項查明原因：

- `auc.S1_polysemy`：0.452 → —　<!-- 原因： -->
- `auc.S2_subject_ellipsis`：0.488 → —　<!-- 原因： -->
- `auc.S3_syntactic_complexity`：0.489 → —　<!-- 原因： -->
- `auc.S4_cultural`：0.498 → —　<!-- 原因： -->
- `auc.S5_llm_direct`：0.493 → —　<!-- 原因： -->
- `auc.S6_roundtrip`：0.527 → —　<!-- 原因： -->
- `auc.S7_n_readings`：0.481 → —　<!-- 原因： -->
- `auc.S8_semantic_entropy`：0.431 → —　<!-- 原因： -->
- `auc.未加權總和`：0.44 → —　<!-- 原因： -->
- `auc.純句長基準`：0.514 → —　<!-- 原因： -->
- `baseline.accuracy`：0.704261 → 0.699248　<!-- 原因： -->
- `baseline.by_stratum.dominant`：0.723618 → 0.735　<!-- 原因： -->
- `baseline.by_stratum.non_dominant`：0.685 → 0.663317　<!-- 原因： -->
- `baseline.diff`：0.0386181 → 0.0716834　<!-- 原因： -->
- `baseline.error_rate`：0.295739 → 0.300752　<!-- 原因： -->
- `baseline.position_effect.acc_gold_a`：0.743719 → 0.728643　<!-- 原因： -->
- `baseline.position_effect.acc_gold_b`：0.665 → 0.67　<!-- 原因： -->
- `baseline.position_effect.diff`：0.0787186 → 0.0586432　<!-- 原因： -->
- `baseline.position_effect.implied_noise`：0.0393593 → 0.0293216　<!-- 原因： -->
- `baseline.position_effect.p`：0.0837222 → 0.200552　<!-- 原因： -->
- `baseline.position_effect.se`：0.0455156 → 0.0458157　<!-- 原因： -->
- `ceilings.S5_llm_direct`：0.8901 → 0.9097　<!-- 原因： -->
- `ceilings.S7_n_readings`：0.7672 → 0.7645　<!-- 原因： -->
- `ceilings.S8_semantic_entropy`：0.9024 → 0.9009　<!-- 原因： -->
- `file_sha.judge_validation_r2.json`：0926d158fbe2ff13 → 2cc90556c0e8d124　<!-- 原因： -->
- `file_sha.lost_in_the_middle.json`：222ecc7c65b38b79 → 207f012f06181c59　<!-- 原因： -->
- `file_sha.signal_preregistration.json`：aaeb81f7ef604888 → b53de178ad5afa23　<!-- 原因： -->
- `file_sha.signals_all.json`：fe011d039f6a926e → 33c83ef6c025b94a　<!-- 原因： -->
- `file_sha.wsd_baseline400.json`：7a231293a0763b23 → 45cc78d07042dc28　<!-- 原因： -->
- `judge_validation.judge_vs_gold`：0.8 → 0.7　<!-- 原因： -->
- `judge_validation.judge_vs_human`：0.85 → 0.75　<!-- 原因： -->
- `required_auc`：0.59 → —　<!-- 原因： -->
