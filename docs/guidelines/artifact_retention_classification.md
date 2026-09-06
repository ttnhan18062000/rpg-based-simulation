---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [ai, agent-monitoring, data-quality, documentation]
---

# Artifact Retention Classification

This doc classifies every repo artifact class that produces durable output outside the
`agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` weekly shards (already fully classified and
resolved by the shipped `TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC` and
`TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`). It is the M2 deliverable of
`docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`, shipped by
`TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`.

## Taxonomy

Every artifact class below is assigned exactly one of four categories:

- **Ephemeral** — derived/build output that is fully rebuildable from source inputs via a documented
  command; not tied to any single run's lifecycle (persists across many runs until the next rebuild);
  gitignored, never committed.
- **Run-scoped** — exists only for the duration of a single process, tool invocation, or workflow run;
  written fresh per run and never intended to outlive it; gitignored, never committed.
- **Ticket-scoped** — produced by one ticket's own workflow; migrates to a durable location once the
  ticket closes rather than staying attached to the ticket's working files.
- **Long-lived / Institutional** — committed, retained indefinitely as part of the project's durable
  record (audit trail, precedent, cross-referenced by tooling); never pruned by convention.

## Retention Classification Table

| Artifact class | Classification | Recommended Treatment | Evidence / Reference |
|---|---|---|---|
| `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` | Long-lived / Institutional | Already resolved by the shipped weekly-sharding work; keep committed, no change from this ticket | `tickets/done/agent-monitoring-weekly-sharding/TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC.md` (Status: DONE), `tickets/done/agent-monitoring-unified-weekly-data/TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC.md` (Status: DONE), `tools/agent-monitoring/verify_referential_integrity.py` |
| `stored_artifacts/{id}/` | Ticket-scoped → Long-lived / Institutional | Keep permanent; never pruned | Referenced by `docs/REGISTRY.yaml` and `tools/registry_query.py`; read by every ticket's Prior Work investigation step |
| `tickets/done/*.md` | Long-lived / Institutional | Keep permanent; never pruned | Same as above — `docs/REGISTRY.yaml` indexes every closed ticket by ID |
| `agent-monitoring/retro/RETRO-*.md` | Long-lived / Institutional | Keep permanent | Generated and committed by `tools/agent-monitoring/generate_retro.py` |
| `tickets/working_log.csv` | Long-lived / Institutional (currently data-quality-broken) | Keep permanent once its parser/format is fixed — see `TCK-20260904-WORKING-LOG-CSV-PARSER` | `tickets/todos/ai-first-hardening-h1-h2-followon/TCK-20260904-WORKING-LOG-CSV-PARSER.md` (not yet implemented) |
| `graphify-out/` | Ephemeral | Keep gitignored; rebuild via `graphify update .` (incremental) or a full `/graphify` rebuild — never commit | See "graphify-out/ resolution" below |
| `knowledge-index/` | Ephemeral | Keep gitignored; rebuild via `make knowledge-index` (full) or `make knowledge-index-update` (incremental) | See "knowledge-index/ resolution" below |
| `.claude/current_run` | Run-scoped | No change needed; already correctly a per-run sidecar | Written per-run by `.claude/workflows/*.js`; never committed |

### `graphify-out/` resolution

This artifact class is confirmed **Ephemeral** build output, with a resolved
recommendation, not a still-pending question:

- `.gitignore:260` — `graphify-out/*` (the active ignore rule).
- `.gitignore:261` — `src/graphify-out/` (a second, path-qualified ignore rule).
- Zero references to `graphify-out` across `.github/workflows/*.yml` (`grep -rn "graphify-out"
  .github/workflows/` returns no matches) — confirms this build output has zero CI dependency.
- Zero git-tracked files under `graphify-out/` (`git ls-files graphify-out/` returns nothing).
- `tests/tools/test_code_health_impact.py:26-40` already documents and enforces this directly: a code
  comment states "graphify-out/ is entirely gitignored (never committed)", and a `_requires_graphify`
  skip marker (`shutil.which("graphify") is not None and (_REPO_ROOT / "graphify-out" /
  "graph.json").exists()`) gates 4 real-path tests so a fresh CI checkout without a prebuilt graph
  skips rather than fails.
- `TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP` (Status: DONE) landed exactly this
  skip-if-missing pattern as a deliberate, already-shipped fix for this relationship.

**Recommendation:** keep `graphify-out/` gitignored build output as-is. Rebuild via `graphify update .`
(incremental, AST-only, per `CLAUDE.md`'s Graphify Integration section) or a full `/graphify` rebuild.
No further action needed.

### `knowledge-index/` resolution

This artifact class is confirmed **Ephemeral** build output, with a resolved
recommendation, not a still-pending question:

- `.gitignore:264` — `knowledge-index/` (the active ignore rule, immediately preceded by the comment
  "Knowledge search index (local only — rebuild with: make knowledge-index)" at `.gitignore:263`).
- `Makefile:331` — the comment `# developer env only — not CI` immediately precedes the
  `knowledge-index:` target; the target's own `##` help text (`Makefile:334`) repeats "(developer env
  only — not CI)".
- `docs/guidelines/agent_working_environment.md`'s existing "Other Local, Gitignored Caches" table
  already documents two `knowledge-index/` paths (`knowledge.db` at line 278, `retrieval_cache.db` at
  line 280), each citing `.gitignore:264` and a rebuild command.
- `tools/hooks/post-commit-reindex.sh` exists and pairs with `docs/guidelines/agent_working_environment.md:82-87`'s
  description of an installable post-commit hook that runs `make knowledge-index-update` and self-skips
  if `knowledge-index/` does not exist.

**Recommendation:** keep `knowledge-index/` gitignored. Rebuild via `make knowledge-index` (full) or
`make knowledge-index-update` (incremental). No further action needed.

## Related Docs

- `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md` — this doc is
  the M2 deliverable for that epic.
- `docs/guidelines/agent_working_environment.md` — structural precedent for this doc's table shape, and
  the existing home for `knowledge-index/` and (as of this ticket) `graphify-out/` cache documentation.
