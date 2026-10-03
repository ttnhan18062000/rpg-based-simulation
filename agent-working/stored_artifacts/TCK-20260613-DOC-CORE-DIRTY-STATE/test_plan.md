---
ticket_id: TCK-20260613-DOC-CORE-DIRTY-STATE
phase: test_plan
date: 2026-06-13
---

# Test Plan: TCK-20260613-DOC-CORE-DIRTY-STATE

## Ticket Type

Documentation-only ticket. No new source code is added or modified. No new tests are required.

---

## Existing Tests That Must Still Pass

These tests verify the behaviors being documented. They must remain green after the docs are merged.

### Dirty set correctness and leak detection

```
tests/perf/test_dirty_set_integrity.py
```

Covers:
- `test_dirty_set_exhaustive_movement` — movement tracking via `DirtySet.from_update()`
- `test_dirty_set_catch_shadow_mutation` — `DirtySetLeakError` on undeclared entity mutation
- `test_dirty_set_incremental_merge` — multi-phase DirtySet accumulation via `DirtySet.merge()`
- `test_dirty_set_exhaustive_world_objects` — resource node tracking and leak detection

### Dirty set vs. full scan parity

```
tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity
```

Covers: bit-identical state hash between `DirtySet`-optimized path and `force_full_scan=True` reference path over 100 ticks. Marked `@pytest.mark.slow`.

### Authoritative apply isolation and determinism

```
tests/integration/pipeline/test_authoritative_apply.py
```

Covers:
- `test_generation_isolation` — prior state not mutated by `apply_generation()`
- `test_deterministic_apply_order` — deterministic entity update ordering
- `test_resource_update_determinism` — global resource delta application

### Architecture boundary guards

```
tests/architecture/test_phase18_import_boundaries.py
tests/architecture/test_phase18_cognition_migration_linter.py
tests/architecture/test_phase19_hot_path_safety_contract.py
tests/architecture/test_phase19_observability_boundaries.py
```

Covers: layer isolation (core never imports domains), EntityState flat field restriction, hot-path safety contract, observability boundary definitions.

---

## New Tests Required

**None.** This is a documentation-only ticket. The behaviors being documented are already verified by the tests listed above.

If the investigation exposed any code-level gaps (see Risks section of `investigation.md`), those are tracked separately:

- The `DirtySet.from_update()` vs `DirtySetBuilder.mark_from_update()` discrepancy on `e_upd.task` is a pre-existing edge case, not introduced by this ticket. A separate bugfix ticket should address it if confirmed.

---

## Scoped Pytest Commands

Run the full set of tests relevant to this documentation area without running the entire suite:

```bash
# Dirty-set integrity and parity (fast subset, excludes slow parity test)
pytest tests/perf/test_dirty_set_integrity.py -v

# Dirty-set vs full-scan parity (slow — run explicitly)
pytest tests/perf/test_dirty_parity.py -v -m slow

# Authoritative apply path tests
pytest tests/integration/pipeline/test_authoritative_apply.py -v

# Architecture boundary guards
pytest tests/architecture/ -v

# All of the above, excluding the slow parity test
pytest tests/perf/test_dirty_set_integrity.py tests/integration/pipeline/test_authoritative_apply.py tests/architecture/ -v -m "not slow"
```

---

## Validation: Frontmatter for New Docs

Both new docs require the following frontmatter block (first element in the file):

```yaml
---
status: active
layer: core
authority: P1
audience: agent
last_verified: 2026-06-13
---
```

Validate frontmatter after creation:

```bash
python3 -c "
import yaml, pathlib

for doc in ['docs/core/dirty_state_and_dependency.md', 'docs/core/update_intents.md']:
    text = pathlib.Path(doc).read_text()
    # Extract frontmatter block
    if not text.startswith('---'):
        print(f'FAIL {doc}: no frontmatter')
        continue
    end = text.index('---', 3)
    fm = yaml.safe_load(text[3:end])
    required = {'status', 'layer', 'authority', 'audience', 'last_verified'}
    missing = required - fm.keys()
    if missing:
        print(f'FAIL {doc}: missing keys {missing}')
    else:
        print(f'OK   {doc}')
"
```

After both docs are written, run:

```bash
make knowledge-index-update
make docs-registry
```

These commands regenerate the agent context search index and `docs/REGISTRY.yaml`. They must complete without errors.
