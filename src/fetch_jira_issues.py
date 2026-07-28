"""
Fetches issues from a Jira Cloud project via the REST API v3 search
endpoint. Same "data source" role as fetch_issues.py (GitHub) — returns
the identical list-of-dicts shape so the rest of the pipeline (prompt,
report generation, PDF rendering) needs no changes regardless of which
tracker is configured (see Config.issue_tracker).
"""

from typing import Any

import requests

from config import Config

JIRA_SEARCH_FIELDS = "summary,status,labels,assignee,created,updated,description,comment"

_ADF_BLOCK_TYPES = {"paragraph", "heading", "listItem", "codeBlock", "blockquote"}


def _escape_jql(value: str) -> str:
    """Escape embedded double-quotes so a config value containing one
    doesn't break the quoted JQL string it's interpolated into."""
    return value.replace('"', '\\"')


def _build_jql(cfg: Config) -> str:
    """Translate the same ISSUE_STATE / ISSUE_LABELS / LOOKBACK_DAYS knobs
    used for GitHub filtering into a JQL query, scoped to JIRA_PROJECT_KEY
    if set."""
    clauses = []

    if cfg.jira_project_key:
        clauses.append(f'project = "{_escape_jql(cfg.jira_project_key)}"')

    if cfg.issue_state == "open":
        clauses.append("statusCategory != Done")
    elif cfg.issue_state == "closed":
        clauses.append("statusCategory = Done")

    if cfg.issue_labels:
        labels = ", ".join(f'"{_escape_jql(label.strip())}"' for label in cfg.issue_labels.split(","))
        clauses.append(f"labels in ({labels})")

    clauses.append(f"updated >= -{cfg.lookback_days}d")

    return " AND ".join(clauses) + " ORDER BY updated DESC"


def _adf_to_text(node: Any) -> str:
    """Flatten Jira's Atlassian Document Format (used for the `description`
    field in REST API v3) down to plain text, concatenating text leaf nodes
    and inserting a newline after each block-level element (paragraph,
    heading, list item, ...) so separate blocks don't run together."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        node_type = node.get("type")
        if node_type == "text":
            return node.get("text", "")
        text = "".join(_adf_to_text(child) for child in node.get("content", []))
        return text + "\n" if node_type in _ADF_BLOCK_TYPES else text
    if isinstance(node, list):
        return "".join(_adf_to_text(child) for child in node)
    return ""


def fetch_issues(cfg: Config) -> list[dict[str, Any]]:
    """Fetch issues from Jira matching the configured filters, with basic
    fields plus a plain-text description, in the same shape fetch_issues.py
    (GitHub) produces."""
    if not cfg.jira_base_url or not cfg.jira_email or not cfg.jira_api_token:
        raise ValueError("JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set")

    jql = _build_jql(cfg)

    raw_issues = []
    start_at = 0
    while True:
        resp = requests.get(
            f"{cfg.jira_base_url}/rest/api/3/search",
            auth=(cfg.jira_email, cfg.jira_api_token),
            headers={"Accept": "application/json"},
            params={"jql": jql, "maxResults": 100, "startAt": start_at, "fields": JIRA_SEARCH_FIELDS},
            timeout=30,
        )
        resp.raise_for_status()
        page = resp.json()
        page_issues = page.get("issues", [])
        raw_issues.extend(page_issues)

        start_at += len(page_issues)
        if not page_issues or start_at >= page.get("total", start_at):
            break

    issues = []
    for issue in raw_issues:
        fields = issue["fields"]
        assignee = fields.get("assignee")
        description = fields.get("description")

        issues.append({
            "number": issue["key"],
            "title": fields["summary"],
            "state": fields["status"]["name"],
            "labels": fields.get("labels", []),
            "assignee": assignee["displayName"] if assignee else "Unassigned",
            "created_at": fields["created"],
            "updated_at": fields["updated"],
            "body": (_adf_to_text(description).strip() if description else "")[:500],
            "comments_count": fields.get("comment", {}).get("total", 0),
            "url": f"{cfg.jira_base_url}/browse/{issue['key']}",
        })

    return issues
