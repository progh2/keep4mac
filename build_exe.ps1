# keep4mac Windows .exe 빌드 스크립트 (PowerShell)
$ErrorActionPreference = "Stop"

$AppName = "keep4mac"
$Version = (python -c "from keep4mac import __version__; print(__version__)")
$ZipName = "$AppName-$Version-win.zip"

Write-Host "▶ 버전: $Version"
Write-Host "▶ 이전 빌드 정리..."
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

Write-Host "▶ .mo 파일 컴파일..."
foreach ($lang in @("ko", "en", "ja")) {
    msgfmt "i18n/$lang/LC_MESSAGES/keep4mac.po" -o "i18n/$lang/LC_MESSAGES/keep4mac.mo"
    Write-Host "  ✓ $lang"
}

Write-Host "▶ EXE 빌드 (PyInstaller)..."
python -m PyInstaller keep4mac_win.spec --noconfirm

$ExePath = "dist/$AppName/$AppName.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "✗ 빌드 실패: $ExePath 가 없습니다."
    exit 1
}

Write-Host "▶ ZIP 패키징..."
Compress-Archive -Path "dist/$AppName" -DestinationPath "dist/$ZipName" -Force

Write-Host "✓ 완료: dist/$ZipName"
$size = (Get-Item "dist/$ZipName").Length / 1MB
Write-Host "  크기: $([math]::Round($size, 1)) MB"
