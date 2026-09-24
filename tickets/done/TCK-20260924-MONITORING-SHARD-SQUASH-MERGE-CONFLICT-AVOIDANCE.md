---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE
phase: done
date: 2026-09-24
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE

## Title
Per-ticket write targets for `agent-monitoring/data/*/*.jsonl` and `tickets/working_log.csv`,
consolidated at retro time, to remove the one gap `merge=union` doesn't cover: GitHub squash-merge

## Status
DONE

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
- `python3 -m pytest tests/tools/test_monitoring_consolidation.py -v` (repo venv): **13 passed** —
  including a real throwaway-git-repo fixture proving two per-ticket files never conflict under
  sequential squash-merges (AC1), round-trip equivalence (AC2), idempotency (AC4), and
  confirmation that `writer.py` and `done_checker_static.py` are unaffected (AC5).
- Fixing this ticket's own change surfaced real, load-bearing breakage in three existing test
  files that pinned the *old* shared-file write path directly — each investigated and fixed
  individually, not assumed:
  - `tests/tools/test_record_run.py` (4 tests), `tests/tools/test_post_tool_hook.py` (1 test),
    `tests/tools/test_record_events.py` (6 tests) — path assertions updated to the new per-ticket
    filename. All three files' full suites re-run clean (22, 22, 31 passed respectively).
  - `tools/retrieval_events.py::emit_retrieval_event()` — a **third, previously undiscovered**
    independent copy of the write-target formula (explicitly documented as mirroring
    `record_events.py`'s own logic), broken by this ticket's change and now updated identically.
    `tests/tools/test_retrieval_events.py`: 36 passed.
  - `tests/tools/test_execution_identity_end_to_end.py` (3 tests) — its own path-reproducing
    helpers needed a `ticket_id` parameter; the "prefix unchanged" test's semantics were
    redesigned (not just path-patched) since a ticket-scoped write now creates a brand-new file
    rather than appending to a seeded one — the stronger, correct claim for the new design is that
    the pre-existing shared/legacy files are byte-for-byte untouched. All 3 pass.
- Full regression: `python3 -m pytest tests/tools/ -m "not slow"` — **3018 passed, 25 skipped, 28
  deselected, 1 xfailed**, 0 failed.
- `python3 -m pytest tests/integrity/` — 37 passed, 1 skipped, 1 xfailed, **1 failed**:
  `test_logic_guards.py::test_autonomous_loop_determinism_drift_guard`, a simulation-kernel
  determinism test with no relationship to any file this ticket touches, and matching an
  already-known, already-parked nondeterminism issue in this repo (confirmed non-regression: it
  reproduced as `xfailed`, not a hard failure, on an isolated re-run — consistent with pre-existing
  flakiness, not something introduced here). Reported per Gate Integrity, not silently dismissed
  or fixed.
- Real live confirmation, not just fixtures: this ticket's own session's monitoring writes were
  already observed landing in a real per-ticket file
  (`agent-monitoring/data/2026-W39/TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE.tools.jsonl`)
  immediately after the `post_tool_hook.py` edit, produced by the live hook, not a test harness.

## Files Changed
- `tools/agent-monitoring/post_tool_hook.py` — per-ticket `tools_file` when `ticket_id` is truthy.
- `tools/agent-monitoring/record_run.py` — per-ticket `runs_file` when `run_id` is truthy.
- `tools/agent-monitoring/record_events.py` — per-ticket `events_file` per `run_id` group;
  `compute_tool_stats()`'s glob widened to also read per-ticket `tools.jsonl` files.
- `tools/agent-monitoring/monitoring_consolidation.py` (new) — the consolidation module and CLI.
- `tools/agent-monitoring/generate_retro.py` — calls `consolidate_all()` before reading, wrapped
  in try/except (fail-open).
- `tools/retrieval_events.py` — `emit_retrieval_event()`'s own independent copy of the write-target
  formula updated identically (see Test Summary — a real, previously-undiscovered third writer).
- `Makefile` — new `agent-monitoring-consolidate` target.
- `tests/tools/test_monitoring_consolidation.py` (new) — 13 tests.
- `tests/tools/test_record_run.py`, `tests/tools/test_post_tool_hook.py`,
  `tests/tools/test_record_events.py`, `tests/tools/test_retrieval_events.py`,
  `tests/tools/test_execution_identity_end_to_end.py` — updated to the new per-ticket write path;
  no assertion weakened, several strengthened (see Test Summary).
- `staging_artifacts/TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE/
  {investigation,plan,test_plan}.md` (new).
- **Not changed** (disclosed scope reduction — see investigation.md):
  `tools/working_log_writer.py`, `tickets/working_log.csv`'s write path,
  `tools/gate_checks/done_checker_static.py::check_working_log_exactly_one_row()`.

## Completion Summary
Implemented per-ticket write targets for `agent-monitoring/data/*/*.jsonl` (`runs`/`events`/
`tools`), removing the one gap `.gitattributes`' `merge=union` doesn't cover: a GitHub squash-merge
invokes no merge driver at all, so two tickets both appending to the same shared weekly file could
still conflict or duplicate under squash-merge even though a real git merge already handles this
case cleanly (confirmed live earlier this same epic batch). Two different tickets writing to two
different per-ticket files can never collide on a diff hunk, proven against a real throwaway git
repo reproducing the exact sequential-squash-merge shape, not asserted by inspection.
Consolidation (`tools/agent-monitoring/monitoring_consolidation.py`) folds per-ticket files back
into the canonical per-week shape every existing reader expects, wired into the existing retro
cadence plus an on-demand `make agent-monitoring-consolidate` target — idempotent by deleting a
per-ticket file only after its lines are successfully folded in, deliberately not manifest-tracked
(a manifest would itself be new, small, non-append-only state with its own merge-conflict
exposure — the exact class of problem this ticket removes, reintroduced at a smaller scale).

**Deliberate, disclosed scope reduction**: `tickets/working_log.csv`'s write path is unchanged.
Investigation found `done_checker_static.py::check_working_log_exactly_one_row()` reads that file
**synchronously at every ticket's own close** (unlike the JSONL files, which have no such
dependency — CLAUDE.md's own Definition of Done states their coverage is "guaranteed by
workflow — not verified by done-checker"), with deliberately nuanced reopen-vs-duplicate detection
logic. Deferring its write to retro-cadence consolidation, as this ticket's own Assumption 2
recommended, would break that check for every ticket closed via the new path until the next retro
run. Fixing this properly needs either extending that check's own logic or a different
synchronization mechanism — real, correctly-scoped follow-up work, not a rushed addition here. AC3
is therefore **not satisfied by this ticket**; `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-
GAP`'s existing detection-only mitigation remains the standing protection for `working_log.csv`.

Fixing the in-scope JSONL change surfaced real breakage in existing tests across 5 files,
including a third, previously undiscovered independent copy of the write-target formula in
`tools/retrieval_events.py` — found only by running the full regression suite, not by inspection
of the ticket's own Related Code Areas list, which didn't name that file. Every found breakage was
investigated and fixed on its own merits, not assumed away. One pre-existing, already-known,
already-parked simulation-determinism test failure in `tests/integrity/` (unrelated to any file
this ticket touches) was reported, not silently dismissed. `data_runs_clean` is expected to FAIL
again on this close for the same pre-existing, shared-worktree reason as every other close in this
batch.
