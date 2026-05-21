# Rykard Bank - Android Setup Automation Script

Write-Host "--- Rykard Bank: Android App Initialization ---" -ForegroundColor Gold

# Check for Node.js
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Node.js is not installed. Please download it from https://nodejs.org/" -ForegroundColor Red
    return
}

Write-Host "[1/4] Installing dependencies..." -ForegroundColor Cyan
npm install @capacitor/core @capacitor/cli @capacitor/android

Write-Host "[2/4] Adding Android platform..." -ForegroundColor Cyan
npx cap add android

Write-Host "[3/4] Syncing web assets..." -ForegroundColor Cyan
npx cap sync android

Write-Host "[4/4] Opening project in Android Studio..." -ForegroundColor Cyan
npx cap open android

Write-Host "`n--- Script Finished Successfully! ---" -ForegroundColor Green
Write-Host "Please wait for Android Studio to load and then build your APK."
