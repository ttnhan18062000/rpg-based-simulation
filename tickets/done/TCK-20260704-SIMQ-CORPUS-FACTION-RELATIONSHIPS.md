---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, faction]
---

# TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS

## Title
Expand faction_relationships.yaml coverage toward the P2-D 50%+ target

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Folds in `docs/plans/audit_fix_plan.md` P2-D ("Faction relationships sparse"). Per
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 and §3,
`data/content/social/faction_relationships.yaml` currently has **34 relationship entries covering
20 of 120 possible undirected faction pairs (16.7%)** across 15 of 16 factions (`neutral` has
zero) — well under the original P2-D target of 50%+ coverage (60+ pairs). This is a **global
content-density gap**, not a per-world one: every world draws from the same underactivated
relationship catalog, so fixing it once benefits every world simultaneously (investigation.md §3:
"same risk class as FACTION tension seeding" — pure content, additive, no code risk).

## Scope
1. Read the current `data/content/social/faction_relationships.yaml` (34 entries, 20/120 pairs) and
   `data/content/social/factions.yaml` (16 factions) to establish the exact current coverage matrix
   — which of the 120 undirected pairs are covered, which are not, and which faction (`neutral`) has
   zero relationships today.
2. Per P2-D's own fix guidance, prioritize **conflict and economy module factions first** (highest
   encounter frequency) — cross-reference which factions actually appear as "populated" across the
   corpus (investigation.md §2's per-world faction lists) to focus new relationship entries on
   factions that actually see gameplay traffic, not purely theoretical catalog completeness.
3. Author new relationship entries to reach at least 50%+ coverage of active cross-faction pairs
   (60+ of 120 undirected pairs, per P2-D's original target) — prioritizing factions with existing
   populated presence in the corpus (per investigation.md §2) and factions appearing in conflict/
   economy modules over factions with no live gameplay presence.
4. Ensure the `neutral` faction gets at least some explicit relationship entries rather than
   remaining fully default (P2-D's finding: "Factions without explicit relationships default to
   neutral, reducing encounter variety").
5. Re-run `make evaluate --dry-run` after the catalog change — this is global content, so it may
   affect FACTION-pillar-adjacent behavior in any world with faction interactions; confirm 0
   regressions or document and resolve any drift found.
6. Update `docs/plans/audit_fix_plan.md`'s P2-D section: change status from "UNVERIFIED" to
   resolved with the new coverage percentage, mirroring the resolution-note style already used for
   other P2 items in that document (e.g. P2-B, P2-C).
7. Update the P2-D row in the Summary Table at the bottom of `audit_fix_plan.md`.

## Out of Scope
- Any per-world content changes (`faction_tension_overrides`, `information_source_profiles`) — that
  is tickets 4, 6-8 in this batch; this ticket is exclusively the global relationship catalog
- Implementing any new faction-interaction engine logic — `DiplomaticStateMachine`/
  `MilitaryConflictPhase` already exist (per `docs/plans/audit_fix_plan.md` P1-C, resolved) and are
  not touched by this ticket; this is pure catalog content
- Fixing any downstream bug this catalog expansion surfaces — file a follow-up ticket

## Acceptance Criteria
- [x] `data/content/social/faction_relationships.yaml` coverage reaches at least 50% of the
      **populated-only 66-pair basis** (34/66 = 51.5%, per this plan's resolved UQ-1 — see
      Implementation Notes); raw-120 basis also improved to 41/120 (34.2%), up from 20/120 (16.7%)
- [x] Conflict and economy module factions are prioritized (documented reasoning in Implementation
      Notes, cross-referencing which factions have live populated presence per investigation.md §2)
- [x] `neutral` faction has at least 1 explicit relationship entry (was 0 before this ticket)
- [x] Corrected verification: `make evaluate-full` (real engine re-run, not `--dry-run` — see
      Risk #4 / plan Step 6) exits 0 with 0 regressions across 610 pillars; dedicated
      unit/integration tests added for every behavior-risk pair (see Implementation Notes)
- [x] `docs/plans/audit_fix_plan.md` P2-D section updated with resolution status and new coverage
      percentage, and the Summary Table's P2-D row updated to match
- [x] `make knowledge-index-update` run (docs/plans/audit_fix_plan.md was modified)
- [x] **New AC (added by plan.md):** every new pair whose source lacks a `perspectives.yaml` entry
      has targeted tests proving both its `combat_rewards.py`/`is_hostile_compat()` delta and its
      separate `legality.py` Friendly-Fire delta; `COMB-294` parity ledger entry added

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO — its new FACTION-isolation world benefits from
  richer relationship coverage once this ticket lands
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — its per-world faction tension seeding becomes
  more meaningfully differentiated once cross-faction relationships are denser
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS — its many-factions/small-map world benefits from richer
  relationship coverage to avoid an all-`neutral`-default outcome

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory table, "Faction relationships catalog density" row) and §3 ("P2-D (faction
  relationships sparse) — fold-in candidate")
- `docs/plans/audit_fix_plan.md` — P2-D section (source finding, current UNVERIFIED status, 50%
  target) and Summary Table P2-D row

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation

## Related Code Areas
- `data/content/social/faction_relationships.yaml` — the file being expanded (75 entries, up from 34)
- `data/content/social/factions.yaml` — 16-faction catalog, `neutral` faction, `alignment_bucket`
  and `legacy_engine_bucket` attributes (both gate different consumers — see Implementation Notes)
- `src/content_semantics/faction.py` — `FactionSemanticsService.is_hostile_compat()`, the real
  hostility predicate this catalog file drives
- `src/content_semantics/relation.py` — `RelationProjectionService.project_relation()`, the
  hostility-axis-to-label projection this catalog file's `axes["hostility"]` values feed
- `src/engine/legality.py` — `LegalityServiceV2.verify_attack_legality()` (Friendly Fire law,
  `docs/mechanics/02_combat_laws.md`), gated by `is_hostile_compat()`
- `src/engine/combat_rewards.py` — `CombatRewardClassificationService.classify_defeated_target()`
  (parity ledger `COMB-280`, P0), also gated by `is_hostile_compat()`
- Correction: `src/engine/faction_decision.py` (`DiplomaticStateMachine`) does **not** read this
  catalog file — confirmed by direct grep during investigation; the original ticket's listing of
  it as a consumer was factually wrong. It manages the separate runtime `FactionState.diplomatic_relations`
  mechanism (`docs/systems/faction_contract.md`), untouched by this ticket.

## Assumptions / Open Questions
- UQ-1: "Active cross-faction pairs" — does this mean all 120 mathematically possible pairs, or
  only pairs where both factions have populated presence somewhere in the current corpus (per
  investigation.md §2)? P2-D's original text says "50%+ coverage of active cross-faction pairs" —
  interpret "active" as populated-somewhere-in-corpus pairs first (a smaller, more meaningful
  denominator), but also report the raw 120-pair percentage for direct comparison against P2-D's
  original 16.7%-of-120 framing, so both readings are available.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS/plan.md` (2nd
architecture-review pass, APPROVED). Implementation spanned two sessions due to a session/API-limit
interruption after Step 3; Step 3's authored content was verified intact before resuming Steps 4-9.

**Step 1-2 — Coverage matrix and pair selection:** Before this ticket: 34 entries, 20/120 raw pairs
(16.7%), 14/66 populated-only pairs (21.2%). Selected 21 new populated-set pairs prioritizing (a)
conflict-module factions likely to meet in combat (`bandit_company`, `goblin_warband`, `orc_clan`,
`wild_beast_pack`, `undead_remnants`, `swamp_tribe`), (b) economy-module factions (`merchant_league`,
`arcane_circle`, `spirit_court`, `forest_wardens`, `hero_guild`), authored bidirectionally except
`neutral`'s AC#3 entry (one direction only, per plan).

**Step 3 — Authored content (final state):** 75 entries, 41 undirected pairs. Populated-only basis:
**34/66 (51.5%)**, exceeding the 33+/66 (50%+) target. Raw-120 basis: 41/120 (34.2%), reported for
comparison to P2-D's original framing (not the gating number, per UQ-1's resolution). `neutral`'s
first-ever entry (`neutral_to_town_council`) uses `axes["hostility"] = "none"` as required.

**Step 4 — Behavior-risk verification (mandatory, both consumers checked independently):**
16 of the 21 new pairs have a source faction without a `perspectives.yaml` entry and required
per-pair delta computation for both consumers. Full delta table (alignment_bucket = legacy
`is_hostile()`/`combat_rewards.py` fallback; legacy_engine_bucket = legacy `legality.py`
Friendly-Fire fallback; new = post-authoring `is_hostile_compat()` result, which both consumers
now share once the relationship gate is True):

| Pair (source→target) | align_bucket(s→t) | legacy_bucket(s,t) | new hostile | combat_rewards delta | legality Friendly-Fire delta | Co-present world(s) |
|---|---|---|---|---|---|---|
| bandit_company→wild_beast_pack | invader/wild | MONSTER_HORDE/MONSTER_HORDE | True | none (True→True) | **illegal→legal** | dungeon_crawl |
| orc_clan→wild_beast_pack | rival/wild | MONSTER_HORDE/MONSTER_HORDE | True | **False→True** | **illegal→legal** | resource_dense_basin, frontier_extended, frontier_marches |
| bandit_company→goblin_warband | invader/invader | MONSTER_HORDE/MONSTER_HORDE | True | **False→True** | **illegal→legal** | dungeon_crawl |
| bandit_company↔orc_clan | invader/rival | MONSTER_HORDE/MONSTER_HORDE | True | none (True→True) | **illegal→legal** | crowded_frontier, frontier_extended, frontier_marches |
| bandit_company→undead_remnants | invader/invader | MONSTER_HORDE/MONSTER_HORDE | True | **False→True** | **illegal→legal** | dungeon_crawl |
| bandit_company→swamp_tribe | invader/rival | MONSTER_HORDE/MONSTER_HORDE | True | none (True→True) | **illegal→legal** | frontier_marches |
| orc_clan→undead_remnants | rival/invader | MONSTER_HORDE/MONSTER_HORDE | True | none (True→True) | **illegal→legal** | frontier_extended, frontier_marches |
| orc_clan→swamp_tribe | rival/rival | MONSTER_HORDE/MONSTER_HORDE | True | **False→True** | **illegal→legal** | frontier_marches |
| spirit_court→merchant_league | neutral/neutral | NEUTRAL/NEUTRAL | False | none (False→False) | none (illegal→illegal) | frontier_extended |
| arcane_circle→merchant_league | neutral/neutral | NEUTRAL/NEUTRAL | False | none (False→False) | none (illegal→illegal) | generated_frontier_3_42 |
| spirit_court↔arcane_circle | neutral/neutral | NEUTRAL/NEUTRAL | False | none (False→False) | none (illegal→illegal) | inert (no world co-populates) |
| forest_wardens→hero_guild | defender/defender | HERO_GUILD/HERO_GUILD | False | none (False→False) | none (illegal→illegal) | inert (no world co-populates) |
| forest_wardens→merchant_league | defender/neutral | HERO_GUILD/NEUTRAL | False | none (False→False) | **legal→illegal** | frontier_extended |
| neutral→town_council | neutral/defender | NEUTRAL/TOWN_COUNCIL | False | none (False→False) | **legal→illegal** | universal fallback ID; no world assigns "neutral" as a populated faction |

**Findings:** The `combat_rewards.py`/`is_hostile_compat()` delta (alignment_bucket-based) and the
`legality.py` Friendly-Fire delta (legacy_engine_bucket-based) are confirmed genuinely independent,
exactly as the plan anticipated: 4 pairs flip only the `combat_rewards.py`-relevant hostility value
(`orc_clan→wild_beast_pack`, `bandit_company→goblin_warband`, `bandit_company→undead_remnants`,
`orc_clan→swamp_tribe`), while 9 pairs flip the `legality.py` Friendly-Fire verdict even where the
`combat_rewards.py` delta shows "no change" (e.g. `bandit_company↔orc_clan`, where `is_hostile()`
already agreed with the new value, but the raw `legacy_engine_bucket` comparison did not). This is
the exact divergence class the plan's Anti-Drift Notes flagged as "the critical gap in an earlier
draft" — confirmed real, not hypothetical, and now covered by explicit per-pair tests.

**Intentional-change classification (mirroring `COMB-280`'s disclosure style):** the 9
same-`legacy_engine_bucket` MONSTER_HORDE pairs flipping Friendly-Fire illegal→legal is the
intended "encounter variety" outcome this ticket set out to produce — these monster-tier factions
could never legally fight each other before (blocked purely by sharing a legacy bucket), and now
can once a relationship record establishes real hostility between them. The 2 legal→illegal flips
(`forest_wardens→merchant_league`, `neutral→town_council`) are the inverse and equally intentional:
newly-declared non-hostile allies now correctly receive Friendly-Fire protection. No unattributable
drift was found — every flip traces cleanly to an authored relationship record.

**World co-presence (item 3/4):** All 6 worlds with a co-present flip pair (`dungeon_crawl`,
`resource_dense_basin`, `frontier_extended`, `crowded_frontier`, `frontier_marches`) are present in
`tests/simulation_quality/fixtures/grade_anchors.json`'s anchor set as of this session — the
anchor set was expanded from 4 to 16 world directories by sibling tickets completed earlier the
same day (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` and others), so the plan's premise that
`make evaluate-full` "only covers 4 templates" is now stale relative to the corpus. Only
`generated_frontier_3_42` remains unanchored, and it has no exclusive co-presence for any flip pair
(its `arcane_circle+merchant_league`/`bandit_company+orc_clan` co-presences are also covered by
other anchored worlds). This is a Deviation from the plan's stated risk profile (in the corpus's
favor, not against it) — recorded in `staging_artifacts/.../plan.md`'s Deviations section.
Despite this, per-pair unit/integration tests were still added exactly as the plan required (fast,
directly assert the real verdict, not dependent on anchor-set composition remaining stable).

**Item 5 (`test_combat_rewards.py` unaffected):** Confirmed. That suite's entities use raw
`Faction` enum literals with no `faction_id` property, so `get_faction_id_str()` falls back to the
lowercased enum name (`"hero_guild"`, `"monster_horde"`, `"neutral"`). `"monster_horde"` is not a
real catalog faction ID and none of this ticket's new entries add a relationship record with
`target_faction: "monster_horde"`, so the perspective/relationship lookup for that literal string
still fails to resolve and the legacy fallback path inside `project_relation()` is unchanged.
Verified by running the suite unmodified (see Test Summary) — passes.

**Step 6 — Regression results:** `make evaluate-full` (real engine re-run, per Risk #4 correction):
**610 pillars checked, 0 regressions, 0 missing**, across all 16 anchored world directories
including every world identified as co-populating a flip pair above. `make world-validate
WORLD=sandbox_world`: 0 errors (3 pre-existing unrelated warnings about `faction_tension_overrides`/
`generation_seed`/`modules` top-level sections, not `CAT-REL-012`).

**Step 7:** Parity ledger `COMB-294` added to `docs/parity_ledger/combat_movement.yaml`
(status `verified`, priority `P0`, cross-referencing `COMB-280`), documenting the two-consumer
divergence and the verified per-pair delta findings above.

**Step 8 (`audit_fix_plan.md`):** P2-D section updated — status UNVERIFIED → resolved,
coverage 34/66 populated-only (51.5%) / 41/120 raw (34.2%), stale `Files:` path corrected.

## Test Summary
New tests:
- `tests/integration/combat/test_relation_combat_integration.py` — 2 new parametrized tests
  (`test_new_catalog_pair_is_hostile_compat_delta`, `test_new_catalog_pair_legality_friendly_fire_delta`),
  16 cases each (32 new test invocations), covering every non-perspective-source new pair for both
  consumers independently. All pass (35 total tests in file pass).
- `tests/unit/content/test_faction_relationships_coverage.py` (new file, 6 tests): coverage
  threshold, `neutral` presence, `neutral` hostility-safety guard, axis/faction referential
  integrity, populated-set prioritization, and `test_new_pair_changes_legality_friendly_fire_verdict`
  (real `LegalityServiceV2.verify_attack_legality()` call for `bandit_company→orc_clan`, the
  `COMB-294` `test_path` target). All 6 pass.

Regression suites run (all pass, 0 failures):
- `pytest tests/unit/content/ -k "faction_relationship or usage_matrix or reference_graph or layered_catalog or resolvers" -q` — 138 passed
- `pytest tests/unit/content_semantics/ tests/unit/engine/test_combat_relation_projection.py tests/integration/combat/ tests/unit/combat/test_combat_rewards.py tests/unit/quest/test_quest_relation_projection.py -q` — 72 passed
- `pytest tests/unit/faction/ -q` — 117 passed
- `pytest tests/architecture/test_enum_migration_report.py tests/architecture/test_legacy_enum_usage_boundaries.py -q` — 11 passed
- `pytest tests/unit/world/test_regional_consequences.py -q` — 11 passed
- `make world-validate WORLD=sandbox_world` — 0 errors
- `make evaluate-full` — 610 pillars, 0 regressions, 0 missing

## Files Changed
- `data/content/social/faction_relationships.yaml` — 41 new entries authored (34→75 total, 20→41
  undirected pairs)
- `tests/integration/combat/test_relation_combat_integration.py` — added 2 parametrized tests
  (32 cases) for the is_hostile_compat()/legality.py Friendly-Fire deltas
- `tests/unit/content/test_faction_relationships_coverage.py` — new file, 6 tests
- `docs/parity_ledger/combat_movement.yaml` — added `COMB-294`
- `docs/plans/audit_fix_plan.md` — P2-D section and Summary Table row updated
- `tickets/inprogress/TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS.md` — this file (Implementation
  Notes, Related Code Areas correction, AC checkboxes)
- `staging_artifacts/TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS/plan.md` — Deviations section
  added

## Completion Summary
Expanded `data/content/social/faction_relationships.yaml` from 34 to 75 entries (20 to 41 undirected
pairs), reaching 34/66 (51.5%) coverage on the populated-only basis — the correct denominator per
this ticket's own investigation, since 3 of the original 16 catalog factions (`moon_cult`,
`dwarven_mine_clan`, `dragon_cult`) are never populated by any current world module and relationships
between never-co-present factions are low-value/unverifiable. `neutral` (the universal fallback
faction id) got its first-ever entry, deliberately `hostility: "none"` given its unbounded blast
radius.

Investigation found this ticket's original premise wrong: the file is not inert content, it's a live
input to two genuinely independent consumers — `CombatRewardClassificationService` (via
`is_hostile_compat()`/`alignment_bucket`) and `LegalityServiceV2.verify_attack_legality()`'s Friendly
Fire check (via its own separate raw-enum `legacy_engine_bucket` fallback). Architecture review caught
this gap on its first pass (the plan initially only modeled one consumer) and required one revision
cycle before approving. Implementation confirmed the risk was real: the reward-classification delta
flipped for 4 pairs while the legality delta flipped for 11 pairs (9 illegal→legal, 2 legal→illegal)
— genuinely divergent outcomes, not the same signal twice. Every flip was traced to a specific
authored relationship record with no unattributable drift, so no escalation was needed. 41 tests
directly exercise both deltas (including a real `verify_attack_legality()` call, the `COMB-294`
parity-ledger `test_path` target); the full 349-test regression sweep plus `make evaluate-full` (a
real engine re-run, not the diff-only `--dry-run`) both pass clean at 610 pillars / 0 regressions.

Also corrected two pre-existing errors found along the way, not left silently propagated: the
ticket's own `Related Code Areas` wrongly cited `src/engine/faction_decision.py` (which never reads
this file) — fixed to the real consumers (`src/content_semantics/faction.py`/`relation.py` via
`src/engine/legality.py`/`combat_rewards.py`); and `docs/plans/audit_fix_plan.md`'s P2-D item is now
marked RESOLVED with the actual measured coverage numbers.

**No material gaps deferred.** The two behavioral risks investigation flagged (the dual-consumer
divergence, and the `neutral`-faction blast radius) were both fully resolved within this ticket's own
scope, not punted to a follow-up. No new gap was discovered during implementation that needed a
separate ticket.
