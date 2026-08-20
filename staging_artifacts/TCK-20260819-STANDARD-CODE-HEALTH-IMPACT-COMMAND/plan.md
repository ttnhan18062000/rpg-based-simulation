---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND
artifact_type: plan
tags: [architecture, testing]
---

# Plan — TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

**Planning/scoping only — no implementation.** A separate agent implements.

## Steps

1. New script, e.g. `tools/code_health_impact.py`, taking a target path as its argument
   (`code-health impact <path>`, wired as a new Makefile target or a direct `python3` invocation —
   match whichever convention this repo's newer `tools/` CLIs use, e.g. `tools/parity_index.py`'s
   subcommand style).
2. **Dependents lookup**: load `graphify-out/graph.json` directly, resolve the target path to its
   node(s), and BFS/DFS over edges targeting that node (import/use edge types) to find direct and
   transitive dependents. Cap transitive depth at a reasonable default (e.g. 2-3 hops) to avoid an
   unreadable wall of output for a highly-central file — the D24 §L example only shows direct
   dependents; decide transitive-depth behavior explicitly, don't leave it undefined.
3. **Architecture rules lookup**: match the target path's subsystem against `tests/architecture/`'s
   17 current boundary test files by subsystem-name heuristic (e.g. path prefix or directory
   match) — list the ones plausibly relevant, don't attempt perfect precision.
4. **Required-tests lookup**: combine two signals — (a) `docs/REGISTRY.yaml`'s
   `related_code_areas` field for entries mentioning this path, resolving bare symbol
   names/filenames via graphify's node index rather than literal path matching (per
   investigation.md's finding — do not assume every entry is a clean resolvable path); (b) the
   existing `src/` → `tests/unit/`/`tests/integration/` naming-convention mapping this repo
   already uses elsewhere (`.claude/agents/test-scoper.md`'s own Test Directory Map is a reusable
   reference for this exact mapping — don't reinvent it).
5. **Criticality tier**: derive from churn × centrality, reusing whatever
   `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`'s tool computes for churn (once that
   ticket lands) combined with the target node's graphify edge-degree for centrality — cross-
   reference, don't duplicate the baseline tool's own churn logic.
6. Verify output shape against D24 §L's `src/engine/pipeline.py` example, and at least one
   additional real path with a different profile (e.g. a low-centrality, low-churn file) to prove
   the command doesn't just work for the one file it was designed against.

## Explicitly out of scope
- Historical snapshots, scorecard, and the PR/AI report generator — remain Epic K's own bundled
  scope, built on top of this command's output shape once it exists.
- Perfect precision on architecture-rule matching or required-test inference — this is a
  discovery/triage aid, not a certified coverage oracle; false positives/negatives in its
  suggestions are acceptable as long as they're not silently presented as certain.
