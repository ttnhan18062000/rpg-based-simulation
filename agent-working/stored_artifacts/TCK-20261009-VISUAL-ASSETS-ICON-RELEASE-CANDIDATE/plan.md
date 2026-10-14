---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE
artifact_type: plan
date: 2026-10-09
tags: [architecture, planning]
---

# Plan

Ordered steps; each ends with `git status` + `git diff --cached --stat` before the commit.

1. **Commit 1, bookkeeping (docs only).** Hardening `SEQUENCE.md` status -> "DONE (2026-10-09): merged as PR #471,
   `0c3a5654b`"; hardening epic AC `[x]`, `## Status DONE`; icon-set-v2 epic `## Status DONE`. Nothing else.
2. **Read before building.** Confirm what `build()` does without a source id. If it could touch any existing artifact,
   build per icon source id. Record the 34 terrain artifact dir hashes first.
3. **Build** the 36 icon sources at their current revision. Re-hash the 34 terrain dirs: must be identical. Run `verify`
   and `audit`. For each icon artifact: decoded size = the key's size; `pixel_hash` vs the source's frame 1 at x1.
   **Commit 2.**
4. **Blocking question to the user** (ask it yourself; a planner or peer message is not an answer): "Assemble
   `pilot/rc-0008`: rc-0007's 34 entries + the 36 adopted icons = 70, on the current registry; nothing activates." Record
   the answer verbatim. On no, stop and report.
5. **Assemble rc-0008.** Check 34 entries equal rc-0007's, 36 icon entries at the current revision, both refusal codes
   silent, manifest size vs `MAX_MANIFEST_BYTES` recorded.
6. **Guards by equality** (rc-0007 precedent, ticket `TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC` lines 70-72): add
   rc-0008 to `adopted_facts.RELEASE_CANDIDATES`; stdio count 7 -> 8; new test rc-0008 = rc-0007 + exactly the 36 icon
   keys; change the "no artifact/no slot for icons" assertions to the new fact. Mutation check: drop one icon entry or
   alter one terrain entry in a scratch copy, the new test fails. **Commit 3.**
7. **Docs + snapshots** (ticket scope 6), `make knowledge-index-update`. **Commit 4.**
8. Merge `origin/main`, regenerate `docs/REGISTRY.yaml`, run the test plan, report to the planner, then ask the user the
   push/PR question.

## AC map
AC1 -> 1; AC2 -> 2-3; AC3 -> 4-5; AC4 -> 3, 5; AC5 -> 6; AC6 -> 7; AC7 -> 8.

## Scope guards
No registry edit; no export config edit; no `export-runtime` into `frontend/` beyond a fixture its own guard asks for;
no gate result moved; no assertion removed.

## Amendment (2026-10-09, after the build): closed draft-set fixture guards
Finding: `draftexport._adopted_references` lists every adopted slot with a built artifact, so building the 36 icons grew a fresh export of `icons-key-v1`, `icons-v2` and `icons-owner-fixes-v1` from 48/56/43 to 70 entries. Three fixture guards failed, and regenerating the fixtures broke 15 frontend tests and the isolation file count (baseline 270/270). Planner ruling, option (c): re-anchor the guard to the gate's own record and keep the export, the fixtures and the page as they are.
Added to step 6 (commit 3): `adopted_facts.CLOSED_DRAFT_SETS` (set id -> adoption record(s) + draft set hash) and a pin test; `tests/visual_assets/closed_draft_fixture.py` (drafts byte-equal to a fresh export, references byte-equal to the catalog artifact they name, nothing else); an open set keeps the full equality; five mutation proofs, each asserted to apply at one site. This is a re-anchoring, not a relaxation: only "must include art built after the gate" is dropped, only for gate-closed sets. Step 7 adds one line to `docs/assets/store_contract.md` where the draft preview is described. The frontend is not touched.
