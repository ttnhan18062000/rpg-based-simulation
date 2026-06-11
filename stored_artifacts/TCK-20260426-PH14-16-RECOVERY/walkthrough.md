---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [ph14, recovery]
---

# Walkthrough: Closing the Parity Gap (Phases 14-16)

This walkthrough documents the final recovery of critical RPG-core logic, achieving 100% parity for the V2 engine.

## 1. Multi-Attacker Opportunity Attacks (Phase 14)

### Changes
- Updated `LegalityServiceV2.get_engaged_hostiles` to return all adjacent hostiles sorted by ID.
- Extended `CombatUpdate` and `CombatIntent` to support multiple simultaneous attackers.
- Updated `MovementSystem.resolve_move` to detect all hostiles on egress and generate a multi-intent update.

### Validation
Verified that a hero moving out of engagement with 3 monsters takes damage from all 3 in a single tick.

```bash
pytest tests/parity/test_multi_oa_parity.py
```

## 2. First-Class Social Bonds (Phase 15)

### Changes
- Added `SocialBond` dataclass to `src/core/state.py`.
- Updated `SocialComponent` to include a `bonds` registry.
- Refactored `SocialAppraisalSystem` to track `familiarity` and `sentiment` separately, removing reliance on trust proxies.
- Updated recruitment costs and evaluation logic to prioritize bond sentiment.

### Validation
Verified that social learning updates directed bonds and affects recruitment costs.

```bash
pytest tests/social/test_social_bonds.py
```

## 3. Advanced Combat & AoE (Phase 16)

### Changes
- Added `verify_aoe_legality` to `LegalityServiceV2`.
- Added `resolve_aoe_attack` to `CombatResolutionSystem`.
- Implemented splash damage resolution in `ApplyPath.apply_generation` (pre-loop calculation and application).

### Validation
Verified that an AoE attack at a target position deals primary damage and splash damage to all neighbors in range.

```bash
pytest tests/combat/test_aoe_splash.py
```

## Final Status: 100% Parity Achieved
The [legacy_logic_coverage_report.md](file:///home/vboxuser/Work/rpg-based-simulation/legacy_logic_coverage_report.md) now reflects total recovery of all "Must-Have" features.
