---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-INTAKE
phase: open
date: 2026-10-02
tags: [architecture, mcp, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-STORE-INTAKE

## Title
Candidate handoff from the drawing tools and independent intake into quarantine, with local review export

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 3 of `TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION`. An agent (or a human with a manually drawn file) can
package one exact drawing revision as a `CandidateHandoffPackage`; the store copies it into a bounded quarantine,
checks every claim against the copied bytes, and records an immutable `IntakeResult`. A passing candidate can be
exported to a local review folder for a human to look at. Nothing here adopts anything, and nothing here writes a
git-tracked file. Blocked by `TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS`. Same branch (`visual-assets-store`).

## Scope
1. `visual_assets/drawing/handoff.py`: `build_handoff(name, revision, *, licence_state, licence_evidence_ref,
   brief_id, review_evidence_ref, limitations)` writes a package directory **inside the experiment workspace**
   (`<workspace>/handoffs/<candidate_id>/`) containing exactly `package.json` (canonical
   `CandidateHandoffPackage`), `source.aseprite` (the exact revision's bytes, hash re-checked against the sidecar)
   and `preview.png`. `producer_class = CAP_A`; provenance fields are filled from what the tools actually know
   (adapter version, Aseprite version, Lua pin) and are `UNAVAILABLE` otherwise, never invented.
   `candidate_id = "cand-" + first 16 hex of sha256(source bytes)`. Rebuilding the same revision is idempotent.
   Imports only `api` and `visual_assets.store.contracts` (already the rule in the boundary test).
2. `visual_assets/drawing/server/handoff_tools.py`: one MCP tool `export_handoff` wrapping item 1. Update every
   test and doc that pins the tool list (15 becomes 16).
3. `visual_assets/store/intake/quarantine.py`: `stage(package_dir) -> staged dir` under
   `config.QUARANTINE_ROOT/<intake_id>/`. Copies only the three allowlisted file names; opens with `O_NOFOLLOW`;
   rejects symlinks, non-regular files, hard-link counts above 1, unexpected extra entries, sub-directories and
   any file above its size bound; never opens a path taken from package content. Creation is exclusive; a partial
   stage is removed on failure.
4. `visual_assets/store/intake/validator.py`: pure Python, never trusts the producer. Checks, each with its own
   `IntakeFinding` code: package parses strictly; assertion literal present; file hashes match claims; source
   starts with a valid Aseprite header (file size field equals real size, magic `0xA5E0`) and its width, height,
   frame count and colour depth equal the claims; layer and tag counts equal the claims via a bounded chunk
   walker over the first frame (cel pixel data is not decompressed; an unknown or oversized chunk is skipped by
   its declared size, a size that overruns the file is a finding); dimensions within `MAX_DIM`; preview has a PNG
   signature and IHDR dimensions consistent with the source; `licence_state` is not `WITHDRAWN`; no declared
   limitation is in the unsupported list. Any finding gives verdict `QUARANTINED`; none gives `PASSED`.
5. `intake(package_dir, *, created_at)`: stage, validate, write `intake_result.json` **inside the quarantine
   directory** (exclusive create). `intake_id = "in-" + first 16 hex of sha256(package.json bytes)`; submitting
   the identical package again returns the existing result and writes nothing.
6. `review(intake_id)`: for a `PASSED` intake only, re-verify the staged hashes, then copy `preview.png` and a
   short text summary to `config.REVIEW_ROOT/<intake_id>/`. No Aseprite needed. Writes nothing tracked.
7. `visual_assets/store/cli.py` + `__main__.py`: `python -m visual_assets.store intake <dir>`, `review <id>`,
   `list`, `show <id>` (the last two read quarantine results only for now). Exit code non-zero on `QUARANTINED`.
8. Tests: `tests/visual_assets/store/unit/` (CI) and `tests/visual_assets/store/integration/` (`needs_aseprite`),
   `tests/visual_assets/store/test_cli.py`. Synthetic source fixtures are built in the tests by a small
   pure-Python Aseprite-header writer, or committed under `visual_assets/catalog/fixtures/intake/`.
9. Docs: `docs/assets/store_contract.md` (intake and review **built**, and the deviation below),
   `docs/assets/drawing_tools.md` (`export_handoff`), structure doc and ADR for the deviation, store README.

## Out of Scope
- `adopt`, `revoke`, build, release, `verify`, `gc` (children 4-5).
- `submit_candidate`, `store_list`, `store_show` MCP tools (child 6).
- Decoding cel pixel data or computing a pixel hash (child 5).
- Any write under the tracked part of `visual_assets/catalog/`.

## Acceptance Criteria
- [ ] A handoff built from a real revision passes intake end to end (integration, needs Aseprite).
- [ ] A hand-built `MANUAL` package with `NOT_APPLICABLE`/`UNAVAILABLE` provenance passes under the same policy
      as a `CAP_A` package (no producer-specific branch in the validator).
- [ ] Each of these is `QUARANTINED` with its own finding code: source hash mismatch, preview hash mismatch,
      wrong magic, header size mismatch, width/height/frames/layers/tags mismatch, over-`MAX_DIM`, truncated
      chunk, missing assertion, `WITHDRAWN` licence, unknown field or duplicate key in `package.json`.
- [ ] Each of these is refused before any byte is copied, and leaves no quarantine directory: symlinked file,
      symlinked package directory entry, extra file, sub-directory, oversize file, FIFO.
- [ ] After every intake and review test, the only paths written are under the patched `QUARANTINE_ROOT` and
      `REVIEW_ROOT`; the tracked catalog tree and the experiment workspace are byte-identical to before.
- [ ] Re-submitting an identical package returns the same `intake_id` and does not modify the existing result;
      an existing `intake_result.json` is never overwritten.
- [ ] `review` refuses a `QUARANTINED` or unknown intake, and refuses when staged bytes no longer match the
      recorded hashes.
- [ ] Boundary test: `drawing` still cannot reference the catalog; `store` still does not import `drawing`.
- [ ] The MCP tool list contains `export_handoff` and no adopt, build, release, revoke or gc tool.
- [ ] `pytest tests/visual_assets -m "not slow and not extra_slow"` green without Aseprite; integration green
      with it.

## Related Tickets
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION (parent)
- TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS (blocks this)
- TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION (consumes `PASSED` intakes)

## Related Docs
- docs/plans/visual-asset-foundation/README.md
- docs/assets/store_contract.md, docs/assets/drawing_tools.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (section 9.6)
- docs/plans/visual-asset-management-runtime-integration/04_candidate_adoption_rehearsal_plan.md (`AM4-W09`)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- visual_assets/drawing/handoff.py, visual_assets/drawing/server/, visual_assets/store/intake/, visual_assets/store/cli.py, tests/visual_assets/

## Assumptions / Open Questions
- **Deviation from the structure doc, decided by the planner and reported to the user:** the doc placed
  `IntakeResult` under the tracked `catalog/provenance/intake/`, but intake has no human gate and decision D3
  says nothing unaccepted enters git history. So the result is written inside the gitignored quarantine
  directory, and child 4 copies it into `provenance/intake/` at adoption time. Record this in the ADR.
- The Aseprite file-format facts (header layout, chunk types `0x2004` layer and `0x2018` tags) must be checked
  against the official format specification during investigation, and against files produced by the pinned
  Aseprite build in the integration test. If the chunk walker cannot be made reliable, stop and tell the planner.
- `created_at` is supplied by the caller (the CLI reads the clock); library code never does.

## Implementation Notes
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(open)
