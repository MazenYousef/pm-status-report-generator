"""
Plain (non-pytest-magic) helper module: repo paths and credential/capability
detection, reused by conftest.py's fixtures and imported directly by test
modules that need these values at collection time (e.g. for
`@pytest.mark.skipif`, which needs a plain boolean, not a fixture).

Reuses src/config.load_config() rather than re-parsing .env, so the suite
always sees exactly what the tool itself would see.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
MAIN_PY = SRC_DIR / "main.py"
REPORTS_DIR = ROOT / "reports"
TEMPLATES_DIR = ROOT / "templates"
TEMPLATE_PATH = TEMPLATES_DIR / "weekly_status_template.docx"

sys.path.insert(0, str(SRC_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from config import load_config  # noqa: E402
from generate_pdf import locate_soffice  # noqa: E402

CFG = load_config()

# Exact placeholder values shipped in .env.example — a "configured" value must
# differ from these. This only catches "never edited the file"; a fake-but-
# different value will still look "configured". Documented limitation.
_PLACEHOLDERS = {
    "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx",
    "github_repo": "your-org/your-repo",
    "jira_base_url": "https://your-company.atlassian.net",
    "jira_email": "you@example.com",
    "jira_api_token": "xxxxxxxxxxxxxxxxxxxx",
    "jira_project_key": "PROJ",
    "anthropic_api_key": "sk-ant-xxxxxxxxxxxxxxxxxxxx",
}


def _is_configured(field: str) -> bool:
    value = getattr(CFG, field)
    return bool(value) and value != _PLACEHOLDERS[field]


HAS_GITHUB_CREDS = _is_configured("github_token") and _is_configured("github_repo")
HAS_JIRA_CREDS = (
    _is_configured("jira_base_url")
    and _is_configured("jira_email")
    and _is_configured("jira_api_token")
)
HAS_ANTHROPIC_KEY = _is_configured("anthropic_api_key")

try:
    locate_soffice()
    HAS_SOFFICE = True
except FileNotFoundError:
    HAS_SOFFICE = False

HAS_PDFTOTEXT = shutil.which("pdftotext") is not None


def pdf_to_text(pdf_path) -> str:
    """Extract text from a PDF via poppler's pdftotext, for content
    assertions in tests. Only called when HAS_PDFTOTEXT is True."""
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30,
    )
    result.check_returncode()
    return result.stdout


def run_cli(args: list, env_overrides: Optional[dict] = None, timeout: int = 90) -> subprocess.CompletedProcess:
    """Invoke `python3 src/main.py <args>` as a real subprocess (the
    blackbox boundary) with the current environment plus any overrides,
    from the repo root, capturing stdout/stderr as text."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(MAIN_PY), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
