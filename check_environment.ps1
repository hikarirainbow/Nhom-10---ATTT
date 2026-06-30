Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   KIEM TRA MOI TRUONG DU LIEU VA MO HINH HE THONG IDS AI" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

$rawDir = "data/raw"
$modelsDir = "models"

# 1. Kiem tra tap du lieu CSV
Write-Host "[*] Dang kiem tra cac tep du lieu CSV trong $rawDir..." -ForegroundColor Yellow
if (Test-Path $rawDir) {
    $csvFiles = Get-ChildItem -Path $rawDir -Filter *.csv
    if ($csvFiles.Count -eq 0) {
        Write-Host "  [!] Khong tim thay tep CSV nao trong $rawDir!" -ForegroundColor Red
    }
    foreach ($file in $csvFiles) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        if ($file.Name -eq "mock_cicids2017.csv") {
            Write-Host "  -> File Mock: $($file.Name) ($sizeMB MB)" -ForegroundColor Gray
        } else {
            if ($file.Length -lt 1MB) {
                Write-Host "  -> File: $($file.Name) ($sizeMB MB) [Canh bao: Dung luong qua nho]" -ForegroundColor Red
            } else {
                Write-Host "  -> File Thuc Te: $($file.Name) ($sizeMB MB)" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "  [!] Thu muc $rawDir khong ton tai!" -ForegroundColor Red
}

# 2. Kiem tra cac mo hinh .pkl
Write-Host "`n[*] Dang kiem tra cac file mo hinh trong $modelsDir..." -ForegroundColor Yellow
if (Test-Path $modelsDir) {
    $pklFiles = Get-ChildItem -Path $modelsDir -Filter *.pkl
    if ($pklFiles.Count -eq 0) {
        Write-Host "  [!] Khong tim thay mo hinh .pkl nao trong $modelsDir!" -ForegroundColor Red
    }
    foreach ($file in $pklFiles) {
        $sizeKB = [math]::Round($file.Length / 1KB, 2)
        Write-Host "  -> Mo hinh: $($file.Name) ($sizeKB KB)" -ForegroundColor Cyan
    }
} else {
    Write-Host "  [!] Thu muc $modelsDir khong ton tai!" -ForegroundColor Red
}

Write-Host "`n[+] Kiem tra hoan tat!" -ForegroundColor Green
