---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-AGENT-REVIEW
artifact_type: investigation
tags: [visualization, simulation-quality, determinism, world]
---

# Investigation — TCK-20260821-VISUAL-AGENT-REVIEW

## Current Behavior

**Nothing in this ticket's scope exists in `src/` today.** Confirmed by listing `src/rendering/`:
`png_writer.py`, `render.py`, `incremental.py` (all `TCK-20260821-WORLD-RENDER-CORE`), and
`connectivity.py`/`density.py`/`shape.py`/`variants.py` (the four metric siblings) plus
`grading.py` (`TCK-20260821-VISUAL-GRADE-SCORER`, just-shipped, real). No `annotated.py`, no
digest/review module, no `.claude/agents/world-render-reviewer.md`.

**A real gap this ticket must close that none of the prior six siblings had to: the
annotated/gridlined renderer was never promoted from `experiments/` into `src/`.**
`WORLD-RENDER-CORE` promoted `render_world.py` → `src/rendering/render.py` (plain render) and
`render_incremental.py` → `src/rendering/incremental.py`, but explicitly left
`render_annotated.py`, `render_trail.py`, and `benchmark.py` un-promoted (its own Related Code
Areas list all three as prototype-only references, not promotion targets; its Scope says nothing
about annotation). This ticket's AC #2 ("the ANNOTATED/gridlined PNG variant ... is fetched")
cannot be satisfied by existing `src/` code — it requires writing a new production module that
ports `experiments/spatial_rendering/prototype/render_annotated.py`'s `render_annotated()`
(gridlines every N tiles + a hand-rolled 3×5 bitmap-digit axis-label font, read in full — lines
1-111) the same way `render.py` ported `render_world.py`. This is more than "one more metric
module consuming existing outputs" (the shape all six prior siblings had) — it is new rendering
capability plus a new orchestration/agent layer on top.

### `src/rendering/grading.py` — Tier 0's exact output shape (read in full)

Four public entry points relevant to this ticket:
- `load_grade_config(path) -> GradeConfig` — `GradeConfig(grade_thresholds: dict[str,float],
  hard_rules: dict[str,HardRuleConfig], soft_rules: dict[str,SoftRuleConfig])`, loaded from
  `config/rendering/grade_thresholds.toml` (stdlib `tomllib`, fail-loud on missing keys).
- `evaluate_hard_rule(name, passed, config) -> HardRuleResult(name, passed: bool, delta: float)`
  — binary fact, fixed `pass_delta`/`fail_delta`, no gradient.
- `evaluate_soft_rule(name, raw_value, config) -> SoftRuleResult(name, raw_value: float, delta:
  float)` — trapezoidal, non-monotonic: `peak_delta` inside `[healthy_low, healthy_high]`, ramps
  to `min_delta` at `low`/`high`, held at `min_delta` beyond.
- `combine_rule_deltas(hard_results, soft_results) -> float` — plain additive sum.
- `assign_grade(combined_score, grade_thresholds) -> str` — strict `>` ladder, `S/A/B/C/D/F`.
- `average_scores(per_seed_scores) -> float` — plain arithmetic mean, not special-cased for N=1.

The real (illustrative, uncalibrated per `TCK-20260821-VISUAL-QUALITY-CALIBRATION`, still open)
config today defines exactly one hard rule (`fully_connected`) and one soft rule
(`fill_ratio_healthy_band`) — `config/rendering/grade_thresholds.toml`, read in full. Grade
thresholds are copied by value from SimQ's own (`S=2.0 A=0.5 B=0.0 C=-0.5 D=-1.0`).

### The four sibling metric modules' output shapes actually available as Tier 0 inputs

- `connectivity.py::analyze_connectivity(terrain, blocked_tiles) -> ConnectivityResult
  (walkable_count, component_count, component_sizes: list[int] desc, percent_reachable: float)`
- `density.py::compute_density_cv(entities) -> DensityResult(cv, entity_count, nn_distances:
  list[float])`; `compute_terrain_histogram(terrain) -> dict[str,int]`
- `shape.py::connected_components(terrain, min_size=20, excluded_types={"PLAIN","ROAD"}) ->
  list[ShapeComponent(terrain_type, tiles: frozenset, size, bbox: tuple4, fill_ratio)]`;
  `detect_rotation_match(a, b) -> bool`
- `variants.py::total_variation_distance(h1,h2) -> float`; `compute_trail_activity(...) ->
  float`; `select_trail_entity(...) -> int`; `normalize_histogram(...) -> dict[str,float]`

All four are frozen dataclasses or primitives, none import `AuthoritativeState` directly (callers
extract `state.terrain`/`state.blocked_tiles`/`state.entities` and pass primitives in — confirmed
convention, and this ticket's own new module(s) must follow it).

### `.claude/agents/simulation-analyst.md` — read in full, confirmed shape

No `tools:` frontmatter key (only `name:`/`description:`) — it gets the harness's default full
tool access, `Read` included, already. Body structure: **Data Sources** (3 bullets: run outputs,
registered runs, Mechanics Bible), **Analysis Dimensions** (5 subsections, each explicitly citing
a Mechanics Bible chapter — Ch01/02/03/04/05), **Anomaly Classification** (CRITICAL/HIGH/
MEDIUM/LOW, defined in mechanics-violation terms: "formula mismatch, conservation broken,
determinism failure" for CRITICAL), **Output** (0. one-line summary ≤200 chars, 1. run summary,
2. anomaly table with dimension/severity/description/evidence/mechanics-law columns, 3. Mechanics
Bible compliance, 4. recommended next steps). The ticket's own paraphrase ("one-line summary,
findings table with severity + evidence, recommended next steps") is accurate but slightly
compresses sections 1 and 3 out of the description — confirmed by reading the real Output list.

**Every one of its five Analysis Dimensions is mechanics-bible-anchored** ("Ch01+Ch05", "Ch02",
"Ch03", "Ch04", "Ch05" — literal subsection headers). This matters directly for Investigation
Point 8 below.

### `.claude/agents/world-debugger.md` — read in full, confirmed different job

System Scope is five specific `src/` trees (`worldassembly`, `worldbuilding`, `worldmodules`,
`worldgeneration`, `content`) plus `src/core/registries.py` — root-cause tracing through the
authoritative pipeline's 17 phases for a *failure symptom* (an error/traceback/broken invariant).
Output is root-cause-location-shaped (file:line, upstream state, pipeline stage, fix
recommendation, regression risk) — nothing about visual/geometric quality, nothing about grading
or severity classification of a *healthy but suboptimal* result (its whole framing assumes
something is broken, not "this looks visually off"). The ticket's own ruling-out is correct,
confirmed by reading, not assumed.

### `experiments/spatial_rendering/PROPOSAL.md` §4c–§4h — read in full

- **§4c**: built and ran a second render mode (`render_annotated.py`) — gridlines every 10 tiles +
  axis labels, compared directly against the plain render on the same `dungeon_crawl` state.
  Real, tested finding: gridlines converted "something looks off in the middle" into a citable
  claim ("biome boundary seam at approximately x=90–95, y=20–60"); plain is better for fast human
  gestalt scanning, annotated is better for agent claims that need to be checkable afterward.
  §1a later resolves the ambiguity explicitly: **annotated/gridlined is the *default* Tier 2
  output**, not a secondary option — plain becomes opt-in/human-only.
- **§4d**: tested a zero-image fill-ratio computation directly from the sparse `terrain` dict,
  found it corroborated the visual finding exactly (same seam, explained by two adjoining
  rectangles) with zero rendering. Proposes the exact three-tier shape this ticket implements:
  Tier 0 pure data/zero image/zero tokens (every world, every sample, free) → Tier 1 compact
  JSON/text digest (default inter-step payload) → Tier 2 actual image, fetched via `Read` only on
  ambiguous-enough Tier 0/1 signal or explicit human request.
- **§4i**: "Renderer determinism — tested directly, not assumed, and confirmed." Three independent
  `render()` calls against the same `dungeon_crawl` state, SHA256-hashed: bit-identical.
  Explicitly proposes "a golden-hash regression test (`assert render(known_state) ==
  known_sha256`)" as the resulting cheap, viable test strategy — **this SHA256 claim is about the
  plain PNG renderer**, already implemented and already tested (`test_render_core.py`, see
  below), not directly about the not-yet-built Tier 0/1 digest. This ticket's AC #3/#5 extend the
  same determinism discipline to the new digest artifact, by analogy, not by reusing evidence that
  already covers the digest itself.
- **§4h**: the concrete end-to-end mechanism this ticket implements, step by step (frame
  rendered → Tier 0 runs automatically, zero agent involvement → Tier 1 digest written as a
  compact JSON sibling artifact → agent reads the digest by default → only on an ambiguous
  Tier 0/1 flag does an agent call `Read` on the real PNG path → which variant depends on why:
  flagged anomaly → annotated/gridlined for citable coordinates, general health-check for a human
  → plain). Explicitly names `simulation-analyst.md` as the structural template and states, "no
  existing subagent in `.claude/agents/` has any image/visual capability today — this would be
  genuinely new ground." Confirmed still true (`grep -l "tools:" .claude/agents/*.md` finds only
  `concern-investigator.md`, which restricts to `Read, Grep, Glob, Bash, WebFetch, WebSearch,
  mcp__knowledge-search__search_docs` — no image-specific restriction pattern exists anywhere in
  this repo's agent definitions to date). §4h explicitly leaves open "the exact digest JSON
  schema, the exact ... threshold ..., and whether this becomes a real
  `.claude/agents/world-render-reviewer.md` file at all" — this ticket's own Assumptions section
  correctly inherits exactly these three open items.

## Mechanics / Engine Constraints

**No `docs/mechanics/` chapter governs this ticket**, same conclusion the `VISUAL-GRADE-SCORER`
investigation reached and independently re-confirmed here: rendering/visual-quality review is not
a simulation law, it is a QA/tooling lane consuming already-shipped structural facts. The one real
engine-contract touchpoint is `docs/engine/contracts/regression_and_verification.md`'s
"Absolute Determinism" law (§4), which `WORLD-RENDER-CORE` already extended with a
render-specific paragraph citing `test_render_core.py`'s golden-hash test. This ticket's AC #3
("Tier 1 digest is deterministic — byte/field-identical across repeated runs") is the same law
applied to a new artifact type (a JSON digest instead of a PNG), and should extend the same
contract section rather than invent a separate determinism doctrine.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: new entry required, `INFRA-375`, following the exact
  precedent of `INFRA-369` (render.py, `WORLD-RENDER-CORE`) through `INFRA-374` (grading.py,
  `VISUAL-GRADE-SCORER`) — this ticket's escalation-gate/Tier-1-digest determinism claim is new,
  real, testable capability with no existing entry covering it. Recommended: `priority: P2`
  (matching all five upstream siblings — report-only, never CI-gated, per this ticket's own Out of
  Scope), `proof_type: parity`.
- `docs/engine/contracts/regression_and_verification.md`: extend §1's "Captured Artifacts" list
  and §4's render-specific determinism paragraph (both already exist, added by
  `WORLD-RENDER-CORE`) with a Tier-1-digest-specific sentence, mirroring exactly how that ticket
  added the render-specific paragraph rather than a wholly new doc.

`docs/plans/world_rendering/idea_world_render_validation.md` is deliberately **not** listed,
matching all five prior siblings' identical judgment call (each one's own investigation excluded
it explicitly): `tickets/todos/world-rendering-core/SEQUENCE.md` assigns "the finished system's
real implemented contract" documentation to the batch's last ticket,
`TCK-20260821-VISUAL-QUALITY-DOCS`, which depends on this ticket precisely so it can document the
real, landed agent-review pipeline rather than a speculative one. Updating it here would be
premature.

## Parity Ledger Overlap

Directly checked `docs/parity_ledger/infrastructure.yaml` INFRA-370 through INFRA-374 (all real,
`status: verified`, `priority: P2`, `proof_type: parity`) — none of the five cover an
escalation-gate or Tier-1-digest determinism claim; all five cover their own single module's raw
output or (for INFRA-374) the grade-assignment mechanism specifically. Confirms this ticket needs
its own entry (`INFRA-375`), not reuse of any existing one. "Report-only, never CI-gated" is
consistent across all five prior entries' `priority: P2` (not P0/P1, and none of their `test_path`
values are wired into any CI gate script — confirmed by this ticket's own Out of Scope matching
the identical wording all five upstream tickets used). No P0 entries anywhere are touched by this
ticket's scope.

## Prior Work

- **`stored_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/investigation.md`** (read in full) — the
  closest-in-kind prior investigation: established the "no Mechanics Bible chapter governs this"
  conclusion, the `INFRA-37x` parity-ID sequencing convention, the flat-file-vs-subpackage module
  placement reasoning (recommended flat file, followed by the shipped `grading.py`), the
  SimQ-independence AST-walk guard pattern (`test_<module>_module_does_not_subclass_pillar_scorer
  _or_import_simq_event_pipeline`), and the "config file, not hardcoded, stdlib-only loader"
  discipline this ticket's Tier 1 digest schema should also follow where a config file is
  warranted (it isn't, for the digest shape itself — see Risks).
- **`tickets/done/TCK-20260821-WORLD-RENDER-CORE.md`** (read in full) — the load-bearing
  prerequisite. Confirms `src/rendering/render.py::render(state, out_path, scale=6) -> dict`'s
  exact stats-dict shape (`width_px, height_px, grid_w, grid_h, terrain_tile_count,
  terrain_histogram, building_tile_count, blocked_tile_count, blocked_tiles_within_bounds,
  entity_count, bounds: tuple4`) — directly reusable Tier 1 digest raw material — and
  `render_output_path(base_dir, run_id, filename) -> str` (`{base_dir}/{run_id}/renders/
  {filename}`, no `RunArtifactRepository` routing). Also confirms a known, deliberately-deferred
  gap (`TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP`) irrelevant to this ticket's scope
  (incremental rendering, not touched here).
- **`tests/unit/rendering/test_render_core.py`** (read in full) — the exact golden-hash pattern
  this ticket's AC #5 test should mirror:
  `test_render_golden_hash_bit_identical_across_three_independent_runs` builds three independently
  constructed but content-equal states, renders each, SHA256-hashes the PNG bytes, asserts all
  three hashes equal. The Tier 1 digest's equivalent test needs the same three-independent-builds
  shape, hashing serialized JSON bytes instead of PNG bytes.
- **`tests/architecture/test_rendering_zero_new_dependency_guard.py`** (read in full) — permanent
  AST-walk guard: every `.py` under `src/rendering/` must import only stdlib or `src.*`. Any new
  module(s) this ticket adds inherit this guard automatically (directory-scoped, not a hardcoded
  file list) — no new guard-test needed for stdlib-only-ness, only for the narrower
  SimQ-independence check (see Anti-Drift Hazards).

## Risks and Open Questions

- **The escalation threshold, decided concretely here per this ticket's own Assumptions
  instruction ("decide jointly with the grade-scorer ticket... now that it's DONE").** Proposed,
  concrete, directly derivable from `grading.py`'s real shipped output types, no new config
  needed:

  ```python
  def should_escalate(hard_results: list[HardRuleResult], grade: str) -> bool:
      return any(not r.passed for r in hard_results) or grade in ("D", "F")
  ```

  Reasoning: this mirrors `simulation-analyst.md`'s own CRITICAL/HIGH severity split in spirit —
  a failed hard rule is a binary broken-fact (CRITICAL-shaped: "formula mismatch" ↔ "connectivity
  fragmented"), and a D/F grade is "severely outside expected range" (HIGH-shaped) even with every
  hard rule passing (e.g. a fill-ratio soft rule pinned at `min_delta` on both extremes). This
  needs zero new config value — it composes two already-shipped `grading.py` outputs
  (`HardRuleResult.passed`, `assign_grade`'s return) rather than inventing a fresh, uncalibrated
  numeric knob on top of an already-uncalibrated one (`TCK-20260821-VISUAL-QUALITY-CALIBRATION`
  has not landed yet — inventing a *second* uncalibrated threshold here would compound, not
  resolve, the batch's real open calibration gap). **Recommend the planner adopt this verbatim or
  near-verbatim** — it is a defensible default, not a placeholder, but the exact grade cutoff
  (`D`/`F` vs. `C`/`D`/`F`) is a soft judgment call the planner can adjust without changing the
  underlying architecture.

- **The Tier 1 digest JSON schema, decided concretely here.** A frozen dataclass, matching every
  sibling module's convention exactly:

  ```python
  @dataclass(frozen=True)
  class Tier1Digest:
      world_id: str
      seed: int
      tick: int
      grade: str                              # grading.assign_grade's return
      combined_score: float                   # grading.combine_rule_deltas's return
      hard_rule_results: tuple[dict, ...]      # {"name", "passed", "delta"} per HardRuleResult
      soft_rule_results: tuple[dict, ...]      # {"name", "raw_value", "delta"} per SoftRuleResult
      terrain_histogram: dict[str, int]        # density.compute_terrain_histogram
      entity_count: int                        # density.DensityResult.entity_count
      connectivity_component_count: int        # connectivity.ConnectivityResult.component_count
      connectivity_percent_reachable: float    # connectivity.ConnectivityResult.percent_reachable
      flagged_shape_components: tuple[dict, ...]  # {"terrain_type","bbox","fill_ratio"} — only
                                                   # components outside the soft rule's healthy band
      escalate: bool                           # should_escalate(...)'s output
      plain_render_path: str | None            # render_output_path(...)'s output, always present
      annotated_render_path: str | None        # None unless escalate is True — see below
  ```

  `hard_rule_results`/`soft_rule_results` are tuples of plain dicts (not the dataclasses
  themselves) specifically because `HardRuleResult`/`SoftRuleResult` are not directly
  `json.dumps`-able without a custom encoder, and this ticket's Out of Scope forbids touching
  `grading.py` itself — converting at the digest boundary (`dataclasses.asdict(r)` per result)
  keeps `grading.py` untouched while making the digest natively `json.dumps(..., sort_keys=True)`-
  able. `sort_keys=True` is required for AC #3's byte-identical claim — plain dict/dataclass field
  order is insertion-order-stable in CPython but `sort_keys=True` removes that as a hidden
  determinism dependency, matching this project's general discipline of not relying on incidental
  ordering guarantees.

- **The single most important architectural resolution: how "zero image is ever fetched via Read"
  (AC #1) can be genuinely enforced, not just asserted.** Investigated both candidate mechanisms
  named in the ticket's own framing:

  1. *Tool-list restriction on the agent's own frontmatter.* Ruled out as the primary mechanism:
     neither `simulation-analyst.md` nor `world-debugger.md` restricts tools today (no `tools:`
     key), and Tier 2 genuinely needs `Read` on a PNG when it *does* escalate — so the same agent
     invocation cannot have `Read` categorically removed. A tool-list restriction can gate *whether
     Read exists at all*, not *when* it may be called within one agent's lifetime — the wrong shape
     for a conditional, same-invocation gate.
  2. **Recommended, and the concrete design this investigation proposes: gate at the render
     step, not at the agent's tool-use discipline.** Make the annotated/gridlined PNG file
     **not exist on disk at all unless `should_escalate(...)` returns `True`** — i.e., the Tier
     0→Tier 1 pipeline function only calls the new `render_annotated()`-equivalent when escalating;
     `annotated_render_path` in the digest is `None` in the non-escalating case, and no file is
     ever written to that path. This converts an unenforceable *behavioral* claim ("the agent
     chooses not to call Read") into a *structural* one ("there is nothing to Read"): even a
     misbehaving or confused agent invocation attempting `Read` on a `None`/absent path fails
     outright (no file found) rather than silently succeeding. This is fully unit-testable —
     assert no PNG file is created under the annotated-output directory after running the pipeline
     against a non-anomalous fixture state, and assert one *is* created (with the expected
     tile-coordinate-bearing content) against an anomalous one.

  **What remains genuinely unenforceable by pytest, stated plainly, not papered over:** whether
  the real `.claude/agents/*.md` subagent's prompt correctly reads `escalate`/`annotated_render_
  path` from the Tier 1 digest before ever attempting `Read`, and correctly refrains from calling
  `Read` on the plain render path as a substitute when the annotated one is absent, is a
  prompt-compliance property — no pytest test can execute a `.claude/agents/*.md` file's own
  reasoning. The mitigation above (file genuinely absent) sharply reduces the blast radius of this
  residual gap (a non-compliant agent can *attempt* `Read` but cannot *succeed* in the
  non-escalating case) but does not eliminate the softer failure mode of the agent reading the
  **plain** render (which — per `WORLD-RENDER-CORE` — is written unconditionally for every frame,
  not gated by this ticket at all) when it should have relied on the digest instead. Flag this for
  Verify/planner attention: AC #1's pytest-provable scope is "the annotated PNG does not exist
  unless escalation fires"; the plain-render-always-exists behavior is `WORLD-RENDER-CORE`'s
  separate, already-shipped, already-out-of-this-ticket's-scope contract, and this ticket cannot
  retroactively gate it without violating its own Out of Scope ("Any change to the renderer itself
  ... beyond consuming their output").

- **New agent vs. folding into `simulation-analyst.md` — investigated, and this leans clearly
  toward "new agent," not a genuine toss-up.** Considerations, weighed directly:
  - *Domain mismatch, the strongest signal.* Every one of `simulation-analyst.md`'s five Analysis
    Dimensions cites a specific Mechanics Bible chapter (Ch01–Ch05) and its CRITICAL/HIGH/MEDIUM/
    LOW classification is defined in mechanics-violation terms ("formula mismatch, conservation
    broken, determinism failure"). This ticket's domain has **no Mechanics Bible chapter at all**
    (confirmed above, independently, twice now — once by `VISUAL-GRADE-SCORER`'s investigation,
    once here) — it is pure geometry/statistics. Adding a sixth "Visual/Spatial Quality" Analysis
    Dimension to `simulation-analyst.md` would be the one dimension with no mechanics citation,
    breaking the file's own internal consistency, and would blur its "escalate CRITICAL findings
    to the `investigate-simulation-result` workflow" contract (that workflow is itself
    mechanics/simulation-behavior-shaped, not a natural escalation target for "biome patch is a
    stamped rectangle").
  - *Tool access is a non-issue either way* — confirmed above, neither existing agent restricts
    tools, so a new agent gets the same default full access `simulation-analyst.md` already has;
    this consideration does not favor either option.
  - *`PROPOSAL.md` §4h's own conclusion*, reached independently in the brainstorm phase, already
    named a **new**, `simulation-analyst.md`-*modeled* (not `simulation-analyst.md`-*extended*)
    agent — "a `world-render-reviewer`-shaped subagent, modeled directly on `simulation-analyst.
    md`'s structure." This ticket's own Related Code Areas cites `simulation-analyst.md` as "the
    closest structural template" — template, not host.
  - *Reusability/scope*: a dedicated agent can evolve its own severity vocabulary
    (structural-shape severity is not naturally CRITICAL/HIGH/MEDIUM/LOW in the same sense — a
    stamped-rectangle biome is not "broken" the way a conservation-law violation is) without
    touching a file five other, unrelated Mechanics-Bible dimensions depend on.

  **Recommendation: `.claude/agents/world-render-reviewer.md`, new file, structurally modeled on
  `simulation-analyst.md`'s Data Sources / Analysis Dimensions / Severity Classification /
  Output shape** (per PROPOSAL.md §4h's own synthesis), reusing the CRITICAL/HIGH/MEDIUM/LOW
  vocabulary as a shared cross-agent convention but redefining each level in visual/geometric
  terms (e.g., CRITICAL = a hard rule failed / grade F; HIGH = grade D; MEDIUM = a soft rule near
  an extreme but grade still C+; LOW = within healthy band). This is stated as a clear
  recommendation with reasoning, not a hard mandate — the planner has final say, but the
  investigation does not find this to be a genuinely close call.

- **Config file needed for the digest shape itself? No — only `grading.py`'s existing config is
  needed.** The Tier 1 digest schema and `should_escalate` threshold proposed above need zero new
  `config/rendering/*.toml` entries; they compose already-config-driven `grading.py` outputs. Do
  not add a second config file for "escalation threshold" — that would fragment one grading
  decision (already config-driven via `grade_thresholds.toml`) across two files for no benefit.

## Anti-Drift Hazards

- **Do not let the escalation gate silently become a second, competing threshold system.**
  `should_escalate` must compose `grading.py`'s real `HardRuleResult`/grade output, never
  duplicate or re-derive a parallel healthy-band check against raw metric values directly — that
  would bypass `grading.py`'s already-config-driven, already-tested combination logic and create
  two sources of truth for "is this anomalous."
  `test_<module>_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`-style guard
  (density.py/shape.py's pattern) should be mirrored for this ticket's new module(s), same
  reasoning as all four prior metric siblings.
- **Do not write the annotated PNG unconditionally "for convenience" or "to warm a cache."** The
  entire structural argument for AC #1's enforceability (see Risks) depends on the file genuinely
  not existing in the non-escalating case. A well-intentioned "always render both variants, just
  don't tell the agent about the plain one" implementation would silently defeat the one concrete,
  testable guarantee this investigation found for AC #1.
- **Do not let `world-render-reviewer.md` (or wherever this pipeline lands) import
  `src.simulation_quality.*` or `src.observability.events`**, matching the Out-of-Scope line every
  prior sibling in this batch carried and `grading.py`'s own module docstring states explicitly.
- **Do not touch `render.py`/`incremental.py`'s existing plain-render behavior** — this ticket's
  Out of Scope explicitly forbids changing "the renderer itself ... beyond consuming their
  output"; the new annotated renderer is new code, not a modification of the existing plain one.
- **Do not hardcode the escalation threshold's D/F cutoff inline scattered across multiple call
  sites** — define `should_escalate` once, in the new Tier 0/1 module, and have any orchestration
  code (CLI tool, agent-invoked script, whatever the plan chooses) call it, not re-implement the
  grade-string comparison inline.
- **Do not let the Tier 1 digest's JSON serialization rely on incidental dict/dataclass field
  ordering** — use `sort_keys=True` explicitly (see Risks); AC #3's determinism claim would be
  fragile without it even though CPython's insertion-ordered dicts would likely pass by accident
  today.
