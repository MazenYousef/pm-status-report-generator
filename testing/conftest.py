"""Shared pytest fixtures for the blackbox test suite. See testhelpers.py for
repo paths and credential/capability detection (plain constants, reused
directly by test modules for skipif conditions)."""

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from testhelpers import REPORTS_DIR, TEMPLATE_PATH  # noqa: E402


@pytest.fixture
def clean_reports_dir():
    """Snapshot reports/ before the test, delete any report_* files the test
    created afterward — CLI-invoking tests write into the real reports/ dir
    (main.py has no --output-dir flag), so cleanup must be automatic."""
    before = set(REPORTS_DIR.glob("report_*"))
    yield REPORTS_DIR
    after = set(REPORTS_DIR.glob("report_*"))
    for path in after - before:
        path.unlink()


@pytest.fixture
def no_template():
    """Temporarily remove templates/weekly_status_template.docx so a test can
    exercise the no-template PDF path, guaranteeing restoration afterward
    even if the test fails — this is a real checked-in asset, not disposable
    test data."""
    if not TEMPLATE_PATH.exists():
        yield
        return
    backup_path = Path(shutil.os.environ.get("TMPDIR", "/tmp")) / "weekly_status_template.docx.testbak"
    shutil.copy2(TEMPLATE_PATH, backup_path)
    TEMPLATE_PATH.unlink()
    try:
        yield
    finally:
        shutil.move(str(backup_path), str(TEMPLATE_PATH))
