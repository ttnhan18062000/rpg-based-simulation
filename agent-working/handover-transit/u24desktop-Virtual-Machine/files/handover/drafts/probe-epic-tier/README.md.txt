# Draft: integrity-report probe, epic-tier tickets (design -> implementer)
Base: origin/main fe6a2f564 (same base as the dedupe branch). `git apply probe.patch` applies cleanly to the current tree.
Fold into branch working-log-duplicate-debt (one batch, one PR) unless the user says otherwise.

## Defect (verified)
tools/agent-monitoring/main_integrity_report.py::check_working_log demands a DONE row from every closed ticket. An epic-tier ticket closes as EPIC_SCOPED, never DONE, so the probe flags it. 22 of the 29 epic-tier findings on origin/main have a row (EPIC_SCOPED) and are false positives; 7 epics really have no row.

## Change (hotfix tier, 2 files, +33/-3)
- Epic tier (`## Tier` = epic, read from the ticket at the ref): any row of any status satisfies it; zero rows -> "<id>: epic has no working-log row (<path>)".
- Non-epic: unchanged. Duplicate-row check: unchanged. Docstrings updated.
- Test: test_an_epic_tier_ticket_needs_a_row_of_any_status_not_a_done_row (EPIC_SCOPED row passes; zero-row epic reported; non-epic with only EPIC_SCOPED still reported).

## Verified in a throwaway worktree
- tests/tools/test_main_integrity_report.py: 9 passed (use the repo .venv, system python lacks pydantic).
- Negative control: new test FAILS against the unpatched module.
- Report on origin/main: working_log findings 179 -> 157 (before the dedupe lands; after it, 26 duplicate findings also go).

## For the implementer
- Hotfix ticket (new id, layer observability); NOT the dedupe ticket. Closure tool run, mechanism advisory, as usual.
- Do not backfill the missing row for TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS (would be a hand-written row; report it, leave it).
- Only the 7 zero-row epics remain as findings; 2 of them are RPG-side (not agent-working).
