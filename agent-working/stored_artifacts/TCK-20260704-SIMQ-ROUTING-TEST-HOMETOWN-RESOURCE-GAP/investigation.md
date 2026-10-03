---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP
artifact_type: investigation
tags: [simulation-quality, world, adventure, bug]
---

# Investigation: TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP

## 1. Confirmed current state: simq_routing_test's resource nodes and tags

Compiled/resolved world at `data/worlds/simq_routing_test/resolved/world.resolved.yaml` has exactly
5 resource node instances:

| node id | kind | placed `region:` field |
|---|---|---|
| `res_0` | `wood_node` | `hometown` |
| `res_1` | `herb_patch` | `hometown` |
| `old_mine_resource_loop__iron_vein_0` | `iron_vein` | `old_mine` |
| `old_mine_resource_loop__crystal_outcrop_1` | `crystal_outcrop` | `old_mine` |
| `old_mine_resource_loop__silver_vein_2` | `silver_vein` | `old_mine` |

Independently re-derived (not trusted from the ticket's own text) the actual
`ResourceRegistry`-projected `source_region_tags` per kind, by running the real
`CatalogRepository("data/content").load_all()` → `CatalogToResourceRegistryAdapter.adapt()` path
live:

```
wood_node          -> ('near_forest',)
iron_vein          -> ('old_mine',)
stone_outcrop       -> ('frontier_village',)
herb_patch          -> ('near_forest', 'moon_cave')
healing_flower_patch -> ('near_forest',)
moon_resin_tree     -> ('moon_cave',)
crystal_outcrop     -> ()
silver_vein         -> ()
```

**Confirmed: no resource kind present in `simq_routing_test` has `hometown` in its
`source_region_tags`.** This matches the ticket's own claim exactly (verified independently, not
just trusted).

### 1a. Root mechanism (this is the part the ticket's own Scope framing gets subtly wrong)

`ResourceOpportunityProvider.get_opportunities()` (`src/world/providers/resources.py:69`) gates
purely on:

```python
if current_region in res_def.source_region_tags:
```

`res_def` comes from `ResourceRegistry.get(node.kind)` — a lookup keyed **only by resource kind**,
not by node instance or the node's actual placement. `ResourceNodeState`
(`src/core/state.py:905-916`) has **no region field at all** — only `id`, `kind`, `position`
(x/y tuple), charges, etc. So the world-content `region:` field on a `resources:` entry (e.g.
`res_0`'s `region: hometown` in `world.resolved.yaml`, or `frontier_village_core.yaml`'s
`resource_recipes[].region: "hometown"`) is used only for spatial placement/position computation
at compile time — it is **never consulted** by the opportunity-gating check. Gating is entirely a
function of a **global, catalog-wide, per-kind allowlist** computed once at content-registry
bootstrap by `CatalogToResourceRegistryAdapter.adapt()` (`src/core/registries.py:391-497`), from
`data/content/world/resources.yaml`.

That adapter's precedence for `source_region_tags` (`registries.py:425-446`):
1. `res.metadata["source_region_tags"]` if present (explicit override — the mechanism the
   STONE-GAP ticket already used for `stone_outcrop`).
2. Else `res.metadata["preferred_biomes"]` if present.
3. Else a hardcoded `legacy_id` keyword-match heuristic (`node_wood`→`near_forest`,
   `node_herb`→`(near_forest, moon_cave)`, `node_iron`→`old_mine`, `node_resin`→`moon_cave`,
   `node_flower`→`near_forest`; anything else falls through to `()`).

Critically, `ResourceDefinition.preferred_biomes` (`src/content/schema.py:241`) is a **top-level
declared Pydantic field**, not nested under `metadata`. `CatalogBaseDefinition.metadata`
(`schema.py:18`) is a separate free-form dict field, and the schema uses `extra="forbid"`
(`schema.py:10`), so a YAML author cannot casually promote a field into `metadata` by proximity —
it must be explicitly nested under a `metadata:` key in the YAML (exactly as `stone_outcrop` does).
Because `wood_node`/`herb_patch`/etc. in `data/content/world/resources.yaml` declare
`preferred_biomes` as a sibling key (not nested under `metadata:`), branch (2) above never fires
for them — `res.metadata` is `{}` (empty, from `default_factory=dict`) for every entry except
`stone_outcrop`. All of `wood_node`/`herb_patch`/`iron_vein`/`moon_resin_tree`/
`healing_flower_patch`'s tags therefore come entirely from branch (3), the hardcoded legacy
heuristic — which has no knowledge of any world's actual region-naming choices (e.g. "hometown").
`silver_vein`/`crystal_outcrop`/`venom_nest`/`spirit_wisp`/`ember_core_cluster`/
`frost_shard_cluster` have no `legacy_id` heuristic branch at all, so they resolve to `()`
(confirmed live above) — this is also correctly reflected in the ticket's original claim.

**Conclusion:** the world's own module (`frontier_village_core.yaml`, see §2) already places
`wood_node`/`herb_patch` nodes physically in "hometown" — the world-content authoring *did* what a
naive read of the Scope item (a) implies is missing. The actual defect is that the **global,
per-resource-kind catalog tag list never included "hometown"** as a valid gating region for any
kind that any world places there. This is a catalog/content-registry gap, not a
composition/module-authoring gap — editing `simq_routing_test`'s own module_refs or world.yaml
cannot fix this on its own, because the gating check never reads a node's placement region in the
first place.

## 2. Where the resource content is actually declared

`simq_routing_test`'s `world.yaml` is `module_refs`-based:
```yaml
module_refs:
  - module_id: "frontier_village_core"   # order 0 — places res_0 (wood_node) + res_1 (herb_patch) in hometown
  - module_id: "old_mine_resource_loop"  # order 1 — places iron_vein/crystal_outcrop/silver_vein in old_mine
  - module_id: "goblin_camp_conflict"    # order 2
  - module_id: "hero_adventurers"        # order 3 — places 3 hero-role entities, all spawn_region: hometown
```
(Correction to the task's framing: this world is not "no shared world_modules" — it fully composes
from 4 shared `data/content/world_modules/*.yaml` modules; "additional" in the world.yaml's header
comment refers to the world composition itself being additively defined, not to its modules being
inline.)

`data/content/world_modules/frontier_village_core.yaml` (lines 24-30):
```yaml
resource_recipes:
  - resource_type: "wood_node"
    count: 8
    region: "hometown"
  - resource_type: "herb_patch"
    count: 5
    region: "hometown"
```
`data/content/world_modules/hero_adventurers.yaml`: 3 `population_recipes` entries, all
`role: "hero"`, all hardcoded `spawn_region: "hometown"`.

Both modules are **shared** — used by exactly two worlds in the corpus: `simq_routing_test` and
`urban_political` (confirmed via `grep -rl hero_adventurers data/worlds/*/world.yaml`). Any fix
made at the module level would need to be duplicated/consistent across both; but as established in
§1a, a module-level `region:` edit would not fix anything anyway, since that field isn't consulted
by the gating check. The only lever that actually changes gating behavior is
`ResourceDef.source_region_tags`, which is sourced exclusively from
`data/content/world/resources.yaml` (global, world-agnostic).

## 3. Fix recommendation

**Recommended: (a-corrected) — add `"hometown"` to the `source_region_tags` of the resource
kind(s) already physically placed there, via an explicit `metadata.source_region_tags` override in
the global catalog file `data/content/world/resources.yaml`** — the same mechanism already used for
`stone_outcrop` (added by the STONE-GAP ticket). This is a content-catalog change, not a
composition/module change, and not a code change.

Concretely, for `wood_node` and `herb_patch` (both already placed in `hometown` by
`frontier_village_core.yaml`, in both worlds that use it):

```yaml
# STATE: EXISTING-LOGIC
- id: "wood_node"
  ...
  metadata:
    source_region_tags: ["near_forest", "hometown"]

# STATE: LEGACY-EXPORT
- id: "herb_patch"
  ...
  metadata:
    source_region_tags: ["near_forest", "moon_cave", "hometown"]
```

Rationale for **both** kinds (not just the one needed to satisfy the AC's "at least one"):
- Both are already co-located in `hometown` by the same module in both worlds that use it — this
  matches the evident original authoring intent from `TCK-20260627-P0B-URBAN-RESOURCE-NODES`
  (working_log.csv: "Added resource_recipes to frontier_village_core (wood_node+herb_patch for
  hometown)"). That ticket's own stated intent was never actually realized for
  opportunity-matching purposes, because it only added node placements, not the catalog tag that
  gates opportunity emission — this fix closes that gap for both node kinds at once, matching what
  P0-B already assumed was true.
- Doing only one leaves a single point of failure (e.g. node depletion / charge exhaustion) that
  could reopen the exact same stasis risk later; doing both costs nothing extra and is strictly
  additive.
- The AC only requires "at least one" — either kind alone is sufficient to satisfy it if Plan
  decides to minimize the diff; recommending both is a judgment call, not a hard requirement.

**Explicitly must NOT do:** replace the tags tuple outright (e.g. `["hometown"]` only) — this must
be additive (`["near_forest", "hometown"]` for `wood_node`, `["near_forest", "moon_cave",
"hometown"]` for `herb_patch`) or it silently regresses every other world/region currently relying
on the `near_forest`/`moon_cave` tags for these same kinds (`frontier_extended`,
`frontier_living_world`, `generated_frontier_3_42`, `sandbox_world`, `swamp_border_world`,
`wilderness_survival` all place `wood_node`/`herb_patch` nodes in `near_forest`, several also in
`moon_cave` via other kinds — see §4).

**Rejected alternatives:**
- **(b) Author a brand-new resource node/content entry tagged for hometown** — unnecessary. Nodes
  already physically exist in `hometown` (`res_0`, `res_1`); the gap is purely in the catalog-level
  gating tag, not in node placement. A new node would still need the same
  `metadata.source_region_tags` treatment and would just duplicate coverage `wood_node`/`herb_patch`
  already (should) provide. Rejected as unnecessary complexity.
- **(c) Change `ResourceNodeState`/`ResourceOpportunityProvider` to gate on the node's actual
  placement region instead of a kind-level catalog allowlist** — architecturally the more "correct"
  long-term fix (it would eliminate this entire bug *class*, not just this instance — see §4's
  audit, which shows this same tag/placement mismatch recurring for `orc_stronghold`,
  `swamp_border_territory`, `river_ford`, etc., independent of "hometown"). But this requires adding
  a region field to `ResourceNodeState` (a durable-state schema change per this repo's Durable
  State Rule) and touching the compiler, the provider, and every test that constructs
  `ResourceNodeState`/mocks `ResourceRegistry` — a much larger blast radius than this ticket's
  Scope authorizes ("Add at least one resource node... whose `source_region_tags` includes
  `hometown`" — explicitly a content-authoring fix, not an architecture change). Recommend flagging
  as a **separate follow-up ticket** (see Open Questions) rather than doing it here.

## 4. Cross-world audit (required Scope item)

Audited **every** world under `data/worlds/*/resolved/world.resolved.yaml` (10 worlds) for: does
any entity spawn in a region not covered by any present resource kind's `source_region_tags`?
Computed with the real, live `ResourceRegistry` projection (not hand-derived):

| world | all-role uncovered spawn regions | **hero-role** uncovered spawn regions |
|---|---|---|
| dungeon_crawl | bandit_road, goblin_camp, haunted_battlefield | (no heroes) |
| frontier_extended | bandit_road, goblin_camp, haunted_battlefield, hometown, orc_stronghold, sacred_grove, wolf_den | (no heroes) |
| frontier_living_world | bandit_road, goblin_camp, haunted_battlefield, hometown, wolf_den | (no heroes) |
| generated_frontier_3_42 | bandit_road, goblin_camp, hometown, orc_stronghold | (no heroes) |
| highland_traverse | hometown, wolf_den | (no heroes) |
| sandbox_world | hometown, wolf_den | (no heroes) |
| **simq_routing_test** | goblin_camp, **hometown** | **hometown** |
| swamp_border_world | hometown, swamp_border_territory, wolf_den | (no heroes) |
| **urban_political** | bandit_road, **hometown**, trading_hometown | **hometown** |
| wilderness_survival | haunted_battlefield, wolf_den | (no heroes) |

Two findings, at two different severities:

**(i) Narrow finding (matches this ticket's actual failure mode — hero stasis risk):**
`AdventureDecisionPhase`/`AdventureRouteGenerator` (the code path that can get permanently stuck on
`defer_with_reason`) only runs for `EntityRole.HERO` entities (`src/domains/adventure/phase.py:75`:
`e.identity.role == EntityRole.HERO`). Filtering the audit to **only regions where hero-role
entities spawn**: exactly **two** worlds have hero-role entities at all —
`simq_routing_test` and `urban_political` — and **both** spawn their 3 heroes in `hometown`, which
is uncovered by any present resource kind's tags in both worlds. This is because both worlds are
the only two users of the shared `hero_adventurers` module
(confirmed: `grep -rl hero_adventurers data/worlds/*/world.yaml` → exactly these two files), and
both also use `frontier_village_core` (which places `wood_node`/`herb_patch` in `hometown` but
whose catalog tags don't cover it). **`urban_political` has the exact same latent gap as
`simq_routing_test`.**

However, `urban_political`'s shipped SimQ calibration profile does not currently force
`ENABLE_ADVENTURE_ROUTING=ON` (confirmed via `docs/simulation_quality/eval_matrix_results.md`'s
"AGENCY — Cross-World Design Note": `simq_routing_test` is documented as "the one calibration world
that forces `ENABLE_ADVENTURE_ROUTING=ON`"; `urban_political` grades AGENCY=C by default because
`AdventureDecisionPhase` never runs there today). So this gap is **currently dormant** for
`urban_political` — it does not manifest as an observed calibration failure today, but would
reproduce `simq_routing_test`'s identical failure mode the moment `urban_political`'s calibration
profile (or any other world reusing `hero_adventurers`) enabled adventure routing and an
unlucky-`sociability` hero landed in `hometown`.

**(ii) Broad finding (out of scope for this ticket, noted for awareness / follow-up):** Looking at
**all** entity roles (not just heroes), the tag/placement mismatch is pervasive — `wolf_den`,
`bandit_road`, `goblin_camp`, `haunted_battlefield`, `orc_stronghold`, `sacred_grove`,
`swamp_border_territory`, `trading_hometown`, `river_ford`, `mountain_pass_zone` are uncovered by
any present resource kind's `source_region_tags` in the worlds that use them. This does not
currently cause the "permanently stuck" failure mode described in this ticket, because
non-hero-role entities do not route through `AdventureDecisionPhase` at all — but it does mean
`ResourceOpportunityProvider` silently returns zero `gather_resource` opportunities for entities of
any role standing in most of these regions, which may matter for other systems that consume
opportunities (out of scope to trace further here). This is the same root mechanism as §1a (kind-level
catalog tags vs. per-node placement region) recurring at a much larger scale than "hometown" alone.
Recommend a **separate follow-up ticket** to decide whether option (c) from §3 (region-aware node
gating) is worth the architecture change, given how widespread this pattern is.

## 5. STONE-GAP regression check (Scope item 4)

The recommended fix reuses `wood_node` and `herb_patch` — both are pre-existing,
already-`ResourceRegistry`-registered resource kinds (confirmed live: both keys present in
`ResourceRegistry.all()` under both their `res_id` and `legacy_id` forms, e.g.
`resources["wood_node"]` and `resources["node_wood"]` both resolve to the same `ResourceDef`
instance). No new `kind` string is introduced anywhere (world content, module, or catalog); the fix
only adds an additional string to an existing tuple field on two already-registered `ResourceDef`
instances. This cannot reintroduce the STONE-GAP crash class (`ResourceRegistry.get()` raising
`KeyError` on an unregistered kind) — it's a pure metadata addition on already-known kinds.

## 6. Test coverage inventory (Scope item 5)

Existing tests exercising `source_region_tags` / resource-opportunity gating / this world's
content, checked individually against the real catalog file to determine if the fix would break
them:

- `tests/unit/strategic/test_opportunities.py` (`test_resource_opportunities_basic`,
  `test_resource_opportunities_with_blocker`) — constructs synthetic `ResourceNodeState`s and puts
  the entity in `near_forest`/`old_mine`, not `hometown`. **Unaffected** — adding `hometown` to
  `wood_node`/`herb_patch`'s tags doesn't touch these regions/assertions.
- `tests/unit/core/test_registry_bridge.py` (~line 355-368) — reads the **real**
  `data/content` catalog, asserts `"near_forest" in res_wood.source_region_tags` and `"old_mine" in
  res_iron.source_region_tags` (subset-style `in` checks, not equality). **Unaffected** — adding
  `hometown` alongside `near_forest` still satisfies `"near_forest" in (...)`.
- `tests/unit/core/test_registry_parity.py` (`test_production_catalog_parity`, ~line 113-117) —
  reads the real catalog, asserts `leg_tags_set.issubset(cat_tags_set)` (legacy hardcoded tags must
  be a subset of catalog-derived tags). Adding `hometown` only **grows** the catalog side further
  past a superset of legacy — subset relation still holds. **Unaffected.**
  `test_catalog_registry_projection_parity` (~line 260-308) only checks presence, not tag content —
  **unaffected**.
- `tests/unit/content/test_adapter_heuristic_reporting.py` — constructs its own synthetic
  `_make_resource(...)` fixtures with hand-set `metadata` dicts, does not read the real
  `data/content/world/resources.yaml`. **Unaffected.**
- `tests/integration/content/test_registry_projection_parity.py` (~line 94-125) — also builds a
  synthetic repo/YAML fixture inline, not the real catalog file. **Unaffected.**
- `tests/unit/world/providers/test_resource_opportunity_provider.py` — contains only a docstring
  reference to `stone_outcrop`'s `source_region_tags=("frontier_village",)` as prior-ticket context;
  no assertions on `wood_node`/`herb_patch`. Recommend a quick read/re-run as a smoke check but no
  changes expected.
- `tests/integration/worldassembly/test_e2e_smoke.py` — `test_smoke_urban_political_compiles_to_authoritative_state`
  asserts `resource_node_count >= 3` and `len(state.resource_nodes) >= 3` for `urban_political`.
  This fix does not change node counts, only catalog tags — **unaffected**, but should be re-run
  since it directly touches the same world/module content family.
- `tests/simulation_quality/test_grade_regression.py` +
  `tests/simulation_quality/fixtures/grade_anchors.json` — per this ticket's own AC5, seed456's
  `simq_routing_test` AGENCY anchor (currently `D`, see
  `docs/simulation_quality/eval_matrix_results.md` "Status as of 2026-07-04
  (TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE): DOCUMENTED EXCEPTION") **will very likely change**
  once this fix lands — entity 23 gaining a legal `gather_resource` route in `hometown` should
  interrupt (or substantially shorten) its 491-event `defer_with_reason` streak entirely, which
  the eval_matrix doc itself anticipates ("even if that lands... a future re-anchor would be a new
  anchor update, not a retroactive edit here"). **Recompute and update this anchor is required by
  the ticket's own AC**, not optional.
- **No test currently asserts that `hometown` yields zero `gather_resource` opportunities** — i.e.
  no test encodes the *absence* of hometown coverage as intentional/expected behavior. This is
  further confirmation the fix is additive and not fighting an existing, deliberately-asserted
  contract.

## 7. Related doc/ledger context (not modified by this investigation; noted for Plan/Implementation)

- `docs/parity_ledger/town_resource.yaml` entry `TOWN-183` documents "urban_political ... >= 3
  resource nodes... wood_node (8 charges, hometown) and herb_patch (5 charges, hometown)" as
  `verified` — but that entry is scoped to node *count*, not opportunity-gating coverage; it
  remains accurate and does not need editing for this fix. Plan/Implementation should consider
  whether a **new** parity ledger entry (in `town_resource.yaml`, since this is
  `ResourceRegistry`/`source_region_tags` territory) is warranted to record the
  gating-vs-placement mismatch and its fix — and whether
  `docs/guidelines/v2_intentional_divergences.md` needs a "Bug Fix" class entry, per this repo's
  Authoritative Mechanics Rule.
- `docs/simulation_quality/eval_matrix_results.md` (AC6 section, "DOCUMENTED EXCEPTION" note) — the
  exact text anticipating this ticket's fix and its expected effect on the seed456 AGENCY anchor;
  Implementation should update this section once the anchor changes.

## 8. Files touched by this investigation (read-only; no source/content changes made)

- `tickets/inprogress/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP.md` (read)
- `stored_artifacts/TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE/investigation.md` (read)
- `data/worlds/simq_routing_test/world.yaml`,
  `data/worlds/simq_routing_test/resolved/world.resolved.yaml` (read)
- `data/worlds/*/resolved/world.resolved.yaml` (all 10 worlds, read/audited programmatically)
- `src/world/providers/resources.py`, `src/core/state.py` (`ResourceNodeState`),
  `src/core/registries.py` (`ResourceDef`, `CatalogToResourceRegistryAdapter`),
  `src/content/schema.py` (`ResourceDefinition`, `CatalogBaseDefinition`) (read)
- `src/domains/adventure/generator.py`, `src/domains/adventure/phase.py` (read, gate confirmation)
- `data/content/world/resources.yaml` (read — target file for the recommended fix)
- `data/content/world_modules/frontier_village_core.yaml`,
  `data/content/world_modules/hero_adventurers.yaml` (read)
- `tests/unit/strategic/test_opportunities.py`, `tests/unit/core/test_registry_bridge.py`,
  `tests/unit/core/test_registry_parity.py`, `tests/unit/content/test_adapter_heuristic_reporting.py`,
  `tests/integration/content/test_registry_projection_parity.py`,
  `tests/unit/world/providers/test_resource_opportunity_provider.py` (read)
- `docs/parity_ledger/town_resource.yaml`, `docs/simulation_quality/eval_matrix_results.md` (read)
- Live-ran `CatalogRepository("data/content").load_all()` +
  `CatalogToResourceRegistryAdapter.adapt()` directly (read-only, no persisted state changed) to
  ground-truth-verify `source_region_tags` per kind instead of hand-deriving from the YAML.

## Open Questions (for Plan phase)

- **OQ-1 (does not block this ticket):** Should `urban_political`'s identical latent gap (hero
  role, `hometown`, currently dormant because `ENABLE_ADVENTURE_ROUTING` is off for its shipped
  calibration profile) be considered "fixed" by this same catalog-level change (it will be, as a
  side effect, since the fix is world-agnostic), or does it warrant its own explicit
  acceptance-criterion/test in this ticket? Recommend treating it as a bonus side-effect fix
  (worth noting in Completion Summary) rather than expanding this ticket's Scope, since
  `urban_political`'s AGENCY grade is not currently gated on this behavior.
- **OQ-2 (explicitly out of scope, flag as follow-up):** The broader §4(ii) finding — that
  most non-`old_mine`/`near_forest`/`moon_cave` regions across the entire world corpus are
  uncovered by any resource kind's `source_region_tags`, for **any** entity role — is a systemic
  content/architecture mismatch (kind-level catalog tags vs. per-node placement region,  §3 option
  (c)). Recommend filing a separate follow-up ticket rather than expanding this one; it does not
  currently cause an observed calibration failure for any role other than hero, and only for the
  two worlds using `hero_adventurers`.
- No open question blocks stating the current state, the root mechanism, or the recommended fix
  direction — all are supported by direct, live-verified evidence above, not guesses.
