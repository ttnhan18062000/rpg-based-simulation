---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260706-MONITORING-REASON-CODE
artifact_type: test_plan
tags: [agent-monitoring, tagging, reporting]
---

# Test Plan — TCK-20260706-MONITORING-REASON-CODE

## Unit tests — `tests/tools/test_done_checker_static.py` (new test class)

- `test_classify_checklist_failure_all_pass_returns_none` — checklist of all `PASS`/`NA` → `None`.
- `test_classify_checklist_failure_tag_registry_rejection` — one `FAIL` entry whose `evidence`
  contains `"is not in the tag registry"` → `"tag_registry_rejection"`.
- `test_classify_checklist_failure_generic_dod_failure` — one `FAIL` entry with unrelated evidence
  (e.g. missing test coverage) → `"dod_condition_failed"`.
- `test_classify_checklist_failure_scans_past_leading_pass_entries` — `PASS`, `PASS`, then a `FAIL`
  with the tag-registry substring → still `"tag_registry_rejection"` (confirms it's not
  hardcoded to index 0).
- `test_classify_checklist_failure_returns_first_fail_when_multiple` — two `FAIL` entries, first
  generic, second tag-registry — returns the *first* FAIL's classification
  (`"dod_condition_failed"`), documenting the "first FAIL wins" tie-break explicitly rather than
  leaving it ambiguous.

## Regression suites

```bash
pytest tests/tools/test_done_checker_static.py tests/tools/test_done_checker_audit.py -v
pytest tests/tools/ -q --ignore=tests/tools/test_knowledge_search.py
```
Must show zero new failures beyond the 2 pre-existing, unrelated `test_search_mcp.py` failures
already disclosed in this session's earlier tickets.

## Non-pytest verification

- Read-through of the edited `.claude/workflows/implement-ticket.js` section — no JS test harness
  exists in this repo for workflow scripts; this is disclosed as a limitation, not hidden.
- `docs/agent-monitoring/schema.md` reviewed for accuracy against the actual code (field name,
  nullability, the exact 2 known values).
- Manually invoke `generate_retro.py` against the live `agent-monitoring/` data to confirm it still
  runs cleanly with the new (currently-empty, since no real run has hit this code path yet)
  aggregation logic present — must not error on the absence of any `reason_code` values.

## Acceptance-criteria-to-check mapping

- "classify_checklist_failure exists, tested" → the 5 unit tests above.
- "tag-registry DOD_BLOCKED run produces reason_code" → covered by unit test +
  code-path read-through (cannot run the live workflow end-to-end on itself, per the
  Assumptions/Open Questions note in investigation.md).
- "every other phase's events unaffected" → confirmed by inspection: `pushEvent`'s new parameter
  is optional/defaults to `null`, and no other call site is edited.
- "schema doc updated" → manual doc review.
- "retro shows reason-code breakdown" → manual `generate_retro.py` invocation.
