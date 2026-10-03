---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-ORACLE-MAP-REPORT
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261003-SOCIAL-ORACLE-MAP-REPORT

Report only. Reviewed as the ticket text by test-architecture-reviewer on 2026-10-03.

1. Read `docs/parity_ledger/social_narrative.yaml` with a read-only script (counts by status and priority; P0 entries with no `test_path`; the divergent and missing entries; whether each cited test file exists).
2. Re-check at the measured SHA: `appraisal.py` lines 46 and 64 (reputation reads), whether `reputation.py` has a direct importer under `tests/unit/social/`, and whether `docs/mechanics/07_social_political_dynamics.md` is in CLAUDE.md's Bible table.
3. Write section 3 of `docs/testing/social_test_report_2026-10-03.md`: the P0-without-`test_path` id list, SOC-052, SOC-242/263/265, the ch07 gap, the CONFLICTING lines, `reputation.py` as a coverage gap.
4. Send one routing message to `rpg-feature-planning` covering sections 1 and 3 and record its date.

Scope guards: no ledger edit, no proposed link list, no mechanism-to-test links, no test touched; party, `memory.py`, perception and dormant paths excluded.
