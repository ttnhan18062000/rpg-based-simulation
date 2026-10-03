"""Asset store: typed records, identities, intake, human-gated adoption and revocation, sandboxed build, release candidates, verify and gc.

Built: everything in `docs/assets/store_contract.md`. Not built: the MCP store tools (`TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS`). Layering rules are enforced by
`tests/visual_assets/test_boundaries.py`: nothing here imports `src`, only `store/build` imports `visual_assets.drawing` (the shared sandbox, nothing else), and the
drawing code may never import the human-gated or tracked-catalog writers. The planned modules and their order are in docs/plans/visual-asset-foundation/README.md and
agent-working/tickets/todos/visual-asset-foundation/SEQUENCE.md.
"""
