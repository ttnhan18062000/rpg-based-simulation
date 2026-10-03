---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCHEMA
artifact_type: investigation
tags: [docsite, schema]
---

# Investigation — TCK-20260606-DOCSITE-SCHEMA

Ticket: Define frontmatter schema for all documentation content types
Date: 2026-06-11

---

## Current Behavior

### tools/ directory (as of 2026-06-11)

| File | Purpose |
|---|---|
| `tools/validate_working_log.py` | Validates `tickets/working_log.csv` — checks duplicates, missing entries, empty fields. Exit 0/1. |
| `tools/extract_defs.py` | Definition extraction utility (unrelated to docs). |
| `tools/test_docker.py` | Docker smoke test (unrelated). |
| `tools/viz_strategy.html` | Static HTML visualizer (unrelated). |
| `tools/agent-monitoring/` | Agent monitoring output directory. |

No `validate_frontmatter.py` exists. No frontmatter validation infrastructure exists anywhere in the project.

### docs/guidelines/ directory (as of 2026-06-11)

| File | Purpose |
|---|---|
| `design_patterns.md` | OOP design patterns: Plugin, Strategy, Builder, Typed Dataclass patterns. Coding conventions. |
| `fallback_retirement_criteria.md` | Criteria for retiring legacy fallback paths. |
| `v2_intentional_divergences.md` | Canonical record of V2 behavior shifts from legacy. |
| `README.md` | Index file for guidelines directory. |

No `frontmatter_schema.md` exists. No frontmatter specification exists anywhere in the project.

### Existing doc integrity tests (`tests/docs/test_doc_integrity.py`)

The existing doc test suite covers:
- Manifest-driven file existence checks (`docs/engine/manifest.json`)
- Structural compliance (required markdown headers per document)
- Terminology alignment (RuntimeMode, HardwareClass, FailureKind enums vs manifest)
- Scoped reporting compliance (release report fields)
- Recorder enforcement logic (CertificationResult fields)
- Release target binding (lawbook vs manifest)
- Link integrity (local file links in mandatory docs)

None of these tests check YAML frontmatter. They are entirely independent of the new schema work and must not be broken.

### Existing validator pattern (`tools/validate_working_log.py`)

Established conventions to follow:
- Shebang + module docstring at top
- argparse-free: hardcoded paths for single-purpose validators (but `validate_frontmatter.py` needs path argument per AC)
- `main()` function pattern, `if __name__ == "__main__": main()`
- Collect all errors into a list before printing
- Print errors to `sys.stderr`
- `sys.exit(0)` on success, `sys.exit(1)` on any error
- Human-readable OK summary on stdout on success

---

## Schema Requirements

Derived from ticket AC, `tickets/todos/doc_feature/PLAN-DOCSITE.md`, and the ticket's Assumptions / Open Questions section.

### Content Type: `doc`

Applies to: `docs/` tree (mechanics, engine, core, architecture, guidelines, testing, combat, strategy, etc.)

| Field | Required | Type | Valid Values |
|---|---|---|---|
| `status` | yes | enum | `authoritative` / `active` / `historical` / `archive` |
| `layer` | yes | enum | `mechanics` / `engine` / `testing` / `simulation` / `ai` / `architecture` / `core` / `ticket` / `artifact` / `guidelines` |
| `authority` | yes | enum | `P0` / `P1` / `P2` |
| `audience` | yes | enum | `developer` / `agent` / `designer` / `historical` |
| `tags` | no | list of strings | free list |
| `last_verified` | conditional | ISO 8601 date string | required when `status == authoritative` |

### Content Type: `ticket`

Applies to: `tickets/done/`, `tickets/inprogress/`

| Field | Required | Type | Valid Values |
|---|---|---|---|
| `status` | yes | enum | `authoritative` / `active` / `historical` / `archive` |
| `layer` | yes | enum | same as doc |
| `authority` | yes | enum | `P0` / `P1` / `P2` |
| `audience` | yes | enum | same as doc |
| `ticket_id` | yes | string | e.g. `TCK-20260606-DOCSITE-SCHEMA` |
| `phase` | yes | enum | `open` / `inprogress` / `blocked` / `done` |
| `date` | yes | ISO 8601 date string | ticket creation date |
| `tags` | no | list of strings | free list |

### Content Type: `artifact`

Applies to: `stored_artifacts/*/` (plan.md, investigation.md, test_plan.md)

| Field | Required | Type | Valid Values |
|---|---|---|---|
| `status` | yes | enum | `authoritative` / `active` / `historical` / `archive` |
| `layer` | yes | enum | same as doc |
| `authority` | yes | enum | `P0` / `P1` / `P2` |
| `audience` | yes | enum | same as doc |
| `ticket_id` | yes | string | parent ticket ID |
| `artifact_type` | yes | enum | `investigation` / `plan` / `test_plan` |
| `tags` | no | list of strings | free list |

### Content Type: `archive`

Applies to: `docs/archive/`, `docs/superpowers/specs/`

| Field | Required | Type | Valid Values |
|---|---|---|---|
| `status` | yes | enum | must be `archive` |
| `layer` | yes | enum | same as doc |
| `original_date` | yes | ISO 8601 date string | original creation/publish date |

Note: `authority` and `audience` are intentionally minimal for archive content per ticket AC. The ticket specifies only `status: archive`, `layer`, and `original_date` as required.

---

## Python Validator Design

### File location

`tools/validate_frontmatter.py`

### Interface

```
python3 tools/validate_frontmatter.py <path>
```

`<path>` is either a single `.md` file or a directory (recursively scanned for `.md` files).

### Exit codes

- `0` — all checked files pass schema validation
- `1` — one or more schema violations found (CI-safe)

### Behavior

1. Accept a single positional argument: file path or directory path.
2. If directory: recursively find all `.md` files.
3. For each file:
   a. Detect whether a YAML frontmatter block is present (`---` delimited at file start).
   b. If no frontmatter: record a violation (missing frontmatter).
   c. If frontmatter present: parse the YAML block.
   d. Detect content type from the `content_type` field (or infer from path — see open question below).
   e. Validate required fields are present and contain valid enum values.
   f. Apply conditional rules (e.g., `last_verified` required when `status == authoritative`).
   g. Collect all errors per file.
4. After processing all files: print errors to `stderr`, print summary to `stdout`.
5. Exit 0 if no errors, exit 1 otherwise.

### Implementation approach

- Use Python stdlib only: `pathlib`, `sys`, `argparse` (for clean CLI), `re` for frontmatter extraction.
- Use `tomllib` or inline YAML parsing. Since stdlib has no YAML parser, use `PyYAML` (`import yaml`) — already a project dependency (check `requirements*.txt`), or use a minimal regex-based extraction for the simple key: value pairs used in frontmatter.
- Define schema as a plain dict of dicts (no external schema library needed for this scope).
- Must be idempotent: running twice produces identical output.
- Must not import any simulation source (`src/`) — pure tooling.

### Schema definition structure (internal)

```python
CONTENT_TYPES = {
    "doc": {
        "required": ["status", "layer", "authority", "audience"],
        "optional": ["tags", "last_verified"],
        "conditional": [("last_verified", lambda fm: fm.get("status") == "authoritative")],
        "enums": { ... }
    },
    "ticket": { ... },
    "artifact": { ... },
    "archive": {
        "required": ["status", "layer", "original_date"],
        "field_constraints": {"status": ["archive"]},
        ...
    }
}
```

### Content type detection

Two viable strategies:
1. **Explicit field**: require a `content_type` field in every frontmatter block (`doc` / `ticket` / `artifact` / `archive`). Clean and unambiguous.
2. **Path inference**: infer from directory prefix (`tickets/` → ticket, `stored_artifacts/` → artifact, `docs/archive/` → archive, `docs/` → doc).

Recommendation: use path inference as default with explicit `content_type` override when present. This avoids requiring a new field on every file during the rollout passes.

---

## Risks and Open Questions

### Open Questions (from ticket)

1. **`status` values sufficient?** Ticket proposes `authoritative` / `active` / `historical` / `archive`. The PLAN-DOCSITE.md is consistent with this. Appears sufficient for all four passes. **Recommendation: confirm and lock these four.**

2. **`layer` values may need additions.** Current list: `mechanics` / `engine` / `testing` / `simulation` / `ai` / `architecture` / `core` / `ticket` / `artifact` / `guidelines`. The `docs/observability/`, `docs/performance/`, `docs/combat/`, `docs/compliance/`, `docs/strategy/`, `docs/systems/` directories are not covered. **Risk: rollout passes (Tickets 3–5) will encounter `layer` values not in the enum and fail validation.** Recommendation: add `observability` / `performance` / `combat` / `compliance` / `strategy` / `systems` to the layer enum now.

3. **`authority` mirrors parity ledger priorities.** This is consistent — `P0` / `P1` / `P2` is already established in `docs/parity_ledger/`. No ambiguity.

4. **`last_verified` required for authoritative docs?** Ticket suggests yes. This is safe and aligns with the parity ledger's existing `status: verified` + `test_path` contract. **Recommendation: make it required when `status == authoritative`.**

5. **Validator scope: `.md` only?** Ticket suggests `.md` only — parity ledger `.yaml` files already have their own schema and validation paths. **Recommendation: `.md` only.**

6. **`content_type` field or path inference?** Not addressed in ticket. See validator design section above.

7. **PyYAML dependency.** The validator must parse YAML frontmatter. PyYAML is a common Python dependency. If it is not in `requirements.txt`, either add it or implement a minimal regex-based frontmatter parser (sufficient for simple flat YAML). This must be confirmed during implementation.

### Risks

- **Layer enum incompleteness**: if the layer enum is not comprehensive enough before rollout passes start, all three parallel tickets (3, 4, 5) will generate false-positive validation failures. This is the highest-risk item.
- **Archive content type strictness**: archive files may have very inconsistent or missing dates. The validator may need a `--warn` vs `--error` mode, or the archive content type must use `last_verified` optionally.
- **Content type ambiguity at boundaries**: `staging_artifacts/` (not yet done) vs `stored_artifacts/` (done). Path inference must handle both correctly.
- **No frontmatter on any existing file**: currently zero files have frontmatter. The validator run on `docs/` will fail everything until rollout passes are complete. CI integration must be deferred until at least one pass is complete.

---

## Anti-Drift Hazards

1. **Enum value drift between schema spec and validator**: `docs/guidelines/frontmatter_schema.md` and `tools/validate_frontmatter.py` must define enums from a single source of truth. If the spec doc is updated manually without updating the script (or vice versa), validation silently drifts. The schema constants in the validator should be the executable truth; the spec doc describes the same values.

2. **`content_type` detection logic drift**: if path-based inference is used, renaming a directory (e.g., moving `tickets/inprogress/` to a new location) silently breaks type detection without any test failure. The inference rules must be tested explicitly.

3. **Conditional field rules not tested**: the `last_verified` conditional (required when `status == authoritative`) is easy to omit from test coverage. A test with `status: authoritative` and no `last_verified` must be included.

4. **Archive `status` constraint not tested**: archive files must have `status: archive`. A test with an archive-path file carrying `status: active` must fail validation.

5. **Exit code contract**: CI relies on exit code 1 for failures. Any exception that causes an unhandled `sys.exit(0)` or silent swallow will break CI silently. The validator must have a top-level exception handler that converts unexpected errors to exit 1.
