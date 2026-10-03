---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation — TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

## Origin
Item 2 of `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`, the next item in that epic's
own dependency chain (impact command → historical snapshots → PR report generator). Extracted
into its own ticket once concretely investigated against the real, current state of its 3 claimed
data sources — the epic doc's own framing ("composable almost entirely from data that already
exists") is directionally correct but was verified, not taken on faith, and one real
implementation gap and one real data-quality nuance were found in the process.

## Verifying the 3 claimed data sources

1. **`graphify-out/`'s dependency-graph edge data** — exists, and **a ready-made CLI verb for this
   already exists: `graphify affected "X" --depth N --relation R`** (reverse traversal to find
   nodes impacted by X, default depth 2). **Correction made during Review** (architecture-reviewer
   ran it directly and confirmed working): the original investigation pass missed this verb in
   `graphify --help`'s output and wrongly concluded no dependents-lookup capability existed at all
   — that conclusion was false and has been corrected here.

   **The real, narrower gap** (confirmed live): `affected` operates at symbol/class-node
   granularity, not file granularity — `graphify affected "src/engine/pipeline.py"` returns "No
   unique node match," while `graphify affected "AuthoritativeApplyPipeline"` (a real class defined
   in that file) returns a large real fan-out (2,000+ output lines at `--depth 2`) including
   `kernel.py`. So the actual new-code
   requirement is: (a) resolve a target *file path* to the symbol node(s) `graphify-out/graph.json`
   records as defined in that file, (b) call `affected` (as a subprocess, since it has no `--json`
   output flag — confirmed via `graphify --help`) once per resolved symbol, (c) aggregate/dedupe the
   per-symbol results back to file-level dependents. This is meaningfully less new code than a
   hand-rolled BFS/DFS graph traversal engine — the traversal itself is reused, not rebuilt.
2. **`tests/architecture/`'s boundary tests** — confirmed current, post-Epic-G state: 17 files
   (`test_api_read_model_guard.py`, `test_phase_domain_permissions.py`,
   `test_phase18_import_boundaries.py`, `test_phase19_observability_boundaries.py`, plus 13 more
   covering docker-compose hygiene, hot-path safety, enum migration, etc.). Real, current,
   directly usable as-is for the "relevant invariants + architecture rules" part of the design.
3. **`docs/REGISTRY.yaml`'s `related_code_areas` field** — real, but only **53.3% filled** (1,015
   of 1,905 entries; 890 have an empty list). Sampling 10 non-empty values found most (7/10) are
   real, resolvable paths, but a real minority (3/10 in this sample —
   `discover_candidate_epics`, `parse_body_section`, `skill_staleness_assertions.py`) are bare
   symbol names or bare filenames without directory context, not full paths. **Design implication**:
   this field is a real but partial, mixed-shape signal — the command needs a symbol-name/bare-
   filename resolution step (via graphify's node index or a repo-wide filename search), not a
   literal path-existence check, and must degrade gracefully (not silently drop) when this field
   is empty for the target path — which will be true for roughly half of all lookups.

## D24's own worked example remains the acceptance bar
`docs/audits/D24_codebase_health_observatory.md` §L's `src/engine/pipeline.py` example (subsystem,
direct dependents, required tests, relevant invariants, architecture rules, a caveat note) is
still the one concrete acceptance target — this ticket's job is to make the command produce that
same shape of output for real paths in general, not just reproduce that one example.

## Related
- `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC` (item extracted from here; epic remains
  open for its other 2 items — historical snapshots/scorecard, PR report generator — which stay
  bundled since they build on this command's own output shape, not independently scopable yet)
- `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET` (sibling item already extracted from the
  same epic; unrelated data source, no dependency between the two)
- `docs/audits/D24_codebase_health_observatory.md` §L (worked design + example)
