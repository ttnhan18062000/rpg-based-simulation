---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCHEMA
artifact_type: test_plan
tags: [docsite, schema]
---

# Test Plan — TCK-20260606-DOCSITE-SCHEMA

Ticket: Define frontmatter schema for all documentation content types
Date: 2026-06-11

---

## Regression Surface

The following existing tests must still pass without modification after this ticket's work is complete. None of them touch frontmatter or the `docs/guidelines/` schema spec.

| Test file | What it guards | Risk from this ticket |
|---|---|---|
| `tests/docs/test_doc_integrity.py` | Manifest-driven doc existence, headers, terminology, link integrity | None — independent of frontmatter |
| All tests under `tests/unit/`, `tests/integration/`, `tests/engine/` | Simulation logic | None — purely tooling work |

Scoped regression run (no slow tests):

```
pytest tests/docs/ -v
```

---

## New Tests Required

All new tests live in `tests/tools/test_validate_frontmatter.py`.

They test the validator as a function library (import `validate_frontmatter` module directly) rather than subprocess calls, for speed and debuggability. One subprocess test for exit code verification is included.

### Group 1 — Frontmatter detection

| Test | Input | Expected |
|---|---|---|
| `test_no_frontmatter_block` | `.md` file with no `---` opener | violation: missing frontmatter |
| `test_empty_frontmatter_block` | `---\n---\n` (empty block) | violation: missing required fields |
| `test_malformed_yaml_frontmatter` | `---\nkey: [unclosed` | violation: YAML parse error |
| `test_valid_frontmatter_not_at_start` | `---` block that is not the first line | treated as no frontmatter — violation |

### Group 2 — Doc content type (path `docs/mechanics/something.md`)

| Test | Frontmatter | Expected |
|---|---|---|
| `test_doc_valid_authoritative` | All required fields, `status: authoritative`, `last_verified: 2026-01-01` | pass |
| `test_doc_valid_active` | All required fields, `status: active`, no `last_verified` | pass |
| `test_doc_missing_status` | All fields except `status` | violation: missing `status` |
| `test_doc_missing_layer` | All fields except `layer` | violation: missing `layer` |
| `test_doc_missing_authority` | All fields except `authority` | violation: missing `authority` |
| `test_doc_missing_audience` | All fields except `audience` | violation: missing `audience` |
| `test_doc_invalid_status_value` | `status: published` (not in enum) | violation: invalid value for `status` |
| `test_doc_invalid_layer_value` | `layer: unknown_layer` | violation: invalid value for `layer` |
| `test_doc_invalid_authority_value` | `authority: P3` | violation: invalid value for `authority` |
| `test_doc_invalid_audience_value` | `audience: stakeholder` | violation: invalid value for `audience` |
| `test_doc_authoritative_missing_last_verified` | `status: authoritative`, no `last_verified` | violation: `last_verified` required when `status == authoritative` |
| `test_doc_authoritative_with_last_verified` | `status: authoritative`, `last_verified: 2026-01-01` | pass |
| `test_doc_tags_optional_present` | Valid required fields + `tags: [combat, ai]` | pass |
| `test_doc_tags_optional_absent` | Valid required fields, no `tags` | pass |

### Group 3 — Ticket content type (path `tickets/done/TCK-XXXX.md`)

| Test | Frontmatter | Expected |
|---|---|---|
| `test_ticket_valid` | All required ticket fields | pass |
| `test_ticket_missing_ticket_id` | All fields except `ticket_id` | violation: missing `ticket_id` |
| `test_ticket_missing_phase` | All fields except `phase` | violation: missing `phase` |
| `test_ticket_missing_date` | All fields except `date` | violation: missing `date` |
| `test_ticket_invalid_phase` | `phase: wip` (not in enum) | violation: invalid value for `phase` |

### Group 4 — Artifact content type (path `stored_artifacts/TCK-XXXX/plan.md`)

| Test | Frontmatter | Expected |
|---|---|---|
| `test_artifact_valid_investigation` | All required fields, `artifact_type: investigation` | pass |
| `test_artifact_valid_plan` | All required fields, `artifact_type: plan` | pass |
| `test_artifact_valid_test_plan` | All required fields, `artifact_type: test_plan` | pass |
| `test_artifact_missing_ticket_id` | All fields except `ticket_id` | violation: missing `ticket_id` |
| `test_artifact_missing_artifact_type` | All fields except `artifact_type` | violation: missing `artifact_type` |
| `test_artifact_invalid_artifact_type` | `artifact_type: notes` | violation: invalid value for `artifact_type` |

### Group 5 — Archive content type (path `docs/archive/something.md`)

| Test | Frontmatter | Expected |
|---|---|---|
| `test_archive_valid` | `status: archive`, `layer: mechanics`, `original_date: 2024-01-01` | pass |
| `test_archive_wrong_status` | `status: active`, `layer: mechanics`, `original_date: 2024-01-01` | violation: archive files must have `status: archive` |
| `test_archive_missing_original_date` | `status: archive`, `layer: mechanics` | violation: missing `original_date` |
| `test_archive_missing_layer` | `status: archive`, `original_date: 2024-01-01` | violation: missing `layer` |

### Group 6 — Directory scan mode

| Test | Setup | Expected |
|---|---|---|
| `test_directory_all_valid` | Temp dir with 3 valid `.md` files of different content types | pass, 0 violations |
| `test_directory_mixed` | Temp dir with 2 valid + 1 invalid `.md` file | violation reported for the invalid file only |
| `test_directory_skips_non_md` | Temp dir with valid `.md` + `.yaml` + `.txt` | only `.md` checked; pass |
| `test_directory_recursive` | Nested subdirectory structure | all `.md` files at any depth are checked |
| `test_empty_directory` | Empty temp dir | pass, 0 files checked, exit 0 |

### Group 7 — Exit code contract (subprocess tests)

| Test | Scenario | Expected |
|---|---|---|
| `test_exit_0_on_valid_file` | Run script on a valid temp file | exit code 0 |
| `test_exit_1_on_invalid_file` | Run script on a file missing required fields | exit code 1 |
| `test_exit_1_on_missing_frontmatter` | Run script on file with no frontmatter | exit code 1 |

### Group 8 — Anti-drift guards

| Test | What it guards |
|---|---|
| `test_enum_values_status` | Assert `STATUS_VALUES == {"authoritative", "active", "historical", "archive"}` |
| `test_enum_values_layer` | Assert `LAYER_VALUES` contains the exact set defined in the schema spec |
| `test_enum_values_authority` | Assert `AUTHORITY_VALUES == {"P0", "P1", "P2"}` |
| `test_enum_values_audience` | Assert `AUDIENCE_VALUES == {"developer", "agent", "designer", "historical"}` |
| `test_enum_values_artifact_type` | Assert `ARTIFACT_TYPE_VALUES == {"investigation", "plan", "test_plan"}` |
| `test_enum_values_phase` | Assert `PHASE_VALUES == {"open", "inprogress", "blocked", "done"}` |

These tests import the enum constants from `tools/validate_frontmatter.py` directly and assert exact set equality. If anyone adds or removes an enum value without updating both the spec doc and the tests, a test will fail immediately.

---

## Scoped Pytest Commands

Run only during implementation of this ticket:

```bash
# New validator tests only
pytest tests/tools/test_validate_frontmatter.py -v

# Regression: existing doc integrity tests must still pass
pytest tests/docs/ -v

# Combined scoped run (no slow tests)
pytest tests/tools/test_validate_frontmatter.py tests/docs/ -v -m "not slow"
```

Do NOT run `pytest tests/` — that runs the full simulation suite which is out of scope for a pure tooling ticket.

---

## Anti-Drift Test Guards

The Group 8 enum assertion tests are the primary anti-drift mechanism. They enforce that:

1. `tools/validate_frontmatter.py` is the single source of executable truth for valid enum values.
2. Any change to enum values (e.g., adding a new `layer` value during a rollout pass) requires updating both the validator constants and the test assertions in the same commit.
3. `docs/guidelines/frontmatter_schema.md` must document the same values — but is not machine-checked against the validator. The test guards prevent the validator from silently drifting; the spec doc is kept in sync by workflow discipline.

Secondary guard: the exit code subprocess tests (`test_exit_0_on_valid_file`, `test_exit_1_on_invalid_file`) ensure that the CI contract (non-zero exit on error) is not accidentally broken by future refactors of `main()`.
