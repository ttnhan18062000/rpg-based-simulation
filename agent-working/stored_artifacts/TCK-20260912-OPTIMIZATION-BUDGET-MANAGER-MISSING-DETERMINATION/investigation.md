# Investigation — TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION

## Real finding: this corrects the origin audit's own classification

The parent audit (`TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION`)
classified `budget_manager.py` as "genuinely missing — no live equivalent." Direct investigation
found there IS a live equivalent, just coarser: the wall-clock mid-tick throttle
(`kernel.py`'s `_phase_resolution()`, `should_throttle`) plus `ResourceGovernor`'s own
`tick_compute_ms` mode-escalation check (`governor.py`) genuinely catches real overruns — dropping
remaining work, forcing `DEGRADED`/`SURVIVAL` — cross-referenced from
`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`'s own earlier confirmation this tick.
It's whole-tick, post-hoc, not per-resource-category or proactive like `PhaseBudgetManager` would
be — but it is real, live, and it works.

This reclassifies the module's own status from "missing" to "partially covered by a coarser live
mechanism" — the same third category (partial supersession, not clean supersession or genuine
gap) the origin C1 audit already established for most of the rest of the `optimization/` package.
Confirmed by looking, not inherited from the survey pass — the survey's own "missing" label was
never re-verified against the real wall-clock/governor mechanism until this ticket checked.

Zero documented incidents found (`grep`'d closed tickets/docs) of a phase actually exceeding its
own declarative budget (`GovernorPolicy`/`PhaseBudgets`) uncaught — the real backstop already
exists and already fires when things actually go over.

## Disposition (user decision, routed via peer): delete, record the capability

Once reclassified as "a finer-grained version of something live," the disposition matches
capabilities 3/5/6 in the sibling `ORPHANED-CAPABILITY-DETERMINATION` exactly: a real,
non-redundant performance-management idea, addressing zero documented incidents, in a category the
user has explicitly deferred to a dedicated future performance effort. Deleted on priority/staleness
grounds, not because the idea is wrong — recorded in
`docs/plans/design_enhancement/performance_milestones_epic.md`.

## Non-import-reference guard

`.github/workflows/*.yml`/`Makefile`: zero hardcoded references to `budget_manager.py`,
`PhaseBudgetManager`, or its dedicated test files. Found and deleted its own dedicated test file at
`tests/unit/perf/test_phase10_phase_budget_manager.py` (missed by the initial narrower grep, caught
by a second, class-name-targeted pass) plus `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`
(confirmed entirely dependent on the deleted class, no independent coverage riding along).
