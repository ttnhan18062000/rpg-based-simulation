# Implementation Plan - Phase 1 Opportunities

## Proposed Changes

### Component: Opportunity Providers
#### [NEW] [resources.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/providers/resources.py)
- Implement `Opportunity` schema and `ResourceOpportunityProvider`.

#### [NEW] [services.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/providers/services.py)
- Implement `ServiceOpportunityProvider` resolving shop, blacksmith, guide, guild, inn options.

#### [NEW] [test_opportunities.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/strategic/test_opportunities.py)
- Write unit tests verifying resource/service opportunity mapping and caps bounds.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/strategic/test_opportunities.py`
