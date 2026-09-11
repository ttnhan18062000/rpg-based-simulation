---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD
phase: open
date: 2026-09-11
tags: [architecture]
---

# TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD

## Title
`unregister_campaign()`/`unregister_chronicle()` are dead — the cleanup half of a register/
unregister pair, never called anywhere, including their own tests

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found during `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (`docs/audits/
unreachable_code_inventory.md`, Cluster C4). `src/api/routes/campaigns.py` and `src/api/routes/
chronicle.py` each declare an in-memory dict registry (`_CAMPAIGN_REGISTRY`, `_CHRONICLE_REGISTRY`)
with a `register_X()`/`unregister_X()` function pair. `register_campaign()`/`register_chronicle()`
are genuinely called — from `tests/api/test_campaign_history_api.py` and `tests/api/
test_chronicle_api.py`, injecting state for API tests. `unregister_campaign()` (`campaigns.py:56`)
and `unregister_chronicle()` (`chronicle.py:52`) have **zero call sites anywhere** — not in `src/`,
not in either test file, not anywhere in `tools/`. Confirmed directly: both test files' own
docstrings say cleanup uses a separate `_clear_registry()` function instead
(`"Inject CampaignState via register_campaign() / _clear_registry()."`).

Fully verified, narrow, and low-risk — this is the cleanup half of a register/unregister pair that
was written but never wired to any real teardown path, in production or in tests.

## Scope
- Confirm `_clear_registry()` (or its per-file equivalent) genuinely covers the same cleanup need
  `unregister_campaign()`/`unregister_chronicle()` were presumably meant to serve, before deciding
  disposition.
- If `_clear_registry()` fully covers it: delete `unregister_campaign()`/`unregister_chronicle()`
  as confirmed-redundant dead code.
- If there's a real gap `_clear_registry()` doesn't cover (e.g. per-campaign/per-chronicle
  selective cleanup, as opposed to a full registry wipe): wire the existing `unregister_X()`
  functions into whatever real call site should be using them instead of deleting them.

## Out of Scope
- Any other cluster from the same audit — each has, or will have, its own ticket.
- `register_campaign()`/`register_chronicle()` themselves — already confirmed live via test usage,
  not part of this finding.

## Acceptance Criteria
- [ ] `_clear_registry()`'s own real cleanup scope is confirmed (full-wipe vs. selective) before
      deciding disposition.
- [ ] `unregister_campaign()`/`unregister_chronicle()` are either deleted (confirmed redundant) or
      wired into a real call site (confirmed genuine gap), with rationale recorded either way.
- [ ] No regression in `tests/api/test_campaign_history_api.py`, `tests/api/test_chronicle_api.py`.

## Related Tickets
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (origin — Cluster C4)

## Related Docs
- `docs/audits/unreachable_code_inventory.md` (Cluster C4's own writeup)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/api/routes/campaigns.py` (`register_campaign()`, `unregister_campaign()`,
  `_CAMPAIGN_REGISTRY`)
- `src/api/routes/chronicle.py` (`register_chronicle()`, `unregister_chronicle()`,
  `_CHRONICLE_REGISTRY`)
- `tests/api/test_campaign_history_api.py`, `tests/api/test_chronicle_api.py` (both reference
  `_clear_registry()` in their own docstrings as the real cleanup mechanism)

## Assumptions / Open Questions
None — scope is a straightforward, well-evidenced hotfix once picked up.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
