---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION
phase: done
date: 2026-10-04
tags: [architecture, mcp]
---

# TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION

## Title
Durable draft sets (unadopted, tracked, never released) and one human `adopt-set` decision for a reviewed set

## Status
DONE

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
- [x] A kept draft survives `gc` and a fresh clone; `build`/`release` ignore drafts (tests).
- [x] `draft keep` refuses a QUARANTINED, revoked or unknown intake, an undeclared key/value, and a duplicate slot without `--replace`.
- [x] `adopt-set` writes N adoption records + one set record on confirm, nothing on refusal or any single failure (tests incl. one bad entry among good ones); the notice lists every entry and the evidence ref.
- [x] No agent tool (MCP server, scripts) can adopt a set; `adopt-set` needs the interactive confirmation like `adopt`.

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
- Re-checked against the code before building; the planner and owner settled the disagreements: (D1) an entry folder holds `package.json` too (adopt re-checks all three staged hashes and reads the package for width and height); (D2) `draft_id` is the intake id (strict `in-` + 16 hex); (D3) `source_asset_id` is recorded at `draft keep --source-asset-id`, default the key with dots as underscores plus `_<detail>`, refused if it exists in the catalog or in the set; (D4) the per-intake review check is replaced by a fresh Aseprite re-render per entry that must equal the draft's preview, a fresh `ReviewRenderCheck` per entry in `provenance/intake`, and a `SetAdoptionRecord` that stores the DraftSet's file hash (printed by the confirmation, to be shown by the preview page); (D5) drafts have their own atomic writer (`catalogwrite.publish` refuses paths outside the catalog) and new boundary rows `drafts` and `setadoption` (a gate layer); (D6) set records live in `provenance/set-adoptions/` because every reader parses `provenance/adoptions/*.json` as an `AdoptionRecord`; (D7/D8, owner, 2026-10-04: "256 tiles per set") `MAX_DRAFT_SET_ENTRIES = 256`, no limit on the number of sets, both records under the ordinary `MAX_RECORD_BYTES`.
- **Field dropped (planner-approved, no bound changed).** The widest `DraftSet` with a `source_hash` per entry measured 138887 B, over `MAX_RECORD_BYTES` (131072), so `DraftEntry` has no `source_hash`: the source is bound through source bytes -> the staged-file hash inside `intake_result.json` -> `intake_hash`, checked by `draft verify` and `adopt-set` through one shared function (`drafts.read_entry`), plus `pixel_hash` for the preview. Measured at 256 entries with maximum-length ids: `DraftSet` 116359 B, `SetAdoptionRecord` 60791 B (`test_record_bounds.py`, `budgets.md`).
- `adopt`'s checks were extracted (staged bytes, the same bytes not adopted or revoked, key/slot/holder, licence and approver, the record builders) into shared functions in `adoption.py`; `adopt`'s own tests are unchanged and green. `adopt-set` adds set-level checks the catalog cannot see before anything is written: two entries filling one effective slot or sharing source bytes are refused.
- Catalog `verify` learned `provenance/set-adoptions/` (each set record parses and every entry points at an adoption of the same intake, key and slot). `draft keep` is not an MCP tool; the MCP server still has no adopt, set or draft tool (tested).
- Tests changed on purpose: the CLI/docs command tests now expect `draft` and `adopt-set` (three human-only commands: `adopt`, `adopt-set`, `revoke`) and the docs gate regex accepts hyphenated command names.

## Test Summary
`tests/visual_assets`: 1322 passed (foreground, 2 GB cap); catalog `verify`: store ok; `draft verify`: drafts ok.
- New `test_drafts.py` (20 tests): keep (files, perms, sorted record, defaults; refuses QUARANTINED, unknown, revoked, undeclared key or value, value on a key without an axis, duplicate slot without `--replace`, source-asset-id collisions, same intake twice, set full, failed write leaves nothing); drafts survive the most aggressive `gc` and a fresh copy and are invisible to the catalog; **one test per link of the chain** (tampered source, intake result and pixel hash each refused by `draft verify`, and again by `adopt-set`); stray files, undeclared keys, duplicate effective slots, a missing entry; `adopt-set` writes N adoption records + one set record after ONE confirmation whose notice lists every entry, the licence and review evidence and the DraftSet hash; nothing is written on refusal, on a render mismatch, or when one entry among good ones fails; the decision arguments; duplicate source bytes; no terminal; no MCP tool.
- **Mutant:** skipping the re-render comparison in `adopt-set` (`if False:`) fails `test_a_render_that_does_not_match_the_draft_preview_is_a_hard_refusal`; restored (checked with `cmp`).

## Files Changed
- visual_assets/store/{drafts,setadoption}.py (new), contracts/draft.py (new), adoption.py (shared checks), cli.py, config.py, errors.py, identities.py, records.py, verify.py, contracts/__init__.py
- visual_assets/catalog/fixtures/contracts/{draft_set,set_adoption_record}.json (new)
- tests/visual_assets/store/unit/{test_drafts (new),test_record_bounds,test_cli,test_docs_commands,conftest}.py, test_boundaries.py
- docs/assets/{store_contract,budgets,drawing_tools}.md, docs/architecture/visual_asset_foundation_adr.md (D12)

## Completion Summary
Draft sets are kept in git outside the catalog with `draft keep` and checked with `draft verify`; the user-only `adopt-set` adopts a reviewed set in one decision, all or nothing, after re-proving every entry against Aseprite and binding the decision to the exact DraftSet bytes. Nothing was adopted by this ticket.

