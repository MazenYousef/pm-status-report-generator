"""
Jira fetcher internals: JQL construction, ADF-to-text flattening, and the
full fetch_issues() mapping against a mocked Jira Cloud v3 search response.
All component-boundary (no CLI, no real Jira instance) — there's no
end-to-end way to exercise these without either live Jira credentials or
mocking the HTTP layer.
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import SRC_DIR  # noqa: E402

sys.path.insert(0, str(SRC_DIR))
from config import Config  # noqa: E402
import fetch_jira_issues  # noqa: E402

pytestmark = pytest.mark.offline


def _cfg(**overrides):
    base = dict(
        github_token="", github_repo="", anthropic_api_key="",
        jira_base_url="https://acme.atlassian.net",
        jira_email="pm@acme.com",
        jira_api_token="fake-token",
        jira_project_key="",
        issue_state="open",
        issue_labels="",
        lookback_days=7,
    )
    base.update(overrides)
    return Config(**base)


class TestBuildJql:
    def test_full_query_with_project_and_labels(self):
        cfg = _cfg(jira_project_key="PROJ", issue_labels="bug,blocker", lookback_days=7)
        jql = fetch_jira_issues._build_jql(cfg)
        assert jql == (
            'project = "PROJ" AND statusCategory != Done AND '
            'labels in ("bug", "blocker") AND updated >= -7d ORDER BY updated DESC'
        )

    def test_closed_state_no_project_no_labels(self):
        cfg = _cfg(issue_state="closed", lookback_days=14)
        jql = fetch_jira_issues._build_jql(cfg)
        assert jql == "statusCategory = Done AND updated >= -14d ORDER BY updated DESC"

    def test_all_state_omits_status_clause(self):
        cfg = _cfg(jira_project_key="X", issue_state="all", lookback_days=30)
        jql = fetch_jira_issues._build_jql(cfg)
        assert "statusCategory" not in jql
        assert jql.startswith('project = "X"')

    def test_embedded_quote_in_project_key_is_escaped(self):
        cfg = _cfg(jira_project_key='PROJ" OR 1=1 OR "')
        jql = fetch_jira_issues._build_jql(cfg)
        assert 'project = "PROJ\\" OR 1=1 OR \\""' in jql

    def test_embedded_quote_in_label_is_escaped(self):
        cfg = _cfg(issue_labels='weird"label')
        jql = fetch_jira_issues._build_jql(cfg)
        assert '"weird\\"label"' in jql


class TestAdfToText:
    def test_multiple_paragraphs_are_newline_separated(self):
        adf = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "First."}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Second."}]},
            ],
        }
        assert fetch_jira_issues._adf_to_text(adf).strip() == "First.\nSecond."

    def test_nested_list_item_flattened(self):
        adf = {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "bullet one"}]}
                ]},
            ],
        }
        assert "bullet one" in fetch_jira_issues._adf_to_text(adf)

    def test_none_and_empty_are_safe(self):
        assert fetch_jira_issues._adf_to_text(None) == ""
        assert fetch_jira_issues._adf_to_text({}) == ""


def test_fetch_issues_maps_mocked_response_to_expected_shape():
    cfg = _cfg(jira_project_key="PROJ")
    fake_response = mock.Mock()
    fake_response.raise_for_status = mock.Mock()
    fake_response.json.return_value = {
        "issues": [
            {
                "key": "PROJ-42",
                "fields": {
                    "summary": "Fix latency regression",
                    "status": {"name": "In Progress"},
                    "labels": ["blocker"],
                    "assignee": {"displayName": "Jane Doe"},
                    "created": "2026-07-01T10:00:00.000+0000",
                    "updated": "2026-07-26T09:00:00.000+0000",
                    "description": {
                        "type": "doc",
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Spikes."}]}],
                    },
                    "comment": {"total": 3},
                },
            },
            {
                "key": "PROJ-43",
                "fields": {
                    "summary": "No description issue",
                    "status": {"name": "To Do"},
                    "labels": [],
                    "assignee": None,
                    "created": "2026-07-10T10:00:00.000+0000",
                    "updated": "2026-07-20T09:00:00.000+0000",
                    "description": None,
                    "comment": {"total": 0},
                },
            },
        ]
    }

    with mock.patch.object(fetch_jira_issues.requests, "get", return_value=fake_response) as mock_get:
        issues = fetch_jira_issues.fetch_issues(cfg)
        jql_sent = mock_get.call_args[1]["params"]["jql"]
        auth_sent = mock_get.call_args[1]["auth"]

    assert auth_sent == (cfg.jira_email, cfg.jira_api_token)
    assert 'project = "PROJ"' in jql_sent

    assert issues[0] == {
        "number": "PROJ-42",
        "title": "Fix latency regression",
        "state": "In Progress",
        "labels": ["blocker"],
        "assignee": "Jane Doe",
        "created_at": "2026-07-01T10:00:00.000+0000",
        "updated_at": "2026-07-26T09:00:00.000+0000",
        "body": "Spikes.",
        "comments_count": 3,
        "url": "https://acme.atlassian.net/browse/PROJ-42",
    }
    assert issues[1]["assignee"] == "Unassigned"
    assert issues[1]["body"] == ""


def _fake_jira_page(keys, total):
    resp = mock.Mock()
    resp.raise_for_status = mock.Mock()
    resp.json.return_value = {
        "total": total,
        "issues": [
            {
                "key": key,
                "fields": {
                    "summary": f"Issue {key}",
                    "status": {"name": "To Do"},
                    "labels": [],
                    "assignee": None,
                    "created": "2026-01-01T00:00:00.000+0000",
                    "updated": "2026-01-01T00:00:00.000+0000",
                    "description": None,
                    "comment": {"total": 0},
                },
            }
            for key in keys
        ],
    }
    return resp


def test_pagination_loops_using_start_at_and_total():
    cfg = _cfg(jira_project_key="PROJ")
    # 3 pages of 1 issue each, out of a reported total of 3
    page1 = _fake_jira_page(["PROJ-1"], total=3)
    page2 = _fake_jira_page(["PROJ-2"], total=3)
    page3 = _fake_jira_page(["PROJ-3"], total=3)

    with mock.patch.object(fetch_jira_issues.requests, "get", side_effect=[page1, page2, page3]) as mock_get:
        issues = fetch_jira_issues.fetch_issues(cfg)

    assert [i["number"] for i in issues] == ["PROJ-1", "PROJ-2", "PROJ-3"]
    assert mock_get.call_count == 3
    start_ats = [call.kwargs["params"]["startAt"] for call in mock_get.call_args_list]
    assert start_ats == [0, 1, 2]


@pytest.mark.parametrize(
    "overrides",
    [
        dict(jira_base_url="", jira_email="", jira_api_token=""),
        dict(jira_email="", jira_api_token=""),
        dict(jira_api_token=""),
    ],
    ids=["all-missing", "email-and-token-missing", "token-missing"],
)
def test_missing_credentials_raises_before_any_request(overrides):
    cfg = _cfg(**overrides)
    with mock.patch.object(fetch_jira_issues.requests, "get") as mock_get:
        with pytest.raises(ValueError, match="JIRA_BASE_URL|JIRA_EMAIL|JIRA_API_TOKEN"):
            fetch_jira_issues.fetch_issues(cfg)
        mock_get.assert_not_called()
