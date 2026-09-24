---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE
phase: open
date: 2026-09-24
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE

## Title
Per-ticket write targets for `agent-monitoring/data/*/*.jsonl` and `tickets/working_log.csv`,
consolidated at retro time, to remove the one gap `merge=union` doesn't cover: GitHub squash-merge

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`.gitattributes` already sets `merge=union` (+ `eol=lf`) on `agent-monitoring/data/*/*.jsonl` and
`tickets/working_log.csv`, and `docs/REGISTRY.yaml` has a custom `merge=registry-regen` driver.
These work well for a real git merge (`git merge`/`rebase`/`cherry-pick -m`) — confirmed working
live during `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS`'s own concurrent pushes (two sessions'
commits to `github-delivery-process-epic` auto-merged `tools.jsonl` cleanly and auto-regenerated
`REGISTRY.yaml`, zero manual resolution).

**The `.gitattributes` file's own comments document the gap this ticket exists to close**:
`merge=union` "does NOT protect against a GitHub squash-merge, which this repo's PRs use almost
exclusively (5/5 of the last 5 merged PRs sampled were squash-merged) — a squash-merge has exactly
one parent and applies a plain diff, invoking no merge driver at all." This already produced one
confirmed real incident: a ~1586-row whole-block duplication in `tickets/working_log.csv`
(`TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`), plus a CRLF-driven variant
(`TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION`, "3 of 4 batch PR merges in 3 days
duplicated a block this way"). The current mitigation for `working_log.csv` is *detection*
(`tests/integrity/test_no_duplicate_content_blocks.py` catches a duplicate block after the fact)
plus a documented manual recovery rule, not *prevention*.

`docs/REGISTRY.yaml` does not have this problem the same way, because it is **derived data**, not a
raw log: it is regenerated wholesale from ticket/doc frontmatter on every ticket close (per
CLAUDE.md's Finalize step), so a stale post-squash-merge copy self-heals the next time anyone
closes a ticket. `agent-monitoring/data/*/*.jsonl` and `tickets/working_log.csv` are raw append-only
logs with no such self-healing property — this ticket brings them the same conflict-proofing
`docs/REGISTRY.yaml` already gets, but via a different mechanism suited to append-only data:
**write to a per-ticket file (which two different tickets can never collide on, even under
squash-merge, because they're different file paths), and consolidate into the existing
single-file-per-week shape at a periodic sync point** rather than writing directly to the shared
file every session already contends for.

## Scope
1. **Per-ticket write targets.** `tools/agent-monitoring/record_run.py`, `record_events.py`, and
   the `tools.jsonl`-appending hook write to `agent-monitoring/data/YYYY-Www/<TCK-ID>.{runs,events,
   tools}.jsonl` instead of the shared `{runs,events,tools}.jsonl` for that week. Two different
   tickets can never produce a colliding diff hunk, under any merge strategy including squash,
   because they write to different paths.
2. **`tools/working_log_writer.py::append_working_log_row()`** gets the equivalent treatment: write
   each ticket's row to its own per-ticket staging file (`tickets/working_log_pending/<TCK-ID>.csv`
   or similar — exact shape is an open question, see Assumptions) rather than appending directly to
   the shared `tickets/working_log.csv`.
3. **Consolidation folded into `tools/agent-monitoring/generate_retro.py`**, which already runs
   weekly (and after every 5+ completed tickets, per the existing cadence hook) and already owns
   `_load_runs_and_events()`/`_load_source()`. Extend it to glob the per-ticket shard files for the
   window it's reporting on, fold them into the canonical `runs.jsonl`/`events.jsonl`/`tools.jsonl`
   (and `working_log.csv`) shape, and write the consolidated result back — so every existing reader
   (`validate.py`, `query.py`, the monitoring index, done-checker's own conditions) keeps reading
   the same 3-per-week-file / 1-CSV contract unchanged. No consumer read-path rewrite required.
4. **A standalone consolidation command** (`make agent-monitoring-consolidate` or similar), for
   consolidating on demand rather than waiting for the next retro trigger — useful right after a
   PR merges, or before a check that wants fresher data than the last retro run.
5. **Decide and document the committed-vs-derived question** (see Assumptions #3): whether the
   canonical per-week files stay committed (as today, just now also self-healing via consolidation)
   or become gitignored/derived-only like `docs/REGISTRY.yaml`'s conceptual sibling `graphify-out/`.
   Either is acceptable; state which and why.
6. **Tests**: a fixture proving two tickets' per-ticket shard files never produce a git conflict
   even when both PRs are squash-merged in sequence (simulate via two throwaway git repos/branches,
   mirroring `tests/integrity/test_merge_union_crlf_duplication_repro.py`'s own throwaway-repo
   pattern); a consolidation round-trip test (per-ticket files in → canonical files out, byte-for-
   byte equivalent to today's direct-append format for existing consumers); a
   `working_log_exactly_one_row`-equivalent check that still holds after consolidation.

## Out of Scope
- **Changing what any consumer reads or how it queries the data.** `validate.py`, `query.py`,
  `monitoring_anomaly_validator.py`, and the rest of `tools/gate_checks/` must see the exact same
  canonical-file shape after consolidation as they do today. This is a write-path and sync-point
  change, not a schema change.
- **Removing the existing `merge=union` `.gitattributes` entries.** They stay — a real git merge
  (still common inside a single multi-ticket branch/PR, as this very epic demonstrated) still
  benefits from them; this ticket only closes the squash-merge gap they can't cover.
- **Any blocking gate.** Consistent with `[[feedback_agent_tooling_checks_proportionate]]` and this
  epic's own advisory-everywhere decision — consolidation staleness is a known, tolerable window
  (nothing currently gates ticket closure on immediate visibility of these files; CLAUDE.md's own
  Definition of Done already states run/event coverage is "guaranteed by workflow — not verified by
  done-checker").
- **Migrating historical data.** Only new writes from this ticket forward use per-ticket targets;
  existing weekly shard content is left as-is and simply becomes one of the "already consolidated"
  inputs.

## Acceptance Criteria
1. Two tickets closing on two different branches, each producing a squash-merged PR against `main`
   in sequence, never show a git conflict on any monitoring file — proven by a real-git-repo fixture
   test, not asserted by inspection.
2. After consolidation, `validate.py`/`query.py`/`generate_retro.py` produce identical output for a
   given week's data whether that data arrived via the old direct-append path or the new
   per-ticket-then-consolidate path — proven by a round-trip test.
3. `working_log.csv`'s existing squash-merge duplication failure mode
   (`TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`) cannot recur for any ticket using the
   new write path — proven by the same class of fixture as criterion 1.
4. The consolidation step is idempotent — running it twice on the same input produces the same
   output, no duplicate rows.
5. `done_checker_static.py`'s `working_log_exactly_one_row` condition (and any other condition
   reading these files) is confirmed to still pass identically after this change.
6. Scoped tests pass; the command and result are recorded in `## Test Summary`.

## Related Tickets
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — where this gap was surfaced (during discussion of
  the delivery lane's own squash-merge conflict tax), but this ticket is **not** a child of that
  epic — different subsystem (agent-monitoring's own data model, not the git/PR/CI delivery lane),
  same reasoning `TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK` used to stay a non-child
  sibling.
- `TCK-20260924-DELIVERY-COST-MEASUREMENT` — **must land first.** Both this ticket and that one
  touch `tools/agent-monitoring/`; per the epic's own explicit ordering constraint, nothing in the
  epic touches `tools/agent-monitoring/` ahead of that ticket, and this ticket must not duplicate or
  destabilize the module it builds on (`bash_command_mix.py`).
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`,
  `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` — the two confirmed real incidents this
  ticket is closing the root cause of.
- `TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX` — "why PRs in this repo conflict so routinely,"
  the same underlying condition, already solved differently for derived (not raw-log) data.

## Related Docs
- `.gitattributes` — the merge-driver configuration and its own documented gap, in detail.
- `docs/guides/agent_monitoring.md` — the monitoring write/read path this ticket changes.
- `docs/guides/delivery_process.md` — "PR Lifecycle" step 7, the squash-merge mechanics this ticket
  is working around.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/record_run.py`, `record_events.py`, `generate_retro.py`, `validate.py`,
  `query.py` — write and read paths
- `tools/working_log_writer.py` — the single sanctioned `working_log.csv` writer
- `.gitattributes` — may need a new entry for the per-ticket file glob pattern
- `tests/integrity/` — the existing merge-union/duplication test suite this ticket extends

## Assumptions / Open Questions
1. **Per-ticket file naming/shape.** One combined per-ticket file with type-tagged records, or three
   per-ticket files (`<TCK-ID>.runs.jsonl` etc.) mirroring today's three-canonical-file split?
   Recommend mirroring today's split — smaller diff for existing writer code, and consolidation
   logic stays a simple per-type concatenation rather than needing to split a combined file back
   apart.
2. **`working_log.csv`'s per-ticket staging shape.** CSV has one header row per file, which doesn't
   shard as cleanly as JSONL (each per-ticket file would need its own header, stripped during
   consolidation) — or the staging format could be JSONL (one ticket's row as a JSON object) with
   CSV emission deferred entirely to consolidation. Recommend the latter: it reuses the same
   consolidation code path as the other three files rather than inventing a second mechanism.
3. **Whether the canonical per-week files stay committed or become gitignored/derived-only** (like
   `docs/REGISTRY.yaml` conceptually, or `graphify-out/` literally). Recommend staying committed for
   now — a derived-only canonical file is a bigger behavioral change (every consumer needs the
   consolidation step run first, including on a fresh clone) for a benefit (avoiding committing
   already-conflict-proof derived data) that's smaller than the conflict-avoidance win itself.
   Revisit if consolidation staleness proves a real friction point in practice.
4. **Consolidation trigger cadence.** Piggybacking on the existing retro cadence (weekly / 5+
   tickets / before an agent-prompt change) may leave a multi-day window where per-ticket files
   exist but aren't yet folded in. Given nothing currently gates on immediate visibility (see Out of
   Scope), this is likely fine, but the standalone `make agent-monitoring-consolidate` command
   (Scope item 4) exists specifically so a session that wants fresher data isn't stuck waiting.

## Implementation Notes
**Branch/PR wiring is a deliberate deviation from the default one-ticket-one-branch rule, by
explicit user instruction (2026-09-24):** despite not being an epic child (see Related Tickets),
this ticket's implementation should land on the existing `github-delivery-process-epic` branch
rather than a fresh branch/PR, so it rides in the same eventual PR as the epic's own six tickets
rather than opening a second PR. Sequence it after `TCK-20260924-DELIVERY-COST-MEASUREMENT` (the
last-ordered epic ticket) both for the dependency reason above and so it's simply the last commit
on that branch before the batch PR opens.

## Test Summary
_To be filled during implementation._

## Files Changed
_To be filled during implementation._

## Completion Summary
Open.
