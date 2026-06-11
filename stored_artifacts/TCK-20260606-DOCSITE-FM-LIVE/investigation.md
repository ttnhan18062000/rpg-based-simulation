---
status: historical
layer: artifact
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-LIVE
artifact_type: investigation
---

# Investigation — TCK-20260606-DOCSITE-FM-LIVE

## Directory Survey and File Counts

Total .md files across all in-scope directories: **244**
Plus 3 loose files at `docs/` root = **247 files** to receive frontmatter.

| Directory | .md files | Notes |
|---|---|---|
| docs/engine/ | 140 | 43 active, 97 historical; 1 manifest.json (skipped) |
| docs/mechanics/ | 10 | All authoritative P0 |
| docs/systems/ | 11 | All active P1 |
| docs/test_coverage/ | 7 | All historical P2 |
| docs/testing/ | 6 | All active P1 |
| docs/architecture/ | 8 | All active P1 |
| docs/combat/ | 9 | 3 active P1 (m7), 6 historical P2 |
| docs/performance/ | 11 | 3 active P1, 8 historical P2 |
| docs/observability/ | 15 (md only) | 4 active P1, 11 historical P2; baselines/ dir = JSON (skipped) |
| docs/strategy/ | 9 | All active P1 |
| docs/core/ | 5 | All authoritative P0 |
| docs/guidelines/ | 5 | All active P1 |
| docs/compliance/ | 3 | All active P1 |
| docs/ai/ | 5 | All active P1 |
| **docs/ root (loose)** | 3 | README.md, logic_checklist_exhaustive.md, optimization_audit_ledger.md |

## Files Already With Frontmatter

Sample check across: mechanics/01_entity_anatomy.md, guidelines/frontmatter_schema.md,
architecture/adr-004-simulation-watchdog.md, systems/README.md,
combat/combat_movement_rulebook_m1.md.

**Result: zero files have frontmatter.** All files begin directly with `#` heading content.
The entire 247-file corpus needs frontmatter injection.

## Classification Map

### Uniform directories (all files get same values)

| Directory | status | authority | layer | audience | last_verified |
|---|---|---|---|---|---|
| docs/mechanics/ | authoritative | P0 | mechanics | developer | 2026-06-06 |
| docs/core/ | authoritative | P0 | core | developer | 2026-06-06 |
| docs/architecture/ | active | P1 | architecture | developer | — |
| docs/systems/ | active | P1 | systems | developer | — |
| docs/strategy/ | active | P1 | strategy | developer | — |
| docs/compliance/ | active | P1 | compliance | developer | — |
| docs/ai/ | active | P1 | ai | developer | — |
| docs/guidelines/ | active | P1 | guidelines | developer | — |
| docs/testing/ | active | P1 | testing | developer | — |

### Per-file heuristic directories

**docs/engine/** — 140 md files:
- ACTIVE (43): contract files, lawbooks, playbooks, verification docs — no phase/milestone/matrix pattern in name
- HISTORICAL (97): phase4–phase13 packages, mX_test_matrix, replacement ledger docs, sweep/inventory/baseline/audit files
- Pattern regex: `phase\d|phase_|attach_gate|m[0-9a-f]+_|m[0-9a-f]+-|_matrix|backlog|closure|entry_package|exit_package|proof_bundle|readiness|ratification|baseline|review|freeze|gap_report|inventory|scope_audit|pipeline_scope|support_boundary|non_preserved|preserved|cutover|legacy|replacement|unsupported|remaining|sweep|src_v2|differential|progression_recovery|truth_package|resource_intelligence|town_resolution`

**docs/combat/** — 9 files:
- ACTIVE (3): observability_rulebook_m7.md, rollout_hardening_rulebook_m7.md, combat_movement_overhaul_spec.md
- HISTORICAL (6): all m1/m4/m6 rulebooks, test matrices

**docs/observability/** — 15 md files (baselines/ subdir contains JSON only, skip):
- ACTIVE (4): hard_law_monitor.md, how_to_run_simulation.md, loki_label_policy.md, prometheus_metrics.md
- HISTORICAL (11): phase_1.md through phase_9_usage.md + phase_14_agentic_lab.md

**docs/performance/** — 11 files:
- ACTIVE (3): optimization_architecture.md, optimization_invariants.md, perf_baseline_policy.md
- HISTORICAL (8): all date-prefixed reports (2026-05-*) + performance-report-*.md

**docs/test_coverage/** — 7 files:
- HISTORICAL (7): all phase*_coverage.md files

**docs/ root loose files** — 3 files:
- docs/README.md → active, P1, layer=misc (index file)
- docs/logic_checklist_exhaustive.md → active, P1, layer=guidelines
- docs/optimization_audit_ledger.md → active, P1, layer=performance

## Engine Dir Heuristic

The classification regex catches all known historical patterns in the engine directory:
- Phase packages (phase4–phase13): entry, exit, closure, proof, readiness, support_boundary
- Milestone test matrices: m1_test_matrix through me_test_matrix
- Replacement/legacy ledger docs: legacy_replacement_ledger, remaining_replacement_scope, etc.
- Sweep, inventory, freeze docs: sweep_configuration, src_v2_inventory, etc.

Active contract files (kernel.md, authoritative_pipeline.md, governance_logic.md, etc.)
are correctly excluded from the historical pattern.

Edge cases confirmed correct by heuristic:
- `minimal_kernel_m2.md` → ACTIVE (no _matrix, no phase prefix — it's a spec doc)
- `simulation_kernel_contract_m1.md` → ACTIVE (contract file, m1 appears mid-name not as prefix)
- `runtime_completion_contract_ma.md` → HISTORICAL (ma_ prefix matches milestone pattern)
- `certification_contract_m9.md` → ACTIVE (no matrix/phase suffix — standalone cert doc)

## Script Design

Follows `tools/add_frontmatter_archive.py` pattern:

- Single script: `tools/add_frontmatter_live.py`
- Runs from repo root (uses relative paths)
- `has_frontmatter(content)`: checks `content.startswith("---")`
- `classify(path)`: returns `(status, authority, layer, last_verified_or_None)` using a
  classification map keyed on directory, with per-file regex override for engine/combat/
  observability/performance/test_coverage
- `build_frontmatter(...)`: renders the YAML block, conditionally includes `last_verified`
  only when `status == "authoritative"`
- `process_file(path)`: read → check frontmatter → classify → write prepended content
- `main()`: walks each target dir via `rglob("*.md")`, skips baselines/ under observability,
  prints modified/skipped summary
- Idempotent: files already starting with `---` are skipped unconditionally

## Risks

1. **Engine false-positives**: A few edge-case engine files (e.g. `runtime_completion_contract_ma.md`)
   are classified HISTORICAL by the `ma_` pattern even though they are named contracts. These should
   be reviewed before committing. The plan includes a dry-run diff step.

2. **observability/baselines/**: This subdirectory contains JSON files. The script must skip it
   explicitly (rglob will find .md only, but the dir contains no .md so no action needed — verify).

3. **docs/guidelines/frontmatter_schema.md**: Will receive frontmatter applied to itself.
   This is correct — the schema doc is itself a live guidelines doc.

4. **244 files is larger than ticket's ~150 estimate**: The engine dir alone is 140 files.
   The ticket scope estimate was approximate. Actual count is 247 files (244 in subdirs + 3 loose).

5. **validate_frontmatter.py must exist and be current**: Confirm validator accepts all
   LAYER_VALUES used (mechanics, engine, core, architecture, systems, combat, observability,
   performance, strategy, compliance, testing, ai, guidelines, misc). All confirmed present
   in schema enum reference.
