#!/usr/bin/env bash
# Cognitive-Core demo 一鍵啟動（macOS / Linux）
#
# 不需要 API key——沒有 key 時自動走離線模式，播放 data/demo/recorded.json
# 的預錄結果。要即時執行任意句子才需要 key，見 .env.example。
set -euo pipefail
cd "$(dirname "$0")"

VENV=.venv
PY="$VENV/bin/python"

if [ ! -x "$PY" ]; then
    echo "建立虛擬環境 $VENV …"
    python3 -m venv "$VENV"
    NEED_INSTALL=1
else
    # 已有環境：只在 streamlit 缺席時才安裝，避免每次啟動都跑一次 pip
    if "$PY" -c "import streamlit" >/dev/null 2>&1; then
        NEED_INSTALL=0
    else
        NEED_INSTALL=1
    fi
fi

if [ "${NEED_INSTALL}" = "1" ]; then
    echo "安裝相依套件（第一次會花幾分鐘）…"
    "$PY" -m pip install --quiet --upgrade pip
    "$PY" -m pip install --quiet -e ".[app]"
else
    echo "環境已就緒，略過安裝。"
fi

if [ -n "${ITHU_API_KEY:-}" ]; then
    echo "偵測到 ITHU_API_KEY → 即時模式"
else
    echo "未設定 ITHU_API_KEY → 離線模式（播放預錄結果）"
fi

echo
exec "$PY" -m streamlit run app/streamlit_app.py
