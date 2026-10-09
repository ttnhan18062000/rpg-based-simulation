---
status: active
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
