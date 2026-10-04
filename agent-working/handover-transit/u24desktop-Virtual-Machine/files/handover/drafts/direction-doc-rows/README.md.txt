# Draft: agent_working_direction.md rows for what shipped in #277 and #280 (design -> implementer)
File: docs/plans/agent_infrastructure/agent_working_direction.md. Fold into PR #280 (open, one open PR per track). Docs change => run `make knowledge-index-update`; stage docs/REGISTRY.yaml with the usual close.

## Edit 1 — row "Post-merge integrity check against `origin/main`" (Observable table, line 44)
Replace the whole row with (keep the existing ticket text, append the reading):

| Post-merge integrity check against `origin/main` | shipped | `TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT` (PR #274): `make agent-monitoring-main-integrity`, on demand and report-only; wiring it into a post-merge hook stays open. First real triage 2026-10-02: 311 findings on `fe6a2f564`, 263 after PR #277 (`TCK-20261001-WORKING-LOG-BYTE-DUPLICATE-DEBT` removed 56 byte-identical working_log lines and the pair ceiling went 46 to 19; `TCK-20261001-INTEGRITY-REPORT-EPIC-TIER-FALSE-POSITIVES` stopped flagging epics that close as EPIC_SCOPED). What remains is known: 119 historical `event_seq` findings (multi-invocation restarts, already explained by `TCK-20260915-EVENT-SEQ-INTEGRITY`), 13 cited-evidence (one real, a gitignored `.json` for `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`), 7 epics with no working_log row (not backfilled: a hand-written row would be invented history), and ~120 pre-September "no DONE row" tickets |

(Numbers: measured on origin/main 45fdc892e; 311 -> 263 is the report's own RESULT line. Re-measure before committing if main moved.)

## Edit 2 — new row at the end of the "Self-diagnosing" table, after "Finding-to-ticket-to-merge funnel"
| PR body `Closes:` must reflect ticket location | shipped | `TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS` (PR #280): a ticket under `todos/` or `inprogress/` is left out of `Closes:` with a warning, so a PR that files a follow-up no longer claims to close it; found twice by a peer reading the body (PRs #276, #279), not by `--check` |

## Notes
- Do not change any other row. Define-information-once: the numbers live only in Edit 1.
- If main moved, re-run `python3 tools/agent-monitoring/main_integrity_report.py --ref origin/main --limit 0` for the totals.
