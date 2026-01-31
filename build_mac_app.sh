#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Routine Score Tracker"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="${ROOT_DIR}/${APP_NAME}.app"

SCRIPT=$(cat <<APPLESCRIPT
set appDir to "${ROOT_DIR}"
do shell script "cd " & quoted form of appDir & "; nohup python3 -m streamlit run app.py --server.headless true --server.port 8501 > streamlit.log 2>&1 &"
do shell script "open http://localhost:8501"
APPLESCRIPT
)

rm -rf "${APP_PATH}"
osacompile -o "${APP_PATH}" -e "${SCRIPT}"

echo "앱 생성 완료: ${APP_PATH}"
