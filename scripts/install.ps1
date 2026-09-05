# Agam Toolchain Installer (Windows PowerShell)
# Usage: irm https://agam.org/install.ps1 | iex

$ErrorActionPreference = "Stop"

$AgamHome = Join-Path $env:USERPROFILE ".agam"
$BinDir = Join-Path $AgamHome "bin"
$ReleaseUrl = "https://github.com/agam-lang/agam/releases/latest/download"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "⚡ Installing Agam Language & Toolchain (S-Grade Native LLVM)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$Arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else { "i686" }
$Target = "$Arch-pc-windows-msvc"
Write-Host "Detected Platform: $Target" -ForegroundColor Yellow

if (!(Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

if (Test-Path "agam\Cargo.toml") {
    Write-Host "📦 Building native release binary from source repository..." -ForegroundColor Green
    cargo build --release --manifest-path agam\Cargo.toml --bin agamc
    Copy-Item "agam\target\release\agamc.exe" "$BinDir\agamc.exe" -Force
} else {
    Write-Host "⬇️ Downloading pre-compiled SDK bundle for $Target..." -ForegroundColor Green
    $ArchiveName = "agam-sdk-$Target.zip"
    $TempZip = Join-Path $env:TEMP $ArchiveName
    Invoke-WebRequest -Uri "$ReleaseUrl/$ArchiveName" -OutFile $TempZip
    Expand-Archive -Path $TempZip -DestinationPath $AgamHome -Force
    Remove-Item $TempZip -Force
}

# Update User PATH
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$BinDir;$UserPath", "User")
    $env:PATH = "$BinDir;$env:PATH"
    Write-Host "✅ Added $BinDir to User PATH." -ForegroundColor Green
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎉 Agam Toolchain installed successfully!" -ForegroundColor Green
Write-Host "Verify installation with: agamc doctor" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
