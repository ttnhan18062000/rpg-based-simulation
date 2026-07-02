# Plan — TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE

## Decision

Replace `data/worlds/sandbox_world/world.yaml` with a minimal `worldcomposition.v1` file using
the `modules:` shorthand (per `WorldCompositionSpec`, `src/worldassembly/schema.py:21-39`),
composed of `frontier_village_core` (settlement) + `wolf_den_near_forest` (ecology, already
`requires: frontier_village_core`). Modeled directly on the existing minimal reference
`data/worlds/highland_traverse/world.yaml`.

Target content:
```yaml
schema_version: "worldcomposition.v1"
world_id: "sandbox_world"
name: "Dev Sandbox"
description: "Starter sandbox world for development and SimQ calibration — frontier settlement with an adjacent wolf-den wilderness."
modules:
  - "frontier_village_core"
  - "wolf_den_near_forest"
generation_seed: 42
```

## Ordered Steps

1. **Back up nothing — replace directly.** Write the new `data/worlds/sandbox_world/world.yaml`
   content above, replacing the `worldtemplate.v1` source entirely (git history preserves the
   old version).
   - Files: `data/worlds/sandbox_world/world.yaml`
2. **Resolve.** Run the composition through `WorldAssemblyResolver` to produce
   `data/worlds/sandbox_world/resolved/world.resolved.yaml` and sidecars
   (`provenance_manifest.json`, `assembly_report.json`, `validation_report.json`,
   `compile_report.json`). Use the same CLI/tooling path other `worldcomposition.v1` worlds
   use (check `src/worldbuilding/cli.py`'s composition-resolve command, or
   `WorldAssemblyResolver.resolve()` directly if no CLI wrapper is simpler).
   - Files: `data/worlds/sandbox_world/resolved/*` (new)
   - Depends on: step 1
3. **Compile and validate.** Compile the resolved spec via `WorldCompiler.compile()`. Confirm
   zero validation warnings/errors. Inspect the resulting `AuthoritativeState` (or
   `world_compile_report.json`) to confirm monster-role entities (from `wolf_pack_small`) get
   non-flat, catalog-resolved stats — this is the primary success signal.
   - Files: `data/worlds/sandbox_world/world_compile_report.json` (regenerated)
   - Depends on: step 2
4. **Empirical re-run.** Run the D20 audit's 200-tick scenario at seed 42 (and 137) against
   the migrated world. Record new `state_hash`, new entity count, and note whether the
   original tick-8 monster extinction still occurs (expected: likely still occurs at this
   stage, since the hazard-drain root cause is fixed separately by
   `TCK-20260701-HAZARD-NATIVE-IMMUNITY` — do NOT treat persistence of that symptom as a
   failure of THIS ticket; this ticket's success criterion is real stats + clean compile, not
   the extinction fix, which needs both sibling tickets).
   - Depends on: step 3
5. **Regenerate calibration anchors (mandatory, not optional).** Per
   `test_grade_regression.py`'s documented procedure: re-run
   `tools/calibrate_simq.py` for all 4 affected keys (`sandbox_world_seed42_200t`,
   `seed137_200t`, `seed999_200t`, `seed42_1000t`), inspect new grades in
   `data/calibration/<run_key>/quality_report.json`, update
   `tests/simulation_quality/fixtures/grade_anchors.json`, re-run
   `test_grade_regression.py` to confirm it passes with the new anchors.
   - Files: `data/calibration/sandbox_world_*` (regenerated),
     `tests/simulation_quality/fixtures/grade_anchors.json`
   - Depends on: step 4
6. **Update D20 audit doc.** `docs/audits/D20_simq_integration.md` — record the new baseline
   (entity count, state_hash, grade table) alongside the old one for traceability; note the
   migration ticket ID.
   - Files: `docs/audits/D20_simq_integration.md`
   - Depends on: step 5
7. **Confirm MODULE_MATRIX coverage.** Check
   `tests/integration/worldassembly/test_real_content_world_modules.py`'s `MODULE_MATRIX` —
   `frontier_village_core` and `wolf_den_near_forest` should already be covered (per
   `TCK-20260630-WORLD-TEST-MATRIX`). Confirm, don't re-add if already present.
   - Depends on: step 3

## Files to Change

- `data/worlds/sandbox_world/world.yaml` (rewritten)
- `data/worlds/sandbox_world/resolved/*` (new, generated)
- `data/worlds/sandbox_world/world_compile_report.json` (regenerated)
- `data/calibration/sandbox_world_*` (regenerated, 4 run keys)
- `tests/simulation_quality/fixtures/grade_anchors.json` (updated)
- `docs/audits/D20_simq_integration.md` (updated)

## Scope Guards

- Do NOT modify `WorldCompiler.compile()`, `WorldAssemblyResolver`, or any resolver/compiler
  code — this is a pure content-authoring change using existing mechanisms.
- Do NOT touch any world other than `sandbox_world`.
- Do NOT attempt to fix the tick-8 extinction in this ticket — that requires
  `TCK-20260701-HAZARD-NATIVE-IMMUNITY` as well; this ticket's job is real stats + clean
  compile + updated calibration baseline only.
- Do NOT author new modules — `frontier_village_core` + `wolf_den_near_forest` are sufficient
  and already paired.
- Do NOT weaken or delete `test_grade_regression.py`'s tolerance/assertions to force a pass —
  regenerate the underlying anchor data instead.

## Dependency Map

```
1 (rewrite world.yaml)
  -> 2 (resolve)
    -> 3 (compile + validate stats)
      -> 4 (empirical re-run)
        -> 5 (regenerate grade anchors)
          -> 6 (update D20 audit doc)
      -> 7 (confirm MODULE_MATRIX coverage, can run parallel to 4-6)
```

## Acceptance Criteria Mapping

| AC | Step |
|---|---|
| `schema_version: worldcomposition.v1` | 1 |
| `resolved/world.resolved.yaml` exists and validates | 2 |
| Compiles cleanly, zero warnings | 3 |
| Monster entities get non-flat catalog stats | 3 |
| 200-tick seed 42/137 re-run completes, new state_hash recorded | 4 |
| D20 audit doc updated | 6 |
| No regression in sandbox_world-referencing tests | 5, 7 (+ regression surface in test_plan.md) |

## Unresolved Questions

None. Module pair choice is grounded in direct file reads (matching `requires:` relationship,
matching town region bounds), the composition format is modeled on an existing working
minimal example (`highland_traverse`), and the grade-anchor regeneration procedure is
explicitly documented in the target test file itself. No human decision is needed before
implementation.

## Deviations

One out-of-plan, low-risk correction was made beyond the 7 steps: during the parity-ledger
confirmation pass (Parity phase), found that `docs/parity_ledger/progression.yaml` entry
`PROG-108`'s `v2_evidence` cited `sandbox_world`'s old `worldtemplate.v1` HERO population
("sandbox_world (3 HERO via recipe + faction villagers)") as one of two example worlds proving
HERO class-assignment coverage. `frontier_village_core` + `wolf_den_near_forest` have no HERO
population, so this citation became stale post-migration. The entry's `status` (`verified`),
`priority`, and `test_path` are unaffected — `test_path`
(`tests/unit/entity/test_entity_archetypes.py::test_hero_archetypes_cover_combat_mage_rogue`)
uses a synthetic fixture (`_HERO_ARCHETYPE_SPEC`), not `sandbox_world`, and `urban_political`'s
HERO population (the other cited example) is untouched by this ticket. Corrected the
`v2_evidence` prose only to reflect current state; no status change. This goes slightly beyond
the architecture review's "no parity ledger entries need updating" determination, but was
judged in-scope as a documentation-accuracy fix required by the project's "100% semantic
parity" rule (CLAUDE.md, Authoritative Mechanics Rule) rather than a new parity claim — it does
not touch `WorldCompiler`/`WorldAssemblyResolver` code or any world other than `sandbox_world`'s
own migration fallout, and stays within the ticket's non-negotiable scope guards.

All other steps executed exactly as planned, no other deviations.
