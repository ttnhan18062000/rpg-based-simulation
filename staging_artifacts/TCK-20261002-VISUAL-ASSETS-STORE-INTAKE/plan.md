---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-INTAKE
artifact_type: plan
tags: [architecture, mcp, testing, documentation]
---

# Plan — TCK-20261002-VISUAL-ASSETS-STORE-INTAKE

Store side first (independent of the drawing tools), drawing side last. Each step keeps `tests/visual_assets` green.

1. Contract adjustments agreed with asset-planner: `package.json` as the staged file name; `producer_state` enum (ACTIVE, QUARANTINED, REVOKED); `frame_count` and
   `layer_count` 1-based; `IntakeResult.candidate_id` may be `UNAVAILABLE` (QUARANTINED only); fine-grained `IntakeFindingCode` (findings only, refusals are errors);
   `ContractError.field`; `StageError`, `IntakeError`. Regenerate fixtures.
2. `store/intake/`: `aseprite.py` and `png.py` (bounded pure readers), `validator.py` (one policy), `quarantine.py` (safe read, exclusive write), `service.py`.
3. `store/cli.py`, `__main__.py`; `STORE_ALLOWED` rows for `intake`, `cli`, `__main__`.
4. Tests: unit (CI) with a pure-Python Aseprite/PNG builder; integration (`needs_aseprite`) where real Aseprite is the oracle for the parser and builder.
5. Docs, then a checkpoint commit (store side).
6. **Separate commit, reviewed alone** (user decision relayed by asset-planner, option (a)): add `res.cels` and `res.aseprite_version` to `summary()` in
   `backend/lua/ops.lua`, re-pin with `python -m visual_assets.drawing.pin`, expose both as `cels` and `aseprite_version` in the drawing API summary; update docs
   that pin inspect output and the ADR line that calls `ops.lua` byte-identical to the spike.
7. `drawing/handoff.py` (`build_handoff`), `drawing/server/handoff_tools.py` (`export_handoff`, 15 -> 16 tools), tests and docs.
8. Close: ticket, working log, registry, monitoring; ask planner for review.

## Deviations from the ticket (all reported to asset-planner)
- Colour depth: the package has no colour-depth claim, so intake enforces a support policy (32-bit RGBA only) instead of comparing a claim.
- Also verified: `cel_count`, `palette_size`, `source_format`; all frames are walked (chunk headers only), not just the first.
- asset-planner changes after the checkpoint review: R1 intake id derives from all three file hashes (collision guard `intake_id_collision`); R2 atomic staging via a `.tmp-*` sibling and rename; R3 `PREVIEW_OUT_OF_BOUNDS`. The ticket 5 addition (preview-to-source binding) is recorded in ticket 5 and the known gaps.
- Palette size is unverifiable for an all-opaque-black stored palette (Aseprite rebuilds it from pixels): `PALETTE_UNVERIFIABLE`, quarantined.
- `producer_validation = FAILED` also quarantines (`PRODUCER_VALIDATION_FAILED`).
