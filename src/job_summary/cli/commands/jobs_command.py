"""Print a summary of job execution attempts."""

import argparse
import json
import sys

from job_summary.exceptions import FileError
from job_summary.io import load_records
from job_summary.jobs import summarize


def jobs_summary(args: argparse.Namespace) -> int:
    try:
        loaded = load_records(args.path)
    except FileError as exc:
        print(exc, file=sys.stderr)
        return 1

    for skip in loaded.skips:
        print(f"skipped record {skip.index + 1}: {skip.reason}", file=sys.stderr)

    summary = summarize(loaded.attempts, skipped_records=len(loaded.skips))
    json.dump(summary.to_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0
