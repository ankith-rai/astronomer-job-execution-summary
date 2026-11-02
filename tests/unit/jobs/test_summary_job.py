import random
from datetime import datetime, timezone

from job_summary.jobs import summarize
from job_summary.models import JobAttempt, Status


def _at(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second, tzinfo=timezone.utc)


def _attempt(
    job_id: str,
    status: Status,
    attempt: int,
    started: datetime,
    finished: datetime | None,
) -> JobAttempt:
    return JobAttempt(job_id, status, started, finished, attempt)


def test_latest_attempt_decides_outcome_and_duration() -> None:
    attempts = [
        _attempt("job-a", Status.FAILED, 1, _at(0), _at(0, 1, 40)),
        _attempt("job-a", Status.SUCCESS, 2, _at(1), _at(1, 0, 30)),
        _attempt("job-b", Status.SUCCESS, 1, _at(2), _at(2, 0, 20)),
        _attempt("job-c", Status.FAILED, 1, _at(3), _at(3, 0, 15)),
        _attempt("job-d", Status.RUNNING, 1, _at(4), None),
        _attempt("job-e", Status.SUCCESS, 3, _at(5), _at(5, 0, 10)),
    ]

    summary = summarize(attempts, skipped_records=1)

    assert summary.total_jobs == 5
    assert summary.successful_jobs == 3
    assert summary.failed_jobs == 1
    assert summary.incomplete_jobs == 1
    assert summary.successful_jobs + summary.failed_jobs + summary.incomplete_jobs == summary.total_jobs
    assert summary.average_successful_job_duration_seconds == 20
    assert summary.jobs_requiring_retries == ["job-a", "job-e"]
    assert summary.skipped_records == 1


def test_running_latest_attempt_does_not_count_an_earlier_success() -> None:
    attempts = [
        _attempt("job-a", Status.SUCCESS, 1, _at(0), _at(0, 0, 30)),
        _attempt("job-a", Status.RUNNING, 2, _at(1), None),
    ]

    summary = summarize(attempts)

    assert summary.successful_jobs == 0
    assert summary.incomplete_jobs == 1
    assert summary.average_successful_job_duration_seconds is None
    assert summary.jobs_requiring_retries == ["job-a"]


def test_no_successful_jobs_leaves_the_average_null() -> None:
    summary = summarize([_attempt("job-c", Status.FAILED, 1, _at(0), _at(0, 0, 15))])

    assert summary.failed_jobs == 1
    assert summary.average_successful_job_duration_seconds is None


def test_empty_input() -> None:
    summary = summarize([])

    assert summary.to_dict() == {
        "total_jobs": 0,
        "successful_jobs": 0,
        "failed_jobs": 0,
        "average_successful_job_duration_seconds": None,
        "incomplete_jobs": 0,
        "jobs_requiring_retries": [],
        "skipped_records": 0,
    }


def test_row_order_does_not_change_the_summary() -> None:
    attempts = [
        _attempt("job-a", Status.FAILED, 1, _at(0), _at(0, 0, 10)),
        _attempt("job-a", Status.SUCCESS, 2, _at(1), _at(1, 0, 30)),
        _attempt("job-b", Status.SUCCESS, 1, _at(2), _at(2, 0, 20)),
        _attempt("job-e", Status.SUCCESS, 3, _at(3), _at(3, 0, 10)),
    ]
    shuffled = attempts.copy()
    random.Random(7).shuffle(shuffled)

    assert summarize(shuffled) == summarize(attempts)
