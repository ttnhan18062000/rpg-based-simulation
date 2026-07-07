---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP
artifact_type: investigation
tags: [simulation-quality, world, adventure, bug]
---

# Investigation — TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP

## Current Behavior

**`urban_political` world composition** (`data/worlds/urban_political/world.yaml`): 4
`module_refs` — `frontier_village_core` (order 0), `trading_company_hub` (order 1, namespace
`trading`), `bandit_road_trade_pressure` (order 2), `hero_adventurers` (order 3). Description:
"Settlement-heavy world with faction relationships and trade pressure. A frontier village
coexists with a separate merchant trading hub and is pressured by bandit road activity." No
mention of adventuring/routing anywhere in the description or `provided_features`
(`settlement`, `trade_hub`, `trade_route`, `faction_pressure`).

**`urban_political`'s SimQ profile** (`config/simulation_quality/profiles/urban_political.yaml`):
`pillar_weights` for FACTION/ECONOMY/SOCIAL (1.5) and COMBAT (0.3); `feature_flags:
{ENABLE_SOCIAL_COOPERATION: "ON", ENABLE_BELIEF_ASSIMILATION: "ON"}`. **No
`ENABLE_ADVENTURE_ROUTING` key present** — resolves to `OFF` by
`FeatureFlagManager`'s absence-means-OFF default (`src/domains/optimization/feature_flags.py:16`).
Confirmed live via `tests/integration/test_world_profile_feature_flag_guardrail.py`'s
`test_agency_da_anti_drift_guard` (T3), which reads
`_FIXTURE["_meta"]["agency_da_non_routing_worlds"]` from
`tests/simulation_quality/fixtures/expected_world_flag_state.json` and asserts every listed world
(which includes `urban_political`) resolves `ENABLE_ADVENTURE_ROUTING` to `OFF`.

**`data/content/world/resources.yaml` current state (read directly, lines 1-43):**
```yaml
- id: "wood_node"
  ...
  preferred_biomes: ["frontier_village", "near_forest"]
  metadata:
    source_region_tags: ["near_forest", "hometown"]
...
- id: "herb_patch"
  ...
  preferred_biomes: ["near_forest", "sunken_swamp"]
  metadata:
    source_region_tags: ["near_forest", "moon_cave", "hometown"]
```
Both entries **already include `"hometown"`** in `metadata.source_region_tags`. This is a global,
world-agnostic catalog file — `ResourceOpportunityProvider.get_opportunities()`
(`src/world/providers/resources.py:69`) gates purely on `current_region in
res_def.source_region_tags`, where `res_def` is looked up by resource **kind**, not by world or
node instance. Since `urban_political` uses `frontier_village_core` (which places `wood_node`/
`herb_patch` physically in `hometown`, same as `simq_routing_test`) and `hero_adventurers` (which
spawns all 3 hero-role entities in `hometown`, same as `simq_routing_test`), the fix landed by
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` **already closes the content half of this
gap for `urban_political` too** — confirmed directly by reading the current file state, not
inferred from the prior ticket's claim.

**`urban_political`'s current AGENCY grade anchors** (`grade_anchors.json`, verified via direct
JSON parse): `urban_political_seed{42,123,456}_{200t,500t,1000t}` all report `AGENCY: "C"` — 7
anchor entries, uniformly C, consistent with `ENABLE_ADVENTURE_ROUTING=OFF`.

## Mechanics / Engine Constraints

- `docs/mechanics/adventure_routing_contract.md` — companion to `04_strategic_cognition.md`;
  defines the route family taxonomy and the `defer_with_reason` fallback contract this gap
  interacts with. Routing runs in the kernel's Scheduling stage via
  `StrategicWorldIntegrationSystem` → `AdventureRouteGenerator.generate()`, gated entirely by
  `ENABLE_ADVENTURE_ROUTING` (`src/engine/pipeline.py`'s `run_phase("adventure_decision", ...,
  "ENABLE_ADVENTURE_ROUTING")`).
- `AdventureDecisionPhase` only processes `EntityRole.HERO` entities
  (`src/domains/adventure/phase.py:75`). `urban_political` has hero-role entities (via
  `hero_adventurers`), so if routing were ever enabled, this phase would begin acting on them
  immediately.
- Per the Authoritative Mechanics Rule, `AdventureDecisionPhase` is documented as **opt-in by
  world archetype, not a global default** (`eval_matrix_results.md`'s AGENCY Cross-World Design
  Note, itself sourced from `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s ruling).

## Parity Ledger Overlap

- **`TOWN-183`** (`docs/parity_ledger/town_resource.yaml:2029`, status `verified`, P1): documents
  `urban_political`'s `>= 3 resource nodes` requirement, explicitly naming `wood_node` (8 charges,
  `hometown`) and `herb_patch` (5 charges, `hometown`) from `frontier_village_core`. Scoped to node
  *count*, not opportunity-gating coverage — remains accurate, does not need editing for this
  ticket (matches the parent ticket's own §7 finding).
- **`INFRA-237`** (`docs/parity_ledger/infrastructure.yaml:2899`, status `verified`, P1):
  `AgencyScorer` contract coverage; `support_boundary` already populated by
  `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` and extended by `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`
  to name both routing-capable worlds (`simq_routing_test`, `hero_guild_routing`). Not modified by
  this ticket if the dormant-accepted path is taken (`urban_political` stays non-routing).
- **`SIMQ-CALIBRATED-001`** (`docs/parity_ledger/infrastructure.yaml:3489`): `route_selected`/
  `action_executed` emission wiring; same `support_boundary` pattern as `INFRA-237`. No P0 entries
  found in this ticket's scope — nothing requires a new `test_path`.

## Prior Work — the two precedents that settle this ticket's Scope item 1

**Precedent A — `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`** (read in full,
`tickets/done/TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA.md`): ruled, per explicit **user direction
2026-07-02**, that `AGENCY=C` in every calibration world except `simq_routing_test` is
**"design-intentional... the AdventureDecisionPhase is opt-in by world archetype, not a global
default."** Its own anti-drift note: **"if a new calibration world enables
`ENABLE_ADVENTURE_ROUTING`, it must be identified in the DA annotation as a routing-capable
archetype and its AGENCY grades must be calibrated separately from the 'routing-inactive'
majority."** This ruling establishes that non-routing status for `urban_political` is a settled
architectural decision, not an open gap — `urban_political` was one of the 27/30 (later 9 named
non-routing worlds) this ruling directly covers.

**Precedent B — `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`** (read in full,
`tickets/done/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY.md`): this is the ticket that most
directly answered "how do we add more AGENCY coverage at real-gameplay scale" (its own Request
Summary: `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 found "a
routing-capable (AGENCY-active) world that is also a 'real' gameplay archetype" as a gap). Its
explicit, evaluated-and-rejected middle ground: it **noted** that `urban_political` already has a
`hero_guild`-framed population (4 entities) and is "not architecturally foreign" to an
adventuring framing (Scope item 2) — but its **chosen implementation path was to author a
brand-new world (`hero_guild_routing`) rather than enable routing on `urban_political` or any
other existing archetype.** Its Request Summary states explicitly: **"This ticket does NOT
reverse `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for any existing world — the 9 non-routing worlds
keep AGENCY=C, permanently, per that ruling. This is a new archetype category ('routing-capable,
real-scale') added alongside 'routing-inactive' and 'routing-test-only,' not a reinterpretation of
any existing world's archetype-correctness."** Its Out of Scope explicitly lists: "Reversing
`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for `urban_political`, `dungeon_crawl`, or any of the other 7
existing non-routing worlds — none of them change AGENCY grade as a result of this ticket."

**Conclusion: this ticket's Scope item 1 ("decide whether `urban_political`'s profile should ever
force `ENABLE_ADVENTURE_ROUTING=ON`") is already answered by direct precedent, twice over — once
by the original DA ruling (which is a standing architectural decision, not merely a default) and
once by the ticket that most directly considered and rejected enabling routing on an existing
archetype (`urban_political` specifically named as the closest candidate, and explicitly not
chosen). No new human decision is required to answer this question; the answer is "no, permanently,
per precedent," matching Scope's own second bullet's "dormant, accepted" path.**

Supporting confirmation: `docs/simulation_quality/corpus_tier_taxonomy.md` classifies
`urban_political` as `Regression/baseline` tier, described as "30 entities, 3 regions — the only
world with any FACTION/INFORMATION/self-model content populated... already End-to-end by
criterion" — framed entirely around FACTION/INFORMATION/settlement mechanics, never adventuring.
Its `pillar_weights` (FACTION/ECONOMY/SOCIAL emphasized, COMBAT de-emphasized) reinforce this
archetype framing as settlement/political, not hero-routing-oriented.

## Risks and Open Questions

None block this ticket. The one item the ticket's own "Assumptions / Open Questions" section
flags ("whether `urban_political` was ever intended to be 'routing-capable' is unconfirmed") is
resolved by the precedent evidence above — it was considered and explicitly rejected as the
implementation vehicle for AGENCY expansion, in favor of a dedicated new world. This is a
definitive negative answer, not an absence of evidence.

If a future ticket wants to reopen this decision, it would need to explicitly propose reversing
both `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` and `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s
Out-of-Scope ruling — a much higher bar than this ticket's own scope authorizes, and one both
prior tickets flagged as requiring a new "user direction" (Precedent A) equivalent decision.

## Anti-Drift Hazards

- **Do not** add `ENABLE_ADVENTURE_ROUTING: "ON"` to `config/simulation_quality/profiles/
  urban_political.yaml` — this would silently break
  `tests/integration/test_world_profile_feature_flag_guardrail.py::test_agency_da_anti_drift_guard`
  (T3), which asserts every world in `expected_world_flag_state.json`'s
  `_meta.agency_da_non_routing_worlds` list (includes `urban_political`) resolves the flag to
  `OFF`. That fixture list itself is only updated in a future ticket if the precedent above is
  ever formally reversed.
- **Do not** re-fix `wood_node`/`herb_patch`'s `source_region_tags` — already fixed (verified
  above); doing so again would be redundant, out-of-scope work explicitly called out in this
  ticket's own Out of Scope.
- **Do not** conflate this ticket with `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT**
  (the broader non-hero-role resource-tag coverage gap) — that is a separate, wider-scope ticket
  per this ticket's own Out of Scope.
- The doc note this ticket adds must go into the **existing** `## AGENCY — Cross-World Design
  Note` section of `eval_matrix_results.md` (not a new top-level section) to match the
  established pattern from `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` and
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`, both of which appended new paragraphs to that same
  section rather than creating parallel sections.

## Drafted "dormant, accepted" note text

To be appended to `docs/simulation_quality/eval_matrix_results.md`'s `## AGENCY — Cross-World
Design Note` section, after the existing "Second routing-capable archetype — `hero_guild_routing`"
paragraph (matching that paragraph's bolded-lead-in, ticket-citation, and closing-scope-clarification
style):

> **Third exception class — `urban_political`'s dormant `hometown` gap, accepted as permanent
> non-issue (TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP):**
> `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s investigation (§4(i)) found that
> `urban_political` shares both `frontier_village_core` (places `wood_node`/`herb_patch` in
> `hometown`) and `hero_adventurers` (spawns all 3 hero-role entities in `hometown`) with
> `simq_routing_test` — the same module combination that produced `simq_routing_test_seed456`'s
> `defer_with_reason` stasis failure mode before that ticket's catalog fix. That fix (adding
> `"hometown"` to `wood_node`/`herb_patch`'s `source_region_tags` in
> `data/content/world/resources.yaml`) is global and already covers `urban_political` too, as a
> confirmed side effect — verified directly against the current catalog file
> (`TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`'s investigation). This gap remains
> **permanently dormant**, not merely temporarily inert: per the archetype decision above and
> `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s explicit choice to author a brand-new
> routing-capable world (`hero_guild_routing`) rather than enable routing on `urban_political` —
> the closest existing candidate, having a `hero_guild` faction population already — `urban_political`
> is confirmed to never force `ENABLE_ADVENTURE_ROUTING=ON`. Its archetype framing (settlement/
> political, FACTION/ECONOMY/SOCIAL-weighted, `Regression/baseline` tier per
> `corpus_tier_taxonomy.md`) was never intended as adventuring/routing-oriented. No further action
> is required unless a future ticket explicitly proposes reversing both
> `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` and `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s
> Out-of-Scope ruling for `urban_political`.

## Gaps Found

- None in the "Related Code Areas" — all listed files exist and were read directly.
- No acceptance criterion references behavior that doesn't exist; the AC's "if routing is never
  enabled" branch is the one this investigation confirms applies.
