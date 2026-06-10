# Test Plan — TCK-20260610-ACTIVE-DATA-CONSUMER-REPAIR

## Regression Surface

- `tests/integration/content/test_expansion_gate.py` — gate 04 (no new dead active data) uses inline
  baseline from test_active_data_consumer; must stay in sync if KNOWN_INACTIVE_CONTENT changes
- All other content integration tests must continue passing

## New Tests Required

Replace the 5 existing STATE-comment-driven tests with 3 new ContentUsageMatrix-driven tests:

| New Test | What it validates |
|---|---|
| `test_active_families_have_documented_consumers` | Each active family in ContentUsageMatrix has `resolver_component` or `compile_runtime_consumer` set |
| `test_active_families_have_graph_coverage` | For each active family, at least one record has an incoming reference graph edge |
| `test_content_usage_matrix_covers_catalog_families` | ContentUsageMatrix covers all families loaded by CatalogRepository |

## Scoped Pytest Commands

```bash
# Run the replacement test file
pytest tests/integration/content/test_active_data_consumer.py -v --tb=short

# Regression: expansion gate should still pass gate 04
pytest tests/integration/content/test_expansion_gate.py::test_gate_04_no_new_dead_active_data -v

# Full content integration
pytest tests/integration/content/ -v -q
```

## Anti-Drift Test Guards

- No test in the replacement file should contain `re.match`, `# STATE:`, or any YAML comment parsing
- Test names must not mention "STATE" or "state markers"
