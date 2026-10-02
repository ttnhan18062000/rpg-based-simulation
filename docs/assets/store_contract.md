---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-02
tags: [architecture, mcp, documentation, rendering]
---

# Visual asset store contract (designed, NOT built)

**Status: nothing in this document is implemented.** `visual_assets/store/` and `visual_assets/catalog/` are
empty skeletons created by `TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT`. This page records what the store is meant
to guarantee so later tickets build to one contract. Each section is marked **designed** or **built**; today the
only **built** items are the layout, the layering test and the rule that drawing tools cannot write the catalog.

Source of truth for vocabulary and gates: `docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md`
(sections 6-9) and `docs/plans/visual-asset-management-runtime-integration/`. Physical layout, layering rules and the
command table: `docs/plans/visual-asset-foundation/README.md`. Build order: `tickets/todos/visual-asset-foundation/SEQUENCE.md`.

## Lifecycle and gates (designed)

```
candidate --(human review)--> adoption approved --> adopted source --> validated build
   --> release candidate --(compatibility validation, human activation)--> active release
```

No tool may collapse a gate. An agent can draw and hand off a candidate; only a human-run command can adopt it;
nothing in this foundation activates anything at runtime (`AM-M5`-`M7` are out of scope).

## Three places, three writers

| What | Where | Who may write | State |
|---|---|---|---|
| Experiment workspace (every drawing revision) | `~/.cache/rpg-aseprite-mcp/` | the drawing tools | built |
| Intake quarantine | `visual_assets/catalog/.quarantine/` (gitignored) | the store's intake step only | designed; directory ignored, nothing writes it |
| Managed store | `visual_assets/catalog/` | the store's human-gated commands only | layout built (empty); commands designed |

## What is built now

- `visual_assets/store/` (package marker and README only) and `visual_assets/catalog/` (README, `STORE_FORMAT`, seven empty directories).
- `tests/visual_assets/test_boundaries.py`: `drawing` has no write path into `catalog/` (it may not even reference the path),
  `store` does not import `drawing`, nothing imports `src/` and `src/` never imports `visual_assets`.

## What is designed, not built

| Piece | Designed behaviour | Child ticket |
|---|---|---|
| Typed records | versioned strict records: handoff package, intake result, adoption record, source, artifact, release candidate manifest, definitions | 2 |
| Identities | `visual_key`, `source_asset_id`, `source_revision`, `artifact_id`, `catalog_id` | 2 |
| Intake | bounded copy into quarantine, claims checked against staged bytes (hashes, format, bounds, symlinks, traversal, licence state), immutable `IntakeResult` | 3 |
| Adoption / revoke | human-gated, record a named approver and licence state, refuse a failed, revoked or already-adopted intake | 4 |
| Build / release candidate | sandboxed allowlisted export, canonical pixel hash, immutable candidate manifests, no "active" pointer | 5 |
| `verify` / `gc` | whole-store integrity in pure Python (runs in CI); reachability-based dry-run gc | 5 |
| MCP store tools | read-only `store_list` / `store_show` and `submit_candidate`; never adopt, build, release, revoke or gc | 6 |

## Decisions still open (not made by this ticket)

D2 (commit sources without Git LFS), D3 (commit generated PNGs and verify by canonical pixel hash in CI) and D4 (hash
artifacts by decoded pixels) are **proposed** in `docs/architecture/visual_asset_foundation_adr.md`; they are re-confirmed with
the user before the tickets that depend on them. Deployment profile (`AM1-W01`), signing/trust channel (`AM1-W08`),
retention numbers, the Aseprite licence review (`U-02`) and CI with Aseprite (`U-14`) remain open.
