# Test Plan — TCK-20260627-P2L-CONTENT-GUIDE

## Regression Surface

Existing tests that must continue to pass:

| Test | Why it matters |
|---|---|
| `tests/docs/test_contributor_guardrails.py` | Guardrails on engine docs; docs/content/ is a new dir, should not conflict |
| `tests/docs/test_doc_integrity.py` | Checks manifest-registered doc existence and headers |
| `tests/docs/test_design_patterns_currency.py` | Design pattern currency checks |

## New Tests Required

This is a docs-only ticket. No new behavioral tests required.

Completeness verification is done by manual cross-check of the 6 acceptance criteria:
1. Guide exists at `docs/content/authoring_guide.md`
2. All 6 scope areas are covered (module walkthrough, module types, initial_conditions,
   make targets, sharp edges, composition + scenario walkthroughs)
3. Sharp edges section names `observability_tags`, `provided_features`, catalog ID constraints
4. At least one make target listed per authoring task
5. `docs/REGISTRY.yaml` updated (via `make docs-registry`)
6. `make knowledge-index-update` run

## Scoped Pytest Commands

```bash
pytest tests/docs/ -x -v
```

This runs the three existing doc-integrity tests. None reference authoring_guide.md, so
the new file does not need to be registered in docs/engine/manifest.json.

## Anti-Drift Test Guards

- The guide references `src/scenarios/schema.py:ALLOWED_INITIAL_CONDITION_CATEGORIES` —
  if categories change, the guide will need updating. No automated test required now.
- The 7 module types match `REGISTERED_MODULE_TYPES` in `src/worldmodules/schema.py` —
  no automated test required; types are stable since worldgen-module-epic.
