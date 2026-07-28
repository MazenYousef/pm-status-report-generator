"""
Renders a generated status report (Markdown) into a PDF, optionally using a
PM-supplied Word template (templates/weekly_status_template.docx).

If the template exists, its `{{p report_content}}` placeholder is filled in
via docxtpl, preserving everything else in the template (letterhead, cover
page, headers/footers). If it doesn't exist, a plain Word document is built
from scratch instead. Either way, the resulting .docx is converted to PDF
with headless LibreOffice (soffice), since that's the only free,
cross-platform way to get real Word-fidelity PDF output.
"""

import platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from docx import Document
from docxtpl import DocxTemplate

TEMPLATE_FILENAME = "weekly_status_template.docx"

_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_TABLE_SEP_RE = re.compile(r"^:?-+:?$")


def parse_report_sections(report_md: str) -> dict[str, str]:
    """Split a report into an ordered {heading: body} dict, one entry per
    `##` heading. Any preamble before the first heading is discarded. A
    report missing a section simply won't have that key."""
    matches = list(_HEADING_RE.finditer(report_md))
    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(report_md)
        sections[match.group(1)] = report_md[start:end].strip("\n")
    return sections


def _add_bold_aware_runs(paragraph: Any, text: str) -> None:
    parts = _BOLD_RE.split(text)
    for i, part in enumerate(parts):
        if not part:
            continue
        run = paragraph.add_run(part)
        if i % 2 == 1:
            run.bold = True


def _split_table_row(line: str) -> list[str]:
    cells = line.strip().split("|")
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _render_table_block(target: Any, lines: list[str]) -> None:
    rows = [_split_table_row(line) for line in lines]
    rows = [row for row in rows if not all(_TABLE_SEP_RE.match(c) for c in row)]
    if not rows:
        return
    n_cols = max(len(row) for row in rows)
    table = target.add_table(rows=len(rows), cols=n_cols)
    table.style = "Table Grid"
    for r, row in enumerate(rows):
        for c in range(n_cols):
            value = row[c] if c < len(row) else ""
            cell = table.cell(r, c)
            cell.text = ""
            para = cell.paragraphs[0]
            run = para.add_run(value)
            if r == 0:
                run.bold = True


def _render_bullet_block(target: Any, lines: list[str]) -> None:
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullets.append(stripped[2:].strip())
        elif bullets:
            bullets[-1] = f"{bullets[-1]} {stripped}"
        else:
            bullets.append(stripped)
    for bullet in bullets:
        para = target.add_paragraph(style="List Bullet")
        _add_bold_aware_runs(para, bullet)


def _render_prose_block(target: Any, lines: list[str]) -> None:
    text = " ".join(line.strip() for line in lines)
    para = target.add_paragraph()
    _add_bold_aware_runs(para, text)


def _render_section_body(target: Any, body: str) -> None:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in body.splitlines():
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)

    for block in blocks:
        if all(line.strip().startswith("|") for line in block):
            _render_table_block(target, block)
        elif block[0].strip().startswith("- ") or block[0].strip().startswith("* "):
            _render_bullet_block(target, block)
        else:
            _render_prose_block(target, block)


def render_sections_into_body(target: Any, sections: dict[str, str]) -> None:
    """Render parsed report sections into `target`, which may be a
    docx.Document or a docxtpl Subdoc — both expose the same
    add_heading/add_paragraph/add_table API, so this one function serves
    both the template-fill and blank-doc code paths."""
    for heading, body in sections.items():
        target.add_heading(heading, level=1)
        _render_section_body(target, body)


def _template_has_placeholder(template_path: Path) -> bool:
    doc = Document(str(template_path))
    combined_text = "\n".join(p.text for p in doc.paragraphs)
    return "{{p report_content}}" in combined_text


def fill_docx_template(template_path: Path, report_md: str) -> DocxTemplate:
    if not _template_has_placeholder(template_path):
        raise ValueError(
            f"{template_path} doesn't contain the required "
            "'{{p report_content}}' placeholder paragraph — see "
            "templates/README.md for the convention."
        )

    tpl = DocxTemplate(str(template_path))
    subdoc = tpl.new_subdoc()
    render_sections_into_body(subdoc, parse_report_sections(report_md))
    tpl.render({"report_content": subdoc})
    return tpl


def build_docx_from_scratch(report_md: str, source_label: str, report_date: str) -> Document:
    doc = Document()
    doc.add_heading(f"Weekly Status Report — {source_label}", level=0)
    doc.add_heading(report_date, level=2)
    render_sections_into_body(doc, parse_report_sections(report_md))
    return doc


def locate_soffice() -> str:
    found = shutil.which("soffice")
    if found:
        return found

    candidates = []
    if platform.system() == "Darwin":
        candidates.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    else:
        candidates.extend(["/usr/bin/soffice", "/usr/local/bin/soffice"])

    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    raise FileNotFoundError(
        "LibreOffice ('soffice') is required to generate the PDF report but "
        "wasn't found. Install it with `brew install --cask libreoffice` "
        "(macOS) or `sudo apt-get install -y libreoffice --no-install-"
        "recommends` (Linux/CI)."
    )


def convert_docx_to_pdf(docx_path: Path, out_dir: Path, timeout: int = 60) -> Path:
    soffice = locate_soffice()
    # Give this conversion its own LibreOffice user profile so concurrent
    # soffice invocations (e.g. a test suite running several conversions,
    # possibly alongside a manual run) don't contend over the same profile lock.
    profile_dir = out_dir / ".libreoffice_profile"
    result = subprocess.run(
        [
            soffice,
            f"-env:UserInstallation=file://{profile_dir}",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(docx_path),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"soffice failed to convert {docx_path} to PDF: {result.stderr}")

    produced = out_dir / (docx_path.stem + ".pdf")
    if not produced.exists():
        raise RuntimeError(
            f"soffice reported success but no PDF was found at {produced}. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return produced


def generate_pdf_report(
    report_md: str,
    source_label: str,
    report_date: str,
    out_pdf_path: Path,
    template_path: Path,
) -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        tmp_docx = tmp_dir / (out_pdf_path.stem + ".docx")

        if template_path.exists():
            tpl = fill_docx_template(template_path, report_md)
            tpl.save(str(tmp_docx))
        else:
            doc = build_docx_from_scratch(report_md, source_label, report_date)
            doc.save(str(tmp_docx))

        produced = convert_docx_to_pdf(tmp_docx, tmp_dir)

        out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(produced), str(out_pdf_path))

    return out_pdf_path
