# tbench-screening

This repository contains a T-bench screening task.

## Task

**log-incident-reconciliation**

The task requires an AI agent to parse multiple heterogeneous log files, normalize incident records, aggregate related incidents across sources, and generate a deterministic JSON report.

## What the Task Does

The agent must:

- read log files from multiple services
- parse different log formats
- extract only `ERROR` and `WARN` entries
- ignore malformed lines
- ignore logs without a valid incident ID
- normalize all timestamps to UTC ISO 8601 format
- merge records with the same `incident_id` across files
- compute incident-level summaries such as:
  - involved services
  - total occurrence count
  - aggregated severity (`ERROR > WARN`)
  - earliest occurrence time
  - latest occurrence time
  - duration in seconds
- generate summary statistics, including:
  - total number of unique incidents
  - incident count per service

The final output must be deterministic and written to `output/report.json`.

## Structure

- `tasks/log-incident-reconciliation/prompt.md`  
  Task instructions for the AI agent

- `tasks/log-incident-reconciliation/solution.py`  
  Candidate solution entrypoint

- `tasks/log-incident-reconciliation/oracle/solve.py`  
  Reference implementation used by the task author only

- `tasks/log-incident-reconciliation/tests/test_task.py`  
  Verification script for candidate output

- `tasks/log-incident-reconciliation/expected/report.json`  
  Expected deterministic output for the provided test data

- `tasks/log-incident-reconciliation/Dockerfile`  
  Isolated execution environment

## Input Files

The task uses log files under `/data`:

- `/data/app.log`
- `/data/worker.log`
- `/data/gateway.log`

Each file uses a different log format, so the candidate must handle heterogeneous parsing robustly.

## Output

The candidate solution must write the final report to:

```text
/output/report.json
```

The output JSON must include:

- `total_incidents`
- `by_service`
- `incidents`

Each incident record must contain:

- `incident_id`
- `services`
- `count`
- `severity`
- `first_seen`
- `last_seen`
- `duration_seconds`

## Deterministic Rules

The task is designed to be strictly deterministic. The solution must apply these rules:

- logs with the same `incident_id` must be merged into a single incident
- only `ERROR` and `WARN` logs are considered
- malformed or unparsable log lines must be ignored
- logs without a valid `incident_id` must be ignored
- severity must be aggregated using highest priority:
  - `ERROR > WARN`
- `first_seen` must be the earliest timestamp for the incident
- `last_seen` must be the latest timestamp for the incident
- `duration_seconds` must equal `last_seen - first_seen`
- services must be unique and sorted alphabetically
- incidents must be sorted by `incident_id` ascending
- the same input must always produce the same output

## Verification Coverage

The test suite validates:

- exact match against `expected/report.json`
- top-level JSON structure
- deterministic sorting
- cross-source incident merging
- timestamp normalization and ordering
- severity aggregation
- duplicate line counting
- exclusion of malformed lines
- exclusion of logs missing valid incident IDs

## Run

```bash
cd tasks/log-incident-reconciliation
docker build -t tbench-log-task .
docker run --rm tbench-log-task
```

## Notes

- The candidate solution must generate `output/report.json`
- Tests validate only the candidate output
- Oracle code is included as a reference and is not executed by the test flow
- The task does not require internet access or external services
