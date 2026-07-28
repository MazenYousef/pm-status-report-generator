"""
Live, credentialed CLI paths: real GitHub/Jira fetches and real Claude API
calls. Each test is skipif-gated on the relevant real (non-placeholder)
credentials being present in .env — see testhelpers.py for detection.

WARNING: any test here that actually runs (because credentials ARE
configured) makes a real, billable API call.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import HAS_ANTHROPIC_KEY, HAS_GITHUB_CREDS, HAS_JIRA_CREDS, run_cli  # noqa: E402

pytestmark = pytest.mark.live

HEADINGS = [
    "## Executive Summary",
    "## Progress",
    "## Risks & Blockers",
    "## Upcoming / Next Steps",
    "## Metrics",
]


@pytest.mark.skipif(not HAS_GITHUB_CREDS, reason="GITHUB_TOKEN/GITHUB_REPO not configured with real values")
def test_dry_run_live_github(clean_reports_dir):
    result = run_cli(["--dry-run"], env_overrides={"ISSUE_TRACKER": "github"})
    assert result.returncode == 0, result.stderr
    assert "Prompt that would be sent to Claude" in result.stdout
    assert list(clean_reports_dir.glob("report_*")) == []


@pytest.mark.skipif(not HAS_JIRA_CREDS, reason="JIRA_BASE_URL/JIRA_EMAIL/JIRA_API_TOKEN not configured with real values")
def test_dry_run_live_jira(clean_reports_dir):
    result = run_cli(["--dry-run"], env_overrides={"ISSUE_TRACKER": "jira"})
    assert result.returncode == 0, result.stderr
    assert "Prompt that would be sent to Claude" in result.stdout
    assert list(clean_reports_dir.glob("report_*")) == []


@pytest.mark.skipif(not HAS_ANTHROPIC_KEY, reason="ANTHROPIC_API_KEY not configured with a real value")
@pytest.mark.parametrize("tracker", ["github", "jira"], ids=["github-sample", "jira-sample"])
def test_sample_real_claude_call(clean_reports_dir, tracker):
    result = run_cli(["--sample"], env_overrides={"ISSUE_TRACKER": tracker})
    assert result.returncode == 0, result.stderr

    md_files = list(clean_reports_dir.glob("report_*.md"))
    pdf_files = list(clean_reports_dir.glob("report_*.pdf"))
    assert len(md_files) == 1
    assert len(pdf_files) == 1

    report_text = md_files[0].read_text()
    for heading in HEADINGS:
        assert heading in report_text, f"Missing '{heading}' in real Claude output"


@pytest.mark.skipif(not (HAS_GITHUB_CREDS and HAS_ANTHROPIC_KEY), reason="requires real GitHub creds + ANTHROPIC_API_KEY")
def test_full_live_run_github(clean_reports_dir):
    result = run_cli([], env_overrides={"ISSUE_TRACKER": "github"})
    assert result.returncode == 0, result.stderr
    _assert_full_run_outputs(clean_reports_dir)


@pytest.mark.skipif(not (HAS_JIRA_CREDS and HAS_ANTHROPIC_KEY), reason="requires real Jira creds + ANTHROPIC_API_KEY")
def test_full_live_run_jira(clean_reports_dir):
    result = run_cli([], env_overrides={"ISSUE_TRACKER": "jira"})
    assert result.returncode == 0, result.stderr
    _assert_full_run_outputs(clean_reports_dir)


def _assert_full_run_outputs(reports_dir):
    name_re = re.compile(r"^report_\d{4}-\d{2}-\d{2}_\d{6}\.(md|pdf)$")
    new_files = list(reports_dir.glob("report_*"))
    assert len(new_files) == 2
    for path in new_files:
        assert name_re.match(path.name)
        assert path.stat().st_size > 0
