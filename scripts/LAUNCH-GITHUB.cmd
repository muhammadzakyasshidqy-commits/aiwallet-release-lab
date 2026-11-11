@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Publish-GitHub.ps1"
if errorlevel 1 (
  echo.
  echo Publikasi belum selesai. Baca pesan di atas; tidak ada force push.
  pause
)
