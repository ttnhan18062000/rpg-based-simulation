---
ticket_id: TCK-20260623-DEAD-CODE-REMOVAL
phase: plan
date: 2026-06-23
revision: 3
status: READY — all decisions made, no unresolved questions
---

# Plan: D11 Audit Correction (TCK-20260623-DEAD-CODE-REMOVAL)

## Executive Summary

This is a **doc-only** ticket. Investigation confirmed all 9 D11 "orphan" directories are
live code. No `src/` files will be deleted. The work is: correct three documentation files,
update seventeen parity ledger entries across three YAML files, rebuild the knowledge index,
and run doc-integrity tests.

UQ-1 was resolved (option a — close as INVALID). All decisions are made. No questions remain.

---

## Scope Guards — What NOT to Touch

- **Do NOT** delete or modify any file under `src/`
- **Do NOT** edit `GoalScorer`/`src/ai/goals/` references in `design_patterns.md` — those
  directories exist and are accurate
- **Do NOT** edit the region around line 2789 in `social_narrative.yaml` — there is a
  pre-existing YAML parse error there in an unrelated entry; touching that region risks
  corrupting the file
- **Do NOT** alter the YAML schema structure of any parity ledger file — only update field
  values (`status`, `divergence_note`) within existing entries
- **Do NOT** delete `docs/audits/D11_dead_code.md` — audit records are permanent; add a
  correction section instead

---

## Ordered Implementation Steps

### Step 1 — Update combat_movement.yaml (COMB-093 through COMB-099)

**File:** `docs/parity_ledger/combat_movement.yaml`

For each of the 7 entries with IDs COMB-093, COMB-094, COMB-095, COMB-096, COMB-097,
COMB-098, COMB-099:

- Change `status: verified` to `status: legacy_verified`
- Add (or replace) `divergence_note` with:
  ```
  Behavior implemented in live src/ai/score_modifiers.py and src/ai/life_stage.py
  (confirmed importers in src/systems/strategic_systems/intelligence.py — not a V1 orphan).
  test_path null because no dedicated unit tests exist for these score-modifier behaviors
  in the V2 test suite. Verified claim was prose-audit only (TCK-20260623-DEAD-CODE-REMOVAL).
  ```

All 7 entries currently have `test_path: null` and `v2_evidence` set to the Phase 1-11
checklist audit string. Leave `test_path` and `v2_evidence` unchanged.

### Step 2 — Update strategic_cognition.yaml (STRAT-166 through STRAT-174)

**File:** `docs/parity_ledger/strategic_cognition.yaml`

For each of the 9 entries with IDs STRAT-166, STRAT-167, STRAT-168, STRAT-169, STRAT-170,
STRAT-171, STRAT-172, STRAT-173, STRAT-174:

- Change `status: verified` to `status: legacy_verified`
- Add (or replace) `divergence_note` with:
  ```
  Covers trait-system behaviors (src/core/traits.py). src/ai/personality.py is live code
  imported by src/systems/strategic_systems/intelligence.py (not a V1 orphan). test_path
  null across all 9 entries; no dedicated V2 test_path exists for these trait-adjacent
  behaviors. Mapping to V2 trait tests is deferred. Verified claim was prose-audit only
  (TCK-20260623-DEAD-CODE-REMOVAL).
  ```

Leave `test_path` and `v2_evidence` unchanged.

### Step 3 — Update social_narrative.yaml (SOC-142)

**File:** `docs/parity_ledger/social_narrative.yaml`

SOC-142 is located near line 1502. Edit ONLY that entry's fields. Do not read or touch
the region around line 2789 (pre-existing parse error in an unrelated entry).

- Change `status: verified` to `status: legacy_verified`
- Add (or replace) `divergence_note` with:
  ```
  test_bravery_modifiers test function does not exist in tests/ (grep confirmed zero
  matches). Behavior lives in live src/ai/ code (not a V1 orphan). Verified claim was
  prose-audit only. No dedicated V2 test exists; mapping deferred
  (TCK-20260623-DEAD-CODE-REMOVAL).
  ```

Leave `test_path` and `v2_evidence` unchanged.

After editing, verify the entry is still valid by reading lines 1498–1515 to confirm
`status: legacy_verified` appears and the surrounding YAML structure is intact. Do NOT
run `yaml.safe_load` on the full file — it will fail on line 2789.

### Step 4 — Edit design_patterns.md (remove dead states.py references)

**File:** `docs/guidelines/design_patterns.md`

`src/ai/states.py` does not exist on disk. Remove all references:

1. **Line 77** — remove the step: `3. Add a \`StateHandler\` in \`ai/states.py\` for
   the new state.` (the surrounding numbered list steps before and after it stay; renumber
   if needed to keep the list contiguous).

2. **Section 5 entirely** (approximately lines 203–228) — remove from the `## 5. AI State
   Machine — Strategy Pattern` heading through its closing `---` separator. This section
   references only `src/ai/states.py` which does not exist.

3. **Pattern Summary table row** (approximately line 236) — remove the row:
   `| **Strategy** (State Handlers) | \`ai/states.py\` | ...`

4. **File Map entries** (approximately lines 327–328) — remove:
   - `│   ├── brain.py              # AIBrain ...` (`brain.py` does not exist)
   - `│   ├── goal_evaluator.py     # Backward-compat shim` (does not exist)
   Keep the `ai/goals/` entries immediately below — those paths exist and are live.

**Do NOT touch** Section 1 (`GoalScorer` plugin pattern) or any other section referencing
`src/ai/goals/` — those directories and files exist and are live.

After editing, verify with:
```bash
grep -n "states\.py\|StateHandler\|STATE_HANDLERS\|brain\.py\|goal_evaluator\.py" \
    docs/guidelines/design_patterns.md
# Expected: zero output

grep -c "GoalScorer" docs/guidelines/design_patterns.md
# Expected: non-zero (Section 1 preserved)
```

### Step 5 — Add Post-Audit Correction to D11 audit doc

**File:** `docs/audits/D11_dead_code.md`

Append a new section at the end of the file (after all existing content):

```markdown
---

## Post-Audit Correction (2026-06-23)

**Status correction:** `corrected` (was: `done`)

**Claim being corrected:** The audit's "zero importer" characterization is incorrect
for all 9 directories examined. Every directory has live production or test importers.
No `src/` deletions are safe without a prior migration epic.

**Evidence per directory (confirmed importers):**

| Directory | Confirmed Importers | Safe to Delete? |
|---|---|---|
| `src/ai/` | `src/systems/strategic_systems/intelligence.py` (live AI loop), `src/systems/social_systems/party.py` | NO |
| `src/quests/` | `src/engine/apply.py` top-level import (authoritative mutation path), `engine/quests.py`, `engine/patches.py` | NO |
| `src/progression/` | `src/engine/apply.py` top-level imports `LevelingService`, `VeterancyService`; `engine/evolution.py`, `engine/rpg_depth.py`, `engine/patches.py` | NO |
| `src/entities/` | `src/worldassembly/entity_spawner.py` top-level import; `engine/quests.py`, `engine/tactical.py` | NO |
| `src/content_semantics/` | 10+ live engine files (legality.py, combat_rewards.py, worldassembly/resolver.py, worldbuilding/compiler.py, world_dynamics.py, region_threat_classifier.py, influence.py, content/warmup.py, and others) | NO — active core infrastructure |
| `src/town/` | `src/world/providers/requirements.py` (lazy import); 8 test files | NO |
| `src/actions/` | 3 test files | NO — tests would break immediately |
| `src/runtime/` | 2 test files | NO — tests would break immediately |
| `src/views/readiness.py` | 1 test file | NO — tests would break immediately |

**Root cause of misclassification:** The D11 import scanner likely scanned only a
`tests_v2/` subtree that does not contain the active test suite, or failed to detect
lazy imports and top-level cross-package references. The active test suite lives under
`tests/unit/` and `tests/integration/`.

**Investigation reference:**
`stored_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/investigation.md`
```

### Step 6 — Update open_audit_findings_backlog.md Section 1E

**File:** `docs/plans/open_audit_findings_backlog.md`

Locate Section 1E (the D11 nine-directory deletion plan). Replace the deletion plan body
with:

```markdown
**INVALID — All directories confirmed live (2026-06-23)**

Investigation TCK-20260623-DEAD-CODE-REMOVAL proved every directory listed in the D11
audit has active production or test importers. No deletion is safe without a prior
migration epic. The "zero importer" claim in D11 was an artifact of the import scanner
not covering the active `tests/` tree and missing lazy/top-level cross-package imports.

See `stored_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/investigation.md` for
per-directory importer evidence.

If module restructuring is later desired, open a new migration epic with a confirmed
V2 landing zone for each directory before touching any callers.
```

Keep the Section 1E heading and any surrounding section structure intact. Only replace
the body of the deletion plan.

### Step 7 — Rebuild knowledge index

```bash
make knowledge-index-update
```

Run after all six doc/YAML edits above are complete. Required because files under
`docs/` were modified. Expected: exits 0, no errors.

### Step 8 — Run doc integrity tests

```bash
pytest tests/docs/ -x -q
```

Expected: zero failures. This verifies:
- All edited markdown files have valid frontmatter
- Parity ledger YAML files (as parsed by the test suite) remain consistent
- Registry entries are intact

If `social_narrative.yaml`'s pre-existing parse error at line 2789 causes a test
failure, note that the error was pre-existing (not introduced by this ticket) and
document it in the ticket's Completion Summary without blocking the ticket on it.

---

## Verification Checklist (run inline during implementation)

After Steps 1–3, spot-check parity ledger edits:

```python
# For combat_movement.yaml and strategic_cognition.yaml (both parse cleanly):
python3 -c "
import yaml, pathlib
files = {
    'combat_movement.yaml': ['COMB-0' + str(n) for n in range(93, 100)],
    'strategic_cognition.yaml': ['STRAT-' + str(n) for n in range(166, 175)],
}
for fname, ids in files.items():
    data = yaml.safe_load(pathlib.Path('docs/parity_ledger/' + fname).read_text())
    entries = data if isinstance(data, list) else data.get('entries', [])
    for e in entries:
        if e.get('id') in ids:
            ok = e.get('status') == 'legacy_verified' and e.get('divergence_note')
            print(f\"{e['id']}: {'OK' if ok else 'FAIL'}\")
"

# For social_narrative.yaml (pre-existing parse error — use line-range read):
python3 -c "
lines = open('docs/parity_ledger/social_narrative.yaml').readlines()
for i, l in enumerate(lines[1498:1515], start=1499):
    print(i, l, end='')
"
# Confirm 'status: legacy_verified' and 'divergence_note:' visible near line 1502
```

After Step 4:

```bash
grep -n "states\.py\|StateHandler\|STATE_HANDLERS\|brain\.py\|goal_evaluator\.py" \
    docs/guidelines/design_patterns.md
# Expected: zero lines

grep -c "GoalScorer" docs/guidelines/design_patterns.md
# Expected: non-zero
```

---

## Files to be Changed

| File | Change Type |
|---|---|
| `docs/parity_ledger/combat_movement.yaml` | Update 7 entries: status + divergence_note |
| `docs/parity_ledger/strategic_cognition.yaml` | Update 9 entries: status + divergence_note |
| `docs/parity_ledger/social_narrative.yaml` | Update 1 entry: status + divergence_note |
| `docs/guidelines/design_patterns.md` | Remove 4 dead-reference blocks |
| `docs/audits/D11_dead_code.md` | Append Post-Audit Correction section |
| `docs/plans/open_audit_findings_backlog.md` | Replace Section 1E body with INVALID notice |

No `src/` files. No new test files. No schema changes.

---

## Post-Implementation Finalization (after tests pass)

These steps are part of the finalize phase, not the implementation phase:

1. Move `tickets/inprogress/TCK-20260623-DEAD-CODE-REMOVAL.md` to `tickets/done/`
2. Move `staging_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/` to
   `stored_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/`
3. Append a row to `tickets/working_log.csv` (bottom of file, never after header)
4. Write run entry to `agent-monitoring/runs.jsonl`
5. Write at least one event entry to `agent-monitoring/events.jsonl`
6. Stage `agent-monitoring/tools.jsonl` in the commit
7. Commit with message prefix `TCK-20260623-DEAD-CODE-REMOVAL: ...`
8. Clean `data/runs/` and `reports/release_proof/` if any temp files were created
