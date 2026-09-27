---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES
date: 2026-09-24
tags: [delivery, documentation, claude-md]
---

# Test Plan — TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES

## New: `tests/tools/test_delivery_templates.py`
- `test_pr_template_exists_and_has_no_attribution_trailer_in_its_body` (AC4)
- `test_pr_template_sections_match_plan_order` (AC4/AC5)
- `test_pr_template_spec_exists_and_is_valid_json` (AC5)
- `test_pr_template_spec_marks_review_notes_as_the_only_hand_written_section` (AC5)
- `test_pr_template_spec_section_order_matches_the_actual_template` (AC5 — cross-check the spec
  against the real template so they cannot silently diverge)
- `test_gitmessage_exists_and_is_comment_only` (AC3 — regression guard against ever shipping the
  placeholder text as a literal default subject)
- `test_gitmessage_documents_the_full_contract_shape` (AC3)

## Retargeted (file path only, assertions unchanged): `tests/docs/test_ci_triage_absent_run_branch.py`,
`tests/docs/test_ci_per_directory_steps_documented.py`
All 11 pre-existing assertions across both files re-run against `docs/guides/delivery_process.md`
instead of `CLAUDE.md` — same section-header slicing, same content checks.

## Citation-preservation check (AC2)
Not a pytest test (a one-off verification script, run and recorded in investigation.md): extract
`TCK-[0-9]{8}-[A-Z0-9-]+` from the four removed `CLAUDE.md` regions, extract the same pattern from
the new guide, assert the first set is a subset of the second. Recommend a future ticket promote
this into a real regression test if the guide is edited again without re-verification in mind — out
of scope here (this ticket's own Out of Scope forbids adding new blocking/gate machinery).

## Full regression check
Every file `grep -rl "CLAUDE\.md" tests/` found (14 files) run together in one `pytest` invocation,
plus `tests/docs/` in full and the two new delivery test files, to confirm the CLAUDE.md/roadmap.md
edits and the new guide don't regress anything already passing.

## Recorded in ticket's `## Test Summary` once run
- Exact `pytest` command(s) invoked.
- Pass/fail/skip/xfail counts.
