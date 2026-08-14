---
status: active
layer: guidelines
authority: P1
audience: developer
---

# Frontmatter Schema

## Overview

Every markdown file in this project must carry a YAML frontmatter block that classifies
the file by content type, status, layer, authority, and audience.

This schema is the foundation for Docusaurus navigation, Registry generation, and agent
doc discovery. It applies to all `.md` files under `docs/`, `tickets/`, `stored_artifacts/`,
and `docs/archive/`.

The validator `tools/validate_frontmatter.py` enforces this schema. The enum constants in
that script are the single executable source of truth. The values listed in this document
must always match those constants exactly.

---

## Content Type Detection

The content type of a file is determined by its path. An explicit `content_type` field in
the frontmatter overrides path inference.

| Path prefix | Inferred content type |
|---|---|
| `tickets/` | `ticket` |
| `stored_artifacts/` | `artifact` |
| `docs/archive/` | `archive` |
| All other `docs/` | `doc` |
| Anything else | `doc` (fallback) |

---

## Schema by Content Type

### `doc` — General documentation

Applies to all files under `docs/` that are not in an archive subdirectory.

| Field | Required | Type | Valid Values |
|---|---|---|---|
| `status` | yes | enum | see STATUS_VALUES |
| `layer` | yes | enum | see LAYER_VALUES |
| `authority` | yes | enum | see AUTHORITY_VALUES |
| `audience` | yes | enum | see AUDIENCE_VALUES |
| `tags` | no | list of strings | free-form |
| `last_verified` | conditional | ISO 8601 date | required when `status: authoritative` |

**Conditional rule:** `last_verified` is required when `status` is `authoritative`.

Example:
```yaml
---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-01-15
tags: [combat, damage]
---
```

---

### `ticket` — Ticket files

Applies to files under `tickets/done/` and `tickets/inprogress/`.

| Field | Required | Type | Valid Values |
|---|---|---|---|
| `status` | yes | enum | see STATUS_VALUES |
| `layer` | yes | enum | see LAYER_VALUES |
| `authority` | yes | enum | see AUTHORITY_VALUES |
| `audience` | yes | enum | see AUDIENCE_VALUES |
| `ticket_id` | yes | string | e.g. `TCK-20260606-DOCSITE-SCHEMA` |
| `phase` | yes | enum | see PHASE_VALUES |
| `date` | yes | ISO 8601 date | ticket creation date |
| `tags` | no | list of strings | see `docs/guidelines/tag_taxonomy.md` — controlled vocabulary, forward-only enforced from `2026-07-04` |

Example:
```yaml
---
status: active
layer: ticket
authority: P1
audience: developer
ticket_id: TCK-20260606-DOCSITE-SCHEMA
phase: done
date: 2026-06-06
---
```

---

### `artifact` — Stored staging artifacts

Applies to files under `stored_artifacts/` (plan.md, investigation.md, test_plan.md).

| Field | Required | Type | Valid Values |
|---|---|---|---|
| `status` | yes | enum | see STATUS_VALUES |
| `layer` | yes | enum | see LAYER_VALUES |
| `authority` | yes | enum | see AUTHORITY_VALUES |
| `audience` | yes | enum | see AUDIENCE_VALUES |
| `ticket_id` | yes | string | parent ticket ID |
| `artifact_type` | yes | enum | see ARTIFACT_TYPE_VALUES |
| `tags` | no | list of strings | see `docs/guidelines/tag_taxonomy.md` — controlled vocabulary, forward-only enforced from `2026-07-04` |

Example:
```yaml
---
status: historical
layer: artifact
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCHEMA
artifact_type: plan
---
```

---

### `archive` — Archived and retired documents

Applies to files under `docs/archive/`.

| Field | Required | Type | Valid Values |
|---|---|---|---|
| `status` | yes | enum | must be `archive` |
| `layer` | yes | enum | see LAYER_VALUES (`misc` is acceptable) |
| `original_date` | yes | ISO 8601 date | original creation or publish date |

**Constraint:** `status` must always be `archive` for files of this content type.

Example:
```yaml
---
status: archive
layer: misc
original_date: 2024-03-10
---
```

---

## Enum Reference

All values listed here must match the constants in `tools/validate_frontmatter.py` exactly.

### STATUS_VALUES
`authoritative`, `active`, `historical`, `archive`

### LAYER_VALUES
`mechanics`, `engine`, `testing`, `simulation`, `ai`, `architecture`, `core`, `ticket`,
`artifact`, `guidelines`, `observability`, `performance`, `combat`, `compliance`,
`strategy`, `systems`, `economy`, `world`, `misc`

### AUTHORITY_VALUES
`P0`, `P1`, `P2`

### AUDIENCE_VALUES
`developer`, `agent`, `designer`, `historical`

### PHASE_VALUES
`open`, `inprogress`, `blocked`, `done`

### ARTIFACT_TYPE_VALUES
`investigation`, `plan`, `test_plan`

---

## Validator Usage

Run the validator against a single file:

```bash
python3 tools/validate_frontmatter.py docs/mechanics/01_entity_anatomy.md
```

Run against an entire directory tree:

```bash
python3 tools/validate_frontmatter.py docs/
python3 tools/validate_frontmatter.py tickets/done/
python3 tools/validate_frontmatter.py stored_artifacts/
```

Override content type inference (useful for files at non-standard paths):

```bash
python3 tools/validate_frontmatter.py path/to/file.md --content-type archive
```

Exit codes:
- `0` — all files pass schema validation
- `1` — one or more violations found

Errors are printed to `stderr`; the summary line is printed to `stdout`.

---

## Related Tools

| Tool | Purpose |
|---|---|
| `tools/validate_frontmatter.py` | Validate any file or directory against this schema |
| `tools/generate_registry.py` | Read frontmatter from all docs + tickets/done/ → emit `docs/REGISTRY.yaml` |
| `tools/add_frontmatter_live.py` | Bulk-apply frontmatter to live docs/ (re-run if adding a new directory) |
| `tools/add_frontmatter_archive.py` | Bulk-apply minimal archive frontmatter to docs/archive/ etc. |
| `tools/add_frontmatter_tickets.py` | Bulk-apply frontmatter to tickets/done/ and stored_artifacts/ |
| `tools/generate_artifact_pages.py` | Generate stored_artifacts/*/index.md landing pages for Docusaurus |

See `make docs-serve` (Docusaurus 3 at `website/`) and `make docs-registry` for the consumer side of this schema.

---

## Extension Guide

To add a new `layer` value (e.g., `narrative`):

1. Update `LAYER_VALUES` in `tools/validate_frontmatter.py`.
2. Update the LAYER_VALUES list in the "Enum Reference" section of this document.
3. Update the `test_enum_values_layer` assertion in `tests/tools/test_validate_frontmatter.py`
   to include the new value.
4. Commit all three changes together under the same ticket reference.

The same process applies to any other enum (STATUS, AUTHORITY, AUDIENCE, PHASE, ARTIFACT_TYPE).
Never update one without updating the others in the same commit — the Group 8 anti-drift
tests will fail if they are out of sync.
