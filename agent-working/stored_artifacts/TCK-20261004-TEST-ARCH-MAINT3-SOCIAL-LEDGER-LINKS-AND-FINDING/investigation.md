---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING

Context scan: `search_docs` returned nothing relevant to the question; graphify had no graph in this worktree.
Findings come from reading the ledger entries and tests directly.

## The four candidates

| Entry | Entry claim | Test asserts | Decision |
|---|---|---|---|
| SOC-010 | arena detects when one side is eliminated | `stop_condition == WIPE` on a one-faction-alive state | link |
| SOC-011 | arena respects the `max_ticks` limit | `stop_condition == TIMEOUT`, `final_state.tick == 110` after `ticks=10` from 100 | link |
| SOC-013 | mutating entities in the decision phase "raises a RuntimeError" | `readonly_view()` mutation raises `ReadOnlyError`, `TypeError`, `FrozenInstanceError` or `AttributeError` (`ReadOnlyError` is a `TypeError`) | leave unlinked: the stated exception is not asserted |
| SOC-058 | contract resolution returns correct updates "for all members" | `resolve_contract_outcome` source update (`social_ups[0]`, `social_ups_b[0]`), strategic status, avenge directive | leave unlinked: the target's update (`[1]`) is never asserted |

All four tests pass (4 passed).

## Counts (re-derived, identical at `bec0b2b85...` and `3eae2e25...`)

294 entries; 227 P0; 211 P0 without `test_path` (166 verified, 44 legacy_verified, 1 missing); 210 with the
boilerplate `v2_evidence`; 115 name a legacy test in backticks (4 resolve to exactly one current `def test_`,
111 to none, 0 to several); 96 name no test; keyword estimate 91.

## `_appraise_position_swap`

`test_shared_gate_no_fallthrough_for_gated_kinds` passes `{}` terms for `POSITION_SWAP` and asserts only
`reason != UNKNOWN`: a weak oracle. `POSITION_SWAP` is not created anywhere in `src/` (separate static check).

## Tool note

`write_entry` re-wraps YAML through `safe_dump`; one unrelated entry's text moved a line break. Reverted by hand.
