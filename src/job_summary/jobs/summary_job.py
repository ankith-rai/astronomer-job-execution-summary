"""Group attempts into jobs and compute the summary."""

from collections import defaultdict

from job_summary.models import JobAttempt, Status, Summary


def summarize(attempts: list[JobAttempt], *, skipped_records: int = 0) -> Summary:
    grouped: dict[str, list[JobAttempt]] = defaultdict(list)
    for attempt in attempts:
        grouped[attempt.job_id].append(attempt)

    successful = 0
    failed = 0
    incomplete = 0
    durations: list[float] = []
    retries: list[str] = []

    for job_id, rows in grouped.items():
        # Latest attempt wins. Earlier tries are history, same as a task instance row.
        latest = max(rows, key=lambda row: row.attempt)
        # A later try_number counts even when earlier rows are absent from the file.
        if latest.attempt >= 2:
            retries.append(job_id)
        if latest.status is Status.SUCCESS:
            successful += 1
            durations.append(latest.duration_seconds())
        elif latest.status is Status.FAILED:
            failed += 1
        else:
            incomplete += 1

    average = sum(durations) / len(durations) if durations else None
    return Summary(
        total_jobs=len(grouped),
        successful_jobs=successful,
        failed_jobs=failed,
        average_successful_job_duration_seconds=average,
        incomplete_jobs=incomplete,
        jobs_requiring_retries=sorted(retries),
        skipped_records=skipped_records,
    )
