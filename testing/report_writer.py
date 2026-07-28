"""
Parses pytest's JUnit XML output into a plain result structure, then renders
that single structure as either Markdown or HTML — so the two report formats
can never drift out of sync with each other.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any


def parse_junit_xml(xml_path) -> dict[str, Any]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    suite = root.find("testsuite") if root.tag == "testsuites" else root

    tests = []
    for case in suite.findall("testcase"):
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        duration = float(case.get("time", 0.0))

        skipped = case.find("skipped")
        failure = case.find("failure")
        error = case.find("error")

        if failure is not None:
            status, message = "failed", failure.get("message", "") or (failure.text or "")
        elif error is not None:
            status, message = "error", error.get("message", "") or (error.text or "")
        elif skipped is not None:
            status, message = "skipped", skipped.get("message", "") or (skipped.text or "")
        else:
            status, message = "passed", ""

        tests.append({
            "name": name,
            "status": status,
            "duration": duration,
            "message": message.strip(),
        })

    return {
        "tests": tests,
        "total": len(tests),
        "passed": sum(1 for t in tests if t["status"] == "passed"),
        "failed": sum(1 for t in tests if t["status"] in ("failed", "error")),
        "skipped": sum(1 for t in tests if t["status"] == "skipped"),
        "duration": float(suite.get("time", 0.0)),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def render_markdown(report: dict[str, Any]) -> str:
    overall = "PASS" if report["failed"] == 0 else "FAIL"
    lines = [
        "# Blackbox Test Report",
        f"_Generated {report['generated_at']}_",
        "",
        "## Executive Summary",
        f"Overall status: **{overall}**. {report['total']} test(s) ran in "
        f"{report['duration']:.2f}s — {report['passed']} passed, {report['failed']} failed, "
        f"{report['skipped']} skipped.",
        "",
        "## Results",
        "| Test | Status | Duration (s) | Note |",
        "|---|---|---|---|",
    ]
    for t in report["tests"]:
        note = t["message"].splitlines()[0] if t["message"] else ""
        note = note.replace("|", "\\|")
        lines.append(f"| {t['name']} | {t['status'].upper()} | {t['duration']:.2f} | {note} |")

    failures = [t for t in report["tests"] if t["status"] in ("failed", "error")]
    if failures:
        lines += ["", "## Failures"]
        for t in failures:
            lines += [f"### {t['name']}", "```", t["message"] or "(no message)", "```"]

    return "\n".join(lines) + "\n"


_STATUS_COLORS = {
    "passed": "#1e8e3e",
    "failed": "#d93025",
    "error": "#d93025",
    "skipped": "#b8860b",
}


def render_html(report: dict[str, Any]) -> str:
    overall = "PASS" if report["failed"] == 0 else "FAIL"
    overall_color = _STATUS_COLORS["passed"] if overall == "PASS" else _STATUS_COLORS["failed"]

    rows = []
    for t in report["tests"]:
        color = _STATUS_COLORS.get(t["status"], "#333")
        note = (t["message"].splitlines()[0] if t["message"] else "").replace("<", "&lt;").replace(">", "&gt;")
        rows.append(
            f"<tr><td>{t['name']}</td>"
            f'<td style="color:{color};font-weight:600">{t["status"].upper()}</td>'
            f"<td>{t['duration']:.2f}</td><td>{note}</td></tr>"
        )

    failures = [t for t in report["tests"] if t["status"] in ("failed", "error")]
    failures_html = ""
    if failures:
        blocks = []
        for t in failures:
            msg = (t["message"] or "(no message)").replace("<", "&lt;").replace(">", "&gt;")
            blocks.append(f"<h3>{t['name']}</h3><pre>{msg}</pre>")
        failures_html = "<h2>Failures</h2>" + "".join(blocks)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Blackbox Test Report</title>
<style>
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; max-width: 900px;
          margin: 2rem auto; padding: 0 1rem; color: #1b1b1b; }}
  h1 {{ margin-bottom: 0.2rem; }}
  .timestamp {{ color: #666; font-size: 0.9rem; margin-top: 0; }}
  .summary {{ padding: 1rem; border-radius: 8px; background: #f4f4f5; margin: 1rem 0; }}
  .summary .status {{ font-weight: 700; color: {overall_color}; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #e5e5e5; font-size: 0.92rem; }}
  th {{ background: #fafafa; }}
  pre {{ background: #f4f4f5; padding: 0.75rem; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; }}
</style>
</head>
<body>
<h1>Blackbox Test Report</h1>
<p class="timestamp">Generated {report['generated_at']}</p>
<div class="summary">
  Overall status: <span class="status">{overall}</span> &mdash;
  {report['total']} test(s) in {report['duration']:.2f}s:
  {report['passed']} passed, {report['failed']} failed, {report['skipped']} skipped.
</div>
<table>
  <thead><tr><th>Test</th><th>Status</th><th>Duration (s)</th><th>Note</th></tr></thead>
  <tbody>
    {''.join(rows)}
  </tbody>
</table>
{failures_html}
</body>
</html>
"""
