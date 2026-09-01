---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-RACE-RELATIONS-MATRIX
artifact_type: plan
tags: [faction, content, combat]
---

# Implementation Plan — TCK-20260831-RACE-RELATIONS-MATRIX

## Summary

Author a new `race_relations` content family (flat list of `RaceRelationRecord`, mirroring
`FactionRelationshipDefinition`'s convention exactly) and wire it into `RelationProjectionService
.project_relation()` as a new, upgrade-only resolution step inserted between the existing
faction-relationship label resolution and the legacy fallback. Two live call sites
(`legality.py`, `tactical.py`) already construct `RelationContext(target_race=...)` but the field
is read nowhere — this plan makes it real. A first-hand read of `relation.py`/`RelationContext`
(cited below) surfaced a real gap investigation.md did not fully resolve: `RelationContext` has no
`source_race` field, so a directed `(source_race, target_race)` lookup as the ticket's "13x12
directed pairs" framing requires is not actually possible today — this plan adds `source_race` as
a sixth optional `RelationContext` field and populates it at both live call sites, which is the
only way to satisfy AC #2's literal wording ("two race pairs with different authored hostility
produce different projected labels"). Race hostility is designed to only ever *tighten* an
existing label (`neutral`→`threat`→`enemy`), never loosen it, and is explicitly disabled for
same-faction pairs, protecting the Friendly Fire law. AC #3 is satisfied by a hand-written,
self-contained integration test that swaps the on-disk `race_relations.yaml` content between two
runs of a real corpus world (`unit_faction_tension` — human+wolf population, already proven
population-stable) and feeds the two runs' real combat-engagement event counts directly into
`MetamorphicRuleEngine.evaluate_rules()` — bypassing `MutationLabOrchestrator`/`MutationEngine`
entirely, per the user's explicit resolution of investigation.md's Risk #1. Coverage is a disclosed
18%-of-populated-pairs subset (24 directed entries / 66 populated undirected pairs), following the
`P2D-FACTION-RELS` precedent's own "high-encounter-frequency, not full coverage" framing.

## Steps

### Step 1 — `RaceRelationRecord` schema
**Files:** `src/content/schema.py`
**Change:** Add a new class directly after `FactionRelationshipDefinition`
(`schema.py:194-199`, confirmed fields: `source_faction: str`, `target_faction: str`,
`relationship_model: str`, `axes: Dict[str, str] = Field(default_factory=dict)`, subclassing
`CatalogBaseDefinition` which is `ConfigDict(frozen=True, extra="forbid")` with `id`,
`display_name`, `description`, `tags`, `schema_version`, `deprecated`, `metadata`, `extension`,
`design_notes` already inherited, `schema.py:8-20`):
```python
class RaceRelationRecord(CatalogBaseDefinition):
    """Schema for hostility/relationship axes between two races."""
    source_race: str = Field(..., description="Source RaceDefinition ID")
    target_race: str = Field(..., description="Target RaceDefinition ID")
    relationship_model: str = Field(..., description="Relationship classification")
    axes: Dict[str, str] = Field(default_factory=dict)
```
No fields beyond this five (`source_race`/`target_race`/`relationship_model`/`axes`, plus
inherited `CatalogBaseDefinition` optionals) — `extra="forbid"` on the base class rejects
anything else, matching the Anti-Drift Hazard in investigation.md verbatim.
**Do NOT touch:** `FactionRelationshipDefinition` itself — reuse only its shape as a template, do
not subclass it or alter it.
**Verify:** covered by Step 2's `test_race_relations_content_family_loads` (schema import succeeds,
`extra="forbid"` rejects an injected bad field).

### Step 2 — `race_relations` content family registration
**Files:** `src/content/repository.py`
**Change:** Three additions, mirroring `faction_relationships`'s exact three touch points:
1. Import `RaceRelationRecord` in the `from src.content.schema import (...)` block
   (`repository.py:25-62`), added after `FactionRelationshipDefinition`.
2. Add `self.race_relations: Dict[str, RaceRelationRecord] = {}` to `CatalogRepository.__init__`
   directly after `self.faction_relationships` (`repository.py:202`).
3. Add to `CANONICAL_FAMILIES` directly after the `social.faction_relationships` entry
   (`repository.py:112`):
   ```python
   ContentFamilySpec("social.race_relations", "social/race_relations.yaml", RaceRelationRecord, "race_relations"),
   ```
   `family="social.race_relations"` (dot-separated) is required — `test_content_usage_matrix.py`
   derives the matrix key via `family.replace(".", "/")` (`test_content_usage_matrix.py:281`
   pattern), so this must produce `"social/race_relations"` to match Step 3's matrix key exactly.
4. Optionally add `get_race_relationship(self, def_id: str) -> Optional[RaceRelationRecord]:
   return self.race_relations.get(def_id)` mirroring `get_faction_relationship`
   (`repository.py:477-478`) for API consistency — not required by any AC or test.
**Do NOT touch:** `get_all_ids_by_type` (`repository.py:520-558`) or `get_deprecated_ids`
(`repository.py:560-600`) — do not add `race_relations` to either mapping; no AC or test requires
it and it is untested surface if added speculatively.
**Do NOT touch:** the `faction_relationships` `ContentFamilySpec` entry itself, or its `.yaml`
file — ticket's Out of Scope is explicit.
**Verify:** `test_race_relations_content_family_loads` (new,
`tests/unit/content/test_race_relations_catalog.py`) — `CatalogRepository("data/content")
.load_all()` populates `repo.race_relations` with `RaceRelationRecord` instances.

### Step 3 — `ContentUsageMatrix` registration
**Files:** `src/content/matrix.py`
**Change:** Add a new `"social/race_relations"` entry to `CONTENT_USAGE_MATRIX` directly after the
existing `"social/faction_relationships"` entry (`matrix.py:246-259`), following its exact field
shape:
```python
"social/race_relations": ContentFamilyMatrixEntry(
    file_path="social/race_relations.yaml",
    schema_class="RaceRelationRecord",
    repository_index="race_relations",
    validator_coverage=None,
    resolver_component=None,
    compile_runtime_consumer="RelationProjectionService",
    test_coverage="tests/unit/content/test_race_relations_catalog.py",
    evidence_tests="tests/unit/content_semantics/test_relation_race_projection.py::test_race_relations_hostility_changes_projected_label",
    resolver_evidence=None,
    runtime_consumer_evidence="RelationProjectionService resolves race_relations entries and factors axes.hostility into the projected label",
    implementation_state="RESOLVED_PARTIALLY",
    content_maturity="ADDITIONAL",
),
```
`implementation_state="RESOLVED_PARTIALLY"` matches `faction_relationships`'s own state (content
is consumed by real logic but only for entities that resolve a `race_id`, not universally).
`content_maturity="ADDITIONAL"` (one of the 6 valid states in `test_content_usage_matrix.py`'s
`VALID_MATURITY_STATES`) — this is genuinely new content, not a redesign of existing logic.
**Do NOT touch:** any other `CONTENT_USAGE_MATRIX` entry.
**Verify:** `tests/unit/content/test_content_usage_matrix.py` (existing, unmodified) — parity check
between `CANONICAL_FAMILIES` and `CONTENT_USAGE_MATRIX` passes once both Step 2 and this step land
together.

### Step 4 — `docs/mechanics/content_usage_matrix.md` row
**Files:** `docs/mechanics/content_usage_matrix.md`
**Change:** Add a new table row directly after the `social/faction_relationships` row (line 43),
matching that row's column shape exactly (confirmed via `grep`: file path, schema class,
repository index, validator coverage, resolver component, compile/runtime consumer, test coverage,
evidence tests, resolver evidence, runtime consumer evidence, implementation state, content
maturity) — values taken verbatim from Step 3's Python entry.
**Do NOT touch:** the `living/races` row (line 38) or any other row.
**Verify:** no automated test for markdown-vs-Python drift on this file; verified by manual
side-by-side comparison against Step 3's entry at Finalize.

### Step 5 — `RelationContext.source_race` field
**Files:** `src/content_semantics/relation.py`
**Change:** Add `source_race: Optional[str] = None` to `RelationContext` (`relation.py:13-21`,
currently five fields: `distance`, `location`, `intruding`, `combat_engaged`, `target_race`) —
directly after `target_race`. **This field does not exist in investigation.md's read of the class
and is a necessary addition, not an ambiguity to leave open**: `project_relation()` currently
receives `source_faction_id`/`target_faction_id` as explicit string params (faction identity), but
has no way to know the *race* of the perspective/attacker side — only `context.target_race` (the
race of the entity being evaluated as a target). A directed `(source_race, target_race)`
`race_relations` lookup, which is what the ticket's own "156 directed pairs" framing and AC #2's
"two race pairs... produce different projected labels" require, is structurally impossible without
it. Both live call sites already have the attacker/entity object in scope to supply this (Steps 6-7).
**Do NOT touch:** `RelationProjection`'s fields (`relation.py:24-32`) — no change needed there,
only `RelationContext`.
**Verify:** covered indirectly by Step 8's tests (a `RelationContext` with both `source_race`
and `target_race` set is the precondition for the new resolution step to fire).

### Step 6 — `project_relation()` race-hostility resolution step
**Files:** `src/content_semantics/relation.py`
**Change:** Insert a new resolution block in `project_relation()` (`relation.py:44-161`) directly
after the existing "Check relationship axes if perspective did not resolve a label" block ends
(currently line 144, right before "# 4. Fallback to legacy semantics" at line 147) and before step
4's `if not label:` fallback. This ordering is deliberate: it runs after perspective/relationship
label resolution (so it can *upgrade* whatever they produced) but before the legacy fallback (so a
`None` label reaching this step still gets a chance at race-level escalation instead of skipping
straight to `is_hostile()`).

```python
# 3.5 Race-hostility escalation (upgrade-only, never loosens an existing label).
# Friendly Fire law guard: same-faction pairs must never become attackable via race
# hostility alone (docs/mechanics/02_combat_laws.md:117; investigation.md Risk #2).
# Ally/protected-label guard: project_relation() can produce five labels outside the
# neutral->threat/intruder->enemy escalation ladder -- "ally" (relation.py:93), "protected"
# (relation.py:112), "opportunity" (relation.py:106), "ignored" (relation.py:110), "prey"
# (relation.py:119), all confirmed by direct read of the perspective-label block. Only
# labels IN the ladder dict are eligible for escalation at all -- this is a fail-closed
# design: an off-ladder or future-unknown label is always skipped, never defaulted to
# rank 0/neutral. (Architecture-review finding: the prior `.get(label, 0)` design defaulted
# any unmapped label -- including "ally" -- to the same rank as "neutral", letting an
# authored race-hostility entry silently invert a perspective-declared ally into
# "enemy"/"threat". Concrete live trigger: data/content/social/perspectives.yaml:7's
# hero_guild_perspective.projected_labels.ally_groups includes forest_wardens (elf-race,
# entity_archetypes.yaml:170-171) and dwarven_mine_clan (dwarf-race,
# entity_archetypes.yaml:389-390); hero_guild itself is human-race
# (entity_archetypes.yaml:404-405). Today's Step 10 content has no human<->elf or
# human<->dwarf pair, so this has not fired live, but nothing in the prior design prevented
# a future content addition from triggering it. See Step 6 regression test below and
# Anti-Drift Notes.)
_RACE_LABEL_LADDER_RANK = {None: 0, "neutral": 0, "threat": 1, "intruder": 1, "enemy": 2}
if (
    source_faction_id != target_faction_id
    and context and context.source_race and context.target_race
    and label in _RACE_LABEL_LADDER_RANK
):
    race_rel = None
    for rr in self.repo.race_relations.values():
        if rr.source_race == context.source_race and rr.target_race == context.target_race:
            race_rel = rr
            break
    if race_rel:
        race_hostility = race_rel.axes.get("hostility", "none")
        current_rank = _RACE_LABEL_LADDER_RANK[label]
        if race_hostility == "high" and current_rank < 2:
            label = "enemy"
        elif race_hostility in ("medium", "medium_contextual", "high_contextual", "low_base_contextual") and current_rank < 1:
            label = "threat"
        if label in ("enemy", "threat"):
            source_records.append(f"race_relationship:{race_rel.id}")
```

The hostility vocabulary (`"high"`, `"medium"`, `"medium_contextual"`, `"high_contextual"`,
`"low_base_contextual"`) is reused verbatim from the existing faction-axis branch two blocks above
(`relation.py:124-137`) — no new vocabulary is invented, matching the Anti-Drift Hazard against
`DiplomaticState`-style enum values.
**Do NOT touch:** step 4's legacy fallback block (`relation.py:147-153`) — it is unchanged and
still fires whenever `label` is `None` after this new step (i.e., no perspective, no relationship,
and either no race entry or the race entry didn't clear the rank threshold).
**Do NOT touch:** the perspective-label block (`relation.py:87-120`) or the relationship-axis block
(`relation.py:123-144`) — this step only reads their output (`label`), never their internal logic.
**Do NOT touch:** `_RACE_LABEL_LADDER_RANK` must stay limited to exactly `{None, "neutral",
"threat", "intruder", "enemy"}` — do not add `"ally"`/`"protected"`/`"opportunity"`/`"ignored"`/
`"prey"` (or any future new label `project_relation()` gains) to this dict under the belief that
"ranking them higher" is more correct than skipping them. The `label in _RACE_LABEL_LADDER_RANK`
guard is the mechanism that makes unknown/future labels safe by default (skipped) rather than
requiring every future label addition to also remember to update this file — do not replace it with
a `.get(label, 0)`-style default.
**Verify:**
- `test_race_relations_hostility_changes_projected_label` (new,
  `tests/unit/content_semantics/test_relation_race_projection.py`) — two calls with contrasting
  `axes.hostility` on the same faction pair produce different `label`s; a `target_race=None` (or
  `source_race=None`) case falls through unchanged (graceful no-op).
- `test_race_relations_same_faction_never_becomes_hostile` (new, same file or the legality test
  file per Step 9) — `source_faction_id == target_faction_id` with an authored race entry between
  the two races still yields no race-driven escalation.
- `test_race_relations_never_overrides_ally_label` (new, same file
  `tests/unit/content_semantics/test_relation_race_projection.py`) — the concrete regression test
  for this architecture-review finding. Uses the real `hero_guild_perspective`
  (`data/content/social/perspectives.yaml:7`, `ally_groups` includes `forest_wardens`) plus a
  synthetic `RaceRelationRecord(id="human_to_elf_test", source_race="human", target_race="elf",
  relationship_model="test_fixture", axes={"hostility": "high"})` injected directly into the test's
  `repo.race_relations` dict (Step 10's real 24-entry content has no human<->elf pair, so this must
  be a synthetic fixture, not a read of the on-disk file, to exercise the guard regardless of what
  content happens to be authored today). Asserts
  `project_relation("hero_guild_perspective", "hero_guild", "forest_wardens",
  RelationContext(source_race="human", target_race="elf")).label == "ally"` — i.e. an authored
  `"high"`-hostility race entry between the two races does NOT invert the perspective-declared ally
  label to `"enemy"`/`"threat"`. A second assertion in the same test using
  `dwarven_mine_clan`/dwarf (also a real `ally_groups` member of `hero_guild_perspective`) is
  optional but recommended for the same reason — both are real, already-authored ally pairings in
  content today, not hypothetical.
- All pre-existing `test_combat_relation_projection.py` cases (test_plan.md's Anti-Drift Test
  Guards) — entities with no authored `race_relations` entry must produce identical output, since
  `race_rel` stays `None` and the block is a no-op.

### Step 7 — Legality path wiring
**Files:** `src/engine/legality.py`
**Change:** In `LegalityServiceV2.verify_attack_legality` (`legality.py:187-247`), add
`source_race=get_race_id_str(attacker)` to the existing `RelationContext(...)` construction at
`legality.py:243-247`:
```python
context = RelationContext(
    distance=float(dist),
    combat_engaged=combat_engaged,
    source_race=get_race_id_str(attacker),
    target_race=get_race_id_str(target),
)
```
`get_race_id_str` is already imported at `legality.py:222`. No other change to this method.
**Do NOT touch:** the `intruding` field — it stays unset (`None`) per the existing comment block
at `legality.py:234-242`, which documents a deliberate, separate, already-resolved decision
(`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`) unrelated to this ticket.
**Do NOT touch:** the `has_clean`/faction-equality short-circuit logic (`legality.py:250-269`) —
race hostility only ever participates through `is_hostile_compat()`'s existing `context` forwarding
(`faction.py:200`); this ticket adds no new branch here.
**Verify:** `test_attack_legality_race_hostility_affects_friendly_fire_check` (new,
`tests/unit/combat/test_race_relations_legality_wiring.py`) plus the same-faction guard test noted
in Step 6.

### Step 8 — Tactical path wiring
**Files:** `src/engine/tactical.py`
**Change:** In `TacticalDecisionSystem.evaluate_entity_intent`'s hostiles-scan loop
(`tactical.py:193-225`), add `source_race=get_race_id_str(entity)` to the existing
`RelationContext(...)` construction at `tactical.py:212-216`:
```python
context = RelationContext(
    distance=float(dist),
    combat_engaged=combat_engaged,
    source_race=get_race_id_str(entity),
    target_race=get_race_id_str(n),
)
```
`get_race_id_str` is already imported at `tactical.py:165` (via the same `from
src.content_semantics.faction import ...` used at line 190). No other change to this loop.
**Do NOT touch:** `target_score()`'s sort tuple (`tactical.py:395-438`, currently the 6-element
`(group_bias, is_current_target, -capability_confidence, h.combat.hp, dist * pressure_dist_mod,
h.id)` landed by `TCK-20260831-CAPABILITY-DRIVEN-TARGETING`). Race hostility affects which
entities land in the `hostiles` list (line 223, upstream of `target_score()` entirely, confirmed
by reading `tactical.py:193-225` directly) — it does not need a 7th tuple element and must not get
one. If race hostility changes hostiles-list membership, `target_score()` runs unchanged over
whatever list results; `test_capability_driven_targeting.py`'s existing tuple-shape assertions are
therefore expected to keep passing unmodified.
**Verify:** `test_tactical_hostile_scan_race_hostility_affects_target_pool` (new,
`tests/unit/combat/test_race_relations_tactical_wiring.py`); `test_capability_driven_targeting.py`
(existing) must pass unmodified.

### Step 9 — `RegionThreatClassifier` — confirmed unaffected, no change
**Files:** none.
**Change:** No code change. First-hand `grep -rn "RegionThreatClassifier" src/` (excluding its own
file `src/world/region_threat_classifier.py`) returns **zero matches** — `.classify()` /
`._classify_via_projection()` have no live caller anywhere in `src/` today. This is a stronger,
more definitive finding than investigation.md's flag ("not traced," "worth Plan calling out") —
the class is dead code with respect to any real caller, so its `context: Optional[RelationContext]`
parameter can never carry a populated `target_race`/`source_race` in production regardless of this
ticket's changes. No test is added for this file; it is confirmed out of AC #2's blast radius by
construction, not by assumption.
**Do NOT touch:** `src/world/region_threat_classifier.py` — explicitly listed in investigation.md's
Anti-Drift Hazards as out of scope; this step's only output is the confirmation above.
**Verify:** N/A (no behavior change, no test needed).

### Step 10 — Author `data/content/social/race_relations.yaml`
**Files:** `data/content/social/race_relations.yaml` (new file)
**Change:** Author 24 directed entries (12 undirected pairs, each authored bidirectionally,
matching `faction_relationships.yaml`'s own bidirectional-entry convention, e.g.
`town_to_wild_beasts`/`wild_beasts_to_town`). Denominator and roster: confirmed 13 races in
`data/content/living/races.yaml` (`human, wolf, goblin, spider, orc, elf, dwarf, undead, troll,
lizardfolk, dragonkin, slime, spirit`). Cross-checked against `data/content/entities
/entity_archetypes.yaml`'s `race:` field (`grep -c` per race): 12 of 13 races have at least one
real spawnable archetype (`human`×7, `goblin`×4, `wolf`×2, `orc`×2, `elf`×2, `lizardfolk`×2,
`dwarf`, `troll`, `dragonkin`, `spirit`, `undead`, `spider`×1 each) — **`slime` has zero
`entity_archetypes.yaml` entries, confirmed via `grep -n "slime"` returning no matches**, i.e. no
live spawn path, exactly mirroring `test_faction_relationships_coverage.py`'s own
`POPULATED_FACTIONS` precedent (factions with "zero module path to population" excluded from the
denominator). **Populated-race denominator: the 12 races above, excluding `slime`. C(12,2) = 66
undirected pairs.** `spirit` is retained in the denominator (it has one archetype,
`259: race: "spirit"`), unlike the faction-level precedent's `spirit_court` exclusion — these are
different entities (a faction vs. a race) and `spirit`-the-race does have a real archetype.

Authored pairs (rationale: hero-race-vs-monster-race and predator/prey pairs most likely to
actually co-populate and fight in a real scenario, mirroring `P2D-FACTION-RELS`'s own
"high-encounter-frequency" framing, not a uniform sample):

| Pair | Rationale | `source→target` hostility | `target→source` hostility |
|---|---|---|---|
| human ↔ wolf | predator/prey; real co-population confirmed in `unit_faction_tension` world (`frontier_village_core` + `wolf_den_near_forest`) | wolf→human: `medium_contextual` | human→wolf: `medium_contextual` |
| human ↔ goblin | classic hero/monster; both multi-archetype | goblin→human: `high` | human→goblin: `high` |
| human ↔ orc | hero/monster | orc→human: `high` | human→orc: `medium_contextual` |
| human ↔ troll | hero/monster | troll→human: `high` | human→troll: `medium_contextual` |
| human ↔ undead | hero/monster | undead→human: `high` | human→undead: `high` |
| human ↔ spider | hero/monster | spider→human: `medium_contextual` | human→spider: `medium_contextual` |
| human ↔ dragonkin | hero/monster (rare, high-stakes) | dragonkin→human: `medium_contextual` | human→dragonkin: `low_base_contextual` |
| human ↔ lizardfolk | hero/monster | lizardfolk→human: `medium_contextual` | human→lizardfolk: `low_base_contextual` |
| elf ↔ goblin | hero-race variant vs. monster | goblin→elf: `high` | elf→goblin: `medium_contextual` |
| elf ↔ orc | hero-race variant vs. monster | orc→elf: `high` | elf→orc: `medium_contextual` |
| dwarf ↔ goblin | hero-race variant vs. monster | goblin→dwarf: `high` | dwarf→goblin: `medium_contextual` |
| dwarf ↔ orc | hero-race variant vs. monster | orc→dwarf: `high` | dwarf→orc: `medium_contextual` |

Each row's `relationship_model` field: a short code-owned string per pair category, e.g.
`"predator_prey"` (wolf pairs), `"hero_vs_monster_race"` (goblin/orc/troll/undead/spider/dragonkin/
lizardfolk pairs). `id` fields follow `"<source>_to_<target>"` (e.g. `"wolf_to_human"`), matching
`faction_relationships.yaml`'s own `id` convention (`town_to_wild_beasts`).

**Disclosed gap** (explicit, not silent): the remaining 54 of 66 populated undirected pairs
(elf↔wolf, elf↔troll, elf↔undead, elf↔spider, elf↔dragonkin, elf↔lizardfolk, dwarf↔wolf,
dwarf↔troll, dwarf↔undead, dwarf↔spider, dwarf↔dragonkin, dwarf↔lizardfolk, and all
monster-vs-monster pairs e.g. goblin↔orc, troll↔undead, spider↔lizardfolk, etc.) are left at
neutral default (no entry, `race_rel` resolves to `None`, no escalation). Rationale: (a) no
evidence found of these pairs co-populating in any real corpus world's population recipe within
this investigation's scope; (b) monster-vs-monster pairs rarely fight each other in the current
scenario roster (both sides are typically hostile-to-player-factions, not to each other); this
mirrors `P2D-FACTION-RELS`'s own acknowledged-gap framing exactly.
**Do NOT touch:** `data/content/social/faction_relationships.yaml`.
**Verify:** `test_race_relations_coverage_meets_disclosed_threshold` (Step 11).

### Step 11 — Coverage-disclosure guard test
**Files:** `tests/unit/content/test_race_relations_coverage.py` (new)
**Change:** Mirror `test_faction_relationships_coverage.py`'s `POPULATED_FACTIONS`-frozenset
pattern (`tests/unit/content/test_faction_relationships_coverage.py:20-27`) with a
`POPULATED_RACES` frozenset of the 12 races from Step 10 (excludes `slime`), asserting:
- `len(_undirected_pairs(repo)) >= 12` (the 12 authored undirected pairs, graded against the
  66-pair populated-only denominator — ~18%, disclosed as a partial-coverage subset, not full
  coverage, matching AC #4's "disclosed defensible subset... not all 156 uniformly").
- every authored `source_race`/`target_race` resolves to a real `RaceDefinition` id
  (`repo.races` keys) and every `axes` key resolves to a real `relationship_axes` id (mirrors
  `test_faction_relationships_coverage.py`'s `test_new_relationship_entries_reference_valid_axes_and_factions`).
- a same-race guard: no entry has `source_race == target_race` (nonsensical, not excluded by
  Pydantic schema itself).
**Do NOT touch:** `test_faction_relationships_coverage.py` — must remain unmodified, acting as the
negative control per test_plan.md.
**Verify:** the test itself, run via `pytest tests/unit/content/test_race_relations_coverage.py`.

### Step 12 — AC #3: hand-orchestrated metamorphic validation (resolves investigation.md Risk #1)
**Files:** `tests/integration/lab/test_race_relations_metamorphic_validation.py` (new)
**Change:** Per the user's explicit resolution (does not extend `MutationEngine`; hand-orchestrates
`MetamorphicRuleEngine.evaluate_rules()` directly). `evaluate_rules(rules: list[
ExpectedRelationshipSpec], variant_metrics: dict[str, dict[str, Any]]) -> list[
MetamorphicComparisonResult]` (`src/lab/metamorphic.py:164-176`, confirmed by direct read — a
`@staticmethod`, no orchestrator/CLI dependency). `ExpectedRelationshipSpec` required fields
(`src/lab/schema.py:319-326`): `id`, `type` (must be one of the 6 in
`src/lab/schema.py:331-338`, use `"monotonic_non_decreasing"`), `metric`, `baseline_variant`
(default `"base"` — override explicitly), `compared_variant`. `variant_metrics` is a plain
`dict[str, dict[str, Any]]` keyed by variant id — no `MutationSpec`/`WorldSpec` involvement
whatsoever, confirmed by the method's signature and body (no schema coupling to `WorldSpec`).

**Mechanics of "vary the authored hostility value" (concrete, not abstract):**
1. Use the real `unit_faction_tension` world (`data/worlds/unit_faction_tension/world.yaml`,
   confirmed on disk) — description confirms it combines `frontier_village_core` (human
   archetypes: `village_worker`, `frontier_guard`, `traveling_merchant`, `village_blacksmith`) with
   `wolf_den_near_forest` (`hungry_wolf`, `alpha_wolf`), "already proven population-stable to 2000
   ticks." This is the real corpus world AC #3 requires.
2. Author a throwaway `ScenarioSpec` (`data/scenarios/race_hostility_metamorphic_check/scenario.yaml`,
   `world_id: "unit_faction_tension"`) and `ExperimentSpec`
   (`data/experiments/race_hostility_metamorphic_check_experiment/experiment.yaml`,
   `experiment_type: "single_run"`, `run.ticks: 200`, `run.seeds: [201, 202, 203]`), mirroring the
   pilot ticket's own Step 1-3 shape (`stored_artifacts/TCK-20260831-METAMORPHIC-LAB-PILOT/plan.md`
   Steps 2-3) — created and torn down inside the test's own fixture (`tmp` creation +
   `shutil.rmtree` teardown), not left on disk.
3. **Baseline variant**: temporarily ensure `data/content/social/race_relations.yaml` has **no**
   `wolf↔human` entries (the two entries this pair got in Step 10 are removed for this run only —
   captured and restored after). Run the experiment via
   `ScenarioLabOrchestrator(...).run_lab(experiment_id, lab_run_id="race_hostility_baseline")`
   directly in Python (not via CLI subprocess — no benefit here since content re-read is guaranteed
   fresh per fresh `Kernel()` construction regardless; confirmed via `src/engine/kernel.py:329-335`,
   `Kernel.__init__` unconditionally calls `ContentWarmupService.warmup()`, which
   (`src/content/warmup.py:43-48`) always constructs a fresh `CatalogRepository` and calls
   `load_all()` when invoked with no `repo` argument — no "already warm" short-circuit exists, so
   each new `Kernel()` re-reads the on-disk file). Read each seed's
   `data/lab_runs/race_hostility_baseline/runs/run_race_hostility_baseline_seed_<seed>
   /simulation_events.jsonl` (path confirmed via `src/lab/orchestrator.py:270-289` +
   `src/observability/reporting/run_report.py:135`'s `os.path.join(run_dir,
   "simulation_events.jsonl")` pattern) and count lines where `event_type ==
   "combat_engagement_started"` (a real, confirmed event type — `src/observability/event_shapers.py
   :250`). Compute `combat_engagement_rate = total_started_events / run.ticks`, averaged across the
   3 seeds.
4. **Compared variant**: overwrite the same two entries with `axes.hostility: "high"` for both
   `wolf→human` and `human→wolf`. Re-run identically with `lab_run_id="race_hostility_high"`.
   Compute the same metric.
5. Restore `data/content/social/race_relations.yaml` to its Step 10 authored state exactly
   (assert file content equality against a captured pre-test snapshot in teardown — a hard
   assertion failure if restoration didn't happen, not a silent `finally`).
6. Build `variant_metrics = {"baseline": {"combat_engagement_rate": <baseline_avg>, "run_count":
   3}, "high_hostility": {"combat_engagement_rate": <high_avg>, "run_count": 3}}` and call:
   ```python
   from src.lab.metamorphic import MetamorphicRuleEngine
   from src.lab.schema import ExpectedRelationshipSpec
   spec = ExpectedRelationshipSpec(
       id="race_hostility_engagement_check",
       type="monotonic_non_decreasing",
       metric="combat_engagement_rate",
       baseline_variant="baseline",
       compared_variant="high_hostility",
   )
   results = MetamorphicRuleEngine.evaluate_rules([spec], variant_metrics)
   ```
7. Assert `results[0].status == "PASSED"` — this is AC #3's literal semantic ("increasing
   hostility does not decrease combat-engagement rate"), not merely "not `INSUFFICIENT_DATA`".
   If the initial `run.ticks`/seed count produces a degenerate equal-metric result (baseline ==
   compared, both hostility escalations having zero observable effect because, e.g., the two
   populations never come within range across all 3 seeds), follow the pilot ticket's own
   documented empirical approach (`stored_artifacts/TCK-20260831-METAMORPHIC-LAB-PILOT/plan.md`
   Deviations section): tune `run.ticks` upward and/or re-check world population density before
   concluding the mechanism itself is broken — do not fabricate a passing result.
8. Clean up all created `data/scenarios/`, `data/experiments/`, and `data/lab_runs/
   race_hostility_baseline/` + `data/lab_runs/race_hostility_high/` directories in the test's
   teardown (`data/lab_runs/` may contain other tickets' runs; delete only the two directories this
   test creates, never `rm -rf data/lab_runs/` wholesale).
**Do NOT touch:** `src/lab/mutation.py`, `src/lab/mutation_orchestrator.py`, `src/lab/cli.py` — no
`MutationEngine`/`MutationLabOrchestrator` code path is modified or invoked by this test, per the
user's explicit resolution.
**Do NOT touch:** `data/worlds/unit_faction_tension/` itself — read-only input.
**Verify:** the test itself; mark `@pytest.mark.slow` (runs real multi-seed simulation twice) so it
is excluded from the standard `-m "not slow"` regression sweep but still exists as permanent,
CI-visible evidence for this ticket's most novel, highest-uncertainty AC.

### Step 13 — Parity ledger updates
**Files:** `docs/parity_ledger/combat_movement.yaml`, `docs/parity_ledger/strategic_cognition.yaml`,
`docs/parity_ledger/social_narrative.yaml`
**Change:** Three new entries, next-free IDs confirmed by investigation.md's tail-check (`COMB-317`,
`STRAT-263`, `SOC-257` — none of the current tails `COMB-316`/`STRAT-262`/`SOC-256` mention race
relations):
- **`COMB-317`** (`combat_movement.yaml`): text describing the legality-path race-hostility
  consumption (Step 7) — `status: verified`, `priority: P0` (live combat-legality gate per Friendly
  Fire law), `v2_evidence` citing `legality.py:243-247`, `test_path:
  tests/unit/combat/test_race_relations_legality_wiring.py`.
- **`STRAT-263`** (`strategic_cognition.yaml`): text describing the tactical-path consumption
  (Step 8) feeding hostile-scan target-pool membership — `status: verified`, `priority: P1`,
  `v2_evidence` citing `tactical.py:212-216`, `test_path:
  tests/unit/combat/test_race_relations_tactical_wiring.py`.
- **`SOC-257`** (`social_narrative.yaml`): text describing the `race_relations` content family
  itself plus `project_relation()`'s new consuming logic (Steps 1-2, 6) — `status: verified`,
  `priority: P1`, `v2_evidence` citing `relation.py`'s new resolution block + `repository.py`'s new
  `ContentFamilySpec`, `test_path: tests/unit/content_semantics/test_relation_race_projection.py`.
  (Investigation noted `faction_relationships.yaml` content itself has no parity entry, treating
  pure content as non-behavioral; this entry is scoped to the new *consuming logic*, not the
  content file, resolving that ambiguity explicitly rather than silently.)
Use `tools/parity_ledger_writer.py` (the sanctioned schema-validating writer) for all three edits,
not raw YAML `Edit` — per the project's own documented risk on ad-hoc full-file parity YAML
rewrites.
**Do NOT touch:** any other entry in these three files.
**Verify:** parity ledger schema validation (existing tooling); `test_path` files exist and pass.

### Step 14 — Docs: `content_semantics_contract.md`
**Files:** `docs/content/content_semantics_contract.md`
**Change:** Two edits to the `RelationProjectionService` section (lines 56-68):
1. Line 66: `**RelationContext fields** (all optional): distance, location, intruding,
   combat_engaged, target_race.` → add `source_race` to the list.
2. After line 60 ("Projects a relationship label... using catalog `PerspectiveDefinition` and
   `FactionRelationshipDefinition` records."), add one sentence describing the new race-hostility
   resolution step at the same level of prose detail as the existing description, e.g.: "If
   `source_race`/`target_race` are both set and a matching `RaceRelationRecord` exists, its
   `axes.hostility` may upgrade (never downgrade) the resolved label, gated off for same-faction
   pairs to preserve the Friendly Fire law."
**Do NOT touch:** any other service's section in this file (`FactionSemanticsService`,
`RoleSemanticsService`, `DefaultSemanticsService`).
**Verify:** no automated test; manual review at Finalize. Run `make knowledge-index-update` after
this edit per the project's After Work rule (docs under `docs/` were modified).

## Scope Guards

- Do not touch `data/content/social/faction_relationships.yaml` or `FactionState` relations —
  reuse only the schema *convention*.
- Do not touch `src/lab/mutation.py`, `src/lab/mutation_orchestrator.py`, or `MutationSpec.target`
  resolution — AC #3 is satisfied without extending the mutation-lab pipeline, per the user's
  explicit decision.
- Do not add a 7th element to `target_score()`'s sort tuple in `tactical.py` — race hostility
  affects hostiles-list membership only, upstream of the tuple.
- Do not wire `RegionThreatClassifier` — confirmed dead code (zero live callers), out of scope.
- Do not add `race_relations` to `CatalogRepository.get_all_ids_by_type` / `get_deprecated_ids`.
- Do not let race hostility ever downgrade an existing label (no "loosening" path exists in Step
  6's design — only `label = "enemy"` / `label = "threat"` assignments, never a path back to
  `"neutral"`).
- Do not let race hostility escalate same-faction pairs — the `source_faction_id !=
  target_faction_id` guard in Step 6 is load-bearing for the Friendly Fire law and must not be
  removed or weakened.
- Do not let race hostility escalate a perspective-declared label that falls outside the
  `neutral`/`threat`/`intruder`/`enemy` ladder — `"ally"`, `"protected"`, `"opportunity"`,
  `"ignored"`, `"prey"` (the full confirmed set `project_relation()` can produce,
  `relation.py:88-120`), or any future label added later. Step 6's `label in
  _RACE_LABEL_LADDER_RANK` guard is load-bearing and must not be replaced with a
  `.get(label, 0)`-style default that treats an unrecognized label as rank-0/neutral — that is
  the exact defect this fix corrects (an authored race-hostility entry could otherwise invert an
  explicit `"ally"` designation, e.g. `hero_guild`/`forest_wardens`, into hostile).
- Do not leave `data/scenarios/race_hostility_metamorphic_check/`,
  `data/experiments/race_hostility_metamorphic_check_experiment/`, or
  `data/lab_runs/race_hostility_baseline/` / `data/lab_runs/race_hostility_high/` on disk after
  Step 12's test runs (teardown, not a one-time manual cleanup — this is a permanent test that
  must self-clean on every run).
- Do not invent new `axes` vocabulary — reuse the existing `"high"/"medium"/"medium_contextual"/
  "high_contextual"/"low_base_contextual"` strings already used by `faction_relationships.yaml`.

## Dependency Map

- Steps 1-4 (schema, catalog registration, matrix registration, matrix doc) are strictly ordered
  (each depends on the prior) and independent of Steps 5-9.
- Steps 5-9 (RelationContext field, project_relation() logic, legality wiring, tactical wiring,
  RegionThreatClassifier confirmation) depend on Step 1 only insofar as Step 6 reads
  `self.repo.race_relations` (Step 2's dict) — Steps 5, 7, 8, 9 are otherwise independent of each
  other and can be implemented in any order, but Step 6 must land before Steps 7-8 are meaningfully
  testable end-to-end (their tests exercise the full call chain through `project_relation()`).
- Step 10 (content authoring) depends on Steps 1-3 (schema + registration must exist for the YAML
  to load) but not on Steps 5-9.
- Step 11 (coverage test) depends on Step 10.
- Step 12 (AC #3 validation) depends on Steps 1-10 all being complete (needs the real schema,
  registration, consuming logic, and authored content all live simultaneously).
- Step 13 (parity ledger) depends on Steps 6-8 being implemented and their tests passing.
- Step 14 (docs) depends on Step 6 being implemented (describes its actual behavior).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: `race_relations` content family loads via new `ContentFamilySpec` + Pydantic model (`extra="forbid"`) | Steps 1, 2 | `test_race_relations_content_family_loads` |
| AC #2: `RelationContext.target_race` consumed by `project_relation()`, two race pairs with different hostility produce different labels | Steps 5, 6, 7, 8 | `test_race_relations_hostility_changes_projected_label`, `test_attack_legality_race_hostility_affects_friendly_fire_check`, `test_tactical_hostile_scan_race_hostility_affects_target_pool` |
| AC #3: `MetamorphicRuleEngine` confirms increasing hostility does not decrease combat-engagement rate, on a real corpus world | Step 12 (hand-orchestrated, not via `MutationLabOrchestrator`, per user's explicit resolution) | `tests/integration/lab/test_race_relations_metamorphic_validation.py`, asserting `results[0].status == "PASSED"` |
| AC #4: disclosed defensible subset, not all 156 uniformly | Steps 10, 11 | `test_race_relations_coverage_meets_disclosed_threshold` |
| AC #5: ticket not started until `TCK-20260831-METAMORPHIC-LAB-PILOT` landed | N/A (process gate, already satisfied — pilot ticket confirmed in `tickets/done/`) | N/A |

## Ticket Text Correction Needed (not an open question — flagging a stale AC wording)

The ticket's AC #3 (`tickets/inprogress/TCK-20260831-RACE-RELATIONS-MATRIX.md`) is currently
worded "`MutationLabOrchestrator.run_mutation_lab()` is invoked against a real mutation spec..." —
this literal wording is now stale relative to the user's explicit, already-final resolution of
investigation.md's Risk #1 (skip `MutationEngine` entirely; hand-orchestrate
`MetamorphicRuleEngine.evaluate_rules()` directly, per Step 12). Nothing in this plan invokes
`MutationLabOrchestrator.run_mutation_lab()`, and it should not. This is not a plan-vs-ticket
contradiction to silently paper over: the orchestrating session should update the ticket's AC #3
text (and its Scope bullet with the same wording) to describe the resolved hand-orchestrated
approach before or during Implement, so `done-checker` and any future reader see AC text that
matches what was actually built, rather than checking for a `MutationLabOrchestrator` call that
this plan deliberately never makes.

## Anti-Drift Notes

- **The `RelationContext.source_race` gap**: investigation.md did not flag that `RelationContext`
  lacks a source-side race field. This plan adds it (Step 5) because without it, a directed
  `(source_race, target_race)` lookup is structurally impossible — do not implement Step 6's race
  resolution keyed on `target_race` alone (e.g. "does any race hate this target race" without
  regard to the attacker's own race) — that would not match the ticket's own "156 directed pairs"
  framing or AC #2's literal wording.
- **Upgrade-only is the single most important correctness property in this ticket.** Every test in
  Step 6/7/8 that exercises the new logic should include at least one case proving a `race_relations`
  entry cannot *downgrade* an existing `"enemy"`/`"threat"` label to something weaker.
- **Same-faction guard is the Friendly Fire law's last line of defense for this feature.** Step 6's
  `source_faction_id != target_faction_id` check must run before the `race_relations` lookup even
  begins, not just before applying its result.
- **Ally/protected-label guard is the second load-bearing invariant for this feature, alongside
  upgrade-only and same-faction — added in response to an architecture-review finding.**
  `project_relation()` can produce five labels outside the `neutral`→`threat`/`intruder`→`enemy`
  escalation ladder — `"ally"` (relation.py:93), `"protected"` (relation.py:112), `"opportunity"`
  (relation.py:106), `"ignored"` (relation.py:110), `"prey"` (relation.py:119), confirmed by direct
  read — and race hostility must never touch any of them. The concrete live trigger:
  `data/content/social/perspectives.yaml:7`'s `hero_guild_perspective.projected_labels.ally_groups`
  includes `forest_wardens` (elf-race, `entity_archetypes.yaml:170-171`) and `dwarven_mine_clan`
  (dwarf-race, `entity_archetypes.yaml:389-390`); `hero_guild` itself is human-race
  (`entity_archetypes.yaml:404-405`). Today's Step 10 authored 24-entry `race_relations.yaml` has no
  `human↔elf`/`human↔dwarf` pair, so this specific inversion has not fired live, but nothing in an
  earlier draft of this design (a `_RACE_LABEL_RANK.get(label, 0)`-style default) prevented a future
  content addition from triggering it — the bug was structural, not content-dependent. Step 6's
  design defends against this by gating the entire escalation block on `label in
  _RACE_LABEL_LADDER_RANK` up front: an unrecognized label is always skipped, never defaulted to
  rank 0/neutral. **Do not revert to a `.get(label, 0)`-style default under any future refactor** —
  that reintroduces this exact bug. `test_race_relations_never_overrides_ally_label` (Step 6) is the
  permanent regression guard for this invariant, using the real `hero_guild`/`forest_wardens` ally
  pairing as its concrete fixture.
- **The metric-name / "hollow metric" trap** (mirroring the pilot ticket's own hard-won lesson):
  `combat_resolution` and `resource_production` in `_extract_variant_metrics`
  (`mutation_orchestrator.py:427-450`) both default to `0.0` because `run_report.json`'s actual
  written keys (`src/observability/reporting/run_report.py:106-122`, confirmed by direct read: only
  `health_score`, `hard_law_violation_count`, `errors_count`, `warnings_count`,
  `total_anomalies_count`, `final_tick`, `final_hash`, `overall_outcome`) never populate a
  "combat_resolution" key. This is why Step 12 does **not** try to read a `combat_engagement_rate`
  field off `run_report.json` — no such field exists anywhere in the codebase. It is computed
  directly by the test from `simulation_events.jsonl`'s real `combat_engagement_started` event
  count, which is genuinely observable and varies with actual simulation behavior.
- **Content-singleton caching is not actually a risk for Step 12**, despite first appearances:
  `Kernel.__init__` unconditionally re-loads all content on every construction
  (`kernel.py:332-333` → `warmup.py:43-48`, confirmed no "already warm" short-circuit exists for
  the no-`repo`-arg call path). Do not add an unnecessary `ContentWarmupService.reset()` call
  between the two variant runs under the mistaken belief it's required — it isn't, though calling
  it defensively is harmless since the test runs under pytest.
- **`unit_faction_tension` was chosen over `resource_dense_basin`** (the pilot's own world)
  specifically because it has a real human+wolf population co-existing
  (`data/worlds/unit_faction_tension/resolved/world.resolved.yaml:111-141`, confirmed via direct
  read: `village_worker`/`frontier_guard`/`traveling_merchant`/`village_blacksmith` = human,
  `hungry_wolf`/`alpha_wolf` = wolf) — `resource_dense_basin` has no comparable multi-race combat
  population and would not exercise this ticket's change at all.

## Unresolved Questions

None. AC #3's approach (direct `MetamorphicRuleEngine.evaluate_rules()` validation, bypassing
`MutationLabOrchestrator`/`MutationEngine` entirely) is resolved and user-confirmed — do not
re-litigate it or attempt to extend `MutationEngine`'s `WorldSpec`/`ScenarioSpec`-only target
resolution. Every other design decision in this plan (the `RaceRelationRecord` schema shape, the
`RelationContext.source_race` addition, the upgrade-only/same-faction-guarded resolution logic in
`project_relation()`, the 12-race/66-pair coverage denominator with `slime` excluded, the 24-entry
authored subset and its rationale, the `RegionThreatClassifier` dead-code confirmation, the
no-feature-flag decision below, and the three parity ledger entries) is fully specified above with
first-hand code citations. Architecture-review should not block this plan on any open question —
there are none left.

## Feature Flag Decision

**No feature flag.** Reasoning:
1. Both consuming call sites (`legality.py`, `tactical.py`) already run in production today and
   already construct `RelationContext(target_race=...)` — this ticket gives meaning to an
   already-declared-but-inert field, not a wholly new code path with unknown blast radius.
2. The resolution logic is architecturally self-limiting: it only ever fires when a matching
   `race_relations` entry exists (24 of 66 populated pairs authored — the other 42 are pure
   no-ops by construction) and only ever tightens, never loosens, an existing label. The blast
   radius is scoped to the 12 authored race pairs, not universal.
3. test_plan.md's existing regression surface (9 combat/strategic/world test files, listed in
   full in `test_plan.md`'s Regression Surface section) explicitly guards that no currently-passing
   outcome changes for any pair without an authored entry — this is the functional equivalent of a
   flag's "off by default" guarantee, enforced by tests rather than a runtime switch.
4. Rollback, if ever needed, is a pure content change (empty or delete
   `race_relations.yaml`'s entries) with no code path to revert — lower operational risk than a
   typical flagged feature, where rollback requires a flag flip plus verification that the flag
   itself is wired correctly.
This differs from the `DEV-002` convention's typical target (large, novel, universally-active
gameplay systems); this ticket is closer in shape to `P2D-FACTION-RELS` (which also shipped
unflagged) than to a `DEV-002` candidate. If the user wants an extra safety net given this ticket's
"highest content risk in the roadmap" framing, the cheapest equivalent is a config toggle wrapping
only the new block in Step 6 (`if race_hostility_enabled(): ...`) — noted here as a documented
alternative, not implemented by default in this plan.

## Deviations

Implementer note (2026-09-01 execution): four deviations from this plan's literal text, all
discovered live during implementation/test execution, none changing the plan's design intent.

1. **Step 3's `validator_coverage=None`/`resolver_component=None` (Python `None`) fails a
   currently-passing test.** `tests/unit/content/test_content_usage_matrix.py::
   test_matrix_validation_and_states` asserts `entry.validator_coverage is not None` and
   `entry.resolver_component is not None` for every `CONTENT_USAGE_MATRIX` entry, with no
   `DESIGN_ONLY` exemption for these two fields (only `schema_class` has one). Every other entry
   in `src/content/matrix.py` that has no real validator/resolver uses the string `"None"`, not
   the Python `None` value (e.g. `foundation/attributes`'s `validator_coverage="None"`,
   `compatibility/legacy_enemy_projection`'s `resolver_component="None"`). Changed both fields to
   the string `"None"` to match this established convention and keep the test green — content and
   intent unchanged (still "no dedicated validator, no resolver component").
2. **Step 4's doc row placement.** The plan said "directly after the social/faction_relationships
   row (line 43)"; `docs/mechanics/content_usage_matrix.md`'s table is actually alphabetically
   sorted (confirmed both by inspection and by `generate_matrix_report()`'s own
   `sorted(CONTENT_USAGE_MATRIX.keys())` iteration), so the row was placed alphabetically —
   directly after `social/perspectives`, before `social/roles` — matching the file's real
   convention and the generator's own sort order. Row content is otherwise exactly as specified.
3. **Step 12 needed `@pytest.mark.resource_budget_large`, not mentioned in the plan.**
   `tests/conftest.py`'s `pytest_runtest_setup` enforces a per-test SIGALRM wall-clock budget
   (60s under the default `medium` `--resource-budget`); the real two-variant, 3-seed, 200-tick
   simulation run (~69s total) was killed mid-run by this budget on the first attempt, causing an
   incomplete `simulation_events.jsonl` and a spurious test failure unrelated to the
   metamorphic-validation logic itself. Added `@pytest.mark.resource_budget_large` (an existing,
   already-registered marker forcing the 600s/8GB budget regardless of the CLI default,
   `pyproject.toml:90`) alongside `@pytest.mark.slow`. No plan mechanics changed.
4. **Step 12's cleanup needed to go one level higher than the plan's four named directories.**
   `ScenarioRepository`/`ExperimentRepository`/`LabRunRepository` each write their own top-level
   index JSON (`scenario_index.json`/`experiment_index.json`/`lab_runs_index.json`) directly under
   `data/scenarios/`, `data/experiments/`, `data/lab_runs/` — one level above the per-item
   directories the plan named (`data/scenarios/race_hostility_metamorphic_check/`, etc.). After
   removing only the plan's four named directories, `git status` still showed
   `data/scenarios/`, `data/experiments/`, `data/lab_runs/` as untracked (containing only these
   leftover index files). Extended `_cleanup_created_dirs()` to also remove these three index
   files and `rmdir` the resulting empty parent directories — confirmed via `git status` showing a
   clean tree after the test runs. `data/lab_runs/race_hostility_baseline/` and
   `data/lab_runs/race_hostility_high/` (the plan's named subdirectories) are still removed first,
   unchanged from the plan.

Separately (not a deviation, an environment note): `graphify update .` was run per CLAUDE.md's
proactive-tool-use convention after the `src/`/`tests/` edits, but declined to write with
`WARNING: new graph has 34645 nodes but existing graph.json has 34656. Refusing to overwrite`,
recommending `--force`. This was not forced (a stale/concurrent-session graph state mismatch is
not this ticket's to resolve by overwriting) — flagged here for visibility, not treated as
blocking.
