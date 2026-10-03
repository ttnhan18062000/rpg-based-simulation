---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-ARCHIVE
artifact_type: investigation
tags: [docsite, fm, archive]
---

PHASE_TS: 2026-06-11T02:01:52Z

# Investigation — TCK-20260606-DOCSITE-FM-ARCHIVE

## Target Directories and File Counts

| Directory | MD files | Non-MD files | Notes |
|---|---|---|---|
| `docs/archive/` | 235 | 2 (`.txt`) | Contains 7 subdirectories: `entity-enhance/`, `world/`, `issues/`, `workflow/`, `resource_v2/`, `profiling_performance/`, `sim-obs-test/`; script must recurse |
| `docs/superpowers/specs/` | 33 | 0 | All files have date prefix `YYYY-MM-DD-` |
| `docs/specs/` | 4 | 0 | All files have date prefix `YYYY-MM-DD-` |
| **Total** | **272** | **2** | Non-MD files (`proposal_v1.txt`, `proposal_v2.txt`) are silently skipped — `rglob("*.md")` handles this automatically |

**Frontmatter pre-existing:** 0 of 272 files. All 272 are bare markdown with no `---` block at position 0.

---

## Filename Pattern Analysis

### Date prefix patterns

| Pattern | Count | Source dirs |
|---|---|---|
| `YYYY-MM-DD-` prefix | 37 | `docs/superpowers/specs/` (33), `docs/specs/` (4) |
| No date in filename | 235 | All of `docs/archive/` |

Files in `docs/archive/` have no embedded date. For these, `original_date` must fall back to a sentinel value. The ticket acceptance criteria state the date is sourced from a filename regex `\d{4}-\d{2}-\d{2}`; when absent the script should use `unknown` or a configurable fallback (e.g., `2026-01-01`). The safest approach is to emit `original_date: unknown` and log a warning — this makes intent visible and allows a future audit pass.

### Keyword stem patterns (docs/archive/ root-level)

| Stem prefix | Example files |
|---|---|
| `combat_movement_*` | `combat_movement_finalized.md`, `combat_movement_implementation_milestone_1..7.md` |
| `intel_capacity_*` | `intel_capacity_implementation_milestone_1..8.md` |
| `resource_*` | 80+ files: `resource_handbook.md`, `resource_phase4..12_*`, `resource_v2_*` |
| `strategy_implementation_*` | `strategy_implementation_milestone_1..7.md` |
| `thinking_*` | `thinking_high_level_implementation.md`, `thinking_implementation_phase_1..6.md` |
| `entity_enhance_*` | `entity_enhance_phase1..11.md` (in `entity-enhance/` subdir) |
| `world_*` | `world_phase_20_28.md`, `world_phases_0_10_updated.md` etc. (in `world/` subdir) |
| `obs_sim_*`, `observability_*` | `obs_sim_phase1..10.md`, `observability_memory_issue.md` |
| `perf_*`, `performance_*`, `optimization_*`, `profiling_*` | 33 files in `profiling_performance/` subdir + root |
| `phase_N_*`, `phase9_*` | `phase_0_ds_implementation_plan.md`, `phase9_walkthrough.md` — no clear domain |
| `pitch.md`, `poposal.md`, `questions.md`, `visual_proposal.md` | free-form, domain unknown |

---

## Layer Inference Keyword Map

Ordered by precedence (first match wins, case-insensitive on stem):

| Keywords in stem | Inferred layer | Estimated file count |
|---|---|---|
| `combat`, `movement` | `combat` | 11 |
| `resource`, `economy`, `crafting` | `economy` | 100 |
| `strategy`, `cognition`, `intel`, `thinking` | `strategy` | 29 |
| `world`, `region`, `ecology` | `world` | 12 |
| `entity`, `aspect` | `core` | 15 |
| `obs_sim`, `observability`, `profiling` | `observability` | 14 |
| `perf`, `performance`, `optimization` | `performance` | 33 |
| _(no match)_ | `misc` (fallback) | **58** |

### Misc files (58) — cannot be auto-classified

These fall back to `layer: misc`. Notable clusters:

- `phase_N_*` files (7): `phase_0_ds_implementation_plan.md` through `phase_4_ds_implementation_plan.md`, `phase9_*` — phase plans with no domain keyword
- `repair_implementation.md`, `another_repair_phase_20_28.md` — generic repair
- `overhaul_spec.md`, `pitch.md`, `poposal.md`, `questions.md`, `visual_proposal.md` — proposal/ideation
- `test_base_rework_plan.md`, `legacy_checklist.md`, `ticket_plan_structure.md` — meta/tooling
- `src_v2_overview.md`, `src_v2_principle.md` — architecture-adjacent but no `architecture` keyword used in ticket map
- `lab_phase12..14.md`, `sim_test_init_instruction_1..3.md` — simulation test scaffolding
- Many `docs/superpowers/specs/` designs without a layer keyword: `centralized-logging`, `codebase-restructure`, `grafana-metrics`, `event-bus`, `turbo-run`, `msgpack-ws-protocol`, `aoa-runtime`, `test-restructure`, `personality-relationships`, `phase0-alignment`, `continuity-and-consequence`, `STRAT-KNOWLEDGE-UNIFICATION` (note: `strat` substring would NOT match `strategy` unless lowercased and `strat` is added — see risk note below), `best-ready-skill`, `core-rulebook-hardening`, `isolation-boundary`, `oracle-framework`, `parity-ledger`, `test-taxonomy`, `attribute-points`, `rpg-core-migration`, `checklist-governance`, `hardening-determinism-v2`, `test-stabilization`, `mutationspec-schema`, `scenariospec-schema`, `trust-boundary-remediation`, `phase-3-pass-1-lived-structure`

**Special note on `STRAT-KNOWLEDGE-UNIFICATION`:** filename contains `strat` not `strategy`. If the keyword match uses `in` substring, it would match. If it uses exact word boundary or full token match, it will fall to `misc`. The script should use substring match (`keyword in stem.lower()`) to catch `strat`→`strategy`.

**Special note on `2026-04-16-strategic-repair-design.md`:** contains `strateg` — this matches `strategy` via substring and should resolve to `strategy` rather than `misc`. Current count analysis already includes this in the strategy bucket.

---

## Frontmatter Schema for Archive Files

Source: `docs/guidelines/frontmatter_schema.md`, `tools/validate_frontmatter.py:_validate_archive`.

### Required fields (all three are mandatory):

| Field | Type | Constraint |
|---|---|---|
| `status` | enum | Must be exactly `archive` — any other value is a hard error |
| `layer` | enum | Must be one of `LAYER_VALUES`; `misc` is explicitly acceptable |
| `original_date` | string | ISO 8601 date (`YYYY-MM-DD`); no format enforcement in validator but convention is ISO |

### Additional fields from ticket scope (not validated as required by schema, but specified in ticket):

| Field | Value | Notes |
|---|---|---|
| `authority` | `P2` | Not required by `_validate_archive` — safe to include as extra field; validator ignores extra keys |
| `audience` | `historical` | Same — not validated but specified in ticket's minimal frontmatter block |

The validator's `_validate_archive` only checks `status`, `layer`, and `original_date`. Extra fields (`authority`, `audience`) are silently ignored, so including them is safe and adds indexing metadata for Docusaurus without breaking validation.

### Minimal valid archive frontmatter block:

```yaml
---
status: archive
layer: combat
authority: P2
audience: historical
original_date: 2026-03-15
---
```

---

## Script Design: `tools/add_frontmatter_archive.py`

### Goals
- Prepend frontmatter to all `.md` files in the three target directories
- Idempotent: skip files that already start with `---`
- Infer `original_date` from `YYYY-MM-DD` pattern in filename; fall back to `unknown` with a warning
- Infer `layer` from keyword map; fall back to `misc`
- Report counts: processed, skipped (already has frontmatter), misc fallbacks

### Algorithm

```
for each dir in [docs/archive/, docs/superpowers/specs/, docs/specs/]:
    for each .md file (recursive):
        read file content
        if content starts with "---":
            skip (already has frontmatter)
            continue
        date = extract_date(filename) or "unknown"
        layer = infer_layer(filename.lower())
        fm_block = build_frontmatter(date, layer)
        write fm_block + "\n" + original_content
        log: prepended to {filepath}

report: N prepended, M skipped, K fell back to misc
```

### Idempotency guarantee
The check `content.lstrip().startswith("---")` is NOT sufficient — it would match a file whose first non-blank line is a heading separator. The correct check is `content.startswith("---")` (strict start-of-file), mirroring the validator's `_FM_PATTERN` which requires `^---`.

### Layer keyword matching
Use `any(kw in stem for kw in keywords)` where `stem = Path(filename).stem.lower()`. Apply rules in priority order (combat before economy before strategy etc.) to avoid false matches (e.g., `resource_phase9` should not match `strategy` even if a future keyword were added).

### Date extraction
```python
import re
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
m = DATE_RE.search(filename)
original_date = m.group(1) if m else "unknown"
```

### Subdirectory handling
`Path(dir).rglob("*.md")` covers all subdirs automatically. No explicit depth limit needed.

---

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| File already has frontmatter (future state after script run) | Low | `content.startswith("---")` guard makes script safe to re-run |
| Non-MD files (`proposal_v1.txt`, `proposal_v2.txt`) | None | `rglob("*.md")` naturally excludes them |
| Subdirectory `profiling_performance/` — some files have `optimization_implementation_milestone*.md` prefix matching both `optimization` and `performance` | Low | First-match wins; `performance` keyword applied before `misc`; result is consistent |
| `original_date: unknown` for 235 archive files with no date in filename | Medium | Not a validator error (validator checks presence not format); logged clearly; acceptable for historical docs |
| Encoding issues in old archive files | Low | Open with `encoding="utf-8", errors="replace"` and write with `encoding="utf-8"` |
| Content begins with BOM or CRLF | Low | Strip BOM on read; normalize line endings if needed |
| `STRAT-KNOWLEDGE-UNIFICATION` stem matching | Low | Substring `strat` in `strategy` keyword set catches it correctly |
| Script mutates files while validator is running | Not applicable | Script is a one-shot CLI tool, not concurrent |
