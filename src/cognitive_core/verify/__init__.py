"""演算法 1：多視角語意驗證（技術設計文件 §4.2、實作規格書 §A-2）。

**四種 profile 是同一條程式碼路徑的不同設定，不是四份實作。**
mode 只有三種，profile 是 mode + 參數的組合：

    cross_lingual   K 種語言各一個譯本      → 三角測量（計畫書主張）
    same_language   一種語言取 n 個樣本     → 同語言重取樣對照（虛無假設）
    single_probe    一種語言一個譯本        → E1-d 消融、便宜偵測器

§4.2.1 偵測／診斷分離：
    detector_score  單探針往返保真度（與原文比）—— 便宜，每句都跑
    consistency     樣本間一致性 —— 僅作收斂診斷，**不得當勝負依據**（地雷 2）
    differences     IdentifyDiff —— 昂貴，只在慢速通道跑，單探針給不出這個
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

import yaml

from ..assets import prompt
from ..llm import Client
from ..models import SemanticAnchor, Translation, VerifyReport
from ..similarity import mean_pairwise, min_vs_source
from ..translate import back_translate, translate_from_anchor

ROOT = pathlib.Path(__file__).resolve().parents[3]
VERIFY_YAML = ROOT / "config" / "verify.yaml"

MODES = ("cross_lingual", "same_language", "single_probe")


@dataclass(frozen=True)
class VerifyProfile:
    name: str
    mode: str
    languages: tuple[str, ...]
    n: int = 1
    temperature: float | None = 0.0

    @property
    def can_diagnose(self) -> bool:
        """單探針只有一個回譯，給不出差異點——反思需要的正是差異點。"""
        return self.mode != "single_probe"


class VerifyConfig:
    def __init__(self, path: pathlib.Path | None = None):
        self.raw = yaml.safe_load((path or VERIFY_YAML).read_text(encoding="utf-8"))

    @property
    def thresholds(self) -> dict:
        return self.raw.get("thresholds", {})

    @property
    def holdout_languages(self) -> list[str]:
        return list(self.raw.get("holdout_languages", []))

    def profile(self, name: str) -> VerifyProfile:
        p = self.raw.get("profiles", {}).get(name)
        if p is None:
            avail = ", ".join(sorted(self.raw.get("profiles", {})))
            raise KeyError(f"未知的 verify profile：{name}。可用：{avail}")
        mode = p["mode"]
        if mode not in MODES:
            raise ValueError(f"未知 mode：{mode}")
        langs = tuple(p["languages"]) if mode == "cross_lingual" else (p["language"],)
        return VerifyProfile(name=name, mode=mode, languages=langs,
                             n=int(p.get("n", 1)),
                             temperature=p.get("temperature", 0.0))

    def profile_names(self) -> list[str]:
        return sorted(self.raw.get("profiles", {}))

    @property
    def detector_profile(self) -> str:
        return self.raw.get("detector", "single_probe")

    @property
    def diagnoser_profile(self) -> str:
        return self.raw.get("diagnoser", "cross_en_ja")


class Verifier:
    def __init__(self, client: Client, cfg: VerifyConfig | None = None):
        self.client = client
        self.cfg = cfg or VerifyConfig()

    # ── 單一路徑，三種 mode 的差異只在「怎麼取得譯本」 ──

    def gather(self, anchor: SemanticAnchor, profile: str) -> list[Translation]:
        """取得譯本。與 evaluate 分離，讓 graph 能有獨立節點（事件粒度）。"""
        return self._gather(anchor, self.cfg.profile(profile))

    def _gather(self, anchor: SemanticAnchor, p: VerifyProfile) -> list[Translation]:
        if p.mode == "cross_lingual":
            out: list[Translation] = []
            for lang in p.languages:
                out += translate_from_anchor(self.client, anchor, lang,
                                             n=1, temperature=p.temperature)
            return out
        if p.mode == "same_language":
            # 單一請求取 n 個樣本。重複呼叫會撞端點快取，等於沒有重取樣。
            return translate_from_anchor(self.client, anchor, p.languages[0],
                                         n=p.n, temperature=p.temperature)
        return translate_from_anchor(self.client, anchor, p.languages[0],
                                     n=1, temperature=p.temperature)

    def run(self, anchor: SemanticAnchor, profile: str = "cross_en_ja", *,
            diagnose: bool | None = None,
            consistency_threshold: float | None = None,
            detector_threshold: float | None = None) -> VerifyReport:
        """執行演算法 1。

        兩個閾值可覆寫：Phase C 掃 ROC 時需要在同一批譯本上變動閾值，
        重跑翻譯只為了換閾值是浪費，且會因非確定性引入額外變異。
        """
        p = self.cfg.profile(profile)
        translations = self._gather(anchor, p)
        return self.evaluate(anchor, translations, profile, diagnose=diagnose,
                             consistency_threshold=consistency_threshold,
                             detector_threshold=detector_threshold)

    def evaluate(self, anchor: SemanticAnchor, translations: list[Translation],
                 profile: str = "cross_en_ja", *, diagnose: bool | None = None,
                 consistency_threshold: float | None = None,
                 detector_threshold: float | None = None) -> VerifyReport:
        """對既有譯本做回譯、量測與診斷。譯本由 gather() 或呼叫端提供。"""
        p = self.cfg.profile(profile)
        n_readings = anchor.uncertainty.n_readings
        if not translations:
            return VerifyReport(profile=p.name, mode=p.mode, languages=list(p.languages),
                                passed=False, n_readings=n_readings,
                                differences=["翻譯階段失敗，無可用譯本"])

        backs = [back_translate(self.client, t) for t in translations]
        labels = [f"{t.language}#{i + 1}" if p.mode == "same_language" else t.language
                  for i, t in enumerate(translations)]
        back_map = dict(zip(labels, backs))

        vecs = self.client.embed([anchor.source_text, *backs])
        src_vec, back_vecs = vecs[0], vecs[1:]

        detector = min_vs_source(src_vec, back_vecs)
        consistency = mean_pairwise(back_vecs)          # None 當只有一個譯本

        th = self.cfg.thresholds
        det_th = (detector_threshold if detector_threshold is not None
                  else float(th.get("detector_slow_path", 0.85)))
        cons_th = (consistency_threshold if consistency_threshold is not None
                   else float(th.get("consistency_pass", 0.75)))
        if consistency is None:
            passed = (detector or 0.0) >= det_th
        else:
            passed = consistency >= cons_th

        report = VerifyReport(profile=p.name, mode=p.mode, languages=list(p.languages),
                              back_translations=back_map,
                              consistency=consistency, detector_score=detector,
                              passed=passed, n_readings=n_readings,
                              n_samples=len(translations))

        want_diag = p.can_diagnose if diagnose is None else diagnose
        if want_diag and not passed and len(backs) >= 2:
            report.differences = self.identify_diff(anchor.source_text, back_map)

        if self.client.run is not None:
            self.client.run.record_event("verify", {
                "profile": p.name, "mode": p.mode, "languages": list(p.languages),
                "n_samples": report.n_samples, "n_readings": report.n_readings,
                "detector_score": detector, "consistency": consistency,
                "passed": passed, "n_differences": report.n_differences,
            })
        return report

    # ── IdentifyDiff：強制列舉，不是是／否判斷 ──

    def identify_diff(self, source_text: str, back_map: dict[str, str]) -> list[str]:
        block = "\n".join(f"{k}：{v}" for k, v in back_map.items())
        msgs = [{"role": "user",
                 "content": prompt("verify").render(source_text=source_text,
                                                    back_translations=block)}]
        try:
            raw = self.client.text("verify", msgs, temperature=0.0, max_tokens=600)
        except Exception:  # noqa: BLE001
            return []
        if "無差異" in raw:
            return []
        out = []
        for line in raw.splitlines():
            s = line.strip().lstrip("-*• ").strip()
            if s and len(s) > 3:
                out.append(s)
        return out[:5]


__all__ = ["VerifyConfig", "VerifyProfile", "Verifier", "MODES"]
