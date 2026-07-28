"""
Configuration loader.

Reads settings from environment variables (populated via .env locally,
or via GitHub Actions repository secrets in CI).
"""

import os
from dataclasses import dataclass

VALID_ISSUE_TRACKERS = {"github", "jira"}


@dataclass
class Config:
    github_token: str
    github_repo: str          # format: "owner/repo"
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-6"
    issue_state: str = "open"  # "open", "closed", or "all"
    issue_labels: str = ""     # comma-separated, e.g. "bug,blocker"
    lookback_days: int = 7     # only consider issues updated in the last N days
    issue_tracker: str = "github"  # "github" or "jira"
    jira_base_url: str = ""        # e.g. "https://yourcompany.atlassian.net"
    jira_email: str = ""           # Atlassian account email
    jira_api_token: str = ""       # https://id.atlassian.com/manage-profile/security/api-tokens
    jira_project_key: str = ""     # e.g. "PROJ" — scopes the JQL to one project


def load_config() -> Config:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv is optional; CI injects real env vars directly

    issue_tracker = os.environ.get("ISSUE_TRACKER", "github").strip().lower()
    if issue_tracker not in VALID_ISSUE_TRACKERS:
        raise ValueError(
            f"Unsupported ISSUE_TRACKER '{issue_tracker}' — must be one of "
            f"{sorted(VALID_ISSUE_TRACKERS)}"
        )

    return Config(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        github_repo=os.environ.get("GITHUB_REPO", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        issue_state=os.environ.get("ISSUE_STATE", "open"),
        issue_labels=os.environ.get("ISSUE_LABELS", ""),
        lookback_days=int(os.environ.get("LOOKBACK_DAYS", "7")),
        issue_tracker=issue_tracker,
        jira_base_url=os.environ.get("JIRA_BASE_URL", "").rstrip("/"),
        jira_email=os.environ.get("JIRA_EMAIL", ""),
        jira_api_token=os.environ.get("JIRA_API_TOKEN", ""),
        jira_project_key=os.environ.get("JIRA_PROJECT_KEY", ""),
    )
