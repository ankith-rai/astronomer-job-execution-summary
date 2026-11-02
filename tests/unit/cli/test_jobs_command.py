import json
from pathlib import Path

import pytest

from job_summary.cli import main
from job_summary.exceptions import FileError
from job_summary.io import load_records
from job_summary.models import SkipReason


EXAMPLE = Path(__file__).parents[3] / "examples" / "records.json"


def test_example_file_matches_the_readme_arithmetic() -> None:
    loaded = load_records(EXAMPLE)

    assert [skip.reason for skip in loaded.skips] == [SkipReason.MISSING_FIELD]
    assert len(loaded.attempts) == 6


def test_cli_prints_summary_json_and_skip_reasons(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(EXAMPLE)]) == 0

    captured = capsys.readouterr()
    assert captured.err == "skipped record 7: missing_field\n"
    summary = json.loads(captured.out)
    assert summary == {
        "total_jobs": 5,
        "successful_jobs": 3,
        "failed_jobs": 1,
        "average_successful_job_duration_seconds": 20.0,
        "incomplete_jobs": 1,
        "jobs_requiring_retries": ["job-a", "job-e"],
        "skipped_records": 1,
    }


def test_cli_rejects_a_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "missing.json"

    assert main([str(missing)]) == 1
    assert "cannot read" in capsys.readouterr().err


def test_cli_rejects_invalid_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{", encoding="utf-8")

    assert main([str(broken)]) == 1
    assert "invalid JSON" in capsys.readouterr().err


def test_cli_rejects_a_non_array_document(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    document = tmp_path / "object.json"
    document.write_text("{}", encoding="utf-8")

    assert main([str(document)]) == 1
    assert "JSON array" in capsys.readouterr().err


def test_load_records_raises_for_a_bad_file(tmp_path: Path) -> None:
    document = tmp_path / "object.json"
    document.write_text("[]", encoding="utf-8")
    assert load_records(document).attempts == []

    document.write_text("{}", encoding="utf-8")
    with pytest.raises(FileError):
        load_records(document)


def test_cli_requires_a_path() -> None:
    with pytest.raises(SystemExit) as exc:
        main([])

    assert exc.value.code == 2
