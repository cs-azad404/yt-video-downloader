#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/venv"
PYTHON=$(which python3 || which python || true)

if [ -z "$PYTHON" ]; then
  echo "Python not found. Install Python 3.8+ and retry."
  exit 1
fi

if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment..."
  "$PYTHON" -m venv "$VENV"
else
  echo "Virtual environment already exists."
fi

VENV_PY="$VENV/bin/python"
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r "$ROOT/requirements.txt"

# Try to detect ffmpeg
if command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg already on PATH"
else
  echo "ffmpeg not found. Attempting to install via package manager..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y ffmpeg
  elif command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  else
    echo "Could not find a supported package manager. Please install ffmpeg manually and ensure it's on PATH."
  fi
fi

echo "Setup complete. Run the app with:"
echo "$VENV_PY main.py"
