# Test Plan — TCK-20260613-DOC-MECHANICS-SUBCONTRACTS

**Date:** 2026-06-13
**Tier:** standard (documentation ticket — verification is doc correctness, not code behavior)

---

## Scope

This is a documentation-only ticket. The test plan covers:
1. Frontmatter validation for each new doc file
2. Knowledge index verification after doc creation
3. Regression surface — existing mechanics tests that must remain green after the four docs are created (docs reference these tests; they must pass)

---

## Tests to Run

### 1. Frontmatter validation

For each of the four new files, verify frontmatter is present and correctly formed:

```bash
python3 -c "
import yaml, pathlib
files = [
    'docs/mechanics/resource_conservation_contract.md',
    'docs/mechanics/adventure_routing_contract.md',
    'docs/mechanics/damage_formula_contract.md',
    'docs/mechanics/attribute_progression_contract.md',
]
for f in files:
    content = pathlib.Path(f).read_text()
    if not content.startswith('---'):
        raise AssertionError(f'{f}: missing frontmatter')
    fm_end = content.index('---', 3)
    fm = yaml.safe_load(content[3:fm_end])
    required = ['status', 'layer', 'authority', 'audience', 'last_verified']
    for key in required:
        assert key in fm, f'{f}: missing frontmatter key: {key}'
    assert fm['status'] == 'authoritative', f'{f}: status must be authoritative'
    assert fm['layer'] == 'mechanics', f'{f}: layer must be mechanics'
    assert fm['authority'] == 'P1', f'{f}: authority must be P1'
    assert fm['last_verified'] == '2026-06-13', f'{f}: last_verified must be 2026-06-13'
    print(f'OK: {f}')
"
```

### 2. README index verification

Confirm `docs/mechanics/README.md` lists all four new sub-contract files:

```bash
python3 -c "
import pathlib
readme = pathlib.Path('docs/mechanics/README.md').read_text()
contracts = [
    'resource_conservation_contract.md',
    'adventure_routing_contract.md',
    'damage_formula_contract.md',
    'attribute_progression_contract.md',
]
for c in contracts:
    assert c in readme, f'README missing reference to {c}'
    print(f'OK: {c} in README')
"
```

### 3. Knowledge index update

Run after all four docs are created:

```bash
make knowledge-index-update
```

Expected: exits 0. Any error here indicates a doc syntax problem.

### 4. Docs registry update

```bash
make docs-registry
```

Expected: `docs/REGISTRY.yaml` updated without error; new entries appear for the four contract files.

---

## Regression Surface — Existing Tests That Must Pass

These tests verify the mechanics that the four sub-contracts document. They must remain green; no source code changes are made in this ticket.

### Resource Conservation

```bash
pytest tests/integration/kernel/test_resource_conservation.py -v
pytest tests/integration/kernel/test_resource_conservation_v2.py -v
pytest tests/unit/resource/test_resource_conservation_regression.py -v
```

Key parity entries covered: TOWN-011, TOWN-012, TOWN-106 through TOWN-120, TOWN-132, TOWN-141 through TOWN-146 (see `docs/parity_ledger/town_resource.yaml`)

### Combat / Damage Formula

```bash
pytest tests/unit/combat/test_combat_matrix.py -v
pytest tests/unit/combat/test_combat_legality_contract.py -v
pytest tests/unit/combat/test_combat_legality_regression.py -v
pytest tests/unit/combat/test_combat_rewards.py -v
pytest tests/unit/combat/test_combat_reward_trace.py -v
pytest tests/integration/pipeline/test_combat_legality_matrix.py -v
```

Key parity entries covered: COMB-021 through COMB-024 (tactical modifiers), COMB-055, COMB-071 through COMB-074 (wounds/stamina), COMB-200 (damage formula parity)

### Attribute Progression / Leveling

```bash
pytest tests/unit/progression/test_leveling.py -v
pytest tests/unit/progression/test_leveling_veterancy.py -v
```

Key parity entries covered: PROG-065 (level thresholds deterministic), PROG-066 (AP grant deterministic), PROG-051 (stat recalculation), PROG-017 through PROG-019 (skill scaling)

### Scoped combined run (all above, excluding slow tests)

```bash
pytest tests/unit/combat/ tests/unit/resource/ tests/unit/progression/ tests/integration/kernel/test_resource_conservation.py tests/integration/kernel/test_resource_conservation_v2.py -m "not slow" -v
```

---

## Acceptance Checks (Non-Automated)

After creating all four docs, verify by inspection:

- [ ] Each doc contains a `## Regression tests` section with at least one concrete test file or group reference
- [ ] Each doc contains an `## Extension rules` section
- [ ] Each doc's formula section matches the source code formulas documented in `investigation.md`
- [ ] The wound threshold divergence (0.25 vs 0.40) is explicitly called out in `damage_formula_contract.md` with a note citing the source as authoritative and flagging the parity ledger entry for update
- [ ] `docs/mechanics/README.md` now lists the four new files under a clear "Sub-contracts" heading

---

## What NOT to Run

- Do NOT run `pytest tests/` (full suite) — scoped runs only per the testing rule
- Do NOT run `pytest tests/docs/` unless that directory exists (it does not currently)
- Do NOT run engine integration suites (`pytest tests/integration/`) in full — too broad for a docs-only change
