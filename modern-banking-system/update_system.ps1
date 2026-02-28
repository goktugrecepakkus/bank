# Banka Sistemi Otomatik Güncelleme Scripti (Windows)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Banka Sistemi - Otomatik Guncelleme Basliyor" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. GitHub'dan en güncel kodları çek
Write-Host "[1/3] GitHub'dan yeni kodlar indiriliyor (git pull)..." -ForegroundColor Yellow
$gitPath = "$env:LOCALAPPDATA\GitHubDesktop\app-3.5.5\resources\app\git\cmd\git.exe"

# Eger normal 'git' yüklüyse onu kullan, yoksa GitHub Desktop içindekini
if (Get-Command git -ErrorAction SilentlyContinue) {
    git pull origin main
} elseif (Test-Path $gitPath) {
    & $gitPath pull origin main
} else {
    Write-Host "  HATA: Git bulunamadi. Lütfen kodu GitHub Desktop ile manuel cekin." -ForegroundColor Red
    exit
}

# 2. infra klasörüne geçiş yap
if (Test-Path "infra") {
    Set-Location "infra"
} else {
    Write-Host "  HATA: 'infra' klasörü bulunamadı. Lütfen scripti ana dizin içinde çalistirin." -ForegroundColor Red
    exit
}

# 3. Docker sunucusunu kapatip yeni kodlarla baslat
Write-Host "[2/3] Eski Docker sunuculari durduruluyor..." -ForegroundColor Yellow
docker compose down

Write-Host "[3/3] Yeni kodlarla Docker sunuculari baslatiliyor..." -ForegroundColor Yellow
docker compose up -d --build

Write-Host "=============================================" -ForegroundColor Green
Write-Host " Islem Tamam! Sistem yeni kodlarla yayinda." -ForegroundColor Green
Write-Host " Arayüz: http://localhost:8000/index.html" -ForegroundColor DarkCyan
Write-Host "=============================================" -ForegroundColor Green

# İşlem bitince pencerenin hemen kapanmaması için
Read-Host "Kapatmak icin Enter'a basin..."
