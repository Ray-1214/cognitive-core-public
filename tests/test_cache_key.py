"""快取鍵回歸測試（技術設計文件 §5.4）。

起因：2026-08-14 的 S0c 實驗中，同語言重取樣條件下 45/45 譯文完全相同。
追查發現校內端點會快取相同請求——即使 temperature=1.5，重送 4 次仍只得 1 種
輸出。同語言條件因此根本沒有重新取樣過，整個對照失效，結果作廢。

本地快取若漏掉取樣參數會複製同一個陷阱，而且更難察覺（至少端點的行為
還能用 n=k 繞過，本地快取連 n=k 都會被吃掉）。

此測試不需要 API，直接檢查 litellm 的快取鍵生成。
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from litellm.caching.caching import Cache  # noqa: E402

BASE = {
    "model": "openai/mistral-small-4",
    "messages": [{"role": "user", "content": "方便的話明天再說吧"}],
}


@pytest.fixture(scope="module")
def cache(tmp_path_factory):
    return Cache(type="disk", disk_cache_dir=str(tmp_path_factory.mktemp("cache")))


def key(cache, **overrides) -> str:
    return cache.get_cache_key(**{**BASE, **overrides})


@pytest.mark.parametrize("param,a,b", [
    ("temperature", 0.0, 1.5),
    ("temperature", 0.0, 0.7),
    ("n", 1, 4),
    ("seed", 1, 2),
    ("top_p", 1.0, 0.5),
])
def test_sampling_params_change_cache_key(cache, param, a, b):
    """取樣參數不同 → 快取鍵必須不同，否則 n=k 重取樣會靜默失效。"""
    ka, kb = key(cache, **{param: a}), key(cache, **{param: b})
    assert ka != kb, (
        f"{param}={a} 與 {param}={b} 產生相同快取鍵。"
        "這會讓不同取樣設定命中同一份回應，重取樣實驗全部失效——"
        "S0c 初版即因端點端的同類行為而作廢。")


def test_identical_request_hits_same_key(cache):
    """完全相同的請求才可以命中同一份快取。"""
    assert key(cache, temperature=0.0) == key(cache, temperature=0.0)


def test_messages_change_cache_key(cache):
    """prompt 改一個字就必須是不同的鍵。"""
    other = [{"role": "user", "content": "方便的話明天再談吧"}]
    assert key(cache, temperature=0.0) != key(cache, temperature=0.0, messages=other)


def test_model_change_cache_key(cache):
    assert key(cache, temperature=0.0) != key(
        cache, temperature=0.0, model="openai/gpt-oss-120b")


def test_response_format_changes_cache_key(cache):
    """降級階梯的三級走不同 response_format，不可共用快取。"""
    k_none = key(cache, temperature=0.0)
    k_obj = key(cache, temperature=0.0, response_format={"type": "json_object"})
    assert k_none != k_obj
