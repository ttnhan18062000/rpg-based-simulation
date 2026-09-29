---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER
phase: open
date: 2026-09-29
tags: [process-improvement, workflows, create-tickets, ticket-scoper]
---

# TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER

## Title

No ticket-creation path checks open tickets for duplicates. Separately, nothing in the process ever
leads to `create-tickets` or `implement-epic` being offered, and both have almost stopped running.

## Status

OPEN

## Tier

standard

## Type

repair

## Priority

P1

## Request Summary

Two linked gaps, found 2026-09-28/29 while answering rpg-feature-planning's questions about when
`create-tickets` and `implement-epic` apply. The user approved fixing both in one ticket (option B,
2026-09-29).

**Gap 1: every automated duplicate check looks only at closed work.** None of these sees an open
ticket in `tickets/todos/` (including subfolders) or in `tickets/inprogress/`:

| Check site | What it scans (origin/main `4512eae30`) |
|---|---|
| `create-tickets` → `.claude/agents/concern-investigator.md` Step 3 (~lines 83–92) | `grep -i … tickets/working_log.csv`, which holds closed tickets only, plus `docs/REGISTRY.yaml` (docs and closed tickets) |
| `implement-ticket.js` Scope, when resuming an existing ticket (lines 128–159) | nothing: loads the file and sets `conflicts=[]` |
| `implement-ticket.js` Scope, when creating a new ticket (line 171) | "inprogress/, done/, and backlogs/", with `todos/` absent |
| `search_docs` / `tools/knowledge_search.py` (lines 9–11, 173–175) | `tickets/done/TCK-*.md` and `working_log.csv` only |

Real miss: rpg-feature-planning's hand-authored wave ticket B0 overlapped the already-open P1
`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`. No tooling flagged it; it was caught only
because the user asked about the backlog.

**Gap 2: the two workflows have stopped being used, and no rule tells an agent to offer them.**
Runs per ISO week, from `agent-monitoring/data/*/runs.jsonl` on origin/main:

| Workflow | through W36 (~2026-09-06) | W37 | W38 | W39 | W40 |
|---|---|---|---|---|---|
| implement-ticket | ~100–160/week | 115 | 89 | 70 | 6 so far |
| implement-epic | 114 total | 0 | 0 | 0 | 0 |
| create-tickets | 45 total | 1 | 0 | 1 | 0 |

The opt-in rule (CLAUDE.md:359, "`Workflow` … user must request the scale") dates from 2026-06-12
(#11), so it isn't the cause. The delivery shape changed instead: planning sessions write tickets by
hand, and the implementer runs `implement-ticket` once per ticket. `docs/ai/ticket-lifecycle.md:632`
says "Use `/implement-epic` when you have multiple tickets", but agents can't start a workflow
themselves, and nothing tells them to **offer** one to the user. So no run ever happens.
Consequence: `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION` can never be confirmed, and
both workflows keep getting maintenance fixes without any runs.

## Scope

1. **Open-ticket overlap scanner.** Add a new CLI under `tools/`, e.g.
   `tools/open_ticket_overlap.py`. It reads `tickets/todos/**/TCK-*.md` and
   `tickets/inprogress/TCK-*.md` live from disk, with no index, so a ticket written a minute ago is
   included. Given either a ticket file, or a title/summary plus an optional list of code paths, it
   reports open tickets that overlap it, using two signals:
   (a) intersection of `## Related Code Areas` paths;
   (b) distinctive-term overlap in title and Request Summary.
   It prints JSON and always exits 0, since it's a report, not a gate. It excludes the queried
   ticket itself (same ticket_id). Parse body sections with the canonical parser
   (`tools/generate_registry.py::parse_body_section`, the same one `tools/epic_folder_status.py`
   reuses), never a hand-rolled regex.
2. **Wire it into all three check sites. It is advisory only:** hits go to
   `related_context` / `related_tickets`, never to `conflicts` / `is_duplicate`. A person or agent
   judges whether a hit is a real duplicate.
   - `concern-investigator.md` Step 3: run the scanner alongside the working_log grep.
   - `implement-ticket.js` Scope, new-ticket path (line 171): add `todos/` via the scanner.
   - `implement-ticket.js` Scope, existing-ticket path (lines 128–159): run the scanner on the loaded
     ticket, and put hits in `related_context`. Don't change its `conflicts` behavior.
3. **Rule to offer the workflows but never start them.** Add guidance that a session must **offer**
   (never start) `/create-tickets` when it is about to turn a plan or proposal into several tickets,
   and `/implement-epic folder=…` when a `tickets/todos/<folder>/` is ready to dispatch. The user
   decides each time; this doesn't change the opt-in rule. It goes in
   `docs/ai/ticket-lifecycle.md` (next to line 632) **and** as one line in CLAUDE.md's
   "Require explicit user opt-in" section, because CLAUDE.md is the only always-loaded file a
   planning session reads.
   **The CLAUDE.md edit needs direct user confirmation of the literal text via AskUserQuestion
   before commit.** A peer's relay doesn't count. Proposed text, for the user to accept or edit:
   > Offering is not invoking: when about to turn a plan into several tickets, or when a
   > `tickets/todos/<folder>/` is ready to dispatch, briefly offer `/create-tickets` or
   > `/implement-epic` (what it would do, rough cost) and let the user choose.
4. **CLAUDE.md "PR Lifecycle" pointer never names `pr_render.py`.** Added 2026-09-29 at the user's
   request. rpg-feature-planning hand-wrote PR #254's body out of template compliance, because
   CLAUDE.md's pointer (origin/main CLAUDE.md:371-374, "commit → push → PR → CI monitor → report →
   …") is the only always-loaded description of the lifecycle and skips rendering.
   `docs/guides/delivery_process.md` already covers it in full (`pr_render.py` for creation at :218,
   `--check` at :235), so don't copy any detail into CLAUDE.md (define-once). Just add the step to
   the pointer's arrow list. The same AskUserQuestion confirmation as item 3 applies; confirming
   both lines in one question is fine. Proposed literal text:
   > Full steps in `docs/guides/delivery_process.md` ("PR Lifecycle"): commit → push → render the
   > title/body with `tools/delivery/pr_render.py` → PR → CI monitor → report → (user-authorized)
   > merge → sync, …

## Out of Scope

- Adding open tickets to the `search_docs` / `knowledge_search.py` index. That index is rebuilt only
  on doc changes, so a newly written ticket would stay invisible until the next rebuild, which is
  the same blind spot again.
- Making overlap blocking, or changing `conflicts` / `is_duplicate` semantics. The user's standing
  preference is proportionate, non-gating agent tooling.
- Retiring or restructuring `implement-epic` (option C). Revisit at a future retro only if runs
  stay at zero after this lands.
- Resolving the B0 / PERCEPTION-UPDATE overlap itself. That belongs to rpg-feature-planning.

## Acceptance Criteria

- AC1: The scanner, run on rpg-feature-planning's B0 wave ticket (or a fixture copy of it), reports
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`. If B0 isn't on main when this is
  implemented, use a fixture that reproduces the pair's real Related Code Areas and summaries, and
  cite its source.
- AC2: Negative controls: an unrelated ticket gets no hits, and a ticket never matches itself.
- AC3: It sees a ticket created in a temp `tickets/todos/` during the test, proving no index or
  staleness dependency.
- AC4: All three check sites invoke the scanner, and hits land only in non-blocking fields. Prove
  this with prompt-text pin tests like the existing workflow pin tests, not only with grep.
- AC5: The offer rule is present in `docs/ai/ticket-lifecycle.md`. The CLAUDE.md line lands only
  after the user confirms its literal text, with that confirmation recorded in Implementation
  Notes. If the user declines, record that and ship the doc half only.
- AC5b: The CLAUDE.md PR Lifecycle pointer names `pr_render.py` in its step list after the same
  confirmed-literal-text process as AC5. No template or section detail is duplicated from
  `delivery_process.md`.
- AC6: Existing implement-ticket / create-tickets workflow tests and the concern-investigator tests
  still pass.

## Related Tickets

- `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION` (blocked on real runs; Gap 2 is why)
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` (the real missed overlap)
- `TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT` (`tools/epic_folder_status.py` precedent
  for a committed helper that workflows call)

## Related Docs

- `docs/ai/ticket-lifecycle.md`
- `docs/ai/workflows.md`
- `CLAUDE.md` ("Require explicit user opt-in")

## Related Stored Artifacts

None.

## Related Code Areas

- `tools/open_ticket_overlap.py` (new)
- `.claude/agents/concern-investigator.md`
- `.claude/workflows/implement-ticket.js`
- `.claude/workflows/create-tickets.js` (only if concern-investigator's schema needs a field)
- `docs/ai/ticket-lifecycle.md`
- `CLAUDE.md`

## Assumptions / Open Questions

- The overlap threshold is the implementer's choice, but it must be justified with the AC1/AC2 pair,
  not picked arbitrarily. Prefer false positives to misses, since the output is advisory.
- Changing prompts triggers the retro cadence rule ("before changing any agent prompt"). Generate
  the retro in the branch's own checkout (cwd = that checkout) before the prompt commit.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
