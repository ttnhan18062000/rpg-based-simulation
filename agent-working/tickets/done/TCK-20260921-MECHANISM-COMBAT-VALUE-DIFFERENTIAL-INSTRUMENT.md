---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT
phase: done
date: 2026-09-21
tags: [simulation-quality, testing, progression]
---

# TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT

## Title
Runtime-evidence program, value-differential axis: one direct question against `combat` — does an
entity's own attributes have measurable purchase on how a real fight resolves? (Re-scoped from an
8-mechanism sweep by explicit peer instruction; see investigation.md for the re-scope note.)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT` (merged into this same PR, #232)
built and proved the value-differential instrument on `progression` and surfaced two findings that
converge on one question: `stats_dirty` erases species-specific base combat stats the moment
anything changes an entity, and biological pressure never differentiated entities by attribute in
the first place. Both ask whether entity identity actually influences the simulation. `combat` is
where that question has the most direct answer available: **do an entity's attributes have any
purchase on how a fight resolves?** If they do, the `stats_dirty` bug is severe because it destroys
something that matters. If they don't, it's severe for a different, worse reason. Per peer
instruction, `combat` is the next target — not `faction`/`social`/`economy` despite their own 0%
runtime share, since the standing priority here is bottom-up: core layers before social ones, and
combat is as core as it gets.

Same instrument as the progression program (§5.1,
`docs/plans/mechanic_verification_scenarios_proposal.md`), same standing constraints: calibration
before verdicts only where the mechanism's own shape differs from what's already calibrated (a pure
formula/same-tick outcome is already calibrated from `progression`; this program does not need to
re-derive that calibration from scratch for the same shape), contradictions recorded and never
fixed, null results earning their label under the horizon rule, the selection caveat stated rather
than implied, and the independent-observation count reported honestly where mechanisms share a
scenario.

**Expect the determinism trap to be live throughout, not the exception**: `combat`'s own
mechanisms are far more likely to touch RNG than `progression`'s formula-shaped ones were. Default
procedure per mechanism: code trace first (confirm the varied input cannot perturb RNG draw order),
then empirical confirmation. Where an input genuinely does move the RNG path, say so and treat the
result as unreadable rather than reporting the difference as the mechanism's own effect — a
difference that cannot be attributed to the mechanism under test is not evidence for it.

## Scope (final, after re-scope — see investigation.md for the original 8-mechanism plan and why
## it was narrowed mid-investigation)
1. Apply §5.1's shape triage to all 8 `combat` mechanisms up front, as a one-time record — done in
   investigation.md before the re-scope, kept for the record, not re-executed as a build plan.
2. Answer one direct question with 1-2 scenarios: within a real, dispatched fight, does an entity's
   own combat attributes have measurable purchase on the outcome? Record the answer only against
   the mechanism entry the scenario(s) genuinely evidence (`combat_resolution`), not stretched
   across entries not actually tested.
3. Cross-reference the answer directly into `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-
   BASE-STATS`'s own open question, in that ticket's own Request Summary — not left as an implicit
   connection for someone else to draw.
4. Report to peer, then stop. No further combat waves in this ticket.

## Out of Scope
- The full 8-mechanism `combat` sweep — explicitly abandoned mid-investigation by peer instruction;
  the shape triage (investigation.md) is kept as a real record of what was found, not built out.
- A `trauma` scenario — drafted under the original broader scope, deleted unrun/uncommitted per
  explicit "leave unbuilt work unbuilt rather than finish it for tidiness" instruction.
- Arbitration (the third failure-to-matter shape) — still needs its own instrument, not built here,
  and explicitly deferred pending a roadmap-session read.
- `faction`/`social`/`economy` — deprioritized by the same bottom-up-ordering instruction that
  picked `combat` over them in the first place.
- Fixing any underlying gap a differential surfaces — this program records evidence, it does not
  fix simulation logic.
- Opening a new PR — folded into the already-open #232 per explicit instruction; stacked commits on
  the same branch, not merged. #232 closes after this ticket, per peer instruction.

## Acceptance Criteria
1. Real, committed positive-control AND negative-control tests answering the one direct question,
   with an explicit determinism-trap trace (code trace first, then empirical confirmation) —
   satisfied by 2 scenario files against `combat_resolution`.
2. `registries/mechanisms.yaml` updated with one dated, additive verified-block note on
   `combat_resolution` only — no overwrite of the prior reachability verdict, registry-field
   bookkeeping done correctly this time (the field itself changed, not just described as changed in
   prose) — verified via `make mechanism-prose-field-drift-check`, clean.
3. The answer cross-referenced directly into `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-
   BASE-STATS`'s own Request Summary.
4. Peer report sent, then this ticket closes — no further waves.

## Related Tickets
- `TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT` — the program this one
  continues, same instrument, same PR.
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — Program A, the sibling
  reachability instrument this program's own instrument is a distinct axis to.
- `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS`,
  `TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES` — the two findings whose
  shared question ("does entity identity influence the simulation") motivates this program's choice
  of `combat` as the next target.

## Related Docs
- `docs/plans/mechanic_verification_scenarios_proposal.md` (§5.1, the instrument this program uses)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT/`

## Related Code Areas
- `src/engine/combat.py::CombatResolutionSystem`
- `src/engine/rpg_depth.py::WoundService`
- `src/engine/tactical.py::TacticalDecisionSystem`
- `src/domains/combat_engagement/service.py::CombatEngagementDecisionService`
- `registries/mechanisms.yaml`
- `tests/mechanic_scenarios/`

## Assumptions / Open Questions
None open at ticket creation — the shape triage is this ticket's own first deliverable, not an
assumption made in advance.

## Implementation Notes
Started with an 8-mechanism shape triage per §5.1 (investigation.md), while a `trauma` scenario was
being drafted alongside `combat_resolution`'s own. Peer re-scoped mid-investigation to one direct
question before the `trauma` test was run or committed — deleted per explicit instruction.

Built 2 scenario files against `combat_resolution` only:
- `test_combat_resolution_damage_value_differential.py`: direct `combat.atk`/`combat.def_stat`
  differential — the mechanism's own most immediate real inputs, avoiding re-testing
  `derived_stats`'s own already-proven attribute-to-atk chain under a different name.
- `test_combat_attributes_real_fight_outcome_value_differential.py`: the narrow question's own
  direct answer, chaining `LevelingService.recalculate_combat_stats()` (called directly, the real
  function, not a shortcut — real apply-path sequencing recalculates derived stats only at the end
  of the tick that changed them, so a same-tick change-then-attack design would use the OLD atk and
  risk a vacuous negative arm) with a real Kernel-dispatched fight.

Both files' determinism-trap analysis: neither `recalculate_combat_stats()` nor
`calculate_damage()` contains an RNG call (re-confirmed by direct code trace, same conclusion this
program already reached for `evolution`/`xp_leveling`). Confirmed empirically too — all 4 test
arms resolve the same real one-hit-no-kill shape.

**Answer, recorded on `combat_resolution`'s own registry entry and cross-referenced into
`TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS`'s Request Summary**: yes — an
entity's own combat attributes have real, formula-exact purchase on how a real fight resolves. The
`stats_dirty` bug is therefore severe for the worse of the two reasons its own ticket named: it
destroys something demonstrably real, not a cosmetic drift.

## Test Summary
- `tests/mechanic_scenarios/test_combat_resolution_damage_value_differential.py` — 2 tests, both
  passing on first real run.
- `tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py` — 2
  tests, both passing on first real run.
- Regression scope: `tests/mechanic_scenarios/`, `tests/unit/progression/`, `tests/unit/tools/
  test_mechanism_registry.py` — 230 passed, 0 failed.
- `make mechanism-registry-validate` + `make mechanism-prose-field-drift-check` — clean.
- All 5 blocking mechanism-registry Makefile targets + the 2 non-blocking view regenerations —
  clean (`mechanism_registry.html` unaffected by this change; `mechanism_verification_view.md`
  regenerated after the `instrument` field change).

## Files Changed
- `tests/mechanic_scenarios/test_combat_resolution_damage_value_differential.py` (new)
- `tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py` (new)
- `registries/mechanisms.yaml` (one additive verified-block note on `combat_resolution`;
  `instrument` upgraded `corpus_run` -> `scenario`)
- `docs/brainstorm/mechanism_verification_view.md` (regenerated)
- `tickets/todos/TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS.md` (cross-referenced
  with this ticket's own direct answer)
- `docs/REGISTRY.yaml` (auto-regenerated, Finalize's unconditional post-migration self-check)

## Completion Summary
Re-scoped mid-flight from an 8-mechanism `combat` sweep to one direct question, per explicit peer
instruction, once the cost/value tradeoff (RNG live throughout combat vs. few real non-arbitration
candidates) became clear. Answered the question that actually mattered to the roadmap session — do
entity attributes have real purchase on combat outcomes — with 2 focused, real scenarios against
`combat_resolution`, both passing on the first real run. Cross-referenced the answer directly into
the `stats_dirty` P0 finding it exists to qualify. No further combat waves; the full sweep and the
arbitration instrument both wait for the roadmap session's own read, per peer instruction. PR #232
closes with this ticket.

**Addendum 2026-09-21, post-report peer review**: a third named trap added to §5.1 (`docs/plans/
mechanic_verification_scenarios_proposal.md`) — **derivation timing**, distinct from determinism/
seed-sensitivity and purpose-built worlds: when a differential's varied input feeds a DERIVED value
rather than being read directly, the derivation has to have actually run relative to the
observation point, or both arms measure stale pre-change state and look identical for a reason
unrelated to whether the input matters. This is exactly the hazard this ticket's own end-to-end
test avoided by calling `LevelingService.recalculate_combat_stats()` directly (the real apply-path
sequencing recalculates derived stats only at tick-end, so a same-tick change-then-attack design
would have fought with the OLD `atk`). Also noted explicitly: calling the real derivation function,
rather than hand-computing the expected value, keeps the scenario's expected value anchored to what
the code actually does rather than to the scenario author's own reading of the formula.
