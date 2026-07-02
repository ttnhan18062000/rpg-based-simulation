---
ticket_id: TCK-20260701-SANDBOX-MONSTER-BALANCE
phase: investigation
date: 2026-07-02
---

# Investigation — TCK-20260701-SANDBOX-MONSTER-BALANCE (ATTEMPT 3, RE-VERIFICATION PASS)

## Context — why this pass exists
The previous attempt-3 pass (recorded in `plan.md`/`test_plan.md` before this overwrite, and
still summarized in the ticket's Implementation Notes) found the premise **falsified**:
`RegionRecipeSpec` (`src/worldbuilding/recipe.py`) and `WorldAssemblyResolver.resolve_module_
contribution()` (`src/worldassembly/resolver.py`) never accepted/forwarded `hazard_kind`, so
`python3 -m src.worldbuilding.cli resolve sandbox_world` failed with a Pydantic
`extra_forbidden` error before `WorldCompiler.compile()` was ever reached. All
`worldcomposition.v1` module loading was blocked (`test_real_content_world_modules.py` 5/5
ERROR). That pass correctly stopped rather than force a fix, and filed
`TCK-20260701-HAZARD-KIND-RESOLVER-GAP` as the defect ticket.

`TCK-20260701-HAZARD-KIND-RESOLVER-GAP` is now DONE (see `tickets/working_log.csv`,
`tickets/done/TCK-20260701-HAZARD-KIND-RESOLVER-GAP.md`). This pass re-verifies from scratch —
it does not assume the hotfix worked, it re-derives evidence.

**Context search performed first (per CLAUDE.md):**
- `mcp__knowledge-search__search_docs("sandbox_world hazard_kind resolver fix recompile
  verification")` returned the `HAZARD-KIND-RESOLVER-GAP` working-log entry (hotfix summary),
  the `HAZARD-NATIVE-IMMUNITY` amendment entry (gap discovery), and
  `docs/audits/D20_simq_integration.md#compile-validation-007` (compile-validation contract
  reference) — confirms the hotfix and its scope are indexed and consistent with the ticket.
- `graphify query "sandbox_world resolve compile hazard_kind wolf_pack_small verification"`
  returned a generic BFS over `compile()`/`resolve()` call-graph neighbors (state/update model
  nodes) — not specific enough to add signal beyond direct code inspection below; direct reads
  were used as the follow-up per CLAUDE.md's "grep/read are follow-up only" rule.

## Step 1 — Confirm the hotfix landed in source
```
$ grep -n "hazard_kind" src/worldbuilding/recipe.py
16:    hazard_kind: Optional[str] = Field("PHYSICAL", description="Semantic type of this
    region's passive hazard drain (e.g. 'PHYSICAL', 'NATURAL_TERRAIN', 'TOXIC_GAS').")

$ grep -n "hazard_kind" src/worldassembly/resolver.py
784:                hazard_kind=getattr(reg, "hazard_kind", "PHYSICAL"),
```
Both edits are present and match the hotfix ticket's working-log description exactly:
`RegionRecipeSpec.hazard_kind` field added (mirroring `RegionSpec`), and
`WorldAssemblyResolver.resolve_module_contribution()` forwards it. (`git diff` against `HEAD`
shows these as part of a larger uncommitted working-tree diff spanning the whole
`worldtemplate-deprecation` epic chain — nothing in this repo state has been committed yet in
this session; that is expected given the working log shows many sequential DONE tickets with no
intervening commits. Confirmed via direct content inspection, not commit history, since these
files have no dedicated commit yet.)

## Step 2 — Re-run the actual resolve/compile commands
```
$ python3 -m src.worldbuilding.cli resolve sandbox_world
Resolving composition world 'sandbox_world'...
Resolution successful for world 'sandbox_world'!
  ...
  Validation report:      sandbox_world/resolved/validation_report.json

$ python3 -m src.worldbuilding.cli compile sandbox_world --seed 42 --from-resolved
Compilation successful!
  Final State Hash: 836b45e8913b46862240c6ba80f177f6
  Entities Spawns:  18
  Quest Count:      6
```
No `extra_forbidden` error, no validation errors (`validation_report.json`:
`catalog_validation` 0 errors / 92 warnings — all pre-existing `CAT-DEAD-*` unused-catalog-term
warnings, unrelated to this ticket; `composition_validation` 0/0; `world_validation` 0/0).
Re-ran `resolve` + `compile --seed 42` a second time to confirm determinism: identical hash
`836b45e8913b46862240c6ba80f177f6` both times. `compile --seed 137` also succeeds cleanly
(hash `7e8ae05dbeffccb8edd65fd9754787aa`).

## Step 3 — Confirm resolved `hazard_kind` on `wolf_den`/`near_forest`
`data/worlds/sandbox_world/resolved/world.resolved.yaml`:
```yaml
regions:
- id: hometown
  hazard_level: 0.0
  hazard_kind: PHYSICAL
- id: near_forest
  hazard_level: 1.0
  hazard_kind: NATURAL_TERRAIN
- id: wolf_den
  hazard_level: 2.0
  hazard_kind: NATURAL_TERRAIN
```
Both wilderness regions resolve `NATURAL_TERRAIN`; the town region defaults to `PHYSICAL` as
expected (no regression to non-monster regions). This same `hazard_kind` value is confirmed
present on the **compiled** `RegionState` objects too (not just the resolved YAML) — see Step 4.

## Step 4 — Trace `hazard_immunities` through the real resolution/drain code path
Not just reading YAML — traced through the actual services used by the engine at runtime:

```python
>>> from src.content_semantics.faction import get_faction_semantics_service
>>> svc = get_faction_semantics_service()
>>> svc.get_hazard_immunities('wild_beast_pack')
frozenset({'NATURAL_TERRAIN'})
>>> svc.get_hazard_immunities('hero_guild')
frozenset()
```
Then loaded the actual compiled `AuthoritativeState` (via `tools.calibrate_simq._load_world_
state('sandbox_world', 42)`, the same loader the D20 calibration harness uses) and called the
real `EnvironmentService.calculate_hazard_drain`:
```python
>>> state, report = _load_world_state('sandbox_world', 42)
>>> report['entity_count']
18
>>> wolf_den = state.regions['wolf_den']         # hazard_level=2.0, hazard_kind=NATURAL_TERRAIN
>>> e14 = state.entities[14]                     # faction=wild_beast_pack, position (104,65) — inside wolf_den bounds
>>> EnvironmentService.calculate_hazard_drain(wolf_den, e14)
0
>>> hero = state.entities[9]                     # faction=hero_guild (defender)
>>> EnvironmentService.calculate_hazard_drain(wolf_den, hero)
20                                                # control: non-immune faction still takes drain
```
This confirms the immunity mechanism is live end-to-end through the real
`FactionSemanticsService` → `EnvironmentService.calculate_hazard_drain` path, not just present
in content YAML. `wild_beast_pack` entities 14-18 (the 5 monsters, matching the original "5
monster-type entities" from the D20 finding) are confirmed positioned inside `wolf_den`'s
`bounds` (`[70,30,105,70]`) and take zero drain there; a control entity of a non-immune faction
in the same region takes the expected non-zero drain (`hazard_level=2.0` → drain `20`).

## Step 5 — Regression suite
```
$ pytest tests/integration/worldassembly/test_real_content_world_modules.py -v
tests/integration/worldassembly/test_real_content_world_modules.py::test_real_world_modules_load_from_data_content PASSED
tests/integration/worldassembly/test_real_content_world_modules.py::test_real_world_modules_normalize PASSED
tests/integration/worldassembly/test_real_content_world_modules.py::test_real_world_modules_preserve_count_maps PASSED
tests/integration/worldassembly/test_real_content_world_modules.py::test_real_world_modules_resolve_contributions PASSED
tests/integration/worldassembly/test_real_content_world_modules.py::test_hazard_kind_survives_module_pipeline PASSED
tests/integration/worldassembly/test_real_content_world_modules.py::test_real_world_modules_reference_graph_edges_exist PASSED
6 passed in 0.48s
```
6/6 passing (was 5/5 ERROR before the hotfix, per the hotfix ticket's own working-log entry).
This matches expectations exactly — no further gap found here.

## Step 6 — Empirical 200-tick re-run, seed 42 and seed 137 (beyond the required steps, done to
directly settle the ticket's actual behavioral AC before handing off a plan)
Ran the Kernel for a full 200 ticks against the real compiled `sandbox_world` state (loaded via
`tools.calibrate_simq._load_world_state`, confirming `report['entity_count'] == 18` — i.e. real
content is loading, not the generic 10-entity fallback noted as a gap in attempt 2's notes; that
gap is naturally resolved now because `resolved/world.resolved.yaml` exists).

| Seed | Wolf entities (14-18) at tick 200 | `hazard_drain_applied` events against them | Death events |
|---|---|---|---|
| 42  | all `active=True`, `death_tick=None` | **0** | none |
| 137 | all `active=True`, `death_tick=None` | **0** | none |

Determinism: recompiling seed 42 twice reproduces the identical state hash
(`836b45e8913b46862240c6ba80f177f6`) both times.

**Note on interpreting "zero events" as a clean result, not a masking artifact:** the run used
default feature flags, under which `ENABLE_COMBAT_ENGAGEMENT` is `OFF`
(`src/domains/optimization/feature_flags.py:17`) — same category of default-off gate previously
documented for `ENABLE_ADVENTURE_ROUTING` in `TCK-20260701-SIMQ-AGENCY-ROUTING-DOC`. This does
**not** invalidate the result: attempt 2's original root-cause finding (see ticket
Implementation Notes) was that the wolves died from `hazard_drain_applied` — a world-evolution/
environment-tick mechanism, not gated by `ENABLE_COMBAT_ENGAGEMENT` — independent of any combat
engagement with town-faction entities. The same conditions that originally reproduced the bug
(no combat engagement, pure environment-tick hazard drain) are reproduced here, and now show
zero drain events and zero deaths for the monster population. Testing with
`ENABLE_COMBAT_ENGAGEMENT=ON` to observe general combat attrition is a different, broader
question (general combat balance) explicitly out of this ticket's scope (see ticket's
"Out of Scope").

One incidental observation, **not actionable by this ticket**: the `sandbox_world_seed42_200t`
calibration anchor's `COMBAT` pillar event_count dropped from a stale pre-hotfix value of 13
(tick_count 57, an older/shorter run) to 0 (tick_count 200, this run) — this is fully explained
by `ENABLE_COMBAT_ENGAGEMENT` defaulting off in this harness invocation, not a regression; noted
for whoever regenerates the anchors in the Plan step, so the grade shift isn't mistaken for an
unexplained change.

## Root Cause Confirmation (final)
The blocking defect (`RegionRecipeSpec`/`WorldAssemblyResolver` not forwarding `hazard_kind`)
is fixed. The underlying mechanism it was blocking
(`TCK-20260701-HAZARD-NATIVE-IMMUNITY`'s typed `hazard_kind`/`hazard_immunities` exemption) now
demonstrably works end-to-end for `sandbox_world`: `wild_beast_pack`-faction monsters
(`wolf_pack_small`, entities 14-18) no longer take any `hazard_drain_applied` damage while
standing in their own `wolf_den`/`near_forest` habitat, and all 5 survive a full 200-tick run at
both seed 42 and seed 137 — a stronger result than the AC's minimum bar ("some early combat
death is fine; a total wipe is not").

## Unresolved Questions
**No genuine blockers remain for the recompile-and-verify mechanism itself.** The hazard-immunity
fix works as designed, through the real code path, for the real content.

Non-blocking items carried into the Plan phase (not blockers, just remaining checklist work):
1. `sandbox_world`'s persisted `resolved/` artifacts and `world_compile_report.json` are
   regenerated (done in this pass, left at the seed-42 canonical compile) but the 4
   `sandbox_world_*` calibration anchors and `docs/audits/D20_simq_integration.md` P2 row are
   **not yet updated** — that's Plan step 4/5, deliberately not done in this Investigate pass to
   keep the anchor regeneration + doc update as one coordinated, reviewable action rather than
   scattering it across an investigation pass.
2. `docs/guidelines/intentional_divergences.md` entry 2.20 already documents the
   `hazard_kind`/`hazard_immunities` mechanism and explicitly notes (line ~184-185) that
   `sandbox_world`'s compiled artifacts "remain stale... until recompiled by
   TCK-20260701-SANDBOX-MONSTER-BALANCE" — that note needs a one-line update once the real
   (non-throwaway) recompile is finalized, not a new entry.
3. `data/calibration/sandbox_world_seed42_200t/quality_report.json` was incidentally refreshed
   by this pass's verification run (real 200-tick data, `tick_count` 57→200) — this is a
   byproduct of running the standard calibration tool to get real events for the survival check,
   not a deliberate "regenerate anchors" action. The other 3 anchors
   (`seed137_200t`, `seed999_200t`, `seed42_1000t`) were already dirty/uncommitted in the working
   tree from the prior migration ticket's regeneration pass and were not touched by this
   verification. Full, coordinated 4-anchor regeneration remains a Plan step.
