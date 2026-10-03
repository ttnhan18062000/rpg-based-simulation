---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: c6306454-56e4-4a14-b03f-7fc75ea22c2d
artifact_type: investigation
tags: [c6306454, 56e4, 4a14, b03f, 7fc75ea22c2d]
---

# Investigation - Tactical Combat Hardening

## Overview
The investigation focused on why `resolve_multi_attack` in `CombatResolutionSystem` was not applying tactical bonuses (flanking, high ground, etc.) compared to the single `resolve_attack` method.

## Findings
1.  `resolve_attack` contained inline logic for calculating tactical multipliers.
2.  `resolve_multi_attack` lacked this logic entirely, only summing raw damage from `calculate_damage`.
3.  `calculate_damage` is a pure math function and does not check state for tactical context.
4.  `LegalityServiceV2` provides the necessary geometric checks (`check_flanking`, `check_high_ground`, `check_cover`).
5.  `StaminaService` and `SocialUpdate` also influence the final damage but were inconsistently applied in multi-attack scenarios.

## Conclusion
The logic needs to be extracted into a reusable component that can be called by both single and multi-attack resolvers. This ensures "Authoritative Truth" parity across all combat interactions.
