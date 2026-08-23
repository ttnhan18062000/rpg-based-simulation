---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-AGENT-REVIEW
artifact_type: plan
tags: [visualization, simulation-quality, determinism, world]
---

# Implementation Plan — TCK-20260821-VISUAL-AGENT-REVIEW

## Summary

This ticket adds two new `src/rendering/` modules and one new `.claude/agents/` file to
close the Tier 0 (pure data) → Tier 1 (JSON digest) → Tier 2 (annotated image, fetched
only on escalation) agent-review pipeline. `src/rendering/render_annotated.py` is a new
module — ported, near-verbatim, from `experiments/spatial_rendering/prototype/
render_annotated.py`'s `render_annotated()` (gridlines every N tiles + the hand-rolled
3×5 bitmap-digit axis-label font), reusing `render.py`'s own `terrain_color`/
`DEFAULT_TERRAIN_COLOR` palette by import rather than duplicating it, and
`png_writer.write_png` exactly as `render.py` does — stdlib-only throughout, no Pillow.
`src/rendering/review_pipeline.py` is a new module implementing `should_escalate`
(composing `grading.py`'s real `HardRuleResult`/grade output, no new config), the
`Tier1Digest` frozen dataclass + `digest_to_json` serializer, and the orchestrating
`run_tier0_tier1_pipeline` entry point that calls the four already-shipped sibling metric
modules plus `grading.py`, and calls the new `render_annotated()` **only** when
`should_escalate(...)` returns `True` — the annotated PNG file structurally does not
exist on disk in the non-escalating case, which is this plan's answer to AC #1's
"zero image is ever fetched" requirement (a gate at the render step, not an
unenforceable tool-list restriction). `.claude/agents/world-render-reviewer.md` is a new
subagent file, structurally modeled on `simulation-analyst.md`'s Data Sources / Analysis
Dimensions / Severity Classification / Output shape, but with zero Mechanics Bible
citations (this domain is pure geometry/statistics, confirmed twice now by this batch's
own investigations) and a severity vocabulary redefined in visual/geometric terms. A new
parity ledger entry `INFRA-375` and an extension to `docs/engine/contracts/
regression_and_verification.md` close out the documentation requirements. No change to
any of the six already-shipped sibling modules, `render.py`, `incremental.py`, or any
SimQ code.

## Key Decisions

**Decision 1 — New module placement: `src/rendering/render_annotated.py` and
`src/rendering/review_pipeline.py`, both flat files, not a subpackage.** Matches the
existing flat-file convention of every prior sibling (`connectivity.py`, `density.py`,
`shape.py`, `variants.py`, `grading.py`, `render.py`, `incremental.py`, `png_writer.py` —
confirmed via `src/rendering/` directory listing, no subpackages exist today) and this
batch's own established precedent (`stored_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/
plan.md` Decision 1, same reasoning applied to `grading.py`). `review_pipeline.py`'s name
matches `test_plan.md`'s own suggested test file `tests/unit/rendering/
test_review_pipeline.py` (test 1, line 58) — module name and test-file name pair up the
same way every other sibling does (`grading.py` ↔ `test_grading.py`).

**Decision 2 — `run_tier0_tier1_pipeline` reads `seed`/`tick` from `state.seed`/
`state.tick` directly (confirmed fields, `src/core/state.py:1090-1091`:
`tick: int` / `seed: int` on `AuthoritativeState`), but takes `world_id: str` as a
required explicit parameter, not a state field.** Verified directly: `AuthoritativeState`
(`src/core/state.py:1083-1137`, read in full) has no `world_id` field anywhere in its
dataclass definition, and `render()`'s own stats-dict return (`src/rendering/render.py:
143-155`) has no `world_id` key either. `WorldRepository`/`WorldCompiler` (the only place
`world_id` exists as a string, e.g. `"dungeon_crawl"`, `"sandbox_world"`) is the caller's
concern, not something derivable from `state` — matching how the prototype's own
`__main__` block (`experiments/spatial_rendering/prototype/render_annotated.py:102-104`)
takes `world_id` from `sys.argv`, not from `state`. Reading `seed`/`tick` from `state`
directly (rather than also taking them as separate parameters) is a deliberate
correctness choice: a caller-supplied `seed`/`tick` that drifted from the state's actual
content would silently corrupt the digest's own determinism claim (AC #3) without any
test catching it; sourcing them from `state` makes the digest's `seed`/`tick` fields
provably consistent with the state that was actually scored.

**Decision 3 — the pipeline does not itself call `render()` (the plain renderer) or
write a plain PNG. `plain_render_path` is a computed path only, via the existing
`render_output_path(base_dir, run_id, filename)` helper (`src/rendering/render.py:
158-166`, confirmed signature and confirmed `{base_dir}/{run_id}/renders/{filename}`
join, no `RunArtifactRepository` routing), not a promise that the file exists.**
Confirmed via `grep -rn "rendering.render import render" src/` (zero hits) that nothing
in `src/` currently calls `render()` automatically today — there is no existing "produce
the plain render" pipeline this ticket's own Out of Scope ("Any change to the renderer
itself... beyond consuming their output") would let it create or modify. Investigation's
own field comment for this field — `plain_render_path: str | None  # render_output_
path(...)'s output, always present` — is consistent with this reading: `render_output_
path` is a pure path-join with no I/O, so it is unconditionally computable regardless of
whether any process has actually written a plain PNG to that path yet. `annotated_render_
path` is different in kind: it is `None` unless `escalate` is `True`, and when `True` the
pipeline itself calls the new `render_annotated()` and creates the file at that exact
path — this asymmetry (plain = path only, annotated = path AND file, conditionally) is
the direct mechanism behind AC #1/#2.

**Decision 4 — the illustrative soft rule (`fill_ratio_healthy_band`) is evaluated
against exactly one `ShapeComponent`: the first one `connected_components(state.terrain)`
returns, matching `tests/unit/rendering/test_grading.py`'s own real-corpus smoke test
convention ("over the first `ShapeComponent` returned", confirmed at `test_grading.py`
test 14 per `stored_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/plan.md` Step 8). If
`connected_components(...)` returns an empty list (no component both ≥ `min_size=20` and
outside the default `excluded_types={"PLAIN","ROAD"}` — both confirmed defaults at
`src/rendering/shape.py:125-126`), no soft rule is evaluated at all
(`soft_rule_results = ()`), and `combined_score` is the hard-rule deltas sum only. This is
a genuine edge case (a world with no large non-trivial terrain patch) that must not raise
— `evaluate_soft_rule` would otherwise be called with no real component to evaluate, an
arbitrary/undefined choice this plan deliberately avoids making up a placeholder for.**

**Decision 5 — `flagged_shape_components` is computed independently of which component
feeds the soft rule: every `ShapeComponent` in the full `connected_components(...)` list
whose `fill_ratio` falls outside `[config.soft_rules["fill_ratio_healthy_band"].
healthy_low, .healthy_high]` is included**, using the same `SoftRuleConfig` bounds
`evaluate_soft_rule`/`_trapezoidal_delta` already use internally (`src/rendering/
grading.py:47-54, 128-139`, confirmed field names `low/healthy_low/healthy_high/high/
peak_delta/min_delta`) — not a second, independently-invented threshold. Each flagged
entry is `{"terrain_type": sc.terrain_type, "bbox": sc.bbox, "fill_ratio": sc.fill_ratio}`
(`ShapeComponent`'s exact three non-tile fields relevant to a citable finding, confirmed
at `src/rendering/shape.py:52-57`: `terrain_type: str`, `bbox: tuple[int,int,int,int]`,
`fill_ratio: float` — `tiles`/`size` are deliberately excluded from the digest, since
`tiles` is a potentially large `frozenset` unsuitable for a "compact" Tier 1 payload per
the ticket's own framing, and `size` is redundant with `bbox`+`fill_ratio` for a citable
finding). **The resulting tuple is explicitly `sorted(..., key=lambda d: (d["terrain_type"],
d["bbox"]))` before being stored** (Review-caught, independently confirmed:
`connected_components`'s own internal iteration order (`src/rendering/shape.py:145`,
`for start in tile_set:` over a plain Python `set[tuple[int,int]]`) has no documented or
tested ordering guarantee — it is an incidental property of CPython's set/hash-table
internals, not a contract this ticket's Out of Scope permits depending on since it cannot
touch `shape.py` itself. `json.dumps(..., sort_keys=True)` (Step 4) sorts dict *keys*, not
array/tuple *element order* — it would not by itself catch a `flagged_shape_components`
ordering drift. Explicitly sorting the tuple here makes AC #3's determinism claim
self-contained within this ticket's own code, not silently reliant on an upstream
module's unstated internal behavior.)

**Decision 6 — `.claude/agents/world-render-reviewer.md`, new file, not folded into
`simulation-analyst.md`.** Adopts investigation.md's recommendation verbatim — confirmed
independently by directly reading `simulation-analyst.md` in full (above): every one of
its five Analysis Dimensions cites a specific Mechanics Bible chapter (`Ch01+Ch05`,
`Ch02`, `Ch03`, `Ch04`, `Ch05` — literal subsection headers at lines 20, 25, 30, 35, 40),
and its `## Output` section (lines 52-58) has five numbered parts (0-4), not the three the
ticket's own paraphrase compresses to. No `tools:` frontmatter key exists on
`simulation-analyst.md` (confirmed, only `name:`/`description:` at lines 2-3) — the new
agent gets the same default full-tool access, `Read` included, so Tier 2 escalation can
actually read the annotated PNG.

## Steps

### Step 1 — Port `render_annotated()` into `src/rendering/render_annotated.py`

**Files:** `src/rendering/render_annotated.py` (new)

**Change:** Create the module by porting `experiments/spatial_rendering/prototype/
render_annotated.py`'s `render_annotated()` function (lines 49-98, read in full above)
near-verbatim, with exactly these changes from the prototype:
1. Drop the `sys.path.insert(...)` bootstrap lines (prototype lines 7-11) — not needed in
   a properly importable `src.rendering` module, matching how `src/rendering/render.py`'s
   own promotion from `render_world.py` (`TCK-20260821-WORLD-RENDER-CORE`) already dropped
   equivalent prototype-only bootstrap code (confirmed: `render.py` has no `sys.path`
   manipulation anywhere).
2. Replace `from png_writer import write_png` with
   `from src.rendering.png_writer import write_png` (confirmed real function signature:
   `write_png(path: str, width: int, height: int, pixels: list[tuple[int,int,int]]) ->
   None`, `src/rendering/png_writer.py:12`).
3. Replace `from render_world import terrain_color, DEFAULT_TERRAIN_COLOR` with
   `from src.rendering.render import terrain_color, DEFAULT_TERRAIN_COLOR` — both names
   are confirmed real, already-exported top-level names in the promoted `render.py`
   (`terrain_color` function at `src/rendering/render.py:47`, `DEFAULT_TERRAIN_COLOR`
   constant at line 44). This reuses the exact same palette `render.py` already uses —
   satisfies test 8's "non-gridline pixels use the same `terrain_color()`/entity-color
   palette `render.py` already uses (no independent, drifted color table)" requirement by
   construction, not by duplicating the color dict.
4. Keep the `DIGITS` dict (3×5 bitmap font, lines 19-30) and `draw_text()` (lines 33-46)
   verbatim — this is the "hand-rolled font" the orchestrator's brief explicitly requires
   porting rather than reaching for Pillow.
5. Keep `render_annotated(state, out_path: str, scale: int = 6, grid_every: int = 10) ->
   None` verbatim (lines 49-98) — same `margin = 20` constant (line 62), same gridline
   color `GRID_LINE = (255, 255, 255)` (line 86), same entity color literal
   `(0x4A, 0x9E, 0xFF)` (line 84, matches `render.py`'s own `ENTITY_COLOR_ALIVE` at line
   55 — could be imported instead of re-literaled, but the prototype hardcodes it and this
   plan keeps the port minimal-diff; not worth a second import for one tuple literal).
   Entity/lifecycle access stays `ent.navigation.position` / `getattr(ent.lifecycle,
   "active", True)` (lines 53-54, 78) — this is `render.py`'s own direct-component-access
   convention (`src/rendering/render.py:80-81`), not `density.py`'s legacy
   `.position`/`.active` property shortcut (`src/core/state.py:766-776`); no change needed
   since both conventions are valid on `EntityState`, and matching `render.py`'s sibling
   convention (same package, same purpose: rendering) is the more locally-consistent
   choice.
6. Drop the `if __name__ == "__main__":` CLI block (lines 101-110) — a promoted `src/`
   module is a library, not a script; `render.py` itself has no equivalent block.
7. Add a module docstring following `render.py`'s and the four metric siblings'
   provenance convention: cite this ticket, cite the exact prototype source path and line
   range ported, state the stdlib-only/no-Pillow constraint explicitly and why
   (`tests/architecture/test_rendering_zero_new_dependency_guard.py` walks the whole
   `src/rendering/` directory, confirmed at `tests/architecture/
   test_rendering_zero_new_dependency_guard.py:19-24,41-65` — directory-scoped, not a
   hardcoded file list, so this new file inherits the guard automatically with no test
   change required).

**Other writers to this file:** none — brand-new file, this ticket is its sole author.
No other ticket in this batch touches `render_annotated.py`.

**Do NOT touch:** `src/rendering/render.py` (read-only import source for
`terrain_color`/`DEFAULT_TERRAIN_COLOR` — do not modify it to "help" this port; import
only), `src/rendering/png_writer.py` (read-only, reused exactly as-is),
`experiments/spatial_rendering/prototype/render_annotated.py` (the prototype stays as a
reference; do not delete or modify it — none of the five prior siblings deleted their
source prototypes either).

**Verify:** `test_annotated_renderer_produces_valid_png_and_matches_plain_terrain_palette`
and `test_annotated_renderer_golden_hash_bit_identical_across_three_independent_runs`
(Step 2), plus `tests/architecture/test_rendering_zero_new_dependency_guard.py` staying
green.

### Step 2 — Write `tests/unit/rendering/test_render_annotated.py`

**Files:** `tests/unit/rendering/test_render_annotated.py` (new)

**Change:** Mirror `tests/unit/rendering/test_render_core.py`'s structure (`_build_state`
helper building a small deterministic `AuthoritativeState`, `_read_chunks` hand-walking
PNG chunk/CRC32 structure — both confirmed real at `test_render_core.py:19-56, 58-72`,
reusable near-verbatim since `render_annotated()` writes PNGs via the same
`png_writer.write_png`). Implement:
1. `test_annotated_renderer_produces_valid_png_and_matches_plain_terrain_palette` — valid
   PNG chunk structure (reuse `_read_chunks`); assert the output dimensions include the
   `margin = 20` offset (`width == grid_w * scale + 20`, `height == grid_h * scale + 20`,
   per `render_annotated.py:62-63`'s confirmed formula) — this alone distinguishes
   annotated output from a plain `render()` of the same state, whose dimensions are
   exactly `grid_w * scale` / `grid_h * scale` with no margin (`render.py:91-92`,
   confirmed no margin term). Also assert non-gridline, non-label terrain pixels
   (interior tiles away from any `grid_every`-multiple row/column) equal `terrain_color(...)`
   from `render.py`, proving no drifted second palette.
2. `test_annotated_renderer_golden_hash_bit_identical_across_three_independent_runs` —
   `regression` marker, mirrors `test_render_core.py::test_render_golden_hash_bit_
   identical_across_three_independent_runs` exactly (three independently-constructed
   content-equal states, SHA256 the PNG bytes, assert all three equal). Docstring/comment
   must cite `TCK-20260821-VISUAL-AGENT-REVIEW` per `docs/testing/test_taxonomy.md`'s
   `regression` marker standard ("must include a comment or link to the original
   ticket/issue", confirmed at `docs/testing/test_taxonomy.md:30-32`). The `regression`
   marker itself is already registered (`pyproject.toml:71`, confirmed: `"regression:
   targets a specific bug identified during porting"`) — no new marker registration
   needed.
3. `test_annotated_render_module_does_not_subclass_pillar_scorer_or_import_simq_event_
   pipeline` — mirrors `test_density.py:147-165`'s exact AST-walk pattern (confirmed read
   above), applied to `src/rendering/render_annotated.py`'s path.

**Do NOT touch:** any existing file in `tests/unit/rendering/` (all listed in
test_plan.md's Regression Surface as must-keep-passing, no change expected).

**Verify:** `PYTHONPATH=. pytest tests/unit/rendering/test_render_annotated.py -v` and
`PYTHONPATH=. pytest tests/unit/rendering/test_render_annotated.py -m regression -v`.

### Step 3 — `should_escalate` in `src/rendering/review_pipeline.py`

**Files:** `src/rendering/review_pipeline.py` (new)

**Change:** Create the module (module docstring per Step 1's provenance convention,
citing this ticket, the four consumed sibling modules, and `grading.py`). Add:

```python
from __future__ import annotations

from src.rendering.grading import HardRuleResult


def should_escalate(hard_results: list[HardRuleResult], grade: str) -> bool:
    return any(not r.passed for r in hard_results) or grade in ("D", "F")
```

Verbatim adoption of investigation.md's proposed function — composes `grading.py`'s real
`HardRuleResult.passed` field (confirmed at `src/rendering/grading.py:110-112`) and
`assign_grade`'s real string-literal return values (`"S"`/`"A"`/`"B"`/`"C"`/`"D"`/`"F"`,
confirmed at `src/rendering/grading.py:155-166`) — no new numeric threshold, no
re-derivation of a parallel healthy-band check against raw metric values. This is the
single call site for the D/F escalation cutoff; no other function or module in this plan
re-implements the grade-string comparison inline (Anti-Drift Hazard, see Scope Guards).

**Other writers to `should_escalate`'s inputs:** none — `HardRuleResult` instances are
produced only by `grading.py::evaluate_hard_rule` (Step 4 of this plan's caller,
`run_tier0_tier1_pipeline`); no other code path in this ticket or any prior sibling
constructs `HardRuleResult` objects.

**Do NOT touch:** `src/rendering/grading.py` — read-only input, must remain
byte-for-byte unchanged (this ticket's Out of Scope: "no change to... the Tier 0 scoring
system's internals beyond consuming their output").

**Verify:** `test_should_escalate_composes_hard_rule_failure_and_grade` (Step 6).

### Step 4 — `Tier1Digest` dataclass and `digest_to_json` serializer

**Files:** `src/rendering/review_pipeline.py` (same file)

**Change:** Add:

```python
import dataclasses
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Tier1Digest:
    world_id: str
    seed: int
    tick: int
    grade: str
    combined_score: float
    hard_rule_results: tuple[dict, ...]
    soft_rule_results: tuple[dict, ...]
    terrain_histogram: dict[str, int]
    entity_count: int
    connectivity_component_count: int
    connectivity_percent_reachable: float
    flagged_shape_components: tuple[dict, ...]
    escalate: bool
    plain_render_path: str
    annotated_render_path: str | None


def digest_to_json(digest: Tier1Digest) -> str:
    return json.dumps(dataclasses.asdict(digest), sort_keys=True)
```

Every field, in order, matches investigation.md's proposed schema exactly (Risks
section). `hard_rule_results`/`soft_rule_results` are tuples of plain dicts (built via
`dataclasses.asdict(r)` per `HardRuleResult`/`SoftRuleResult` instance, at the point
`run_tier0_tier1_pipeline` constructs the digest in Step 5 — not stored as the dataclass
instances themselves) specifically because `HardRuleResult`/`SoftRuleResult` are not
natively `json.dumps`-able and this ticket's Out of Scope forbids adding a custom JSON
encoder or `__json__` method to `grading.py` itself. `dataclasses.asdict(digest)` recurses
through `Tier1Digest`'s own fields; since every field is already a JSON-primitive-native
type (`str`/`int`/`float`/`bool`/`dict`/`tuple`/`None` — no nested dataclass instances
remain inside `Tier1Digest` itself, only plain dicts built ahead of time), `json.dumps(...,
sort_keys=True)` serializes it directly with no custom encoder. `sort_keys=True` is
required for AC #3's byte-identical claim (Anti-Drift Hazard — do not rely on incidental
dict/dataclass field-insertion order).

**Other writers to this dataclass:** none — `Tier1Digest` instances are constructed only
by `run_tier0_tier1_pipeline` (Step 5); no other function in this module or elsewhere
constructs one.

**Do NOT touch:** `src/rendering/grading.py`'s `HardRuleResult`/`SoftRuleResult`
dataclasses — read-only, converted to plain dicts at the digest boundary, never modified
to add a JSON-encoder method themselves.

**Verify:** `test_tier1_digest_is_json_serializable_and_round_trips` (Step 6).

### Step 5 — `run_tier0_tier1_pipeline` orchestration function

**Files:** `src/rendering/review_pipeline.py` (same file)

**Change:** Add:

```python
import os

from src.core.state import AuthoritativeState
from src.rendering.connectivity import analyze_connectivity
from src.rendering.density import compute_density_cv, compute_terrain_histogram
from src.rendering.grading import (
    GradeConfig,
    assign_grade,
    combine_rule_deltas,
    evaluate_hard_rule,
    evaluate_soft_rule,
    load_grade_config,
)
from src.rendering.render import render_output_path
from src.rendering.render_annotated import render_annotated
from src.rendering.shape import connected_components


def run_tier0_tier1_pipeline(
    state: AuthoritativeState,
    world_id: str,
    base_dir: str,
    run_id: str,
    grade_config: GradeConfig | None = None,
) -> Tier1Digest:
    config = grade_config if grade_config is not None else load_grade_config()

    connectivity_result = analyze_connectivity(state.terrain, state.blocked_tiles)
    density_result = compute_density_cv(state.entities)
    terrain_histogram = compute_terrain_histogram(state.terrain)
    shape_components = connected_components(state.terrain)

    hard_result = evaluate_hard_rule(
        "fully_connected", connectivity_result.component_count == 1, config
    )
    hard_results = [hard_result]

    soft_results = []
    if shape_components:
        soft_results.append(
            evaluate_soft_rule(
                "fill_ratio_healthy_band", shape_components[0].fill_ratio, config
            )
        )

    combined_score = combine_rule_deltas(hard_results, soft_results)
    grade = assign_grade(combined_score, config.grade_thresholds)
    escalate = should_escalate(hard_results, grade)

    band = config.soft_rules["fill_ratio_healthy_band"]
    flagged_shape_components = tuple(
        sorted(
            (
                {"terrain_type": sc.terrain_type, "bbox": sc.bbox, "fill_ratio": sc.fill_ratio}
                for sc in shape_components
                if sc.fill_ratio < band.healthy_low or sc.fill_ratio > band.healthy_high
            ),
            key=lambda d: (d["terrain_type"], d["bbox"]),
        )
    )

    plain_render_path = render_output_path(base_dir, run_id, f"{world_id}_tick{state.tick}.png")
    annotated_render_path = None
    if escalate:
        annotated_render_path = render_output_path(
            base_dir, run_id, f"{world_id}_tick{state.tick}_annotated.png"
        )
        os.makedirs(os.path.dirname(annotated_render_path), exist_ok=True)
        render_annotated(state, annotated_render_path)

    return Tier1Digest(
        world_id=world_id,
        seed=state.seed,
        tick=state.tick,
        grade=grade,
        combined_score=combined_score,
        hard_rule_results=tuple(dataclasses.asdict(r) for r in hard_results),
        soft_rule_results=tuple(dataclasses.asdict(r) for r in soft_results),
        terrain_histogram=terrain_histogram,
        entity_count=density_result.entity_count,
        connectivity_component_count=connectivity_result.component_count,
        connectivity_percent_reachable=connectivity_result.percent_reachable,
        flagged_shape_components=flagged_shape_components,
        escalate=escalate,
        plain_render_path=plain_render_path,
        annotated_render_path=annotated_render_path,
    )
```

This is the architecturally load-bearing function in this plan. **Hard rule**:
`render_annotated(...)` (Step 1) is called **only** inside the `if escalate:` branch —
there is no other call to `render_annotated` anywhere in this function or module. This is
what makes AC #1 ("zero image is ever fetched via Read" when Tier 0 does not flag an
anomaly) structurally true rather than merely asserted: when `escalate` is `False`,
`annotated_render_path` is `None` and, critically, **no file is ever written** to the
path it would have used — there is nothing for a misbehaving agent invocation to `Read`.
Every input this function consumes is a confirmed real signature: `analyze_connectivity(
terrain, blocked_tiles) -> ConnectivityResult` (`src/rendering/connectivity.py:44-47`),
`compute_density_cv(entities: dict) -> DensityResult` (`src/rendering/density.py:33`,
called with `state.entities` directly, matching `tests/unit/rendering/test_density.py:39`'s
own real-corpus call pattern), `compute_terrain_histogram(terrain: dict) -> dict[str,int]`
(`density.py:58`), `connected_components(terrain, min_size=20, excluded_types={"PLAIN",
"ROAD"}) -> list[ShapeComponent]` (`src/rendering/shape.py:123-126`, defaults used
as-is — no override), `evaluate_hard_rule`/`evaluate_soft_rule`/`combine_rule_deltas`/
`assign_grade`/`load_grade_config` (`grading.py`, Step 3-5 signatures confirmed above),
`render_output_path(base_dir, run_id, filename) -> str` (`render.py:158-166`, confirmed
`os.makedirs` is the caller's responsibility per its own docstring — done explicitly
before the `render_annotated` call, matching that documented contract).

**Other writers to the filesystem path `annotated_render_path` resolves to:** none other
than this function itself — `render_output_path`'s `{base_dir}/{run_id}/renders/
{filename}` join with the `_annotated` filename suffix this step introduces is a filename
pattern no other sibling or existing code path writes to (plain `render()` calls, if any
existed, would use a filename without the `_annotated` suffix, landing at a different
path in the same directory — confirmed no collision by construction of the two distinct
filename templates).

**Do NOT touch:** `src/rendering/connectivity.py`, `density.py`, `shape.py`, `grading.py`,
`render.py` (all read-only inputs); do not add a plain `render()` call here (Decision 3 —
out of this ticket's scope).

**Verify:** `test_tier0_tier1_pipeline_writes_digest_without_writing_annotated_png_when_
not_escalated`, `test_tier0_tier1_pipeline_writes_annotated_png_with_gridlines_when_
escalated`, `test_tier1_digest_golden_hash_field_identical_across_three_independent_runs`
(Step 6).

### Step 6 — Write `tests/unit/rendering/test_review_pipeline.py`

**Files:** `tests/unit/rendering/test_review_pipeline.py` (new)

**Change:** Mirror `test_grading.py`'s/`test_render_core.py`'s fixture conventions
(`_build_state`-style helper for synthetic `AuthoritativeState`s; `tmp_path` for
`base_dir`). Implement every test from test_plan.md's "New Tests Required" mapped to this
file:

1. `test_should_escalate_composes_hard_rule_failure_and_grade` — the four cases
   test_plan.md specifies (all-pass+A→False, one-fail+A→True, all-pass+D→True,
   all-pass+F→True, all-pass+C→False), calling `should_escalate` directly with synthetic
   `HardRuleResult` instances — no rendering, no state, no pipeline invocation.
2. `test_tier1_digest_is_json_serializable_and_round_trips` — build a `Tier1Digest`
   directly (synthetic field values), call `digest_to_json`, assert `json.loads(json.
   dumps(...))` round-trips to an equal dict, and every dataclass field name (via
   `dataclasses.fields(Tier1Digest)`) is present as a JSON key.
3. `test_tier0_tier1_pipeline_writes_digest_without_writing_annotated_png_when_not_
   escalated` — build a fixture `AuthoritativeState` engineered so `analyze_connectivity`
   reports `component_count == 1` (single fully-connected walkable region — e.g. a small
   open 4×4 `PLAIN` grid with no `WALL`/`blocked_tiles`) and the illustrative config's
   grade lands above the D/F cutoff (achievable with the real default `config/rendering/
   grade_thresholds.toml` and a fill-ratio-healthy component, or by passing a synthetic
   `GradeConfig` directly to avoid coupling this test to the still-uncalibrated real
   config's exact numbers). Call `run_tier0_tier1_pipeline(state, "test_world", str(
   tmp_path), "test_run", grade_config=...)`. Assert the returned digest has
   `escalate is False` and `annotated_render_path is None`, **and** assert via
   `os.listdir`/`Path.glob` on `tmp_path` that no `.png` file exists anywhere under the
   output tree — checking the filesystem directly, not just the return value, per
   test_plan.md's explicit instruction that this is "the load-bearing anti-drift guard
   for this entire ticket."
4. `test_tier0_tier1_pipeline_writes_annotated_png_with_gridlines_when_escalated` —
   build a fixture state with two disconnected walkable regions (fails `fully_connected`),
   run the pipeline, assert `escalate is True`, `annotated_render_path` is not `None`, a
   real PNG file exists at that exact path, and its dimensions include the `margin = 20`
   offset (same distinguishing check as Step 2 test 1) proving it is genuinely the
   annotated variant, not a plain render misrouted to that path.
5. `test_tier1_digest_golden_hash_field_identical_across_three_independent_runs` —
   `regression` marker, citing this ticket ID in a comment. Three independently
   constructed but content-equal `AuthoritativeState` fixtures with a fixed `world_id`,
   engineered to have **at least two flagged `ShapeComponent`s** (two distinct terrain
   patches whose `fill_ratio` falls outside the healthy band) so the fixture actually
   exercises `flagged_shape_components`'s explicit sort (Review-caught determinism gap,
   Decision 5) rather than passing vacuously with 0-1 elements. Run
   `run_tier0_tier1_pipeline` against each with a fixed `base_dir`/`run_id`, serialize
   each digest via `digest_to_json` (which internally uses `sort_keys=True`), SHA256-hash
   the resulting JSON bytes, assert all three hashes equal. Mirrors
   `test_render_core.py::test_render_golden_hash_bit_identical_across_three_independent_
   runs`'s exact three-independent-builds shape.
6. `test_review_pipeline_module_does_not_subclass_pillar_scorer_or_import_simulation_
   quality_or_observability_events` — mirrors `test_density.py:147-165`'s exact AST-walk
   pattern, applied to `src/rendering/review_pipeline.py`'s path.
7. Record explicitly (per test_plan.md test 6, `test_agent_review_output_contract_shape`):
   this plan does **not** add a Python-side output-skeleton helper — the structured
   verdict (one-line summary, findings table, recommended next steps) is owned entirely
   by `world-render-reviewer.md`'s own prompt body (Step 7), matching
   `simulation-analyst.md`'s own precedent (no Python-side output-assembly helper exists
   for it either, confirmed by its absence from `src/` in the investigation). AC #4's real
   verification is a manual read of the finished agent file against `simulation-analyst.
   md`'s `## Output` section shape — no pytest test is added for this, and none should be
   (a test asserting prose shape inside a `.md` prompt file cannot execute the agent's own
   reasoning, per test_plan.md's own explicit N/A call).

**Do NOT touch:** any existing file in `tests/unit/rendering/`.

**Verify:** `PYTHONPATH=. pytest tests/unit/rendering/test_review_pipeline.py -v` and
`PYTHONPATH=. pytest tests/unit/rendering/test_review_pipeline.py -m regression -v`.

### Step 7 — Create `.claude/agents/world-render-reviewer.md`

**Files:** `.claude/agents/world-render-reviewer.md` (new)

**Change:** New subagent file. Frontmatter (no `tools:` key — confirmed
`simulation-analyst.md` itself has none, `.claude/agents/simulation-analyst.md:2-3`, and
`concern-investigator.md` is the only agent in the repo with a `tools:` restriction,
confirmed via `grep -l "tools:" .claude/agents/*.md` in investigation.md — this new agent
follows the unrestricted default, matching `simulation-analyst.md`, since Tier 2
escalation genuinely needs `Read`):

```yaml
---
name: world-render-reviewer
description: Tiered visual/geometric quality review of a rendered world state — Tier 0 pure-data scoring by default, escalating to the annotated/gridlined render only when Tier 0/1 flags an anomaly. Cites tile coordinates from the annotated image, never the plain render.
---
```

Body structure, modeled directly on `simulation-analyst.md`'s shape (Data Sources /
Analysis Dimensions / Anomaly Classification / Output — confirmed exact section order at
`.claude/agents/simulation-analyst.md:12-58`), but with every dimension defined in
visual/geometric terms with **zero Mechanics Bible chapter citations** (Decision 6):

- **Data Sources**: (1) the Tier 1 digest JSON (`Tier1Digest`/`digest_to_json`'s output,
  `src/rendering/review_pipeline.py`) — always the first thing read; (2) the annotated
  PNG at `Tier1Digest.annotated_render_path`, **read only when `escalate` is `True`**;
  (3) the plain PNG at `Tier1Digest.plain_render_path`, for human-requested general
  health checks only, never as an escalation substitute.
- **Review Dimensions** (renamed from `simulation-analyst.md`'s "Analysis Dimensions" —
  no Mechanics Bible chapter applies, so the parallel heading is deliberately not
  identical): Connectivity (is the walkable region fully reachable —
  `connectivity_component_count`/`connectivity_percent_reachable`), Terrain Shape
  (stamped-rectangle/repetition artifacts — `flagged_shape_components`, citable via
  `bbox`), Density (entity clustering — `entity_count`, nearest-neighbor CV if present in
  a future digest revision), Grade (`grade`/`combined_score` as the single-number
  summary).
- **Severity Classification** (reuses the CRITICAL/HIGH/MEDIUM/LOW vocabulary as a
  shared cross-agent convention, redefined per investigation.md's proposal): **CRITICAL**
  = a hard rule failed (e.g. `fully_connected` false) or grade is `F`. **HIGH** = grade is
  `D` with all hard rules passing. **MEDIUM** = a flagged shape component near a healthy-
  band extreme but grade is `C` or better. **LOW** = within the healthy band, grade `B` or
  better.
- **Output** (matches `simulation-analyst.md`'s five-part shape, `Output` section
  confirmed at lines 52-58): 0. one-line summary (≤200 chars); 1. digest summary (grade,
  combined score, escalate flag); 2. findings table — dimension | severity | description |
  evidence (tile-coordinate range, cited **only** from the annotated image when one was
  read, never invented from the digest alone) | related digest field; 3. which fields were
  Tier-0-verifiable vs. required the annotated image; 4. recommended next steps.

**The following instruction must be written into the agent prompt body verbatim in
spirit** (investigation.md's flagged residual, pytest-unenforceable, prompt-compliance
gap — the correct available mitigation, not a decorative note): "Always read the Tier 1
digest first. Only call `Read` on `annotated_render_path` when the digest's `escalate`
field is `True`. If `escalate` is `False`, do not call `Read` on any image path — there is
no annotated render to read, and the plain render at `plain_render_path` must never be
substituted as an escalation image; it exists for unrelated human-requested general
health checks only."

**Other writers to `.claude/agents/`:** none for this specific filename — brand-new file,
no collision with `simulation-analyst.md`, `world-debugger.md`, or `concern-investigator.
md` (all confirmed distinct, unrelated files by direct read).

**Do NOT touch:** `.claude/agents/simulation-analyst.md`, `.claude/agents/world-debugger.
md` (both read-only structural references — do not add a sixth Analysis Dimension to
`simulation-analyst.md`, per Decision 6's reasoning).

**Verify:** no automated test executes this file's prose; manual read-through against
`simulation-analyst.md`'s shape is the verification (test_plan.md test 6's explicit N/A
call, Step 6 item 7 above).

### Step 8 — Add parity ledger entry `INFRA-375`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Confirmed by direct read (`grep -n "^- id: INFRA-37" -A 10 docs/parity_
ledger/infrastructure.yaml`) that `INFRA-374` (line 10896, `VISUAL-GRADE-SCORER`,
`status: verified`) is the current maximum id and the last entry in the file, so
`INFRA-375` is genuinely the next available id at plan-write time. Append, following
`INFRA-370`-`374`'s exact 8-field shape:

```yaml
- id: INFRA-375
  text: Tiered Tier 0/Tier 1/Tier 2 agent-review pipeline (src/rendering/review_pipeline.py)
    composes grading.py's HardRuleResult/grade output into a deterministic escalation
    decision (should_escalate) and a JSON-serializable Tier1Digest (sort_keys=True,
    hashed for byte-identical determinism across independent runs). The annotated/
    gridlined render (src/rendering/render_annotated.py, ported from experiments/
    spatial_rendering/prototype/render_annotated.py) is written to disk only when
    should_escalate returns True -- structurally enforcing that zero image exists to
    read in the non-escalating case, rather than relying on agent tool-use discipline.
  status: verified
  priority: P2
  v2_evidence: src/rendering/review_pipeline.py, src/rendering/render_annotated.py
  test_path: tests/unit/rendering/test_review_pipeline.py::test_tier0_tier1_pipeline_writes_digest_without_writing_annotated_png_when_not_escalated
  divergence_note: null
  proof_type: parity
```

**Other writers to this file:** `docs/parity_ledger/infrastructure.yaml` is a single YAML
list appended to by every ticket landing a new infrastructure-layer parity fact. All five
upstream siblings (`INFRA-370`-`374`) are already merged and DONE (confirmed present under
`stored_artifacts/TCK-20260821-VISUAL-{CONNECTIVITY,DENSITY,SHAPE,VARIANTS}-METRIC/` and
`stored_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/`), so there is no concurrent-write
race with those specifically. Per CLAUDE.md's Hard Rules (shared working directory across
sessions), re-run the `grep` immediately before appending at implementation time to
confirm `INFRA-375` is still the next free id — do not hardcode the number blindly if a
concurrent session has appended further entries since this plan was written.

**Do NOT touch:** `docs/plans/world_rendering/idea_world_render_validation.md` (deferred
to `TCK-20260821-VISUAL-QUALITY-DOCS` per investigation.md's Docs Requiring Update
section) or `docs/simulation_quality/quality_scoring_contract.md` (not applicable).

**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/
infrastructure.yaml'))"` parses without error. The cited `test_path` (Step 6, test 3)
must exist and pass before this entry can honestly claim `status: verified`.

### Step 9 — Extend `docs/engine/contracts/regression_and_verification.md`

**Files:** `docs/engine/contracts/regression_and_verification.md`

**Change:** Two targeted additions, both to sections `WORLD-RENDER-CORE` already
extended (confirmed: §1's "Captured Artifacts" list item 4 and §4's render-specific
determinism paragraph both already exist, added by that ticket — read in full above,
lines 22-24 and 66-75):
1. §1 "Captured Artifacts", extend item 4 (or add a short trailing sentence to it) to
   note that an escalation-flagged render additionally produces an annotated/gridlined
   variant at the same `renders/` location with an `_annotated` filename suffix, written
   only when Tier 0/1 scoring flags an anomaly (not on every frame).
2. §4 "Determinism Check (Bors Check)", append one paragraph after the existing
   render-specific instance paragraph (after line 75, before the `---` separator at line
   76): the Tier 1 digest (`src/rendering/review_pipeline.py::Tier1Digest`/
   `digest_to_json`) is a pure, read-only function of `AuthoritativeState` content and the
   already-tested `grading.py`/sibling-metric outputs — three independent
   `run_tier0_tier1_pipeline` calls against content-equal state produce a byte-identical
   JSON digest (`sort_keys=True` serialization), enforced via `tests/unit/rendering/
   test_review_pipeline.py::test_tier1_digest_golden_hash_field_identical_across_three_
   independent_runs`.

**Other writers to this file:** `WORLD-RENDER-CORE` already landed its own two additions
(confirmed, DONE). No other ticket in this batch or currently in-progress is known to be
editing this file concurrently (checked `tickets/inprogress/` at investigation time); per
CLAUDE.md's shared-workdir Hard Rule, re-run `git status`/`git diff` on this file
immediately before editing at implementation time to confirm no concurrent session has
touched it since this plan was written.

**Do NOT touch:** any other section of this file (§2 Test Harness, §3 Log Rotation, §5
Visual Verification, §6 Arena Regression Harness) — none are relevant to this ticket's
scope.

**Verify:** `PYTHONPATH=. pytest tests/docs/test_doc_integrity.py -q` stays green
(frontmatter/schema check, per test_plan.md's Regression Surface).

## Scope Guards

Must NOT be touched or introduced by this ticket, per the ticket's Out of Scope,
investigation.md's Anti-Drift Hazards, and the orchestrator's explicit instructions:

- **No `import src.simulation_quality.*` anywhere** in `src/rendering/render_annotated.py`,
  `src/rendering/review_pipeline.py`, `.claude/agents/world-render-reviewer.md`, or either
  new test file.
- **No `import src.observability.events`** anywhere in the new modules or tests.
- **No `PillarScorer` subclass** anywhere.
- **No new `PillarId` enum member.**
- **Do not write the annotated PNG unconditionally** — `render_annotated(...)` is called
  from exactly one call site (`run_tier0_tier1_pipeline`'s `if escalate:` branch, Step 5)
  and nowhere else. No "always render both variants for caching" shortcut, no test-only
  helper that renders it outside the escalation gate — this is the AC #1 anti-drift
  hazard, and Step 6 test 3 exists specifically to catch a regression here by checking the
  filesystem directly, not just the returned digest.
- **No Pillow/PIL import anywhere in `src/rendering/`** — the hand-rolled 3×5 `DIGITS`
  bitmap font and `draw_text()` (ported verbatim in Step 1) are the only text-rendering
  mechanism; `tests/architecture/test_rendering_zero_new_dependency_guard.py` enforces
  this automatically (directory-scoped AST walk, no guard-test change needed, no
  loosening of its allowlist permitted per CLAUDE.md's gate-integrity rule).
- **Do not touch `render.py`'s or `incremental.py`'s existing plain-render behavior** —
  `render_annotated.py`/`review_pipeline.py` only *import* `terrain_color`/
  `DEFAULT_TERRAIN_COLOR`/`render_output_path` from `render.py`; neither file is modified.
- **Do not hardcode the D/F escalation cutoff at more than one call site** —
  `should_escalate` (Step 3) is the sole place this comparison exists; no CLI tool, test
  helper, or agent-prompt logic re-implements `grade in ("D", "F")` inline anywhere.
- **Do not let `digest_to_json`'s serialization rely on incidental dict/dataclass field
  ordering** — `json.dumps(..., sort_keys=True)` is mandatory (Step 4), never a bare
  `json.dumps(dataclasses.asdict(digest))`.
- **No CI-gating this pipeline anywhere** — report-only, matching all five upstream
  siblings; do not add any of this ticket's new files, tests, or the parity entry to any
  regression-baseline/gate-check manifest.
- **Do not add a sixth Analysis Dimension to `simulation-analyst.md`** — the new agent is
  a separate file (Decision 6), not an extension of the existing one.
- **Do not pin a specific `grade` letter or `combined_score` value against real corpus
  worlds as a regression anchor** — mirrors `test_grading.py`'s own documented precedent;
  this ticket's `should_escalate` threshold is derived from `grading.py`'s still-
  uncalibrated config (`TCK-20260821-VISUAL-QUALITY-CALIBRATION` is separate, not-yet-
  landed scope).
- **Do not modify `docs/plans/world_rendering/idea_world_render_validation.md`** —
  deferred to `TCK-20260821-VISUAL-QUALITY-DOCS`.
- **Do not add a Python-side output-skeleton helper for the agent's findings table** —
  Step 6 item 7 records this explicitly as a deliberate non-addition, matching
  `simulation-analyst.md`'s own precedent (prompt-owned output shape, no Python helper).

## Dependency Map

- Step 1 (`render_annotated.py`) has no dependency on any other step; it only imports
  already-shipped `render.py`/`png_writer.py`.
- Step 2 (its tests) depends on Step 1.
- Step 3 (`should_escalate`) depends only on already-shipped `grading.py`; independent of
  Steps 1-2.
- Step 4 (`Tier1Digest`/`digest_to_json`) is independent of Steps 1-3; it only needs
  stdlib `dataclasses`/`json`.
- Step 5 (`run_tier0_tier1_pipeline`) depends on Steps 1, 3, and 4 (calls
  `render_annotated`, `should_escalate`, and constructs `Tier1Digest`), plus the four
  already-shipped sibling modules and `grading.py`.
- Step 6 (tests) depends on Steps 3, 4, and 5 all being complete (exercises every
  function in `review_pipeline.py`) and on Step 1 (test 4 needs `render_annotated`
  wired through the pipeline).
- Step 7 (`world-render-reviewer.md`) depends on Steps 4-5 conceptually (the agent's
  prompt references `Tier1Digest`'s real field names) but has no code dependency — it
  could be authored in parallel with Steps 1-6, though field-name accuracy is easiest to
  guarantee once Step 4 has landed.
- Step 8 (parity ledger) depends on Step 6 passing (its `test_path` must exist and pass).
- Step 9 (docs) depends on Step 6 passing (cites the same test path) and is independent
  of Step 8 (different file).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: When Tier 0 does not flag an anomaly, the pipeline completes with a Tier 1 digest only and zero image is ever fetched via Read | Step 5 (`if escalate:` gate around the sole `render_annotated` call site) | `test_tier0_tier1_pipeline_writes_digest_without_writing_annotated_png_when_not_escalated` |
| AC #2: When Tier 0 flags an anomaly, the ANNOTATED/gridlined PNG variant (not plain) is fetched, citing tile-coordinate ranges | Step 1 (`render_annotated`), Step 5 (escalation branch writes the file and path) | `test_tier0_tier1_pipeline_writes_annotated_png_with_gridlines_when_escalated` |
| AC #3: The Tier 1 digest is deterministic — byte/field-identical across repeated runs of the same state | Step 4 (`digest_to_json` with `sort_keys=True`), Step 5 (pure function of state content) | `test_tier1_digest_golden_hash_field_identical_across_three_independent_runs` |
| AC #4: Agent-review output follows `simulation-analyst.md`'s contract shape (one-line summary, findings table with severity + evidence/coordinates, recommended next steps) | Step 7 (`world-render-reviewer.md`'s `## Output` section) | No automated test (test_plan.md's explicit N/A call, Step 6 item 7); manual read-through against `simulation-analyst.md` |
| AC #5: A golden-hash regression test (`tests/unit/`, `regression` marker) covers the Tier 0/1 determinism claim | Step 6 | `test_tier1_digest_golden_hash_field_identical_across_three_independent_runs` |

## Anti-Drift Notes

- **The `if escalate:` gate around `render_annotated(...)` in Step 5 is the single most
  load-bearing line in this entire plan.** It is the only mechanism making AC #1
  structurally, not just behaviorally, true. Do not refactor `run_tier0_tier1_pipeline`
  in a way that computes `annotated_render_path` unconditionally, or that calls
  `render_annotated` before checking `escalate` "for convenience" (e.g. to warm a
  filesystem cache). Step 6 test 3 checks the filesystem directly for exactly this reason.
- **`world_id` cannot be read from `AuthoritativeState` — it has no such field**
  (verified directly, `src/core/state.py:1083-1137`). Any future refactor that tries to
  derive `world_id` from `state` instead of the explicit parameter will need a new field
  added to `AuthoritativeState` first — out of this ticket's scope, and not something to
  improvise around by, e.g., stuffing `world_id` into `state.world_time` or any other
  unrelated existing field.
- **`seed`/`tick` are read from `state.seed`/`state.tick` directly, never taken as
  separate function parameters** — this is a deliberate correctness choice (Decision 2),
  not an oversight; a caller passing a mismatched seed/tick would otherwise silently
  produce a digest whose `seed`/`tick` fields lie about what was actually scored.
- **The soft rule is evaluated against exactly the first `ShapeComponent`
  `connected_components(...)` returns, and only if the list is non-empty** (Decision 4).
  Do not iterate and evaluate the soft rule against every component (that would produce
  multiple `SoftRuleResult`s per digest, a different schema than investigation.md's
  proposal and not required by any AC) and do not raise or fabricate a placeholder
  component when the list is empty.
- **`flagged_shape_components` uses the soft rule's own `healthy_low`/`healthy_high`
  config bounds, never an independently invented threshold** (Decision 5) — this keeps a
  single source of truth for "what counts as an unhealthy fill-ratio," matching the same
  discipline `should_escalate` already applies to the hard-rule/grade cutoff.
- **`flagged_shape_components` must stay explicitly `sorted(...)` by `(terrain_type, bbox)`
  before it is tupled (Decision 5, Step 5).** `sort_keys=True` on `digest_to_json` sorts
  dict keys only, never array/tuple element order — do not remove this explicit sort under
  the mistaken belief that `sort_keys=True` alone already guarantees AC #3's determinism
  claim for this field; `connected_components`'s own return order depends on unordered
  Python `set` iteration internally and is not a documented contract this ticket may rely
  on (Review-caught, `src/rendering/shape.py:145`).
- **`.claude/agents/world-render-reviewer.md`'s prompt-compliance instruction (read the
  digest first, only Read the annotated image when `escalate` is `True`, never substitute
  the plain render) is written into the prompt precisely because it is NOT pytest-
  enforceable** — do not treat its presence in the prompt as equivalent to the Step 5
  filesystem-level guarantee; both exist because they cover different failure modes (a
  file that structurally cannot be read vs. an agent that might still try, or that might
  reach for the wrong existing file).
