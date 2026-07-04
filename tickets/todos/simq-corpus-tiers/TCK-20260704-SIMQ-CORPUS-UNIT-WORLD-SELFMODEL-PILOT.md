---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation_quality, self-model, branch-b, unit-tier, calibration, cognition]
---

# TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT

## Title
Pilot Branch B (self-model) activation in a real unit-tier world with live multi-tick evidence

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §3 ("Branch B
(self-model) activation in a REAL shipped world") found that `ENABLE_SELF_MODEL_COGNITION` is
currently OFF everywhere, and its only live-fire evidence is a single hand-built,
single-entity, few-tick unit test
(`tests/integration/domains/test_fused_loop.py::test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`).
No calibration run has ever exercised Branch B across a full population (11-56 entities) over
200-1000 ticks. The investigation also documents a real, previously-live interaction bug
(Finding 4 in the Branch B ticket's own investigation): `InformationBeliefPhase` and
`SelfModelUpdatePhase` clobbered each other when `ENABLE_SELF_MODEL_COGNITION` and
`ENABLE_BELIEF_ASSIMILATION` ran simultaneously — a bug found only because no calibration profile
had ever run both together before that investigation.

Per the user's Branch B decision, this ticket pilots self-model activation via one dedicated
unit-tier world, which doubles as the real-load evidence-gathering step the investigation found
missing (this is the informal pre-approval step — no separate architecture-ruling ticket is
created, per the user's explicit decision).

## Scope
1. Author 1 new unit-tier world seeding `pending_self_model_information_events` (mirroring
   `urban_political`'s `pop_1`/`unknown`/`material.moon_resin.source` entry in shape) and turning
   `ENABLE_SELF_MODEL_COGNITION: "ON"` via that world's `config/simulation_quality/profiles/
   <world>.yaml` `feature_flags:` block.
2. **(a) Run a real multi-entity, multi-tick calibration** — not just a unit test. Scale
   the world to a realistic multi-entity population (comparable to the smaller existing worlds,
   e.g. `wilderness_survival`'s 11 entities, at minimum — do not use a single-entity world, since
   the investigation's own point is that no multi-entity evidence exists yet) and run at least
   200-300 ticks at 3 seeds, following the population-stability verification pattern
   (>=60% alive floor) `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` established.
3. **(b) Explicitly check for the `ENABLE_BELIEF_ASSIMILATION` interaction risk.** Per
   investigation.md §3 Finding 4's risk and consistent with the unit-tier philosophy of isolating
   exactly one mechanic, **keep this pilot world's `ENABLE_BELIEF_ASSIMILATION` OFF** (baseline) —
   do not seed `information_source_profiles`/`pending_information_responses` in this world. This
   keeps the pilot a genuinely isolated single-mechanic test. If a future ticket wants to test the
   Branch-B + belief-assimilation interaction deliberately, that is separate, explicitly-labeled
   follow-on work, not folded into this pilot.
4. **(c) Document the resulting grade/behavior honestly.** Whatever the calibration run reveals —
   a clean B/A grade, a stubborn C, or a newly-discovered bug — record it as-is in
   `docs/simulation_quality/eval_matrix_results.md`. A bug discovery is a valid, expected, and
   successful outcome of this ticket, not a failure to fix before closing. If a bug is found, file
   a separate follow-up ticket for the fix (do not silently patch engine code inside this
   world-authoring ticket without updating scope first) and reference it in this ticket's
   Completion Summary.
5. Note in `docs/parity_ledger/` (relevant subsystem file, likely `strategic_cognition.yaml`) that
   `self_model` participates in the canonical hash (per investigation.md §3 point 4, confirmed
   `SUB-374`) — turning this flag on for this world changes its committed hash baseline; this is a
   determinism/baseline-churn consideration to flag, not a correctness risk.
6. Add grade-anchor entries to `grade_anchors.json`/`FAST_ANCHOR_KEYS` for this world (3-seed
   matrix), whatever the resulting grades are.
7. Run `make evaluate --dry-run` (0 regressions on the pre-existing corpus) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Turning `ENABLE_SELF_MODEL_COGNITION` on for any existing archetype world (`urban_political`,
  etc.) — this ticket authors a new dedicated world only
- Seeding `ENABLE_BELIEF_ASSIMILATION` alongside self-model in this world (explicitly kept at
  baseline/OFF per Scope item 3 — that combination is a distinct, not-yet-scoped follow-on)
- Fixing any interaction bug this pilot might surface — file a follow-up ticket instead (this
  ticket's job is to gather the evidence honestly, not necessarily to resolve everything it finds)
- Combining self-model activation with AGENCY/`ENABLE_ADVENTURE_ROUTING` in the same world (a third
  never-live-tested combination per investigation.md §3 point 3 — explicitly out of scope, would
  defeat the single-mechanic isolation goal)

## Acceptance Criteria
- [ ] New unit-tier world exists with `pending_self_model_information_events` seeded and
      `ENABLE_SELF_MODEL_COGNITION: "ON"` in its profile YAML
- [ ] World has a realistic multi-entity population (>=11 entities, not a single-entity test world)
- [ ] `ENABLE_BELIEF_ASSIMILATION` confirmed OFF (baseline) in this world's profile YAML, and no
      `information_source_profiles`/`pending_information_responses` content seeded in it
- [ ] A real 200-300+ tick, 3-seed calibration run completed and its actual COGNITION/INFORMATION
      pillar grades (whatever they are) recorded in `eval_matrix_results.md`
- [ ] Population stability verified (>=60% alive floor) through the full run length
- [ ] If a bug or unexpected interaction is discovered, it is documented honestly in this ticket's
      Completion Summary with a reference to a filed follow-up ticket (not silently absorbed or
      silently ignored)
- [ ] `self_model` canonical-hash participation and baseline-churn note added to the relevant parity
      ledger file
- [ ] Grade-anchor entries added for this world (3-seed matrix)
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions on the pre-existing corpus

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines the unit-tier criteria this world must meet
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO — sibling unit-tier tickets; same isolation
  philosophy
- TCK-20260703-SIMQ-UPLIFT3-BRANCH-B (if present in `tickets/done/`) — the Branch B correctness fix
  and its Finding 4 interaction-bug discovery this ticket's real-load pilot follows up on

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §3 ("Branch B
  (self-model) activation in a REAL shipped world" — full risk characterization) and §4 open
  question 3
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/parity_ledger/strategic_cognition.yaml`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-BRANCH-B/` — the underlying Branch B fix's own
  investigation (Finding 4, the interaction bug this pilot must not re-trigger), and its "Honesty
  Note" on what "proven but not shipped" means

## Related Code Areas
- `src/worldbuilding/schema.py:228` (`pending_self_model_information_events`), `:54`/`:182`
  (composition-level mirrors)
- `src/domains/optimization/feature_flags.py:18` (`ENABLE_SELF_MODEL_COGNITION`, and
  `ENABLE_BELIEF_ASSIMILATION` for the interaction check)
- `src/engine/` — `SelfModelUpdatePhase`, `InformationBeliefPhase` (interaction-risk phases; not
  modified by this ticket, only observed)
- `tests/integration/domains/test_fused_loop.py` — the existing single-entity proof this ticket
  extends with real multi-entity evidence
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- UQ-1: What population size counts as sufficiently "real multi-entity" evidence — the investigation
  cites 11-56 entities as the existing worlds' range. Default to at least matching
  `wilderness_survival`'s 11-entity floor; a larger population (comparable to `sandbox_world`'s 18)
  would give stronger evidence if implementation effort allows, at the implementer's judgment.
- UQ-2: If the pilot reveals a genuine bug (per Scope item 4c), should this ticket be blocked from
  reaching `tickets/done/` until the bug is fixed, or can it close with the finding documented and a
  follow-up ticket filed? Per the Request Summary framing ("this is a valid and expected outcome,
  not a ticket failure"), this ticket can close with an honest finding + filed follow-up — it does
  not need to itself fix any bug it uncovers.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
