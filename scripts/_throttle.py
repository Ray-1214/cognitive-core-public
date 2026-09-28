"""跨腳本共用的節流與熔斷（技術設計文件 §5.4）。

起因：2026-08-14 一天內對校內 LLM 端點累計約四千次呼叫後，該主機 TCP 443
完全不通（DNS 正常、handshake 逾時）。無法斷定是否由本專案造成，但當時
所有腳本都沒有任何節流，只有各自的重試——重試反而在服務異常時加重負載。

本模組提供：
  RateLimiter  全域每秒請求上限，跨執行緒共用
  CircuitBreaker  連續失敗達門檻即停止送出，避免對已異常的服務持續加壓

用法：
    from _throttle import RateLimiter, CircuitBreaker
    ITHU = RateLimiter(rps=4.0)
    BREAKER = CircuitBreaker(threshold=8)

    BREAKER.check()          # 已熔斷則拋出 CircuitOpen
    ITHU.acquire()           # 阻塞到可以送出
    ...送出請求...
    BREAKER.record(ok=True)  # 或 ok=False
"""

from __future__ import annotations

import threading
import time


class CircuitOpen(RuntimeError):
    """服務連續失敗，已停止送出請求。"""


class RateLimiter:
    """全域每秒請求上限。多執行緒共用同一個實例才有意義。"""

    def __init__(self, rps: float = 4.0):
        self.interval = 1.0 / rps if rps > 0 else 0.0
        self._lock = threading.Lock()
        self._next = 0.0

    def acquire(self) -> None:
        if self.interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            wait = max(0.0, self._next - now)
            self._next = max(now, self._next) + self.interval
        if wait:
            time.sleep(wait)


class CircuitBreaker:
    """連續失敗達 threshold 次即熔斷；cooldown 秒後允許一次試探。"""

    def __init__(self, threshold: int = 8, cooldown: float = 120.0):
        self.threshold = threshold
        self.cooldown = cooldown
        self._lock = threading.Lock()
        self._consecutive = 0
        self._opened_at = 0.0

    def check(self) -> None:
        with self._lock:
            if self._consecutive < self.threshold:
                return
            if time.monotonic() - self._opened_at >= self.cooldown:
                self._consecutive = self.threshold - 1   # 放行一次試探
                return
            raise CircuitOpen(
                f"連續失敗 {self._consecutive} 次，已熔斷；"
                f"{self.cooldown:.0f}s 後才會再試探。請先確認服務狀態，不要盲目重跑。")

    def record(self, ok: bool) -> None:
        with self._lock:
            if ok:
                self._consecutive = 0
            else:
                self._consecutive += 1
                if self._consecutive == self.threshold:
                    self._opened_at = time.monotonic()


# 各服務的預設值。校內端點雖標示 1200 RPM，但持續高壓後曾整台失聯，
# 故預設遠低於名目上限；Gemini 免費層另有每日配額，序列化並放慢。
ITHU = RateLimiter(rps=4.0)          # 240 RPM，名目上限的 1/5
GEMINI = RateLimiter(rps=0.15)       # 9 RPM
ITHU_BREAKER = CircuitBreaker(threshold=8, cooldown=120.0)
GEMINI_BREAKER = CircuitBreaker(threshold=5, cooldown=300.0)
