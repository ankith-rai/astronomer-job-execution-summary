"""Domain records for one attempt and the summary of many."""

from job_summary.models.attempt import JobAttempt, Status
from job_summary.models.skip import Skip, SkipReason
from job_summary.models.summary import Summary

__all__ = ["JobAttempt", "Skip", "SkipReason", "Status", "Summary"]
