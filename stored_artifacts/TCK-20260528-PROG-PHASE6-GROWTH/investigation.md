---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260528-PROG-PHASE6-GROWTH
artifact_type: investigation
tags: [prog, phase6, growth]
---

# Investigation: Phase 6 — Progression / Equipment / Reward Conversion

This document tracks technical findings and codebase integration points for Phase 6.

## Core Findings

- **Shop & Blacksmith Transactions**: Blacksmith crafting and Shop transactions rely on `ResourceTransferIntent`. These already have full authoritative validity checks, which we must not duplicate.
- **AP/XP Allocation**: AP and level attributes exist on `IdentityComponent` and are updated during authoritative evolution.
- **Proximity check**: Blacksmiths and shops are modeled as map locations. Proximity coordinates dictate whether a MOVE_TO intent is generated.
- **Personality modifiers**: greed, bravery, sociability, and industry are derived from `PersonalityComponent`.
