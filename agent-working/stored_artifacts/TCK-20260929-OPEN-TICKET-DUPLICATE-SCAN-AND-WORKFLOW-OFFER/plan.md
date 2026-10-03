---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER
artifact_type: plan
tags: [process-improvement, workflows, create-tickets, ticket-scoper]
---

# Plan — TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER

## Step 1 — `tools/open_ticket_overlap.py` (Scope item 1)

New module. Pure function `find_overlapping_open_tickets(query_title, query_summary,
query_code_areas, query_ticket_id, todos_root, inprogress_root) -> list[dict]`, thin `main()`
CLI wrapper (mirrors `tools/epic_folder_status.py`'s shape exactly).

- Candidate discovery: `todos_root.rglob("TCK-*.md")` (covers flat files and subfolder tickets
  alike) + `inprogress_root.rglob("TCK-*.md")`. Excludes any candidate whose frontmatter
  `ticket_id` equals `query_ticket_id`.
- Per candidate: `extract_frontmatter` for `ticket_id`, `_strip_frontmatter` +
  `parse_body_section(body, "Title")` / `"Request Summary"` / `"Related Code Areas"`, then
  `parse_related_code_areas()` on that last section's text — all four imported from
  `tools.generate_registry`, matching `epic_folder_status.py`'s own import shape.
- Signal (a) — code-area intersection: exact-string intersection between `query_code_areas` and
  the candidate's parsed path list.
- Signal (b) — term overlap: `_distinctive_terms(text)` — lowercase `\w+` tokens, length >= 5,
  minus a small stopword set — applied to `query_title + " " + query_summary` and to the
  candidate's own title + Request Summary; hit when the intersection size >= 2.
- A candidate is returned if EITHER signal fires (loose, per Assumptions: prefer false positives).
  Each result: `{ticket_id, path, matched_code_areas: [...], matched_terms: [...]}`.
- CLI: `--ticket-path PATH` (load title/summary/code-areas from a real ticket file, and use its
  own `ticket_id` as the exclusion) OR `--title TEXT --summary TEXT [--code-area PATH ...]
  [--ticket-id ID]` (the ID arg lets a not-yet-written ticket still exclude itself when checked
  under a placeholder id, though every real caller in this ticket's scope passes `--ticket-path`).
  `--todos-root`/`--inprogress-root` overrides for tests. Prints a JSON array, always exits 0.

## Step 2 — Wire into the 3 check sites (Scope item 2)

All three calls are advisory: JSON output only ever lands in a prompt's own `related_context`
(or `related_ticket`/informational field for concern-investigator), never `conflicts`/
`is_duplicate`.

1. `.claude/agents/concern-investigator.md` Step 3: add a paragraph immediately after the
   existing `grep -i "<keyword>" tickets/working_log.csv` instruction: run
   `python3 tools/open_ticket_overlap.py --title "<concern title>" --summary "<concern
   description>"` and fold hits into the same "up to 3 matching prior tickets" framing —
   `is_duplicate`/`related_ticket` outcome unchanged in kind, just a wider candidate pool.
2. `.claude/workflows/implement-ticket.js` Scope, new-ticket path, Step 1: append "and
   `tickets/todos/` via `python3 tools/open_ticket_overlap.py --title "..." --summary "..."`
   (its hits are informational, fold into the same related_context step below — never
   `conflicts`)" to the existing tickets/ scan sentence.
3. `.claude/workflows/implement-ticket.js` Scope, existing-ticket path: add one line before the
   `related_context=` output-field instruction directing the agent to run
   `python3 tools/open_ticket_overlap.py --ticket-path "${ticket_path}"` and fold any hits into
   `related_context`. `conflicts` computation is untouched (still only the ticket-not-found case).

No `create-tickets.js` schema change: `concern-investigator.md`'s existing `related_ticket`
output field already exists and already flows through unchanged (confirmed by reading
`create-tickets.js`'s own consumption of `concern-investigator`'s output before assuming a field
add was needed) — Related Code Areas item 3 in the ticket ("only if concern-investigator's schema
needs a field") turns out not to apply; recorded here rather than silently done.

## Step 3 — Offer-the-workflows rule (Scope item 3)

- `docs/ai/ticket-lifecycle.md`, next to line 632: add a short paragraph stating a session must
  offer (never auto-start) `/create-tickets` when about to turn a plan/proposal into several
  tickets, and `/implement-epic folder=…` when a `tickets/todos/<folder>/` is ready — the user
  decides each time.
- `CLAUDE.md`'s "Require explicit user opt-in" table: one line, the ticket's own proposed text
  (below). **Blocked on direct `AskUserQuestion` user confirmation of the literal text before any
  commit** — a peer's relay does not count, per this project's own standing rule and this
  session's own established practice earlier in this batch.

## Step 4 — CLAUDE.md PR Lifecycle pointer (Scope item 4, added 2026-09-29)

One line in CLAUDE.md's existing "PR Lifecycle" pointer paragraph, naming `pr_render.py` in the
arrow-list, per the ticket's own proposed text. Same confirmation gate as Step 3 — both lines
asked in one `AskUserQuestion` call. No content duplicated from `docs/guides/delivery_process.md`
(define-once).

## Step 5 — Tests (see test_plan.md)

## Step 6 — Retro / prompt-change cadence

This ticket edits two agent prompt files (`concern-investigator.md`, `implement-ticket.js`) — the
retro cadence rule ("before changing any agent prompt") applies. Already satisfied earlier in
this same branch/session: `agent-monitoring/retro/RETRO-2026-W40.md` generated and committed
(`8d3dff99d`) before this ticket's own prompt edits land, per the design peer's explicit request.
Not regenerating again for this one ticket — the rule is about the retro being current before a
prompt change, not one retro per prompt-changing ticket.

## Sequencing

1. `tools/open_ticket_overlap.py` + its tests + the AC1 fixture (self-contained, no prompt
   dependency).
2. Wire the 3 call sites + pin tests (depends on step 1 existing).
3. `docs/ai/ticket-lifecycle.md` doc addition (independent, can happen anytime).
4. User confirmation for both CLAUDE.md lines (Steps 3 and 4's literal text) — single
   `AskUserQuestion` call.
5. CLAUDE.md edit (only after 4 confirms; ships doc-only per AC5 if declined).
6. Finalize.
