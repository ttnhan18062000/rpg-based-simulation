---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-PHASE1-INFORMATION
artifact_type: plan
tags: [cog, phase1, information]
---

# Implementation Plan - Phase 1 Information Provider

## Proposed Changes

### Component: Information Provider
#### [NEW] [information.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/providers/information.py)
- Implement `InformationQuery`, `InformationResponse`, `GuideInformationProvider`, `GuildInformationProvider`, and `BlacksmithInformationProvider` classes.

#### [NEW] [test_information.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/strategic/test_information.py)
- Write unit tests verifying Guide queries, secret material routing, and Gold cost evaluation.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/strategic/test_information.py`
