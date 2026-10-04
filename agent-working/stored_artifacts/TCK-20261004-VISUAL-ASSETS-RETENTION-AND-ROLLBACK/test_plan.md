---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK
artifact_type: test_plan
tags: [mcp, live-map, testing]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK

gc: young PASSED intake and its review protected (0, 29 and exactly 30 days); old one and its review listed and deleted; adopted intake never expired; tracked state never listed or removed; unreferenced tracked artifacts reported and never deleted; nothing reported when every artifact is in a release. Drill: five combinations plus a mid-load switch. Mutants: age guard, adoption guard, infinite age, empty report, mixed snapshot.

## Proof Plan

- Level: unit.
- Proof kind: executable tests plus recorded mutants.
- Oracle source: the ticket's acceptance criteria and the planner decision.
- Expected effect: all pass; each mutant fails a named test.
- Selected commands: `pytest tests/visual_assets`; `npx vitest run src/visualAssets`; scoped eslint.
