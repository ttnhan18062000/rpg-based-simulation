---
status: historical
layer: artifact
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-LIVE
artifact_type: plan
---

# Plan — TCK-20260606-DOCSITE-FM-LIVE

## Overview

Write `tools/add_frontmatter_live.py` to inject YAML frontmatter into all 247 in-scope
markdown files under `docs/`. The script classifies each file using a directory-keyed map
plus per-directory heuristics for engine, combat, observability, performance, and
test_coverage. It is idempotent and follows the pattern of `tools/add_frontmatter_archive.py`.

Total scope: 247 files (244 across 14 subdirectories + 3 loose at docs/ root).

---

## Implementation Steps

### Step 1 — Verify prerequisites

Confirm `tools/validate_frontmatter.py` exists and that all LAYER_VALUES used in this
ticket's classification map are present in its enum constants:
`mechanics, engine, core, architecture, systems, combat, observability, performance,
strategy, compliance, testing, ai, guidelines, misc`

Run: `grep -A 30 "LAYER_VALUES" tools/validate_frontmatter.py`

If any value is missing, stop and resolve before proceeding (schema ticket dependency).

### Step 2 — Write tools/add_frontmatter_live.py

Structure (following archive script pattern):

**Constants and classification map:**

```python
# Uniform directories — all files get same values
UNIFORM_MAP = {
    "docs/mechanics":    dict(status="authoritative", authority="P0", layer="mechanics", last_verified="2026-06-06"),
    "docs/core":         dict(status="authoritative", authority="P0", layer="core",      last_verified="2026-06-06"),
    "docs/architecture": dict(status="active",        authority="P1", layer="architecture"),
    "docs/systems":      dict(status="active",        authority="P1", layer="systems"),
    "docs/strategy":     dict(status="active",        authority="P1", layer="strategy"),
    "docs/compliance":   dict(status="active",        authority="P1", layer="compliance"),
    "docs/ai":           dict(status="active",        authority="P1", layer="ai"),
    "docs/guidelines":   dict(status="active",        authority="P1", layer="guidelines"),
    "docs/testing":      dict(status="active",        authority="P1", layer="testing"),
}

# Heuristic directories — classify per filename
HEURISTIC_DIRS = {"docs/engine", "docs/combat", "docs/observability",
                  "docs/performance", "docs/test_coverage"}

# Loose docs/ root files
LOOSE_FILES = {
    "docs/README.md":                       dict(status="active", authority="P1", layer="misc"),
    "docs/logic_checklist_exhaustive.md":   dict(status="active", authority="P1", layer="guidelines"),
    "docs/optimization_audit_ledger.md":    dict(status="active", authority="P1", layer="performance"),
}
```

**Historical heuristic regex (engine):**

```python
ENGINE_HISTORICAL_PAT = re.compile(
    r'(phase\d|phase_|attach_gate|m[0-9a-f]+_|m[0-9a-f]+-|_matrix'
    r'|backlog|closure|entry_package|exit_package|proof_bundle|readiness'
    r'|ratification|baseline|review|freeze|gap_report|inventory|scope_audit'
    r'|pipeline_scope|support_boundary|non_preserved|preserved|cutover'
    r'|legacy|replacement|unsupported|remaining|sweep|src_v2|differential'
    r'|progression_recovery|truth_package|resource_intelligence|town_resolution)',
    re.IGNORECASE
)
```

**classify(path) function:**
Returns `dict(status, authority, layer, audience="developer", last_verified=None)`.

Logic:
1. Check LOOSE_FILES by path string → return mapped values
2. Find matching key in UNIFORM_MAP by checking `str(path).startswith(key)` → return mapped values
3. For HEURISTIC_DIRS:
   - `docs/engine/`: ENGINE_HISTORICAL_PAT match → historical P2, else active P1; layer=engine
   - `docs/combat/`: filename contains 'm7' or 'overhaul_spec' → active P1, else historical P2; layer=combat
   - `docs/observability/`: filename matches `phase_?\d` → historical P2, else active P1; layer=observability
   - `docs/performance/`: filename starts with date pattern or contains 'report' → historical P2;
     else active P1; layer=performance
   - `docs/test_coverage/`: all → historical P2; layer=testing

**build_frontmatter(classification) function:**
Builds YAML block. Includes `last_verified` only when `status == "authoritative"`.
Audience is always `developer`. No `tags` field (optional per schema).

```
---
status: {status}
layer: {layer}
authority: {authority}
audience: developer
[last_verified: {last_verified}]  # only if authoritative
---
```

**process_file(path) function:**
- Read content
- If `content.startswith("---")`: return "skipped"
- Build frontmatter, prepend with blank line separator, write back
- Return "modified"

**main() function:**
Walk targets in order:
1. Each UNIFORM_MAP dir via `Path(key).rglob("*.md")` if dir exists
2. Each HEURISTIC_DIRS dir via `Path(dir).rglob("*.md")` if dir exists
   - For observability: skip files in `baselines/` subdir
3. LOOSE_FILES: process each individually if exists

Print summary: `N files modified, M files skipped (already had frontmatter)`.

### Step 3 — Dry-run validation (manual)

Before writing any files, add a `--dry-run` flag that prints the classification for each
file without modifying disk. Run it and spot-check:
- 5 engine files (mix of active/historical edge cases)
- All mechanics files
- m7 combat files
- Loose docs/ files

Fix any misclassification in the heuristic before proceeding.

### Step 4 — Execute the script

```bash
python3 tools/add_frontmatter_live.py
```

Expect output: ~247 modified, 0 skipped.

### Step 5 — Run validator on all modified dirs

```bash
for dir in docs/mechanics docs/core docs/architecture docs/systems docs/combat \
           docs/observability docs/performance docs/strategy docs/compliance \
           docs/testing docs/test_coverage docs/ai docs/guidelines docs/engine; do
    python3 tools/validate_frontmatter.py $dir
done
python3 tools/validate_frontmatter.py docs/README.md docs/logic_checklist_exhaustive.md docs/optimization_audit_ledger.md
```

All must exit 0 with zero violations. Fix any failures before continuing.

### Step 6 — Idempotency check

Run the script a second time. Confirm output: `0 files modified, 247 files skipped`.

### Step 7 — Update docs/README.md

Add a sentence to the README noting that all docs/ markdown files carry YAML frontmatter
and are browsable via Docusaurus. Re-run validator on docs/README.md.

### Step 8 — Finalize ticket

- Update ticket `## Implementation Notes`, `## Test Summary`, `## Files Changed`,
  `## Completion Summary`
- Set `## Status` to `DONE`
- Move ticket: `tickets/inprogress/` → `tickets/done/`
- Move staging artifacts: `staging_artifacts/TCK-20260606-DOCSITE-FM-LIVE/` → `stored_artifacts/`
- Append to `tickets/working_log.csv`
- Write agent-monitoring run entry and at least one event entry
- Clean `data/runs/` and `reports/release_proof/` if populated

---

## File Inventory

**New files:**
- `tools/add_frontmatter_live.py`

**Modified files:**
- All ~247 `.md` files in scope (prepended frontmatter only)
- `docs/README.md` (content update per AC-8)

**Not modified:**
- `docs/archive/` (Ticket 5)
- `docs/superpowers/`, `docs/specs/` (Ticket 5)
- `docs/parity_ledger/*.yaml` (YAML, not markdown)
- `docs/scenarios/*.yaml` (YAML)
- `docs/engine/manifest.json` (JSON)
- `docs/observability/baselines/` (JSON baselines)

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Engine heuristic mis-classifies edge-case files | Step 3 dry-run with manual spot-check before writing |
| Validator rejects a layer value | Step 1 pre-flight check against validate_frontmatter.py constants |
| File count diverges from plan | Script prints exact count; investigate before committing |
| docs/archive/ already has frontmatter from Ticket 3 | Script never targets archive/ — confirmed out of scope |
