---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-RACE-RELATIONS-MATRIX
artifact_type: investigation
tags: [faction, content, combat]
---

# Investigation — TCK-20260831-RACE-RELATIONS-MATRIX

## Current Behavior

### `RelationContext` / `RelationProjectionService` (`src/content_semantics/relation.py`)

`RelationContext` (`relation.py:13-21`) is a Pydantic `BaseModel` (`arbitrary_types_allowed=True`,
not frozen) with five optional fields: `distance`, `location`, `intruding`, `combat_engaged`,
`target_race`. `RelationProjection` (`relation.py:24-32`) is the return type: `label: str`,
`axes: Dict[str, str]`, `confidence: float = 1.0`, `relationship_model: Optional[str]`,
`source_records: List[str]`.

`RelationProjectionService.project_relation(perspective_id, source_faction_id, target_faction_id,
context=None)` (`relation.py:44-161`) does exactly four things, in order:
1. Resolve a `PerspectiveDefinition` by ID or by `chosen_faction` match (`relation.py:61-67`).
2. Resolve a `FactionRelationshipDefinition` by exact `(source_faction, target_faction)` match
   against `self.repo.faction_relationships` (`relation.py:73-82`).
3. Determine `label`: first from the perspective's `projected_labels` groups (ally/hostile/
   neutral/threat/intruder/opportunity/ignored/protected/trade/prey_or_threat_by_context)
   (`relation.py:87-120`, uses `context.intruding`/`context.combat_engaged`/`context.distance`
   here — but never `context.target_race`); if no perspective label, fall back to the
   relationship's `axes.get("hostility", ...)` (`relation.py:123-144`, same three context fields
   used, never `target_race`); if neither resolves, fall back to
   `FactionSemanticsService.is_hostile()` legacy bucket check (`relation.py:147-153`).
4. Return the `RelationProjection`.

**Confirmed: `context.target_race` is read nowhere in `project_relation()`'s body.** A full read of
the method (all 118 lines) shows `context.intruding`, `context.combat_engaged`, and
`context.distance` each referenced multiple times; `context.target_race` never appears. The field
is accepted on the model and silently dropped.

**Existing precedent for how another axis factors into the label — the pattern to follow:**
`context.combat_engaged`/`context.intruding`/`context.distance` are consumed as plain boolean/
numeric branch conditions inside the `if not label and relationship:` block (`relation.py:123-144`),
gating which string label a given `axes["hostility"]` qualitative value resolves to (e.g.
`hostility == "medium_contextual"` + `context.intruding` → `"threat"`; same axis value +
`context.combat_engaged` → `"enemy"`). A race-hostility factor should follow the same shape: resolve
a second catalog record (a `race_relations` entry keyed off `(source_race, target_race)` — analogous
to how `relationship` is resolved off `(source_faction_id, target_faction_id)` at step 2) and fold
its `axes.hostility` into the same label-resolution branch, most naturally by tightening (never
loosening) the faction-derived label — e.g. race hostility can upgrade `neutral`→`threat` or
`threat`→`enemy` but per AC #2 the observable requirement is only "two race pairs with different
authored hostility produce different projected labels," not a specific combination rule. Note
`get_race_id_str` (`src/content_semantics/faction.py:62-66`) returns `None` when
`entity.identity.properties` lacks a `race_id` key — a race-relations lookup must handle
`target_race=None` (or an unregistered race id) as a no-op fallthrough, not an error, matching the
existing `if not relationship:` graceful-miss pattern.

**Five real call sites reach `project_relation()`, only two of which construct a `RelationContext`
with `target_race` set:**
- `src/engine/legality.py:243-247` (`LegalityServiceV2.verify_attack_legality`) — sets
  `target_race=get_race_id_str(target)`. Reaches `project_relation()` indirectly via
  `FactionSemanticsService.is_hostile_compat()` (not read directly in this file — confirm
  `is_hostile_compat` forwards `context` unchanged into `project_relation()`; `faction.py:164,200`
  shows it does).
- `src/engine/tactical.py:212-216` (`TacticalDecisionSystem.evaluate_entity_intent`, hostiles-scan
  loop) — sets `target_race=get_race_id_str(n)` per neighbor `n`. Same `is_hostile_compat()` path.
- `src/world/region_threat_classifier.py:44,112,116-118,127-129`
  (`RegionThreatClassifier._classify_via_projection`) — **third live consumer, not in the ticket's
  Related Code Areas.** Its `context: Optional[RelationContext]` parameter is passed straight
  through from its own caller with no `get_race_id_str()` call anywhere in this file — confirmed via
  full read. It calls `project_relation()` twice (once for `controlling_faction_id`, once per
  `population_faction_ids` entry), both passing the same `context` object through unmodified. It
  will pick up race-hostility factoring "for free" once `project_relation()` consumes
  `target_race`, but only if *its own caller* ever populates `target_race` on the context it passes
  in — a grep for callers of `RegionThreatClassifier.classify()`/`_classify_via_projection()` should
  be part of Plan's scope check if region-threat race-awareness is claimed as in-scope; nothing in
  this ticket's AC requires it, and out-of-scope explicitly excludes anything beyond
  legality/tactical wiring, so this is a "gets it by construction, not by explicit test" case worth
  flagging rather than silently assuming tested.
- `src/engine/quests.py:133-135` (`_proj_service.project_relation(_perspective_id,
  _attacker_faction_id, _victim_faction_id, None)`) — passes `context=None` explicitly. No
  `target_race` involved; unaffected by this ticket unless `None` context handling in the new
  race-lookup step needs a null-guard (it does — see above).
- `src/content_semantics/faction.py:164,200` (`FactionSemanticsService.is_hostile_compat`) — pure
  passthrough, forwards whatever `context` its caller gives it into `project_relation()`. This is
  the shared path both `legality.py` and `tactical.py` route through.
- `src/engine/combat_rewards.py:91-98` (`RewardClassificationService.classify_defeated_target`,
  via `is_hostile_compat`) — constructs `RelationContext(combat_engaged=True)` only, no
  `target_race`. Unaffected unless Plan decides to also wire race here (not required by AC).

## Mechanics / Engine Constraints

- **Friendly Fire law** (`docs/mechanics/02_combat_laws.md:117`): "Faction allies do not take
  splash damage from their teammates." `LegalityServiceV2.verify_attack_legality` is the
  authoritative enforcement point (Logic IDs COMB-004/005/256-258, `legality.py:190-269`) — any
  race-hostility factor that feeds into `is_hostile_compat()` here directly participates in combat
  legality, not just flavor text. A race-relations entry that resolves to `"enemy"` between two
  same-faction entities would need to not silently break the "faction allies" invariant — Plan
  should confirm whether same-faction friendly-fire law takes precedence over race hostility, or
  whether race hostility is only consulted after faction-level neutrality is already established
  (current code structure: race lookup would live inside the *relationship-axes* fallback branch,
  step 3 above, which only runs when a `FactionRelationshipDefinition` exists between the two
  factions — same-faction pairs have no `faction_relationships` entry by construction in this repo
  today, per `test_faction_relationships_coverage.py`'s neutral-entry note, so same-faction
  short-circuit risk is low but not zero and worth Plan calling out explicitly).
- **WORLD-SEM-003/004** (`docs/content/content_semantics_contract.md:58,66,122`): the
  `RelationProjectionService` contract doc already lists `target_race` as a `RelationContext`
  field but documents zero consumption behavior for it — this is the doc that must change once
  consumption is wired (see Docs Requiring Update).
- **WORLD-CAT-004/005** (`src/content/repository.py:1,14-19`): content must be fully loaded before
  any kernel tick begins; `CatalogRepository.load_all()` raises `ContentHotPathViolation` if called
  mid-tick. A new `race_relations` `ContentFamilySpec` loads through the same `load_all()` path as
  every other family — no special-casing needed, but confirms the new content file must be present
  at world-load time, not lazily resolved during a tick.

## Docs Requiring Update

- `docs/content/content_semantics_contract.md`: the "Projection contract" section for
  `RelationProjectionService` (lines 56-68) documents `target_race` as an accepted-but-unused
  `RelationContext` field; once `project_relation()` actually consumes it to resolve a
  `race_relations` entry and factor `axes.hostility` into the label, this section's prose must
  describe that new resolution step (mirroring how the existing "faction relationship" resolution
  step is already described at a high level in this same section).
- `docs/mechanics/content_usage_matrix.md`: this is the rendered doc mirror of
  `CONTENT_USAGE_MATRIX` in `src/content/matrix.py` — every `CANONICAL_FAMILIES` entry in
  `src/content/repository.py` has a corresponding row here (confirmed via the existing
  `living/races` row at line 38, matching `matrix.py:246-249`'s `social/faction_relationships`
  entry shape). A new `social/race_relations` (or `living/race_relations`, per Plan's chosen family
  namespace) row must be added — `tests/unit/content/test_content_usage_matrix.py` exists
  specifically to police `CANONICAL_FAMILIES` vs. `CONTENT_USAGE_MATRIX` parity (per
  `TCK-20260604-PHASE21-FAMILY-REGISTRY` / `TCK-20260627-P2K-CONTENT-MATRIX`'s stated purpose:
  "Adding a new YAML file to `data/content/` requires manually registering the family in
  `ContentUsageMatrix`").
- `docs/parity_ledger/combat_movement.yaml`, `docs/parity_ledger/social_narrative.yaml`,
  `docs/parity_ledger/strategic_cognition.yaml`: explicitly required by this ticket's Scope — see
  Parity Ledger Overlap below for the specific new-entry IDs and rationale per file.

The `docs/content/pipeline_contract.md` ContentUsageMatrix description (path:
`docs/content/pipeline_contract.md`, under `docs/content/`) is not required to change for this
ticket: it describes `ContentUsageMatrix`'s role in general terms ("tracks implementation status for
every content family... single source of truth") without enumerating individual families, so adding
one more family requires no prose change there — only the per-family row in
`content_usage_matrix.md` and the registry in `matrix.py` itself.

The `docs/mechanics/06_worldbuilding_foundation.md` entity-archetype mention (path:
`docs/mechanics/06_worldbuilding_foundation.md`, under `docs/mechanics/`) is not required to change:
its one race-adjacent line (186) describes entity archetypes linking to races/factions generically
and does not describe race-to-race relationships or hostility resolution — out of this ticket's
scope per the ticket's own Out of Scope section (no change to entity archetype content).

## Parity Ledger Overlap

Next free IDs confirmed by tailing each file (`grep -c "^- id:"` / last `- id:` line):
- `docs/parity_ledger/combat_movement.yaml` — 316 entries, last ID `COMB-316`
  (`TCK-20260831-CAPABILITY-DRIVEN-TARGETING`, `tactical.py` target-score sort-tuple change).
  **Next free ID: `COMB-317`.** This is the entry for the legality-path race-hostility wiring
  (`legality.py:243-247` consumption) — P0 candidate since it's a live combat-legality gate
  (Friendly Fire law), requiring a passing `test_path`.
- `docs/parity_ledger/social_narrative.yaml` — 277 entries, last ID `SOC-256`
  (`ClanState` schema addition). **Next free ID: `SOC-257`.** Candidate entry for the
  `race_relations` content family itself (schema/loader, analogous to how
  `faction_relationships.yaml` content changes are tracked as social-narrative-adjacent — though
  note P2D-FACTION-RELS's own investigation found *no* parity ledger entry covers
  `faction_relationships.yaml` content counts, treating it as "purely additive content, not
  behavior" — Plan should decide whether the same reasoning applies here or whether the *new
  consuming logic* (not the content) is what earns the SOC entry).
- `docs/parity_ledger/strategic_cognition.yaml` — 263 entries, last ID `STRAT-262`
  (habit-bias ActionStyle wiring). **Next free ID: `STRAT-263`.** Candidate entry for the
  tactical-path race-hostility wiring (`tactical.py:212-216` consumption feeding into hostile-scan
  target classification, upstream of `target_score()`'s sort tuple).

None of `COMB-316`, `SOC-256`, `STRAT-262` (the current tails) mention race relations or
`target_race` — this is genuinely new ground on all three ledgers, not an existing entry to update
in place.

## Prior Work

- **`TCK-20260627-P2D-FACTION-RELS`** (`stored_artifacts/TCK-20260627-P2D-FACTION-RELS/`): the
  direct coverage-subset precedent this ticket must follow.
  - Started at 14 existing `faction_relationships.yaml` entries, 16 factions (120 directed pairs
    excluding self-pairs). AC was "≥30 entries, ≥10 hostile" — not full coverage.
  - Authored exactly 20 new directed entries (plan.md's table, all with explicit
    `relationship_model` + `axes.hostility`), landing at 34 total, ~20 hostile. Rationale
    documented as "covering high-encounter-frequency pairs" — i.e., pairs between factions that
    actually co-populate in scenarios, not a uniform/random sample.
  - Investigation flagged 5 factions with zero incoming/outgoing relationships at the time
    (`hero_guild`, `arcane_circle`, `swamp_tribe`, `dragon_cult`, `spirit_court`) as the acknowledged
    gap, left explicitly unaddressed with the reasoning that 50%-of-all-pairs was infeasible and the
    AC's intent was read as "high-priority/high-encounter pairs," not full coverage — this
    "disclosed, not uniform, with explicit gap acknowledgment" shape is exactly what this ticket's
    AC #4 asks for.
  - **Current state has moved on**: `data/content/social/faction_relationships.yaml` now has **75**
    entries (not 34) — later tickets (`TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`/COMB-294,
    plus an AC#3 `neutral_to_town_council` addition) added further pairs, including all 5 previously-
    zero factions. A follow-on test file,
    `tests/unit/content/test_faction_relationships_coverage.py`, now enforces a **≥33 populated-pair
    threshold graded against a 12-faction "populated-only" 66-pair denominator** (`POPULATED_FACTIONS`
    excludes `moon_cult`, `dwarven_mine_clan`, `dragon_cult`, `neutral` as having "zero module path
    to population"). **This is the concrete precedent-of-precedent for how to state a defensible
    subset with a hard test guard** — Plan should consider an analogous "populated-only" or
    "actually-spawnable-races" denominator for the 13-race roster (156 raw pairs) rather than
    grading against the full 13×12, if some races (e.g. `spirit`, `slime`) have limited or no live
    spawn path today. That should be verified against `entity_archetypes.yaml`/`populations.yaml`
    race references before Plan commits to a denominator.
- **`TCK-20260831-METAMORPHIC-LAB-PILOT`** (`stored_artifacts/TCK-20260831-METAMORPHIC-LAB-PILOT/`):
  hard prerequisite, confirmed landed (`tickets/done/TCK-20260831-METAMORPHIC-LAB-PILOT.md` exists).
  Its investigation confirmed the exact runnable CLI shape
  (`python -m src.lab.cli run-mutation <mutation_id> --experiment <experiment_id>`), the
  `MutationSpec`/`MutationItem`/`ExpectedRelationshipSpec` schema shapes, and used a
  `target: "resources.res_0.regen_rate"` / `operation: "multiply"` mutation against a real
  `WorldSpec.resources` (`ResourceNodeSpec`) field. **This is a WorldSpec-field mutation, not a
  content-catalog mutation** — see Risks below for why this pattern does not directly transfer.

## Risks and Open Questions

1. **BLOCKING — content-catalog mutation is not precedented in the mutation lab tooling and the
   current code cannot address it via `MutationSpec.target`.** Full read of
   `MutationEngine.apply_mutations` (`src/lab/mutation.py:181-262`): for every `MutationItem`, it
   takes `target.split(".")[0]` and requires that first segment be a member of either
   `WorldSpec.model_fields` or `ScenarioSpec.model_fields` (`mutation.py:206-213`) — any other root
   segment hits the `else` branch and produces a `FAILED` `MutationApplyReport` (or raises under
   `strict=True`, which `VariantMatrixBuilder.build_matrix` always uses, `mutation.py:464`). A
   `race_relations.yaml` content-catalog file is loaded entirely separately via
   `CatalogRepository`/`ContentFamilySpec` (`src/content/repository.py`) — it is not part of
   `WorldSpec` or `ScenarioSpec` at all, and `WorldSpec`'s own fields (`topology`, `regions`,
   `factions`, `entities` (`PopulationSpec`, references `race`/`faction` by ID string only, not
   hostility axes), `resources`, `buildings`, `quest_definitions`, `validation`, `budgets` —
   `src/worldbuilding/schema.py:230-244`) have no field that reaches into race-relations hostility
   values. **This means AC #3 ("Run `MutationLabOrchestrator.run_mutation_lab()` against a real
   mutation spec varying race-relations hostility") cannot be satisfied by pointing `target` at the
   new content file the way the pilot pointed at `resources.res_0.regen_rate` — the mechanism is
   structurally WorldSpec/ScenarioSpec-only today.** This is a real open question for Plan, not an
   implementation detail: either (a) extend `MutationEngine.apply_mutations` to recognize a third
   target root that resolves against the loaded `CatalogRepository`/a content YAML file path
   (non-trivial — `modify_nested_dict` and the whole variant-write/reload pipeline in
   `VariantMatrixBuilder.build_matrix` assume `WorldSpec`/`ScenarioSpec` reconstruction via
   `model_validate`, not arbitrary catalog file rewriting), or (b) find an indirect WorldSpec-level
   lever that changes *effective* race-hostility outcomes without mutating the content file directly
   (no such lever currently exists — hostility axes live only in catalog content), or (c) scope AC
   #3 down to a lighter-weight validation that doesn't require the full `MutationLabOrchestrator`
   content-catalog path (would conflict with the ticket's literal AC wording as scoped and should be
   raised as a scope question rather than assumed). **This should not be resolved silently by
   Investigate or Plan picking (a)/(b)/(c) unilaterally — flag for explicit confirmation before
   implementation, since it changes mutation-lab infrastructure scope, not just content authoring.**
2. **Same-faction friendly-fire interaction** (see Mechanics section above) — low risk given current
   content has no same-faction `faction_relationships` entries, but not structurally impossible;
   Plan should state explicitly whether race hostility is scoped to only ever tighten (never
   loosen) an existing faction-derived label, to avoid accidentally creating a friendly-fire hole.
3. **`region_threat_classifier.py` race-awareness "for free"** (see Current Behavior) — this file's
   callers were not traced in this investigation (out of the Related Code Areas list, and outside
   this ticket's explicit AC). If any caller ever sets `target_race` on the `RelationContext` it
   passes to `RegionThreatClassifier.classify()`, region-threat labels would silently start
   reflecting race hostility once `project_relation()` consumes the field — with zero test coverage
   from this ticket's own AC. Plan should either explicitly confirm no live caller sets
   `target_race` there today (low cost — one more grep) or note the behavior-change surface.
4. **13-race roster denominator**: confirmed 13 races in `data/content/living/races.yaml` (human,
   wolf, goblin, spider, orc, elf, dwarf, undead, troll, lizardfolk, dragonkin, slime, spirit) — 13×12
   = 156 directed pairs excluding self-pairs, matching the ticket's "156 directed race pairs" claim
   exactly. Whether all 13 have a live spawn/population path (parallel to faction_relationships'
   "populated-only" precedent) was not verified in this investigation — Plan should cross-check
   against `entity_archetypes.yaml`/`populations.yaml` race references before committing to a
   coverage denominator, per Prior Work note above.

## Anti-Drift Hazards

- **Do not add fields to `RaceRelationRecord` beyond `id`/`source_race`/`target_race`/
  `relationship_model`/`axes` (plus inherited `CatalogBaseDefinition` optionals)** —
  `CatalogBaseDefinition` is `extra="forbid"` (`schema.py:8-10`), confirmed identical to
  `FactionRelationshipDefinition`'s own convention. A `Dict[Tuple[str,str], float]` shape (the
  roadmap concern text's stale suggestion) would not even be valid YAML/Pydantic-list content in
  this repo's convention — every other content family is a flat list of records with a string `id`.
- **Do not use `DiplomaticState` enum values as axis values** — same hazard P2D-FACTION-RELS flagged
  for faction relationships; `axes` values are free-form descriptive strings ("high", "medium_
  contextual", etc.), not runtime enum members.
- **Do not let race hostility bypass the Friendly Fire law** — same-faction entities must not become
  attackable via race-hostility alone; see Risk #2.
- **Do not silently pick a mutation-lab extension strategy** for AC #3 without flagging it — see
  Risk #1; this is the single highest-uncertainty item in the whole ticket and the one most likely
  to blow up scope if guessed wrong.
- **Do not touch `faction_relationships.yaml` itself** — ticket's Out of Scope is explicit; race
  relations reuses only the *schema convention* (flat list, `CatalogBaseDefinition` subclass,
  `extra="forbid"`), not the file or its content.
- **`region_threat_classifier.py` is not in Related Code Areas and has no AC coverage** — do not
  scope-creep into wiring race-awareness there; if it changes behavior "for free" per Risk #3, that
  needs to be disclosed, not silently expanded into new test surface beyond what AC #2 requires
  (legality + tactical only).
