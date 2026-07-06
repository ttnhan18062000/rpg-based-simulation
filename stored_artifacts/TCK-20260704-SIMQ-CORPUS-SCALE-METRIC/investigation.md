---
ticket_id: TCK-20260704-SIMQ-CORPUS-SCALE-METRIC
phase: investigation
date: 2026-07-06
---

# Investigation: Track "distinct populated factions" as an explicit per-world scale metric

PHASE_TS: 2026-07-06T16:39:11Z

## Context search performed (per CLAUDE.md hard rule)

1. `mcp__knowledge-search__search_docs` (query: "world_compile_report.json distinct populated
   factions WorldCompiler scale metric") — top hits: `tickets/done/TCK-20260523-WORLD-COMPILER.md`
   (original WorldCompiler ticket), `docs/world/compiler_contract.md` (two-compilation-paths doc),
   `tickets/done/TCK-20260530-WORLD-PHASE3.md`/its stored investigation (Profile Consumer Bridge /
   `CompileProfileResolver`), and `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md`
   (the corpus-diversity precedent this ticket extends). No existing doc describes a
   "distinct populated factions" field — confirmed this is genuinely new instrumentation, not
   duplicated work.
2. `graphify query "world_compile_report.json WorldCompiler distinct populated factions scale
   metric"` — 2354-node BFS rooted at `WorldCompiler`/the exact sentence "State contains entities
   from at least two distinct factions. frontier_living" (a docstring/test-adjacent string hit
   confirming per-world faction-population variety is already an observed property, just not a
   reported one). Traversal surfaced `WorldCompiler` (`src/worldbuilding/compiler.py`),
   `AuthoritativeState`/`EntityState`/`FactionState` (`src/core/state.py`), `WorldSpec`
   (`src/worldbuilding/schema.py`), `WorldAssemblyResolver`/`CompileProfileResolver`
   (`src/worldassembly/resolver.py`), `RunArtifactRepository` (`src/observability/reporting/`) —
   confirmed `WorldCompiler.compile()` as the single relevant compile-time code path; no other
   undiscovered report-writer exists.

Both tools point at the same place the ticket body already names
(`src/worldbuilding/compiler.py`); raw grep/Read used only as follow-up, per Hard Rules.

## Source investigation cross-reference

Per the parent-ticket note, the path cited in this ticket
(`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`) was renamed; the
real, current location is
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` §2 ("World / scenario
scale diversity" table) and §4 open question 1. Read in full — §2's table is the authority this
ticket's field must reproduce exactly.

## Current Behavior

### 1. Where `world_compile_report.json` is generated

Single code path: `WorldCompiler.compile()` (`src/worldbuilding/compiler.py:110-531`), invoked from
`src/worldbuilding/cli.py::handle_compile` (line ~279, `report_path = output_report or str(world_dir
/ "world_compile_report.json")`) and from `src/lab/orchestrator.py:197-201` (lab-run compile path,
writes to a temp run dir, not `data/worlds/`). Both call sites pass `output_report_path` straight
into `WorldCompiler.compile`, which does the actual `json.dump` at line 526-528. There is exactly
one report-writing helper — the inline `report = {...}` dict literal at lines 513-524 followed by
the `json.dump` — no separate report-builder function to special-case.

Current report shape (verified against `data/worlds/wilderness_survival/world_compile_report.json`
and `data/worlds/frontier_extended/world_compile_report.json` on disk):

```json
{
  "world_id": "...",
  "seed": ...,
  "entity_count": ...,
  "region_count": ...,
  "resource_node_count": ...,
  "building_count": ...,
  "quest_count": ...,
  "warnings": [...],
  "compile_duration_ms": ...,
  "state_hash": "..."
}
```

This matches the compiler.py literal exactly — no drift between code and on-disk artifacts.

### 2. The exact data structure holding entity→faction assignment at compile time

Two different "faction" representations exist inside `WorldCompiler.compile()`, and only one of
them is the correct basis for "distinct populated factions":

- **`faction_enum` (coarse, wrong basis)** — `get_faction_enum(pop_spec.faction, context=context)`
  (compiler.py:283) maps each population's raw faction string onto the `Faction` enum
  (`src/core/enums.py:24`), which in this file's call pattern (no `catalog_repo` passed) only ever
  resolves to 4 buckets: `HERO_GUILD`, `MONSTER_HORDE`, `TOWN_COUNCIL`, `NEUTRAL` (fallback). This
  is used to build the `entities[...].identity.faction` int and to seed `global_resources`
  starting-gold keys. It cannot distinguish `undead_remnants` from `wild_beast_pack` (both bucket
  to `MONSTER_HORDE`) — using it would produce counts of at most 3-4 regardless of world, which
  does **not** match investigation.md §2 (`frontier_extended` = 9, `wilderness_survival` = 2 with
  two *different* monster factions).
- **`entity.properties["faction_id"]` (correct basis)** — set at compiler.py:315-323:
  ```python
  ent_properties = {
      "spawn_region": pop_spec.spawn_region,
      "population_id": pop_key,
      "faction_id": pop_spec.faction,
  }
  if context is not None and pop_key in context.entities:
      resolved = context.entities[pop_key]
      if hasattr(resolved, "faction_id") and resolved.faction_id:
          ent_properties["faction_id"] = resolved.faction_id
  ```
  This is the **raw, catalog-registered faction ID string** (e.g. `"undead_remnants"`,
  `"wild_beast_pack"`, `"merchant_league"`, `"forest_wardens"`) — resolved-composition context
  overrides the raw spec value when present, matching the same override precedent already used
  for `hp`/`atk`/`role`/etc. earlier in the same loop. `EntityState.properties` is a `@property`
  (`src/core/state.py:766`) that delegates to `self.identity.properties` (`IdentityComponent`,
  `src/core/state.py:469+`) — so `entity.properties.get("faction_id")` is the correct, already-used
  accessor (the compiler itself reads it the same way at line 433 for
  `pending_information_responses` target resolution: `e.properties.get("population_id")`).

**Conclusion:** "distinct populated factions" = the count of unique
`entity.properties.get("faction_id")` values across all compiled `entities`, excluding falsy/missing
values. This is a read-only aggregation over the already-built `entities: Dict[int, EntityState]`
local — no new state, no `FactionState`/`AuthoritativeState.factions` involvement at all.

### 3. Verification — recompiled all 10 worlds and cross-checked against investigation.md §2

Wrote a throwaway script (not committed) that mirrors `cli.py::handle_compile`'s exact
resolved-vs-raw branch logic (loads `resolved/world.resolved.yaml` + `resolved/compile_context.json`
via `CompileContext.from_dict` for composition-schema worlds, else `WorldRepository.load_world`),
using each world's own seed as recorded in its current `world_compile_report.json`, then computed
`len({e.properties.get("faction_id") for e in state.entities.values() if e.properties.get("faction_id")})`.

| World | Seed | Recomputed distinct populated factions | investigation.md §2 value | Match? |
|---|---|---|---|---|
| wilderness_survival | 101 | 2 (`undead_remnants`, `wild_beast_pack`) | 2 | yes |
| sandbox_world | 42 | 3 (`merchant_league`, `town_council`, `wild_beast_pack`) | 3 | yes |
| highland_traverse | 91 | 3 (`merchant_league`, `town_council`, `wild_beast_pack`) | 3 | yes |
| urban_political | 202 | 4 (`bandit_company`, `hero_guild`, `merchant_league`, `town_council`) | 4 | yes |
| dungeon_crawl | 303 | 4 (`bandit_company`, `goblin_warband`, `undead_remnants`, `wild_beast_pack`) | 4 | yes |
| swamp_border_world | 77 | 4 (`merchant_league`, `swamp_tribe`, `town_council`, `wild_beast_pack`) | 4 | yes |
| simq_routing_test | 42 | 5 (`goblin_warband`, `hero_guild`, `merchant_league`, `town_council`, `wild_beast_pack`) | 5 | yes |
| frontier_living_world | 42 | 6 (+`bandit_company`, `undead_remnants`, `goblin_warband`, ...) | 6 | yes |
| generated_frontier_3_42 | 42 | 7 (+`arcane_circle`, `orc_clan`) | 7 | yes |
| frontier_extended | 43 | 9 (+`forest_wardens`, `spirit_court`) | 9 | yes |

Recomputed `entity_count` for every world also matched the existing on-disk
`world_compile_report.json` exactly (e.g. `frontier_extended` = 56, `wilderness_survival` = 11),
confirming the recompile is faithfully reproducing the currently-committed artifacts (determinism
holds; no stale-compile drift of the kind found by
`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s hazard-kind investigation).

**No discrepancy found.** All 10 worlds match investigation.md §2's table exactly, using
`entity.properties["faction_id"]` as the extraction basis. This confirms both the field definition
and that investigation.md §2's numbers were computed the same way (almost certainly by the same
kind of ad hoc script against `resolved/world.resolved.yaml`'s population→faction assignments,
since that investigation states its counts came from "`world_compile_report.json` ... and
`resolved/world.resolved.yaml` (module composition, populated-faction count)").

### 4. Exact code change

In `src/worldbuilding/compiler.py`, inside `WorldCompiler.compile()`, add one field to the existing
`report = {...}` dict literal (lines 513-524), computed from the already-in-scope local `entities`
dict (no new variables needed elsewhere, no change to the `AuthoritativeState(...)` constructor
call, no change to `factions`/`FactionState` construction):

```python
        report = {
            "world_id": spec.world_id,
            "seed": seed,
            "entity_count": len(entities),
            "region_count": len(regions),
            "resource_node_count": len(resource_nodes),
            "building_count": len(buildings),
            "quest_count": len(compiled_quests),
            "distinct_populated_factions": len({
                fid for e in entities.values()
                if (fid := e.properties.get("faction_id"))
            }),
            "warnings": warnings,
            "compile_duration_ms": compile_duration_ms,
            "state_hash": state_hash
        }
```

Placed after `quest_count` (the last of the existing count fields) and before `warnings`, matching
the existing convention of "all count fields together, then warnings/timing/hash."

**Downstream consumer impact (checked, one breakage found):**
`tests/certification/test_world_compile_determinism.py::test_compile_report_contents` (lines
96-134) asserts `set(report.keys()) == expected_keys` against a **hardcoded, exhaustive** key set
(lines 108-119) that does not include the new field. This test **will fail** once the field is
added and **must be updated** in the same change (add `"distinct_populated_factions"` to
`expected_keys`). No other consumer does an exact-key-set check:
- `src/lab/store.py::load_compile_report` — passthrough JSON load, no key filtering.
- `src/lab/orchestrator.py` — passes `output_report_path` through, doesn't inspect keys.
- `tests/unit/lab/test_lab_result_store.py` — writes its own synthetic fixture JSON, doesn't call
  `WorldCompiler.compile()`, unaffected.
- `docs/parity_ledger/town_resource.yaml` — references `resource_node_count` only, prose, not a
  schema check.

### 5. Test coverage — `tests/unit/worldassembly/test_corpus_diversity.py`

Read in full (213 lines). Established pattern (`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`):
- `_load_compile_report(world_id)` helper (lines 67-71) reads
  `data/worlds/{world_id}/world_compile_report.json`, `pytest.skip`s if the file doesn't exist yet
  (never fails outright on a missing recompile — matches this ticket's Scope item 5, "recompile all
  10 worlds" being a prerequisite, not a hard dependency baked into the test itself).
- Existing `test_entity_count_band` (lines 111-122) is the closest precedent: a
  `@pytest.mark.parametrize` over a `dict[str, tuple[int, int|None]]` of expected bands, reading
  `report["entity_count"]` via the same helper.
- All 10 worlds are addressable via `WORLDS_ROOT = REPO_ROOT / "data" / "worlds"` already defined
  at module level (line 32) — no new path plumbing needed.

**Extending this file (not a new file) is the right call**: the module docstring already frames
itself as "corpus-diversity regression guards," this ticket's field is exactly a corpus-diversity
signal, and the `_load_compile_report` helper is directly reusable with zero changes. A new test
function `test_distinct_populated_factions` parametrized over a
`dict[str, int]` of `{world_id: expected_count}` (using investigation.md §2's confirmed values —
at minimum the ticket's own named worlds `wilderness_survival: 2`, `frontier_extended: 9`, plus 1-2
more, e.g. `urban_political: 4`, `frontier_living_world: 6`) mirrors `test_entity_count_band`'s
shape exactly.

### 6. Out-of-Scope confirmation

- **No `FactionState` change**: the new field only reads `entity.properties["faction_id"]`
  (already-set, pre-existing data) via a `len({set comprehension})` — `FactionState` construction
  (compiler.py:199-202) and the `factions: Dict[str, FactionState]` dict are untouched.
- **No faction-assignment-logic change**: `get_faction_enum`, the `ent_properties["faction_id"]`
  assignment itself, and the context-override branch are all read, not modified.
- **No FACTION pillar scoring change**: `src/simulation_quality/scorers/faction.py` (the FACTION
  pillar scorer) has no import of or dependency on `WorldCompiler`'s report dict — confirmed via
  `grep -rln "class FactionScorer\|FACTION.*Scorer" src/`, single hit, no cross-reference to
  `world_compile_report.json` or `distinct_populated_factions`. This is a purely additive,
  read-only reporting field.

### 7. `docs/simulation_quality/eval_matrix_results.md` "world-scale reporting section" — clarification

The ticket describes this as "the existing entity/region/resource-node scale reporting" section.
On inspection, the actual home of entity/region counts in this doc is narrower than that phrasing
implies:
- Only the **"Newly-Anchored Worlds" section** (lines 463-546) reports entity/region counts, in
  five per-world markdown headers, e.g.
  `### frontier_extended (56 entities, 10 regions — >50-entity band, widest region spread in corpus)`
  — covering only 5 of the 10 worlds (`frontier_extended`, `frontier_living_world`,
  `wilderness_survival`, `highland_traverse`, `swamp_border_world`).
- **No resource-node counts appear anywhere in this doc** — `grep -rn
  "resource_node_count|building_count|quest_count" docs/simulation_quality/` returns zero hits.
  The ticket's phrasing ("alongside the existing entity/region/resource-node scale reporting")
  overstates what's actually there; only entities+regions are reported, and only for 5/10 worlds.
- `generated_frontier_3_42` has **zero anchor entries** in `grade_anchors.json` and is not
  mentioned anywhere in `eval_matrix_results.md` — it is not part of the calibration corpus this
  doc tracks at all (confirmed: `grep -n "generated_frontier_3_42"
  docs/simulation_quality/eval_matrix_results.md` → no output).

This is a **documented discrepancy in the ticket's framing, not a blocker**: the underlying data
(all 10 worlds' scale counts) already exists in `world_compile_report.json`; this doc simply never
consolidated it into one place. Recommended approach for implementation (not decided here, flagging
for the plan phase): add a new subsection (e.g. "## Corpus World-Scale Summary") with one table
covering all 10 worlds' entity/region/resource-node/building/quest/distinct-populated-faction
counts — mirroring investigation.md §2's table shape exactly — rather than only patching the 5
existing "Newly-Anchored Worlds" headers (which would leave 5 worlds, including the two most
faction-dense ones' siblings `simq_routing_test`/`urban_political`/`dungeon_crawl`/`sandbox_world`,
undocumented). This satisfies AC3 ("includes the new metric alongside the existing... counts")
more completely than piecemeal header edits.

## Open Questions

None requiring a human decision. The ticket's own UQ-1 (compile-time definition vs. runtime-spawn
drift) is already resolved in the ticket body itself ("Scope this ticket to the compile-time
definition ... runtime-population drift is a separate ... signal and out of scope here") and is
consistent with the read-only, compile-time-only extraction this investigation confirms. The one
genuine ambiguity found (§7, doc-section scope) is a documentation-shape choice with a low-risk
default (add a consolidated table) rather than a decision that changes correctness or acceptance —
noted for the plan phase, not blocking.
