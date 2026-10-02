"""Asset store: typed records, identities and the semantic registry loader (built); writers are NOT built yet.

Built: `errors`, `config`, `identities`, `contracts/`, `catalog/registry.py` (read-only), `intake/` and the `cli`
(`intake`, `review`, `list`, `show`; nothing tracked is written). Not built: adoption, build, release candidates, verify, gc. The planned modules and their order are in
docs/plans/visual-asset-foundation/README.md and tickets/todos/visual-asset-foundation/SEQUENCE.md. Nothing here may
import `visual_assets.drawing` (except `store/build` using the shared sandbox, later) or `src`.
"""
