---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE
artifact_type: plan
tags: [observability, engine, simulation-quality, performance]
---

# plan.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE

## Unresolved Questions

None — investigation.md answered all 6 scoped questions with evidence (determinism: no issue;
Zero Simulation Impact: doesn't apply to emission; performance: existing harness reusable;
coverage: 3 of 4 checked domains already push-ready; volume control: solvable per-shaper; migration
risk: bounded by the existing `FeatureMode.SHADOW` pattern). Recommendation is a phased build, not a
further investigation.

## Steps

1. **File the Phase 1 follow-up implementation ticket**:
   `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-EMISSION-PHASE1-COMBAT-ECONOMY-FACTION` — standard tier,
   scoped to the 3 domains confirmed push-ready in investigation.md Finding 4, with the shaper
   registry design and SHADOW-mode rollout plan from the Recommendation.
2. **Update `D20_simq_quality_status_review.md`** — add a finding recording this ticket's
   conclusion and the Phase 1 ticket reference.
3. **Update `SEQUENCE.md`** to reflect this ticket's DONE status and the new Phase 1 ticket.
4. Do not file a Phase 2 ticket yet — investigation.md's Finding 4 audit of PROGRESSION's quest
   detection was not exhaustive enough to scope Phase 2 precisely (only 1 domain checked in depth;
   demographic/XP domains flagged but not fully traced). Phase 1's own findings should inform
   Phase 2's scope rather than guessing it now.
5. Run `make knowledge-index-update` (D20 doc touched).

## Scope guard

No `src/`/`tests/` files touched by this ticket — the actual apply-layer emission code is Phase 1's
Implement step, not this investigation's.

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| Determinism question answered with evidence | investigation.md Finding 1 |
| Zero Simulation Impact compatibility assessed | investigation.md Finding 2 |
| Coverage audit completed | investigation.md Finding 4 (4 domains checked in depth; not exhaustive across all ~10, disclosed as such) |
| Volume/mode-control sketch | investigation.md Finding 5 |
| Migration/rollout sketch | investigation.md Finding 6 |
| Concrete recommendation | investigation.md Recommendation + Plan step 1 (Phase 1 ticket filed) |
