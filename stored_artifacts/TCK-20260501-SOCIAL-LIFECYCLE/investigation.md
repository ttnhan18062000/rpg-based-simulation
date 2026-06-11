---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260501-SOCIAL-LIFECYCLE
artifact_type: investigation
tags: [social, lifecycle]
---

# Investigation: Social Contract and Party Lifecycle

## Current State Audit
- **Contracts**: Existing `ContractState` in `src/core/social.py` has basic fields but limited status transitions.
- **Parties**: Currently created through `PartyCoordinationSystem.form_party`, but not strictly linked to a durable `ContractState`.
- **Appraisal**: `SocialAppraisalSystem` handles trust recalibration but doesn't have an "offer evaluation" layer yet.
- **Propagation**: Shared objectives are currently proximity-based or forced. Need a structured "Directive" distribution path.

## Architectural Constraints
- Social changes MUST use `SocialUpdate` through the authoritative pipeline.
- Contracts MUST have unique IDs and be registered in both the initiator's and receiver's `SocialComponent`.
- Party membership should be a "read model" derived from active cooperative contracts to ensure atomicity.

## Key Challenges
- **Betrayal Detection**: Defining what constitutes a betrayal (e.g., leaving a party during combat, not sharing loot).
- **Coordinate Convergence**: Ensuring party members don't "oscillate" between their own goals and the party goal.
