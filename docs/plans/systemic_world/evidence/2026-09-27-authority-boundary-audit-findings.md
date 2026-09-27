---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `foundation-audit-findings.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Bounded cross-domain authority audit — findings

Directive: run the bounded foundation/authority audit called for by `docs/plans/systemic_world_roadmap.md` §3.1/§8 and the third-round external review's finalize instruction §4. Precedent shape: the regional-sovereignty dual-authority bug (two systems independently writing the same durable ownership/control field, at different thresholds), found in an already-shipped, already-tested domain during unrelated work. Investigation only — no production code changed.

## Named boundaries checked (5)

### 1. Region ownership: `RegionState.owner_faction_id` vs. `FactionState.territory` — `DEFECT_CONFIRMED` (already known/tracked; downstream consequence unverified)

Two representations of "who owns this region" exist:
- `owner_faction_id` (`Optional[int]`) is written only by `src/engine/world_dynamics.py:83,87` (hazard/monster-horde takeover).
- Authoritative ownership after a *military* siege transfer instead updates `FactionState.territory` via `FactionUpdate.territory_add/remove` in `src/engine/military_conflict.py`. That file's own docstring (lines 163–166) states `owner_faction_id` is **NOT** set during siege transfer — "known limitation (FAC-010)."

Parity ledger `docs/parity_ledger/faction.yaml:227-237` (`FAC-010`, `status: verified`) confirms this divergence is documented and intentional, not a hidden bug.

**Consequence unverified**: `src/engine/town_resolution.py:128-170` reads `region.owner_faction_id` for taxation and suppression logic. No test combines a siege-based territory transfer with a subsequent taxation tick on the same region — whether taxation actually fires against the stale pre-transfer faction after a siege is `UNKNOWN_WITH_REASON`: no test either way.

### 2. Entity death: `alive_set` written from `combat.py` and `world_dynamics.py` — `UNKNOWN_WITH_REASON`

`alive_set` is written from `src/engine/combat.py:232,318,445,499,557` (combat resolution) and `src/engine/world_dynamics.py:39` (hazard damage) — two independent domains that can both kill the same entity. Unlike the sovereignty bug, there's explicit cross-system awareness in comments: `src/systems/world_systems/groups.py:99` and `src/engine/pipeline_phases/clan_lifecycle.py:19` both note "same-tick `CombatUpdate(alive_set=False)` must be respected here." This looks like deliberate precedence, not an accidental duplicate writer — but no scenario test was found exercising a same-tick hazard-kill + combat-kill collision on one entity, so the merge behavior is asserted by comment, not verified by a run.

### 3. Faction diplomacy: `diplomatic_relations_set` from the autonomous state machine and the auto-alliance handler — `UNKNOWN_WITH_REASON`

`src/domains/faction/diplomatic_state_machine.py::compute_transitions` (autonomous, threshold-based) and `src/domains/faction/diplomatic_actions.py::handle` (only reachable via one caller, `src/engine/pipeline.py:265-273`, for auto-generated `ALLIANCE_PROPOSAL`s) both write the same `FactionState.diplomatic_relations` dict, in the same pipeline phase (`"diplomatic_transitions"`, `pipeline.py:255-283`), same tick, list-concatenated (`_diplo_updates = _diplo_transition_updates + _diplo_alliance_updates`, line 274) before one `merge()` call. Ordering is fixed and looks intentional (transitions computed first, alliance layered after), but no test was found asserting what happens when both target the *same faction pair* in the same tick (e.g., transition sets `HOSTILE` while alliance sets `ALLIED` for the same pair) — resolution is by list/dict-key overwrite order, unverified by scenario.

### 4. Quest status: `QuestUpdate.status_set` from 4 files — `CONFIRMED_FINE_WITHIN_SCOPE`

Written from `src/engine/economy.py:268` (→`ACTIVE`), `src/systems/world_systems/quest_engine.py:53` (→`COMPLETED`), `src/core/conservation.py:251` (→`REWARDED`), `src/engine/quests.py:222` (→`REWARD_PENDING`). This is a strict forward state machine across distinct pipeline phases, and matches the systemic roadmap's own prior finding (Part A) that quest reward is "the cleanest state-authority pattern found anywhere" (single-writer per stage). Reusing that existing finding here rather than re-deriving it; no new risk found.

### 5. Public reputation: `SocialComponent.reputation` (`reputation_set`) from 2 files — `UNKNOWN_WITH_REASON`

Written from `src/domains/campaigns/social_memory.py:528` (recomputed value) and `src/domains/campaigns/orchestrator.py:928` (`cf.reputation`, a campaign-finding-derived value). Two real writer call sites for the same durable field; this round did not check phase ordering or whether they can target the same entity in the same tick — genuinely unresolved. Separate from the roadmap's already-flagged *semantic* question of what `public_reputation` is supposed to mean (Owner Decision List item 2), which this audit does not re-litigate — this is a mechanical dual-writer check only.

## Exit condition

This is a **named, finite set of 5 boundaries with explicit outcomes** — 1 `DEFECT_CONFIRMED` (pre-existing, documented, consequence-unverified), 3 `UNKNOWN_WITH_REASON`, 1 `CONFIRMED_FINE_WITHIN_SCOPE`. It does **not** claim the regional-sovereignty defect class is absent elsewhere in the engine — only that these 5 specific boundaries were checked and this is what was found. No production code was modified; item 1's consequence gap is flagged for escalation, not fixed.

## Deliberately NOT checked this round (named, not silently skipped)

- Market/economy authoritative price or inventory fields.
- Combat durability/HP fields across the 3 known dispatch paths (`ActionRouter`/Guild-visit/Objective-Reward) — already flagged in Part A from a dispatch-plurality angle, not re-checked here for dual-writer risk specifically.
- `cooldown_set`, `group_id_set`/`GroupRecord`, `self_model_bundle_set`/`cognition_bundle_set` (strategic cognition) fan-in.
- `src/economy/vacancy.py`'s vacancy/settlement fields.
- Institutional standing (does not yet exist as a mechanism, so moot).
