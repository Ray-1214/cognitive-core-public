"""CLI 的測試（P1 測試提示詞第 2 條）。

**不呼叫真實 API**：用 monkeypatch 把 cli 模組裡的 Client 換成 FakeClient。
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cognitive_core import cli  # noqa: E402
from tests.conftest import FakeClient  # noqa: E402


@pytest.fixture
def patched(monkeypatch):
    """把 cli.Client 換掉，並記錄實際被建立的 FakeClient。"""
    created: list[FakeClient] = []

    def factory(*a, **kw):
        c = FakeClient(run=kw.get("run"), profile=kw.get("profile"))
        created.append(c)
        return c

    monkeypatch.setattr(cli, "Client", factory)
    return created


@pytest.fixture
def tiny_dataset(tmp_path):
    p = tmp_path / "tiny.yaml"
    p.write_text(yaml.safe_dump({"items": [
        {"id": "t-01", "text": "他昨天走了"},
        {"id": "t-02", "text": "那家店關門了"},
        {"id": "t-03", "text": "會議改到下週三"},
    ]}, allow_unicode=True), encoding="utf-8")
    return p


# ── run ──

def test_run_json_is_parseable(patched, capsys):
    rc = cli.main(["run", "--text", "他昨天走了", "--json"])
    assert rc == 0
    obj = json.loads(capsys.readouterr().out)
    for k in ["source_text", "timeline", "final", "translations"]:
        assert k in obj, f"run --json 缺欄位 {k}"
    assert obj["source_text"] == "他昨天走了"


def test_run_human_output_has_timeline(patched, capsys):
    rc = cli.main(["run", "--text", "他昨天走了"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "原文：他昨天走了" in out
    assert "Router" in out and "錨點建構" in out
    assert "成本：" in out
    assert "格式違規" in out          # 本輪 §b 要求的那一行


def test_run_json_has_no_reasoning_content(patched, capsys):
    cli.main(["run", "--text", "他昨天走了", "--json"])
    assert "reasoning_content" not in capsys.readouterr().out


# ── batch ──

def test_batch_yes_skips_confirmation(patched, tiny_dataset, tmp_path, monkeypatch):
    """--yes 跳過成本確認。若沒跳過，input() 會被呼叫而測試失敗。"""
    def boom(*a, **kw):
        raise AssertionError("--yes 未生效，仍要求確認")
    monkeypatch.setattr("builtins.input", boom)
    out = tmp_path / "b.jsonl"
    rc = cli.main(["batch", "--dataset", str(tiny_dataset), "--out", str(out), "--yes"])
    assert rc == 0
    assert out.exists()
    assert len(out.read_text(encoding="utf-8").strip().splitlines()) == 3


def test_batch_prints_cost_estimate_marked_as_estimate(patched, tiny_dataset,
                                                       tmp_path, capsys):
    cli.main(["batch", "--dataset", str(tiny_dataset),
              "--out", str(tmp_path / "b.jsonl"), "--yes"])
    out = capsys.readouterr().out
    assert "預估" in out
    assert "估計值不是實測" in out, "成本預估必須明確標示為估計值"
    assert "估計" in out and "實際" in out, "跑完須印估計 vs 實際對照"


def test_batch_resume_skips_completed(patched, tiny_dataset, tmp_path):
    """斷點續跑：已完成項目不重複呼叫。"""
    out = tmp_path / "b.jsonl"
    cli.main(["batch", "--dataset", str(tiny_dataset), "--out", str(out), "--yes"])
    n_first = len(patched)
    calls_first = sum(len(c.calls) for c in patched)

    cli.main(["batch", "--dataset", str(tiny_dataset), "--out", str(out), "--yes"])
    calls_second = sum(len(c.calls) for c in patched[n_first:])
    assert calls_second == 0, f"續跑仍呼叫了 {calls_second} 次，斷點未生效"
    assert len(out.read_text(encoding="utf-8").strip().splitlines()) == 3


def test_batch_no_resume_reruns(patched, tiny_dataset, tmp_path):
    out = tmp_path / "b.jsonl"
    cli.main(["batch", "--dataset", str(tiny_dataset), "--out", str(out), "--yes"])
    n_first = len(patched)
    cli.main(["batch", "--dataset", str(tiny_dataset), "--out", str(out),
              "--yes", "--no-resume"])
    assert sum(len(c.calls) for c in patched[n_first:]) > 0


def test_batch_writes_incrementally(patched, tiny_dataset, tmp_path):
    """逐筆寫入：檔案在跑完前就有內容，中斷不會全丟。"""
    out = tmp_path / "b.jsonl"
    cli.main(["batch", "--dataset", str(tiny_dataset), "--out", str(out), "--yes"])
    for line in out.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        assert {"id", "profile", "text", "ok"} <= set(rec)


def test_batch_failure_recorded_not_fatal(monkeypatch, tiny_dataset, tmp_path):
    """單筆失敗不應中斷整批，且失敗原因要留痕。"""
    def factory(*a, **kw):
        return FakeClient(run=kw.get("run"), fail_on={"reflect"})
    monkeypatch.setattr(cli, "Client", factory)
    out = tmp_path / "b.jsonl"
    rc = cli.main(["batch", "--dataset", str(tiny_dataset), "--out", str(out),
                   "--yes", "--retries", "0"])
    lines = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 3, "失敗筆數未寫入，無從診斷"
    assert all(not r["ok"] for r in lines)
    assert all("error" in r for r in lines)
    assert rc == 1


# ── golden ──

def test_golden_does_not_exit_on_failure(monkeypatch, capsys):
    """golden 是觀測工具：單句失敗不整體退出，永遠回 0。"""
    def factory(*a, **kw):
        return FakeClient(run=kw.get("run"), fail_on={"reflect"})
    monkeypatch.setattr(cli, "Client", factory)
    rc = cli.main(["golden", "--yes"])
    assert rc == 0, "golden 不得因失敗而非零退出"
    assert "不符預期" in capsys.readouterr().out


def test_golden_reports_expectation_mismatches(patched, capsys):
    """FakeClient 一律回 2 個讀法，負例（max_readings=1）必被標為不符。"""
    cli.main(["golden", "--yes"])
    out = capsys.readouterr().out
    assert "過度生成" in out
    assert "觀測工具，不視為失敗" in out


def test_golden_cases_exclude_dev30(patched):
    """黃金案例不得使用 dev-30 的句子（地雷 3）。"""
    root = pathlib.Path(__file__).resolve().parents[1]
    golden = yaml.safe_load((root / "data" / "golden" / "cases.yaml")
                            .read_text(encoding="utf-8"))
    dev = yaml.safe_load((root / "data" / "dev30" / "sentences.yaml")
                         .read_text(encoding="utf-8"))
    g = {c["text"] for c in golden["cases"]}
    d = {i["text"] for i in dev["items"]}
    d |= {i["minimal_pair"]["text"] for i in dev["items"] if i.get("minimal_pair")}
    assert not (g & d), f"黃金案例與 dev-30 重疊：{g & d}"


# ── adaptive-n ──

def test_adaptive_n_respects_config_cap(capsys):
    rc = cli.main(["adaptive-n", "--profile", "same_en"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "建議 n" in out and "依據" in out
