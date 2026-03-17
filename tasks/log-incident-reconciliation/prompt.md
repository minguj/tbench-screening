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
- Incident list must be sorted by:
  1. `incident_id` ascending
- Services list must be sorted alphabetically
- Ignore any logs without a valid `incident_id`
- All timestamps must be normalized to UTC
- The solution must run in a Linux terminal environment

---

## Notes

- You may use any scripting language available in the environment (e.g., Python, Bash)
- The solution should not rely on external services or internet access
- Ensure your solution handles mixed formats robustly

---

## Goal

Produce a correct and fully structured `/output/report.json` based on the given log files.