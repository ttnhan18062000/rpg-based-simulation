# codebase-m7-event-extractor: M7 refactor lane, batch 2 (`src/observability/event_extractor.py`)

rpg-planner (u24) cleared the file for M7 batch 2 on 2026-10-28, relayed word for word by lead-planner. Its conditions:
- Characterization tests come first.
- Start only after #779 (rpg-observability-hotfix-batch) merges, and branch from that main. #779 edits `event_recorder.py`, which imports `EventExtractor`, and `kernel.py`.
- Event output stays byte-identical: the same `event_type`, `event_category` and payload keys and values on every tick.
- The pure-run digest is unchanged, shown by an event-log diff on one short run plus the characterization tests.
- Any change to an event's shape goes to rpg-planner first, because SimQ scorers and `decision_trace_contract.md` read those fields.
- rpg-planner reviews the PR.

**Owner DISPATCH GO, 2026-10-28:** https://github.com/ttnhan18062000/rpg-based-simulation/issues/715#issuecomment-6475232510 ("Go (after #779)"). This covers both tickets, which are standard tier. Dispatch only after #779 has merged, and start from that main. The push and the merge need fresh asks.

1. `TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS`: pin the event stream that `EventExtractor.extract` produces, under the default flags and under each rollback flag. The tests pass on the post-#779 main with `src/` untouched. Commit this ticket before any move.
2. `TCK-20261028-EVENT-EXTRACTOR-SPLIT-BY-DOMAIN`: split the 1,581-line `extract()` into one function per event domain, in a new `src/observability/extraction/` subpackage. `event_extractor.py` stays as the public facade. This is a pure move: the ticket 1 fixtures stay unchanged, and the code-health, mypy and pyrefly baselines for the file only go down.

**Order:** 1 before 2. The whole folder ships as one PR.

**Before push:**
1. The implementer sends codebase-planner the SHA, `git diff --stat origin/main`, and the fixture-unchanged proof (ticket 1's fixtures are byte-identical at the head).
2. codebase-planner sends it to lead-planner.
3. The owner approves the push, logged on #715.
4. The PR is opened (standing approval S3, #715 issuecomment-6473439661).
5. rpg-planner is requested as reviewer.

**Out of this batch, for rpg-planner:**
- the four `ENABLE_PUSH_EVENT_SHAPERS*` rollback branches, which are kept as-is;
- the private import `_MAX_CONSECUTIVE_REJECTIONS` from `src/systems/strategic_systems/intelligence.py`.
