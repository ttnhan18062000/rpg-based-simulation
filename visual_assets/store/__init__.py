"""Asset store: typed records, identities and the semantic registry loader (built); writers are NOT built yet.

Built: `errors`, `config`, `identities`, `contracts/`, `catalog/registry.py` (read-only). Not built: intake, adoption,
build, release candidates, verify, gc, CLI. The planned modules and their order are in
docs/plans/visual-asset-foundation/README.md and tickets/todos/visual-asset-foundation/SEQUENCE.md. Nothing here may
import `visual_assets.drawing` (except `store/build` using the shared sandbox, later) or `src`.
"""
