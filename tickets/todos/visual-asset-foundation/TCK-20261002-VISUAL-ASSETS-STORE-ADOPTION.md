---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION
phase: open
date: 2026-10-02
tags: [architecture, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION

## Title
Human-gated adoption and revocation with provenance records and an audit-reconstruction test

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 4 of `TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION`. A human runs `adopt` on an intake-passed candidate; the
store writes a new immutable source revision plus the records that prove who approved exactly which bytes. A
human can revoke a candidate or a source revision, which makes it ineligible for build and release. This is the
first command that writes git-tracked catalog files. Blocked by `TCK-20261002-VISUAL-ASSETS-STORE-INTAKE`. Same
branch (`visual-assets-store`).

## Scope
1. `visual_assets/store/adoption.py`: `adopt(intake_id, *, visual_key, approver, approver_role, licence_state,
   licence_evidence_ref, source_asset_id, decided_at, confirm)`.
   Refuses, each with a distinct error code and without writing anything: unknown intake; verdict not `PASSED`;
   staged bytes no longer match the `IntakeResult` hashes (re-verified now); intake already adopted; intake or
   target source revoked; `visual_key` not in the registry (no dynamic registration); `licence_state` other than
   `CLEARED`; empty approver; source above `MAX_SOURCE_BYTES` (message cites ADR D2); `confirm` not satisfied.
   A new `source_asset_id` starts at `r0001`; an existing one gets the next revision with its parent recorded.
2. Writes, all or nothing (build the files in a temporary directory inside the catalog, then move into place with
   exclusive creation; on any failure nothing remains): `sources/<source_asset_id>/rNNNN.aseprite`,
   `sources/<source_asset_id>/rNNNN.source.json`, `provenance/adoptions/<adoption_id>.json`,
   `provenance/intake/<intake_id>.json` (copy of the quarantine `IntakeResult`). No existing file is ever
   overwritten. `adoption_id = "ad-" + first 16 hex of sha256(intake_id + source_asset_id + revision)`.
3. D2: sources are committed as ordinary files. No `.gitattributes` LFS rule is added for `visual_assets/`.
4. `visual_assets/store/revoke.py`: `revoke(target, *, reason, approver, decided_at, confirm)`. Target is an
   intake or a source revision. A source-revision revocation writes `provenance/revocations/<id>.json` (tracked);
   an un-adopted intake's revocation is written inside its quarantine directory (local). Nothing is deleted.
   `is_build_eligible(source_asset_id, revision) -> bool` is the single function later code asks.
5. The human gate: the library functions take a `confirm` callable; the CLI's `adopt` and `revoke` require
   `--approver`, refuse when stdin is not a terminal, and make the operator type the intake or revision id to
   confirm. Neither function is imported by `visual_assets/drawing/server/` (boundary rule, with a planted test).
6. CLI: `python -m visual_assets.store adopt <intake_id> --visual-key K --approver NAME --approver-role R
   --licence STATE --licence-evidence REF [--source-asset-id ID]` and `revoke <target> --reason TEXT --approver
   NAME`. `list` and `show` now also read sources and adoption records.
7. Audit reconstruction: `audit_chain(catalog_root)` rebuilds, from the catalog tree alone, the chain
   intake result -> adoption record -> source record -> source bytes for every source revision and reports every
   break. Lives in the store (child 5's `verify` will call it).
8. Tests under `tests/visual_assets/store/unit/` (CI, temporary catalog roots, synthetic fixtures only) and
   `test_cli.py`.
9. Docs: `docs/assets/store_contract.md` (adoption, revoke **built**; what an agent may and may not run),
   structure doc, store and catalog READMEs. Add to `docs/assets/drawing_tools.md` or the store README a plain
   rule for agents: an agent never runs `adopt` or `revoke`. Also state, in the store docs, the known gap carried from
   ticket 3 until ticket 5 lands: the human reviews `preview.png` but adopts `source.aseprite`, and intake cannot prove
   the preview depicts the source (added by asset-planner 2026-10-03).

## Out of Scope
- Build, release, `verify`, `gc` (child 5). MCP store tools (child 6).
- Adopting any real asset: the committed catalog keeps zero sources after this ticket.
- Licence review `U-02`; who is allowed to be an approver (the name is recorded, not authenticated).

## Acceptance Criteria
- [ ] Adopting a `PASSED` synthetic intake produces exactly the four files of scope item 2, each record parses
      strictly, and the source bytes hash to the value in all three records.
- [ ] A second adoption of the same `source_asset_id` produces `r0002` with parent `r0001`; `r0001` files are
      byte-identical afterwards.
- [ ] Each refusal in scope item 1 has a test that asserts the error code and that the catalog tree is
      byte-identical to before.
- [ ] A failure injected between the writes (each position) leaves the catalog tree byte-identical to before.
- [ ] Revoking a source revision makes `is_build_eligible` false and makes a later `adopt` of the same intake
      refuse; the revoked files are still present.
- [ ] CLI `adopt` and `revoke` exit non-zero without a terminal on stdin and without `--approver`.
- [ ] `audit_chain` passes on a freshly adopted tree and reports the specific break for each planted tamper:
      edited source byte, deleted adoption record, deleted intake record, edited approver, swapped source record.
- [ ] The MCP tool list has no adopt or revoke tool, and the boundary test forbids `server` from importing
      `store.adoption` and `store.revoke`.
- [ ] No test writes outside its temporary roots; the committed `visual_assets/catalog/` has no source,
      adoption or revocation file.
- [ ] `pytest tests/visual_assets -m "not slow and not extra_slow"` green without Aseprite.

## Related Tickets
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION (parent)
- TCK-20261002-VISUAL-ASSETS-STORE-INTAKE (blocks this)
- TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE (consumes adopted sources and eligibility)

## Related Docs
- docs/plans/visual-asset-foundation/README.md
- docs/architecture/visual_asset_foundation_adr.md (D2, D5)
- docs/assets/store_contract.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (sections 6, 7, 9.4)
- docs/plans/visual-asset-management-runtime-integration/04_candidate_adoption_rehearsal_plan.md

## Related Stored Artifacts
- None yet.

## Related Code Areas
- visual_assets/store/adoption.py, visual_assets/store/revoke.py, visual_assets/store/cli.py, visual_assets/catalog/, tests/visual_assets/store/

## Assumptions / Open Questions
- D2 confirmed by the user on 2026-10-02: adopted `.aseprite` sources are committed directly, no Git LFS.
- The terminal check and typed confirmation make an accidental or scripted adoption fail; they do not
  authenticate the person. That limit is stated in the docs, not hidden.
- Only `CLEARED` is adoptable. Whether `RESTRICTED` can ever be adopted is left to the licence review (`U-02`).
- `decided_at` is read from the clock by the CLI only.

## Implementation Notes
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(open)
