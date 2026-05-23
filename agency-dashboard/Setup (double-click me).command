#!/bin/bash
# Double-click this file to build the Agency Dashboard app.
# It installs what's needed and creates the clickable app in the "dist" folder.

cd "$(dirname "$0")" || exit 1

echo "=============================================="
echo "  Building Agency Dashboard..."
echo "  (this takes a few minutes the first time)"
echo "=============================================="
echo ""

# Skip code-signing so the build works without an Apple developer account.
export CSC_IDENTITY_AUTO_DISCOVERY=false

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: Node.js / npm not found."
  echo "Install Node from https://nodejs.org (the LTS version), then run this again."
  read -r -p "Press Enter to close..."
  exit 1
fi

echo "Step 1/2: Installing components..."
npm install || { echo ""; echo "Install failed. Check your internet connection and try again."; read -r -p "Press Enter to close..."; exit 1; }

echo ""
echo "Step 2/2: Packaging the app..."
npm run dist || { echo ""; echo "Build failed. See the messages above."; read -r -p "Press Enter to close..."; exit 1; }

echo ""
echo "=============================================="
echo "  Done! Opening the 'dist' folder."
echo "  Drag 'Agency Dashboard' into your Applications folder."
echo ""
echo "  First time you open it: right-click the app -> Open"
echo "  (because it's not signed by Apple), then click Open."
echo "=============================================="
open dist 2>/dev/null
read -r -p "Press Enter to close..."
