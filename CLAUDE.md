# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A small automation pipeline that turns issue-tracker activity (GitHub or Jira) into a
Claude-written, stakeholder-ready weekly PM status report, run on a schedule via GitHub Actions.

## Commands

```bash
pip3 install -r requirements.txt
cp .env.example .env   # fill in GITHUB_TOKEN/GITHUB_REPO (default) or JIRA_* vars, + ANTHROPIC_API_KEY

python3 src/main.py --sample --dry-run   # no API key needed: writes report_<date>_<timestamp>.md/.pdf from the bundled sample report matching ISSUE_TRACKER
python3 src/main.py --dry-run            # live fetch, no --sample: just prints the prompt that would be sent, writes no files
python3 src/main.py --sample             # uses sample data but calls the real Claude API (needs ANTHROPIC_API_KEY)
python3 src/main.py                      # full run: live fetch (GitHub or Jira, per ISSUE_TRACKER) + Claude generation, writes reports/report_<date>_<timestamp>.md and .pdf
```

There is no linter or build step in this repo. There is a blackbox regression test suite under
`testing/` — see the Testing section below.

**System dependency**: PDF generation shells out to headless LibreOffice (`soffice`) to convert
an intermediate `.docx` to PDF. Install with `brew install --cask libreoffice` (macOS) or
`sudo apt-get install -y libreoffice --no-install-recommends` (Linux/CI). On macOS, `soffice`
isn't on `PATH` by default even after a Homebrew install — `generate_pdf.locate_soffice()`
falls back to the LibreOffice.app bundle path, so this isn't usually something you need to fix.

## Architecture

Five modules in `src/`, wired together by `src/main.py`:

```
Issue Tracker (GitHub / Jira)  ─▶  fetch_issues.py / fetch_jira_issues.py  ─▶  generate_report.py (Claude API)  ─▶  reports/report_<date>_<timestamp>.md
                                                                                          │
                                                              templates/weekly_status_template.docx (optional)
                                                                                          │
                                                                                          ▼
                                                              generate_pdf.py ─▶ LibreOffice ─▶ reports/report_<date>_<timestamp>.pdf
```

Filenames include both date and a `HHMMSS` timestamp so repeated same-day runs (e.g. local
testing, or a manual `workflow_dispatch` re-run) don't overwrite each other.

- **`config.py`** — `load_config()` reads all settings from environment variables (via `.env` locally,
  or injected directly in CI) into a `Config` dataclass. This is the single source of truth for config;
  nothing else reads `os.environ` directly.
- **`fetch_issues.py`** / **`fetch_jira_issues.py`** — the tracker-specific modules. Each hits its
  tracker's REST API and normalizes results into the identical flat list-of-dicts shape (number,
  title, state, labels, assignee, timestamps, truncated body, comment count) — `fetch_jira_issues.py`
  additionally builds a JQL query from `issue_state`/`issue_labels`/`lookback_days` (`_build_jql()`)
  and flattens Jira's Atlassian Document Format `description` field to plain text (`_adf_to_text()`).
  `main.py` dispatches between them based on `Config.issue_tracker` (`"github"` or `"jira"`, from
  `ISSUE_TRACKER`). To support another tracker, add a `fetch_<tracker>_issues.py` returning that same
  shape and extend the dispatch — nothing downstream needs to change.
- **`generate_report.py`** — turns the issue list into a prompt and calls the Claude API. `SYSTEM_PROMPT`
  is where the PM judgment lives: it enforces a fixed report structure (Executive Summary → Progress →
  Risks & Blockers → Upcoming → Metrics) and instructs the model to flag stale/unassigned issues as
  process risks. Editing report structure or tone means editing this constant, not the calling code.
- **`generate_pdf.py`** — turns the generated Markdown into a PDF. `parse_report_sections()` splits
  the report into an ordered `{heading: body}` dict on `##` headings. `render_sections_into_body()`
  is the shared renderer (headings, bullet lists — including multi-line-wrapped bullets merged back
  into one, a real Word table for the Metrics section, `**bold**` spans) and works against either a
  `docx.Document` or a `docxtpl` `Subdoc`, since both expose the same
  `add_heading`/`add_paragraph`/`add_table` API — this is what lets the same rendering logic serve
  both code paths below. If `templates/weekly_status_template.docx` exists,
  `fill_docx_template()` fills its `{{p report_content}}` placeholder via `docxtpl`, preserving
  everything else in the template; otherwise `build_docx_from_scratch()` builds a plain document.
  Either way, `convert_docx_to_pdf()` shells out to `soffice --headless --convert-to pdf` (located via
  `locate_soffice()`) to produce the final PDF. `generate_pdf_report()` is the single entry point
  `main.py` calls, and builds the intermediate `.docx` in a `tempfile.TemporaryDirectory()` — it's
  never written into `reports/`.
- **`main.py`** — CLI entry point wiring the above together. Dispatches to `fetch_github_issues` or
  `fetch_jira_issues` based on `cfg.issue_tracker`, producing a `source_label` (repo name or Jira
  project key) that flows through `build_user_prompt`/`generate_report`/`generate_pdf_report` —
  nothing tracker-specific below the fetch step. `--sample` uses `sample_data/github_sample_issues.json`
  or `sample_data/jira_sample_issues.json` instead of live fetch, also picked by `issue_tracker`.
  `--dry-run` alone (live fetch) prints the prompt and returns before any API call or file write.
  `--dry-run` combined with `--sample` skips Claude entirely and instead feeds the matching bundled
  canned report (`reports/example_output_github.md` or `reports/example_output_jira.md`) through
  the normal md-write + PDF-generation path — the way to test the PDF/template pipeline with zero
  API calls, for either tracker.

## Automation

`.github/workflows/weekly-report.yml` runs every Monday 07:00 UTC (or manually via
`workflow_dispatch`), installs LibreOffice, executes `python src/main.py` (the workflow uses
`python`/`pip` directly, not `python3`/`pip3`, since `actions/setup-python` aliases them on the
runner) against the current repo,
and commits the generated `.md`/`.pdf` straight into `reports/` if the diff is non-empty. Secrets
(`ANTHROPIC_API_KEY`) must be configured in the repo's Actions secrets; `GITHUB_TOKEN` is the default
Actions token. The workflow defaults to `ISSUE_TRACKER=github` (unset); switching the scheduled run
to Jira means adding `ISSUE_TRACKER=jira` and the `JIRA_*` variables to the workflow's `env:` block
and as Actions secrets — the workflow file itself isn't preconfigured for that.

## Testing

```bash
pip3 install -r requirements.txt -r testing/requirements.txt
python3 testing/run_tests.py            # everything; writes reports to testing/reports/
python3 testing/run_tests.py -m offline # only the always-run, no-credentials-needed subset
```

pytest-based, mostly blackbox (drives the real CLI as a subprocess and inspects `reports/`
output), with a small labeled component-boundary tier (`test_jira_fetcher.py`,
`test_github_fetcher.py`, and two tests in `test_pdf_generation.py`) for conditions that can't be
forced end-to-end (JQL/ADF logic, missing-`soffice`, malformed sections). Tests needing real
credentials (`test_cli_live.py`) auto-`skipif` via `testhelpers.HAS_GITHUB_CREDS`/`HAS_JIRA_CREDS`/
`HAS_ANTHROPIC_KEY` (placeholder-aware, reusing `config.load_config()`) — running with real
credentials configured makes real, billable API calls. See `testing/README.md` for the full
picture.
