---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E-NARRATIVE-CONSEQUENCE
phase: open
date: 2026-06-28
tags: [epic, narrative, consequence, motivation, chronicle, p3, deferred]
---

# TCK-20260628-E-NARRATIVE-CONSEQUENCE

## Title
Epic: Narrative Consequence Layer — chronicle events into real-time motivation feedback

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P3

## Request Summary
Chronicle (`ChronicleCompiler`) and social memory (`SocialMemoryRecord`) exist and are
fully implemented. The missing link: chronicle milestone events (death, betrayal, rescue,
conquest) are not fed back into entity motivation urgency at runtime. There is no
grief/rage urgency, no nemesis formation from chronicle entries. This epic wires those
two feedback paths.

**Gate conditions met:**
- E51 (TCK-20260619-E51*) — ChronicleCompiler fully implemented (DONE).
- E43B / E43A–E43E — CampaignOrchestrator + SocialMemoryRecord fully implemented (DONE).

## Scope
1. **Grief/rage → motivation urgency**: When a `ChronicleEntry` of kind DEATH or
   BETRAYAL involves an entity with a positive `SocialMemoryRecord` toward the victim/
   perpetrator, inject a timed urgency modifier into `MotivationState` for that entity.
2. **Nemesis formation**: When the same entity is flagged as antagonist in 2+ chronicle
   entries against the same protagonist, create a `NemesisRelation` record that:
   - Blocks cooperation route selection with the nemesis.
   - Adds a motivation bonus for revenge-flavored routes.
   - Is carried forward via `CampaignOrchestrator._advance_state()`.
3. **Scenario feedback surface**: Expose active nemesis relations and grief urgencies
   via the decision trace / observability layer so they are inspectable.

## Out of Scope
- Re-implementing ChronicleCompiler, SocialMemoryRecord, or CampaignOrchestrator.
- Narrative rendering or display changes.
- Faction-level narrative consequences (those go through `FactionSocialMemory` and
  FactionDecisionPhase — separate scope).

## Acceptance Criteria
- [ ] An entity whose ally died in episode N has elevated threat urgency in episode N+1.
- [ ] Two chronicle antagonist appearances by the same entity pair create a
      `NemesisRelation` that is inspectable via observability API.
- [ ] Nemesis relation blocks `PartyFormation` route for that entity pair.
- [ ] Grief/rage urgency decays over time (follows `SocialMemoryDecay` cadence).
- [ ] All new typed records (`GriefUrgencyModifier`, `NemesisRelation`) pass through
      the authoritative pipeline — no direct mutation of `MotivationState`.

## Related Tickets
- Parent: TCK-20260627-P3A-DEFERRED-EPICS
- Gate: TCK-20260619-E51-CHRONICLE (DONE — E51A–E51E)
- Gate: E43A–E43E Campaign Runtime (DONE)
- Adjacent: TCK-20260619-E41D (BetrayalDesertionEvent — already emits the canonical signal)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` §Narrative Consequence Layer
- `docs/mechanics/04_strategic_cognition.md` — motivation urgency model
- `docs/mechanics/05_world_evolution.md` — chronicle event taxonomy
- `docs/systems/faction_contract.md` — reference for typed durable record pattern

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/domains/chronicle/` — ChronicleCompiler, ChronicleEntry
- `src/domains/campaigns/orchestrator.py` — _advance_state()
- `src/domains/campaigns/state.py` — CampaignState, NarrativeLedger
- `src/domains/motivation/` — MotivationState, urgency model
- `src/domains/social/` — SocialMemoryRecord, SocialMemoryDecay
- `src/observability/` — decision trace schema extension

## Assumptions / Open Questions
- `ChronicleEntry` kinds: confirm DEATH and BETRAYAL are the primary kinds to hook on,
  or whether all milestone kinds (RESCUE, CONQUEST) should also produce motivation effects.
- Urgency decay cadence: tie to existing `SocialMemoryDecay` half-life or define a
  separate grief decay rate?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
