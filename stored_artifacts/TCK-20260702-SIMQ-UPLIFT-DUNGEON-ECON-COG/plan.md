# Plan: TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG
# ECONOMY / COGNITION Zero-Activation in dungeon_crawl

**Date:** 2026-07-02
**Phase:** Planning (seq 3)
**Decision:** DA — Archetype-Intentional (documentation only)
**Tier:** standard

---

## Pre-condition Summary

Confirmed before writing this plan:

- `grade_anchors.json`: all 10 dungeon_crawl runs (seeds 42/123/456 × 200t/500t/1000t/2000t,
  seed42 has 200t) already encode ECONOMY=C and COGNITION=C. No anchor changes required.
- `eval_matrix_results.md` lines 91–99: stability analysis mentions COMBAT/PROGRESSION only;
  ECONOMY=C and COGNITION=C are **not** labeled archetype-intentional. This is the primary gap.
- `town_resource.yaml` entries TOWN-173, TOWN-178, TOWN-179, TOWN-180: `support_boundary: null`.
  No dungeon_crawl archetype-scope notes exist.
- `strategic_cognition.yaml` entry STRAT-242 (decision_divergence_detected): `support_boundary: null`.
  No dungeon_crawl archetype-scope notes exist.
- `event_type_coverage.md`: mentions dungeon_crawl in audit base context; no archetype-blocking
  annotation for ECONOMY/COGNITION. Minor note warranted.

---

## Scope Guards

These actions are **out of scope** for this plan and must not be performed:

- No changes to world spec files (`data/worlds/dungeon_crawl/`)
- No changes to engine code, scorer code, or simulation pipeline
- No calibration re-runs (`data/calibration/` is read-only for this ticket)
- No changes to `grade_anchors.json` (anchors already correct)
- No new parity ledger entries (only annotations to existing entries)
- No changes to other worlds (sandbox_world, urban_political, simq_routing_test)

---

## Ordered Steps

### Step 1 — Pre-condition verification (read-only, no file changes)

Run T-1, T-2, T-3 from `test_plan.md` to confirm baseline before writing documentation.

**T-1**: Confirm zero ECONOMY/COGNITION events across all dungeon_crawl calibration runs.

```bash
python3 -c "
import json
from pathlib import Path
from collections import defaultdict

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
print('PASS' if not failures else f'FAIL: {failures}')
"
```

Expected: `PASS`

**T-2**: Confirm `gold_sink_fired` is the only active ECONOMY event type globally.

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

Expected: only `gold_sink_fired` appears; no `resource_harvested`, `trade_executed`, etc.

**T-3**: Confirm dungeon_crawl resolved spec has no economic entities or service buildings.

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
print('PASS' if not bad_roles and not bad_buildings else f'FAIL — roles:{bad_roles} buildings:{bad_buildings}')
print(f'  entity roles: {entity_roles}')
print(f'  buildings: {building_types}')
"
```

Expected: `PASS`; entity roles = `{scout, raider, leader, predator_hunter, sentinel}`; buildings = `{mine_entrance}`.

**If any of T-1/T-2/T-3 fail, stop and reassess the DA decision before proceeding.**

---

### Step 2 — Update `docs/simulation_quality/eval_matrix_results.md`

**File:** `docs/simulation_quality/eval_matrix_results.md`
**Location:** After the stability analysis paragraph (currently ends at line 99, "dungeon_crawl remains the most deterministic world in the corpus.")

Append the following DA annotation block immediately after that paragraph, before the `---` separator:

```markdown
**Archetype decision — ECONOMY and COGNITION (DA: Archetype-Intentional):** dungeon_crawl
ECONOMY=C and COGNITION=C across all seeds and tick counts are **archetype-correct** and
require no remediation. Root causes confirmed in TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG:

- **ECONOMY=C**: The only active ECONOMY event path is `gold_sink_fired`, which fires when
  the entity population's Gini coefficient exceeds 0.7 (GoldSinkSystem, `src/economy/health_monitor.py:22`).
  dungeon_crawl entities (goblin scout/raider/archer/warlord, cave_spider, undead_sentinel, bandit scout)
  are pure combat/creature archetypes with no gold-accumulating economic agents, no service buildings,
  and no merchant NPCs. Gold distribution remains near-uniform through symmetric combat looting;
  Gini never approaches 0.7. The 3 resource nodes (iron_vein, crystal_outcrop, silver_vein) are world
  dressing — no entity has a harvesting behavioral profile.
- **COGNITION=C**: The only active COGNITION event path is `decision_divergence_detected`, which fires
  when a DANGER concern with urgency > 0.7 coexists with a *non-survival project* (harvesting,
  exploration, social, crafting). All dungeon_crawl entities are permanently in combat/survival mode;
  the non-survival project condition is never satisfied.

dungeon_crawl is designed as a **combat-arena archetype** activating COMBAT, WORLD, and PROGRESSION.
ECONOMY and COGNITION are structurally inapplicable to this archetype and are correctly graded C.
Anti-drift: if a merchant NPC, service building, or non-combat entity with a non-survival project
is ever added to dungeon_crawl, these grades must be reassessed and grade_anchors.json updated.
```

**Acceptance mapping:** AC item 1 ("add archetype-correct annotation to dungeon_crawl ECONOMY/COGNITION stability analysis").

---

### Step 3 — Update `docs/parity_ledger/town_resource.yaml`

**File:** `docs/parity_ledger/town_resource.yaml`
**Action:** Set `support_boundary` from `null` to a scope note on four entries.

No structural YAML changes — only replace `support_boundary: null` with a string value on the
identified entries. All entries already have the `support_boundary` key; it is safe to populate.

#### 3a — TOWN-173 (harvest / RESOURCE_DEPLETED event)

Line 1846: `support_boundary: null`

Replace with:
```yaml
  support_boundary: >
    Requires an entity with an active harvesting behavioral profile interacting with a resource node.
    Archetype-blocked in dungeon_crawl: all entities are combat/creature archetypes (goblin_*,
    cave_spider, undead_sentinel, bandit_scout) with no harvesting behavioral profile assigned.
    The 3 resource nodes in dungeon_crawl (iron_vein, crystal_outcrop, silver_vein) are present
    as world dressing but are never harvested; RESOURCE_DEPLETED calibration_hits=0 across all
    dungeon_crawl runs. (TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG, decision DA)
```

#### 3b — TOWN-178 (EconomyHealthMonitor.check_alerts, INFLATION_SPIRAL Gini>0.7)

Line 1930: `support_boundary: null`

Replace with:
```yaml
  support_boundary: >
    INFLATION_SPIRAL fires only when entity population Gini coefficient exceeds 0.7.
    Archetype-blocked in dungeon_crawl: symmetric combat looting across creature archetypes
    produces near-uniform gold distribution; Gini does not approach 0.7 even at 2000t.
    (TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG, decision DA)
```

#### 3c — TOWN-179 (GoldSinkSystem, REPAIR_FEE/SERVICE_FEE/TAX intents)

Line 1953: `support_boundary: null`

Replace with:
```yaml
  support_boundary: >
    Applies only when INFLATION_SPIRAL fires (Gini>0.7). Archetype-blocked in dungeon_crawl:
    no merchant NPC, no service buildings (only mine_entrance exists), no gold-accumulating
    economic agents. gold_sink_fired calibration_hits=0 across all dungeon_crawl runs at
    all tick counts and seeds. (TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG, decision DA)
```

#### 3d — TOWN-180 (gold sink conservation invariant)

Line 1976: `support_boundary: null`

Replace with:
```yaml
  support_boundary: >
    Conservation invariant applies only when gold sink intents are generated (Gini>0.7 trigger).
    Not exercised in dungeon_crawl calibration runs (archetype-blocked; see TOWN-179).
    (TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG, decision DA)
```

**Acceptance mapping:** AC item 2 (parity ledger scope notes for gold_sink entries in town_resource.yaml).

---

### Step 4 — Update `docs/parity_ledger/strategic_cognition.yaml`

**File:** `docs/parity_ledger/strategic_cognition.yaml`
**Action:** Set `support_boundary` on STRAT-242.

#### 4a — STRAT-242 (decision_divergence_detected)

Line 2750: `support_boundary: null`

Replace with:
```yaml
  support_boundary: >
    decision_divergence_detected fires only when DANGER concern urgency > 0.7 AND the entity
    is on a non-survival project (harvesting, exploration, social, crafting — per
    _NON_SURVIVAL_PROJECT_KINDS frozenset). Archetype-blocked in dungeon_crawl: all entities
    (goblin_*, cave_spider, undead_sentinel, bandit_scout) are permanently in combat/survival
    mode; non-survival project condition is never satisfied. decision_divergence_detected
    calibration_hits=0 across all dungeon_crawl runs at all tick counts and seeds.
    (TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG, decision DA)
```

**Acceptance mapping:** AC item 2 (parity ledger scope notes for decision_divergence entries in strategic_cognition.yaml).

---

### Step 5 — Update `docs/simulation_quality/event_type_coverage.md` (minor note)

**File:** `docs/simulation_quality/event_type_coverage.md`
**Action:** Locate the section covering `gold_sink_fired` (§1.1 or equivalent) and the section
covering `decision_divergence_detected`. Add a bracketed archetype note to the dungeon_crawl
calibration_hits=0 cells if they appear as table rows, or append a sub-note to the relevant
paragraph if the file uses prose format.

If the file already has a "calibration_hits=0 globally" note that covers both events, and
dungeon_crawl is already listed as part of the zero-hit corpus, **no change is required** — the
existing text is sufficient. Only add text if the zero-hit entry is not already cross-referenced
to dungeon_crawl's archetype-intentional status.

**Acceptance mapping:** AC item 4 (event_type_coverage.md notes about archetype-blocking) — conditional.

---

### Step 6 — Post-documentation verification

Run T-4 through T-7 from `test_plan.md`.

**T-4**: eval_matrix_results.md contains explicit DA annotation.
```bash
grep -n "archetype-correct\|archetype-intentional\|DA\|combat-only archetype\|combat arena" \
  docs/simulation_quality/eval_matrix_results.md | head -10
```
Expected: at least 1 match in the dungeon_crawl section.

**T-5**: All parity ledger YAML files parse without error.
```bash
python3 -c "
import yaml
from pathlib import Path
for f in sorted(Path('docs/parity_ledger').glob('*.yaml')):
    try:
        yaml.safe_load(f.read_text())
        print(f'PASS: {f.name}')
    except yaml.YAMLError as e:
        print(f'FAIL: {f.name}: {e}')
"
```
Expected: `PASS` for every file. **If any YAML parse error, fix before proceeding.**

**T-6**: `make evaluate --dry-run` exits 0.
```bash
make evaluate --dry-run
```
Expected: exit 0. No grade anchor changes are part of this ticket; if this fails with a
grade mismatch, investigate but do NOT change anchors without reassessing the DA decision.

**T-7**: dungeon_crawl COMBAT/WORLD/PROGRESSION score counts unchanged.
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
Expected: non-zero counts for COMBAT, WORLD, PROGRESSION in every run (documentation edits
must not touch calibration data).

---

## Files to Change

| Step | File | Change |
|---|---|---|
| 2 | `docs/simulation_quality/eval_matrix_results.md` | Add DA archetype-correct annotation block after stability analysis paragraph |
| 3a | `docs/parity_ledger/town_resource.yaml` | TOWN-173: set `support_boundary` (harvest profile requirement) |
| 3b | `docs/parity_ledger/town_resource.yaml` | TOWN-178: set `support_boundary` (Gini>0.7 archetype-block) |
| 3c | `docs/parity_ledger/town_resource.yaml` | TOWN-179: set `support_boundary` (gold_sink archetype-block) |
| 3d | `docs/parity_ledger/town_resource.yaml` | TOWN-180: set `support_boundary` (conservation invariant scope) |
| 4a | `docs/parity_ledger/strategic_cognition.yaml` | STRAT-242: set `support_boundary` (decision_divergence archetype-block) |
| 5 | `docs/simulation_quality/event_type_coverage.md` | Minor note if dungeon_crawl archetype-blocking not already cross-referenced |

**Not changed:** world spec, engine code, scorer code, calibration data, grade_anchors.json, any other parity ledger file.

---

## Acceptance Criteria Mapping

| AC Item | Step | Verification |
|---|---|---|
| dungeon_crawl world spec config documented | investigation.md (done) | — |
| sandbox_world gold_sink enabling config identified | investigation.md (done) | — |
| Archetype decision (DA) documented | Step 2 (eval_matrix), investigation.md (done) | T-4 |
| DA: eval_matrix_results.md updated with archetype-correct statement | Step 2 | T-4 |
| DA: grade_anchors.json confirms C already | Pre-condition (confirmed) | T-6 |
| Parity ledger scope notes (town_resource: gold_sink) | Steps 3b–3d | T-5 |
| Parity ledger scope notes (town_resource: harvest) | Step 3a | T-5 |
| Parity ledger scope notes (strategic_cognition: decision_divergence) | Step 4a | T-5 |
| `make evaluate --dry-run` exits 0 | Step 6 | T-6 |

---

## Execution Order

1. Run T-1, T-2, T-3 (Step 1) — all in parallel, read-only.
2. Apply Steps 2, 3, 4, 5 (documentation edits) — can be done in any order; all are file-isolated.
3. Run T-5 (YAML parse check) immediately after parity ledger edits.
4. Run T-4 after eval_matrix edit.
5. Run T-6 (evaluate --dry-run).
6. Run T-7 (regression guard).

Total expected files changed: 3–4 (eval_matrix_results.md, town_resource.yaml, strategic_cognition.yaml,
optionally event_type_coverage.md).
