---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION
phase: open
date: 2026-10-04
tags: [architecture, mcp]
---

# TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION

## Title
Durable draft sets (unadopted, tracked, never released) and one human `adopt-set` decision for a reviewed set

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
User, 2026-10-04 (blocking question "Drafts now, batch review"): the RPG is not final, and reviewing tiles one by one is
hard and biased. Draft many assets now with no adoption; review a whole set later (for example every map tile), then
approve it in one decision. Adoption stays the human gate (`AM-F01`): this changes its unit from one tile to one
reviewed set; it does not remove it.

## Scope
- **Draft set store.** `visual_assets/drafts/<set_id>/`, tracked in git, OUTSIDE the catalog. `build`, `release`,
  `runtime_export` and catalog `verify` never read it; `gc` never touches it (its 30-day rule is for local quarantine and
  review files only, which drafts must not depend on). A typed record `DraftSet` (`record_type: draft_set`) lists entries
  `{visual_key, detail?, draft_id, source_hash, pixel_hash, intake_hash}`; each entry's folder holds the source, the
  preview PNG and the intake result copied from a PASSED intake. Bounds use existing budgets where they fit
  (`MAX_SOURCE_BYTES`, `MAX_VISUAL_KEYS` entries); any new bound goes to the planner (owner decision), not invented.
- **Keeping a draft.** `draft keep <intake_id> --set <set_id> --as <visual_key> [--detail <value>]`: only from a PASSED,
  not revoked intake; the key and value must be declared; one entry per slot per set (replacing an entry is explicit:
  `--replace`). Agents may run it: it records no approval.
- **`draft verify`**: every file matches its recorded hash, every key/value is declared, no stray files.
- **Set adoption.** `adopt-set <set_id> --approver ... --approver-role ... --licence-evidence ...`, run by the user only.
  For every entry it does what `adopt` does today (re-render with the store's Aseprite and check it matches the preview,
  key and slot checks, holder checks), then shows ONE confirmation listing every entry, and writes one ordinary
  `AdoptionRecord` per entry (schema unchanged) plus one `SetAdoptionRecord` naming the set, its entries and the review
  evidence. All or nothing: any failure writes nothing. Existing single `adopt` stays.
- Docs: `docs/assets/store_contract.md` (drafts section, set adoption), ADR row (why set-level gating keeps `AM-F01`),
  `docs/assets/drawing_tools.md` (agent flow: draw -> hand off -> intake -> `draft keep`).

## Out of Scope
- The preview page (`TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE`), drawing the set (`...-TERRAIN-DRAFT-SET`).
- Any change to the meaning of an adoption record, release or runtime manifest. Any `src/` change.

## Acceptance Criteria
- [ ] A kept draft survives `gc` and a fresh clone; `build`/`release` ignore drafts (tests).
- [ ] `draft keep` refuses a QUARANTINED, revoked or unknown intake, an undeclared key/value, and a duplicate slot without `--replace`.
- [ ] `adopt-set` writes N adoption records + one set record on confirm, nothing on refusal or any single failure (tests incl. one bad entry among good ones); the notice lists every entry and the evidence ref.
- [ ] No agent tool (MCP server, scripts) can adopt a set; `adopt-set` needs the interactive confirmation like `adopt`.

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE, TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET

## Related Docs
- docs/assets/store_contract.md, docs/assets/retention_and_rollback.md, docs/architecture/visual_asset_foundation_adr.md

## Related Stored Artifacts
- None.

## Related Code Areas
- visual_assets/store/{adoption,cli,gc,verify,records}.py, visual_assets/store/contracts/, new visual_assets/drafts/

## Assumptions / Open Questions
- Licence evidence is stated once per set by the user; per-entry licence differences would need single `adopt`.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
