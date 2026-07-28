"""
--sample --dry-run for both trackers: the fully offline path, zero API keys
needed. ANTHROPIC_API_KEY is explicitly forced empty to prove there really is
no dependency on it.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import ROOT, run_cli  # noqa: E402

pytestmark = pytest.mark.offline


@pytest.mark.parametrize(
    "tracker_env, expected_label, canned_report",
    [
        ({}, "sample/demo-repo", "example_output_github.md"),
        ({"ISSUE_TRACKER": "github"}, "sample/demo-repo", "example_output_github.md"),
        ({"ISSUE_TRACKER": "jira"}, "UGW", "example_output_jira.md"),
    ],
    ids=["tracker-unset", "tracker-github", "tracker-jira"],
)
def test_sample_dry_run(clean_reports_dir, tracker_env, expected_label, canned_report):
    env = {"ANTHROPIC_API_KEY": "", **tracker_env}
    result = run_cli(["--sample", "--dry-run"], env_overrides=env)

    assert result.returncode == 0, result.stderr
    assert f"Fetched 5 issue(s) from {expected_label}." in result.stdout
    assert "no API call made" in result.stdout

    md_files = sorted(clean_reports_dir.glob("report_*.md"))
    pdf_files = sorted(clean_reports_dir.glob("report_*.pdf"))
    assert len(md_files) == 1, f"Expected exactly one new .md file, found {md_files}"
    assert len(pdf_files) == 1, f"Expected exactly one new .pdf file, found {pdf_files}"

    expected_content = (ROOT / "reports" / canned_report).read_text(encoding="utf-8")
    assert md_files[0].read_text(encoding="utf-8") == expected_content
    assert pdf_files[0].stat().st_size > 0


def test_output_md_is_valid_utf8_and_preserves_em_dash(clean_reports_dir):
    """Regression test: main.py's read_text()/write_text() calls must pass
    encoding="utf-8" explicitly — pathlib defaults to the locale-preferred
    encoding (commonly cp1252 on Windows), and the canned reports contain an
    em dash (—), which would raise UnicodeEncodeError under that default."""
    result = run_cli(["--sample", "--dry-run"], env_overrides={"ANTHROPIC_API_KEY": ""})
    assert result.returncode == 0, result.stderr

    md_files = list(clean_reports_dir.glob("report_*.md"))
    assert len(md_files) == 1

    raw_bytes = md_files[0].read_bytes()
    assert "—".encode("utf-8") in raw_bytes, "Expected UTF-8-encoded em dash in output"
    # Round-trips cleanly as UTF-8 (would raise UnicodeDecodeError otherwise)
    raw_bytes.decode("utf-8")


def test_dry_run_without_sample_is_prompt_preview_only(clean_reports_dir):
    """A plain --dry-run (no --sample) still needs a live tracker fetch to
    succeed before it can print anything (see test_cli_live.py) — this test
    only covers the --sample combination's early-return semantics, i.e. that
    --dry-run --sample never falls through to a live Claude call regardless
    of tracker."""
    result = run_cli(["--sample", "--dry-run"], env_overrides={"ANTHROPIC_API_KEY": ""})
    assert "Prompt that would be sent to Claude" not in result.stdout
