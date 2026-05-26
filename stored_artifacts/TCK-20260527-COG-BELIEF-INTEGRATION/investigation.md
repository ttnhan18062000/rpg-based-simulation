# Investigation - TCK-20260527-COG-BELIEF-INTEGRATION

## Objectives
- Understand how the belief system is defined in `src/systems/strategic_systems/belief.py`.
- Formulate schema additions to `StrategicComponent` and `StrategicUpdate` to natively support `BeliefEntry`.
- Trace how detour scores in `detour.py` are influenced by lead certainty, source trust, and contradiction count.
- Implement threat-confirmation and threat-contradiction detection when an entity visits a lead location in `fused_strategic_pass()`.

## Findings
- `BeliefEntry` has fields `certainty`, `source`, `contradictions`, and `source_entity_id`.
- `LeadState` has fields `tested`, `test_outcome`, `failure_count`, and `certainty`.
- By tying them together:
  - Rumors start at VAGUE / certainty = 0.3.
  - Success/Confirmation upgrades LeadCertainty to PRECISE and BeliefCertainty to 1.0.
  - Failures degrade LeadCertainty using `BeliefCycleSystem.apply_contradiction` and increment contradictions count.
- Detour scoring penalizes by `contradictions * 25.0`, making false rumors quickly ignored after a single failed check.
