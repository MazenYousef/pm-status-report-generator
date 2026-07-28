# Blackbox regression test suite

A regression suite for the PM status report generator, built around invoking the real CLI
(`python3 src/main.py`) and inspecting its outputs — the way an actual user would exercise the
tool — rather than importing internal functions wherever avoidable.

## ⚠️ Running with real credentials makes real, billable API calls

This suite auto-adapts to whatever is configured in the repo's `.env`. Tests that need real
credentials (a live GitHub token, live Jira credentials, a real Anthropic API key) are
**included**, not left out — but each one is individually skipped with a clear reason if the
relevant credentials aren't configured. If you **do** have a real `ANTHROPIC_API_KEY` (or GitHub/
Jira credentials) in `.env`, running the full suite will make genuine, billable calls to those
services. Blank/comment out credentials you don't want exercised before running if that matters
to you.

## Two tiers of test

1. **Blackbox (CLI-driven)** — the large majority of tests: they run `python3 src/main.py` with
   various flags/env vars as a real subprocess and assert on its exit code, stdout, and the files
   it writes under `reports/`. This is how the tool is actually used, so this is where most
   coverage lives.
2. **Component-boundary** — a small, explicitly-labeled minority (in `test_pdf_generation.py`'s
   missing-soffice/malformed-section tests, and all of `test_jira_fetcher.py`/
   `test_github_fetcher.py`) that call internal functions directly or mock the HTTP layer
   (`requests.get`). These exist because some conditions genuinely can't be forced end-to-end
   without either a live Jira instance or deliberately broken input Claude won't reliably produce
   on demand — mocking the network boundary is the only way to test JQL construction, ADF
   parsing, and the missing-credentials/missing-`soffice` error paths at all. Every such test says
   so in its module or function docstring.

## Setup

```bash
pip3 install -r ../requirements.txt -r requirements.txt
```

(The main tool's own dependencies are needed too, since these tests import `src/` directly for
the component-boundary cases and shell out to the real CLI for the rest.)

## Running

```bash
python3 run_tests.py                # everything
python3 run_tests.py -k jira         # anything matching "jira" (pytest -k passthrough)
python3 run_tests.py -m offline      # only the always-run, no-credentials-needed tests
python3 run_tests.py -m "not live"   # skip the live/credentialed tier explicitly
```

Any extra arguments are passed straight through to `pytest`. Every run writes both
`reports/test_report_<date>_<timestamp>.md` and `reports/test_report_<date>_<timestamp>.html` —
see `reports/example_test_report.md` / `.html` for what a run looks like. Exits with pytest's own
exit code (non-zero if anything failed).

## What gets skipped, and why

| Requires | Skipped when | Detected in |
|---|---|---|
| Real `GITHUB_TOKEN` + `GITHUB_REPO` | Either is empty or still the literal `.env.example` placeholder | `testhelpers.HAS_GITHUB_CREDS` |
| Real `JIRA_BASE_URL`/`JIRA_EMAIL`/`JIRA_API_TOKEN` | Any is empty or still the placeholder | `testhelpers.HAS_JIRA_CREDS` |
| Real `ANTHROPIC_API_KEY` | Empty or still the placeholder | `testhelpers.HAS_ANTHROPIC_KEY` |
| LibreOffice (`soffice`) installed | `generate_pdf.locate_soffice()` can't find it | `testhelpers.HAS_SOFFICE` |
| `pdftotext` (poppler) installed | Not on `PATH` | `testhelpers.HAS_PDFTOTEXT` |

Placeholder detection is an exact match against the values shipped in `.env.example` — it catches
"never edited the file" but won't catch a fake-but-different value you typed in yourself. That's
a known, accepted limitation, not a bug.

## Cleanup discipline

Every CLI-invoking test uses the `clean_reports_dir` fixture (`conftest.py`), which snapshots
`reports/` before the test and deletes anything new it created afterward — the tool has no
`--output-dir` flag, so tests necessarily write into the real `reports/` directory, and this
fixture guarantees the suite never leaves stray artifacts behind. The `no_template` fixture
similarly guarantees `templates/weekly_status_template.docx` (a real checked-in asset, not
disposable test data) is restored even if a test crashes mid-run.

## Adding a new test case

Add a function to the relevant file under `testcases/` (or a new file, following the
`test_*.py` naming pytest expects). Mark it `@pytest.mark.offline`, `@pytest.mark.live`, or
`@pytest.mark.pdf` depending on what it needs, and use the `skipif` pattern already used
throughout for anything credential- or capability-gated.
