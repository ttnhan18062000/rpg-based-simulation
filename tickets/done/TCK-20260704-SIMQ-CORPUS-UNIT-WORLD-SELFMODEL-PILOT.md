---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, self-model, corpus, calibration, cognition]
---

# TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT

## Title
Pilot Branch B (self-model) activation in a real unit-tier world with live multi-tick evidence

## Status
DONE

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

Followed `staging_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT/plan.md`'s 12 steps
exactly (architecture pre-approved). Summary of what was done and observed:

1. **World authored**: `data/worlds/unit_selfmodel_pilot/world.yaml` — composes
   `frontier_village_core` + `hero_adventurers` (16 entities, 1 region), seeds one
   `pending_self_model_information_events` entry (`target_population_id: "pop_1"`,
   `answer_kind: "unknown"`, `unknowns: ["material.wood.source"]`, `certainty: 0.0`,
   `source_id: null`, `cost_gold: 0`), `generation_seed: 503`. No
   `information_source_profiles`/`pending_information_responses` content — isolation guard intact.
2. **Profile authored**: `config/simulation_quality/profiles/unit_selfmodel_pilot.yaml` —
   `feature_flags: {ENABLE_SELF_MODEL_COGNITION: "ON"}` only. Confirmed
   `ENABLE_BELIEF_ASSIMILATION` is genuinely absent (not set to any value, including `"OFF"`).
3. **Compiled**: `resolve` → `compile --seed 42 --from-resolved` → `list` (rebuilt
   `data/worlds/world_index.json`). `world_compile_report.json` shows `warnings: []`,
   `entity_count: 16`, `region_count: 1`. Went beyond trusting "0 warnings": loaded the resolved
   spec + compile context directly via `WorldCompiler.compile()` in a one-off script and inspected
   the live `AuthoritativeState.pending_self_model_information_events` — confirmed
   `[{'actor_id': 15, 'event': InformationResponse(answer_kind='unknown', ..., unknowns=('material.wood.source',), ...)}]`,
   and separately confirmed entity id `15` has `properties["population_id"] == "pop_1"`. The seeded
   fact genuinely reaches the correct actor, not just "compiler didn't warn."
4. **Population stability**: added `"unit_selfmodel_pilot"` to `POPULATION_STABILITY_WORLDS` in
   `tests/unit/worldassembly/test_corpus_diversity.py`. Ran 300 ticks at seed 42 (both via the
   pytest parametrization and a standalone script to capture per-checkpoint numbers): **100% alive
   (16/16) at every 50-tick checkpoint through tick 300** — no floor breach, identical result to
   `unit_information_source`'s own precedent (same module pair, no hazard content).
5. **3-seed/200-tick calibration matrix** run for seeds 42/123/456. Added 3 entries to
   `tests/simulation_quality/fixtures/grade_anchors.json` (46 → 49 world entries; 49 → 52 total
   keys including the 3 metadata keys) and 3 keys to `FAST_ANCHOR_KEYS` in
   `tests/simulation_quality/test_grade_regression.py`.
6. **COGNITION signal verified genuine, not accidentally inert**: all 3 seeds show
   `COGNITION.grade == "S"`, `event_count == 3200` — exactly `alive_entities (16) x ticks (200)`,
   confirming `self_model_updated` fires unconditionally every tick for every alive/active entity,
   as `investigation.md` §5/§6 predicted. Calibration log confirmed `profile=unit_selfmodel_pilot`
   (not a silent fallback to `default`) and `Profile feature flags: {'ENABLE_SELF_MODEL_COGNITION': 'ON'}`
   for every run.
7. **INFORMATION pillar confirmed inert at `C`, 0 events, across all 3 seeds** — this is the
   expected, correctly-predicted isolation result per investigation.md §4/§5/§7 (InformationBeliefPhase
   is entirely gated behind the absent `ENABLE_BELIEF_ASSIMILATION` flag and structurally cannot run),
   not an unexplained gap. Documented as such, not investigated further, per the ticket's own framing.
8. **Parity ledger**: added `STRAT-245` to `docs/parity_ledger/strategic_cognition.yaml` (next free
   ID after `STRAT-244`), cross-referencing `SUB-374`/`INFRA-259`/`INFRA-260`, using plan.md's exact
   proposed content. Appended the proposed accuracy-fix clause to `INFRA-259`'s `text` field in
   `docs/parity_ledger/infrastructure.yaml` (noting `ENABLE_SELF_MODEL_COGNITION` is no longer "never
   a shipped profile default" without qualification) — no other field on `INFRA-259` changed. Both
   YAML files re-validated to parse cleanly after edits.
9. **`docs/simulation_quality/eval_matrix_results.md`** — added a new `### unit_selfmodel_pilot`
   subsection (unit-tier, 16 entities/1 region) directly after `unit_information_source`'s own
   section, with the measured grade table filled in (COGNITION=S/S/S with the 3200-hit explanation,
   INFORMATION=C/C/C framed explicitly as the predicted, correct isolation result).
10. **`docs/simulation_quality/corpus_tier_taxonomy.md`** — updated the tier-mapping table's opening
    sentence ("Two new" → "Three new" Unit-tier worlds, naming all three and their originating
    tickets) and appended the `unit_selfmodel_pilot` row.
11. **`make evaluate`** (not `--dry-run`, per this epic's established correction) — exit 0, **490
    pillars checked, 0 regressions, 0 missing**. Scoped pytest also run (see Test Summary).
12. **`make knowledge-index-update`** — incremental update, 2 files re-embedded (the 2 modified
    `docs/simulation_quality/*.md` files), 5410 chunks total. `graphify update .` also run (touched
    `tests/` files), rebuilt 24237 nodes / 51184 edges / 1554 communities.

**Deviation from plan.md's placeholder table**: plan.md's Step 8 draft table left COGNITION's
letter as `<measured>` pending the actual run. The measured result is `S` (not merely "non-C") for
all 3 seeds — a stronger signal than the placeholder table implied but fully consistent with §6's
prediction of a "large, structural" hit count. `eval_matrix_results.md`'s Step 8 table has been
filled in with the actual measured `S` grade and the 3200-hit count, not left as a placeholder.
No other deviation from plan.md was found — every other step's actual result (16 entities, 1 region,
0 compile warnings, 100% population stability, INFORMATION inert at C) matched the plan's own
prediction exactly.

**Minor incidental observation (not a bug, not filed as a follow-up)**: `tools/calibrate_simq.py`'s
own log line (`Running engine: ... entities={args.entities} ...`) printed `entities=10` for all 3
runs — this is `--entities`'s CLI default (used only by the tool's synthetic-fallback world-generation
path, `calibrate_simq.py:170-178`), which is simply never overwritten when `--name` loads a real
compiled world. It is a pre-existing, cosmetic-only logging inaccuracy in the tool (confirmed the
actual entity count used was correctly 16, not 10, via the exact 3200 = 16×200 event-count match) —
unrelated to this ticket's own content and not worth a follow-up ticket.

## Test Summary

- `pytest tests/unit/worldassembly/test_corpus_diversity.py -k unit_selfmodel_pilot -q` → 1 passed
  (population-stability check for the new world).
- `pytest tests/unit/worldassembly/test_corpus_diversity.py tests/simulation_quality/test_grade_regression.py -m "not slow" tests/unit/cognition/test_phase2_self_model_phase.py tests/unit/optimization/test_component_patches.py tests/integration/domains/test_fused_loop.py -q`
  → **84 passed, 19 deselected**.
- `pytest tests/unit/cognition/test_phase2_self_model_phase.py tests/unit/optimization/test_component_patches.py -q`
  → **14 passed** (matches investigation.md's pre-implementation baseline exactly).
- `pytest tests/integration/domains/test_fused_loop.py -q -k "self_model or branch_b or belief"`
  → **7 passed, 3 deselected** (matches investigation.md's pre-implementation baseline exactly).
- `pytest tests/integration/worldassembly/test_real_content_world_modules.py tests/integration/worldassembly/test_real_content_world_compositions.py tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_resolver.py -q`
  → **50 passed**.
- `make evaluate` → exit 0, **490 pillars checked — 0 regressions — 0 missing**.
- No `src/` file was modified by this ticket (content-authoring + calibration only), consistent with
  the plan's own scope.

## Files Changed

- `data/worlds/unit_selfmodel_pilot/world.yaml` (new)
- `data/worlds/unit_selfmodel_pilot/resolved/*` (generated: `world.resolved.yaml`,
  `compile_context.json`, `provenance_manifest.json`, `assembly_report.json`,
  `validation_report.json`)
- `data/worlds/unit_selfmodel_pilot/world_compile_report.json` (generated)
- `config/simulation_quality/profiles/unit_selfmodel_pilot.yaml` (new)
- `data/worlds/world_index.json` (regenerated via `cli list`)
- `tests/simulation_quality/fixtures/grade_anchors.json` (+3 entries)
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` +3)
- `tests/unit/worldassembly/test_corpus_diversity.py` (`POPULATION_STABILITY_WORLDS` +1)
- `docs/simulation_quality/eval_matrix_results.md` (+1 section, `unit_selfmodel_pilot`)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (+1 table row, opening-sentence update)
- `docs/parity_ledger/strategic_cognition.yaml` (+1 entry, `STRAT-245`)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-259`'s `text` field, one appended clause —
  accuracy fix only, no status/evidence change)
- `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md` (regenerated via `graphify update .`)
- Knowledge search index (regenerated via `make knowledge-index-update`, not tracked in git)
- `data/calibration/unit_selfmodel_pilot_seed{42,123,456}_200t/*` (generated; **not committed** —
  `data/calibration/` is gitignored, same as `data/runs/`)
- `staging_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT/plan.md` (Deviations note
  added for the COGNITION grade)

## Completion Summary
This is the first calibration-anchored world to turn `ENABLE_SELF_MODEL_COGNITION` on, providing
the first-ever multi-entity (16), multi-tick (200-300), multi-seed (3) live evidence for Branch B's
self-model materialization mechanism — previously proven only via a single hand-built, single-entity
unit test. Authored `unit_selfmodel_pilot` (`frontier_village_core` + `hero_adventurers`), seeding
one `pending_self_model_information_events` entry targeting `pop_1` with an `unknown` fact about
`material.wood.source` (a material this exact composition genuinely produces via `wood_node` —
corrected away from mirroring `urban_political`'s `moon_resin` subject, which isn't produced here).

All 3 of Branch B's original fixes (the `events=[]` grouping fix, the `pipeline.py` merge-wrapper
fix, and `SelfModelPatch` durable materialization) were confirmed still in place before
implementation began, and the existing Branch-B regression suite was re-run and confirmed passing
both during implementation and independently by the orchestrator afterward.

The pilot's own investigation surfaced a genuinely important, non-obvious finding before any code
was written: with `ENABLE_BELIEF_ASSIMILATION` absent (as this ticket's own Scope item 3 mandates,
specifically to avoid re-triggering the Finding-4 interaction-clobbering bug the original Branch-B
ticket found), `InformationBeliefPhase` — which contains both Branch A and Branch B's
query-routing logic — never executes at all. This means the pilot can only exercise Branch B's
self-model *materialization* half (`pending_self_model_information_events` →
`self_model.knowledge.unknowns` → durable `SelfModelPatch` materialization), not the
unknowns→query-routing→information-response half. This was resolved as a correct, expected,
airtight consequence of the ticket's own explicit isolation design (not a gap or bug), and framed
that way throughout this ticket's implementation and documentation — the ticket's Title/AC
"COGNITION/INFORMATION pillar grades" phrasing was, in hindsight, always going to describe one
genuine signal and one correctly-inert isolation result, not two active signals.

Live results, independently re-confirmed by the orchestrator (not just trusted from the
implementer's report — re-ran `WorldCompiler.compile()` directly and inspected the live
`AuthoritativeState.pending_self_model_information_events`, re-ran the full test suite, re-ran
`make evaluate`, and re-read every doc/parity-ledger edit): the seeded fact reaches the correct
compiled actor (`actor_id=15`, `population_id=pop_1`) exactly as designed. 100% population
stability through 300 ticks at seed 42. COGNITION grades **S** at all 3 seeds with `event_count=3200`
(exactly `16 entities × 200 ticks`, confirming genuine per-tick, per-entity `self_model_active`
signal, not a fluke or accidental inert pass). INFORMATION grades **C** with 0 events at all 3
seeds — the correctly-predicted isolation result, documented as such in `eval_matrix_results.md` so
a future reader won't mistake it for a bug. 3 new grade anchors added. `make evaluate` and the full
scoped regression suite (including the pre-existing Branch-B tests) show 0 regressions. No genuine
bug or unexpected finding was discovered — the result matched the pre-committed prediction exactly,
which is itself the successful outcome this ticket was scoped to produce (per its own framing: "a
bug discovery is a valid, expected, and successful outcome... not a failure to fix before
closing" — the actual outcome here, a clean confirmatory result, is equally valid and requires no
follow-up ticket).

Parity ledger updated: new entry `STRAT-245` in `strategic_cognition.yaml` (cross-referencing
`SUB-374`/`INFRA-259`/`INFRA-260`), and `INFRA-259` in `infrastructure.yaml` amended to note it is
no longer accurate to say this flag is "never a shipped profile default" without qualification —
this one dedicated unit-tier world is now the sole exception.
