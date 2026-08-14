@echo off
REM ==============================================================================
REM Build Script for Windows (PyInstaller EXE Packager)
REM Terminal System Dashboard Pro
REM ==============================================================================

echo ==========================================
echo  Building Terminal System Dashboard Pro (Windows)
echo ==========================================

REM 1. Clean previous build files
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.spec del /q *.spec

REM 2. Install dependencies & PyInstaller
echo Checking dependencies...
pip install -r requirements.txt
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM 3. Build standalone .exe
echo Building standalone EXE with PyInstaller...
pyinstaller --onefile --name "TSDP-Windows" --add-data "config.json;." --collect-all "rich" --collect-all "psutil" --collect-all "cpuinfo" --hidden-import "speedtest" --hidden-import "GPUtil" --console project.py

REM 4. Create release folder
echo Packaging release files...
if exist release rd /s /q release
mkdir release
copy dist\TSDP-Windows.exe release\
copy config.json release\
copy README.md release\

echo ==========================================
echo  Build Complete!
echo  Executable: dist\TSDP-Windows.exe
echo  Release Dir: release\
echo ==========================================
