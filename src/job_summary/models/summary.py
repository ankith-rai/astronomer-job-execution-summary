"""The summary printed for a file of attempts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Summary:
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    average_successful_job_duration_seconds: float | None
    incomplete_jobs: int
    jobs_requiring_retries: list[str]
    skipped_records: int

    def to_dict(self) -> dict[str, object]:
        return {
            "total_jobs": self.total_jobs,
            "successful_jobs": self.successful_jobs,
            "failed_jobs": self.failed_jobs,
            "average_successful_job_duration_seconds": self.average_successful_job_duration_seconds,
            "incomplete_jobs": self.incomplete_jobs,
            "jobs_requiring_retries": self.jobs_requiring_retries,
            "skipped_records": self.skipped_records,
        }
