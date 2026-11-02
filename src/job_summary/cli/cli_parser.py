"""Parse arguments and dispatch to the jobs command."""

import argparse
from pathlib import Path

from job_summary.cli.commands.jobs_command import jobs_summary


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize job execution attempts from a JSON file")
    parser.add_argument("path", type=Path, help="JSON array of job attempts")
    return parser


def main(argv: list[str] | None = None) -> int:
    return jobs_summary(get_parser().parse_args(argv))
