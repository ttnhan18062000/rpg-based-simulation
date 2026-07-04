---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP
artifact_type: investigation
tags: [simulation_quality, world, ecology, resource-registry, bug]
---

# Investigation — TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP

## Context Scan Performed

1. `mcp__knowledge-search__search_docs` (query: "ResourceRegistry KeyError STONE resource kind
   ecology dynamic resource node generation") — surfaced `docs/world/ecology_and_calamity_contract.md`
   (ecology.py contract), `docs/mechanics/03_economic_laws.md` §3 Resource Harvesting, and the E21
   resource-ecology ticket chain (`TCK-20260619-E21A/B/C`, `TCK-20260628-E21C-COMPILER-REGEN`).
   None of these docs describe the dynamic-seeding `kind` selection logic in ecology.py's
   `process_ecology` — the ecology contract covers regen cadence and node replenishment targets,
   not the specific string literals used for `kind`.
2. `graphify query "ResourceRegistry resource kind ecology dynamic resource node generation"` —
   confirmed `ResourceRegistry` lives in `src/core/registries.py`, node/state models in
   `src/core/state.py`, and surfaced `CatalogRepository` / `CatalogToItemRegistryAdapter` as the
   catalog-adapter pattern used for all registries.

Both tools' results converged with reading `src/world/ecology.py` and `src/core/registries.py`
directly — no conflicting or duplicate work found.

## Root Cause

### Emission site

`src/world/ecology.py:124-125`, inside `ResourceEcologyService.process_ecology`:

```python
124:                    kind = "WOOD" if region.kind == "FOREST" else "STONE"
125:                    if region.kind == "MOUNTAIN": kind = "IRON"
```

This is the dynamic resource-node seeding path (runs every `ECOLOGY_INTERVAL=200` ticks, per
region, 50% chance if the region is under its node-density target — see lines 108-144). The
`kind` string chosen here is written directly into a new `ResourceNodeState` (line 134-143) with
no validation against `ResourceRegistry`.

**Git history** (`git blame -L120,130 src/world/ecology.py`): this exact three-branch
`WOOD`/`STONE`/`IRON` logic was introduced in commit `562116889` (2026-05-18) and is untouched
since (confirmed present unchanged back through `9fcd8c8`, 2026-04-28 — the earliest ecology.py
commit found). This predates the catalog-driven `ResourceRegistry` becoming the authoritative
registration source (see the `NOTE` comment at `src/core/registries.py:195-198`: catalog-backed
registries sourced from `data/content/` are authoritative for "all active development"; the
hardcoded Python seed maps are legacy fallback only). The ecology.py literals were never migrated
to reference real catalog ids when that transition happened — this is staleness/oversight, not a
deliberate design decision.

### Crash site (the actual `KeyError`)

`src/world/providers/resources.py:60`, inside `ResourceOpportunityProvider.get_opportunities`:

```python
59:            # (ResourceRegistry definitions mapped via kind)
60:            res_def = ResourceRegistry.get(node.kind)
61:            if not res_def:
62:                continue
```

This iterates **every** node in `state.resource_nodes` (line 53) and calls `ResourceRegistry.get()`
unguarded. `ResourceRegistry.get()` (`src/core/registries.py:92-96`) raises `KeyError` on a miss —
it does not return `None` — so the `if not res_def: continue` fallback on line 61 is dead code;
there is no scenario where it executes. This is the one unguarded call site in the codebase:

- `src/town/guild.py:67-69` calls `ResourceRegistry.contains(node.kind)` before `.get()`, with an
  explicit comment (lines 62-64) that this guard exists precisely because ecology-seeded /
  test-fixture nodes can carry an unregistered `kind`.
- `src/engine/intent/action_intent.py:73-74` similarly guards with `contains()` before `.get()`.
- `src/world/providers/resources.py:60` is the only call site missing this guard.

### Registration source of truth

`ResourceRegistry` is populated by `seed_phase1_content()` (`src/core/registries.py:562-635`) via
`CatalogToResourceRegistryAdapter(catalog_repo).adapt()` (line 604), which reads
`data/content/world/resources.yaml` — the authoritative catalog. That file defines 11 resource
records (`wood_node`, `iron_vein`, `herb_patch`, `healing_flower_patch`, `moon_resin_tree`,
`crystal_outcrop`, `silver_vein`, `venom_nest`, `spirit_wisp`, `ember_core_cluster`,
`frost_shard_cluster`). Each is registered under **both** its catalog `id` and its `legacy_id`
(e.g. `wood_node` / `node_wood`, `iron_vein` / `node_iron` — see
`src/core/registries.py:487-496`).

**Confirmed: no "stone" resource of any kind exists anywhere in `data/content/`** (checked
`data/content/world/resources.yaml` in full, plus a repo-wide case-insensitive whole-word grep for
`stone` across `src/` and `data/content/` — the only other hit is `src/core/items.py:81-82`, a
generic crafting *material* `ItemDefinition(id="stone", ...)`, unrelated to resource *nodes*).

**All three of ecology.py's literals are wrong against the catalog, not just `STONE`:**
| ecology.py literal | Region trigger | Matching catalog id? |
|---|---|---|
| `"WOOD"` | `region.kind == "FOREST"` | No — catalog uses `node_wood` / `wood_node` (lowercase) |
| `"IRON"` | `region.kind == "MOUNTAIN"` | No — catalog uses `node_iron` / `iron_vein` (lowercase) |
| `"STONE"` | else (any other region kind — the fallback/default branch) | No — no stone resource exists in the catalog at all |

`STONE` is the one that surfaced in practice because it is the **fallback branch** — it fires for
every region whose `kind` is neither `FOREST` nor `MOUNTAIN` (e.g. `TOWN` and any other region
kind), which is the most common case in typical world compositions. `WOOD` and `IRON` are equally
broken (wrong case, don't match any registered id) but happen not to have surfaced yet in a crash
because nothing has hit that exact combination of region kind + read path yet — they are latent
instances of the same defect and must be fixed together, not left as a second undiscovered bug.

## Reproduction

Ran the exact command from `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/plan.md`
Step 4a:

```
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 42 --name simq_routing_test
```

Result: crashes deterministically, confirmed stack trace:

```
File ".../src/engine/kernel.py", line 386, in _tick_once_inner
    self._phase_resolution()
File ".../src/engine/kernel.py", line 637, in _phase_resolution
    refined_update = AuthoritativeApplyPipeline.refine(...)
File ".../src/engine/pipeline.py", line 228, in refine
    update = run_phase("adventure_decision", update, ..., "ENABLE_ADVENTURE_ROUTING")
File ".../src/engine/pipeline.py", line 117, in run_phase
    phase_upd = phase_fn(upd)
File ".../src/domains/adventure/phase.py", line 100, in apply
    opportunities = ResourceOpportunityProvider.get_opportunities(hero, state)
File ".../src/world/providers/resources.py", line 60, in get_opportunities
    res_def = ResourceRegistry.get(node.kind)
File ".../src/core/registries.py", line 95, in get
    raise KeyError(f"Resource not found in ResourceRegistry: {resource_id}")
KeyError: 'Resource not found in ResourceRegistry: STONE'
```

Exact match to the ticket's reported error. `data/calibration/` is gitignored — no cleanup needed
for these repro runs; `data/runs/` and `reports/release_proof/` were cleared per workflow rule.

## UQ-1 Resolved: Routing-specific vs. general

**The underlying defect is general; the crash trigger is routing-specific.** Evidence:

1. `ResourceOpportunityProvider.get_opportunities()` (the only unguarded `ResourceRegistry.get()`
   call site) is invoked from exactly two places:
   - `src/domains/adventure/phase.py:100`, inside `AdventureDecisionPhase.apply()`, which is only
     ever run via `src/engine/pipeline.py:228-236`'s `run_phase(..., "ENABLE_ADVENTURE_ROUTING")` —
     `run_phase` (pipeline.py:102-110) skips the phase entirely when the flag's mode is `OFF`.
     `ENABLE_ADVENTURE_ROUTING` defaults `OFF` (`src/domains/optimization/feature_flags.py:16`).
   - `src/testing/scenario_runner.py:91-93`, a test harness that always forces
     `ENABLE_ADVENTURE_ROUTING: 1.0` into `pressure_signals` (line 103) — i.e. it also only
     exercises this path in routing-simulated mode.
2. Confirmed empirically: ran `python3 tools/calibrate_simq.py --ticks 500 --seed 42 --name
   dungeon_crawl` (routing flag **not** set) — 500 ticks (well past the 200-tick ecology interval,
   so `process_ecology`'s seeding path definitely executes and definitely writes `STONE`/`WOOD`
   nodes into state) — and it **completed successfully** with a full quality report. The bad `kind`
   values are silently written into `resource_nodes` in every world, but nothing crashes because no
   other consumer of `resource_nodes` in the default (non-routing) pipeline calls
   `ResourceRegistry.get()` without a `contains()` guard.

**Conclusion:** every calibration world is silently accumulating resource nodes with unregistered
`kind` values once `process_ecology` runs (any world ≥ 200 ticks). This is dormant/latent in all of
them today. It only becomes a hard crash in `simq_routing_test` because that is the one calibration
world that forces `ENABLE_ADVENTURE_ROUTING=ON` (per `docs/simulation_quality/eval_matrix_results.md`
lines 194, 310-311) and thus is the only one that reaches the unguarded read path. This means the
SimQ Corpus Tiers epic (`TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`) is at risk **only** for any
routing-enabled world it authors — non-routing worlds will keep silently accumulating bad nodes but
won't crash unless/until some other code path adds an unguarded `ResourceRegistry.get(node.kind)`
call (or `guild.py`'s/`action_intent.py`'s existing guards are removed). The fix should close the
root cause (bad emission), not just patch the one crash site, precisely because of this latent
blast radius.

## Fix Recommendation: (b) Fix the generator, not the registry

**Do not register `STONE` (or `WOOD`/`IRON` as-is) in `ResourceRegistry`.** Reasoning:

1. **No such resource exists in the design.** `data/content/world/resources.yaml` is the
   authoritative catalog (confirmed via `seed_phase1_content()` → `CatalogToResourceRegistryAdapter`
   → `data/content/world/resources.yaml`) and has zero stone-type entries. There is no evidence
   `STONE` was ever an intended, simply-forgotten resource — it was never designed, never appears
   in any recipe, item-usage, or quest reference anywhere in `data/content/` or `src/` (repo-wide
   grep confirmed). Registering it now would be inventing new content scope, which is explicitly
   **out of scope** per this ticket ("Any other content/world changes beyond what's needed to fix
   this specific crash").
2. **Architecture explicitly forbids it.** `src/core/registries.py:195-198`: *"No new hardcoded
   definitions should be added to python structures directly... catalog-backed registries... are
   authoritative."* Hardcoding a `STONE` entry into `ResourceRegistry`'s Python fallback map (or
   registering a still-needs-inventing catalog record) would violate this rule and the project's
   Durable State Rule (durable content must go through the catalog, not ad hoc literals in engine
   code).
3. **`WOOD` and `IRON` are equally unregistered** (wrong case vs. catalog ids `node_wood`/`wood_node`,
   `node_iron`/`iron_vein`) — registering only `STONE` would leave two more latent instances of the
   identical defect. The generator must be fixed to emit ids that already exist in the catalog for
   all three branches, not just patched for the one that happened to crash first.

**Correct fix:** `ResourceEcologyService.process_ecology` (`src/world/ecology.py:124-125`) must
select `kind` from real, `ResourceRegistry`-registered ids — e.g. `"node_wood"` (or `"wood_node"`)
for `FOREST` regions and `"node_iron"` (or `"iron_vein"`) for `MOUNTAIN` regions, matching what
`src/worldbuilding/compiler.py:219-229` and `src/worldassembly/resolver.py` already do for
authoritative/compiled node creation (both use catalog-sourced `resource_type`/`res_spec.resource_type`
values, never ad hoc uppercase literals). Line 138's `yields_item` derivation
(`kind.lower() + "_ore" if kind != "WOOD" else "wood_log"`) is coupled to the same literals and must
be re-derived from the chosen `ResourceDef.yield_item` (via `ResourceRegistry.get(kind).yield_item`)
rather than hand-computed, so it can't drift out of sync again the same way.

## Open Questions Requiring a Human Decision

**UQ-2 (new, surfaced during investigation): what should the `else` (fallback) branch resolve to?**

The `else` branch (currently `"STONE"`) fires for every region whose `kind` is neither `FOREST` nor
`MOUNTAIN` — i.e. it is the generic/default case, not a narrow one. There is no generic
"stone"/"rock"/catch-all resource in the catalog, and no single existing registered resource has a
`source_region_tags` that means "any region" — the closest, `herb_patch`/`node_herb`, is tagged
`("near_forest", "sunken_swamp")`, still narrower than "everything else." Concretely, the
implementer must choose one of:
  (a) Reuse an existing registered kind (e.g. `node_wood`) as the generic fallback, accepting that
      its `source_region_tags` won't semantically match every region it's placed in (mirrors what
      `ResourceOpportunityProvider` already tolerates — it just filters nodes whose region isn't
      in `source_region_tags`, it doesn't require an exact match to function).
  (b) Restrict dynamic seeding to only `FOREST`/`MOUNTAIN` regions (drop the `else` branch — no
      node seeded for other region kinds). This changes the resource-node density/economy in every
      other region kind and would need a documented Intentional Divergence entry
      (`docs/guidelines/v2_intentional_divergences.md`) plus a check of whether any calibration
      world's ECONOMY-pillar anchors depend on today's (buggy) behavior of "gets *a* node either way."
  (c) Author a new, generic catalog resource (e.g. a `stone_outcrop`/`stone_node` record) to give
      the fallback branch a real, purpose-built home. This is the most correct long-term shape but
      is new content authoring, arguably beyond "whichever fix closes this crash" scope — flagging
      rather than assuming.

This ticket's acceptance criteria do not prescribe which; the choice affects region-level resource
economy (a durable-state/architecture question, not just a bug fix), so per the Uncertainty Rule
("do not collapse investigation into exact coordinates too early") this is left for implementation-time
decision with a documented rationale, not decided here.

**No other open questions.** UQ-1 (routing-specific vs. general) is resolved above with evidence —
no further human input needed on that point.
