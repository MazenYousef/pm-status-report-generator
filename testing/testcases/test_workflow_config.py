"""
Lightweight sanity check of the GitHub Actions workflow: plain text/regex
assertions on expected substrings, not a full YAML parse (avoids adding
PyYAML as a dependency just for this).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import ROOT  # noqa: E402

pytestmark = pytest.mark.offline

WORKFLOW_PATH = ROOT / ".github" / "workflows" / "weekly-report.yml"

EXPECTED_SUBSTRINGS = [
    "cron:",
    "workflow_dispatch",
    "Install LibreOffice",
    "python src/main.py",
    "git add reports/",
]


def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists()


@pytest.mark.parametrize("expected", EXPECTED_SUBSTRINGS)
def test_workflow_contains_expected_substring(expected):
    content = WORKFLOW_PATH.read_text()
    assert expected in content, f"Expected '{expected}' in weekly-report.yml"
