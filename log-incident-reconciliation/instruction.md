# Task: Multi-Source Log Incident Reconciliation

## Overview

You are given multiple log files from different services in a Linux environment.
Each file uses a different log format and may also contain malformed, irrelevant, or incomplete lines.

Your task is to parse, normalize, and aggregate incident data across all log sources, then generate a deterministic JSON report.

---

## Input

All input files are available in the working directory:

* /app/app.log
* /app/worker.log
* /app/gateway.log

Each file contains mixed log entries.

### Example log formats

#### app.log

2026-03-15 10:16:01 ERROR service=auth msg="..." incident_id=INC001

#### worker.log

[2026-03-15T01:16:03Z] ERROR worker: ... (incident=INC001)

#### gateway.log

15/03/2026 10:16:02 ERROR gateway ... id=INC001

---

## Requirements

### 1. Parse logs

Extract only ERROR and WARN entries.

Ignore:

* malformed lines
* lines with missing or empty incident identifiers
* irrelevant lines such as INFO

For each valid log entry, extract:

* timestamp
* service name
* incident ID
* severity

---

### 2. Normalize timestamps

Normalize all timestamps to UTC in this exact format:

YYYY-MM-DDTHH:MM:SSZ

---

### 3. Aggregate incidents

Group all valid entries by incident_id.

For each incident, compute:

* services: unique service names sorted alphabetically
* count: total number of matching log entries
* severity: aggregated severity using the rule below
* first_seen: earliest timestamp
* last_seen: latest timestamp
* duration_seconds: difference between last_seen and first_seen in seconds

---

### 4. Deterministic rules

Your output must follow all of these rules:

* Only ERROR and WARN entries are considered
* Entries with the same incident_id must be merged
* Severity priority is: ERROR > WARN
* services must be unique and sorted alphabetically
* incidents must be sorted by incident_id ascending
* first_seen must be the earliest normalized timestamp
* last_seen must be the latest normalized timestamp
* duration_seconds must be the exact integer difference in seconds
* malformed lines must be ignored
* lines without a valid incident ID must be ignored
* output must be deterministic

---

### 5. Summary statistics

Also generate:

* total_incidents: number of unique incident IDs
* by_service: number of unique incidents involving each service

---

## Output

Write the final result to:

/app/report.json

---

## Output format

{
"total_incidents": 0,
"by_service": {
"service_name": 0
},
"incidents": [
{
"incident_id": "INC001",
"services": ["auth", "worker"],
"count": 2,
"severity": "ERROR",
"first_seen": "2026-03-15T01:16:01Z",
"last_seen": "2026-03-15T01:16:03Z",
"duration_seconds": 2
}
]
}

---

## Constraints

* No external network access
* No external API usage
* Must run inside the provided Linux container
* Output must be deterministic
