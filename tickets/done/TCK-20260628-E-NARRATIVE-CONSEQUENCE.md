---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E-NARRATIVE-CONSEQUENCE
phase: done
date: 2026-06-28
tags: [epic, narrative, consequence, motivation, chronicle, p3, deferred]
---

# TCK-20260628-E-NARRATIVE-CONSEQUENCE

## Title
Epic: Narrative Consequence Layer — chronicle events into real-time motivation feedback

## Status
DONE — all 3 child tickets complete: E43F (grief urgency), E43G (nemesis relation), E43H (observability surface)

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
**Investigation findings (2026-06-28):**
- `NarrativeLedgerEntry.event_type` values are "entity_death" | "faction_shift" | etc.
  (not "DEATH"/"BETRAYAL" as noted in scope — child tickets must use the actual field values).
- `SocialMemoryRecord` lives in `src/domains/campaigns/social_memory.py` (not `src/domains/social/`).
- No `NemesisRelation` or `GriefUrgencyModifier` types exist — must be created as new typed records.
- `src/domains/motivation/` contains evaluator.py, resolver.py, service.py — no `MotivationState`
  class found; child tickets must confirm the urgency injection hook before implementation.
- `ChronicleCompiler` is a stateless post-run compiler (not a per-tick system) — the hook
  must fire at episode advance time, not per-tick.

**Recommended child tickets (implement in order):**
1. TCK-...-E43F-GRIEF-URGENCY: `GriefUrgencyModifier` record + motivation injection at episode
   advance when NarrativeLedgerEntry.event_type="entity_death" and ally SocialMemoryRecord exists.
2. TCK-...-E43G-NEMESIS-RELATION: `NemesisRelation` record + party-formation route block +
   antagonist-count detection from narrative_ledger in CampaignOrchestrator._advance_state().
3. TCK-...-E43H-NARRATIVE-OBS: Expose GriefUrgencyModifier and NemesisRelation via decision trace
   observability. Gated behind E43F and E43G.

## Test Summary
E43F: 13 tests (grief detection, decay, concern injection). E43G: 9 tests (nemesis detection, blocker injection, party block). E43H: 5 tests (narrative_modifiers extraction). All pass.

## Files Changed
See child tickets TCK-20260628-E43F-GRIEF-URGENCY, TCK-20260628-E43G-NEMESIS-RELATION, TCK-20260628-E43H-NARRATIVE-OBS.

## Completion Summary
All acceptance criteria met: ally death → grief urgency concern → episode decay; 2+ antagonist episodes → nemesis relation → FORM_PARTY block; grief + nemesis visible in EntityInspectionSnapshot.narrative_modifiers. Parity ledger entries SOC-231 and SOC-232 added.

