---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND
phase: done
date: 2026-10-01
tags: [agent-monitoring, data-quality]
---

# TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND

## Title
Explicit week-close command: fold a finished week's monitoring shards into the three canonical files

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Today the only automatic consolidation trigger is `generate_retro.py` calling `consolidate_all()`. Add an explicit, on-demand week close so a finished week ends up as plain `runs.jsonl`, `events.jsonl` and `tools.jsonl` (like W39), plus a report-only nudge when a finished week still has shards. This lands before `TCK-20261001-RETRO-REPORT-READ-ONLY` removes the retro's fold.

## Scope
1. `make agent-monitoring-close-week WEEK=<YYYY-Www>`, built on `monitoring_consolidation.py` (reuse the delete-after-append fold; do not add a manifest).
2. Refuse the current ISO week and any week not yet ended, with a clear message.
3. Deterministic result: rows ordered by `ts` then `seq`, exact-line de-duplication, same line count in as out minus exact duplicates reported.
4. Fold the week's pending `*.working_log.jsonl` shards through the existing single-writer path (`consolidate_pending_rows`), never by opening `tickets/working_log.csv` directly.
5. A report-only nudge hook (same style as the retro nudge) when a finished week still has per-batch shards. It never blocks.
6. Record the late-shard policy: a shard for an already-closed week that arrives later is re-folded by the next close.

## Out of Scope
- Gzip or any other compression: a closed week stays plain jsonl.
- Scheduling the close (manual plus nudge only).
- Changing shard naming or the per-batch write targets.

## Acceptance Criteria
1. Closing a fixture week leaves exactly three canonical files and no shard files; a second run changes nothing.
2. Closing the current ISO week exits non-zero without touching any file.
3. Row counts before and after match, de-duplication is reported, and the working-log rows each appear once in `tickets/working_log.csv`.
4. A late shard added after a close is folded by the next close.
5. The nudge fires for a finished week with shards and is silent otherwise.

## Related Tickets
- TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE (done; why shards exist)
- TCK-20261001-RETRO-REPORT-READ-ONLY (depends on this)
- TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS (done; the cwd/checkout trap to avoid)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md` (update the matching row's status in this ticket's own batch)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/agent-monitoring/monitoring_consolidation.py`, `tools/agent-monitoring/monitoring_shard_paths.py`, `tools/working_log_writer.py`, `Makefile`

## Assumptions / Open Questions
- The week-close commit is made by the implementer, one session per closed week, so two folds cannot collide.
- Open: the first real close is W40, at the start of W41.

## Implementation Notes
New `tools/agent-monitoring/week_close.py` and `make agent-monitoring-close-week WEEK=<YYYY-Www>`. Reuses `per_identifier_shard_paths` and `monitoring_consolidation.DEFAULT_DATA_DIR`; unlike the existing fold it rewrites the canonical file sorted by (ts, seq) with exact-line dedup (tmp file + os.replace, shards deleted after), so a crash between replace and delete is healed on the next close. working_log shards go through `consolidate_pending_rows`, which gained an optional `week` filter (default unchanged). Nudge: `week_close_nudge.py`, wired into the existing `retro_nudge_hook.py` instead of a new settings.json hook entry (a governing-file edit needing separate user approval). No manifest; the 'W40 first real close' question stays with the user and W40 was NOT closed.
Draft by agent-working-design; the implementer commits it.

## Test Summary
10 tests in tests/tools/test_week_close.py (one per AC plus unparseable-line ordering, other-week working_log shard untouched, crash-heal, hook integration); 46 passed with the retro-nudge, consolidation and working_log_writer suites. Real-repo check: closing W40 exits 2 (unfinished) and the nudge reports no finished week with shards.
Not started.

## Files Changed
- `tools/agent-monitoring/week_close.py`, `week_close_nudge.py`, `retro_nudge_hook.py`
- `tools/working_log_writer.py` (optional week filter), `Makefile`
- `tests/tools/test_week_close.py`
- `docs/agent-monitoring/README.md`, `docs/plans/agent_infrastructure/agent_working_direction.md`
None yet.

## Completion Summary
A finished week can now be closed explicitly and deterministically; the retro can stop folding (next ticket).
Not started.
