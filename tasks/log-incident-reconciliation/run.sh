#!/usr/bin/env bash
set -euo pipefail

echo "[1/2] Running candidate solution..."
python solution.py

echo "[2/2] Running tests..."
python tests/test_task.py

echo "[OK] All tests passed"