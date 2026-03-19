import json
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


BASE_DIR = Path("/app")
UTC = timezone.utc
KST = timezone(timedelta(hours=9))

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

SEVERITY_RANK = {"WARN": 1, "ERROR": 2}


def parse_app(line: str):
    match = APP_PATTERN.match(line)
    if not match:
        return None

    timestamp = datetime.strptime(match["ts"], "%Y-%m-%d %H:%M:%S")
    timestamp = timestamp.replace(tzinfo=KST).astimezone(UTC)

    return {
        "timestamp": timestamp,
        "severity": match["severity"],
        "service": match["service"],
        "incident_id": match["incident_id"],
    }


def parse_worker(line: str):
    match = WORKER_PATTERN.match(line)
    if not match:
        return None

    timestamp = datetime.strptime(match["ts"], "%Y-%m-%dT%H:%M:%SZ")
    timestamp = timestamp.replace(tzinfo=UTC)

    return {
        "timestamp": timestamp,
        "severity": match["severity"],
        "service": match["service"],
        "incident_id": match["incident_id"],
    }


def parse_gateway(line: str):
    match = GATEWAY_PATTERN.match(line)
    if not match:
        return None

    timestamp = datetime.strptime(match["ts"], "%d/%m/%Y %H:%M:%S")
    timestamp = timestamp.replace(tzinfo=KST).astimezone(UTC)

    return {
        "timestamp": timestamp,
        "severity": match["severity"],
        "service": match["service"],
        "incident_id": match["incident_id"],
    }


def read_entries():
    entries = []

    sources = [
        ("app.log", parse_app),
        ("worker.log", parse_worker),
        ("gateway.log", parse_gateway),
    ]

    for filename, parser in sources:
        path = BASE_DIR / filename
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            parsed = parser(line)
            if parsed is not None:
                entries.append(parsed)

    return entries


def aggregate(entries):
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry["incident_id"]].append(entry)

    incidents = []
    by_service = defaultdict(set)

    for incident_id in sorted(grouped):
        items = grouped[incident_id]
        timestamps = [item["timestamp"] for item in items]
        services = sorted({item["service"] for item in items})

        severity = max(
            (item["severity"] for item in items),
            key=lambda level: SEVERITY_RANK[level],
        )

        for service in services:
            by_service[service].add(incident_id)

        first_seen = min(timestamps)
        last_seen = max(timestamps)

        incidents.append(
            {
                "incident_id": incident_id,
                "services": services,
                "count": len(items),
                "severity": severity,
                "first_seen": first_seen.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "last_seen": last_seen.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "duration_seconds": int((last_seen - first_seen).total_seconds()),
            }
        )

    return {
        "total_incidents": len(incidents),
        "by_service": {
            service: len(incident_ids)
            for service, incident_ids in sorted(by_service.items())
        },
        "incidents": incidents,
    }


def main():
    entries = read_entries()
    report = aggregate(entries)
    output_path = BASE_DIR / "report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()