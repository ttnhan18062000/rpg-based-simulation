---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS
phase: done
date: 2026-10-02
tags: [architecture, mcp, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS

## Title
Read-only store tools and `submit_candidate` on the MCP server; complete the store documentation

## Status
DONE

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
   - `submit_candidate(handoff_id)` (changed by asset-planner 2026-10-03: the handoff id returned by `export_handoff`, i.e. `<candidate_id>--<12 hex of
     package.json sha256>`, not the candidate id, because several handoffs may exist for one candidate): runs store intake on a package previously written by `export_handoff`
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
   "After Work" folder rule in `CLAUDE.md` (the whole `agent-working/tickets/todos/visual-asset-foundation/` folder moves to
   `agent-working/tickets/done/` when every child is done).

## Out of Scope
- Any MCP tool that adopts, builds, releases, revokes, deletes or activates (D5).
- Runtime consumption, `frontend/` or `src/` changes.
- New store behaviour: this ticket only exposes what children 3-5 built.

## Acceptance Criteria
- [x] `export_handoff` then `submit_candidate` over stdio gives a `PASSED` intake for a real revision
      (integration, needs Aseprite); a tampered package gives `QUARANTINED` with findings.
- [x] `submit_candidate` with an unknown handoff id, a path-like id or `..` is refused and writes nothing; a bare candidate id is refused (handoff id required).
- [x] `store_list` and `store_show` change no file (tree byte-identical before and after), bound their output,
      and return no absolute path.
- [x] Tool-surface and boundary tests of scope items 2-3 pass, and each planted violation fails for its rule.
- [x] `docs/assets/store_contract.md` has no "designed, not built" item left that is in this epic's scope, and
      every command in it exists in the CLI (one test compares the documented command names to the CLI parser).
- [x] Epic acceptance criteria evaluated truthfully; anything not met is stated, not ticked.
- [x] `pytest tests/visual_assets -m "not slow and not extra_slow"` green without Aseprite; integration and
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
Staging artifacts: `agent-working/stored_artifacts/TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS/`.

- `visual_assets/store/readmodel.py`: shaped, bounded, read-only views (intakes, sources, artifacts, release candidates). It lives in the store because the boundary test forbids drawing code from even naming the catalog.
- `drawing/handoff.handoff_directory(handoff_id)`: only the exact `cand-<16 hex>--<12 hex>` shape resolves, always to `<workspace>/handoffs/<handoff_id>` (no path, no `..`, no bare candidate id, no symlink).
- `drawing/server/store_readonly_tools.py`: `submit_candidate`, `store_list`, `store_show` (19 tools in all); the server instructions state the gates in one sentence.
- Boundary rule: the drawing server may import from the store only `intake`, `readmodel`, `contracts`, `identities`, `errors`, `config` (an allowlist, stricter than the gate blacklist), with planted tests for every other layer.
- Docs: `store_contract.md` rewritten from "designed" to built with a command table and an MCP tool table that a test compares with the real CLI parser and server; plan README gains an "As built: deviations" section; status notes in the two older plan READMEs; ADR consequences.

### Where ticket and reality differed (reported to asset-planner)
1. The ticket names `store.catalog.release` (it is `store/release.py`); the planned server rule became an allowlist.
2. Drawing code may not reference the catalog at all, so the listing logic is a store layer (`readmodel`) and the tool module is thin. The tool module reads the clock for `created_at`, like the CLI.
3. Stdio tests run the server from an isolated copy of the `visual_assets` package so a successful submission can only write that copy's quarantine, never the real one.
4. An existing tool-surface test forbade tool names containing `submit` and `store_` (exactly the new tools); it is replaced by an exact-set test plus a forbidden-verbs and forbidden-parameter test.

## Test Summary
Every suite run separately under `systemd-run --user --scope -p MemoryMax=2G`. `tests/visual_assets`: 1071 passed with Aseprite; 870 passed, 201 skipped with the Aseprite binary unavailable (CI-like; the read model, handoff lookup, stdio tools and docs-versus-CLI tests all run there). `tests/tools` MCP registration, launcher hardening and path guards: 38 passed. Static + architecture + docs: 234 passed, 2 skipped, 1 xfailed.
- Real Aseprite over stdio: draw, `export_handoff`, `submit_candidate` gives PASSED; tampering with the handoff gives a different intake, QUARANTINED with `SOURCE_HASH_MISMATCH`; only the isolated copy's quarantine changed and nothing was adopted.
- 16 unknown, path-like, `..`, bare-candidate-id, newline and symlink handoff ids are refused and write nothing; `store_list` / `store_show` leave the tree byte-identical, are bounded and carry no absolute path; producer statements are labelled as claims.
- Mutation: 12 hand-applied mutants of the new guards plus the earlier batches; one survived at first (the `StoreError` to `ValueError` translation, equivalent over stdio because FastMCP wraps any exception) and led to a direct test of the helper's contract; all are now caught.

## Files Changed
Added: `visual_assets/store/readmodel.py`, `visual_assets/drawing/server/store_readonly_tools.py`, `tests/visual_assets/store/unit/{test_readmodel,test_docs_commands}.py`, `tests/visual_assets/drawing/test_store_tools_stdio.py`.
Changed: `drawing/{handoff.py,server/__init__.py,server/app.py}`, `store/errors.py` (`ReadError`), `tests/visual_assets/{test_boundaries.py,drawing/stdio_support.py,drawing/test_server_stdio.py,drawing/unit/test_handoff_unit.py,drawing/integration/test_server_stdio.py}`, docs (`store_contract.md`, `drawing_tools.md`, ADR, plan README, the two older plan READMEs), the epic and `SEQUENCE.md`. No `src/`, `frontend/`, requirements or pyproject change.

## Completion Summary
An agent can now submit a handoff for intake and read the store through the MCP server, and still cannot adopt, revoke, build, release or delete anything: no such tool exists, the server may import only the intake and read-only store layers, and the instructions and tests say so. The store contract documents every command and tool, checked against the CLI parser and the server. The epic is closed with its open items stated.
