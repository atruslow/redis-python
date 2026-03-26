#!/bin/bash
set -e

echo "=== ruff format ==="
ruff format --check .

echo "=== mypy ==="
mypy .

echo "=== pytest ==="
python3 -m pytest

echo "=== all checks passed ==="
