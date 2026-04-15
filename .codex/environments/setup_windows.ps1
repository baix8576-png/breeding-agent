$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$venvDir = Join-Path $repoRoot ".venv"
$venvConfig = Join-Path $venvDir "pyvenv.cfg"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

$needsRebuild = $false

if (-not (Test-Path $venvConfig)) {
    $needsRebuild = $true
} else {
    $configText = Get-Content $venvConfig -Raw
    if ($configText -match "/usr/bin" -or $configText -match "/mnt/" -or $configText -match "\.venv/bin") {
        $needsRebuild = $true
    }
}

if ($needsRebuild) {
    if (Test-Path $venvDir) {
        Remove-Item -LiteralPath $venvDir -Recurse -Force
    }

    python -m venv $venvDir
}

if (-not (Test-Path $venvPython)) {
    throw "Windows virtual environment creation failed: $venvPython was not created."
}

Write-Host "GeneAgent PowerShell environment is ready."
Write-Host "Activate with: .\.venv\Scripts\Activate.ps1"
