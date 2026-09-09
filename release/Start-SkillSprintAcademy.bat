@echo off
set "UPDATER_DIR=%LOCALAPPDATA%\SkillSprintAcademy"
if not exist "%UPDATER_DIR%" mkdir "%UPDATER_DIR%"
copy /Y "%~dp0updater.exe" "%UPDATER_DIR%\updater.exe" >nul
echo Starting SkillSprintAcademy...
echo The app will open at http://127.0.0.1:52837
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0SkillSprintAcademy"
SkillSprintAcademy.exe
pause
