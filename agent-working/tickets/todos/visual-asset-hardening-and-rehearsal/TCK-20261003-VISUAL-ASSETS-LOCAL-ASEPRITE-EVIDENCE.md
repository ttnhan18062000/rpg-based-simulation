---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-LOCAL-ASEPRITE-EVIDENCE
phase: open
date: 2026-10-03
tags: [testing, mcp, security]
---

# TCK-20261003-VISUAL-ASSETS-LOCAL-ASEPRITE-EVIDENCE

## Title
Strict local real-Aseprite test run with a binary pin check, explicit CI skip reporting, and a guard that no workflow installs Aseprite

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
ADR `D10` (user, 2026-10-03; facts in `docs/assets/aseprite_licence_review.md`): real Aseprite runs only on the licence
holder's own machine, never on a hosted runner. Today the `needs_aseprite` tests skip silently wherever Aseprite or bwrap is
missing, so a local run that quietly skipped looks the same as one that passed, and nothing stops a future workflow from
installing Aseprite. This ticket makes the local evidence strict and the CI skip visible, and turns D10 into a test.

## Scope
1. **Strict mode.** In `tests/visual_assets/conftest.py`: when the environment variable `VISUAL_ASSETS_REQUIRE_ASEPRITE=1`
   is set, a missing Aseprite or bwrap makes every `needs_aseprite` test **fail** with a clear reason instead of skipping.
   Without the variable, behaviour is unchanged (skip).
2. **Binary pin.** Add the pinned editor version to `visual_assets/drawing/config.py` as a module attribute
   (`ASEPRITE_VERSION = "1.3.18.6"`, read as `config.NAME` at call time per the ADR's rule). In strict mode the session also
   fails if `aseprite --version` does not report that version. Do **not** pin the binary's sha256 in code (it changes per
   install; it is recorded in the licence review only).
3. **One make target** `visual-assets-aseprite-local`: runs `tests/visual_assets` with `-m needs_aseprite` and
   `VISUAL_ASSETS_REQUIRE_ASEPRITE=1`, under the repo's memory cap convention
   (`systemd-run --user --scope -p MemoryMax=2G` when available), and writes a small JSON evidence file to
   `reports/visual_assets/aseprite_local_run.json` (gitignored; `reports/` is the run-output area): git commit, UTC time,
   `aseprite --version` output, passed / failed / skipped / total counts from the JUnit XML. It exits non-zero on any failure or
   any skip.
4. **CI states the skip.** The `Run: tests/visual_assets` step keeps running without Aseprite. Make the job summary show one
   line with the number of `needs_aseprite` tests skipped and why ("local only, ADR D10"). Reuse the existing JUnit summary
   path (`tools/ci_junit_summary.py`) if it can carry it; otherwise a tiny separate summary line is fine. Keep the workflow diff
   minimal: another session is editing `.github/workflows/test.yml` on branch `python-code-craft-gates`.
5. **D10 guard.** A static test (e.g. `tests/visual_assets/test_aseprite_licence_guard.py`) fails if any file under
   `.github/workflows/` installs, downloads, builds or caches Aseprite (match on the editor name in `run:`/`uses:`/cache keys;
   a comment or the skip-summary text naming D10 is allowed), or if any tracked file is an Aseprite executable or package
   (`*.deb` / `*.AppImage` / an ELF named `aseprite*`). Prove it fails on a mutant workflow line.
6. Docs: `docs/assets/drawing_tools.md` and `visual_assets/README.md` say how to run the strict target and what the evidence file
   holds; the CI comment above the step cites D10 instead of "plan U-14".

## Out of Scope
- Any self-hosted runner, container, cache or install of Aseprite in CI (D10).
- Changing which tests are marked `needs_aseprite`, or the tests themselves.
- Committing evidence files (they are local output; the ticket's Test Summary quotes the run).

## Acceptance Criteria
- [ ] With `VISUAL_ASSETS_REQUIRE_ASEPRITE=1` and Aseprite hidden (e.g. `ASEPRITE_MCP_BINARY=/nonexistent`), every `needs_aseprite` test fails, none skips (test proves it).
- [ ] Without the variable, the same run skips them exactly as before (test proves it).
- [ ] Strict mode with a wrong reported version fails the session (test with a fake binary script reporting another version).
- [ ] `make visual-assets-aseprite-local` passes on this machine with 0 skipped, and writes the evidence file with the fields above; quote the file in Test Summary.
- [ ] CI's `tests/visual_assets` step summary shows the skipped `needs_aseprite` count and D10.
- [ ] The D10 guard passes on the real tree and fails on a mutant workflow that installs Aseprite (mutant proof recorded).
- [ ] `tests/static` passes (workflow edits must keep head/base path parity), plus `tests/visual_assets` without Aseprite.

## Related Tickets
- TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL (parent)
- TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT (added the CI step and the `needs_aseprite` marker)

## Related Docs
- docs/assets/aseprite_licence_review.md, docs/architecture/visual_asset_foundation_adr.md (D10)
- docs/assets/drawing_tools.md

## Related Stored Artifacts
- None.

## Related Code Areas
- tests/visual_assets/conftest.py, visual_assets/drawing/config.py, Makefile, .github/workflows/test.yml, tools/ci_junit_summary.py

## Assumptions / Open Questions
- `reports/` is gitignored run output (confirm; if not, use a gitignored path under it and add the ignore rule).
- Hand-orchestrated close: record monitoring with `record_hand_orchestrated_closure.py` (never pass `--agent <session-name>`).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
