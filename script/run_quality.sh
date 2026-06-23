#!/usr/bin/env bash
# run_quality.sh – ejecuta todos los controles de calidad localmente.
# Uso: bash script/run_quality.sh [--venv .venv313]
#
# Requiere que el entorno virtual esté creado previamente:
#   python3.13 -m venv .venv313
#   source .venv313/bin/activate
#   pip install -r requirements.txt && pip install -e .

set -euo pipefail

VENV="${1:-.venv313}"
PY="${VENV}/bin/python"

echo "========================================"
echo " json2csv – controles de calidad"
echo " Entorno: ${VENV}"
echo "========================================"

echo ""
echo "▶  ruff lint"
"${PY}" -m ruff check src tests

echo ""
echo "▶  ruff format --check"
"${PY}" -m ruff format --check src tests

echo ""
echo "▶  black --check"
"${PY}" -m black --check src tests

echo ""
echo "▶  mypy"
"${PY}" -m mypy src tests

echo ""
echo "▶  pyright"
"${PY}" -m pyright src tests

echo ""
echo "▶  pytest (cobertura ≥ 85 %)"
"${PY}" -m pytest

echo ""
echo "▶  bandit"
"${PY}" -m bandit -r src -c pyproject.toml

echo ""
echo "✅  Todos los controles pasaron."
