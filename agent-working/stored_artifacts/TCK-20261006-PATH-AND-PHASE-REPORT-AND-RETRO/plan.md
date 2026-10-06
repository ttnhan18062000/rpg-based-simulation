---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-PATH-AND-PHASE-REPORT-AND-RETRO
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Plan
1. New `path_report.py`: `analyze` (per tier and `execution_mode`: `path_reason` mix; per planned phase ran / skipped / omitted / conditional-absent and the `skip_reason` mix), `routing` (80% skipped or omitted, 10+ runs carrying the fields, `unstated` at most 25%, with a reason line for a held-back phase), `render_section`, CLI `--week`.
2. `generate_retro.py`: `_paths_section` and a `paths=` argument of `generate`, placed after Gates, never failing the retro.
3. Direction doc: path-record row to `shipped (code)`, routing row note, strike the two resolved "Decisions pending" lines.

## Unresolved Questions

None.
