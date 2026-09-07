---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-09-07
---

# Chapter 7: Social & Political Dynamics

This chapter describes the "Social Laws" governing trust, contracts, reputation, relationship
history, and party/group coordination — how entities judge, bond with, and organize around each
other. Source: `src/systems/social_systems/` (appraisal.py, contracts.py, relationships.py,
guilds.py, party.py, party_composition.py, memory.py, group_service.py, reputation.py,
party_lifecycle.py), `src/domains/commitment/reputation.py`.

**Provenance note:** this chapter promotes and corrects `docs/simulation/social_systems_contract.md`
(TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER). Every formula below was independently re-verified
directly against source, not transcribed from that doc unverified — five of its sections (Reputation,
the Appraisal trust formula, Contracts, Guilds, Party) were found to materially diverge from real
code and are corrected here; see `docs/simulation/social_systems_contract.md`'s own top-of-file
correction note for the itemized list. The remaining sections (Relationships/clamp table, Social
Memory, Party Composition) were confirmed accurate and are promoted with only presentation changes.

**Caller/callee direction:** the cooperation and commitment domains (`src/domains/cooperation/`,
`src/domains/commitment/`) make decisions about social posture and produce `ContractState`/
`BlockerState`/`PublicReputationProfile` outputs; social systems apply those decisions as durable
state changes. Social systems do not call back into a domain.

---

## 1. Trust Appraisal & Social Contracts

`SocialAppraisalSystem.appraise_contract()` (`appraisal.py`) evaluates every social contract offer.

### Trust Score Pipeline
The trust score is computed in one of two ways, then two hard-reject gates apply before kind-specific
dispatch:

1. **Private bond override** — if a `SocialBond` exists between the entities: `trust_score =
   (bond.sentiment + 1.0) / 2.0` (sentiment −1.0..1.0 mapped to 0.0..1.0). Private sentiment always
   overrides the blended fallback below.
2. **Blended fallback** (no bond) — three additive terms:
   ```
   public_trust  = source_entity.social.public_reputation / 2.0        # 0.0-1.0
   history_trust = entity.social.trust_history.get(source_id, 0.5)     # 0.0-1.0 (defaults neutral)
   clan_trust    = clans[clan_id].clan_reputation / 2.0 if clan_id else 0.5

   trust_score = public_trust * 0.7 + history_trust * 0.3 + (clan_trust - 0.5) * 0.2
   ```
   The `clan_trust` term (`CLAN_INFLUENCE_WEIGHT = 0.2`) is a guilt-by-association signal (idea 54,
   `TCK-20260904-CLAN-REPUTATION-ASSOCIATION`) — it is exactly `0.0` at the neutral/no-clan default
   (`clan_trust == 0.5`), so it strictly extends the older two-term formula rather than reweighting it.
3. **Hard-reject gates**, evaluated after the score above: `trust_score < 0.2` **or**
   `bond.sentiment < -0.8` → `CANCELLED, TOTAL_DISTRUST`; else if `betrayal_count > 0 and trust_score
   < 0.4` → `CANCELLED, BETRAYAL_HISTORY`.

### Contract Kinds
`ContractKind` has 10 real members: `RECRUITMENT`, `LOAN`, `PROTECTION`, `MERCHANT`, `POSITION_SWAP`,
`TEAM_UP`, `PAID_INFORMATION`, `TEACH`, `MARRIAGE`, `CLAN`. Each routes through the trust pipeline
above before kind-specific dispatch:

| Kind | Special logic |
|---|---|
| RECRUITMENT | Social fatigue check; party-commitment check; employment cost evaluation |
| LOAN | Simple trust threshold; no counter-terms |
| POSITION_SWAP | Spatial proximity check; validates both parties can reach the target position |
| MERCHANT | `_appraise_trade`: `utility = price / item_value` (hard-cancel `INSUFFICIENT_INCENTIVE` if `item_value <= 0` or `utility < 0.5`); `score = trust_score * 0.4 + min(1.0, utility) * 0.6`; `>= 0.6` → ACCEPTED (`FAIR_COMPENSATION`); `>= 0.4` and `negotiation_count < 2` → COUNTERED at `price = item_value` (`HAGGLING_FOR_PAY`); else CANCELLED |
| TEAM_UP | `_appraise_team_up`: pure trust gate, no utility/pay dimension; `trust_score >= 0.6` → ACCEPTED (`TEAM_UP_ACCEPTED`), else CANCELLED (`TEAM_UP_DECLINED`) |
| PAID_INFORMATION | Always ACCEPTED once the trust/hard-cancel prelude passes — the prelude alone is the entire gate |
| TEACH | Always ACCEPTED once the prelude passes. On ACCEPTED: `IdentityUpdate(recipes_learned=[skill_id])` set directly on the student — no gold cost (trust replaces the never-enforced legacy `TRAIN_COST`; see `docs/guidelines/intentional_divergences.md` DEV-007) |
| MARRIAGE | Always ACCEPTED once the prelude passes — no utility/risk model, no `familiarity` threshold. On ACCEPTED, a durable `MarriageState` is written on **both** parties via `StrategicUpdate.marriages_add_or_update`. Bigamy prevention and aging/duration thresholds are deliberately out of scope — see `docs/mechanics/04_strategic_cognition.md` §8 |
| CLAN | Clan-membership contract kind — see `docs/systems/faction_contract.md` for Clan formation/succession rules this chapter does not duplicate |

Every dispatch except MERCHANT/RECRUITMENT/POSITION_SWAP is a pure trust-gate — no counter-terms,
no utility model. On ACCEPTED, the resulting `ContractState` attaches to `EntityUpdate.strategic`
with **no `ResourceTransferIntent`** for TEAM_UP — no gold changes hands on party formation.

**Implementing code:** `src/systems/social_systems/appraisal.py`.

---

## 2. Relationship Dimensions & Bonds

`RelationshipService.process_update()` (`relationships.py`) applies `SocialUpdate` deltas to
`SocialComponent`, clamping every field on write:

| Field | Range | What it tracks |
|---|---|---|
| `trust_history` | −1.0 to 1.0 | Per-entity trust accumulation |
| `familiarity_history` | 0.0 to 1.0 | Interaction frequency |
| `debt_history` | −1.0 to 1.0 | Social obligation balance |
| `fear_history` | 0.0 to 1.0 | Fear from combat/intimidation |
| `grudge_history` | 0.0 to 5.0 | Accumulated harm |
| `salience_history` | 0.0 to 1.0 | How "top of mind" an entity is |
| `place_attachment` | 0.0 to 1.0 | Per-region home attachment (§3) |
| `regional_reputation` | 0.0 to 2.0 | Per-region reputation (§4) |

`SocialBond` is a richer directional relationship: `familiarity` (0.0-1.0), `sentiment` (−1.0 to
1.0), `last_interaction_tick`, `role` (`RelationshipRole`: `NEUTRAL` default / `FRIEND` / `RIVAL`).
Bond sentiment takes priority over `trust_history` wherever both exist (§1's own rule).

**`role` write path, corrected 2026-09-07 (`TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH`):** the explicit
`SocialBondUpdate.role_set` override always existed, but had **zero real (non-test) callers**
anywhere in `src/` — every live `SocialBond.role` was permanently `NEUTRAL` until this ticket, despite
a real, already-live consumer (§9's `role_affinity_term`, reached via
`AdventureRouteGenerator`'s `FORM_PARTY` route) silently always reading `NEUTRAL`. Fixed by deriving
`role` directly inside `RelationshipService.process_update()` from the bond's own resulting
`sentiment` whenever a real `sentiment_delta` is applied (already a live signal — flows from
`contracts.py`, `combat.py`, `appraisal.py`): `sentiment >= 0.8` → `FRIEND`, `sentiment <= -0.8` →
`RIVAL` (mirroring §1's own real `TOTAL_DISTRUST` bound, not an invented threshold), else the
existing `role` is left untouched (a familiarity-only or zero-`sentiment_delta` update never touches
`role` — sticky, one-crossing-per-real-sentiment-change, matching `last_interaction_tick_set`'s own
set-if-provided precedent). `role_set` itself remains a real, honored explicit override, evaluated
first. Deliberately kept independent of `nemesis_ids`/`grudge_history` (per this field's own original
design intent, `TCK-20260824-RELATIONSHIP-ROLE-FIELD`) — **`nemesis_ids`'s own promotion mechanism,
`SocialMemoryService.check_nemesis_promotion()`, was found to have zero real callers either** during
this investigation (a separate, undisclosed dormancy on an adjacent field, out of this ticket's own
scope — not corrected here, flagged for a future ticket).

**Decay:** live `SocialComponent`/`SocialBond` fields have **no passive decay of any kind** — once
set, a value stays exactly where it was left until a new interaction changes it. The only real decay
mechanism, `SocialMemoryDecay.apply_decay()` (`FRIENDSHIP_DECAY=0.40`/episode,
`GRUDGE_DECAY=0.10`/episode), operates on a separate cross-episode structure
(`SocialMemoryRecord`) and only fires at Campaign episode boundaries — see
`docs/simulation/domains/social_memory_contract.md`. It never affects live-tick `SocialComponent`
state.

`prune_low_salience()` removes history entries below a salience threshold (default 0.05) to bound
state growth — applied to `trust_history`, `familiarity_history`, `debt_history`, `fear_history`,
`grudge_history`, `salience_history` jointly (an entity dropping below threshold in `salience_history`
is pruned from all five).

**Implementing code:** `src/systems/social_systems/relationships.py`.

---

## 3. Social Memory: Place Attachment & Nemesis Promotion

`SocialMemoryService` (`memory.py`) defines two social memory effects — **correction, 2026-09-07
(`TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH`): both are dormant, not "per-tick" as previously stated.**
Direct verification found zero real (non-test) callers anywhere in `src/` of either method:

- **Place attachment:** `tick_place_attachment()` would apply `+0.001`/tick while an entity is inside
  a region's bounds (`SocialUpdate(place_attachment_delta={region_id: 0.001})`) — a real, correct,
  unit-tested pure function with no live caller wiring it into any per-tick phase.
- **Nemesis promotion:** `check_nemesis_promotion()` would promote an entity into `nemesis_ids` when
  `grudge_history[eid] >= 3.0` — likewise real, correct, and unit-tested, but with no live caller.
  `SocialComponent.nemesis_ids` can still be seeded once at entity construction
  (`V2EntityBuilder(nemesis_ids=...)`), so a non-empty `nemesis_ids` set is possible in a hand-built
  scenario, but no real per-tick gameplay path grows it from `grudge_history` today.

Per §1's own rule, `RIVAL` bond role and `nemesis_ids` are independently-driven signals by design —
`nemesis_ids` is documented as taking precedence over a stale `FRIEND` bond role in
`PartyCompositionScorer` (§9, `TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE`) on the theory that it's
backed by sustained real harm history — but since neither side of that precedence rule currently has
a live per-tick producer, this specific interaction is not yet reachable in real gameplay. Not
corrected here — this ticket's own scope was `SocialBond.role`'s write path (§2), not
`SocialMemoryService`'s; flagged for a future ticket to wire real callers, matching this chapter's
own `route_new_query` (§4) and contract-betrayal (§5) precedent for disclosing a dormant-but-real
mechanism rather than silently describing it as live.

**Distinction from other memory types:** social memory (this layer, place attachment + nemesis) is
separate from domain memory (`src/domains/memory/`, causal/spatial/temporal per-tick memory) and the
cognition knowledge model (`src/cognition/knowledge_model.py`, factual world knowledge with
freshness).

**Implementing code:** `src/systems/social_systems/memory.py`.

---

## 4. Reputation: Two Distinct Systems

**A naming collision, disclosed rather than silently conflated (this is the section
`docs/simulation/social_systems_contract.md` got materially wrong):** this codebase has **two
independently-typed fields both named "public reputation"**, updated through entirely different
mechanisms:

### 4.1 `SocialComponent.public_reputation` — the real trust/discount/inheritance scalar
A plain `float`, clamped **0.0–2.0**, read by §1's trust pipeline (`/2.0` → 0.0-1.0 baseline), the
shop-discount formula (§6, relocated from `docs/mechanics/03_economic_laws.md`), and idea 53's
birth-seed inheritance. Written only via `RelationshipService.process_update()`
(`relationships.py`), which resolves it as:
```
public_reputation = update.reputation_set if update.reputation_set is not None else
                     clamp(public_reputation + heroism_delta - notoriety_delta, 0.0, 2.0)
```
Real live writers, all confirmed via direct grep of `heroism_delta=`/`notoriety_delta=`/
`reputation_set=` call sites:

| Trigger | Delta | Source |
|---|---|---|
| Contract reaches FULFILLED | `heroism_delta = 0.05` | `contracts.py::transition_contract()` |
| Contract expiry resolved as success | `heroism_delta = 0.05` | `contracts.py::process_active_contracts()` → `resolve_contract_outcome(success=True)`, real live path |
| Contract resolved as failure | `notoriety_delta = 0.1` | `resolve_contract_outcome(success=False)` |
| Contract resolved as betrayal | `notoriety_delta = 0.5`, `betrayal_increment = 1` | `resolve_contract_outcome(betrayal=True, betrayer_id=...)` — **disclosed dead path**: `process_active_contracts()`, the only production caller, never passes `betrayal=True`; reachable only from direct unit tests today |
| Entity defects from a party group | `notoriety_delta = 2.0` | `party_lifecycle.py::check_defection()`, real live path (SOC-230) |
| Newborn's birth-seed | `reputation_set = clamp((parent_a + parent_b) / 2.0, 0.0, 2.0)` | `ReputationService.combine_public_reputation()` (idea 53, `V2EntityBuilder.birth_record()`) |
| Campaign episode carry-forward | `reputation_set = <carried-forward value>` | `src/domains/campaigns/{social_memory,orchestrator}.py` |

Separately, `heroism_score`/`notoriety_score` are **unclamped running totals** (`+= delta`, never
capped) — distinct from the clamped `public_reputation` scalar itself, tracked for narrative/scoring
purposes.

### 4.2 `PublicReputationProfile.labels` — a separate qualitative label bag
Lives at `entity.cognition.relationships.public_reputation` (`src/core/cognition.py`) — a **different
component path, different type** (`Mapping[str, float]` of named labels, not a clamped scalar).
Updated only by `ReputationUpdateService.process_witnessed_event()`
(`src/domains/commitment/reputation.py`), with exactly one real live caller
(`src/engine/quests.py:233`, on ESCORT quest completion):

| `event_kind` | Label deltas |
|---|---|
| `"successful_escort"` | `labels["reliable"] += 0.1` (each label clamped 0.0-1.0 independently) |
| `"betrayal"` | `labels["betrayer"] += 0.4`, `labels["reliable"] -= 0.3` |
| `"clear_camp"` | `labels["camp_clearer"] += 0.2`, `labels["heroic"] += 0.1` |

This function **never touches `SocialComponent.public_reputation`** — it is a purely additive labels
dictionary on a structurally unrelated component. Only the `"successful_escort"` event kind is
confirmed to fire from real production code today; `"betrayal"`/`"clear_camp"` have no confirmed
live caller (not investigated further here — out of this chapter's own scope to trace).

**Implementing code:** `src/systems/social_systems/reputation.py`,
`src/domains/commitment/reputation.py`.

---

## 5. Contract Lifecycle

Social contracts are durable `ContractState` records: `kind`, `source_id`, `target_id`, `terms`,
`status` (`OFFERED`/`COUNTERED`/`ACCEPTED`/`ACTIVE`/`FULFILLED`/`FAILED`/`BETRAYED`/`CANCELLED`/
`EXPIRED`), `deadline_tick`/`expiry_tick`.

**Consequence resolution is a single generic mechanism, not per-kind breach rules**
(`SocialContractSystem.resolve_contract_outcome()`, `contracts.py`) — applies uniformly across every
`ContractKind`:

```
sentiment_delta    = 0.2 if success else -0.2       # -1.0 (max distrust) if betrayal
familiarity_delta  = 0.1
heroism_delta       = 0.05 if success else 0.0
notoriety_delta     = 0.0 if success else 0.1        # 0.5 + betrayal_increment=1 if betrayer_id set
```
Both parties receive a `SocialBondUpdate` with the sentiment/familiarity deltas above; the reputation
deltas feed §4.1's scalar via `SocialUpdate.heroism_delta`/`notoriety_delta`. A confirmed betrayal
also spawns an `AVENGE` `DirectiveState` and a `TurningPointState` for the wronged party.

**Disclosed gap:** the `betrayal=True`/`betrayer_id` arguments are structurally real and unit-tested,
but `process_active_contracts()` — the only production caller — only ever invokes
`resolve_contract_outcome(success=True, ...)` on contract expiry. The betrayal-specific branch is
reachable only from direct unit tests until a future ticket wires a real in-pipeline betrayal
trigger for social contracts specifically (distinct from the party-defection betrayal path in §7).

**Implementing code:** `src/systems/social_systems/contracts.py`.

---

## 6. Reputation Shop Discount

Relocated from `docs/mechanics/03_economic_laws.md` §4.1 (a Social-domain field read by an Economic
consumer — see that section's own former placement note, now replaced with a pointer here).

```
entity_rep  = clamp(public_reputation, 0.0, 2.0) / 2.0   # normalized 0.0-1.0
discount    = entity_rep * 0.20                            # up to 20% at max reputation
discounted  = floor(base_cost * (1.0 - discount))
final_cost  = max(1, discounted)                           # floor: never free
```
At default reputation (1.0): 10% discount. At maximum (2.0): 20%. At zero: 0% (no penalty, no
bonus). Both real call sites (`src/engine/shop.py`, `src/town/shop.py`) read only the global
§4.1 scalar, not `regional_reputation` — region-aware discounting is a disclosed, not-yet-implemented
follow-up. Faction cross-check is not applied (`docs/guidelines/intentional_divergences.md` DEV-001)
— the discount is universal across all shops. Conservation law satisfied: buyer pays less, shop
receives less, net world gold unchanged.

**Implementing code:** `src/systems/economy_systems/reputation_discount.py`.

---

## 7. Guild Intelligence

**Corrected — `GuildMembership`/guild dues/guild rank do not exist anywhere in `src/`.** The real
mechanism, `GuildIntelSystem.update()` (`guilds.py`), is an intel-gathering interaction: an entity
interacting with a functional guild `BuildingState` (`interaction.kind == "guild"`) accumulates
`interaction.progress` by `+1.0`/tick; at `progress >= 10.0`, the guild identifies the region with
the **highest `trauma_score`** in the world and creates a real rumor `LeadState`/`BeliefState` about
danger there (`BeliefCycleSystem.process_rumor()`), and — if that region's `trauma_score > 5.0` — a
`ConcernState(kind="danger")` scaled by `trauma_score / 10.0`. The entity's interaction then resets.

**Implementing code:** `src/systems/social_systems/guilds.py`.

---

## 8. Party & Group Coordination

**Corrected — there is no `PartyRecord` type anywhere in `src/`.** Multi-entity coordination is a
`GroupRecord` (`member_ids`, `anchor`, `cohesion_radius`, `roles`, `composition_score`,
`grievance_log`), not a leader-owned party record, with three cooperating services:

### Cohesion & Roles (`group_service.py`)
`GroupService.calculate_cohesion()` returns the fraction of `member_ids` within `cohesion_radius` of
the group's spatial `anchor` (0.0-1.0). `assign_role()` sets a per-member functional role tag.

### Leadership Influence (`party.py`)
`PartyCoordinationSystem.apply_leadership_influence()` is a goal-injection mechanism, not a
directive-propagation one: on scoring, a party member with an ACTIVE `RECRUITMENT` contract to a
living leader receives an injected `GoalScore` candidate matching the leader's own active objective,
with utility:
```
boost = 25.0 + (trust_score * 15.0)     # trust_score: bond.sentiment or trust_history, 0.0-1.0-mapped
```
This is strong enough to dominate ordinary goal candidates but can still be overridden by survival
needs (hunger/HP) scoring higher. `validate_shared_target()` clears a group's `shared_target_id` if
the target dies, deactivates, or leaves `2 * cohesion_radius` of the anchor. `issue_party_command()`
creates a `CRITICAL`-priority `DirectiveState` (REGROUP/RETREAT/ATTACK) for all members.

### Leadership Election & Defection (`party_lifecycle.py`, SOC-228/SOC-230)
- **Election:** every `LEADERSHIP_CHECK_INTERVAL` ticks, if the highest-sociability member exceeds
  the current leader's sociability by `>= 0.2`, that member (lowest id as tiebreaker) is elected and
  a `LeadershipChangedEvent` fires.
- **Defection:** an entity defects when `len(group.grievance_log) >= effective_defection_threshold(group)`:
  ```
  threshold = max(1, 3 + round(composition_score * 2) - round(loyalty_pressure * 2))
  ```
  Baseline `3`; a high-composition-quality group (`composition_score` toward 1.0) sustains up to
  `+2` extra grievances before dissolving; `loyalty_pressure` (idea 56, §9 of
  `docs/world/culture_drift_contract.md`) can lower it by up to `2` — floored at `1`, never made
  impossible. On defection: the entity is removed from `member_ids`, a `BetrayalDesertionEvent`
  fires, `notoriety_delta = 2.0` applies (§4.1), and `identity.faction` is set to `NEUTRAL` (idea 39,
  `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` — a neutral-sentinel design, not rival-faction
  selection; see `docs/world/affiliation_mutation.md`). If the group drops to `<= 1` member,
  `dissolution_tick` is set.

**Implementing code:** `src/systems/social_systems/{party,party_lifecycle,group_service}.py`.

---

## 9. Party Composition Scoring

`PartyCompositionScorer.score()` (`party_composition.py`) scores a candidate pool's party-formation
quality, `0.0`–`1.0`, feeding `FORM_PARTY` route's expected-benefit:

```
base_score = 0.6 * role_diversity + 0.4 * ocean_compatibility
score      = base_score  (if no acting entity supplied — reproduces pre-idea-54/247 output exactly)
score      = clamp(base_score + 0.15 * trust_term + 0.10 * role_affinity_term, 0.0, 1.0)  (if actor supplied)
```
- `role_diversity`: fraction of the 4 inferred roles (TANK/HEALER/DPS/SUPPORT) represented in the
  pool, `0.0`–`1.0`.
- `ocean_compatibility`: mean of normalized bravery/sociability variance across the pool (higher
  variance → more complementary personalities).
- `trust_term` (optional, `actor` supplied): mean directed trust/bond sentiment the actor holds
  toward each candidate — bond sentiment takes priority over `trust_history` (§1's rule), `0.0`
  default for no prior relationship.
- `role_affinity_term` (optional): mean directed `RelationshipRole` affinity — `FRIEND` → `+1.0`,
  `RIVAL` → `−1.0`, neutral/no bond → `0.0`. A candidate in the actor's `nemesis_ids` scores `−1.0`
  regardless of bond role — `nemesis_ids` takes precedence over a stale `FRIEND` tag (§3).

Used by `AdventureRouteGenerator`'s `FORM_PARTY` route and `GroupSystem`'s ally-cohesion formation
(`src/systems/world_systems/groups.py`, which never passes `actor`).

**Implementing code:** `src/systems/social_systems/party_composition.py`.

---

## 10. Mutation Rules & Architecture Boundary

All social state changes route through `SocialUpdate` → `RelationshipService.process_update()` →
the authoritative apply path. Direct mutation of `SocialComponent` fields outside this path is
prohibited. `tests/architecture/test_social_write_paths.py` is the real architecture guard for this
rule — it caught and led to fixing two pre-existing bypasses (`SocialMemoryImporter.apply()` and
`CampaignOrchestrator._build_initial_state()`, both now routed through `process_update()`).

Domain services (cooperation, commitment) never read social state directly — they produce
`ContractState`/`SocialUpdate`/`PublicReputationProfile` outputs; social systems apply them. A
cross-import from a domain into `src/systems/social_systems/` violates this boundary.

**Extension rules:**
1. New contract kind → add to `ContractKind`, implement an `_appraise_*` method, add resolution
   handling in `contracts.py`, add tests.
2. New relationship dimension → extend `SocialComponent`/`SocialUpdate`, add clamping in
   `RelationshipService.process_update()`.
3. New guild benefit → extend `guilds.py`; guild-derived signals must be readable by the adventure
   domain without importing social systems directly.
4. Never read social state in a domain service.

---

## Related Contracts

Cross-episode and narrative-adjacent social behavior is documented separately, not duplicated here:

- **[`docs/simulation/domains/social_memory_contract.md`](../simulation/domains/social_memory_contract.md)**
  — cross-episode social memory carry-forward, decay, and consequence-event re-expression
  (`SocialMemoryDecay`, `SocialMemoryRecord`) — the Campaign-mode counterpart to this chapter's §3.
- **[`docs/simulation/domains/chronicle_contract.md`](../simulation/domains/chronicle_contract.md)**
  — how `NarrativeLedger` events (including social/reputation consequence events this chapter
  describes) compress into the four-level Chronicle hierarchy.
- **[`docs/systems/faction_contract.md`](../systems/faction_contract.md)** — `FactionState`,
  diplomacy, and Clan formation/succession — the CLAN `ContractKind` (§1) and clan_reputation term
  (§1's blended trust formula) are Clan-subsystem concerns owned by that contract, not this chapter.

---

## 📜 Compliance Status

This chapter is **Certified Level 1 (Authoritative)** as of 2026-09-07. Every formula above was
independently spot-checked directly against the cited source file/function, not transcribed from
`docs/simulation/social_systems_contract.md` unverified — see this file's own Provenance note at the
top for the 5 sections that diverged and were corrected in the process.
