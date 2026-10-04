---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER
artifact_type: test_plan
tags: [mcp, live-map, testing]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER

Rerun of all M5 checks on one clean commit; no new product code. Charter and record validated by frontmatter checks and the docs tests.

## Proof Plan

- Level: integration (local real browsers) plus unit.
- Proof kind: executable reruns on a named clean commit.
- Oracle source: the ticket's acceptance criteria and the planner rulings.
- Expected effect: all pass; classifications follow the evidence, never a pass by default.
- Selected commands: `pytest tests/visual_assets tests/docs tests/architecture tests/static`; `npx vitest run`; scoped eslint; `npm run build`; `npx playwright test -c playwright.pilot.config.ts` and `playwright.rehearsal.config.ts` (local).
