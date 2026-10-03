---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260426-PH15-SOCIAL-BONDS
phase: done
date: 2026-04-26
tags: [ph15, social, bonds]
---

# TCK-20260426-PH15-SOCIAL-BONDS

## Title
Implement First-Class Social Bonds

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Replace the simplified 'Trust Proxy' model with a first-class SocialBond system in the V2 engine.

## Scope
- Add SocialBond dataclass to state schema.
- Update SocialComponent to include a bonds registry.
- Refactor SocialAppraisalSystem to track Familiarity and Sentiment.
- Update recruitment evaluation to use bonds.

## Acceptance Criteria
- Interaction depth (Familiarity) and directed bias (Sentiment) are tracked independently.
- Recruitment cost scales with bond sentiment.
- 100% parity with legacy "Must-Have" social logic.

## Related Tickets
- None

## Related Docs
- legacy_logic_coverage_report.md

## Implementation Notes
- Sentiment is mapped from [-1, 1] for bond tracking.
- Recruitment evaluation prefers bonds over trust history if available.

## Test Summary
- tests/social/test_social_bonds.py (PASSED)
- tests/social/test_source_trust.py (UPDATED & PASSED)

## Files Changed
- src/core/state.py
- src/core/updates.py
- src/social/relationships.py
- src/systems/social.py

## Completion Summary
Total recovery of legacy social bonds logic. First-class directed relationships are now authoritative in V2.
