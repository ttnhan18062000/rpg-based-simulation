---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-HAND-CLOSURE-AGENT-COUNT-UNKNOWN
phase: open
date: 2026-10-20
tags: [agent-monitoring, data-quality, retro]
---

# TCK-20261020-HAND-CLOSURE-AGENT-COUNT-UNKNOWN

## Title
Hand closures record agent_count as unknown (null) instead of a phase-event count, and the retro's "Avg agents per run" leaves them out

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
From RETRO-2026-W43's final note (40 runs), item 3, proposal C. The owner approved it on 2026-10-20, relayed by lead-planner.

`docs/agent-monitoring/schema.md` defines `agent_count` as "Total number of agent calls that produced events". `record_hand_orchestrated_closure.py` sets it to `len(events) - recorder_added`. That's the number of phase events the closer narrated, plus artifact-derived Investigate/Plan events, and it's 6 or 8 for every hand run. It isn't a count of agent calls; a hand closure makes no agent calls the recorder can see. W43's "Avg agents per run" of 6.5 and its 262 "claude" calls for 40 runs are therefore meaningless.

#690 (TCK-20261020-HAND-CLOSURE-RECORDS-FOLDED-PHASES-AS-SKIPPED) already excludes recorder-added folded phases from the count. This ticket supersedes that for hand closures: their count is unknown, the same way an unknown duration is (`duration_source: unknown`), and never a number that looks measured.

## Scope
1. **`tools/agent-monitoring/record_hand_orchestrated_closure.py`.**
   - The run record's `agent_count` becomes `null` for hand closures.
   - Remove the `recorder_added` subtraction if nothing else needs it; keep the folded-phase events themselves.
   - Update the inline comment to say why.
2. **`tools/agent-monitoring/record_run.py`.** `agent_count` stays a required key, but `null` is a valid value. Check `validate_record` and any type check on it.
3. **Readers** treat `null` as unknown, never as 0 in an average:
   - `generate_retro.py`: "Avg agents per run" is computed over runs with a non-null `agent_count` only, and the row says how many runs it covers. For example: "Avg agents per run (n=0 of 40; hand closures record unknown)". When n is 0, print `n/a`, as for durations.
   - Check `query.py` (prints the column), `run_dedup.py` (`or 0` in a tie-break, fine as is), `duckdb_view.py` (BIGINT, nullable) and `validate.py`/integrity checks. None must crash or flag `null`.
4. **Docs:**
   - `docs/agent-monitoring/schema.md`, the `agent_count` row: int or null; null for `execution_mode: hand` (the recorder can't see agent calls); pipeline and native runs are unchanged.
   - Make the #690 wording in `docs/agent-monitoring/README.md` ("Recording coverage for a hand-orchestrated closure") consistent with this: folded phases are recorded, and agent_count is null.
5. **Tests:**
   - the recorder writes `agent_count: null`;
   - `record_run` accepts it;
   - the retro's average excludes null runs and prints `n/a` when every run is null;
   - a pipeline-shaped run with `agent_count: 9` still averages as before.
   - Update existing tests that assert the old count, including #690's agent_count test, to the new contract. Don't delete them.

## Out of Scope
- Backfilling past hand runs' `agent_count`. The retro row's n makes the mix visible; old rows keep their numbers.
- The pipeline and native recording paths.
- The Agent Status Distribution table, which counts events, not agent_count.

## Acceptance Criteria
- A new hand closure writes `agent_count: null`, and `record_run`, validate, query and the retro all accept it.
- "Avg agents per run" never averages a hand closure, and its row shows n.
- The schema text, the README and the recorder agree.
- Tests pass, including the updated #690 test. REGISTRY is regenerated after the last docs edit.

## Related Tickets
- TCK-20261020-HAND-CLOSURE-RECORDS-FOLDED-PHASES-AS-SKIPPED (#690; superseded for agent_count)
- TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS (the unknown-not-zero precedent for durations)
- TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON (artifact-derived events)

## Related Docs
- agent-working/agent-monitoring/retro/RETRO-2026-W43.md (final note, item 3)
- docs/agent-monitoring/schema.md, docs/agent-monitoring/README.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py (`run_record`), record_run.py (`REQUIRED`, `validate_record`)
- tools/agent-monitoring/generate_retro.py (`avg_agents`, Run Summary row), query.py, run_dedup.py, duckdb_view.py, validate.py

## Assumptions / Open Questions
- Null, not 0 and not a removed key. The key stays required, so a missing key is still a schema error and "unknown" is explicit. This matches `duration_s` handling.

## Implementation Notes
- 2026-10-20 (agent-working-planner): owner yes (via lead-planner), with the note that it supersedes #690's agent_count change for hand closures and must keep the schema and retro consistent. Batch 7, dispatched to agent-working-implementer.

## Test Summary

## Files Changed

## Completion Summary
