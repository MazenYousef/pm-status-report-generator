"""
PDF generation: no-template and with-template rendering, driven through the
real CLI (blackbox) and verified via pdftotext content extraction.

The other tests (missing-soffice, malformed-section robustness, missing
template placeholder) are deliberately NOT CLI-driven: there is no reliable
way to force those conditions end-to-end without either uninstalling
LibreOffice or getting Claude to emit a genuinely malformed report on
demand. They call generate_pdf.py's internal functions directly instead —
a documented, narrow exception to blackbox testing (see testing/README.md).
Only the two rendering tests actually need soffice installed, so only they
carry the HAS_SOFFICE skipif — the rest run unconditionally offline.
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import HAS_PDFTOTEXT, HAS_SOFFICE, SRC_DIR, TEMPLATE_PATH, pdf_to_text, run_cli  # noqa: E402

sys.path.insert(0, str(SRC_DIR))
import generate_pdf  # noqa: E402
from docx import Document  # noqa: E402

HEADINGS = ["Executive Summary", "Progress", "Risks & Blockers", "Upcoming", "Metrics"]


@pytest.mark.pdf
@pytest.mark.skipif(not HAS_SOFFICE, reason="LibreOffice (soffice) not installed")
@pytest.mark.skipif(not HAS_PDFTOTEXT, reason="pdftotext (poppler) not installed")
def test_no_template_pdf_contains_all_sections(clean_reports_dir, no_template):
    result = run_cli(["--sample", "--dry-run"], env_overrides={"ANTHROPIC_API_KEY": ""})
    assert result.returncode == 0, result.stderr

    pdf_files = list(clean_reports_dir.glob("report_*.pdf"))
    assert len(pdf_files) == 1
    text = pdf_to_text(pdf_files[0])
    for heading in HEADINGS:
        assert heading in text, f"Missing '{heading}' in no-template PDF"
    assert "Weekly Status Report" in text


@pytest.mark.pdf
@pytest.mark.skipif(not HAS_SOFFICE, reason="LibreOffice (soffice) not installed")
@pytest.mark.skipif(not HAS_PDFTOTEXT, reason="pdftotext (poppler) not installed")
def test_with_template_pdf_contains_branding_and_sections(clean_reports_dir):
    """Assumes templates/weekly_status_template.docx is present (the
    checked-in XYZ GmbH demo template) — skips if it isn't."""
    if not TEMPLATE_PATH.exists():
        pytest.skip("templates/weekly_status_template.docx not present")

    result = run_cli(["--sample", "--dry-run"], env_overrides={"ANTHROPIC_API_KEY": ""})
    assert result.returncode == 0, result.stderr

    pdf_files = list(clean_reports_dir.glob("report_*.pdf"))
    assert len(pdf_files) == 1
    text = pdf_to_text(pdf_files[0])
    assert "XYZ GmbH" in text
    for heading in HEADINGS:
        assert heading in text, f"Missing '{heading}' in with-template PDF"


@pytest.mark.offline
def test_missing_soffice_raises_clear_error():
    """Component-boundary: forces locate_soffice() to fail regardless of
    the real machine's LibreOffice install, and confirms the error message
    is actionable."""
    with mock.patch.object(generate_pdf.shutil, "which", return_value=None), \
         mock.patch.object(generate_pdf.Path, "exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="LibreOffice"):
            generate_pdf.locate_soffice()


@pytest.mark.offline
@pytest.mark.parametrize(
    "malformed_md",
    [
        "## Executive Summary\nEverything is fine.\n",  # missing other sections entirely
        "## Executive Summary\nFine.\n\n## Risks & Blockers\n",  # section with empty body
    ],
    ids=["missing-sections", "empty-section-body"],
)
def test_malformed_sections_do_not_crash_rendering(malformed_md):
    """Component-boundary: feeds hand-built malformed markdown directly into
    the section parser/renderer, since there's no reliable way to force
    Claude to produce malformed output on demand."""
    doc = Document()
    sections = generate_pdf.parse_report_sections(malformed_md)
    generate_pdf.render_sections_into_body(doc, sections)  # must not raise


@pytest.mark.offline
def test_template_missing_placeholder_raises_clear_error(tmp_path):
    """Component-boundary: a template without the {{p report_content}}
    paragraph should fail loudly and early, not silently produce a PDF
    missing the entire report body."""
    bad_template = tmp_path / "bad_template.docx"
    doc = Document()
    doc.add_paragraph("This template forgot the placeholder tag.")
    doc.save(str(bad_template))

    with pytest.raises(ValueError, match="report_content"):
        generate_pdf.fill_docx_template(bad_template, "## Executive Summary\nFine.\n")


@pytest.mark.offline
def test_template_with_placeholder_passes_validation(tmp_path):
    """Sanity-check the positive case: a template that does contain the tag
    should not raise from the validation step."""
    good_template = tmp_path / "good_template.docx"
    doc = Document()
    doc.add_paragraph("{{p report_content}}")
    doc.save(str(good_template))

    assert generate_pdf._template_has_placeholder(good_template) is True
