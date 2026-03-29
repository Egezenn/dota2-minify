# Build script for Windows testing, not recommended for releases!
# The application should be built in the bare git state. Will include your configurations.
# You can run `git clean -dFX` for a clean slate.

Param(
    [switch]$NoInstaller,
    [switch]$OnlyInstaller,
    [switch]$Run,
    [switch]$RunSetup
)

$ErrorActionPreference = "Stop"

# Set location to scripts directory
Set-Location $PSScriptRoot

if (-not $OnlyInstaller) {
    Write-Host "Cleaning dist/ directory..." -ForegroundColor Cyan
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
    }

    Write-Host "Running PyInstaller..." -ForegroundColor Cyan
    uv run pyinstaller Minify.spec

    Write-Host "Copying dependencies to dist/Minify..." -ForegroundColor Cyan
    Copy-Item -Path "..\Minify\bin" -Destination "dist\Minify\bin" -Recurse
    Copy-Item -Path "..\Minify\mods" -Destination "dist\Minify\mods" -Recurse
    Copy-Item -Path "..\README.md" -Destination "dist\Minify\README.md"
    Copy-Item -Path "..\LICENSE" -Destination "dist\Minify\LICENSE"
    Copy-Item -Path "..\Minify\Source2Viewer-CLI.exe" -Destination "dist\Minify"
    Copy-Item -Path "..\Minify\rg.exe" -Destination "dist\Minify"
} else {
    Write-Host "Skipping PyInstaller build (-OnlyInstaller set)" -ForegroundColor Gray
    if (-not (Test-Path "dist\Minify")) {
        Write-Error "dist\Minify not found! You must run a full build at least once."
    }
}

Write-Host "Generating version metadata..." -ForegroundColor Cyan
python version_util.py
$version = (Select-String -Path 'version_info.iss' -Pattern '#define AppVersion "(.*)"').Matches.Groups[1].Value

if (-not $NoInstaller) {
    Write-Host "Building Installer with Inno Setup..." -ForegroundColor Cyan
    $isccPath = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    $globalIsccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

    if (Test-Path $isccPath) {
        & $isccPath installer.iss
    } elseif (Test-Path $globalIsccPath) {
        & $globalIsccPath installer.iss
    } else {
        Write-Host "ISCC.exe not found in common locations. Trying to call ISCC from PATH..." -ForegroundColor Yellow
        & ISCC installer.iss
    }
} else {
    Write-Host "Skipping Installer build (-NoInstaller set)" -ForegroundColor Gray
}

if ($Run) {
    Write-Host "`nLaunching Minify.exe..." -ForegroundColor Cyan
    Start-Process "dist\Minify\Minify.exe"
}

Write-Host "`nBuild Complete!" -ForegroundColor Green
if (-not $NoInstaller) {
    Write-Host "Installer is located at: scripts\Minify-Setup-$version.exe" -ForegroundColor Green
    if ($RunSetup) {
        Write-Host "`nLaunching Setup..." -ForegroundColor Cyan
        Invoke-Item "Minify-Setup-$version.exe"
    }
}
