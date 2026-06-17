---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: 2026-04-16
---

# Design Specification: Strategic Cognition Repair & Hardening

## 1. Cognition Capacity Derivation (Milestone 1)

### 1.1 Sparse Personality Mappings
We will integrate a narrow set of float-based personality inputs into the `CognitionCapacityProfile` derivation to close the "honesty" gap.

| Personality Input | Profile Field | Influence | Formula (within _clamp) |
| :--- | :--- | :--- | :--- |
| **Curiosity** (0.0-1.0) | `lead_retention_limit` | Direct Adder | `... + (p_cur * 1.5)` |
| **Caution** (0.0-1.0) | `resume_reliability` | Direct Adder | `... + (p_cau * 0.15)` |
| **Neuroticism** (0.0-1.0) | `judgment_stability` | Penalty | `... - (p_neu * 0.10)` |

### 1.2 Verification Surface
- **Service Tests**: Maintain `tests/unit/ai/test_cognition_capacity_builder.py` for formula stability.
- **Assertions**: `assert p_high_curiosity.lead_retention_limit > p_low_curiosity.lead_retention_limit`.

## 2. Authoritative Persistence & Workflow (Milestone 2 & 3)

### 2.1 Authoritative Path
The "Truth Surface" for all behavior will be the `brain.decide(...)` cycle. We will stop counting test-local pool sorting as proof.

### 2.2 Multi-Tick Integration Proof
A new integration test will demonstrate the following loop:
1. **Tick 0**: Brain observes a fail outcome for Source A.
2. **Tick 1**: `ActionSystem` applies `source_trust_updates` (A -> 0.1).
3. **Tick 2**: Brain observes a NEW Lead from Source A and assigns it a significantly lower weight than it would have at Tick 0.

## 3. Structured Explainability (Milestone 4)

We will standardize the `StrategicDriver` labels and descriptions to ensure they are first-class contracts, not just "magic strings" in the brain logic.

Standard Reason Labels:
- `RETAIN_PROJECT`: Logic for staying on current goal.
- `SWITCH_PROJECT`: Logic for switching to a higher-priority rival.
- `SUSPEND_PROJECT`: Logic for dropping a project due to capacity/threats.
- `RESUME_PROJECT`: Logic for picking up a previously suspended project.

## 4. Contradiction & Uncertainty (Milestone 5)

Contradiction handling will be implemented at the knowledge ingestion layer. 
- If Evidence A (Location X) conflicts with Evidence B (Location Y), the **Uncertainty Hypothesis** will split or lower confidence rather than overwriting.
- **Drift Guard**: `StrategicUpdate` must never emit exact coordinates from conflicting, un-investigated rumors.

## 5. Truth-Surface Overlap Guards (Milestone 6)

We will add a "Parity Intent" check to `src/testing/assertions.py`.
- If a new field is added to `StrategicState` but is NOT marked for Replay Comparison, the assertion layer will require explicit documentation/exclusion.
- Prevents "invisible drift" where we think we are testing everything but are actually skipping new fields.
