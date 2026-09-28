"""judge_cross 的**行為**檢查（2026-08-23 裁示 A-3）。

## 為什麼字串檢查不夠

`Config.assert_judge_is_cross()` 比較的是 provider/model **字串**。
本專案全程用 `ithu/mistral-small-4` 當受測模型、`ithu/gpt-oss-120b` 當 judge，
字串不同，檢查一路通過——**但兩個 id 由同一個後端提供服務**。

發現的經過與完整證據見 `data/results/endpoint_identity_check.md`。決定性的是：

    同一個「原樣輸出」指令，三個不同的 max_tokens 下截斷點逐字相同
      max_tokens=6  → 兩者皆「人工智慧與」（5 字）
      max_tokens=10 → 兩者皆「人工智慧與機器學」（8 字）
      max_tokens=16 → 兩者皆「人工智慧與機器學習的差異在」（13 字）

截斷發生在推論引擎、用模型自己的 tokenizer。Mistral 的 Tekken 與
GPT-OSS 的 o200k 對中文的切分方式不同，三個切點全同的機率極低。

⇒ 一個用來防止球員兼裁判的機制，通過了所有測試，
  卻在**部署層面**被架空，而且無法從 API 察覺
  （沒有 `system_fingerprint`，`/models` 的 `created` 是固定佔位值）。

## 這個模組怎麼檢查

送同一個「請原樣輸出以下文字」的指令，在數個不同的 `max_tokens` 下
取回被截斷的字串。截斷位置是 tokenizer 的指紋。
兩個角色的截斷序列完全相同 → 判定為同一後端。

⚠️ 這是**必要條件不是充分條件**：截斷點不同一定是不同 tokenizer，
但相同也可能是「不同模型共用一份 tokenizer 設定」的部署錯誤。
兩種情況下 judge_cross 的實質保證都不成立，所以都該擋。
"""

from __future__ import annotations

from dataclasses import dataclass

# 中英混合、含多字詞，讓不同 tokenizer 的切分差異容易顯現。
# 刻意不取自評測資料或 dev-30。
TRUNCATION_PROBE = (
    "人工智慧與機器學習的差異在於前者涵蓋範圍更廣，機器學習只是其中一個子領域。")
TRUNCATION_INSTRUCTION = "Output exactly this and nothing else: "
MAX_TOKENS_LADDER = (6, 10, 16)


class SameBackend(RuntimeError):
    """兩個角色看起來由同一個後端提供服務。"""


@dataclass(frozen=True)
class CrossCheckResult:
    subject_role: str
    judge_role: str
    subject_model: str
    judge_model: str
    names_differ: bool
    subject_cuts: tuple[str, ...]
    judge_cuts: tuple[str, ...]

    @property
    def cuts_identical(self) -> bool:
        return self.subject_cuts == self.judge_cuts

    @property
    def is_cross(self) -> bool:
        """真正的跨模型：名稱不同**且**截斷行為不同。"""
        return self.names_differ and not self.cuts_identical

    def explain(self) -> str:
        lines = [f"受測 {self.subject_model}　judge {self.judge_model}",
                 f"名稱不同：{'✅' if self.names_differ else '🔴'}",
                 f"截斷行為不同：{'✅' if not self.cuts_identical else '🔴 逐字相同'}"]
        for mt, a, b in zip(MAX_TOKENS_LADDER, self.subject_cuts, self.judge_cuts):
            mark = "🔴 同" if a == b else "✅ 異"
            lines.append(f"  max_tokens={mt:<3} {mark}　"
                         f"{a[:20]!r} / {b[:20]!r}")
        return "\n".join(lines)


def truncation_signature(client, role: str, *,
                         profile: str | None = None) -> tuple[str, ...]:
    """回傳該角色在各 max_tokens 下被截斷的輸出。tokenizer 的指紋。"""
    out = []
    for mt in MAX_TOKENS_LADDER:
        r = client.call(role,
                        [{"role": "user",
                          "content": TRUNCATION_INSTRUCTION + TRUNCATION_PROBE}],
                        temperature=0.0, max_tokens=mt)
        txt = (r.choices[0].message.content or "").strip()
        out.append(txt)
    return tuple(out)


def check_cross(client, *, profile: str | None = None,
                subject_role: str = "translate",
                judge_role: str = "judge") -> CrossCheckResult:
    """量測，不拋錯。呼叫端決定怎麼處置。"""
    subj = client.cfg.resolve(subject_role, profile)
    judge = client.cfg.resolve(judge_role, profile)
    return CrossCheckResult(
        subject_role=subject_role, judge_role=judge_role,
        subject_model=f"{subj.provider}/{subj.model}",
        judge_model=f"{judge.provider}/{judge.model}",
        names_differ=(subj.provider, subj.model) != (judge.provider, judge.model),
        subject_cuts=truncation_signature(client, subject_role, profile=profile),
        judge_cuts=truncation_signature(client, judge_role, profile=profile))


def assert_judge_is_cross(client, *, profile: str | None = None,
                          subject_role: str = "translate") -> CrossCheckResult:
    """行為層的 judge_cross 檢查。不通過即 `SameBackend`。

    ⚠️ 本專案的現行設定**通不過**這個檢查。那不是要修掉的 bug，
    是研究發現本身——見模組 docstring 與
    `data/results/endpoint_identity_check.md`。
    """
    r = check_cross(client, profile=profile, subject_role=subject_role)
    if not r.names_differ:
        raise SameBackend(
            f"球員兼裁判：{subject_role} 與 judge 都是 {r.judge_model}"
            + (f"（profile={profile}）" if profile else ""))
    if r.cuts_identical:
        raise SameBackend(
            "名稱不同但**行為相同**——兩個 model id 極可能由同一後端提供服務。\n"
            + r.explain()
            + "\njudge_cross 的實質保證不成立，self-preference bias 無法排除。"
              "\n詳見 data/results/endpoint_identity_check.md")
    return r
