import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


BASE_DIR = Path("/app")
UTC = timezone.utc
KST = timezone(timedelta(hours=9))
SEVERITY_RANK = {"WARN": 1, "ERROR": 2}

APP_PATTERN = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"(?P<severity>ERROR|WARN) "
    r"service=(?P<service>[A-Za-z0-9_-]+)\s+"
    r'.*incident_id=(?P<incident_id>[A-Za-z0-9_-]+)$'
)

WORKER_PATTERN = re.compile(
    r"^\[(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\] "
    r"(?P<severity>ERROR|WARN) "
    r"(?P<service>[A-Za-z0-9_-]+):.*"
    r"\(incident=(?P<incident_id>[A-Za-z0-9_-]+)\)$"
)

GATEWAY_PATTERN = re.compile(
    r"^(?P<ts>\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}) "
    r"(?P<severity>ERROR|WARN) "
    r"(?P<service>[A-Za-z0-9_-]+)\s+.*"
    r"id=(?P<incident_id>[A-Za-z0-9_-]+)$"
)


def build_entry(timestamp: datetime, severity: str, service: str, incident_id: str) -> dict:
    return {
        "timestamp": timestamp,
        "severity": severity,
        "service": service,
        "incident_id": incident_id,
    }


def parse_app_log(line: str):
    match = APP_PATTERN.match(line)
    if not match:
        return None

    timestamp = datetime.strptime(match["ts"], "%Y-%m-%d %H:%M:%S")
    timestamp = timestamp.replace(tzinfo=KST).astimezone(UTC)

    return build_entry(
        timestamp=timestamp,
        severity=match["severity"],
        service=match["service"],
        incident_id=match["incident_id"],
    )


def parse_worker_log(line: str):
    match = WORKER_PATTERN.match(line)
    if not match:
        return None

    timestamp = datetime.strptime(match["ts"], "%Y-%m-%dT%H:%M:%SZ")
    timestamp = timestamp.replace(tzinfo=UTC)

    return build_entry(
        timestamp=timestamp,
        severity=match["severity"],
        service=match["service"],
        incident_id=match["incident_id"],
    )


def parse_gateway_log(line: str):
    match = GATEWAY_PATTERN.match(line)
    if not match:
        return None

    timestamp = datetime.strptime(match["ts"], "%d/%m/%Y %H:%M:%S")
    timestamp = timestamp.replace(tzinfo=KST).astimezone(UTC)

    return build_entry(
        timestamp=timestamp,
        severity=match["severity"],
        service=match["service"],
        incident_id=match["incident_id"],
    )


def get_log_sources():
    return [
        ("app.log", parse_app_log),
        ("worker.log", parse_worker_log),
        ("gateway.log", parse_gateway_log),
    ]


def read_entries() -> list[dict]:
    entries = []

    for filename, parser in get_log_sources():
        path = BASE_DIR / filename
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            parsed = parser(raw_line.strip())
            if parsed is not None:
                entries.append(parsed)

    return entries


def group_entries_by_incident(entries: list[dict]) -> dict:
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry["incident_id"]].append(entry)
    return grouped


def choose_aggregated_severity(items: list[dict]) -> str:
    return max(
        (item["severity"] for item in items),
        key=lambda level: SEVERITY_RANK[level],
    )


def build_incident_record(incident_id: str, items: list[dict]) -> dict:
    timestamps = [item["timestamp"] for item in items]
    services = sorted({item["service"] for item in items})
    first_seen = min(timestamps)
    last_seen = max(timestamps)

    return {
        "incident_id": incident_id,
        "services": services,
        "count": len(items),
        "severity": choose_aggregated_severity(items),
        "first_seen": first_seen.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_seen": last_seen.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": int((last_seen - first_seen).total_seconds()),
    }


def build_service_summary(grouped: dict) -> dict:
    by_service = defaultdict(set)

    for incident_id, items in grouped.items():
        for service in {item["service"] for item in items}:
            by_service[service].add(incident_id)

    return {
        service: len(incident_ids)
        for service, incident_ids in sorted(by_service.items())
    }


def aggregate(entries: list[dict]) -> dict:
    grouped = group_entries_by_incident(entries)

    incidents = [
        build_incident_record(incident_id, grouped[incident_id])
        for incident_id in sorted(grouped)
    ]

    return {
        "total_incidents": len(incidents),
        "by_service": build_service_summary(grouped),
        "incidents": incidents,
    }


def write_report(report: dict) -> None:
    output_path = BASE_DIR / "report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main():
    entries = read_entries()
    report = aggregate(entries)
    write_report(report)


if __name__ == "__main__":
    main()