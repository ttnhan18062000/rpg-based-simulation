---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE
artifact_type: plan
tags: []
---

# Implementation Plan — TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE

## Summary

Promote `experiments/cost_proxy_calibration/validate_rank_order.py` into
`tools/agent-monitoring/weight_sensitivity_check.py` — a tested, parameterized CLI comparing
`cost_proxy_score` rank order under two weight sets. Delete the pre-promotion experiment script;
update its two documented references (`RESULTS.md`, this ticket's own body already lists lines
19/115) to point at the new location.

## Anti-Drift Notes

**Deviation from normal Scope→Investigate→Plan→Review→Implement ordering, self-flagged per this
project's traceability rule**: implementation (`weight_sensitivity_check.py`,
`test_weight_sensitivity_check.py`, both independently verified — 10/10 tests passing) landed
before this file, `investigation.md`, and `test_plan.md` were persisted — a session-limit stall
interrupted the original run partway through. All three staging artifacts were written
retroactively, describing the real, already-verified implementation accurately, not a prospective
plan for unwritten code. Every claim below was independently re-checked against the actual code on
disk, not merely asserted — mirroring `TCK-20260719-AGENT-ROLE-GLOSSARY`'s identical precedent
earlier in this same session.

## Decisions (required by the ticket's own Assumptions/Open Questions, made here)

1. **CLI weight-set serialization: a single JSON-string flag per weight set**
   (`--candidate-weights '{"bash": ..., "agent": ..., "edit": ...}'`, optional
   `--baseline-weights` override). Matches this repo's existing `--data '<json>'` convention
   already used throughout `tools/agent-monitoring/*.py` (`record_run.py`, `record_events.py`) —
   not a new serialization shape invented from scratch.
2. **Old experiment script: deleted after promotion, not left as a thin pointer.** No repo
   precedent was found requiring either choice. Deletion avoids two copies of the same logic
   (inline weight dicts, scoring formula, reporting) drifting apart over time — the promoted
   module is a strict superset of the old script's behavior (parameterized instead of hardcoded,
   plus real tests), so nothing is lost. `RESULTS.md`'s two references updated to point at the new
   location instead of a now-deleted file.

## Steps

### Step 1 — New module: `tools/agent-monitoring/weight_sensitivity_check.py`

Pure function `compute_weight_sensitivity_report(tool_rows_by_group, phase_of, agent_of,
baseline_weights, candidate_weights)` — no file I/O, fully testable with fixture dicts. Internal
helpers: `_score_with_weights()` (deliberately a separate implementation from
`cost_proxy.py::compute_cost_proxy_score` — that function hardcodes the module-level shipped
constants for the real production write path; this tool needs to score under two *arbitrary*
CLI-supplied weight sets, a different contract, same formula), `_spearman_rank_correlation()` (pure
Python, no numpy — `tools/agent-monitoring/*.py` scripts run via bare `python3`), `_group_report()`
(shared bucket/rank/delta shaping for both phase and agent breakdowns). `SHIPPED_WEIGHTS` reads
`cost_proxy.py`'s live `W_BASH`/`W_AGENT`/`W_EDIT` directly (import, never a second hardcoded
literal) as the default baseline comparand. `main()`/CLI: `--candidate-weights` required (no
default, ever), `--baseline-weights` optional (defaults to `SHIPPED_WEIGHTS`), both validated as
parseable JSON with the 3 required keys, clear `ERROR:` messages + exit 1 on bad input.
`_load_tool_rows_and_events()` is the only file-I/O function, kept separate from the pure
computation.

### Step 2 — Tests: `tests/tools/test_weight_sensitivity_check.py`

Fixture-dict style mirroring `test_cost_proxy.py` — no subprocess, no real file dependency. Covers
`_score_with_weights`, `SHIPPED_WEIGHTS`'s live-constant sourcing, Spearman correlation edge cases,
`compute_weight_sensitivity_report()`'s grouping/ranking/skip-on-no-event behavior, and a
material-rank-reorder proof (the actual signal this tool exists to surface).

### Step 3 — Delete the pre-promotion experiment script, update its references

`rm experiments/cost_proxy_calibration/validate_rank_order.py`. Update
`experiments/cost_proxy_calibration/RESULTS.md`'s two references (the Scripts list, and the
"Recommendation" section's re-run instruction) to name the new `tools/agent-monitoring/
weight_sensitivity_check.py` location instead.

### Step 4 — Docs + Makefile

`docs/agent-monitoring/README.md`: new paragraph placed immediately after
`TCK-20260719-COST-PROXY-CALIBRATION-NOTE`'s existing calibration-finding note (confirmed no edit
conflict — that note ends before the Navigation section), stating the promoted tool's path and its
"required check before any weight change" role, plus a `Quick Start` example line.
`Makefile`: new `agent-monitoring-weight-check` target, `$(ARGS)` passthrough (same pattern as
`agent-monitoring-query`), not added to `.PHONY` (matches the existing, confirmed-via-grep
precedent that no other `agent-monitoring-*` target is listed there either).

## Scope Guards

- No change to `tools/agent-monitoring/cost_proxy.py`'s shipped constants or
  `compute_cost_proxy_score()`'s formula.
- No baked-in candidate weight set (no Fit C literal shipped as a default) — every invocation must
  explicitly supply `--candidate-weights`.
- No numpy dependency introduced into `tools/agent-monitoring/`.

## Dependency Map

Step 1 before Step 2 (tests exercise the module Step 1 writes). Step 3 is independent of Steps
1-2 but logically follows (only sensible to delete/redirect once the promoted replacement is real
and tested). Step 4 depends on Step 1 (documents the real, landed tool).

## Acceptance Criteria Map

- AC1 (new module exports a pure function, matches `*_check.py` naming) → Step 1.
- AC2 (fixture-dict-style tests, no subprocess/real-file dependency) → Step 2.
- AC3 (CLI takes two weight sets as args, default baseline = shipped weights, never a hardcoded
  Fit C default) → Step 1.
- AC4 (README documents the tool + its required-check role) → Step 4.
- AC5 (new Makefile target) → Step 4.
- AC6 (RESULTS.md's tool-path references updated) → Step 3.

## Deviations

None from this plan itself (written retroactively to describe the actual landed implementation
exactly) — see Anti-Drift Notes above for the deviation that matters: staging artifacts were
written after implementation, following a session-limit stall, not before.
