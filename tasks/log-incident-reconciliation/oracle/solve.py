import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "report.json"

KST_TO_UTC = timedelta(hours=9)

APP_PATTERN = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"(?P<level>INFO|WARN|ERROR) "
    r"service=(?P<service>[a-zA-Z0-9_-]+) "
    r'.*?incident_id=(?P<incident_id>INC\d+)\s*$'
)

WORKER_PATTERN = re.compile(
    r"^\[(?P<ts>[^\]]+)\] "
    r"(?P<level>INFO|WARN|ERROR) "
    r"(?P<service>[a-zA-Z0-9_-]+): "
    r".*?\(incident=(?P<incident_id>INC\d+)\)\s*$"
)

GATEWAY_PATTERN = re.compile(
    r"^(?P<ts>\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}) "
    r"(?P<level>INFO|WARN|ERROR) "
    r"(?P<service>[a-zA-Z0-9_-]+) "
    r".*?\bid=(?P<incident_id>INC\d+)\s*$"
)


def to_utc_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_kst_naive(ts: str, fmt: str) -> datetime:
    local_dt = datetime.strptime(ts, fmt)
    utc_dt = local_dt - KST_TO_UTC
    return utc_dt.replace(tzinfo=timezone.utc)


def parse_app_line(line: str):
    match = APP_PATTERN.match(line.strip())
    if not match or match.group("level") not in {"ERROR", "WARN"}:
        return None

    return {
        "timestamp": parse_kst_naive(match.group("ts"), "%Y-%m-%d %H:%M:%S"),
        "service": match.group("service"),
        "incident_id": match.group("incident_id"),
    }


def parse_worker_line(line: str):
    match = WORKER_PATTERN.match(line.strip())
    if not match or match.group("level") not in {"ERROR", "WARN"}:
        return None

    return {
        "timestamp": datetime.strptime(
            match.group("ts"), "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc),
        "service": match.group("service"),
        "incident_id": match.group("incident_id"),
    }


def parse_gateway_line(line: str):
    match = GATEWAY_PATTERN.match(line.strip())
    if not match or match.group("level") not in {"ERROR", "WARN"}:
        return None

    return {
        "timestamp": parse_kst_naive(match.group("ts"), "%d/%m/%Y %H:%M:%S"),
        "service": match.group("service"),
        "incident_id": match.group("incident_id"),
    }


def parse_file(path: Path, parser):
    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parsed = parser(line)
            if parsed is not None:
                events.append(parsed)
    return events


def load_events():
    events = []
    events.extend(parse_file(DATA_DIR / "app.log", parse_app_line))
    events.extend(parse_file(DATA_DIR / "worker.log", parse_worker_line))
    events.extend(parse_file(DATA_DIR / "gateway.log", parse_gateway_line))
    return events


def build_report(events):
    incidents = defaultdict(lambda: {"services": set(), "timestamps": [], "count": 0})
    by_service = defaultdict(int)

    for event in events:
        incident_id = event["incident_id"]
        service = event["service"]
        timestamp = event["timestamp"]

        incidents[incident_id]["services"].add(service)
        incidents[incident_id]["timestamps"].append(timestamp)
        incidents[incident_id]["count"] += 1
        by_service[service] += 1

    incident_list = []
    for incident_id in sorted(incidents.keys()):
        item = incidents[incident_id]
        first_seen = min(item["timestamps"])
        last_seen = max(item["timestamps"])

        incident_list.append(
            {
                "incident_id": incident_id,
                "services": sorted(item["services"]),
                "count": item["count"],
                "first_seen": to_utc_iso(first_seen),
                "last_seen": to_utc_iso(last_seen),
                "duration_seconds": int((last_seen - first_seen).total_seconds()),
            }
        )

    return {
        "total_incidents": len(incident_list),
        "by_service": {service: by_service[service] for service in sorted(by_service)},
        "incidents": incident_list,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report(load_events())

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()