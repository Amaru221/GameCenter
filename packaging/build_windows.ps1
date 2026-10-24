# Builds the Windows one-folder app and the Inno Setup installer.
# Usage:  powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
#         powershell ... -File packaging\build_windows.ps1 -SkipInstaller

param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

try {
    $version = (Select-String -Path "gamecenter\__init__.py" -Pattern '__version__ = "([^"]+)"').Matches[0].Groups[1].Value
    Write-Host "Building GameCenter $version"

    python packaging\make_icon.py
    if ($LASTEXITCODE -ne 0) { throw "Icon generation failed" }

    python -m PyInstaller --noconfirm --clean packaging\gamecenter.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

    if (-not $SkipInstaller) {
        $candidates = @(
            "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            "C:\Program Files\Inno Setup 6\ISCC.exe",
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
        )
        $iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
        if (-not $iscc) {
            throw "Inno Setup 6 not found. Install it, or run with -SkipInstaller."
        }

        & $iscc "/DAppVersion=$version" "packaging\gamecenter.iss"
        if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }
    }

    Write-Host ""
    Write-Host "Outputs:"
    Get-ChildItem "dist" -Filter "GameCenter*" | ForEach-Object { Write-Host "  $($_.FullName)" }
}
finally {
    Pop-Location
}
