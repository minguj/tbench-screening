# Task: Multi-Source Log Incident Reconciliation

## Overview

You are given multiple log files from different services in a Linux environment.  
Each log file has a different format and may contain malformed or irrelevant lines.

Your task is to parse, normalize, and aggregate incident data across all log sources, and generate a structured JSON report.

---

## Input

All log files are located in the `/data` directory:

- `/data/app.log`
- `/data/worker.log`
- `/data/gateway.log`

Each file contains log entries with different formats.

### Log Format Variations

#### 1. app.log
```
2026-03-15 10:16:01 ERROR service=auth msg="..." incident_id=INC001
```

#### 2. worker.log
```
[2026-03-15T01:16:03Z] ERROR worker: ... (incident=INC001)
```

#### 3. gateway.log
```
15/03/2026 10:16:02 ERROR gateway ... id=INC001
```

---

## Requirements

### 1. Parse Logs

- Extract only `ERROR` and `WARN` level logs
- Ignore malformed or invalid lines
- Extract:
  - timestamp
  - service name
  - incident ID
  - severity (`ERROR` or `WARN`)

---

### 2. Normalize Timestamp

Convert all timestamps into **UTC ISO 8601 format**:

```
YYYY-MM-DDTHH:MM:SSZ
```

---

### 3. Incident Aggregation

Group logs by `incident_id`.

For each incident:

- Collect all related log entries
- Track:
  - services involved (unique list)
  - number of occurrences
  - earliest timestamp (`first_seen`)
  - latest timestamp (`last_seen`)
  - duration in seconds
  - aggregated severity

---

## Additional Rules (Deterministic Behavior)

The following rules MUST be strictly applied:

- Logs with the same `incident_id` must be merged into a single incident
- Only `ERROR` and `WARN` logs are considered (ignore others)
- Severity must be aggregated using the highest priority:
  ```
  ERROR > WARN
  ```
- `first_seen` must be the earliest timestamp across all entries
- `last_seen` must be the latest timestamp across all entries
- `duration_seconds` must be calculated as the difference between `last_seen` and `first_seen` in seconds
- Services must be unique and sorted alphabetically
- Incident list must be sorted by `incident_id` in ascending order
- Logs without a valid `incident_id` must be ignored
- Malformed or unparsable log lines must be ignored
- Logs from different files with the same `incident_id` must be aggregated together
- The output must be fully deterministic (same input must always produce the same output)

---

### 4. Summary Statistics

Generate:

- total number of unique incidents
- incident count per service

---

### 5. Output

Write the result to:

```
/output/report.json
```

---

## Output Format

The output must be a valid JSON object with the following structure:

```json
{
  "total_incidents": <int>,
  "by_service": {
    "<service_name>": <count>
  },
  "incidents": [
    {
      "incident_id": "<string>",
      "services": ["<string>", "..."],
      "count": <int>,
      "severity": "<string>",
      "first_seen": "<ISO8601 UTC>",
      "last_seen": "<ISO8601 UTC>",
      "duration_seconds": <int>
    }
  ]
}
```

---

## Constraints

- Output must be **deterministic**
- All timestamps must be normalized to UTC
- The solution must run in a Linux terminal environment
- Do not rely on external services or internet access

---

## Notes

- You may use any scripting language available in the environment (e.g., Python, Bash)
- Ensure your solution handles mixed formats robustly

---

## Goal

Produce a correct and fully structured `/output/report.json` based on the given log files.

---

## Output Requirements

Your solution must read input files from `/data` and write the final report to `/output/report.json`.

Do not modify files under `/expected` or `/oracle`.
