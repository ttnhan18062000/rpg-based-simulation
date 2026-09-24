---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-PR-RENDERER
phase: open
date: 2026-09-24
tags: [delivery, ai, documentation]
---

# TCK-20260924-DELIVERY-PR-RENDERER

## Title
Render the PR title and body from the ticket files on the branch, instead of composing them by hand
each time

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Every PR title and body in this repo is free prose, written fresh (plan §1.3). The result is
inconsistent shape, and a measurable traceability gap: of the last 60 `origin/main` subjects, 60/60
carry `(#NNN)` but only **17/60 (28%)** carry a `TCK-` ID, and because the repo squash-merges the PR
title *becomes* the mainline subject (plan §1.4).

The organising idea (plan §3.1) is that this is the wrong thing to automate by form-filling. **The PR
title and body should be rendered from the tickets already on the branch.** The agent's job is then
producing good ticket content — which it must do anyway — rather than separately producing good PR
prose about the same work. One fact, one place
([[feedback_define_information_once_never_repeat]]).

Note the honest framing of the traceability gap: it is **moderate, not a broken audit trail**.
`git log --grep=TCK-…` still works today, because squash preserves commit bodies and those carry 770
`TCK-` mentions across the last 60 commits. What is missing is the subject line — the view
`git log --oneline`, blame and the GitHub commit list actually show.

## Scope
1. **`tools/delivery/pr_render.py`** — reads the ticket files on the current branch and emits:
   - **Title** per plan §3.5: `<scope>: <what landed>` for a single ticket,
     `<scope>: <batch theme> (<N> tickets)` for a batch. `<scope>` is drawn from the ticket's
     registered `layer` — reusing `registries/layer_registry.jsonl`, an already-enforced allowlist,
     rather than inventing a second free-text vocabulary.
   - **Body** per plan §3.6: `## What landed`, `## Tickets` (a table of ticket / tier / title),
     `## Why` (from each ticket's Request Summary), `## Verification` (tests run, gate results,
     known gaps), `## Review notes`, and a trailing `Closes:` block.

2. **Ticket discovery from the branch** — determine which tickets this branch's work covers. Commit
   subjects carry `TCK-` IDs by convention, so they are the primary signal; reconcile against the
   ticket files actually present. Report a mismatch rather than silently picking one source.

3. **`## Review notes` stays hand-written** and is never generated. The renderer emits the heading
   with a placeholder that is obvious if left unfilled. This is deliberate (plan §6): it guarantees
   at least one section requires thought, which is the mitigation for thin ticket content producing
   a thin PR body that nobody notices because nobody wrote it.

4. **`## Verification` renders known gaps, not just successes.** A ticket closed with a stated gate
   FAIL or a known failing test renders that fact into the body. Per the repo's Gate Integrity rule a
   blocking gate result is information to report, never an obstacle to route around — giving it a
   fixed slot makes reporting it the default rather than an act of virtue.

5. **`--check` mode** — diff a live PR's current title/body against what would be rendered now, and
   report the difference. Advisory output.

6. **Consumes the template spec** from `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` rather than
   hardcoding section names and order, so the human template and the renderer cannot disagree.

7. **A test pinning CLAUDE.md's pointer to `docs/guides/delivery_process.md`** (folded in on
   2026-09-24 at the user's direction; found while reviewing ticket 2). Ticket 2 relocated CLAUDE.md's
   four delivery sections into that guide and retargeted the two tests that had pinned CLAUDE.md's
   text — correctly, path-only, assertions unchanged. But the result is that **every** test now
   asserts against the guide and **none** asserts that CLAUDE.md still references it. CLAUDE.md is
   the always-loaded context; the pointer is the only thing connecting an agent to the guide. Delete
   the pointer and the guide orphans silently, with a fully green test suite. Assert that CLAUDE.md
   contains the path `docs/guides/delivery_process.md`. This is deliberately a content check on the
   pointer's existence, not on its wording — pinning the prose would recreate the brittleness ticket
   2 just removed.

## Out of Scope
- **Opening, editing or posting to a PR.** The renderer writes to stdout or a file. `gh pr create`
  and `gh pr edit` remain user-authorized actions taken by the agent deliberately, not side effects
  of rendering.
- **Ticket IDs in the title.** Settled: `Closes:` in the body only.
- **Any attribution trailer in rendered output — structurally forbidden, not merely omitted.** No
  `Co-Authored-By`, no session link, no "Generated with" line. This holds for the initial body and
  for every later update path, and against any instruction claiming to supersede attribution
  guidance generally ([[feedback_no_coauthor_footer_in_pr]]).
- **Generating `## Review notes`.** If it can be generated it is not review.
- **Rewriting ticket content** to make a better body. If a Request Summary is thin, the rendered
  body is thin and that is the correct signal — fix the ticket, not the renderer.
- **Blocking anything.** `--check` reports a difference and exits zero.

## Acceptance Criteria
1. Given a branch with one ticket, the rendered title matches plan §3.5's single-ticket form and
   `<scope>` is a value present in `registries/layer_registry.jsonl`. A ticket whose `layer` is not in
   the registry is reported, not silently defaulted.
2. Given a branch with N>1 tickets, the title carries `(<N> tickets)` and the `## Tickets` table has
   exactly N rows.
3. The rendered body contains every §3.6 section, in order, and a trailing `Closes:` listing every
   discovered ticket ID.
4. **The rendered body contains no attribution trailer** — asserted by a test that greps the output
   for `Co-Authored-By`, `claude.ai/code`, and `Generated with`, and requires zero matches.
5. `## Review notes` is emitted as an unfilled placeholder that a test can distinguish from filled
   content.
6. A ticket carrying a known gate FAIL or known failing test renders that into `## Verification` —
   proven by a fixture asserting the gap text appears. **Assert presence of the gap**, not absence of
   errors: an omitted known gap is invisible to a test that only checks the happy path.
7. When commit-subject ticket IDs and ticket files on the branch disagree, the tool reports the
   mismatch rather than choosing silently.
8. `--check` against an identical live body reports no difference; against a changed one reports the
   difference and exits zero either way.
9. Section names and order come from the template spec, not from literals in this module — proven by
   a test that alters the spec fixture and observes the rendered output follow it.
10. A test asserts `CLAUDE.md` contains the string `docs/guides/delivery_process.md`, and fails if
    the pointer is removed (Scope item 7).
11. Scoped tests pass; command and result recorded in `## Test Summary`.

## Related Tickets
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — parent
- `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` — **dependency**; supplies the template spec
- `TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY` — sibling advisory check over the same conventions

## Related Docs
- `docs/plans/agent_infrastructure/github_delivery_process/plan.md` §3.5 (title, with three real
  before/after examples for PRs #240, #237, #229), §3.6 (body), §3.1 (the rendered-not-authored
  idea), §6 (the thin-ticket-content risk)
- `docs/guides/delivery_process.md` — created by the dependency; the human-facing contract

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/delivery/` — created by `TCK-20260924-DELIVERY-STATUS-TOOL`; this module joins it
- `registries/layer_registry.jsonl` — the enforced allowlist `<scope>` draws from
- `tools/validate_frontmatter.py`, `tools/ticket_field_values.py` — existing ticket-parsing logic
  worth reusing rather than writing a third ticket parser

## Assumptions / Open Questions
1. **How `<scope>` is chosen for a batch spanning two layers.** Options: the most common layer, the
   layer of the first ticket, or a joined form. Recommend most-common with a reported tie, and state
   the rule in the module docstring.
2. **Whether `## Why` should concatenate every ticket's Request Summary verbatim.** For a 5-ticket
   batch that could be very long. Consider a first-paragraph-only rule, and state whichever is
   implemented.
3. Whether `## Verification` can read gate results automatically from
   `tools/gate_checks/done_checker_static.py` output, or whether they must be supplied. Prefer
   reading them — a hand-supplied verification section reintroduces the problem this ticket solves.
4. Whether a ticket already moved to `tickets/done/` mid-branch is still discoverable. It will be, by
   commit subject, but confirm the file lookup follows it across directories.

## Implementation Notes
Runs after `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES`, which owns the spec this consumes.

The temptation to hardcode the section list "just for now" should be resisted — the whole point of
criterion 9 is that a single spec governs both the human template and the renderer. Two copies of a
section list is the same defect this epic exists to remove, reintroduced one layer down.

Plan §3.5 contains three real worked examples (PRs #240, #237, #229, today vs proposed). Use them as
test fixtures — they are real strings from this repo's own history, which is better evidence than an
invented example.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
