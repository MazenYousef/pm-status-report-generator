# Weekly Status Report — sample/demo-repo
_Generated 2026-07-27 (example output, generated from sample_data/github_sample_issues.json)_

## Executive Summary
Overall status: **Yellow**. The UGW customer acceptance milestone closed successfully this
period, but an unassigned AVB/TSN latency blocker and a stalled supplier risk both need
ownership assigned this week to avoid schedule slip.

## Progress
- UGW platform customer acceptance test plan reviewed and formally signed off (#103) —
  execution phase can begin.
- Gateway firmware v2.3 CI integration nearly complete; only flaky HIL rerun logic remains (#101).

## Risks & Blockers
- **[Blocker, unassigned]** AVB/TSN latency regression on test bench 3 (#102) — gPTP sync
  drifting out of spec under load, suspected NIC firmware mismatch. No owner and no update
  in 13 days — needs an owner assigned this week.
- **[Compliance risk]** Traceability matrix has 3 unlinked requirements ahead of the August
  ISO 26262 gate review (#104) — closeable but on a tight runway.
- **[Stale, unassigned]** Supplier delay risk on gateway ECU samples (#98) — no update in
  37 days despite an indicated 2-week delay. Recommend a status check with the supplier.

## Upcoming / Next Steps
- Assign an owner and root-cause the AVB/TSN latency regression (#102).
- Close remaining traceability gaps ahead of the August gate review (#104).
- Begin UGW customer acceptance test execution following sign-off (#103).

## Metrics
| Metric | Value |
|---|---|
| Open issues | 4 |
| Closed this period | 1 |
| Unassigned | 2 |
| Oldest open issue age | 42 days (#98) |
