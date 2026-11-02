"""One execution attempt of a job."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"


@dataclass(frozen=True)
class JobAttempt:
    job_id: str
    status: Status
    started_at: datetime
    finished_at: datetime | None
    attempt: int

    def duration_seconds(self) -> float:
        if self.finished_at is None:
            raise ValueError(f"{self.job_id} attempt {self.attempt} has no finished_at")
        return (self.finished_at - self.started_at).total_seconds()
