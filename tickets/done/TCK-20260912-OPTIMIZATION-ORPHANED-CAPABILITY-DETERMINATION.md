---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION
phase: done
date: 2026-09-12
tags: [performance, architecture]
---

# TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION

## Title
Five real capabilities, orphaned when their containing modules' core job was superseded elsewhere — are any of them actually wanted?

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found and determined during `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION` (`stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION/investigation.md`). That ticket's own headline finding, refining the parent audit's
"superseded, not missing" conclusion: **supersession in `src/domains/optimization/` has been
partial, not total, for 4 of the 8 modules.** A live mechanism took over each module's *core* job
via a different implementation — but in every one of these 4 cases, the dead module also contains a
genuinely distinct capability that the live replacement never carried forward, and no live
equivalent exists anywhere for it. Grouped into one determination ticket per peer review's explicit
direction, since "is this wanted" is the same shape of question across all 5 — one decision
session, not four fragmented ones.

**Do not read any of the 4 modules' names below as "delete the file."** Each one's superseded core
and orphaned capability live in the same file, often the same class. The disposition for each is at
method/behavior granularity — see Scope.

**The 5 capabilities:**
1. `degradation.py`'s `GracefulDegradationManager.should_skip_phase()` — skips entire named
   optional phases (`ENABLE_WORLD_EMERGENCE`, `ENABLE_LIFE_ARC_CAMPAIGNS`, `ENABLE_COOPERATION`)
   outright under DEGRADED/CRITICAL pressure. The live pressure-response mechanism
   (`PhaseBudgetGovernor.evaluate()`) only throttles budget *numbers*, never skips a whole phase by
   name.
2. `degradation.py`'s `GracefulDegradationManager.resolve_content_source()` — under degraded/
   critical pressure, prefers catalog-driven content over hardcoded static defaults, cheapest-first.
   No comparable "prefer catalog under pressure" logic exists anywhere else.
3. `degradation.py`'s `GracefulDegradationManager.get_provider_cap()` — scales a "provider cap"
   number down under pressure (÷2/÷3/÷4 by level). The same *pattern* `GovernorPolicy` already
   applies to `candidate_budget`/`movement_budget`/`strategic_budget`, just never extended to this
   category.
4. `cache_strategy.py`'s `CacheStrategy`'s `shop_stock`/`services`/`pressure` region-scoped query
   caching with event-driven invalidation (the `resource_nodes` use case is redundant with
   `WorldIndexService` regardless of this ticket's outcome).
5. `dirty_scheduler.py`'s `DirtyWorkScheduler.next_entities()`/`next_regions()` — bounded,
   incremental, cross-tick batch draining of a persistent dirty backlog. The live `DirtySet`/
   `DirtySetBuilder` computes the full dirty set fresh every tick; nothing anywhere in the engine
   maintains a persistent, boundedly-drained backlog.
6. `trace_governor.py`'s `TraceVolumeGovernor.process_events()`'s "summarize N repeated messages
   into one counted entry" behavior specifically (the cap-and-keep-important-events job is
   redundant with `EventRecorder`'s own volume bounding regardless of this ticket's outcome; the
   closest live analogue, `AlertDeduplicator.should_suppress()`, fully suppresses rather than
   summarizing-with-count, and only covers the alerts pipeline, not general trace events).

(Numbered 1-6 above since `degradation.py` contributes 3 of the 6 individual behaviors to this
determination, not 5 modules × 1 behavior each.)

## Scope
- For each of the 6 numbered capabilities above: is it actually wanted? This is a real product/
  design decision, not something to resolve unilaterally during Investigate — route through peer
  review before implementing either outcome.
- **If NOT wanted**: delete the whole containing module/class, including its superseded core —
  nothing is served by the superseded core surviving standalone once its unique reason for existing
  is declined. Concretely: if none of 1-3 are wanted, delete `degradation.py` in full (including
  `DegradationLevel`/`update_pressure()`/`get_level()`, its confirmed-superseded core); if 4 isn't
  wanted, delete `cache_strategy.py` in full; if 5 isn't wanted, delete `dirty_scheduler.py` in
  full; if 6 isn't wanted, delete `trace_governor.py` in full.
  - **Required step before any deletion — verify non-import references too, not just Python-level
    ones.** Confirmed as a real, recurring blind spot when the two prior deletions in this same
    package (`TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION`,
    `TCK-20260912-OPTIMIZATION-MEMORY-LIMITS-ABANDONED-DESIGN-DELETION`) both grepped only for the
    class/function names (Python imports) and missed two hardcoded `tests/unit/diagnostics` path
    arguments in `.github/workflows/test.yml` — a real CI regression, caught only by CI itself, not
    by the deletion's own verification. Before deleting any of these modules or their test files:
    grep the module's own filename/path and its test file's own directory path (not just the class/
    function names) across `.github/workflows/`, `Makefile`, and `docs/` — a path can be referenced
    as a bare string (a CI job's positional pytest argument, a Makefile target, a doc's file
    listing) with no Python import anywhere.
- **If wanted**: the real implementation shape is a separate design question from this
  determination — do not presume it here. The strong likely direction, per this investigation's own
  findings, is to rescope each kept capability to plug into whichever live mechanism already owns
  the adjacent superseded half (`ResourceGovernor`'s own `RuntimeMode` for 1-3, `WorldIndexService`
  for 4, `DirtySet` for 5, `EventRecorder` for 6) rather than reviving the dead module's own
  parallel state. In particular, if any of 1-3 is kept, do **not** let `update_pressure()`/
  `get_level()`/`DegradationLevel` survive as a shim just to feed it a pressure signal — that
  recreates the exact dual-mechanism-preemption shape `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-
  DUAL-MECHANISM-PREEMPTION` already found real elsewhere in this codebase.
- Correct `admission_control.py`'s own comments (`admission_control.py:59-60,96-97`) once
  `cache_strategy.py`'s disposition (capability 4) is settled — they currently cite `cache_strategy.
  py` by name and line number as if it's a live dependency; confirmed it isn't
  (`admission_control.py` never imports from `src.domains.optimization` at all, it only borrowed
  `CacheStrategy.put()`'s eviction-shape pattern for its own, unrelated per-client rate-limiting
  domain). Point the comment at the real pattern source, or state plainly it's illustrative only —
  either way, stop implying a dependency that doesn't exist.

## Out of Scope
- The other 4 follow-up tickets from the same determination
  (`TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION`,
  `TCK-20260912-OPTIMIZATION-MEMORY-LIMITS-ABANDONED-DESIGN-DELETION`,
  `TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION`,
  `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION`) — each has its own scope.
- `budget_manager.py` and `provider_enforcement.py` — genuinely missing with no live equivalent at
  all, a different question ("should we build this from scratch") than this ticket's own ("this
  orphaned piece was left behind when something else took over the core job — is it still wanted").
  Filed as their own separate tickets per peer review's explicit instruction.

## Acceptance Criteria
- [x] Each of the 6 numbered capabilities has an explicit "wanted" or "not wanted" determination,
      obtained via peer review (and, for this genuine priority/architecture decision, the user)
      before implementation: **all 6 not wanted now** — 1/2/4 because the concepts they target
      have aged out of the live codebase (stale phase-flag names, no live Shop/regional-pressure
      system); 3/5/6 because they are real but address zero observed problems, in a performance
      category the user has explicitly deferred to a dedicated future effort.
- [x] For each "not wanted" outcome: the whole containing module/class is deleted (superseded core
      included), confirmed via grep that zero references remain — covering non-import references
      (CI workflow paths, `Makefile` targets, doc file listings), not just Python-level imports.
- [x] "Wanted" outcome AC does not apply — none of the 6 was determined wanted now.
- [x] `admission_control.py`'s own misdirecting comments are corrected — updated to reflect the
      deletion (the pattern reference is now explicitly illustrative-only, citing no live file).
- [x] The capability ideas (not the stale implementations) are recorded where the future
      performance effort will find them:
      `docs/plans/design_enhancement/performance_milestones_epic.md`'s new "Preserved capability
      ideas" section, explicit that this is a priority/staleness deletion, not a worthlessness
      finding.

## Related Tickets
- `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` (origin — the full
  8-module determination)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit, Cluster C1)
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (the dual-mechanism-preemption
  shape to avoid recreating if capabilities 1-3 are kept)

## Related Docs
- `stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION/
  investigation.md` (sections 1, 3, 4, 8, full evidence for each of the 6 capabilities)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/optimization/degradation.py`, `cache_strategy.py`, `dirty_scheduler.py`,
  `trace_governor.py`
- `src/engine/governor.py` (`ResourceGovernor`), `src/engine/phase_governor.py`
  (`PhaseBudgetGovernor`), `src/engine/world_index.py` (`WorldIndexService`),
  `src/core/dirty.py` (`DirtySetBuilder`/`DirtySet`), `src/observability/event_recorder.py`
  (`EventRecorder`) — the live mechanisms each kept capability would need to plug into
- `src/api/admission_control.py` (the misdirecting comment)

## Assumptions / Open Questions
- Whether any of the 6 capabilities is actually wanted is the entire point of this ticket —
  deliberately not pre-judged. A "none wanted" outcome (delete all 4 modules in full) is as valid an
  answer as "some wanted."

## Implementation Notes
Full evidence per capability recorded in
`stored_artifacts/TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION/investigation.md`.
Reported to peer before deciding anything; disposition (delete all 6, record ideas) came back as
the user's own decision. Capability 3's own "is provider-call rate limiting needed" question was
explicitly answered once, under the sibling `PROVIDER-ENFORCEMENT-MISSING-DETERMINATION` ticket,
and inherited here rather than re-investigated — per peer's explicit instruction that answering it
twice would be exactly the duplication this arc has spent this whole batch deleting.

Deleted `degradation.py`, `cache_strategy.py`, `dirty_scheduler.py`, `trace_governor.py` in full,
plus their 3 dedicated test files. Found and preserved (not deleted) real, independent test
coverage riding along in `tests/unit/core/test_degraded_fallback.py` — 4 of its 10 tests covered
live code (`CatalogRepository.get_lowest_cost_for_type()`, a `registries.py` module-default check)
with no dependency on the deleted `GracefulDegradationManager`; removed only the 6 tests exercising
the deleted class. Applied the non-import-reference guard (CI workflow paths, `Makefile` targets)
to all 4 modules before deleting — zero hits, unlike the diagnostics-deletion miss earlier this
batch. Corrected `admission_control.py`'s two comments that cited `cache_strategy.py` by
name/line as an illustrative pattern reference (already flagged stale by this ticket's own Scope
even before the deletion; now doubly stale). Recorded the 3 structurally-real capability ideas
(provider rate-limiting inherited from the sibling ticket, cross-tick dirty-work drain, and
repeat-event summarization) in `docs/plans/design_enhancement/performance_milestones_epic.md`'s new
section, explicit that this is a priority/staleness deletion, not a worthlessness finding.

## Test Summary
`pytest tests/unit/domains/optimization/ tests/unit/perf/ tests/perf/ tests/unit/core/
tests/unit/observability/ tests/unit/world/providers/ tests/integration/perf/
tests/api/test_admission_control.py -q -m "not slow and not extra_slow"`: 1528 passed, 1 skipped —
full regression sweep, no failures. `test_degraded_fallback.py` specifically: 4 passed (down from
10, the 6 removed tests exclusively covered the deleted class). Post-deletion grep: zero remaining
references to any of the 4 deleted classes anywhere in `src/`/`tests/`, and zero hardcoded
references in `.github/workflows/*.yml`/`Makefile`.

## Files Changed
- `src/domains/optimization/degradation.py` — deleted.
- `src/domains/optimization/cache_strategy.py` — deleted.
- `src/domains/optimization/dirty_scheduler.py` — deleted.
- `src/domains/optimization/trace_governor.py` — deleted.
- `tests/integration/perf/test_phase10_graceful_degradation.py` — deleted.
- `tests/unit/perf/test_phase10_cache_invalidation.py` — deleted.
- `tests/unit/perf/test_phase10_dirty_work_scheduler.py` — deleted.
- `tests/unit/observability/test_phase10_trace_volume_governor.py` — deleted.
- `tests/unit/core/test_degraded_fallback.py` — edited: removed the 6 tests exercising the deleted
  `GracefulDegradationManager`, kept the 4 independent tests.
- `src/api/admission_control.py` — two comments corrected to stop citing the deleted
  `cache_strategy.py` as if it were live.
- `docs/plans/design_enhancement/performance_milestones_epic.md` — new "Preserved capability ideas"
  section, shared with the two sibling tickets.

## Completion Summary
All 6 numbered capabilities determined not wanted now — 1/2/4 for demonstrated staleness (target
concepts that no longer exist in the live codebase), 3/5/6 for being real-but-unneeded performance
capabilities the user's own standing direction defers to a future dedicated effort. Deleted all 4
containing modules in full, preserved independent test coverage found riding along, corrected a
stale comment reference, and recorded the underlying capability ideas — not the stale
implementations — where the future performance effort will find them. This is a deletion on
priority and staleness grounds, stated explicitly, not a finding that the capabilities are
worthless. No known material gap left unstated.
