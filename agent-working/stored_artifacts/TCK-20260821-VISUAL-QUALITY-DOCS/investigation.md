---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-DOCS
artifact_type: investigation
tags: [visualization, simulation-quality, world]
---

# Investigation — TCK-20260821-VISUAL-QUALITY-DOCS

## Search Tooling Note

`mcp__knowledge-search__search_docs` returned `{"error": "index not found", "action": "run make
knowledge-index"}` when queried directly (`"visual quality rendering grade scorer documentation
SimQ precedent"`) — confirming the dispatching agent's report that the semantic index is
unavailable in this session. `graphify query` is reachable but returned stale results: querying
`"render.py connectivity density shape variants grading"` surfaced only
`experiments/spatial_rendering/prototype/*` nodes and `.claude/agents/world-render-reviewer.md`,
not the real `src/rendering/*.py` modules that actually exist on disk — the graph has not been
updated (`graphify update .`) since this batch's 8 prior tickets landed real code there. Both
tool calls were made and logged per CLAUDE.md's hard rule before falling back to direct
Read/Grep, as instructed by the dispatching agent.

## Current Behavior

This is a pure-documentation ticket (Type: chore) — there is no `src/`/`tools/` behavior to
change. "Current behavior" here means the real, shipped state of the 8 prerequisite tickets'
code, which this ticket's new docs must describe accurately.

### The shipped visual-quality system (all `status: DONE`, `layer: world`, merged onto this branch)

- **`src/rendering/render.py`** (`TCK-20260821-WORLD-RENDER-CORE`) — `render(state, out_path,
  scale=6) -> dict` draws terrain → buildings → blocked-tile outline → entities (`DRAW_ORDER`
  constant, `render.py:65`), via `terrain_color(raw_value)` (`render.py:47`) and
  `render_output_path(base_dir, run_id, filename) -> str` (`render.py:158`, path shape
  `{base_dir}/{run_id}/renders/{filename}`). `src/rendering/incremental.py`'s
  `IncrementalRenderer` produces pixel-identical output to a full re-render via `src/core/dirty.py`
  DirtySet reuse (verified: `sha256(incremental_final.png) == sha256(full_final.png)` for
  `sandbox_world` seed 42 over 15 ticks). Pure stdlib (`struct`/`zlib` only, via
  `src/rendering/png_writer.py`) — zero third-party dependency added. Known, documented, un-fixed
  gap: `IncrementalRenderer.update()` never paints `ENTITY_COLOR_DEAD` for a mid-run death (not
  exercised by the golden-hash test scenario; follow-up ticket
  `TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP` filed and closed separately).

- **`src/rendering/connectivity.py`** (`TCK-20260821-VISUAL-CONNECTIVITY-METRIC`) —
  `analyze_connectivity(terrain, blocked_tiles) -> ConnectivityResult` (walkable_count,
  component_count, component_sizes, percent_reachable). BFS flood-fill over exactly the first two
  checks of `LegalityServiceV2.verify_occupancy` (`src/engine/legality.py:71-77`): a tile is
  walkable iff `terrain.get(pos) != "WALL"` and `pos not in blocked_tiles`. Membership is checked
  against a precomputed `walkable_tiles` set, never a live re-check (an unbounded live check would
  flood-fill past any tile absent from the terrain dict).

- **`src/rendering/density.py`** (`TCK-20260821-VISUAL-DENSITY-METRIC`) —
  `compute_density_cv(entities) -> DensityResult`: population-stdev (`statistics.pstdev`, NOT
  sample-stdev) of per-entity nearest-Euclidean-distance, divided by the mean, over active
  entities only. Verified to reproduce `sandbox_world` (0.6478017242079448) and `dungeon_crawl`
  (0.6782405727873148) to 6+ significant figures — matches this ticket's own cited anchors
  exactly. `compute_terrain_histogram(terrain) -> dict[str, int]` is a verbatim extraction from
  `experiments/spatial_rendering/prototype/render_world.py:90-95`.

- **`src/rendering/shape.py`** (`TCK-20260821-VISUAL-SHAPE-METRIC`) —
  `connected_components(terrain, min_size=20, excluded_types={"PLAIN","ROAD"}) ->
  list[ShapeComponent]`: BFS run once PER DISTINCT RAW terrain-type string (not one global BFS —
  that's connectivity.py's different question), fill_ratio = `len(tiles) / bbox_area` computed
  per connected component (the real bug this ticket fixed: the pre-fix implementation aggregated
  all same-type tiles into one bounding box with no connectivity check, producing a meaningless
  FOREST fill-ratio of 0.716 instead of the correct 1.000/1.000 pair). `detect_rotation_match(a,
  b) -> bool` tests transpose/rotate-90-CW/rotate-90-CCW against a bounding-box dimension-swap
  gate; documented caveat that for solid rectangular components all three transforms coincide, so
  a `True` result is diagnostic only for non-rectangular/textured components.

- **`src/rendering/variants.py`** (`TCK-20260821-VISUAL-VARIANTS-METRIC`) —
  `total_variation_distance(h1, h2) -> float` (0.5·Σ|h1[k]−h2[k]| over normalized proportions);
  reproduces `TVD(sandbox_world, dungeon_crawl) == 0.23161981243456373` (matches this ticket's own
  cited anchor exactly) and same-spec/different-seed TVD of exactly 0.0 for `dungeon_crawl`.
  `select_trail_entity(world_id, seed, entities) -> int` deliberately uses
  `hashlib.sha256(f"{world_id}:{seed}")` over a sorted active-entity-ID list, NOT
  `DeterministicRNG`/`Domain` — reusing the replay-critical simulation-randomness mechanism for
  read-only QA selection would itself violate the Durable State Rule. `compute_trail_activity` is
  defined but **never calibrated or wired into `tools/calibrate_rendering.py`** — deferred, see
  Current State below.

- **`src/rendering/grading.py`** (`TCK-20260821-VISUAL-GRADE-SCORER`) — turns the four modules'
  raw structural facts into an S/A/B/C/D/F grade via `load_grade_config()` (fail-loud
  `tomllib` loader of `config/rendering/grade_thresholds.toml`), `evaluate_hard_rule` (binary
  pass/fail, fixed delta), `evaluate_soft_rule`/`_trapezoidal_delta` (non-monotonic healthy-band
  function — positive inside `[healthy_low, healthy_high]`, ramping to `min_delta` at both
  `low`/`high` extremes), `combine_rule_deltas` (plain additive sum), `assign_grade` (strict-`>`
  ladder, S=2.0/A=0.5/B=0.0/C=-0.5/D=-1.0 — copied BY VALUE from
  `config/simulation_quality/grade_thresholds.yaml`, confirmed identical, never imported), and
  `average_scores` (plain arithmetic mean, no N=1 special case). Architecturally independent from
  `src.simulation_quality`: does not import `src.simulation_quality.*`/`src.observability.events`,
  does not subclass `PillarScorer`, does not register a new `PillarId` — enforced by
  `tests/architecture/test_rendering_zero_new_dependency_guard.py`.

- **`src/rendering/review_pipeline.py`** (`TCK-20260821-VISUAL-AGENT-REVIEW`) —
  `run_tier0_tier1_pipeline(state, world_id, base_dir, run_id, grade_config=None) -> Tier1Digest`
  composes connectivity/density/shape + grading into one deterministic, JSON-serializable digest
  (`digest_to_json`, `sort_keys=True`). `should_escalate(hard_results, grade) -> bool` is the
  single call site for the escalation cutoff (any hard-rule failure, or grade in `{D, F}`). The
  structural enforcement mechanism for "zero image is ever fetched when Tier 0 does not flag an
  anomaly" is the `if escalate:` gate at `review_pipeline.py:112-117` — `render_annotated(...)`
  (`src/rendering/render_annotated.py`, ported from
  `experiments/spatial_rendering/prototype/render_annotated.py`) is called, and the annotated PNG
  written to disk, ONLY inside that branch. This is enforced in code, not left to agent-prompt
  discipline alone.

- **`.claude/agents/world-render-reviewer.md`** — the Tier-0/1/2 reviewing agent. Reads the
  `Tier1Digest` first; reads `annotated_render_path` only when `escalate == True`; never
  substitutes `plain_render_path` as an escalation image. Four Review Dimensions (Connectivity,
  Terrain Shape, Density, Grade) and a four-tier Severity Classification
  (CRITICAL/HIGH/MEDIUM/LOW). Explicitly out of scope for Mechanics Bible review — that's
  `simulation-analyst`'s job over different data.

- **`config/rendering/grade_thresholds.toml`** — the grade-threshold table is copied by value
  from SimQ (confirmed identical), but the `[hard_rules.fully_connected]` and
  `[soft_rules.fill_ratio_healthy_band]` values are explicitly commented **"Illustrative values
  only, NOT calibrated"** in the file itself.

- **`tools/calibrate_rendering.py`** (`TCK-20260821-VISUAL-QUALITY-CALIBRATION`) — `run --world
  --seed` runs the four families (connectivity/density/shape/variants-TVD) against one real
  compiled world+seed and writes `data/calibration/rendering/{world}_seed{seed}/
  quality_report.json`, guarded by `CalibrationIntegrityError` (fails loud on any compile warning,
  `entity_count == 0`, or `region_count == 0`, writing a `compile_health.json` sidecar before
  raising). `aggregate` scans a directory of per-run artifacts and writes ONE
  provenance-headed, purely-descriptive JSON report to `config/rendering/
  calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION.json` — **never opens, parses, or
  writes `grade_thresholds.toml`**, and the report's own `validation_summary` field states
  explicitly: "no threshold value in this report is asserted, gated, or final. Not consumed by any
  pytest/CI gate or scoring pipeline." `compute_trail_activity` is deliberately NOT implemented or
  called by this script (deferred to a future ticket — would require ticking a `Kernel` forward N
  times, a materially more expensive operation than the single `WorldCompiler.compile()` call
  every other family needs).

## Current State — What's Actually Calibrated vs. Still Illustrative

This is the load-bearing fact the ticket's own "REAL, FINISHED, LANDED system" framing depends
on, and it must be stated honestly and precisely in the new `docs/visual_quality/` current-state
doc:

1. All four raw-metric modules (connectivity, density, shape, variants-TVD) are implemented,
   unit-tested, and empirically verified against real corpus values (density CV, TVD anchors
   above) — this part is fully real and finished.
2. The grading mechanism (hard/soft rule evaluation, additive combination, S–F assignment) is
   implemented and tested, reusing SimQ's exact threshold *ladder* (copied by value) — also real
   and finished.
3. The actual healthy-band *rule* values in `config/rendering/grade_thresholds.toml`
   (`fully_connected` pass/fail deltas, `fill_ratio_healthy_band` low/healthy_low/healthy_high/
   high) are **explicitly documented in the config file itself as illustrative, not calibrated**.
4. `tools/calibrate_rendering.py` exists, is tested (11 passing tests), and is capable of
   producing descriptive min/max/mean statistics per family from real per-(world, seed) runs —
   but as of this investigation, **no `config/rendering/calibration_report_*.json` file exists on
   disk** (`config/rendering/` currently contains only `grade_thresholds.toml`) — the aggregate
   report is generated on manual invocation and was not committed as a run artifact.
   `compute_trail_activity` has zero calibration evidence at all (never run).
5. `INFRA-372`'s own parity-ledger text states the shape-metric's 0.95 reference threshold is
   "uncalibrated and provisional, tracked separately (TCK-20260821-VISUAL-QUALITY-CALIBRATION)" —
   and that ticket's own Out of Scope explicitly forbids CI-gating these thresholds and defers
   the FOREST-specific-band question.

**Conclusion for the docs:** the metric/scoring *mechanism* is complete and real; the specific
numeric healthy-band *values* it operates on are still illustrative/uncalibrated placeholders,
exactly mirroring where `docs/simulation_quality/current_state.md` would describe an in-progress
calibration effort — this is not a gap in this ticket's own work, it is the honest, current,
disclosed state of the system it must document.

## Mechanics / Engine Constraints

None. `docs/mechanics/` and `docs/engine/` govern simulation laws and the deterministic tick
loop; the visual-quality/rendering system is explicitly a read-only, non-authoritative QA layer
over `AuthoritativeState` (confirmed by `src/rendering/`'s own architectural-independence
discipline — no module here mutates durable state, and `variants.py`'s `select_trail_entity`
explicitly avoids `DeterministicRNG`/`Domain` to avoid touching the authoritative-randomness
mechanism). No Mechanics Bible chapter or engine contract constrains what this ticket's docs can
say.

## Docs Requiring Update

- `docs/visual_quality/scoring_contract.md`: new file (naming decision below) — the
  quality_scoring_contract.md-equivalent describing `grading.py`'s hard/soft rule mechanism, the
  reused SimQ threshold ladder, and the escalation pipeline; does not yet exist.
- `docs/visual_quality/current_state.md`: new file — the current_state.md-equivalent recording
  what's actually calibrated (metrics: yes; threshold values: no, illustrative) vs. still
  illustrative, referencing `tools/calibrate_rendering.py` and its current empirical/uncalibrated
  status; does not yet exist.
- `docs/visual_quality/audit_workflow.md`: new file — the audit_workflow.md-equivalent describing
  how to run `tools/calibrate_rendering.py`, how the Tier 0/1/2 agent-review pipeline
  (`review_pipeline.py` + `world-render-reviewer.md`) is invoked, and what
  `world-render-reviewer.md` does; does not yet exist.
- `docs/audits/D26_visual_quality_integration.md`: new file (exact slug decided at Plan time) —
  the periodic audit-dimension entry mirroring `D20_simq_integration.md`'s Dimension Profile /
  Related dimensions / Findings Summary format; does not yet exist.

The master index `docs/audits/audit_dimensions.md` (path: `audits/audit_dimensions.md`, under
`docs/`) is deliberately **not** listed above as requiring an update — this is an open decision,
not resolved here, see Risks and Open Questions. If the planner elects to add a D26 row to this
master index (rather than following the already-stale precedent), that file would need a new
row in the main "Dimension Table" plus its matching Group sub-table. If the planner elects to
follow precedent instead (leave the index as-is, matching how D19/D21-D25 were already left
off), no edit to that file is required, and that decision should be recorded in the new D26
doc's own text instead.

No `docs/mechanics/`, `docs/engine/`, or `docs/parity_ledger/*.yaml` file requires any change —
this ticket adds no new logic and changes no existing behavior; it only documents behavior that
was already implemented, tested, and parity-ledger-recorded by the 8 prerequisite tickets
(`INFRA-370` through `INFRA-376`, all already `status: verified`).

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` — all `status: verified`, `priority: P2`:

- `INFRA-370` — BFS connectivity (`src/rendering/connectivity.py`)
- `INFRA-371` — density CV (`src/rendering/density.py`)
- `INFRA-372` — shape fill-ratio + rotation detection (`src/rendering/shape.py`) — text itself
  flags the 0.95 reference threshold as "uncalibrated and provisional"
- `INFRA-373` — TVD (`src/rendering/variants.py`) — also documents that `sandbox_world` is
  deliberately NOT used as a same-spec-seed-invariance anchor (stale resolved-cache artifact, not
  a structural property)
- `INFRA-374` — grade-band scorer (`src/rendering/grading.py`) — explicitly distinct from
  `SIMQ-CALIBRATED-001` and `INFRA-255`
- `INFRA-375` — Tier 0/1/2 pipeline (`src/rendering/review_pipeline.py`,
  `src/rendering/render_annotated.py`)
- `INFRA-376` — calibration-script run-integrity guard (`tools/calibrate_rendering.py`)

No P0 entries in this set — all P2, so no `test_path` is contractually required to pass as a
gating condition for this ticket, though each entry does carry a real `test_path` regardless
(confirmed present for INFRA-370/371/375/376; not independently re-verified for 372/373/374 in
this pass since none are P0). This ticket touches none of these entries' `status` — it only
cites them in new prose.

## Prior Work

- All 8 prerequisite tickets are in `tickets/done/`, each with a `staging_artifacts/` →
  `stored_artifacts/` pair: `TCK-20260821-WORLD-RENDER-CORE`,
  `TCK-20260821-VISUAL-CONNECTIVITY-METRIC`, `TCK-20260821-VISUAL-DENSITY-METRIC`,
  `TCK-20260821-VISUAL-SHAPE-METRIC`, `TCK-20260821-VISUAL-VARIANTS-METRIC`,
  `TCK-20260821-VISUAL-GRADE-SCORER`, `TCK-20260821-VISUAL-AGENT-REVIEW`,
  `TCK-20260821-VISUAL-QUALITY-CALIBRATION`. Each module's own docstring already cites its
  originating ticket, its architectural-independence discipline, and (where relevant) the exact
  PROPOSAL.md line range it was ported/written from — these docstrings are treated as
  load-bearing source material for the new docs, not just code comments.
- `docs/simulation_quality/quality_scoring_contract.md` — 14-section numbered contract doc
  (Purpose & Scope, Architectural Position, Performance Contract, Score Model, the pillars, a
  Scenario Registry, Extensibility Protocol, Data Flow, Traceability, REST API, Testing Contract,
  Acceptance Criteria, Implementation Epics, Non-Goals) — far larger in scope than the
  visual-quality system currently is (10 pillars, REST API, dual-feed broker mode all have no
  visual-quality equivalent). The new scoring-contract doc should mirror the *shape* (numbered
  sections, ticket/module-path header, ## N. headings) at a scale proportionate to the smaller
  real system (4 metric families + 1 grader + 1 pipeline, no REST surface, no persistence layer)
  — not pad out sections that don't apply.
- `docs/simulation_quality/current_state.md` — a chronologically-appended, dated-session-log
  style doc (multiple `## YYYY-MM-DD ...` headings), not a single static snapshot. The
  visual-quality equivalent can start as a single dated entry (this ticket's date) describing the
  one calibration pass that has happened, in the same style, ready to be appended to by future
  sessions the same way SimQ's has been.
- `docs/simulation_quality/audit_workflow.md` — a 5-section prose doc (What this replaces, the
  N-phase pipeline, a governance decision, Usage, Do-not list) describing a formal multi-agent
  `/simq-audit` workflow with its own `.claude/workflows/simq-audit.js`. No equivalent workflow
  file exists for visual-quality (no `/visual-quality-audit` skill/workflow was built by any of
  the 8 prerequisite tickets) — the new audit_workflow.md-equivalent must document the two real,
  simpler entry points that do exist (`tools/calibrate_rendering.py run`/`aggregate`, and
  dispatching the `world-render-reviewer` agent over a `Tier1Digest`), not invent a formal
  multi-phase pipeline that was never built. This is a real scope difference from SimQ's
  precedent, not an omission.
- `docs/audits/D20_simq_integration.md` — historical-record format: Dimension Profile table (7
  rows: Group/State/Impact/Interest/Priority/Method/Audit history — the Audit history cell is a
  long narrative chain, not a single date), a "Related dimensions" 2-column table
  (Dimension/Relationship), then prose sections (Original Finding, Verification, Batch History,
  Module Health, Findings Summary table). For a brand-new D26 (first audit pass, no history to
  chain), the Audit history cell should be a single dated entry, not an empty/fabricated chain.

## Risks and Open Questions

- **D26 number re-verification (ticket's own explicit AC #2 requirement):** re-confirmed at
  investigation time by listing `docs/audits/D*.md` directly:
  `D01`...`D18`, `D19_domain_phase_inventory.md`, `D20_simq_integration.md`,
  `D20_simq_quality_status_review.md` (two files both claiming D20 — a pre-existing duplicate,
  not introduced by this ticket), `D21_entity_lifecycle_foundation_layers.md`,
  `D22_dormant_content_wiring.md`, `D23_architecture_resilience.md`,
  `D24_codebase_health_observatory.md`, `D25_engine_docs_drift.md`. **Highest number on disk is
  D25 — D26 is confirmed still the correct next available number as of this investigation pass.**
  The ticket's own claim that "D25 was claimed same-day by an unrelated ticket" is independently
  confirmed: `D25_engine_docs_drift.md` exists and its content (via
  `tests/docs/test_doc_path_existence.py`'s own xfail reason, which cites
  `docs/audits/D25_engine_docs_drift.md`'s "Recommended Follow-Up" section) matches
  `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`, consistent with `docs/plans/world_rendering_core_epic.md`
  line 31's own citation of that same ticket ID. **This must be re-checked again at actual
  implementation time** — this is a shared, actively-changing repo, and investigation-time
  confirmation is not implementation-time confirmation.
- **The pre-existing D20 duplicate is a real, load-bearing precedent risk for this ticket's own
  approach to `audit_dimensions.md`:** two files already independently exist and answer to "D20"
  (`D20_simq_integration.md`, cited throughout this ticket, and `D20_simq_quality_status_review.md`,
  which `D20_simq_integration.md`'s own final line describes as "a broader-view synthesis
  document, distinct from both this integration-history record and
  `docs/simulation_quality/current_state.md`'s own numbers-only snapshot"). `audit_dimensions.md`'s
  master table lists only the first of the two under `D20`. This means the master index was
  already out of sync with the real file set even before D19/D21-D25 went missing from it — the
  "stale precedent" this ticket could follow is not just an omission pattern, it already contains
  an unresolved duplicate-numbering situation. Flagged for the planner, not resolved here.
- **`audit_dimensions.md` staleness — directly confirmed, not merely trusted from the ticket's own
  claim:** the file's own Purpose text states "This index tracks state, priority, and method
  across all 18 dimensions," but its Dimension Table currently lists 19 distinct D-numbers
  (D01-D18 plus D20) — already inconsistent with its own stated count — and is missing D19, D21,
  D22, D23, D24, D25 entirely (zero occurrences of any of those strings in the file, confirmed by
  direct grep). The ticket's Assumptions section is correct that this file is stale. Whether to
  repair it as part of this ticket is explicitly left as the planner's decision (ticket's own
  Scope item 4) — see recommendation below.
  - **Recommendation:** do NOT attempt a full repair of `audit_dimensions.md` in this ticket. The
    repair is non-trivial (6 missing dimensions × 2 tables each — the master Dimension Table and
    a per-Group sub-table — plus reconciling the pre-existing D20 duplicate, none of which this
    ticket's own scope or acceptance criteria call for), and a partial fix (adding only a D26 row
    while leaving D19/D21-D25 and the D20 duplicate unaddressed) would create a *third*,
    differently-inconsistent state rather than resolving the inconsistency. Following the existing
    stale precedent (the same choice implicitly made by D21 through D25, none of which appear in
    the master index either) keeps this ticket's blast radius to its own stated scope. This
    should be stated explicitly as a known, disclosed limitation in the new D26 doc's own text
    (e.g., a one-line note: "Not reflected in docs/audits/audit_dimensions.md's master index,
    which has been stale since before D19 and is out of scope for this ticket to repair") rather
    than silently added to a document already known to be incomplete. A dedicated follow-up
    documentation-hygiene ticket for `audit_dimensions.md` itself would be the correct place to
    fix all of D19/D20-duplicate/D21-D26 in one consistent pass.
- **`docs/visual_quality/` naming (ticket's own explicit "TBD" open item):** no existing
  convention constrains the per-file names beyond mirroring the three SimQ files' *roles*. SimQ's
  own files are named `quality_scoring_contract.md` / `current_state.md` / `audit_workflow.md`
  (not prefixed with `simq_` or `simulation_quality_`, since the *directory* `simulation_quality/`
  already scopes them). The parallel, most consistent choice is
  `docs/visual_quality/scoring_contract.md` / `current_state.md` / `audit_workflow.md` — same
  bare names, since `visual_quality/` is the equivalent scoping directory. This investigation
  used those three names throughout; the planner should confirm or override before implementation.
- **Registry-allowlist claim — confirmed, not just trusted:** `python3 tools/layer_registry.py
  list` confirms `world` is a registered layer (2026-07-18, "World generation, worldbuilding,
  region/biome content" — matches every one of the 8 prerequisite tickets' own `layer: world`).
  `python3 tools/tag_registry.py list` confirms `rendering` (registered 2026-08-20,
  subsystem-topic) and `visualization` (registered 2026-08-20, subsystem-topic) both exist, plus
  `simulation-quality` (registered 2026-07-06, subsystem-topic — this ticket's own frontmatter
  already uses it) and `documentation` (registered 2026-07-06, meta-process). No new
  layer/tag registration is required.
- **Important distinction confirmed:** `tools/validate_frontmatter.py`'s `_validate_doc()` (the
  function that applies to every plain `docs/**/*.md` file, as opposed to `_validate_ticket()`/
  `_validate_artifact()`) requires only `status`/`layer`/`authority`/`audience` — it does **not**
  call `_check_tags()`, so a generic doc's `tags:` field, if present, is not registry-checked by
  `validate_frontmatter.py` the way a ticket's or artifact's tags are. Including registry-valid
  tags on the new docs is still good practice (matches every existing precedent doc, which all
  carry a `tags:` list) but is not what AC #3 ("registry-allowlisted layer/tags") is gate-checked
  against for the `docs/visual_quality/*.md`/`docs/audits/D26_*.md` files themselves — it is
  gate-checked for the ticket's own frontmatter, which is a `ticket` content-type and does go
  through `_check_tags()`.
- **`config/rendering/` naming precedent for the calibration report:** the aggregate report's
  default output path baked into `calibrate_rendering.py`
  (`config/rendering/calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION.json`) does not
  currently exist on disk. The new current-state-equivalent doc should describe this as "the tool
  exists and is tested; no aggregate report has been generated/committed yet" rather than
  asserting specific aggregate numbers that cannot be verified from any file actually present.

## Anti-Drift Hazards

- **Do not re-derive or "improve" any numeric anchor while writing the docs.** The three
  anchors this ticket must cite (density CV 0.6478017242079448 / 0.6782405727873148, TVD
  0.23161981243456373, SimQ threshold ladder S=2.0/A=0.5/B=0.0/C=-0.5/D=-1.0) are already
  verified against real running code by the prerequisite tickets and by direct re-read of
  `density.py`/`variants.py`/`grade_thresholds.toml` in this investigation. Copy them verbatim;
  do not round, do not recompute.
- **Do not present the illustrative `grade_thresholds.toml` values as calibrated.** The single
  easiest inaccuracy this ticket could introduce is writing a current-state doc that implies
  `TCK-20260821-VISUAL-QUALITY-CALIBRATION` finished calibrating the actual threshold numbers —
  it did not; it built and tested the *tooling* to do so, and produced descriptive statistics
  only, never written into `grade_thresholds.toml`. This is explicitly disclosed in the config
  file's own comments and the calibration script's own `validation_summary` field — the new docs
  must preserve that disclosure, not soften it.
  Softening this into "the system is calibrated" would misrepresent the documented reality
  and would itself become a doc/code parity gap.
- **Do not invent a formal multi-phase `/visual-quality-audit` workflow that was never built.**
  `docs/simulation_quality/audit_workflow.md` documents a real 7-phase `.claude/workflows/
  simq-audit.js` orchestration. No equivalent workflow file exists for visual-quality. The new
  audit_workflow.md-equivalent must describe the two real, simpler entry points
  (`tools/calibrate_rendering.py`, and dispatching `world-render-reviewer` over a `Tier1Digest`)
  — mirroring SimQ's document *shape* (What this replaces / how to run it / Do-not list) without
  fabricating a pipeline this batch never built.
- **Do not silently repair `audit_dimensions.md`'s stale index as a side effect.** This is an
  explicit, ticket-flagged open decision (Scope item 4); making the edit without surfacing it as
  a deliberate choice (with the disclosed reasoning above) would be exactly the kind of
  unstated/undocumented decision CLAUDE.md's Definition of Done forbids ("No important decision
  is undocumented").
- **Do not add `docs/visual_quality/` to `tests/docs/test_doc_path_existence.py`'s scope as a
  drive-by change.** That test's `SCOPE_DIRS` is currently `("docs/engine", "docs/architecture",
  "docs/performance")` — it does not even cover `docs/simulation_quality/`, the very precedent
  this ticket mirrors. Adding `docs/visual_quality/` while `docs/simulation_quality/` stays
  uncovered would be an inconsistent, unrequested scope expansion (ticket's own Out of Scope
  explicitly marks this "worth deciding, not required") — see Test Plan for the concrete
  recommendation.
- **Do not re-verify D26 only once.** The ticket's own Acceptance Criteria requires re-confirming
  D26 "at implementation time (not just trusted from prior investigation)" — this investigation's
  own re-check is a third independent confirmation (after proposal-time and epic-doc-time), and
  the plan/implementation phases must still re-run the `docs/audits/D*.md` listing themselves
  rather than trusting this document's timestamp.
