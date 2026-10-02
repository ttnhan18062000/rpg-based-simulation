---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS
phase: open
date: 2026-10-02
tags: [architecture, mcp, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS

## Title
Read-only store tools and `submit_candidate` on the MCP server; complete the store documentation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 6 (last) of `TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION`. Let an agent submit a handoff package for intake
and read the store's state through the MCP server, without ever being able to adopt, build, release, revoke or
delete. Finish the store documentation and close the epic's bookkeeping. Blocked by
`TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE`. Same branch (`visual-assets-store`).

## Scope
1. `visual_assets/drawing/server/store_readonly_tools.py`, three tools:
   - `submit_candidate(candidate_id)`: runs store intake on a package previously written by `export_handoff`
     (looked up by id inside the experiment workspace, never by a caller-supplied path); returns the verdict and
     findings. Writes only the quarantine.
   - `store_list(kind)`: bounded listing of intakes, sources, artifacts, release candidates.
   - `store_show(kind, id)`: one record as a shaped summary, not raw file contents and no absolute paths.
2. Boundary rule in `tests/visual_assets/test_boundaries.py`: `server` may import from the store only an explicit
   allowlist of read functions plus intake; importing `store.adoption`, `store.revoke`, `store.build`,
   `store.catalog.release`, `store.gc` or `store.cli` is a violation, with planted tests.
3. Tool-surface test: the registered tool names are exactly the expected set; no tool name or description
   offers adopt, build, release, revoke, gc or activation. Server instructions state the gates in one sentence.
4. Docs: `docs/assets/store_contract.md` rewritten from "designed, not built" to what is built, with each
   command, its gate, what it writes and whether it is tracked; `docs/assets/drawing_tools.md` tool reference
   (new tools, count); `docs/plans/visual-asset-foundation/README.md` matches what was built or lists each
   deviation; status notes in `docs/plans/visual-asset-management-runtime-integration/README.md` and
   `docs/plans/aseprite-mcp-pixel-art/README.md`; ADR consequences; `make knowledge-index-update`.
5. Epic close-out: tick the epic's acceptance criteria that hold, record what stays open, and follow the
   "After Work" folder rule in `CLAUDE.md` (the whole `tickets/todos/visual-asset-foundation/` folder moves to
   `tickets/done/` when every child is done).

## Out of Scope
- Any MCP tool that adopts, builds, releases, revokes, deletes or activates (D5).
- Runtime consumption, `frontend/` or `src/` changes.
- New store behaviour: this ticket only exposes what children 3-5 built.

## Acceptance Criteria
- [ ] `export_handoff` then `submit_candidate` over stdio gives a `PASSED` intake for a real revision
      (integration, needs Aseprite); a tampered package gives `QUARANTINED` with findings.
- [ ] `submit_candidate` with an unknown id, a path-like id or `..` is refused and writes nothing.
- [ ] `store_list` and `store_show` change no file (tree byte-identical before and after), bound their output,
      and return no absolute path.
- [ ] Tool-surface and boundary tests of scope items 2-3 pass, and each planted violation fails for its rule.
- [ ] `docs/assets/store_contract.md` has no "designed, not built" item left that is in this epic's scope, and
      every command in it exists in the CLI (one test compares the documented command names to the CLI parser).
- [ ] Epic acceptance criteria evaluated truthfully; anything not met is stated, not ticked.
- [ ] `pytest tests/visual_assets -m "not slow and not extra_slow"` green without Aseprite; integration and
      stdio tests green with it; `tests/tools/test_mcp_json_registration.py` and
      `tests/tools/test_mcp_launcher_hardening.py` green.

## Related Tickets
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION (parent)
- TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE (blocks this)

## Related Docs
- docs/plans/visual-asset-foundation/README.md
- docs/architecture/visual_asset_foundation_adr.md (D5)
- docs/assets/store_contract.md, docs/assets/drawing_tools.md

## Related Stored Artifacts
- None yet.

## Related Code Areas
- visual_assets/drawing/server/, visual_assets/store/, tests/visual_assets/, docs/assets/

## Assumptions / Open Questions
- The server process and the store share one machine and one checkout; there is no remote store.
- Restarting the MCP server is needed for new tools to appear in a running session; say so in the docs.

## Implementation Notes
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(open)
