# Job execution summary

A small command that reads job execution attempts from a JSON file and prints a summary.

Each object in the file is one attempt. Attempts that share a `job_id` are one job. The highest `attempt` number decides whether that job succeeded, failed, or is still running. This matches a task instance: the current try is the outcome, and earlier tries are history.

The exercise brief is [Python Coding Exercise.pdf](<Python Coding Exercise.pdf>). It asks for a JSON reader, validation that survives bad rows, durations for completed jobs, and a summary of totals, successes, failures, average successful duration, and jobs that needed retries.

## Run

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
job-summary examples/records.json
pytest
```

`job-summary` prints the summary as JSON on stdout. Rows that cannot be used are counted in `skipped_records` and named on stderr, so the summary can be piped without parsing logs.

A missing file, invalid JSON, or a document that is not an array exits with status 1. A bad row does not.

## Example

`examples/records.json` has six usable attempts and one row with no `job_id`.

| Job | Attempts | Outcome | Duration used |
| --- | --- | --- | --- |
| job-a | 1 failed (10s), 2 success | success, retried | 30s, from 00:01:00 to 00:01:30 |
| job-b | 1 success | success | 20s |
| job-c | 1 failed | failed | not included |
| job-d | 1 running | incomplete | not included |
| job-e | 3 success, earlier tries absent | success, retried | 10s |

Successful durations are 30, 20, and 10 seconds. The average is `(30 + 20 + 10) / 3 = 20`.

```json
{
  "total_jobs": 5,
  "successful_jobs": 3,
  "failed_jobs": 1,
  "average_successful_job_duration_seconds": 20.0,
  "incomplete_jobs": 1,
  "jobs_requiring_retries": ["job-a", "job-e"],
  "skipped_records": 1
}
```

`successful_jobs + failed_jobs + incomplete_jobs` equals `total_jobs`. Stderr for this file is `skipped record 7: missing_field`.

## How it works

- `models/` holds an attempt, a skipped row, and the summary.
- `utils/dates.py` parses timestamps and treats a missing timezone as UTC.
- `io/json_records.py` reads the file. A problem with the file raises `FileError`. A problem with one row becomes a skip with a reason code: `missing_field`, `bad_type`, `bad_timestamp`, `negative_duration`, `unknown_status`, or `duplicate_attempt`.
- `jobs/summary_job.py` groups the valid attempts by `job_id` and reduces each group to its highest attempt. It does not read files.
- `cli/cli_parser.py` parses arguments and calls `cli/commands/jobs_command.py`, which writes skip reasons to stderr and the summary to stdout.

Tests live under `tests/unit/` and follow the same packages.

## Assumptions

- `attempt` starts at 1, the same as Airflow's `try_number`.
- The outcome is the latest try, not the sum of earlier tries.
- Duration is `finished_at - started_at` on that latest try, in seconds. Failed and running time is not part of the average.
- No successful jobs makes the average `null`, not `0`.
- A job required retries when its highest attempt number is 2 or more. A file that only contains attempt 3 still counts, because the earlier tries may be missing.
- If a later attempt is `running`, the job is incomplete even when an earlier attempt succeeded.
- `running` stands in for non-terminal states such as `queued`, `up_for_retry`, and `deferred`. Any other status is skipped rather than guessed.
- `finished_at` may be omitted or null only for `running`. A timestamp that falls before `started_at` is invalid.
- Duplicate `(job_id, attempt)` keeps the first row.
- Timestamps are ISO-8601. A value with no timezone is treated as UTC.
- The whole file is loaded into memory.

## What I would improve

- Stream or chunk the file. Loading it all is fine for this sample and wrong for a daily batch.
- Report a duration percentile instead of a mean. A mean hides the slow jobs.
- Accept the rest of the task state machine. `upstream_failed` would count as failed, and `skipped` as neither success nor failure.
- On a duplicate `(job_id, attempt)`, keep the later write or the later event time. First-wins is simple and wrong for a replayed feed.
- Add a schema version so a new field can be introduced without guessing.
