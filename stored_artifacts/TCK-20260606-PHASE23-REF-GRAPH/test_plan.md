# Test Plan - Phase 23 Reference Graph and active-data validation

We will run the content unit tests to verify:
- Graph ignores YAML comments.
- Family-level consumer validation works.
- Compatibility files validate against clean source data.
- Typed edges are correctly created for module count maps (resources, buildings, services) with count metadata preserved.
- Composition to module edges are created correctly.

## Automated Tests

Run:
```bash
pytest tests/unit/content/
```
