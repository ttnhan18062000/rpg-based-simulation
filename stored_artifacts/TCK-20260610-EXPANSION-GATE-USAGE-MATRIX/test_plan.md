---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-EXPANSION-GATE-USAGE-MATRIX
artifact_type: test_plan
tags: [expansion, gate, usage, matrix]
---

# Test Plan — TCK-20260610-EXPANSION-GATE-USAGE-MATRIX

## Existing Tests to Re-run

```
pytest tests/integration/content/test_expansion_gate.py -v
pytest tests/integration/content/test_active_data_consumer.py -v
```

All 12 gate items must pass after refactor.

## Regression

```
pytest tests/unit/content/ -v
```

No content test should regress.

## Acceptance Criteria Checks

| Criterion | How verified |
|---|---|
| No `_STATE_RE`, `_ACTIVE_STATES`, `_ID_RE`, `_KNOWN_INACTIVE_CONTENT` | `grep` shows absent |
| Gate 04 uses ContentUsageMatrix | Code review: calls `collect_family_graph_violations` |
| `tests/helpers/content_usage_gate.py` exists | File present |
| Both gate tests call shared helper | Code review |
| No "must stay in sync" comment | `grep` shows absent |
| No stale CAT-REL-099 xfail language in docstring | Manual review |
| `re` import removed | `grep` shows absent |
| YAML `# STATE:` comments unchanged | Content files untouched |
| All expansion gate tests pass | pytest exit 0 |
