# Test Plan — TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION

This is a determination-only ticket — no `src/`/`tests/` code changed, so no new automated tests.
The real verification is the investigation's own evidence trail: each of the 8 modules compared
directly against the real live mechanism doing its job today (read, not grepped-and-assumed), with
one explicit self-correction recorded (`trace_governor.py`) to demonstrate the check held under its
own stated method.

## Real evidence (see investigation.md for full detail)
- `degradation.py` vs. `ResourceGovernor`: read both files in full; confirmed structural match on
  core pressure-level computation; confirmed no live equivalent for `should_skip_phase()`/
  `resolve_content_source()`/`get_provider_cap()` via targeted checks of `PhaseBudgetGovernor.
  evaluate()` and a repo-wide grep for catalog-preference-under-pressure logic.
- `budget_manager.py` vs. live `GovernorPolicy`/`PhaseBudgets`: read both; confirmed different
  enforcement model (declarative pre-computed vs. imperative stateful), not merely different
  numbers.
- `cache_strategy.py` vs. `WorldIndexService`/`admission_control.py`: read `admission_control.py`'s
  own comments and confirmed no real import/dependency on `cache_strategy.py`, only a borrowed
  eviction-shape pattern for an unrelated domain; read `world_index.py` and confirmed a real,
  functionally-overlapping live mechanism for the `resource_nodes` case specifically.
- `dirty_scheduler.py` vs. `DirtySetBuilder`/`DirtySet`: read `src/core/dirty.py` directly, confirmed
  no `next_*`/batch-scheduling methods exist live.
- `memory_limits.py`: grepped `src/core/strategic.py` and `src/core/` for any opponent/reward/
  cooperation-memory tracked state; found none — confirms abandoned design, not a capability gap.
  Confirmed `add_fact()`'s live equivalent via `assimilation.py:48-53` and its own citing comment in
  `action_intent.py:158`.
- `diagnostics.py` vs. `AlertsManager`/`AlertRouter`: confirmed live via a real `[ALERT]
  type=WatchdogTrip` observed firing during this ticket's own earlier instrumentation runs this
  arc.
- `provider_enforcement.py`: checked `src/world/providers/`, `src/domains/information/`, and
  `admission_control.py`'s own rate limiter for any live equivalent at any scope; found none.
- `trace_governor.py`: self-corrected an initial narrow-grep false negative by checking
  `EventRecorder`'s real, broader volume-management mechanism directly; confirmed live and
  functionally overlapping for the core cap-and-keep-important-events job, with one specific
  behavior (repeat-summarization) still unmatched after the broader check.

## Regression check
No `src/`/`tests/` files changed by this ticket. `tests/integrity/test_no_duplicate_content_blocks.py`
and `validate_frontmatter.py --content-type ticket` cover the structural correctness of this ticket
and its 5 filed follow-ups.

## Acceptance criteria mapping
- Each of the 8 modules has an explicit, evidence-backed determination → investigation.md's 8
  numbered sections plus the summary table.
- For every module determined superseded, confirmed no unique behavior would be silently lost, or
  named as a real gap to preserve → done for all 8; the "no module is clean" finding IS this
  confirmation working as intended.
- For any module determined genuinely missing, a wire/delete/document decision routed through peer
  review before implementation → Tickets C/D/E each route their own real decision to whoever picks
  them up, per this ticket's own Scope (determine, don't implement, in the same pass).
- `admission_control.py`'s own `cache_strategy.py`-referencing comments corrected to match real
  disposition → confirmed misdirecting (implies a dependency that doesn't exist); correction folded
  into Ticket C's own scope, since it should land alongside whatever `cache_strategy.py`'s eventual
  disposition turns out to be, not as a disconnected doc fix here.
