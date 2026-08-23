---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-GRADE-SCORER
artifact_type: investigation
tags: [visualization, simulation-quality, world]
---

# Investigation — TCK-20260821-VISUAL-GRADE-SCORER

## Current Behavior

**No grade-band scoring code exists in `src/rendering/` today.** Confirmed by reading all four
shipped sibling modules in full — `connectivity.py`, `density.py`, `shape.py`, `variants.py` — each
returns only raw structural facts (frozen dataclasses or primitive floats/ints), and each module's
own docstring explicitly disclaims grading: `shape.py` and `variants.py` both state verbatim "This
module returns raw structural facts only ... never a grade/S-A-B-C-D-F band ... and is not a
`src.simulation_quality.scorers.base.PillarScorer` subclass; it does not import
`src.simulation_quality.*` or `src.observability.events` (TCK-20260821-VISUAL-GRADE-SCORER and
TCK-20260821-VISUAL-QUALITY-CALIBRATION own scoring/grading and threshold calibration,
respectively)." This ticket is genuinely the first to consume these outputs rather than produce a
raw-metric one, and is named directly in three of the four sibling docstrings as the intended
consumer — confirming the batch's own design intent, not just this ticket's own framing.

### The four inputs available (read in full, exact shapes)

- **`src/rendering/connectivity.py::analyze_connectivity(terrain, blocked_tiles) -> ConnectivityResult`**
  — `walkable_count: int`, `component_count: int`, `component_sizes: list[int]` (sorted descending),
  `percent_reachable: float` (0-100, largest-component share of walkable tiles). Walkability = exactly
  the first two `LegalityServiceV2.verify_occupancy` checks (`terrain != "WALL"` and not in
  `blocked_tiles`).
- **`src/rendering/density.py::compute_density_cv(entities) -> DensityResult`** — `cv: float`
  (population-stdev / mean of per-active-entity nearest-neighbor Euclidean distance; `0.0` if
  `entity_count < 2`), `entity_count: int`, `nn_distances: list[float]`. Also
  `compute_terrain_histogram(terrain) -> dict[str, int]` (raw per-type tile counts, reused by
  `variants.py`).
- **`src/rendering/shape.py::connected_components(terrain, min_size=20, excluded_types={"PLAIN","ROAD"}) -> list[ShapeComponent]`**
  — each `ShapeComponent` has `terrain_type: str`, `tiles: frozenset[tuple[int,int]]`, `size: int`,
  `bbox: tuple[int,int,int,int]`, `fill_ratio: float` (tiles / bbox area, per connected component, not
  per terrain-type aggregate — the fixed pre-existing bug). Also `detect_rotation_match(a, b) -> bool`
  for stamped-rectangle repetition detection between two components.
- **`src/rendering/variants.py`** — `total_variation_distance(h1, h2) -> float` (0-1, 0.5·Σ|proportion
  diffs| over normalized histograms — needs `normalize_histogram` first), `compute_trail_activity
  (unique_tiles_visited, ticks_sampled) -> float` (unique tiles / ticks, zero-guarded),
  `select_trail_entity(world_id, seed, entities) -> int` (deterministic sha256-based single-entity
  pick, raises `ValueError` if no active entities). `normalize_histogram(raw) -> dict[str, float]`.

None of these four modules import `AuthoritativeState` directly — callers extract
`state.terrain`/`state.blocked_tiles`/`state.entities` (confirmed on `src/core/state.py:1091-1138`:
`seed: int`, `entities: Dict[int, EntityState]`, `terrain: Dict[tuple[int,int], str]`,
`blocked_tiles: set[tuple[int,int]]`, all on the frozen `AuthoritativeState` dataclass) and pass
primitives in. This ticket's own module should follow the same calling convention — it must not take
an `AuthoritativeState` parameter directly, matching the sibling pattern.

## SimQ's Real Combination/Grading Mechanism (read in full: `pillars.py`, `weights.py`,
`score_record.py`, `pillar_accumulator.py`, `quality_report.py`, `scorers/combat.py`,
`docs/simulation_quality/quality_scoring_contract.md`)

**The exact reused threshold table is confirmed accurate.** Both `config/simulation_quality/
grade_thresholds.yaml` and the hardcoded fallback `GRADE_THRESHOLDS` in `src/simulation_quality/
pillars.py:85-91` read: `S: 2.0, A: 0.5, B: 0.0, C: -0.5, D: -1.0`. Grade assignment
(`src/simulation_quality/quality_report.py::_assign_grade`, lines 72-83) is a strict descending
`normalized_score > threshold` ladder: `S` if `> 2.0`, `A` if `> 0.5`, `B` if `> 0.0`, `C` if `> -0.5`,
`D` if `> -1.0`, else `F`. This exactly matches the ticket's cited values — no discrepancy found.

**SimQ's combination step, precisely, is a two-stage linear/additive cascade — the ticket's "unlike
SimQ's linear cascade" characterization is accurate, and here is the concrete mechanism it contrasts
with:**

1. **Per-event delta accumulation (rule level).** Every scorer (e.g. `CombatScorer.score()`,
   `src/simulation_quality/scorers/combat.py`) is a chain of `if event_type == X: return
   ScoreRecord(delta=weights["fixed_key"], ...)` branches. Every rule fires a **fixed-magnitude**
   delta (e.g. `combat_active: +2`, `attrition: -1`) drawn straight from
   `config/simulation_quality/scoring_weights.yaml` — never a gradient/graduated value computed from
   how far a raw metric sits inside some range. There is no "healthy band" concept anywhere in SimQ's
   rule vocabulary: every signal in the `quality_scoring_contract.md` §5 tables (all 10 pillars) is a
   binary "this discrete event happened → apply this fixed delta," monotonic in event count (more
   good events strictly raises the score, more bad events strictly lowers it, with no upper-extreme
   penalty for "too much of a good thing").
2. **Time-normalization (pillar level).** `PillarAccumulator.add()` (pillar_accumulator.py:43-58) sums
   deltas into `raw_score` (plain running total) and tracks `last_event_tick`.
   `QualityReportBuilder.build()` (quality_report.py:88-132) then computes `normalized_score =
   raw_score / effective_denominator`, where `effective_denominator = max(floor_tick, last_event_tick)`
   and `floor_tick = max(1, current_tick // 4)` — a straight division, not a shaped function.
3. **Cross-pillar combination (report level).** `overall_score = Σ(normalized_score_i × pillar_weight_i)
   / Σ(pillar_weight_i)` (quality_report.py:119-122; documented identically in `quality_scoring_
   contract.md` §4.6) — a plain weighted arithmetic mean, default weight 1.0 for every pillar.

**This substantiates the ticket's design claim precisely:** SimQ's combination mechanism (sum deltas →
divide by time → weighted-average across pillars) is linear end-to-end, and its rule vocabulary is
monotonic-only (no rule anywhere produces a positive delta in a middle range and a negative delta at
both extremes of the same underlying value). A genuinely new combination/rule-shape design is required
for this ticket's non-monotonic healthy-band soft rules — SimQ's own cascade is not reusable in spirit
for that specific mechanism, only its **grade-threshold vocabulary and numeric boundaries** are reused
(exactly what the ticket scopes reuse to). The **time-normalization** and **weighted-average
combination** patterns (steps 2-3) *are* reusable in spirit for the "combine N hard/soft rule deltas
into one normalized score" step this ticket must design, since nothing about them is specific to
event-stream input — a hard/soft rule delta is structurally the same "signed float, needs combining"
shape as a `ScoreRecord.delta`.

**Concrete illustrative rules derivable from the four real modules' outputs** (design examples only —
the ticket's AC does not mandate exact rule content, but a generic mechanism needs worked examples to
validate its shape against):

- *Hard rule (binary fact) candidates:*
  - `component_count == 1` (fully connected map) → pass/fail fact from `ConnectivityResult`.
  - `entity_count >= 2` (density metric meaningful at all) → pass/fail fact from `DensityResult`.
  - `fill_ratio >= some_min` per `ShapeComponent` (not a degenerate sliver shape).
- *Soft rule (gradient, healthy-band, non-monotonic) candidates:*
  - `ConnectivityResult.percent_reachable` — healthy near 100%, but a soft rule over `fill_ratio` or
    `cv` is the better illustration of genuine non-monotonicity:
  - `DensityResult.cv` — too low (near 0) means uniform/grid-like, artificial-looking entity placement;
    too high means degenerate clustering/isolation; a healthy band sits in the middle (e.g. the real
    observed `~0.648`/`~0.678` corpus values from `density.py`'s own docstring evidence suggest the
    healthy band is somewhere around that range, though this ticket does not calibrate the exact
    numbers — that is `TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s scope).
  - `ShapeComponent.fill_ratio` — too low (near 0) means scattered noise; too high (near 1.0,
    perfect-rectangle) means an unnaturally regular stamped shape; a healthy middle band reads as
    "organic." This is the exact "Biome fill-ratio within a healthy band (neither near-perfect-
    rectangle nor scattered-noise)" signal named in `experiments/spatial_rendering/PROPOSAL.md:149`.
  - `total_variation_distance` between seeds/specs — too low means no real variety; too high might mean
    incoherent/broken variant weighting.
- *Multi-seed averaging:* combine N per-seed scores for one world spec into one arithmetic mean.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter or `docs/engine/` contract governs rendering, visualization, or quality
grading — confirmed by the four shipped siblings' own investigation docs (none cite a Mechanics Bible
chapter) and by `docs/plans/world_rendering/idea_world_render_validation.md` and
`experiments/spatial_rendering/PROPOSAL.md §5a`, both of which frame this whole family as a SimQ
*sibling*, not a simulation law or pillar. The only real constraint is fidelity to the reused SimQ
grade-threshold vocabulary (§4.5 of `quality_scoring_contract.md`) and to the architectural-
independence boundary the ticket's Out of Scope states explicitly (no `PillarScorer` subclass, no
`ObservabilityEventEnvelope`/`QualityHub`/`PillarAccumulator`/`ScoringContext` import, no new
`PillarId`). `docs/testing/test_taxonomy.md` (already cited by all four sibling investigations):
metric/scoring-correctness tests are ordinary `tests/unit/` tests, no `tests/parity/` marker required.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: this ticket's new grade-band scoring/combination
  mechanism is genuinely new, non-mechanics-bible capability, following the exact precedent the four
  shipped siblings set (`INFRA-370` connectivity, `INFRA-371` density, `INFRA-372` shape, `INFRA-373`
  variants — all four confirmed present, `status: verified`, `priority: P2`). Next available ID:
  `INFRA-374`. See "Parity Ledger Overlap" below for the full reasoning on why this is required
  despite `SIMQ-CALIBRATED-001` already existing for SimQ's own threshold table.
Two docs were considered and explicitly excluded (neither requires an update, so neither is
listed as a bullet path above — recorded here only as prose so this section's parsed path list
stays limited to the one doc genuinely required):

The world-render-validation idea doc (path: plans/world_rendering/idea_world_render_validation.md,
under docs/) is not required, deliberately, matching all four prior siblings' identical judgment
call: `tickets/todos/world-rendering-core/SEQUENCE.md` explicitly assigns "the finished system's
real implemented contract" documentation to the last ticket in the batch,
`TCK-20260821-VISUAL-QUALITY-DOCS`. Updating it here would be premature against a system three
further tickets (`VISUAL-AGENT-REVIEW`, `VISUAL-QUALITY-CALIBRATION`, `VISUAL-QUALITY-DOCS`) are
still going to shape.

The quality-scoring contract doc (path: simulation_quality/quality_scoring_contract.md, under
docs/) is not required. It documents SimQ's own scoring model; this ticket builds an
architecturally-independent sibling and must not modify SimQ's own contract doc — doing so would
blur the independence boundary the ticket's Out of Scope establishes. If a cross-reference from
that doc to the sibling system is ever wanted, it belongs to the doc-authoring ticket
(`VISUAL-QUALITY-DOCS`), not here.

## Parity Ledger Overlap

**Correction to the ticket's own Assumptions/Open Questions premise, found by directly grepping
`docs/parity_ledger/*.yaml` for `grade_thresholds`/threshold values, not assumed:** SimQ's own grading
system is **not** parity-ledger-exempt. Two real entries exist:

- **`SIMQ-CALIBRATED-001`** (`docs/parity_ledger/infrastructure.yaml`, `status: verified`,
  `priority: P1`) — covers the grade-threshold *values themselves*
  (`grade_thresholds.yaml`: S=2.0 A=0.5 B=0.0 C=-0.5 D=-1.0) and their calibration status per pillar.
- **`INFRA-255`** (`docs/parity_ledger/infrastructure.yaml`, `status: verified`, `priority: P1`) —
  covers the `normalized_score` combination formula (`floor_tick`/`last_event_tick` divisor logic in
  `QualityReportBuilder.build`), with `COMB-293` in `combat_movement.yaml` as a secondary reference to
  the same entry.

So the real open question this ticket must answer is **not** "does SimQ's grading have any parity
entry" (it does, twice over) but **"does a new, architecturally-independent sibling system that reuses
the same numeric threshold values by copying them into its own config — not by importing or
referencing SimQ's config — need its own entry, distinct from `SIMQ-CALIBRATED-001`."** The answer is
**yes**, for the same reason the four upstream metric siblings each added their own entry rather than
relying on `SIMQ-CALIBRATED-001`'s or each other's: this is new, real, testable capability
(`docs/parity_ledger/*.yaml`'s own purpose, per `schema.json` and CLAUDE.md's Authoritative Mechanics
Rule — "If no entry exists, add one" when a behavior changes/is added) living in a different module
with its own independent grade-assignment code path (a new `_assign_grade`-equivalent function over
`config/rendering/*.yaml` or similar, not `config/simulation_quality/grade_thresholds.yaml`). Reusing
the same numbers does not make it the same behavior for parity-tracking purposes — `SIMQ-CALIBRATED-001`
tracks SimQ's own pillars' empirical calibration status against those numbers; this ticket's own grade
assignment over geometry-derived scores is a structurally distinct code path that happens to share a
threshold table by value. Recommend a new entry, **`INFRA-374`**, `priority: P2` (matching all four
upstream siblings — this is report-only, never CI-gated, per the ticket's own Out of Scope), text
along the lines of: "Rendering-quality grade-band scorer assigns S/A/B/C/D/F using SimQ's exact
threshold values (S=2.0/A=0.5/B=0.0/C=-0.5/D=-1.0), sourced from its own config file (not imported from
`config/simulation_quality/`), combining hard+soft rule deltas via [the mechanism this ticket
designs] before assignment."

**A real design/maintenance risk this creates, worth flagging explicitly (not a blocker):** because
the two systems are deliberately architecturally independent, the threshold values are **duplicated by
value across two config files**, not shared by reference. If `SIMQ-CALIBRATED-001` is ever
recalibrated (its own text says these are still "initial estimates" for most pillars), this sibling's
config will silently drift out of sync unless someone remembers to update both. This is an accepted
cost of the independence requirement (no shared import), not something this ticket should try to
solve architecturally (e.g. no shared "grade thresholds" library module — that would reintroduce
coupling the ticket's Out of Scope forbids). Recommend the new module's config file docstring/header
comment note the SimQ origin and the "keep in sync manually, no code coupling" caveat, mirroring how
`grade_thresholds.yaml`'s own header documents its calibration history.

No P0 parity entries anywhere are touched by this ticket's scope.

## Prior Work

- **All four shipped siblings' `investigation.md`/`plan.md`/`test_plan.md`**
  (`stored_artifacts/TCK-20260821-VISUAL-{CONNECTIVITY,DENSITY,SHAPE,VARIANTS}-METRIC/`) — read in
  full or in relevant part. Established: frozen-`@dataclass` result types, pure functions over
  primitive `terrain`/`blocked_tiles`/`entities` dicts (never `AuthoritativeState` directly), the
  "cite `PROPOSAL.md` line range in the module docstring" convention, the `INFRA-37x` parity-ledger-ID
  sequencing this ticket continues (next: `INFRA-374`), the `tests/unit/rendering/test_<module>.py`
  naming convention, and the SimQ-independence AST-walk guard pattern (`test_<module>_module_does_not_
  subclass_pillar_scorer_or_import_simq_event_pipeline`, present in `test_density.py`/`test_shape.py`,
  confirmed absent from `test_connectivity.py` — flagged as a real gap in the sibling pattern by
  `VARIANTS-METRIC`'s own investigation, not something for this ticket to copy uncritically).
- **`tests/architecture/test_rendering_zero_new_dependency_guard.py`** (read in full) — a package-wide
  static AST guard: every `.py` file under `src/rendering/` must import only stdlib or `src.*`
  modules. This is a **generic** third-party-dependency guard, not SimQ-specific — a bare `import
  src.simulation_quality.pillars` would technically pass this guard's `_is_allowed()` check (top-level
  module is `"src"`), so this ticket's own SimQ-independence requirement needs the same **per-module,
  more targeted** AST-walk test the density/shape siblings added locally in their own test files
  (checking literally for `"simulation_quality"` and `"observability.events"` substrings in import
  names, and for `PillarScorer` in any class's base list) — the package-wide guard alone is
  insufficient to catch this ticket's specific Out-of-Scope violation.
- **`tools/calibrate_simq.py`** — real precedent for multi-seed sweeping (`--seed` CLI flag, one
  seed per invocation, results written to `data/calibration/{name}_seed{seed}_{ticks}t/`). No existing
  code in the repo averages multiple already-computed scores across seeds for one spec — this ticket's
  multi-seed averaging function is new, not a port.
- **`VARIANTS-METRIC`'s "THE CRITICAL FINDING" section** (its own `investigation.md`, read in full) —
  directly relevant to this ticket's multi-seed averaging design, see Risks below.

## Risks and Open Questions

- **Module/config placement is not yet decided — no existing sibling to copy exactly, and this
  ticket's own scope is larger than any single sibling's.** Two real options, following the same
  reasoning frame the connectivity sibling's investigation used for its own placement decision:
  - (a) A single new file, `src/rendering/grading.py`, alongside the four flat sibling modules. Matches
    the established flat-file convention exactly (all four existing metric modules are single files,
    no subpackages anywhere in `src/rendering/` yet).
  - (b) A new subpackage, e.g. `src/rendering/scoring/` (with `hard_rules.py`, `soft_rules.py`,
    `combine.py`, `grade.py`, `__init__.py` or similar split). Justified if the combination mechanism
    this ticket must design (hard rules + non-monotonic soft rules + a genuinely new combination step +
    multi-seed averaging + grade assignment) is judged too large for one flat file to stay readable —
    a materially larger surface than any of the four ~60-160-line sibling modules.

  **Recommendation for the planner: start with (a), a single `src/rendering/grading.py` file**, unless
  the plan's actual rule count/combination logic genuinely exceeds what one file can hold readably
  (a soft judgment call the planner is better positioned to make once the exact rule set is drafted).
  Reasons to prefer (a) as the default: it matches the sibling package's own established convention
  exactly (one file per bounded concern); nothing in the ticket's scope description requires physical
  separation of hard/soft/combination/averaging/grading — those are logical sections within one module,
  not independently reusable units; and a subpackage introduces `__init__.py` re-export surface area
  the four siblings deliberately don't have. If the planner does choose (b), the existing per-module
  AST-walk guards (SimQ-independence, image-dependency) would need to walk the whole subpackage
  directory rather than one file — a mechanical adjustment, not a blocker either way.

  **Config file placement follows the same shape**: a new `config/rendering/grade_thresholds.yaml` (or
  similar), mirroring `config/simulation_quality/grade_thresholds.yaml`'s own location pattern
  one level down from `config/`, rather than reusing that exact path (which belongs to SimQ). No
  `config/rendering/` directory exists yet — this ticket would be the first to create it, matching how
  `TCK-20260821-WORLD-RENDER-CORE`/the four metric siblings did not need any config at all (pure
  functions with no tunable parameters), so there is no existing `config/rendering/` precedent to
  match against, only the cross-subsystem `config/simulation_quality/` shape to mirror.

- **The hard+soft → single-normalized-score combination step has no existing precedent to port,
  confirmed above** — SimQ's own combination (sum deltas → divide by time → weighted-average pillars)
  is linear/additive throughout and never expresses a healthy-band, non-monotonic shape at the
  individual-rule level. This is real, in-ticket design work, not a port. The planner should design
  this as (illustratively, not prescriptively): hard rules contribute pass/fail-derived deltas (e.g.
  fixed penalty on fail, 0 on pass — hard rules are binary facts per the ticket's own Scope wording, so
  they do not need a "healthy band," only soft rules do); soft rules contribute a healthy-band-shaped
  delta (e.g. a triangular or trapezoidal function of the raw metric value, positive inside the healthy
  range, negative at both the low and high extreme, by construction non-monotonic in the raw metric);
  all deltas sum (mirroring SimQ's own additive combination, which is a reasonable, precedented shape
  to reuse for *this* narrow step even though the per-rule shape differs) into one combined score,
  which is then graded via the reused threshold table. This needs explicit unit tests proving the
  non-monotonicity (AC #2) since it is the one genuinely novel piece of math in the whole ticket.

- **Multi-seed averaging's testable surface is thinner than the mechanism itself, and the VARIANTS
  sibling's finding materially affects how "no-op" this framing should be treated.** `VARIANTS-METRIC`'s
  investigation found that `sandbox_world`'s `wolf_den`/`near_forest` regions **do** carry real
  `terrain_variants` and **do** produce genuinely different per-seed terrain histograms once the stale
  `resolved/world.resolved.yaml` cache is bypassed — the seed-invariance observed today via the normal
  `WorldRepository.load_world()` path is an artifact of that stale cache, not evidence the underlying
  mechanism is inert. **This means the ticket's "currently a no-op given seed-invariant terrain" framing
  is accurate only for the normal on-disk load path as it stands today, and only for worlds/modules that
  never declare `terrain_variants` at all (`dungeon_crawl`, robustly and structurally, confirmed by
  `VARIANTS-METRIC`) — it is not a durable architectural fact for `sandbox_world`, and could silently
  stop being true the moment someone runs `make world-resolve WORLD=sandbox_world` (or any of the other
  8 downstream compositions referencing `wolf_den_near_forest`) without anyone touching this ticket's
  own code.** This does not change this ticket's AC (N=1 identity is still the only testable behavior
  given the current on-disk state), but the function signature must genuinely generalize to N>1 — e.g.
  `average_scores(per_seed_scores: list[float]) -> float` (or equivalent) — not special-cased to assume
  N is always 1, and the test plan should test N>1 explicitly with synthetic multi-value input even
  though no real corpus world can produce N>1 *through the normal load path* today.

- **`config/simulation_quality/scoring_weights.yaml`'s data-driven-config discipline (§4.8 of the
  contract doc) is a strong precedent worth following, even though this ticket's Out of Scope forbids
  importing SimQ's actual `ScoringWeights`/Pydantic model.** The planner should still choose to store
  rule deltas/healthy-band boundaries/grade thresholds in a config file per this ticket's own AC #1
  ("sourced from a config file, never hardcoded in scorer code") — this can and should be done with
  plain `yaml.safe_load()` + a small stdlib-only frozen-dataclass loader (matching the pure-function/
  frozen-dataclass sibling pattern), not by reusing `pydantic.BaseModel`/`ScoringWeights` machinery,
  which would both violate the stdlib-only architectural constraint the other four siblings' guard test
  enforces and blur the independence boundary.

- **`percent_reachable`'s definition ambiguity (flagged, unresolved, in `CONNECTIVITY-METRIC`'s own
  investigation as a question for its own planner) is now this ticket's problem too**, since this
  ticket's hard/soft rules will likely read `ConnectivityResult.percent_reachable` as an input. Confirm
  in `plan.md` that the shipped `connectivity.py` implementation's actual chosen definition
  (`component_sizes[0] / walkable_count * 100.0` — largest-component-relative, confirmed by reading the
  real shipped code, not the open question from investigation time) is the one this ticket's rules
  should be written against — it is resolved in the merged code even though the connectivity ticket's
  own investigation flagged it as open at investigation time.

## Anti-Drift Hazards

- **Do not import anything from `src.simulation_quality.*` or `src.observability.events`, anywhere in
  the new module(s) or config loader.** This is the ticket's own explicit Out of Scope and AC #4. Model
  the AST-walk guard test on `test_density.py`/`test_shape.py`'s existing
  `test_<module>_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` pattern, adapted
  to this module's own name(s).
- **Do not register a new `PillarId`** — `src/simulation_quality/pillars.py`'s `PillarId` enum must not
  gain a new member for this system. There is no reason implementation would touch that file at all;
  flagging only because AC #4 states it explicitly.
- **Do not make hard rules non-monotonic and do not make soft rules monotonic** — the ticket's AC #1/#2
  distinction is a hard architectural line: hard rules are binary pass/fail facts (Scope wording), soft
  rules are the ones requiring the healthy-band non-monotonic shape (AC #2). Conflating the two designs
  (e.g. giving a hard rule a graduated delta, or giving a soft rule a monotonic delta) would fail AC #2
  even if the code technically runs.
- **Do not hardcode the S/A/B/C/D thresholds inline anywhere in scorer/combination code** — AC #1
  requires config-file sourcing, mirroring SimQ's own §4.8 data-driven-scoring discipline
  ("Scoring deltas, grade thresholds ... are stored in config files — not hardcoded in scorer Python
  code"), even though this ticket's config loader must be a fresh, stdlib-only implementation, not a
  reuse of `ScoringWeights`.
- **Do not special-case the multi-seed averaging function around N=1.** AC #3 requires the function to
  "naturally generalize to N>1" — a function that only accepts a single score (or that branches
  specially on `len(scores) == 1`) would technically satisfy today's only-real-testable case but
  violate the architectural intent (this is called out explicitly in the ticket's own Scope, and is
  exactly the kind of narrow-scope-avoidance CLAUDE.md's Uncertainty Rule warns against — "do not
  collapse investigation into exact coordinates too early" applies equally to over-narrowing an
  implementation to today's only observable case).
- **Do not silently skip the `INFRA-374` parity entry based on a mistaken belief that SimQ's own
  grading is parity-exempt** — it is not (see "Parity Ledger Overlap" above); this ticket's AC #5
  requires an explicit, evidenced confirmation either way, and the evidence gathered here points
  toward "needs its own entry," not "exempt."
- **Do not silently CI-gate this system.** Out of Scope explicitly states "report-only, never
  CI-gated" — matching all four upstream siblings' identical constraint. Do not add this to any
  regression-baseline/gate script.
- **Do not couple to the renderer or image pipeline.** Mirror the density/shape siblings' own
  `test_<module>_module_has_zero_image_or_render_dependency` guard (checking for `png_writer`,
  `rendering.render`, `rendering.incremental`, `PIL`/`Pillow` substrings) — this module consumes the
  four metric modules' structured outputs, never pixels.
- **Do not mutate any input.** All four metric modules' outputs (`ConnectivityResult`, `DensityResult`,
  `ShapeComponent`, and variants.py's primitives) are frozen dataclasses or plain immutable-by-
  convention primitives; the grading module must only read them, matching the "read-only logic did not
  mutate live state" architecture-test rule (CLAUDE.md Testing Rule).
