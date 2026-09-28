"""Prompt 與語言技能檔的載入（實作規格書 §A-4、§A-5）。

prompt 改一個字，之前的數據就視為不同批次——因此載入時一律取 SHA-256 並寫進
run 記錄。這是 §5 地雷 5「基礎設施債會偽裝成研究問題」的直接對策：先前
「patch 沒套用卻拿舊結果當新結果」的事故，就是因為 prompt 沒有版本識別。

語言技能檔（skills/<code>.md）每語言一檔，新增語言零程式碼改動（G7）。
"""

from __future__ import annotations

import hashlib
import pathlib
import re
from dataclasses import dataclass
from functools import lru_cache

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROMPT_DIR = ROOT / "prompts"
SKILL_DIR = ROOT / "skills"

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def _split_frontmatter(text: str) -> tuple[dict, str]:
    m = _FRONTMATTER.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, text[m.end():]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Asset:
    name: str
    path: pathlib.Path
    meta: dict
    body: str
    sha256_16: str

    def render(self, **vars_: object) -> str:
        """以 {name} 佔位符填值。缺值即報錯，不靜默留下未填的佔位符。"""
        out = self.body
        missing = []
        for key in re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", out):
            if key not in vars_:
                missing.append(key)
        if missing:
            raise KeyError(
                f"{self.name} 缺少變數：{sorted(set(missing))}。"
                "未填的佔位符會直接進 prompt，導致數據無聲失真。")
        for k, v in vars_.items():
            out = out.replace("{" + k + "}", str(v))
        return out.strip()


def _load(directory: pathlib.Path, name: str, kind: str) -> Asset:
    p = directory / f"{name}.md"
    if not p.exists():
        avail = sorted(x.stem for x in directory.glob("*.md") if not x.stem.startswith("_"))
        raise FileNotFoundError(f"找不到{kind} {name}（{p}）。可用：{', '.join(avail) or '（無）'}")
    raw = p.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(raw)
    return Asset(name=name, path=p, meta=meta, body=body.strip(), sha256_16=_sha(raw))


@lru_cache(maxsize=64)
def prompt(name: str) -> Asset:
    return _load(PROMPT_DIR, name, "prompt")


@lru_cache(maxsize=64)
def skill(lang: str) -> Asset:
    return _load(SKILL_DIR, lang, "語言技能檔")


def available_skills() -> list[str]:
    return sorted(p.stem for p in SKILL_DIR.glob("*.md") if not p.stem.startswith("_"))


def available_prompts() -> list[str]:
    return sorted(p.stem for p in PROMPT_DIR.glob("*.md") if not p.stem.startswith("_"))


def asset_manifest() -> dict[str, str]:
    """所有 prompt 與 skill 的 hash，開跑時寫進 run 記錄的 header。"""
    out: dict[str, str] = {}
    for n in available_prompts():
        out[f"prompt:{n}"] = prompt(n).sha256_16
    for n in available_skills():
        out[f"skill:{n}"] = skill(n).sha256_16
    return out


def clear_cache() -> None:
    """測試用：檔案改動後重新載入。"""
    prompt.cache_clear()
    skill.cache_clear()
