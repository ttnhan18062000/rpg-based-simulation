---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY
date: 2026-07-30
tags: [dashboard, observability, api-design]
---

# Test Plan — TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY

## Regression Surface (existing tests that must pass)

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py -q
```

## New Tests Required (per AC)

- A test asserting `facets['tags']` equals `sorted(tag_registry.load_registry(repo_root).keys())`
  regardless of which tags appear in the filtered/paginated ticket corpus — including a case where
  a registered tag has zero matching tickets in the fixture corpus and still appears.
- A test asserting `facets['tags']` is unchanged when a tier/layer/status/priority/tags query
  filter is applied — mirrors the existing canonical-facet test pattern already used for
  `tiers`/`layers`/`statuses`/`priorities`.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py -q
```

## Anti-Drift Test Guards

- The new tests must use a real `tag_registry.jsonl` fixture (tmp_path-rooted), not a mocked
  return value — mirrors this test file's existing fixture-based style for the other 4 canonical
  facets.
- Confirm no `TicketsView.tsx`/`TicketsView.test.tsx` change was needed by reading both, not
  assuming — record the confirmation in Implementation Notes.
