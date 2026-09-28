@echo off
REM Cognitive-Core demo 一鍵啟動（Windows）
REM
REM 不需要 API key——沒有 key 時自動走離線模式，播放 data\demo\recorded.json
REM 的預錄結果。要即時執行任意句子才需要 key，見 .env.example。
setlocal
cd /d "%~dp0"

set VENV=.venv
set PY=%VENV%\Scripts\python.exe

if not exist "%PY%" (
    echo 建立虛擬環境 %VENV% ...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo.
        echo [錯誤] 建立虛擬環境失敗。請確認已安裝 Python 3.11 以上並在 PATH 上。
        exit /b 1
    )
    set NEED_INSTALL=1
) else (
    REM 已有環境：只在 streamlit 缺席時才安裝，避免每次啟動都跑一次 pip
    "%PY%" -c "import streamlit" >nul 2>&1
    if errorlevel 1 (set NEED_INSTALL=1) else (set NEED_INSTALL=0)
)

if "%NEED_INSTALL%"=="1" (
    echo 安裝相依套件（第一次會花幾分鐘）...
    "%PY%" -m pip install --quiet --upgrade pip
    "%PY%" -m pip install --quiet -e ".[app]"
    if errorlevel 1 (
        echo.
        echo [錯誤] 安裝失敗。
        exit /b 1
    )
) else (
    echo 環境已就緒，略過安裝。
)

if defined ITHU_API_KEY (
    echo 偵測到 ITHU_API_KEY -^> 即時模式
) else (
    echo 未設定 ITHU_API_KEY -^> 離線模式（播放預錄結果）
)

echo.
"%PY%" -m streamlit run app\streamlit_app.py
endlocal
