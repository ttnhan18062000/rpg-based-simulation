---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION
artifact_type: test_plan
tags: [ai, agent-monitoring, data-quality, documentation]
---

# Test Plan — TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION

This ticket is pure documentation (no `src/` or `tools/` behavior change). "Testing" here means:
(1) doc-structure/frontmatter validation that machine-checkable properties hold, and (2) a manual
content-accuracy checklist re-verifying every cited piece of evidence against the real repo state
at Verify time (not just trusting this investigation's snapshot, since the repo continues to
change). There is no behavioral regression surface in `src/` to protect.

## Regression Surface

No `src/` or `tools/` runtime code is touched, so there is no simulation/engine regression surface.
The only pre-existing tests that could be affected by this ticket's file changes are the frontmatter
and registry-machinery tests that run over all `docs/` files:

- **unit / doc-tooling**
  - `tests/tools/test_validate_frontmatter.py` — must keep passing against the new doc's frontmatter (status/layer/authority/audience/tags all valid enum values).
  - `tests/tools/test_tag_registry.py`, `tests/tools/test_layer_registry.py` — confirm no new tag/layer is introduced without registration (this ticket reuses only already-registered tags: `ai`, `agent-monitoring`, `data-quality`, `documentation`; layer `guidelines` is already registered).
  - `tests/tools/test_generate_registry.py` — confirms `docs/REGISTRY.yaml` regeneration picks up the new doc without error.
  - `tests/tools/test_registry_query.py` — confirms `filter_registry`/seed-vocabulary matching still works with the new doc present (sanity check only; this ticket does not change `tools/registry_query.py`).
- **doc-structure (existing sibling pattern)**
  - `tests/docs/test_redaction_retention_policy_doc.py` — unrelated file, but the closest existing example of the doc-structure-assertion pattern this ticket's own new test (below) should follow; must keep passing unmodified since this ticket does not touch `docs/observability/retrieval_retention_redaction_policy.md`.
- **architecture guard (existing)**
  - `tests/tools/test_code_health_impact.py` — must keep passing; this ticket does not change `graphify-out/` handling or the `_requires_graphify` skip logic, only documents the existing behavior. Confirms the doc's claims about this file remain accurate (its skip-marker logic and comment text are cited verbatim in investigation.md).

## New Tests Required

- **Test name:** `test_artifact_retention_classification_doc_exists_and_has_required_sections`
  **Category:** doc-structure (unit)
  **What it verifies:** the new doc file exists at its chosen path and contains one required heading/row per artifact class (all 8: `agent-monitoring/data/`, `stored_artifacts/`, `tickets/done/`, `retro/RETRO-*.md`, `working_log.csv`, `graphify-out/`, `knowledge-index/`, `.claude/current_run`), following the same static-assertion pattern as `tests/docs/test_redaction_retention_policy_doc.py` (read the file as text, assert required section headings and required literal phrases are present — never runtime behavior).
  **Where it should live:** `tests/docs/test_artifact_retention_classification_doc.py`

- **Test name:** `test_artifact_retention_classification_doc_resolves_both_open_questions`
  **Category:** doc-structure (unit)
  **What it verifies:** the `graphify-out/` and `knowledge-index/` rows/sections each contain a resolved recommendation (not the literal string "open question" left unresolved) and cite concrete evidence tokens (e.g. `.gitignore:260`, `.gitignore:264`, a CI-reference-count claim, a tracked-file-count claim) — directly enforces this ticket's acceptance criteria #2/#3/#4.
  **Where it should live:** `tests/docs/test_artifact_retention_classification_doc.py` (same file, second test function)

- **Test name:** `test_artifact_retention_classification_doc_frontmatter_valid`
  **Category:** unit (frontmatter/registry)
  **What it verifies:** the new doc's YAML frontmatter parses and satisfies `tools/validate_frontmatter.py`'s schema for `doc` content type (status/layer/authority/audience present and valid; any tags already registered). This can be covered by running `tools/validate_frontmatter.py` directly rather than a bespoke pytest test if that script already has a corpus-wide test that will pick up the new file automatically (confirm via `tests/tools/test_validate_frontmatter.py` before adding a duplicate).
  **Where it should live:** covered by existing `tests/tools/test_validate_frontmatter.py` corpus scan if it walks all of `docs/`; otherwise add a targeted case there.

- **Test name:** `test_working_log_csv_row_references_parser_ticket_by_id_only`
  **Category:** doc-structure (unit)
  **What it verifies:** the `working_log.csv` row in the new doc contains the literal string `TCK-20260904-WORKING-LOG-CSV-PARSER` and does not duplicate that ticket's own scope text or claim this ticket is blocked on it — a light regex/substring check (e.g. absence of phrasing like "blocked on" or "gated on" adjacent to the ticket ID) guarding against the specific drift this ticket was told to avoid.
  **Where it should live:** `tests/docs/test_artifact_retention_classification_doc.py` (same file, third test function)

## Scoped Pytest Commands

```
pytest tests/docs/ tests/tools/test_validate_frontmatter.py tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v
```

Also run the doc-registry regeneration itself as a functional smoke check (not pytest, but required by CLAUDE.md's After Work step whenever `docs/` changes):

```
make knowledge-index-update
make docs-registry
```

Never run the full suite (`pytest tests/`) for this ticket — there is no code-behavior surface to justify it.

## Anti-Drift Test Guards

- `tests/tools/test_code_health_impact.py` staying green with **zero modifications** is itself a guard: this ticket must describe `graphify-out/`'s existing skip-if-missing behavior, never change it. Any edit to that test file during this ticket is a signal of scope creep into M1-adjacent code, which is explicitly out of scope.
- `tests/docs/test_redaction_retention_policy_doc.py` staying green with **zero modifications** and `docs/observability/retrieval_retention_redaction_policy.md` remaining untouched (`git status` shows no diff to that path) guards against accidentally treating the unrelated retrieval-redaction retention policy as "the same open question" and editing it instead of writing a new doc.
- A `git status` check before closing the ticket confirming the only new/modified files are: the new `docs/guidelines/artifact_retention_classification.md`, optionally `docs/guidelines/agent_working_environment.md` (if the graphify-out/ row is added per the investigation's recommendation), optionally `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md` (M2 status update), plus the ticket file itself, staging/stored artifacts, `docs/REGISTRY.yaml`, and `agent-monitoring/` — guards against accidentally touching `working_log.csv`'s actual parser logic (out of scope) or `tickets/todos/ai-first-hardening-h1-h2-followon/TCK-20260904-WORKING-LOG-CSV-PARSER.md` (sibling ticket, referenced by ID only, never edited by this ticket).
