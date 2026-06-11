---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260424-PH12-M1-READINESS
artifact_type: investigation
tags: [ph12, m1, readiness]
---

# Phase 12 M1 Investigation: Cutover Surface Audit

## Ratified Allowed Surface (from Phase 11)
- **Movement**: 100% Bit-identical parity.
- **Resource**: Harvest/Loot (Item Registry capped).
- **Strategic**: Bounded Cognition (Redirection System).
- **Social**: Recruitment (SocialComponent).
- **Combat**: Legal Moves only (LegalityService LoS).
- **System**: CLI/REST/WS protocols.

## Divergence Constraints
- AI "Attention Limits" are intentional.
- `ILLEGAL_MOVE` rejection is mandatory.
- Lowercase normalization required for inputs.

## Unsupported Scope
- XP / Leveling logic.
- RNG-based combat variance.
- Territory ownership.

## Findings
- The `src` engine is architecturally isolated via the `V2EngineManager`.
- Most unsupported logic is already "No-Op" or explicitly bypassed in `src`.
- The transition to "operational default" requires ensuring all CLI/API entrypoints point to `src` by default in Milestone 2.
Supported Rows: 145
Constrained Rows: 39
