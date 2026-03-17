# tbench-screening

This repository contains a T-bench screening task.

## Task
**log-incident-reconciliation**

The task requires an AI agent to parse multiple heterogeneous log files, normalize incident records, and generate a deterministic JSON report.

## Structure

- `tasks/log-incident-reconciliation/prompt.md`  
  Task instructions for the AI agent

- `tasks/log-incident-reconciliation/solution.py`  
  Candidate solution entrypoint

- `tasks/log-incident-reconciliation/oracle/solve.py`  
  Reference implementation used by the task author only

- `tasks/log-incident-reconciliation/tests/test_task.py`  
  Verification script for candidate output

- `tasks/log-incident-reconciliation/Dockerfile`  
  Isolated execution environment

## Run

```bash
cd tasks/log-incident-reconciliation
docker build -t tbench-log-task .
docker run --rm tbench-log-task


## Notes

- The candidate solution must generate `output/report.json`
- Tests validate only the candidate output
- Oracle code is included as a reference and is not executed by the test flow