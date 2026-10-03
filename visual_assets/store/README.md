# visual_assets/store — asset store logic (not implemented)

**Status: skeleton only. No store logic exists yet; see `agent-working/tickets/todos/visual-asset-foundation/SEQUENCE.md`
for the child tickets that build it, in order.**

This package will hold the producer-neutral store: typed records (`contracts/`), identities, intake into
quarantine and validation, the human-gated `adopt` and `revoke` commands, sandboxed build, release-candidate
assembly, `verify` and `gc`. The design, the command/gate table and the layering rules are in
`docs/plans/visual-asset-foundation/README.md`; the contract summary (designed vs built) is in
`docs/assets/store_contract.md`.

Rules that already hold (enforced by `tests/visual_assets/test_boundaries.py`):

- nothing under `visual_assets/` imports `src/`, and `src/` never imports `visual_assets`;
- `store` does not import `visual_assets.drawing` (the shared sandbox in `store/build` is the one later exception);
- `drawing` never writes under `visual_assets/catalog/`.
