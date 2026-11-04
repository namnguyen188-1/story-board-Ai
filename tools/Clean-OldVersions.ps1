# Clean-OldVersions.ps1 - Don dep cac ban sao luu, file cap nhat cu va bo nho tam cho Storyboard AI (Ap dung ca May Chinh va May Phu)
param(
    [switch]$KeepLatestBackup = $true,
    [switch]$Force = $false
)

$ErrorActionPreference = 'SilentlyContinue'
$totalFreedBytes = 0
$cleanedItems = @()

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  STORYBOARD AI - DON DEP BAN CU VA BO NHO TAM" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Don dep thu muc backups cua Updater trong LocalAppData
$backupsRoot = Join-Path $env:LOCALAPPDATA 'StoryboardAI\Updater\backups'
if (Test-Path -LiteralPath $backupsRoot) {
    $allBackups = @(Get-ChildItem -LiteralPath $backupsRoot -Directory | Sort-Object CreationTime -Descending)
    $toDelete = if ($KeepLatestBackup -and $allBackups.Count -gt 1) {
        $allBackups | Select-Object -Skip 1
    } elseif (-not $KeepLatestBackup) {
        $allBackups
    } else {
        @()
    }

    foreach ($b in $toDelete) {
        $files = Get-ChildItem -LiteralPath $b.FullName -Recurse -File -Force
        $sz = ($files | Measure-Object -Property Length -Sum).Sum
        Remove-Item -LiteralPath $b.FullName -Recurse -Force
        $totalFreedBytes += $sz
        $cleanedItems += "Backup cu: $($b.Name) ($([math]::Round($sz / 1MB, 2)) MB)"
        Write-Host "  [Xoa Backup Cu] $($b.Name) ($([math]::Round($sz / 1MB, 2)) MB)" -ForegroundColor Yellow
    }
}

# 2. Don dep cac file zip / thu muc tam Updater trong Temp
$tempDirs = @(
    $env:TEMP,
    (Join-Path $env:LOCALAPPDATA 'Temp')
) | Select-Object -Unique

foreach ($tDir in $tempDirs) {
    if (Test-Path -LiteralPath $tDir) {
        $tempUpdates = @(Get-ChildItem -LiteralPath $tDir -Filter 'StoryboardAI-Update-*' -Force)
        foreach ($t in $tempUpdates) {
            $sz = 0
            if ($t.PSIsContainer) {
                $files = Get-ChildItem -LiteralPath $t.FullName -Recurse -File -Force
                $sz = ($files | Measure-Object -Property Length -Sum).Sum
            } else {
                $sz = $t.Length
            }
            Remove-Item -LiteralPath $t.FullName -Recurse -Force
            $totalFreedBytes += $sz
            $cleanedItems += "File tam updater: $($t.Name) ($([math]::Round($sz / 1MB, 2)) MB)"
            Write-Host "  [Xoa File Tam] $($t.Name) ($([math]::Round($sz / 1MB, 2)) MB)" -ForegroundColor Yellow
        }
    }
}

# 3. Don dep file trang thai tam .tmp-* trong Updater
$updaterRoot = Join-Path $env:LOCALAPPDATA 'StoryboardAI\Updater'
if (Test-Path -LiteralPath $updaterRoot) {
    $tmpFiles = @(Get-ChildItem -LiteralPath $updaterRoot -Filter '*.tmp*' -File -Force)
    foreach ($tf in $tmpFiles) {
        $sz = $tf.Length
        Remove-Item -LiteralPath $tf.FullName -Force
        $totalFreedBytes += $sz
    }
}

# 4. Neu dang o may chinh (co thu muc dist), don dep cac ban ZIP cu hon
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path (Split-Path -Parent $scriptDir) 'dist'
if (Test-Path -LiteralPath $distDir) {
    $zips = @(Get-ChildItem -LiteralPath $distDir -Filter '*.zip' -File | Sort-Object CreationTime -Descending)
    if ($zips.Count -gt 2) {
        $oldZips = $zips | Select-Object -Skip 2
        foreach ($oz in $oldZips) {
            $sz = $oz.Length
            Remove-Item -LiteralPath $oz.FullName -Force
            $totalFreedBytes += $sz
            $cleanedItems += "Goi build ZIP cu: $($oz.Name) ($([math]::Round($sz / 1MB, 2)) MB)"
            Write-Host "  [Xoa ZIP Build Cu] $($oz.Name) ($([math]::Round($sz / 1MB, 2)) MB)" -ForegroundColor Yellow
        }
    }
}

$freedMB = [math]::Round($totalFreedBytes / 1MB, 2)
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan
if ($freedMB -gt 0) {
    Write-Host "  THANH CONG: Da don dep tong cong $freedMB MB du lieu cu!" -ForegroundColor Green
} else {
    Write-Host "  HE THONG SACH SE: Khong co du lieu cu hay file tam nao can don dep." -ForegroundColor Green
}
Write-Host "==========================================================" -ForegroundColor Cyan

return [pscustomobject]@{
    ok = $true
    freed_mb = $freedMB
    cleaned_count = $cleanedItems.Count
    cleaned_items = $cleanedItems
}
