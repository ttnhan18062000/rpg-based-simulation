---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-FACTION
artifact_type: investigation
tags: [simulation-quality, faction, world, corpus, calibration]
---

# Investigation — TCK-20260710-SIMQ-DEPTH-FACTION

## Current Behavior

**Pattern-6 compiler/resolver plumbing (confirmed reusable as-is, zero engine changes needed):**

- `src/worldbuilding/schema.py:47-55` — `FactionSpec.initial_tension_level: float` (default `0.0`,
  bounded `ge=0.0, le=1.0`), frozen model. Confirms ticket's cited line range.
- `src/worldassembly/schema.py:40-43` — `WorldCompositionSpec.faction_tension_overrides:
  Dict[str, float]` (default `{}`), and `src/worldassembly/schema.py:168-171` — the mirrored field
  on `NormalizedWorldComposition`. Confirms ticket's cited line range.
- `src/worldbuilding/compiler.py:179-202` (`WorldCompiler.compile()` step 3, "Compile factions") —
  for each `f_spec in spec.factions`, constructs `FactionState(faction_id=f_spec.id,
  tension_level=f_spec.initial_tension_level)` (line 199-202) and inserts into the single
  `factions: Dict[str, FactionState]` dict that is later passed into the one
  `AuthoritativeState(...)` constructor call. This is the sole authoritative init point (per
  Pattern 6's failure-signature check) — confirmed no second construction path exists.
- `src/worldassembly/resolver.py:230` (`WorldAssemblyResolver.assemble()`) and `resolver.py:638-641`
  — after module/catalog merge, iterates `normalized_comp.faction_tension_overrides.items()`,
  applying each override onto the merged factions dict via full `FactionSpec.model_validate(...)`
  reconstruction (not `.model_copy(update=...)`, preserving Pydantic v2 field validation), raising
  on unknown faction IDs. This produces the `WorldSpec` that `WorldCompiler.compile()` then consumes.

This mechanism is exercised by 11 of the corpus's 17 worlds today (see coverage table below) — it
is proven at both small scale (`sandbox_world`, 18 entities) and large scale (`frontier_marches`,
62 entities/9 regions, authored-from-inception).

## Mechanics / Engine Constraints

- `docs/simulation_quality/quality_scoring_contract.md` §5 — FACTION pillar (`Faction & Military`:
  diplomacy, military conflict, territory; Pipeline anchors PP-08–11, PP-23; D01 Tier 2, 20/25).
  Grading depends on `diplomatic_transition`/`faction_tension_delta` calibration hits, which in turn
  require `DiplomaticStateMachine.compute_transitions()`'s `pair_tension > 0.4` threshold
  (`docs/parity_ledger/faction.yaml` FAC-006) to ever be crossable — impossible unless
  `FactionState.tension_level` is seeded above 0 at compile time (this is exactly the "no bootstrap"
  gap FAC-012 documents as closed).
- `docs/guidelines/design_patterns.md` Pattern 6 ("Compile-Time Pillar Activation Pattern", lines
  277-301) — the general shape this ticket's plumbing follows: a durable-state field on
  `AuthoritativeState` that is permanently empty/default for every compiled world because nothing in
  `WorldCompiler.compile()` ever constructs it from world content. Confirmed: this gap is already
  closed for FACTION (`TCK-20260702-SIMQ-UPLIFT2-FACTION`) — the remaining candidate work under this
  ticket's original framing is per-world *content* authoring, not further engine work.

## Parity Ledger Overlap

- `docs/parity_ledger/faction.yaml` **FAC-012** (status: `verified`, priority: `P1`) — "FactionState
  is constructed with tension_level seeded from WorldSpec.factions[].initial_tension_level at
  world-compile time." `v2_evidence` already cites `urban_political` and `frontier_marches` as two
  data points. All `test_path` entries verified to exist on disk (see Test Plan). This is the entry
  the ticket's Scope item 7 targets for extension — **but see UQ-1 resolution below: there is no new
  world to add evidence for**, so this entry needs no change unless the Plan phase decides
  otherwise.
- `docs/parity_ledger/faction.yaml` **FAC-001** (verified, P1) — durable persistence of
  `AuthoritativeState.factions`; cross-referenced by FAC-012, not itself touched by this ticket.
- `docs/parity_ledger/faction.yaml` **FACTION-TENSION-001** (verified, P1) — the distinct *runtime*
  tension mechanism (`FactionAwarenessService.compute_tension_updates()` reacting to
  `RESOURCE_DEPLETED` events). Confirmed out of scope, not touched by compile-time seeding.
- No P0 entries in `faction.yaml` are implicated by this ticket's scope.

## Prior Work

- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/` — original Pattern-6 engine fix
  (schema/compiler/resolver) plus `urban_political` seeding (`bandit_company: 0.5, town_council:
  0.5`). This is the plumbing everything downstream reuses unmodified.
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/` — authored bespoke,
  archetype-matched `faction_tension_overrides` into 8 more worlds (`highland_traverse`,
  `dungeon_crawl`, `swamp_border_world`, `sandbox_world`, `generated_frontier_3_42`,
  `wilderness_survival`, `frontier_extended`, `frontier_living_world`), all confirmed present with
  non-zero values by direct `grep` against live `world.yaml` files (see coverage table). This is the
  precedent for "archetype-honest, not copy-pasted" judgment calls this ticket's Scope item 2 would
  have to follow if any candidate remained.
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/` — authored `crowded_frontier`,
  `resource_dense_basin` (deliberately FACTION-inert, tier-purity) and `frontier_marches`
  (FACTION-active from inception). Directly relevant precedent for why `crowded_frontier` and
  `resource_dense_basin` must stay out of scope: `crowded_frontier`'s own `world.yaml` composes 5
  faction-populating modules and its own description says "six distinct factions contest a
  footprint" (`data/worlds/crowded_frontier/world.yaml:5`), yet **no** `faction_tension_overrides`
  key exists in that file — confirmed by direct grep, not inferred from docs. This is a *deliberate*
  omission per `eval_matrix_results.md:1291-1292` ("tier-purity rule — this world's justification is
  scale alone"), not an oversight — the world genuinely could carry FACTION content mechanically,
  but doing so would break the stress tier's single-variable isolation contract.
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` (done) — authored `unit_faction_tension`
  (the unit-tier world that *does* isolate FACTION, already counted in the 11 covered) plus
  `unit_information_source`/`unit_selfmodel_pilot`'s explicit "faction_tension_overrides stays at
  catalog default" isolation framing, confirmed verbatim in both worlds' `world.yaml` `description:`
  fields (see coverage table).
- `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` (done) — `docs/simulation_quality/corpus_tier_taxonomy.md`,
  the tier classification this ticket's Out-of-Scope section defers to. Cross-checked against live
  `data/worlds/*/world.yaml` state below (UQ-3) and found accurate as of this investigation.

## Corpus-Wide FACTION Coverage Re-Verification

Ground truth: direct `grep -n -A3 "faction_tension_overrides" data/worlds/*/world.yaml` and read of
each of the 6 "remaining" worlds' `world.yaml` in full, cross-checked against
`eval_matrix_results.md`'s per-world grade tables and `corpus_tier_taxonomy.md`'s tier mapping.
17 worlds total under `data/worlds/` (excluding `world_index.json`).

| # | World | Tier | FACTION content? | `faction_tension_overrides` (live grep) | Tier-purity rationale (if not covered) |
|---|---|---|---|---|---|
| 1 | `urban_political` | Regression/baseline (already E2E by criterion) | **Covered** | `{bandit_company: 0.5, town_council: 0.5}` | — |
| 2 | `highland_traverse` | End-to-end | **Covered** | `{town_council: 0.5, merchant_league: 0.5}` | — |
| 3 | `dungeon_crawl` | End-to-end | **Covered** | `{goblin_warband: 0.5, bandit_company: 0.5}` | — |
| 4 | `swamp_border_world` | End-to-end | **Covered** | `{town_council: 0.5, swamp_tribe: 0.5}` | — |
| 5 | `sandbox_world` | End-to-end | **Covered** | `{town_council: 0.5, merchant_league: 0.5}` | — |
| 6 | `generated_frontier_3_42` | End-to-end | **Covered** | `{arcane_circle: 0.5, orc_clan: 0.5}` | — |
| 7 | `wilderness_survival` | End-to-end | **Covered** | `{undead_remnants: 0.5, wild_beast_pack: 0.5}` | — |
| 8 | `frontier_extended` | End-to-end | **Covered** | `{orc_clan: 0.5, forest_wardens: 0.5}` | — |
| 9 | `frontier_living_world` | End-to-end | **Covered** | `{bandit_company: 0.5, merchant_league: 0.5}` | — |
| 10 | `frontier_marches` | Stress (gap 3, authored-from-inception) | **Covered** | `{bandit_company: 0.5, orc_clan: 0.5}` | — |
| 11 | `unit_faction_tension` | Unit (isolates FACTION itself) | **Covered** | `{town_council: 0.5, merchant_league: 0.5}` | — |
| 12 | `crowded_frontier` | Stress (gap 1: many-factions/small-map) | Not covered | absent (verified: no key in `world.yaml` at all) | Deliberate tier-purity default — world populates 6 distinct factions (`town_council`, `merchant_league`, `hero_guild`, `bandit_company`, `goblin_warband`, `orc_clan`, per `world_compile_report.json`'s `distinct_populated_factions`) but the stress tier's job is isolating scale as the sole variable (`eval_matrix_results.md:1291-1292`, `corpus_tier_taxonomy.md`). FACTION=C confirmed stable across all 3 seeds. |
| 13 | `resource_dense_basin` | Stress (gap 2: resource-saturated/small-map) | Not covered | absent (verified: no key in `world.yaml` at all) | Same tier-purity default — composes `orc_clan_territory` (faction-populating module) but deliberately isolates resource density as the sole variable. FACTION=C confirmed stable across all 3 seeds (`eval_matrix_results.md:1353`). |
| 14 | `simq_routing_test` | Regression/baseline | Not covered | absent (no key in `world.yaml`) | Purpose-built minimal AGENCY calibration fixture predating the FACTION Pattern-6 uplift, not a shipped-gameplay archetype (`corpus_tier_taxonomy.md:129`). FACTION=C, 0 events, all 3 seeds (`eval_matrix_results.md:292`). |
| 15 | `hero_guild_routing` | Unit (isolates AGENCY/routing only) | Not covered | absent (no key in `world.yaml`) | Deliberately isolates AGENCY/route-selection; FACTION explicitly noted "isolation-tier default" (`eval_matrix_results.md:1222`). |
| 16 | `unit_information_source` | Unit (isolates INFORMATION only) | Not covered | key absent in `world.yaml`; description explicitly states "`faction_tension_overrides` stays at catalog default (all factions 0.0)" (`world.yaml:4`) | Deliberate single-mechanic isolation (INFORMATION). FACTION=C, "isolation confirmed... 0 events, as designed" (`eval_matrix_results.md:1137`). |
| 17 | `unit_selfmodel_pilot` | Unit (isolates COGNITION self-model only) | Not covered | key absent in `world.yaml`; description explicitly states "`faction_tension_overrides` stays at catalog default (all factions 0.0)" (`world.yaml:4`) | Deliberate single-mechanic isolation (COGNITION self-model). FACTION=C, "isolation confirmed" (`eval_matrix_results.md:1180`). |

**Totals: 11/17 covered, 6/17 not covered — all 6 have a documented, live-verified tier-purity
rationale.** This exactly matches the ticket's own UQ-1 claim; the roadmap's stale premise
("FACTION active only in `urban_political`") is confirmed stale, and the ticket's own correction is
confirmed accurate against ground truth, not just against the (possibly stale, per UQ-3) docs.

Note the `initial_tension_level` grep (distinct from `faction_tension_overrides`) matched all 17
worlds' *resolved* specs (`data/worlds/*/resolved/world.resolved.yaml`) — this is expected and not
a sign of hidden coverage: `FactionSpec.initial_tension_level` is a schema field present on every
`FactionSpec` in every resolved world (defaulting to `0.0` unless overridden), not itself evidence
of authored content. The `faction_tension_overrides` grep against `world.yaml` (the authored
composition, not the resolved output) is the correct signal and is what the table above is built
from.

## UQ-1 Resolution

**Definitive answer: NO genuinely uncovered, tier-appropriate FACTION candidate remains in the
17-world corpus.** All 6 nominally "remaining" worlds (`crowded_frontier`, `resource_dense_basin`,
`simq_routing_test`, `hero_guild_routing`, `unit_information_source`, `unit_selfmodel_pilot`) were
individually re-verified against live `world.yaml` content (not just against
`corpus_tier_taxonomy.md`/`eval_matrix_results.md`, both of which were also independently
spot-checked and found accurate — resolving UQ-3 as "not stale" for FACTION purposes) and each has
a legitimate, deliberate tier-purity reason to stay FACTION-inert:

- **Stress tier (`crowded_frontier`, `resource_dense_basin`):** each isolates one scale/composition
  variable (many-factions/small-map; resource-saturated/small-map) as its sole authoring
  justification. `crowded_frontier` is the strongest evidence this is deliberate, not an oversight:
  it mechanically populates 6 distinct factions (more than any FACTION-covered world in the corpus)
  and could trivially carry `faction_tension_overrides`, but doing so would defeat the stress tier's
  single-variable-isolation contract that this ticket's own Out-of-Scope section already flags.
- **Regression/baseline tier (`simq_routing_test`):** purpose-built minimal AGENCY calibration
  fixture, explicitly documented as predating and distinct from the shipped-gameplay archetype
  category this ticket's Scope targets.
- **Unit tier (`hero_guild_routing`, `unit_information_source`, `unit_selfmodel_pilot`):** each
  isolates exactly one other gated mechanic (AGENCY/routing; INFORMATION; COGNITION self-model) per
  the taxonomy's unit-tier classification criterion — adding FACTION content to any of them would
  violate the single-variable isolation the unit tier exists to provide, and two of the three
  (`unit_information_source`, `unit_selfmodel_pilot`) explicitly document "faction_tension_overrides
  stays at catalog default" as a load-bearing design choice in their own `world.yaml` description,
  not an incidental gap.

**This ticket cannot proceed as scoped.** There is no set of 2-3 (or even 1) archetype-appropriate,
tier-legitimate candidate worlds left to author FACTION content into. Scope items 2-8 (candidate
selection, content authoring, recalibration, doc/parity updates) have no valid target. This is not a
failure of investigation — it is investigation correctly discovering that prior work
(`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` + `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` +
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`) already fully satisfied the roadmap's Phase 3
FACTION-half intent before this ticket was picked up for implementation.

## Risks and Open Questions

- **UQ-1: RESOLVED (see above) — blocks this ticket's scope as written.** The Plan phase must not
  attempt to force content authoring into a tier-inappropriate world (e.g., requesting a
  tier-purity exception for `crowded_frontier`) merely to satisfy the roadmap's "2-3 worlds" framing
  — the ticket's own UQ-2 default assumption ("proceed with however many legitimate candidates exist
  even if only 1") does not apply here because the legitimate candidate count is 0, not 1.
- **UQ-2: Moot.** With 0 legitimate candidates, there is no target count to debate.
- **UQ-3: RESOLVED — not stale for FACTION purposes.** Both `corpus_tier_taxonomy.md` (dated
  "as of 2026-07-07") and `eval_matrix_results.md`'s relevant sections were independently
  cross-checked against live `data/worlds/*/world.yaml` grep output and found accurate — no drift
  found. (This does not rule out staleness in unrelated sections of either doc outside FACTION
  scope, which was not exhaustively checked.)
- **Open question for Plan phase (not blocking, but decision-relevant):** how should this ticket be
  closed? Three options were named in the ticket's own UQ-1 text: (a) re-scope as a stress/unit-tier
  tier-purity exception with explicit justification — **not recommended**, since no investigation
  finding supports overriding any of the 6 worlds' isolation contracts; (b) close as
  already-satisfied by prior work — **recommended**, since the roadmap's Phase 3 FACTION-half intent
  is fully met by the 11/17 coverage already in place; (c) fold into the roadmap's Phase 5 Coverage
  Decision Gate — plausible alternative if that gate is designed to formally record "coverage
  complete, no further action" decisions corpus-wide. This investigation defers the final choice
  between (b) and (c) to the Plan phase, since it depends on Phase 5's exact framing (not read as
  part of this investigation — out of this ticket's Related Docs list).

## Anti-Drift Hazards

- **Do not add `faction_tension_overrides` to `crowded_frontier` or `resource_dense_basin`** even
  though both are mechanically capable of carrying it (both populate faction-bearing modules) — this
  would silently collapse the stress tier's single-variable isolation contract and invalidate the
  gap-1/gap-2 evidentiary purpose those worlds were authored for.
  `docs/simulation_quality/corpus_tier_taxonomy.md`'s "do not touch" framing for tier-purity is a
  hard design constraint, not a soft default.
  Do not add `faction_tension_overrides` to `unit_information_source` or `unit_selfmodel_pilot` —
  both explicitly document `faction_tension_overrides` absence as part of their single-mechanic
  isolation design in their own `world.yaml` `description:` field; adding it would break their
  ability to cleanly attribute a future FACTION regression to a specific mechanic.
- **Do not treat `simq_routing_test` or `hero_guild_routing` as FACTION-appropriate just because
  they carry the `"faction_pressure"`/`"conflict"` `provided_features` tags** — those tags describe
  the *modules* composed (which do include faction-adjacent content like `goblin_camp_conflict`),
  not a commitment to seed compile-time tension. Both worlds' FACTION=C grade is documented as
  correct/expected, not a gap.
- **Do not conflate `initial_tension_level` presence with `faction_tension_overrides` presence** —
  every resolved world spec (`data/worlds/*/resolved/world.resolved.yaml`) shows
  `initial_tension_level` because it is a schema field on every `FactionSpec`, defaulting to `0.0`.
  Only a non-empty `faction_tension_overrides` in the *authored* `world.yaml` (or a non-zero
  `initial_tension_level` set directly in catalog content, which does not occur in this corpus) is
  genuine evidence of seeded tension.
- **Do not silently close this ticket without a Plan-phase decision recorded** — the investigation
  resolves UQ-1 but does not itself have authority to choose between "close as already-satisfied"
  vs. "fold into Phase 5 Coverage Decision Gate"; that is a scope decision for the Plan phase per
  the project workflow rule (Investigate does not silently reduce or close scope on its own).
- **If the Plan phase proceeds anyway (e.g. by finding new information this investigation missed),**
  it must re-run the same live-`world.yaml`-grep verification step, not trust this document's table
  as permanently current — corpus content can change between ticket pickup and implementation.
