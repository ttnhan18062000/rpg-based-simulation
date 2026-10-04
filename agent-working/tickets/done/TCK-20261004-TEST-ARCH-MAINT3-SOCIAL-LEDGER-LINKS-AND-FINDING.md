---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING
phase: done
date: 2026-10-04
tags: [testing]
---

# TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING

## Title
Social ledger: link the entries whose tests genuinely match, and record the evidence-shape finding

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary

User decision 2026-10-04, "Link 4 + record", relayed in the maintenance-3 brief (T2): link `test_path` for SOC-010,
SOC-011, SOC-013 and SOC-058 only where the test genuinely asserts what the entry claims and passes; append a
report addendum with the re-derived ledger counts and the `_appraise_position_swap` weak-oracle line; add two
deferred items to roadmap section 11.

## Scope

- (a) `docs/parity_ledger/social_narrative.yaml`: `test_path` for the entries that pass the read-and-run check,
  written through `tools/parity_ledger_writer.py`; no test, status, `v2_evidence` or other entry touched.
- (b) New section 7 in `docs/testing/social_test_report_2026-10-03.md` (section 6 is taken by the 2026-10-03
  addendum): the re-derived counts, the link decisions with reasons, and the `_appraise_position_swap` line.
- (c) `docs/plans/test_architecture/roadmap.md` section 11: two deferred items (social P0 evidence re-verification
  and relocation of misfiled entries, trigger owner decision; `src/testing/` moving under test support, trigger `src/`
  reopening, agreed on PR #322).

## Out of Scope

- Editing any test; changing any entry's status, text or `v2_evidence`; re-verifying or relocating any other P0
  entry; any `src/` change; deciding whether `POSITION_SWAP` is unfinished or dead (held by `rpg-feature-planning`).

## Acceptance Criteria

- [x] Each candidate was read against its test and the test was run; only matching entries linked, the others left
  unlinked with the reason recorded.
- [x] The ledger diff is exactly the linked `test_path` lines (the writer's unrelated YAML re-wrap was reverted by hand).
- [x] The counts were re-derived at the base and any drift reported (none).
- [x] Roadmap section 11 has the two items with their triggers.

## Related Tickets

- `TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN` (the section 6 addendum, same report)
- Siblings: `TCK-20261004-TEST-ARCH-MAINT3-EPIC-B-COST-ROWS-AFTER-306`,
  `TCK-20261004-TEST-ARCH-MAINT3-API-SERVER-READINESS-POLL`,
  `TCK-20261004-TEST-ARCH-MAINT3-DECISION-TRACE-VACUOUS-ASSERT`

## Related Docs

- `docs/testing/social_test_report_2026-10-03.md` sections 3, 4, 7
- `docs/plans/test_architecture/roadmap.md` section 11
- `docs/parity_ledger/social_narrative.yaml`

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING/`

## Related Code Areas

- `tools/parity_ledger_writer.py` (used, not changed); the four candidate tests (read and run, not changed)

## Assumptions / Open Questions

- **Two of the four were not linked.** SOC-013's text says the mutation "raises a RuntimeError" but the test asserts
  `ReadOnlyError`/`TypeError`/`FrozenInstanceError`/`AttributeError` (`ReadOnlyError` subclasses `TypeError`).
  SOC-058's text says "for all members" but the test asserts only `social_ups[0]` and `social_ups_b[0]`, never the
  target's update. Linking either needs the entry text corrected or a test extended, which this brief forbids; the
  owner or the ledger owner can decide.
- The keyword count (about 90 of 211 mention a social term) is an estimate from a regex; 91 with the one used here.
- `search_docs` returned nothing relevant and graphify had no graph in this worktree; not a gate.

## Implementation Notes

The counts were derived by a script over the committed YAML and `git grep` over `tests/` at the base
`bec0b2b856e5f734346304296ecb9e490d5a241d` and again at `3eae2e25058b36cdd6013d0491b155d7b6dad154`: identical, so
no drift against the reviewer's figures. The reviewer's `test_shared_gate_no_fallthrough_for_gated_kinds` claim was
checked by reading the test (empty `terms` for `POSITION_SWAP`, asserts only `reason != UNKNOWN`). The writer's
`safe_dump` re-wrapped one unrelated entry's text; that whitespace-only change was reverted so the diff is the two
`test_path` lines.

## Test Summary

All four candidate tests were run: 4 passed. Docs and ledger only; no test or `src/` change in this ticket.

## Files Changed

- `docs/parity_ledger/social_narrative.yaml` (SOC-010 and SOC-011 `test_path`)
- `docs/testing/social_test_report_2026-10-03.md` (new section 7)
- `docs/plans/test_architecture/roadmap.md` (two section 11 rows)

## Completion Summary

Done 2026-10-04. SOC-010 and SOC-011 are linked; SOC-013 and SOC-058 are left unlinked with the reason recorded.
The report now records the ledger's evidence shape (211 of 227 P0 entries without a `test_path`, 210 on boilerplate
evidence, 111 of 115 named tests absent) and the `_appraise_position_swap` weak-oracle finding; the roadmap carries
the two deferred items.
