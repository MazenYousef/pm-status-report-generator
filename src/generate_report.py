"""
Turns raw issue data into a structured, stakeholder-ready status report
using the Claude API.

The prompt is intentionally opinionated about PM report structure
(Progress / Risks & Blockers / Upcoming / Metrics) — edit SYSTEM_PROMPT
to match your organization's reporting template.
"""

import json
import sys
from datetime import date
from typing import Any

import anthropic

from config import Config

SYSTEM_PROMPT = """\
You are an experienced technical project manager writing a concise weekly \
status report for a steering committee audience (execs and cross-functional \
leads who do not need implementation detail).

You will be given a JSON list of issues from a project tracker (GitHub or \
Jira) — title, state, labels, assignee, body, comment count, timestamps — \
representing recent project activity. Produce a status report in Markdown \
with exactly these sections:

## Executive Summary
2-3 sentences: overall health (Green/Yellow/Red) and the single most \
important thing a stakeholder should know this week.

## Progress
Bullet points of what moved forward, grouped sensibly. Reference each item \
using the identifier given in its data (e.g. (#123) for GitHub, (PROJ-123) \
for Jira).

## Risks & Blockers
Bullet points, ordered by severity. Flag anything stale (no update in a \
while) or unassigned as a process risk. If none, say so explicitly.

## Upcoming / Next Steps
What's expected to land next reporting period.

## Metrics
A short table: open issues, closed this period, unassigned count, \
oldest open issue age.

Be direct and specific. Do not invent facts not present in the data. If \
data is sparse, say so rather than padding the report.
"""


def build_user_prompt(issues: list[dict[str, Any]], source_label: str) -> str:
    return (
        f"Source: {source_label}\n"
        f"Report date: {date.today().isoformat()}\n\n"
        f"Issues data (JSON):\n{json.dumps(issues, indent=2)}"
    )


def generate_report(issues: list[dict[str, Any]], cfg: Config, source_label: str) -> str:
    if not cfg.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY must be set")

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    response = client.messages.create(
        model=cfg.anthropic_model,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_user_prompt(issues, source_label)}
        ],
    )

    if response.stop_reason == "max_tokens":
        print(
            "\nWarning: the report was cut off at the max_tokens limit — it may be "
            "truncated or malformed. Consider narrowing LOOKBACK_DAYS/ISSUE_LABELS "
            "or raising max_tokens in generate_report.py.",
            file=sys.stderr,
        )

    return "".join(block.text for block in response.content if block.type == "text")
