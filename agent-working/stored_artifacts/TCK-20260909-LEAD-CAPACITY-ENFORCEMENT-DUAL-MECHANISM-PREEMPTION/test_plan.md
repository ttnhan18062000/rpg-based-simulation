# Test Plan — TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION

This is a documentation-only disposition — no code changed under `src/`, so no new automated
tests. The real verification is the investigation's own instrumented evidence trail.

## Real evidence (see investigation.md for full detail)
- Real 500-tick instrumented `frontier_living_world` reproduction (seed 7, `hero_guild_perspective`,
  the same scenario/seed this whole audit arc uses), monkeypatching both
  `DetourSuggestionSystem.enforce_bandwidth()` and `CapacityEnforcementPhase.enforce()` directly.
- Both mechanisms confirmed live: `enforce_bandwidth()` called 10,570 times, the dedicated phase
  called 500 times (once per tick, 11,703 entity-update evaluations) — ruling out the "unreachable
  code" explanation before concluding anything about the collection itself.
- Three independent measurement angles confirm `entity.strategic.leads` is empty for every entity
  at every tick for the entire run: (1) running `len()` tally at every `enforce_bandwidth()` call;
  (2) snapshot of `entity_updates[*].strategic.leads_add_or_update` on entry to
  `CapacityEnforcementPhase.enforce()`; (3) direct inspection of live `state.entities` at the
  last-observed tick (0/49 entities had any lead).
- Root-cause trace of all four real `LeadState(...)` construction sites in `src/`, confirming each
  is unreachable under real defaults for a distinct reason (dead code, flag-gated off, update-only,
  structurally-unconstructed provider type) — ruling out that this is an artifact specific to this
  one scenario/seed rather than a general condition.

## Regression check
No `src/`/`tests/` files changed by this ticket. `tests/unit/strategic/
test_belief_staleness_decay_pipeline.py::test_capacity_enforcement_prunes_newly_decayed_lead_over_fresh_ones`
(the ticket's own originating test, which constructs the precondition synthetically) is left
unchanged — it remains valid evidence that the interaction is real *given* a pre-existing
over-capacity lead set; this investigation does not dispute or need to alter that test.
`tests/integrity/test_no_duplicate_content_blocks.py` and `validate_frontmatter.py` cover the
structural correctness of the ticket/doc changes.

## Acceptance criteria mapping
- Real evidence establishing how often/under what conditions preemption occurs in practice →
  investigation.md's instrumentation section: never, under real conditions, because the shared
  precondition is never met.
- Real evidence establishing design intent → investigation.md's call-site analysis (three call
  sites, one shared computation) plus the root-cause trace of why leads are never created —
  neither "superseded" nor "intentionally layered" applies; the premise of an active conflict does
  not hold.
- Design decision obtained via peer review before any implementation → obtained; disposition is
  "close on narrower claim, no code change," confirmed by peer review.
- If a fix is implemented, real test evidence the correct logic wins → N/A, no fix implemented;
  peer review explicitly agreed reconciling mechanisms that never fire is not a defensible use of
  a fix.
