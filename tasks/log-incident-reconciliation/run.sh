#!/bin/bash
set -e

echo "[1/2] Running oracle solution..."
python oracle/solve.py

echo "[2/2] Running tests..."
python tests/test_task.py

echo "[OK] All tests passed"