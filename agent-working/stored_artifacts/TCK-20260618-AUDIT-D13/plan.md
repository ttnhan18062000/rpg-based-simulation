# D13 Audit Plan

## Approach
Measure method. AST scan of all public functions in src/ for annotation gaps.
Cross-reference against validation patterns at system boundaries (API routes, content loading).

## Data Sources
- pyproject.toml / mypy.ini / pyrightconfig.json — type checker config (none found)
- Python AST scan via ast module — annotation counts per file
- src/api/server.py, src/api/engine_manager.py — API boundary
- src/api/routes/* — FastAPI route validation
- src/lab/workflows.py — lab workflow boundaries
- src/engine/patches.py — engine patch boundary
- src/core/state.py — serialization boundary

## Output
- docs/audits/D13_type_safety.md
