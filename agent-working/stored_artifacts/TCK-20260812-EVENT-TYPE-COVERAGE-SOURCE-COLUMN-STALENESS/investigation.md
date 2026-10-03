---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS
artifact_type: investigation
tags: [observability, documentation, economy]
---

# Investigation — TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS

## Current Behavior

`docs/simulation_quality/event_type_coverage.md` is a hand-maintained table auditing which code
path derives each SimQ-scored event type. Its `source` column was written when
`EventExtractor.extract()` (`src/observability/event_extractor.py`) was the only derivation path.
Since the four push-shaper migrations (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`,
`TCK-20260806-PUSH-CUTOVER-PHASE2`, `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`,
`TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP`/`TCK-20260807-REJECTION-CASCADE-TICK-PUSH-
MIGRATION-GAP`), most of these event types are now derived — in the live, default configuration —
by a shaper class in `src/observability/event_shapers.py`, with `event_extractor.py`'s original
loops surviving only as flag-gated rollback paths. The doc's `source` column was never
systematically updated at any of these cutover points; `resource_harvested`/`item_crafted` (lines
109-110) are the sole rows already corrected, by `TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-
REGRESSION`'s Verify phase.

### The 4 shaper registries (re-derived fresh from current source, not the ticket's own list)

All 4 registries are populated and all 4 gating flags default `"ON"` — confirmed directly in
`src/observability/event_shapers.py` and `src/observability/event_extractor.py`, not assumed:

| Registry | Line | Domains → classes | Gate (default) |
|---|---|---|---|
| `SHAPER_REGISTRY` | `event_shapers.py:944` | `combat`→`CombatShaper`, `economy`→`EconomyShaper`, `faction`→`FactionShaper` | `ENABLE_PUSH_EVENT_SHAPERS` (kernel.py:930, extractor.py:134 both read default `"ON"`) |
| `PHASE2_SHAPER_REGISTRY` | `event_shapers.py:1877` | `strategy`→`StrategyShaper`, `progression`→`ProgressionShaper`, `world_dynamics`→`WorldDynamicsShaper`, `social`→`SocialShaper`, `deferred_instrumentation`→`DeferredInstrumentationShaper` | `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (`run_shadow_shapers()`:1920-1921, default `"ON"`) |
| `QUEST_SHAPER_REGISTRY` | `event_shapers.py:1743` | `narrative`→`NarrativeShaper` | `ENABLE_PUSH_EVENT_SHAPERS_QUEST` (default `"ON"`, `run_shadow_shapers()`:1957-1958) |
| `AGENCY_SHAPER_REGISTRY` | `event_shapers.py:1860` | `agency`→`AgencyShaper` | `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` (default `"ON"`, `run_shadow_shapers()`:1979-1980) |

`run_shadow_shapers()` (`event_shapers.py:1886-1995`) also computes `conservation_law_verified`
directly (lines 1932-1938) — a cross-shaper aggregation, not any single domain shaper's job — as
part of the Phase-2-gated block, so its correct `source` label is the function itself, not a class
name.

I re-derived the full event_type → shaper mapping by grepping every `event_type="..."` literal in
`event_shapers.py` and locating each inside its owning `class` block (verified line ranges, not
assumed from docstrings alone). Full method in Anti-Drift Hazards.

## §1.1 Direct Emission table — stale rows found (70 of the table's ~81 rows)

Grouped by the shaper now actually deriving them (all live-by-default). Format:
`event_type` (doc line) — current `source` value → correct value.

**CombatShaper** (5 rows) — correct value `event_shapers (CombatShaper)`:
| event_type | line | current source |
|---|---|---|
| `hero_death_unrecorded` | 97 | `event_extractor` |
| `combat_damage` | 98 | `CombatDamageEvent` — **not literally "event_extractor" but equally stale**: `CombatDamageEvent` (the class) is only constructed in `event_extractor.py:451`, the rollback path (`if not _push_shapers_active`); the live path (`CombatShaper.shape()`, line 231) builds a plain `SimulationEvent(event_type="combat_damage", ...)`, not a `CombatDamageEvent` instance. Naming a class that only exists on the dead-by-default path is the same class of staleness. |
| `combat_initiated` | 99 | `event_extractor` |
| `near_death_survival` | 100 | `event_extractor` |
| `hazard_drain_applied` | 143 | `event_extractor` |

**StrategyShaper** (13 rows) — correct value `event_shapers (StrategyShaper)`:
`route_selected`(103), `action_executed`(104), `self_model_updated`(105), `belief_assimilated`(106),
`belief_updated`(107), `cooperation_event`(108, scored by `SocialScorer` but derived inside
`StrategyShaper`, deliberately colocated per its own docstring and parity ledger `SOC-239` — worth
a one-line doc note so a reader doesn't assume a `SocialShaper` typo), `defer_with_reason`(119),
`route_family_first_use`(120), `lead_certainty_updated`(123), `paid_info_changed_goal`(125),
`belief_stale`(126), `decision_diverged_by_belief`(127), `decision_divergence_detected`(128),
`lead_certainty_changed`(145).
All current source = `event_extractor`.
**Caveat for `route_selected`/`action_executed`**: `StrategyShaper` reads
`update.entity_updates[eid].property_updates["last_routing_family"]` (event_shapers.py:751) — the
same field the doc's own note says has had its sole writer deleted
(`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`), so both now construct 0 events per the doc's own
2026-08-13 re-verification note. The `source` column question is "which code path derives this in
the live config," independent of hit count — it should still be corrected to
`event_shapers (StrategyShaper)`; the existing dead-writer note stays, just gets a short
"(shaper-side, not extractor-side)" clarification so the two facts don't read as contradictory.

**EconomyShaper** (6 rows) — correct value `event_shapers (EconomyShaper)`:
`shop_transaction`(111), `trade_executed`(112), `quest_reward_dispensed`(113),
`gold_sink_fired`(114), `paid_information_transaction`(115), `paid_info_transaction`(116).
All current source = `event_extractor`.

**FactionShaper** (8 rows) — correct value `event_shapers (FactionShaper)`:
`alliance_proposed`(136), `resource_seized`(137), `diplomatic_transition`(164),
`alliance_accepted`(165), `territory_ownership_changed`(166), `faction_tension_delta`(167),
`war_declared`(168), `military_conflict_resolved`(169). All current source = `event_extractor`.

**ProgressionShaper** (7 rows) — correct value `event_shapers (ProgressionShaper)`:
`xp_granted`(101), `level_up`(102), `skill_unlocked`(129), `trait_expressed`(130),
`pillar_trait_unlocked`(131), `progression_conversion_applied`(132),
`progression_plateau_detected`(133). All current source = `event_extractor`.

**WorldDynamicsShaper** (14 rows) — correct value `event_shapers (WorldDynamicsShaper)`:
`demographic_mortality`(95), `demographic_birth`(96), `ecology_cycle_completed`(139),
`spawn_cadence_fired`(140), `threat_evolved`(141), `building_sabotaged`(144),
`region_trauma_delta`(157), `region_ownership_changed`(158), `region_transformed`(159),
`calamity_spawned`(160), `boss_spawned`(161), `narrative_milestone`(162),
`raid_party_spawned`(163), `world_emergence_event`(170). All current source = `event_extractor`.

**DeferredInstrumentationShaper** (3 rows in §1.1 + 1 in §5) — correct value
`event_shapers (DeferredInstrumentationShaper)`:
`node_recharged`(142), `resource_node_depleted`(156), `faction_extinct`(171) — all §1.1, current
source `event_extractor`. Plus **§5** `resource_node_regenerated`(line 349, source column
`event_extractor`) — same shaper class also derives this one (event_shapers.py:1369); §5's table
header is `source` too, same staleness class.

**SocialShaper** (10 rows) — correct value `event_shapers (SocialShaper)`:
`social_memory_created`(146), `contract_milestone_completed`(147), `group_joined`(148),
`group_expelled`(149), `reputation_delta`(150), `contract_offer_created`(151),
`contract_offer_accepted`(152), `contract_completed`(153), `contract_lapsed`(154),
`contract_expired_offer`(155). All current source = `event_extractor`.

**AgencyShaper** (2 rows) — correct value `event_shapers (AgencyShaper)`:
`commitment_abandoned`(121), `rejection_cascade_tick`(122). Both current source = `event_extractor`.

**`run_shadow_shapers()` aggregation** (1 row) — correct value
`event_shapers (run_shadow_shapers)`:
`conservation_law_verified`(117), current source = `event_extractor`. Not a per-domain shaper
class — computed directly inside `run_shadow_shapers()` by checking the Phase-1 shapers' combined
output (event_shapers.py:1932-1938).

## Already correct — confirmed, excluded from the fix list

- `resource_harvested`(109) / `item_crafted`(110) — `event_shapers (EconomyShaper)`, fixed by
  `TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`. Re-read: still correct, no
  regression.
- `faction_trajectory_stagnant`(138) — already `event_shapers (FactionShaper)`, correct.
- `combat_resolved` (§3.10) — already `event_shapers.py's CombatShaper`, correct.
- `combat_engagement_started`/`combat_engagement_ended` (§5, lines 369-370) — already
  `event_shapers (CombatShaper)`, correct.

## Genuinely NOT migrated — confirmed accurate as `event_extractor`, no change

Verified by grepping every `event_type=` literal in `event_shapers.py` (67 distinct strings found,
full list cross-referenced above) — none of the following event_type strings appear anywhere in
that file, so their `event_extractor` label is still correct:
`capability_growth_stalled`(134), `life_arc_incoherent`(135) — new, never had a shaper.
`lead_contradiction_resolved`(124) — its own producer, `lead_contradiction.py`, not
`event_shapers.py`. `biological_state_changed`, `stamina_changed`, `wound_sustained`/
`wound_healed`/`scar_gained`, `attribute_changed`, `item_equipped`/`item_unequipped`,
`equipment_durability_changed`, `entity_role_changed`/`entity_faction_changed`, `recipe_learned`,
`skill_cooldown_started` (all §5) — none migrated; entity-vitals/attributes/equipment/identity
observability work (`TCK-20260808-ENTITY-*`) added these directly to `event_extractor.py`, after
the push-shaper migrations, and never routed them through a shaper. `movement`, `lifecycle`
(spawn), `LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `OLD_DEBT_COLLECTED`, `REFINED_UPDATE`,
`GovernorModeChanged`, `TICK_END`, `InvariantViolation` (unknown law), `belief_contradiction`,
`plan_revision`, `DEFLATION_RISK`/`INFLATION_SPIRAL`/`ECONOMIC_COLLAPSE`/`GOLD_HOARDING` (all §5) —
correctly non-shaper. `scenario_objective_progressed`(118), `chronicle_entry_created`(172),
`quest_completed`(173, the campaign-runner one, distinct from `quest_event`),
`scenario_objective_completed`(174), `scenario_stalled`(175) — campaign/scenario-gated, never in
scope for any of the 4 shaper registries.

## §3 Engine Emission Gaps table — same staleness, duplicate citations

§3.2-§3.9's "resolved by" column repeats several §1.1 event types with their own, separately-stale
`event_extractor.py` citation (these sub-tables predate the migrations and were never touched by
them):
- §3.2 `decision_divergence_detected` (line 237) → `StrategyShaper`
- §3.3 `lead_certainty_updated`(245) → `StrategyShaper`; `paid_info_changed_goal`(247) →
  `EconomyShaper`; `belief_stale`(248) → `StrategyShaper`; `decision_diverged_by_belief`(249) →
  `StrategyShaper`. (`lead_contradiction_resolved`(246) stays `lead_contradiction.py` — correct.)
- §3.4 `paid_info_transaction`(257) → `EconomyShaper`; `conservation_law_verified`(258) →
  `run_shadow_shapers`.
- §3.6 `skill_unlocked`(274), `trait_expressed`(275), `pillar_trait_unlocked`(276),
  `progression_conversion_applied`(277), `progression_plateau_detected`(278) → `ProgressionShaper`.
- §3.7 `alliance_proposed`(286), `resource_seized`(287) → `FactionShaper`.
- §3.8 `social_memory_created`(295), `contract_milestone_completed`(296) → `SocialShaper`.
- §3.9 `ecology_cycle_completed`(304), `spawn_cadence_fired`(305), `threat_evolved`(306) →
  `WorldDynamicsShaper`; `node_recharged`(307) → `DeferredInstrumentationShaper` (not
  `WorldDynamicsShaper` — verified by exact class-boundary line check, easy to get wrong since
  it's grouped with the other 3 WORLD-DYNAMICS rows in this same table row visually).

Plan should decide whether to keep §3 as a frozen historical record (its own header calls these
"previously listed gaps", already resolved) or apply the same correction — recommend correcting it:
the "resolved by" column makes the identical factual claim as §1.1's `source` column and the doc's
own §6 Maintenance Notes treats §3 as a live reference ("primary expansion surface"), not an
archive.

## Naming convention for Plan

Established precedent (already-fixed `resource_harvested`/`item_crafted` rows): `event_shapers
(<ShaperClassName>)`. Recommend extending verbatim to all rows above, with two special cases:
1. `conservation_law_verified` has no owning shaper class — use `event_shapers
   (run_shadow_shapers)` (the function name, matching how the doc already names bare files/modules
   for non-shaper sources like `lead_contradiction.py`, `engine/scenario_runtime`).
2. Rows whose scorer domain differs from the deriving shaper's own domain (`cooperation_event`:
   `SocialScorer` but `StrategyShaper`; `paid_info_changed_goal`: `InformationScorer` but
   `EconomyShaper`) should keep a one-clause parenthetical in the `notes` column flagging the
   cross-domain colocation, so a future reader doesn't file it as a typo.

## Mechanics / Engine Constraints

No mechanics-bible or engine-contract law governs this doc's own bookkeeping — it is a derived
observability audit artifact, not a simulation-law source. `docs/engine/kernel.md`'s
observability phase description and the shaper/extractor mutual-exclusion contract
(`_push_shapers_active`-style flags) are the actual behavioral contract this doc is auditing;
this ticket does not touch that contract, only the doc's description of it.

## Docs Requiring Update

- `docs/simulation_quality/event_type_coverage.md`: ~70 `source` column corrections in §1.1, ~15
  duplicate "resolved by" corrections in §3.2-§3.9, 1 `source` correction in §5
  (`resource_node_regenerated`), plus the `last_verified` frontmatter field bump.
- `docs/parity_ledger/strategic_cognition.yaml`: entries `STRAT-240` (`lead_certainty_updated`),
  `STRAT-241` (`belief_stale`), `STRAT-242` (`decision_diverged_by_belief`/
  `decision_divergence_detected`) each independently cite `event_extractor.py` in `v2_evidence`
  with no cross-reference or update note to `STRAT-247` (the correct, already-updated
  `StrategyShaper` cutover entry in the same file) — same-ledger factual divergence.
- `docs/parity_ledger/world_dynamics.yaml`: entries `WORLD-108` (`ecology_cycle_completed`) and
  `WORLD-109` (`spawn_cadence_fired`/`node_recharged`/`threat_evolved`) cite `event_extractor.py`
  with no cutover correction, while this file's WORLD-115-class entry (referenced from
  `faction.yaml` FAC-013) already documents the `WorldDynamicsShaper` migration elsewhere.
- `docs/parity_ledger/social_narrative.yaml`: entries `SOC-233` (`cooperation_event`/
  `reputation_delta`), `SOC-234` (`contract_completed`/`contract_lapsed`/`contract_expired_offer`),
  `SOC-235` (`diplomatic_transition`/`alliance_accepted`/`war_declared`/
  `military_conflict_resolved`/`territory_ownership_changed`/`faction_tension_delta`/
  `faction_extinct`), `SOC-236` (`alliance_proposed`/`resource_seized`/`paid_info_transaction`/
  `conservation_law_verified`), `SOC-237` (`social_memory_created`), `SOC-238`
  (`contract_milestone_completed`) all independently cite `event_extractor.py` with no cutover
  note, even though `SOC-239` (cooperation_event/StrategyShaper) and `SOC-240` (the 10-event
  SocialShaper aggregate) already exist in the same file and correctly name the live shaper
  terminus for several of the same event types.
- `docs/parity_ledger/progression.yaml`: entries `PROG-114` (`skill_unlocked`), `PROG-115`
  (`trait_expressed`/`pillar_trait_unlocked`), `PROG-116` (`progression_conversion_applied`/
  `progression_plateau_detected`) cite `event_extractor.py` only, while `PROG-117` (same file)
  already documents the `ProgressionShaper` cutover for the identical events.
- `docs/event_ledger/entity.yaml`: **NOT out of scope — shares the staleness.** See below.

`docs/parity_ledger/faction.yaml`, `combat_movement.yaml`, `town_resource.yaml`,
`infrastructure.yaml`, `substrate.yaml` were checked and found already correctly updated (each has
a domain-aggregate entry with its own `update_2026_08_0N` cutover note naming the live shaper) —
no changes needed there. `substrate.yaml`'s entries only cover vitals/attributes/equipment/identity
events, none of which are shaper-migrated, so they are already accurate as-is.

## `docs/event_ledger/entity.yaml` — ticket's own "likely out of scope" assumption is wrong

The ticket's Out of Scope section says this file is excluded "unless Investigate finds it shares
the same staleness." It does:
- `ENTITY-003` (`EntityUpdate.combat`, line 28-31): `evidence: "src/observability/
  event_extractor.py (multiple sites)..."` for `event_types: [combat_damage, combat_initiated,
  near_death_survival, ..., hazard_drain_applied, ...]` — same staleness as the doc's Combat rows.
- `ENTITY-007` (`EntityUpdate.identity`, line 55-60): `evidence` cites `event_extractor.py` for
  `event_types` including `skill_unlocked`, `trait_expressed`, `pillar_trait_unlocked`, `level_up`
  — all now `ProgressionShaper`-derived.

This file uses an `evidence` field, not a `source` column, and has a different schema
(`docs/event_ledger/entity.yaml`'s own header comment says it "mirrors
`docs/parity_ledger/schema.json`'s discipline", not `event_type_coverage.md`'s table format), so
fixing it is a distinct edit, not a drop-in reuse of the §1.1 table fix. Flagging as an open
question for Plan: fix inline in this ticket (the ticket's own conditional clause permits it) or
file a sibling follow-up ticket scoped to `entity.yaml` specifically. Given this ticket's Type is
`chore`/doc-only and the fix is mechanically identical (swap `event_extractor.py` citation for the
shaper class name in the relevant `evidence` strings), recommend fixing inline — small, same
session, avoids yet another "flagged, not fixed" deferral in this same staleness class (this would
be the 4th time; see ticket's own Request Summary).

## Parity Ledger Overlap

All entries named above under "Docs Requiring Update" are `status: verified`, no entry is `P0`
requiring a fresh passing `test_path` as a result of this ticket (no behavior change, `test_path`
values remain valid regardless of which code path is named in prose) — this is a pure textual
correction of `v2_evidence`/`text` staleness, not a status change. None of the 4 shaper-related
`P0` entries checked (`FAC-013`, `COMB-295`, `TOWN-190`, `SOC-240`, `PROG-117`) need any change —
they are already correct.

## Prior Work

- `stored_artifacts/TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION/` — precedent for the
  exact fix pattern (`event_shapers (EconomyShaper)` naming) and for finding+fixing the same
  staleness class twice within one parity ledger entry (`STRAT-246`).
- `tickets/done/TCK-20260807-QUEST-EVENT-PUSH-MIGRATION.md` — first ticket to flag this doc's
  staleness for COMBAT/FACTION/QUEST/AGENCY rows, without fixing it (this is the "flagged twice,
  fixed never" history this ticket exists to close out).
- `tickets/done/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION.md`,
  `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC.md`,
  `TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP.md`,
  `TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP.md` — the 4 migrations that introduced
  each shaper registry, cited above for line numbers and gate names.

## Risks and Open Questions

- **`docs/event_ledger/entity.yaml` scope decision** (see above) — blocks nothing technically, but
  Plan must explicitly decide in-scope vs. follow-up ticket before Implement starts, since the
  ticket's own Out of Scope section makes this conditional on Investigate's finding.
- **§3 Engine Emission Gaps table** — recommend correcting (see rationale above) but this is a
  judgment call Plan should confirm, since §3's own framing ("previously listed gaps... resolved
  by") reads as a closed historical record in a way §1.1 doesn't.
- **§1.2/§1.3 translation tables have no `source` column at all** — structurally out of this
  ticket's scope (nothing to fix), but worth flagging as a discovery: `CombatShaper` emits
  `entity_killed` directly (event_shapers.py:307), the post-translation contract type, not the raw
  `combat_kill` engine event_type §1.2 documents translating. In the live default config, the
  `combat_kill → entity_killed` `_TRANSLATE_SIMPLE` mapping (line 181) is now exercised only by
  the flag-gated rollback path, not by the shaper path. This doesn't need a doc fix (no source
  column exists there) but Plan/reviewers should not be surprised if a future audit finds this row
  "unreachable in default config" — it's an artifact of the same migration, not a new bug.
- The exact wording for the `route_selected`/`action_executed` dead-writer caveat (both a stale
  `source` AND a separately-already-noted 0-hit fact) needs care so the corrected row doesn't read
  as internally contradictory — draft language proposed above under StrategyShaper.

## Anti-Drift Hazards

- **Do not conflate "derives" with "delivers".** All 4 gates default `ON`, so in the *default*
  configuration every row above is both derived AND delivered by its shaper. But the `source`
  column's job is naming the derivation path, and `event_extractor.py`'s branches are NOT deleted
  — they remain the real, tested rollback path when a flag is set OFF. The doc fix must not imply
  `event_extractor.py`'s code is dead/removable; several existing rows already model this
  correctly (`resource_harvested`'s note: "`event_extractor.py`'s own loop is now the flag-gated
  ... rollback path, not the live source" — reuse this phrasing, don't just swap the bare source
  value with no context, or a future reader loses the rollback-path fact entirely).
- **`node_recharged` is `DeferredInstrumentationShaper`, not `WorldDynamicsShaper`** — easy
  mistake since §3.9's own table visually groups it with 3 `WorldDynamicsShaper` rows
  (`ecology_cycle_completed`/`spawn_cadence_fired`/`threat_evolved`). Verified by exact
  class-boundary line ranges in `event_shapers.py`, not by proximity in the doc.
  `resource_node_depleted`/`resource_node_regenerated` are the same shaper (`DeferredInstrumentat
  ionShaper`), confirming the pattern — the 3 "resource_node_*"-prefixed events plus
  `faction_extinct` are grouped together in source code (`event_shapers.py:1314-1426`) even though
  they scatter across 3 different SimQ pillars in the doc (World, World, World, Faction).
- **`cooperation_event`/`paid_info_changed_goal` cross-domain colocation** — don't "fix" these into
  `SocialShaper`/`InformationScorer`-matching shaper names; the actual code deliberately colocates
  them elsewhere (documented rationale in both the shaper class docstrings and parity ledger
  `SOC-239`). Getting this "right" by analogy to the scorer name would introduce a NEW staleness
  bug, the opposite of this ticket's purpose.
- **No behavior change.** This is a pure prose/table-value edit. Any implementer tempted to "also
  fix" the `route_selected`/`action_executed` dead-writer gap, the `combat_kill` translation-table
  reachability finding, or any `0`-hit calibration count is scope-creeping into work this ticket's
  own Out of Scope section explicitly excludes.
- **`make knowledge-index-update`** must run after this ticket's doc edits per CLAUDE.md's After
  Work rule (docs/ files changed) — easy to forget on a "just a table edit" ticket.
