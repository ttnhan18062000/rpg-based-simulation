---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-TOWN-COUNCIL-HAZARD-DA
artifact_type: investigation
tags: [world, faction, simulation-quality]
---

# Investigation — TCK-20260710-TOWN-COUNCIL-HAZARD-DA

## Current Behavior

**`town_council` faction definition** — `data/content/social/factions.yaml:11-19`:
```yaml
- id: "town_council"
  display_name: "Town Council"
  alignment_bucket: "defender"
  influence_role: "sovereign"
  common_races: ["human", "dwarf", "elf"]
  themes: ["village", "frontier"]
  legacy_engine_bucket: "TOWN_COUNCIL"
```
No `hazard_immunities` key at all (defaults to `[]` per schema).

**`bandit_road` region** — `data/content/world_modules/bandit_road_trade_pressure.yaml:8-14`:
`hazard_level: 2.0`, `hazard_kind: "NATURAL_TERRAIN"`. Correctly matches `bandit_company`'s
`hazard_immunities: ["NATURAL_TERRAIN"]` (`factions.yaml:65-73`).

**`trading_company_hub` module's `hometown` region** — `data/content/world_modules/
trading_company_hub.yaml:18-26`: `hazard_level: 0.5`, `hazard_kind: "NATURAL_TERRAIN"`. The
module's own `population_recipes` (`trading_company_hub.yaml:27-31`) spawn only `merchant_league`
there (`merchant_league` now carries `hazard_immunities: ["NATURAL_TERRAIN"]`,
`factions.yaml:54-62` — added by `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`). `factions:
["merchant_league", "town_council"]` (`trading_company_hub.yaml:26`) is a module-level metadata
list, not a population assignment.

**Drain mechanism (read-only reference)** — `src/world/environment.py::EnvironmentService.
calculate_hazard_drain` (lines 16-41): resolves `get_faction_id_str(entity)`, checks it against
`region.hazard_kind in get_faction_semantics_service().get_hazard_immunities(faction_id)`; if no
match, drain = `int(region.hazard_level * (1.0 + calamity_intensity) * 10.0)`, further scaled
`*1.5` if `"MIASMA"` is an active modifier. Unconditional, faction-declared, never inferred from
hostility. Working exactly as designed — confirmed not to be touched by this ticket.

## Blast-Radius Check (Result)

**Clean.** Checked both worlds' actual composed/resolved specs, not the module in isolation:

- `data/worlds/urban_political/resolved/world.resolved.yaml`: `trading_company_hub` is composed
  with `namespace: "trading"`, so its `hometown` region resolves to region id
  `trading_hometown` (`hazard_level: 0.5`, `hazard_kind: NATURAL_TERRAIN`, lines 37-49). Its only
  population entry is `trading_pop_0` (`count: 6, role: merchant, faction: merchant_league,
  spawn_region: trading_hometown`, lines 197-201) — **no `town_council` entity is spawned
  there.** `town_council`'s entire population in `urban_political`
  (`frontier_village_population_village_worker` ×8, `frontier_village_population_frontier_guard`
  ×3, `frontier_village_population_village_blacksmith` ×1, all `spawn_region: hometown`,
  `hazard_level: 0.0`) is at the zero-hazard `frontier_village_core` `hometown` region, plus the
  2 `merchant_caravan_frontier_guard` at `bandit_road` (the case in question).
- `data/worlds/generated_frontier_3_42/resolved/world.resolved.yaml`: does **not** compose
  `trading_company_hub` at all (`module_refs`: `frontier_village_core`, `old_mine_resource_loop`,
  `bandit_road_trade_pressure`, `goblin_camp_conflict`, `moon_cult_ruins`, `orc_clan_territory`).
  `town_council`'s only hazard-level>0 exposure here is the identical 2-entity
  `merchant_caravan_frontier_guard` group at `bandit_road`.

**Conclusion**: `town_council` is populated in exactly one hazardous region across both worlds —
`bandit_road` (2 `frontier_guard` entities each world). The candidate `trading_hometown`/`hometown`
exposure named in the ticket's Scope does **not** materialize in either composed world; the
module's `factions:` list is metadata, not a population wiring, and no world's `world.yaml` adds a
separate `town_council` population recipe against that region id. A corpus-wide `grep` was not
performed beyond the two named worlds (out of scope per ticket's "any world beyond..." clause) —
if a third world later composes `trading_company_hub` *and* separately wires a `town_council`
population recipe to its `hometown`/namespaced region, that would be new information requiring a
fresh blast-radius check, not an assumption this ruling already covers it.

## Mechanics / Engine Constraints

`docs/mechanics/05_world_evolution.md` §3 "Regional Sovereignty" → "Hazard Impacts" / "Native
Endurance to a Region's Hazard Kind" (lines 55-93) is authoritative:

- Endurance is "strictly a property a faction declares for itself, never an inference from being
  hostile (or not) to another faction." The doc's own illustrative examples (`wild_beast_pack`,
  `goblin_warband` enduring "their own forest habitats"; `undead_remnants` enduring "the
  corruption of their own battlefield for a distinct in-fiction reason") are all cases of a
  faction native to the hazard it's exempt from.
- "A hazard kind that no faction present has declared endurance for hurts **every** faction
  standing in it equally" — the doc's explicit worked example is a hero party and a wolf pack
  fighting each other inside a `TOXIC_GAS` region, both taking full unmitigated drain, "because
  neither faction lists `TOXIC_GAS` in its `hazard_immunities`."
  This directly informs the ruling: `town_council`'s guards are not native to `bandit_road` (a
  wilderness/`road` region, `type: "road"`, `tags: [wilderness]`) — they are dispatched there
  specifically because it is bandit-contested, i.e. the opposite of "native habitat."
- The doc is explicit that this is opt-in per content and warns against blanket reasoning; it does
  not itself dictate whether `town_council` should be added — that judgment is exactly what this
  ticket exists to make.

## Parity Ledger Overlap

- `docs/parity_ledger/world_dynamics.yaml::WORLD-029` (P0, `verified`) — "Calamity aura and
  regional hazards apply local debuffs/drain." `test_path` includes
  `tests/unit/worldassembly/test_corpus_diversity.py::test_hazard_kind_matches_populating_faction_immunity`,
  `::test_population_stability`, `::test_generated_frontier_3_42_extended_population_stability`,
  and `tests/unit/worldbuilding/test_world_compiler.py::
  test_urban_political_resolved_bandit_road_hazard_kind_matches_source`. All `test_path` entries
  exist on disk and were confirmed runnable (see Prior Work / test run below).
- `docs/parity_ledger/world_dynamics.yaml::WORLD-060` (P0, `verified`) — "Regional hazards drain
  HP/Readiness based on intensity." Same `v2_evidence` narrative chain, same `test_path` family
  (no separate `test_path` line duplicated in the entry; it inherits WORLD-029's evidence trail
  contextually per the file's existing prose style).
- Both are **P0** — per the Authoritative Mechanics Rule, both require a passing `test_path`.
  **Only ruling (b) requires editing `v2_evidence`** for these two entries (per the ticket's own
  AC). Ruling (a) leaves both entries unchanged, since no mechanism or content behavior changes —
  only a design-intent record is added elsewhere.
- No parity ledger entry currently names `town_council` specifically at `bandit_road` as an
  accepted/documented exception either way — this ticket is the first to record that fact,
  regardless of ruling.

## Prior Work

- `stored_artifacts/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE/investigation.md` Risk #2 —
  first discovery. States plainly: "This may be intentional 'conflict pressure' flavor... the
  investigation does not have evidence to decide this either way." Its arithmetic showed fixing
  the co-located `bandit_road` stale-compile bug (unrelated `bandit_company` recompile) was
  independently sufficient to clear `urban_political`'s 60% population floor — i.e. the
  `town_council` gap was never load-bearing for that ticket's own pass/fail criterion.
- `stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/
  investigation.md` Root cause 2 — second, independent re-discovery of the identical case,
  same non-committal framing, explicitly cross-referencing the first investigation's Risk #2
  "verbatim." Its Root cause 3 (tick-budget-throttle wall-clock non-determinism, unrelated engine
  behavior, explicitly out of scope for this ticket) is the *dominant* driver of that world's
  extended-window (700-1000 tick) population erosion — the `town_council`/`bandit_road` gap
  (Root cause 2) is described as "a real, distinct, fixable gap in its own right" but was never
  isolated as the dominant cause of any test failure.
- `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/investigation.md` "Why the first-pass
  mechanism was rejected" (lines 49-62) — the rejected design gated exemption on
  `entity.identity.faction == Faction.MONSTER_HORDE and region.kind == "WILDERNESS"`; rejected
  specifically because it "conflates 'is bucketed MONSTER_HORDE' with 'endures hazards.'" This is
  directly relevant anti-pattern evidence: `town_council` is `alignment_bucket: "defender"`,
  `legacy_engine_bucket: "TOWN_COUNCIL"` — nothing about its bucket implies terrain endurance one
  way or the other, so neither ruling can lean on bucket-based reasoning; only an explicit,
  faction-specific `hazard_immunities` declaration (ruling b) or an explicit divergence record
  (ruling a) satisfies the mechanism's own design discipline.
- `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` (Phase 1.1 sibling) — **confirmed still in
  `tickets/todos/simq-roadmap-phase1-process-hardening/`, not started, not in
  `tickets/inprogress/`.** Its own text explicitly designs for this ordering ("if P2-Q lands
  first, prefer letting the test pass unaided"). Its planned temporary test-level exception in
  `tests/unit/worldassembly/test_corpus_diversity.py` (a narrow, named `town_council`/
  `bandit_road` carve-out) **does not exist yet** — confirmed by grep of the current file (no
  `town_council` or `bandit_road`-specific exception comment present). `docs/plans/
  audit_fix_plan.md` line 800 currently states P2-O's "ticket exists at
  `tickets/inprogress/TCK-20260710-HAZARD-KIND-CORPUS-WIDE.md`" — **this is stale**; the file is
  actually still under `tickets/todos/simq-roadmap-phase1-process-hardening/`, not
  `tickets/inprogress/`. Flagged for the Plan/Finalize phase to correct if in scope, since this
  ticket's own AC does not include fixing that unrelated sibling-ticket path reference.
- **Corpus consistency finding**: `merchant_league`'s own `bandit_road` exposure — named in this
  ticket's Out of Scope as "also flagged, unresolved, in both prior investigations" — is **no
  longer unresolved**. `factions.yaml:54-62` shows `merchant_league` already carries
  `hazard_immunities: ["NATURAL_TERRAIN"]`, added by `TCK-20260708-DUNGEON-URBAN-POPULATION-
  COLLAPSE` (confirmed in that investigation's text and in `WORLD-060`'s `v2_evidence`: "merchant_
  league gains a new NATURAL_TERRAIN hazard_immunities entry"). `town_council` is therefore now
  **the only** populating faction at `bandit_road` without a matching `hazard_immunities` entry —
  every other faction present (`bandit_company`, `merchant_league`) is already immune. This is new
  information relative to the ticket's own framing (written assuming `merchant_league` was still
  an open, parallel case) and sharpens the ruling: it is no longer "two unresolved cases," it is
  "one anomaly in an otherwise fully-reconciled region."

## Ruling Evidence

**Evidence supporting (a) — rule intentional / document as divergence:**
- `test_population_stability` passes cleanly today for both `urban_political` and
  `generated_frontier_3_42` at the existing 300-tick window with `town_council`'s unmitigated
  `bandit_road` exposure present and unmodified (confirmed by direct test run, see Test Plan) —
  the exposure is not currently causing measurable harm against the documented floor.
  `test_hazard_kind_matches_populating_faction_immunity` also currently passes for both worlds
  without any `town_council` change, because it asserts region-level match ("`any` populating
  faction's immunity matches"), not per-entity coverage — `bandit_company`'s (and now
  `merchant_league`'s) immunity already satisfies it.
- Small, isolated blast radius: exactly 2 entities per world, both a small fraction of each
  world's total population, both explicitly *stationed* (not spawned-native) at a
  bandit-contested wilderness road — thematically the opposite of "native habitat," which is the
  mechanics doc's own criterion for endurance.
- The mechanics doc's worked example (hero party vs. wolf pack both taking full `TOXIC_GAS` drain
  because neither declares endurance) structurally supports non-native factions taking drain by
  design in a hazard they are not adapted to — a guard escort posted to a dangerous road taking
  slow attrition over a long campaign is a coherent "conflict-pressure" narrative, consistent with
  how both prior investigations independently characterized it without being asked to.
- Two independent investigations converged on the same non-committal read without either treating
  it as an obvious bug, despite both having full visibility into the mechanism and motive to fix
  it if it looked like an oversight.

**Evidence supporting (b) — rule genuine gap / add `hazard_immunities`:**
- Both prior investigations explicitly declined to decide, calling it "a design question, not a
  technical unknown" and stating outright they "do not have evidence to decide this either way" —
  this is closer to an acknowledged gap in decision-making than a confident endorsement of
  intentionality.
- Corpus consistency (see Prior Work finding above): `town_council` is now the *only* populating
  faction left unmitigated at `bandit_road` — every other faction present already has a matching
  immunity. A blanket-per-region pattern ("everyone stationed here who isn't hostile-invader gets
  exempted") is visible elsewhere in the corpus's authoring history (successive "the last
  remaining never-declared module" fixes across `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` →
  `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` → `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-
  POPULATION-COLLAPSE`), suggesting the corpus's overall authoring trend has been toward closing
  these gaps rather than preserving them as flavor.
- Root cause 2 in the frontier investigation still counts `town_council`'s `bandit_road` drain as
  "already contributing at the earliest checkpoints" (non-zero effect), even though it is not the
  dominant driver of that world's extended-window failure (Root cause 3 dominates). "Not currently
  load-bearing for a floor test" is evidence of tolerance, not proof of intentional design.
- Blast radius being clean (only 2 entities, only one region, only two worlds) is exactly the
  profile the ticket's own Assumptions describe as the "safe corpus-wide" precondition for adding
  `NATURAL_TERRAIN` to `town_council` — the narrower-`hazard_kind` fallback path is not needed
  here since there is no unwanted exemption spillover to guard against.

**Recommendation (not binding — planner decides):** the evidence leans toward (a) — intentional —
primarily because of the passing `test_population_stability` floor at the documented window and
the mechanics doc's own "native vs. non-native" framing lining up with "guard posted to contested
road" as the paradigm non-native case, not the native one. However, the corpus-consistency finding
(`town_council` now uniquely unmitigated) and both investigations' explicit non-endorsement are
real evidence for (b) that a planner should weigh, especially if closing the last remaining gap is
valued for its own sake (matching the corpus's demonstrated authoring trend).

## Risks and Open Questions

1. **This ruling's rationale may mechanically also apply to future non-`town_council` non-native
   factions stationed in other hazard regions corpus-wide** — out of scope per the ticket's own
   text, but flagged since `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` (Phase 1.1) will run a
   corpus-wide sweep and may surface structurally identical cases. If so, whether this ticket's
   ruling generalizes as precedent is a fresh judgment call for that ticket, not something to
   assume here.
2. **`docs/plans/audit_fix_plan.md` line 800's stale path reference** (`tickets/inprogress/
   TCK-20260710-HAZARD-KIND-CORPUS-WIDE.md`, actually in `tickets/todos/
   simq-roadmap-phase1-process-hardening/`) is a pre-existing doc inaccuracy unrelated to this
   ticket's own scope but discovered during investigation — flagging rather than silently fixing,
   since correcting it is not this ticket's AC.
3. **If ruling (b) is chosen**, the exact `hazard_immunities` value is a further open question:
   the ticket's Assumptions suggest `["NATURAL_TERRAIN"]` "if safe corpus-wide" (confirmed safe by
   the blast-radius check above) — but adding `NATURAL_TERRAIN` broadly to `town_council` (not
   scoped only to `bandit_road`) would also silently exempt `town_council` from *any* future
   region declaring `NATURAL_TERRAIN`, including regions not yet authored. This is consistent with
   how every other faction's `hazard_immunities` entry works in this corpus (faction-level, not
   region-scoped — there is no existing per-region immunity mechanism), so it would not be a new
   architectural pattern, but the planner should confirm this blanket-per-kind (not
   blanket-per-region) semantics is acceptable before implementing.
4. **Race-level `hazard_immunities`** (`RaceDefinition` extension point) remains out of scope per
   `TCK-20260701-HAZARD-NATIVE-IMMUNITY`'s explicit deferral — not revisited here, not needed for
   either ruling.

## Anti-Drift Hazards

- Do not modify `src/world/environment.py::calculate_hazard_drain` or
  `src/worldassembly/resolver.py`'s `"PHYSICAL"` hazard_kind default under any ruling — both are
  explicitly out of scope and working as documented; every prior investigation in this chain
  reaffirms this.
- Do not expand this ruling to `merchant_league` — its `bandit_road` case is **already resolved**
  (see Prior Work corpus-consistency finding); do not re-touch its `hazard_immunities` entry under
  this ticket.
- Do not silently absorb `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`'s scope (corpus-wide test
  extension) into this ticket — that ticket is still unstarted; this ticket only needs to leave a
  ruling that ticket can react to when it eventually lands, per its own explicit design ("if P2-Q
  lands first, prefer letting the test pass unaided").
- If ruling (b), do not forget the required recompile of **both** `urban_political` and
  `generated_frontier_3_42` — a source-only edit without recompiling reproduces the exact
  stale-artifact bug class both prior investigations diagnosed for this same content family.
- If ruling (a), do not add a `hazard_immunities` entry "just in case" alongside the divergence
  record — the AC is explicit that `factions.yaml` and `world_dynamics.yaml` must be **unchanged**
  under ruling (a).
