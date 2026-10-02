---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-02
tags: [architecture, mcp, documentation, rendering]
---

# Visual asset store contract (partly built)

**Status: the typed records, identities and the semantic registry loader are built; every store writer is still
designed only.** `visual_assets/store/` and `visual_assets/catalog/` were created as skeletons by
`TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT`; `TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS` added the pure contract layer.
This page records what the store is meant to guarantee so later tickets build to one contract. Each section is marked
**designed** or **built**.

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
| Intake quarantine | `visual_assets/catalog/.quarantine/` (gitignored) | the store's intake step only | **built** (store side); holds the staged files and the `IntakeResult` until adoption |
| Local review area | `visual_assets/catalog/.review/` (gitignored) | `review` only | **built** |
| Managed store | `visual_assets/catalog/` | the store's human-gated commands only | layout built (empty); commands designed |

## What is built now

- `visual_assets/store/` with `errors`, `config`, `identities`, `contracts/` and `catalog/registry.py` (read-only), and `visual_assets/catalog/`
  (README, `STORE_FORMAT` = version 1, the zero-key `definitions/visual_keys.yaml`, synthetic `fixtures/contracts/`, other directories empty).
- Typed records (`extra="forbid"`, frozen, strict, `record_type` + `schema_version`, no free-form field): `CandidateHandoffPackage`,
  `IntakeResult`, `AdoptionRecord`, `RevocationRecord`, `SourceRecord`, `ArtifactRecord`, `ReleaseCandidateManifest`,
  `VisualKeyRegistry`. Canonical JSON (`canonical_json`) and strict parsing (`parse_record`: oversize, UTF-8, duplicate keys, NaN,
  unknown fields, wrong type, unsupported version each rejected with a stable `ContractError.code`).
- Identities with no normalisation: `VisualKey`, eight opaque id types, `SourceRevision`, `FileHash` (`sha256:`), `PixelHash`
  (`pixels-v1:`; the algorithm is child 5), `UtcTimestamp`.
- Registry loader: duplicate YAML keys, anchors, alias problems and the reserved `fixture.*` namespace are rejected; nothing registers dynamically.
- Intake (store side; `python -m visual_assets.store intake|review|list|show`): the package directory is opened without following symlinks and read
  into memory first (refused before any byte is copied, leaving no quarantine directory, for a symlink, extra file or sub-directory, oversize file,
  FIFO or hard-linked file; these are `StageError`s, not findings). The independent validator then judges the bytes with one policy for every
  producer class and records an immutable `IntakeResult` **inside the quarantine directory** (`in-` + 16 hex of the `package.json` hash). Re-submitting the
  identical package returns the existing result and writes nothing; the same `package.json` with different source or preview bytes is refused.
  `review` re-verifies the staged hashes and exports the preview plus a text summary of a PASSED intake to `.review/`. No intake step adopts anything.
- `tests/visual_assets/test_boundaries.py`: `drawing` has no write path into `catalog/` (it may not even reference the path),
  `store` does not import `drawing`, nothing imports `src/` and `src/` never imports `visual_assets`.

## What is designed, not built

| Piece | Designed behaviour | Child ticket |
|---|---|---|
| Intake | bounded copy into quarantine, claims checked against staged bytes (hashes, format, bounds, symlinks, traversal, licence state), immutable `IntakeResult` | 3 |
| Adoption / revoke | human-gated, record a named approver and licence state, refuse a failed, revoked or already-adopted intake | 4 |
| Build / release candidate | sandboxed allowlisted export, canonical pixel hash, immutable candidate manifests, no "active" pointer | 5 |
| `verify` / `gc` | whole-store integrity in pure Python (runs in CI); reachability-based dry-run gc | 5 |
| MCP store tools | read-only `store_list` / `store_show` and `submit_candidate`; never adopt, build, release, revoke or gc | 6 |

## Known gaps (stated, not hidden)

- Animation metadata beyond `frame_count` and `tag_count` (per-frame durations, tag ranges, loop modes) is not part of the handoff package or checked by intake
  (proposal 9.6 lists "animation metadata"; ticket 3 adds only the producer state).
- **Palette size is unverifiable for an all-opaque-black stored palette.** Aseprite 1.3.18.6 rebuilds such a palette from the image when it loads a file
  (size = 1 + distinct opaque colours), which needs pixel decoding. Intake quarantines it with `PALETTE_UNVERIFIABLE`. Only a never-edited first revision
  carries one; any edit re-saves a palette with real entries. Every other palette is checked exactly against what Aseprite reports.
- Intake accepts only 32-bit RGBA sources (`SOURCE_UNSUPPORTED_COLOR_DEPTH` otherwise); the package carries no colour-depth claim, so it is a support policy, not a claim check.
- The unsupported-feature list (`unsupported:tilemap`, `...indexed_color`, `...grayscale`, `...linked_cels`, `...external_reference`) and the preview/file size bounds are provisional (`U-05`).

## Decisions still open

D2 (sources committed directly, no Git LFS), D3 (only adopted assets' PNGs committed; verified in CI by pixel hash) and D4
(artifact identity is the decoded-pixel hash) are **decided** (`docs/architecture/visual_asset_foundation_adr.md`). Still open: deployment profile (`AM1-W01`), signing/trust channel (`AM1-W08`),
retention numbers, the Aseprite licence review (`U-02`), numeric budgets (`U-05`) and CI with Aseprite (`U-14`).
