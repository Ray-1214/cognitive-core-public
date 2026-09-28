# 在 PowerShell 啟用 cognitive-core 環境，不必寫入 $PROFILE。
#
# 為什麼需要這支：Windows Defender 的「受控資料夾存取」（Controlled Folder Access）
# 預設保護 Documents，會擋掉 conda 寫 %userprofile%\Documents\WindowsPowerShell\profile.ps1
# ——Defender 事件 1123，而 conda 會把它誤報成 `needs sudo`。
# 結果是 `conda init powershell` 失敗，`conda activate` 只解析到 conda.bat、
# 跑在子行程裡改不到父 shell 的 PATH，於是**安靜地成功但什麼也沒做**。
# 這支繞開整個 profile 機制，只對當前 session 載入 conda 的 PowerShell hook。
#
# 用法（開頭那個點是 dot-source，不能省，否則一樣只會影響子行程）：
#
#     . .\scripts\activate.ps1
#
# 詳見 README「環境安裝（conda）」。

$ErrorActionPreference = 'Stop'

$envName = 'cognitive-core'

$condaExe = (Get-Command conda.exe -ErrorAction SilentlyContinue).Source
if (-not $condaExe) {
    $condaExe = Join-Path $env:USERPROFILE 'miniforge3\Scripts\conda.exe'
}
if (-not (Test-Path $condaExe)) {
    throw "找不到 conda.exe（試過 PATH 與 $condaExe）。請確認 miniforge/miniconda 已安裝。"
}

(& $condaExe shell.powershell hook) | Out-String | Invoke-Expression
conda activate $envName

if ($env:CONDA_PREFIX -notlike "*$envName") {
    throw "活化失敗：CONDA_PREFIX = '$env:CONDA_PREFIX'，預期結尾為 '$envName'。"
}

# 自我檢查：conda-forge 的 numpy 靠 %CONDA_PREFIX%\Library\bin 的 MKL，
# 那個目錄沒上 PATH 的話，第一個 BLAS 呼叫會讓整個行程當掉（0xc06d007f），
# 而且是 OS 層 fatal exception、Python 攔不到。這裡先踩一次確認它是活的。
& python -c "import numpy as np; np.cov([1.0,2.0,3.0],[1.0,2.0,3.0])" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "numpy 的 BLAS 沒載入成功（exit $LASTEXITCODE）。%CONDA_PREFIX%\Library\bin 可能不在 PATH 上。"
} else {
    Write-Host "✅ $envName 已啟用（BLAS 正常）  python: $((Get-Command python).Source)" -ForegroundColor Green
}
