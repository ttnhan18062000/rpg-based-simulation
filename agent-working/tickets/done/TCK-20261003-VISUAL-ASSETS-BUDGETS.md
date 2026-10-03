---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-BUDGETS
phase: done
date: 2026-10-03
tags: [performance, testing, mcp]
---

# TCK-20261003-VISUAL-ASSETS-BUDGETS

## Title
Measure every provisional visual-asset bound (U-05), propose owner-approvable values in `docs/assets/budgets.md`, and pin doc-code parity with a test

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Every size, count, dimension and time bound in `visual_assets/` is marked "provisional (U-05)". The user decided on 2026-10-03:
the implementer measures, the planner proposes values, the owner approves the numbers in PR review. This ticket produces the
measurements and the budget record, and makes the record and the code impossible to drift apart.

## Scope
1. **Inventory** every bound marked provisional or `U-05` (at planning time): `visual_assets/store/config.py`
   (`MAX_RECORD_BYTES`, `MAX_REGISTRY_BYTES`, `MAX_VISUAL_KEYS`, `MAX_ALIASES`, `MAX_SOURCE_BYTES`, `MAX_DIM`, `MAX_PREVIEW_BYTES`,
   `MAX_PREVIEW_DIM`, `MAX_DECODED_BYTES`), `store/rendering.py` (`MAX_RENDER_SCALE`), `store/contracts/handoff.py`
   (`MAX_LIMITATIONS`), `store/contracts/definitions.py` (`MAX_AXES`, `MAX_AXIS_VALUES`), `store/contracts/intake.py`
   (`MAX_FINDINGS`), the unsupported-feature list in `store/intake/validator.py`, and the drawing limits in
   `visual_assets/drawing/config.py` (`MAX_DIM` ... `MAX_FILE_BYTES`, `JOB_TIMEOUT_S`). Grep again at start: anything new counts too.
2. **Measure**, with a small re-runnable script outside the import graph the boundary test polices (for example
   `tools/visual_assets_measure_budgets.py`; if you put it under `visual_assets/`, add its `STORE_ALLOWED` row). It prints a JSON
   report. Measure at least:
   - record sizes of every fixture record and of the largest record the contracts allow (`MAX_FINDINGS` findings, `MAX_LIMITATIONS` limitations);
   - pure-Python PNG decode + `pixels-v1` time and peak memory at `MAX_PREVIEW_DIM` square and at `MAX_DECODED_BYTES`;
   - source `.aseprite` bytes for 16, 32, 64 and 128 px sprites with 1 and `MAX_FRAMES` frames (real Aseprite, local only, D10);
   - wall time of `apply_ops` with `MAX_OPS` ops, `review` render, `adopt` re-render and `build` export (local, via ticket 1's strict path);
   - registry load time with `MAX_VISUAL_KEYS` keys and `MAX_ALIASES` aliases.
   Run heavy measurements one at a time under the memory cap.
3. **Budget record** `docs/assets/budgets.md` (frontmatter, `layer: architecture`): one table row per bound with the module, the
   attribute name, the current value, the measured worst case, the **proposed** value, the rule that produced it, and a status
   column. Proposal rule (planner's; apply it, flag any row where it gives a silly answer instead of forcing it):
   - keep the current value when it is at least 2x the realistic worst case measured and the cost at the bound stays under
     2 s and 256 MiB per operation;
   - raise it to 2x the realistic worst case when it is tighter than that;
   - lower it to the largest value whose cost stays under 2 s / 256 MiB when the current value costs more;
   - `MAX_SOURCE_BYTES` stays the D2 reversal trigger: propose it, but say plainly that changing it reopens D2.
   Status is `PROPOSED` for every row in this ticket. Retention (age-based quarantine or review clean-up) stays **unset** with the
   reason "no real catalog yet; `gc` is reachability-only"; list it as an unset row, do not invent a number.
4. **Apply** the proposed values in code, each comment changed from "provisional (U-05)" to "budget: docs/assets/budgets.md". After
   the owner approves in PR review the planner flips the rows to `APPROVED <date>`; the code does not change then unless the owner
   changes a number.
5. **Parity test** `tests/visual_assets/test_budgets_parity.py`: parses the doc's table, imports each named module attribute and
   asserts the value matches; fails on a code bound with no row, on a row naming a missing attribute, and on any leftover
   "provisional (U-05)" comment. Mutation-prove it (change one value in code; the test must fail naming that row).
6. Update `docs/assets/store_contract.md` ("Known gaps": the provisional-bounds line) and the Aseprite plan README's `U-05` row to
   point at the record.

## Out of Scope
- Age-based retention or any new `gc` behaviour.
- Changing what a bound protects or adding bounds that do not exist yet (record a gap instead).
- Performance optimization of the PNG decoder (if the measurement shows a problem, record it as a finding for the planner).

## Acceptance Criteria
- [x] The measurement script runs and its JSON report is quoted (or summarized with the exact numbers) in `investigation.md`.
- [x] `docs/assets/budgets.md` has one row per bound found in the inventory, each with measurement, proposal, rule and status `PROPOSED`, plus the unset retention row.
- [x] Code values equal the proposed values; no "provisional (U-05)" comment remains.
- [x] `test_budgets_parity.py` passes, and fails on the recorded mutant.
- [x] `tests/visual_assets` passes without Aseprite, and `make visual-assets-aseprite-local` passes with 0 skipped (a lowered bound must not break a real-Aseprite test).

## Related Tickets
- TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL (parent)
- TCK-20261003-VISUAL-ASSETS-LOCAL-ASEPRITE-EVIDENCE (provides the strict local run)

## Related Docs
- docs/assets/store_contract.md, docs/assets/drawing_tools.md
- docs/plans/aseprite-mcp-pixel-art/README.md (U-05), docs/plans/visual-asset-management-runtime-integration/README.md (`AM-U08`)
- docs/architecture/visual_asset_foundation_adr.md (D2 reversal trigger)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-BUDGETS/` (plan, investigation with the measurements, test_plan)

## Related Code Areas
- visual_assets/store/config.py, store/rendering.py, store/contracts/{handoff,definitions,intake}.py, store/intake/validator.py, visual_assets/drawing/config.py

## Assumptions / Open Questions
- The proposed numbers are not decisions until the owner approves them in PR review. The PR does not merge before that.
- If a measurement cannot run (for example a time measurement that needs Aseprite), record the row as `NOT MEASURED` with the reason; do not estimate.

## Implementation Notes
- Inventory found three bounds beyond the ticket's list (`readmodel.DEFAULT_LIMIT`/`MAX_LIMIT`, `intake.aseprite.MAX_PALETTE_ENTRIES`); they have rows (R0, NOT MEASURED).
- Two values changed in code: `MAX_SOURCE_BYTES` 102400 -> 114688 (R2 + R4, reopens D2: owner decision) and `MAX_DECODED_BYTES` 25165824 -> 4195328 (R3). Every other value is kept.
- Six flags (F1-F6) where the rule gives a silly or conflicting answer; the value is kept and the planner/owner must rule. The most important: **F1, the registry's real capacity is about 207 keys** because `parse_record` applies `MAX_RECORD_BYTES` (64 KiB) to the registry, so `MAX_REGISTRY_BYTES` and `MAX_VISUAL_KEYS` are unreachable.
- The measurement tool lives in `tools/` (outside the boundary guard) and uses the test builders for synthetic PNGs.
- Strict-mode wording fix from the ticket 1 review folded in (`drawing_tools.md`, ticket 1 Test Summary).

## Test Summary
- `test_budgets_parity.py`: 6 pass. Mutants (each failed naming the row): `MAX_PREVIEW_DIM` 1024 -> 2048 ("code has 2048, budgets.md proposes 1024"); a new `MAX_NEW_THING` bound ("a bound in the code with no row"); `JOB_TIMEOUT_S` row deleted (same); row renamed `MAX_REFZ` ("the row names a missing module or attribute", plus `MAX_REFS` with no row); a restored "provisional (U-05)" comment (names `store/config.py:21`).
- `tests/visual_assets` without Aseprite: 903 passed, 201 skipped. `make visual-assets-aseprite-local`: 201 passed, 0 skipped (after the value changes). `tests/static tests/architecture tests/docs`: 240 passed, 2 skipped, 1 xfailed.
- Measurements: quoted in `investigation.md` (stored artifacts).

## Files Changed
- `tools/visual_assets_measure_budgets.py` (new), `tests/visual_assets/test_budgets_parity.py` (new), `docs/assets/budgets.md` (new)
- Code values/comments: `visual_assets/store/{config,rendering}.py`, `store/contracts/{handoff,intake,definitions}.py`, `store/intake/validator.py`
- Docs: `docs/assets/store_contract.md`, `docs/assets/drawing_tools.md`, `docs/plans/aseprite-mcp-pixel-art/README.md`

## Completion Summary
Every bound in `visual_assets/` is measured, recorded as a `PROPOSED` row in `docs/assets/budgets.md`, and pinned to the code by a parity test. Two values changed; six rows are flagged for a ruling; the owner approves the numbers in PR review.
