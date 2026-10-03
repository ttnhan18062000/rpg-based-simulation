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
2. **Dependents lookup — corrected during Review (see investigation.md's Review-correction note)**:
   do NOT hand-roll a BFS/DFS over `graphify-out/graph.json` — `graphify affected "X" --depth N`
   already implements exactly this traversal and is confirmed working. New code needed:
   (a) resolve the target file path to the symbol/class node(s) `graphify-out/graph.json` records
   as defined in that file (a graph.json lookup, not a traversal), (b) invoke `graphify affected`
   as a subprocess once per resolved symbol (it has no `--json` flag, confirmed via `graphify
   --help` — parse its plain-text output), (c) aggregate and dedupe the per-symbol results back to
   file-level dependents. Use `--depth 2` (the CLI's own default) as this tool's default transitive
   depth, matching D24 §L's "direct dependents" framing while allowing the same flag to expose
   deeper traversal if useful — don't hand-roll a separate depth cap parallel to the one `affected`
   already exposes.
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
5. **Criticality tier — corrected during Review**: `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`
   landed with `tools/codebase_health_baseline.py::compute_churn_lines_changed(repo_root,
   exclude_pathspecs=None)`, which only computes a repo-wide aggregate (hardcoded `"."` pathspec) —
   there is no existing per-path churn function to reuse as-is. To honor "reuse, don't duplicate":
   extend `compute_churn_lines_changed()` with an optional `target_pathspec: str = "."` parameter
   (backward-compatible default — `build_report()`'s existing call site is unaffected), and pass
   `[target_pathspec] + exclude_pathspecs` instead of `["."] + exclude_pathspecs` into the git
   invocation. This new tool then imports and calls that same function with the target path instead
   of writing a second, parallel `git log --shortstat -- <path>` implementation. Combine with the
   target node's graphify edge-degree (in-edges + out-edges count from `graphify-out/graph.json`)
   for centrality.
6. Verify output shape against D24 §L's `src/engine/pipeline.py` example, and at least one
   additional real path with a different profile (e.g. a low-centrality, low-churn file) to prove
   the command doesn't just work for the one file it was designed against.

## Explicitly out of scope
- Historical snapshots, scorecard, and the PR/AI report generator — remain Epic K's own bundled
  scope, built on top of this command's output shape once it exists.
- Perfect precision on architecture-rule matching or required-test inference — this is a
  discovery/triage aid, not a certified coverage oracle; false positives/negatives in its
  suggestions are acceptable as long as they're not silently presented as certain.
