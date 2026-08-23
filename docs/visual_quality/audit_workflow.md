---
status: active
layer: world
authority: P1
audience: developer
tags: [rendering, visualization, simulation-quality, documentation]
---

# Visual Quality Audit Workflow

This is the `docs/visual_quality/` equivalent of
`docs/simulation_quality/audit_workflow.md`, scaled to the real, smaller
visual-quality workflow. Where SimQ's document describes a real, formal 7-phase
`.claude/workflows/simq-audit.js` orchestration, this document describes the two real,
simpler entry points that actually exist for visual-quality — no formal
`/visual-quality-audit` workflow was ever built for this system.

## 1. What this is (and is not)

Unlike SimQ's real `.claude/workflows/simq-audit.js` 7-phase orchestration, **no
equivalent formal multi-phase `/visual-quality-audit` workflow exists** for
visual-quality. There is no `.claude/workflows/*.js`-equivalent file, no formal
governance decision step, and no scripted phase sequence. This document describes the
two real, simpler entry points that do exist, and nothing beyond them.

## 2. Entry Point A — `tools/calibrate_rendering.py`

`run --world <world_id> --seed <seed>` compiles one world+seed, runs all four metric
families against the compiled `AuthoritativeState`, and writes a per-run JSON artifact
to `data/calibration/rendering/{world}_seed{seed}/quality_report.json`. This is guarded
by `CalibrationIntegrityError` on any compile warning, `entity_count == 0`, or
`region_count == 0` condition — it fails loud rather than writing a degenerate report,
and writes a `compile_health.json` sidecar before raising.

`aggregate [--input-dir <dir>] [--output <path>]` scans a directory of already-written
per-run artifacts (default `data/calibration/rendering/`) and writes one
provenance-headed, purely-descriptive JSON report (default
`config/rendering/calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION.json`).
It never opens, parses, or writes `grade_thresholds.toml` — its output is
descriptive statistics only, not a source of gating values.

## 3. Entry Point B — dispatching `world-render-reviewer` over a `Tier1Digest`

`run_tier0_tier1_pipeline(state, world_id, base_dir, run_id, grade_config=None) ->
Tier1Digest` (`src/rendering/review_pipeline.py`) produces the digest a reviewing
agent reads. The `.claude/agents/world-render-reviewer.md` agent reads the digest
first, and reads `annotated_render_path` only when `Tier1Digest.escalate == True` —
it never substitutes `plain_render_path` as an escalation image.

**Four Review Dimensions:**

- **Connectivity** — `connectivity_component_count` / `connectivity_percent_reachable`.
- **Terrain Shape** — `flagged_shape_components` (terrain_type/bbox/fill_ratio outside
  the configured healthy band).
- **Density** — `entity_count` (nearest-neighbor CV is not yet in the digest schema).
- **Grade** — `grade` and `combined_score`, the single-number summary.

**Four-tier Severity Classification:**

- **CRITICAL** — a hard rule failed, or `grade` is `F`.
- **HIGH** — `grade` is `D` with all hard rules passing.
- **MEDIUM** — a flagged shape component sits near a healthy-band extreme but `grade`
  is `C` or better.
- **LOW** — within the healthy band, `grade` is `B` or better.

## 4. Usage

Entry Point A, one run plus an aggregate pass over everything collected so far:

```
python3 tools/calibrate_rendering.py run --world sandbox_world --seed 42
python3 tools/calibrate_rendering.py aggregate
```

Entry Point B, from Python, producing a digest and dispatching the reviewing agent
over it:

```python
from src.rendering.review_pipeline import run_tier0_tier1_pipeline

digest = run_tier0_tier1_pipeline(state, world_id="sandbox_world", base_dir="data/runs", run_id=run_id)
```

The resulting `Tier1Digest` (via `digest_to_json`) is what gets handed to the
`world-render-reviewer` agent dispatch.

## 5. Do not

- Do not treat any `calibrate_rendering.py aggregate` output as a gating/CI-enforced
  value — its own `validation_summary` field states explicitly that no threshold value
  in it is asserted, gated, or final.
- Do not skip Tier 0 straight to fetching the annotated image — the digest is always
  read first, and the annotated image is fetched only when `escalate == True`.
- Do not fabricate a formal orchestrated `/visual-quality-audit` pipeline beyond these
  two entry points — none exists.
