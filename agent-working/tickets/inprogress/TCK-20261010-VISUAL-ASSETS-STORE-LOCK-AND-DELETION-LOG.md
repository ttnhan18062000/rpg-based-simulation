---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG
phase: open
date: 2026-10-10
tags: [architecture, security, testing]
---

# TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG

## Title
A store-wide lock, an append-only deletion log and kill-mid-publish tests (ADR D24, reverses D18)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. ADR D18 says there is no store lock (one store command at a time) and `gc --delete` keeps no record (store_contract.md:208, ADR:47). `catalogwrite.publish` admits a hard kill can leave orphan files (catalogwrite.py:1-6). Owner, 2026-10-10 (blocking question): reverse D18.

## Scope
- **Design first (planner approves before code); the D24 text is approved by the owner.** New ADR D24 supersedes D18's "no lock / no deletion record" parts; D18 stays in the ADR marked superseded-in-part.
- One store-wide advisory lock (`fcntl.flock` on a lock file in the store root) taken by every writing store command (intake, review, adopt, adopt-set, revoke, draft *, build, release, export, gc --delete). A second writer **refuses** at once with the holder's pid/command (no waiting: agents must not hang). Read-only commands take no lock.
- An append-only, typed deletion log for `gc --delete` (one record per removed path: path, content hash, reason, decided_at injected like other timestamps), canonical JSON, inspectable by a CLI listing; `audit_chain` verifies it.
- Kill-mid-publish tests: a subprocess killed (SIGKILL) at injected points inside `catalogwrite.publish` and `runtime_export`; prove the store stays readable, `audit_chain` reports the orphans, and a re-run either completes or refuses cleanly. The lock is released by the kernel on kill (prove it).
- store_contract.md, ADR D24, budgets if any bound is added.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Authenticating the human gate (approver stays recorded, not proven). Lock for the drawing workspace (has its own per-sprite lock).

## Acceptance Criteria
- [ ] D24 design approved by the planner and its text by the owner before code.
- [ ] Concurrent writer refused with holder info; read-only commands unaffected (tests).
- [ ] gc --delete writes one typed log record per removal; audit_chain checks it (tests incl. a tampered log).
- [ ] Kill-mid-publish tests at >=3 injection points pass; recovery documented in store_contract.md.
- [ ] Security review clean.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions
- Lock file location must not collide with `VISUAL_ASSETS_CHECKOUT` worktree data roots (one lock per store data root).

## Implementation Notes
Design approved by asset-planner and D24 text/budget by the owner (2026-10-10). Code: `store/lock.py`, `store/deletionlog.py`, `contracts/deletion.py`, `gc`/`audit`/`verify`/`cli` wiring, MCP `submit_candidate`. Kill tests found two gaps fixed here: hard-linked files unreadable until the staging directory is removed (documented recovery), and an empty `sources/<id>` directory left by a kill before the first link (`audit` now reports it). Security review: APPROVED, hardening applied (torn-tail refusal, short-write loop, size cap on log reads); stated limits in `store_contract.md`. See staging `plan.md`, `investigation.md`, `test_plan.md`.


## Test Summary
`tests/visual_assets` full tree passed (1976) before the last hardening; store/boundaries/budgets/no_ignored_files (1164) after it. New: test_lock.py (38), test_deletion_log.py (30), test_kill_mid_publish.py (20). 11 single-match mutants all killed.


## Files Changed
- `.gitignore`
- `docs/architecture/visual_asset_foundation_adr.md`
- `docs/assets/budgets.md`
- `docs/assets/m1_contract_register.md`
- `docs/assets/retention_and_rollback.md`
- `docs/assets/store_contract.md`
- `tests/visual_assets/store/kill_helper.py`
- `tests/visual_assets/store/unit/conftest.py`
- `tests/visual_assets/store/unit/test_deletion_log.py`
- `tests/visual_assets/store/unit/test_drafts.py`
- `tests/visual_assets/store/unit/test_gc.py`
- `tests/visual_assets/store/unit/test_kill_mid_publish.py`
- `tests/visual_assets/store/unit/test_lock.py`
- `tests/visual_assets/test_boundaries.py`
- `tests/visual_assets/test_no_ignored_files.py`
- `visual_assets/drawing/server/store_readonly_tools.py`
- `visual_assets/store/audit.py`
- `visual_assets/store/cli.py`
- `visual_assets/store/config.py`
- `visual_assets/store/contracts/deletion.py`
- `visual_assets/store/deletionlog.py`
- `visual_assets/store/gc.py`
- `visual_assets/store/lock.py`
- `visual_assets/store/verify.py`

## Completion Summary
A store-wide advisory write lock that refuses a second writer and names the holder, a hash-chained `gc --delete` deletion log with archiving and an `audit` chain check, kill-mid-publish tests at several injection points with the recovery documented in `store_contract.md`, and ADR D24 (the design approved by the planner and the text and budget by the owner, 2026-10-10). The independent security review was APPROVED with hardening applied (recorded in Implementation Notes). Read-only commands are unaffected.
