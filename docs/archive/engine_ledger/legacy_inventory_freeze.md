---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 6 Legacy Inventory Freeze

This document marks the formal freeze of the **Authoritative Replacement Ledger** inventory. This inventory represents the consolidated surface of the legacy `src` system that must be addressed during Phase 6 and Phase 7.

## Freeze Details

- **Freeze Date**: 2026-04-21
- **Snapshot Version**: Initial Phase 6 Baseline
- **Ledger Path**: [legacy_replacement_ledger.md](../engine_ledger/legacy_replacement_ledger.md)
- **Total Rows**: 185 (RPG-CORE: 165, SYS-COMPAT: 20)

## Inventory Summary

The inventory has been consolidated from 5 legacy checklists:

1. **RPG-CORE Semantic Surface**: Covers Actions, Combat/Movement, Resource Interaction, Strategic AI, Social, and World/Engine logic.
2. **SYS-COMPAT Compatibility Surface**: Covers CLI, Infrastructure fallbacks (Broker-disabled), Replay contracts, and API/Transport protocols.

## Post-Freeze Protocol

1. **Comparison Target**: All subsequent replacement tasks (Phase 6 Milestone 3+) must reference the IDs in this frozen ledger.
2. **Modifications**: Silent edits to row IDs or items are prohibited. Any missing scope discovered later must be added as a "Correction" row with a rationale.
3. **Auditability**: Every row is anchored to legacy `src` source or `tests` evidence as defined in the checklists.

## Verification

The ledger integrity was verified on 2026-04-21 via structural link audits and spot-checks against the source checklists.
