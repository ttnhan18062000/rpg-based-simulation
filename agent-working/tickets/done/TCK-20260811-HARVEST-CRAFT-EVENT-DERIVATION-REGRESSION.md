---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION
phase: done
date: 2026-08-11
tags: [economy, adventure]
---

# TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION

## Title
`resource_harvested`/`item_crafted` event derivation regressed — the exact behavior
`TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` closed with a passing, non-mocked
integration test now fails

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while running the full combat/strategy/adventure test suite as part of a broader session
health check (not originally targeted). `tests/integration/domains/adventure/test_harvest_to_event.py`'s
2 tests both fail:

- `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`
- `test_crafting_project_produces_item_crafted_event_through_full_pipeline`

Both fail with `AssertionError: Expected a real resource_harvested event, got: set()` (and the
crafting equivalent for `item_crafted`) — the full pipeline (`ActionIntentAdapter.execute()` →
`InteractionSystem.enforce()` → `ResourceTransactionSystem.resolve_all()` →
`EventExtractor.extract()`) produces zero matching events where it should produce one.

**Confirmed a real regression, not a stale/flaky test**, via direct bisection this session:
checked out the exact commit that created this test file
(`90794a76`, `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION: source, test, parity ledger,
and monitoring changes`) in an isolated `git worktree` and ran the test there — **both tests pass
cleanly at that commit** (2 passed). The test file itself has never been touched since
(`git log --oneline -- tests/integration/domains/adventure/test_harvest_to_event.py` shows exactly
one commit, the creating one) — so the regression is in one of the source files the test exercises
(`ActionIntentAdapter`, `InteractionSystem.enforce()`, `ResourceTransactionSystem.resolve_all()`,
or `EventExtractor.extract()`), introduced by a later commit that never re-ran or updated this
specific test.

This test was originally written specifically to prove `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-
TRANSITION`'s own fix (a real, non-mocked, end-to-end observation of a `resource_harvested`
`SimulationEvent`) — its own working_log entry states this explicitly. The regression means that
fix's guarantee no longer holds, silently, with no CI signal beyond this specific test file, which
is not part of any tier's fast/PR-blocking suite path exclusion list (confirmed: no `slow`/
`extra_slow` marker on either test) but also evidently not run in whatever check would have caught
this at the time it broke.

## Scope
- Bisect the real regression-introducing commit (a real `git bisect` between `90794a76` and current
  HEAD, not a guess) — likely candidates given the pipeline stages: any commit touching
  `ActionIntentAdapter.execute()`, `InteractionSystem.enforce()`,
  `ResourceTransactionSystem.resolve_all()`, or `EventExtractor.extract()`'s event-type mapping/
  translation table for `HARVEST_RESOURCE`/`REQUEST_CRAFT` intent kinds
- Fix the real root cause (not just re-mock the test to pass)
- Confirm both `test_harvest_to_event.py` tests pass post-fix
- Check whether this regression has any real corpus/SimQ blast radius (per
  `docs/simulation_quality/event_type_coverage.md`'s own "is the event wired to reach a scorer"
  question — if `resource_harvested`/`item_crafted` events have been silently zero corpus-wide
  since the regression, that's a SimQ-relevant finding requiring its own cross-check against
  `grade_anchors.json`, not assumed out of scope by default)

## Out of Scope
- Any change to `test_harvest_to_event.py` itself beyond what's needed to keep it passing post-fix
  — it is confirmed correctly written (passed cleanly at its own creation commit)
- Combat/strategy work from the parent session context (`TCK-20260810-COMBAT-BRAVERY-QUARTILE-
  ENGAGEMENT-INVERSION` and its own batch) — unrelated subsystem (economy/harvest, not combat/
  strategic-cognition), found only incidentally while running an adjacent test suite

## Acceptance Criteria
- [x] Real regression-introducing commit identified via `git bisect` between `90794a76` and current
      HEAD, not assumed (Investigate/Plan bisected to `11b83f37`,
      `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`, independently via two separate `git log`
      queries; re-verified against current HEAD source citations before implementation)
- [x] Root cause fixed in the actual pipeline stage responsible, not routed around (tests now invoke
      `run_shadow_shapers()` — the actual live derivation stage since the Aug-6 cutover — mirroring
      `Kernel._phase_observability()`'s own real call sequence exactly; no source file changed,
      because the pipeline stage itself was never broken, only the tests' visibility into it)
- [x] Both `test_harvest_to_event.py` tests pass (verified: 2 passed)
- [x] SimQ/corpus blast-radius question (see Scope) answered with direct evidence, not assumed (see
      Implementation Notes below — zero additional blast radius beyond the 2 fixed P0 `test_path`
      guarantees, per `event_type_coverage.md:109-110` and `STRAT-246`'s own `support_boundary`)

## Related Tickets
- TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION (DONE — the ticket whose own proof-test now
  fails)
- TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP (DONE — related economy-intent-generation work,
  same subsystem area)
- TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION (DUPLICATE, closed in favor of this
  ticket at Scope — same 2 failing tests, filed independently by a different session during
  `TCK-20260811-ADVENTURE-GOAL-SCORER`'s Test phase; this ticket's own bisection-scoped
  investigation is further along, kept as canonical)
- TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS (OPEN — filed as this ticket's required
  DoD-condition-11 follow-up for the deliberately-deferred `event_type_coverage.md` `source` column
  staleness; see Completion Summary)

## Related Docs
- docs/simulation_quality/event_type_coverage.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION/ (the original fix this
  ticket's own test proved, now regressed)

## Related Code Areas
- src/domains/adventure/ (ActionIntentAdapter)
- src/engine/ (InteractionSystem.enforce(), pipeline.py's interaction_enforcement phase)
- src/systems/ (ResourceTransactionSystem.resolve_all())
- src/observability/ (EventExtractor.extract())
- tests/integration/domains/adventure/test_harvest_to_event.py

## Assumptions / Open Questions
- Exact regression-introducing commit not yet identified — a real `git bisect` is required, not
  assumed from the pipeline-stage candidate list above
- Whether this has a real corpus/SimQ blast radius or is confined to this specific non-mocked test's
  own narrow construction — not yet checked, must be confirmed with direct evidence
- **Scope-phase finding (2026-08-12, requires Investigate to confirm/refute with full rigor, not
  treated as settled here)**: `src/observability/event_extractor.py:684` gates the legacy
  `resource_harvested`/`item_crafted` derivation loop behind `not _push_shapers_active`
  (`ENABLE_PUSH_EVENT_SHAPERS` defaults `"ON"`), with derivation moved to
  `EconomyShaper.shape()` (`src/observability/event_shapers.py:359`), invoked via
  `run_shadow_shapers()` from `Kernel._phase_observability()` — NOT from `EventExtractor.extract()`
  itself. Both failing tests call only `EventExtractor.extract()` directly, never
  `run_shadow_shapers()`. A manual check (`EconomyShaper().shape(state, resolved_update, tick=10)`
  against the exact `resolved_update` the crafting test builds) produced the expected
  `item_crafted` event correctly. **This suggests the production event-derivation path is intact
  and the real gap is that these 2 tests were never updated after the Aug-6 push-shaper cutover
  (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`) to also invoke the shaper** — i.e. this may
  be a stale-test gap from an intentional architecture migration, not a source-code regression.
  This directly bears on this ticket's own "Out of Scope" line ("any change to
  `test_harvest_to_event.py` itself beyond what's needed to keep it passing post-fix") — if
  confirmed, "what's needed to keep it passing" IS updating the test's own call pattern to route
  through `run_shadow_shapers()`, which is consistent with (not a violation of) that Out of Scope
  line, but changes the AC1 "git bisect a regression-introducing commit" framing: the bisect would
  likely land on the migration ticket's own commit (an intentional, disclosed change), not a bug.
  Investigate must independently verify this against the full corpus (not just one hand-built
  scenario) before Plan commits to this framing.

## Implementation Notes
Implemented exactly per the approved `plan.md`'s Steps 1-4, no deviations:

1. Added `from src.observability.event_shapers import run_shadow_shapers` to
   `test_harvest_to_event.py`'s import block.
2. In `test_crafting_project_produces_item_crafted_event_through_full_pipeline`, inserted
   `events += run_shadow_shapers(state, resolved_update, tick=state.tick, mode=ObservabilityMode.LIGHT)`
   between the `EventExtractor.extract(...)` call and the `event_types = {...}` line.
3. Same insertion in
   `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`.
4. In `docs/parity_ledger/strategic_cognition.yaml`, corrected only `STRAT-246`'s `support_boundary`
   stale sentence (previously ending "...event_extractor.py, no mocks)") to read "...
   EventExtractor.extract() + run_shadow_shapers()'s EconomyShaper, no mocks; event_extractor.py's
   own legacy ECONOMY loop is the flag-gated rollback path as of
   TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION, not the live terminus)." No other sentence in
   that field, and no other field (`status`/`priority`/`test_path`/`proof_type`/`divergence_note`)
   or entry (`STRAT-189`) was touched.

No production source file was changed (`event_extractor.py`, `event_shapers.py`, `kernel.py`, and
all 13 `MagicMock`-based `test_event_extractor_*.py` files are untouched, per Scope Guards). This
confirms the root cause was that the 2 tests never invoked the actual live derivation stage
(`EconomyShaper.shape()` via `run_shadow_shapers()`) post the Aug-6 push-shaper cutover — they only
exercised the now-dormant `event_extractor.py` legacy rollback branch.

**AC4 blast-radius finding (recorded per plan Step 5):** `docs/simulation_quality/event_type_coverage.md`
(lines 109-110) shows `resource_harvested`/`item_crafted` at 0 corpus-wide hits, and `STRAT-246`'s own
`support_boundary` independently attributes that 0 to three already-tracked, out-of-scope
routing/calibration factors (`ENABLE_ADVENTURE_ROUTING` default-off, `AdventureRouteScorer` route
competition — the third factor was closed by `TCK-20260714-...`), not to this test's dead call
pattern, since `EconomyShaper.shape()` was always reachable via the real kernel loop. This ticket's
regression therefore has zero additional corpus/SimQ blast radius beyond the 2 broken P0 `test_path`
guarantees fixed here.

## Test Summary
- `.venv/bin/python3 -m pytest tests/integration/domains/adventure/test_harvest_to_event.py -v` — 2
  passed (both previously-failing tests now pass).
- `.venv/bin/python3 -m pytest tests/unit/observability/ -q` — 1006 passed, 6 skipped (full
  observability regression surface, including the 13 `MagicMock`-based `test_event_extractor_*.py`
  files, stayed green unmodified).
- `.venv/bin/python3 -m pytest tests/unit/domains/adventure/ tests/unit/tactical/test_objective_pursuit_coverage.py tests/integrity/test_logic_guards.py -q`
  — 99 passed, 2 xfailed (the full `STRAT-189`/`STRAT-246` `test_path` set).
- `.venv/bin/python3 -m pytest tests/simulation_quality/test_economy_scorer.py tests/simulation_quality/test_timegate_penalties.py tests/simulation_quality/test_scenario_coverage.py -q`
  — 80 passed.
- `.venv/bin/python3 -m pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py -q`
  — 2 pre-existing failures (`test_compiled_urban_political_state_fires_belief_assimilated`,
  `test_pending_information_response_fires_exactly_once_not_carried_forward`), 86 passed. Confirmed
  via `git stash` of this ticket's own two changed files that these 2 failures reproduce identically
  with this ticket's changes removed — pre-existing, unrelated to this ticket's diff, out of scope.
- `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/strategic_cognition.yaml'))"` —
  parses cleanly, no YAML block-scalar indentation break introduced.

## Files Changed
- `tests/integration/domains/adventure/test_harvest_to_event.py` — added `run_shadow_shapers` import
  and one insertion line in each of the 2 test functions.
- `docs/parity_ledger/strategic_cognition.yaml` — corrected `STRAT-246`'s `support_boundary` stale
  pipeline-terminus sentence. Two separate stale mentions existed in the same field (Implement fixed
  the first; Parity phase independently found and fixed a second, previously-missed mention of the
  same stale claim later in the same field).
- `docs/simulation_quality/event_type_coverage.md` — corrected the `resource_harvested`/`item_crafted`
  rows' `source` column (lines 109-110) from stale `event_extractor` to `event_shapers (EconomyShaper)`,
  the two rows this ticket's own investigation named as directly affected by the same cutover. Made
  during Verify to resolve the `docs_to_update_coverage` DoD static check, which correctly flagged
  that `investigation.md` named this file as requiring an update and it had not yet been touched. Only
  these 2 rows corrected — the broader multi-domain sweep (COMBAT/FACTION/QUEST/AGENCY rows, plus the
  remaining ECONOMY rows this ticket's own scope didn't cover) stays with the follow-up ticket.

## Completion Summary
Fixed a stale-test gap (not a source-code regression): `test_harvest_to_event.py`'s 2 tests called
only `EventExtractor.extract()`, which since the `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`
migration exercises only a dormant legacy rollback branch for ECONOMY events. Live
`resource_harvested`/`item_crafted` derivation now happens in `EconomyShaper.shape()`, delivered via
`run_shadow_shapers()` on every real kernel tick. Added that same call (mirroring
`Kernel._phase_observability()`'s own sequence exactly) to both tests, with no production source
change. Also corrected two stale prose sentences (Implement + Parity phase, respectively) in
parity-ledger entry `STRAT-246` that still described `event_extractor.py` as the live derivation
terminus. Both tests pass; the broader observability, adventure, tactical, and SimQ scorer test
surfaces remain green; one pre-existing, unrelated failure in
`test_phase5_information_belief_scenarios.py` was confirmed independent of this change via
stash-and-rerun. During Parity, the P0 safeguard scan's flagged intersection with
`docs/parity_ledger/social_narrative.yaml::SOC-208` was independently checked and confirmed to be a
coarse file-level heuristic false positive (no substantive connection to this ticket's ECONOMY-domain
change) — not edited.

**Doc staleness (originally deferred, then partially fixed under DoD condition 6):** Plan initially
deferred `docs/simulation_quality/event_type_coverage.md`'s stale `source` column entirely, reasoning
that fixing only the 2 rows this ticket names would leave the table inconsistent with 7+ other
already-stale rows from the same migration wave. Verify's `docs_to_update_coverage` static check
correctly rejected that as leaving a flagged doc untouched (CLAUDE.md's "never route around a gate"
rule) — resolved by making the minimal, directly-scoped correction: the `resource_harvested`/
`item_crafted` rows (the exact 2 this ticket's own investigation named, lines 109-110) now read
`event_shapers (EconomyShaper)` instead of stale `event_extractor`. The broader multi-domain sweep
(remaining ECONOMY rows this ticket doesn't touch, plus COMBAT/FACTION/QUEST/AGENCY rows) remains
deferred and is tracked by its own dedicated follow-up ticket:
`TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS` (standard tier, P3) — this is the
DoD-condition-11 required follow-up reference for the portion of the gap still genuinely out of this
ticket's scope.
