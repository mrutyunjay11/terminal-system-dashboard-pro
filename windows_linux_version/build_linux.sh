#!/usr/bin/env bash
# ==============================================================================
# Build Script for Linux (PyInstaller Binary + Tarball Packager)
# Terminal System Dashboard Pro
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo " Building Terminal System Dashboard Pro (Linux)"
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
rm -rf build dist release *.spec *.tar.gz
mkdir -p build/pyi_cache
export PYINSTALLER_CONFIG_DIR="$SCRIPT_DIR/build/pyi_cache"

# 3. Build standalone executable using PyInstaller
echo "Building standalone binary with PyInstaller..."
pyinstaller \
    --onefile \
    --name "TSDP-Linux" \
    --add-data "config.json:." \
    --collect-all "rich" \
    --collect-all "psutil" \
    --collect-all "cpuinfo" \
    --hidden-import "speedtest" \
    --hidden-import "GPUtil" \
    --console \
    project.py

# 4. Package as .tar.gz tarball
echo "Creating Tarball package..."
mkdir -p release
cp dist/TSDP-Linux release/
cp config.json release/
cp README.md release/

tar -czf dist/TSDP-Linux.tar.gz -C release TSDP-Linux config.json README.md
rm -rf release

echo "=========================================="
echo " Build Complete!"
echo " Binary:  dist/TSDP-Linux"
echo " Tarball: dist/TSDP-Linux.tar.gz"
echo "=========================================="
