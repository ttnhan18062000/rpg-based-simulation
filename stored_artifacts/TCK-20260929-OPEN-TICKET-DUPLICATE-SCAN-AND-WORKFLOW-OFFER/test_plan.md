---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER
artifact_type: test_plan
tags: [process-improvement, workflows, create-tickets, ticket-scoper]
---

# Test Plan — TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER

New file: `tests/tools/test_open_ticket_overlap.py`, mirroring `tests/tools/test_epic_folder_status.py`'s
fixture-directory-per-test style (`tmp_path` with real `tickets/todos/`/`tickets/inprogress/`
shaped subtrees, no mocking of the parser).

## AC1 — real missed pair, via fixture

- `test_finds_overlap_with_real_target_ticket_via_fixture`: copies the real
  `tickets/todos/TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED.md` content into a
  `tmp_path/tickets/todos/`, plus the new `tests/fixtures/open_ticket_overlap/
  B0-PERCEPTION-UPDATE-WAVE-FIXTURE.md` fixture (cited source: investigation.md). Runs the scanner
  against the fixture ticket's own title/summary/code-areas. Asserts
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` is in the result, with at least one
  matched code area.

## AC2 — negative controls

- `test_unrelated_ticket_gets_no_hits`: a control ticket with an unrelated title/summary/code-area
  (e.g. combat/economy domain) alongside the two perception tickets above — result excludes it.
- `test_ticket_never_matches_itself`: querying with a ticket's own `ticket_id` set excludes any
  candidate file whose frontmatter `ticket_id` equals it, even if title/code-areas are identical
  (self-citation via `--ticket-path` naturally can't self-match since the scan root won't contain
  a copy of itself in a real run, but this proves the exclusion is enforced by ID, not by
  incidental path difference alone — seed a candidate file with the SAME ticket_id as the query
  and confirm it's excluded).

## AC3 — no index/staleness dependency

- `test_sees_a_ticket_created_during_the_test`: writes a brand-new `tickets/todos/TCK-*.md` file
  inside the test's own `tmp_path` (created within the test function, never touching any real
  index or cache), then immediately queries against it and confirms it's found — proves the
  `rglob` live-disk-read design, not an index.

## Signal-isolation tests (supporting AC1/AC2, not separately numbered in the ticket)

- `test_code_area_signal_alone_triggers_a_hit`: two tickets sharing one exact code-area path, no
  shared distinctive terms in title/summary — still a hit.
- `test_term_overlap_signal_alone_triggers_a_hit`: two tickets sharing >= 2 distinctive terms,
  disjoint code areas — still a hit.
- `test_single_shared_term_is_not_enough`: exactly one shared distinctive term, disjoint code
  areas — no hit (proves the >= 2 threshold is real, not `>= 1`).

## AC4 — wiring, prompt-text pin tests

- `tests/tools/test_concern_investigator_open_ticket_scanner_pin.py`: anchor-substring pin
  (mirroring `test_finalize_working_log_uses_helper_pin.py`'s pattern) on
  `.claude/agents/concern-investigator.md`'s Step 3 section — asserts
  `open_ticket_overlap.py` appears there, and that the surrounding text still frames it as
  informational (not `conflicts`/blocking language) in that same section.
- `tests/tools/test_implement_ticket_open_ticket_scanner_pin.py`: two pins against
  `.claude/workflows/implement-ticket.js`'s raw source text —
  (a) the new-ticket Scope prompt's Step 1 sentence includes `tickets/todos/` and
  `open_ticket_overlap.py`;
  (b) the existing-ticket Scope prompt includes `open_ticket_overlap.py` positioned before the
  `related_context=` output-field line, and the `conflicts=` line is byte-unchanged from its
  pre-ticket form (proves the wiring didn't accidentally touch `conflicts`).

## AC5 / AC5b — doc + CLAUDE.md gate

- `test_ticket_lifecycle_doc_has_the_offer_rule`: `docs/ai/ticket-lifecycle.md` contains language
  matching the offer-not-invoke rule near its existing line ~632 anchor.
- No automated test for the CLAUDE.md line itself (it's a single confirmed sentence in a project
  policy file, not code) — verified manually: the literal committed text matches exactly what the
  user confirmed via `AskUserQuestion`, pinned in Implementation Notes instead.

## AC6 — no regression

- Run existing suites unchanged: `tests/tools/test_epic_folder_status.py` (style precedent,
  unaffected), any existing `concern-investigator`/`implement-ticket.js` pin test files (find via
  `grep -rl "concern-investigator\|implement-ticket.js" tests/tools/` first), and
  `tests/tools/test_finalize_working_log_uses_helper_pin.py`/
  `test_finalize_phase_status_instruction_pin.py` (same file family, confirms the anchor-pin
  pattern itself hasn't broken).
