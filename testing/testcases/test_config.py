"""Config loading: defaults and env-var parsing (offline, no external calls).

Note: config.load_config() calls dotenv.load_dotenv() internally, which
would find and load this project's real .env (searching upward from cwd)
even with os.environ cleared. Every test here also patches
dotenv.load_dotenv to a no-op so it genuinely tests code defaults, not
whatever happens to be in the real .env.
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from testhelpers import SRC_DIR  # noqa: E402

sys.path.insert(0, str(SRC_DIR))
from config import load_config  # noqa: E402

pytestmark = pytest.mark.offline


def test_defaults_when_env_unset():
    with mock.patch("dotenv.load_dotenv", return_value=None), \
         mock.patch.dict("os.environ", {}, clear=True):
        cfg = load_config()
    assert cfg.issue_tracker == "github"
    assert cfg.anthropic_model == "claude-sonnet-4-6"
    assert cfg.issue_state == "open"
    assert cfg.issue_labels == ""
    assert cfg.lookback_days == 7
    assert cfg.github_token == ""
    assert cfg.jira_base_url == ""


def test_issue_tracker_is_lowercased_and_stripped():
    with mock.patch("dotenv.load_dotenv", return_value=None), \
         mock.patch.dict("os.environ", {"ISSUE_TRACKER": "  JIRA  "}, clear=True):
        cfg = load_config()
    assert cfg.issue_tracker == "jira"


def test_lookback_days_parsed_as_int():
    with mock.patch("dotenv.load_dotenv", return_value=None), \
         mock.patch.dict("os.environ", {"LOOKBACK_DAYS": "30"}, clear=True):
        cfg = load_config()
    assert cfg.lookback_days == 30
    assert isinstance(cfg.lookback_days, int)


def test_jira_base_url_trailing_slash_stripped():
    with mock.patch("dotenv.load_dotenv", return_value=None), \
         mock.patch.dict("os.environ", {"JIRA_BASE_URL": "https://example.atlassian.net/"}, clear=True):
        cfg = load_config()
    assert cfg.jira_base_url == "https://example.atlassian.net"


def test_unrecognized_issue_tracker_raises_clear_error():
    with mock.patch("dotenv.load_dotenv", return_value=None), \
         mock.patch.dict("os.environ", {"ISSUE_TRACKER": "azuredevops"}, clear=True):
        with pytest.raises(ValueError, match="Unsupported ISSUE_TRACKER"):
            load_config()
