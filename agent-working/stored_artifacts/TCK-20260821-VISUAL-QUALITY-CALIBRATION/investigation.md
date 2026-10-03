---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-CALIBRATION
artifact_type: investigation
tags: [visualization, simulation-quality, calibration, world]
---

# Investigation — TCK-20260821-VISUAL-QUALITY-CALIBRATION

## Search-tooling note (read first)

`mcp__knowledge-search__search_docs` was unavailable this session (persistent network block,
confirmed by the dispatching agent before this investigation started). `graphify query` was run
and returned only generic SimQ structural nodes with nothing specific to this ticket's actual
domain (a `tools/` calibration script for the rendering metric family, not a `src/` module the
graph has indexed relationships for). Per CLAUDE.md's Hard Rules this is a documented exception,
not a silent skip — both required tools were invoked first and neither produced usable results,
so the investigation proceeded via direct Read/Grep/Bash against the real files below, plus one
empirical script (`.venv/bin/python3 -c "..."`) run three times to verify claims rather than trust
paraphrase (results below, not assumed).

## Current Behavior

**No calibration script exists yet for the rendering metric family.** `tools/` contains
`calibrate_simq.py` (SimQ pillars) and no `calibrate_rendering.py` or equivalent — confirmed via
`ls tools/`. `config/rendering/` contains exactly one file, `grade_thresholds.toml`
(`TCK-20260821-VISUAL-GRADE-SCORER`), whose own header states its `[hard_rules.fully_connected]`
and `[soft_rules.fill_ratio_healthy_band]` values are "Illustrative values only, NOT calibrated —
calibration is TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope" (this ticket, named directly).
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-372` entry (shape.py) independently confirms the
same thing from the other direction: "the 0.95 threshold itself is uncalibrated and provisional,
tracked separately (TCK-20260821-VISUAL-QUALITY-CALIBRATION)."

### 1. `tools/calibrate_simq.py` — read in full, the ticket's own cited precedent

**CLI shape** (`argparse`, `main()`): `--ticks` (int, default 100), `--seed` (int, default 42,
**one seed per invocation** — confirmed: a bare `int`, not `nargs="+"` or a list type; sweeping
multiple seeds means multiple separate process invocations, e.g. a shell loop or a Python loop
around `_run_engine()`/equivalent internal functions), `--name` (str, default `"generic"`),
`--entities` (int, default 10), `--profile` (str, optional), `--output` (str, optional override),
`--window-size`/`--loop-threshold` (float, per-run detection-param overrides, not persisted).

**Output artifact location** (confirmed directly, not from memory): `run_tag =
f"{args.name}_seed{args.seed}_{args.ticks}t"`; `cal_dir = args.output or
os.path.join("data", "calibration", run_tag)`. Verified live on disk —
`data/calibration/` contains 20+ real directories in exactly this `{name}_seed{seed}_{ticks}t`
shape (e.g. `urban_political_seed456_500t`, `dungeon_crawl_seed42_1000t`). Each directory holds
`quality_report.json` (via `QualityPersistence.write_report()`, tmp-write-then-`os.rename()`
atomic pattern) and `quality_report.run_health.json` (via the static
`QualityPersistence.write_run_health()`, same atomic pattern, written **before** the integrity
guard's raise so it exists even on a failed run).

**`CalibrationIntegrityError`** (`tools/calibrate_simq.py:33-36`): raised when
`not guard_passed`, where `guard_passed = (dropped_count == 0 and obs_status["mode"] == "NORMAL"
and not survival_triggered)`. Concretely guards against exactly two independent loss mechanisms in
the `Kernel.tick_once()` → `EventRecorder` → replayed-`simulation_events.jsonl` → `QualityHub`
pipeline: **queue-drop** (`BoundedObservabilityQueue` overflow-eviction, `queue.dropped_count > 0`)
and **SURVIVAL-mode event-shed** (`ObservabilityController` entering `SURVIVAL` and bypassing the
queue entirely — SimQ receives nothing while the run *appears* to complete normally). This is the
exact, direct precedent for AC #5's "queue-drop/corruption hard-fail" wording — confirmed via the
parity ledger, not paraphrase: **`INFRA-320`** (`docs/parity_ledger/infrastructure.yaml:7868-7909`,
`priority: P0`, `proof_type: regression`) documents this guard verbatim, with
`test_path: tests/simulation_quality/test_calibrate_simq.py::TestQueueOverflowGuard::...,
TestSurvivalModeGuard::...`. The raise is its own top-level statement, never nested inside
`kernel.shutdown()`'s exception-swallowing `try/except` (a documented anti-pattern-avoidance in the
source comments) — so cleanup always runs but the hard-fail can never be silently caught.

**Threshold-writing is NOT automated by `calibrate_simq.py` today** — a real gap between the
script's own module docstring's aspiration and its actual code, confirmed by reading `main()` in
full: the docstring says "After running all 8 canonical scenarios, analyze `normalized_score`
distributions and update `config/simulation_quality/grade_thresholds.yaml` accordingly," but
`main()` only ever calls `persistence.write_report(report)` — it never opens, computes against, or
writes `grade_thresholds.yaml`. That threshold-recalibration step is a **manual, human/agent
analysis** performed *across* multiple already-written `quality_report.json` files after the fact
(this is exactly what `grade_thresholds.yaml`'s own header documents happened for
`TCK-20260630-SIMQ-RECALIBRATE`: a human read 3 runs' printed pillar breakdowns and hand-verified
the existing thresholds were "proportionally sound," making no edit that time). **This materially
changes what "mirroring `calibrate_simq.py`'s precedent" can honestly mean for this ticket's AC #2**
("Healthy-band values are written to a config file ... by [this ticket's script]") — this ticket's
AC #2 asks for something `calibrate_simq.py` itself has never actually done in code: automating the
raw-output → healthy-band-numbers → config-file-write step. See Risks below; this is a real design
decision for the planner, not a mechanical port.

### 2. `config/simulation_quality/grade_thresholds.yaml`'s exact header format — read in full again

```
# Calibration: 2026-06-30 | TCK-20260630-SIMQ-RECALIBRATE
# World: sandbox_world | Seeds: 42, 137, 999 | Ticks: 200 | Entities: 10
#
# Observed normalized scores per seed (3-run offline replay via calibrate_simq.py):
#   COMBAT:     +0.04, +0.04, +0.46  (2–13 events/run) → grades B
#   ...
#
# Thresholds validated: NARRATIVE correctly lands A, COMBAT correctly lands B.
# No threshold changes required from initial estimates — they are proportionally sound.
S: 2.0
...
```

Exact field set: `Calibration: <date> | <ticket_id>` (line 1); `World: <name> | Seeds: <csv> |
Ticks: <n> | Entities: <n>` (line 2, **singular** "World" — that calibration run covered exactly
one world spec); a blank `#` line; an "Observed ... per seed" prose block, one line per
signal/pillar; a blank `#` line; a "Thresholds validated: ..." closing summary; then the real YAML
keys. **This ticket's own run is multi-world** (Scope: ">=3 seeds", multiple metric families each
touching multiple worlds) — the header's "World:" line does not literally fit a multi-world run.
Faithfully "matching the exact header format" (AC #2's wording) means matching the *field set and
structure* (date+ticket, scope-of-run metadata line, observed-values block, validation-summary
line), pluralizing "World:" → "Worlds:" with a real multi-entry list, which is a deliberate, honest
adaptation of the format, not a deviation from it — flagged explicitly here rather than left
implicit for the planner to notice or miss.

### 3. The four metric modules (`connectivity.py`, `density.py`, `shape.py`, `variants.py`) — read in full — and `grading.py`

Numeric outputs each family produces that a healthy-band soft rule could consume (cross-referenced
against `grading.py`'s `SoftRuleConfig` shape: `low`, `healthy_low`, `healthy_high`, `high`,
`peak_delta`, `min_delta`):

| Family | Function | Candidate calibration target(s) |
|---|---|---|
| Shape | `connected_components(terrain).fill_ratio` (per `ShapeComponent`) | `fill_ratio` — the **one** soft rule config already stubbed in `grade_thresholds.toml` (`soft_rules.fill_ratio_healthy_band`, currently `low=0.0 healthy_low=0.3 healthy_high=0.85 high=1.0`, marked illustrative) |
| Density | `compute_density_cv(entities).cv` | `cv` (nearest-neighbor coefficient of variation) — **no existing soft-rule stub in `grade_thresholds.toml`**; this ticket's output would need to propose a **new** `[soft_rules.density_cv_healthy_band]`-shaped entry |
| Connectivity | `analyze_connectivity(terrain, blocked_tiles)` → `percent_reachable`, `component_count` | `percent_reachable` — `GRADE-SCORER`'s own investigation names this as the illustrative soft-rule candidate (its `hard_rules.fully_connected` binary check already reads `component_count == 1`, so `component_count` itself is more naturally a **hard**-rule fact than a soft-rule healthy band) |
| Variants | `total_variation_distance(h1, h2)`, `compute_trail_activity(unique_tiles_visited, ticks_sampled)` | Both are real candidates; TVD (terrain-histogram diversity) and trail-activity (movement liveliness) are structurally different in what they need to iterate over — see "Trail-activity's real cost" in Risks below |

`grading.py`'s `load_grade_config()` is fully **data-driven**: it iterates
`raw.get("soft_rules", {}).items()` / `raw.get("hard_rules", {}).items()` generically — adding a
brand-new `[soft_rules.density_cv_healthy_band]` (or similarly-named) TOML table requires **zero**
code change to `grading.py` itself. Writing new calibrated healthy-band numbers into
`config/rendering/grade_thresholds.toml` (or a file that later gets merged into it) is therefore a
pure **config-data** change, not a "change to the metric/scoring implementations" this ticket's Out
of Scope forbids — confirmed by reading `load_grade_config`'s loop shape directly, not assumed.

**A real gap in the ticket's own Related Code Areas, worth flagging directly:** the ticket lists
`tools/calibrate_simq.py`, `config/simulation_quality/grade_thresholds.yaml`, and the three
`experiments/spatial_rendering/prototype/render_*.py` files, but omits **`config/rendering/
grade_thresholds.toml`** and **`src/rendering/grading.py`** — the exact production file/module
whose `SoftRuleConfig` shape this ticket's calibration output must be compatible with (AC #2's
"config file" almost certainly means this one, or a sibling of it). Both were read in full for this
investigation; the planner should treat them as load-bearing even though the ticket's own frontmatter
didn't list them.

### 4. Evidence-coverage gap — verified directly, not from memory or paraphrase

Ran `WorldRepository("data/worlds").list_worlds()` directly: **21 real worlds**, not the "18" the
ticket's Assumptions section states (`crowded_frontier, dungeon_crawl, frontier_extended,
frontier_living_world, frontier_marches, generated_frontier_3_42, hero_guild_routing,
highland_traverse, lifecycle_full_coverage_world, quest_dense_frontier, resource_dense_basin,
sandbox_world, simq_routing_test, simq_scale_stress_seed42, swamp_border_world,
unit_faction_tension, unit_information_density, unit_information_source, unit_selfmodel_pilot,
urban_political, wilderness_survival` — 21 entries, `world_index.json` excluded). This matches the
"21 worlds" figure from prior-session memory the dispatching agent cited, **not** the ticket's own
"18-world" Assumptions text — the ticket's own number is stale.

Ran `tests/unit/rendering/test_shape.py::test_corpus_wide_sweep_every_below_threshold_component_is_forest`'s
exact logic directly (`repo.list_worlds()` → `WorldCompiler.compile(spec, seed=42)` →
`connected_components(state.terrain)`, single seed, all worlds): **21/21 worlds compile
successfully, 46 total components, 9 below the 0.95 fill-ratio reference threshold, all 9
confirmed FOREST type** — not "33 components" as the ticket's Assumptions text states. That "33"
(and a companion "26") figure is **explicitly the *historical* number** `test_shape.py`'s own module
docstring names and deliberately does not re-implement: *"Test 11 (the literal historical 26/33
corpus reproduction via a hardcoded 3-world exclusion list) is deliberately NOT implemented here...
Test 10 below asserts the qualitative, corpus-size-independent invariant instead ... which holds
identically regardless of how many worlds `data/worlds/` currently contains."* The ticket's own
Assumptions text re-cites a superseded historical count as if current — **flagged as a stale-number
correction**, not a blocker: Shape's real, current single-seed coverage is **21 worlds / 46
components**, and the qualitative invariant (every sub-threshold component is FOREST) still holds.

Confirmed each sibling's own real-corpus test-file world touch-count directly (`grep` +
read, not estimated):
- **Connectivity**: 1 world (`dungeon_crawl` only, `test_dungeon_crawl_matches_documented_evidence`).
- **Density**: 2 worlds (`sandbox_world`, `dungeon_crawl`).
- **Variants**: 2 worlds (`sandbox_world`, `dungeon_crawl`) for the TVD cross-spec anchor; `dungeon_crawl` alone at 2 seeds (42, 137) for the same-spec/different-seed invariance test.
- **Shape**: all 21 worlds, but **single seed (42) only** — the "1-3 worlds" characterization in the
  ticket's Assumptions applies to Connectivity/Density/Variants; Shape's real gap is different in
  kind (all-worlds but single-seed, not few-worlds).

**What "expand to comparable multi-world coverage" concretely means, given this:** run each of the
four families' real-metric computation across the full (or a deliberately justified representative
subset of the) 21-world `data/worlds/` corpus — mirroring `test_shape.py`'s existing
`repo.list_worlds()` sweep pattern, which is already the right shape to extend — **crossed with
`>=3` seeds per world** (this ticket's own Scope wording), which none of the four families'
existing test suites do today (Shape sweeps all worlds at one seed; the other three sweep 1-3
worlds at one seed, except Variants' seed-invariance test which uses 2 seeds but only checks
equality, not a distribution). The calibration script's job is a **new axis** (multi-seed) crossed
with **breadth already partially proven for one family** (multi-world, Shape only) — not starting
from zero on either axis.

### 5. Seed-variance findings — verified empirically this session, not assumed

Ran the following directly (`.venv/bin/python3 -c ...`, real `WorldRepository`/`WorldCompiler`
calls, seeds 42 and 137, `sandbox_world` and `dungeon_crawl`):

```
sandbox_world  cv42=0.6478  cv137=0.9105  blocked_equal=False  percent_reachable42=100.0  percent_reachable137=100.0  terrain_equal=True
dungeon_crawl  cv42=0.6782  cv137=0.6751  blocked_equal=False  percent_reachable42=100.0  percent_reachable137=100.0  terrain_equal=True
```

This confirms, precisely, which of the four families' calibration inputs are seed-sensitive **under
the real, current, on-disk load path** (`WorldRepository.load_world()`, no cache-bypassing — the
same path every shipped sibling's real-corpus test already uses):

- **Terrain is byte-identical across seeds for both anchor worlds** (`terrain_equal=True`),
  confirming `VARIANTS-METRIC`'s own finding (below) generalizes: **Shape's `fill_ratio`/component
  structure and Variants' `total_variation_distance`** (both pure functions of `terrain`) will be
  **seed-invariant for every world in the corpus today**, not a Shape-specific quirk — this is a
  structural consequence of terrain seed-invariance, and the same "expected, not a bug" framing AC
  #3 requires for Shape applies identically to Variants' TVD half, even though the ticket's own text
  only names Shape. **Recommend the calibration output record this explicitly for both families**,
  not Shape alone — flagged here as a scope extension the planner should make deliberately, not an
  assumption already baked into the ticket text.
- **Density's `cv` genuinely varies by seed** — `sandbox_world`'s `cv` moves from 0.6478 to 0.9105
  between seed 42 and 137, a real, non-trivial difference (entity spawn positions are seed-scoped
  independently of terrain noise-fill). Density calibration across seeds is **not** a no-op; it is
  the one family most likely to produce a genuinely informative multi-seed distribution.
- **Connectivity's `blocked_tiles` input differs by seed** (`blocked_equal=False`, both worlds) even
  though `percent_reachable` happened to stay saturated at 100.0/100.0 for both anchor worlds at
  both seeds tested. This does **not** prove Connectivity is seed-invariant in general — only that
  these two anchor worlds are highly connected regardless of which few tiles get blocked. Other
  worlds in the 21-world corpus (denser/narrower layouts) may show real `percent_reachable` or
  `component_count` variance across seeds; this needs to be checked corpus-wide by the calibration
  script itself, not assumed from two anchor worlds.

**`VARIANTS-METRIC`'s own prior finding** (`stored_artifacts/TCK-20260821-VISUAL-VARIANTS-METRIC/
investigation.md`, read in full), extended rather than re-derived: `sandbox_world`'s (and 8 other
worlds') apparent terrain seed-invariance is an **artifact of a stale `resolved/
world.resolved.yaml` cache** predating `wolf_den_near_forest.yaml`'s `terrain_variants` field
(`TCK-20260821-WOLF-DEN-NOISE-MIGRATION` never regenerated the 9 downstream compositions). Bypassing
that cache **in-memory only** (no file mutation) showed real, non-zero terrain divergence for
`sandbox_world` at different seeds. That investigation's own conclusion — use the real, on-disk
load path as-is, do not bypass the stale cache, and do not silently "fix" it as a side effect of
this work — applies identically here: **this calibration script must use the same real, unmodified
`WorldRepository.load_world()` path every shipped sibling test uses, with no cache-bypassing**,
consistent with `dungeon_crawl` being the durable, structural seed-invariance anchor and
`sandbox_world` being a today-only, cache-staleness-dependent one. No Shape-specific special
handling beyond "record the zero-variance fact explicitly, do not treat it as a run-integrity
failure" is warranted — it is the same corpus-wide terrain-seed-invariance fact `VARIANTS-METRIC`
already established, observed through a second lens.

### 6. Calibration output artifact shape

`calibrate_simq.py` writes, per invocation: `quality_report.json` (via
`QualityPersistence.write_report()`, atomic tmp-then-rename) and
`quality_report.run_health.json` (via the static `QualityPersistence.write_run_health()`, same
atomic pattern, written **before** any integrity-guard raise so it survives a failed run). Both are
plain JSON, no special serialization beyond `dataclass.to_dict()`/`json.dump(..., indent=2)`.

A "quality_report-equivalent artifact per (world, seed)" (AC #1) for this ticket's four metric
families, mirroring that exact atomic-write convention, would reasonably be a single JSON per
`(world, seed)` run directory containing the four families' raw structured outputs (not grades —
grading is `GRADE-SCORER`'s job, already shipped and separate) — e.g. (illustrative field
names, not prescriptive):

```json
{
  "world_id": "sandbox_world", "seed": 42, "ticks": 0,
  "connectivity": {"walkable_count": ..., "component_count": ..., "percent_reachable": ...},
  "density": {"cv": ..., "entity_count": ...},
  "shape": {"components": [{"terrain_type": ..., "size": ..., "fill_ratio": ...}, ...]},
  "variants": {"terrain_histogram": {...}}
}
```

`ticks: 0` deliberately, for the three terrain/entity-position metric families — see the "Trail-
activity's real cost" risk below: `connectivity`/`density`/`shape`/TVD-half-of-`variants` are all
computable from a single `WorldCompiler.compile(spec, seed)` call with **no** `Kernel.tick_once()`
loop at all (confirmed: every real-corpus test for all four families calls `WorldCompiler.compile`
directly, never `kernel.tick_once()`) — this is a materially cheaper operation than
`calibrate_simq.py`'s own engine-driven runs, and does not touch `EventRecorder`/`QualityHub` at
all. Only `compute_trail_activity` (needs entity positions sampled over many ticks) would require
actually ticking a `Kernel`, the same way `render_trail.py`/`calibrate_simq.py` do.

### 7. Module/script placement

Recommend `tools/calibrate_rendering.py` (or a similarly-named sibling under `tools/`, never
`src/rendering/`) — matches `calibrate_simq.py`'s own placement exactly (an operational script, not
library code any test imports as production logic) and keeps it outside
`tests/architecture/test_rendering_zero_new_dependency_guard.py`'s scope (that guard AST-walks
`src/rendering/*.py` specifically; a `tools/` script is not bound by it and, like
`calibrate_simq.py` itself, may import `yaml`/other real project dependencies if needed for reading
config — though see the TOML-writer finding below, no third-party dependency is actually needed
here).

**Test placement**: CI already runs `tests/tools` (job `"API / tools / logging"`,
`.github/workflows/test.yml:135`) and `tests/unit/rendering` (job `"Unit · infra / observability"`,
line 90) as existing jobs — a new `tests/tools/test_calibrate_rendering.py` would be picked up
automatically with **no new CI workflow job needed**, and (unlike putting it under
`tests/simulation_quality/`, SimQ's own dedicated job) correctly signals this script's
architectural independence from SimQ, matching the four metric modules' own "does not import
`src.simulation_quality.*`" discipline.

**TOML-writer finding, real and load-bearing:** Python's stdlib `tomllib` (used by `grading.py`) is
**read-only** — there is no stdlib TOML writer, and `grep`ing `requirements.txt` and all of
`src/`/`tools/` for `tomli_w`/`toml` writer usage returns zero hits. If the calibration script's
output config format needs to be TOML (to stay loadable by `grading.py`'s existing
`load_grade_config()`), it must **hand-format the TOML text** (plain string templating — the
existing `grade_thresholds.toml`'s shape is simple enough: flat `[section]` tables of scalar
floats, no nesting/arrays that would need a real serializer) rather than add a new third-party
dependency. This is a real constraint the planner needs, not an incidental detail.

### 8. CI-gating check — confirmed clean

Grepped `.github/workflows/*.yml` for `calibrate`/`grade_thresholds`/`simulation_quality`: the only
hit is `test.yml:181`, `pytest tests/simulation_quality` — this runs `calibrate_simq.py`'s **own**
unit tests (`test_calibrate_simq.py`, `test_calibrate_world_loading.py`), which test the script's
*guard/CLI logic itself* (e.g. "does the integrity guard actually raise on a forced queue
overflow"), never the calibrated **threshold values** it produces. No workflow anywhere asserts
against `grade_thresholds.yaml`'s numeric contents or gates a build on them. **This is the correct
precedent to mirror, and resolves point 8's question precisely**: this ticket's new script's own
logic (CLI parsing, artifact-writing, the integrity guard) *can and should* have ordinary pytest
coverage that runs in CI (exactly like `calibrate_simq.py`'s does) — that is not "CI-gating
thresholds." What Out of Scope forbids is any test/gate that asserts against the *calibrated
numeric healthy-band values themselves* (e.g. "assert `cv` healthy band is `[0.5, 0.9]`") — no such
test should be added anywhere, and none of `calibrate_simq.py`'s own tests do this for SimQ either
(confirmed by reading `test_calibrate_simq.py` in full: it tests guard behavior with monkeypatched
Kernel state, never asserts on real calibrated numbers).

### 9. Parity ledger representation

`tools/calibrate_simq.py` **is** represented in the parity ledger — not exempt. Grepped
`docs/parity_ledger/*.yaml` for `calibrate_simq`/`CalibrationIntegrityError`: at least
**`INFRA-320`** (`infrastructure.yaml:7868`, `priority: P0`, `proof_type: regression`, the
integrity-guard entry above) directly covers `calibrate_simq.py`'s own tooling behavior, and
several other entries (`INFRA-255`-adjacent, `SIMQ-CALIBRATED-001`, and multiple entries whose
`v2_evidence`/text cite `calibrate_simq.py` as the confirming instrument for unrelated engine fixes)
reference it as evidence, not as the subject. The precedent is therefore: **the calibration
tooling's own real, testable behavior (its integrity guard, specifically) does get a parity entry;
the specific numeric calibration outputs it produces do not** (no entry anywhere asserts "SimQ's
`grade_thresholds.yaml` numbers are `S=2.0 A=0.5 ...` and here is the `test_path` proving it" beyond
`SIMQ-CALIBRATED-001`'s status/evidence tracking, which is about calibration *process* maturity per
pillar, not a numeric regression test).

**Recommendation for this ticket**: yes, the `INFRA-37x` pattern applies, in the same narrow sense
— a new entry (next available ID after `INFRA-375`: **`INFRA-376`**, confirmed by reading the full
current tail of `infrastructure.yaml`) covering this new script's own **run-integrity guard**
behavior (mirroring `INFRA-320`'s shape: what it guards against, how it fails loud, its real
`test_path`), `priority` plausibly `P1` or `P2` (not `P0` — `INFRA-320`'s `P0` reflects that a
silent SimQ-scoring corruption could mislead live gameplay-quality decisions; this ticket's Out of
Scope explicitly forbids any CI-gating/decision-consumption of its output, which is a real,
material difference in blast radius the planner should weigh explicitly rather than copy `P0` by
rote). **Not** a `data/calibration/`-artifact-generation exemption — `calibrate_simq.py` itself
proves artifact-generation tools are not exempt from parity tracking when they have real, testable
guard logic. The calibrated **numeric threshold values** this script writes do not need their own
parity entry (empirical outputs, not asserted-against behavior) — consistent with how
`SIMQ-CALIBRATED-001` tracks calibration-process status, not the numbers as a regression anchor.

### 10. FOREST separate-threshold-band question — confirmed deferred, not addressed here

The ticket's own Out of Scope explicitly excludes "Resolving whether FOREST needs its own separate
threshold band," and `INFRA-372`'s text already frames the 0.95 reference threshold as "uncalibrated
and provisional, tracked separately (`TCK-20260821-VISUAL-QUALITY-CALIBRATION`)" without asserting
FOREST needs a *distinct* band from other terrain types — this investigation does not attempt to
answer that question, consistent with the ticket's explicit scope boundary and CLAUDE.md's
Uncertainty Rule ("do not collapse investigation into exact coordinates too early"). The
calibration script's output should be structured so a FOREST-specific band *could* be added later
(e.g. per-terrain-type breakdown in the raw calibration data, not a single corpus-wide number that
would need to be thrown away) without that being this ticket's own deliverable.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter or `docs/engine/` contract governs this work — same conclusion all
five shipped siblings in this batch already reached and this investigation re-confirms: rendering
metrics and their calibration are non-authoritative, read-only, post-hoc validation tooling, not a
simulation law. The one indirect engine-side interaction is `WorldCompiler.compile()`'s noise-fill
mechanism (`docs/mechanics/06_worldbuilding_foundation.md`'s "Noise-Fill Terrain Law"), which
determines whether a given world's terrain is seed-varying at all — this calibration script's
seed-sweep logic must stay correct regardless of which worlds that law currently affects (see
Seed-variance findings above), not hardcode which worlds are/aren't affected today.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: add `INFRA-376` covering this script's own
  run-integrity guard (mirroring `INFRA-320`'s precedent), `status: verified` once implemented and
  tested, `priority` P1/P2 per the planner's explicit blast-radius judgment (see "Parity Ledger
  Overlap" below — this is the one doc this ticket's own code change genuinely requires).

No other `docs/parity_ledger/*.yaml` entry needs a status change — this ticket adds new calibrated
config **data** and a new tooling script's guard behavior; it does not change any of the four
metric families' formulas or `grading.py`'s combination logic (those entries, `INFRA-370` through
`INFRA-375`, stay `verified` as-is).

Two docs were considered and explicitly excluded, matching every prior sibling's identical judgment
call, recorded here as prose only so the parsed bullet-path list above stays limited to the one doc
genuinely required:

The world-render-validation idea doc (path: `plans/world_rendering/idea_world_render_validation.md`,
under `docs/`) is not required — `SEQUENCE.md` assigns documenting "the finished system's real
implemented contract" to the batch's last ticket, `TCK-20260821-VISUAL-QUALITY-DOCS` (position 9,
depends on this ticket among others per the sequence file, confirmed by reading it directly).
Updating it here would be premature.

The quality-scoring contract doc (`simulation_quality/quality_scoring_contract.md`, under `docs/`)
is not required — it documents SimQ's own scoring model; this ticket's script is an
architecturally-independent sibling tool and must not blur that boundary by editing SimQ's own
contract doc.

**`config/rendering/grade_thresholds.toml`'s own header comment** (not a `docs/` path, so not
listed as a bullet above, but flagged here as real follow-on work either this ticket or a
close-following one must do): once real calibrated numbers exist, that file's header
("Illustrative values only, NOT calibrated — calibration is
`TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s scope") becomes stale and should be updated to point at
this ticket's real calibration output instead of describing it as a future TODO — whether that edit
happens *in* this ticket (if the planner decides to write calibrated values directly into
`grade_thresholds.toml`) or is deferred to a follow-up that merges this ticket's calibration report
into it is exactly the open design question flagged in Risks below.

## Parity Ledger Overlap

- **`INFRA-320`** (`infrastructure.yaml`, `P0`, `proof_type: regression`) — direct precedent for
  this ticket's own integrity guard; not itself modified by this ticket (it covers
  `calibrate_simq.py` specifically), but its shape is the template `INFRA-376` (new) should follow.
- **`INFRA-372`** (shape.py, `P2`) — explicitly names this ticket as the thing that will calibrate
  its "uncalibrated and provisional" 0.95 threshold. This ticket's output should be traceable back
  to `INFRA-372` once real numbers exist (e.g. the calibration output's header/provenance
  referencing which parity entries its numbers are meant to inform), though updating `INFRA-372`'s
  own `status`/`text` is not required by this ticket unless the planner also chooses to write the
  calibrated numbers directly into `grade_thresholds.toml` in the same session (see Risks).
- **`INFRA-374`** (`grading.py`, `P2`) — the grade-band scorer this calibration output is meant to
  feed; not modified by this ticket, but the config-shape contract (`SoftRuleConfig`'s six required
  keys) this ticket's output must be compatible with.
- No **P0** parity entries are touched by this ticket's own new work (`INFRA-320` is `P0` but
  belongs to `calibrate_simq.py`, unmodified here). If the planner scopes `INFRA-376` as `P0`
  (matching `INFRA-320`'s precedent exactly rather than the P1/P2 recommended above), it would
  require a passing `test_path` per CLAUDE.md's Authoritative Mechanics Rule — flagging this
  explicitly since it changes the done-checker's bar.

## Prior Work

- **All five shipped siblings' `investigation.md`/`plan.md`/`test_plan.md`**
  (`stored_artifacts/TCK-20260821-VISUAL-{CONNECTIVITY,DENSITY,SHAPE,VARIANTS,GRADE-SCORER}-METRIC*/`,
  read in full or in the relevant sections cited throughout this document) — established the
  frozen-dataclass/pure-function convention, the `INFRA-37x` parity-ID sequencing, the
  `tests/unit/rendering/test_<module>.py` naming convention, and the SimQ-independence AST-walk
  guard pattern this ticket's own script should mirror in spirit (a `tools/`-appropriate variant,
  not a copy — see Test Plan).
- **`VARIANTS-METRIC`'s "THE CRITICAL FINDING" section** — the direct, load-bearing prior finding
  this investigation built on for point 5 above (terrain seed-invariance is a stale-cache artifact
  for most of the corpus, structural-and-durable only for worlds with zero `terrain_variants`-
  declaring modules like `dungeon_crawl`).
- **`GRADE-SCORER`'s investigation** — established `grading.py`'s exact config-loading contract
  (`SoftRuleConfig`'s six required keys) and flagged the multi-seed-averaging/no-existing-precedent
  gap this ticket's calibration sweep is the first thing to actually produce real multi-seed data
  for.
- **`tools/calibrate_simq.py`** itself, and its parity entry **`INFRA-320`** — the concrete,
  line-level precedent this investigation traced in full (see point 1 and point 9 above), rather
  than trusting the ticket's own paraphrase of it.

## Risks and Open Questions

- **Blocking for the planner: where does the calibration script write its output, relative to
  `config/rendering/grade_thresholds.toml`?** Two real options, not resolved here:
  (a) A **separate** calibration-report file (e.g. `config/rendering/calibration_report_
  {date}.{yaml,toml}` or similar), carrying the provenance header and raw/derived numbers, which a
  human or a later ticket manually reviews and merges into `grade_thresholds.toml`'s
  `[soft_rules.*]`/`[hard_rules.*]` tables — mirrors what `calibrate_simq.py` **actually does today**
  (never auto-writes `grade_thresholds.yaml`, despite its docstring's aspiration; see point 1).
  (b) The calibration script **directly rewrites** `config/rendering/grade_thresholds.toml` in
  place with the newly-computed numbers (preserving/regenerating its existing architectural-
  rationale header comments), matching AC #2's literal wording ("written to a config file... by
  [this ticket's script]") more directly. **Recommendation: (a)**, both because it is the actually-
  proven precedent (not the aspirational docstring `calibrate_simq.py` itself never fulfilled) and
  because directly overwriting a file another already-shipped, already-tested ticket
  (`GRADE-SCORER`) owns and whose header carries hand-written architectural rationale is a higher-
  risk, harder-to-review change than producing a clearly-provenanced report a human/later ticket
  applies deliberately — but this is a real design call for the planner to make explicitly, not
  something this investigation should decide unilaterally.

- **Blocking for the planner: does trail-activity calibration require running a `Kernel` tick
  loop?** `compute_trail_activity` needs `(unique_tiles_visited, ticks_sampled)` sampled by actually
  ticking a `Kernel` forward N times and recording entity positions (`render_trail.py`'s existing
  shape) — a materially more expensive, more failure-prone operation than the terrain/entity-
  snapshot-only calls the other three-and-a-half families need (a single `WorldCompiler.compile()`
  call, no ticking). If trail-activity calibration is in scope for this ticket (the Scope section
  lists "all 4 metric families" without carving Variants' two halves apart), the
  `CalibrationIntegrityError`-style guard (AC #5) has real teeth — an actual `Kernel`/
  `EventRecorder` queue exists during trail sampling, and the same queue-drop/SURVIVAL-mode-shed
  failure modes `calibrate_simq.py` guards against could occur here too (position samples could be
  incomplete if the tick loop itself degrades under pressure, even though SimQ/`QualityHub` isn't
  the consumer). If trail-activity calibration is deferred/descoped (only TVD, terrain-histogram-
  based, calibrated for Variants this round), the guard has **no real queue to protect** for the
  remaining three-and-a-half families — connectivity/density/shape/TVD are all single-
  `WorldCompiler.compile()`-call operations with no `EventRecorder` involvement at all, and the
  honest analog for a "run-integrity guard" there is a **compile-report corruption check**
  instead (`compile_report["warnings"]` non-empty, or `entity_count == 0`/`region_count == 0` —
  both real, populated fields confirmed directly in `src/worldbuilding/compiler.py:620-635` and
  `:281,367,487,544,574`), not a literal port of the queue-drop/SURVIVAL check. **This is not
  resolved here** — the planner must decide explicitly which of these two guard designs (or both,
  scoped to their respective code paths) satisfies AC #5, and whether trail-activity is in this
  ticket's real scope at all.

- **Not blocking, but the planner should decide deliberately:** should the calibration output
  record Variants' TVD-half zero-cross-seed-variance the same way it must record Shape's (per the
  empirical finding in point 5 — both are pure functions of seed-invariant terrain today)? The
  ticket's own AC #3 text names only Shape; this investigation recommends extending the same
  "expected, not a bug" framing to Variants' TVD for the same underlying reason, but the ticket's
  own wording does not explicitly require it.

- **Not blocking:** the exact set of worlds/seeds this ticket's ">=3 seeds" sweep should use.
  `calibrate_simq.py`'s own precedent run (`grade_thresholds.yaml`'s header) used seeds `42, 137,
  999` for one world — a reasonable default to reuse for consistency across the whole calibration
  ecosystem, though nothing requires it. Whether to sweep all 21 real worlds or a deliberately
  smaller representative subset (cost/runtime tradeoff, since 21 worlds × >=3 seeds × 4 families
  means dozens of `WorldCompiler.compile()` calls, cheap individually but non-trivial in aggregate)
  is a real scoping decision left to the planner.

## Anti-Drift Hazards

- **Do not let the calibration script import anything from `src.simulation_quality.*` or
  `src.observability.events`** — the same independence boundary every shipped sibling in this batch
  (`connectivity.py`, `density.py`, `shape.py`, `variants.py`, `grading.py`) already establishes and
  this ticket's own dispatching instructions confirm is realistic and intentional. Reading
  `calibrate_simq.py` as a **reference pattern** is fine and expected; importing from it or from
  `src.simulation_quality` is not.
- **Do not add any pytest/CI assertion against the calibrated numeric threshold values
  themselves** — Out of Scope is explicit, and `calibrate_simq.py`'s own test suite already
  demonstrates the correct discipline (tests the guard's *behavior*, never asserts a specific
  calibrated number as a regression anchor for SimQ either).
- **Do not silently regenerate any `resolved/world.resolved.yaml` cache** as a side effect of
  wanting "real" seed-varying terrain for a more interesting calibration sample — `VARIANTS-METRIC`'s
  own Anti-Drift Hazards section already flags this exact temptation and rejects it; this ticket
  inherits that constraint unchanged. Use the real, unmodified `WorldRepository.load_world()` path
  only.
- **Do not change any of the four metric modules' formulas, or `grading.py`'s combination logic,**
  to make the calibration numbers "come out nicer." Out of Scope is explicit; if a metric's
  implementation looks wrong while calibrating it, that is a finding to report (a new ticket), not
  something to silently fix inline here.
- **Do not resolve the FOREST-separate-band question** — Out of Scope is explicit; structure the
  output so it *could* be answered later (per-terrain-type breakdown available in the raw data)
  without deciding it now.
- **Do not add a new TOML/YAML third-party writer dependency** — hand-format the TOML text (see
  point 7); no such dependency exists anywhere in this project today, and adding one for a single
  `tools/` script is disproportionate.
- **Do not let a run that silently produced zero components / zero entities / a `compile_report`
  warning pass through as a valid calibration data point.** Whatever shape the run-integrity guard
  takes (see the trail-activity risk above), it must fail loud rather than let a degenerate/
  corrupted compile silently pull a healthy-band number in a misleading direction — this is the one
  substantive behavior AC #5 requires, regardless of which concrete failure modes end up guarded.
