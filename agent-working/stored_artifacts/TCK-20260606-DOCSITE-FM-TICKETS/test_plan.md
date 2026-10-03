# Test Plan — TCK-20260606-DOCSITE-FM-TICKETS

Ticket: Apply frontmatter to tickets and stored artifacts; update ticket format for new tickets
Date: 2026-06-11

---

## Regression Surface

Existing tests that must keep passing:

| File | What it covers |
|---|---|
| `tests/tools/test_validate_frontmatter.py` | Validator correctness, enum values, schema by content type |
| `tests/tools/test_add_frontmatter_archive.py` (if exists) | Archive frontmatter script idempotency |

Run before and after to confirm no regressions:
```bash
pytest tests/tools/ -v
```

---

## New Tests Required

### 1. test_add_frontmatter_tickets_idempotent
- **Category**: unit
- **What it verifies**: Running `tools/add_frontmatter_tickets.py` twice on the same file does not double-prepend frontmatter; file content is identical after second run.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 2. test_add_frontmatter_tickets_standard_tck
- **Category**: unit
- **What it verifies**: Standard TCK ticket (e.g. `TCK-20260606-DOCSITE-FM-TICKETS.md`) gets correct `ticket_id`, `date` (2026-06-06), `phase: done`, `status: historical`, `authority: P1`, `audience: agent`. Layer inferred non-misc.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 3. test_add_frontmatter_tickets_legacy_filename
- **Category**: unit
- **What it verifies**: Non-TCK filename (e.g. `METRICS-01.md`) gets `date: unknown`, `ticket_id: METRICS-01`. Script does not crash.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 4. test_add_frontmatter_tickets_artifact_plan
- **Category**: unit
- **What it verifies**: `stored_artifacts/TCK-YYYYMMDD-XYZ/plan.md` gets `artifact_type: plan`, `ticket_id: TCK-YYYYMMDD-XYZ`, `status: historical`, `authority: P2`, `audience: agent`.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 5. test_add_frontmatter_tickets_artifact_investigation
- **Category**: unit
- **What it verifies**: `stored_artifacts/.../investigation.md` gets `artifact_type: investigation`.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 6. test_add_frontmatter_tickets_artifact_test_plan
- **Category**: unit
- **What it verifies**: `stored_artifacts/.../test_plan.md` gets `artifact_type: test_plan`.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 7. test_add_frontmatter_tickets_artifact_non_standard_skipped
- **Category**: unit
- **What it verifies**: Non-standard artifact filenames (e.g. `guide.md`, `implementation_plan.md`) under `stored_artifacts/` are skipped — not modified.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 8. test_add_frontmatter_tickets_inprogress_not_touched
- **Category**: architecture guard
- **What it verifies**: Script does not walk or modify any files under `tickets/inprogress/`.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 9. test_add_frontmatter_tickets_layer_inference
- **Category**: unit
- **What it verifies**: Layer keyword mapping produces correct LAYER_VALUES enum entries (spot-check: DOCSITE → guidelines, PHASE22 → engine, COMBAT → combat). No invalid enum values are emitted.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 10. test_validate_frontmatter_accepts_output
- **Category**: integration
- **What it verifies**: After running `add_frontmatter_tickets.py` on a temp directory containing sample ticket and artifact files, `validate_frontmatter.py` exits with code 0 for all modified files.
- **Where**: `tests/tools/test_add_frontmatter_tickets.py`

### 11. test_ticket_scoper_template_has_frontmatter (manual/review)
- **Category**: review
- **What it verifies**: The `.claude/agents/ticket-scoper.md` ticket template section contains a frontmatter YAML block before `# TCK-YYYYMMDD-SHORT-SCOPE`.
- **How**: Read the file and assert `---` appears before the `# TCK` line in the template.
- **Where**: Can be a simple grep/read check in the done-checker run.

### 12. test_done_checker_has_frontmatter_condition (manual/review)
- **Category**: review
- **What it verifies**: `.claude/agents/done-checker.md` contains a condition numbered 12 that references frontmatter and `validate_frontmatter.py`.
- **How**: Read the file and confirm the condition text.

---

## Scoped Pytest Commands

Primary test run:
```bash
pytest tests/tools/test_add_frontmatter_tickets.py -v
```

Regression run (existing tools tests):
```bash
pytest tests/tools/ -v
```

Do NOT run:
```bash
pytest tests/   # full suite — too broad for this change
```

---

## Anti-Drift Test Guards

- `test_add_frontmatter_tickets_inprogress_not_touched` — guards the explicit out-of-scope requirement.
- `test_add_frontmatter_tickets_idempotent` — prevents double-frontmatter corruption on re-runs.
- `test_add_frontmatter_tickets_layer_inference` — guards against invalid enum values being written to disk; validator would catch these at validation time but the unit test catches them at generation time.
- `test_validate_frontmatter_accepts_output` — closes the loop end-to-end: generated frontmatter must pass the validator, not just be syntactically present.
