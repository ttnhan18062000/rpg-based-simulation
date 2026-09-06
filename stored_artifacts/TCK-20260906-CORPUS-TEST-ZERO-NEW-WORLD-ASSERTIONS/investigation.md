---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS
date: 2026-09-06
---

# Investigation: TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS

## Current Behavior (file:line refs) — per idea, re-verified against real code

- **Idea 4**: `tests/simulation_quality/test_grade_regression.py` + `tests/simulation_quality/fixtures/grade_anchors.json`
  already pin COMBAT (and every other pillar) for `urban_political_seed42_200t` (COMBAT grade=A,
  score=1.505) and `simq_routing_test_seed42_500t`. This regression infrastructure already exists
  and already runs — **idea 4 needs zero new authoring**, only a citation confirming the coverage
  already satisfies its own AC.
- **Idea 10**: `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py:221-252`)
  resolves `heir_id = entity.lifecycle.heir_entity_id`, writes `heir_entity_id_set`, and combines
  `entity.inventory.items` + heirloom stacks into `all_transfer_items` onto the heir — real,
  single-tick, deterministic.
- **Idea 13**: `ContractKind.TEAM_UP` (not a class named `TeamUpInvite` — that identifier does not
  exist anywhere in `src/`) routed through `SocialAppraisalSystem.appraise_contract()` ->
  `_appraise_team_up()` (`appraisal.py:331-346`): `trust_score >= 0.6` -> `ACCEPTED`, else
  `CANCELLED`. Real action: `execute_team_up` (`src/engine/domain/core_actions.py:147`).
  `ResourceTransferIntent` (idea 13's other half) is real and widely used
  (`src/world/regional_sovereignty.py`, `src/engine/combat.py`, etc.).
- **Idea 14**: `SpeciesDefinition.intelligence_tier: str` (`src/content/schema.py:142-152`), a
  content-level field validated against `natural_traits` containing `tool_user` (per this
  session's own M2-scoping "known gotcha" — anchor via `natural_traits`, not
  `attribute_tendencies.intelligence`).
- **Idea 22**: `SocialBond.role: RelationshipRole` (`src/core/models/social.py:14-20`), real enum
  field on every bond.
- **Idea 30**: `ItemInstance.owner_history: List[str]` / `acquired_method: AcquiredMethod`
  (`src/core/models/inventory.py:72-74`), appended via `ItemInstanceUpdate.owner_history_append`
  through `apply.py:259-262` — real, already-shipped durable field.
- **Idea 33 — CORRECTION, real gate is NOT "familiarity >= 0.6".** `execute_propose_marriage`
  (`core_actions.py:401-453`) builds a `temp_contract` (`ContractKind.MARRIAGE`), calls
  `appraise_contract()` -> `_appraise_marriage()` (`appraisal.py:372-382`), which uses **only the
  shared prelude** (`trust_score < 0.2` or `bond.sentiment < -0.8` -> `CANCELLED`; betrayal-history
  check) — no marriage-specific threshold, no `familiarity` term at all, and it **always accepts**
  once the prelude passes. The real `0.6` constant belongs to idea 13's `_appraise_team_up`
  (`trust_score >= 0.6`), not marriage — the ticket's own citation conflated the two sibling
  contract kinds in the same file. Also: `MarriageState` is created directly with
  `status=MarriageStatus.ACCEPTED` in one action — `MarriageStatus.PROPOSED` exists as an enum
  value but is never actually used as a durable `MarriageState.status`; there is no
  PROPOSED->ACCEPTED transition to observe.
- **Idea 36/40 — CORRECTION, reuses ticket 4's own already-confirmed finding.** `orc_clan_territory.yaml`
  (`data/content/world_modules/`) defines only `factions: ["orc_clan"]` — zero `clans:`/`ClanState`
  content. No registered corpus world has ever carried real Clan content (re-confirmed directly,
  same as `TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS`'s own investigation.md). "Retarget
  existing orc_clan_territory content into a real ClanState" has no basis in real content structure.
- **Idea 39**: `IdentityUpdate.faction_set` (M6, `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`) —
  confirmed zero references to `identity.faction`/`faction_set` anywhere in
  `src/systems/social_systems/relationships.py`, so `SocialBond` entries are never touched by a
  faction change — the "does NOT auto-degrade" assertion is real and directly verifiable.
- **Idea 44 — CORRECTION, `settlement_capacity`/`FULL_SETTLEMENT`/`CAMP_ONLY` do not exist as real
  identifiers anywhere in `src/`.** Zero grep hits. The real classification mechanism is
  `PlaceKind` (idea 66, `src/core/state.py:329-337`: `CITY`, `CAMP`, `NEST`, `LAIR`, `RUIN`,
  `DUNGEON`, `LANDMARK`) plus `PlaceState`. The epic doc's own text already discloses the real
  caveat: `goblin_camp_conflict`'s region never opted into `creature_kind`, so `WorldCompiler.compile()`
  constructs no `CampState`/`Place(kind=CAMP)` for it at all — a real settlement/non-settlement
  split is observable via `PlaceKind` presence (a real `Place(kind=CITY)` for
  `frontier_village_core`'s region vs. no Place, or a non-CITY Place, for `goblin_camp`'s region),
  not via literal `settlement_capacity`/`FULL_SETTLEMENT` constants that were never shipped.
- **Idea 49 — refined framing, mechanism confirmed real but the "gate" is availability, not a live
  proximity check.** `mountain_pass.yaml`'s `mountain_pass_zone` region defines
  `resources: {iron_vein: 4, frost_shard_cluster: 2}` — real `ResourceNodeState` placement, only
  in that region. `frost_shard` (the crafting material) can only be obtained by harvesting a
  `frost_shard_cluster` node, and those nodes exist only in `mountain_pass_zone` — the "place-tied"
  constraint is a natural consequence of resource-node placement (an entity must physically travel
  to and harvest at that region to ever hold `frost_shard` at all), not a separate proximity check
  gating the crafting action itself. No such live proximity-gate code exists in
  `src/systems/*/crafting*.py`/`harvest*.py` — confirmed via grep, none found.

## Corrections summary (5 real corrections found, all disclosed, none forced)
1. Idea 33: real gate is the shared trust-prelude only, not `familiarity >= 0.6`; the `0.6` figure
   actually belongs to idea 13's Team-Up gate. No PROPOSED->ACCEPTED transition exists — direct
   single-action ACCEPTED creation only.
2. Idea 36/40: no corpus world has real `ClanState` content (same finding as the immediately-prior
   M9 sibling ticket) — a hand-seeded Unit-tier proof is used instead of "retargeting" nonexistent
   content.
3. Idea 44: `settlement_capacity`/`FULL_SETTLEMENT`/`CAMP_ONLY` are descriptive framing in the epic
   doc, not real code identifiers — the real, assertable mechanism is `PlaceKind`.
4. Idea 49: the "gate" is resource-node placement/harvest availability, not a live crafting-time
   proximity check — assert on obtaining `frost_shard` only via that region's node, not a
   crafting-time location guard that does not exist.
5. Idea 13's real class name is `TeamUpInvite`-as-described-in-the-ticket -> actually
   `ContractKind.TEAM_UP` through the same general contract-appraisal pipeline every other social
   contract kind uses (matches idea 33/54's own already-confirmed shared-pipeline shape).

## Docs Requiring Update
None. All 11 sub-items exercise already-shipped, already-documented mechanisms with no behavior
change — test-only ticket, matching every other M9 sibling ticket's own precedent for pure
assertion-authoring work.

## Parity Ledger Overlap
None — no `src/` production code changes, `behavior_changed=false`. SOC-268 (idea 54's own entry,
referenced for the shared appraisal-pipeline shape), STRAT-270/SOC-273 (idea 39's M6 entries) are
unaffected, only re-confirmed.

## Prior Work
- `TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS` (this same M9 batch's immediately-prior sibling) —
  established the exact "hand-seeded ClanState through a real Kernel.tick_once()" precedent this
  ticket's own idea 36/40 sub-test reuses directly, and independently found the same
  `orc_clan_territory` faction-not-clan finding.
- `tests/simulation_quality/test_age_tier_transitions_corpus.py` (M9 ticket 2) — the Unit-tier
  hand-seeded-`AuthoritativeState`-through-`Kernel.tick_once()` template most of this ticket's
  sub-tests follow.
- `tests/unit/social/test_clan_appraisal.py`, `tests/unit/strategic/` — existing pure-function
  precedent for the appraisal-pipeline-shaped assertions (marriage/team-up/clan).

## Risks and Open Questions
None outstanding — all 5 corrections above are evidence-based, not judgment calls requiring human
input.

## Anti-Drift Hazards
- Do not assert a `familiarity >= 0.6` marriage gate — it does not exist; use the real trust-prelude
  gate instead.
- Do not build a new corpus world for idea 36/40 — reuse the sibling ticket's hand-seeded precedent.
- Do not invent `settlement_capacity`/`FULL_SETTLEMENT`/`CAMP_ONLY` fields — assert on real
  `PlaceKind` presence/absence instead.
- Do not assert a live crafting-time proximity check for idea 49 — assert on resource-node
  placement/harvest availability instead, the real mechanism.

## Addendum — 3 further corrections found during Implement (beyond the 5 above)
6. **Idea 14**: `intelligence_tier`'s only real consumer is `RoleModelImitationService.compute_imitation_fidelity()`
   (imitation-fidelity multiplier), not a coming-of-age/Progression-Planner exclusion gate.
7. **Idea 22**: `BondUpdate.role_set`/`SocialBond.role` has zero real production writers anywhere
   (confirmed via grep) — the real grudge>=3.0 classification mechanism is
   `SocialMemoryService.check_nemesis_promotion()` promoting to `SocialComponent.nemesis_ids`.
8. **Idea 44**: running the real compiler refined the epic doc's own caveat — `goblin_camp_conflict`
   DOES compile a real `Place(kind=CAMP)`, with `maturity=None` (no live CampState machinery), not
   "no Place at all."

Also: idea 49's material is really named `frost_shard_cluster`, not `frost_shard`; idea 30's
`ItemInstanceService.maybe_create_instance()` has zero real production callers today
(`ENABLE_ITEM_INSTANCE_HISTORY` defaults OFF), confirmed via grep.
