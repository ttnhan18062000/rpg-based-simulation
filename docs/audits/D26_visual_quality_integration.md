---
status: historical
layer: world
authority: P1
audience: developer
tags: [audit, rendering, visualization, simulation-quality, documentation]
---

# D26 — Visual Quality Module Integration

## Summary

This is the first-ever audit pass for the visual-quality system, covering the 8
prerequisite tickets of the `world-rendering-core` batch
(`TCK-20260821-WORLD-RENDER-CORE` through `TCK-20260821-VISUAL-QUALITY-CALIBRATION`,
all `status: DONE`). The system's raw-metric modules (connectivity, density, shape,
variants-TVD) and its grading/escalation mechanism are implemented, unit-tested, and
empirically verified against real corpus values. The healthy-band threshold *values* in
`config/rendering/grade_thresholds.toml` remain illustrative/uncalibrated by the config
file's own admission — the calibration tooling built to eventually produce real values
exists and is tested, but has not yet been run to produce a committed calibration
report.

**2026-08-25 re-verification**: while auditing the live-map-reconnection and
world-rendering-core epics for anything left outstanding, the full Tier 0 → Tier 1 → Tier 2
pipeline (raw metrics → grading → escalation decision → annotated-PNG write) was driven
live end-to-end for the first time outside pytest, via a new repeatable tool
(`tools/review_pipeline_check.py`, `TCK-20260825-LIVE-VERIFICATION-TOOLING`) — both the
no-escalation and escalation branches confirmed working against real and synthetic data
respectively (see F4). This strengthens F1's confidence but does not change F2 or F3;
threshold calibration remains open and out of scope for this pass.

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | A — Simulation Quality (mirrors D20's own Group assignment — visual-quality is architecturally analogous: raw metrics → grading → threshold ladder, the same shape SimQ uses) |
| **State** | `done` — metric/grading mechanism; `partial` — threshold calibration (see Findings Summary) |
| **Impact** | 3 / 5 — moderate contribution: gives a real, automated way to catch structural/geometric rendering bugs (already caught a real FOREST fill-ratio bug pre-fix), but the rendering system it QA's is itself an explicitly non-authoritative, read-only QA layer over `AuthoritativeState`, not a prerequisite for a core simulation system; absence would be noticeable but manageable via manual review |
| **Interest** | 3 / 5 — useful, standard engineering concern: a tiered Tier 0/1/2 escalation pipeline is a real, sensible cost-control pattern (avoids fetching an image unless Tier 0 flags an anomaly), but it mirrors an existing precedent (SimQ's grading shape) rather than being novel |
| **Priority** | 6 (Impact + Interest) |
| **Method** | code-read + test-run |
| **Audit history** | `2026-08-23 (original, first pass — mechanism verified complete, threshold values confirmed illustrative/uncalibrated)`; `2026-08-25 (re-verification — see below)` |

**Related dimensions:**

| Dimension | Relationship |
|---|---|
| D20 (SimQ Integration) | Structural precedent — visual-quality's grading mechanism reuses SimQ's exact threshold ladder by value, and this doc mirrors D20's own format |
| D10 (Test Coverage & Regression Risk) | The 8 prerequisite tickets added `tests/unit/rendering/`, `tests/architecture/test_rendering_zero_new_dependency_guard.py`, `tests/tools/test_calibrate_rendering.py` |
| D17 (Documentation Currency) | This ticket is itself a documentation-currency action; also the source of the disclosed `audit_dimensions.md` staleness note below |

---

## Findings Summary

| # | Finding | Severity | Status |
|---|---|---|---|
| F1 | Four raw-metric modules + grading mechanism implemented, tested, empirically verified | — | **CONFIRMED REAL** |
| F2 | `config/rendering/grade_thresholds.toml`'s healthy-band rule values remain illustrative/uncalibrated; no `calibration_report_*.json` has been generated/committed; `compute_trail_activity` has zero calibration evidence | Low (disclosed, tracked, non-blocking — no CI gate depends on these values) | **OPEN, DISCLOSED** — tracked by `TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s own completed scope (tooling shipped; calibration pass itself deferred) |
| F3 | `docs/audits/audit_dimensions.md`'s master index is stale — missing D19/D21–D25 and containing a pre-existing D20-duplicate — and was not repaired as part of this ticket | Low | **DISCLOSED, OUT OF SCOPE** — not reflected in `docs/audits/audit_dimensions.md`'s master index, which has been stale since before D19 and is out of scope for this ticket to repair (see this ticket's own `plan.md` Decision 3; a dedicated documentation-hygiene ticket is the correct place to fix it) |
| F4 | The Tier 2 escalation branch (`run_tier0_tier1_pipeline`'s `escalate=True` path — hard-rule failure or grade D/F, real annotated-PNG write) had only ever been exercised by `tests/unit/rendering/test_review_pipeline.py`'s synthetic fixture, never driven live outside pytest, prior to this re-verification | — | **CLOSED** — `tools/review_pipeline_check.py` (`TCK-20260825-LIVE-VERIFICATION-TOOLING`) now drives both branches live and repeatably: a real compiled world (`dungeon_crawl`, seed 42) scores `grade=B combined_score=0.262 escalate=False` with correctly no PNG written; a deliberately disconnected synthetic world scores `grade=F combined_score=-1.000 escalate=True` with a real, valid 98×98/322-byte annotated PNG written to disk. Re-run any time via `python3 tools/review_pipeline_check.py` |
