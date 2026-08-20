---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
artifact_type: plan
tags: [architecture, testing]
---

# Plan — TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET

**Planning/scoping only — no implementation.** A separate agent implements.

## Steps

1. Add a new script, e.g. `tools/codebase_health_baseline.py`, that measures and prints (or writes
   as JSON, implementer's choice — but at minimum human-readable stdout, matching this repo's
   `tools/parity_index.py`/`epic_staleness_check.py` CLI convention) the metrics table from
   investigation.md's "What this specific item needs to produce" section, computed fresh from the
   live repo state:
   - `git ls-files` + `wc -l` for source/test LoC and file counts (mirroring the methodology
     already implicitly used to produce D24 §B/§C's numbers — infer the exact split rule for
     "source" vs. "test" from how `src/` vs `tests/` are already partitioned repo-wide).
   - `git log --shortstat` or equivalent for churn, **excluding**
     `agent-monitoring/*.jsonl`, `tickets/working_log.csv`, `docs/REGISTRY.yaml` via a pathspec
     exclusion, not a post-hoc filter (avoid pulling the excluded files' history into the
     computation at all).
   - `find` or `git ls-files` counts for top-level `src/` packages, test subdirectories, `.md` doc
     count, `docs/REGISTRY.yaml` size.
   - `git log --oneline | wc -l` for commit count.
2. Add a `Makefile` target, `codebase-health-baseline`, invoking the script — matching the
   existing `agent-monitoring-*`/`parity-index*` target-naming convention.
3. Decide (and document the decision, don't leave it implicit) whether this target is CI-wired or
   on-demand-only — this session found at least 2 other tools in this same family
   (`status-drift-check`, `agent-monitoring-epic-staleness`) that are Makefile-only, not CI-gated;
   default to on-demand-only unless there's a specific reason to gate CI on it, consistent with
   that established local convention.
4. Run it once against the live repo to confirm it produces sensible, non-stale numbers (verifying
   against investigation.md's caveat that D24 §C's own numbers are now outdated).

## Explicitly out of scope
- The `code-health impact <path>` command, historical snapshots/scorecard, and PR/AI report
  generator — these remain Epic K's own bundled scope, not extracted here, since they're
  genuinely sequential (impact command → snapshots need its data shape → PR report builds on the
  impact model) and still have open design decisions (exact scorecard dimensions) unresolved.
- A single aggregate "health score" — per the source audit's explicit guidance, if this target
  later feeds a scorecard (Epic K's own remaining scope), that scorecard must use trend arrows
  across dimensions, not a single number. Not directly relevant to this ticket's own scope (a
  point-in-time baseline snapshot, not a scorecard), noted for forward consistency only.
