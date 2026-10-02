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
| Intake quarantine | `visual_assets/catalog/.quarantine/` (gitignored) | the store's intake step only | designed; directory ignored, nothing writes it |
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

## Decisions still open

D2 (sources committed directly, no Git LFS), D3 (only adopted assets' PNGs committed; verified in CI by pixel hash) and D4
(artifact identity is the decoded-pixel hash) are **decided** (`docs/architecture/visual_asset_foundation_adr.md`). Still open: deployment profile (`AM1-W01`), signing/trust channel (`AM1-W08`),
retention numbers, the Aseprite licence review (`U-02`), numeric budgets (`U-05`) and CI with Aseprite (`U-14`).
