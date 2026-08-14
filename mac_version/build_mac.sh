#!/usr/bin/env bash
# ==============================================================================
# Build Script for macOS (PyInstaller + DMG Packager)
# Terminal System Dashboard Pro
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo " Building Terminal System Dashboard Pro (macOS)"
echo "=========================================="

# 1. Activate venv if present
if [ -d "venv" ]; then
    export PATH="$SCRIPT_DIR/venv/bin:$PATH"
fi

# Verify / Install dependencies & PyInstaller
echo "Checking dependencies..."
pip install -r requirements.txt
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing PyInstaller..."
    pip install pyinstaller
fi

# 2. Clean previous build artifacts & setup isolated cache
echo "Cleaning old build files..."
rm -rf build dist dmg_staging *.spec
mkdir -p build/pyi_cache
export PYINSTALLER_CONFIG_DIR="$SCRIPT_DIR/build/pyi_cache"

# 3. Build standalone executable using PyInstaller
echo "Building standalone binary with PyInstaller..."
pyinstaller \
    --onefile \
    --name "TSDP-macOS" \
    --add-data "config.json:." \
    --collect-all "rich" \
    --collect-all "psutil" \
    --collect-all "cpuinfo" \
    --hidden-import "speedtest" \
    --console \
    project.py

# 4. Package as .dmg disk image
echo "Creating DMG package..."
mkdir -p dmg_staging
cp dist/TSDP-macOS dmg_staging/
cp config.json dmg_staging/
cp README.md dmg_staging/

# Create DMG with hdiutil
hdiutil create \
    -volname "TSDP-macOS" \
    -srcfolder dmg_staging \
    -ov \
    -format UDZO \
    dist/TSDP-macOS.dmg

# Cleanup staging
rm -rf dmg_staging

echo "=========================================="
echo " Build Complete!"
echo " Binary: dist/TSDP-macOS"
echo " DMG:    dist/TSDP-macOS.dmg"
echo "=========================================="
