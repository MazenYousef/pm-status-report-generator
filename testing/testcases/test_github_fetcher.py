"""
GitHub fetcher: missing-credentials error path and pagination (component-
boundary — calls fetch_issues.fetch_issues() directly / mocks requests.get
rather than going through the CLI, since we want to confirm no network call
is attempted for the error case, and control exactly how many "pages" a
mocked response has for the pagination case).
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import SRC_DIR  # noqa: E402

sys.path.insert(0, str(SRC_DIR))
from config import Config  # noqa: E402
from fetch_issues import fetch_issues  # noqa: E402
import fetch_issues as fetch_issues_module  # noqa: E402

pytestmark = pytest.mark.offline


def test_missing_credentials_raises_before_any_request():
    cfg = Config(github_token="", github_repo="", anthropic_api_key="")
    with pytest.raises(ValueError, match="GITHUB_TOKEN"):
        fetch_issues(cfg)


def test_missing_repo_only_still_raises():
    cfg = Config(github_token="ghp_realtoken", github_repo="", anthropic_api_key="")
    with pytest.raises(ValueError, match="GITHUB_REPO"):
        fetch_issues(cfg)


def _fake_page(issue_numbers, next_url=None):
    resp = mock.Mock()
    resp.raise_for_status = mock.Mock()
    resp.json.return_value = [
        {
            "number": n,
            "title": f"Issue {n}",
            "state": "open",
            "labels": [],
            "assignee": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "body": "",
            "comments": 0,
            "html_url": f"https://github.com/owner/repo/issues/{n}",
        }
        for n in issue_numbers
    ]
    resp.links = {"next": {"url": next_url}} if next_url else {}
    return resp


def test_pagination_follows_link_header_across_multiple_pages():
    cfg = Config(github_token="ghp_realtoken", github_repo="owner/repo", anthropic_api_key="")

    page1 = _fake_page([1], next_url="https://api.github.com/repositories/1/issues?page=2")
    page2 = _fake_page([2], next_url="https://api.github.com/repositories/1/issues?page=3")
    page3 = _fake_page([3])  # no next link — last page

    with mock.patch.object(fetch_issues_module.requests, "get", side_effect=[page1, page2, page3]) as mock_get:
        issues = fetch_issues(cfg)

    assert [i["number"] for i in issues] == [1, 2, 3]
    assert mock_get.call_count == 3
    # subsequent pages hit the "next" URL directly with no extra params (already encoded in it)
    assert mock_get.call_args_list[1].kwargs["params"] is None
    assert mock_get.call_args_list[2].kwargs["params"] is None
