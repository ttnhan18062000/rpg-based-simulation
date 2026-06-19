---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32-CAMPAIGN-RUNTIME
phase: open
date: 2026-06-19
tags: [campaign-runtime, persistent-state, narrative-ledger, episode-continuity, epic, phase-3]
---

# TCK-20260619-E32-CAMPAIGN-RUNTIME

## Title
Epic 3.2 · Persistent Campaign Runtime

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`CampaignRunner` is explicitly analysis-only — isolated shadowed state, no `Failed` state, no shared `AuthoritativeState` with a live sim. Each run is amnesiac. No actual multi-scenario continuity exists anywhere. `CampaignRunner` must be renamed `SimulationAnalysisRunner` before this epic to eliminate the naming collision.

Score: 9/10 · D01 score 20/25 · Effort: L · Source: `docs/plans/engine_future_epics_roadmap.md` § D, `docs/audits/D01_rpg_feature_impact.md`

## Scope
- **Prerequisite:** TCK-20260619-E31-SCENARIO-RUNTIME complete
- **Rename first:** `CampaignRunner` → `SimulationAnalysisRunner` in `src/domains/campaigns/runner.py` and all callers (to free the "campaign" namespace)
- `CampaignState` data model: `episode_history[]`, `persistent_entities{}`, `persistent_factions{}`, `world_timeline[]`, `narrative_ledger[]`
- `CampaignOrchestrator`: owns a sequence of `ScenarioSpec`; carries `CampaignState` forward; uses `ScenarioRuntimeService` to run each episode
- Inter-episode state transfer: entity XP/equipment/reputation/injury persists; dead entities stay dead; faction tension/alliance state carries forward
- `NarrativeLedger`: structured record of significant campaign events (quest completions, entity deaths, faction shifts, calamities) by tick + episode; queryable
- Campaign spec format: YAML defining episode sequence, world transition rules, carry-forward rules, campaign victory conditions
- Campaign checkpoint: serialize full `CampaignState` between episodes; resumable from any episode boundary
- REST: `GET /api/v1/campaigns/{id}/history` → `NarrativeLedger` as structured event stream
- Child tickets: (a) rename CampaignRunner, (b) CampaignState model, (c) CampaignOrchestrator + episode handoff, (d) NarrativeLedger, (e) REST endpoint

## Out of Scope
- Campaign UI
- Player agency / interactive decision points
- Cross-campaign storyline (Phase 6)
- Social memory within episodes (Epic 4.3 feeds in automatically via NarrativeLedger)

## Acceptance Criteria
- A 3-episode campaign where: (a) a HERO entity that reaches level 5 in episode 1 starts episode 2 at level 5; (b) a faction destroyed in episode 1 does not spawn in episode 2; (c) `NarrativeLedger` contains ≥10 cross-episode entries
- Campaign checkpoint can be restored from any episode boundary

## Related Tickets
- TCK-20260619-E31-SCENARIO-RUNTIME (prerequisite)
- TCK-20260619-E41-PARTY-LOOP (unlocked)
- TCK-20260619-E42-INFO-SEEKING (unlocked)
- TCK-20260619-E43-SOCIAL-MEMORY (depends on NarrativeLedger from this epic)
- TCK-20260619-E51-CHRONICLE (depends on NarrativeLedger)

## Related Docs
- `docs/simulation/domains/campaigns_contract.md` (major update: add CampaignOrchestrator, NarrativeLedger, episode handoff; update boundary table)
- `docs/audits/D01_rpg_feature_impact.md` § Persistent Campaign Runtime
- `docs/plans/long_term_development_roadmap.md` § Epic 3.2
- `docs/plans/engine_future_epics_roadmap.md` § D
- `docs/core/state.md` (AuthoritativeState carry-forward rules — state transfer between episodes must respect immutability law; read before designing entity persistence)
- `docs/engine/kernel.md` (CampaignOrchestrator drives ScenarioRuntimeService which wraps Kernel; update to show the orchestration hierarchy)
- `docs/parity_ledger/substrate.yaml` (authoritative state persistence across episodes)
- `docs/parity_ledger/social_narrative.yaml` (NarrativeLedger as social/narrative record)
- New doc: `docs/simulation/domains/campaign_orchestrator_contract.md` (CampaignOrchestrator lifecycle, NarrativeLedger schema, episode handoff rules, carry-forward rules)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260612-DOMAINS-ARCH-MAP/`
- `stored_artifacts/TCK-20260528-PHASE9-LIFE-ARCS/` (prior life-arc campaign — analysis-only, not continuous)

## Related Code Areas
- `src/domains/campaigns/runner.py` (CampaignRunner — rename target)
- `src/domains/campaigns/schema.py:L43` (CampaignEvent — extend)
- `src/domains/campaigns/spec.py` (CampaignSpec)
- `src/engine/kernel.py:L34` (Kernel — via ScenarioRuntimeService)
- `src/core/state.py:L981` (AuthoritativeState — persistent entity state carrier)

## Assumptions / Open Questions
- What fields does `CampaignEvent` currently have? Check `src/domains/campaigns/schema.py:L43`
- Does `ScenarioSpec` already support episode-sequence YAML, or does the campaign spec format need to wrap it?
- How is faction state currently stored in `AuthoritativeState`? Verify before designing the faction carry-forward mechanism

## Implementation Notes
The rename (`CampaignRunner` → `SimulationAnalysisRunner`) must happen first in its own child ticket to avoid confusion throughout the implementation. This is a large epic (L) — expect 4-5 child standard tickets. The NarrativeLedger is the most critical deliverable because it gates Epic 4.3 and 5.1.

After implementation: update `docs/simulation/domains/campaigns_contract.md` boundary table to reflect CampaignOrchestrator vs. SimulationAnalysisRunner. Create `docs/simulation/domains/campaign_orchestrator_contract.md`. Update `docs/parity_ledger/substrate.yaml` and `social_narrative.yaml`. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/integration/scenarios/test_campaign_runtime.py`:
  - `test_entity_state_persists_across_episodes()` — level 5 entity at episode 1 end → level 5 at episode 2 start
  - `test_dead_faction_absent_in_episode_2()` — faction destroyed in ep1 not spawned in ep2
  - `test_narrative_ledger_populated_with_cross_episode_events()` — assert ≥10 NarrativeLedger entries spanning both episodes
  - `test_campaign_checkpoint_restores_from_episode_boundary()` — serialize CampaignState, restore, run ep2; assert same outcome as non-checkpoint run
- New file `tests/api/test_campaign_history_api.py`:
  - `test_campaign_history_endpoint_returns_narrative_ledger()` — GET `/api/v1/campaigns/{id}/history`; assert structured event stream with ≥10 entries

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
