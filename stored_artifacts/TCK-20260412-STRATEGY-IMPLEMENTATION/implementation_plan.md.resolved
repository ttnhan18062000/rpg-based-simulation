# Implementation Plan - Strategic Cognition Stabilization (Milestones 3-5)

Stabilize the strategic cognition layer by finalizing Milestone 5 (Event-driven Reprioritization), adding memory for tested leads in Milestone 3, and hardening social candidate selection in Milestone 4.

## User Review Required

> [!IMPORTANT]
> This plan involves adding persistent state to `StrategicState` (specifically `tested_lead_ids`) to ensure "knowledge continuity". This prevents entities from re-deciding to investigate a lead that they have already proven false or redundant.

## Proposed Changes

### 1. Milestone 5 — Event-driven Strategic Reprioritization

We need to close the loop between narrated events and active project choice.

#### [MODIFY] [StrategicEvaluator](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/strategy/strategic_evaluator.py)
Update to factor in "Trauma" and "Betrayal" concerns into the weighting of candidates, not just using them as interruption triggers.

#### [MODIFY] [SocialCandidateSelectionService](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/strategy/social_candidate_selection.py)
Update to check `StrategicConcern` for betrayal trauma when ranking potential allies.

#### [NEW] [test_strategic_reprioritization.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/core/logic/test_strategic_reprioritization.py)
Automated unit tests for `ConcernGenerationService`, `DirectiveMutationService`, and `ProjectMutationService`.

---

### 2. Milestone 3 — Knowledge Continuity (Tested Leads)

Entities currently "forget" that they've tested a lead if it doesn't result in a persistent discovery.

#### [MODIFY] [strategy.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/strategy.py)
Add `tested_lead_ids: list[str]` to `StrategicState` to track consumed leads.

#### [MODIFY] [ActionSystem](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/gameplay/action_system.py)
Update to handle `tested_lead_ids` in `StrategicUpdate`.

#### [MODIFY] [StrategicEvaluator](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/strategy/strategic_evaluator.py)
When an objective (e.g., INVESTIGATE) is resolved or fails, mark the associated lead as "tested".

---

### 3. Milestone 4 — Social Filtering Hardening

#### [MODIFY] [SocialCandidateSelectionService](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/strategy/social_candidate_selection.py)
Add explicit checks for faction hostility (non-hero factions) and social debt.

## Verification Plan

### Automated Tests
- `pytest tests/unit/core/logic/test_strategic_reprioritization.py`
- `pytest tests/unit/ai/strategy/test_tested_leads.py`
- `pytest tests/e2e/test_strategic_reprioritization.py` (New E2E scenario)

### Manual Verification
- Visual inspection of cognition graphs after a "Near Death" event to ensure the "Safety" directive was acquired and the project was suspended.
