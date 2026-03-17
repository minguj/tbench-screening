#!/usr/bin/env python3
import json
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA_DIR = Path("/data")
OUTPUT_PATH = Path("/output/report.json")

KST = timezone(timedelta(hours=9))
UTC = timezone.utc

APP_PATTERN = re.compile(
    r"""
    ^
    (?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})
    \s+
    (?P<severity>ERROR|WARN)
    \s+
    service=(?P<service>[A-Za-z0-9_-]+)
    \s+
    msg=".*?"
    \s+
    incident_id=(?P<incident_id>[A-Za-z0-9_-]+)
    $
    """,
    re.VERBOSE,
)

WORKER_PATTERN = re.compile(
    r"""
    ^
    \[(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\]
    \s+
    (?P<severity>ERROR|WARN)
    \s+
    (?P<service>[A-Za-z0-9_-]+):
    .*
    \(incident=(?P<incident_id>[A-Za-z0-9_-]+)\)
    $
    """,
    re.VERBOSE,
)

GATEWAY_PATTERN = re.compile(
    r"""
    ^
    (?P<ts>\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})
    \s+
    (?P<severity>ERROR|WARN)
    \s+
    (?P<service>[A-Za-z0-9_-]+)
    \s+
    .*
    \sid=(?P<incident_id>[A-Za-z0-9_-]+)
    $
    """,
    re.VERBOSE,
)

SEVERITY_RANK = {
    "WARN": 1,
    "ERROR": 2,
}


def to_iso_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_app_line(line: str):
    match = APP_PATTERN.match(line.strip())
    if not match:
        return None

    incident_id = match.group("incident_id")
    if not incident_id:
        return None

    # app.log timestamps are local KST and must be normalized to UTC
    dt_local = datetime.strptime(match.group("ts"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)
    dt_utc = dt_local.astimezone(UTC)

    return {
        "timestamp": dt_utc,
        "service": match.group("service"),
        "incident_id": incident_id,
        "severity": match.group("severity"),
    }


def parse_worker_line(line: str):
    match = WORKER_PATTERN.match(line.strip())
    if not match:
        return None

    incident_id = match.group("incident_id")
    if not incident_id:
        return None

    dt_utc = datetime.strptime(match.group("ts"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)

    return {
        "timestamp": dt_utc,
        "service": match.group("service"),
        "incident_id": incident_id,
        "severity": match.group("severity"),
    }


def parse_gateway_line(line: str):
    match = GATEWAY_PATTERN.match(line.strip())
    if not match:
        return None

    incident_id = match.group("incident_id")
    if not incident_id:
        return None

    # gateway.log timestamps are local KST and must be normalized to UTC
    dt_local = datetime.strptime(match.group("ts"), "%d/%m/%Y %H:%M:%S").replace(tzinfo=KST)
    dt_utc = dt_local.astimezone(UTC)

    return {
        "timestamp": dt_utc,
        "service": match.group("service"),
        "incident_id": incident_id,
        "severity": match.group("severity"),
    }


def parse_file(path: Path, parser):
    entries = []
    if not path.exists():
        return entries

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parsed = parser(line)
        if parsed is not None:
            entries.append(parsed)
    return entries


def aggregate(entries):
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry["incident_id"]].append(entry)

    incidents = []
    by_service_sets = defaultdict(set)

    for incident_id in sorted(grouped.keys()):
        items = grouped[incident_id]
        timestamps = [item["timestamp"] for item in items]
        services = sorted({item["service"] for item in items})
        highest_severity = max(items, key=lambda item: SEVERITY_RANK[item["severity"]])["severity"]
        first_seen = min(timestamps)
        last_seen = max(timestamps)

        for service in services:
            by_service_sets[service].add(incident_id)

        incidents.append(
            {
                "incident_id": incident_id,
                "services": services,
                "count": len(items),
                "severity": highest_severity,
                "first_seen": to_iso_utc(first_seen),
                "last_seen": to_iso_utc(last_seen),
                "duration_seconds": int((last_seen - first_seen).total_seconds()),
            }
        )

    by_service = {service: len(by_service_sets[service]) for service in sorted(by_service_sets.keys())}

    return {
        "total_incidents": len(incidents),
        "by_service": by_service,
        "incidents": incidents,
    }


def main():
    entries = []
    entries.extend(parse_file(DATA_DIR / "app.log", parse_app_line))
    entries.extend(parse_file(DATA_DIR / "worker.log", parse_worker_line))
    entries.extend(parse_file(DATA_DIR / "gateway.log", parse_gateway_line))

    report = aggregate(entries)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()