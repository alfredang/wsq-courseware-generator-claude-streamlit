#!/bin/bash
# Server setup script — run ONCE after cloning the repo on a production server
# Installs Python dependencies and Playwright browsers with OS dependencies.
#
# Usage:
#   chmod +x setup_server.sh
#   ./setup_server.sh

set -e

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Installing Playwright Chromium browser + OS dependencies..."
# --with-deps installs required system libraries (libnss3, libasound2, etc.)
python -m playwright install --with-deps chromium

echo ""
echo "Setup complete. Start the app with:"
echo "  streamlit run app.py --server.port 7860 --server.address 0.0.0.0"
