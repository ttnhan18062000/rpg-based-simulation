---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION
artifact_type: test_plan
tags: [simulation-quality, testing, architecture]
---

# Test Plan — TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION

`tests/mechanic_scenarios/test_action_pacing_readiness_gate.py`:

1. **`test_readiness_gate_withholds_a_real_action_when_readiness_is_below_threshold`** —
   `combat.readiness = 50.0`, staged `ATTACK`, one real `Kernel.tick_once()`. Assert
   `CombatActions.execute_attack` was never called for the goblin.
2. **`test_readiness_gate_does_not_withhold_when_readiness_meets_the_threshold`** —
   `combat.readiness = 100.0` (compiled default), same staged `ATTACK`. Assert
   `CombatActions.execute_attack` WAS called at least once for the goblin. This is the differential
   half — without it, test 1 alone could pass for a reason unrelated to the readiness gate (e.g.
   the attack blocked by legality/range/some other check), and the scenario would not actually be
   testing the readiness gate specifically.

**Reason-attribution check** (not a permanent pytest assertion, run manually and recorded in
investigation.md — mirrors the rigor the combat-judgement scenario applied): calling
`ActionRouter.execute_action` directly in the readiness=50.0 condition returns
`EntityUpdate(..., failure_reason=ReasonCode.INSUFFICIENT_READINESS, ...)` — confirms the specific
reason code, not just "no attack happened," which could in principle have a different, unrelated
cause.

**Whole-suite re-verification**: `tests/unit/tools/ tests/unit/engine/test_capability_registry.py
tests/mechanic_scenarios/`, full pass required, `graphify-out/` genuinely moved aside and restored
— standing discipline carried from the mechanism-registry epic into this follow-up ticket.

No new registry-schema tests needed — `verified` block validity is already covered by
`TCK-20260915-MECHANISM-VERIFICATION-AXIS`'s own existing test suite
(`tests/unit/tools/test_mechanism_registry.py`), which this ticket's registry edit must continue
to pass unmodified.
