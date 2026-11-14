#!/usr/bin/env bash
set -euo pipefail

# Install Python dependencies for this project into a local virtual environment.
# Usage:
#   ./install.sh
#   OLLAMA_MODEL=gpt-oss:20b-cloud ./install.sh
#   ./install.sh --skip-ollama

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
REQ_FILE="${SCRIPT_DIR}/requirements.txt"
SKIP_OLLAMA=0

if [[ "${1:-}" == "--skip-ollama" ]]; then
  SKIP_OLLAMA=1
fi

if [[ ! -f "${REQ_FILE}" ]]; then
  echo "requirements.txt not found at ${REQ_FILE}"
  exit 1
fi

if command -v python3.13 >/dev/null 2>&1; then
  PYTHON_BIN="python3.13"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "Python 3 is not installed."
  exit 1
fi

echo "Using Python: $(${PYTHON_BIN} --version)"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Creating virtual environment at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "Upgrading pip, setuptools, and wheel"
python -m pip install --upgrade pip setuptools wheel

echo "Installing dependencies from requirements.txt"
pip install -r "${REQ_FILE}"

if [[ "${SKIP_OLLAMA}" -eq 1 ]]; then
  echo "Skipping Ollama setup (--skip-ollama set)."
else
  OLLAMA_MODEL="${OLLAMA_MODEL:-gpt-oss:20b-cloud}"
  if command -v ollama >/dev/null 2>&1; then
    echo "Found Ollama. Pulling model: ${OLLAMA_MODEL}"
    ollama pull "${OLLAMA_MODEL}" || {
      echo "Could not pull model '${OLLAMA_MODEL}'. You can retry manually: ollama pull ${OLLAMA_MODEL}"
    }
  else
    echo "Ollama not found in PATH. Install it from https://ollama.com/download"
    echo "Then run: ollama pull ${OLLAMA_MODEL:-gpt-oss:20b-cloud}"
  fi
fi

echo "Setup complete. Activate environment with: source .venv/bin/activate"
