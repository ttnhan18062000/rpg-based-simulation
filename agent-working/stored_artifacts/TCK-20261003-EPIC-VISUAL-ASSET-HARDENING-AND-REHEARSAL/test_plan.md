---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL
artifact_type: test_plan
tags: [architecture, testing, mcp, security]
---

# Test Plan (as built) — TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL

Evidence per child, as of the last run on the branch head (counts from the final runs, each command run once under a memory cap):

| Child | Evidence |
|---|---|
| 1 local evidence | `make visual-assets-aseprite-local`: 202 passed, 0 skipped (twice in a row after 2b); strict-mode tests (missing binary errors, default skips, wrong version errors); the D10 guard fails on a planted workflow install line and a planted binary; 4 mutants |
| 2 budgets | `test_budgets_parity.py` (5 mutants) and `test_record_bounds.py` (the maximum legal instance of all 9 record types plus the worst legal PNG; 5 mutants); `docs/assets/budgets.md` rows all `PROPOSED` |
| 2b sandbox leak | `test_sandbox_kill_tree.py` (real processes, a fake `/proc`, an interrupt test; mutants), the timeout stress test (old code failed 2 of 5 runs, new code 20 of 20 without load) |
| 3 runtime manifest | contract 14, export 17, fixture 3 tests; 9 mutants; the committed fixture equals a fresh regeneration |
| 4 rehearsal | frontend `npx vitest run`: 11 files, 94 tests (new: manifest 29, resolver 9, loader 4, fallback 7, scene 5, harness 4, isolation 5 incl. a real production build); `npm run build` passes and `dist/` has no match for the rehearsal; 7 frontend mutants; one local Chromium 148 capture, pixel-identical cells |
| whole branch | `tests/visual_assets` without Aseprite 979 passed, 202 skipped; `tests/static tests/architecture tests/docs` 240 passed |

**Load rule (this VM):** the host starved and a session crashed once when 8 CPU burners ran a stress loop (load average 43; a later 4-burner run also reached 44). Nobody runs tests in loops or under artificial CPU load on this machine; heavy commands run once, one at a time, under a memory cap (and a CPU cap for the knowledge index). The interrupt case became a deterministic unit test instead.

**Open:** owner approval of the budget rows in PR review (the planner then flips them to `APPROVED <date>`); the PR does not merge before that. Aseprite-backed evidence exists only from the licence holder's machine (D10), never in CI.

## Proof Plan

- Level: the children's own unit, component and integration tests; the epic adds no tests of its own.
- Proof kind: executable tests with recorded mutants, plus the per-gate result record for the rehearsal.
- Oracle source: each child's acceptance criteria and `docs/assets/surface_rehearsal_result.md`.
- Expected effect: all suites above pass on the branch head; the rehearsal result stays honest (`INCONCLUSIVE`, nothing passed toward activation).
- Selected commands: `pytest tests/visual_assets`; `make visual-assets-aseprite-local` (local only); `pytest tests/static tests/architecture tests/docs`; `npx vitest run` and `npm run build` in `frontend/`.
