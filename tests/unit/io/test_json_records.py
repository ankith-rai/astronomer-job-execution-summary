from datetime import datetime, timezone

import pytest

from job_summary.io import validate_record
from job_summary.models import JobAttempt, SkipReason, Status


def _valid(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "job_id": "job-a",
        "status": "success",
        "started_at": "2024-01-01T00:00:00Z",
        "finished_at": "2024-01-01T00:00:10Z",
        "attempt": 1,
    }
    record.update(overrides)
    return record


def test_valid_row_normalizes_naive_and_zulu_timestamps_to_utc() -> None:
    seen: set[tuple[str, int]] = set()
    record = validate_record(_valid(started_at="2024-01-01T00:00:00", finished_at="2024-01-01T00:00:10Z"), 0, seen)

    assert isinstance(record, JobAttempt)
    assert record.started_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert record.finished_at == datetime(2024, 1, 1, 0, 0, 10, tzinfo=timezone.utc)
    assert record.duration_seconds() == 10


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("not-an-object", SkipReason.BAD_TYPE),
        ({"status": "success"}, SkipReason.MISSING_FIELD),
        (_valid(job_id="  "), SkipReason.MISSING_FIELD),
        (_valid(job_id=12), SkipReason.BAD_TYPE),
        (_valid(attempt="1"), SkipReason.BAD_TYPE),
        (_valid(attempt=True), SkipReason.BAD_TYPE),
        (_valid(attempt=0), SkipReason.BAD_TYPE),
        (_valid(status=1), SkipReason.BAD_TYPE),
        (_valid(status="queued"), SkipReason.UNKNOWN_STATUS),
        (_valid(started_at="yesterday"), SkipReason.BAD_TIMESTAMP),
        (_valid(finished_at="yesterday"), SkipReason.BAD_TIMESTAMP),
        (_valid(finished_at=None), SkipReason.MISSING_FIELD),
        (_valid(finished_at="2023-12-31T23:59:59Z"), SkipReason.NEGATIVE_DURATION),
    ],
)
def test_invalid_row_returns_a_reason_code(raw: object, reason: str) -> None:
    record = validate_record(raw, 3, set())

    assert record.index == 3
    assert record.reason == reason


def test_running_may_omit_finished_at() -> None:
    record = validate_record(_valid(status="running", finished_at=None), 0, set())

    assert isinstance(record, JobAttempt)
    assert record.status is Status.RUNNING
    assert record.finished_at is None


def test_duplicate_attempt_keeps_the_first_row() -> None:
    seen: set[tuple[str, int]] = set()
    first = validate_record(_valid(), 0, seen)
    second = validate_record(_valid(status="failed", finished_at="2024-01-01T00:00:20Z"), 1, seen)

    assert isinstance(first, JobAttempt)
    assert first.status is Status.SUCCESS
    assert second.reason == SkipReason.DUPLICATE_ATTEMPT
