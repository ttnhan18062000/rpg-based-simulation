# Implementation Sequence — visual-asset-foundation

`TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION` is the epic-tier parent and is not implemented directly. Structure
and layering rules: `docs/plans/visual-asset-foundation/README.md`.

**All six children are done.** Child 1 landed in PR #286 (merged, branch finished). Children 2-6 were built together on branch `visual-assets-store`
as one batch (one PR, opened only when the planner says the batch is ready; not yet opened). Each ticket's commit was reviewed by the planner (`asset-planner`).

## Order

1. `TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT` (P1, **done**, `agent-working/tickets/done/`).
2. `TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS` (P1) — typed records, identities, semantic registry loader; pure,
   fully CI-tested. Also carries the D2/D4 doc updates and child 1's last checkbox. Blocks 3-6.
3. `TCK-20261002-VISUAL-ASSETS-STORE-INTAKE` (P1) — `export_handoff`, quarantine, independent validator,
   `IntakeResult` (kept in the gitignored quarantine until adoption), local `review` export, first CLI commands.
4. `TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION` (P1) — human-gated `adopt` and `revoke`, records, audit
   reconstruction. First tracked catalog writes.
5. `TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE` (P1) — sandboxed export, `pixels-v1` hash, release-candidate
   manifest, `verify`, `gc`.
6. `TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS` (P2) — `submit_candidate`, `store_list`, `store_show`; store
   docs completed; epic close-out.

Strictly sequential: each ticket depends on the one before it.

## Decisions

- D2 (sources committed directly, no Git LFS) and D4 (artifact identity is the decoded-pixel hash): confirmed by
  the user on 2026-10-02.
- D3 (only adopted assets' PNGs are committed; candidates stay local in gitignored `.review/`): decided by the
  user on 2026-10-02.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what
  actually landed; where they disagree, tell the planner instead of guessing.
