---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY
date: 2026-07-30
tags: [dashboard, observability, api-design]
---

# Plan — TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY

## Ordered Steps

1. **Import `tag_registry` in `ingest.py`.** Add `import tag_registry` alongside the existing
   `import layer_registry` (line 51), same module-level cross-package pattern.
2. **Change `facets["tags"]`** (line 620) from `_distinct_sorted(tag for r in filtered for tag in
   r["tags"])` to `sorted(tag_registry.load_registry(self._repo_root).keys())`.
3. **Rewrite the stale comment block** (lines 605-611) explaining the old "tags is genuinely
   open-vocabulary, not a small closed enum" rationale — replace with a note that the registry now
   makes `tags` canonical too, following the same pattern as the other four, with the deliberate
   consequence (legacy/non-registered tags and phase-N tags won't appear) stated inline.
4. **Update `docs/parity_ledger/infrastructure.yaml` INFRA-275** — `text`/`v2_evidence` updated to
   describe registry-derived (not corpus-derived) behavior.
5. **Update `docs/guides/agent_ops_dashboard.md` and
   `docs/observability/agent_ops_dashboard_contract.md`** — Tickets view tags-filter description
   updated to registry-derived, matching how tier/layer/status/priority are already described.
6. **Add 2 new tests** to `tests/tools/test_agent_ops_dashboard_ingest.py` per test_plan.md.
7. **Verify `TicketsView.tsx`/`TicketsView.test.tsx` need no change** (read both, confirm, record
   in Implementation Notes — do not skip this verification).
8. **Run regression suite.**

## Files to Change

`src/api/agent_ops_dashboard/ingest.py`, `docs/parity_ledger/infrastructure.yaml`,
`docs/guides/agent_ops_dashboard.md`, `docs/observability/agent_ops_dashboard_contract.md`,
`tests/tools/test_agent_ops_dashboard_ingest.py`.

## Explicit Scope Guards

- No change to `tools/tag_registry.py` — consumer-side only.
- No change to `TicketsView.tsx` unless step 7 finds a genuine need (not expected).

## Dependency Map

Step 1 before 2. Steps 3-5 independent of 1-2, can run in any order. Step 6 after 1-2 (needs the
real behavior to test against). Step 8 last.

## Acceptance Criteria Map

- AC1 (facets['tags'] == sorted(registry.keys())) → Steps 1-2, tested in Step 6
- AC2 (unaffected by active filters) → Step 2 (reads registry directly, never `filtered`), tested in Step 6
- AC3 (same import pattern as layer_registry) → Step 1
- AC4 (INFRA-275 updated) → Step 4
- AC5 (deliberate behavior-change stated explicitly) → Step 3 + this investigation.md's Risks section
- AC6 (docs updated) → Step 5

## Unresolved Questions

None.
