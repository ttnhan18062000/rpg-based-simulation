---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, testing]
---

# Epic Plan — Codebase Health Observatory Tooling

**Tracking ticket:** `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`
**Source:** `docs/audits/D24_codebase_health_observatory.md` §J, §L, §M Phase 3-4
**Priority:** P3, deliberately built last — most of its own inputs come from other epics' outputs (e.g. hardened boundary tests from Epic G) or from tooling that already exists.

## Problem

Most of what a "codebase health observatory" needs already exists in some form in this repo — the
gap is wiring it together and adding two genuinely missing pieces, not building from scratch:
`graphify-out/` already provides dependency-graph data (though its corpus mixes code, docs, and
tickets rather than being pure code); a churn script is cheap to make permanent but must exclude
known append-only bookkeeping files (`agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
`docs/REGISTRY.yaml`) or every report drowns in expected noise; and no mechanism persists metrics
over time today.

## Scope for the eventual `create-tickets` pass

- ~~**(2026-08-19) Extracted to `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`.**
  `make codebase-health-baseline`: a permanent target producing the LoC/churn snapshot this
  session ran ad hoc, with the append-only-file exclusions baked in from the start.~~ **Resolved**
  (`TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`, 2026-08-19): built
  `tools/codebase_health_baseline.py` + `make codebase-health-baseline`, computing the LoC/churn/
  dependency table fresh from `git ls-files`/`git log`/the live filesystem on every run, with the
  `agent-monitoring/*.jsonl`/`tickets/working_log.csv`/`docs/REGISTRY.yaml` churn exclusion
  implemented as a real git pathspec (not a post-hoc filter) and verified by a synthetic-noise
  fixture test. On-demand only, not CI-wired, matching the `status-drift-check`/
  `agent-monitoring-epic-staleness` precedent this epic's Problem section already cites. Extracted
  once confirmed self-contained (no dependency on the rest of this epic's scope) — this epic's own
  prerequisite (Epic G) was also confirmed done at the same time, unblocking the epic as a whole.
- **(2026-08-19) Extracted to `TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`.**
  `code-health impact <path>` command: composable from `graphify-out/`'s existing edge data,
  `tests/architecture/`'s boundary tests (post Epic G hardening), and `docs/REGISTRY.yaml`'s
  existing `related_code_areas` field — full worked design and example (`src/engine/pipeline.py`)
  in `docs/audits/D24_codebase_health_observatory.md` §L. Extracted once each of the 3 data
  sources was individually verified against real, current state — found `graphify` has no
  ready-made "dependents of path X" CLI verb (needs a custom traversal), and
  `related_code_areas` is only 53.3% filled with sometimes-mixed path/symbol-name shapes.
- Historical metric snapshots: an append-only file following the same pattern
  `agent-monitoring/runs.jsonl` already uses, plus a multi-dimension scorecard (trend arrows, not
  a single aggregate score, per the source audit's own explicit guidance against turning this
  into a single number).
- PR/AI change-impact report generator, built on top of the impact-model command above — the
  last item in sequence, since it depends on everything before it.

## Out of scope

- A single aggregate "health score" — the source audit explicitly recommends trend arrows across
  multiple dimensions instead.

**(2026-08-19)** Epic G's boundary-test hardening is confirmed done
(`tickets/done/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC.md`) — the prerequisite that
previously gated this epic's remaining scope is cleared.

## Acceptance signal for this epic (not yet broken into child tickets)

- (LoC/churn baseline: see `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`. Impact
  command: see `TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`. Neither tracked here anymore.)
- Metrics persist across at least two runs in an append-only history file.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic K)
- `docs/audits/D24_codebase_health_observatory.md` (§J, §L, §M Phase 3-4)
