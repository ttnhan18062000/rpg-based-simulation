---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, regression, simulation-quality]
---

# rpg gate baseline: format, staleness and re-baseline

Child 2 of `TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC`. The authoritative description is the docstring of
`tools/test_architecture/rpg_gate_baseline.py`; this page is the short orientation. Testing owns the format and the rules; rpg owns the
content (metric ids, groups, values), the config and the stop lines. The module never names a metric id.

## Files

- One immutable file per version, `rpg_gate_v<N>.json`, in `tests/simulation_quality/rpg_gate/baselines/` (the mutation-baseline convention).
  A re-baseline writes `v<N+1>`; an existing file is never modified (the writer opens with exclusive create).
- Each file carries provenance (commit SHA, harness hash, worlds, seeds, ticks, recorded_at, stale_after), the metric rows, the milestone id and
  a re-baseline record (null for version 1).

## Dual reference

A run is compared with the LAST baseline and the FIRST baseline of the current milestone. Re-baselining every time would otherwise hide a slow drift.

## Staleness

A baseline is stale past `stale_after`, when its harness hash differs from the current harness (an unknown current hash also counts), or when
its worlds, seeds or ticks differ from the config. A stale baseline never yields a pass (roadmap principle 4).

## Re-baseline

`python -m tools.test_architecture.rpg_gate_baseline rebaseline ...` refuses without a divergence id and/or memo row plus a PR, and refuses a
new value outside a stop line (declared in rpg's config) unless an `owner_ruling` is given. The before/after of every changed row is computed from
the two files and stored in the record.

## Rules added in review

- The row key `(id, scope, world, group, key, tick)` is the pairing key the report (child 4) must use. `scope` is `run` or `pooled`; a pooled outcome row has a `value` and no `per_seed`.
- A baseline holds validity rows only at 0 violations; a validity fail is owned in `rpg_gate_known.yaml` (`state: fail`), never normalised by a re-baseline, and no ruling overrides that.
- `provenance.cites` is required and non-empty on every version; a later version must contain the PR and a divergence id or memo row.
- `owner_ruling` is `{ref, date}`; only the owner's ruling counts (a peer's or designer's message does not; a designer-recorded memo row the owner confirmed does).
- Stop lines are checked on every candidate row, so a ruling is needed at each re-baseline while a value stays past the line.

## Open points for rpg

- Config: `tests/simulation_quality/rpg_gate/config.yaml`, rpg's (agreed by rpg-planner). Stop-line shape: `name`, `metric`/`group` free fnmatch patterns (`group` is a property-based kind group, D42, never an EntityRole name), `min`/`max` on a row's value.
- The candidate document a re-baseline reads is the baseline shape without `version` and `rebaseline`; child 4's report will emit it.
