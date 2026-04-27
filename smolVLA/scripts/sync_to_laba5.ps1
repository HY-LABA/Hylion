# Hylion/BG smolVLA -> LABA5_Bootcamp/main 단방향 백업 스크립트
#
# 사용법 (Hylion 루트에서):
#   pwsh smolVLA/scripts/sync_to_laba5.ps1
#   pwsh smolVLA/scripts/sync_to_laba5.ps1 -DryRun       # 미리보기만
#   pwsh smolVLA/scripts/sync_to_laba5.ps1 -NoPush       # commit 만, push 안 함
#
# 동작:
#   1. Hylion/smolVLA/  ->  LABA5_Bootcamp/smolVLA/  로 robocopy 미러
#   2. submodule 폴더는 제외 (lerobot, seeed-lerobot, reComputer-Jetson-for-Beginners)
#   3. .git, .venv, __pycache__ 등 위생 폴더 제외
#   4. LABA5_Bootcamp 에서 git add . && git commit && git push
#
# 전제:
#   - LABA5_Bootcamp 가 Hylion 옆 디렉토리에 위치 (..\LABA5_Bootcamp)
#   - LABA5_Bootcamp 의 main 브랜치에서 작업 중일 것
#   - LABA5_Bootcamp 에 푸시 권한이 있을 것

param(
    [switch]$DryRun,
    [switch]$NoPush,
    [string]$Laba5Path = (Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent | Split-Path -Parent) "LABA5_Bootcamp")
)

$ErrorActionPreference = "Stop"

$HylionRoot = Split-Path $PSScriptRoot -Parent | Split-Path -Parent | Split-Path -Parent
$SrcSmolVla = Join-Path $HylionRoot "smolVLA"
$DstSmolVla = Join-Path $Laba5Path "smolVLA"

Write-Host "=== Hylion -> LABA5 smolVLA sync ===" -ForegroundColor Cyan
Write-Host "Source : $SrcSmolVla"
Write-Host "Target : $DstSmolVla"
Write-Host ""

if (-not (Test-Path $SrcSmolVla)) {
    throw "Source not found: $SrcSmolVla"
}
if (-not (Test-Path $Laba5Path)) {
    throw "LABA5 path not found: $Laba5Path"
}

# LABA5 가 main 브랜치인지 확인
$Laba5Branch = (& git -C $Laba5Path branch --show-current).Trim()
if ($Laba5Branch -ne "main") {
    throw "LABA5 is on '$Laba5Branch', expected 'main'. Switch first: git -C $Laba5Path checkout main"
}

# robocopy /MIR 옵션 + 제외 항목
# /MIR : 대상을 소스의 거울로 (소스에 없는 파일은 대상에서 삭제)
# /XD  : exclude directory
# /XF  : exclude file
# /NFL /NDL /NP : 로그 줄임
$RobocopyArgs = @(
    "$SrcSmolVla",
    "$DstSmolVla",
    "/MIR",
    "/XD", "lerobot", "seeed-lerobot", "reComputer-Jetson-for-Beginners",
    "/XD", ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "/XD", "node_modules",
    "/XF", ".DS_Store", "Thumbs.db", "desktop.ini",
    "/XF", "*.pyc", "*.pyo",
    "/NFL", "/NDL", "/NP", "/NJH"
)

if ($DryRun) {
    $RobocopyArgs += "/L"
    Write-Host "[DryRun] robocopy preview:" -ForegroundColor Yellow
}

& robocopy @RobocopyArgs
$rc = $LASTEXITCODE
# robocopy exit codes: 0-7 정상, 8+ 에러
if ($rc -ge 8) {
    throw "robocopy failed with exit code $rc"
}
Write-Host "robocopy ok (exit $rc)" -ForegroundColor Green

if ($DryRun) {
    Write-Host "[DryRun] stopping before git operations." -ForegroundColor Yellow
    exit 0
}

# LABA5 측 git 변경사항 확인
$Status = & git -C $Laba5Path status --porcelain
if (-not $Status) {
    Write-Host "No changes in LABA5. Already in sync." -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "=== LABA5 git status ===" -ForegroundColor Cyan
& git -C $Laba5Path status --short
Write-Host ""

# commit message
$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$HylionSha = (& git -C $HylionRoot rev-parse --short HEAD).Trim()
$Msg = "sync: smolVLA from Hylion/BG @ $HylionSha ($Stamp)"

& git -C $Laba5Path add smolVLA/
& git -C $Laba5Path commit -m $Msg
Write-Host "committed: $Msg" -ForegroundColor Green

if ($NoPush) {
    Write-Host "[NoPush] skipping push." -ForegroundColor Yellow
    exit 0
}

& git -C $Laba5Path push origin main
Write-Host "pushed to LABA5/main" -ForegroundColor Green
