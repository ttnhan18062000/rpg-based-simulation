---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS
artifact_type: test_plan
tags: [simulation-quality, faction]
---

# Test Plan — TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS

## Regression Surface

This ticket is catalog-data-only, but the investigation established that
`faction_relationships.yaml` is a live input to combat legality and reward classification (via
`FactionSemanticsService.is_hostile_compat()` / `RelationProjectionService.project_relation()`).
The regression surface is therefore wider than "content validation passes" — it includes every
suite that exercises that call graph.

**Unit — content/catalog validation:**
- `tests/unit/content/test_content_usage_matrix.py` — `CONTENT_USAGE_MATRIX["social/faction_relationships"]`
  entry must still resolve; new file content must not break the matrix registration.
- `tests/unit/content/test_reference_graph.py` — asserts `faction_relationship:<id>` edges exist
  in the dependency graph for known fixture IDs; must not regress on real-catalog load.
- `tests/unit/content/test_layered_catalog.py` — writes/reads a `faction_relationships.yaml`
  fixture; confirm schema assumptions still match (`source_faction`, `target_faction`,
  `relationship_model`, `axes`).
- `tests/unit/content/test_resolvers.py` — exercises `src/content/resolver.py`'s use of
  `faction_relationships` (unresolved consumer flagged in investigation — verify test coverage
  here before/after the change).
- Any `make world-validate` / `make content-check` catalog validator run — confirms no
  `CAT-REL-012` (missing source/target faction, missing axis ID) issues from new entries.

**Unit — content_semantics (the real behavior surface):**
- `tests/unit/content_semantics/test_semantics.py`
- `tests/unit/engine/test_combat_relation_projection.py` — `test_hero_treats_goblin_warband_as_hostile`,
  `test_hero_treats_merchant_league_as_neutral`, `test_wild_beast_threat_requires_territory_context`,
  `test_legacy_monster_horde_is_hostile_via_fallback`, plus the 3
  `test_projection_source_in_*`/`test_neutral_entity_not_targeted` end-to-end targeting tests.
  These all use factions with existing `perspectives.yaml` entries (`hero_guild`, `wild_beast_pack`,
  `merchant_league`) — perspective labels take priority over relationship axes, so these should be
  low-risk, but must still be run since they are the only direct coverage of
  `is_hostile_compat()`/`project_relation()`.

**Integration — combat legality:**
- `tests/integration/combat/test_relation_combat_integration.py` —
  `test_integration_perspective_hostility` (asserts `LegalityServiceV2.verify_attack_legality`
  legal/illegal outcomes for hero_guild vs goblin_warband and hero vs hero-ally),
  `test_integration_contextual_beast_threat`, `test_integration_legacy_fallback` (uses
  `"unconfigured_hero_faction"`/`"unconfigured_monster_faction"` — synthetic IDs that will never
  match real catalog entries, so genuinely orthogonal to this change; keep passing regardless).
- `tests/unit/quest/test_quest_relation_projection.py` — separate consumer of relation projection;
  confirm no incidental coupling to specific faction pairs this ticket will touch.

**Unit/Integration — combat rewards (P0 parity, `COMB-280`):**
- `tests/unit/combat/test_combat_rewards.py` — **must pass** (P0 parity entry `COMB-280`
  requires this per CLAUDE.md). Uses legacy `Faction` enum literals
  (`HERO_GUILD`/`MONSTER_HORDE`/`NEUTRAL`) which do not match real catalog faction ID strings, so
  expected to be unaffected — confirm this holds, do not just assume.

**Architecture / legacy-boundary guards:**
- `tests/architecture/test_enum_migration_report.py`
- `tests/architecture/test_legacy_enum_usage_boundaries.py`
  (both showed up in the `faction_relationships`/`content_semantics` grep sweep — confirm they
  don't assert a fixed relationship-entry count or fixed pair list that this ticket would break.)

**World-level regression (regional consequences use faction context too):**
- `tests/unit/world/test_regional_consequences.py`

## New Tests Required

Per Acceptance Criteria:

1. **Test name:** `test_faction_relationships_coverage_meets_threshold`
   **Category:** unit (content)
   **Verifies:** AC#1 — programmatically counts unique undirected `(source, target)` pairs in
   `data/content/social/faction_relationships.yaml` against the 120 possible pairs (or the 66
   populated-only pairs, per whichever denominator the planner resolves UQ-1 to) and asserts
   ≥ the agreed threshold. Prevents silent regression of coverage in future edits.
   **Location:** `tests/unit/content/test_faction_relationships_coverage.py` (new file) or added
   to `tests/unit/content/test_content_usage_matrix.py` if a narrower home is preferred.

2. **Test name:** `test_neutral_faction_has_explicit_relationship`
   **Category:** unit (content)
   **Verifies:** AC#3 — `neutral` appears as `source_faction` or `target_faction` in at least one
   entry.
   **Location:** same new file as above.

3. **Test name:** `test_new_relationship_entries_reference_valid_axes_and_factions`
   **Category:** unit (content, architecture-guard style)
   **Verifies:** every new entry's `source_faction`/`target_faction` resolves in `factions.yaml`
   and every `axes` key resolves in `relationship_axes.yaml` — a direct, fast-running assertion of
   what the catalog validator (`CAT-REL-012`) already checks, so a broken entry fails at unit-test
   speed rather than only at `make world-validate` time.
   **Location:** same new file, or `tests/unit/content/test_layered_catalog.py`.

4. **Test name:** `test_neutral_first_relationship_is_not_high_hostility`
   **Category:** unit (anti-drift / behavior-risk guard)
   **Verifies:** the `neutral`-faction entry(ies) added for AC#3 do not set `axes["hostility"]`
   to `"high"`/`"medium"` (which would make `is_hostile_compat()` unconditionally hostile for the
   universal fallback faction ID) unless the planner has explicitly signed off on that blast
   radius. See investigation Risk #3.
   **Location:** same new file.

5. **Test name:** `test_new_populated_faction_pairs_prioritized`
   **Category:** unit (content, documents intent) — optional but recommended
   **Verifies:** AC#2 — a majority of newly-added pairs (vs. the 20 existing) involve only
   factions from the 12-populated set (`town_council, merchant_league, wild_beast_pack,
   goblin_warband, bandit_company, forest_wardens, spirit_court, orc_clan, undead_remnants,
   arcane_circle, swamp_tribe, hero_guild`), not `moon_cult`/`dwarven_mine_clan`/`dragon_cult`.
   **Location:** same new file.

6. **Test name:** `test_is_hostile_compat_unchanged_for_previously_legacy_fallback_pairs` (or
   equivalent targeted regression test)
   **Category:** integration (behavior-risk guard, directly answers Risk #2)
   **Verifies:** for any faction pair that goes from "no relationship entry" (legacy alignment-
   bucket fallback) to "has a relationship entry" as a result of this ticket, explicitly assert
   the new `is_hostile_compat()` result and document whether it differs from the pre-change
   legacy-bucket result. This is the direct regression test for the central risk this
   investigation surfaced — not automatically covered by existing suites, since none of them
   exercise the specific new pairs this ticket will add (unknown until implementation).
   **Location:** `tests/integration/combat/test_relation_combat_integration.py` (extend) or a new
   `tests/unit/content_semantics/test_faction_relationship_expansion.py`.

## Scoped Pytest Commands

```
# Content/catalog validation (fast)
pytest tests/unit/content/ -k "faction_relationship or usage_matrix or reference_graph or layered_catalog or resolvers" -q

# content_semantics + legality/reward behavior surface (the real risk area)
pytest tests/unit/content_semantics/ tests/unit/engine/test_combat_relation_projection.py \
       tests/integration/combat/ tests/unit/combat/test_combat_rewards.py \
       tests/unit/quest/test_quest_relation_projection.py -q

# Faction runtime state sanity (confirm no accidental coupling)
pytest tests/unit/faction/ -q

# Architecture/legacy-boundary guards touched by the same grep sweep
pytest tests/architecture/test_enum_migration_report.py tests/architecture/test_legacy_enum_usage_boundaries.py -q

# World/regional consequence sanity
pytest tests/unit/world/test_regional_consequences.py -q

# Full catalog validation
make world-validate WORLD=sandbox_world

# SimQ regression — evaluate-full (real engine re-run), NOT --dry-run (see investigation Risk #4)
make evaluate-full
```

Never run `pytest tests/` in full. Do not rely on `make evaluate --dry-run` alone as the "0
regressions" signal for this ticket — it does not re-run the engine and cannot detect a
legality/reward-classification change caused by new catalog content (investigation Risk #4).

## Anti-Drift Test Guards

- **Perspective-priority guard:** `test_hero_treats_goblin_warband_as_hostile` and
  `test_hero_treats_merchant_league_as_neutral` (existing) implicitly prove that perspective
  labels still win over relationship axes for the 6 perspective-bearing factions — if a future
  edit to `perspectives.yaml` or `RelationProjectionService` changes that priority order, these
  tests catch it, protecting this ticket's assumption that perspective-faction entries are
  lower-risk than non-perspective-faction entries.
- **Legacy-fallback guard:** `test_legacy_monster_horde_is_hostile_via_fallback` and
  `test_integration_legacy_fallback` use synthetic faction IDs that never match a real catalog
  entry — these must keep passing untouched by this ticket, proving the legacy bucket path
  (`is_hostile()`) itself was not altered, only its applicability range (fewer pairs fall through
  to it as more relationship entries are added).
- **`neutral`-blast-radius guard:** new test #4 above (`test_neutral_first_relationship_is_not_high_hostility`)
  — directly guards against the widest-blast-radius mistake this ticket could make.
- **Coverage-denominator guard:** new test #1 — once UQ-1 is resolved and a threshold is chosen,
  this test prevents the ticket (or any future content edit) from silently dropping back below
  the agreed percentage.
- **P0 parity guard:** `tests/unit/combat/test_combat_rewards.py` passing is the direct guard for
  `COMB-280` (P0) — do not consider this ticket done if this suite is skipped.
- **Non-scope-creep guard:** confirm `src/engine/faction_decision.py`,
  `src/domains/faction/diplomatic_state_machine.py`, `src/core/state.py` (`FactionState`), and
  `src/core/updates.py` (`FactionUpdate`) have **zero** diff after implementation — this ticket
  should touch only `data/content/social/faction_relationships.yaml`,
  `docs/plans/audit_fix_plan.md`, and whichever parity ledger file gets a new/updated entry.
