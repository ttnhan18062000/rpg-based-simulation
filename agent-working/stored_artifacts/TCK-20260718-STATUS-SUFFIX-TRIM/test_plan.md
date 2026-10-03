---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATUS-SUFFIX-TRIM
artifact_type: test_plan
tags: [data-quality, observability]
---

# Test Plan — TCK-20260718-STATUS-SUFFIX-TRIM

## Regression Surface

This ticket's primary change is markdown body-text edits to 10 `tickets/done/*.md` files — there is
no `src/` behavior change under the "defer" path. Regression surface is entirely about the tooling
that *reads* those files, plus (conditionally) the checker itself if the go/defer decision is
"extend now."

**Unit / tool tests (must keep passing regardless of go/defer):**
- `tests/tools/test_status_drift_check.py` — full 11-test module (`test_clean_corpus_passes`,
  `test_stale_ticket_status_flagged`, `test_epic_tier_exception_ignored_by_value`,
  `test_legacy_naming_file_ignored_by_pattern`, `test_same_line_colon_status_format_not_newly_flagged`,
  `test_lowercase_final_status_flagged`, `test_legacy_runs_jsonl_shape_ignored`,
  `test_runs_jsonl_clean_uppercase_passes`, `test_check_status_drift_aggregates_both_scans`,
  `test_check_is_read_only`, `test_marker_json_output_contract`,
  `test_exit_code_nonzero_on_any_fail_zero_on_clean`, `test_regex_matches_baseline_scan_pattern`).
  All use `tmp_path` fixtures, not the live 10 files, so this ticket's data edits cannot break them
  under "defer." Under "extend now," `test_regex_matches_baseline_scan_pattern` and/or the check
  function's behavior contract will need deliberate updates (see New Tests Required) — not a
  silent regression, a scoped design change.
- `tests/tools/test_generate_registry.py` (if it exists — confirm at Implement time; not
  independently verified to exist in this investigation pass) — covers `parse_body_section`, whose
  contract (capture everything to next `## ` heading) is explicitly unchanged by this ticket
  (Out of Scope: "Modifying ... `tools/generate_registry.py`'s `parse_body_section()`"). This
  ticket's data edits change *what* `parse_body_section` returns for these 10 files (now `"DONE"`
  instead of the fragmented strings) but not the function's behavior — any existing test asserting
  specific fixture content is unaffected since it does not read these 10 live files.
- `tests/tools/test_validate_frontmatter.py` — frontmatter on all 10 files is explicitly untouched
  by this ticket (AC: "no frontmatter field of any of the 10 files modified"), so this suite's
  results must be identical before/after.

**Integration:**
- No integration test currently exercises `src/api/agent_ops_dashboard/ingest.py::parse_ticket_file`
  against the live `tickets/done/` corpus by file content assertion (confirmed: the dashboard
  contract doc describes only fixture/unit-level testing patterns for `ingest.py`, and no test file
  under `tests/` was found asserting exact `workflow_status` string values for named files in this
  investigation's read scope). If such a test exists and asserts one of these 10 files' *old*
  fragmented `workflow_status` string, it would need updating — this must be checked at Implement
  time via `grep -rn "workflow_status" tests/` before considering the change complete, since this
  investigation did not exhaustively enumerate every test file.

**Arena-combat:** Not applicable — no combat-domain code or content is touched by this ticket.

## New Tests Required

Per the ticket's Acceptance Criteria, mapped one-to-one:

1. **Data-correctness verification (not a new pytest test — a verification script/one-liner)**
   - Category: verification script (matches predecessor's `derive_status_drift_scope.py` pattern —
     a one-off, not committed to `tests/`)
   - Verifies: `tools/generate_registry.py`'s `parse_body_section(body, 'Status')`, run against each
     of the 10 post-fix files, returns exactly `"DONE"` (AC3).
   - Where it lives: `staging_artifacts/TCK-20260718-STATUS-SUFFIX-TRIM/scripts/verify_status_trim.py`
     (one-off, mirrors predecessor's `scripts/` staging convention) — not a permanent `tests/`
     addition, since this is a one-time data-fix verification, not an ongoing regression concern
     (the ongoing concern is covered by item 2 below via the existing/extended checker).

2. **Regex exact-match verification (script or manual, per AC1's literal regex)**
   - Category: verification script
   - Verifies: `^## Status\s*\n+\s*DONE\s*\n` matches immediately followed by the next `## ` heading
     or EOF, with no other non-whitespace text in between, for all 10 files (AC1).
   - Where it lives: same `verify_status_trim.py` script as item 1, or inline in the same check.

3. **`git diff --stat` scope guard (manual, run at Implement/Verify time — not a pytest test)**
   - Category: manual verification command
   - Verifies: exactly the 10 named files changed, no unrelated file touched, no frontmatter field
     modified (AC5). Command: `git diff --stat tickets/done/` plus a frontmatter-only diff check
     (`git diff tickets/done/<file>.md | grep -A5 '^---$'` per file, confirming the frontmatter
     block's diff hunk is empty).

4. **IF "extend now" is chosen** — new pytest coverage in
   `tests/tools/test_status_drift_check.py` for the new "first-token-DONE-but-trailing-prose-follows"
   class:
   - `test_trailing_prose_after_done_flagged` — unit — a fixture with `## Status\nDONE (SOME NOTE)\n`
     is flagged `FAIL` by the extended check. Verifies the new detection logic actually catches the
     defect class this ticket was created to fix, not just that it runs.
   - `test_clean_done_with_no_trailing_prose_still_passes` — unit — a fixture with plain `## Status\nDONE\n`
     (no trailing text) continues to pass, confirming the extension does not regress the existing
     "true DONE" happy path.
   - `test_epic_tier_trailing_prose_not_conflated_with_generic_drift` — unit — confirms
     `DONE (EPIC_SCOPED)`-shaped values (the pre-existing, legitimate epic-tier exemption pattern
     already tested by `test_epic_tier_exception_ignored_by_value`) are not double-flagged or
     reclassified by the new trailing-prose logic if the extension's design keeps `EPIC_SCOPED`
     tail-text as a distinct exemption rather than uniformly flagging any tail text. This test's
     exact assertion depends on the extension's chosen design (flag all trailing prose
     unconditionally vs. exempt known epic-tier patterns) — write it to match whatever design
     Implement actually picks, not a pre-decided shape.
   - `test_regex_matches_baseline_scan_pattern` (existing, `tests/tools/test_status_drift_check.py:213-215`)
     — must be deliberately updated (not silently left stale) if the extension changes
     `TICKET_STATUS_RE` itself, or left as-is with a second, additive regex/check function if the
     extension instead adds a new function without touching `TICKET_STATUS_RE`. Either way this is a
     required, explicit decision point at Implement time — flagged here so it is not accidentally
     skipped.
   - Where they live: `tests/tools/test_status_drift_check.py` (existing file, append new test
     functions following its established `tmp_path`-fixture shape).
   - If "defer": none of the above are written in this ticket; the recommendation is recorded in the
     ticket's Implementation Notes per the ticket's own Scope instruction, and
     `tests/tools/test_status_drift_check.py` is left completely untouched.

## Scoped Pytest Commands

```
pytest tests/tools/test_status_drift_check.py -v
```

If a `tests/tools/test_generate_registry.py` file exists (confirm at Implement time):
```
pytest tests/tools/test_generate_registry.py -v
```

Frontmatter regression guard (confirms the 10 files' untouched frontmatter still validates cleanly):
```
pytest tests/tools/test_validate_frontmatter.py -v
```

Combined scoped run for this ticket's full regression surface:
```
pytest tests/tools/test_status_drift_check.py tests/tools/test_validate_frontmatter.py -v
```

Never: `pytest tests/` (repo-wide) — out of scope per project Testing Rule; this ticket's change
surface is entirely within `tools/` tests plus (conditionally) `tickets/done/*.md` data, neither of
which requires the full suite to validate.

## Anti-Drift Test Guards

- **`test_check_is_read_only`** (existing, `tests/tools/test_status_drift_check.py:142-158`) —
  already guards that `check_status_drift()` never mutates the files it scans (byte-identical
  content + mtime before/after). This is directly relevant anti-drift coverage for this ticket: it
  proves the checker itself cannot be the mechanism that accidentally corrupts one of the 10 target
  files during verification runs.
- **`test_regex_matches_baseline_scan_pattern`** (existing) — guards that
  `TICKET_STATUS_RE` stays byte-identical to the approved baseline unless a deliberate "extend now"
  decision changes it. Under "defer," this test's continued pass is itself an anti-drift signal that
  this ticket did not silently touch `status_drift_check.py`'s matching logic — a stronger guard
  than relying on `git diff --stat` alone, since it fails loudly inside the test suite rather than
  only being caught by manual diff inspection.
- **`test_same_line_colon_status_format_not_newly_flagged`** (existing) — guards the predecessor's
  own excluded 6-colon-suffixed-file scope is not newly disturbed. Relevant here because this
  ticket's 10 files are a *disjoint* set from those 6 (confirmed in investigation.md) — this test
  passing continues to confirm that disjointness holds at the tooling level, not just by manual
  filename comparison.
- **New guard needed (write in this ticket, applies under both go and defer):** a lightweight
  verification (script, per New Tests Required item 1) asserting `parse_body_section` returns
  exactly `"DONE"` for all 10 named files post-fix — this is the guard that would catch a scope-creep
  or incomplete-rewording mistake (e.g. a leftover trailing space, an accidentally-reinserted
  parenthetical, or a file missed in the batch edit) that `status_drift_check.py`'s own
  first-token-only regex is structurally incapable of catching either before or after this ticket,
  regardless of the go/defer outcome.
- **Frontmatter-untouched guard:** `git diff tickets/done/<each-of-10>.md` inspected per-file at
  Verify time to confirm the diff hunk never includes the `---...---` frontmatter block — this is
  the guard against the specific scope-creep risk of an editor tool normalizing YAML frontmatter
  formatting (e.g. reordering keys, changing quote style) as an unintended side effect of editing
  the body below it.
- **10-file-exact-scope guard:** `git diff --stat tickets/done/ | wc -l` (or equivalent) checked
  against exactly 10 at Verify time — catches both under-scope (a file missed) and over-scope (an
  extra file accidentally touched, e.g. from a global find-replace run too broadly) mistakes in one
  check.
