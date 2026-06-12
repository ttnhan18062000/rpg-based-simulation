---
ticket_id: TCK-20260612-CONTENT-PIPELINE-CONTRACT
phase: test_plan
---

# Test Plan: Content Pipeline Contract

## Regression Surface (existing tests that must pass)
- tests/unit/content/test_content_usage_evidence.py::test_all_matrix_evidence_paths_exist
- tests/unit/content/test_catalog.py
- tests/unit/content/test_resolvers.py

## New Tests Required
None — this ticket writes documentation only, no source code changes.

## Scoped Pytest Commands
None for implementation. For verification only:
```
pytest tests/unit/content/ -x -q
```

## Validation Commands (DoD)
```bash
python3 tools/validate_frontmatter.py docs/content/
make docs-registry
```

## Anti-Drift Test Guards
- python3 tools/validate_frontmatter.py must exit 0
- make docs-registry must succeed (REGISTRY.yaml updated)
