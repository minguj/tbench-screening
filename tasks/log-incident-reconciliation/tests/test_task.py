import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ORACLE_FILE = BASE_DIR / "oracle" / "solve.py"
OUTPUT_FILE = BASE_DIR / "output" / "report.json"
EXPECTED_FILE = BASE_DIR / "expected" / "report.json"


def run_oracle():
    subprocess.run([sys.executable, str(ORACLE_FILE)], check=True, cwd=BASE_DIR)


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    run_oracle()

    assert OUTPUT_FILE.exists(), "Output file not found"

    actual = load_json(OUTPUT_FILE)
    expected = load_json(EXPECTED_FILE)

    assert actual == expected, f"\nActual:\n{actual}\n\nExpected:\n{expected}"

    print("All tests passed.")


if __name__ == "__main__":
    main()