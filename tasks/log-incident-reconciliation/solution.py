import json
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_PATH = OUTPUT_DIR / "report.json"

KST = timezone(timedelta(hours=9))

APP_PATTERN = re.compile(
    r'^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) '
    r'(?P<severity>ERROR|WARN) '
    r'service=(?P<service>\S+) '
    r'msg="(?P<msg>.*?)" '
    r'incident_id=(?P<incident_id>\S+)$'
)

WORKER_PATTERN = re.compile(
    r'^\[(?P<ts>[^\]]+)\]\s+'
    r'(?P<severity>ERROR|WARN)\s+'
    r'(?P<service>\w+):.*'
    r'\(incident=(?P<incident_id>[^)]+)\)$'
)

GATEWAY_PATTERN = re.compile(
    r'^(?P<ts>\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})\s+'
    r'(?P<severity>ERROR|WARN)\s+'
    r'(?P<service>\w+)\s+.*'
    r'\bid=(?P<incident_id>\S+)$'
)


def to_utc_iso(ts: str, source_type: str) -> str:
    if source_type == "app":
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if source_type == "gateway":
        dt = datetime.strptime(ts, "%d/%m/%Y %H:%M:%S").replace(tzinfo=KST)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if ts.endswith("Z"):
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_app_log(path: Path):
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = APP_PATTERN.match(line.strip())
        if not m:
            continue
        events.append(
            {
                "incident_id": m.group("incident_id"),
                "service": m.group("service"),
                "timestamp": to_utc_iso(m.group("ts"), "app"),
            }
        )
    return events


def parse_worker_log(path: Path):
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = WORKER_PATTERN.match(line.strip())
        if not m:
            continue
        events.append(
            {
                "incident_id": m.group("incident_id"),
                "service": m.group("service"),
                "timestamp": to_utc_iso(m.group("ts"), "worker"),
            }
        )
    return events


def parse_gateway_log(path: Path):
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = GATEWAY_PATTERN.match(line.strip())
        if not m:
            continue
        events.append(
            {
                "incident_id": m.group("incident_id"),
                "service": m.group("service"),
                "timestamp": to_utc_iso(m.group("ts"), "gateway"),
            }
        )
    return events


def aggregate(events):
    grouped = defaultdict(list)
    by_service = defaultdict(int)

    for event in events:
        grouped[event["incident_id"]].append(event)
        by_service[event["service"]] += 1

    incidents = []
    for incident_id, rows in grouped.items():
        timestamps = sorted(
            datetime.strptime(r["timestamp"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            for r in rows
        )
        services = sorted({r["service"] for r in rows})
        first_seen = timestamps[0]
        last_seen = timestamps[-1]
        duration_seconds = int((last_seen - first_seen).total_seconds())

        incidents.append(
            {
                "incident_id": incident_id,
                "services": services,
                "count": len(rows),
                "first_seen": first_seen.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "last_seen": last_seen.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "duration_seconds": duration_seconds,
            }
        )

    incidents.sort(key=lambda x: x["incident_id"])

    return {
        "total_incidents": len(incidents),
        "by_service": dict(sorted(by_service.items())),
        "incidents": incidents,
    }


def main():
    events = []
    events.extend(parse_app_log(DATA_DIR / "app.log"))
    events.extend(parse_worker_log(DATA_DIR / "worker.log"))
    events.extend(parse_gateway_log(DATA_DIR / "gateway.log"))

    report = aggregate(events)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()