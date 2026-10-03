---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-CAMPSTATE-PLACE-BRIDGE
artifact_type: investigation
tags: [content, architecture]
---

# Investigation — TCK-20260904-CAMPSTATE-PLACE-BRIDGE

## Current Behavior

### PlaceState/PlaceKind construction is already fully generic (confirmed, not just claimed)

`WorldCompiler.compile()` (`src/worldbuilding/compiler.py:236-330,695-713`) already constructs a real
`PlaceState` for **any** `PlaceKind`, including `CAMP` and `NEST` — there is nothing camp/nest-specific
missing here:

- `src/worldbuilding/compiler.py:280` initializes `places: Dict[str, PlaceState] = {}`.
- `src/worldbuilding/compiler.py:319-330`, inside the `for r_spec in spec.regions:` loop, iterates
  `getattr(r_spec, "places", [])` and constructs `PlaceState(place_id=..., region_id=r_spec.id,
  kind=PlaceKind(p_spec.kind), position=..., footprint=..., owner_faction_id=..., scale=...,
  maturity=..., hazard_level=...)` for every declared `PlaceSpec`, unconditional on kind.
- `src/worldbuilding/compiler.py:342` sets `RegionState.places=[p_spec.id for p_spec in ...]` (the
  forward half of the dual-sided membership pattern).
- `src/worldbuilding/compiler.py:702` passes `places=places` into the final `AuthoritativeState(...)`.
- **Both compilation paths converge on this single call.** The Composition path
  (`src/worldassembly/resolver.py:800-824`, `resolve_module_contribution()`) converts
  `RegionRecipeSpec.places` (`PlaceRecipeSpec`) → `RegionSpec.places` (`PlaceSpec`), namespaced by the
  module `prefix`, exactly mirroring the Direct path's `PlaceSpec` shape — confirmed by
  `tests/unit/worldassembly/test_resolver.py::test_resolve_module_contribution_wires_place_shaped_region`.
  `docs/world/compiler_contract.md`'s own "Two Compilation Paths" table and `cli.py:282`
  (`WorldCompiler.compile(spec, seed=seed, ..., context=context)`) confirm the Composition-built
  `WorldSpec` is compiled through the identical `WorldCompiler.compile()` entry point — there is no
  separate `AuthoritativeState` construction site to duplicate wiring into.
- **Real, live proof this already works for `CAMP` today:** `data/worlds/hero_guild_routing/resolved/world.resolved.yaml`
  (region `goblin_camp`, lines 37-54) already declares `places: [{id: goblin_camp_place, kind: CAMP,
  position: [110, 38]}]`, and `tests/unit/worldbuilding/test_place_wiring.py::test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds`
  asserts `state.places["goblin_camp_place"].kind == PlaceKind.CAMP` compiles correctly against this
  real content today. **Ticket AC #2 ("`WorldCompiler.compile()` constructs `PlaceState(kind=CAMP)` and
  `PlaceState(kind=NEST)` instances... for both Direct and Composition paths") is therefore already
  satisfied by existing code — this ticket adds nothing new on the `PlaceState` side.** The real
  remaining gap, confirmed below, is entirely on the `CampState` side.

### CampState / CampService — confirmed still no production construction path, post-sibling-ticket

- `CampState` (`src/core/state.py:1233-1265`) now carries 8 fields:
  `id: str`, `kind: str` (creature-flavor string, e.g. `"goblin"`, `"wolf"` — **not** `PlaceKind**),
  `position: tuple[float,float]`, `maturity: float`, `active: bool`, `faction: str = "hostile"`,
  `last_raid_tick: int`, plus the 3 new scaffolding fields from the sibling ticket:
  `totem_tier: int = 0`, `stockpile: float = 0.0`, `palisade_integrity: float = 0.0`.
- `grep -rn "CampState(" src/ tests/` confirms **zero production call sites** — every `CampState(...)`
  construction is inside a test file (`test_camp_lifecycle.py`, `test_creature_territory_lifecycle.py`,
  `test_world_dynamics.py`, `test_natural_creature_reproduction.py`,
  `test_apply_plan_builder.py`). The sibling ticket's own "Anti-Drift Notes" ("no `CampState`
  construction") and `test_nest_branch_does_not_construct_new_campstate` both confirm this is
  deliberate and still holds after that ticket landed.
- `WorldCompiler.compile()`'s final `AuthoritativeState(...)` call (`compiler.py:695-713`) does **not**
  pass `camps=`, so `AuthoritativeState.camps` (`state.py:1290`, `field(default_factory=dict)`) is
  always `{}` out of world-gen — confirmed directly, not inferred.
- `CampUpdate` (`src/core/updates.py:891-911`) has a full apply path
  (`src/engine/apply_plan.py:275-291`, `src/engine/apply.py`) including the 3 new fields the sibling
  ticket wired through — but there is no corresponding `PlaceUpdate` class anywhere (`grep -n "class
  PlaceUpdate" src/core/updates.py` → no match) and no `PlaceState` handling in `apply.py`/
  `apply_plan.py` at all. The apply-path asymmetry (Camp fully wired, Place entirely absent) is
  expected at this stage — no ticket has yet needed to mutate a `PlaceState` post-construction.

### CampService's real consumers, and what "wiring the bridge" actually activates

`CampService.process_camps()` (`src/world/camp.py:22-137`) and
`CreatureTerritoryService.process_territories()` (`src/world/creature_territory.py:36`, out of scope
for code changes but a real second consumer of `state.camps`) both iterate `state.camps.items()` /
`state.camps.values()`. Both are wired into the per-tick pipeline in `src/engine/world_dynamics.py`:

- `CampService.process_camps()` — `world_dynamics.py:167-168`, called **every tick, unconditionally,
  with no feature flag** (only the Nest-vs-raid *sub-choice* inside it is gated by
  `ENABLE_CAMP_NEST_SPREAD`; the raid branch and monster-spawn branch themselves are not gated at all).
- `CreatureTerritoryService.process_territories()` — `world_dynamics.py:205-211`, gated behind
  `ENABLE_CREATURE_TERRITORY_LIFECYCLE` (default `OFF`).

Because `state.camps` has been empty in every real compiled world to date, both of these have been
**dead code in production** — the loops run zero iterations. Once this ticket seeds even one real
`CampState` at world-compile time (option a) or migrates `CampService` onto real `PlaceState` content
(option b), `CampService`'s maturity growth / monster spawning / raid-triggering **activates live and
unconditionally** for any world containing Camp/Nest-kind content — this is a real, immediate gameplay
behavior change, not merely infrastructure wiring, and is flagged explicitly under Risks below.

### The creature-race data gap — confirmed via real content, blocks both options equally

Neither `PlaceRecipeSpec` (`src/worldbuilding/recipe.py:15-32`) nor `PlaceSpec`
(`src/worldbuilding/schema.py:37-61`) has any field carrying a creature-race string (e.g. `"goblin"`,
`"orc"`, `"wolf"`). Their 7 fields (`id`, `kind`, `position`, `footprint`, `owner_faction_id`, `scale`,
`maturity`, `hazard_level`) map cleanly onto `PlaceState`'s City/Ruin/Dungeon fields, but none of them
is the creature-flavor value `CampState.kind` needs (`CampService.process_camps()` reads `camp.kind`
directly for spawn archetype selection — `"goblin_warrior" if camp.kind == "goblin" else
"orc_warrior"` — and for `NEST_RACE_KINDS` membership). Confirmed against the one real `CAMP`-kind
Place already on disk (`data/worlds/hero_guild_routing/resolved/world.resolved.yaml`'s
`goblin_camp_place`): its YAML has only `id`/`kind`/`position`, nothing that could seed
`CampState.kind`. Both `PlaceRecipeSpec` and `PlaceSpec` are Pydantic models with
`extra="forbid"`/frozen configs, so this cannot be smuggled through an untyped extra field — a new,
explicit, typed field is required regardless of which architecture option is chosen. Nothing in
`docs/brainstorm/rpg_expected_schemas.html#schema-66`'s Place schema table anticipates this field
either (confirmed via `search_docs`/direct read — the table lists exactly the 7 fields already on
`PlaceState`).

### `AuthoritativeState.places` immutability gap (pre-existing, unrelated ticket's territory, flagged for awareness)

`AuthoritativeState.to_readonly()` (`state.py:1405-1449`) wraps `camps=ReadOnlyDict(self.camps)`
(`state.py:1426`) but does **not** wrap `places` in any read-only container — `places` is passed
through unwrapped in the `replace(self, ...)` call. This is a real, pre-existing gap from the Place
schema/wiring lineage (`TCK-20260902-PLACE-SCHEMA-MIGRATION`/`WORLDCOMPILER-PLACE-WIRING`), not
introduced or required to be fixed by this ticket — `CanonicalStateHasher` (which does cover `places`,
confirmed by `test_place_participates_in_canonical_hash`) is the mechanism that actually enforces
Place-state determinism today, not `to_readonly()`'s shallow-freeze. Flagged under Anti-Drift Hazards;
not in this ticket's scope to fix.

## Mechanics / Engine Constraints

- `docs/mechanics/05_world_evolution.md` §6 "Camp/Nest Classification & Nest Spread" (added by the
  sibling ticket) is the authoritative source for which races are Camp (goblin, orc), Nest (wolf,
  spider, troll, slime), City (human, elf, dwarf, lizardfolk), or Excluded (undead, spirit, dragonkin).
  Any new content-schema field this ticket adds to carry creature-race data must stay consistent with
  this table — it must accept exactly the Camp/Nest race set, not an arbitrary string.
- `docs/mechanics/06_worldbuilding_foundation.md` (declarative topology / Ch. 06) has **zero** mention
  of `PlaceState`/`PlaceKind` today (confirmed via grep) — this predates this ticket (the earlier idea
  66 tickets never backfilled this chapter either) and is out of this ticket's scope to backfill
  wholesale; see Docs Requiring Update for the narrower, in-scope doc touches.
- `docs/world/raid_boss_camp_contract.md`'s "Camp" section (`## Camp — camp.py`) documents growth,
  spawning, raid trigger, the Nest fork, and classification — but has no subsection describing how (or
  whether) a `CampState` ever gets constructed at world-gen. This is the doc most directly affected by
  whichever option is chosen.
- `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-109` `divergence_note` currently reads: *"camp_constructed
  has no viable engine path... camps are pre-placed at world generation and CampService... only evolves
  existing camps"* — this premise ("camps are pre-placed at world generation") is **currently false**
  (confirmed above: zero production `CampState` construction exists). Implementing this ticket, under
  either option, makes that clause true for the first time — the entry needs re-verification/rewording
  once implemented, independent of which option is chosen.

## Docs Requiring Update

- `docs/world/raid_boss_camp_contract.md`: needs a new subsection under "## Camp — camp.py" (or a
  cross-reference into it) describing the world-gen construction path once implemented — currently this
  doc documents only the tick-to-tick evolution of a `CampState` that today never exists in a real
  compiled world; readers have no way to learn how one comes to exist.
- `docs/parity_ledger/world_dynamics.yaml`: `WORLD-109`'s `divergence_note` asserts "camps are
  pre-placed at world generation" — false today, becomes (at least partially) true once this ticket
  ships; the entry's `status`/`divergence_note`/`v2_evidence` need re-verification against the
  as-implemented behavior (this may resolve the divergence entirely, or may need a new/updated entry —
  Plan should decide the exact mechanics, not just leave the stale text in place).
- `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md`: item 2 ("Idea 45's insertion
  point... `CampState` is never constructed anywhere in production code, `WorldModuleSpec` has no
  `camp_recipes` field, and the compiler has no camp step at all... needs a new schema field plus a new
  compiler step") is the exact stale framing this ticket's own Request Summary calls out for
  correction — idea 66's Place hierarchy already supplies the generic `PlaceState(kind=CAMP/NEST)`
  insertion point (confirmed above); only a narrow race-kind field is still missing, not a whole new
  schema/compiler step. This doc is explicitly named in the ticket's own "Related Docs" for this
  correction.
- Whichever content-authoring schema doc documents `PlaceRecipeSpec`/`PlaceSpec` field lists (currently
  only `docs/world/compiler_contract.md:53`'s one-line summary, which does not enumerate individual
  optional fields today) needs the new creature-race field added if/when it's introduced — Format 1
  here is conditional on Plan actually choosing to add that field, which is a near-certainty given the
  confirmed schema gap above, but the exact field name/doc location is Plan's call.

The `docs/mechanics/06_worldbuilding_foundation.md` chapter (path:
`docs/mechanics/06_worldbuilding_foundation.md`, under `docs/mechanics/`) is not required to change for
this ticket: it has never documented `PlaceState`/`PlaceKind` at all, even through two prior Place
tickets, and backfilling that pre-existing gap wholesale is out of this ticket's narrower Camp/Nest
bridging scope.

The `docs/brainstorm/rpg_expected_schemas.html` schema-66 table (path:
`docs/brainstorm/rpg_expected_schemas.html`, under `docs/brainstorm/`) is not required to change for
this ticket: it is a design-tracking/brainstorm artifact documenting the originally-proposed shape, not
a live contract this ticket is bound to keep in sync — the CAMP-NEST-CLASSIFICATION precedent did not
touch it either for a comparable schema addition (totem/stockpile/palisade fields on `CampState`).

## Parity Ledger Overlap

- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-109` (priority P1, status `verified`): directly
  overlaps, see Docs Requiring Update above. Not P0, so a passing `test_path` is not hard-required, but
  should still be kept accurate.
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-124` (priority P2, status `verified`, from the
  sibling ticket): documents `CampState`/`CampUpdate`'s current shape and explicitly notes "No new
  `CampState` is constructed anywhere in this branch (WORLD-109 remains true)" — this ticket is exactly
  the follow-on that makes that clause stop being true; `WORLD-124`'s text does not itself need editing
  (it accurately describes the sibling ticket's own scope, which didn't change), but Plan should be
  aware the next reader of `WORLD-124` needs `WORLD-109`'s corrected text to understand the full
  picture.
- No P0 entries found overlapping this ticket's scope (`WORLD-109`/`WORLD-124` are P1/P2) — no
  pre-existing hard test-path gate blocks this work, but new tests are still required per Acceptance
  Criteria regardless.

## Prior Work

- `TCK-20260902-WORLDCOMPILER-PLACE-WIRING` (`stored_artifacts/TCK-20260902-WORLDCOMPILER-PLACE-WIRING/`):
  the direct precedent for the exact insertion-point pattern this ticket must mirror — its `plan.md`'s
  8 ordered steps (add `PlaceRecipeSpec`/`PlaceSpec` fields → wire resolver → wire `WorldCompiler.compile()`
  → verify Composition-path convergence → tests in `test_place_wiring.py`/`test_resolver.py` → update
  `compiler_contract.md` → add a parity entry) is the template this ticket's `plan.md` should follow for
  whatever new field/construction step it adds.
- `TCK-20260902-PLACE-SCHEMA-MIGRATION`: established `PlaceState`/`PlaceKind`'s shape, including the
  `maturity: Optional[float]` field explicitly documented as "reused from CampState.maturity" — direct
  confirmation that a Camp/Nest ↔ Place semantic link was always intended, just not built yet.
- `TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT`: migrated the real `hero_guild_routing` world's
  `goblin_camp` region to a `CAMP`-kind Place (`goblin_camp_place`) — this is the one real, live
  `PlaceState(kind=CAMP)` in the whole content corpus today, and it has no creature-race data attached,
  concretely demonstrating the schema gap identified above.
- `TCK-20260904-CAMP-NEST-CLASSIFICATION` (just landed, sibling): resolved the City/Camp/Nest/Excluded
  classification rule (documented in `docs/mechanics/05_world_evolution.md` §6), added
  `CampService.NEST_RACE_KINDS`, the `ENABLE_CAMP_NEST_SPREAD` flag-gated Nest-spread branch, and the 3
  new `CampState`/`CampUpdate` scaffolding fields (`totem_tier`, `stockpile`, `palisade_integrity`) with
  a full `apply_plan.py` commit path. Its own Anti-Drift Notes and Out of Scope section explicitly
  forbid `CampState` construction and any `WorldCompiler`/world-generation change — this ticket picks up
  exactly where it left off, per both tickets' own Related Tickets cross-references.
- `TCK-20260831-CREATURE-TERRITORY-LIFECYCLE`: built `CreatureTerritoryService`, the second (flag-gated)
  consumer of `state.camps` — its own docstring frames it as "an intentionally separate, parallel
  per-entity territory mechanism," which this ticket's Out of Scope section correctly preserves by
  forbidding `CreatureTerritoryService` code changes; see Risks below for why that scope line does not
  fully insulate it from this ticket's effects.

## Risks and Open Questions

1. **Option (b) — CampService migrating onto PlaceState directly — appears infeasible within this
   ticket's own stated Out of Scope line.** `CreatureTerritoryService.process_territories()`
   (`src/world/creature_territory.py:36`) reads `state.camps.values()` directly, exactly like
   `CampService`. Option (b) as described in Scope ("migrate CampService to operate on PlaceState
   directly... retiring the separate AuthoritativeState.camps dict") would leave
   `CreatureTerritoryService` reading an always-empty, permanently-retired `camps` dict — silently
   breaking it (not merely "out of scope," but a real regression) unless `CreatureTerritoryService` is
   also migrated, which the ticket's own Out of Scope line ("`CreatureTerritoryService` changes")
   forbids. **Recommendation: choose option (a)** (companion `CampState` construction, `CampService`
   unchanged) — it is the only option consistent with the ticket's own scope boundaries, has the
   smaller blast radius the Scope section already flags, and matches the AC's own asymmetric wording
   ("If option (a): existing CampService tests continue to pass unmodified" vs. "If option (b): all
   existing CampState call sites are updated consistently" — the AC author already anticipated (a) as
   the more natural fit). This is a strong recommendation with direct evidence, but remains Plan's
   formal call per this ticket's own Scope section.
2. **The creature-race content-schema gap (see Current Behavior) blocks option (a)'s companion
   `CampState` construction from being meaningful, not just cosmetic.** Without a race-kind field
   somewhere in `PlaceRecipeSpec`/`PlaceSpec`, a companion `CampState` could only be built with a
   placeholder/default `kind` value, which would not correctly drive `CampService`'s
   `NEST_RACE_KINDS` branch or spawn-archetype logic for real content. Plan must decide: (i) add a new
   typed field (e.g. `creature_kind: Optional[str]`, Camp/Nest-only) to both `PlaceRecipeSpec` and
   `PlaceSpec`, validated against the classification table's Camp+Nest race set
   (`{goblin, orc, wolf, spider, troll, slime}`), or (ii) some other mechanism. This is a genuine open
   question requiring an explicit decision, not an assumption.
3. **Whether real content (`hero_guild_routing`'s `goblin_camp_place`) needs migrating in this ticket,
   or is left as a synthetic-spec-only mechanism with real-content migration deferred.** The
   `PLACE-MIGRATION-STAGE-*` tickets treated "wire the mechanism" and "migrate real content to use it"
   as separate, sequenced tickets. This ticket's own Acceptance Criteria only require the mechanism +
   tests proving non-Camp content is unaffected — they do not explicitly require updating
   `goblin_camp_place`'s YAML with a creature-race value. Recommend treating real-content migration as
   optional/stretch for this ticket (flag explicitly in `plan.md` either way) rather than assuming it's
   required.
4. **`CampService.process_camps()` is not feature-flag-gated at all** (only the Nest-vs-raid
   sub-choice inside it is). Implementing either option activates live raid-triggering and
   monster-spawning behavior, unconditionally, for any world with Camp/Nest content, the moment such a
   world is compiled after this ticket ships — this is a genuine gameplay/balance change, not just an
   infrastructure change, and should be called out explicitly to Plan/the user rather than treated as
   an implicit side effect of "wiring."
5. **Faction field semantics differ between `CampState.faction: str` (default `"hostile"`, free-form
   narrative string) and `PlaceState.owner_faction_id: Optional[int]` (a `Faction` IntEnum id).** If
   option (a) constructs a companion `CampState`, Plan needs to decide how (or whether) to derive
   `CampState.faction` from `PlaceState.owner_faction_id` — a simple constant default (`"hostile"`,
   matching the dataclass default and Camp/Nest content's inherently-hostile nature) is likely
   sufficient, since no real content today sets `owner_faction_id` on any Place, but this should be an
   explicit plan.md decision, not silently assumed.

## Anti-Drift Hazards

- Do not re-implement or duplicate the generic `PlaceState(kind=...)` construction loop in
  `compiler.py:319-330` — it already handles `CAMP`/`NEST` correctly. The only new code belongs in a
  narrow, additive branch keyed on `p_spec.kind in {"CAMP", "NEST"}` (or equivalent), not a parallel
  compilation pass.
- Do not touch `src/world/creature_territory.py` — explicitly out of scope, per both this ticket and the
  sibling ticket's Out of Scope lines. It will begin receiving real data as a side effect of seeding
  `state.camps`, which is expected and acceptable, but its code must not change.
- Do not re-open or re-decide the City/Camp/Nest/Excluded race classification — that is
  `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s already-closed, already-documented decision
  (`docs/mechanics/05_world_evolution.md` §6). This ticket only needs a way to *carry* that
  already-decided race-kind value from content into `CampState.kind` — not to re-derive it.
- Do not add accrual/effect logic for `totem_tier`/`stockpile`/`palisade_integrity` — these remain
  explicitly provisional scaffolding per the sibling ticket's own scope; a companion `CampState`
  constructed by this ticket should leave them at their dataclass defaults unless a real value is
  genuinely available from content.
- Preserve the `camps=ReadOnlyDict(self.camps)` wrapping in `to_readonly()` for any newly-constructed
  camps — do not accidentally bypass immutability for the new construction path (this is the one place
  `places`'s existing gap, noted above, would be easy to accidentally replicate for `camps` too if the
  construction logic is copy-pasted carelessly).
- If a new content-schema field is added to `PlaceRecipeSpec`/`PlaceSpec`, keep it CAMP/NEST-scoped
  (`Optional[...]`, `None` for all other kinds) — do not make it a required field on every `PlaceSpec`,
  which would break the existing `test_non_place_shaped_content_compiles_unchanged`-style regression
  guards and every non-Camp/Nest `PlaceSpec` construction across the test suite.
