---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260904-OWNERSHIP-LIFECYCLE-DOC
artifact_type: test_plan
tags: [ai, documentation, governance]
---

# Test Plan — TCK-20260904-OWNERSHIP-LIFECYCLE-DOC

## Regression Surface

**Unit / doc-structure (`tests/docs/`):**
- `tests/docs/test_artifact_retention_classification_doc.py` — the directly-adjacent M2 sibling
  doc's structure test; must stay green and untouched (proves this ticket did not disturb M2's
  deliverable while adding the new meta-row referencing it).
- `tests/docs/test_redaction_retention_policy_doc.py` — unrelated doc, same static-assertion test
  family/pattern; regression guard only.

**Integration / tooling (`tests/tools/`):**
- `tests/tools/test_validate_frontmatter.py` — the new doc's frontmatter must pass
  `tools/validate_frontmatter.py` unmodified.
- `tests/tools/test_tag_registry.py`, `tests/tools/test_layer_registry.py` — the new doc's tags
  (`ai`, `documentation`, `governance`) and layer (`guidelines`) must already be registry-backed
  (confirmed during Investigation — no new registration expected).
- `tests/tools/test_generate_registry.py`, `tests/tools/test_registry_query.py` — the new doc must
  appear correctly in `docs/REGISTRY.yaml` after regeneration.

## New Tests Required

- **Test name:** `test_subsystem_ownership_lifecycle_doc_exists_and_has_five_columns`
  **Category:** unit (doc-structure)
  **Verifies:** `docs/guidelines/subsystem_ownership_lifecycle.md` exists and its table header
  contains all 5 column names — `Subsystem`, `Accountable role`, `Update trigger`, `Staleness
  signal`, `Removal condition` — fixing the exact defect Investigation confirmed in the draft
  (header missing the 4th named attribute).
  **Where:** `tests/docs/test_subsystem_ownership_lifecycle_doc.py` (new file, following
  `tests/docs/test_artifact_retention_classification_doc.py`'s static-assertion pattern —
  read-as-text, never import/execute the doc).

- **Test name:** `test_subsystem_ownership_lifecycle_doc_covers_both_drafted_rows`
  **Category:** unit (doc-structure)
  **Verifies:** the doc contains both pre-drafted subsystems ("Capability-envelope baseline" /
  "Agent Configuration Maintainer" and "Ticket-claim detection log" / "Workflow Runtime
  Maintainer") with non-empty text in all 5 columns for each.
  **Where:** `tests/docs/test_subsystem_ownership_lifecycle_doc.py`

- **Test name:** `test_subsystem_ownership_lifecycle_doc_documents_each_batch_subsystem_or_justified_exclusion`
  **Category:** unit (doc-structure)
  **Verifies:** each of the 5 named batch subsystems (bash secret-scan hook, tools frontmatter
  rollout, AST import-boundary enforcement, doc-coverage reverse-check, test-scoper hang guard)
  appears in the doc, either as a full table row or inside an explicit exclusion note that names
  the excluding ticket/epic. Mirrors the reverse-check ticket's "resolves both open questions"
  test shape — asserts presence of concrete evidence tokens (a ticket ID) per excluded item rather
  than vague non-decision language.
  **Where:** `tests/docs/test_subsystem_ownership_lifecycle_doc.py`

- **Test name:** `test_subsystem_ownership_lifecycle_doc_defines_role_vocabulary`
  **Category:** unit (doc-structure)
  **Verifies:** the doc contains an explicit role-vocabulary section (e.g. `## Accountable Role
  Vocabulary`) defining every role name used anywhere in the table — asserts every distinct
  "Accountable role" cell value also appears as a defined term in that section, closing the
  dangling-citation gap at the doc that now hosts the vocabulary.
  **Where:** `tests/docs/test_subsystem_ownership_lifecycle_doc.py`

- **Test name:** `test_telemetry_retention_epic_no_longer_cites_roadmap_role_vocabulary`
  **Category:** unit (cross-file doc-structure regression)
  **Verifies:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`
  no longer contains the literal dangling phrase "roadmap's shared role vocabulary" (case-
  insensitive), and instead references the new canonical doc's path
  (`docs/guidelines/subsystem_ownership_lifecycle.md`) somewhere in its M3 section. Directly
  reproduces and closes Investigation's confirmed-dangling-citation finding as a regression guard.
  **Where:** `tests/docs/test_subsystem_ownership_lifecycle_doc.py` (reads both files; same
  cross-file pattern `tests/tools/test_done_checker_static.py`'s reverse-check tests use, applied
  to static doc text instead of git-diff state)

- **Test name:** `test_sibling_epic_docs_link_to_canonical_ownership_doc`
  **Category:** integration (cross-file doc-structure)
  **Verifies:** `governance_capability_policy_epic.md` and `workflow_reliability_epic.md` (both in
  `docs/plans/agent_infrastructure/ai_first_hardening_epics/`) each contain the string
  `docs/guidelines/subsystem_ownership_lifecycle.md`, per this ticket's Scope requirement that
  sibling epic docs link rather than restate rows.
  **Where:** `tests/docs/test_subsystem_ownership_lifecycle_doc.py`

- **Test name:** `test_accountable_role_column_never_names_a_person`
  **Category:** architecture guard (anti-drift)
  **Verifies:** every "Accountable role" table-cell value is drawn from the doc's own declared role
  vocabulary set (a closed, enumerable list of role nouns) — guards against a future edit silently
  substituting a person's name, directly enforcing the source epic doc's explicit "not a person"
  instruction.
  **Where:** `tests/docs/test_subsystem_ownership_lifecycle_doc.py`

## Scoped Pytest Commands

```
pytest tests/docs/ tests/tools/test_validate_frontmatter.py tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v
```

Plus a direct (non-pytest) validator run, matching the M2 sibling ticket's own verification step:

```
python3 tools/validate_frontmatter.py docs/guidelines/subsystem_ownership_lifecycle.md
```

Never `pytest tests/` — scoped to the doc/registry-validation domain this ticket actually touches,
consistent with CLAUDE.md's Testing Rule and this repo's own established pattern for pure-
documentation tickets (see `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`'s Test Summary).

## Anti-Drift Test Guards

- **`test_three_existing_ownership_docs_unmodified`** (architecture guard): asserts
  `docs/testing/content_migration_test_ownership.md`, `docs/simulation/domains/domain_ownership_map.md`,
  and `docs/architecture/cognition_domain_ownership.md` are byte-identical to their pre-ticket
  state (e.g. via a committed content hash or `git diff --quiet` at Verify time) — directly
  enforces the ticket's Out-of-Scope bullet forbidding merge/rewrite of these 3 docs; only a
  cross-link from the *new* doc is permitted.
- **`test_artifact_retention_classification_row_count_unchanged`** (architecture guard): asserts
  `docs/guidelines/artifact_retention_classification.md` still contains exactly its original 8
  artifact-class rows and none of its taxonomy-category text was altered — guards against the
  literal scope-creep this ticket's Out-of-Scope bullet 3 names ("Building or populating M2's...
  table content"), while still permitting this ticket's new doc to reference that file by path in
  a meta-row.
- **`test_draft_m3_table_marked_historical_not_edited_in_place`** (anti-drift, doc-structure):
  asserts `telemetry_retention_epic.md`'s original 4-column M3 draft table (lines ~99-102) is left
  textually intact (still 4 columns, still the same 2 rows) and a separate "M3 is shipped — see
  canonical doc" note is what changed — guards against silently patching the header in place
  instead of following the M2-established supersession pattern, which would create two divergent
  "corrected" surfaces.
- **`test_bash_secret_scan_hook_not_given_shipped_style_row`** (anti-drift): if the bash
  secret-scan hook subsystem appears in the new doc as a full table row (rather than an exclusion
  note), asserts its row is visibly marked speculative/pre-ship (e.g. contains "BLOCKED" or
  "not yet built") rather than reading identically to the 4 shipped/drafted rows — guards against
  quietly inventing staleness/removal metadata for code that does not exist yet.
