---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-COGNITION-DIFF-EVENTS
artifact_type: investigation
tags: [cognition, diff, events]
---

# investigation.md - Graph Diff Mechanics

Evaluating comparative graph models:
- Node added/removed/changed detection: check keys inside node collections.
- Edge changes: compare source-target-kind tuples.
- Metadata: compare current project, objective, and overload fields.
- Sorting: to ensure determinism, all additions/removals will be alphabetically sorted by node ID or edge source-target keys before output.
