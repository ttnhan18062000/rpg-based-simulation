---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER
artifact_type: investigation
tags: [architecture, documentation]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER

Read for this ticket: the plan's acceptance cells, proposal 9.1-9.6, `store_contract.md`, the ADR (D1-D12), `budgets.md`, `retention_and_rollback.md`, `aseprite_licence_review.md`, `surface_rehearsal_result.md`, `pilot_charter_am6.md`, `pilot_terrain_key.md`, and the store contracts, registry loader, `gc`, `revoke`, `verify`, build, intake and the client `manifest`/`resolver`/`fallback`/`loader` code.

Findings that shaped verdicts:
- `RuntimeManifest` carries `schema_version` and `fallback_contract_version` (both literal 1, both rejected by the client when different) and nothing else about compatibility: no client, renderer, descriptor or capability range. Client range is `N/A` under Profile A (D8); renderer and capability ranges are `GAP`.
- `VisualKeyDefinition` has no safety-class field, so `W02` safety-class link is `GAP`.
- `variant_axes` exist and are bounded but nothing resolves them and all 23 committed keys have `variant_axes: []`; only the detail axis has a deterministic rule.
- No doc or code names who derives a visual key from game state; `TERRAIN_DRAFT_KEYS` is the dev-only draft page's mapping.
- `gc --delete` writes no deletion record; there is no lock; no storage-pressure rule.
- Docs that still say `AM1-W01`, `W08`, `U-02` or retention are open (store contract "Decisions still open", ADR Status, plan README) contradict ADR D8-D10 and `budgets.md`; listed in the register, not fixed (the plan README status lines belong to M1-STATUS-CLOSEOUT).
- The 2026-10-04 charter draft still names `pilot/rc-0001` and "no variant axes"; the committed release is `pilot/rc-0003` with three slots.
