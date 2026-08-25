---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260824-WIRE-ORPHANED-MECHANISMS
phase: open
date: 2026-08-24
tags: [social, cognition, progression]
---

# TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Title
Wire the Remaining Orphaned Mechanisms

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Nine originally-orphaned mechanisms exist (two now folded into affection-gating and M3 Reproduction), leaving seven still needing wiring per the atlas's checklist. The author wants those seven orphaned mechanisms wired into real production call sites.

## Scope
- Wire `InformationNeedDetector.detect_and_generate()` into `CognitionDomain.execute_brain()`, at the documented insertion point (after project eval, before route scoring) per `src/engine/domain/cognition_extras.py`'s docstring
- Investigate and disclose whether `EvolutionService` (`src/progression/evolution.py`) is a dead duplicate of the already-live `EvolutionSystem` (`src/engine/evolution.py`, same goblin_0/1/2 mechanism) before wiring; prove additive, or fold/delete
- Investigate and disclose whether `SabotageAction` (`src/town/sabotage.py`) is a duplicate or distinct-purpose path from the live `BuildingSabotageSystem` (`src/engine/sabotage.py`) before wiring; wire with a distinct purpose or delete/merge as a confirmed duplicate
- Call `EmotionUpdateService.update_on_event()` (`src/domains/emotion/emotion_service.py`) from a real event-emission site, distinct from the unrelated `AppraisalSystem.evaluate_emotional_state()`
- Call `ReputationUpdateService.process_witnessed_event()` (`src/domains/commitment/reputation.py`) from a real witnessed-event site
- Call `compute_elder_attribute_update()` (`src/domains/demographics/cohort.py`) once per aging-cycle tick where `get_age_bracket()` is already invoked
- Call `consequence_events.py`'s function at the start of a social encounter, read-only, emitted via the authoritative pipeline

## Out of Scope
- MemoryUpdatePhase wiring -- owned by TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING (C11), same gap/file/consumer, must not be duplicated here
- GeneticsSystem wiring -- owned by M3 Reproduction, entirely out of this M1 epic
- Any consolidation of TCK-20260425-PH7-M4-SABOTAGE's historical claims beyond flagging the discrepancy

## Acceptance Criteria
- [ ] InformationNeedDetector.detect_and_generate() is called from CognitionDomain.execute_brain() at the documented insertion point, verified via a real Kernel run
- [ ] SabotageAction is either wired with a distinct purpose from the live BuildingSabotageSystem, or deleted/merged as a confirmed duplicate, with the duplicate check documented
- [ ] EvolutionService wiring is preceded by an explicit duplicate-check against the live EvolutionSystem, proving additive or fold/delete
- [ ] EmotionUpdateService.update_on_event() is called from a real event-emission site, distinct from AppraisalSystem.evaluate_emotional_state()
- [ ] ReputationUpdateService.process_witnessed_event() is called from a real witnessed-event site
- [ ] compute_elder_attribute_update() is called once per aging-cycle tick at the existing get_age_bracket() call site

## Related Tickets
- TCK-20260619-E42A-INFO-NEED
- TCK-20260619-E43E-CONSEQUENCE-EVENTS
- TCK-20260619-E52C-AGE-ADVANCEMENT
- TCK-20260425-PH7-M4-SABOTAGE
- TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING
- TCK-20260618-AUDIT-D11-DEAD
- TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE
- TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/emotion/emotion_service.py
- src/domains/emotion/__init__.py
- src/progression/evolution.py
- src/engine/evolution.py
- src/engine/pipeline.py
- src/engine/domain/cognition_extras.py
- src/engine/domain/cognition.py
- src/systems/social_systems/consequence_events.py
- src/town/sabotage.py
- src/engine/sabotage.py
- src/domains/commitment/reputation.py
- src/domains/commitment/__init__.py
- src/domains/demographics/cohort.py
- src/core/cognition.py
- src/systems/social_systems/reputation.py
- src/engine/cognition.py

## Assumptions / Open Questions
- EvolutionService is very likely a dead duplicate of the already-live EvolutionSystem -- the atlas did not catch this, so this ticket must investigate and disclose before wiring
- TCK-20260425-PH7-M4-SABOTAGE (closed DONE) claims SabotageAction was already implemented, but current reality shows zero callers -- flagged as a possibly stale historical closure needing reconciliation
- Per the atlas's own precedent, consider splitting into 7 separate small tickets rather than one shared ticket if scope proves too large to land atomically
- `layer: engine` chosen because the majority of wiring call sites (`src/engine/domain/*`, `src/engine/pipeline.py`, `src/engine/evolution.py`, `src/engine/sabotage.py`, `src/engine/cognition.py`) sit in the deterministic tick/domain-execution loop; the mechanisms themselves span cognition, social, progression, and demographics domains but the unifying scope is wiring them into that engine execution path

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
