---
status: active
layer: world
authority: P1
audience: developer
tags: [rendering, visualization, simulation-quality, documentation]
---

# Visual Quality Current State

This is the `docs/visual_quality/` equivalent of
`docs/simulation_quality/current_state.md` — a chronologically-appended, dated-session
log, not a single static snapshot. This is the first entry, since this is the
visual-quality system's first such record.

## 2026-08-23 — Initial capture: mechanism complete, threshold values illustrative

This is the load-bearing anti-drift content of this entire ticket. Read it precisely:
the metric/grading **mechanism** is real, finished, and tested. The healthy-band
**threshold values** it currently operates on are illustrative placeholders, not
calibrated numbers. Do not conflate the two.

**Real and finished:**

All four raw-metric modules (connectivity, density, shape, variants-TVD) are
implemented, unit-tested, and empirically verified against real corpus values. Cite the
anchors verbatim, uncomputed: density CV `0.6478017242079448` (`sandbox_world`) /
`0.6782405727873148` (`dungeon_crawl`); TVD `0.23161981243456373`
(`sandbox_world`/`dungeon_crawl`). The grading mechanism (hard/soft rule evaluation,
additive combination, S–F assignment) is implemented and tested, reusing SimQ's exact
threshold ladder by value: `S=2.0/A=0.5/B=0.0/C=-0.5/D=-1.0`.

**Still illustrative, not calibrated:**

The actual healthy-band *rule* values in `config/rendering/grade_thresholds.toml`
(`[hard_rules.fully_connected]` pass/fail deltas; `[soft_rules.fill_ratio_healthy_band]`
low/healthy_low/healthy_high/high) are explicitly documented in the config file's own
header comments, quoted directly: **"Illustrative values only, NOT calibrated"** —
stated once above `[hard_rules.fully_connected]` and once above
`[soft_rules.fill_ratio_healthy_band]`. The S/A/B/C/D ladder itself is, per that same
file's header, "copied BY VALUE from `config/simulation_quality/grade_thresholds.yaml`
... this file does NOT import or reference that file." State this plainly: the ladder
values are shared with SimQ by copy, but the hard/soft rule thresholds that feed into
that ladder for rendering are not calibrated.

**Calibration tooling status:**

`tools/calibrate_rendering.py` exists, is tested (`run`/`aggregate` subcommands), and
can produce descriptive min/max/mean statistics per family from real per-`(world,
seed)` runs. Its `aggregate` mode's own `validation_summary` field states plainly:
"Descriptive calibration statistics only -- no threshold value in this report is
asserted, gated, or final. Not consumed by any pytest/CI gate or scoring pipeline."

As of this entry, **no `config/rendering/calibration_report_*.json` file exists on
disk** — confirmed by listing `config/rendering/`, which contains only
`grade_thresholds.toml`. The aggregate report has never been generated/committed as a
run artifact. `compute_trail_activity` (`src/rendering/variants.py`) has zero
calibration evidence at all — it has never been run, and it is not wired into
`tools/calibrate_rendering.py`.

**Related:**

- `docs/visual_quality/scoring_contract.md`
- `config/rendering/grade_thresholds.toml`
- `tools/calibrate_rendering.py`
- Parity ledger `INFRA-372` (shape threshold explicitly flagged "uncalibrated and
  provisional")
- Parity ledger `INFRA-376` (calibration-script run-integrity guard)
