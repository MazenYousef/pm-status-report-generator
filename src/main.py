"""
CLI entry point.

Usage:
    python src/main.py                # fetch live from the configured issue tracker (GitHub or Jira), call Claude
    python src/main.py --sample       # use bundled sample data, calls Claude
    python src/main.py --dry-run      # fetch live issues, print prompt, skip Claude call
    python src/main.py --sample --dry-run
        # no API calls at all: writes report_<date>_<timestamp>.md/.pdf from the
        # bundled reports/example_output_github.md or example_output_jira.md sample
        # report (matching ISSUE_TRACKER), useful for testing the PDF pipeline (or a
        # custom templates/weekly_status_template.docx) for free
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from config import load_config
from fetch_issues import fetch_issues as fetch_github_issues
from fetch_jira_issues import fetch_issues as fetch_jira_issues
from generate_report import generate_report, build_user_prompt
from generate_pdf import generate_pdf_report, TEMPLATE_FILENAME

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_GITHUB = ROOT / "sample_data" / "github_sample_issues.json"
SAMPLE_DATA_JIRA = ROOT / "sample_data" / "jira_sample_issues.json"
SAMPLE_REPORT_GITHUB = ROOT / "reports" / "example_output_github.md"
SAMPLE_REPORT_JIRA = ROOT / "reports" / "example_output_jira.md"
REPORTS_DIR = ROOT / "reports"
TEMPLATES_DIR = ROOT / "templates"


def main():
    parser = argparse.ArgumentParser(description="Generate an AI-powered PM status report.")
    parser.add_argument("--sample", action="store_true", help="Use bundled sample data instead of a live fetch from GitHub or Jira")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Skip the Claude API call. Alone: fetch live issues and just print the "
            "prompt. With --sample: also write report_<date>_<timestamp>.md/.pdf from "
            "the bundled sample report, no API key needed."
        ),
    )
    args = parser.parse_args()

    cfg = load_config()

    if args.sample:
        if cfg.issue_tracker == "jira":
            issues = json.loads(SAMPLE_DATA_JIRA.read_text(encoding="utf-8"))
            source_label = "UGW"
        else:
            issues = json.loads(SAMPLE_DATA_GITHUB.read_text(encoding="utf-8"))
            source_label = "sample/demo-repo"
    elif cfg.issue_tracker == "jira":
        issues = fetch_jira_issues(cfg)
        source_label = cfg.jira_project_key or cfg.jira_base_url
    else:
        issues = fetch_github_issues(cfg)
        source_label = cfg.github_repo

    print(f"Fetched {len(issues)} issue(s) from {source_label}.")

    if args.dry_run and not args.sample:
        print("\n--- Prompt that would be sent to Claude ---\n")
        print(build_user_prompt(issues, source_label)[:2000])
        return

    if args.dry_run:
        print(
            "\n--dry-run + --sample: using the bundled sample report instead of "
            "calling Claude (no API call made).\n"
        )
        sample_report = SAMPLE_REPORT_JIRA if cfg.issue_tracker == "jira" else SAMPLE_REPORT_GITHUB
        report_md = sample_report.read_text(encoding="utf-8")
    else:
        report_md = generate_report(issues, cfg, source_label)

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y-%m-%d_%H%M%S")

    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / f"report_{stamp}.md"
    out_path.write_text(report_md, encoding="utf-8")

    print(f"\nReport written to {out_path}\n")
    print(report_md)

    pdf_path = REPORTS_DIR / f"report_{stamp}.pdf"
    template_path = TEMPLATES_DIR / TEMPLATE_FILENAME
    try:
        generate_pdf_report(report_md, source_label, today, pdf_path, template_path)
        print(f"PDF report written to {pdf_path}")
    except FileNotFoundError as e:
        print(f"\nPDF generation skipped: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nPDF generation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\nPDF generation failed — invalid template: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nPDF generation failed unexpectedly: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
