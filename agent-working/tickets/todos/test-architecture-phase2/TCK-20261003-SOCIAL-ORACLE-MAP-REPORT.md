---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-SOCIAL-ORACLE-MAP-REPORT
phase: open
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-SOCIAL-ORACLE-MAP-REPORT

## Title
Phase 2 social item 3 (Oracle map): map social tests to `social_narrative.yaml` ids, P0 first, report only

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary

Phase 2 plan §6 item 3. Map the social tests to the ids in `docs/parity_ledger/social_narrative.yaml`,
P0 first, and report what the map shows. **Report only: no ledger edit, no proposed link list, no
mechanism-to-test link.** Findings go to `rpg-feature-planning`.

## Scope

1. A findings record (a new doc under `docs/testing/`, named at plan review) listing, with full
   `origin/main` SHA and date:
   - the P0 entries without a `test_path` (211 of 227 at `2f520f0dd`; re-counted), as a list;
   - the 3 divergent entries (SOC-242, SOC-263, SOC-265) and the 1 missing entry (SOC-052, P0);
   - the ch07 Bible-table gap (`docs/mechanics/07_social_political_dynamics.md` is not in CLAUDE.md's
     Bible table; owned by `rpg-feature-planning`, raised already);
   - the `appraisal.py` lines 46 and 64 reputation-read behaviour, labelled "current behaviour,
     catalog-CONFLICTING" (PERC-01 / KNOW-01), re-checked at the measured SHA;
   - `reputation.py` as a coverage gap (no direct importer under `tests/unit/social/`).
2. Each finding routed to `rpg-feature-planning` by a message, recorded with date.

## Out of Scope

- Applying or proposing ledger status changes or `test_path` links (the owner chose report-only).
- Creating mechanism-to-test links in the mechanism registry.
- Any test edit, move, marker or deletion (owner constraint, 2026-10-03).
- party*.py, memory.py, perception, dormant paths.

## Acceptance Criteria

- [ ] `git diff --name-only` against `origin/main` shows no test file and no
  `docs/parity_ledger/` file.
- [ ] Every list item carries its ledger id and is reproducible from a stated command.
- [ ] The counts are re-measured at the stated SHA, and any difference from the plan's
  `2f520f0dd` figures is stated.
- [ ] The CONFLICTING lines are labelled as above and not called bugs or fixes.
- [ ] The record carries the RELATIONSHIP-VECTOR staleness line.
- [ ] A routing message to `rpg-feature-planning` was sent and is recorded, and no reply is claimed
  that was not received.

## Related Tickets

- Parent: `TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL`.
- Overlap to respect: `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD`, `TCK-20260822-SOCIAL-MEMORY-DECISION-CONTEXT`.

## Related Docs

- `docs/plans/test_architecture/phase2_social_scale_out.md` §3 and §6 item 3
- `docs/parity_ledger/social_narrative.yaml`
- `docs/world_rules/social-lineage/`

## Related Stored Artifacts

None.

## Related Code Areas

- `src/systems/social_systems/appraisal.py`, `reputation.py` (read only)
- `tests/unit/social/` (read only)

## Assumptions / Open Questions

- Mapping a test to an id is by the ledger's own `test_path` plus direct imports; where only a name
  match exists it is listed as unverified, not as a link (name matching is not a path).
- The id-level map is read from the ledger, not inferred by a tool.

## Implementation Notes

All figures re-measured at the then-current `origin/main`, with the full SHA.

## Test Summary

Not run yet.

## Files Changed

None yet.

## Completion Summary

Not complete.
