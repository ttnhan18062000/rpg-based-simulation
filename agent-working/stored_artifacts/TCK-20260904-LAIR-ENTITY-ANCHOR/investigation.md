---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-LAIR-ENTITY-ANCHOR
artifact_type: investigation
tags: [content, world, determinism]
---

# Investigation — TCK-20260904-LAIR-ENTITY-ANCHOR

## Current Behavior

### `BossService.check_for_boss_spawn` (`src/world/boss.py:20-154`)

Verified directly against current source (post-sibling-tickets state):

- Idempotency source-of-truth is **entity-side identity metadata**, not any Region/Place field:
  `_boss_region_id(entity)` (`boss.py:54-71`) reads, in priority order, (1)
  `entity.identity.properties.get("boss_region_id")`, (2) `entity.strategic.home_region_id`, (3) a
  position-based fallback via `LegalityServiceV2.get_region_for_position`. Nothing on `RegionState`
  or `PlaceState` is ever read or written by this function.
- `check_for_boss_spawn` builds `region_boss_map: Dict[region_id, entity]` by scanning
  **`state.entities.values()`** every call (`boss.py:73-83`), then iterates `state.regions.items()`
  (`boss.py:86`) and skips any region already present in the map. This is a full per-call rescan, not
  a persisted flag — idempotency is re-derived from live entity state on every invocation, exactly as
  the function's own docstring states ("Boss ownership source... 1. identity.properties[...]").
- On spawn, the new boss's `identity.properties["boss_region_id"]` is set via `dataclasses.replace`
  (`boss.py:117-131`) — this is the **only** write in the whole function; no `RegionState` or
  `PlaceState` is constructed, replaced, or referenced in any `StateUpdate`.
- Spawn gate: `state.maturity >= 50.0 and region.trauma_score >= 20.0` (`boss.py:90-94`) — note this
  reads **`state.maturity`** (world-level), not any per-region/per-camp maturity value, despite
  `docs/world/raid_boss_camp_contract.md:131` currently documenting the gate as `camp.maturity >=
  50` — a **pre-existing doc/code drift**, not introduced by this ticket (see Docs Requiring Update).
- Called from `src/engine/world_dynamics.py:156-157` (confirmed): `BossService.check_for_boss_spawn(state,
  generator)` inside `WorldDynamicsSystem.resolve_dynamics()`, once per invocation, no cadence gate of
  its own beyond the maturity/trauma check.
- Boss spawns via `generator.spawn_monster(spawn_pos, state=state, kind="ancient_sentinel",
  difficulty_tier=5)` then relabeled `kind="world_boss"` (`boss.py:110-119`).

### `PlaceState` / `PlaceKind` (`src/core/state.py:323-385`)

- `PlaceKind.LAIR = "LAIR"` (`state.py:328`) — already a valid enum member and already present in
  both `PLACE_RECIPE_KINDS` (`src/worldbuilding/recipe.py:12`) and `PLACE_SPEC_KINDS`
  (`src/worldbuilding/schema.py:34`). **No schema change is needed to declare LAIR-kind content** —
  this is unlike the CAMPSTATE-PLACE-BRIDGE ticket, which had to add a brand-new `creature_kind`
  field; LAIR-kind `PlaceSpec`s are already fully constructible and pass schema validation today.
- `occupant_entity_id: Optional[int] = None` (`state.py:354`) — "LAIR-kind, reused from today's
  boss_region_id pattern." Confirmed via `to_canonical_dict()` (`state.py:377`) that it *does*
  participate in canonical hashing once set.
- **Critical finding: nothing in the current codebase ever writes a non-`None` value to
  `occupant_entity_id`.**
  - `WorldCompiler.compile()`'s Place-construction loop (`src/worldbuilding/compiler.py:321-332`,
    confirmed read) constructs every `PlaceState` — including `kind=LAIR` — via a single generic
    call that passes `place_id`, `region_id`, `kind`, `position`, `footprint`, `owner_faction_id`,
    `scale`, `maturity`, `hazard_level`. **`occupant_entity_id` is never passed as a kwarg**, so it
    always defaults to `None` at world-gen for every Place of every kind, LAIR included.
  - `grep -rn "occupant_entity_id"` across `src/`, `tests/`, `docs/` (full-repo) returns exactly 4
    hits: the field declaration, its `to_canonical_dict()` entry, one test asserting the default is
    `None` and one test round-tripping a literal `dataclasses.replace(place, occupant_entity_id=7)`
    construction (`tests/unit/core/test_place_state.py:26,109`) — **no production code path
    constructs or mutates it.**
  - `src/core/updates.py`'s `StateUpdate` (`969-1026`, confirmed read in full) has **zero**
    place-related update fields — no `place_updates`, no `PlaceUpdate` dataclass exists anywhere in
    the file (compare to the fully-realized `WorldUpdate`/`CampUpdate`/`BuildingUpdate` sibling
    mechanisms, each with their own dict-keyed update collection + `merge()`).
  - `src/engine/apply_plan.py` — `grep -n "places\|PlaceState\|PlaceUpdate"` returns **zero matches
    in the entire file**. There is no authoritative apply-path insertion point for a Place field
    mutation at all today.
  - Conclusion: `PlaceState.occupant_entity_id` is currently a **write-never** field. It is
    schema-frozen and canonical-hash-aware, but there is no durable-state mechanism by which any
    system (including a hypothetical `LairService`) could actually set it through the authoritative
    apply pipeline as it exists today.
- Doc drift also found: `docs/brainstorm/rpg_expected_schemas.html:593` documents
  `occupant_entity_id` as `Optional[str]`; the real field (`state.py:354`) is `Optional[int]`
  (consistent with `entities: Dict[int, EntityState]`'s int-keyed ids elsewhere, e.g.
  `BossService.resolve_boss_death(state, boss_id: int)`). Pre-existing drift, `docs/brainstorm/`
  is not one of the Mechanics Bible/engine-contract authoritative doc families, flagged but not
  treated as a required-fix doc for this ticket (see Docs Requiring Update).

### `AuthoritativeState.places` / `RegionState.places` (`state.py:286,1292`)

Confirmed dual-keyed exactly like the sibling `camps`/`places` pattern: `RegionState.places:
List[str]` (forward references) and `AuthoritativeState.places: Dict[str, PlaceState]` (canonical
storage), both populated at compile time (`compiler.py:321-356`). A Region can hold zero or many
Places (`RegionState.places` is a list, not a single value) — this is exactly the collision case the
ticket describes: today's `BossService` keys idempotency per-`region_id`, so two LAIR-kind Places in
the same Region would incorrectly share one idempotency slot if the mechanism were extended naively
by iterating `state.places` but still keying off `region_id`.

### CAMPSTATE-PLACE-BRIDGE precedent (`stored_artifacts/TCK-20260904-CAMPSTATE-PLACE-BRIDGE/`, just landed)

Directly relevant as the freshest real precedent for bridging a typed companion state to a
`PlaceState`, but structurally different in one important way: `CampState` is built **entirely at
world-compile time** (a static companion object, no further mutation needed at runtime beyond the
existing `CampUpdate`/`apply_plan.py:275-291` path that already existed before that ticket). Lair
occupancy is not analogous in that respect — a Lair's occupant entity is meant to be **spawned during
the tick loop** (mirroring `BossService`'s calamity-driven, mid-run spawn), not pre-seeded at compile
time. This means the CAMPSTATE-PLACE-BRIDGE "additive branch inside the existing compile loop"
pattern is not directly reusable for the write side of this ticket — only its *investigative
approach* (verify the real gap before designing) and its general "don't add new apply-pipeline
plumbing unless truly required" discipline carry over.

### Camp/Nest classification precedent for dragonkin (`stored_artifacts/TCK-20260904-CAMP-NEST-CLASSIFICATION/investigation.md`, just landed)

Confirmed directly: dragonkin (`data/content/living/races.yaml:206-223` — `natural_traits: [flying,
large_body, fire_aligned, magic_sensitive]`, `cognition_profile: arcane_scholar`, `drive_profile:
disciplined_protector`, `intelligence_tier: high`) was explicitly excluded from Camp/Nest
classification and named as "Lair-adjacent," with this exact ticket ID cited as the intended owner
(`docs/mechanics/05_world_evolution.md:412`: `dragonkin | Excluded (Lair-adjacent) | ... owned by
TCK-20260904-LAIR-ENTITY-ANCHOR`). Additionally, `data/content/entities/entity_archetypes.yaml:256-263`
already authors a `dragon_cult_champion` archetype (`race: dragonkin`, `faction: dragon_cult`, `role:
leader`, `combat_profile: dragon_fire`), and `data/content/social/factions.yaml:151-154` already
defines a `dragon_cult` faction ("Cult faction serving dragonkin/fire-aligned power"). **Dragonkin is
confirmed as the intended and best-evidenced LAIR occupant race precedent** — no other race in the
13-race table has this combination of prior narrative authoring (archetype + faction) plus an
explicit classification-table pointer to this ticket.

Note: `spawn_monster`/`EntityGenerator` (`src/systems/world_systems/generator.py:60-84`) treats
`kind` as a free-form string with no archetype-catalog lookup (confirmed: no `entity_archetypes.yaml`
consumption exists in `generator.py`) — exactly like `BossService`'s own `kind="ancient_sentinel"`.
Using `kind="dragonkin"` (or a similar string) for a Lair occupant requires no new resolution
machinery; it is a plain string tag, consistent with existing precedent.

### Existing test: `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region` (`tests/unit/world/test_world_dynamics.py:75-146`)

Confirmed to exist and pass as claimed. Builds one `world_boss` entity with
`identity.properties["boss_region_id"] = "region_1"` positioned *outside* the region's bounds, and
asserts `BossService.check_for_boss_spawn(...)` produces `entities_add == []` — i.e., it proves the
lock survives the boss wandering away from its home region. This is a per-Region-single-boss test; it
does not (and, per the ticket's Out of Scope, is not required to) cover multiple LAIR Places within
one Region.

## Mechanics / Engine Constraints

- `docs/world/raid_boss_camp_contract.md` §"Boss — `boss.py`" (lines 125-149) is the authoritative
  engine contract for this exact mechanism, verified directly. Its "Idempotency" subsection (lines
  136-140) accurately describes the current entity-properties-based lock. Its own "Extension rules"
  §3 (line 193, verified verbatim) **already anticipates this exact ticket**: *"To add a new boss
  type: add to `SPAWN_POOLS` and `DIFFICULTY_ZONES` in `spawn_config.py`. The idempotency lock is per
  `region_id` — if multiple boss types should coexist in one region, the locking mechanism needs
  extending."* This is strong existing-doc confirmation that per-region-only locking is a known,
  named limitation this ticket is meant to close.
- CLAUDE.md's Durable State Rule: "If something survives beyond the current tick or current function
  call, it must have a typed model, a stable location in entity/world/registry state, a defined
  lifecycle, inspection/debug visibility, and tests." `boss_region_id` (living in
  `identity.properties`, a `Dict[str, Any]`) is an *existing* precedent that arguably sits in tension
  with the "typed model" half of this rule, but it predates this ticket and is not something this
  ticket is asked to fix. Whether the Lair mechanism should continue this precedent (entity-property
  keying) or instead route through a newly-typed `PlaceUpdate`/`occupant_entity_id` write path (which
  would more fully satisfy the Durable State Rule but requires new apply-pipeline plumbing not
  present anywhere today) is the central open structural question of this ticket — see Risks and
  Open Questions.
- CLAUDE.md's Architecture Rule ("Durable changes must be represented through typed records/updates.
  Authoritative application is the only place durable state should be committed.") directly bears on
  whichever option Plan selects: if `PlaceState.occupant_entity_id` is to be genuinely, durably
  written (not just conceptually referenced), a `PlaceUpdate` dataclass plus `StateUpdate.place_updates`
  dict plus an `apply_plan.py` application block would be the architecturally correct, precedent-consistent
  way to do it (mirroring `CampUpdate`'s existing shape at `updates.py:891-905` and its
  `apply_plan.py:275-286` application block exactly).

## Docs Requiring Update

- `docs/world/raid_boss_camp_contract.md`: the "Boss — `boss.py`" §"Idempotency" subsection (lines
  136-140) must be extended to describe the new Place-scoped locking mechanism once implemented, and
  "Extension rules" §3 (line 193) — which currently states the per-`region_id` limitation as an open
  gap — must be updated to reflect that the gap is now closed (or partially closed, per whatever
  scope Plan lands on), following the exact structural pattern the CAMPSTATE-PLACE-BRIDGE ticket used
  to add its own "World-gen construction" subsection to this same doc (lines 76-101 of the current
  file).
- `docs/parity_ledger/world_dynamics.yaml`: **WORLD-085** (`text: "World boss spawn rule is
  deterministic."`, `status: verified`, `priority: P0`, `test_path: null`) directly describes the
  exact rule this ticket changes (the spawn/idempotency rule). Per CLAUDE.md's Parity Ledger rule
  ("When a behavior changes: find the relevant parity ledger entry and update `status` and
  `v2_evidence`... P0 entries require a passing `test_path`"), this entry's `v2_evidence` must be
  updated to reference the new Place-scoped mechanism, and — since it is P0 and currently has
  `test_path: null` (a pre-existing gap this ticket's own extended/new tests are well-positioned to
  close) — a `test_path` should be supplied pointing at the extended idempotency test(s). Must be
  edited via `tools/parity_ledger_writer.py`, never a raw YAML edit, per CLAUDE.md and the
  CAMPSTATE-PLACE-BRIDGE precedent (its own Step 9).

The `docs/parity_ledger/world_dynamics.yaml` **WORLD-086** entry (path:
`docs/parity_ledger/world_dynamics.yaml`, under `docs/parity_ledger/`) is not required to change for
this ticket: it describes "World boss state appears in replay/fingerprint," a canonical-hashing/replay
concern. `PlaceState.to_canonical_dict()` already includes `occupant_entity_id` (`state.py:377`) and
world-boss entities already participate in `AuthoritativeState`'s existing entity-hashing path
regardless of how idempotency is keyed — this ticket's changes to the *locking* mechanism do not
change what gets hashed or how bosses appear in replay, so WORLD-086's own claim is unaffected.

The `docs/mechanics/05_world_evolution.md` doc (path: `docs/mechanics/05_world_evolution.md`, under
`docs/mechanics/`) is not required to change for this ticket beyond what
`TCK-20260904-CAMP-NEST-CLASSIFICATION` already added (the dragonkin/Lair-adjacent table row, already
landed): this ticket does not add a new race classification rule or a new §6-level mechanic
subsection in the sense that Camp/Nest's spread-outcome or Creature-Territory-Lifecycle subsections
did — it generalizes an existing boss/spawn mechanism's *keying granularity*, which is
`raid_boss_camp_contract.md`'s (not the Mechanics Bible chapter's) documentation responsibility, per
the existing division of labor between the two docs (chapter = laws/formulas, contract = per-file
mechanism detail) already established by the sibling tickets.

The `docs/brainstorm/rpg_expected_schemas.html` `Optional[str]`/`Optional[int]` drift on
`occupant_entity_id` (path: `docs/brainstorm/rpg_expected_schemas.html`, under `docs/brainstorm/`) is
not required to change for this ticket: it is a pre-existing inaccuracy in a brainstorm/planning doc,
not one of the Mechanics Bible/engine-contract/parity-ledger authoritative families this ticket's
Authoritative Mechanics Rule governs, and fixing unrelated pre-existing brainstorm-doc drift is
outside this ticket's scope.

The bullet below is a genuinely conditional Format 1 entry per the
TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED convention: its need depends on which
of the two options in "Risks and Open Questions" (Option A: entity-property keying, or Option B: new
`PlaceUpdate` apply-path) Plan/Implement selects — a choice not yet made at investigation time. It is
left in Format 1 deliberately (not downgraded to Format 2 prose) so `done-checker` still checks it by
default; whoever resolves it (implementer or doc-updater) should add the phrase "Resolved during
implementation, condition not met" to this bullet's own text if Option A (no new update mechanism) is
the one actually chosen, per that convention's `_RESOLVED_CONDITION_MARKER_RE` handling:
- `docs/world/compiler_contract.md`: only if this ticket adds a new `PlaceUpdate`/
  `StateUpdate.place_updates` apply-path mechanism (Option B), this doc's field-list summary should
  gain a line describing the new update-collection kind, mirroring how it already documents
  `PlaceSpec.creature_kind`. **Resolved during implementation, condition not met** — Option A was
  chosen (see plan.md Decision #1); `check_for_lair_spawn` keys occupancy via
  `identity.properties["lair_place_id"]`, not a new `PlaceUpdate`/`StateUpdate.place_updates`
  mechanism, so `compiler_contract.md` requires no edit.

## Parity Ledger Overlap

- **WORLD-085** (P0, `status: verified`, `test_path: null`) — "World boss spawn rule is
  deterministic." Directly touched; requires `v2_evidence` update and ideally a `test_path` per
  CLAUDE.md's P0 rule (see Docs Requiring Update above). This is the single most directly relevant
  entry to this ticket's core change.
- **WORLD-086** (P0, `status: verified`, `test_path: null`) — "World boss state appears in
  replay/fingerprint." Reviewed, not required to change (see above) — flagged for Verify-phase
  awareness since it shares the same pre-existing `test_path: null` gap as WORLD-085 but is not this
  ticket's rule.
- **WORLD-109** (`status: verified`, P1) — `spawn_cadence_fired`'s exclusion list already names
  `world_boss`/`ancient_sentinel`/`goblin_raider` as non-cadence spawn kinds
  (`src/observability/event_extractor.py:1357`, confirmed: `if getattr(e, "kind", None) not in (None,
  "world_boss", "ancient_sentinel", "goblin_raider")`). A parallel `_BOSS_KINDS = frozenset(("world_boss",
  "ancient_sentinel"))` also exists at `event_extractor.py:1461`. **If this ticket's implementation
  introduces a new entity `kind` string for Lair occupants** (e.g. `"dragonkin"` or
  `"lair_occupant"`) distinct from the existing `"world_boss"`/`"ancient_sentinel"` kinds, both of
  these lists would need to be extended, or newly-spawned Lair occupants will be misclassified by the
  observability pipeline (counted as a cadence spawn event when they shouldn't be, and/or excluded
  from boss-kind-specific consequence/event handling). If the implementation instead reuses the
  existing `"world_boss"`/`"ancient_sentinel"` kind strings for Lair occupants (differentiated only
  by which Place spawned them), no change to these lists is needed. This is a real, concrete
  consequence of whichever entity-kind-naming choice Plan makes — flagged here, not decided.
- No other `P0` entries in `world_dynamics.yaml`, `substrate.yaml`, or `combat_movement.yaml`
  reference boss/Place/Lair mechanics directly (targeted search of `boss|Boss|LAIR|Lair|occupant`
  across `docs/parity_ledger/*.yaml` performed; only the entries above matched).

## Prior Work

- `stored_artifacts/TCK-20260904-CAMPSTATE-PLACE-BRIDGE/` (done, landed on this branch) — closest
  structural precedent for bridging a companion typed state to a `PlaceState`, but compile-time-only
  (see Current Behavior above for why it doesn't directly transfer to this ticket's runtime-spawn
  need). Its documentation-update pattern (adding a new subsection to
  `docs/world/raid_boss_camp_contract.md`) and its discipline of investigating the real gap before
  designing (rather than assuming the schema-frozen field already has a write path) are the two
  concrete things this ticket should mirror.
- `stored_artifacts/TCK-20260904-CAMP-NEST-CLASSIFICATION/` (done, landed on this branch) — source of
  the confirmed dragonkin/Lair-adjacent classification and the explicit ownership pointer to this
  ticket ID.
- `tests/unit/world/test_world_dynamics.py::test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`
  — the existing test this ticket extends/generalizes, confirmed to exist and pass, per this ticket's
  own Out of Scope ("does not establish boss-spawn testing for the first time").

## Risks and Open Questions

- **Blocking-if-wrong, central design question**: does the ticket's AC phrase "keyed per-Place (via
  `PlaceState.occupant_entity_id` / `place_id`)" require the implementation to *actually write* a
  non-`None` value to `PlaceState.occupant_entity_id` through a new, typed apply-pipeline mechanism
  (Option B), or is it satisfied by generalizing the *existing* entity-property-keying pattern from
  `region_id` to `place_id` — e.g. `identity.properties["lair_place_id"] = place.place_id` — while
  leaving `PlaceState.occupant_entity_id` itself unwritten, exactly as it is today (Option A)?
  - **Option A (entity-property keying, generalized)**: Mirrors `boss_region_id` almost exactly —
    smallest change, no new `StateUpdate`/`apply_plan.py` plumbing, fully consistent with
    CAMPSTATE-PLACE-BRIDGE's "smallest change consistent with existing patterns" discipline and with
    this ticket's own framing as "generalizes the pattern." Satisfies the AC's literal requirement
    ("keyed per-Place, not per-Region") without requiring `occupant_entity_id` to ever be non-`None`
    in practice. Leaves `PlaceState.occupant_entity_id` a schema-only, still-write-never field for a
    future ticket to actually wire up (analogous to how `CampState`'s bridge left several fields at
    dataclass defaults for a future ticket).
  - **Option B (new `PlaceUpdate` apply-path)**: Adds a `PlaceUpdate` dataclass (`occupant_entity_id_set:
    Optional[int]`), a `StateUpdate.place_updates: Dict[str, PlaceUpdate]` collection, and an
    `apply_plan.py` application block (mirroring `CampUpdate`'s exact shape/insertion point at
    `updates.py:891-905`/`apply_plan.py:275-286`) so the Lair spawn function can durably commit
    `occupant_entity_id` to the actual `PlaceState`. More architecturally complete relative to the
    Durable State Rule, and makes `occupant_entity_id` a real, queryable, inspectable field (useful
    for e.g. a future idea-48 dissolution-on-death ticket that would need to look up "which entity
    occupies this Place"). Materially larger scope than Option A and than anything CAMPSTATE-PLACE-BRIDGE
    needed to build.
  - **Recommendation (not a decision — Plan must make this explicit and stated)**: Option A is the
    lower-risk, precedent-consistent, AC-satisfying choice for a ticket whose own Request Summary
    frames itself as "generalizes... the pattern," and defers the heavier apply-pipeline plumbing to
    whichever future ticket (plausibly idea 48's dissolution mechanism) actually needs to *read*
    `occupant_entity_id` durably. But Option B is defensible if Plan judges that leaving
    `occupant_entity_id` permanently unwritten defeats the purpose of the field existing at all under
    this ticket's own title ("Generalize... to Place-scoped Lair spawning" — arguably implying the
    Place itself should durably know its occupant, not just the occupant knowing its Place).
- **Not blocking, but must be stated explicitly in Plan**: which entity `kind` string(s) Lair
  occupants use. Reusing `"world_boss"`/`"ancient_sentinel"` requires no observability-list changes
  (WORLD-109 concern above); introducing `"dragonkin"` (or similar) as a new kind requires extending
  `event_extractor.py`'s two exclusion lists (lines 1357, 1461) or accepting a real event-classification
  gap.
- **Not blocking, pre-existing, worth flagging**: `EntityGenerator.spawn_monster`'s
  `DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])` (`generator.py:65`) silently falls back
  to tier-1 stats for any `difficulty_tier` not in `{1,2,3,4}` — `spawn_config.py`'s `DIFFICULTY_TIERS`
  dict only has entries 1-4, yet `BossService` already calls `spawn_monster(..., difficulty_tier=5)`
  today, meaning the existing world boss silently spawns at tier-1 stats despite the `difficulty_tier=5`
  argument. If a Lair occupant reuses this same `difficulty_tier=5` convention, it inherits the same
  silent fallback. Pre-existing, not introduced by this ticket, but real — worth a one-line note in
  Implementation Notes if the same pattern is reused, so it isn't mistaken for new-ticket behavior.
- **Real open scope decision, already correctly flagged in the ticket**: Lair dissolution/transformation
  on occupant death belongs to idea 48 (place-type transitions, no ticket yet). Confirmed no code
  anywhere references `PlaceState.prior_kind`/`transformed_tick` in connection with entity death or
  `BossService.resolve_boss_death` (`boss.py:156-176`) — this boundary is real and clean today, and
  this ticket must not build any of it.
- **Content-authoring decision, not blocking but real**: whether to add a real LAIR-kind Place to a
  corpus world (`hero_guild_routing`'s `mountain_pass_zone` is the explicit candidate — see next
  section) or use a synthetic fixture. Both are AC-acceptable; see Anti-Drift Hazards for the concrete
  cost of the real-content path.

## Anti-Drift Hazards

- `tests/unit/worldbuilding/test_place_wiring.py::test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds`
  (lines 130-164, confirmed read) **explicitly locks `mountain_pass_zone` to zero Places** — the exact
  code comment reads "mountain_pass_zone: intentionally zero Places -- pure transit terrain, the 'or
  none at all' case from idea 66's own Target Shape," and asserts `mountain_places == []` plus
  `report["place_count"] == 3`. If this ticket adds a real LAIR-kind Place to `mountain_pass_zone`
  (the "only wildlife-flavored candidate content" the ticket brief references), this exact assertion
  must be deliberately updated (not silently broken) — `mountain_places == []` → the new LAIR entry,
  `place_count == 3` → `4`, and the `state.places.keys()` set extended. This also requires editing the
  **source** `data/worlds/hero_guild_routing/world.yaml` and regenerating (or hand-mirroring)
  `resolved/world.resolved.yaml` via the compile CLI (`src/worldbuilding/cli.py`) — the `resolved/`
  directory is generated output, not hand-authored. Given CAMPSTATE-PLACE-BRIDGE's own deliberate
  choice to avoid touching real corpus content (to keep `state.camps == {}` stable for every
  CI-tested world), a synthetic fixture (mirroring `test_place_wiring.py`'s own
  `_minimal_spec()`-based tests) is the lower-risk default unless Plan explicitly decides real-content
  migration is worth the cost.
- Do not let the Lair spawn mechanism reuse `region.trauma_score`/`state.maturity` gates verbatim
  without checking whether a Place-scoped gate should instead reference something Place-local (e.g.
  `PlaceState.hazard_level`) — the ticket's Scope is about the *keying* mechanism (per-Place vs.
  per-Region), not the spawn *trigger conditions*; changing the trigger conditions would be scope
  creep beyond "generalize the idempotency pattern."
- Do not touch `CampService`/`CampState`/Camp-Nest classification (C1) or `CampState`/`PlaceState`
  bridging (C2) — both explicitly out of scope, both confirmed unrelated to any file this ticket must
  touch (`src/world/boss.py`, `src/core/state.py`, `tests/unit/world/test_world_dynamics.py`, plus
  whichever content/fixture file is chosen).
- Do not build any dissolution/transformation-on-death logic (idea 48) — confirmed no code references
  this today; must stay that way after this ticket, and the ticket's own Out of Scope section must
  keep naming idea 48 explicitly (already does).
- If Option B (new `PlaceUpdate` mechanism) is chosen, do not forget the canonical-hash
  serialization path is already correct (`PlaceState.to_canonical_dict()` already includes
  `occupant_entity_id`) — the risk is specifically the `apply_plan.py` commit point and the `merge()`
  semantics on the new `PlaceUpdate`, mirroring the exact silent-gap failure mode
  `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s own investigation flagged for `CampUpdate`'s
  totem/stockpile/palisade fields ("a field present on the dataclass but missing from this dict is a
  real, easy-to-miss silent bug").
