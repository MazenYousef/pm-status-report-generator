"""Output filename convention: report_<date>_<timestamp>.{md,pdf}."""

import re
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import run_cli  # noqa: E402

pytestmark = pytest.mark.offline

NAME_RE = re.compile(r"^report_\d{4}-\d{2}-\d{2}_\d{6}\.(md|pdf)$")


def test_filenames_match_date_timestamp_convention(clean_reports_dir):
    result = run_cli(["--sample", "--dry-run"], env_overrides={"ANTHROPIC_API_KEY": ""})
    assert result.returncode == 0, result.stderr

    new_files = list(clean_reports_dir.glob("report_*"))
    assert len(new_files) == 2
    for path in new_files:
        assert NAME_RE.match(path.name), f"Unexpected filename shape: {path.name}"


def test_repeated_runs_do_not_overwrite_each_other(clean_reports_dir):
    """Two runs at least a second apart must produce two distinct,
    non-overwriting file pairs. (Two runs within the same second would
    collide on the HHMMSS-granularity timestamp — a known, accepted
    limitation, not exercised here.)"""
    before = set(clean_reports_dir.glob("report_*"))

    result1 = run_cli(["--sample", "--dry-run"], env_overrides={"ANTHROPIC_API_KEY": ""})
    assert result1.returncode == 0, result1.stderr
    time.sleep(1.1)
    result2 = run_cli(["--sample", "--dry-run"], env_overrides={"ANTHROPIC_API_KEY": ""})
    assert result2.returncode == 0, result2.stderr

    after = set(clean_reports_dir.glob("report_*"))
    new_files = after - before
    assert len(new_files) == 4, f"Expected 2 distinct pairs (4 files), got {new_files}"
