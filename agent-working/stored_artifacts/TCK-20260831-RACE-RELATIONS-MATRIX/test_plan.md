---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-RACE-RELATIONS-MATRIX
artifact_type: test_plan
tags: [faction, content, combat]
---

# Test Plan — TCK-20260831-RACE-RELATIONS-MATRIX

## Regression Surface

**Unit — relation projection:**
- `tests/unit/engine/test_combat_relation_projection.py` — `test_hero_treats_goblin_warband_as_hostile`,
  `test_hero_treats_merchant_league_as_neutral`, `test_wild_beast_threat_requires_territory_context`,
  `test_legacy_monster_horde_is_hostile_via_fallback`, `test_projection_source_in_attack_payload_clean_metadata`,
  `test_projection_source_in_payload_legacy_entity`, `test_neutral_entity_not_targeted`,
  `test_identity_resolver_clean_metadata`, `test_identity_resolver_legacy_compat_projection` — must
  keep passing unchanged (none of these entities have race-relations content authored for their
  pairs, so faction-only label resolution must remain the fallback path when no `race_relations`
  entry matches).
- `tests/unit/content_semantics/test_semantics.py` — `FactionSemanticsService`/`is_hostile_compat`
  general coverage.
- `tests/unit/quest/test_quest_relation_projection.py` — `quests.py`'s `project_relation(..., None)`
  call site; context is always `None` here so must be entirely unaffected.
- `tests/integration/combat/test_relation_combat_integration.py` — end-to-end relation-driven combat
  behavior.

**Unit — content catalog:**
- `tests/unit/content/test_content_usage_matrix.py` — enforces `CANONICAL_FAMILIES` ↔
  `CONTENT_USAGE_MATRIX` registration parity; will fail once `race_relations` is added to one but
  not the other, so must pass with both updated together.
- `tests/unit/content/test_faction_relationships_coverage.py` — must be entirely unaffected (it
  scopes to `faction_relationships.yaml` only); acts as the negative control proving the new content
  family didn't touch faction relationship loading.

**Unit — combat legality / friendly fire:**
- `tests/unit/combat/test_phase5_negative_cases.py`
- `tests/unit/combat/test_phase5_combat_legality.py`
- `tests/unit/combat/test_combat_legality_regression.py`
- `tests/unit/combat/test_combat_legality_contract.py`
- `tests/unit/combat/test_combat_matrix.py`
- `tests/unit/combat/test_readiness_regen.py`
- `tests/unit/world/test_local_environment_semantics.py`
- `tests/unit/strategic/test_strategic_cognition_regression.py`
All of the above must keep passing unchanged — race-hostility factoring must never flip an existing
passing/failing legality outcome for pairs that have no authored `race_relations` entry (i.e., the
new lookup's miss-path must be a true no-op, matching the existing `if not relationship:` graceful-
miss pattern in `project_relation()`).

**Unit — tactical target selection:**
- `tests/unit/combat/test_capability_driven_targeting.py` — covers `target_score()`'s current
  6-tuple `(group_bias, is_current_target, -capability_confidence, h.combat.hp, dist*pressure_dist_mod,
  h.id)` shape (landed via `TCK-20260831-CAPABILITY-DRIVEN-TARGETING`). Must keep passing — if race
  hostility changes which entities land in the `hostiles` list (via `is_hostile_compat`) but does
  not change `target_score()`'s tuple shape itself, this file's existing assertions on tuple
  structure/ordering must be unaffected. If Plan chooses to *also* fold race hostility into the sort
  tuple itself (not required by AC #2, which only asks for hostile-scan/label-level behavior), that
  would require updating this file — flag explicitly if scope grows to touch `target_score()`'s
  tuple shape, since AC #2 as written targets `project_relation()`'s label output, not the sort
  tuple.

**Arena-combat / integration:**
- `tests/integration/combat/test_relation_combat_integration.py` (listed above, repeated for
  emphasis — closest existing integration-level regression guard for this exact wiring path).

## New Tests Required

Per AC:

1. **Race-relations content loads via new `ContentFamilySpec`**
   - Test name: `test_race_relations_content_family_loads`
   - Category: unit
   - Verifies: `CatalogRepository("data/content").load_all()` populates a new repository index
     (e.g. `repo.race_relations`) with `RaceRelationRecord` instances parsed from the new
     `race_relations.yaml`; schema rejects unknown fields (`extra="forbid"`) via a
     `pytest.raises`/`ValidationError` case with an injected bad field.
   - Location: `tests/unit/content/test_race_relations_catalog.py` (new file, mirrors
     `test_faction_relationships_coverage.py`'s fixture pattern: module-scoped `CatalogRepository`
     fixture, `reset_faction_semantics_service` autouse fixture if `FactionSemanticsService` caching
     is touched by the new lookup).

2. **`CONTENT_USAGE_MATRIX` registration**
   - Test name: covered by existing `test_content_usage_matrix.py` parity check — no new test file
     needed, just ensure the new `ContentFamilyMatrixEntry` is added to `matrix.py` alongside the
     new `ContentFamilySpec` in `repository.py` in the same change.

3. **`target_race` consumption produces different labels for different hostility**
   - Test name: `test_race_relations_hostility_changes_projected_label`
   - Category: unit
   - Verifies: two calls to `RelationProjectionService.project_relation(...)` with the same
     perspective/source_faction/target_faction but `RelationContext(target_race=<race_a>)` vs.
     `RelationContext(target_race=<race_b>)`, where `race_a`/`race_b` have authored `race_relations`
     entries with different `axes.hostility` values for the same faction pair, produce different
     `RelationProjection.label` values. This is AC #2's literal verification requirement — write it
     against two races Plan actually authors with contrasting hostility for the same faction pair.
   - Location: `tests/unit/content_semantics/test_relation_race_projection.py` (new file) or as an
     addition to `tests/unit/engine/test_combat_relation_projection.py` — prefer the new file since
     `relation.py` is the module under test, not `engine/`.
   - A second case in the same test: `target_race=None` (or an unregistered race id) falls through
     to the existing faction-only label — regression guard for the graceful-miss requirement in
     Anti-Drift Hazards.

4. **Legality path wiring** (`src/engine/legality.py:243-247`)
   - Test name: `test_attack_legality_race_hostility_affects_friendly_fire_check`
   - Category: unit
   - Verifies: `LegalityServiceV2.verify_attack_legality` returns a different
     `(bool, ReasonCode)` outcome (specifically around `FRIENDLY_FIRE_ILLEGAL`) for two otherwise-
     identical attacker/target pairs that differ only in `target.identity.properties["race_id"]`,
     where the two races have contrasting authored `race_relations` hostility against the
     attacker's faction-derived stance.
   - Location: `tests/unit/combat/test_race_relations_legality_wiring.py` (new file) — keep separate
     from the existing `test_combat_legality_*.py` files per the "don't retrofit unrelated
     assertions into existing files" convention implied by how narrowly-scoped
     `test_capability_driven_targeting.py` and `test_faction_relationships_coverage.py` are.

5. **Tactical path wiring** (`src/engine/tactical.py:212-216`)
   - Test name: `test_tactical_hostile_scan_race_hostility_affects_target_pool`
   - Category: unit
   - Verifies: `TacticalDecisionSystem.evaluate_entity_intent`'s neighbor hostile-scan (`hostiles`
     list construction, `tactical.py:193-225`) includes/excludes a neighbor entity based on
     race-relations hostility, holding faction pairing constant across the two cases.
   - Location: `tests/unit/combat/test_race_relations_tactical_wiring.py` (new file).

6. **Mutation lab metamorphic validation** (AC #3)
   - Test name/shape: depends on the outcome of the BLOCKING open question in investigation.md
     (Risk #1) — `MutationSpec.target` cannot currently address content-catalog fields. **This is
     not purely a test-authoring task; it requires an implementation decision first.** Once Plan
     resolves that:
     - If Plan extends `MutationEngine` to support a content-catalog target root: add a unit test
       for the new target-resolution branch in `tests/unit/lab/test_mutation.py` (or wherever
       `MutationEngine.apply_mutations` unit tests currently live — grep before creating a new
       file), plus an integration-level test analogous to the pilot's own verification, running
       `MutationLabOrchestrator.run_mutation_lab()` against a real mutation spec and asserting
       `MetamorphicRuleEngine.evaluate_rules(...)` returns a `PASSED` `monotonic_non_decreasing`
       result for a `combat_engagement`-shaped metric between baseline and higher-hostility variant.
     - Category: integration (mirrors the pilot ticket's own verification shape — a real corpus
       world, real CLI invocation or direct orchestrator call, not a synthetic fixture-only test).
     - Location: follow the pilot ticket's own test/verification location convention exactly (check
       `stored_artifacts/TCK-20260831-METAMORPHIC-LAB-PILOT/test_plan.md` for the precise path it
       used — not re-derived here since the mechanism itself is still an open question).
   - Flag explicitly in Plan/Implement: this AC cannot be test-planned to file-level precision until
     the target-addressing mechanism is decided (Risk #1 in investigation.md).

7. **Coverage-subset disclosure test** (AC #4)
   - Test name: `test_race_relations_coverage_meets_disclosed_threshold`
   - Category: unit / architecture-guard (regression floor, same shape as
     `test_faction_relationships_coverage_meets_threshold`)
   - Verifies: authored `race_relations.yaml` entry count meets or exceeds whatever threshold Plan
     commits to (e.g. "≥N populated-race pairs" against a denominator Plan derives — see
     investigation.md Prior Work note on checking `entity_archetypes.yaml`/`populations.yaml` race
     references before picking a denominator), mirroring
     `test_faction_relationships_coverage.py`'s `POPULATED_FACTIONS`-style frozenset pattern.
   - Location: `tests/unit/content/test_race_relations_coverage.py` (new file, sibling to
     `test_faction_relationships_coverage.py`).

## Scoped Pytest Commands

Regression verification (never `pytest tests/`):

```
pytest tests/unit/content/ tests/unit/content_semantics/ -m "not slow"
pytest tests/unit/engine/test_combat_relation_projection.py tests/unit/quest/test_quest_relation_projection.py -m "not slow"
pytest tests/unit/combat/ -m "not slow"
pytest tests/unit/strategic/test_strategic_cognition_regression.py tests/unit/world/test_local_environment_semantics.py -m "not slow"
pytest tests/integration/combat/test_relation_combat_integration.py -m "not slow"
```

New-test-inclusive full domain sweep once new files exist:

```
pytest tests/unit/content/ tests/unit/content_semantics/ tests/unit/combat/ tests/unit/engine/test_combat_relation_projection.py tests/integration/combat/ -m "not slow"
```

Mutation-lab AC #3 verification (once target-addressing mechanism is resolved — see New Tests #6):

```
python -m src.lab.cli validate-mutation <race_hostility_mutation_id>
python -m src.lab.cli run-mutation <race_hostility_mutation_id> --experiment <experiment_id>
pytest tests/unit/lab/ tests/integration/lab/ -m "not slow"
```

## Anti-Drift Test Guards

- `test_faction_relationships_coverage.py` must pass **unmodified** — proves the new
  `race_relations` content family did not silently touch faction relationship loading, counts, or
  the `neutral` faction's zero-hostility invariant.
- `test_content_usage_matrix.py` must pass with the new family registered on **both** sides
  (`CANONICAL_FAMILIES` in `repository.py` and `CONTENT_USAGE_MATRIX` in `matrix.py`) — this is the
  existing mechanical guard against a registered-but-undocumented (or documented-but-unregistered)
  content family.
- All pre-existing `test_combat_relation_projection.py` cases must produce identical outcomes when
  run against entity pairs that have **no** authored `race_relations` entry — this is the concrete
  regression guard against the miss-path silently changing default behavior (the graceful-miss
  requirement flagged in investigation.md's Anti-Drift Hazards).
- `test_capability_driven_targeting.py` must pass unmodified unless Plan explicitly decides to widen
  scope into `target_score()`'s sort-tuple shape — if that file needs edits, it is a signal that
  scope grew beyond AC #2's literal wording (label-level projection, not sort-tuple composition) and
  should be called out at Verify, not silently absorbed.
- A dedicated same-faction guard: a test asserting that when `attacker.identity.faction ==
  target.identity.faction`, `verify_attack_legality` still returns `FRIENDLY_FIRE_ILLEGAL`
  regardless of any authored race-relations hostility between their two races — directly guards
  against Risk #2 (race hostility bypassing the Friendly Fire law) in investigation.md.
