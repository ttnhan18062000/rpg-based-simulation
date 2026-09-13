# Plan — TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED

## Disposition (peer-reviewed and approved before closing)
Document the real state; build nothing. See investigation.md for the full declared-intent check —
Mechanics Bible is silent, and the two ledger/checklist citations that appeared to declare intent
are both themselves unsubstantiated (one names a dead V1 concept, the other cites a test file and
code line that don't exist/don't match). Wiring `get_stat_multiplier()` now would be inventing
gameplay, not completing a declared design.

## Steps
1. Correct `docs/parity_ledger/progression.yaml` `PROG-014` via `tools/parity_ledger_writer.py`:
   `status: verified` → `status: missing`, `support_boundary` recording the correction and citing
   the checklist.md cross-reference and this ticket.
2. Correct `docs/compliance/checklist.md` `PROG-086`'s stale citations in place: unchecked the box,
   noted the correction inline, fixed the TEST reference to the real file
   (`test_leveling_veterancy.py`), and stated plainly that its own line reference is unrelated code.
3. File `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` — record, don't run, a full-ledger
   sweep for the same defect shape (verified + null test_path), now confirmed three times in one
   file across two unrelated investigations.
4. Close this ticket: staging artifacts → stored_artifacts, ticket → tickets/done, working_log
   entry, docs/REGISTRY.yaml regen (docs/ changed — also run `make knowledge-index-update`), hand-
   orchestrated monitoring record.

## Scope guard
No code in `src/` changes — `get_stat_multiplier()` and `process_points()` are untouched. This
ticket only corrects documentation/ledger citations and records a follow-up sweep ticket.

## Acceptance-criteria map

| AC | Step |
|---|---|
| Re-verified zero callers for `get_stat_multiplier()` | investigation.md |
| Peer-routed decision obtained before any implementation | investigation.md (peer confirmed document-only) |
| No implementation (disposition is document-only) | N/A — nothing wired |
