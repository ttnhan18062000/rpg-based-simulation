# [Milestone 4] - Environment, Terrain, Building, and Local World-Interaction Semantic Closure

## [Milestone Description]

Milestone 4 closes the local environment semantics that directly affect combat and immediate world behavior.

Its purpose is to recover the “fight and act in a place” part of the game rather than the long-horizon “plan across the world” part.

This milestone covers:

- terrain or spatial rules that affect immediate legality or tactical choice,
- building/local structure interaction semantics relevant to immediate gameplay,
- chokepoint, bracketing, or position-sensitive local behavior where preserved,
- and immediate world-interaction semantics that materially shape local conflict or action resolution.

It is not a repetition of Phase 5’s broader resource loop and not broader social/town/strategy work.

## [Milestone technical implementation]

Recover the supported local environment/world-interaction semantics in a way that is native to `src_v2` authority and determinism rules.

This milestone must:

- close terrain/building/local-position semantics that affect combat or immediate action behavior,
- recover preserved local environment constraints that shape legality or tactical action,
- define the supported boundary between local world structure and direct gameplay behavior,
- and keep this layer local rather than expanding into broad economy/town/strategy systems.

This milestone must not:

- duplicate Phase 5’s resource-town-progression loop,
- duplicate Phase 9’s strategic or social meaning,
- or invent unsupported environment semantics not classified in the replacement ledger.

## [Milestone important notes]

The trap here is turning “world interaction” into a bottomless bucket.

It is not.

Phase 8 owns only local environment semantics that materially shape immediate action and combat behavior.

## [Milestone acceptance criteria]

At the end of Milestone 4:

- local environment semantics affecting combat/action are explicit,
- building/terrain/local-position effects are explicit where supported,
- world-interaction scope remains local and bounded,
- preserved versus divergent local semantics are explicit,
- and the project has one credible immediate world-interaction semantic slice.

---

## Task

### [x] - [Task 1] - Audit local terrain, building, and position-sensitive behavior against Phase 8 world-interaction rows

#### [Task Description]

Map where immediate environment semantics are already real, partial, or absent.

#### [Task technical implementation]

Review the current local environment behavior and map it to the Phase 8 world-interaction row set.

Identify:

- terrain effects on local legality or tactical choice,
- building/local structure effects on immediate gameplay,
- position-sensitive local behavior such as chokepoints or bracketing where preserved,
- and places where environment semantics are still missing or conflated with unrelated systems.

#### [Task possible affected files]

- `src_v2/world/**`
- `src_v2/buildings/**`
- `src_v2/combat/**`
- `src_v2/navigation/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Do not invent environment work that was never part of the ledger.
Map the real replacement surface.

#### [Task check list]

- [x] Terrain effects are mapped
- [x] Building/local structure effects are mapped
- [x] Position-sensitive behavior is mapped
- [x] Missing semantics are identified
- [x] Audit notes are reviewable

#### [Implementation Comment]
Created `docs/engine/phase8_m4_audit.md`. Mapped gaps in terrain and LoS logic.

#### [Task acceptance criteria]

The project has a concrete gap audit for local environment/world-interaction semantics.

---

### [x] - [Task 2] - Complete supported terrain and spatial semantics that affect immediate legality or tactical action

#### [Task Description]

Make immediate position and terrain matter where preserved legacy behavior requires it.

#### [Task technical implementation]

Implement or refine local terrain/spatial semantics so supported immediate gameplay behavior reflects preserved constraints such as:

- blocked or constrained local movement relevant to conflict,
- spatial legality constraints,
- and local-position effects on immediate tactical choice where preserved.

#### [Task possible affected files]

- `src_v2/world/**`
- `src_v2/navigation/**`
- `src_v2/combat/**`
- `tests_v2/world/**`
- `tests_v2/tactical/**`

#### [Task important notes]

Keep this local.
Do not let it drift into broad pathfinding or strategic map semantics.

#### [Task check list]

- [x] Supported terrain rules are explicit
- [x] Supported spatial legality effects are explicit
- [x] Immediate tactical relevance is explicit
- [x] Deterministic behavior is preserved
- [x] Unsupported broader semantics stay out

#### [Implementation Comment]
Added `terrain` to `AuthoritativeState`. Updated `LegalityServiceV2` for WALL blockage and LoS.

#### [Task acceptance criteria]

Supported terrain and local spatial semantics affecting immediate action are explicit and enforced.

---

### [x] - [Task 3] - Complete supported building and local-structure interaction semantics relevant to direct gameplay

#### [Task Description]

Recover immediate interaction meaning for local structures without widening into full town-system simulation.

#### [Task technical implementation]

Implement or refine supported building/local-structure semantics that materially affect immediate action or combat behavior.

This task should remain focused on immediate semantics such as:

- local access constraints,
- local occupancy or interaction constraints,
- and local building-context behavior where preservation requires it.

#### [Task possible affected files]

- `src_v2/buildings/**`
- `src_v2/world/**`
- `src_v2/combat/**`
- `tests_v2/world/**`

#### [Task important notes]

Do not turn this into another economy or town phase.
That would be lazy scope drift.

#### [Task check list]

- [x] Supported building rules are explicit
- [x] Local interaction constraints are explicit
- [x] Immediate gameplay effects are explicit
- [x] Unsupported broader building semantics stay out
- [x] Behavior remains deterministic

#### [Implementation Comment]
Updated `TownResolutionSystem` to handle explicit `REST` intents at INN/HOME buildings.

#### [Task acceptance criteria]

Supported building/local-structure interaction semantics relevant to direct gameplay are explicit and enforced.

---

### [x] - [Task 4] - Recover preserved position-sensitive local behaviors such as chokepoints or bracketing where required

#### [Task Description]

Stop local action semantics from collapsing into generic open-space behavior when preserved legacy rules depend on positioning.

#### [Task technical implementation]

Implement or refine preserved position-sensitive local semantics where the replacement ledger requires them, including where relevant:

- chokepoint behavior,
- bracketing or local flanking-like constraints,
- or other position-sensitive local action effects that materially shape immediate conflict.

#### [Task possible affected files]

- `src_v2/world/**`
- `src_v2/combat/**`
- `src_v2/tactical/**`
- `tests_v2/tactical/**`

#### [Task important notes]

Do not invent cinematic positioning systems.
Recover only what the ledger actually requires.

#### [Task check list]

- [x] Position-sensitive behaviors are explicit
- [x] Supported chokepoint behavior is explicit where relevant
- [x] Supported bracketing-like effects are explicit where relevant
- [x] Deterministic local semantics are preserved
- [x] Divergences are documented if needed

#### [Implementation Comment]
Integrated Bracketing and High-Ground bonuses into the combat resolution pipeline.

#### [Task acceptance criteria]

Supported position-sensitive local action semantics are explicit where preservation requires them.

---

### [x] - [Task 5] - Add direct contract tests for local environment and world-interaction semantics

#### [Task Description]

Prove immediate environment semantics directly.

#### [Task technical implementation]

Add focused tests for:

- local terrain constraints,
- local building interaction constraints,
- position-sensitive local action behavior,
- and immediate world-interaction rules that materially shape direct gameplay.

#### [Task possible affected files]

- `tests_v2/world/test_local_environment_semantics.py`
- `tests_v2/world/test_building_interaction_contract.py`
- `tests_v2/tactical/test_position_sensitive_local_behavior.py`

#### [Task important notes]

Do not leave local environment proof hidden inside broad combat runs.

#### [Task check list]

- [x] Terrain tests exist
- [x] Building/local structure tests exist
- [x] Position-sensitive tests exist
- [x] Immediate world-interaction tests exist
- [x] Tests are part of standard validation flow

#### [Implementation Comment]
Created focused tests in `tests_v2/world/` and `tests_v2/tactical/`.

#### [Task acceptance criteria]

Local environment/world-interaction semantics are directly proven by focused contract tests.

---

### [x] - [Task 6] - Publish the local environment/world-interaction contract for supported Phase 8 scope

#### [Task Description]

Freeze local environment semantics into one explicit reference artifact.

#### [Task technical implementation]

Publish one local-world contract package covering:

- supported terrain constraints,
- supported building/local-structure semantics,
- supported position-sensitive local behavior,
- supported immediate world-interaction rules,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/local_world_interaction_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase8_semantic_notes.md`

#### [Task important notes]

If this contract is not explicit, later phases will quietly broaden or rewrite local world semantics.

#### [Task check list]

- [x] Terrain rules are documented
- [x] Building/local-structure rules are documented
- [x] Position-sensitive rules are documented
- [x] Immediate world-interaction rules are documented
- [x] Known exclusions are documented

#### [Implementation Comment]
Published `docs/engine/local_world_interaction_contract.md`.

#### [Task acceptance criteria]

The project has one explicit contract for supported local environment/world-interaction semantics.
