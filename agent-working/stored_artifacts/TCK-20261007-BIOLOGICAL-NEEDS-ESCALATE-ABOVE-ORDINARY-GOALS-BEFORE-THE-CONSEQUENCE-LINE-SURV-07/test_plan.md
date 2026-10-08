---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07
artifact_type: test_plan
tags: [strategy, cognition]
---

# Test plan

New: `tests/unit/ai/test_need_pull.py` (raw below the onset; monotone; above the highest ordinary goal by 0.75 of the line and above `town_return`'s by 0.85; a mild need stays one wish among many; a longer walk escalates earlier; per-kind rates (high, medium, low, none) order the arrival pull). `tests/unit/ai/test_need_scorers.py` (the scorers carry the escalation over the walk to the inn; a present threat removes it; a wound alone does not; no inn means no walk). `tests/unit/engine/test_rest_in_place.py` (rest in place dispatches `REST` with reason `REST_IN_PLACE` through the tactical pass; per-kind sleep rate decides when a walk is too late; a bed within adjacent reach, a home, or a non-bed building).

## Proof Plan
- **Level**: unit, a constructed tactical-pass dispatch, and a five-seed corpus before and after on three worlds.
- **Proof kind**: regression tests that fail without the hook; before and after measurement with a stated acceptance bar.
- **Oracle source**: world rule SURV-07 (Decision 24), SURV-06 (rest in place, a bed only improves rest), AGENCY-07 (present threat).
- **Expected effect**: starvation deaths fall on every world; total deaths and alive at t=1000 and t=1100 within one SD; rest in place proved by the constructed test (the corpus never reaches it in 1500 or 3000 ticks).
- **Selected commands**: `pytest tests/unit/ai tests/unit/engine/test_rest_in_place.py tests/unit/engine/test_biological_needs.py tests/unit/strategic`; `probes/run_ms.sh <arm> <label> <world> <seed>` over seeds 42 to 46 on three worlds for each arm.
