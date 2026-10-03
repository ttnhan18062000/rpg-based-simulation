---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-INTAKE
phase: done
date: 2026-10-02
tags: [architecture, mcp, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-STORE-INTAKE

## Title
Candidate handoff from the drawing tools and independent intake into quarantine, with local review export

## Status
DONE

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
   directory** (exclusive create). `intake_id = "in-" + first 16 hex of sha256` over the package, source and
   preview `FileHash` strings joined with `\n` in that fixed order (**rule changed by asset-planner 2026-10-03**; the
   ticket first said package.json alone, which let wrong bytes under a genuine package.json take the id for good).
   Submitting the identical files again returns the existing result and writes nothing; an existing directory whose
   staged hashes differ is an `intake_id_collision` error. Staging is atomic (asset-planner R2): the four files are
   written and fsynced in a `.tmp-*` sibling directory that is then renamed to `<intake_id>`, so a killed process
   leaves only an ignored, deletable temporary directory. A preview above `MAX_PREVIEW_DIM` is `PREVIEW_OUT_OF_BOUNDS`.
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
- [x] A handoff built from a real revision passes intake end to end (integration, needs Aseprite).
- [x] A hand-built `MANUAL` package with `NOT_APPLICABLE`/`UNAVAILABLE` provenance passes under the same policy
      as a `CAP_A` package (no producer-specific branch in the validator).
- [x] Each of these is `QUARANTINED` with its own finding code: source hash mismatch, preview hash mismatch,
      wrong magic, header size mismatch, width/height/frames/layers/tags mismatch, over-`MAX_DIM`, truncated
      chunk, missing assertion, `WITHDRAWN` licence, unknown field or duplicate key in `package.json`.
- [x] Each of these is refused before any byte is copied, and leaves no quarantine directory: symlinked file,
      symlinked package directory entry, extra file, sub-directory, oversize file, FIFO.
- [x] After every intake and review test, the only paths written are under the patched `QUARANTINE_ROOT` and
      `REVIEW_ROOT`; the tracked catalog tree and the experiment workspace are byte-identical to before.
- [x] Re-submitting an identical package returns the same `intake_id` and does not modify the existing result;
      an existing `intake_result.json` is never overwritten.
- [x] `review` refuses a `QUARANTINED` or unknown intake, and refuses when staged bytes no longer match the
      recorded hashes.
- [x] Boundary test: `drawing` still cannot reference the catalog; `store` still does not import `drawing`.
- [x] The MCP tool list contains `export_handoff` and no adopt, build, release, revoke or gc tool.
- [x] `pytest tests/visual_assets -m "not slow and not extra_slow"` green without Aseprite; integration green
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
Built in three commits plus planner-requested changes; staging artifacts are in `stored_artifacts/TCK-20261002-VISUAL-ASSETS-STORE-INTAKE/`.

- **Store side** (`b058a435`, `5cc836ec`): `store/intake/{quarantine,aseprite,png,validator,service}.py`, `store/cli.py`, `store/__main__.py`. All three files are read into
  memory through an `O_NOFOLLOW` directory descriptor and verified before anything is written; the stage is written to a `.tmp-*` sibling and renamed. One policy for every
  producer class; findings carry only numbers, hash prefixes and fixed tokens, never producer text.
- **Pinned template change** (`40d16d74`, its own commit, user decision option (a)): one read-only line in `summary()` of `ops.lua` plus the re-pin; `cels` and
  `aseprite_version` now appear in every sprite summary. The first attempt at this edit was blocked by the session permission check and was only made after the user approved.
- **Drawing side**: `api.read_revision`, `drawing/handoff.py` (`build_handoff`), `drawing/server/handoff_tools.py` (`export_handoff`; 16 tools, no gate tool).
- `needs_aseprite` marker and skip hook moved from `tests/visual_assets/drawing/conftest.py` to `tests/visual_assets/conftest.py`.

### Where ticket and reality differed (all reported to asset-planner)
1. Staged file is `package.json` (my ticket-2 proposal said `handoff.json`); `IntakeResult.candidate_id` may be `UNAVAILABLE` for an unparseable package (QUARANTINED only).
2. The validator also verifies `cel_count`, `palette_size`, `source_format`, walking all frames' chunk headers (ticket said first frame, counts for layers/tags only). The package has no
   colour-depth claim, so colour depth is a support policy (32-bit RGBA only).
3. **Palette size** equals what Aseprite 1.3.18.6 reports after loading, verified by round-tripping 14 palette setups through the real binary, except an all-opaque-black stored palette:
   Aseprite rebuilds it from the pixels (1 + distinct opaque colours), which needs pixel decoding, so intake reports `PALETTE_UNVERIFIABLE` and quarantines it (only a never-edited r0001).
4. `intake_id` rule **changed by asset-planner 2026-10-03** (hash over all three file hashes; collision guard `intake_id_collision`); staging made atomic; `PREVIEW_OUT_OF_BOUNDS` added.
5. Added `producer_state` (ACTIVE/QUARANTINED/REVOKED) per planner; `producer_validation = FAILED` also quarantines; the unsupported-limitation tokens and preview bounds are provisional (`U-05`).
6. The preview-to-source gap (a human reviews the preview but adopts the source) is recorded as a known gap in `store_contract.md`; ticket 5 carries the fix (added by asset-planner).
7. One existing test changed for a legitimate reason: the unknown-store-layer planted test now uses `adoption` because `intake` became a known layer.

## Test Summary
Run with the main checkout's venv (the system python lacks `mcp`).
- `tests/visual_assets` + static + architecture + docs: 888 passed, 2 skipped, 1 xfailed. With `ASEPRITE_MCP_BINARY` pointing at a missing binary (what CI sees): 462 passed, 192 skipped,
  so every new store unit test and the store/handoff unit tests run in CI; the `needs_aseprite` integration tests run locally.
- Real Aseprite is the oracle: parser facts equal Aseprite's own counts on drawing-tool revisions, on every revision of an edited sprite, on 14 palette setups and on the synthetic builder files;
  the Lua cel count equals the store reader's at every revision of a sprite with an empty layer and a multi-frame layer; a real handoff passes intake end to end; an untouched r0001 is
  quarantined with `PALETTE_UNVERIFIABLE` only; a WITHDRAWN licence is packaged but quarantined.
- Mutation checks: 21 mutants of the store intake guards, 6 of the R1-R3 changes, 8 of the handoff builder, each failing the intended test (survivors found along the way led to new tests:
  special files never opened, frame-header check, temp-directory cleanup, post-read hash re-check).
- Not run: the full suite; `tests/tools/test_knowledge_search.py::TestLiveQueryDocsMechanics` (known local timeout).

## Files Changed
Added: `visual_assets/store/intake/*`, `visual_assets/store/{cli,__main__}.py`, `visual_assets/drawing/{handoff.py,server/handoff_tools.py}`, `tests/visual_assets/conftest.py`,
`tests/visual_assets/store/{builders.py,unit/test_{intake_validator,quarantine,intake_service,cli}.py,integration/test_real_aseprite.py}`,
`tests/visual_assets/drawing/{unit/test_handoff_unit.py,integration/test_handoff.py,integration/test_summary_facts.py}`.
Changed: contracts (`handoff`, `intake`, `base`, `__init__`), `errors.py`, `config.py`, `drawing/{api.py,config.py (pin),backend/lua/ops.lua (one line),server/__init__.py}`,
`tests/visual_assets/{test_boundaries.py,drawing/conftest.py,drawing/stdio_support.py,drawing/test_server_stdio.py,drawing/integration/test_server_stdio.py}`, fixtures `package.json` naming,
docs (`store_contract.md`, ADR, plan README, `drawing_tools.md`, READMEs), tickets 4 and 5 (planner additions), `STORE_FORMAT`.
No `src/`, `frontend/`, requirements or pyproject change.

## Completion Summary
A candidate can be packaged from one exact drawing revision, staged into a bounded quarantine, judged by an independent validator that is cross-checked against real Aseprite, and exported to a local review area, without adopting anything or writing a tracked file. The intake id, atomic staging and the pinned-template change were done as the planner and user decided; palette size is exact except where Aseprite itself makes it depend on pixels, which is quarantined rather than guessed.
