"""Read a JSON file of attempts and keep the rows that can be summarized."""

import json
from datetime import datetime
from pathlib import Path

from job_summary.exceptions import FileError
from job_summary.models import JobAttempt, Skip, SkipReason, Status
from job_summary.utils.dates import parse_timestamp


class LoadResult:
    def __init__(self, attempts: list[JobAttempt], skips: list[Skip]) -> None:
        self.attempts = attempts
        self.skips = skips


def load_records(path: str | Path) -> LoadResult:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FileError(f"cannot read {file_path}: {exc.strerror}") from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FileError(f"invalid JSON in {file_path}: {exc.msg}") from exc

    if not isinstance(payload, list):
        raise FileError(f"expected a JSON array in {file_path}")

    attempts: list[JobAttempt] = []
    skips: list[Skip] = []
    seen: set[tuple[str, int]] = set()
    for index, raw in enumerate(payload):
        record = validate_record(raw, index, seen)
        if isinstance(record, Skip):
            skips.append(record)
        else:
            attempts.append(record)
    return LoadResult(attempts, skips)


def validate_record(raw: object, index: int, seen: set[tuple[str, int]]) -> JobAttempt | Skip:
    if not isinstance(raw, dict):
        return Skip(index, SkipReason.BAD_TYPE)

    for field in ("job_id", "status", "started_at", "attempt"):
        if field not in raw or raw[field] is None:
            return Skip(index, SkipReason.MISSING_FIELD)

    job_id = raw["job_id"]
    if not isinstance(job_id, str):
        return Skip(index, SkipReason.BAD_TYPE)
    if not job_id.strip():
        return Skip(index, SkipReason.MISSING_FIELD)

    status_raw = raw["status"]
    if not isinstance(status_raw, str):
        return Skip(index, SkipReason.BAD_TYPE)
    try:
        status = Status(status_raw)
    except ValueError:
        return Skip(index, SkipReason.UNKNOWN_STATUS)

    attempt = raw["attempt"]
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        return Skip(index, SkipReason.BAD_TYPE)

    started = parse_timestamp(raw["started_at"])
    if started is None:
        return Skip(index, SkipReason.BAD_TIMESTAMP)

    finished: datetime | None
    if "finished_at" not in raw or raw["finished_at"] is None:
        if status is not Status.RUNNING:
            return Skip(index, SkipReason.MISSING_FIELD)
        finished = None
    else:
        finished = parse_timestamp(raw["finished_at"])
        if finished is None:
            return Skip(index, SkipReason.BAD_TIMESTAMP)
        if finished < started:
            return Skip(index, SkipReason.NEGATIVE_DURATION)

    key = (job_id, attempt)
    if key in seen:
        return Skip(index, SkipReason.DUPLICATE_ATTEMPT)
    seen.add(key)
    return JobAttempt(
        job_id=job_id,
        status=status,
        started_at=started,
        finished_at=finished,
        attempt=attempt,
    )
