---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING

1. For each of SOC-010, SOC-011, SOC-013, SOC-058: read the entry text and the named test, run the test, decide
   link or leave unlinked (link only if the test genuinely asserts the entry's claim).
2. Link the matching entries through `tools/parity_ledger_writer.py::write_entry` (never a hand-edited full-file
   rewrite). Check `git diff` afterwards and revert any unrelated re-wrap the YAML dump introduces.
3. Re-derive the ledger counts at the base with a script (committed YAML plus `git grep` over `tests/`); compare with
   the reviewer's figures and report any drift.
4. Append section 7 to `docs/testing/social_test_report_2026-10-03.md` (section 6 exists): counts table, link decisions,
   the `_appraise_position_swap` weak-oracle line (after reading the test it cites).
5. Add the two deferred rows to `docs/plans/test_architecture/roadmap.md` section 11.

Scope guards: no test edit, no status or `v2_evidence` change, no other entry touched, no `src/` change.
