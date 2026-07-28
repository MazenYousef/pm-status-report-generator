#!/usr/bin/env python3
"""
Blackbox regression test runner.

Usage:
    python3 testing/run_tests.py                # run everything
    python3 testing/run_tests.py -k jira         # any extra args are passed through to pytest
    python3 testing/run_tests.py -m offline      # only the always-run, no-credentials-needed tests

Runs the suite under testing/testcases/ via pytest, then writes both a
Markdown and an HTML report to testing/reports/, named
test_report_<date>_<timestamp>.{md,html} — the same naming convention the
tool itself uses for its generated reports.
"""

import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

TESTING_DIR = Path(__file__).resolve().parent
REPORTS_DIR = TESTING_DIR / "reports"

sys.path.insert(0, str(TESTING_DIR))
from report_writer import parse_junit_xml, render_markdown, render_html  # noqa: E402


def main():
    extra_args = sys.argv[1:]
    REPORTS_DIR.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        junit_path = Path(tmp) / "junit.xml"
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                str(TESTING_DIR / "testcases"),
                "-v",
                f"--junit-xml={junit_path}",
                *extra_args,
            ],
            cwd=TESTING_DIR,
        )

        if not junit_path.exists():
            print("\npytest did not produce a JUnit XML report — no test report written.", file=sys.stderr)
            return result.returncode

        report = parse_junit_xml(junit_path)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    md_path = REPORTS_DIR / f"test_report_{stamp}.md"
    html_path = REPORTS_DIR / f"test_report_{stamp}.html"

    md_path.write_text(render_markdown(report))
    html_path.write_text(render_html(report))

    print(f"\nMarkdown report: {md_path}")
    print(f"HTML report:     {html_path}")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
