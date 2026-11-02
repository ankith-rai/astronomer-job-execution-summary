"""Run the installed command the way a person would from a shell."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[2]
EXAMPLE = ROOT / "examples" / "records.json"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "job_summary", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_sample_file_scenario() -> None:
    completed = _run(str(EXAMPLE))

    assert completed.returncode == 0
    assert completed.stderr == "skipped record 7: missing_field\n"
    assert json.loads(completed.stdout) == {
        "total_jobs": 5,
        "successful_jobs": 3,
        "failed_jobs": 1,
        "average_successful_job_duration_seconds": 20.0,
        "incomplete_jobs": 1,
        "jobs_requiring_retries": ["job-a", "job-e"],
        "skipped_records": 1,
    }


def test_missing_file_scenario(tmp_path: Path) -> None:
    completed = _run(str(tmp_path / "missing.json"))

    assert completed.returncode == 1
    assert "cannot read" in completed.stderr
    assert completed.stdout == ""
