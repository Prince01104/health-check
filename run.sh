#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -f .venv/bin/activate ] && source .venv/bin/activate
python -m uvicorn backend.main:app --port 8000
