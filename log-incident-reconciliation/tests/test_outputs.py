import json
import re
from datetime import datetime
from pathlib import Path

REPORT_PATH = Path("/app/report.json")

ISO_8601_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def load_report():
    assert REPORT_PATH.exists(), f"Missing output file: {REPORT_PATH}"
    with REPORT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_utc(ts: str) -> datetime:
    assert ISO_8601_UTC_PATTERN.match(ts), f"Invalid UTC timestamp format: {ts}"
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def get_incident(report: dict, incident_id: str) -> dict:
    for item in report["incidents"]:
        if item["incident_id"] == incident_id:
            return item
    raise AssertionError(f"Incident not found: {incident_id}")


def test_report_file_exists():
    assert REPORT_PATH.exists(), "report.json was not created"


def test_top_level_structure():
    report = load_report()

    assert isinstance(report, dict), "Top-level report must be a JSON object"
    assert set(report.keys()) == {"total_incidents", "by_service", "incidents"}, (
        f"Unexpected top-level keys: {set(report.keys())}"
    )

    assert isinstance(report["total_incidents"], int), "total_incidents must be an integer"
    assert isinstance(report["by_service"], dict), "by_service must be an object"
    assert isinstance(report["incidents"], list), "incidents must be a list"


def test_total_incidents():
    report = load_report()
    assert report["total_incidents"] == 10, (
        f"Expected 10 unique incidents, got {report['total_incidents']}"
    )


def test_by_service_counts():
    report = load_report()

    expected_by_service = {
        "auth": 3,
        "billing": 2,
        "gateway": 8,
        "orders": 1,
        "search": 1,
        "worker": 7,
    }

    assert report["by_service"] == expected_by_service, (
        f"Unexpected by_service counts: {report['by_service']}"
    )


def test_incidents_sorted_by_incident_id():
    report = load_report()
    incident_ids = [item["incident_id"] for item in report["incidents"]]
    assert incident_ids == sorted(incident_ids), (
        f"Incidents must be sorted by incident_id ascending, got {incident_ids}"
    )


def test_each_incident_has_required_fields_and_types():
    report = load_report()

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
        assert set(item.keys()) == required_keys, (
            f"Unexpected keys for incident {item}: {set(item.keys())}"
        )

        assert isinstance(item["incident_id"], str) and item["incident_id"], (
            "incident_id must be a non-empty string"
        )
        assert isinstance(item["services"], list), "services must be a list"
        assert isinstance(item["count"], int) and item["count"] > 0, (
            "count must be a positive integer"
        )
        assert item["severity"] in {"WARN", "ERROR"}, (
            f"severity must be WARN or ERROR, got {item['severity']}"
        )
        assert isinstance(item["duration_seconds"], int) and item["duration_seconds"] >= 0, (
            "duration_seconds must be a non-negative integer"
        )

        parse_utc(item["first_seen"])
        parse_utc(item["last_seen"])


def test_services_are_unique_and_sorted():
    report = load_report()

    for item in report["incidents"]:
        services = item["services"]
        assert services == sorted(services), (
            f"services must be sorted for {item['incident_id']}: {services}"
        )
        assert len(services) == len(set(services)), (
            f"services must be unique for {item['incident_id']}: {services}"
        )


def test_duration_matches_first_and_last_seen():
    report = load_report()

    for item in report["incidents"]:
        first_seen = parse_utc(item["first_seen"])
        last_seen = parse_utc(item["last_seen"])
        expected_duration = int((last_seen - first_seen).total_seconds())

        assert expected_duration == item["duration_seconds"], (
            f"duration_seconds mismatch for {item['incident_id']}: "
            f"expected {expected_duration}, got {item['duration_seconds']}"
        )


def test_incident_count_matches_number_of_parsed_entries():
    report = load_report()

    expected_counts = {
        "INC001": 4,
        "INC002": 1,
        "INC003": 2,
        "INC004": 1,
        "INC005": 4,
        "INC006": 2,
        "INC007": 4,
        "INC008": 3,
        "INC010": 3,
        "INC011": 3,
    }

    actual_counts = {item["incident_id"]: item["count"] for item in report["incidents"]}

    assert actual_counts == expected_counts, (
        f"Unexpected incident occurrence counts: {actual_counts}"
    )


def test_severity_aggregation_rule():
    report = load_report()

    expected_severities = {
        "INC001": "ERROR",
        "INC002": "WARN",
        "INC003": "ERROR",
        "INC004": "WARN",
        "INC005": "ERROR",
        "INC006": "ERROR",
        "INC007": "ERROR",
        "INC008": "ERROR",
        "INC010": "ERROR",
        "INC011": "WARN",
    }

    actual_severities = {item["incident_id"]: item["severity"] for item in report["incidents"]}

    assert actual_severities == expected_severities, (
        f"Unexpected incident severities: {actual_severities}"
    )


def test_expected_services_per_incident():
    report = load_report()

    expected_services = {
        "INC001": ["auth", "gateway", "worker"],
        "INC002": ["auth"],
        "INC003": ["worker"],
        "INC004": ["gateway"],
        "INC005": ["billing", "gateway", "worker"],
        "INC006": ["gateway", "worker"],
        "INC007": ["gateway", "orders", "worker"],
        "INC008": ["auth", "gateway", "worker"],
        "INC010": ["gateway", "search", "worker"],
        "INC011": ["billing", "gateway"],
    }

    actual_services = {item["incident_id"]: item["services"] for item in report["incidents"]}

    assert actual_services == expected_services, (
        f"Unexpected services per incident: {actual_services}"
    )


def test_expected_time_ranges():
    report = load_report()

    expected_ranges = {
        "INC001": ("2026-03-15T01:16:01Z", "2026-03-15T01:16:05Z", 4),
        "INC002": ("2026-03-15T01:17:10Z", "2026-03-15T01:17:10Z", 0),
        "INC003": ("2026-03-15T01:18:00Z", "2026-03-15T01:18:30Z", 30),
        "INC004": ("2026-03-15T01:20:00Z", "2026-03-15T01:20:00Z", 0),
        "INC005": ("2026-03-15T01:18:20Z", "2026-03-15T01:20:20Z", 120),
        "INC006": ("2026-03-15T01:21:00Z", "2026-03-15T01:23:00Z", 120),
        "INC007": ("2026-03-15T01:20:10Z", "2026-03-15T01:20:40Z", 30),
        "INC008": ("2026-03-15T01:19:50Z", "2026-03-15T01:21:30Z", 100),
        "INC010": ("2026-03-15T01:22:00Z", "2026-03-15T01:24:35Z", 155),
        "INC011": ("2026-03-15T01:23:15Z", "2026-03-15T01:25:00Z", 105),
    }

    for incident_id, (first_seen, last_seen, duration_seconds) in expected_ranges.items():
        item = get_incident(report, incident_id)
        assert item["first_seen"] == first_seen, (
            f"{incident_id} first_seen mismatch: expected {first_seen}, got {item['first_seen']}"
        )
        assert item["last_seen"] == last_seen, (
            f"{incident_id} last_seen mismatch: expected {last_seen}, got {item['last_seen']}"
        )
        assert item["duration_seconds"] == duration_seconds, (
            f"{incident_id} duration_seconds mismatch: expected {duration_seconds}, got {item['duration_seconds']}"
        )


def test_ignored_invalid_or_non_incident_lines_do_not_create_extra_incidents():
    report = load_report()
    incident_ids = {item["incident_id"] for item in report["incidents"]}

    assert "INC999" not in incident_ids, "Malformed app entry must not create INC999"
    assert "" not in incident_ids, "Empty incident id must be ignored"
    assert len(incident_ids) == 10, f"Expected exactly 10 incident IDs, got {len(incident_ids)}"


def run_all_tests():
    test_report_file_exists()
    test_top_level_structure()
    test_total_incidents()
    test_by_service_counts()
    test_incidents_sorted_by_incident_id()
    test_each_incident_has_required_fields_and_types()
    test_services_are_unique_and_sorted()
    test_duration_matches_first_and_last_seen()
    test_incident_count_matches_number_of_parsed_entries()
    test_severity_aggregation_rule()
    test_expected_services_per_incident()
    test_expected_time_ranges()
    test_ignored_invalid_or_non_incident_lines_do_not_create_extra_incidents()


if __name__ == "__main__":
    run_all_tests()
    print("All tests passed.")