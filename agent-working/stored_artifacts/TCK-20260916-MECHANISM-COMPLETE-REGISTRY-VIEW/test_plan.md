---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW
artifact_type: test_plan
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW

## Scoped suite

```
.venv313/bin/python3 -m pytest tests/unit/tools/ tests/unit/engine/test_capability_registry.py tests/mechanic_scenarios/ -q
```

## Cases

- `test_mechanism_registry_view.py` (8 tests): combined view includes every mechanism (not just
  unverified), sorted by priority descending, evidence classification matches the verification
  view's own runtime/static/unverified split, render reports verification counts at the head,
  render is not truncated, make target generates the file, `--check` mode detects staleness, the
  real committed file is up to date.
- `test_mechanism_registry_html.py` (7 tests): every mechanism id appears, the epic ticket is
  linked and its specific measured figures are NOT restated verbatim (load-bearing), HTML escaping
  is wired in, render is not truncated (accounting for the header `<tr>`), make target works,
  `--check` mode detects staleness, the real committed file is up to date.

## Result

165 tests passing in the full scoped suite, both with `graphify-out/` present and with it
genuinely moved aside and restored.
