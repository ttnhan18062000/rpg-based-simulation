---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-GRADE-SCORER
artifact_type: plan
tags: [visualization, simulation-quality, world]
---

# Implementation Plan — TCK-20260821-VISUAL-GRADE-SCORER

## Summary

Add a new, architecturally-independent sibling module `src/rendering/grading.py` (single
flat file — see Decision 1) that consumes the four shipped sibling metric modules'
outputs (`ConnectivityResult`, `DensityResult`, `ShapeComponent`, `variants.py`'s
primitives) and turns them into an S/A/B/C/D/F grade. The module implements, in this
order: a config-sourced `GradeConfig` loader (fail-loud on malformed/missing config);
binary hard-rule evaluation (fixed pass/fail delta, no gradient); non-monotonic
healthy-band soft-rule evaluation (trapezoidal function of a raw metric — positive inside
the band, negative at both extremes); an additive combination step that sums all hard+soft
deltas into one combined score (mirroring SimQ's own additive combination pattern for this
narrow step, per investigation.md); grade assignment reusing SimQ's exact threshold values
and exact strict-`>` ladder semantics, sourced from a new, separate config file (never
imported from SimQ's own config); and multi-seed averaging via a plain arithmetic mean
that is not special-cased for N=1. A new parity-ledger entry, `INFRA-374`, is added,
because — contrary to the ticket's own stated Assumption — investigation.md found SimQ's
own grading system is **not** parity-exempt (`SIMQ-CALIBRATED-001`, `INFRA-255` both
exist), so this architecturally-independent sibling needs its own entry for the same
reason the four upstream metric siblings each did. No `src.simulation_quality.*` or
`src.observability.events` import, no `PillarScorer` subclass, no new `PillarId` member,
and no threshold/delta/boundary literal hardcoded in Python — all numeric tuning lives in
`config/rendering/grade_thresholds.toml`.

## Key Decisions

**Decision 1 — Module placement: single flat `src/rendering/grading.py`, not a
subpackage.** The full design surface is 3 frozen dataclasses (`GradeConfig` plus two
small nested config dataclasses), 2 result dataclasses (`HardRuleResult`,
`SoftRuleResult`), and 6 functions (`load_grade_config`, `evaluate_hard_rule`,
`evaluate_soft_rule`, `combine_rule_deltas`, `assign_grade`, `average_scores`) plus one
private helper (`_trapezoidal_delta`). This is comparable in size to
`src/rendering/shape.py` (224 lines, read in full above — the largest of the four shipped
siblings) and does not require independently reusable submodules — hard rules, soft
rules, combination, and grade assignment are logical sections of one bounded concern
("turn metric outputs into a grade"), not separable units. A subpackage would add
`__init__.py` re-export surface the four siblings deliberately do not have (confirmed:
`src/rendering/` today contains only flat `.py` files, no subpackages). This follows
investigation.md's explicit recommendation for option (a).

**Decision 2 — Config placement and format: `config/rendering/grade_thresholds.toml`
(TOML, parsed via stdlib `tomllib`, NOT YAML/`yaml.safe_load`), first file in a new
directory, values duplicated by copy from `config/simulation_quality/
grade_thresholds.yaml` (`S: 2.0, A: 0.5, B: 0.0, C: -0.5, D: -1.0`, confirmed identical by
direct read), not imported or referenced.**

This corrects a factual assumption in the ticket/investigation framing (both suggested
`yaml.safe_load` + a `.yaml` file, reasoning that PyYAML "is already a project
dependency," which is true at the repo level — `requirements.txt:42`,
`src/simulation_quality/weights.py:4` — but is the wrong scope to check). The actually
binding constraint is narrower and stricter: `tests/architecture/
test_rendering_zero_new_dependency_guard.py` (read in full above) walks every `.py` file
under `src/rendering/` specifically and asserts every import's top-level module is either
stdlib or `src.*` — confirmed directly by running `python3 -c "import sys;
print('yaml' in sys.stdlib_module_names)"` → `False`, and the guard's own passing baseline
run (`1 passed`) before this ticket touches anything. Adding `import yaml` to
`src/rendering/grading.py` would make this currently-green, must-keep-passing test
(test_plan.md's own Regression Surface, `tests/architecture/
test_rendering_zero_new_dependency_guard.py`) fail — a real, self-contradicting plan if
left as originally suggested. The correct fix is not to weaken that guard (it is a
deliberate, documented `src/rendering/`-specific architectural boundary from
`TCK-20260821-WORLD-RENDER-CORE`, and CLAUDE.md forbids editing a gate to make it pass
instead of fixing the underlying substance) but to pick a config format `src/rendering/`
can parse with a *stdlib* module. `tomllib` (stdlib since Python 3.11; this repo runs
3.12.3, confirmed `python3 --version`) is confirmed present in `sys.stdlib_module_names`
and supports nested tables (`[grade_thresholds]`, `[hard_rules.fully_connected]`,
`[soft_rules.fill_ratio_healthy_band]`) and `#` comments — the same human-readability the
`.yaml` suggestion wanted, without the third-party import. `tomllib.load()` requires a
binary-mode file handle (`open(path, "rb")`), unlike `yaml.safe_load`'s text-mode
acceptance — Step 2 states this explicitly.

This is still "sourced from a config file, never hardcoded" per AC #1's actual
requirement — the AC names no specific file format, only that thresholds/deltas live
outside Python code. The `.toml` file's header comment states the duplication-by-value
fact and the "update both manually" caveat explicitly, mirroring how `config/
simulation_quality/grade_thresholds.yaml`'s own header documents its calibration history
(read directly above: dated header comment with calibration provenance) — same spirit,
different (stdlib-compatible) syntax.

**Decision 3 — Hard+soft combination mechanism (the ticket's real design risk).** Designed
as: hard rules contribute a fixed-magnitude delta (`pass_delta` or `fail_delta`, no
gradient — binary by construction); soft rules contribute a trapezoidal delta over a raw
metric value (`min_delta` at and beyond `low`/`high`, linearly ramping to `peak_delta`
across `[low, healthy_low]` and `[healthy_high, high]`, held at `peak_delta` across
`[healthy_low, healthy_high]` — non-monotonic in the raw metric by construction); all
individual rule deltas (hard and soft) sum via plain addition into one combined score
(`combine_rule_deltas`), mirroring SimQ's own additive `PillarAccumulator.add()` pattern
for this narrow "sum signed floats" step (`src/simulation_quality/pillar_accumulator.py:
43-58`, read in investigation.md) even though the per-rule shape differs; the combined
score then feeds `assign_grade`, the reused threshold ladder. One illustrative hard rule
and one illustrative soft rule are built into the config and module (see Steps 3-4) —
their numeric boundaries are explicitly illustrative, not calibrated
(`TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s job).

**Decision 4 — Multi-seed averaging: `average_scores(per_seed_scores: list[float]) ->
float` = `sum(per_seed_scores) / len(per_seed_scores)`, no `len == 1` branch.** A plain
arithmetic mean naturally returns the single input unchanged when `N == 1` (`sum([x]) /
1 == x` exactly, no floating-point rounding introduced by division by 1) and the true mean
when `N > 1` — both AC #3 cases are satisfied by the same one-line expression. Any
`if len(scores) == 1: return scores[0]` branch would be dead-weight special-casing this
plan deliberately avoids per investigation.md's Anti-Drift Hazards.

**Decision 5 — Grade assignment reuses SimQ's exact threshold *values* and exact
comparison *semantics*, by copied logic, not by import.** `src/simulation_quality/
quality_report.py::_assign_grade` (lines 72-83, read directly above) is a strict
descending `score > threshold` ladder: `S` if `> grade_thresholds["S"]` (2.0), `A` if
`> grade_thresholds["A"]` (0.5), `B` if `> grade_thresholds["B"]` (0.0), `C` if
`> grade_thresholds["C"]` (-0.5), `D` if `> grade_thresholds["D"]` (-1.0), else `F`. This
plan's `assign_grade` reproduces this exact ladder shape (same operators, same descending
order, same "else F" fallthrough) against `GradeConfig.grade_thresholds` — a dict loaded
from this ticket's own config file, structurally identical in shape to
`src/simulation_quality/pillars.py:85-91`'s `GRADE_THRESHOLDS` dict but never imported
from it.

**Decision 6 — Parity ledger: new entry `INFRA-374`, `priority: P2`.** investigation.md's
"Parity Ledger Overlap" section corrects the ticket's own stated Assumption: SimQ's own
grading system is **not** parity-exempt — `SIMQ-CALIBRATED-001`
(`docs/parity_ledger/infrastructure.yaml:3894`, `status: verified`, `priority: P1`) covers
the threshold *values themselves*, and `INFRA-255` (`infrastructure.yaml:4056`, `status:
verified`, `priority: P1`) covers the `normalized_score` combination formula. Neither
covers this ticket's system: this module's grade-assignment code path is structurally
distinct (different module, different combination mechanism, config values copied not
shared) even though it reuses the same numeric threshold table by value. AC #5 requires
confirming this explicitly, which this plan does by adding `INFRA-374`, matching
`INFRA-370`/`371`/`372`/`373`'s exact 8-field shape (`id`, `text`, `status`, `priority`,
`v2_evidence`, `test_path`, `divergence_note`, `proof_type`).

## Steps

### Step 1 — Create `config/rendering/grade_thresholds.toml`

**Files:** `config/rendering/grade_thresholds.toml` (new; new directory, first file in it)

**Change:** Create the directory and file. Confirmed by direct read that no
`config/rendering/` directory exists yet (investigation.md, and the four metric siblings
needed no config at all). Content:

```toml
# Rendering-quality grade-band scorer config (TCK-20260821-VISUAL-GRADE-SCORER).
#
# grade_thresholds below are copied BY VALUE from config/simulation_quality/
# grade_thresholds.yaml (S=2.0 A=0.5 B=0.0 C=-0.5 D=-1.0, confirmed identical by direct
# read) -- this file does NOT import or reference that file. This is a deliberate
# architectural-independence boundary (docs/parity_ledger/infrastructure.yaml INFRA-374;
# staging_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/investigation.md "Parity Ledger
# Overlap"). If SIMQ-CALIBRATED-001 is ever recalibrated, this file must be updated
# manually to match -- there is no code coupling that keeps the two in sync.
#
# Format is TOML, not YAML, deliberately: src/rendering/ is guarded stdlib-only by
# tests/architecture/test_rendering_zero_new_dependency_guard.py, and PyYAML ("yaml")
# is NOT a stdlib module (confirmed: 'yaml' not in sys.stdlib_module_names) even though
# it is a real project dependency elsewhere (requirements.txt, src/simulation_quality/
# weights.py) -- that guard's scope is src/rendering/ specifically, stricter than the
# repo at large. tomllib IS stdlib (Python 3.11+, this repo runs 3.12.3) and supports
# the same nested-table + comment shape YAML would have given. See plan.md Decision 2.
[grade_thresholds]
S = 2.0
A = 0.5
B = 0.0
C = -0.5
D = -1.0

# Hard rules: binary pass/fail facts. No gradient -- a fixed delta on pass, a fixed
# (typically negative) delta on fail. Illustrative values only, NOT calibrated --
# calibration is TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope.
[hard_rules.fully_connected]
pass_delta = 1.0
fail_delta = -1.0

# Soft rules: gradient, healthy-band-shaped (trapezoidal), non-monotonic in the raw
# metric. peak_delta inside [healthy_low, healthy_high]; ramps linearly down to
# min_delta across [low, healthy_low] and [healthy_high, high]; held at min_delta at
# and beyond low/high. Illustrative values only, NOT calibrated.
[soft_rules.fill_ratio_healthy_band]
low = 0.0
healthy_low = 0.3
healthy_high = 0.85
high = 1.0
peak_delta = 1.0
min_delta = -1.0
```

**Other writers to this file:** none — this is a brand-new file in a brand-new directory;
no other ticket or code path writes to `config/rendering/` today (confirmed by
investigation.md).

**Do NOT touch:** `config/simulation_quality/grade_thresholds.yaml` (read-only reference,
never edited or imported).

**Verify:** `python3 -c "import tomllib; tomllib.load(open('config/rendering/grade_thresholds.toml', 'rb'))"`
parses without error; exercised end-to-end by Step 2's `load_grade_config` tests.

### Step 2 — Create `src/rendering/grading.py` with config dataclasses and the fail-loud loader

**Files:** `src/rendering/grading.py` (new)

**Change:** Create the module with a docstring following the four shipped siblings'
provenance convention (cite this ticket, cite the four sibling modules as the outputs
consumed, state explicitly that this module is the intended grading consumer three of the
four sibling docstrings already name — `shape.py:32-37`, `variants.py:28-34`, both read in
full above). Use stdlib `tomllib` (Python 3.11+, this repo runs 3.12.3), **not**
`yaml.safe_load`, to parse the config file — see Decision 2 for the full rationale:
`PyYAML` is a confirmed existing project dependency at the repo level
(`requirements.txt:42`: `PyYAML==6.0.2`; already imported by
`src/simulation_quality/weights.py:4`: `import yaml`), but `src/rendering/` specifically
is guarded stdlib-only by `tests/architecture/test_rendering_zero_new_dependency_guard.py`
(confirmed by direct read and by running `python3 -c "import sys; print('yaml' in
sys.stdlib_module_names)"` → `False`), so `import yaml` inside `grading.py` would fail
that currently-green, must-keep-passing guard test. `tomllib` IS in
`sys.stdlib_module_names` (confirmed directly), so it passes the guard without any
change to the guard itself.

Add:

```python
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "rendering" / "grade_thresholds.toml"
)

_REQUIRED_GRADE_KEYS = ("S", "A", "B", "C", "D")
_REQUIRED_HARD_RULE_KEYS = ("pass_delta", "fail_delta")
_REQUIRED_SOFT_RULE_KEYS = ("low", "healthy_low", "healthy_high", "high", "peak_delta", "min_delta")


@dataclass(frozen=True)
class HardRuleConfig:
    pass_delta: float
    fail_delta: float


@dataclass(frozen=True)
class SoftRuleConfig:
    low: float
    healthy_low: float
    healthy_high: float
    high: float
    peak_delta: float
    min_delta: float


@dataclass(frozen=True)
class GradeConfig:
    grade_thresholds: dict[str, float]
    hard_rules: dict[str, HardRuleConfig]
    soft_rules: dict[str, SoftRuleConfig]


def load_grade_config(path: str | Path = _DEFAULT_CONFIG_PATH) -> GradeConfig:
    ...
```

`load_grade_config` implementation: open `path` in **binary** mode (`"rb"` —
`tomllib.load()` requires a binary file handle, unlike `yaml.safe_load`'s text-mode
acceptance) and `tomllib.load(f)`; then eagerly (at load time, not lazily at score time)
validate and coerce:
1. `raw["grade_thresholds"]` must exist and contain all of `_REQUIRED_GRADE_KEYS`, each a
   `float`/`int` — raise `KeyError` naming the missing key, or `ValueError` naming the
   offending non-numeric value.
2. Each entry under `raw["hard_rules"]` must contain both `_REQUIRED_HARD_RULE_KEYS`,
   numeric — same fail-loud discipline.
3. Each entry under `raw["soft_rules"]` must contain all of `_REQUIRED_SOFT_RULE_KEYS`,
   numeric — same fail-loud discipline. Do not validate `low <= healthy_low <=
   healthy_high <= high` ordering here (out of scope — the illustrative config in Step 1
   already satisfies it; enforcing ordering invariants belongs to
   `TCK-20260821-VISUAL-QUALITY-CALIBRATION` if it ever needs a config-authoring guard).
4. Build and return the frozen `GradeConfig`.

This mirrors SimQ's own `ScoringWeights.load()` fail-loud discipline
(`INFRA-234`, cited in test_plan.md) without importing or reusing `ScoringWeights`/
`pydantic.BaseModel` itself — a fresh, stdlib-only loader, per investigation.md's explicit
guidance against reusing SimQ's Pydantic machinery (and per Decision 2, more strictly
stdlib-only than investigation.md anticipated, since it did not check the
`src/rendering/`-specific guard).

**Other writers to this file:** none — brand-new file, this ticket is its sole author.

**Do NOT touch:** `src/simulation_quality/weights.py` (read-only precedent reference, not
imported, not modified).

**Verify:** `test_config_sources_grade_thresholds_not_hardcoded` (loads real temp config
files, doubling as the "loads from a real file" proof), `test_config_load_fails_loud_on_missing_key`,
`test_config_load_fails_loud_on_non_numeric_value` (new tests, Step 8).

### Step 3 — Hard rule evaluation + the `fully_connected` illustrative hard rule

**Files:** `src/rendering/grading.py` (same file)

**Change:** Add:

```python
@dataclass(frozen=True)
class HardRuleResult:
    name: str
    passed: bool
    delta: float


def evaluate_hard_rule(name: str, passed: bool, config: GradeConfig) -> HardRuleResult:
    rule = config.hard_rules[name]
    delta = rule.pass_delta if passed else rule.fail_delta
    return HardRuleResult(name=name, passed=passed, delta=delta)
```

No numeric literal for `pass_delta`/`fail_delta` appears in this function — both are read
from `config.hard_rules[name]`, satisfying AC #1's "sourced from a config file, never
hardcoded" discipline extended to rule deltas (matching investigation.md's Risks section
guidance on `scoring_weights.yaml`'s data-driven precedent). The illustrative
`fully_connected` hard rule (defined in Step 1's config) is evaluated by callers as
`evaluate_hard_rule("fully_connected", connectivity_result.component_count == 1, config)`
— `ConnectivityResult.component_count` is confirmed to exist at
`src/rendering/connectivity.py:24-29` (the `ConnectivityResult` frozen dataclass), read in
full above; `component_count == 1` means the whole walkable region is a single connected
component (fully reachable map), a genuine binary fact with no gradient.

**Do NOT touch:** `src/rendering/connectivity.py` (read-only input, sibling module, must
remain byte-for-byte unchanged).

**Verify:** `test_hard_rule_binary_shape` (Step 8).

### Step 4 — Soft rule evaluation (trapezoidal, non-monotonic) + the `fill_ratio_healthy_band` illustrative soft rule

**Files:** `src/rendering/grading.py` (same file)

**Change:** Add:

```python
@dataclass(frozen=True)
class SoftRuleResult:
    name: str
    raw_value: float
    delta: float


def _trapezoidal_delta(raw_value: float, rule: SoftRuleConfig) -> float:
    if raw_value <= rule.low or raw_value >= rule.high:
        return rule.min_delta
    if raw_value < rule.healthy_low:
        span = rule.healthy_low - rule.low
        frac = (raw_value - rule.low) / span
        return rule.min_delta + frac * (rule.peak_delta - rule.min_delta)
    if raw_value > rule.healthy_high:
        span = rule.high - rule.healthy_high
        frac = (rule.high - raw_value) / span
        return rule.min_delta + frac * (rule.peak_delta - rule.min_delta)
    return rule.peak_delta


def evaluate_soft_rule(name: str, raw_value: float, config: GradeConfig) -> SoftRuleResult:
    rule = config.soft_rules[name]
    delta = _trapezoidal_delta(raw_value, rule)
    return SoftRuleResult(name=name, raw_value=raw_value, delta=delta)
```

All boundary/delta numbers (`low`, `healthy_low`, `healthy_high`, `high`, `peak_delta`,
`min_delta`) are read from `config.soft_rules[name]` — none appear as literals in this
function. This is by construction non-monotonic in `raw_value`: strictly increasing from
`min_delta` to `peak_delta` on `[low, healthy_low]`, flat at `peak_delta` on
`[healthy_low, healthy_high]`, strictly decreasing from `peak_delta` to `min_delta` on
`[healthy_high, high]`, flat at `min_delta` at and beyond both `low` and `high` —
positive inside the healthy band, negative at both extremes, satisfying AC #2 exactly.

The illustrative `fill_ratio_healthy_band` soft rule (config from Step 1: `low=0.0,
healthy_low=0.3, healthy_high=0.85, high=1.0, peak_delta=1.0, min_delta=-1.0`) is
evaluated by callers as `evaluate_soft_rule("fill_ratio_healthy_band",
shape_component.fill_ratio, config)` — `ShapeComponent.fill_ratio` is confirmed to exist
at `src/rendering/shape.py:51-57` (the `ShapeComponent` frozen dataclass), read in full
above: "tiles / bbox area, per connected component." With this illustrative config: a
`fill_ratio` of `0.5` (comfortably inside `[0.3, 0.85]`) yields `delta = 1.0`; a
`fill_ratio` of `0.05` (well below `0.3`, near `low=0.0`) yields a delta close to `-1.0`;
a `fill_ratio` of `0.98` (well above `0.85`, near `high=1.0`) also yields a delta close to
`-1.0` — the concrete three-point non-monotonicity example AC #2's test requires. These
numbers are explicitly illustrative, not calibrated against real corpus fill-ratio
distributions (`TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s job, per investigation.md).

**Do NOT touch:** `src/rendering/shape.py` (read-only input, sibling module, must remain
byte-for-byte unchanged).

**Verify:** `test_soft_rule_non_monotonicity_three_point` (Step 8) — the ticket's single
most novel piece of math, per investigation.md, needs the most explicit coverage.

### Step 5 — Combine hard+soft rule deltas into one score

**Files:** `src/rendering/grading.py` (same file)

**Change:** Add:

```python
def combine_rule_deltas(
    hard_results: list[HardRuleResult],
    soft_results: list[SoftRuleResult],
) -> float:
    return sum(r.delta for r in hard_results) + sum(r.delta for r in soft_results)
```

Plain addition, mirroring `PillarAccumulator.add()`'s own additive combination pattern
(`src/simulation_quality/pillar_accumulator.py:43-58`, cited in investigation.md) for this
narrow "sum signed floats" step — the one piece of SimQ's combination mechanism this plan
reuses in spirit, per investigation.md's explicit statement that the *shape* (sum) is
reusable even though the *per-rule* shape (fixed vs. trapezoidal) is not. A strictly
larger positive delta set (holding all else fixed) strictly increases the returned sum,
even though each individual soft rule is non-monotonic in its own raw input — this
distinction (monotonic in the *combination*, non-monotonic in each *soft rule's raw
input*) is exactly what test_plan.md's "combination step" test asserts.

**Other writers to `combine_rule_deltas`'s inputs:** none — `HardRuleResult`/
`SoftRuleResult` are produced only by Steps 3-4's functions within this same module; no
other code path constructs or mutates them.

**Do NOT touch:** `src/simulation_quality/pillar_accumulator.py` (read-only precedent
reference, not imported).

**Verify:** `test_combination_step_produces_single_normalized_score` (Step 8).

### Step 6 — Grade assignment reusing SimQ's exact threshold table and comparison semantics

**Files:** `src/rendering/grading.py` (same file)

**Change:** Add:

```python
def assign_grade(combined_score: float, grade_thresholds: dict[str, float]) -> str:
    if combined_score > grade_thresholds["S"]:
        return "S"
    if combined_score > grade_thresholds["A"]:
        return "A"
    if combined_score > grade_thresholds["B"]:
        return "B"
    if combined_score > grade_thresholds["C"]:
        return "C"
    if combined_score > grade_thresholds["D"]:
        return "D"
    return "F"
```

This reproduces `src/simulation_quality/quality_report.py::_assign_grade`'s exact ladder
(lines 72-83, read directly above) — same strict `>` (never `>=`) comparison, same
descending `S → A → B → C → D → F` order, same "else F" fallthrough. No numeric literal
for any threshold appears in this function; `grade_thresholds` is
`GradeConfig.grade_thresholds`, loaded by Step 2's `load_grade_config` from `config/
rendering/grade_thresholds.toml` (Step 1), never from `config/simulation_quality/
grade_thresholds.yaml` and never imported from `src.simulation_quality.pillars.
GRADE_THRESHOLDS`. This satisfies AC #1 in full: correct letter per the exact reused
threshold table, sourced from a config file, not hardcoded.

**Do NOT touch:** `src/simulation_quality/quality_report.py` (read-only reference for the
ladder shape only; not imported, not modified — this ticket's `assign_grade` is a fresh
function, structurally identical but not a shared call target).

**Verify:** `test_grade_assignment_boundaries` (Step 8) — synthetic scores at and around
each of the five thresholds plus one value comfortably inside each band.

### Step 7 — Multi-seed averaging

**Files:** `src/rendering/grading.py` (same file)

**Change:** Add:

```python
def average_scores(per_seed_scores: list[float]) -> float:
    return sum(per_seed_scores) / len(per_seed_scores)
```

No `len(per_seed_scores) == 1` branch — a plain arithmetic mean satisfies both the N=1
identity case and the N>1 mean case by construction (Decision 4 above). This function has
no dependency on `GradeConfig` or any other part of this module; it operates on plain
`list[float]` (already-combined-and-averaged-per-seed scores, or any other list of
floats), matching investigation.md's explicit requirement that the signature "genuinely
generalize to N>1... not special-cased to assume N is always 1."

**Other writers to this function's conceptual "multi-seed score list" input:** none exist
yet — investigation.md confirms no current code path in the repo produces N>1 distinct
per-seed scores through the normal world-load path (`VARIANTS-METRIC`'s stale-cache
finding). This function is written to generalize correctly regardless; no caller wiring
it into a real multi-seed sweep is part of this ticket's scope (`tools/calibrate_simq.py`'s
existing `--seed`-per-invocation CLI pattern is the only real multi-seed precedent in the
repo, and this ticket does not modify it).

**Do NOT touch:** `tools/calibrate_simq.py` (read-only precedent reference for
multi-seed sweeping conventions; not imported, not modified — wiring this function into
an actual multi-seed sweep tool is out of this ticket's scope).

**Verify:** `test_multi_seed_averaging_n1_identity`, `test_multi_seed_averaging_n_gt_1_synthetic_mean` (Step 8).

### Step 8 — Write `tests/unit/rendering/test_grading.py`

**Files:** `tests/unit/rendering/test_grading.py` (new)

**Change:** Create the test file mirroring `tests/unit/rendering/test_density.py`'s and
`tests/unit/rendering/test_shape.py`'s structure and import conventions (`WorldRepository
("data/worlds").load_world(...)` → `WorldCompiler.compile(spec, seed=42)` for the
real-corpus smoke test; plain synthetic fixtures for everything else). Implement every
test from test_plan.md's "New Tests Required" section:

1. `test_grade_assignment_boundaries` — parametrized over `2.0`, `2.0001`, `0.5`,
   `0.5001`, `0.0`, `0.0001`, `-0.5`, `-0.5001`, `-1.0`, `-1.0001`, plus one value
   comfortably inside each band; assert `assign_grade` returns exactly the letter
   SimQ's own `_assign_grade` would (strict `>`, not `>=`).
2. `test_config_sources_grade_thresholds_not_hardcoded` — load two `GradeConfig`s from two
   different temp `.toml` files (`tmp_path` fixture, real TOML `[section]`/`key = value`
   syntax matching Step 1's shape, written and opened in binary mode per `tomllib.load()`'s
   contract) with different `grade_thresholds` values, assert `assign_grade` on the same
   `combined_score` returns a different letter for each — proves runtime config-sourcing,
   matching test_plan.md's stated "simpler, still-valid alternative" to an AST-literal scan.
3. `test_config_load_fails_loud_on_missing_key` — a temp `.toml` file missing
   `grade_thresholds`'s `"D"` key (or a hard/soft rule's required key); assert
   `load_grade_config` raises `KeyError` at load time.
4. `test_config_load_fails_loud_on_non_numeric_value` — a temp `.toml` file with a string
   value where a threshold/delta/boundary number is expected; assert `load_grade_config`
   raises `ValueError` at load time.
5. `test_hard_rule_binary_shape` — `evaluate_hard_rule("fully_connected", True, config)`
   returns exactly `config.hard_rules["fully_connected"].pass_delta`;
   `evaluate_hard_rule("fully_connected", False, config)` returns exactly `.fail_delta` —
   two-value output only, no gradient.
6. `test_soft_rule_non_monotonicity_three_point` — using the `fill_ratio_healthy_band`
   config, assert `evaluate_soft_rule(..., 0.5, config).delta > 0` (inside band),
   `evaluate_soft_rule(..., 0.05, config).delta < 0` (well below `healthy_low`), AND
   `evaluate_soft_rule(..., 0.98, config).delta < 0` (well above `healthy_high`) — three
   explicit assertions, per test_plan.md's Anti-Drift Test Guards warning that "positive
   somewhere, negative somewhere" alone would not catch an accidentally-monotonic
   implementation.
7. `test_combination_step_produces_single_normalized_score` — fixed synthetic hard+soft
   result lists; assert `combine_rule_deltas` returns a single float; assert that
   replacing one result with a strictly larger delta (holding the rest fixed) strictly
   increases the returned sum.
8. `test_multi_seed_averaging_n1_identity` — `average_scores([2.5]) == 2.5` exactly (not
   `pytest.approx`).
9. `test_multi_seed_averaging_n_gt_1_synthetic_mean` — `average_scores([1.0, 2.0, 3.0]) ==
   2.0` exactly.
10. `test_grading_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` —
    mirrors `test_density.py:147-165`'s exact AST-walk pattern (read in full above),
    adapted to `src/rendering/grading.py`'s path: no class with `PillarScorer` in its
    base list; no import containing `"simulation_quality"` or `"observability.events"`.
11. `test_grading_module_does_not_register_new_pillar_id` — snapshot
    `set(src.simulation_quality.pillars.PillarId)` (10 members: `COGNITION`, `AGENCY`,
    `COMBAT`, `FACTION`, `ECONOMY`, `PROGRESSION`, `SOCIAL`, `INFORMATION`, `WORLD`,
    `NARRATIVE` — confirmed by direct read, `src/simulation_quality/pillars.py:5-15`)
    and assert it is unchanged from this fixed baseline. No pre-existing baseline test for
    this was confirmed to exist elsewhere (test_plan.md flags this as unconfirmed); this
    plan places it in `test_grading.py` since none was found.
12. `test_grading_module_has_zero_image_or_render_dependency` — mirrors
    `test_density.py`/`test_shape.py`'s existing pattern: AST-parse `grading.py`, assert
    no import contains `png_writer`, `rendering.render`, `rendering.incremental`, `PIL`,
    or `Pillow`.
13. `test_grading_does_not_mutate_inputs` — construct a real `ConnectivityResult` and
    `ShapeComponent` (or their primitive builders), call `evaluate_hard_rule`/
    `evaluate_soft_rule` against them, assert the same objects are unchanged afterward
    (they are frozen dataclasses, so this also implicitly confirms no reconstruction
    swapped fields) — mirrors `test_density.py::test_does_not_mutate_authoritative_state`.
14. `test_real_corpus_grading_smoke_test` — load `dungeon_crawl` via `WorldRepository
    ("data/worlds").load_world(...)` → `WorldCompiler.compile(spec, seed=42)`, run
    `analyze_connectivity`, `connected_components` (shape.py) on the compiled state, build
    one hard-rule result (`fully_connected`) and at least one soft-rule result
    (`fill_ratio_healthy_band`, over the first `ShapeComponent` returned) via
    `evaluate_hard_rule`/`evaluate_soft_rule`, `combine_rule_deltas` them,
    `assign_grade` the result. Assert the returned grade is one of
    `{"S", "A", "B", "C", "D", "F"}` and the combined score is a finite float — per
    test_plan.md's Anti-Drift Test Guards, do **not** pin a specific letter/value as a
    regression anchor, since the illustrative thresholds are explicitly uncalibrated.

**Do NOT touch:** any existing file in `tests/unit/rendering/` (all listed in
test_plan.md's Regression Surface as "must keep passing, no change expected") or
`tests/simulation_quality/` (must stay green as an anti-coupling guard, not modified).

**Verify:** `.venv/bin/python3 -m pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v`
and `.venv/bin/python3 -m pytest tests/simulation_quality/test_report.py tests/simulation_quality/test_weights.py tests/simulation_quality/test_grade_regression.py -v`
both fully green, per test_plan.md's Scoped Pytest Commands (bare directories/explicit
file lists, never `pytest tests/`).

### Step 9 — Add parity ledger entry `INFRA-374`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Confirmed by direct read (`grep -n "^- id: INFRA-3" docs/parity_ledger/
infrastructure.yaml | tail`) that `INFRA-373` (line 10877) is the current maximum
`INFRA-*` id and the last entry in the file, so `INFRA-374` is genuinely the next
available id. Append at the end of the file, following `INFRA-370`-`373`'s exact 8-field
shape (read directly, lines 10840-10889):

```yaml
- id: INFRA-374
  text: Rendering-quality grade-band scorer assigns S/A/B/C/D/F using SimQ's exact
    threshold values (S=2.0 A=0.5 B=0.0 C=-0.5 D=-1.0), sourced from its own config file
    (config/rendering/grade_thresholds.toml, copied by value, not imported from
    config/simulation_quality/), combining binary hard-rule and non-monotonic
    trapezoidal soft-rule deltas via a plain additive sum before assignment. This
    architecturally-independent code path is distinct from SIMQ-CALIBRATED-001 (which
    covers SimQ's own threshold-value calibration status) and INFRA-255 (which covers
    SimQ's own normalized_score time-division formula) -- neither entry covers this
    module's separate grade-assignment code path.
  status: verified
  priority: P2
  v2_evidence: src/rendering/grading.py
  test_path: tests/unit/rendering/test_grading.py::test_grade_assignment_boundaries
  divergence_note: null
  proof_type: parity
```

**Other writers to this file:** `docs/parity_ledger/infrastructure.yaml` is a single YAML
list appended to by every ticket that lands a new infrastructure-layer parity fact. The
four upstream siblings (`INFRA-370`-`373`) are already merged and DONE (confirmed present,
`stored_artifacts/TCK-20260821-VISUAL-{CONNECTIVITY,DENSITY,SHAPE,VARIANTS}-METRIC/`), so
there is no concurrent-write race with those. Per this repo's CLAUDE.md Hard Rules (shared
working directory across sessions), if a concurrent session has appended further entries
since the read above, re-run the `grep` immediately before appending to confirm
`INFRA-374` is still the next free id; do not hardcode the number if the file has moved.

**Do NOT touch:** `docs/plans/world_rendering/idea_world_render_validation.md` (deliberately
deferred to the batch's final ticket, `TCK-20260821-VISUAL-QUALITY-DOCS`, per
investigation.md's Docs Requiring Update section) or `docs/simulation_quality/
quality_scoring_contract.md` (documents SimQ's own model; not applicable here, per the
same section).

**Verify:** no automated test covers this file directly; `done-checker`'s
frontmatter/parity checks validate it structurally. Manually confirm the new entry parses
as valid YAML: `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`.
The cited `test_path` must exist and pass (Step 8) before this entry can honestly claim
`status: verified`.

## Scope Guards

Must NOT be touched or introduced by this ticket, per the ticket's Out of Scope,
investigation.md's Anti-Drift Hazards, and the orchestrator's explicit instructions:

- **No `import src.simulation_quality.*` anywhere** in `src/rendering/grading.py`,
  `config/rendering/grade_thresholds.toml`, or `tests/unit/rendering/test_grading.py`.
- **No `import src.observability.events`** (or `ObservabilityEventEnvelope`,
  `QualityHub`, `PillarAccumulator`, `ScoringContext` specifically) anywhere in the new
  module or its tests.
- **No `PillarScorer` subclass** anywhere — `src/simulation_quality/scorers/base.py:11`
  (`class PillarScorer(ABC)`, read in full above) is never subclassed.
- **No new `PillarId` enum member** — `src/simulation_quality/pillars.py`'s `PillarId`
  (10 members, confirmed by direct read) stays byte-identical; Step 8's test 11 guards
  this explicitly.
- **No hardcoded threshold/delta/boundary numeric literal in `grading.py`'s scorer/loader
  functions** — every threshold, `pass_delta`/`fail_delta`, and
  `low`/`healthy_low`/`healthy_high`/`high`/`peak_delta`/`min_delta` value is read from
  `GradeConfig`, sourced from `config/rendering/grade_thresholds.toml`. (Test fixtures in
  `test_grading.py` legitimately contain numeric literals as inputs — that is not a
  violation; the guard applies to the scorer/loader code itself.)
- **No monotonic soft rules and no graduated hard rules** — the AC1/AC2 architectural
  line investigation.md flags: hard rules stay strictly binary (`evaluate_hard_rule`
  returns exactly one of two values per rule), soft rules stay strictly non-monotonic
  (trapezoidal, per Step 4).
- **No N=1 special-casing in `average_scores`** — a plain `sum(...) / len(...)`, no
  `if len(...) == 1` branch (Decision 4, Step 7).
- **No CI-gating this system anywhere** — report-only, matching all four upstream
  siblings' identical constraint; do not add `grading.py`, its config, or its tests to any
  regression-baseline/gate-check manifest.
- **No importing `config/simulation_quality/grade_thresholds.yaml`** from
  `src/rendering/grading.py` or its config loader — `config/rendering/
  grade_thresholds.toml` (Step 1) is the sole config source, values copied by hand, not
  referenced.
- **Do not modify any of the four sibling metric modules**
  (`connectivity.py`/`density.py`/`shape.py`/`variants.py`) — read-only inputs throughout.
- **Do not modify `docs/plans/world_rendering/idea_world_render_validation.md` or
  `docs/simulation_quality/quality_scoring_contract.md`** — deferred/not applicable, per
  investigation.md.
- **Data-lookup or placement-legality checks are out of scope** — this module consumes
  already-computed metric outputs only; it does not re-derive walkability, occupancy, or
  legality itself (that remains `LegalityServiceV2`'s and the sibling modules' concern).

## Dependency Map

- Step 1 (config file) has no dependencies; it is the first step.
- Step 2 (`GradeConfig` dataclasses + `load_grade_config`) depends on Step 1 (the config
  file's exact key shape).
- Step 3 (hard rule evaluation) depends on Step 2 (`GradeConfig`, `HardRuleConfig`).
- Step 4 (soft rule evaluation) depends on Step 2 (`GradeConfig`, `SoftRuleConfig`); it is
  independent of Step 3 — either could be implemented first.
- Step 5 (`combine_rule_deltas`) depends on Steps 3 and 4 (`HardRuleResult`,
  `SoftRuleResult` types).
- Step 6 (`assign_grade`) depends only on Step 2 (`GradeConfig.grade_thresholds`); it is
  independent of Steps 3-5 and could be implemented in parallel with them.
- Step 7 (`average_scores`) has no dependency on any other step — it operates on plain
  `list[float]` with no `GradeConfig` involvement; it could be implemented first or last.
- Step 8 (tests) depends on all of Steps 1-7 being complete, since `test_grading.py`
  exercises every function.
- Step 9 (parity ledger) depends on Step 8 passing, since the new entry's `test_path`
  cites a specific test that must exist and pass before the entry can honestly claim
  `status: verified`.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: Grade assignment returns the correct letter per the exact reused threshold table (S:2.0, A:0.5, B:0.0, C:-0.5, D:-1.0), sourced from a config file, not hardcoded | Step 1 (config), Step 2 (loader), Step 6 (`assign_grade`) | `test_grade_assignment_boundaries`, `test_config_sources_grade_thresholds_not_hardcoded` |
| AC #2: A soft rule with a healthy band produces a positive delta inside its range and a negative delta at BOTH low and high extremes (non-monotonic) | Step 1 (config), Step 4 (`evaluate_soft_rule`/`_trapezoidal_delta`) | `test_soft_rule_non_monotonicity_three_point` |
| AC #3: Given N per-seed scores for one world spec, the averaged score equals the arithmetic mean; with N=1 it equals that single score exactly | Step 7 (`average_scores`) | `test_multi_seed_averaging_n1_identity`, `test_multi_seed_averaging_n_gt_1_synthetic_mean` |
| AC #4: The module does not import ObservabilityEventEnvelope, QualityHub, PillarAccumulator, or ScoringContext, and does not register a new PillarId | Steps 2-7 (module contains zero such imports by construction; no `PillarId` touched) | `test_grading_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`, `test_grading_module_does_not_register_new_pillar_id` |
| AC #5: This ticket explicitly confirms (not assumes) whether the sibling system needs a parity-ledger entry or is exempt like SimQ's own grading system | Step 9 (`INFRA-374` added, with explicit text citing why `SIMQ-CALIBRATED-001`/`INFRA-255` do not cover this code path) | N/A (docs, no automated test; `done-checker` structural validation) |
| Combination step (real design risk named in ticket Scope, not a separate numbered AC but load-bearing) | Step 5 (`combine_rule_deltas`) | `test_combination_step_produces_single_normalized_score` |

## Anti-Drift Notes

- **The trapezoidal soft-rule shape is the single most load-bearing, genuinely novel piece
  of math in this plan.** It must produce `peak_delta` (positive, per the illustrative
  config) inside `[healthy_low, healthy_high]` and `min_delta` (negative) at and beyond
  both `low` and `high` — not just "somewhere positive, somewhere negative." Step 8's test
  6 asserts all three points explicitly; test_plan.md's Anti-Drift Test Guards flags this
  as the most likely silent scope-creep failure mode (an implementer building a familiar
  monotonic "higher is always better, capped" rule instead, since that is exactly what
  every SimQ rule already does).
- **`average_scores` must never special-case N=1.** `sum(x)/len(x)` alone satisfies both
  AC #3 cases; any `len == 1` branch is dead weight this plan explicitly does not want,
  even though it would technically pass today's only real-corpus-observable case.
- **The two config files (`config/rendering/grade_thresholds.toml` and `config/
  simulation_quality/grade_thresholds.yaml`) are duplicated by value, not shared by
  reference — this is an accepted, documented cost, not a bug to fix.** Do not introduce a
  shared "grade thresholds" helper module or import between the two config trees; that
  would reintroduce the coupling this ticket's independence requirement forbids.
- **`assign_grade`'s comparison semantics must match `_assign_grade`'s exactly**: strict
  `>`, never `>=`, same descending order, same "else F" fallthrough. A boundary test
  (`combined_score == 2.0` exactly) must land on `A`, not `S` — this is a common off-by-one
  mistake the boundary-parametrized test (Step 8, test 1) exists specifically to catch.
- **Do not import `src.simulation_quality.pillars.GRADE_THRESHOLDS`** as a shortcut to
  avoid re-typing the five values in `config/rendering/grade_thresholds.toml` — that would
  violate both the architectural-independence Out of Scope item and Decision 2's explicit
  "copied by value, not by reference" design.
- **This ticket's illustrative `fully_connected`/`fill_ratio_healthy_band` rules are the
  only rules this plan builds.** Do not add further hard/soft rules from
  investigation.md's other candidate list (`entity_count >= 2`, `percent_reachable`,
  `DensityResult.cv`, `total_variation_distance`) — those are legitimate future rules but
  expanding the rule set is not required by any AC and would be scope creep beyond what
  this ticket's Scope/AC text asks for; a future ticket (plausibly
  `TCK-20260821-VISUAL-QUALITY-CALIBRATION`) can add more once real thresholds are
  calibrated.
- **`percent_reachable`'s definition is resolved, not open**: `ConnectivityResult.
  percent_reachable` is `component_sizes[0] / walkable_count * 100.0`
  (`src/rendering/connectivity.py:78-80`, confirmed by direct read) — largest-component-
  relative. This plan's illustrative rules do not consume `percent_reachable` directly
  (they use `component_count` and `fill_ratio`), but any future rule built on it should be
  written against this confirmed definition.
- **Use `tomllib`, never `yaml`, inside `src/rendering/grading.py`.** This was verified,
  not assumed: `'yaml' not in sys.stdlib_module_names` (confirmed by direct run) means
  `import yaml` inside `src/rendering/` would fail `tests/architecture/
  test_rendering_zero_new_dependency_guard.py`'s currently-green, must-keep-passing
  stdlib-only check (test_plan.md's own Regression Surface). `tomllib` (Python 3.11+,
  confirmed present in `sys.stdlib_module_names`, this repo runs 3.12.3) is the corrected
  choice — see Decision 2. Do not "fix" a guard-test failure here by loosening
  `test_rendering_zero_new_dependency_guard.py`'s allowlist; that guard is a deliberate,
  documented `src/rendering/`-specific boundary from `TCK-20260821-WORLD-RENDER-CORE`, and
  CLAUDE.md forbids editing a gate to make it pass instead of fixing the underlying
  substance (here, the underlying substance is "pick a stdlib-parseable config format").

## Deviations

- **`load_grade_config`'s body was written from the plan's prose description, not from
  verbatim code** — Step 2's own code block ends its function with `...`; only the
  four-point validation discipline was given in prose. Implemented as a small private
  `_require_numeric(container, key, context)` helper reused across the
  `grade_thresholds`/`hard_rules`/`soft_rules` sections, raising `KeyError` on a missing
  key and `ValueError` on a non-numeric value, matching the described fail-loud
  discipline exactly. `hard_rules`/`soft_rules` top-level tables are read via
  `raw.get(name, {})` rather than a hard `raw["hard_rules"]` index — the plan's prose
  only requires each *entry* under those tables to be fail-loud-validated, not that the
  table itself must exist; this satisfies all four of Step 8's config-loader tests
  without adding an unrequired constraint.
- **Step 8 test 1's exact boundary-value list had one wrong expected grade, caught and
  fixed during implementation.** Hand-tracing `assign_grade`'s strict-`>` ladder against
  the illustrative thresholds showed `-0.5001` lands on grade `D` (not `C` as an initial
  draft assumed) — `-0.5001 > -0.5` is False, so the ladder falls through to
  `-0.5001 > -1.0`, True, `D`. Fixed the test fixture (not `assign_grade`, which is
  unchanged verbatim from Step 6) and added an explicit "comfortably inside D band"
  case (`-0.75 -> D`) that the original 10-point list omitted. No production code
  changed as a result — this was a test-fixture-only correction.
