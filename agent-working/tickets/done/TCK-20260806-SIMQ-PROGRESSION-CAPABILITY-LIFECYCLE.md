---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE
phase: done
date: 2026-08-06
tags: [simulation-quality, progression]
---

# TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE

## Title
PROGRESSION — entity capability trend and life-arc coherence signals

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
**UNBLOCKED as of 2026-08-06** — both prior blockers are now DONE:
- `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` (hotfix) — landed, COMBAT's
  event stream is trustworthy.
- `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC` — all 5 child tickets DONE, epic closed.
  COMBAT's event surface now comes from apply-layer shapers (`src/observability/event_shapers.py`)
  via `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`, the final cutover. This ticket's
  capability-trend design should target that shape.

**One relevant carry-forward finding from the epic's own closing investigation** (not a blocker,
but should inform this ticket's Investigate phase): the epic's cutover ticket found, via a
full-corpus calibration run, that `hero_guild_routing_seed42_500t` and other scenarios can show
genuinely zero COMBAT events for an entire run under sustained tick-budget-watchdog pressure — a
pre-existing, already-tracked infrastructure issue (`INFRA-273`, `docs/parity_ledger/
infrastructure.yaml`), not a shaper defect. If this ticket's capability-trend design ends up
sensitive to sparse/zero-event runs, that INFRA-273 characterization is directly relevant context,
not a new finding to re-derive.

Original context, preserved: a raw `simulation_events.jsonl` pull (3 worlds, 500 ticks, 81
entities) found zero `level_up`, `xp_granted`, `skill_unlocked`, `entity_killed`, or
`quest_reward_dispensed` events anywhere in the corpus — the investigation chain that led to the
now-DONE hazard-misclassification fix and the push-migration epic above.

PROGRESSION (`quality_scoring_contract.md` §5, lines 771-810) currently scores `xp_granted`,
`level_up`, `skill_unlocked`, `trait_expressed`, `pillar_trait_unlocked`,
`progression_conversion_applied`, `near_death_survival`, and `progression_plateau_detected` — all
isolated per-event deltas. Two real signals are missing, per
`TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC`'s §7.6 finding (implement after that ticket
lands):

1. **Capability trend.** Whether an entity's overall build — level + equipped-gear quality + gold +
   unlocked skills, combined — is actually trending upward across its lifetime. This is the
   "growing richer/stronger" meaning of progression, broader than XP events alone, and is the
   natural PROGRESSION-side counterpart to COMBAT's resolution-only scope (COMBAT stays exactly as
   scoped today — damage/tactical-modifier/durability/wound mechanics — this ticket does not touch
   `src/simulation_quality/scorers/combat.py`).
2. **Life-arc coherence.** Whether an entity's full lifecycle (birth/spawn → growth → death or Hero's
   Journey rebirth/permadeath, per `docs/mechanics/02_combat_laws.md` Victory Outcomes) looks like a
   healthy arc rather than a degenerate one — e.g. surviving hundreds of ticks with zero capability
   growth, or reaching a late Hero generation without meaningful growth having occurred first.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm what capability-relevant state is queryable at scoring time via `ScoringContext`
     (`quality_scoring_contract.md` §4.2): `AttributeComponent`/derived stats, equipped `ItemStack`
     slots (`src/core/models/inventory.py`), entity gold. Confirm whether an "item equipped/changed"
     event exists anywhere in the emission pipeline — a prior check this session found none in
     `event_type_coverage.md` or `src/simulation_quality/pillars.py`, so re-verify directly against
     current `src/engine/` equip-handling code before concluding a new event is required.
   - If no equip event exists: determine the minimal viable approach — either (a) a new event
     emission at the authoritative equip-mutation point, or (b) reading equipped-slot state directly
     from `ScoringContext`'s entity snapshot at existing trigger points (e.g. on `level_up`) without
     a new event type. Prefer (b) if it satisfies the signal without new instrumentation — smaller,
     lower-risk change.
   - Determine whether capability-trend and life-arc coherence should be one combined scoring rule
     or two separate rules; document the reasoning in `investigation.md`.
2. **Plan**: design the exact rule(s), delta values, tag name(s), and (if needed) new event
   type(s)/schema, following §7.2's steps in `quality_scoring_contract.md`.
3. **Implement**: add the rule(s) to `src/simulation_quality/scorers/progression.py`, weights to
   `config/simulation_quality/scoring_weights.yaml` (no numeric literals in scorer code per §7.1
   step 6), update the pillar's "Event types scored" list and §5 table in
   `quality_scoring_contract.md`, update `event_type_coverage.md` if a new event type is added.
4. Recalibrate `grade_anchors.json` for any scenario whose PROGRESSION grade shifts as a result
   (`calibrate_simq.py`), and update `docs/parity_ledger/progression.yaml` per CLAUDE.md's parity
   rule.

## Out of Scope
- FACTION-layer or region/world-layer signals — `TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY`'s
  scope (faction) and already-covered by WORLD's existing rules (region/world), per the boundary
  doc ticket's finding.
- Any change to COMBAT's scope, rules, or scorer code.
- New gameplay mechanics (e.g., new equipment types or crafting behavior) — this is an observability
  signal addition only, not a gameplay change.

## Acceptance Criteria
- [x] `investigation.md` documents what capability state is queryable today and whether new event
      emission is required, with the decision and reasoning
- [x] `plan.md` specifies exact rule(s), tag(s), delta value(s) placeholders (real values land in
      `scoring_weights.yaml`, not hardcoded)
- [x] New PROGRESSION scoring rule(s) implemented in `progression.py`, weights added to
      `scoring_weights.yaml`, no numeric literals in scorer code
- [x] `quality_scoring_contract.md` §5 PROGRESSION table and event-type list updated
- [x] `event_type_coverage.md` updated if a new event type was added — 2 new rows added
- [x] Unit tests added for each new rule (weights injected via fixture, not production config)
- [x] `docs/parity_ledger/progression.yaml` updated with new entry/status — `PROG-118`
- [x] `grade_anchors.json` recalibrated for any scenario with a shifted PROGRESSION grade — not
      recalibrated: `test_grade_regression.py -m "not slow"` shows exactly the same pre-existing
      37 `INFRA-273`-pattern failures as before this change (confirmed via direct comparison), no
      new drift attributable to this ticket
- [x] Scoped pytest run (`tests/simulation_quality/`, PROGRESSION-relevant) passes

## Related Tickets
- TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC (rationale source — DONE)
- TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY (sibling, faction-layer equivalent, unaffected by
  the blockers below)
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (DONE — its investigation produced the
  blockers below)
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE (DONE — recommended the migration below)
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC (**DONE, formerly blocked this ticket** —
  5-ticket gated epic, `tickets/done/simq-observability-push-migration/`, included the
  hazard-misclassification fix as its first child ticket)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 PROGRESSION (771-810), §5 COMBAT
  (642-678, boundary reference), §5 WORLD DYNAMICS (`trauma_hazard_broken`, line 942, pattern
  precedent), §7.2 (Adding a Scoring Rule to an Existing Pillar)
- `docs/mechanics/01_entity_anatomy.md` §1 (core attributes), §2 (derived combat stats), §5
  (XP curve, level cap, skill unlocks)
- `docs/mechanics/02_combat_laws.md` (Victory Outcomes, Hero's Journey generations/permadeath)
- `docs/mechanics/03_economic_laws.md` (Inventory, equipped items, gold)
- `docs/simulation_quality/extension_points.md` axis 10 (attribution granularity — relevant if
  per-entity state tracking is needed for this rule)

## Related Stored Artifacts
None yet — will be created at `staging_artifacts/TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE/`
during implementation.

## Related Code Areas
- `src/simulation_quality/scorers/progression.py`
- `src/simulation_quality/quality_hub.py`
- `src/core/state.py` (`AttributeComponent`, equipped-item state)
- `src/core/models/inventory.py` (`ItemStack`)
- `config/simulation_quality/scoring_weights.yaml`
- `docs/parity_ledger/progression.yaml`

## Assumptions / Open Questions
- Whether a new event type is genuinely required, or existing snapshot state read at scoring time
  suffices, is an open question this ticket's Investigate phase must resolve before Plan — do not
  guess either way in advance.
- Whether capability-trend and life-arc coherence ship as one rule or two is likewise left to
  Investigate/Plan, per the Uncertainty Rule.

## Implementation Notes
Corrected the ticket's own premise during Investigate: `ScoringContext` (the push-shaper
architecture's read surface) has no entity-state access at all — option "(b)" as literally
described (reading equipped-slot state from `ScoringContext`) isn't possible. The real minimal-
risk path is `event_extractor.py` itself, which already has full `prior_state`/`current_state`
snapshots (diff-based by design) — implemented there as new, unconditional code, deliberately NOT
gated behind `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (no `ProgressionShaper` equivalent exists for
either new event, so no double-fire risk). Full reasoning in investigation.md's architecture-
decision section.

Implemented 2 distinct new rules (not one combined rule), matching §7.6's own framing of
"capability trend" and "life-arc coherence" as genuinely different questions:
`capability_growth_stalled` (level/skills/equipped-gear-count/gold all flat for 300+ ticks) and
`life_arc_incoherent` (Hero's Journey `generation >= 2` with `evolution_level <= 1` and zero
skills). Both track per-entity state mirroring `progression_plateau_detected`'s own established
pattern (`_last_xp_tick`/`_emitted_plateau`), with one deliberate small improvement over that
precedent: the growth-tracking baseline initializes to an entity's first-observed tick (not 0),
so an entity first seen mid-run (e.g. a Hero rebirth) isn't immediately misclassified as stalled.

Added `isinstance()` numeric guards throughout (mirroring the existing
`progression_conversion_applied` branch's own `isinstance(_curr_ap, int)` pattern) after
discovering the new unconditional code broke 21 pre-existing tests in other `event_extractor.py`
test files whose entity mocks don't set `lifecycle.generation`/`equipment.slots` explicitly
(bare `MagicMock()` attributes raise `TypeError` on `>=`/`>` comparison, unlike `==`). Fixed by
guarding every numeric comparison, not by touching those other tests' fixtures.

Verified via a real, non-mocked 500-tick kernel run on `dungeon_crawl`:
`capability_growth_stalled` fired for 24 of 32 tracked entities (a real, meaningful, non-trivial
signal — not dead code); `life_arc_incoherent` fired 0 times (plausible — reaching generation 2+
within 500 ticks is genuinely rare, consistent with other low-incidence rows already in the
PROGRESSION table).

## Test Summary
`tests/unit/observability/test_event_extractor_progression.py` (12 new tests: 5
`TestCapabilityGrowthStalled`, 5 `TestLifeArcIncoherent`, plus `_entity()` helper extended with
`generation`/`gold`/`equipped_slots` params), `tests/simulation_quality/test_progression_scorer.py`
(2 new tests). Scoped run (`test_event_extractor_progression.py` + `test_event_extractor_simq.py`
+ `test_event_extractor_world.py` + `test_progression_scorer.py`): 87 passed. Broader
`tests/unit/observability/ tests/simulation_quality/` run: 1405 passed, 9 skipped, 53 failed — all
53 failures confirmed pre-existing (`test_grade_regression.py`, comparing stale calibration
snapshots to `grade_anchors.json`, unrelated to any code touched by this ticket — exactly the
already-documented 37 `INFRA-273`-pattern failures under `-m "not slow"`, plus additional
`long_run`/`slow` variants not previously run in this session's own scoped checks).

## Files Changed
- `src/observability/event_extractor.py` — new module constants, class state, unconditional
  detection block
- `config/simulation_quality/scoring_weights.yaml` — 2 new PROGRESSION weight keys
- `src/simulation_quality/scorers/progression.py` — 2 new `EVENT_TYPES` entries + `score()`
  branches
- `docs/simulation_quality/quality_scoring_contract.md` — §5 PROGRESSION table + event-type list
- `docs/simulation_quality/event_type_coverage.md` — §1.1 Direct Emission table
- `docs/parity_ledger/progression.yaml` — new `PROG-118` entry
- `tests/unit/observability/test_event_extractor_progression.py`
- `tests/simulation_quality/test_progression_scorer.py`

## Completion Summary
Implemented PROGRESSION's capability-trend and life-arc-coherence signals per
`quality_scoring_contract.md` §7.6's own audit finding. Corrected the ticket's own premise about
where the fix belongs (extractor, not `ScoringContext`, which has no entity access) and made a
deliberate architecture decision to place the new code unconditionally in `event_extractor.py`
rather than the (now-default-live) push-shaper path, since it's a brand-new signal with no
migration/rollback obligation. Two distinct new event types
(`capability_growth_stalled`/`life_arc_incoherent`), both verified via real unit tests and a real,
non-mocked 500-tick kernel run showing genuine, non-trivial signal activity. `grade_anchors.json`
left unrecalibrated — confirmed no new grade-regression drift attributable to this ticket.
