---
status: active
layer: mechanics
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER
date: 2026-09-07
---

# Investigation: TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER

## Current Behavior (file:line refs)
- `docs/mechanics/` has chapters 01-06; next available chapter number is `07`.
- `docs/simulation/social_systems_contract.md` (`status: active`, `authority: P1`,
  `last_verified: 2026-09-04`) is a substantial existing contract doc covering
  Appraisal/Relationships/Social Memory/Contracts/Guilds/Party/Party Composition/Reputation.
- Liveness question (pre-resolved before this pass, per the orchestrating session): BOTH
  `ReputationUpdateService.process_witnessed_event()` (`src/domains/commitment/reputation.py:15`,
  real caller `src/engine/quests.py:233`) and `ReputationService.combine_public_reputation()`
  (`src/systems/social_systems/reputation.py:32`, real caller `src/core/builder.py:676`) are live.

## Fresh-vs-promote decision
Chose **promote with correction**, not author-from-scratch. Reason: independently spot-checking every
formula in `social_systems_contract.md` against real code (per this ticket's own AC1, the SUB-327
precedent) found the doc is a genuine mixed bag, not uniformly reliable — the safer path is real-code-
first authoring using the doc only as a structural starting point, correcting every divergence found
rather than assuming any one section is trustworthy because most of the doc reads as thorough.

## Five real, material corrections found (not stale numbers — described mechanisms with no basis in `src/`)
1. **Appraisal trust formula (partial omission)**: the doc's "blended fallback" step (`public_trust ×
   0.7 + history_trust × 0.3`) omits a real third term — `(clan_trust - 0.5) × 0.2`
   (`CLAN_INFLUENCE_WEIGHT`, idea 54, confirmed at `appraisal.py:72-77`). The doc's hard-reject gate
   also omits the real `or bond.sentiment < -0.8` OR-condition (`appraisal.py:81`).
2. **Reputation (structural conflation)**: the doc's Reputation table describes
   `ReputationUpdateService.process_witnessed_event()` as changing a "reputation" scalar with
   deltas/labels ("reputation +0.1; RELIABLE label added", etc.) that do not exist in real code at
   all. The real function only ever mutates `PublicReputationProfile.labels` (a `Mapping[str, float]`
   at `entity.cognition.relationships.public_reputation` — a DIFFERENT component path and type from
   `SocialComponent.public_reputation`, the real clamped scalar used by trust/discount/birth-seed).
   Real label deltas (confirmed via direct read, `reputation.py:15-27`):
   `"successful_escort"` → `reliable += 0.1`; `"betrayal"` → `betrayer += 0.4, reliable -= 0.3`;
   `"clear_camp"` → `camp_clearer += 0.2, heroic += 0.1`. No "COMBATANT" label exists.
3. **Contracts (fabricated ContractKind + table)**: `ContractKind` has no `ESCORT` member (confirmed
   via `src/core/strategic.py:73-88` — real members: RECRUITMENT/LOAN/PROTECTION/MERCHANT/
   POSITION_SWAP/TEAM_UP/PAID_INFORMATION/TEACH/MARRIAGE/CLAN). ESCORT is a `QuestKind` (a separate
   quest-domain enum). There is no per-kind breach table — `resolve_contract_outcome()`
   (`contracts.py:183-233`) is a single generic mechanism applied uniformly across all real kinds.
4. **Guilds (fabricated system)**: `GuildMembership`/guild dues/guild rank/guild-presence route bias
   have zero hits anywhere in `src/` (confirmed via grep). The real mechanism, `GuildIntelSystem.
   update()` (`guilds.py`), is an intel-gathering interaction unrelated to membership at all — visiting
   a functional guild building accumulates progress toward generating a rumor Lead/Belief about the
   world's highest-trauma region.
5. **Party (fabricated state type)**: `PartyRecord` does not exist anywhere in `src/` (confirmed via
   grep). The real state type is `GroupRecord` (`member_ids`/`anchor`/`cohesion_radius`/`roles`/
   `composition_score`/`grievance_log`), with three real cooperating services:
   `PartyCoordinationSystem` (goal-injection leadership influence, `party.py`), `GroupService`
   (cohesion/role assignment, `group_service.py`), and `PartyLifecycleService` (leadership election
   SOC-228 + grievance-driven defection SOC-230, `party_lifecycle.py`) — none of "LEAVE action",
   "trust -0.25 on leader death", or party-specific `force_route_reevaluation` sync have real basis;
   `force_route_reevaluation` is real but lives in the unrelated `src/domains/world_emergence/`.

## Sections confirmed accurate, promoted as-is (presentation changes only)
- Relationships clamp table (trust ±1.0, familiarity 0-1.0, debt ±1.0, fear 0-1.0, grudge 0-5.0,
  salience 0-1.0, place_attachment 0-1.0, regional_reputation 0-2.0) — confirmed exactly against
  `relationships.py:16-100`.
- Social Memory (place attachment +0.001/tick, nemesis promotion at grudge >= 3.0) — confirmed exactly
  against `memory.py`.
- Party Composition scoring weights (0.6 role diversity, 0.4 OCEAN, optional 0.15 trust + 0.10 role
  affinity) — confirmed exactly against `party_composition.py`.
- Decay (zero passive decay on live `SocialComponent`; the only real decay, `SocialMemoryDecay`,
  operates on a separate cross-episode structure) — confirmed accurate, already itself a 2026-09-02
  correction in the source doc.

## Real write paths to `SocialComponent.public_reputation` (new finding, not in either doc before)
Confirmed via direct grep of `heroism_delta=`/`notoriety_delta=`/`reputation_set=` call sites: contract
FULFILLED transition (`heroism_delta=0.05`, `contracts.py:45`); contract expiry resolved success
(same delta, real live path via `process_active_contracts()` → `resolve_contract_outcome(success=True)`,
`contracts.py:308`); contract failure/betrayal (`notoriety_delta=0.1`/`0.5`, betrayal path disclosed
dead — `process_active_contracts()` never passes `betrayal=True`); party defection
(`notoriety_delta=2.0`, `party_lifecycle.py:223`, real live path); idea 53 birth-seed
(`reputation_set`, `builder.py:676`); Campaign episode carry-forward (`social_memory.py:528`,
`orchestrator.py:668`).

## Docs Requiring Update
- `docs/mechanics/07_social_political_dynamics.md` (new, this ticket's own core deliverable).
- `docs/mechanics/README.md`: TOC entry + Compliance Status line for chapter 07.
- `docs/mechanics/06_worldbuilding_foundation.md`: master Compliance Status table gains a row for 07.
- `docs/mechanics/03_economic_laws.md`: §4.1 reputation-discount fragment relocated (pointer left
  behind, not duplicated).
- `docs/simulation/social_systems_contract.md`: 5 sections corrected in place (see above), plus a
  top-of-file provenance/correction note.
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md`: status note
  updated to reflect all 5 hardening-backlog items now shipped.
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`: Hardening backlog item 1 marked shipped.

## Parity Ledger Overlap
None — no `src/` production code changed, `behavior_changed=false`. `docs/parity_ledger/
social_narrative.yaml` entries (SOC-*, STRAT-*) are unaffected; this ticket documents existing,
already-shipped mechanisms with no behavior change. The 5 corrections above are documentation-accuracy
fixes, not divergences from any Mechanics Bible law (there was no prior chapter to diverge from).

## Prior Work
- `docs/simulation/social_systems_contract.md` — promoted-from source, corrected in place.
- `docs/simulation/domains/social_memory_contract.md`, `chronicle_contract.md`,
  `docs/systems/faction_contract.md` — cross-linked (not rewritten) from the new chapter's own
  "Related Contracts" section.
- `TCK-20260905-SUB-327-FABRICATED-CITATION-FIX` — the precedent this ticket's own liveness/formula
  spot-check requirement is modeled on; a fabricated citation was found there too (same class of bug
  as the 5 corrections above).

## Risks and Open Questions
None outstanding — all 5 corrections are evidence-based (direct grep confirming zero hits, or a
direct code read confirming the real formula), not judgment calls requiring escalation.

## Anti-Drift Hazards
- Do not cite `social_systems_contract.md`'s Reputation/Appraisal/Contracts/Guilds/Party sections as
  ground truth without re-checking against Chapter 07 or real code first — even after this
  correction pass, treat any future edit to those sections with the same scrutiny.
- Do not conflate `SocialComponent.public_reputation` (the scalar) with `PublicReputationProfile.
  labels` (the label bag) — they share a name but are structurally unrelated.
- Do not assert the betrayal-specific branch of `resolve_contract_outcome()` is live — it remains
  reachable only from direct unit tests today.
