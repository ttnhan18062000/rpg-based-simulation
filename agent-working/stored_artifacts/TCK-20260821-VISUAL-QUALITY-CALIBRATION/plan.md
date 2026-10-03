---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-CALIBRATION
artifact_type: plan
tags: [visualization, simulation-quality, calibration, world]
---

# Implementation Plan — TCK-20260821-VISUAL-QUALITY-CALIBRATION

## Summary

Add `tools/calibrate_rendering.py`, a new `tools/`-tier calibration script mirroring
`tools/calibrate_simq.py`'s real (not aspirational) precedent: a `run` mode that loads one
real world at one real seed (`WorldRepository("data/worlds").load_world(world_id)` →
`WorldCompiler.compile(spec, seed=seed)`, `src/worldbuilding/repository.py:63`,
`src/worldbuilding/compiler.py:177-190`), runs all four rendering metric families
(`connectivity.analyze_connectivity`, `density.compute_density_cv`,
`shape.connected_components`, and a per-run `variants.normalize_histogram` capture — TVD
itself is a cross-run comparison, computed in `aggregate` mode, see Step 3) against the
compiled state, and writes a `quality_report.json`-equivalent JSON artifact per
`(world, seed)`, atomically (tmp-write-then-`os.rename()`, mirroring
`QualityPersistence.write_report`, `src/simulation_quality/persistence.py:47-53`); and a
separate `aggregate` mode that scans a directory of already-written per-run artifacts,
computes descriptive (min/max/mean, never asserted-against) healthy-band candidate
statistics per family, explicitly records Shape's and Variants' TVD-half's zero
cross-seed variance as expected (not a bug, not a guard failure), and writes one
provenance-headed JSON report to `config/rendering/` — a file **separate** from
`grade_thresholds.toml`, never overwriting it (Decision 1). A run-integrity guard
(`CalibrationIntegrityError`, mirroring `calibrate_simq.py:32-36`'s shape) fails loud on a
corrupted/degenerate `WorldCompiler.compile()` result, adapted to this script's real
single-compile-call architecture — no `Kernel`/`EventRecorder` queue exists here, so
`compute_trail_activity` (the one family half that would need one) is deliberately
deferred out of this ticket's scope (Decision 2). No `src.simulation_quality.*` or
`src.observability.events` import anywhere in the new script; no third-party dependency;
no mutation of `data/worlds/*/resolved/`; no change to any of the four metric modules'
formulas or `grading.py`'s combination logic; no CI-gating of the calibrated numbers. A
new parity-ledger entry, `INFRA-376`, covers the script's own run-integrity guard
(mirroring `INFRA-320`'s shape, `priority: P2` — not `P0`, per investigation.md's explicit
blast-radius reasoning).

## Key Decisions

**Decision 1 — Config write strategy: option (a), a SEPARATE calibration-report file;
`config/rendering/grade_thresholds.toml` is never written or modified by this ticket.**
Adopted per investigation.md's explicit recommendation and its own stated reasoning,
confirmed directly rather than re-derived: `tools/calibrate_simq.py`'s `main()` (read in
full, `tools/calibrate_simq.py:368-461`) never opens, computes against, or writes
`config/simulation_quality/grade_thresholds.yaml` — it only ever calls
`persistence.write_report(report)` (line 449) — despite the module docstring's aspiration
("update `config/simulation_quality/grade_thresholds.yaml` accordingly", lines 12-13).
That is the real, proven precedent this ticket mirrors, not the docstring's unfulfilled
aspiration. The alternative, option (b) (directly rewriting `config/rendering/
grade_thresholds.toml` in place), would mean editing a file another already-shipped,
already-tested ticket (`TCK-20260821-VISUAL-GRADE-SCORER`) owns and whose header carries
hand-written architectural-rationale comments (`config/rendering/grade_thresholds.toml:1-17`,
read in full above) — a materially higher-risk, harder-to-review change for a `chore`-tier
ticket whose own Out of Scope forbids any CI-gating/decision-consumption of its output
(so there is no correctness pressure requiring the numbers to land in the production file
immediately). Because option (a) is adopted, `test_plan.md`'s "if option (b) is chosen"
regression surface (`test_grading.py`'s config-loading test against a post-calibration
file) does **not** become load-bearing — `grade_thresholds.toml` is read-only throughout
this plan.

**Decision 2 — Trail-activity scope: OUT of scope this round. Only TVD (the
terrain-histogram half of Variants) is calibrated; `compute_trail_activity` is deferred to
a future ticket.** Reasoning: (1) `compute_trail_activity(unique_tiles_visited,
ticks_sampled)` (`src/rendering/variants.py:63-72`) structurally requires actually ticking
a `Kernel` forward N times and recording entity positions (`render_trail.py`'s shape) —
confirmed directly, not assumed, by reading the function and cross-referencing
investigation.md point 6 — a materially more expensive, more failure-prone operation than
the single `WorldCompiler.compile()` call every other family (and TVD's own
per-run-histogram half) needs. (2) None of `config/rendering/grade_thresholds.toml`'s
existing stubbed rules (`[hard_rules.fully_connected]`, `[soft_rules.fill_ratio_healthy_band]`,
confirmed by direct read above) reference trail-activity/movement-liveliness at all — the
one soft rule already stubbed is Shape's `fill_ratio`. (3) The ticket's own Acceptance
Criteria list generic "4 metric families... write an artifact per (world, seed)" language,
never naming trail-activity or movement-liveliness explicitly, and `render_trail.py` is
listed in Related Code Areas as a reference pattern (mirroring `render_annotated.py`'s and
`render_world.py`'s equally-uninvoked listing), not as a required consumer. (4) Introducing
real `Kernel`/`EventRecorder` wiring inside a `chore`-tier calibration script materially
expands this ticket's surface (a new failure-mode class: queue drops, SURVIVAL-mode shed,
tick-loop determinism) for a benefit (trail-activity's healthy band) no AC or stubbed
config rule currently requires. investigation.md explicitly states this smaller,
honestly-scoped pass is a defensible choice given the ticket's Scope text does not
explicitly carve Variants' two halves apart — this plan takes that option. **Consequence
for Decision 8 (run-integrity guard):** since no `Kernel`/`EventRecorder` queue exists
anywhere in this script's real code path, the guard is the compile-report corruption
check, not a literal port of `calibrate_simq.py`'s queue-drop/SURVIVAL-mode check (see
Step 2). **Consequence for the CLI (Decision 6):** no `--ticks` flag is added this round —
adding one with no consumer would be dead CLI surface; a future ticket that implements
trail-activity calibration can add it then.

**Decision 3 — Module/script placement: `tools/calibrate_rendering.py`.** Confirmed per
investigation.md's recommendation: matches `calibrate_simq.py`'s own placement exactly (an
operational script, not library code any test imports as production logic), and sits
outside `tests/architecture/test_rendering_zero_new_dependency_guard.py`'s scope (that
guard AST-walks `src/rendering/*.py` specifically, confirmed by the guard's own passing
baseline in the `GRADE-SCORER` plan above — a `tools/` script is not bound by it).

**Decision 4 — Per-run output artifact shape.** One JSON per `(world, seed)` run,
written to `data/calibration/rendering/{world_id}_seed{seed}/quality_report.json`
(namespaced under a `rendering/` subdirectory of `data/calibration/`, deliberately
distinct from `calibrate_simq.py`'s own `data/calibration/{name}_seed{seed}_{ticks}t/`
convention — see Step 3's "Other writers" note for why this avoids a real collision risk).
Fields, each confirmed against a real, read source rather than inferred from a name:

```json
{
  "world_id": "dungeon_crawl",
  "seed": 42,
  "compile_report": { "...": "raw dict returned by WorldCompiler.compile(), unmodified" },
  "connectivity": {"walkable_count": 0, "component_count": 0, "component_sizes": [], "percent_reachable": 0.0},
  "density": {"cv": 0.0, "entity_count": 0},
  "shape": {"components": [{"terrain_type": "FOREST", "size": 0, "fill_ratio": 0.0, "bbox": [0, 0, 0, 0]}]},
  "variants": {"terrain_histogram_normalized": {"FOREST": 0.0}}
}
```

`connectivity`'s four keys are `ConnectivityResult`'s exact fields
(`src/rendering/connectivity.py:25-29`, read directly: `walkable_count`,
`component_count`, `component_sizes`, `percent_reachable`). `density`'s two keys are a
subset of `DensityResult`'s fields (`src/rendering/density.py:27-30`: `cv`,
`entity_count`, `nn_distances` — `nn_distances` is deliberately **excluded** from the
artifact: it is a per-entity list whose length equals `entity_count`, adding size without
calibration value; `cv`/`entity_count` are the two fields a healthy-band candidate needs).
`shape.components` is built from `ShapeComponent`'s fields
(`src/rendering/shape.py:52-57`: `terrain_type`, `tiles`, `size`, `bbox`, `fill_ratio`) —
**`tiles` (a `frozenset[tuple[int,int]]`) is deliberately excluded**: it is not
JSON-serializable as-is and is not needed for a fill-ratio healthy-band calibration;
`bbox` (a plain 4-tuple) is retained and serialized as a 4-element list. `variants`
carries only `terrain_histogram_normalized` (via `variants.normalize_histogram`,
`src/rendering/variants.py:43-51`, over `density.compute_terrain_histogram`'s raw counts,
`src/rendering/density.py:58` — confirmed both exist) — **not** a TVD value, because TVD
is inherently a *comparison* of two histograms (`total_variation_distance(h1, h2)`,
`src/rendering/variants.py:53-60`) and a single `(world, seed)` run produces only one
histogram; TVD itself is computed in `aggregate` mode by comparing histograms already
written across multiple per-run artifacts (Step 3). `compile_report` is retained verbatim
(not re-keyed) for traceability and because it is what the run-integrity guard already
validated before this artifact was written.

Written via `tools/calibrate_rendering.py`'s own atomic-write helper: write to
`{cal_dir}/quality_report.json.tmp`, then `os.rename()` to the final path — the same
tmp-then-rename pattern `QualityPersistence.write_report`/`write_run_health`
(`src/simulation_quality/persistence.py:47-53`, `:58-72`) use, reimplemented locally in
the new script (never imported from `src.simulation_quality.persistence`, per the
independence boundary).

**Decision 5 — Format: JSON throughout, not TOML.** No stdlib TOML *writer* exists
(`tomllib` is read-only, confirmed by `GRADE-SCORER`'s own plan/investigation and
re-confirmed here: `grep`ing `requirements.txt` and all of `src/`/`tools/` for a
`tomli_w`/TOML-writer import returns zero hits) — a real, load-bearing constraint. Since
this ticket's separate calibration report (Decision 1's option (a)) is never parsed by
`grading.py`'s `tomllib.load()` call (it is a human/later-ticket-reviewed report, not
production config), there is no reason to hand-format TOML text for it at all: **the
report is plain JSON**, with a `"provenance"` object whose field set semantically mirrors
`config/simulation_quality/grade_thresholds.yaml`'s comment-block header
(`Calibration: <date> | <ticket_id>`; a scope-of-run line; an observed-values block; a
validation-summary line — see Decision 7) translated into JSON keys rather than `#`
comment lines. This resolves investigation.md's point 5 by choosing the explicitly-offered
alternative ("JSON with a text provenance header... that's also fine") rather than
hand-formatting TOML for a file with no TOML consumer.

**Decision 6 — CLI shape: two subcommands, `run` and `aggregate`, via
`argparse.ArgumentParser.add_subparsers()`.**
- `run --world <str> --seed <int> [--output <dir>]`: `--seed` is a bare `int` (`type=int`,
  no `default`, required — unlike `calibrate_simq.py`'s `default=42`, this script always
  names an explicit world+seed pair rather than falling back to a generic scenario, since
  it has no generic-scenario fallback path), matching investigation.md point 1's confirmed
  "one seed per invocation" CLI shape — multi-seed/multi-world sweeping is an external
  loop (a shell script or a thin Python wrapper calling this script's `main()`/subprocess
  repeatedly), never a `nargs="+"` list. `--world` is a bare `str` naming a real
  `data/worlds/{world}/` entry (validated by `WorldRepository.load_world` raising if not
  found — no new validation needed, the repository already fails loud). `--output`
  overrides `cal_dir` exactly like `calibrate_simq.py --output` overrides `cal_dir`
  (`tools/calibrate_simq.py:419`).
- `aggregate --input-dir <dir> [--output <path>]`: `--input-dir` defaults to
  `data/calibration/rendering` (the parent of every `run`-mode output directory);
  `--output` defaults to `config/rendering/calibration_report_
  TCK-20260821-VISUAL-QUALITY-CALIBRATION.json` (ticket-scoped filename, not date-scoped,
  so repeated aggregate runs during this ticket's own development overwrite one canonical
  file rather than accumulating dated duplicates under version control).
No `--ticks` flag this round (Decision 2's consequence — dead CLI surface with no
consumer). No `--entities`/`--profile`/`--window-size`/`--loop-threshold` flags —
`calibrate_simq.py`'s engine-tuning flags have no equivalent here since this script never
ticks an engine.

**Decision 7 — Provenance header field set (the `aggregate`-mode report's `"provenance"`
object).** Matches `config/simulation_quality/grade_thresholds.yaml`'s exact field set
(read in full above, lines 89-101 of investigation.md's quoted excerpt), pluralized for
this ticket's genuinely multi-world run, per investigation.md point 2's explicit,
deliberate adaptation reasoning:

```json
"provenance": {
  "calibration": "<YYYY-MM-DD> | TCK-20260821-VISUAL-QUALITY-CALIBRATION",
  "worlds": ["dungeon_crawl", "sandbox_world", "..."],
  "seeds": [42, 137, 999],
  "ticks": 0,
  "scope_note": "connectivity/density/shape/variants-TVD only (single WorldCompiler.compile() call per run); compute_trail_activity is deferred, see plan.md Decision 2"
}
```

`"calibration"` mirrors the `Calibration: <date> | <ticket_id>` line;
`"worlds"`/`"seeds"`/`"ticks"` mirror the `World: ... | Seeds: ... | Ticks: ...` line,
pluralized (`"Worlds"` → `"worlds"` as a real list, not a single string) since this run
covers multiple worlds, unlike the `TCK-20260630-SIMQ-RECALIBRATE` precedent's single-world
run. The report's top-level `"observed"` object is the "Observed ... per seed" prose
block's structural equivalent (Decision 4/Step 4's descriptive-stats output); a top-level
`"validation_summary"` string field is the "Thresholds validated: ..." closing line's
equivalent, stating in prose that no threshold value in this report is asserted, gated, or
final.

**Decision 8 — Run-integrity guard: compile-report corruption check, not a literal
queue-drop/SURVIVAL-mode port.** Direct consequence of Decision 2: since no `Kernel`/
`EventRecorder` exists anywhere in this script's real execution path, the honest guard
analog checks the one real, populated artifact every run does produce —
`WorldCompiler.compile()`'s `report` dict, confirmed by direct read to contain
`"warnings"` (a `list[str]`, declared at `src/worldbuilding/compiler.py:281` and appended
to at four distinct call sites — `:367`, `:487`, `:544`, `:574` — across resource/entity/
quest/information-response compilation, corrected count per Review), `"entity_count"`,
and `"region_count"` (both `int`,
`src/worldbuilding/compiler.py:620-635`'s `report = {...}` dict literal, confirmed by
direct read). `guard_passed = (not warnings) and entity_count > 0 and region_count > 0`;
`CalibrationIntegrityError` (this script's own class, not imported from
`calibrate_simq.py`) raises when `not guard_passed`, as its own top-level statement (never
nested inside a `try/except` that could swallow it — mirroring `calibrate_simq.py:322-326`'s
documented anti-pattern-avoidance). A small `compile_health.json` sidecar (this script's
own equivalent of `write_run_health`) is written, atomically, **before** the raise, so a
failed run still leaves a diagnosable trace on disk — mirroring `calibrate_simq.py:288-297`'s
"written before any integrity-guard raise" ordering exactly.

**Decision 8b — Step 5's cross-seed `total_variation_distance()` usage is reconciled
explicitly against `VARIANTS-METRIC`'s own Anti-Drift Hazard, not a silent extension into
territory that ticket flagged as reserved (Review-caught: this reconciliation was missing
from the original plan and is now made explicit).** `VARIANTS-METRIC`'s own
`investigation.md` states verbatim: *"Do not let `total_variation_distance()` grow
same-spec/different-seed-aware logic ... the function must stay a pure, spec-blind
statistical primitive; any 'is this a fair cross-spec comparison' judgment belongs to a
caller/orchestration layer this ticket does not build (Out of Scope: multi-seed averaging
is `TCK-20260821-VISUAL-GRADE-SCORER`'s job)."* Two things confirm Step 5's design is the
legitimate fulfillment of that anticipated role, not a boundary violation:
1. `total_variation_distance()` itself (`src/rendering/variants.py:53-60`) is never
   modified by this plan — it stays exactly the pure, spec-blind `(h1, h2) -> float`
   primitive `VARIANTS-METRIC` shipped. Step 5 only ever *calls* it, from outside, as an
   external consumer — precisely the "caller/orchestration layer" shape that ticket
   anticipated, never touching the function's own signature or internals (Scope Guards
   already forbid modifying `variants.py` at all).
2. `GRADE-SCORER`'s own investigation/plan (checked directly:
   `stored_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/plan.md`) confirms it did **not**
   build this same-spec/different-seed TVD comparator — it built only a generic
   `average_scores()` arithmetic mean over already-computed grade *scores*, and its own
   plan states explicitly that "wiring this function into an actual multi-seed sweep tool
   is out of this ticket's scope." `VARIANTS-METRIC` named `GRADE-SCORER` as the
   anticipated future caller, but `GRADE-SCORER` deliberately declined to build that
   specific comparator — leaving the role open, not filled elsewhere, for whichever ticket
   actually needed a same-spec/different-seed TVD reading. This calibration ticket is that
   ticket: it is diagnostic, non-authoritative tooling computing a **descriptive
   statistic** (`"seed_variance": "none (expected)"` / a plain numeric spread) for a
   provenance report a human reviews, never a grade/pillar/diversity signal consumed by
   any scoring or gameplay decision — the exact "orchestration layer, out of this
   [VARIANTS-METRIC] ticket's scope" framing, applied honestly rather than silently
   assumed. AC #4's forbidden pattern ("no code path treats same-spec/different-seed as a
   diversity signal") governs `grading.py`'s scoring pipeline specifically (confirmed:
   `GRADE-SCORER`'s own AC #4 text, unchanged and untouched by this ticket); this
   calibration script's Out-of-Scope CI-gating prohibition (Scope Guards, this plan) is the
   parallel enforcement mechanism keeping its own output equally non-authoritative and
   non-consumed, so the same "never a diversity signal" spirit holds here by a different,
   already-present guarantee, not a new one this Decision invents.

**Decision 9 — Parity ledger: new entry `INFRA-376`, `priority: P2`.** Confirmed still the
next free ID at plan-write time: `grep -n "INFRA-376\|INFRA-375" docs/parity_ledger/
infrastructure.yaml` shows `INFRA-375` (the `review_pipeline.py`/`AGENT-REVIEW` entry) is
the last entry in the file; no `INFRA-376` exists yet. `priority: P2` (not `P0`, and not
the higher end of investigation.md's offered "P1 or P2" range) — chosen for two concrete
reasons: (1) this ticket's Out of Scope explicitly forbids any CI-gating or
decision-consumption of the script's output, a real, material blast-radius reduction from
`INFRA-320`'s `P0` (whose guard protects live SimQ scoring, a system other code *does*
consume for grading decisions); (2) `P2` matches every other entry this same batch has
landed for report-only rendering-quality tooling (`INFRA-370` through `INFRA-375`, all
confirmed `priority: P2` by direct read above) — consistent with the established batch
convention rather than a one-off deviation.

## Steps

### Step 1 — Module skeleton, imports, and CLI argument parsing

**Files:** `tools/calibrate_rendering.py` (new)

**Change:** Create the file with a module docstring mirroring `calibrate_simq.py`'s
`Usage:` block shape (`tools/calibrate_simq.py:1-19`, read directly), documenting both
subcommands and an explicit external-loop sweep example (a `for world in ...; for seed in
42 137 999; do python3 tools/calibrate_rendering.py run --world "$world" --seed "$seed";
done` shell snippet, plus `python3 tools/calibrate_rendering.py aggregate` afterward) —
this satisfies the ">=3 seeds" Scope requirement via documented external orchestration,
per Decision 6, not a new list-accepting flag. State explicitly in the docstring that
`compute_trail_activity` is deferred (Decision 2) and that this script never imports
`src.simulation_quality.*`/`src.observability.events` (mirroring the four sibling metric
modules' own docstring-level independence statements, confirmed present in
`shape.py:32-37`/`variants.py:28-34` per the `GRADE-SCORER` investigation).

Imports: `argparse`, `json`, `os`, `sys`, `statistics` (Review-caught: Step 5's
descriptive-stats computation calls `statistics.mean`/`min`/`max`, stdlib, and this was
missing from the original import list), `dataclasses.dataclass`, `pathlib.Path`,
`datetime` (for the provenance `"calibration"` date field); from the project:
`from src.worldbuilding.repository import WorldRepository` (`src/worldbuilding/
repository.py:16`), `from src.worldbuilding.compiler import WorldCompiler`
(`src/worldbuilding/compiler.py:170`), `from src.rendering.connectivity import
analyze_connectivity`, `from src.rendering.density import compute_density_cv,
compute_terrain_histogram`, `from src.rendering.shape import connected_components`,
`from src.rendering.variants import normalize_histogram, total_variation_distance` — all
four confirmed to exist at exactly these names by direct read above. Add `sys.path.insert`
bootstrapping identical to `calibrate_simq.py:26` if the script is expected to run as a
bare `python3 tools/calibrate_rendering.py` invocation from the repo root (confirmed
necessary by that precedent).

Add `argparse` scaffolding: a top-level parser with `add_subparsers(dest="mode",
required=True)`; a `run` subparser with `--world` (`type=str, required=True`), `--seed`
(`type=int, required=True`), `--output` (`type=str, default=None`); an `aggregate`
subparser with `--input-dir` (`type=str, default=os.path.join("data", "calibration",
"rendering")`), `--output` (`type=str, default=os.path.join("config", "rendering",
"calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION.json")`).

**Other writers to this file:** none — brand-new file, this ticket is its sole author.

**Do NOT touch:** `tools/calibrate_simq.py` (read-only reference pattern only, never
imported, never edited).

**Verify:** `test_seed_flag_is_singular_per_invocation` (parses `["run", "--world", "x",
"--seed", "42"]` and confirms `args.seed == 42` as a plain `int`; confirms `--seed a b`
style multi-value input is rejected by `argparse` itself).

### Step 2 — `_load_and_compile` + the run-integrity guard + atomic sidecar write

**Files:** `tools/calibrate_rendering.py` (same file)

**Change:** Add:

```python
class CalibrationIntegrityError(Exception):
    """Raised when a calibration run's WorldCompiler.compile() produced a corrupted or
    degenerate compile_report -- mirrors tools/calibrate_simq.py's CalibrationIntegrityError
    (INFRA-320), adapted to this script's real single-compile-call architecture (no
    Kernel/EventRecorder queue exists here -- see plan.md Decision 2/8)."""


def _load_and_compile(world_id: str, seed: int):
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    return WorldCompiler.compile(spec, seed=seed)


def _check_compile_integrity(compile_report: dict, cal_dir: str) -> None:
    warnings = compile_report.get("warnings", [])
    entity_count = compile_report.get("entity_count", 0)
    region_count = compile_report.get("region_count", 0)
    guard_passed = (not warnings) and entity_count > 0 and region_count > 0
    _atomic_write_json(
        os.path.join(cal_dir, "compile_health.json"),
        {"warnings": warnings, "entity_count": entity_count,
         "region_count": region_count, "guard_passed": guard_passed},
    )
    if not guard_passed:
        raise CalibrationIntegrityError(
            f"compile integrity guard failed for world_id={compile_report.get('world_id')} "
            f"seed={compile_report.get('seed')}: warnings={warnings}, "
            f"entity_count={entity_count}, region_count={region_count}. Calibration data "
            f"for this run is unreliable and must not be written."
        )
```

`_load_and_compile` uses `WorldRepository.load_world(world_id: str) -> WorldSpec`
(`src/worldbuilding/repository.py:63`, confirmed signature) and
`WorldCompiler.compile(spec, seed, output_report_path=None, context=None) ->
tuple[AuthoritativeState, dict]` (`src/worldbuilding/compiler.py:177-190`, confirmed
signature and return shape — the second tuple element is the same `report` dict whose
`"warnings"`/`"entity_count"`/`"region_count"` keys `_check_compile_integrity` reads,
confirmed populated at `src/worldbuilding/compiler.py:620-635`). The `_atomic_write_json`
helper (defined in Step 3) is called here **before** the raise, matching
`calibrate_simq.py:288-297`'s write-before-raise ordering (Decision 8) — this call is the
sidecar's only writer.

**Other writers to `data/calibration/rendering/{world}_seed{seed}/`:** none besides this
script's own `run` subcommand — this is a brand-new subdirectory tree; `calibrate_simq.py`
writes to the sibling (non-nested) `data/calibration/{name}_seed{seed}_{ticks}t/` paths
(confirmed 20+ real directories exist there today, none under a `rendering/` subpath),
so there is no path collision between the two calibration systems even though both share
the `data/calibration/` parent.

**Do NOT touch:** `src/worldbuilding/compiler.py`, `src/worldbuilding/repository.py`
(read-only inputs; this ticket must not change compile/load behavior).

**Verify:** `test_calibration_run_integrity_guard_fails_loud_on_corrupted_compile`
(monkeypatch `WorldCompiler.compile` to return a `report` dict with a non-empty
`"warnings"` list, assert `CalibrationIntegrityError` raises and `compile_health.json`
exists with `guard_passed: false`); `test_calibration_run_succeeds_normally_on_clean_compile`
(real compile of `dungeon_crawl`, assert no raise and `compile_health.json` has
`guard_passed: true`).

### Step 3 — Per-run family computation, the artifact dataclass, and the atomic-write helper

**Files:** `tools/calibrate_rendering.py` (same file)

**Change:** Add:

```python
def _atomic_write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    os.rename(tmp_path, path)


@dataclass(frozen=True)
class RenderingCalibrationRunArtifact:
    world_id: str
    seed: int
    compile_report: dict
    connectivity: dict
    density: dict
    shape: dict
    variants: dict

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id, "seed": self.seed,
            "compile_report": self.compile_report, "connectivity": self.connectivity,
            "density": self.density, "shape": self.shape, "variants": self.variants,
        }


def _build_run_artifact(world_id: str, seed: int, state, compile_report: dict) -> RenderingCalibrationRunArtifact:
    conn = analyze_connectivity(state.terrain, state.blocked_tiles)
    dens = compute_density_cv(state.entities)
    shape_components = connected_components(state.terrain)
    raw_histogram = compute_terrain_histogram(state.terrain)
    normalized_histogram = normalize_histogram(raw_histogram)
    return RenderingCalibrationRunArtifact(
        world_id=world_id, seed=seed, compile_report=compile_report,
        connectivity={"walkable_count": conn.walkable_count,
                      "component_count": conn.component_count,
                      "component_sizes": conn.component_sizes,
                      "percent_reachable": conn.percent_reachable},
        density={"cv": dens.cv, "entity_count": dens.entity_count},
        shape={"components": [
            {"terrain_type": c.terrain_type, "size": c.size,
             "fill_ratio": c.fill_ratio, "bbox": list(c.bbox)}
            for c in shape_components
        ]},
        variants={"terrain_histogram_normalized": normalized_histogram},
    )
```

`state.terrain`, `state.blocked_tiles`, `state.entities` are confirmed real
`AuthoritativeState` fields by direct read of the constructor call this ticket's own
`_load_and_compile` (Step 2) exercises transitively
(`src/worldbuilding/compiler.py:594-610`: `AuthoritativeState(tick=0, seed=seed,
entities=entities, ..., terrain=terrain, ..., blocked_tiles=blocked_tiles, ...)`).
`analyze_connectivity(terrain, blocked_tiles)`, `compute_density_cv(entities)`,
`connected_components(terrain)`, `compute_terrain_histogram(terrain)`,
`normalize_histogram(raw)` are each confirmed to exist at exactly these signatures by
direct read above (`connectivity.py:44-46`, `density.py:33`, `shape.py:123-126`,
`density.py:58`, `variants.py:43`).

**Other writers to `data/calibration/rendering/{world}_seed{seed}/quality_report.json`:**
none — this script's `run` subcommand (Step 4) is the sole writer of this specific path;
see Step 2's collision analysis for the shared `data/calibration/` parent directory.

**Do NOT touch:** any of `connectivity.py`/`density.py`/`shape.py`/`variants.py` — all
four are read-only inputs; calling their public functions is this ticket's only
interaction with them.

**Verify:** `test_cli_runs_all_four_families_for_one_world_seed_pair` (calls
`_build_run_artifact` for `dungeon_crawl`/seed 42 directly, asserts all four family keys
are present and non-empty in `.to_dict()`); `test_output_artifact_written_to_correct_location_atomically`
(asserts `quality_report.json` exists at the documented path with no leftover `.tmp` file
after a successful `run` invocation).

### Step 4 — `run` subcommand wiring

**Files:** `tools/calibrate_rendering.py` (same file)

**Change:** Add a `_run_one(args) -> None` function called when `args.mode == "run"`:
compute `cal_dir = args.output or os.path.join("data", "calibration", "rendering",
f"{args.world}_seed{args.seed}")`; call `state, compile_report = _load_and_compile(args.world,
args.seed)`; call `_check_compile_integrity(compile_report, cal_dir)` (raises and stops
before any `quality_report.json` is written, per Decision 8, if the guard fails); on
success, call `artifact = _build_run_artifact(args.world, args.seed, state,
compile_report)` and `_atomic_write_json(os.path.join(cal_dir, "quality_report.json"),
artifact.to_dict())`; print a short human-readable summary line (mirroring
`calibrate_simq.py:452-461`'s print-summary convention) naming the artifact path.

**Other writers:** none beyond Steps 2-3's already-analyzed writers; this function is
purely an orchestration wrapper around them.

**Do NOT touch:** nothing new — this step only wires together Steps 1-3's already-scoped
pieces.

**Verify:** `test_cli_runs_all_four_families_for_one_world_seed_pair` (via `_run_one`
directly, mirroring `test_calibrate_world_loading.py`'s pattern of testing the internal
function rather than only subprocess/CLI, per test_plan.md).

### Step 5 — `aggregate` subcommand: cross-run descriptive stats and the provenance report

**Files:** `tools/calibrate_rendering.py` (same file)

**Change:** Add `_aggregate(args) -> None`: glob `os.path.join(args.input_dir, "*",
"quality_report.json")`, load each into a list of run-artifact dicts (skip/warn on any
directory missing the file — a run that raised `CalibrationIntegrityError` in Step 2 never
wrote one, by construction, so it is correctly excluded from aggregation without any
extra filtering logic). Group loaded artifacts by `world_id`. Compute:

- `connectivity.percent_reachable` and `density.cv`: flat `{"min": ..., "max": ...,
  "mean": ..., "n": ...}` over all loaded runs (`statistics.mean`/`min`/`max`, stdlib,
  no new dependency).
- `shape.fill_ratio_by_terrain_type`: for each distinct `terrain_type` seen across all
  runs' `shape.components`, the same `{"min", "max", "mean", "n"}` stats over that
  type's `fill_ratio` values only — keeping the breakdown per-terrain-type (not
  collapsed to one corpus-wide number) is the direct mechanism by which a future
  FOREST-specific band *could* be added later without deciding that question now (per
  the ticket's Out of Scope and investigation.md point 10).
- `shape.same_world_cross_seed_variance` and `variants.same_world_cross_seed_tvd`: for
  each `world_id` with >=2 loaded seeds, compare: (shape) whether the sorted
  `(terrain_type, size, fill_ratio)` tuples are identical across every seed for that
  world; (variants) `total_variation_distance(h1, h2)` between the first two seeds'
  `terrain_histogram_normalized` values for that world (pairwise across all seed pairs
  if more than two are present, reporting the max observed TVD). Record a
  `"seed_variance": "none (expected)"` annotation when the result is exactly
  zero/identical, and a plain numeric variance report otherwise — this is the direct
  mechanism satisfying AC #3 for Shape and extending the same framing to Variants' TVD
  (per investigation.md point 5's finding that both are pure functions of seed-invariant
  terrain for today's real corpus, and the sibling instruction's explicit direction to
  extend the framing). **This computation never touches or feeds
  `_check_compile_integrity`'s guard (Step 2) — the guard is scoped entirely to one
  run's own `compile_report`, evaluated and passed/failed before this cross-run
  comparison ever runs, so a zero-variance world can never trip the guard by
  construction, with no special-case exception needed.**

Build the provenance object (Decision 7) from the loaded runs' own `world_id`/`seed`
values (`sorted(set(...))` for `"worlds"`/`"seeds"`) and `datetime.date.today().isoformat()`
for the date. Write the final report via `_atomic_write_json(args.output, {"provenance":
..., "observed": {...}, "validation_summary": "...", "runs_included": [...]})`.

**Other writers to `config/rendering/`:** `config/rendering/grade_thresholds.toml` was
created by `TCK-20260821-VISUAL-GRADE-SCORER` and is never touched by this ticket
(Decision 1). This step's output filename
(`calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION.json`) is new and does not
collide with the existing file. No other ticket or code path writes into
`config/rendering/` today (confirmed by investigation.md).

**Do NOT touch:** `config/rendering/grade_thresholds.toml` (read-only; not opened, not
parsed, not written by this step or any other step in this plan).

**Verify:** `test_shape_zero_cross_seed_variance_is_recorded_as_expected_not_flagged`
(real `dungeon_crawl` runs at seeds 42 and 137 — the durable, structural seed-invariance
anchor per investigation.md point 5, not `sandbox_world`); `test_density_and_connectivity_show_real_cross_seed_variance_in_output`
(real `sandbox_world` runs at seeds 42 and 137, asserting the aggregate's `density.cv`
stats reflect the real 0.6478/0.9105 spread, not a collapsed single value);
`test_output_config_header_matches_grade_thresholds_yaml_field_set` (parses the written
report's `"provenance"` object, asserts all required fields present).

### Step 6 — `main()` dispatch

**Files:** `tools/calibrate_rendering.py` (same file)

**Change:** Add `main()`: parse args via Step 1's parser; dispatch to `_run_one(args)` if
`args.mode == "run"`, else `_aggregate(args)`; `if __name__ == "__main__": main()` at
module end, matching `calibrate_simq.py`'s own entrypoint convention.

**Other writers:** none — pure dispatch.

**Do NOT touch:** nothing new.

**Verify:** `test_cli_runs_all_four_families_for_one_world_seed_pair` exercised via
`main()` with `sys.argv` patched, as an additional CLI-level smoke assertion alongside the
direct-function-call test from Step 4.

### Step 7 — Write `tests/tools/test_calibrate_rendering.py`

**Files:** `tests/tools/test_calibrate_rendering.py` (new)

**Change:** Implement all 11 tests from `test_plan.md`'s "New Tests Required" section
against Steps 1-6's real code, using real `WorldRepository`/`WorldCompiler` calls (no
mocking of compile itself, per test_plan.md's stated category for test 1) and `tmp_path`
for all written artifacts (never writing into the real `data/calibration/rendering/` tree
from tests). Fold test 9 (the CI-gating architecture guard) into this same file per
test_plan.md's stated lighter-weight default, as a repo-wide `grep`/AST scan asserting no
file under `tests/` other than this one imports/opens the calibration report path and
asserts a specific numeric value from it. Test 10 (no `simulation_quality`/
`observability.events` import) is an AST-walk over `tools/calibrate_rendering.py` itself,
mirroring `test_density.py`'s per-module pattern. Test 11 (no `resolved/` cache mutation)
records `os.path.getmtime` of every file under a real world's `resolved/` directory before
and after a `run` invocation and asserts no change.

**Other writers to this file:** none — new test file, this ticket's sole author.

**Do NOT touch:** any existing file under `tests/unit/rendering/`,
`tests/simulation_quality/`, or `tests/architecture/` — all are regression surface only
(test_plan.md's Regression Surface section), read/run but never modified.

**Verify:** `pytest tests/tools/test_calibrate_rendering.py -m "not slow and not extra_slow" --tb=short -q`
fully green; `pytest tests/unit/rendering tests/simulation_quality/test_calibrate_simq.py
tests/simulation_quality/test_calibrate_world_loading.py tests/architecture -m "not slow
and not extra_slow" --tb=short -q` (the full regression surface from test_plan.md) stays
green, unchanged by this ticket.

### Step 8 — Add parity ledger entry `INFRA-376`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Immediately before appending, re-run `grep -n "^- id: INFRA-3" docs/
parity_ledger/infrastructure.yaml | tail` to reconfirm `INFRA-375` is still the last entry
(per CLAUDE.md's shared-working-directory caveat — this repo may have a concurrent
session appending entries between plan-write time and implementation time). Append,
following `INFRA-370`-`375`'s exact 8-field shape:

```yaml
- id: INFRA-376
  text: tools/calibrate_rendering.py's run-integrity guard (CalibrationIntegrityError)
    fails loud when a calibration run's WorldCompiler.compile() report contains any
    warnings, or entity_count == 0, or region_count == 0 -- adapted from
    calibrate_simq.py's CalibrationIntegrityError/INFRA-320 queue-drop/SURVIVAL-mode
    guard to this script's real single-compile-call architecture (no Kernel/
    EventRecorder queue exists in this code path; compute_trail_activity, the one
    family half that would need one, is deferred to a future ticket -- see
    staging_artifacts/TCK-20260821-VISUAL-QUALITY-CALIBRATION/plan.md Decision 2/8). A
    compile_health.json sidecar is written atomically before the raise, mirroring
    calibrate_simq.py's write-before-raise ordering. This ticket's Out of Scope
    forbids any CI-gating or decision-consumption of the calibrated numeric output
    itself -- only this guard's own pass/fail behavior is covered by this entry.
  status: verified
  priority: P2
  v2_evidence: tools/calibrate_rendering.py
  test_path: tests/tools/test_calibrate_rendering.py::test_calibration_run_integrity_guard_fails_loud_on_corrupted_compile
  divergence_note: null
  proof_type: regression
```

**Other writers to this file:** `docs/parity_ledger/infrastructure.yaml` is a single YAML
list appended to by every ticket that lands a new infrastructure-layer parity fact — the
same shared-resource caveat `GRADE-SCORER`'s plan (`INFRA-374`, Step 9) already documented
for this exact file. `INFRA-375` (`AGENT-REVIEW`, already shipped) is the immediately
preceding entry; no concurrent-write race exists against it since it is already merged.

**Do NOT touch:** `docs/parity_ledger/infrastructure.yaml`'s existing entries
(`INFRA-370` through `INFRA-375`), `INFRA-320` (`calibrate_simq.py`'s own entry, unmodified
precedent), and `INFRA-372` (Shape's uncalibrated-0.95-threshold entry, which names this
ticket but whose own `status`/`text` this ticket does not need to update, per
investigation.md's Parity Ledger Overlap section — this ticket produces calibration *data*
and a script's guard entry, not a change to Shape's own formula/threshold-usage code).

**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
parses without error; the cited `test_path` (Step 7) must exist and pass before this entry
can honestly claim `status: verified`.

## Scope Guards

Must NOT be touched or introduced by this ticket, per the ticket's Out of Scope,
investigation.md's Anti-Drift Hazards, and this plan's own decisions:

- **No `import src.simulation_quality.*` or `import src.observability.events` anywhere**
  in `tools/calibrate_rendering.py` or `tests/tools/test_calibrate_rendering.py`.
- **No CI-gating or threshold-value assertion anywhere** — no test anywhere in `tests/`
  asserts a specific calibrated numeric value (`cv`'s healthy band is `[x, y]`, etc.) from
  either the per-run artifacts or the aggregate report. Enforced by Step 7's test 9.
- **`config/rendering/grade_thresholds.toml` is never opened, parsed, or written by any
  step in this plan** (Decision 1) — the separate `calibration_report_
  TCK-20260821-VISUAL-QUALITY-CALIBRATION.json` file is the sole output artifact under
  `config/rendering/`. Merging calibrated numbers into `grade_thresholds.toml`'s
  `[soft_rules.*]`/`[hard_rules.*]` tables, and updating that file's header comment away
  from "Illustrative values only, NOT calibrated," is explicitly deferred to a human or a
  follow-up ticket — not this ticket's deliverable.
- **No third-party dependency added** — no `tomli_w`, no new PyYAML usage beyond what
  already exists at the repo level (this script does not import `yaml` at all, since its
  sole output format is JSON, per Decision 5).
- **No mutation of any `data/worlds/*/resolved/` cache file** — `WorldRepository.
  load_world()` is used unmodified, exactly as every shipped sibling test already uses it;
  no cache-regeneration/"fixing" logic is added anywhere in this script. Enforced by Step
  7's test 11.
- **No change to any of the four metric modules' formulas
  (`connectivity.py`/`density.py`/`shape.py`/`variants.py`) or to `grading.py`'s
  combination logic** — all five are read-only inputs throughout this plan.
- **Do not resolve the FOREST-separate-threshold-band question** — Step 5's
  `shape.fill_ratio_by_terrain_type` breakdown makes a future answer *possible* without
  this ticket deciding it.
- **`compute_trail_activity` is not implemented, called, or calibrated anywhere in this
  plan** (Decision 2) — no `Kernel`/`EventRecorder` import, no tick loop, no `--ticks`
  CLI flag.
- **Do not let a run with a non-empty `compile_report["warnings"]` or a zero
  `entity_count`/`region_count` silently produce a `quality_report.json`** — Step 2's
  guard must run, and must write its sidecar, before Step 3's artifact write is ever
  reached.

## Dependency Map

- Step 1 (skeleton + CLI parsing) has no dependencies; it is first.
- Step 2 (`_load_and_compile` + integrity guard) depends on Step 1's imports.
- Step 3 (family computation + artifact dataclass + atomic-write helper) depends on Step
  1's imports; it is independent of Step 2 (different functions), though Step 4 needs
  both.
- Step 4 (`run` subcommand wiring) depends on Steps 2 and 3.
- Step 5 (`aggregate` subcommand) depends on Step 3's `quality_report.json` shape (it
  parses files in that exact shape) but is otherwise independent of Steps 2/4 — it could
  be implemented in parallel with Step 4.
- Step 6 (`main()` dispatch) depends on Steps 1, 4, and 5.
- Step 7 (tests) depends on Steps 1-6 being complete, since the test file exercises every
  function.
- Step 8 (parity ledger) depends on Step 7 passing, since the new entry's `test_path`
  cites a specific test that must exist and pass before the entry can honestly claim
  `status: verified`.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: A calibration script mirroring calibrate_simq.py's CLI/output shape runs each of the 4 metric families across >=3 seeds and writes a quality_report-equivalent artifact per (world, seed) | Steps 1, 2, 3, 4 (run subcommand); external-loop sweep documented in Step 1's docstring | `test_cli_runs_all_four_families_for_one_world_seed_pair`, `test_output_artifact_written_to_correct_location_atomically`, `test_seed_flag_is_singular_per_invocation` |
| AC #2: Healthy-band values are written to a config file with a provenance header (date, ticket ID, worlds, seeds, ticks) matching grade_thresholds.yaml's exact header format | Step 5 (aggregate subcommand, provenance object per Decision 7) | `test_output_config_header_matches_grade_thresholds_yaml_field_set` |
| AC #3: Output explicitly records Shape's zero cross-seed variance as expected, not flagged as a bug (extended to Variants' TVD per investigation.md point 5) | Step 5 (`shape.same_world_cross_seed_variance`, `variants.same_world_cross_seed_tvd`) | `test_shape_zero_cross_seed_variance_is_recorded_as_expected_not_flagged` |
| AC #4: No pytest/CI gate consumes these thresholds | Step 7 (test 9, folded architecture guard); Scope Guards | `test_no_pytest_or_ci_gate_asserts_against_calibrated_threshold_values` (folded into `tests/tools/test_calibrate_rendering.py`) |
| AC #5: A run-integrity guard mirroring CalibrationIntegrityError (queue-drop/corruption hard-fail) is present in the calibration script | Step 2 (`CalibrationIntegrityError`, `_check_compile_integrity`, compile-report corruption check per Decision 8) | `test_calibration_run_integrity_guard_fails_loud_on_corrupted_compile`, `test_calibration_run_succeeds_normally_on_clean_compile` |

## Anti-Drift Notes

- **Do not wire Step 5's cross-seed variance/TVD annotation into `grading.py`'s scoring
  pipeline, any hard/soft rule, or any CI gate** (Decision 8b). Its legitimacy rests on
  staying diagnostic-only, reviewed by a human via the provenance report — the moment any
  code path reads this calibration output to influence a grade, escalation decision, or
  gate outcome, it becomes exactly the "diversity signal" `VARIANTS-METRIC`'s Anti-Drift
  Hazard forbids, and Decision 8b's reconciliation no longer holds. The existing
  Out-of-Scope CI-gating Scope Guard is the enforcement mechanism; this bullet exists so a
  future reader scanning Anti-Drift Notes (not just Key Decisions) sees the same
  constraint restated where this document's other decisions each get a matching bullet.
- **Trail-activity (`compute_trail_activity`) is out of scope for this ticket by explicit
  decision (Decision 2), not an oversight.** A future ticket that wants trail-activity
  calibration must add real `Kernel`/`EventRecorder` wiring and a `--ticks` flag; do not
  retrofit this deferral away mid-implementation without a new decision being made
  explicitly (this plan's own reasoning, not silently).
- **The run-integrity guard (Step 2) and the cross-seed variance annotation (Step 5) are
  structurally decoupled by design** — the guard evaluates and either raises or passes
  before any artifact exists to compare across seeds; the zero-variance annotation is
  computed later, in `aggregate` mode, from already-written (already-guard-passed)
  artifacts. A future change must not merge these two concerns (e.g. "flag suspiciously
  identical runs" inside the guard itself) — that would directly contradict AC #3's
  requirement that legitimate zero-variance not be treated as a failure.
- **`ShapeComponent.tiles` (a `frozenset`) must never be serialized into
  `quality_report.json`** — it is large, not JSON-native, and unnecessary for calibration;
  only `terrain_type`, `size`, `fill_ratio`, and `bbox` are retained (Decision 4).
- **Use `dungeon_crawl`, not `sandbox_world`, as the anchor for any zero-cross-seed-variance
  test or documentation claim** — per `VARIANTS-METRIC`'s prior finding (re-confirmed in
  investigation.md point 5), `sandbox_world`'s apparent seed-invariance is a stale-cache
  artifact, while `dungeon_crawl`'s is structural (none of its composed modules declare
  `terrain_variants`). Do not swap this anchor for convenience.
- **`config/rendering/grade_thresholds.toml`'s header still says "Illustrative values
  only, NOT calibrated" after this ticket ships — that is expected, not a bug to fix
  here.** Updating it is explicitly deferred (Decision 1, Scope Guards).
- **Do not add a `.tomli_w`/hand-rolled TOML writer "just in case" a future ticket wants
  to merge the aggregate report into `grade_thresholds.toml` automatically** — that
  automation, if ever built, belongs to whichever future ticket actually performs the
  merge, with its own explicit design decision; this ticket's own output format is JSON
  throughout (Decision 5), full stop.
- **`INFRA-376`'s `priority: P2` must not be silently bumped to `P0` to "match INFRA-320
  more closely"** — the blast-radius reasoning in Decision 9 is specific to this ticket's
  Out-of-Scope CI-gating prohibition; the two entries cover systems with genuinely
  different consumption risk.

## Deviations

- **Step 5's `_stats()` helper: `statistics.min`/`statistics.max` do not exist in the
  Python stdlib `statistics` module** — only `statistics.mean` does. This plan's own
  prose ("descriptive min/max/mean stats via `statistics.mean`/`min`/`max`") was
  imprecise on this point. Implemented `_stats()` using the builtins `min()`/`max()`
  plus `statistics.mean()`, which is the only combination that actually exists and
  produces exactly the descriptive min/max/mean/`n` statistics this plan's Step 5 and
  Decision-level intent require — no behavioral or structural difference from what was
  planned, no new dependency, and `statistics` is still imported (and still used, for
  `mean`) exactly as Step 1 specifies.
