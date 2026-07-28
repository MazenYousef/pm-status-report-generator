"""Smoke tests: required files exist and runtime dependencies import cleanly."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import ROOT  # noqa: E402

pytestmark = pytest.mark.offline

REQUIRED_FILES = [
    "sample_data/github_sample_issues.json",
    "sample_data/jira_sample_issues.json",
    "reports/example_output_github.md",
    "reports/example_output_jira.md",
    "templates/README.md",
    ".env.example",
    "src/main.py",
    "src/config.py",
    "src/fetch_issues.py",
    "src/fetch_jira_issues.py",
    "src/generate_report.py",
    "src/generate_pdf.py",
]

REQUIRED_MODULES = ["anthropic", "requests", "dotenv", "docx", "docxtpl", "docxcompose"]


@pytest.mark.parametrize("relative_path", REQUIRED_FILES)
def test_required_file_exists(relative_path):
    assert (ROOT / relative_path).exists(), f"Missing required file: {relative_path}"


@pytest.mark.parametrize("module_name", REQUIRED_MODULES)
def test_dependency_importable(module_name):
    importlib.import_module(module_name)
