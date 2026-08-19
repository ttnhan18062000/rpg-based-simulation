---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP
phase: open
date: 2026-08-19
tags: [ai, documentation]
---

# TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP

## Title
Parity ledger hygiene: fix 2 malformed entries, triage stale file citations, archive orphaned predecessor checklist

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
High-level health investigation of `docs/parity_ledger/*.yaml` (2,047 entries, 9 subsystems),
using the existing `tools/parity_index.py` SQLite query tooling rather than raw YAML reads.
Overall health is good — 98.8% verified/legacy_verified, no duplicate IDs. Four concrete,
independently-actionable findings surfaced, each population-level (not anecdotal):
1. Exactly 2 of 2,047 entries (`TOWN-040`, `TOWN-041`) are malformed — every evidence field empty,
   degenerate fixture-name-leak text. Isolated anomaly, not a pattern (the `` `test_name`:
   description `` format itself is a real, widespread, correct convention elsewhere).
2. 173 `absent_file` health findings (paths cited in the ledger that don't resolve on disk) — a
   mix of checker imprecision (frontend paths missing a `dashboard-frontend/` root, prose mentions
   of intentionally-deleted files) and likely-genuine drift, concentrated in 120 `test_refs` hits
   that plausibly reflect real test-file moves.
3. 1,552 of 2,047 entries (76%) lack machine-parseable structured references
   (`legacy_unstructured`) — can't power the tooling's own `impact` blast-radius query. Real, but
   large — flagged out of scope for this ticket.
4. `docs/logic_checklist_exhaustive.md` (3,197 lines) is the confirmed historical predecessor of
   the parity ledger itself — its own already-archived design spec describes the exact migration
   into today's ID scheme. Last touched 2026-07-02, 5 support scripts wired into neither `Makefile`
   nor CI, one dangling internal reference to a nonexistent filename variant. Never archived.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- Fix (or remove, if unrecoverable) the 2 malformed entries.
- Triage the 173 `absent_file` findings — fix genuine drift, fix or flag the checker's own
  frontend-root resolution gap, distinguish narrative mentions from live citations. Do this
  **after** `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING` lands (it's actively moving 61 test
  files as of this investigation — triaging against a moving target wastes effort).
- Archive `docs/logic_checklist_exhaustive.md` and its 5 orphaned support scripts; fix the
  dangling filename reference in `src/engine/rpg_depth.py`.

## Out of Scope
- Retrofitting the 1,552 `legacy_unstructured` entries with structured references — large,
  speculative, separate effort; not broken, just less automatable.
- Any change to `docs/parity_ledger/schema.json`.

## Acceptance Criteria
- [ ] No entry in the ledger has every evidence field empty (down from 2).
- [ ] `absent_file` count meaningfully drops from the 173 baseline, with each remaining/fixed hit
      triaged (not blindly suppressed).
- [ ] The orphaned checklist system (`docs/logic_checklist_exhaustive.md` + 5 scripts) is
      archived, not just noted as orphaned.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line this
  session's investigations belong to)
- TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING (its in-flight test-file moves are directly
  relevant to finding 2's `test_refs` triage — implement after this one lands)
- TCK-20260817-DEAD-INFRA-REMOVAL-EPIC (source of the correctly-`unsupported` broker entries noted
  as context, not a finding, in this ticket's investigation)

## Related Docs
- tools/parity_index.py
- docs/archive/specs/2026-05-03-checklist-governance-design.md
- docs/logic_checklist_exhaustive.md
- docs/parity_ledger/*.yaml

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP/

## Related Code Areas
- docs/parity_ledger/town_resource.yaml
- tools/parity_index.py (`_populate_entry_health`)
- docs/logic_checklist_exhaustive.md
- scripts/validate_checklist.py, scripts/ledger_validator.py, scripts/remediate_checklist.py,
  scripts/report_coverage.py, scripts/apply_traceability.py
- src/engine/rpg_depth.py (dangling filename reference)

## Assumptions / Open Questions
- Whether any of the 5 orphaned scripts contain logic worth preserving as reference (vs. pure
  duplication of what `tools/parity_ledger_scan.py`/`writer.py`/`index.py` now do) is left to the
  implementer's judgment.
- Exact count of genuinely-fixable `absent_file` hits (vs. checker false positives) wasn't
  determined here by design — population-level counts only, per this investigation's explicit
  high-level scope; per-item triage is the implementer's job.

## Implementation Notes
(pending — implementation by a separate agent, per this ticket's own scope)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
