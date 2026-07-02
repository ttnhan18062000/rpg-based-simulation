---
status: active
artifact_type: plan
ticket_id: TCK-20260701-HAZARD-NATIVE-IMMUNITY
date: 2026-07-02
---

# Plan — TCK-20260701-HAZARD-NATIVE-IMMUNITY

> **Revision note (2026-07-02):** This plan supersedes an earlier draft that gated the
> exemption on `entity.identity.faction == Faction.MONSTER_HORDE AND region.kind ==
> "WILDERNESS"`. The user rejected that design mid-session: it re-derives "endurance" from
> hero-hostility ("monster faction" = "hostile to hero"), which is exactly the coupling the user
> wants removed. Requirement, verbatim: a faction/race can *endure* a **specific kind of
> hazard/drain** for its own in-fiction reason (e.g. fiends endure chaos corruption because
> they're fiends, not because they're hostile to heroes), independent of who is "hostile" to
> whom — and a hazard a nobody is flagged as enduring (e.g. toxic gas) must hurt every faction
> present, including two mutually hostile ones fighting in it together. See "Migration Note"
> at the bottom for what to do with the stale uncommitted code this repo currently has on disk.

## Decided Mechanism: Typed Hazard + Typed Faction Endurance

Two independent, data-driven pieces, both defaulting to "no immunity anywhere" so existing
behavior is unchanged unless content explicitly opts in:

1. **`RegionState.hazard_kind: str = "PHYSICAL"`** (new durable field) — what *kind* of hazard a
   region's passive drain represents. Threaded through from a new, optional
   `RegionSpec.hazard_kind: Optional[str] = Field("PHYSICAL", ...)` content field
   (`src/worldbuilding/schema.py:27-35`, sibling to the existing `hazard_level`), compiled in
   `src/worldbuilding/compiler.py:164-172` exactly like `hazard_level` already is
   (`hazard_kind=getattr(r_spec, "hazard_kind", "PHYSICAL")`).
2. **`FactionDefinition.hazard_immunities: List[str] = Field(default_factory=list)`** (new
   catalog content field, `src/content/schema.py:149-156`, sibling to the existing
   `alignment_bucket`/`legacy_engine_bucket`/`common_races` fields on the same class) — the set
   of `hazard_kind` values a faction's members endure without harm. Empty by default.

`EnvironmentService.calculate_hazard_drain(region, entity)` resolves the entity's catalog
faction id via the **already-existing** `get_faction_id_str(entity)` helper
(`src/content_semantics/faction.py:42-60` — reads `entity.identity.properties["faction_id"]`,
falling back to the legacy `Faction` enum name), looks up that faction's `hazard_immunities` via
the **already-existing** process-singleton `FactionSemanticsService`
(`get_faction_semantics_service()`, `src/content_semantics/faction.py:21-28` — explicitly
documented in its own docstring as "a valid performance optimization for the hot path"), and
returns `0` if `region.hazard_kind` is in that set; otherwise the base formula is unchanged.

```python
@staticmethod
def calculate_hazard_drain(region: RegionState, entity: EntityState) -> int:
    from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service

    faction_id = get_faction_id_str(entity)
    defn = get_faction_semantics_service().repo.get_faction(faction_id)
    if defn is not None and region.hazard_kind in defn.hazard_immunities:
        return 0

    base_drain = region.hazard_level * (1.0 + region.calamity_intensity)
    if "MIASMA" in region.active_modifiers:
        base_drain *= 1.5
    return int(base_drain * 10.0)
```
(`FactionSemanticsService` gets a thin `get_hazard_immunities(faction_id) -> frozenset[str]`
convenience method alongside its existing `get_alignment_bucket`/`get_legacy_faction_bucket`,
used here in place of the direct `.repo.get_faction(...)` call shown above for consistency with
the service's existing style — direct repo access shown here only to make the resolution path
explicit.)

### Why this design (and why the earlier one was wrong)
- **Decouples "endures a hazard" from "is hostile to hero."** Nothing in the check references
  `Faction.HERO_GUILD`, `Faction.MONSTER_HORDE`, or region *type*. Two factions can be mutually
  hostile (hero vs. wolf) and still both lack immunity to a given `hazard_kind` (e.g.
  `"TOXIC_GAS"`), so both take full drain when fighting in it — this falls out of the design for
  free, no special-casing needed, matching the user's stated scenario directly.
- **A faction/race endures a hazard because content says so, not because of a faction bucket.**
  `wild_beast_pack` gets `hazard_immunities: ["NATURAL_TERRAIN"]` because wolves belong in their
  den, not because `legacy_engine_bucket: "MONSTER_HORDE"` implies universal hazard immunity — a
  `MONSTER_HORDE`-bucketed faction with no authored `hazard_immunities` takes full drain from
  every hazard, exactly like a `HERO_GUILD`-bucketed one. This directly satisfies "hostile
  factions/races to hero [are not automatically] immune."
- **Reuses existing, already-hot-path-sanctioned infrastructure.** `get_faction_id_str` and
  `get_faction_semantics_service()`/`FactionSemanticsService` already exist specifically to
  resolve an entity's catalog-level faction id and query faction-catalog semantics at runtime;
  this ticket adds one field to an existing schema class and one query method, not a new
  subsystem. `entity.identity.properties["faction_id"]` is confirmed populated for **every**
  production entity by both spawn paths (`src/worldbuilding/compiler.py:304-312` and
  `src/worldassembly/entity_spawner.py:104-114`), so no entity-side plumbing is needed.
- **Extensible to race, not just faction, without redesign.** `RaceDefinition`
  (`src/content/schema.py:133-142`, `data/content/living/races.yaml`) is a real, separate
  catalog (wolf is `id: "wolf"` there) with the same `CatalogBaseDefinition` base and an
  existing `repo.get_race()` lookup. If a future case needs race-level (not faction-level)
  granularity, the identical `hazard_immunities: List[str]` field can be added there and the
  resolution in `calculate_hazard_drain` extended to check `entity.identity.properties["race_id"]`
  (also already populated by both spawn paths) as a second, more-specific source, unioned with
  the faction-level set. **Not implemented in this ticket** — no current content needs
  race-level distinction (a faction's `common_races` are currently homogeneous re: habitat,
  e.g. `wild_beast_pack`'s wolves/spiders/slimes are all forest fauna). Documented here as the
  designed extension point per the user's "faction/race" phrasing, not silently dropped.
- **Old design's flaw, concretely**: `Faction.MONSTER_HORDE == entity.identity.faction` treats
  "is a monster" as "endures hazards," which is factually the same bug shape as "hostile to hero
  implies immune" — the user's redirect specifically named this coupling as wrong. It also could
  never model "toxic gas hurts everyone" without a second special case, whereas the new design
  handles it as the default (no faction has `"TOXIC_GAS"` in `hazard_immunities` unless
  authored).

### Regression Safety (unchanged guarantee)
`RegionState.hazard_kind` defaults to `"PHYSICAL"`; `FactionDefinition.hazard_immunities`
defaults to `[]`. No existing region/faction in the catalog or in any test fixture sets either
field today, so `region.hazard_kind in defn.hazard_immunities` is `False` for every existing
test and every existing region until content is explicitly authored — identical safety property
to the rejected design, re-verified against the same test files (see test_plan.md Regression
Surface).

## Ordered Plan Steps

1. **`src/content/schema.py`** — add `hazard_immunities: List[str] = Field(default_factory=list,
   description="Hazard-kind tags this faction's members endure without harm (e.g.
   'NATURAL_TERRAIN', 'CHAOS_CORRUPTION').")` to `FactionDefinition` (line ~149-156).
2. **`src/worldbuilding/schema.py`** — add `hazard_kind: Optional[str] = Field("PHYSICAL",
   description="Semantic type of this region's passive hazard drain (e.g. 'PHYSICAL',
   'NATURAL_TERRAIN', 'TOXIC_GAS').")` to `RegionSpec` (line ~27-35).
3. **`src/core/state.py`** — add `hazard_kind: str = "PHYSICAL"` to `RegionState` (line
   ~236-258), alongside `hazard_level`. Update `to_canonical_dict` if it enumerates fields
   explicitly (verify at implementation time — `RegionState.to_canonical_dict` was read in
   investigation but not exhaustively; confirm all durable fields are included in the canonical
   hash so determinism/replay is preserved).
4. **`src/worldbuilding/compiler.py`** — thread `hazard_kind=getattr(r_spec, "hazard_kind",
   "PHYSICAL")` into the `RegionState(...)` construction at line ~164-172, sibling to the
   existing `hazard_level=getattr(r_spec, "hazard_level", 0.0)`.
5. **`src/content_semantics/faction.py`** — add `FactionSemanticsService.get_hazard_immunities(self,
   faction_id: str) -> frozenset[str]`: `defn = self.repo.get_faction(faction_id); return
   frozenset(defn.hazard_immunities) if defn else frozenset()`.
6. **`src/world/environment.py`** — replace `calculate_hazard_drain` per the code block above.
   `Faction` import may become unused in this function (still used in `get_aura_multipliers` in
   the same file — do not remove the module-level import).
7. **Content authoring** (now in scope — see "Scope Change" below):
   - `data/content/world_modules/wolf_den_near_forest.yaml` — add `hazard_kind:
     "NATURAL_TERRAIN"` to both regions (`near_forest`, `wolf_den`).
   - `data/content/world_modules/goblin_camp_conflict.yaml` — add `hazard_kind:
     "NATURAL_TERRAIN"` to region `goblin_camp` (same principle: goblins are native to their own
     camp; leaving this out would be an inconsistent half-fix of the same bug class).
   - `data/content/social/factions.yaml` — add `hazard_immunities: ["NATURAL_TERRAIN"]` to
     `wild_beast_pack` and `goblin_warband`.
   - Do **not** author a `"CHAOS_CORRUPTION"`/fiend example into production content — no
     fiend/demon faction or chaos-corruption region exists in the catalog today, and inventing
     one is unrequested scope. That example is illustrated in the mechanics doc and covered by a
     synthetic (test-fixture-only) unit test instead (see test_plan.md).
8. **`tests/unit/world/test_regional_consequences.py`** (and/or a new
   `tests/unit/world/test_hazard_endurance.py` — decide at implementation time based on file
   size) — add the tests specified in test_plan.md.
9. **`tests/unit/content_semantics/test_semantics.py`** — add a test for
   `FactionSemanticsService.get_hazard_immunities` using the real catalog (`wild_beast_pack` →
   `{"NATURAL_TERRAIN"}`), mirroring the existing `test_faction_semantics` pattern in that file.
10. **`docs/mechanics/05_world_evolution.md`** — **CORRECTED PER ARCHITECTURE REVIEW
    (2026-07-01, redesign pass): this ticket's own FIRST pass already made and fixed this exact
    mistake (see `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/plan.md` lines 89-104)
    — the plan regressed to §2 during the redesign; do not repeat the error.** The prose
    describing `calculate_hazard_drain`'s per-entity behavior ("Passive HP Drain: Health is
    lost every tick based on the hazard's intensity") lives in `### Hazard Impacts` (lines
    51-55) under `## 3. Regional Sovereignty`, NOT `## 2. Regional Trauma & Hazards` (which
    only covers Trauma Score → hazard-level escalation, no per-entity drain claim). Edit
    `### Hazard Impacts` under §3 directly: document the hazard-kind/faction-endurance
    mechanic there — regions carry a `hazard_kind`; factions declare which hazard kinds their
    members endure; endurance is unconditional (zero drain) and independent of any hostility
    relationship. Use the toxic-gas-affects-both-sides case as the explicit illustrative
    counter-example so the doc doesn't read as "monsters are immune to danger." Add a short
    cross-reference in §2 pointing to §3's `Hazard Impacts` for readers following "Hazard
    Level" from there. (The doc has two sections both numbered "## 3." — pre-existing
    numbering defect, out of scope.)
    **Also add (non-blocking review note, folded in here rather than a new step):** state
    explicitly that `data/worlds/sandbox_world/`'s compiled/resolved artifacts stay stale
    (no immunity effect) until recompiled — that recompile is `TCK-20260701-SANDBOX-MONSTER-BALANCE`'s
    job, not this ticket's, per that ticket's own dependency note.
11. **`docs/parity_ledger/world_dynamics.yaml`** — update `WORLD-060` `v2_evidence`/`test_path`
    as previously planned, describing the hazard-kind/endurance mechanism (not the old
    faction-bucket one).
12. **`docs/guidelines/intentional_divergences.md`** — add the divergence entry (Rationale
    Class: **Bug Fix**, same justification as before — the unused `entity` parameter). Content
    must describe the *shipped* mechanism (typed hazard + typed faction endurance), not the
    rejected faction-bucket one.

## Scope Change (from original ticket)
The original ticket's Out of Scope said "`sandbox_world`-specific changes... engine code only."
That guard is **preserved** for the *compiled world instance* (`data/worlds/sandbox_world/` —
still untouched by this ticket). It is **narrowed**, not violated, by this plan: the new
mechanism is data-driven by design and cannot exempt anything until `hazard_kind` and
`hazard_immunities` are authored somewhere — Step 7 touches shared **catalog source content**
(`data/content/world_modules/*.yaml`, `data/content/social/factions.yaml`), which is reusable
content shipped with the engine, not a specific compiled world instance. Without Step 7 the
ticket's core acceptance criterion ("native entities take reduced/zero drain") is unfalsifiable
in production — only satisfiable in unit tests with synthetic fixtures. Recorded here explicitly
rather than silently expanding scope; the ticket's Scope/Out of Scope sections are being updated
to match (see ticket file edit accompanying this plan revision).

## Scope Guards (unchanged/reaffirmed)
- Do NOT change the base drain formula/constants for entities without a matching
  `hazard_immunities` entry.
- Do NOT touch `src/world/calamity.py`.
- Do NOT touch `data/worlds/sandbox_world/` (the compiled instance) — only shared catalog
  source content per Step 7.
- Do NOT add a fiend/demon faction or a chaos-corruption region to production content — that
  example stays illustrative/test-only.
- Do NOT implement race-level (`RaceDefinition.hazard_immunities`) resolution in this ticket —
  documented extension point only.

## Dependency Map
`src/content/schema.py` (FactionDefinition field)
  → `data/content/social/factions.yaml` (authored values)
  → `src/content_semantics/faction.py` (`get_hazard_immunities`)
`src/worldbuilding/schema.py` (RegionSpec field)
  → `data/content/world_modules/wolf_den_near_forest.yaml`,
    `data/content/world_modules/goblin_camp_conflict.yaml` (authored values)
  → `src/core/state.py` (`RegionState.hazard_kind`)
  → `src/worldbuilding/compiler.py` (compile-time threading)
`src/world/environment.py` (`calculate_hazard_drain`, consumes both of the above via
  `get_faction_id_str` + `FactionSemanticsService`)
  → `src/engine/world_dynamics.py` (call site, unchanged)
  → tests (Step 8, 9) → parity ledger (Step 11) → mechanics doc (Step 10) → divergence log
    (Step 12)

## Acceptance Criteria Mapping
| AC | Satisfied by |
|---|---|
| `calculate_hazard_drain` reads `entity` to determine native-vs-hostile status | Step 6 (reads entity's resolved faction id, not raw hostility) |
| Native entities take reduced/zero drain in home-type region; hostile entities in same region take full drain | Steps 1-7 (wolf in `wolf_den` with `NATURAL_TERRAIN` immunity = 0; hero in same region = full, since `hero_guild`-mapped factions have no `hazard_immunities`) |
| `docs/mechanics/05_world_evolution.md` updated and in parity with code | Step 10 (corrected location: §3 "Regional Sovereignty" / "Hazard Impacts", plus §2 cross-reference) |
| Parity ledger entry updated/added with passing `test_path` | Step 11 |
| New unit tests cover native/hostile/zero-hazard cases | Steps 8-9 + test_plan.md |
| No regression in existing hazard/environment/world_dynamics tests | Regression Safety section above, re-verified against same test files as prior revision |
| `docs/guidelines/intentional_divergences.md` entry added if applicable | Step 12 |
| *(new, from user redirect)* A hazard kind with no faction opted in affects all factions present, including mutually hostile ones | test_plan.md toxic-gas-equivalent test — falls out of the design with no special-case code |

## Migration Note — Stale Uncommitted Code Found On Disk
`git status`/`git diff` (checked 2026-07-02, mid-session) shows **uncommitted, unstaged**
working-tree modifications to `src/world/environment.py`,
`docs/guidelines/intentional_divergences.md`, `docs/mechanics/05_world_evolution.md`,
`docs/parity_ledger/world_dynamics.yaml`, and `tests/unit/world/test_regional_consequences.py`
that implement the **rejected** `Faction.MONSTER_HORDE`-in-`region.kind == "WILDERNESS"` design
(verbatim match to this plan's earlier revision — likely written by a concurrently-running sibling
Implement-phase agent operating on the same working tree before the user's redirect reached this
phase). These changes are not committed and **must not be committed as-is** — the Implement phase
must replace them with the typed-hazard-kind/typed-faction-endurance design in this revision, not
build on top of the stale diff. This investigation/plan phase does not modify source or doc files
directly (out of this phase's scope); flagging here so the Implement phase does not silently
inherit the superseded approach.

## Unresolved Questions
None. The mechanism, its data model, its resolution path, and its content-authoring scope are
fully decided above with evidence. The only judgment call — extending `goblin_camp_conflict`
alongside `wolf_den_near_forest` in Step 7 — is made explicitly (for consistency, same bug
class) rather than left open.
