---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-DOCS
artifact_type: plan
tags: [documentation, visualization, simulation-quality]
---

# Implementation Plan — TCK-20260821-VISUAL-QUALITY-DOCS

## Summary

This is a pure-documentation, no-`src`/`tools` ticket — the capstone of the 8-ticket
world-rendering-core batch. It creates four new files: three under a new
`docs/visual_quality/` directory (`scoring_contract.md`, `current_state.md`,
`audit_workflow.md`) mirroring `docs/simulation_quality/`'s three-file shape but scaled
down to the visual-quality system's genuinely smaller real scope, and one new periodic
audit entry, `docs/audits/D26_visual_quality_integration.md`, mirroring
`docs/audits/D20_simq_integration.md`'s format. It deliberately does **not** touch
`docs/audits/audit_dimensions.md` (disclosed as a known limitation inside the D26 doc's
own text instead of silently repaired), does **not** add `docs/visual_quality/` to
`tests/docs/test_doc_path_existence.py`'s `SCOPE_DIRS`, and does **not** add a new
parity-ledger entry (it documents already-`verified` `INFRA-370`–`INFRA-376` entries; it
introduces no new logic for a ledger entry to track). The single hardest constraint this
plan must hold the line on: the new docs must state that the metric/grading *mechanism*
is complete and real, while the actual healthy-band *threshold values* in
`config/rendering/grade_thresholds.toml` remain illustrative/uncalibrated — confirmed
directly by re-reading that file's own header comments and `tools/calibrate_rendering.py`
during this planning pass (citations inline below), not merely trusted from
investigation.md.

## Key Decisions (resolving the ticket's open items)

**Decision 1 — `docs/visual_quality/` file set and naming: adopt investigation.md's
proposal, bare names.** `docs/visual_quality/scoring_contract.md`,
`docs/visual_quality/current_state.md`, `docs/visual_quality/audit_workflow.md`. Confirmed
by direct read that SimQ's own three files use bare names
(`docs/simulation_quality/quality_scoring_contract.md`,
`docs/simulation_quality/current_state.md`, `docs/simulation_quality/audit_workflow.md`)
— actually `quality_scoring_contract.md` is not fully bare (carries a `quality_` prefix),
but `current_state.md`/`audit_workflow.md` are bare, and the directory itself
(`simulation_quality/`) does the scoping. For `visual_quality/`, `scoring_contract.md`
(no `visual_` or `quality_` prefix) is the more consistent choice, matching the two
already-bare siblings' convention rather than the one partially-prefixed file — the
directory alone scopes all three. No override found; adopted as proposed.

**Decision 2 — `docs/audits/D26_<slug>.md` naming: `D26_visual_quality_integration.md`.**
Mirrors `D20_simq_integration.md`'s exact naming pattern (`D<NN>_<subsystem>_integration.md`)
since D26 documents the same relationship shape (a new scoring subsystem's integration
into the docs/audit ecosystem) that D20 documents for SimQ.

**Decision 3 — `audit_dimensions.md`: do NOT repair it in this ticket. Adopted, not
overridden.** Re-confirmed directly during this planning pass (not just trusted from
investigation.md): `docs/audits/audit_dimensions.md:20` states "across all 18 dimensions"
while its Dimension Table (`docs/audits/audit_dimensions.md:97-124`, confirmed by
`grep -n "^## \|^### "` section listing) lists only D01–D18 plus one `D20` row
(`docs/audits/audit_dimensions.md:109`) — D19 and D21–D25 have zero occurrences anywhere
in the file (confirmed by grep). The master table's one `D20` row also only links to
`D20_simq_integration.md`, not the second, independently-existing
`D20_simq_quality_status_review.md` — a pre-existing duplicate this ticket did not create
and is not asked to resolve. A partial fix (adding only a D26 row) would produce a
*third* inconsistent state (index says "18", lists 19, is missing 6, and now has 2
untouched pre-existing problems plus 1 freshly-added row) rather than resolving anything.
Full repair is 6 missing dimensions × 2 tables each (master Dimension Table +
per-Group sub-table, confirmed both exist: `docs/audits/audit_dimensions.md:97-124` and
`:125-185`) plus reconciling the D20 duplicate — materially larger than this ticket's
own Scope/Acceptance Criteria call for. Disclosed instead as a one-line note inside the
new D26 doc (Step 4, Dimension Profile section) per investigation.md's exact wording.

**Decision 4 — `docs/visual_quality/current_state.md` accuracy: mechanism real, threshold
values illustrative — verified directly, not just trusted from investigation.md.**
Re-read `config/rendering/grade_thresholds.toml:1-8` directly: header comment states
"Illustrative values only, NOT calibrated" twice (once above `[hard_rules.fully_connected]`,
once above `[soft_rules.fill_ratio_healthy_band]`) and states the S/A/B/C/D ladder itself
(`S=2.0 A=0.5 B=0.0 C=-0.5 D=-1.0`) is "copied BY VALUE from
config/simulation_quality/grade_thresholds.yaml... this file does NOT import or reference
that file." Re-read `tools/calibrate_rendering.py`: `validation_summary` field exists at
line 246; the script's `aggregate` mode writes its report to
`config/rendering/calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION.json`
(line 276) — confirmed by `ls config/rendering/` that this path does **not** exist on
disk (only `grade_thresholds.toml` is present). Step 3 below must state both facts
side by side: metrics/grader mechanism complete and tested; threshold *values* and the
aggregate calibration report itself not yet produced/committed.

**Decision 5 — `docs/visual_quality/audit_workflow.md` content: document the two real
entry points only, no fabricated formal pipeline.** `tools/calibrate_rendering.py`
(`run`/`aggregate` subcommands, confirmed present by grep above) and dispatching the
`world-render-reviewer` agent (`.claude/agents/world-render-reviewer.md`) over a
`Tier1Digest` produced by `src/rendering/review_pipeline.py`'s
`run_tier0_tier1_pipeline`. No `.claude/workflows/*.js`-equivalent file exists for
visual-quality (unlike SimQ's real `simq-audit.js`) — the doc must not imply one does.

**Decision 6 — `tests/docs/test_doc_path_existence.py` coverage: do NOT add
`docs/visual_quality/` to `SCOPE_DIRS`. Adopted, not overridden.** `SCOPE_DIRS` is
currently `("docs/engine", "docs/architecture", "docs/performance")` — it excludes
`docs/simulation_quality/`, the exact directory this ticket's new files are modeled on.
Adding coverage for the new, smaller directory while its own structural precedent stays
uncovered is an inconsistent, unrequested scope expansion, and risks tripping the test's
existing `strict=True` xfail mechanism for no requested benefit.

**Decision 7 — no new parity-ledger entry.** This ticket adds no new logic or behavior;
it documents behavior already covered by `INFRA-370` through `INFRA-376`
(`docs/parity_ledger/infrastructure.yaml:10840-10940`, confirmed present, all
`status: verified`, `priority: P2`, by direct grep during this planning pass). The
Authoritative Mechanics Rule's parity requirement ("if logic changes, update... the
parity ledger entry") does not trigger — no logic changes. Mechanically adding an
`INFRA-377` entry with no corresponding behavior change would itself be an inaccurate
ledger entry. No new entry is added by this plan.

## Steps

### Step 1 — Re-verify D26 is still the correct next available audit-dimension number

**Files:** None (verification-only step; no file written).
**Change:** Before creating `docs/audits/D26_visual_quality_integration.md` in Step 4,
the implementer must independently re-run `ls docs/audits/D*.md | sort -V` themselves,
at actual implementation time, and confirm the highest existing number is still D25 (this
plan's own verification, run during planning on 2026-08-23, found:
`D01`...`D18`, `D19_domain_phase_inventory.md`, `D20_simq_integration.md`,
`D20_simq_quality_status_review.md`, `D21_entity_lifecycle_foundation_layers.md`,
`D22_dormant_content_wiring.md`, `D23_architecture_resilience.md`,
`D24_codebase_health_observatory.md`, `D25_engine_docs_drift.md` — D25 is the max,
confirming D26 is free). Per the ticket's own AC #2 and CLAUDE.md's "do not guess" rule,
this plan's timestamp is not sufficient — the implementer's own re-run, immediately
before Step 4, is the actual gate. If a `D26_*.md` file is found to already exist at
implementation time, stop and re-scope to the next free number rather than overwriting.
**Do NOT touch:** Any existing `docs/audits/D*.md` file.
**Verify:** Manual — the `ls`/`sort -V` output itself, re-run and inspected by the
implementer, not copied from this plan.

### Step 2 — Create `docs/visual_quality/scoring_contract.md`

**Files:** `docs/visual_quality/scoring_contract.md` (new).
**Change:** New file, frontmatter:
```yaml
---
status: active
layer: world
authority: P1
audience: developer
tags: [rendering, visualization, simulation-quality, documentation]
---
```
(`status`/`layer`/`authority`/`audience` required by `_validate_doc()`,
`tools/validate_frontmatter.py:184-197`, confirmed by direct read during this planning
pass — `tags` not registry-gated for `doc` content-type since `_validate_doc` never calls
`_check_tags`, confirmed by the same read: only `_validate_ticket`/`_validate_artifact`
call `_check_tags`, lines 210/224. `layer: world` matches every one of the 8 prerequisite
tickets' own frontmatter.)

Content — numbered sections mirroring `quality_scoring_contract.md`'s shape
(`docs/simulation_quality/quality_scoring_contract.md:23-1578`, section headers confirmed
by grep: `## 1. Purpose & Scope` through `## 14. Non-Goals for MVP`) at a scale
proportionate to the real, smaller visual-quality system — no REST API section (no REST
surface exists in `src/rendering/`), no 10-pillar registry (there is no `PillarScorer`
subclassing, no `PillarId` registration — enforced by
`tests/architecture/test_rendering_zero_new_dependency_guard.py`, per investigation.md),
no dual-feed broker mode section (no `QualityFeedAdapter`/Redis consumer exists for
rendering):

1. **Purpose & Scope** — this module scores structural/geometric quality of a rendered
   world state (connectivity, density, terrain shape, variant diversity), turning raw
   facts into an S/A/B/C/D/F grade and an escalation decision for agent review. It does
   not score simulation *behavioral* health (that is `src.simulation_quality`) or
   render-pixel correctness (that is the golden-hash incremental-render test).
2. **Architectural Position** — data flow diagram: `render.py`/`connectivity.py`/
   `density.py`/`shape.py`/`variants.py` (raw metric facts) → `grading.py`
   (`load_grade_config`, `evaluate_hard_rule`, `evaluate_soft_rule`, `combine_rule_deltas`,
   `assign_grade`, `average_scores`) → `review_pipeline.py`'s
   `run_tier0_tier1_pipeline` (`Tier1Digest`) → `.claude/agents/world-render-reviewer.md`.
   State the architectural-independence boundary explicitly: `src/rendering/` never
   imports `src.simulation_quality.*` or `src.observability.events`, never subclasses
   `PillarScorer`, never registers a `PillarId` — enforced by
   `tests/architecture/test_rendering_zero_new_dependency_guard.py` (cite
   `INFRA-374`, `docs/parity_ledger/infrastructure.yaml:10896-10911`).
3. **The Four Metric Families** — one subsection per module, each stating its real
   function signature and the one behavioral fact worth documenting per family:
   - Connectivity (`connectivity.py`): `analyze_connectivity(terrain, blocked_tiles) ->
     ConnectivityResult`; BFS flood-fill mirroring exactly the first two checks of
     `LegalityServiceV2.verify_occupancy` (`src/engine/legality.py:71-77`).
   - Density (`density.py`): `compute_density_cv(entities) -> DensityResult`;
     population-stdev (`statistics.pstdev`, not sample-stdev) of nearest-neighbor
     distance over the mean. Cite the two verified anchors verbatim, uncomputed:
     `sandbox_world` CV = `0.6478017242079448`, `dungeon_crawl` CV =
     `0.6782405727873148`.
   - Shape (`shape.py`): `connected_components(terrain, min_size=20,
     excluded_types={"PLAIN","ROAD"}) -> list[ShapeComponent]`; BFS run once per
     distinct raw terrain-type string, `fill_ratio = len(tiles) / bbox_area` computed
     per connected component (not one aggregated bounding box — document the
     pre-fix bug this replaced: FOREST fill-ratio 0.716 vs. corrected 1.000/1.000).
   - Variants (`variants.py`): `total_variation_distance(h1, h2) -> float`
     (0.5·Σ|h1[k]−h2[k]|); cite the verified anchor verbatim, uncomputed:
     `TVD(sandbox_world, dungeon_crawl) = 0.23161981243456373`, and same-spec/
     different-seed TVD = exactly 0.0 for `dungeon_crawl`. Note
     `select_trail_entity` deliberately uses `hashlib.sha256`, not
     `DeterministicRNG`/`Domain` — a read-only QA selection must not touch the
     replay-critical authoritative-randomness mechanism.
4. **Grade Model** — hard rules (binary pass/fail, fixed delta) vs. soft rules
   (trapezoidal, healthy-band-shaped, non-monotonic — peak inside
   `[healthy_low, healthy_high]`, ramping to `min_delta` at `low`/`high`), additive
   combination (`combine_rule_deltas`), and the assignment ladder. Cite the ladder
   verbatim, uncomputed: `S > 2.0`, `A > 0.5`, `B > 0.0`, `C > -0.5`, `D > -1.0`, `F`
   otherwise — copied **by value**, not imported, from
   `config/simulation_quality/grade_thresholds.yaml` (confirmed identical by direct
   read of `config/rendering/grade_thresholds.toml:3-8` during this planning pass).
   `average_scores` is a plain arithmetic mean, no N=1 special case.
5. **Escalation Pipeline** — `Tier1Digest` (JSON-serializable, `digest_to_json`,
   `sort_keys=True`); `should_escalate(hard_results, grade) -> bool` (any hard-rule
   failure, or grade in `{D, F}`); the structural enforcement point is the `if
   escalate:` gate at `review_pipeline.py:112-117` — `render_annotated(...)` and the
   annotated PNG write happen only inside that branch, enforced in code, not by
   agent-prompt discipline alone.
6. **Testing Contract** — list the real test files covering this system:
   `tests/unit/rendering/test_connectivity.py`, `test_density.py`, `test_shape.py`,
   `test_variants.py`, `test_grading.py`, `test_review_pipeline.py`, plus
   `tests/architecture/test_rendering_zero_new_dependency_guard.py` and
   `tests/tools/test_calibrate_rendering.py`.
7. **Non-Goals** — explicitly state what this system does not have, to prevent a
   future reader assuming SimQ-parity feature-for-feature: no REST API surface, no
   persistence/`QualityHub`-equivalent event-driven scoring, no `PillarScorer`
   registry, no dual-feed broker mode, no CI-gating of grade thresholds.

**Do NOT touch:** `docs/simulation_quality/*.md` (read-only reference, not edited);
`config/rendering/grade_thresholds.toml`; any `src/rendering/*.py` file.
**Verify:** `python3 tools/validate_frontmatter.py docs/visual_quality/scoring_contract.md`
exits 0.

### Step 3 — Create `docs/visual_quality/current_state.md`

**Files:** `docs/visual_quality/current_state.md` (new).
**Change:** Same required frontmatter fields as Step 2
(`status: active`, `layer: world`, `authority: P1`, `audience: developer`,
`tags: [rendering, visualization, simulation-quality, documentation]`). Content: a
single dated session-entry, matching `docs/simulation_quality/current_state.md`'s
chronologically-appended, dated-heading style (confirmed by grep:
`## 2026-08-07 ...`, `## 2026-08-05 ...` headings) but starting with just one entry
since this is the visual-quality system's first such record:

```
## 2026-08-23 — Initial capture: mechanism complete, threshold values illustrative
```

Under that heading, state — this is the load-bearing anti-drift content of this
entire ticket, do not soften:

- **Real and finished:** all four raw-metric modules (connectivity, density, shape,
  variants-TVD) implemented, unit-tested, and empirically verified against real
  corpus values. Cite the anchors verbatim, uncomputed: density CV
  `0.6478017242079448` (`sandbox_world`) / `0.6782405727873148` (`dungeon_crawl`);
  TVD `0.23161981243456373`. The grading mechanism (hard/soft rule evaluation,
  additive combination, S–F assignment) is implemented and tested, reusing SimQ's
  exact threshold ladder by value: `S=2.0/A=0.5/B=0.0/C=-0.5/D=-1.0`.
- **Still illustrative, not calibrated:** the actual healthy-band *rule* values in
  `config/rendering/grade_thresholds.toml` (`[hard_rules.fully_connected]`
  pass/fail deltas; `[soft_rules.fill_ratio_healthy_band]` low/healthy_low/
  healthy_high/high). State plainly, quoting the file's own header: the file's
  comments explicitly read "Illustrative values only, NOT calibrated" — confirmed
  by direct re-read of `config/rendering/grade_thresholds.toml:1-8` during this
  planning pass (Decision 4 above).
- **Calibration tooling status:** `tools/calibrate_rendering.py` exists, is tested
  (`run`/`aggregate` subcommands), and can produce descriptive min/max/mean
  statistics per family from real per-`(world, seed)` runs. Its
  `validation_summary` field (`tools/calibrate_rendering.py:246`) states plainly
  that no threshold value in any report it produces is "asserted, gated, or
  final." As of this entry, **no `config/rendering/calibration_report_*.json`
  file exists on disk** — confirmed by `ls config/rendering/` during this
  planning pass, which shows only `grade_thresholds.toml` present. The aggregate
  report has never been generated/committed as a run artifact.
  `compute_trail_activity` (`src/rendering/variants.py`) has zero calibration
  evidence at all — never run, never wired into `calibrate_rendering.py`.
- **Related:** link `docs/visual_quality/scoring_contract.md`,
  `config/rendering/grade_thresholds.toml`, `tools/calibrate_rendering.py`,
  parity ledger `INFRA-372` (shape threshold explicitly flagged "uncalibrated
  and provisional") and `INFRA-376` (calibration-script integrity guard).

**Do NOT touch:** `config/rendering/grade_thresholds.toml` itself (documented, not
edited — no threshold value changes in this ticket).
**Verify:** `python3 tools/validate_frontmatter.py docs/visual_quality/current_state.md`
exits 0; manual prose review confirms no sentence implies the threshold *values* (as
opposed to the mechanism) are calibrated — this is the Verify-phase human/agent
review point test_plan.md flags as having no automated test.

### Step 4 — Create `docs/visual_quality/audit_workflow.md`

**Files:** `docs/visual_quality/audit_workflow.md` (new).
**Change:** Same required frontmatter fields as Step 2. Content — 5 sections mirroring
`docs/simulation_quality/audit_workflow.md`'s shape (confirmed by grep:
`## 1. What this replaces`, `## 2. The 7-phase pipeline`, `## 3. Governance decision`,
`## 4. Usage`, `## 5. Do not`), scaled to the real, smaller visual-quality workflow:

1. **What this is (and is not)** — state plainly that, unlike SimQ's real
   `.claude/workflows/simq-audit.js` 7-phase orchestration, no equivalent formal
   multi-phase `/visual-quality-audit` workflow exists for visual-quality. This
   document describes the two real, simpler entry points that do exist.
2. **Entry Point A — `tools/calibrate_rendering.py`** — `run --world --seed` (compiles
   one world+seed, runs all four metric families, writes a per-run JSON artifact
   under `data/calibration/rendering/{world}_seed{seed}/quality_report.json`,
   guarded by `CalibrationIntegrityError` on any compile warning/zero-entity/
   zero-region condition) and `aggregate` (scans a directory of per-run artifacts,
   writes one provenance-headed, purely-descriptive JSON report to
   `config/rendering/calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION.json`
   — never opens, parses, or writes `grade_thresholds.toml`).
3. **Entry Point B — dispatching `world-render-reviewer` over a `Tier1Digest`** — how
   `run_tier0_tier1_pipeline` produces the digest; how the agent reads it first,
   only reads `annotated_render_path` when `escalate == True`, and never substitutes
   `plain_render_path` as an escalation image; the Four Review Dimensions
   (Connectivity, Terrain Shape, Density, Grade) and four-tier Severity
   Classification (CRITICAL/HIGH/MEDIUM/LOW).
4. **Usage** — concrete example invocations for both entry points.
5. **Do not** — do not treat any `calibrate_rendering.py aggregate` output as a
   gating/CI-enforced value; do not skip Tier 0 straight to fetching the annotated
   image; do not fabricate a formal orchestrated pipeline beyond these two entry
   points.

**Do NOT touch:** `.claude/agents/world-render-reviewer.md` (referenced, not edited);
`src/rendering/review_pipeline.py`.
**Verify:** `python3 tools/validate_frontmatter.py docs/visual_quality/audit_workflow.md`
exits 0.

### Step 5 — Create `docs/audits/D26_visual_quality_integration.md`

**Files:** `docs/audits/D26_visual_quality_integration.md` (new).
**Change:** Frontmatter mirroring `D20_simq_integration.md`'s own shape (confirmed by
direct read, `docs/audits/D20_simq_integration.md:1-7`):
```yaml
---
status: historical
layer: world
authority: P1
audience: developer
tags: [audit, rendering, visualization, simulation-quality, documentation]
---
```
(`status: historical` matches D20's own value — this is a point-in-time audit record,
not a living doc; `layer: world` matches the visual-quality system's own layer rather
than D20's `layer: observability`, since this dimension's subject matter is the
rendering/world-QA system, not an observability pipeline.)

Content, mirroring D20's Dimension Profile / Related dimensions / Findings Summary
format (`docs/audits/D20_simq_integration.md:22-41`, `:241-249`):

- **Summary** (short prose, 1 paragraph): this is the first-ever audit pass for the
  visual-quality system, covering the 8 prerequisite tickets
  (`WORLD-RENDER-CORE` through `VISUAL-QUALITY-CALIBRATION`, all `status: DONE`).
- **Dimension Profile table** (7 rows, matching D20's exact axis set):

  | Axis | Value |
  |---|---|
  | **Group** | A — Simulation Quality (mirrors D20's own Group assignment — visual-quality is architecturally analogous: raw metrics → grading → threshold ladder, the same shape SimQ uses) |
  | **State** | `done` — metric/grading mechanism; `partial` — threshold calibration (see Findings Summary) |
  | **Impact** | (implementer's own 1–5 judgment call per `docs/audits/audit_dimensions.md:52-61`'s Impact rubric — do not invent a number without reading that rubric first) |
  | **Interest** | (implementer's own 1–5 judgment call per the same file's Interest rubric, `:62-71`) |
  | **Priority** | Impact + Interest (computed, not independently chosen) |
  | **Method** | code-read + test-run |
  | **Audit history** | a single dated entry only: `2026-08-23 (original, first pass — mechanism verified complete, threshold values confirmed illustrative/uncalibrated)`. Per investigation.md's explicit instruction: this is a first-ever pass, the cell must not fabricate a narrative chain the way D20's own cell (built from 4+ real historical events) does. |

- **Related dimensions table** (2-column, Dimension/Relationship):

  | Dimension | Relationship |
  |---|---|
  | D20 (SimQ Integration) | Structural precedent — visual-quality's grading mechanism reuses SimQ's exact threshold ladder by value, and this doc mirrors D20's own format |
  | D10 (Test Coverage & Regression Risk) | The 8 prerequisite tickets added `tests/unit/rendering/`, `tests/architecture/test_rendering_zero_new_dependency_guard.py`, `tests/tools/test_calibrate_rendering.py` |
  | D17 (Documentation Currency) | This ticket is itself a documentation-currency action; also the source of the disclosed `audit_dimensions.md` staleness note below |

- **Findings Summary table** (# / Finding / Severity / Status, matching D20's shape):

  | # | Finding | Severity | Status |
  |---|---|---|---|
  | F1 | Four raw-metric modules + grading mechanism implemented, tested, empirically verified | — | **CONFIRMED REAL** |
  | F2 | `config/rendering/grade_thresholds.toml`'s healthy-band rule values remain illustrative/uncalibrated; no `calibration_report_*.json` has been generated/committed; `compute_trail_activity` has zero calibration evidence | Low (disclosed, tracked, non-blocking — no CI gate depends on these values) | **OPEN, DISCLOSED** — tracked by `TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s own completed scope (tooling shipped; calibration pass itself deferred) |
  | F3 | `docs/audits/audit_dimensions.md`'s master index is stale — missing D19/D21–D25 and containing a pre-existing D20-duplicate — and was not repaired as part of this ticket | Low | **DISCLOSED, OUT OF SCOPE** — not reflected in `docs/audits/audit_dimensions.md`'s master index, which has been stale since before D19 and is out of scope for this ticket to repair (see Decision 3 above; a dedicated documentation-hygiene ticket is the correct place to fix it) |

**Do NOT touch:** `docs/audits/audit_dimensions.md` (see Decision 3 — explicitly not
edited by this step or any other step in this plan); `docs/audits/D20_simq_integration.md`
or `D20_simq_quality_status_review.md` (referenced only, not edited).
**Verify:** `python3 tools/validate_frontmatter.py docs/audits/D26_visual_quality_integration.md`
exits 0; the implementer's own Step 1 re-run confirms the filename's `D26` prefix is
still the correct next number at the moment this file is actually written.

### Step 6 — Registry regeneration and static verification pass

**Files:** `docs/REGISTRY.yaml` (regenerated, not hand-edited).
**Change:** Run `make docs-registry` (equivalently
`python3 tools/generate_registry.py`) after Steps 2–5 land. This is the **only** writer
to `docs/REGISTRY.yaml` in this ticket's scope — no other step or concurrent process in
this plan touches it. Per CLAUDE.md's "After Work" rule, full regeneration also happens
automatically at Finalize regardless, so this step is a pre-Finalize confirmation, not a
distinct durable action: confirm the tool exits 0 with no new frontmatter-parse errors,
and that the regenerated file contains an entry for each of the 4 new paths
(`grep -c "docs/visual_quality/\|docs/audits/D26_" docs/REGISTRY.yaml`). Also run the
layer/tag registry list commands as an informational cross-check (not a hard gate for
`doc`-type files, per Decision-adjacent finding in Step 2): `python3
tools/layer_registry.py list` (confirm `world` present) and `python3
tools/tag_registry.py list` (confirm `rendering`/`visualization`/`simulation-quality`/
`documentation` all present — all four already registered per investigation.md, not
newly registered by this ticket).
**Do NOT touch:** Any pre-existing `docs/REGISTRY.yaml` entry unrelated to this ticket's
4 new files — diff the regenerated file against its prior committed version and confirm
every changed/added line is attributable to the new files (or `generate_registry.py`'s
already-known routine timestamp/ordering churn), not an accidental removal.
**Verify:** `make docs-registry` exit code 0; grep count ≥ 4 for the new paths; diff
review shows no unrelated entry dropped.

### Step 7 — Run the doc-integrity and rendering regression suites

**Files:** None (test-run-only step).
**Change:** Run the three scoped pytest commands from `test_plan.md`:
```
pytest tests/docs/ -m "not slow and not extra_slow"
pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py \
       tests/tools/test_calibrate_rendering.py -m "not slow and not extra_slow"
pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py \
       tests/tools/test_layer_registry.py tests/tools/test_tag_registry.py \
       -m "not slow and not extra_slow"
```
These confirm: (a) `tests/docs/test_doc_integrity.py` stays green (its checks read off a
fixed manifest of `mandatory_documents`, not a directory scan, so the 4 new files are not
implicitly pulled into scope — confirm this suite's outcome is unchanged, not that it
newly exercises the new files); (b) `tests/docs/test_doc_path_existence.py` shows its
pre-existing `strict=True` xfail with the same 12-dead-citation count, not a new failure
shape (its `SCOPE_DIRS` does not include `docs/visual_quality/`/`docs/audits/` per
Decision 6, so it structurally cannot regress from this ticket); (c) the rendering system
this ticket documents is still green underneath the new docs; (d) the frontmatter/
registry tooling this ticket's Steps 2–6 depend on is unaffected.
**Do NOT touch:** Any file under `tests/` — this step runs existing tests, it does not
add or modify any.
**Verify:** All three commands exit 0 (with `test_doc_path_existence.py`'s known
`strict=True` xfail as its expected, unchanged outcome).

## Scope Guards

- Do not edit `docs/audits/audit_dimensions.md` (Decision 3) — the D20 duplicate and the
  D19/D21–D25 gaps stay as-is; disclosed only inside the new D26 doc's own text.
- Do not add `docs/visual_quality/` (or `docs/audits/`) to
  `tests/docs/test_doc_path_existence.py`'s `SCOPE_DIRS` (Decision 6).
- Do not add a new `docs/parity_ledger/*.yaml` entry (Decision 7) — no new logic exists
  to track; `INFRA-370`–`INFRA-376` are cited, not modified.
- Do not edit `config/rendering/grade_thresholds.toml` — its values are documented as
  illustrative, never changed, in this ticket.
- Do not edit any `src/rendering/*.py` or `tools/calibrate_rendering.py` file — this is a
  docs-only ticket; the rendering system is read and cited, never modified.
- Do not edit `docs/simulation_quality/*.md` or `docs/audits/D20_*.md` — reference-only.
- Do not round, recompute, or "improve" any of the three numeric anchors (density CV
  ×2, TVD, grade ladder) — copy verbatim as given in this plan and in investigation.md.
- Do not claim or imply the threshold *values* in `grade_thresholds.toml` are calibrated
  anywhere in the new docs (Decision 4) — this is the single highest-risk drift this
  ticket could introduce.
- Do not fabricate a formal multi-phase `/visual-quality-audit` workflow file or
  orchestration that was never built (Decision 5).

## Dependency Map

Steps 2, 3, 4, and 5 are independent of each other (four distinct new files, no shared
mutable state) and may be done in any order, though Step 5 references content decisions
made explicit in Step 3 (the illustrative-threshold disclosure) and should logically
follow it for consistency of phrasing. Step 1 must run before Step 5 specifically (its
output — the confirmed-free `D26` number — gates the filename Step 5 creates). Step 6
depends on Steps 2–5 all being complete (it regenerates the registry over the finished
file set). Step 7 depends on Steps 2–6 being complete (it is the final regression/
verification pass over the whole change set).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `docs/visual_quality/` subfolder exists with >=3 files mirroring the three SimQ shapes, each passing `tools/validate_frontmatter.py` | Steps 2, 3, 4 | `python3 tools/validate_frontmatter.py docs/visual_quality/*.md` exit 0 (per-file in each step's Verify; `tests/tools/test_validate_frontmatter.py` regression run in Step 7) |
| `docs/audits/D26_<slug>.md` created following D20's format, D26 re-confirmed as next number at implementation time | Steps 1, 5 | Step 1's own `ls docs/audits/D*.md \| sort -V` re-run; `python3 tools/validate_frontmatter.py docs/audits/D26_visual_quality_integration.md` exit 0 |
| All new docs use only registry-allowlisted layer/tags | Steps 2, 3, 4, 5, 6 | `python3 tools/layer_registry.py list` / `tools/tag_registry.py list` cross-check in Step 6 (informational — `_validate_doc()` itself does not gate doc tags, per Step 2's cited confirmation) |
| `docs/REGISTRY.yaml` regeneration correctly picks up the new docs | Step 6 | `make docs-registry` exit 0 + grep count ≥ 4 for the 4 new paths |

## Anti-Drift Notes

- **The D26 number must be re-verified by the implementer's own command run, not
  trusted from this plan, investigation.md, or the proposal.** This plan's own
  verification (Step 1) was performed 2026-08-23 during planning and found D25 as the
  max — but this is a shared, actively-changing repo, and the ticket's own AC #2
  requires a fresh, implementation-time check.
- **The illustrative-vs-calibrated distinction (Decision 4) is the highest-value thing
  this plan protects.** Every one of Steps 2, 3, and 5 that mentions
  `grade_thresholds.toml` or `calibrate_rendering.py` must state the mechanism is real
  and the specific threshold values are not — never merge the two into a single
  "calibrated" claim.
- **`audit_dimensions.md` is one edit away from an easy, well-intentioned scope
  violation.** Because Step 5 creates a file directly adjacent to that index, and the
  natural instinct when creating D26 is "just add the row," Step 5's own Do NOT touch
  line and this plan's Scope Guards both call this out explicitly. If a reviewer or the
  implementer is tempted to add a D26 row "just this once," that is exactly the drift
  Decision 3 forecloses — raise it as a separate documentation-hygiene ticket instead.
- **Numeric anchors are load-bearing and must be copied verbatim.** Density CV
  `0.6478017242079448` (`sandbox_world`) / `0.6782405727873148` (`dungeon_crawl`), TVD
  `0.23161981243456373`, and the grade ladder `S=2.0/A=0.5/B=0.0/C=-0.5/D=-1.0` all
  appear in this plan exactly as given by investigation.md and independently
  re-confirmed against `config/rendering/grade_thresholds.toml` during planning — do not
  recompute or round when transcribing them into the new docs.
- **No parity-ledger entry is a deliberate decision, not an omission.** If a future
  reviewer expects an `INFRA-377` by pattern-matching the prior 8 tickets, point them to
  Decision 7 above: this ticket changes no behavior, so there is nothing new for a
  ledger entry to track.
