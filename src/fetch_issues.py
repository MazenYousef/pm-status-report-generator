"""
Fetches issues from a GitHub repository via the REST API. This is the "data
source" layer — swap this module out for a Jira or Azure DevOps client and
the rest of the pipeline is unchanged.
"""

import datetime as dt
from typing import Any

import requests

from config import Config

GITHUB_API = "https://api.github.com"


def fetch_issues(cfg: Config) -> list[dict[str, Any]]:
    """Fetch issues updated within the lookback window, with basic fields
    plus a comment count (not comment text/content)."""
    if not cfg.github_token or not cfg.github_repo:
        raise ValueError("GITHUB_TOKEN and GITHUB_REPO must be set")

    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=cfg.lookback_days)).isoformat()

    headers = {
        "Authorization": f"Bearer {cfg.github_token}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "state": cfg.issue_state,
        "since": since,
        "per_page": 100,
    }
    if cfg.issue_labels:
        params["labels"] = cfg.issue_labels

    url = f"{GITHUB_API}/repos/{cfg.github_repo}/issues"
    raw_issues = []
    next_url, next_params = url, params
    while next_url:
        resp = requests.get(next_url, headers=headers, params=next_params, timeout=30)
        resp.raise_for_status()
        raw_issues.extend(resp.json())
        # Follow GitHub's Link: rel="next" header for pagination past per_page=100;
        # the next URL already encodes all query params, so drop `params` after page 1.
        next_url = resp.links.get("next", {}).get("url")
        next_params = None

    issues = []
    for issue in raw_issues:
        # Skip pull requests — the Issues API returns PRs too
        if "pull_request" in issue:
            continue

        issues.append({
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "labels": [label["name"] for label in issue.get("labels", [])],
            "assignee": issue["assignee"]["login"] if issue.get("assignee") else "Unassigned",
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "body": (issue.get("body") or "")[:500],  # truncate long bodies
            "comments_count": issue.get("comments", 0),
            "url": issue["html_url"],
        })

    return issues
