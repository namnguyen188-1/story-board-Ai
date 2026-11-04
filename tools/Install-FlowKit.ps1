# Storyboard AI Studio Pro - FlowKit Standalone Engine Auto-Installer
# Use on Secondary Machines to set up FlowKit and WebTool dependencies automatically.

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   🎬 STORYBOARD AI STUDIO - CAI DAT DONG CO FLOWKIT      " -ForegroundColor Cyan
Write-Host "   (Danh cho May Phu / Setup Moi Hoan Toan Tu Dong)       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$primaryUrl = "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.18/FlowKit_Engine_Standalone.zip"
$fallbackUrl = "https://github.com/namnguyen188-1/story-board-Ai/releases/download/v1.3.18/FlowKit_Engine_Standalone.zip"

# 1. Determine target directory
$targetDir = "D:\FLOWKIT"
if (-not (Test-Path "D:\")) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $candProj = Join-Path (Split-Path -Parent $scriptDir) "FLOWKIT"
    if (Test-Path (Split-Path -Parent $candProj)) {
        $targetDir = $candProj
    } else {
        $targetDir = "C:\FLOWKIT"
    }
}

Write-Host "--> Thu muc dich: $targetDir" -ForegroundColor Yellow

if ((Test-Path "$targetDir\app\gateway.py") -and (Test-Path "$targetDir\Start_API.vbs")) {
    Write-Host "[OK] Dong co FlowKit da duoc cai dat day du tai: $targetDir" -ForegroundColor Green
    Write-Host "Dang khoi dong FlowKit daemon..." -ForegroundColor Yellow
    Start-Process "wscript.exe" -ArgumentList "`"$targetDir\Start_API.vbs`"" -WorkingDirectory $targetDir
    Start-Sleep -Seconds 3
    exit 0
}

# 2. Check for local ZIP archive
$localZipCandidates = @(
    "D:\STORYBOARD_AI\FlowKit_Engine_Standalone.zip",
    "D:\FLOWKIT_Engine_Standalone.zip",
    "$env:USERPROFILE\Downloads\FlowKit_Engine_Standalone.zip",
    (Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) "FlowKit_Engine_Standalone.zip"),
    (Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) "dist\FlowKit_Engine_Standalone.zip")
)

$zipPath = $null
foreach ($cand in $localZipCandidates) {
    if (Test-Path $cand) {
        $size = (Get-Item $cand).Length
        if ($size -gt 100000000) {
            $zipPath = $cand
            Write-Host "[OK] Tim thay file nen cuc bo: $zipPath" -ForegroundColor Green
            break
        }
    }
}

# 3. Download if not found locally
if (-not $zipPath) {
    $tempZip = Join-Path $env:TEMP "FlowKit_Engine_Standalone.zip"
    Write-Host "--> Dang tai FlowKit_Engine_Standalone.zip tu GitHub Releases (~537 MB)..." -ForegroundColor Yellow
    $downloadSuccess = $false

    if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
        Write-Host "Su dung curl de tai nhanh da luong..." -ForegroundColor Cyan
        & curl.exe -L --fail --retry 3 --connect-timeout 20 --output $tempZip $primaryUrl
        if ($LASTEXITCODE -eq 0 -and (Test-Path $tempZip) -and ((Get-Item $tempZip).Length -gt 100000000)) {
            $downloadSuccess = $true
        } else {
            Write-Host "Thu lai voi fallback server..." -ForegroundColor Yellow
            & curl.exe -L --fail --retry 3 --connect-timeout 20 --output $tempZip $fallbackUrl
            if ($LASTEXITCODE -eq 0 -and (Test-Path $tempZip) -and ((Get-Item $tempZip).Length -gt 100000000)) {
                $downloadSuccess = $true
            }
        }
    }

    if (-not $downloadSuccess) {
        Write-Host "Su dung WebClient de tai..." -ForegroundColor Cyan
        $wc = New-Object System.Net.WebClient
        try {
            $wc.DownloadFile($primaryUrl, $tempZip)
            $downloadSuccess = $true
        } catch {
            $wc.DownloadFile($fallbackUrl, $tempZip)
            $downloadSuccess = $true
        } finally {
            $wc.Dispose()
        }
    }

    if (-not $downloadSuccess -or -not (Test-Path $tempZip) -or ((Get-Item $tempZip).Length -lt 100000000)) {
        Write-Host "[LOI] Khong the tai dong co FlowKit. Vui long kiem tra lai ket noi mang." -ForegroundColor Red
        pause
        exit 1
    }

    $zipPath = $tempZip
}

# 4. Extract archive
Write-Host "--> Dang giai nen FlowKit Engine vao $targetDir (khoang 30-45 giay)..." -ForegroundColor Yellow
$extractParent = Split-Path -Parent $targetDir
if (-not (Test-Path $extractParent)) { [IO.Directory]::CreateDirectory($extractParent) | Out-Null }

$sevenZ = "C:\Program Files\7-Zip\7z.exe"
if (Test-Path $sevenZ) {
    & $sevenZ x -y "-o$extractParent" $zipPath
} else {
    Expand-Archive -LiteralPath $zipPath -DestinationPath $extractParent -Force
}

# 5. Verify and Configure
$actualRoot = $targetDir
if (-not (Test-Path "$actualRoot\app\gateway.py")) {
    $candSub = Join-Path $targetDir "FLOWKIT"
    if (Test-Path "$candSub\app\gateway.py") {
        $actualRoot = $candSub
    }
}

if (-not (Test-Path "$actualRoot\app\gateway.py")) {
    Write-Host "[LOI] Cau truc thu muc giai nen khong hop le!" -ForegroundColor Red
    pause
    exit 1
}

$stateDir = Join-Path $actualRoot "state"
if (-not (Test-Path $stateDir)) { [IO.Directory]::CreateDirectory($stateDir) | Out-Null }
$machineJson = Join-Path $stateDir "machine.json"
$machineData = @{
    debug_port = 9461
    flow_profile = (Join-Path $stateDir "flow_profile")
    installed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
} | ConvertTo-Json
[IO.File]::WriteAllText($machineJson, $machineData, [System.Text.Encoding]::UTF8)

# 6. Launch FlowKit
Write-Host "--> Khoi dong FlowKit API tai cong 18110..." -ForegroundColor Cyan
Start-Process "wscript.exe" -ArgumentList "`"$actualRoot\Start_API.vbs`"" -WorkingDirectory $actualRoot

Start-Sleep -Seconds 3
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   ✓ THANH CONG: Dong co FlowKit da san sang hoat dong!   " -ForegroundColor Green
Write-Host "   Thu muc: $actualRoot                                   " -ForegroundColor Green
Write-Host "   Cong API: http://127.0.0.1:18110                       " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
pause
