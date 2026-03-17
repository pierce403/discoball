#!/usr/bin/env bash
is_sourced=0
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  is_sourced=1
fi

die() {
  echo "$1" >&2
  if [[ "${is_sourced}" -eq 1 ]]; then
    return 1
  fi
  exit 1
}

if [[ "${is_sourced}" -ne 1 ]]; then
  die "Run this script with: source ./pysetup.sh"$'\n'"Executing it directly cannot activate your current shell."
fi

VENV_DIR="${VENV_DIR:-.venv}"
REQ_FILE="${REQ_FILE:-requirements.txt}"

if ! command -v uv >/dev/null 2>&1; then
  die "uv is required. Install it: https://docs.astral.sh/uv/getting-started/installation/"
  return 1
fi

if [[ ! -f "${REQ_FILE}" ]]; then
  die "Missing dependency file: ${REQ_FILE}"
  return 1
fi

echo "Creating virtual environment at ${VENV_DIR}..."
uv venv "${VENV_DIR}" || return 1

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate" || return 1

echo "Installing Python dependencies from ${REQ_FILE}..."
uv pip install --python "${VENV_DIR}/bin/python" -r "${REQ_FILE}" || return 1

echo "Python environment ready and activated."
echo "python: $(command -v python)"
echo "Use uv pip with this environment via: uv pip --python ${VENV_DIR}/bin/python ..."
