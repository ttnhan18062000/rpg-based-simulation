# Implementation Sequence — visual-asset-foundation

`TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION` is the epic-tier parent and is not implemented directly. Structure
and layering rules: `docs/plans/visual-asset-foundation/README.md`. All children land on branch
`aseprite-mcp-pixel-art` (PR #286) unless that PR merges first, in which case later children use a fresh branch.

## Order

1. `TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT` (P1, **in progress**, ticket in `tickets/inprogress/`) — move and
   restructure the drawing tools into `visual_assets/drawing/`, tests into `tests/visual_assets/drawing/`, with no
   behaviour change; boundary test; CI step; `.mcp.json` + launcher; `store/` and `catalog/` skeletons (no logic);
   docs and ADR; plan-package status updates. Everything else depends on this.
2. Store contracts and identities (not yet filed) — `visual_assets/store/contracts`, `identities`, semantic
   registry; pure and fully CI-tested. Blocks 3-5.
3. Intake (not yet filed) — `CandidateHandoffPackage` builder in `drawing/handoff.py`, quarantine, independent
   validator, `IntakeResult`; `review` export of candidate previews into the local gitignored `.review/` area.
4. Adoption and provenance (not yet filed) — human-gated `adopt` and `revoke`, records, audit-reconstruction test.
   Re-confirm decision D2 with the user before starting.
5. Build and release candidate (not yet filed) — sandboxed export, canonical hash, manifest, `verify`, `gc`.
   D3 is decided (only adopted assets' PNGs are committed; a local gitignored `.review/` area holds candidate
   previews). Re-confirm decision D4 with the user before starting.
6. Store docs and read-only MCP store tools (not yet filed) — `docs/assets/store_contract.md` completed;
   `store_list`, `store_show`, `submit_candidate` on the server; never adopt/build/release/revoke.

Children 2-6 are filed as tickets when their turn comes, by re-investigating the then-current repository.
