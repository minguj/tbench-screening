import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXPECTED_PATH = BASE_DIR / "expected" / "report.json"
OUTPUT_PATH = BASE_DIR / "output" / "report.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def assert_output_file_exists():
    assert OUTPUT_PATH.exists(), f"Missing output file: {OUTPUT_PATH}"


def assert_valid_top_level_schema(data):
    assert isinstance(data, dict), "Top-level JSON must be an object"

    required_keys = {"total_incidents", "by_service", "incidents"}
    missing = required_keys - set(data.keys())
    assert not missing, f"Missing required keys: {missing}"

    assert isinstance(data["total_incidents"], int), "total_incidents must be an integer"
    assert isinstance(data["by_service"], dict), "by_service must be an object"
    assert isinstance(data["incidents"], list), "incidents must be a list"


def assert_valid_incident_schema(data):
    incidents = data["incidents"]

    for idx, item in enumerate(incidents):
        assert isinstance(item, dict), f"Incident #{idx} must be an object"

        required_keys = {
            "incident_id",
            "services",
            "count",
            "first_seen",
            "last_seen",
            "duration_seconds",
        }
        missing = required_keys - set(item.keys())
        assert not missing, f"Incident #{idx} missing required keys: {missing}"

        assert isinstance(item["incident_id"], str), f"Incident #{idx}: incident_id must be string"
        assert isinstance(item["services"], list), f"Incident #{idx}: services must be list"
        assert isinstance(item["count"], int), f"Incident #{idx}: count must be int"
        assert isinstance(item["first_seen"], str), f"Incident #{idx}: first_seen must be string"
        assert isinstance(item["last_seen"], str), f"Incident #{idx}: last_seen must be string"
        assert isinstance(item["duration_seconds"], int), f"Incident #{idx}: duration_seconds must be int"


def assert_exact_match(actual, expected):
    if actual != expected:
        print("=== ACTUAL ===")
        print(json.dumps(actual, indent=2, ensure_ascii=False))
        print("=== EXPECTED ===")
        print(json.dumps(expected, indent=2, ensure_ascii=False))
    assert actual == expected, "Output JSON does not match expected/report.json exactly"


def main():
    assert_output_file_exists()

    actual = load_json(OUTPUT_PATH)
    expected = load_json(EXPECTED_PATH)

    assert_valid_top_level_schema(actual)
    assert_valid_incident_schema(actual)
    assert_exact_match(actual, expected)

    print("All tests passed.")


if __name__ == "__main__":
    main()