---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE
artifact_type: plan
tags: [simulation-quality, world, economy, corpus, calibration]
---

# plan.md — TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE

## Ordered Steps

1. **Verify gap #2 against real corpus data** before authoring anything — computed node-per-region
   density across all 19 worlds via `world_compile_report.json`, found `resource_dense_basin`
   (2.33 density, 3 regions) already sits well outside the gap text's claimed "roughly flat
   1.3-1.75" range, and is already documented in the per-world table as closing this gap.
2. **No new world authored** — would duplicate `resource_dense_basin`'s already-established role.
3. **Correct `corpus_tier_taxonomy.md`'s stale gap-list section** — mark gap #2 CLOSED, citing
   `resource_dense_basin`, matching the correction pattern already applied to gap #1 in the
   sibling ticket.
   - Files: `docs/simulation_quality/corpus_tier_taxonomy.md`.
4. **Fill this ticket's Completion Summary.**

## Scope Guards

- Do NOT author a new world — confirmed unnecessary before any world-authoring work began (unlike
  the sibling gap-1 ticket, which built a draft world before catching the redundancy; this ticket
  verified first).
- Do NOT touch `resource_dense_basin` itself — correct, already-anchored, already-committed.

## Dependency Map

Step 3 depends on step 1's finding. No other dependencies.

## Acceptance Criteria Map

- AC1 (new world with density decoupled from map size) → **not met, deliberately** — found
  unnecessary; investigation.md documents why.
- AC2 (classified in corpus_tier_taxonomy.md) → N/A, no new world.
- AC3 (anchors committed, tests pass) → N/A, no new anchors; existing regression suite verified
  unaffected.
- AC4 (gap #2 entry marked closed, citing this ticket) → Step 3.

No unresolved questions requiring human review.
