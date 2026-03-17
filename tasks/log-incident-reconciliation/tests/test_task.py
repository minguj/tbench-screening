import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "output" / "report.json"
EXPECTED_PATH = BASE_DIR / "expected" / "report.json"


def load_json(path: Path):
    assert path.exists(), f"Missing file: {path}"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_incident(report: dict, incident_id: str) -> dict:
    for item in report["incidents"]:
        if item["incident_id"] == incident_id:
            return item
    raise AssertionError(f"Incident not found: {incident_id}")


def test_report_exists_and_matches_expected():
    actual = load_json(OUTPUT_PATH)
    expected = load_json(EXPECTED_PATH)
    assert actual == expected, "report.json does not match expected/report.json exactly"


def test_top_level_structure():
    report = load_json(OUTPUT_PATH)

    assert set(report.keys()) == {"total_incidents", "by_service", "incidents"}
    assert isinstance(report["total_incidents"], int)
    assert isinstance(report["by_service"], dict)
    assert isinstance(report["incidents"], list)


def test_total_incidents_and_sorting():
    report = load_json(OUTPUT_PATH)

    assert report["total_incidents"] == 10
    incident_ids = [item["incident_id"] for item in report["incidents"]]
    assert incident_ids == sorted(incident_ids), "incidents must be sorted by incident_id ascending"


def test_by_service_counts():
    report = load_json(OUTPUT_PATH)

    assert report["by_service"] == {
        "auth": 3,
        "billing": 2,
        "gateway": 8,
        "orders": 1,
        "search": 1,
        "worker": 7,
    }


def test_inc001_cross_source_merge():
    report = load_json(OUTPUT_PATH)
    inc = get_incident(report, "INC001")

    assert inc["services"] == ["auth", "gateway", "worker"]
    assert inc["count"] == 4
    assert inc["severity"] == "ERROR"
    assert inc["first_seen"] == "2026-03-15T01:16:01Z"
    assert inc["last_seen"] == "2026-03-15T01:16:05Z"
    assert inc["duration_seconds"] == 4


def test_inc007_unsorted_timestamps_and_severity():
    report = load_json(OUTPUT_PATH)
    inc = get_incident(report, "INC007")

    assert inc["services"] == ["gateway", "orders", "worker"]
    assert inc["count"] == 4
    assert inc["severity"] == "ERROR"
    assert inc["first_seen"] == "2026-03-15T01:20:10Z"
    assert inc["last_seen"] == "2026-03-15T01:20:40Z"
    assert inc["duration_seconds"] == 30


def test_inc008_severity_priority():
    report = load_json(OUTPUT_PATH)
    inc = get_incident(report, "INC008")

    assert inc["severity"] == "ERROR", "ERROR must override WARN for the same incident"
    assert inc["first_seen"] == "2026-03-15T01:19:50Z"
    assert inc["last_seen"] == "2026-03-15T01:21:30Z"
    assert inc["duration_seconds"] == 100


def test_inc011_duplicate_lines_counted():
    report = load_json(OUTPUT_PATH)
    inc = get_incident(report, "INC011")

    assert inc["services"] == ["billing", "gateway"]
    assert inc["count"] == 3
    assert inc["severity"] == "WARN"
    assert inc["duration_seconds"] == 105


def test_invalid_or_missing_incidents_are_excluded():
    report = load_json(OUTPUT_PATH)
    incident_ids = {item["incident_id"] for item in report["incidents"]}

    assert "INC999" not in incident_ids
    assert "" not in incident_ids


def test_every_incident_shape_and_ordering():
    report = load_json(OUTPUT_PATH)

    required_keys = {
        "incident_id",
        "services",
        "count",
        "severity",
        "first_seen",
        "last_seen",
        "duration_seconds",
    }

    for item in report["incidents"]:
        assert set(item.keys()) == required_keys
        assert item["severity"] in {"ERROR", "WARN"}
        assert item["services"] == sorted(item["services"])
        assert len(item["services"]) == len(set(item["services"]))
        assert isinstance(item["count"], int) and item["count"] > 0
        assert isinstance(item["duration_seconds"], int) and item["duration_seconds"] >= 0
        assert item["first_seen"].endswith("Z")
        assert item["last_seen"].endswith("Z")