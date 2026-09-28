"""驗證配置的結構測試（實作規格書 §A-2）。

重點：四種 profile 必須是同一條路徑的不同設定。
測試不呼叫 API——只確認 config 解析與 mode 分派正確。
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core.verify import MODES, VerifyConfig  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    return VerifyConfig()


def test_required_profiles_exist(cfg):
    """§A-2 指定的四種必須都在。"""
    for name in ["cross_en_ja", "cross_en_de", "same_en", "single_ja"]:
        assert name in cfg.profile_names(), f"缺少 profile {name}"


def test_every_profile_uses_a_known_mode(cfg):
    for name in cfg.profile_names():
        assert cfg.profile(name).mode in MODES


def test_cross_lingual_has_multiple_languages(cfg):
    p = cfg.profile("cross_en_ja")
    assert p.mode == "cross_lingual"
    assert p.languages == ("en", "ja")


def test_same_language_has_single_language_and_n_gt_1(cfg):
    """同語言重取樣必須 n>1，否則它不是重取樣，只是單探針。"""
    p = cfg.profile("same_en")
    assert p.mode == "same_language"
    assert len(p.languages) == 1
    assert p.n > 1, "same_language 的 n 必須大於 1"
    assert p.temperature and p.temperature > 0, "重取樣需要 temperature>0"


def test_single_probe_cannot_diagnose(cfg):
    """單探針只有一個回譯，給不出差異點——反思需要的正是差異點（§4.2.1）。"""
    assert cfg.profile("single_ja").can_diagnose is False
    assert cfg.profile("cross_en_ja").can_diagnose is True
    assert cfg.profile("same_en").can_diagnose is True


def test_unknown_profile_lists_available(cfg):
    with pytest.raises(KeyError) as e:
        cfg.profile("no_such_profile")
    assert "可用" in str(e.value)


def test_detector_and_diagnoser_point_to_real_profiles(cfg):
    """§4.2.1 偵測／診斷分離：兩者都必須指向存在的 profile。"""
    names = cfg.profile_names()
    assert cfg.diagnoser_profile in names
    # detector 可以是 mode 名稱或 profile 名稱，兩者皆須可解析
    assert cfg.detector_profile in names or cfg.detector_profile in MODES


def test_holdout_language_not_used_by_default_diagnoser(cfg):
    """留出語言不得進反思迴圈，否則一致性量測變成循環論證（地雷 2）。"""
    holdout = set(cfg.holdout_languages)
    assert holdout, "至少要有一個留出語言"
    diag = cfg.profile(cfg.diagnoser_profile)
    assert not (set(diag.languages) & holdout), (
        f"診斷 profile {diag.name} 用到了留出語言 {holdout}，"
        "該語言就不再是獨立的量測基準")


def test_thresholds_present_and_sane(cfg):
    th = cfg.thresholds
    for k in ["consistency_pass", "detector_slow_path", "max_revisions"]:
        assert k in th, f"缺少閾值 {k}"
    assert 0 < th["consistency_pass"] <= 1
    assert 0 < th["detector_slow_path"] <= 1
    assert th["max_revisions"] >= 1
