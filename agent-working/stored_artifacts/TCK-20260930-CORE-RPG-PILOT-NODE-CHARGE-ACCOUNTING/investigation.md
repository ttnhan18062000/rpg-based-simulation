---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING
artifact_type: investigation
tags: [testing]
---

# Investigation

## Current Behavior
`src/core/conservation.py` lines 79-95: the NODE branch computes remaining charges as `node.remaining_charges` plus any same-tick `node_overrides` delta, minus in-tick `reservations`; at 0 it rejects with `SOURCE_DEPLETED`; otherwise the charge delta is `-remaining_charges` for `LOOT` nodes and `-1` for others. The pipeline accumulates reservations across intents in one `refine` call.

## Mechanics / Engine Constraints
`docs/mechanics/03_economic_laws.md` §3 (regular nodes lose 1 charge per harvest; loot nodes fully consumed on first success) and §1 (Atomic Conservation).

## Docs Requiring Update
- `docs/parity_ledger/town_resource.yaml`: `TOWN-122` gets a `test_path`.
- `docs/testing/core_rpg_test_pilot_2026-09-30.md`: the pilot report (new).

## Parity Ledger Overlap
`TOWN-122` (P0, verified, `test_path` was null). `TOWN-123` (corpse loot, same shape) is not covered here.

## Prior Work
Mutation baseline `tests/mutation/baselines/src_core_conservation.json` (Epic A): survivors at lines 82-91 justify the choice. The rejection-path family belongs to another ticket.

## Risks and Open Questions
- Stability of the surface is a scope-level confirmation only (see the pilot report caveats).
- `tests/tools/test_parity_index_baseline.py` reads the ledger; it still passes after the `test_path` addition.

## Anti-Drift Hazards
Do not assert on mutated source text; do not touch the baseline file; do not add rejection-path tests.
