---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD
phase: open
date: 2026-10-10
tags: [testing, determinism]
---

# TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD

## Title
A committed local real-Aseprite proof record and a CI check that it is not stale (D10 kept)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. ADR D10 keeps real Aseprite off CI and shared machines; CI only states the skip count (tools/ci_aseprite_skip_line.py). Owner, 2026-10-10: keep D10; add a committed local proof record that CI checks.

## Scope
- **Design first (planner approves the guarded-path list and record shape).** `make visual-assets-aseprite-local` (strict, refuses to skip) writes a committed proof record: Aseprite version, commit, a content hash over the guarded paths (the code the `needs_aseprite` tests exercise: drawing tools, store build/exporter, those tests), pass/skip/fail counts, child 3's rc rebuild verdict.
- A CI-run test (no Aseprite) recomputes the guarded-path hash and fails when it differs from the record (message names the make target). The proof record excludes itself from the hash.
- `ci_aseprite_skip_line.py` summary line also states the proof record's commit and freshness.
- ADR: a D10 addendum (owner approves text) describing the proof record; D10's decision is unchanged.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- A self-hosted runner (owner declined, 2026-10-10).

## Acceptance Criteria
- [x] Guarded-path list and record shape approved by the planner; D10 addendum text by the owner.
- [ ] CI test fails on a changed guarded file and passes after a fresh local run (mutation proof).
- [ ] First record committed from a real local run.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions
- Depends on child 3 (rebuild verdict field).

## Implementation Notes
- **Planner approval (2026-10-10):** guarded-path list and record shape APPROVED with additions: keep the BROAD guarded set (all of `store/**` and `drawing/**` minus `*.md`; no ast import-closure); the runner writes the record ONLY for the full make target (any pytest selection, a path or node id, or a selecting `PYTEST_ADDOPTS` means no record and the runner says why); the CI failure message says the only fix is a real `make visual-assets-aseprite-local` run and the record is never hand-edited (the test docstring says the same).
- **Pieces:** `tools/visual_assets_aseprite_proof.py` (pure rules: guarded set, hash, compare, record validation, selection rule), `tools/visual_assets_aseprite_local.py` (writes `docs/assets/aseprite_local_proof.json` after a clean strict complete run), `tests/visual_assets/test_aseprite_local_proof.py` (CI, no Aseprite), `tools/ci_aseprite_skip_line.py` (the summary line also states the record's commit, version, date and match/DIFFER; reporting only, exit 0). Child 3's rebuild test writes its verdict JSON to `VISUAL_ASSETS_REBUILD_VERDICT_OUT` when the runner sets it.
- **Beyond the plan, same intent:** the runner also refuses to write a record when a guarded file is modified or untracked (the record names the commit the tests ran on, so a dirty tree would make `run_commit` untrue). The proof module builds the marker name from parts so it and its test are not "marked" (and so guarded) merely by naming it.
- **First record, from a real strict local run:** commit `9a4083372`, Aseprite 1.3.18.6-x64, 204 passed, 0 failed/errors/skipped, `pilot/rc-0008` rebuild 70 of 70 identical (0 bytes-differ), 108 guarded files, `guarded_hash sha256:f652cd57...`.
- **D10 addendum: written.** Owner decision, 2026-10-10, relayed by asset-planner from its blocking question (the owner's answer, verbatim): "Approve as written". The text of the plan is in `docs/architecture/visual_asset_foundation_adr.md` as "Addendum to D10 (2026-10-10)", exactly as the plan has it; D10's decision is unchanged.
- **Operational note for the batch:** the guarded set includes `visual_assets/store/**`, so any later store code change in this batch (children 7 and others) makes this record stale and the CI test fails until a fresh local run rewrites it. The record must be refreshed once, after the last store change, before the PR.

## Test Summary
- `tests/visual_assets/test_aseprite_local_proof.py`: 49 passed (guarded-set rules, hash and compare, 17 planted record violations each applied at one site, 10 selection cases and 5 full-target cases, the runner's refusals and its valid write, the committed record, and three comparison mutants: changed, added, removed file).
- Real end-to-end mutation: one byte appended to `visual_assets/store/pixels.py` made the CI comparison fail naming that file, the make target and "never edit that record by hand"; restored, 49 passed.
- Strict local run: 204 passed, 0 skipped (the first record).

## Files Changed
`tools/visual_assets_aseprite_proof.py` (new), `tools/visual_assets_aseprite_local.py`, `tools/ci_aseprite_skip_line.py`, `tests/visual_assets/{test_aseprite_local_proof (new),test_ci_aseprite_skip_line,test_release_byte_reproducibility}.py`, `docs/assets/aseprite_local_proof.json` (new, written by the runner), `docs/assets/store_contract.md` (one paragraph).

## Completion Summary
(open: the record is refreshed again after the batch's last store change; the D10 addendum is in the ADR, owner-approved)

