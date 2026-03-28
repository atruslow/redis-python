#!/bin/bash
set -e

echo "=== pytest ==="
python3 -m pytest --cov

echo "=== mypy ==="
mypy .

echo "=== ruff format ==="
ruff format .

echo "=== ruff format ==="
ruff check . --fix


echo "=== all checks passed ==="
