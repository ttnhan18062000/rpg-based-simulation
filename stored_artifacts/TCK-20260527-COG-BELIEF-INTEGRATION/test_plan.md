---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-BELIEF-INTEGRATION
artifact_type: test_plan
tags: [cog, belief, integration]
---

# Test Plan - TCK-20260527-COG-BELIEF-INTEGRATION

We will verify that beliefs are created correctly, direct observations update certainty, contradictions decrease utility, and detours factor in both certainty and source trust.

## Scenarios to Test

### 1. Guild Intel Rumors
- Hero visits the guild.
- Assert a `BeliefEntry` of source `"rumor"` is created with low certainty (`0.3` or `LeadCertainty.VAGUE`).

### 2. Direct Observation confirms threat
- Entity reaches target location where threat is present.
- Assert belief is upgraded to certainty `1.0` / `LeadCertainty.PRECISE`.
- Assert `BeliefUpgraded` event trace is logged.

### 3. Contradiction degrades certainty
- Entity reaches target location where threat is absent.
- Assert belief is demoted and contradiction count is incremented.
- Assert `BeliefContradicted` event trace is logged.
- Assert lead is suppressed.

### 4. Detour Selection weights source trust & certainty
- Construct two competing rumors with different source trust scores.
- Assert the rumor with the higher source trust gets selected as the detour project.
- Confirm that once a rumor is contradicted, its detour score drops drastically so it is not repeatedly pursued.
