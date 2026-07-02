---
ticket_id: TCK-20260623-DEAD-CODE-REMOVAL
phase: test_plan
date: 2026-06-23
revision: 2
---

# Test Plan: D11 Audit Correction (TCK-20260623-DEAD-CODE-REMOVAL)

## Scope Note

This ticket makes **doc-only changes**: parity ledger YAML updates, markdown doc
edits, and knowledge index rebuild. No `src/` files are modified or deleted.
No behavior changes occur. The test surface is therefore minimal.

---

## Required Tests

### 1. Doc Frontmatter Integrity

```bash
pytest tests/docs/ -x -q
```

Run after all doc and parity ledger edits are complete. This verifies:
- All edited markdown files have valid frontmatter
- YAML parity ledger files remain parseable (catches accidental syntax corruption)
- Registry entries are consistent

Expected: zero failures.

### 2. Knowledge Index Rebuild

```bash
make knowledge-index-update
```

Run after all doc changes are committed. This is not a test but a required
post-edit step to keep the agent context search index current.

Expected: exits 0, no errors.

---

## What Does NOT Need to Be Tested

- No `src/` tests are needed (no source code changed)
- No import chain checks needed (no files deleted)
- No engine startup checks needed
- No scoped `pytest tests/unit/` or `pytest tests/integration/` runs needed
- The full suite (`pytest -m "not slow"`) is not required for a doc-only change

---

## Parity Ledger Edit Verification

After updating the three YAML files, confirm the edits took effect:

```bash
python3 -c "
import yaml, pathlib
files = {
    'combat_movement.yaml': [f'COMB-0{n}' for n in range(93, 100)],
    'strategic_cognition.yaml': [f'STRAT-{n}' for n in range(166, 175)],
    'social_narrative.yaml': ['SOC-142'],
}
for fname, ids in files.items():
    path = pathlib.Path('docs/parity_ledger') / fname
    data = yaml.safe_load(path.read_text())
    entries = data if isinstance(data, list) else data.get('entries', [])
    for e in entries:
        if e.get('id') in ids:
            status = e.get('status')
            note = e.get('divergence_note')
            ok = status == 'legacy_verified' and note
            print(f\"{e['id']}: {'OK' if ok else 'FAIL'} status={status} note={'present' if note else 'MISSING'}\")
"
```

Expected: all entries print `OK`.

Note: `social_narrative.yaml` has a pre-existing YAML parse error at line 2789
(unrelated entry). If the above script fails on that file, use a line-range read
to verify SOC-142 directly:

```bash
python3 -c "
import pathlib
lines = pathlib.Path('docs/parity_ledger/social_narrative.yaml').read_text().splitlines()
# SOC-142 is near line 1502; print surrounding 10 lines
for i, l in enumerate(lines[1500:1515], start=1501):
    print(i, l)
"
```

Confirm `status: legacy_verified` and `divergence_note:` is non-null.

---

## design_patterns.md Verification

After removing Section 5 and the dead `states.py` references:

```bash
grep -n "states\.py\|StateHandler\|STATE_HANDLERS\|brain\.py\|goal_evaluator\.py" \
    docs/guidelines/design_patterns.md
```

Expected: zero output (all dead references removed).

Confirm Section 1 (`GoalScorer` plugin pattern) is still present:

```bash
grep -c "GoalScorer" docs/guidelines/design_patterns.md
```

Expected: non-zero (Section 1 content preserved).
