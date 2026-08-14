---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS
artifact_type: plan
tags: [simulation-quality, faction]
---

# Implementation Plan — TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS

## Summary

This ticket expands `data/content/social/faction_relationships.yaml` coverage, but the
investigation established that this file is **not inert content** — it is a live input to
`RelationProjectionService.project_relation()` and `FactionSemanticsService.is_hostile_compat()`,
which gate `LegalityServiceV2.verify_attack_legality()` (Friendly Fire law) and
`CombatRewardClassificationService.classify_defeated_target()` (parity ledger `COMB-280`, P0).
For the 10 of 16 factions with no `perspectives.yaml` entry, adding a relationship record with an
elevated `hostility` value unconditionally flips that pair's `is_hostile_compat()` result away from
today's coarser legacy `alignment_bucket` fallback. This plan therefore treats the ticket as a
**content-authoring change with a mandatory behavior-verification step**, not pure content: it
resolves the ticket's own open denominator question, restricts new pairs to gameplay-relevant
(populated) factions, requires a targeted regression test for every newly-affected non-perspective
pair, replaces the ticket's insufficient `--dry-run` verification with a real engine re-run plus
targeted unit/integration tests, adds a new parity ledger entry closing the gap the investigation
found, and corrects the ticket's own wrong "Related Code Areas" so the implementer does not waste
time looking for catalog usage in `src/engine/faction_decision.py` (which never reads this file).

**Resolved decisions (see Unresolved Questions section for what is explicitly NOT decided here):**

- **UQ-1 (denominator):** Graded against the **populated-only 66-pair basis** (currently 14/66,
  21.2%; target 33+/66, i.e. 50%+). Reasoning: the ticket's own stated goal is "avoid an
  all-`neutral`-default outcome" and "improve encounter variety" for gameplay that actually
  happens — pairs between `moon_cult`/`dwarven_mine_clan`/`dragon_cult` (zero module path to
  population today) cannot improve any world's actual encounter variety no matter how many are
  added. The raw-120 percentage (currently 20/120, 16.7%) is still computed and reported in the
  ticket's Implementation Notes for direct comparison to P2-D's original framing, but it is not
  the gating number for AC#1.
- **Hostility-flip risk:** every new pair is restricted to combinations of the 12 populated
  factions (`town_council, merchant_league, wild_beast_pack, goblin_warband, bandit_company,
  forest_wardens, spirit_court, orc_clan, undead_remnants, arcane_circle, swamp_tribe, hero_guild`)
  plus `neutral`'s single required entry (AC#3). For every new pair whose source faction is one of
  the 10 without a `perspectives.yaml` entry (`town_council, neutral, bandit_company,
  forest_wardens, orc_clan, dwarven_mine_clan, moon_cult, arcane_circle, dragon_cult,
  spirit_court`), Step 4 below requires a targeted unit test proving the actual
  `is_hostile_compat()` delta versus the legacy `alignment_bucket` fallback, plus a real engine
  re-run (`make evaluate-full`, not `--dry-run`) and an anchored-world co-presence check.
- **`neutral`'s first entry:** must use `axes["hostility"] = "none"` (an existing, already-used
  literal in the catalog — confirmed by direct grep, not invented) — never `"high"`/`"medium"`/any
  `*_contextual` variant that resolves to `"enemy"`/`"threat"` for the universal fallback faction
  ID. This is a hard requirement, not a suggestion.
- **New parity ledger entry:** `docs/parity_ledger/combat_movement.yaml`, new ID `COMB-294`
  (confirmed next available — last existing ID in that file is `COMB-293`), documenting "catalog
  relationship coverage → legality/reward outcome" as its own tracked concern, cross-referencing
  `COMB-280`.
- **Corrected code areas:** the ticket's "Related Code Areas" citing `src/engine/faction_decision.py`
  is wrong (confirmed: that module never reads `faction_relationships.yaml`). The real consumers,
  used throughout this plan, are `src/content_semantics/faction.py`,
  `src/content_semantics/relation.py`, `src/engine/legality.py`, `src/engine/combat_rewards.py`,
  and `src/content/repository.py`/`src/content/validator.py`/`src/content/resolver.py` at the
  content-loading layer.

## Steps

### Step 1 — Establish and document the coverage matrix
**Files:** `staging_artifacts/TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS/` (working notes;
final numbers go in the ticket's Implementation Notes in Step 8), no source files touched.
**Change:** Re-derive (or reuse investigation.md's already-verified numbers) the exact set of
covered vs. uncovered pairs on both bases:
- Raw 120-pair basis: 20/120 covered today (16.7%).
- Populated-only 66-pair basis (`C(12,2)`, the 12 populated factions listed above): 14/66 covered
  today (21.2%).
List explicitly which of the 66 populated-only pairs are currently uncovered — this is the
candidate list Step 3 draws new entries from. Do not include `moon_cult`, `dwarven_mine_clan`, or
`dragon_cult` in this candidate list (out of the populated set; new pairs among them would pad the
raw-120 number without satisfying AC#1's populated-only gate).
**Do NOT touch:** No file writes in this step — this is a documentation/derivation step whose
output feeds Step 3's authoring list and Step 8's Implementation Notes.
**Verify:** Manual cross-check against investigation.md's Current Behavior section (20/120,
14/66 counts already independently confirmed there); no automated test for this step alone.

### Step 2 — Select the specific new pairs to author (populated-set priority)
**Files:** none (planning artifact only — the selected list becomes Step 3's authoring input)
**Change:** From Step 1's uncovered populated-only pairs, select at least 19 new pairs (to move
14/66 → 33+/66) prioritizing, in this order: (a) conflict-module factions likely to actually meet
in combat per the module table in `stored_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/investigation.md`
(`bandit_company`, `goblin_warband`, `orc_clan`, `wild_beast_pack`, `undead_remnants` vs.
`town_council`/`forest_wardens`/`hero_guild`), (b) economy-module factions
(`merchant_league`, `town_council`, `swamp_tribe`), (c) remaining populated-set pairs not yet
covered. Author both directions per pair (matching the existing file's convention) unless a
one-directional relationship is clearly correct (e.g. asymmetric predator/prey framing already
used for `wild_beast_pack`). For every selected pair, note which factions have a
`perspectives.yaml` entry as source (`hero_guild, wild_beast_pack, goblin_warband,
merchant_league, undead_remnants, swamp_tribe`) — pairs where the *source* has a perspective are
lower-risk (perspective labels win over relationship axes in `project_relation()`); pairs where the
source is one of the 10 non-perspective factions are the ones Step 4's targeted tests must cover.
**Do NOT touch:** Do not select any pair involving `moon_cult`, `dwarven_mine_clan`, or
`dragon_cult` in this step (reserved out of scope per Step 1). Do not silently exceed the 33-pair
minimum by padding with these three factions' pairs to look more complete.
**Verify:** The selected list, cross-tabulated with perspective-vs-non-perspective source, is
recorded in the ticket's Implementation Notes (Step 8) before Step 3 authors anything.

### Step 3 — Author the new relationship entries and the `neutral` entry
**Files:** `data/content/social/faction_relationships.yaml`
**Change:** Add new entries following the existing `FactionRelationshipDefinition` schema
(`extra="forbid"`: `id, source_faction, target_faction, relationship_model, axes: Dict[str,
str]`), matching `tickets/done/TCK-20260627-P2D-FACTION-RELS.md`'s established conventions:
snake_case `relationship_model` naming, `# STATE: ADDITIONAL` comment above each new entry (not
`REDESIGNED-CORE`/`LEGACY-EXPORT`, which are reserved for pre-existing entries), only `axes` keys
from the 11 registered IDs in `data/content/foundation/relationship_axes.yaml` (`hostility, trust,
fear, respect, territorial_conflict, trade_affinity, resource_competition, religious_conflict,
ancient_grudge, kinship, debt` — do not invent a 12th without registering it first, and this ticket
has no stated need to). Before writing, grep the existing 34 entries to confirm no
`(source_faction, target_faction)` duplicate is created (the schema does not enforce
pair-uniqueness — a silent duplicate would create a first-match-wins ordering bug).
Add `neutral`'s first-ever entry (at least one, either direction) with `axes["hostility"] =
"none"` explicitly — this is a hard requirement per this plan's resolved decision above, not an
implementer's free choice. Pick a target faction from the 12-populated set with a plausible
narrative fit (implementer's discretion within this constraint); do not use any axis value that
resolves to `"enemy"`/`"threat"` in `RelationProjectionService.project_relation()`.
**Do NOT touch:** `data/content/social/perspectives.yaml`, `data/content/foundation/relationship_axes.yaml`
(no new axis IDs needed), `data/content/social/factions.yaml` (no new factions).
**Verify:** `make world-validate WORLD=sandbox_world` (catalog validator, `CAT-REL-012`) passes
with 0 referential-integrity errors; `tests/unit/content/test_faction_relationships_coverage.py`
(new, Step 5) asserts ≥33/66 populated-only coverage and `neutral`'s presence.

### Step 4 — Behavior-risk verification for non-perspective-source pairs (mandatory, new AC)
**Files:**
- New test additions to `tests/integration/combat/test_relation_combat_integration.py` (extend —
  use its existing `create_relation_entity(e_id, pos, faction_id, faction_enum, role)` helper and
  the pattern already established by `test_integration_perspective_hostility` /
  `test_integration_legacy_fallback`, which build entities with **both** a catalog `faction_id`
  string and a raw legacy `Faction` enum value and call `LegalityServiceV2.verify_attack_legality`
  directly)
- Read-only cross-reference: `data/worlds/*/resolved/world.resolved.yaml` (per-entity `faction_id`
  values, to determine which worlds actually populate both factions of a given new pair) and the
  module→populated-faction table in
  `stored_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/investigation.md`
- `data/content/social/factions.yaml` (read-only, for each faction's `alignment_bucket` **and**
  `legacy_engine_bucket` fields — both are needed, they gate two different consumers, see below)

**Change:** This step has **two consumers with genuinely different pre-change fallback mechanisms**
— they must be verified separately, not treated as one delta. Both were confirmed by direct read of
`src/engine/legality.py:241-261`, `src/content_semantics/faction.py:160-213` (`is_hostile_compat`),
and `src/worldassembly/resolver.py:954-1023`:

- **`combat_rewards.py`'s consumer** (`CombatRewardClassificationService.classify_defeated_target()`)
  calls `FactionSemanticsService.is_hostile_compat()` directly and unconditionally. Internally,
  `is_hostile_compat()` computes its own gate (`has_perspective` OR `has_relationship` for the exact
  directed `(source, target)` pair); when the gate is False it falls to `self.is_hostile(source,
  target)`, which is **`alignment_bucket`-based** (`invader` vs non-`invader`, a `factions.yaml`
  catalog attribute).
- **`legality.py`'s consumer** (`LegalityServiceV2.verify_attack_legality`, Friendly Fire step,
  lines 241-261) computes its **own separate** `has_clean` flag using the *identical* gate
  expression (`has_perspective` OR `has_relationship` for the exact directed pair — the two gates
  flip in lockstep). But its "gate is False" branch is **not** `is_hostile()` at all — it directly
  compares `attacker.identity.faction == target.identity.faction`, the raw legacy 4-value `Faction`
  IntEnum field (`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/`NEUTRAL`). For any catalog-driven
  entity this field is set once at world-assembly time
  (`src/worldassembly/resolver.py:954,995,1023`) to `Faction[faction_defn.legacy_engine_bucket]` —
  a **different** `factions.yaml` attribute (`legacy_engine_bucket`) than `alignment_bucket`, and
  the two need not agree (two factions can share a `legacy_engine_bucket` while having different
  `alignment_bucket` values, or vice versa). So `legality.py`'s pre-change Friendly-Fire verdict for
  a gate-False pair is **"illegal iff `legacy_engine_bucket(source) == legacy_engine_bucket(target)`"**
  — a materially different computation from the `alignment_bucket`-based one used for the
  `combat_rewards.py` delta. When the gate flips True (Step 3 adds a relationship record for that
  exact directed pair), `legality.py` switches to calling `is_hostile_compat()` itself and treats the
  attack as **illegal iff NOT hostile** — the same relation-projection value already being computed
  for the `combat_rewards.py` delta below.

For every new pair from Step 3 whose *source* faction is one of the 10 without a
`perspectives.yaml` entry (`town_council, neutral, bandit_company, forest_wardens, orc_clan,
dwarven_mine_clan, moon_cult, arcane_circle, dragon_cult, spirit_court`), compute **both** deltas
(both directions if both were authored):

1. **`combat_rewards.py` / `is_hostile_compat()` delta**: legacy result = `is_hostile()`,
   `alignment_bucket == "invader"` vs. not (record both factions' `alignment_bucket`). New result =
   the authored `axes["hostility"]` value mapped through `RelationProjectionService.project_relation()`'s
   label rules (`"high"`/`"medium"` → unconditional `"enemy"` → hostile True; `*_contextual` →
   context-dependent; else neutral/False). Add an explicit unit/integration test asserting the new
   `is_hostile_compat()` result for that directed pair.
2. **`legality.py` Friendly-Fire delta** (separate check, new in this revision): legacy result =
   `FRIENDLY_FIRE_ILLEGAL` iff `legacy_engine_bucket(source) == legacy_engine_bucket(target)` (record
   both factions' `legacy_engine_bucket`). New result = `FRIENDLY_FIRE_ILLEGAL` iff `not
   is_hostile_compat(source, target, context)` (same hostility value as item 1's new result). Add an
   explicit test calling `LegalityServiceV2.verify_attack_legality(attacker, target, state)` directly
   — built via `create_relation_entity` with the real catalog `faction_id` string on each entity AND
   `faction_enum` set to that faction's actual `legacy_engine_bucket` value (not an arbitrary
   literal) — asserting the real legal/illegal verdict and `ReasonCode` for that directed pair.
   **A pair can show "no change" under item 1 while item 2's verdict still flips (or vice versa) —
   they are independent checks; do not treat item 1 alone as sufficient.** If Step 1's/Step 2's
   pair list contains two factions that already share a `legacy_engine_bucket` but differ in
   `alignment_bucket` (or vice versa), prioritize that pair as an explicit regression case to make
   the two-mechanism divergence visible rather than assumed.
3. Cross-reference `data/worlds/*/resolved/world.resolved.yaml` faction_id sets: for each new pair,
   list which (if any) worlds have **both** factions populated simultaneously. Only those worlds are
   actually at risk of a combat-legality/reward-classification change. For any such world, document
   in Implementation Notes (Step 8) whether the legacy result and new result differ for **either**
   consumer (items 1 and 2), and if they differ, explicitly state this is an intentional, documented
   behavior change (mirroring `COMB-280`'s existing `divergence_note` style: "X now gives Y instead
   of Z") rather than an unnoticed side effect. If a pair has no world with both factions populated,
   state that explicitly too (change is currently inert for the corpus, though it will affect any
   future world composing those factions together).
4. **`make evaluate-full` world-coverage gap (new in this revision):** `make evaluate-full` only
   re-runs the 4 world templates present in `tests/simulation_quality/fixtures/grade_anchors.json`'s
   anchor set (`sandbox_world`, `dungeon_crawl`, `urban_political`, `simq_routing_test`) — it does
   **not** exercise the other world directories under `data/worlds/` (e.g. `crowded_frontier`,
   `frontier_marches`, `hero_guild_routing`, `unit_faction_tension`, and the rest, including several
   multi-faction stress/isolation worlds built by sibling tickets today). For any new pair where
   item 3's cross-reference finds **both factions populated together** in one of these
   non-anchored world directories, add a specific, narrow integration/unit test that exercises that
   world's actual `LegalityServiceV2`/`CombatRewardClassificationService` behavior for that faction
   pair — construct entities using that world's real `faction_id`/`legacy_engine_bucket`/
   `alignment_bucket` values and assert the real verdict, a schema/coverage check is not sufficient
   evidence for these worlds. Do not rely on `make evaluate-full`'s 4-template coverage as evidence
   for any pair whose only co-presence is in a non-anchored world.
5. Confirm `tests/unit/combat/test_combat_rewards.py` still passes unmodified — investigation
   confirmed this test uses legacy `Faction` enum literals (`HERO_GUILD`/`MONSTER_HORDE`/`NEUTRAL`)
   whose `get_faction_id_str()` fallback (lowercased enum name) does not match any real catalog
   faction ID, so it should stay on the legacy path regardless of new catalog entries — verify this
   holds after authoring, do not assume it.

**Do NOT touch:** `src/content_semantics/faction.py`, `src/content_semantics/relation.py`,
`src/engine/legality.py`, `src/engine/combat_rewards.py` — this step verifies their *behavior*
against new data, it does not modify their logic. Do not modify
`tests/unit/combat/test_combat_legality_contract.py`'s existing raw-enum-literal tests — the new
catalog-aware legality tests belong in `test_relation_combat_integration.py`, which already has the
dual `faction_id`/`faction_enum` helper needed; the two files serve different, non-overlapping
conventions.
**Verify:** New targeted test(s) pass for both the `combat_rewards.py`/`is_hostile_compat()` delta
(item 1) and the separate `legality.py` Friendly-Fire delta (item 2), for every affected pair;
new per-world targeted test(s) pass for every non-anchored-world co-presence found (item 4);
`tests/unit/combat/test_combat_rewards.py` passes unmodified; Implementation Notes documents the
per-pair, per-consumer legacy-vs-new delta table and the world co-presence findings (anchored and
non-anchored).

### Step 5 — Add the coverage/guard unit tests
**Files:** `tests/unit/content/test_faction_relationships_coverage.py` (new file)
**Change:** Add the tests specified in test_plan.md:
1. `test_faction_relationships_coverage_meets_threshold` — counts unique undirected pairs among the
   12 populated factions and asserts ≥33/66 (50%+); also computes and asserts/reports the raw
   120-pair percentage for visibility (not gated, per this plan's UQ-1 resolution).
2. `test_neutral_faction_has_explicit_relationship` — `neutral` appears as `source_faction` or
   `target_faction` in ≥1 entry.
3. `test_new_relationship_entries_reference_valid_axes_and_factions` — every entry's
   `source_faction`/`target_faction` resolves in `factions.yaml`, every `axes` key resolves in
   `relationship_axes.yaml`.
4. `test_neutral_first_relationship_is_not_high_hostility` — asserts `neutral`'s entry/entries never
   set `axes["hostility"]` to `"high"`/`"medium"`/any `*_contextual` value.
5. `test_new_populated_faction_pairs_prioritized` (optional but included) — asserts a majority of
   newly-added pairs (vs. the original 20) involve only the 12-populated set, not
   `moon_cult`/`dwarven_mine_clan`/`dragon_cult`.
6. `test_new_pair_changes_legality_friendly_fire_verdict` (new, required — this is what makes
   `COMB-294`'s `test_path` citation accurate, see Step 7): pick one representative pair from Step
   4's item 2 list (a non-perspective-source pair whose `legality.py` Friendly-Fire delta actually
   flips old→new) and, using the same `create_relation_entity`-style construction Step 4 uses in
   `tests/integration/combat/test_relation_combat_integration.py` (import/reuse that helper or an
   equivalent local one), call `LegalityServiceV2.verify_attack_legality(attacker, target, state)`
   directly and assert the real new verdict + `ReasonCode`. This does not need to duplicate every
   pair Step 4 already covers — its purpose is to make this coverage-test file itself exercise a
   genuine legality-path outcome, not just schema/counts, so that a single `test_path` field can
   honestly represent "catalog coverage determines combat-legality outcomes." Do not substitute a
   call to `is_hostile_compat()` alone here — the entry is specifically about the
   `LegalityServiceV2` gate, so the test must call `verify_attack_legality` itself.
**Do NOT touch:** existing test files in `tests/unit/content/` other than adding this new file;
do not modify `tests/unit/content/test_content_usage_matrix.py`,
`tests/unit/content/test_reference_graph.py`, `tests/unit/content/test_layered_catalog.py`,
`tests/unit/content/test_resolvers.py` — these are regression checks to run (Step 6), not to edit.
**Verify:** `pytest tests/unit/content/test_faction_relationships_coverage.py -q` — all pass,
including the new `test_new_pair_changes_legality_friendly_fire_verdict` (item 6).

### Step 6 — Run the full regression surface (replaces ticket's insufficient `--dry-run` check)
**Files:** none changed; this is a verification-only step.
**Change:** Run, in order:
```
pytest tests/unit/content/ -k "faction_relationship or usage_matrix or reference_graph or layered_catalog or resolvers" -q
pytest tests/unit/content_semantics/ tests/unit/engine/test_combat_relation_projection.py \
       tests/integration/combat/ tests/unit/combat/test_combat_rewards.py \
       tests/unit/quest/test_quest_relation_projection.py -q
pytest tests/unit/faction/ -q
pytest tests/architecture/test_enum_migration_report.py tests/architecture/test_legacy_enum_usage_boundaries.py -q
pytest tests/unit/world/test_regional_consequences.py -q
make world-validate WORLD=sandbox_world
make evaluate-full
```
Per investigation Risk #4, `make evaluate --dry-run` is diff-only against calibration JSON and
cannot detect a legality/reward-classification change from new catalog content — it must NOT be
used as the "0 regressions" signal for this ticket's AC#4. `make evaluate-full` (real engine
re-run) is required instead. If `make evaluate-full` surfaces any grade drift, document it plainly
in Implementation Notes: either (a) trace it to Step 4's identified intentional pair changes and
confirm the drift is expected/correctly scoped, or (b) treat it as a genuine regression requiring
the new entries to be revised before this ticket can close (do not silently ignore, per ticket
AC#4's own "or resolved" clause).
**Do NOT touch:** No source or test files are modified in this step (verification only). If drift
requires revision, that revision happens by returning to Step 3, not by editing test expectations
to match unexpected output.
**Verify:** All listed suites pass; `make evaluate-full` output reviewed and any drift resolved or
explicitly documented as intentional.

### Step 7 — Add the new parity ledger entry
**Files:** `docs/parity_ledger/combat_movement.yaml`
**Change:** Add a new entry with `id: COMB-294` (confirmed next available — last existing ID in
file is `COMB-293`):
```yaml
- id: COMB-294
  text: Faction relationship catalog coverage determines combat-legality and reward-classification
    outcomes for faction pairs without a perspectives.yaml override.
  status: verified
  priority: P0
  legacy_evidence: null
  v2_evidence: '`data/content/social/faction_relationships.yaml` entries are read by
    `RelationProjectionService.project_relation()` (`src/content_semantics/relation.py`) and
    `FactionSemanticsService.is_hostile_compat()` (`src/content_semantics/faction.py`), which gate
    `LegalityServiceV2.verify_attack_legality()` (`src/engine/legality.py`, Friendly Fire law) and
    `CombatRewardClassificationService.classify_defeated_target()` (`src/engine/combat_rewards.py`,
    see COMB-280). For factions without a perspectives.yaml entry, a new relationship entry flips
    each consumer''s own gate (has_perspective OR has_relationship for the exact directed pair) from
    False to True. The two consumers diverge on the "gate False" fallback: is_hostile_compat()
    (combat_rewards.py''s path) falls back to is_hostile(), alignment_bucket-based; legality.py''s
    own Friendly Fire step computes a separate has_clean flag with the identical gate expression but
    falls back to raw attacker.identity.faction == target.identity.faction (legacy_engine_bucket-based,
    a different factions.yaml attribute than alignment_bucket) when the gate is False, then switches
    to calling is_hostile_compat() itself once the gate flips True. Both fallback mechanisms and the
    post-flip convergence are verified per new pair.
    TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS.'
  proof_type: regression
  test_path: tests/unit/content/test_faction_relationships_coverage.py
  divergence_note: null
  support_boundary: null
```
Mark `priority: P0` because it gates the same combat-legality/reward path as `COMB-280` (P0).
**Do NOT touch:** any other existing entry in `combat_movement.yaml`, including `COMB-280` itself
(read-only cross-reference, not edited).
**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/combat_movement.yaml'))"`
parses without error; entry conforms to `docs/parity_ledger/schema.json` (`id` pattern
`^[A-Z]+-[0-9]{3}$`, required fields present).

### Step 8 — Update the ticket and `audit_fix_plan.md`
**Files:**
- `tickets/inprogress/TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS.md` — fill Implementation
  Notes (coverage matrix from Step 1, selected-pairs list from Step 2, per-pair legacy-vs-new
  delta table and anchored-world findings from Step 4, `make evaluate-full` result from Step 6),
  Test Summary, Files Changed. Also correct "Related Code Areas" in this same file to remove
  `src/engine/faction_decision.py` and list the real consumers (see Summary above).
- `docs/plans/audit_fix_plan.md` — update P2-D section: status UNVERIFIED → resolved, new
  populated-only coverage percentage (33+/66, 50%+) and raw-120 percentage reported alongside,
  mirroring P2-B/P2-C's resolution-note style. Also fix the stale `Files:` field (currently says
  `data/content/faction_relationships/`, a nonexistent directory — correct to
  `data/content/social/faction_relationships.yaml`). Update the Summary Table's P2-D row to match.
**Do NOT touch:** any other P2 section or Summary Table row in `audit_fix_plan.md`.
**Verify:** Manual review — ticket's Acceptance Criteria checkboxes all reflect true state;
`audit_fix_plan.md` P2-D section and Summary Table row are internally consistent.

### Step 9 — Docs index update
**Files:** none changed directly (tooling step)
**Change:** Run `make knowledge-index-update` because `docs/plans/audit_fix_plan.md` and
`docs/parity_ledger/combat_movement.yaml` were modified.
**Do NOT touch:** no manual doc edits in this step.
**Verify:** command exits 0.

## Scope Guards

- Do not touch `src/engine/faction_decision.py`, `src/domains/faction/diplomatic_state_machine.py`,
  or `MilitaryConflictPhase` — out of scope per the ticket, and confirmed by investigation to not
  even read `faction_relationships.yaml`.
- Do not touch `src/core/state.py` (`FactionState`) or `src/core/updates.py` (`FactionUpdate`) —
  runtime diplomacy state, a separate mechanism from this catalog file.
- Do not "fix" `docs/content/content_semantics_contract.md`'s stale "compile-time only" claim as
  part of this ticket — real gap, explicitly out of scope; leave for a follow-up doc-fix ticket.
- Do not add any new relationship pair involving `moon_cult`, `dwarven_mine_clan`, or `dragon_cult`
  — zero module path to population today; would pad the raw-120 number without satisfying the
  populated-only AC gate.
- Do not invent a new `axes` key not already in `data/content/foundation/relationship_axes.yaml`.
- Do not create a duplicate `(source_faction, target_faction)` entry — check the existing 34 first.
- Do not give `neutral`'s first entry any hostility value other than `"none"`.
- Do not treat `make evaluate --dry-run` passing as sufficient evidence of "0 regressions" — it is
  diff-only against calibration JSON and does not re-run the engine.
- Do not implement any new faction-interaction engine logic — this is pure catalog content plus
  verification tests, no production code changes.
- Do not expand this ticket into fixing any downstream bug the expansion surfaces — file a
  follow-up ticket per the ticket's own Out of Scope.

## Dependency Map

- Step 1 → Step 2 (candidate list needs the coverage matrix).
- Step 2 → Step 3 (authoring needs the selected pair list).
- Step 3 → Step 4 (behavior verification needs the actual authored entries).
- Step 3 → Step 5 (coverage tests need the actual final file content).
- Step 4 → Step 5's item 6 (`test_new_pair_changes_legality_friendly_fire_verdict` reuses the
  specific pair Step 4's item 2 already identified as flipping the `legality.py` Friendly-Fire
  verdict — do Step 4 first, or at least identify that pair before writing Step 5's item 6). The
  rest of Step 5 (items 1-5) depends only on Step 3, same as before.
- Step 4 + Step 5 → Step 6 (full regression run should happen after both are in place).
- Step 6 → Step 7 (parity entry documents the verified behavior; write it once behavior is confirmed).
- Step 7 → Step 8 (ticket Implementation Notes reference the parity entry ID).
- Step 8 → Step 9 (docs index update runs after doc edits land).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC#1: coverage reaches ≥50% (60+/120 raw, per ticket text) | Steps 1-3 (re-graded against populated-only 66-basis, 33+/66, per resolved UQ-1) | `test_faction_relationships_coverage_meets_threshold` |
| AC#2: conflict/economy factions prioritized, reasoning documented | Steps 2, 8 | Manual review of Implementation Notes; `test_new_populated_faction_pairs_prioritized` |
| AC#3: `neutral` has ≥1 explicit entry | Step 3 | `test_neutral_faction_has_explicit_relationship`, `test_neutral_first_relationship_is_not_high_hostility` |
| AC#4: `make evaluate --dry-run` exits 0 / drift documented | Step 6 (corrected to `make evaluate-full` per Risk #4) | `make evaluate-full` output review |
| AC#5: `audit_fix_plan.md` P2-D + Summary Table updated | Step 8 | Manual review |
| AC#6: `make knowledge-index-update` run | Step 9 | Command exit code |
| **New AC (this plan, not in original ticket):** every new pair whose source lacks a `perspectives.yaml` entry has targeted tests proving **both** its `combat_rewards.py`/`is_hostile_compat()` delta vs. legacy `alignment_bucket` fallback **and** its separate `legality.py` Friendly-Fire delta vs. legacy `legacy_engine_bucket` fallback, and any world-affecting change (anchored or non-anchored) is explicitly documented as inert or intentional | Step 4 | New test(s) extended in `test_relation_combat_integration.py` (items 1, 2, 4); `tests/unit/combat/test_combat_rewards.py` unchanged-pass (item 5) |
| **New AC (this plan):** `COMB-294`'s single `test_path` must itself exercise a real `LegalityServiceV2.verify_attack_legality()` outcome, not just schema/coverage counts | Step 5 (item 6) | `test_new_pair_changes_legality_friendly_fire_verdict` in `test_faction_relationships_coverage.py` |

## Anti-Drift Notes

- **The central hazard**: this file is read live, per-attack, by `is_hostile_compat()` — treat
  every new entry involving a non-perspective-source faction as a real behavior change candidate,
  not inert data, until Step 4's verification proves otherwise for each specific pair.
- **`legality.py` does NOT call `is_hostile_compat()` in its "gate is False" branch — this was the
  critical gap in an earlier draft of this plan.** `LegalityServiceV2.verify_attack_legality`
  (`src/engine/legality.py:241-261`) computes its own `has_clean` flag with the same gate expression
  `is_hostile_compat()` uses internally, but on "gate False" it falls back to raw
  `attacker.identity.faction == target.identity.faction` (the legacy 4-value `Faction` enum, driven
  by each faction's `legacy_engine_bucket` catalog attribute) — not to `is_hostile()`'s
  `alignment_bucket` comparison. A pair judged "no change" under the `alignment_bucket`-based
  `combat_rewards.py` delta can still flip `legality.py`'s actual Friendly Fire verdict once a new
  relationship record flips that pair's gate from False to True. Step 4 computes and tests these two
  deltas **separately** for every affected pair — never assume the `combat_rewards.py` delta result
  also describes `legality.py`'s behavior.
- **`make evaluate-full` only covers the 4 `grade_anchors.json` template worlds** (`sandbox_world`,
  `dungeon_crawl`, `urban_political`, `simq_routing_test`) — it is not evidence of "0 regressions"
  for any new pair whose only co-presence is in one of the other `data/worlds/*` directories (e.g.
  `crowded_frontier`, `frontier_marches`, `hero_guild_routing`, `unit_faction_tension`). Step 4's
  item 4 requires a specific targeted test for those cases; do not treat Step 6's `make
  evaluate-full` pass as covering them.
- **`COMB-280`'s existing `divergence_note`** is the project's own precedent for how to document
  exactly this class of change ("X now gives Y instead of Z") — Step 4 and Step 7 should follow
  that same honest-disclosure style rather than asserting "no behavior change" without having
  checked.
- **`tests/unit/combat/test_combat_rewards.py` uses legacy enum literals** that will not match any
  real catalog faction ID string — expected to be unaffected, but Step 4 explicitly re-confirms
  this rather than assuming it holds.
- **`tests/integration/combat/test_relation_combat_integration.py`'s `test_integration_legacy_fallback`**
  uses synthetic faction IDs (`"unconfigured_hero_faction"`/`"unconfigured_monster_faction"`) that
  will never match a real catalog entry — must keep passing untouched, proving the legacy bucket
  path itself was not altered, only its applicability range.
- **`docs/systems/faction_contract.md`'s runtime `DiplomaticState`** is a completely separate
  mechanism from this catalog file — do not conflate "absence = NEUTRAL, do not populate all pairs
  at construction" (which refers to runtime state) with this ticket's catalog-density goal.
- **`src/content/resolver.py:319`** also iterates `faction_relationships` at world-assembly time —
  investigation flagged this as not fully traced; Step 6's `make world-validate` run is the
  practical guard here, but if it surfaces any resolver-level issue, treat it as a Step 3 authoring
  fix (schema/reference issue), not a resolver code change (resolver code is out of scope).
- **Prior work**: `tickets/done/TCK-20260627-P2D-FACTION-RELS.md` already took this file 14→34
  entries once — this is the second pass; reuse its established authoring conventions
  (`# STATE: ADDITIONAL`, schema fields, bidirectional-with-asymmetric-flavor pattern) rather than
  inventing new ones.

## Unresolved Questions

None require escalation to block this ticket. All open questions raised in the investigation have
been resolved above with documented reasoning (UQ-1 denominator, hostility-flip verification
procedure, `neutral`'s safe first value, parity ledger placement, corrected code areas). The one
remaining implementer-level judgment call — the exact final list of which populated-set pairs to
author beyond the required conflict/economy priorities, and which specific target faction to pick
for `neutral`'s entry — is ordinary content-authoring discretion bounded by this plan's explicit
guardrails (no `moon_cult`/`dwarven_mine_clan`/`dragon_cult` pairs, `neutral` must use
`hostility: "none"`), not an architectural decision requiring sign-off before implementation
begins.

If Step 4's anchored-world cross-reference or Step 6's `make evaluate-full` run surfaces a grade
drift that cannot be cleanly attributed to an intentionally-scoped pair (i.e., a currently-anchored
world's combat legality or reward classification changes in a way that looks like a genuine
regression rather than a documented, intended divergence), the implementer must stop and escalate
back to the main session rather than forcing a resolution — that would be new evidence changing
the risk profile this plan was built against, not a case this plan already anticipated.

## Deviations

- **Session split:** implementation was interrupted by a session/API limit after Step 3 completed
  and verified good (75 entries, 41 pairs, `neutral`'s entry present with `hostility: "none"`). A
  second implementer session resumed from Step 4 after re-confirming Step 3's on-disk state matched
  what was reported — no re-authoring occurred, no duplication introduced.
- **`make evaluate-full` anchor-set coverage grew during the same day, ahead of this ticket's own
  assumption:** the plan's Anti-Drift Notes state `make evaluate-full` "only covers the 4
  `grade_anchors.json` template worlds." By the time this ticket's Step 6 ran,
  `tests/simulation_quality/fixtures/grade_anchors.json` had been expanded to 16 world directories
  by sibling tickets completed earlier the same day (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` and
  others). All 5 non-anchor worlds Step 4's cross-reference originally identified
  (`resource_dense_basin`, `frontier_extended`, `crowded_frontier`, `frontier_marches`,
  `hero_guild_routing`) turned out to already be anchored by the time `make evaluate-full` actually
  ran, so the real engine re-run independently corroborated nearly every Step 4 delta finding (610
  pillars, 0 regressions) in addition to the dedicated per-pair unit/integration tests Step 4
  required regardless. Only `generated_frontier_3_42` remains unanchored, and no flip pair's
  co-presence is exclusive to it. This is a favorable deviation (stronger evidence than the plan
  anticipated), not a gap — recorded here per CLAUDE.md's "never silently deviate" rule, and noted
  in the ticket's Implementation Notes.
- No other deviations. Steps 4-9 were executed exactly as specified, including both the
  `combat_rewards.py`/`is_hostile_compat()` delta (item 1) and the separate `legality.py`
  Friendly-Fire delta (item 2) for all 16 non-perspective-source pairs — no unattributable drift
  was found, so the plan's escalation clause above was not triggered.
