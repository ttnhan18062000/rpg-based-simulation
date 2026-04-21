# Phase 6 Differential Gap Report

This report identifies the authoritative logic gaps between the Frozen Legacy Inventory and the Current-State audited `src_v2` engine.

## Gap Summary

| Area | Total Legacy Items | V2 Implemented | Absolute Gaps | Maturity Gaps |
| :--- | :--- | :--- | :--- | :--- |
| **RPG-CORE** | 165 | 29 | 115+ | 15 |
| **SYS-COMPAT**| 20 | 15 | 5 | 0 |
| **TOTAL** | 185 | 44 | 120+ | 15 |

## Identified Gaps

### Absolute Gaps (Missing Logic)

These items exist in the legacy logic but have no corresponding implementation in `src_v2`.

#### RPG-CORE: Social & Strategic Cognition
- **Social Trust & Betrayal**: LEG-RPG-049 to LEG-RPG-056. trust-weighted resolution, betrayal history, public vs private reputation.
- **Recruitment & Contracts**: LEG-RPG-124, LEG-RPG-056. काउंटर-offer thresholds, social recruitment evaluations.
- **Genetic/Innate Talents**: LEG-RPG-144, LEG-RPG-154. Training rate multipliers, innate talent scaling.
- **Calamity & Hazards**: LEG-RPG-071, LEG-RPG-139. Regional hazards, calamity evolution.

#### RPG-CORE: Combat Depth
- **Directional Bonuses**: LEG-RPG-091, LEG-RPG-092, LEG-RPG-158. High ground, Flanking, Backstab.
- **Opportunity Attacks**: LEG-RPG-099, LEG-RPG-017 (Partial). Disengagement consequences.
- **Environmental Cover**: LEG-RPG-094, LEG-RPG-075. Cover seeking, ranged cover bonus.

#### RPG-CORE: Progression & Scaling
- **XP & Level Up**: LEG-RPG-061, LEG-RPG-126 to LEG-RPG-129. Level up gating, milestone stats, veterancy ranks.
- **Skill Breakthroughs**: LEG-RPG-060, LEG-RPG-133. Scaling thresholds, breakthrough application.

### Maturity Gaps (Sub-Par Verification)

These items are implemented in `src_v2` but are marked as `DIVERGENT` or `PARTIAL` due to limited verification or changed semantics.

- **LEG-RPG-017**: Disengagement/OA. Currently "Partial" as the OA trigger contract is missing from movement resolution.
- **LEG-RPG-041/107**: Detour/Search Breadth. Capped in V2 to preserve performance (DIVERGENT from legacy depth).
- **LEG-RPG-110**: Cognitive Overload. V2 uses a hard profile cap (DIVERGENT from legacy adaptive intake).

---

## Triage & Roadmap

| ID | Item | Priority | Triage Target |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-049** | Social Trust/History | **P0** | Phase 6 (Milestone 5) |
| **LEG-RPG-099** | Opportunity Attacks | **P0** | Phase 6 (Milestone 5) |
| **LEG-RPG-061** | Combat XP/Rewards | **P1** | Phase 6 (Milestone 6) |
| **LEG-RPG-071** | Calamity Evolution | **P2** | Phase 7 Roadmap |
| **LEG-RPG-143** | Entity Archetype Mutation| **P2** | Phase 7 Roadmap |

## Approval for Phase 6 Priority

> [!IMPORTANT]
> The P0 items identified above represent the "Must Have" features for Phase 6 to satisfy the Replacement Entry Gate. Implementing the Social Trust baseline and OA mechanics will close the primary "Decorative Implementation" risks identified in this audit.

---
*End of Gap Report*
