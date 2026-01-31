#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

nohup python3 -m streamlit run app.py --server.headless true --server.port 8501 > streamlit.log 2>&1 &

sleep 1
open http://localhost:8501
