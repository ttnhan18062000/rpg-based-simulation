---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-CAMPSTATE-PLACE-BRIDGE
artifact_type: plan
tags: [content, architecture]
---

# Implementation Plan — TCK-20260904-CAMPSTATE-PLACE-BRIDGE

## Summary

`WorldCompiler.compile()` already constructs a real `PlaceState(kind=CAMP/NEST)` generically for
both the Direct and Composition paths (`src/worldbuilding/compiler.py:319-330`, confirmed live
against `hero_guild_routing`'s `goblin_camp_place`) — this ticket does **not** touch that loop.
The real gap is that `AuthoritativeState.camps` is never populated: `compiler.py:695-713`'s final
`AuthoritativeState(...)` call has no `camps=` kwarg at all, so `CampService.process_camps()` and
`CreatureTerritoryService.process_territories()` iterate an always-empty dict in every real
compiled world today. This plan closes that gap by (1) adding a single new `Optional[str]`
creature-race field (`creature_kind`) to `PlaceRecipeSpec`/`PlaceSpec`, CAMP/NEST-scoped and
`None` by default, and (2) extending the *existing* per-region Place-construction loop in
`compiler.py` with an additive branch that builds a companion `CampState`, keyed by the same
`place_id`, whenever a CAMP/NEST-kind `PlaceSpec` carries a non-`None` `creature_kind`. Because
the new field is optional and no existing content sets it, the bridge is inert for every world
compiled today (including `hero_guild_routing`, which this plan deliberately does not migrate) —
it only activates for content that opts in by declaring the field, which is deferred to a future
ticket. `CampService`, `CreatureTerritoryService`, and the Camp/Nest classification rule are not
touched.

## Architecture Decision (required before implementation)

**Chosen: Option (a) — construct a companion `CampState` alongside each `PlaceState(kind=CAMP/NEST)`
at compile time; `CampService` keeps operating on `CampState` unchanged.**

Justification (adopting the investigation's recommendation, not overriding it):

- Option (b) (migrate `CampService` onto `PlaceState` directly, retiring `AuthoritativeState.camps`)
  is infeasible **within this ticket's own Out-of-Scope line**. `CreatureTerritoryService.process_territories()`
  (`src/world/creature_territory.py:36`) reads `state.camps.values()` directly, exactly like
  `CampService`. Retiring `camps` would leave `CreatureTerritoryService` reading a permanently-empty,
  retired dict — a silent regression — unless `CreatureTerritoryService` is also migrated, which this
  ticket's Out of Scope section explicitly forbids ("`CreatureTerritoryService` changes"). Option (a)
  is therefore the only option consistent with the ticket's own scope boundaries.
- Option (a) has the smaller blast radius the ticket's own Scope section flags, requires zero changes
  to `src/world/camp.py` or `src/world/creature_territory.py`, and matches the AC's own asymmetric
  wording ("If option (a): existing CampService tests continue to pass unmodified").
- Linkage scheme: the companion `CampState.id` is set to the **same string** as its `PlaceState.place_id`
  (`state.camps[place_id]` and `state.places[place_id]` share one key). No new field is added to
  `CampState` for this — `AuthoritativeState.places` and `AuthoritativeState.camps` are already both
  keyed by plain `str` (`src/core/state.py:1290,1292`), so a shared key is sufficient for bidirectional
  lookup and mirrors the existing `RegionState.places` / `AuthoritativeState.places` dual-keying
  pattern rather than inventing a new cross-reference field.
- `CampState.faction` is left at its dataclass default (`"hostile"`, `src/core/state.py:1240`) rather
  than derived from `PlaceState.owner_faction_id` (`Optional[int]`, a `Faction` IntEnum id with
  different semantics, `src/core/state.py:351`) — no real content sets `owner_faction_id` on any Place
  today, and Camp/Nest content is inherently hostile per the classification rule
  (`docs/mechanics/05_world_evolution.md` §6), so the constant default is correct and requires no new
  mapping logic.
- `CampState.totem_tier`/`stockpile`/`palisade_integrity` (the sibling ticket's scaffolding fields) are
  left at their dataclass defaults (`0`/`0.0`/`0.0`) — no content-schema field carries real values for
  them, and inventing accrual/seed logic is explicitly out of scope (Anti-Drift Hazards).

## Gameplay-Activation Risk Decision (required before implementation)

Investigation flagged that `CampService.process_camps()` runs every tick unconditionally
(`src/engine/world_dynamics.py:167-168`, no feature flag on the whole function) — so seeding a
real, non-empty `state.camps` activates raid-triggering and monster-spawning live, for the first
time, in any world with populated Camp/Nest content.

**Decision: do not add a new engine-level `ENABLE_*` feature flag, and do not gate `CampService` or
`WorldCompiler.compile()`.** Instead, rely on the field itself as the opt-in gate, and leave the one
real CAMP-kind content on disk unmigrated:

- The new `creature_kind` field is `Optional[str] = None`. The compiler bridge only constructs a
  `CampState` when a `PlaceSpec`'s `kind` is `CAMP`/`NEST` **and** `creature_kind is not None`. No
  existing content sets this field (confirmed: `data/worlds/hero_guild_routing/resolved/world.resolved.yaml`'s
  `goblin_camp_place` declares only `id`/`kind`/`position`), so the bridge is inert for every world
  compiled today by construction, not by a runtime flag check.
  - `WorldCompiler.compile()` runs at world-gen/build time (offline, before the tick engine's
    `FeatureFlagManager` is even constructed — `FeatureFlagManager()` is only instantiated inside
    `src/engine/pipeline.py:70`, a runtime/per-tick concern). There is no existing precedent for
    `compile()` consuming `FeatureFlagManager`, and threading one through `compile()`/`CompileContext`/
    `cli.py` for this single narrow gate would be a disproportionate scope expansion the ticket's ACs
    do not ask for.
  - This ticket deliberately does **not** modify `data/worlds/hero_guild_routing/resolved/world.resolved.yaml`
    to add `creature_kind: goblin` to `goblin_camp_place` (resolving investigation Risk #3: real-content
    migration is treated as out of scope/deferred, not a stretch goal attempted here). This guarantees
    `state.camps == {}` continues to hold for every real, CI-tested compiled world after this ticket
    ships — the literal AC requirement ("non-Camp-shaped content compiles unchanged") is satisfied, and
    so is the *spirit* of it for the one real Camp-shaped content that does exist today.
  - A future ticket that migrates `goblin_camp_place` (or any other content) to declare `creature_kind`
    is the point where `CampService` starts running against real data for the first time — that ticket
    should treat the raid/spawn activation as an intentional, reviewed gameplay change at that time (and
    can reconsider flag-gating `CampService` itself then, if warranted). Recorded here as a forward note,
    not solved by this ticket.

## Steps

### Step 1 — Add `creature_kind` field to `PlaceRecipeSpec` and `PlaceSpec`
**Files:** `src/worldbuilding/recipe.py`, `src/worldbuilding/schema.py`
**Change:**
- In `src/worldbuilding/recipe.py` (`PlaceRecipeSpec`, currently 7 fields at lines 25-32, confirmed
  read), add a module-level constant `CAMP_NEST_CREATURE_RACES = frozenset({"goblin", "orc", "wolf",
  "spider", "troll", "slime"})` (mirrors the existing `PLACE_RECIPE_KINDS` constant pattern at line 12)
  sourced from `docs/mechanics/05_world_evolution.md` §6's Camp+Nest race table. Add field:
  `creature_kind: Optional[str] = Field(None, description="CAMP/NEST-kind only: creature race driving CampState.kind (goblin/orc/wolf/spider/troll/slime); None for all other kinds and for CAMP/NEST content not yet migrated to the world-gen Camp bridge")`.
  Add a `field_validator("creature_kind")` that, when the value is not `None`, rejects any string
  outside `CAMP_NEST_CREATURE_RACES` (uppercase-insensitive raise, mirroring `validate_kind`'s
  pattern at recipe.py:34-40).
- In `src/worldbuilding/schema.py` (`PlaceSpec`, currently 7 fields at lines 46-53, confirmed read),
  add the identical `creature_kind: Optional[str] = Field(None, ...)` field and the identical
  `CAMP_NEST_CREATURE_RACES` constant + validator, mirroring `PLACE_SPEC_KINDS`'s existing pattern
  (schema.py:34) exactly as `PlaceRecipeSpec`/`PlaceSpec` already mirror each other for every other
  field.
- Do **not** add any cross-validation forcing `creature_kind` to be required when `kind in {CAMP,
  NEST}`, and do not forbid setting it on other kinds. Both classes already use `extra="forbid"`
  (recipe.py) / are `frozen=True` (schema.py) Pydantic models — a required-when-CAMP rule would break
  `goblin_camp_place`'s existing on-disk YAML the moment it's re-validated (it declares `kind: CAMP`
  with no creature-race data), which is exactly the anti-drift hazard investigation.md flags ("do not
  make it a required field... which would break... existing content"). Optional stays optional
  regardless of `kind`.
**Do NOT touch:** `PLACE_RECIPE_KINDS`/`PLACE_SPEC_KINDS`, `validate_kind()`, any other field on
either class, `RegionRecipeSpec`/`RegionSpec`'s own fields (only their existing `places: List[...]`
list keeps working unchanged).
**Verify:** `test_invalid_creature_race_rejected_at_schema_level`,
`test_creature_kind_field_is_none_for_non_camp_nest_place_kinds` (Step 4).

### Step 2 — Thread `creature_kind` through the Composition-path resolver
**Files:** `src/worldassembly/resolver.py`
**Change:** In `resolve_module_contribution()`'s `PlaceSpec(...)` construction inside the Places
list-comprehension (`src/worldassembly/resolver.py:812-823`, confirmed read — currently copies `id`
(namespaced), `kind`, `position`, `footprint`, `owner_faction_id`, `scale`, `maturity`,
`hazard_level` from each `PlaceRecipeSpec p`), add `creature_kind=p.creature_kind` to the
constructor call, alongside the other pass-through fields. This is a pure additive one-line change
inside an existing comprehension — no new logic, no new namespacing (unlike `id`, `creature_kind` is
not an identifier and needs no `prefix` treatment).
**Other writers to this construction site:** none — `resolve_module_contribution()`'s
`PlaceSpec(...)` call (lines 813-822) is the single site that builds `RegionSpec.places` from
`RegionRecipeSpec.places` on the Composition path; the Direct path builds `RegionSpec`/`PlaceSpec`
directly from parsed YAML via Pydantic (no resolver involvement), so there is no ordering/race
concern between the two paths — they are alternative entry points into the same downstream
`WorldCompiler.compile()`, not concurrent writers.
**Do NOT touch:** the `id=f"{prefix}{p.id}"` namespacing line, any other field in this
comprehension, `RegionSpec(...)`'s own construction below it (lines 800-825), factions/biomes
resolution below (lines 827+).
**Verify:** `test_resolve_module_contribution_wires_camp_kind_place_with_race_field` (Step 5).

### Step 3 — Build companion `CampState` in `WorldCompiler.compile()`'s existing Place loop
**Files:** `src/worldbuilding/compiler.py`
**Change:**
- Add `camps: Dict[str, CampState] = {}` next to the existing `places: Dict[str, PlaceState] = {}`
  declaration (`compiler.py:280`).
- Inside the existing `for p_spec in getattr(r_spec, "places", []):` loop (`compiler.py:319-330`,
  confirmed read — this is the loop that already builds every `PlaceState(kind=CAMP/NEST/...)`
  generically and must **not** be duplicated or replaced), after the existing
  `places[p_spec.id] = PlaceState(...)` line, add an additive branch:
  ```
  if p_spec.kind in ("CAMP", "NEST") and getattr(p_spec, "creature_kind", None) is not None:
      camps[p_spec.id] = CampState(
          id=p_spec.id,
          kind=p_spec.creature_kind,
          position=(float(p_spec.position[0]), float(p_spec.position[1])),
      )
  ```
  `CampState`'s remaining fields (`maturity`, `active`, `faction`, `last_raid_tick`, `totem_tier`,
  `stockpile`, `palisade_integrity`) are left at their dataclass defaults
  (`src/core/state.py:1238-1244`, confirmed read: `maturity=0.0`, `active=True`,
  `faction="hostile"`, `last_raid_tick=0`, `totem_tier=0`, `stockpile=0.0`,
  `palisade_integrity=0.0`) — per the Architecture Decision above, none of these has a content-schema
  source yet.
- Import `CampState` into `compiler.py` (it already imports `PlaceState`/`PlaceKind` from
  `src.core.state` for the existing loop — add `CampState` to that same import line).
- Pass the new `camps` dict into the final `AuthoritativeState(...)` call
  (`compiler.py:695-713`, confirmed read — currently has no `camps=` kwarg at all): add
  `camps=camps,` alongside the existing `places=places,  # Idea 66` line (line 702).
**Other writers to `AuthoritativeState.camps`:** `CampService.process_camps()`
(`src/world/camp.py:23`) and `CreatureTerritoryService.process_territories()`
(`src/world/creature_territory.py:36`) both **read** `state.camps` every tick
(`src/engine/world_dynamics.py:167-168,205-211`) but neither constructs new `CampState` entries or
writes to the dict directly — durable mutation of an existing `CampState` goes through
`CampUpdate`/`apply_plan.py`'s camp-application block (`src/engine/apply_plan.py:275-291`), which
replaces entries keyed by an id already present in `state.camps`. This step is the **first and only**
site that ever inserts *new* keys into `camps` — there is no collision risk with the tick-time
mutation path, since world-gen (`compile()`) always runs once, before tick 0, before any
`CampUpdate` exists. No other test file or production code path constructs `CampState` at all
(confirmed via investigation's `grep -rn "CampState(" src/ tests/` — zero production call sites
before this step).
**Do NOT touch:** the existing `places[p_spec.id] = PlaceState(...)` construction itself, any other
field of the final `AuthoritativeState(...)` call, `RegionState.places` forward-membership wiring
(line 342, unaffected), the fingerprint/hash calculation immediately after (lines 715-719,
unaffected — `CanonicalStateHasher` already covers `camps` per `test_place_participates_in_canonical_hash`'s
sibling coverage).
**Verify:** `test_camp_kind_place_compiles_to_companion_campstate`,
`test_nest_kind_place_compiles_to_companion_campstate`,
`test_non_camp_nest_place_kinds_do_not_construct_campstate`,
`test_non_place_shaped_content_compiles_unchanged_with_camp_bridge`,
`test_campstate_place_linkage_round_trips_via_place_id` (Step 4).

### Step 4 — Direct-path tests in `test_place_wiring.py`
**Files:** `tests/unit/worldbuilding/test_place_wiring.py`
**Change:** Add, mirroring the existing file's structure (imports `WorldSpec`, `TopologySpec`,
`RegionSpec`, `PlaceSpec`, `WorldCompiler`, `PlaceKind`, `CanonicalStateHasher` already present at
lines 9-13; helper `_minimal_spec()` at line 16):
- `test_camp_kind_place_compiles_to_companion_campstate` — `PlaceSpec(kind="CAMP",
  creature_kind="goblin", ...)` produces both `state.places["p1"]` and `state.camps["p1"]`, with
  `state.camps["p1"].kind == "goblin"` and position matching.
- `test_nest_kind_place_compiles_to_companion_campstate` — same for `kind="NEST",
  creature_kind="wolf"`, asserting `state.camps["p1"].kind in CampService.NEST_RACE_KINDS`
  (import `CampService` from `src.world.camp` for this one assertion only).
- `test_non_camp_nest_place_kinds_do_not_construct_campstate` — `PlaceSpec(kind="CITY", ...)` (and
  one of RUIN/DUNGEON/LANDMARK/LAIR) with no `creature_kind` produces `state.camps == {}`.
- `test_non_place_shaped_content_compiles_unchanged_with_camp_bridge` — a region with no `places` at
  all still compiles with `state.camps == {}` and `state.places == {}`, extending the existing
  `test_non_place_shaped_content_compiles_unchanged` pattern.
- `test_campstate_place_linkage_round_trips_via_place_id` — given `place_id="p1"`, both
  `state.places["p1"]` and `state.camps["p1"]` resolve and share the same key.
- `test_invalid_creature_race_rejected_at_schema_level` — `PlaceSpec(kind="CAMP",
  creature_kind="dragon", ...)` raises a Pydantic `ValidationError`, mirroring the existing
  `test_invalid_place_kind_rejected_at_schema_level` pattern in this file.
- `test_creature_kind_field_is_none_for_non_camp_nest_place_kinds` — `PlaceSpec(kind="CITY", ...)`
  with `creature_kind` unset defaults to `None` and compiles without error.
- `test_campstate_place_bridge_participates_in_canonical_hash` — two otherwise-identical
  `WorldSpec`s, one with a `creature_kind`-populated CAMP Place and one without, produce different
  `CanonicalStateHasher.get_hash()` values (mirrors `test_place_participates_in_canonical_hash`'s
  existing pattern in this file).
**Do NOT touch:** any existing test in this file (all 7 must keep passing unmodified, per the
Regression Surface in test_plan.md).
**Verify:** `pytest tests/unit/worldbuilding/test_place_wiring.py -q`.

### Step 5 — Composition-path test in `test_resolver.py`
**Files:** `tests/unit/worldassembly/test_resolver.py`
**Change:** Add `test_resolve_module_contribution_wires_camp_kind_place_with_race_field`, mirroring
the existing `test_resolve_module_contribution_wires_place_shaped_region` structure: a
`RegionRecipeSpec` with one `PlaceRecipeSpec(kind="CAMP", creature_kind="goblin", ...)`, assert the
resolved `RegionSpec.places[0].creature_kind == "goblin"` and that the id namespacing (`prefix`)
still applies correctly to `id` while `creature_kind` passes through unnamespaced.
**Do NOT touch:** `test_resolve_module_contribution_wires_place_shaped_region`,
`test_resolve_module_contribution_region_without_places_yields_empty_list`, or any other existing
test in this file.
**Verify:** `pytest tests/unit/worldassembly/test_resolver.py -q`.

### Step 6 — Architecture-guard / anti-drift tests in `test_camp_lifecycle.py`
**Files:** `tests/unit/world/test_camp_lifecycle.py`
**Change:** Add `test_campservice_process_camps_operates_on_world_gen_seeded_camp` (unit-tier, in
this file rather than a new integration-tier file — the cross-module surface is small: one
`WorldCompiler.compile()` call feeding one `CampService.process_camps()` call, no additional
integration fixtures needed): compile a minimal `WorldSpec` with a `creature_kind`-populated CAMP
Place via `WorldCompiler.compile()`, then feed the resulting `state.camps[...]` entry directly into
`CampService.process_camps()` and assert it runs without error and produces the expected
maturity-accrual `StateUpdate` shape — proving the world-gen-seeded `CampState` is not just
structurally present but functionally usable by the existing, unmodified service.
Also add two explicit anti-drift guard tests named in test_plan.md:
- A test confirming `CampService.process_camps()`'s raid-trigger/monster-spawn code path is not
  newly wrapped in any new flag check (read `src/world/camp.py`'s source, or exercise the raid
  branch directly with a matured world-gen-seeded camp) — this ticket seeds data into an
  already-unconditional service, it does not add new gating.
- A test confirming `AuthoritativeState.to_readonly()`'s `camps=ReadOnlyDict(self.camps)`
  wrapping (`src/core/state.py:1426`, confirmed read) still applies to a `CampState` constructed via
  this new bridge — build a state via `WorldCompiler.compile()` with a populated Camp, call
  `.to_readonly()`, and assert `type(result.camps) is ReadOnlyDict` (or equivalent), guarding
  against accidentally replicating the pre-existing `places`-is-unwrapped gap (see Anti-Drift Notes)
  onto the new camps construction path.
**Do NOT touch:** any existing test/assertion in this file (maturity evolution, spawn cap, raid
trigger, Nest-spread fork, typed-field round-trip/merge/apply-plan tests must all keep passing
unmodified, per test_plan.md's Regression Surface).
**Verify:** `pytest tests/unit/world/test_camp_lifecycle.py -q`.

### Step 7 — Update `docs/world/raid_boss_camp_contract.md`
**Files:** `docs/world/raid_boss_camp_contract.md`
**Change:** Add a new subsection under the existing `## Camp — camp.py` section (confirmed present
per investigation.md) describing the world-gen construction path added by this ticket: a
`PlaceSpec(kind=CAMP/NEST, creature_kind=...)` compiles to a companion `CampState` keyed by the
same `place_id`, only when `creature_kind` is explicitly set (opt-in, no existing content sets it
today), and that `CampService`/`CreatureTerritoryService` themselves are unchanged. Cross-reference
this ticket ID for traceability, matching the doc's existing citation style.
**Do NOT touch:** the doc's existing description of tick-to-tick evolution (growth, spawning, raid
trigger, Nest fork, classification) — this ticket only adds the missing "how does one come to
exist" piece, it does not change any existing behavior description.
**Verify:** Manual doc review (no automated doc test for this file); cross-checked against Step 3's
actual implementation before finalizing the ticket.

### Step 8 — Update `docs/world/compiler_contract.md`'s field-list summary
**Files:** `docs/world/compiler_contract.md`
**Change:** Extend the one-line `RegionSpec` field summary at `docs/world/compiler_contract.md:53`
(currently: `` `List[RegionSpec]` — region definitions (..., `places: List[PlaceSpec]` — idea 66, empty
for content not yet migrated to Place-shaped form)``, confirmed read) to mention the new
`creature_kind` field on `PlaceSpec`, e.g. append "; `PlaceSpec.creature_kind: Optional[str]` —
CAMP/NEST-kind only, drives companion `CampState.kind` construction, `None` by default."
**Do NOT touch:** the rest of the "Two Compilation Paths" table, terrain-fill documentation (lines
85-102), or any other section of this contract doc.
**Verify:** Manual doc review; this is a documentation-only step with no test.

### Step 9 — Correct the stale `WORLD-109` divergence note
**Files:** `docs/parity_ledger/world_dynamics.yaml`
**Change:** `WORLD-109`'s current `divergence_note` (lines 1410-1413, confirmed read verbatim):
*"camp_constructed has no viable engine path under the current camp lifecycle model: camps are
pre-placed at world generation and CampService (src/world/camp.py) only evolves existing camps
(maturity, raids) — there is no dynamic construction mechanic to emit from. Not pending/future
work; confirmed by TCK-20260701-SIMQ-EMIT-CAMP."* asserts a premise ("camps are pre-placed at world
generation") that was **false** before this ticket (confirmed: zero production `CampState`
construction existed, `compiler.py:695-713` never passed `camps=`) and becomes only **partially**
true after this ticket (a `CampState` is now constructible at world-gen, but only for content that
opts in via `creature_kind` — no real content does so yet, per the Gameplay-Activation Risk
Decision above). Update the `divergence_note` to read (exact wording, via
`tools/parity_ledger_writer.py`'s validating write path, not a raw YAML edit, per CLAUDE.md's
Parity Ledger rule and the sibling ticket's own precedent):
*"camp_constructed remains blocked but for a narrower reason than previously stated: as of
TCK-20260904-CAMPSTATE-PLACE-BRIDGE, WorldCompiler.compile() CAN construct a real CampState
alongside a PlaceState(kind=CAMP/NEST) when content declares the optional PlaceSpec.creature_kind
field — but no real content does so yet (the field is opt-in and unset on
hero_guild_routing's goblin_camp_place), so CampService still has no populated camps to emit
camp_constructed from in any real compiled world today. The original premise ('camps are
pre-placed at world generation') was inaccurate prior to this ticket — zero production CampState
construction existed. Still not pending/future work for THIS entry's event-emission scope; see
TCK-20260904-CAMPSTATE-PLACE-BRIDGE for the construction-path change."*
`status` stays `verified` (P1, no `test_path` change required — this entry's own `test_path`
concerns `spawn_cadence_fired`/`node_recharged`/`threat_evolved`, not `camp_constructed`, and is
unaffected). Do not edit `WORLD-124` (sibling ticket's entry, accurately describes that ticket's own
scope and needs no change per investigation.md).
**Do NOT touch:** `WORLD-124`, any other entry in `world_dynamics.yaml`, the `text`/`v2_evidence`/
`test_path`/`status`/`priority` fields of `WORLD-109` itself (only `divergence_note` changes).
**Verify:** `tools/parity_ledger_writer.py`'s own schema-validating write succeeds (no separate test
file); confirms `docs/parity_ledger/world_dynamics.yaml` still parses/validates against
`docs/parity_ledger/schema.json` after the edit.

### Step 10 — Correct the stale framing in the M8 epic doc
**Files:** `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md`
**Change:** Item 2's framing ("`CampState` is never constructed anywhere in production code,
`WorldModuleSpec` has no `camp_recipes` field, and the compiler has no camp step at all... needs a
new schema field plus a new compiler step") is stale per this ticket's own Request Summary — idea
66's Place hierarchy already supplied the generic insertion point; this ticket added only the
narrow `creature_kind` field plus an additive branch inside the existing loop, not a new schema/compiler
step. Update this item to reflect the as-built mechanism (reference this ticket ID) rather than the
originally-anticipated (and now incorrect) shape.
**Do NOT touch:** any other item in this epic doc, or the doc's own status/scope framing beyond item 2.
**Verify:** Manual doc review; documentation-only, no test.

## Scope Guards

- Do not modify `src/world/creature_territory.py` (`CreatureTerritoryService`) — forbidden by this
  ticket's own Out of Scope line and the sibling ticket's. It begins receiving real, non-empty
  `state.camps` data only once real content opts in via `creature_kind` (deferred beyond this
  ticket), which is expected and requires no code change on its part.
- Do not modify `docs/mechanics/05_world_evolution.md` §6 or re-derive/re-open the City/Camp/Nest/
  Excluded classification rule — already closed by `TCK-20260904-CAMP-NEST-CLASSIFICATION`. This
  plan only *carries* the already-decided race value through content into `CampState.kind`.
- Do not add accrual/effect logic for `totem_tier`/`stockpile`/`palisade_integrity` — leave at
  dataclass defaults on every newly-constructed `CampState` (Step 3).
- Do not touch `src/world/camp.py` (`CampService`) or `src/engine/world_dynamics.py` at all — Option
  (a) requires zero changes to either.
- Do not add a new `ENABLE_*` entry to `src/domains/optimization/feature_flags.py` — the
  Gameplay-Activation Risk Decision explicitly rejects a new engine-level flag in favor of the
  field-presence opt-in gate.
- Do not modify `data/worlds/hero_guild_routing/resolved/world.resolved.yaml` (or any other real
  content file) to add `creature_kind` — real-content migration is explicitly deferred to a future
  ticket (investigation Risk #3, resolved as "deferred" not "stretch").
- Do not wrap `AuthoritativeState.places` in a `ReadOnlyDict` inside `to_readonly()` — that
  pre-existing gap (`src/core/state.py:1405-1454`, `places` passed unwrapped through `replace()`) is
  out of this ticket's scope; only preserve (not extend) the existing correct `camps=ReadOnlyDict(...)`
  wrapping for the newly-constructed camps.
- Do not add cross-validation forcing `creature_kind` to be required when `kind in {CAMP, NEST}` —
  it must stay fully optional at the schema level (Step 1) to avoid breaking `goblin_camp_place`'s
  existing on-disk YAML.
- Do not run `pytest tests/` unscoped — use the Scoped Pytest Commands from test_plan.md.

## Dependency Map

- Step 1 (schema field) must land before Step 2 (resolver) and Step 3 (compiler), since both read
  `p_spec.creature_kind`.
- Step 2 (resolver) and Step 3 (compiler) are independent of each other and can be implemented in
  either order, but both depend on Step 1.
- Step 4 (Direct-path tests) depends on Steps 1 and 3. Step 5 (Composition-path test) depends on
  Steps 1 and 2. Step 6 (architecture-guard tests) depends on Step 3.
- Steps 7-10 (docs/parity) are independent of each other and of Steps 4-6, but should land after
  Steps 1-3 are implemented so the doc/parity text accurately describes the as-built mechanism, not
  the planned one.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `plan.md` states and justifies the chosen architecture before implementation begins | Architecture Decision section (this document) | N/A — documentation AC |
| `WorldCompiler.compile()` constructs `PlaceState(kind=CAMP)`/`PlaceState(kind=NEST)`, Direct + Composition paths | Already satisfied by prior work (`compiler.py:319-330`, `resolver.py:800-824`) — no new step needed; this plan adds nothing here | `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds` (existing, unmodified) |
| New test proves non-Camp-shaped content compiles unchanged (regression) | Step 4 | `test_non_place_shaped_content_compiles_unchanged_with_camp_bridge` |
| If option (a): `CampState` instances round-trip with their `PlaceState` counterpart; existing `CampService` tests pass unmodified | Steps 3, 4, 6 | `test_campstate_place_linkage_round_trips_via_place_id`, `test_campservice_process_camps_operates_on_world_gen_seeded_camp`, full `pytest tests/unit/world/test_camp_lifecycle.py -q` unmodified pass |

Option (b)'s AC row is not applicable — option (a) was chosen (see Architecture Decision).

## Anti-Drift Notes

- The generic `PlaceState(kind=...)` construction loop (`compiler.py:319-330`) already handles
  `CAMP`/`NEST` correctly — the only new code is the additive `camps[...] = CampState(...)` branch
  inside that same loop (Step 3), never a parallel/duplicate compilation pass.
- `CreatureTerritoryService` will begin receiving real `state.camps` data as a side effect once
  future content opts in via `creature_kind` — this is expected per the Architecture Decision, and
  its code must not change now or later as part of this ticket.
- No accrual/effect logic for `totem_tier`/`stockpile`/`palisade_integrity` — dataclass defaults only.
- `camps=ReadOnlyDict(self.camps)` in `to_readonly()` (`state.py:1426`) must keep applying to
  newly-constructed camps; do not copy the construction logic in a way that bypasses it (Step 6's
  guard test is the direct check for this).
- The `creature_kind` field must stay `Optional[str] = None` and CAMP/NEST-scoped in spirit (used
  only by CAMP/NEST kinds) but not schema-enforced as required for those kinds — `goblin_camp_place`'s
  existing on-disk YAML has no such field and must keep validating.
- This ticket deliberately leaves `state.camps == {}` for every real, CI-tested compiled world
  (including `hero_guild_routing`) — real-content migration and any accompanying gameplay-activation
  review are out of scope, left for a future ticket per the Gameplay-Activation Risk Decision.
- `WORLD-109`'s `divergence_note` update (Step 9) must go through `tools/parity_ledger_writer.py`,
  never a raw YAML edit — CLAUDE.md's Parity Ledger rule and the "Parity-updater full-file YAML
  rewrite risk" precedent both apply. `WORLD-124` is not to be edited.
