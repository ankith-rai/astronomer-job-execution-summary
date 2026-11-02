"""A row that was read and not used."""

from dataclasses import dataclass


class SkipReason:
    MISSING_FIELD = "missing_field"
    BAD_TYPE = "bad_type"
    BAD_TIMESTAMP = "bad_timestamp"
    NEGATIVE_DURATION = "negative_duration"
    UNKNOWN_STATUS = "unknown_status"
    DUPLICATE_ATTEMPT = "duplicate_attempt"


@dataclass(frozen=True)
class Skip:
    index: int
    reason: str
