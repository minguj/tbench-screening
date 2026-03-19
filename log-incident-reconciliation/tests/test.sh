#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier

echo "[1/2] Running solution..."
bash /solution/solve.sh

echo "[2/2] Running tests..."
if python3 /tests/test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
  echo "[OK] All tests passed"
else
  echo 0 > /logs/verifier/reward.txt
  echo "[FAIL] Tests failed"
  exit 1
fi