---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT
artifact_type: plan
tags: [simulation-quality, world, resource-registry, corpus]
---

# Implementation Plan — TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT

## Summary

The investigation confirmed 8 distinct uncovered regions corpus-wide. 5 of them
(`orc_stronghold`, `sacred_grove`, `swamp_border_territory`, `haunted_battlefield`,
`trading_hometown`) have resource nodes physically placed by their composing world module but are
missing the corresponding catalog kind's `source_region_tags` entry — the exact same
tag-omission-bug shape as the `hometown` fix (`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`,
TOWN-188) and the `mountain_pass_zone` fix (`TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP`). This
plan applies the same additive `metadata.source_region_tags` fix, one catalog-entry edit per resource
kind, to close all 5. The remaining 3 regions (`bandit_road`, `goblin_camp`, `wolf_den`) have zero
resource nodes placed anywhere in the corpus; the investigation could not resolve from evidence alone
whether this is intentional hazard-zone design or an authoring oversight (OQ-1), so this question was
escalated to a human reviewer, who decided: **document as an intentional gap** (matches the pattern of
other danger regions in the corpus; no new content authored). Step 17 implements that documentation
decision. Every catalog
edit is followed by its own regression test (rewrite the existing "expects zero" test for
`orc_stronghold`, add new positive-coverage tests for the other 4), plus a corpus-wide audit test that
turns "zero hero-role gaps today" into a durable regression guard, a parity ledger entry, an
`intentional_divergences.md` entry, and an `eval_matrix_results.md` update recording the
region-aware-`ResourceNodeState` architecture recommendation (DEFER) and the dormant `GuildAction`
risk note. No engine/provider/compiler code is touched anywhere in this plan — every fix is a
catalog-content edit, per the investigation's explicit anti-drift hazard.

## Steps

### Step 1 — `wood_node` tag-gap fix (`orc_stronghold`, `swamp_border_territory`)
**Files:** `data/content/world/resources.yaml` (lines 2-10, the `wood_node` entry)
**Change:** Extend the existing `metadata.source_region_tags` list additively. Current:
```yaml
  metadata:
    source_region_tags: ["near_forest", "hometown"]
```
New:
```yaml
  metadata:
    source_region_tags: ["near_forest", "hometown", "orc_stronghold", "swamp_border_territory"]
```
Rationale: `orc_clan_territory.yaml` places `wood_node: 6` in `orc_stronghold`;
`sunken_swamp_border.yaml` places `wood_node: 4` in `swamp_border_territory`. Neither region was in
the catalog allowlist despite the node being physically present.
**Do NOT touch:** `preferred_biomes` (stays `["frontier_village", "near_forest"]`, unconsulted for
gating per the adapter's branch-1-wins precedence — do not "fix" it, it is dead for this purpose by
design, matching every prior precedent). Do not remove `"near_forest"` or `"hometown"` from the tuple.
**Verify:** `tests/unit/strategic/test_opportunities.py::test_resource_opportunities_orc_stronghold_tag_gap`
(after Step 6 rewrite) and the new swamp_border_territory test (Step 8).

### Step 2 — `iron_vein` tag-gap fix (`orc_stronghold`, `trading_hometown`)
**Files:** `data/content/world/resources.yaml` (lines 13-21, the `iron_vein` entry)
**Change:**
```yaml
  metadata:
    source_region_tags: ["old_mine", "mountain_pass_zone", "orc_stronghold", "trading_hometown"]
```
Rationale: `orc_clan_territory.yaml` places `iron_vein: 4` in `orc_stronghold`.
`trading_company_hub.yaml`'s `resource_recipes: [{resource_type: iron_vein, count: 6, region:
"hometown"}]` compiles to region id `trading_hometown` for any world composing it under the `trading`
namespace (confirmed via `src/worldassembly/resolver.py:335`'s namespace-prefixing — this is a
**distinct** region id from plain `hometown`, already closed by the parent ticket family; do not
conflate the two).
**Do NOT touch:** `preferred_biomes` (stays `["old_mine"]`). Do not conflate `trading_hometown` with
plain `hometown` — this is a different region id and a different, still-open finding.
**Verify:** `test_resource_opportunities_orc_stronghold_tag_gap` (Step 6 rewrite) and the new
trading_hometown test (Step 10).

### Step 3 — `herb_patch` tag-gap fix (`swamp_border_territory`)
**Files:** `data/content/world/resources.yaml` (lines 35-43, the `herb_patch` entry)
**Change:**
```yaml
  metadata:
    source_region_tags: ["near_forest", "moon_cave", "hometown", "swamp_border_territory"]
```
Rationale: `sunken_swamp_border.yaml` places `herb_patch: 3` in `swamp_border_territory`; `herb_patch`'s
own `preferred_biomes` already names `"sunken_swamp"` (the module's *biome*, not its region id) as
supporting evidence of authoring intent.
**Do NOT touch:** `preferred_biomes`. Do not remove any existing tag from the tuple.
**Verify:** New swamp_border_territory herb_patch test (Step 8).

### Step 4 — `healing_flower_patch` tag-gap fix (`sacred_grove`)
**Files:** `data/content/world/resources.yaml` (lines 46-52, the `healing_flower_patch` entry)
**Change:** This entry currently has **no** `metadata` block at all, so gating falls through to the
hardcoded `legacy_id` heuristic (`node_flower` → `("near_forest",)` only,
`src/core/registries.py:439-440`). Adding a `metadata` block bypasses that heuristic branch entirely
(branch-1-wins precedence), so the new list **must explicitly include `"near_forest"`** or that
existing coverage silently disappears. New:
```yaml
- id: "healing_flower_patch"
  material: "healing_flower"
  display_name: "Healing Flower Patch"
  resource_type: "healing_flower"
  required_ticks: 12
  default_charges: 5
  preferred_biomes: ["near_forest", "sacred_grove"]
  metadata:
    source_region_tags: ["near_forest", "sacred_grove"]
```
Rationale: `forest_warden_grove.yaml` places `healing_flower_patch: 5` in `sacred_grove`; this kind's
own `preferred_biomes` already names `"sacred_grove"` directly — the strongest evidence case in the
whole audit.
**Do NOT touch:** `preferred_biomes` (already correct, just not consulted for gating without the
`metadata` nest — do not attempt to "fix" gating by promoting the top-level field instead of adding
`metadata`, that has zero effect per the adapter's schema, `extra="forbid"` on
`CatalogBaseDefinition`).
**Verify:** New sacred_grove healing_flower_patch test (Step 7). Also re-run
`tests/unit/strategic/test_opportunities.py::test_resource_opportunities_basic` and any other test that
implicitly relies on `healing_flower_patch`'s prior near_forest-only heuristic tags (none currently
do per test_plan.md's regression surface, but confirm live).

### Step 5 — `spirit_wisp` tag-gap fix (`sacred_grove`, `haunted_battlefield`)
**Files:** `data/content/world/resources.yaml` (lines 91-97, the `spirit_wisp` entry)
**Change:** This entry also has no `metadata` block; `spirit_wisp`'s res_id does not match any of the
5 legacy_id keyword branches, so it resolves to `()` (zero tags) today. New:
```yaml
- id: "spirit_wisp"
  material: "spirit_essence"
  display_name: "Spirit Wisp"
  resource_type: "spirit_essence"
  required_ticks: 25
  default_charges: 2
  preferred_biomes: ["sacred_grove", "haunted_battlefield"]
  metadata:
    source_region_tags: ["sacred_grove", "haunted_battlefield"]
```
Rationale: `forest_warden_grove.yaml` places `spirit_wisp: 2` in `sacred_grove`; `undead_battlefield.yaml`
places `spirit_wisp: 2` in `haunted_battlefield` (only in worlds composing that module —
`frontier_extended`, `wilderness_survival`; worlds using only `ruins_mystery_quest` place no
`spirit_wisp` there at all). Adding the `haunted_battlefield` tag is safe corpus-wide even for worlds
without a physically-placed node there: `ResourceOpportunityProvider` also requires a live
`ResourceNodeState` to exist in `mock_state`/world state before it can surface an opportunity — an
empty-node-list world in that region still yields zero opportunities regardless of catalog tag
coverage (this is exactly what
`test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes` already exercises
and which remains valid after this fix).
**Do NOT touch:** `preferred_biomes` (both values already correct and now mirrored, not modified).
**Verify:** New sacred_grove spirit_wisp test (Step 7) and new haunted_battlefield spirit_wisp test
(Step 9).

### Step 6 — Rewrite `test_resource_opportunities_orc_stronghold_tag_gap` to assert positive coverage
**Files:** `tests/unit/strategic/test_opportunities.py` (currently lines 232-262)
**Change:** This test currently asserts **zero** opportunities for both `iron_vein` and `wood_node` in
`orc_stronghold`, with an explicit docstring instruction: "If this assertion starts failing, the tag
gap has been closed and this test should be rewritten to assert coverage." After Steps 1-2 land, this
assertion WILL start failing — it must be deliberately rewritten, not left broken. Follow the exact
pattern already established by `test_resource_opportunities_mountain_pass_zone_iron_vein` (lines
132-153): loop over `("iron_vein", "iron_ore")` and `("wood_node", "wood")`, set
`region_id = "orc_stronghold"`, build a `ResourceNodeState` of that kind, assert
`len(opportunities) > 0`, `all(opp.kind == "gather_resource" ...)`, and `any(opp.subject == item ...)`.
Update the docstring to cite this ticket (`TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`)
and explain the fix, mirroring the mountain_pass_zone test's "Supersedes the former ... which
documented this as a zero-opportunity gap before the fix" pattern. Keep the function name unchanged
(`test_resource_opportunities_orc_stronghold_tag_gap`) — do not rename it, per test_plan.md's explicit
instruction ("same file, same function name").
**Do NOT touch:** Any other test function in this file.
**Verify:** Test itself, run via
`pytest tests/unit/strategic/test_opportunities.py::test_resource_opportunities_orc_stronghold_tag_gap -v`.

### Step 7 — New positive-coverage tests for `sacred_grove`
**Files:** `tests/unit/strategic/test_opportunities.py`
**Change:** Add two new test functions (mirroring `test_resource_opportunities_mountain_pass_zone_iron_vein`'s
structure exactly — entity built, `region_id` set, single `ResourceNodeState` of the target kind,
assert non-empty `gather_resource` opportunities naming the right `subject`):
- `test_resource_opportunities_sacred_grove_healing_flower_patch` — `kind="healing_flower_patch"`,
  `yields_item="healing_flower"`, `region_id="sacred_grove"`, assert `any(opp.subject ==
  "healing_flower" ...)`.
- `test_resource_opportunities_sacred_grove_spirit_wisp` — `kind="spirit_wisp"`,
  `yields_item="spirit_essence"`, `region_id="sacred_grove"`, assert `any(opp.subject ==
  "spirit_essence" ...)`.
Docstrings must cite this ticket ID and the physical-placement evidence (`forest_warden_grove.yaml`).
**Do NOT touch:** Existing tests in this file.
**Verify:** Both new tests pass; depends on Steps 4 and 5.

### Step 8 — New positive-coverage tests for `swamp_border_territory`
**Files:** `tests/unit/strategic/test_opportunities.py`
**Change:** Add two new test functions, same pattern:
- `test_resource_opportunities_swamp_border_territory_wood_node` — `kind="wood_node"`,
  `yields_item="wood"`, `region_id="swamp_border_territory"`, assert `any(opp.subject == "wood" ...)`.
- `test_resource_opportunities_swamp_border_territory_herb_patch` — `kind="herb_patch"`,
  `yields_item="herb"`, `region_id="swamp_border_territory"`, assert `any(opp.subject == "herb" ...)`.
Docstrings cite this ticket ID and `sunken_swamp_border.yaml` as the placement evidence.
**Do NOT touch:** Existing tests.
**Verify:** Both new tests pass; depends on Steps 1 and 3.

### Step 9 — New positive-coverage test for `haunted_battlefield`
**Files:** `tests/unit/strategic/test_opportunities.py`
**Change:** Add `test_resource_opportunities_haunted_battlefield_spirit_wisp` — `kind="spirit_wisp"`,
`yields_item="spirit_essence"`, `region_id="haunted_battlefield"`, assert non-empty opportunities
naming `"spirit_essence"`. Docstring must explicitly note this only applies in worlds composing
`undead_battlefield.yaml` (`frontier_extended`, `wilderness_survival`); worlds using only
`ruins_mystery_quest` place no node there, so
`test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes` (which tests the
"no live node in mock state" case) remains valid and unmodified alongside this new test — the two are
not contradictory, they test different mock-state shapes for the same region.
**Do NOT touch:**
`test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes` — leave it exactly
as-is; it documents a real, still-true fact (some worlds place zero nodes in this region).
**Verify:** New test passes; depends on Step 5.

### Step 10 — New positive-coverage test for `trading_hometown`
**Files:** `tests/unit/strategic/test_opportunities.py`
**Change:** Add `test_resource_opportunities_trading_hometown_iron_vein` — `kind="iron_vein"`,
`yields_item="iron_ore"`, `region_id="trading_hometown"`, assert non-empty opportunities naming
`"iron_ore"`. Docstring must explicitly distinguish this region id from plain `hometown` (already
closed by the parent ticket family) and cite `trading_company_hub.yaml`'s `resource_recipes` +
`src/worldassembly/resolver.py:335`'s namespace-prefixing as the evidence trail.
**Do NOT touch:** Any existing `hometown`-named test (`test_resource_opportunities_hometown_wood_node`,
`_herb_patch`) — those are for a different region id and already closed.
**Verify:** New test passes; depends on Step 2.

### Step 11 — Real-catalog projection assertions in `test_registry_bridge.py`
**Files:** `tests/unit/core/test_registry_bridge.py`
**Change:** Following the exact precedent set by
`test_production_catalog_wood_and_herb_cover_hometown` (added by the parent hometown ticket after
discovering the original target assertion block used a synthetic fixture, not the real catalog), add
one new test function that loads `CatalogRepository("data/content")` directly (matching
`test_registry_parity.py::test_production_catalog_parity`'s pattern) and asserts, via `in`-membership
checks only (never equality):
- `"orc_stronghold" in res_wood.source_region_tags` and `"orc_stronghold" in res_iron.source_region_tags`
- `"swamp_border_territory" in res_wood.source_region_tags` and `"swamp_border_territory" in res_herb.source_region_tags`
- `"trading_hometown" in res_iron.source_region_tags`
- `"sacred_grove" in res_healing_flower.source_region_tags` and `"sacred_grove" in res_spirit_wisp.source_region_tags`
- `"haunted_battlefield" in res_spirit_wisp.source_region_tags`
This catches YAML structural mistakes (e.g. a typo'd region id, or a `metadata` block nested under the
wrong key) that a synthetic-fixture opportunity test cannot catch, since it reads the actual production
catalog file.
**Do NOT touch:** Any existing assertion in this file — this is a new, additive function only.
**Verify:** New test passes; depends on Steps 1-5.

### Step 12 — Corpus-wide region-coverage audit test
**Files:** New file `tests/integration/content/test_resource_region_coverage_corpus.py`
**Change:** Programmatically reproduce this ticket's live audit method (investigation.md §2): glob
`data/worlds/*/resolved/world.resolved.yaml`, load each, build the real `ResourceRegistry` projection
via `CatalogRepository("data/content").load_all()` → `CatalogToResourceRegistryAdapter.adapt()`, extract
each world's `entities[].spawn_region`/`entities[].role`, and assert the **hero-role** uncovered-region
set is empty corpus-wide (turning "zero hero-role gaps today" — this ticket's most safety-critical
finding — into a durable regression guard). Use a live glob, not a hardcoded world-name list, so newly
authored worlds are automatically included (the exact "corpus grew silently" drift this investigation
found relative to the parent ticket's stale table). Do not additionally assert an exact-equality
all-role uncovered set in this step — the 3 undispositioned regions (`bandit_road`, `goblin_camp`,
`wolf_den`) don't have a final accepted-set answer yet (blocked on OQ-1, Step 17); asserting exact
equality now would need revision the moment OQ-1 resolves, and risks becoming a silently-stale
assertion itself. A follow-up ticket (or Step 17 once OQ-1 resolves) can tighten this to exact-equality
once the 3 remaining regions have a final disposition.
**Do NOT touch:** Any other test file. Do not hardcode the 17-world list from investigation.md §2 —
that list is a point-in-time snapshot, not the corpus definition.
**Verify:** New test passes; depends on Steps 1-5 (must reflect the post-fix registry state) — run
after all catalog edits land.

### Step 13 — `GuildAction` dormancy guard (recommended, low-risk)
**Files:** New or existing file under `tests/architecture/` (match existing dispatcher-wiring guard
placement convention if one exists; otherwise a new small file,
e.g. `tests/architecture/test_guild_action_dormancy.py`)
**Change:** Assert that `GuildAction.visit()` (`src/town/guild.py`) is not referenced by any
dispatcher/pipeline-phase module under `src/engine/` or `src/domains/` (a static grep-style check over
those source trees, or an import-graph check if the project has an existing pattern for this — match
whatever mechanism existing architecture guards in this repo already use). This codifies §4's finding
that `GuildAction`'s scarcity computation (which reimplements the same `source_region_tags` gating
check independently) is currently unreachable from any live pipeline path — if this test ever starts
failing, it's a signal that the dormant risk documented in Step 16 has gone live and needs its own
region-coverage evaluation, not silent inheritance of this ticket's "currently dormant" conclusion.
**Do NOT touch:** `src/town/guild.py` itself — this step is a guard test only, not a fix or a wiring
change (wiring `GuildAction` into a dispatcher is explicitly out of scope for this ticket).
**Verify:** New test passes (asserts current dormancy).

### Step 14 — Parity ledger entry (`docs/parity_ledger/town_resource.yaml`)
**Files:** `docs/parity_ledger/town_resource.yaml`
**Change:** Add one new consolidated entry, `TOWN-189` (next unused ID after `TOWN-188`), following the
`TOWN-188` precedent's exact field structure:
```yaml
- id: TOWN-189
  text: >
    wood_node, iron_vein, herb_patch, healing_flower_patch, and spirit_wisp resource nodes placed in
    orc_stronghold, sacred_grove, swamp_border_territory, haunted_battlefield, and trading_hometown
    (by orc_clan_territory.yaml, forest_warden_grove.yaml, sunken_swamp_border.yaml,
    undead_battlefield.yaml, and trading_company_hub.yaml respectively) now correctly yield
    gather_resource opportunities for entities standing in those regions. Same root mechanism as
    TOWN-188 (hometown): ResourceOpportunityProvider.get_opportunities() gates on a global,
    catalog-wide, per-resource-kind source_region_tags allowlist, not the node's own placement
    region; these 5 kinds previously omitted the relevant region id(s) from that allowlist despite
    nodes already being physically placed there.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: >
    data/content/world/resources.yaml — wood_node/iron_vein/herb_patch's metadata.source_region_tags
    additively extended; healing_flower_patch/spirit_wisp gained new metadata.source_region_tags
    blocks (previously relied on the node_flower legacy_id heuristic or resolved to zero tags,
    respectively). src/core/registries.py CatalogToResourceRegistryAdapter.adapt() precedence unchanged.
    src/world/providers/resources.py:69 gating check unchanged.
  proof_type: parity
  test_path: >
    tests/unit/strategic/test_opportunities.py; tests/unit/core/test_registry_bridge.py;
    tests/integration/content/test_resource_region_coverage_corpus.py
  divergence_note: >
    Content-authoring gap, not a decision-logic or scoring bug, identical root cause to TOWN-188.
    zero hero-role entities affected in the live corpus prior to this fix (confirmed in
    investigation.md §2 — every hero-role entity corpus-wide spawns in hometown, already covered).
  support_boundary: null
```
**Do NOT touch:** `TOWN-183`, `TOWN-188`, or any other existing entry.
**Verify:** No test — YAML schema validation only (`docs/parity_ledger/schema.json` if a validator
script exists; confirm the file still parses as valid YAML).

### Step 15 — `intentional_divergences.md` entry
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** Add a new `### 2.28` heading immediately after `### 2.27 Hometown Resource-Opportunity
Gating Fix`, **Rationale: Bug Fix** (same class as §2.26/§2.27 — authoring staleness, not a deliberate
design decision), covering all 5 tag-gap fixes from Steps 1-5. Follow the exact §2.27 template:
Subsystem, Old Behavior, New Behavior (list each kind's before/after `source_region_tags` tuple),
Rationale, Verification (list the test files from Step 14's `test_path`), Status: ACTIVE.
**Do NOT touch:** Any existing `### 2.N` section.
**Verify:** No test — doc review only; must be internally consistent with Step 14's parity entry.

### Step 16 — `eval_matrix_results.md` follow-up closure + architecture recommendation + OQ-1 status note
**Files:** `docs/simulation_quality/eval_matrix_results.md`
**Change:** Three additions, appended (do not edit prior dated paragraphs, per this doc's established
append-only convention):
1. Near the existing `orc_stronghold` "recommended follow-up" note (~lines 993-1012/1076-1094): append
   a dated status line marking it closed by this ticket, citing `TOWN-189`.
2. A new dated note recording the region-aware `ResourceNodeState` architecture recommendation:
   **DEFER** (not adopt-now, not reject) — cite the investigation's Risks section rationale verbatim
   in substance: the pattern has recurred in 5+ regions (structural, not one-off), but the additive
   `metadata.source_region_tags` fix continues to fully resolve every case found so far with zero
   blast radius, while implementing region-awareness requires a durable-state schema change to the
   frozen `ResourceNodeState` dataclass plus touching the compiler, the provider, `GuildAction.visit()`'s
   parallel scarcity computation, and dozens of test call sites. Flag for re-evaluation if a 6th+
   occurrence surfaces where the additive fix cannot express the needed distinction (e.g. two worlds
   wanting the same kind covered in one region but not another).
3. A note recording that `GuildAction.visit()` (STRAT-244, `src/town/guild.py`) independently
   reimplements the same gating check for its `scarcity` signal but is currently unwired from any
   dispatched pipeline phase — a currently-dormant secondary risk of the same root mechanism, not fixed
   here (do not modify the STRAT-244 parity ledger entry itself).
4. A note recording that `bandit_road`, `goblin_camp`, and `wolf_den` (zero resource nodes placed
   corpus-wide) were reviewed for disposition (OQ-1) and a human reviewer decided: intentional
   hazard-zone gap, no new content authored — cite Step 17's regression-guard tests and
   `intentional_divergences.md` §2.29 (added by Step 17) as the durable record of this decision.
**Do NOT touch:** Any existing paragraph in this file — append only, matching the pattern already used
by the STONE-GAP / AGENCY-STASIS-COLLAPSE / hometown tickets' prior entries in this same file.
**Verify:** No test — doc review only.

### Step 17 — Document `bandit_road`/`goblin_camp`/`wolf_den` as an intentional hazard-zone gap (OQ-1 resolved)
**Files:** `tests/unit/strategic/test_opportunities.py`, `docs/guidelines/intentional_divergences.md`
**Change:** OQ-1 was escalated to a human reviewer (no evidence in code/docs settled it either way), who
decided: these 3 regions' total absence of resource content is an **intentional hazard-zone gap**, not
an authoring oversight — no new content is authored. Implement the decision as a durable record:
1. Add explicit-zero regression guard tests to `tests/unit/strategic/test_opportunities.py` for
   `bandit_road` and `wolf_den` (mirroring
   `test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes`'s existing
   pattern for `goblin_camp`/`haunted_battlefield` — that test already covers `goblin_camp`, so only
   `bandit_road` and `wolf_den` are net-new), asserting zero `gather_resource` opportunities for any
   resource kind when a mock entity stands in that region. Docstrings must cite this ticket ID and
   state explicitly: "intentional hazard-zone gap, decided by human review 2026-07-08 — not an
   authoring oversight."
2. Add a new `### 2.29` entry to `docs/guidelines/intentional_divergences.md` (immediately after Step
   15's new `### 2.28` entry), **Rationale: Intentional Gameplay Change**, recording that
   `bandit_road`, `goblin_camp`, and `wolf_den` carry zero resource-node content by design (hazard/combat
   regions do not offer foraging), citing the regression guard tests from item 1 (plus the pre-existing
   `goblin_camp`/`haunted_battlefield` test) as Verification, Status: ACTIVE.
**Do NOT touch:** Any world module YAML (`scalable_bandit_camp.yaml`, `bandit_road_trade_pressure.yaml`,
`goblin_camp_conflict.yaml`, `wolf_den_near_forest.yaml`) — no new content is authored per the reviewer's
decision. Do not touch the catalog fixes from Steps 1-5 or their tests.
**Verify:** New tests pass; `docs/guidelines/intentional_divergences.md` §2.29 is internally consistent
with the test names cited.

### Step 18 — Final regression gate
**Files:** None (verification only)
**Change:** Run, in order:
```bash
.venv/bin/python3 -m pytest tests/unit/strategic/test_opportunities.py -v
.venv/bin/python3 -m pytest tests/unit/core/test_registry_bridge.py tests/unit/core/test_registry_parity.py -v
.venv/bin/python3 -m pytest tests/unit/quest/test_quest_generation.py tests/unit/world/test_guild_pipeline.py -v
.venv/bin/python3 -m pytest tests/integration/worldassembly/test_e2e_smoke.py tests/unit/worldassembly/test_corpus_diversity.py tests/unit/worldassembly/test_hero_guild_routing_population_stability.py -v
.venv/bin/python3 -m pytest tests/perf/test_phase3_adventure_decision_budget.py -v
.venv/bin/python3 -m pytest tests/integration/content/test_resource_region_coverage_corpus.py -v
make evaluate
```
All must exit 0 with no unexpected failures (the two pre-existing, unrelated failures documented by the
parent hometown ticket's Deviation #4 — a test-order-pollution issue in
`test_resource_opportunity_provider.py` and a `stone_outcrop` material-catalog issue in
`test_e2e_smoke.py` — are pre-existing and out of scope; confirm via `git stash` A/B comparison if
either reappears, do not assume it is caused by this ticket's changes without checking).
**Do NOT touch:** Nothing to change here — this step is verification only. If `make evaluate` reports
any non-zero regression, treat it as a real signal to root-cause before closing the ticket, per repo
convention — do not silently re-anchor `grade_anchors.json`.
**Verify:** All commands above exit 0.

## Scope Guards

- Do not touch `src/world/providers/resources.py`, `src/core/registries.py`
  (`CatalogToResourceRegistryAdapter`), or `src/core/state.py` (`ResourceNodeState`) — every fix in
  this plan is a `data/content/world/resources.yaml` catalog-content edit only. The region-aware
  `ResourceNodeState` architecture change is a recommendation (Step 16, item 2: DEFER), never an
  implementation, in this ticket.
- Do not touch `src/domains/adventure/phase.py` or `AdventureDecisionPhase`/`Generator` decision logic
  — this is a content/catalog audit, not a routing-logic change (explicit ticket Out of Scope).
- Do not touch `src/town/guild.py`'s `GuildAction.visit()` — it is unwired dead code today; "fixing"
  its scarcity computation is scope creep with no observable effect (Step 13 only adds a dormancy
  *guard test*, never a code change to this file).
- Do not touch the `simq_routing_test`/`urban_political` plain-`hometown` rows or any test/doc already
  covering them (`TOWN-188`, `test_resource_opportunities_hometown_wood_node`,
  `_hometown_herb_patch`) — already closed by the parent ticket family. `trading_hometown` (Steps 2, 10)
  is a distinct, unrelated region id and is correctly in scope.
- Do not make any `source_region_tags` edit non-additive (never replace a tuple/list wholesale — always
  append to the existing values). A bare `["orc_stronghold"]` on `wood_node` would silently break
  `near_forest`/`hometown` coverage for 8+ other worlds.
- Do not edit `preferred_biomes` on any resource kind as a substitute for adding/extending
  `metadata.source_region_tags` — the adapter never consults the top-level field for gating; this has
  zero effect on behavior and would be a wasted, misleading edit.
- OQ-1 (`bandit_road`/`goblin_camp`/`wolf_den` disposition) was resolved by human review: intentional
  hazard-zone gap, no new content authored. Step 17 implements only the regression-guard tests and
  divergence-doc entry for that decision — do not author new resource content for these 3 regions.
- Do not re-derive "the corpus" from the parent ticket's stale 10/11-world table — Step 12's audit test
  must live-glob `data/worlds/*/resolved/world.resolved.yaml`, matching investigation.md §2's corrected
  17-world count.
- Do not modify the `STRAT-225` or `STRAT-244` parity ledger entries themselves — Step 16 adds a note
  referencing `STRAT-244`'s dormant-risk finding in `eval_matrix_results.md`, but the ledger entry text
  stays as-is (no behavior change to either's subject).
- `data/runs/` and `reports/release_proof/` are not created or read by any step in this plan — no
  cleanup obligation beyond the standard end-of-ticket housekeeping.

## Dependency Map

- Steps 1-5 (catalog edits) are mutually independent — each touches a different resource kind's entry
  in the same file, no ordering constraint between them, but all should land before Steps 6-12 run
  (those steps assert against the post-fix registry state).
- Step 6 depends on Steps 1 and 2 (both `wood_node` and `iron_vein` orc_stronghold tags).
- Step 7 depends on Steps 4 and 5 (`sacred_grove` tags on both kinds).
- Step 8 depends on Steps 1 and 3 (`swamp_border_territory` tags on both kinds).
- Step 9 depends on Step 5 (`haunted_battlefield` tag on `spirit_wisp`).
- Step 10 depends on Step 2 (`trading_hometown` tag on `iron_vein`).
- Step 11 depends on Steps 1-5 (asserts the real catalog projection post-fix).
- Step 12 depends on Steps 1-5 (must reflect the post-fix registry when computing the hero-role
  uncovered set).
- Step 13 is independent of all other steps (asserts current, unrelated-to-this-fix dormancy).
- Step 14 (parity ledger) depends on Steps 1-5 and should reference the test paths added in Steps
  6-12 (write after those tests exist, so the `test_path` field is accurate).
- Step 15 (`intentional_divergences.md`) depends on Step 14 (must stay internally consistent with the
  parity entry).
- Step 16 (`eval_matrix_results.md`) depends on Steps 14-15 (cites `TOWN-189`) and item 4 cites Step
  17's resolution of OQ-1 (intentional gap, documented in `intentional_divergences.md` §2.29).
- Step 17 is independent of Steps 1-16 — it documents a separate, human-resolved question — but should
  land before Step 18's final regression gate so its new tests are included in that run.
- Step 18 depends on all prior steps (1-17) being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Live-reverified uncovered-region table (per world, per region) | Already done in investigation.md §2 (no plan step re-does this; Step 12 turns it into a durable test) | `tests/integration/content/test_resource_region_coverage_corpus.py` (Step 12) |
| Non-hero opportunity-consumer trace completed | Already done in investigation.md §4 (no plan step re-does this; Step 13 turns the `GuildAction` finding into a durable guard) | `tests/architecture/test_guild_action_dormancy.py` (Step 13) |
| Each uncovered region has explicit disposition recorded | Steps 1-5 (fixed via tag) for the 5 tag-gap regions; Step 17 (intentional-gap decision + guard tests) for the 3 zero-content regions; Steps 14-16 (parity + divergence doc + eval-matrix note) | Steps 14/15/16 are doc-review-verified; Step 17 verified by its own new tests |
| Recommendation recorded (adopt-now/defer/reject) on region-aware `ResourceNodeState` | Step 16 item 2 | Doc review only (`eval_matrix_results.md`) |
| `make evaluate --dry-run` exits 0 with 0 regressions | Step 18 | `make evaluate` (Makefile target already implies `--dry-run`) |
| `make knowledge-index-update` run if `docs/` files were modified | Not a plan step — Steps 14-16 modify `docs/`, so this must run during Finalize (post-plan pipeline phase), not during Implement | N/A (workflow-level, not implementation-level) |

## Anti-Drift Notes

- **`test_resource_opportunities_orc_stronghold_tag_gap`'s pre-fix "expects zero" assertion is itself
  documentation of the pre-fix state** — Step 6 must deliberately rewrite it, not merely notice it
  failing and patch around it. If it fails during Step 18's verification pass before Step 6 has run,
  that is expected and correct, not a bug.
- **`preferred_biomes` vs. `metadata.source_region_tags` is a structural trap, not a naming
  preference** — `ResourceDefinition.preferred_biomes` (top-level Pydantic field,
  `src/content/schema.py:241`) is never consulted by the adapter's gating precedence unless explicitly
  re-nested under `metadata:`. Every catalog edit in Steps 1-5 targets `metadata.source_region_tags`
  specifically; touching only the top-level `preferred_biomes` field (which in 3 of 5 cases already
  happens to name the correct region, since it's descriptive authoring metadata, not gating input) has
  **zero** effect on runtime behavior.
- **`healing_flower_patch` and `spirit_wisp` (Steps 4-5) currently have no `metadata` block at all** —
  adding one is not purely additive at the YAML level the way Steps 1-3 are (which extend an existing
  list); it displaces the legacy_id-heuristic fallback (`healing_flower_patch`) or the empty-tuple
  fallback (`spirit_wisp`) entirely. Step 4 explicitly re-includes `"near_forest"` in the new list for
  this reason — omitting it would silently regress `healing_flower_patch`'s existing `near_forest`
  coverage, which no `preferred_biomes` field would catch since that field stays unchanged either way.
- **`trading_hometown` ≠ `hometown`** — confirmed via `src/worldassembly/resolver.py:335`'s
  namespace-prefixing (`prefix = f"{ref.namespace}_"`). Any implementer instinct to fold Step 2/10's
  `trading_hometown` work into the already-closed plain-`hometown` fix is a mistake; they are different
  catalog-tag values and different regions in resolved world state.
- **`haunted_battlefield`'s per-world split (some worlds place a node there, some don't) does not
  block the catalog-level fix** — the fix is at the resource-*kind* level (global, corpus-wide), not
  per-world. Adding the tag is safe for worlds with zero nodes there because
  `ResourceOpportunityProvider` still requires a live node in `resource_nodes` state; the tag alone
  produces zero opportunities absent a node, exactly as
  `test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes` already verifies.
- **OQ-2 (`orc_stronghold`'s weaker evidentiary case) does not block Steps 1-2 or Step 6** — the
  investigation explicitly recommends fixing it despite lacking `preferred_biomes` self-evidence,
  because a resource node is physically placed there (matching the `hometown` precedent's root-cause
  shape). This plan proceeds with that recommendation.
- **Do not run the full `pytest tests/` suite** — every verification step above is deliberately scoped
  to the world/resource/quest/strategic-cognition domains this ticket touches, per CLAUDE.md's Testing
  Rule.

## Questions Resolved During Planning

- **OQ-1** — Is the zero-resource-node condition in `bandit_road`, `goblin_camp`, and `wolf_den` an
  intentional design choice or an authoring oversight? The investigation found no code or doc evidence
  settling this either way. Escalated to a human reviewer, who decided (2026-07-08): **intentional
  hazard-zone gap** — no new content authored. Implemented by Step 17.
