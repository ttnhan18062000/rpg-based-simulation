---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET

## Title
Validate the parity ledger data against schema.json in CI, with a non-increasing error baseline

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Requested by the owner via perf-planner (2026-10-03). docs/parity_ledger/*.yaml (2,197 entries) gives 2,862 errors against docs/parity_ledger/schema.json on main (planner reproduction: 1,312 from allOf/0 'verified/divergent requires test_path', 1,525 from allOf/2 'P0 requires test_path', 25 proof_type values outside the enum). No test validates the data: tests/tools/test_parity_ledger_schema.py checks only the schema file, and parity_ledger_writer.validate_entry runs only on writes. Add a CI check that fails on any new or additional error, without loosening the schema.

## Scope
- A small checker (in `codebase/health/` or `codebase/gates/`, following the root-move ticket) that validates each ledger file with jsonschema Draft 7 against schema.json and counts errors per (file, rule), where rule = the failing schema path
- Committed baseline `codebase/baselines/parity_ledger_schema_baseline.json` holding those counts; the check fails when any (file, rule) count rises or a new (file, rule) appears, and reports decreases so the baseline can be tightened (a `tighten` command, like the ratchet's)
- A test in the static or docs lane runs the check on every PR (blocking from the start: the ledger is docs-domain data with no soak decision pending; say so if Investigate finds a reason to soak)
- Document the check and the tighten rule in the parity-ledger docs

## Out of Scope
- Changing schema.json in any way (no loosening; the proof_type enum decision belongs to the owner and the remediation epic)
- Fixing any ledger entry (TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC)
- Changing parity_ledger_writer.validate_entry, except to share code with the checker if that is clearly simpler

## Acceptance Criteria
- [ ] On main's ledger the checker reports 2,862 errors split as above (or the current count, recorded), and the committed baseline matches it
- [ ] Adding one entry with status verified and test_path null makes the test fail and names the file and rule; removing an existing error passes and reports the decrease
- [ ] schema.json is byte-identical to main
- [ ] The test runs in a CI job (coverage test passes); green PR run recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC
- TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL
- TCK-20260902-PARITY-TEST-PATH-GAP
- TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP
- TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE (depends on)

## Related Docs
- docs/parity_ledger/schema.json
- docs/parity_ledger/README (or the ledger doc that describes the schema)

## Related Stored Artifacts
None.

## Related Code Areas
- docs/parity_ledger/*.yaml, schema.json
- tests/tools/test_parity_ledger_schema.py
- tools/parity_ledger_writer.py

## Assumptions / Open Questions
- The ledger itself is owned by the domains whose mechanics it records (mostly rpg); this ticket adds a check over it, not content
- PR #306 surfaced the gap (infrastructure.yaml alone has 330 errors per perf-planner)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
