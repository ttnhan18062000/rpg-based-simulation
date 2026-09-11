---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT
artifact_type: test_plan
tags: [process-improvement]
---

# Test Plan — TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT

## Step 1 — cross-field rule (fixture-based, `tmp_path`)

- `tickets/done/` + `historical`/`done` → passes.
- `tickets/done/` + `active`/`open` → fails (the valid-but-inconsistent class; the enum check alone passes it).
- `tickets/done/` + `active`/`done` → fails.
- `tickets/done/` + `done`/`done` → fails (invalid status, still caught).
- `tickets/inprogress/` + `phase: done` → fails.
- `tickets/inprogress/` + `active`/`inprogress` → passes.
- `done_checker_static.check_frontmatter_valid()` returns FAIL for a closing ticket with `active`/`open`.

## Step 2 — `epic_scoped`

Under the recommended option: the 9 epics end at `historical`/`done`, their body `## Status` unchanged.
Under the alternative, a test asserting `epic_scoped` is in `PHASE_VALUES`.

## Step 3 — remediation integrity

- Before-count recorded; after-count of non-canonical files is 0.
- For every changed file: body hash (everything after the closing `---`) is identical before and after.
- For every changed file: the diff touches only the `status:` and `phase:` lines.
- The script's dry-run output matches the file set it then changes.

## Step 4 — corpus enforcement

- The new test runs the rule over every real `tickets/done/**/*.md` and passes after Step 3.
- It fails if any single file is reverted to `active`/`open` — proves it can catch a regression, not only
  pass on clean data.
- Runtime stays small (YAML parsing only).

## Step 5 — epic close instruction

A static test asserting `implement-epic.js`'s epic-close step contains the `status: historical` /
`phase: done` instruction, following the repo's existing raw-source-text tests of workflow prompts. Also
assert `implement-ticket.js` still contains its existing line-1671 instruction, so it can't be
silently removed.

## Step 6 — parity

INFRA-180, INFRA-278 and INFRA-305 are rewritten through `write_entry()` and pass `validate_entry()`.
INFRA-305's line references match `check_frontmatter_valid()`'s real location after Step 1.

## Regression

```
pytest tests/tools/test_validate_frontmatter.py tests/tools/test_done_checker_static.py \
       tests/tools/test_add_frontmatter_tickets.py -q
```

Plus the new corpus test, and `python3 tools/validate_frontmatter.py` over `tickets/done/`.
