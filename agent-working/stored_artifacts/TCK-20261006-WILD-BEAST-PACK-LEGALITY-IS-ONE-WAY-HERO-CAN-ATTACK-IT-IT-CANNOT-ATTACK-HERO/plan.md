---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO
phase: done
date: 2026-10-07
tags: [world, combat, legality]
---

# Plan

1. `LegalityServiceV2._attack_permitted` decides the pair symmetrically under the designer's three-case rule (both declare: either hostile; one declares: its verdict decides both ways; neither: legacy different-faction fallback). `_declares` = perspective for the faction, or a relationship row toward the other.
2. Map wolf, slime, bear, harpy, golem to `wild_beast_pack` in `SPAWN_KIND_CATALOG_FACTION`.
3. Tests pin both directions (spawned wolf/bear/golem, rules 1/2/3), and the existing defected-neutral pin stays unchanged.
4. Matrix over 16 factions, 24-world before/after, bench before/after, docs/parity/DEV-016.

Scope guards: no edit to `kernel.py` or `state.py`; no catalog content change; decision layer untouched (contextual engagement stays parked, memo row 7). Planner sign-off 2026-10-07 for the general rule (6 non-wild flips) and, from the designer, for the three-case rule that resolves the 58 asymmetric verdicts.
