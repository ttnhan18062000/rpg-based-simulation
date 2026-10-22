---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT
phase: done
date: 2026-10-22
tags: [architecture, determinism, audit]
---

# TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT

## Title
Port-leak audit: an evidence table, with file:line, for every "known leak" in engine_execution_modes_proposal.md §5, each classed as breaking Mode 1 today or only Mode 3 and later

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`docs/plans/architecture/engine_execution_modes_proposal.md` §5 (from #719) lists a "known leak to close first" for each
proposed port (clock, random source, executor, commit path, event sink, state store and hash, process scope). The proposal
names this as the precondition for any Mode 3 work. The leaks come from lead-planner-u24's review and have not been
traced against the code. The user approved this audit on 2026-10-22 (#715 issuecomment-6345579717), from lead-planner's
brief. The work is a read-only code read with no simulation runs.

## Scope
- Write a new doc, `docs/plans/architecture/port_leak_audit.md` (frontmatter `layer: architecture`), with one row per
  leak. Each row gives:
  - port
  - leak
  - evidence `path:line`, at main `b281d0c3d` (state the SHA in the doc)
  - what the code does
  - **impact class**: `M1-now` (breaks Mode 1 determinism or the final hash today), `M2` (only once replay is off or the
    Mode 2 fast path is used), or `M3+` (only under parallel, process-pooled or relaxed execution)
  - why that class
  - suggested fix owner (`rpg-planner` or `perf-planner`)
- Cover, at minimum:
  1. **clock**: `kernel.py` `perf_counter_ns` and `time.sleep` pacing, `worker_manager.py:44/234`, `run_identity.py:21`.
     Say for each whether a wall-clock value reaches state, the hash, the event digest or only telemetry.
  2. **random source**: `scenario_checkpoint.py` restoring with `base_seed=0`; salted `hash()` at `military_conflict.py:339`;
     plus a sweep for any other `random.`, `hash(`, `id(`, `set` iteration order or `uuid` use on an authoritative path.
  3. **process-global singletons**: behavior_consumers, `ObservabilityConfig._override_mode`, the observability queue,
     stream adapter, decision_trace_writer, scenario_registry, content thread-local, and any others the read finds.
     For each, say whether two runs in one process (the Mode 3 pool case) would interfere.
  4. **CanonicalStateHasher coverage (the main item)**: list every `AuthoritativeState` field and say whether the hash
     covers it, with a `path:line` for both the field and the hasher site. Confirm or refute the §5 claim that the hash
     omits factions, clans, quest_registry, item_instances, terrain and recent_world_events. For each omitted field,
     say whether it is durable and mutable after world assembly (a real gap) or constant or derived (no gap).
     `docs/performance/hash_callsite_inventory.md` is the starting inventory.
  5. **executor**, **commit path** and **event sink**: one line each confirming or correcting the §5 entry.
- End with a "Findings to route" section: one block per `M1-now` or `M2` leak, written as a ready-to-send finding for
  rpg-planner or perf-planner. Do not send them; architecture-planner sends them.
- Add the doc to `docs/plans/architecture/README.md` Contents. Do not edit the proposal; that is item B, held for
  coordination with architecture-planner-u24.

## Out of Scope
- Any change under `src/**`, `tests/**` or `docs/architecture/**` (the v1 freeze is on, and these are other domains).
- Simulation runs, profiling or hash experiments. If a claim cannot be settled by reading, mark it `UNVERIFIED (needs run)`
  and say which run would settle it.
- Editing `engine_execution_modes_proposal.md` (item B) or the conformance-suite design (item C).

## Acceptance Criteria
- AC1: every §5 leak has a row with at least one `path:line` at the stated SHA, or an explicit "not found" with the search used.
- AC2: the hasher-coverage table lists every `AuthoritativeState` field, with covered/omitted and gap/no-gap verdicts.
- AC3: every row has an impact class (`M1-now`, `M2` or `M3+`) and a one-line reason.
- AC4: every `M1-now` and `M2` row has a drafted finding in "Findings to route", naming its owner.
- AC5: frontmatter validates, README Contents updated, `docs/REGISTRY.yaml` regenerated (`make docs-registry`) and committed.
- AC6: no file outside `docs/plans/architecture/**`, `docs/REGISTRY.yaml`, this ticket and `agent-working/agent-monitoring/`
  is changed.

## Related Tickets
- TCK-20261022-ARCHITECTURE-FOUR-SEATS (the seats)

## Related Docs
- docs/plans/architecture/engine_execution_modes_proposal.md (§5, §6)
- docs/plans/architecture/faster_feature_testing_draft_tickets.md
- docs/performance/hash_callsite_inventory.md
- docs/engine/kernel.md, docs/core/state.md
- docs/architecture/kernel_concurrency_design_philosophy (binding recorded decision)

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/kernel.py, src/engine/apply.py, src/core/state.py, the CanonicalStateHasher module, src/platform/rng.py,
  worker_manager.py, run_identity.py, scenario_checkpoint.py, military_conflict.py, src/observability/

## Assumptions / Open Questions
- Assumes a read at a fixed SHA is enough; anything needing execution is marked UNVERIFIED rather than run.
- Open: whether recent_world_events is meant to be hashed is an rpg semantics call. Record the fact and route the question; do not decide it.

## Implementation Notes
Context scan first (search_docs, then graphify query), then targeted reads. Hand-orchestrated close with
`--path-reason investigation_only`. Send the commit SHA to architecture-planner for review before any push.

## Test Summary
Read-only audit; no tests apply. `tools/validate_frontmatter.py` on the new doc: no violations. `make docs-registry` regenerated.

## Files Changed
- docs/plans/architecture/port_leak_audit.md (new)
- docs/plans/architecture/README.md (Contents row)
- docs/REGISTRY.yaml (regenerated)
- agent-working/ ticket move and monitoring shards

## Completion Summary
Port-leak audit written at main b281d0c3d. Key results: the hasher omits six mutable durable fields (item_instances,
recent_world_events, quest_registry, factions, clans, plus information_providers which the proposal missed; terrain is
constant, no gap); the clock leak is the default LIVE signal contract, not the pacing sleeps; checkpoint restore with
base_seed=0 corrupts stateless draws; the event-digest claim in section 5 was not confirmed. Five drafted findings (F1-F5)
for architecture-planner to route. Items UNVERIFIED are listed in section 8 of the doc.
