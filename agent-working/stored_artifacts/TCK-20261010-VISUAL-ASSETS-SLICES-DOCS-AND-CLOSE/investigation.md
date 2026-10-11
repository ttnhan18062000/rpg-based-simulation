---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICES-DOCS-AND-CLOSE
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation
- The parked sentence in `store_contract.md` listed slices, 9-slice and pivots; the animation section is the layout pattern. The docs-only tree is not guarded by the proof record, so docs commit first, then the proof re-run, then closure.
- The Makefile target picks the first python with pydantic; that interpreter lacks `mcp`, so the run used `make PYTHON3=<project venv>` (an interpreter choice, not a code change).
- Planner conditions: rc-0008 must rebuild 70/70 identical with the re-pinned Lua; the record shows 70/70 identical, 0 differing, 215 passed.
