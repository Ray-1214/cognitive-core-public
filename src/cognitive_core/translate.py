"""翻譯與回譯（技術設計文件 §4.2）。

核心約束：**翻譯一律從錨點出發，不從上一輪譯文出發**。
鏈式翻譯的誤差是 O(n) 累積，錨點式是 O(1) 常數。
"""

from __future__ import annotations

from .assets import prompt, skill
from .llm import Client
from .models import SemanticAnchor, Translation


def language_name(code: str) -> str:
    """語言的中文名稱，取自 skill 檔的 frontmatter。"""
    return str(skill(code).meta.get("name", code))


def translate_from_anchor(client: Client, anchor: SemanticAnchor, lang: str, *,
                          n: int = 1, temperature: float | None = 0.0,
                          role: str = "translate") -> list[Translation]:
    """從錨點翻到 lang。n>1 時用**單一請求**取多個樣本。

    ⚠️ n>1 不可用重複呼叫實現：校內端點會快取相同請求，即使 temperature=1.5
    重送四次也只得一種輸出（實測），同語言重取樣會靜默失效。
    """
    sys_p = prompt("translate").render(
        target_name=language_name(lang), skill=skill(lang).body)
    msgs = [{"role": "system", "content": sys_p},
            {"role": "user", "content": anchor.to_prompt_block()}]
    texts = client.texts(role, msgs, n=n, temperature=temperature, max_tokens=600)
    return [Translation(language=lang, text=t, from_anchor=True) for t in texts if t]


def translate_direct(client: Client, text: str, lang: str, *,
                     role: str = "translate") -> Translation:
    """快速通道的直翻：不建錨點。作為 B0 baseline 與 fast path 使用。"""
    sys_p = prompt("translate").render(
        target_name=language_name(lang), skill=skill(lang).body)
    msgs = [{"role": "system", "content": sys_p},
            {"role": "user", "content": f"【原文】{text}"}]
    out = client.text(role, msgs, temperature=0.0, max_tokens=600)
    return Translation(language=lang, text=out, from_anchor=False)


def back_translate(client: Client, translation: Translation, *,
                   role: str = "backtrans") -> str:
    """回譯成中文。用途是量測資訊損失，故 prompt 明訂不得回補未寫出的資訊。"""
    sys_p = prompt("backtrans").render(source_name=language_name(translation.language))
    msgs = [{"role": "system", "content": sys_p},
            {"role": "user", "content": translation.text}]
    return client.text(role, msgs, temperature=0.0, max_tokens=600)
