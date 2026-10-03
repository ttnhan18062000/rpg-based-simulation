# Test Plan: TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG
# ECONOMY / COGNITION Zero-Activation in dungeon_crawl

**Date:** 2026-07-02
**Decision:** DA — Archetype-Intentional (no world spec changes)
**Tier:** standard

---

## Test Scope

This is a DA (documentation-only) resolution. No implementation changes to engine, scorers, or world spec are required. Testing verifies:

1. The existing calibration data correctly shows 0 ECONOMY and 0 COGNITION events in dungeon_crawl
2. The eval_matrix documentation update is consistent with calibration reality
3. No grade anchor changes are introduced (dungeon_crawl C grades are already correct)
4. `make evaluate --dry-run` continues to exit 0 after documentation updates
5. Parity ledger annotations do not introduce parse errors

---

## Phase 1 — Pre-existing Calibration Verification (no code change)

These checks confirm the root cause evidence before any documentation is written.

### T-1: Confirm zero ECONOMY/COGNITION across all dungeon_crawl runs

```bash
python3 -c "
import json
from pathlib import Path
from collections import Counter, defaultdict

root = Path('data/calibration')
failures = []
for key in sorted(root.iterdir()):
    if 'dungeon_crawl' not in key.name:
        continue
    qs = key / 'quality_scores.jsonl'
    if not qs.exists():
        continue
    pillars = defaultdict(int)
    for line in qs.read_text().splitlines():
        row = json.loads(line)
        p = row.get('pillar')
        if p in ('ECONOMY', 'COGNITION'):
            pillars[p] += 1
    if pillars.get('ECONOMY', 0) > 0 or pillars.get('COGNITION', 0) > 0:
        failures.append(f'{key.name}: ECONOMY={pillars.get(\"ECONOMY\",0)} COGNITION={pillars.get(\"COGNITION\",0)}')
if failures:
    print('FAIL — unexpected events:', failures)
else:
    print('PASS — all dungeon_crawl runs: ECONOMY=0, COGNITION=0')
"
```

**Expected:** `PASS — all dungeon_crawl runs: ECONOMY=0, COGNITION=0`

**Coverage:** Covers all 10 dungeon_crawl calibration runs (seeds 42/123/456 × 200t/500t/1000t/2000t, minus 200t which only exists for seed42).

### T-2: Confirm gold_sink_fired is the only active ECONOMY path

```bash
python3 -c "
import json
from pathlib import Path
from collections import Counter

for world in ['sandbox_world_seed42_1000t', 'urban_political_seed42_1000t']:
    qs = Path(f'data/calibration/{world}/quality_scores.jsonl')
    c = Counter()
    for line in qs.read_text().splitlines():
        row = json.loads(line)
        if row.get('pillar') == 'ECONOMY':
            c[row.get('event_type','?')] += 1
    print(f'{world}: {dict(c)}')
"
```

**Expected:** Only `gold_sink_fired` appears (no `resource_harvested`, `trade_executed`, etc.).

### T-3: Confirm dungeon_crawl world spec has no economic entities or service buildings

```bash
python3 -c "
import yaml
from pathlib import Path
spec = yaml.safe_load(Path('data/worlds/dungeon_crawl/resolved/world.resolved.yaml').read_text())
economic_roles = {'merchant', 'trader', 'worker', 'blacksmith', 'innkeeper', 'shopkeeper'}
economic_buildings = {'shop', 'blacksmith', 'inn', 'town_hall', 'healer_hut', 'market', 'tavern'}

entity_roles = {e.get('role') for e in spec.get('entities', [])}
building_types = {b.get('type') for b in spec.get('buildings', [])}

bad_roles = entity_roles & economic_roles
bad_buildings = building_types & economic_buildings

if bad_roles or bad_buildings:
    print(f'FAIL — economic roles: {bad_roles}, economic buildings: {bad_buildings}')
else:
    print(f'PASS — no economic entities or service buildings')
    print(f'  entity roles: {entity_roles}')
    print(f'  buildings: {building_types}')
"
```

**Expected:** `PASS — no economic entities or service buildings`; entity roles = `{scout, raider, leader, predator_hunter, sentinel}`; buildings = `{mine_entrance}`.

---

## Phase 2 — Documentation Update Verification

After `docs/simulation_quality/eval_matrix_results.md` is updated with the DA annotation:

### T-4: eval_matrix_results.md contains explicit DA annotation

```bash
grep -n "archetype-correct\|archetype-intentional\|DA\|combat-only archetype\|combat arena" \
  docs/simulation_quality/eval_matrix_results.md | head -10
```

**Expected:** At least 1 match in the dungeon_crawl section confirming the DA decision is documented.

### T-5: Parity ledger YAML files parse without error after annotations

```bash
python3 -c "
import yaml
from pathlib import Path
for f in Path('docs/parity_ledger').glob('*.yaml'):
    try:
        yaml.safe_load(f.read_text())
        print(f'PASS: {f.name}')
    except yaml.YAMLError as e:
        print(f'FAIL: {f.name}: {e}')
"
```

**Expected:** `PASS` for every `.yaml` file in `docs/parity_ledger/`.

---

## Phase 3 — Evaluate Harness Verification

### T-6: `make evaluate --dry-run` exits 0

```bash
make evaluate --dry-run
```

**Expected:** Exit code 0. This confirms no grade anchor changes are needed (dungeon_crawl C grades are already encoded correctly).

**Note:** If this fails with a `grade_anchors.json` mismatch, check whether the anchor file already reflects C for dungeon_crawl ECONOMY/COGNITION. It should; no anchor changes are part of this ticket.

---

## Phase 4 — Regression Guard

### T-7: Existing dungeon_crawl COMBAT/WORLD/PROGRESSION grades unaffected

```bash
python3 -c "
import json
from pathlib import Path
from collections import defaultdict

root = Path('data/calibration')
for key in sorted(root.iterdir()):
    if 'dungeon_crawl' not in key.name:
        continue
    qs = key / 'quality_scores.jsonl'
    if not qs.exists():
        continue
    pillars = defaultdict(int)
    for line in qs.read_text().splitlines():
        row = json.loads(line)
        p = row.get('pillar')
        if p in ('COMBAT', 'WORLD', 'PROGRESSION'):
            pillars[p] += 1
    print(f'{key.name}: COMBAT={pillars[\"COMBAT\"]} WORLD={pillars[\"WORLD\"]} PROGRESSION={pillars[\"PROGRESSION\"]}')
"
```

**Expected:** Non-zero counts for COMBAT, WORLD, PROGRESSION in every run (same as pre-investigation baseline). This verifies no score record corruption occurred from documentation edits.

---

## What Is NOT Tested

- Calibration re-run for dungeon_crawl: Not needed — DA decision means existing calibration data is authoritative
- World spec changes: Not applicable — DA decision means no world spec edits
- New engine code paths: Not applicable — no engine changes
- Adding economic entities and verifying gold_sink_fired: This is the DB path which is not taken; documented in investigation.md §"If DB Were Chosen" for future reference if the archetype decision is revisited

---

## Test Execution Order

1. T-1, T-2, T-3 (in parallel — all read-only, no dependencies)
2. Apply documentation changes to `docs/simulation_quality/eval_matrix_results.md` and parity ledger
3. T-4, T-5 (after documentation edits)
4. T-6 (after T-5 confirms no YAML parse errors)
5. T-7 (final regression check, independent of documentation)

---

## Pass Criteria for Ticket Closure

- [ ] T-1: All dungeon_crawl runs confirm ECONOMY=0, COGNITION=0 events
- [ ] T-2: gold_sink_fired confirmed as sole active ECONOMY path globally
- [ ] T-3: dungeon_crawl world spec confirmed — no economic entities, no service buildings
- [ ] T-4: eval_matrix_results.md contains explicit DA archetype annotation
- [ ] T-5: All parity ledger YAML files parse without error
- [ ] T-6: `make evaluate --dry-run` exits 0
- [ ] T-7: COMBAT/WORLD/PROGRESSION score record counts unchanged from baseline
