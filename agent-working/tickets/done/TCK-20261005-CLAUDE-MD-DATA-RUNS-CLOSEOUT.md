---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261005-CLAUDE-MD-DATA-RUNS-CLOSEOUT
phase: done
date: 2026-10-05
tags: [ai, process-improvement]
---

# TCK-20261005-CLAUDE-MD-DATA-RUNS-CLOSEOUT

## Title
CLAUDE.md close-out lines tell agents to `rm -rf data/runs/*`, which deletes other sessions' run data

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED` (PR #340) made `clean_data_runs_early` report-only and added the scoped `--clean-data-runs --path <run_id>` command. Two lines in the project CLAUDE.md still told every closing session to `rm -rf data/runs/* reports/release_proof/*` (After Work) and to treat "temporary run data cleaned" as a Definition-of-Done item. CLAUDE.md is a governing file, so the edit needed the owner's confirmation of the literal text.

## Scope
- Replace the After Work clean-up line and the Definition of Done run-data line with the owner-approved wording.

## Out of Scope
- Any other CLAUDE.md text; the docs outside CLAUDE.md that mention `rm -rf data/runs` in unrelated simulation guides.

## Acceptance Criteria
1. The two lines read exactly as the owner approved (2026-10-05, confirmed directly in the implementer terminal through an AskUserQuestion showing the literal before/after).
2. No test pins the old wording.

## Related Tickets
- TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED

## Related Docs
- CLAUDE.md

## Related Stored Artifacts
- none

## Related Code Areas
- CLAUDE.md

## Assumptions / Open Questions
- None.

## Implementation Notes
Two lines in CLAUDE.md changed, exactly as the owner approved: After Work now says to clean up only the run data your own session wrote with `python3 tools/gate_checks/done_checker_static.py --clean-data-runs --path <run_id>` and never `rm -rf data/runs/*`; the Definition of Done line now says run data this session wrote is cleaned by run id and that the Verify check `data_runs_clean` is advisory. Approval: the owner confirmed the literal before/after text directly in this terminal (AskUserQuestion, 2026-10-05); design's relay in its own session was not treated as approval. A grep of `tests/` found no test pinning the old wording; `docs/` mentions of `rm -rf data/runs` are in unrelated simulation and scoring guides and were left alone.

## Test Summary
No test pins either line (grep of `tests/` for the old wording found none). No code changed. The related done_checker and session tests were run with the rest of this batch and pass.

## Files Changed
- CLAUDE.md

## Completion Summary
CLAUDE.md no longer tells agents to blanket-delete `data/runs/`; it points at the scoped, run-id based command.
