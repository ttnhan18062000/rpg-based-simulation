---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCHEMA
artifact_type: plan
tags: [docsite, schema]
---

# Plan — TCK-20260606-DOCSITE-SCHEMA

Ticket: Define frontmatter schema for all documentation content types
Date: 2026-06-11

---

## Resolved Open Questions

All open questions are resolved. No unresolved items remain.

1. **Layer enum** — expanded to 19 values covering all docs/ subdirectories:
   `mechanics`, `engine`, `testing`, `simulation`, `ai`, `architecture`, `core`, `ticket`, `artifact`, `guidelines`, `observability`, `performance`, `combat`, `compliance`, `strategy`, `systems`, `economy`, `world`, `misc`

2. **Content type detection** — path inference is the default; explicit `content_type` field in frontmatter overrides when present. Path rules:
   - `tickets/` prefix → `ticket`
   - `stored_artifacts/` prefix → `artifact`
   - `docs/archive/` prefix → `archive`
   - all other `docs/` paths → `doc`
   - anything else → `doc` (fallback)

3. **PyYAML** — NOT present in `requirements.txt`. Use a stdlib-only minimal frontmatter parser: extract the `---` block with regex, then parse simple `key: value` and `key: [list]` patterns inline. This avoids adding a dependency and is sufficient for the flat YAML frontmatter structure in scope. No external parser needed.

4. **CI integration** — validator is manual-only for this ticket. No CI hook, no pre-commit integration, no GitHub Actions changes.

---

## Dependency Map

```
Step 1 (schema constants in validator)
    └─► Step 2 (validator logic — depends on constants)
        └─► Step 4 (test file — imports constants and logic)
Step 3 (schema spec doc)
    └─► independent of Steps 1/2/4, but should match Step 1 constants exactly
Step 5 (regression run)
    └─► depends on Step 4 complete
Step 6 (finalize ticket + artifacts)
    └─► depends on Steps 1–5 all complete
```

Steps 1 and 3 can be worked in parallel. Step 3 has no code dependency.

---

## Ordered Implementation Steps

### Step 1 — Write `tools/validate_frontmatter.py` (schema constants + parser only)

**What:** Create the validator script with all enum constants and the frontmatter extraction/parsing logic, but leave `main()` as a stub (raises `NotImplementedError`). This establishes the single source of truth for all enum values before any test is written.

**Files changed:**
- `tools/validate_frontmatter.py` — CREATE

**Enum constants to define (module-level, importable):**
```python
STATUS_VALUES      = {"authoritative", "active", "historical", "archive"}
LAYER_VALUES       = {"mechanics", "engine", "testing", "simulation", "ai",
                      "architecture", "core", "ticket", "artifact", "guidelines",
                      "observability", "performance", "combat", "compliance",
                      "strategy", "systems", "economy", "world", "misc"}
AUTHORITY_VALUES   = {"P0", "P1", "P2"}
AUDIENCE_VALUES    = {"developer", "agent", "designer", "historical"}
PHASE_VALUES       = {"open", "inprogress", "blocked", "done"}
ARTIFACT_TYPE_VALUES = {"investigation", "plan", "test_plan"}
```

**Parser functions to define:**
- `extract_frontmatter(text: str) -> dict | None` — returns parsed dict if `---` block is present at file start, `None` if absent, raises `ValueError` on malformed YAML.
- `detect_content_type(path: Path) -> str` — path inference returning `"doc"`, `"ticket"`, `"artifact"`, or `"archive"`.

**Scope guard:** Do NOT implement `validate_file()`, `validate_directory()`, or `main()` in this step. Only constants and pure parsing/detection functions.

**Verifiable:** `python3 -c "from tools.validate_frontmatter import STATUS_VALUES, LAYER_VALUES, AUTHORITY_VALUES, AUDIENCE_VALUES, PHASE_VALUES, ARTIFACT_TYPE_VALUES; print('OK')"` succeeds.

---

### Step 2 — Complete `tools/validate_frontmatter.py` (validation logic + CLI)

**What:** Implement the full validation and CLI on top of Step 1 constants and parser.

**Files changed:**
- `tools/validate_frontmatter.py` — EDIT (replace `NotImplementedError` stub with full implementation)

**Functions to implement:**
- `validate_file(path: Path) -> list[str]` — returns list of error strings (empty = pass). Calls `extract_frontmatter`, `detect_content_type`, applies schema rules per content type, collects all errors.
- `validate_directory(path: Path) -> dict[Path, list[str]]` — recursively finds `.md` files, calls `validate_file` for each, returns path→errors map.
- `main()` — argparse single positional arg (`path`), dispatch to file or directory, print errors to `stderr`, summary to `stdout`, exit 0/1.

**Schema rules per content type:**

| Content type | Required fields | Enum constraints | Conditional rules |
|---|---|---|---|
| `doc` | `status`, `layer`, `authority`, `audience` | all four fields enum-checked | `last_verified` required when `status == "authoritative"` |
| `ticket` | `status`, `layer`, `authority`, `audience`, `ticket_id`, `phase`, `date` | `status`, `layer`, `authority`, `audience`, `phase` enum-checked | none |
| `artifact` | `status`, `layer`, `authority`, `audience`, `ticket_id`, `artifact_type` | `status`, `layer`, `authority`, `audience`, `artifact_type` enum-checked | none |
| `archive` | `status`, `layer`, `original_date` | `status` constrained to `"archive"` only; `layer` enum-checked | none |

**Error message format:** `"{filepath}: {field}: {reason}"` — e.g. `"docs/foo.md: status: missing required field"` or `"docs/foo.md: layer: invalid value 'unknown_layer' (valid: ...)"`.

**Top-level exception handler in `main()`:** Any unhandled exception prints to `stderr` and exits 1 (never silently swallows).

**Scope guard:** Do NOT modify any existing file in `tools/`. Do NOT add PyYAML to `requirements.txt`. Do NOT wire into CI or pre-commit hooks.

**Verifiable:** `python3 tools/validate_frontmatter.py --help` prints usage. `echo $?` returns 0.

---

### Step 3 — Write `docs/guidelines/frontmatter_schema.md`

**What:** Create the human-readable schema specification document. This is pure documentation — no code, no imports. It must document exactly the same enum values as the constants in Step 1.

**Files changed:**
- `docs/guidelines/frontmatter_schema.md` — CREATE

**Required sections:**
1. Overview — purpose, scope, what files are covered
2. Content type detection — path inference rules (same rules as `detect_content_type`)
3. Schema per content type — one table per type with field name, required/optional, type, valid values
4. Conditional rules — `last_verified` rule for authoritative docs, archive `status` constraint
5. Enum reference — single canonical list of all enum values (STATUS, LAYER, AUTHORITY, AUDIENCE, PHASE, ARTIFACT_TYPE)
6. Validator usage — how to run `tools/validate_frontmatter.py` on a file or directory
7. Extension guide — how to add a new layer value (update validator constants + spec doc + enum assertion tests in same commit)

**Scope guard:** Do NOT modify `docs/guidelines/README.md` unless it already has a table-of-contents section that would become inconsistent. Do NOT apply frontmatter to any existing file (that is Tickets 3–5).

**Verifiable:** File exists at `docs/guidelines/frontmatter_schema.md`. All enum values in the spec exactly match the constants in `tools/validate_frontmatter.py`.

---

### Step 4 — Write `tests/tools/test_validate_frontmatter.py`

**What:** Create the full test suite as specified in `test_plan.md`. Tests import the validator module directly for Groups 1–8, plus subprocess calls for Group 7.

**Files changed:**
- `tests/tools/test_validate_frontmatter.py` — CREATE

**Test groups (per test_plan.md):**
- Group 1: Frontmatter detection (4 tests)
- Group 2: Doc content type (14 tests)
- Group 3: Ticket content type (5 tests)
- Group 4: Artifact content type (6 tests)
- Group 5: Archive content type (4 tests)
- Group 6: Directory scan mode (5 tests)
- Group 7: Exit code contract via subprocess (3 tests)
- Group 8: Anti-drift enum assertions (6 tests)

**Total: 47 tests.**

**Test file structure:**
- Uses `tmp_path` pytest fixture for all file/directory creation — no real project files mutated.
- Imports `validate_frontmatter` module using `sys.path` insertion pointing to the repo root, to avoid requiring `tools/` to be a package (it is not a package; `tools/__init__.py` does not exist).
- Group 7 subprocess tests use `subprocess.run([sys.executable, str(validator_path), ...])` with `tmp_path` temp files.
- Group 8 tests assert exact set equality against the module-level constants.

**Scope guard:** Do NOT modify `tests/tools/__init__.py` (it already exists). Do NOT modify `tests/conftest.py` or any existing test file.

**Verifiable:** `pytest tests/tools/test_validate_frontmatter.py -v` runs 47 tests and all pass.

---

### Step 5 — Run scoped test suite

**What:** Execute the two required test commands from `test_plan.md` and confirm both pass.

**Commands:**
```bash
pytest tests/tools/test_validate_frontmatter.py -v
pytest tests/docs/ -v -m "not slow"
```

**Expected:**
- All 47 new tests pass.
- All existing `tests/docs/` tests pass (regression — none should be affected by this ticket).

**Files changed:** None (read-only verification step).

**Scope guard:** Do NOT run `pytest tests/` (full suite is out of scope).

**Verifiable:** Both commands exit 0 with no failures or errors.

---

### Step 6 — Finalize ticket and close out

**What:** Update the ticket, append working log entry, move staging artifacts to `stored_artifacts/`, write agent monitoring records.

**Files changed:**
- `tickets/inprogress/TCK-20260606-DOCSITE-SCHEMA.md` — EDIT (fill Implementation Notes, Test Summary, Files Changed, Completion Summary; set Status: DONE)
- Move to `tickets/done/TCK-20260606-DOCSITE-SCHEMA.md`
- `tickets/working_log.csv` — APPEND one row at bottom
- `stored_artifacts/TCK-20260606-DOCSITE-SCHEMA/` — MOVE from `staging_artifacts/TCK-20260606-DOCSITE-SCHEMA/` (plan.md, investigation.md, test_plan.md)
- `agent-monitoring/runs.jsonl` — APPEND run entry
- `agent-monitoring/events.jsonl` — APPEND at least one event entry

**Scope guard:** Do NOT clean `data/runs/` or `reports/release_proof/` (those directories may not exist for a pure tooling ticket — skip if absent). Do NOT modify any other docs or tickets.

**Verifiable:** `tickets/done/TCK-20260606-DOCSITE-SCHEMA.md` exists with Status: DONE. `staging_artifacts/TCK-20260606-DOCSITE-SCHEMA/` is gone. `stored_artifacts/TCK-20260606-DOCSITE-SCHEMA/` contains all three artifacts. Working log has the new row at bottom.

---

## Acceptance Criteria Mapped to Steps

| Acceptance Criterion | Covered by Step(s) |
|---|---|
| Schema spec exists at `docs/guidelines/frontmatter_schema.md` with field defs and valid values for all four content types | Step 3 |
| Required vs optional fields clearly distinguished per content type | Steps 2, 3 |
| `tools/validate_frontmatter.py` can run on a single file or directory and reports missing/invalid fields | Step 2 |
| Schema covers doc fields: `status`, `layer`, `authority`, `audience`, `tags`, `last_verified` | Steps 1, 2, 3 |
| Schema covers ticket-specific fields: `ticket_id`, `phase`, `date` | Steps 1, 2, 3 |
| Schema covers artifact-specific fields: `ticket_id`, `artifact_type` (investigation/plan/test_plan) | Steps 1, 2, 3 |
| Schema covers archive minimal fields: `status: archive`, `layer`, `original_date` | Steps 1, 2, 3 |
| Validator exits non-zero on schema violation (CI-safe) | Steps 2, 4 (Group 7) |

---

## Scope Guards Summary

The following are explicitly out of scope and must NOT be touched:

- Any existing `.md` file in `docs/`, `tickets/`, or `stored_artifacts/` (no frontmatter applied)
- `requirements.txt` — no new dependencies
- `.github/workflows/` — no CI integration
- `.pre-commit-config.yaml` — no hook wiring
- `tests/docs/test_doc_integrity.py` — must not be modified
- `tests/conftest.py` — must not be modified
- `docs/guidelines/README.md` — only update if it already has a table of contents that would be broken by omission
- Any file under `src/` — pure tooling work
- Docusaurus configuration (Ticket 2 scope)
- Registry generation (Ticket 6 scope)
