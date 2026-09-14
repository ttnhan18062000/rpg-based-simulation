---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING
phase: done
date: 2026-09-11
tags: [workflows, process-improvement]
---

# TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING

## Title
`implement-epic.js` has no step that closes the epic ticket itself once all children are done

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Follow-on from `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`'s investigation
(`staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/investigation.md`
§8, second correction). No workflow in this repo ever closes an *epic ticket itself*:

- `implement-ticket.js`'s epic-tier routing path returns `EPIC_SCOPED` for a ticket tagged
  `## Tier: epic` and never touches the epic ticket file's own frontmatter or location.
- `implement-epic.js` (482 lines) only moves a finished `tickets/todos/{folder}/` directory once
  all its child tickets are done — it never updates or moves the epic ticket file itself.
- `create-tickets.js`'s Link phase looks up the epic only to append child ticket IDs to it — also
  not a close step.

As a result, every epic ticket that has ever reached `tickets/done/` got there by a human/agent
manually editing its frontmatter and `git mv`-ing it (or via a bulk PR squash merge), with no
workflow instruction and no automated check. Investigation's evidence: of 12 epic tickets with an
`implement-epic` run record, 11 (91.7%) still show frontmatter drift by the time they land in
`tickets/done/` — the highest drift rate of any closing path measured (vs. 24.6% for
`implement-ticket` ticket-tier closes, which at least have Finalize's instruction to fall back on).

Confirmed real, not hypothetical: the 9+1 `phase: epic_scoped` tickets found in that investigation
(E13/E21/E31/E32/E33/E41/E42/E43/E53A/E53D) are exactly this — closed epics whose frontmatter was
never normalized by any workflow step, only by TCK-20260907's own bulk remediation.

## Scope
- Add an epic-close step to `implement-epic.js` (the natural home, since it already owns the
  "all children done" detection that currently only triggers the `tickets/todos/{folder}/` →
  `tickets/done/{folder}/` move) that, once triggered:
  - Sets the epic ticket's own frontmatter `phase: done` / `status: historical` (matching
    `tickets/done/`'s location-aware rule added by TCK-20260907, in
    `tools/validate_frontmatter.py::check_ticket_location_consistency`).
  - Sets the epic ticket's own body `## Status` per whatever value CLAUDE.md's epic vocabulary
    settles on (`DONE` vs `EPIC_SCOPED` — CLAUDE.md documents `EPIC_SCOPED` as a valid body status
    for epics; TCK-20260907 found live disagreement even among the 10 existing epics, 7 say
    `DONE` and 3 say `EPIC_SCOPED` post-normalization — this ticket should settle which is
    canonical going forward, not just replicate the existing split).
  - Moves the epic ticket file itself: `tickets/inprogress/{epic_id}.md` (or wherever it lives)
    → `tickets/done/{epic_id}.md`, alongside the existing folder move.
- Add a static/regression test proving the new step actually fires and produces canonical
  frontmatter, following this repo's established raw-source-text-parsing pattern for `.js`
  workflow files (see `tests/tools/test_finalize_knowledge_index_refresh.py`,
  `tests/tools/test_finalize_phase_status_instruction_pin.py`).

## Out of Scope
- Re-normalizing the 9-10 already-closed epic tickets' frontmatter — already done by
  `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`'s Step 3 bulk remediation.
- Any change to `tools/validate_frontmatter.py`'s location-aware rule itself, or to the
  `tickets/done/` corpus test — both already exist and are what this new workflow step must
  satisfy, not something this ticket needs to touch.
- Deciding the DONE-vs-EPIC_SCOPED body-status question in isolation from the workflow-step work —
  investigate both together, since the workflow step needs to know which value to write.

## Acceptance Criteria
- [ ] `implement-epic.js` sets the epic ticket's frontmatter to `phase: done` /
      `status: historical` and moves the file to `tickets/done/` once all children are confirmed
      done, in the same step that already moves the `tickets/todos/{folder}/` directory.
- [ ] The new step also resolves and writes the epic ticket's own body `## Status` value
      (DONE vs EPIC_SCOPED — decide which is canonical as part of this ticket).
- [ ] A test proves the step fires (raw-source-text pin, following
      `tests/tools/test_finalize_knowledge_index_refresh.py`'s pattern — no JS test runner exists
      in this repo for `.claude/workflows/*.js`).
- [ ] `tools/validate_frontmatter.py::check_ticket_location_consistency`'s `tickets/done/` rule
      passes on an epic closed through the new step, without needing a follow-up bulk-remediation
      ticket.

## Related Tickets
- `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT` (done) — filed this ticket at its own
  Finalize; added the `tickets/done/` location-aware validator rule and corpus test this ticket's
  new workflow step must satisfy, and bulk-remediated the 9-10 already-closed epics' frontmatter
  as a one-time fix (not a durable one — this ticket is the durable fix for epics going forward).

## Related Docs
- `staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/investigation.md`
  §8 (second correction) — the evidence this ticket is based on.

## Related Stored Artifacts
None yet — Investigate should produce `investigation.md`/`plan.md`/`test_plan.md` per this
ticket's `standard` tier.

## Related Code Areas
- `.claude/workflows/implement-epic.js`
- `.claude/workflows/create-tickets.js` (Link phase — confirm it stays out of scope, or is the
  better home, during Investigate)
- `tools/validate_frontmatter.py` (`check_ticket_location_consistency` — consumed, not modified)

## Assumptions / Open Questions
- Whether `implement-epic.js` or a different workflow file is the correct place for this step —
  Scope's best guess is `implement-epic.js` since it already owns "all children done" detection,
  but Investigate should confirm rather than assume.
- Whether DONE or EPIC_SCOPED should be the canonical body `## Status` for a fully-closed epic —
  open per the existing 7/3 split found in the live corpus.

## Implementation Notes

See `staging_artifacts/TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING/investigation.md` and
`plan.md` for the full design-question writeup (3 options considered, Option A chosen) and the
DONE-vs-EPIC_SCOPED evidence. Summary: `implement-epic.js`'s `epic_id` mode had zero equivalent
of its own `folder`-mode cleanup step — every epic ticket previously reached `tickets/done/` by
hand or in a batch commit. Added a new guarded block (`if (batchStatus === 'DONE' && epicId)`)
immediately after the existing folder-cleanup block, mirroring its shape: an agent instruction
that sets the epic ticket's frontmatter to `phase: done`/`status: historical`, its body
`## Status` to `DONE` unconditionally — not only replacing `EPIC_SCOPED`, but overwriting whatever
the field currently reads (confirmed via a corrected, recursive-glob live-corpus check: 71/79
(89.9%) already-closed epics already read `DONE`; 7 read `EPIC_SCOPED` and 1 reads `OPEN` — a third
drift shape, `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`, neither `DONE` nor `EPIC_SCOPED` —
all 8 are drift from this exact missing-step bug, and the step's unconditional "set to DONE"
instruction corrects all three shapes the same way, not just `EPIC_SCOPED`) — and moves the file to
`tickets/done/{epic_id}.md`. Uses a fresh, non-colliding negative sidecar seq (`-5`), confirmed
against every existing `writeSidecar(-N, ...)` call site before picking it.

**Correction (post-review, agent-working-design):** the original investigation undercounted the
corpus 52 vs. the true 79 — it globbed only `tickets/done/TCK-*.md` and missed epic tickets living
inside per-batch subfolders (`tickets/done/{folder}/TCK-*.md`), created by the existing
folder-move step's own long-standing convention. Re-verified with a recursive glob; the DONE
majority (89.9% vs. the original 88%) and the decision both survive the correction unchanged —
see investigation.md §1/§4 for the full re-derivation.

## Test Summary

New `tests/tools/test_implement_epic_close_step.py` (10 tests, all passing): 7 raw-source-text pins
against `implement-epic.js`, following `test_finalize_phase_status_instruction_pin.py`'s
established pattern (no JS test runner exists for `.claude/workflows/*.js`) — frontmatter
instruction present, body-status instruction says DONE with the EPIC_SCOPED contrast still
explained, `mv` instruction present, guard is `epicId` not `folder`, ordering (after
folder-cleanup, before `phase('Report')`), bookkeeping "never fail the workflow" framing, and the
fresh `-5` sidecar seq — plus 3 parametrized fixture tests (added post-review, see the honest
disclosure below) applying the prompt's own specified transformation to a synthetic ticket
starting from each real drift shape (`EPIC_SCOPED`/`OPEN`/`DONE`) and checking the result against
the real `check_ticket_location_consistency()` validator.

Updated `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` (pre-existing pin over
implement-epic.js's writeSidecar call set/order) to include the new `-5` call at its correct file
position (`-1, -2, -3, -5, -4` — epic-close runs in the Implement phase, before the Report-phase
tracking-doc-update step, despite -5 > -4 numerically) — this was a real, legitimate update to a
test whose previous expectation genuinely became outdated by this ticket's own new code, not a
gate-evasion edit.

Full suite run: `tests/tools/test_implement_epic_close_step.py`,
`test_epic_create_tickets_sidecar_orchestrator.py`, `test_epic_tracking_doc_static.py`,
`test_monitoring_bypass_fix.py`, `test_record_events.py`,
`test_retrieval_event_wrapper_single_source.py`, `test_step0_ts_orchestrator.py`,
`test_workflow_meta_conformance.py` — 107 passed, 1 xfailed (pre-existing, unrelated), 0 failed.

Parity: skip-eligible (no `src/` path changed; this is pure agent-orchestration/workflow-tooling
logic with no simulation-mechanics relevance). `find_p0_intersection` against the changed files
returned `[]` — no P0 ledger entry depends on any of them.

**Honest disclosure (post-review, agent-working-design): the 7 raw-source-text-pin tests are
prompt-text pins, not behavior tests.** Every assertion matches literal text inside
`implement-epic.js`'s agent prompt — that the frontmatter/body-status/`mv` instructions and the
`epicId` guard appear, in the right order, with the right framing. None of them executes the close
step or asserts that a real epic ticket actually ends up transformed — they pass if the prompt is
worded correctly even if the dispatched agent ignores it, and fail on any reword that preserves
meaning. This mirrors the existing folder-cleanup block's own test coverage in the same file (also
a prompt-text pin, never a behavior test) — not a new gap this ticket introduced, but one this
ticket's own new step inherits rather than closes.

The 3 added fixture tests (`test_epic_close_step_target_values_satisfy_the_real_location_validator`,
parametrized `EPIC_SCOPED`/`OPEN`/`DONE`) close part of this gap: they apply the prompt's own
specified end-state transformation to a synthetic ticket in `tmp_path` and check the result against
the real `check_ticket_location_consistency()` — the same function TCK-20260907's own corpus test
runs over all of `tickets/done/` at CI. **They still do not prove the dispatched agent performs the
transformation correctly at runtime** — no fixture can, short of a real `implement-epic` run, which
isn't warranted for this change. **The real CI-enforced backstop remains TCK-20260907's
frontmatter-only corpus test**: it will catch a drifting epic's `phase`/`status` frontmatter. Body
`## Status` has no automated CI enforcement at all — only this step's own (unverified-at-runtime)
prompt instruction — a real, disclosed gap, not something these tests should be read as closing.

**Second-round fix (post-review, agent-working-design): the fixture test's frontmatter check was
self-referential.** The first version passed a hand-built `{"status": "historical", "phase":
"done"}` dict straight to the validator — confirming only that a literal the test itself wrote
satisfied the rule, not that the `re.sub` transformation above it actually produced that result. A
broken rewrite (wrong anchor, unexpected spacing, `count=1` hitting the wrong line) would have
sailed through undetected. Fixed by parsing the frontmatter back out of the written file via
`extract_frontmatter()` instead. Confirmed the fix actually catches a broken rewrite before
shipping it (a deliberately-broken `re.sub` in a scratch check correctly failed the assertion).

## Files Changed

- `.claude/workflows/implement-epic.js` — new epic-close step (guarded `epicId` block, after
  folder-cleanup, before Report phase)
- `tests/tools/test_implement_epic_close_step.py` (new) — 7 raw-source-text pin tests + 3
  parametrized fixture tests against the real `check_ticket_location_consistency()` validator
- `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` — updated pre-existing
  writeSidecar call-set/order pin to include the new `-5` call
- `docs/ai/workflows.md` — updated `implement-epic`'s Implement-phase row to describe the new
  epic-close behavior

## Completion Summary

Added the missing epic-ticket close step to `implement-epic.js`'s `epic_id` mode, closing the gap
`TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`'s investigation identified (91.7% of
`implement-epic`-run epics drifted because nothing ever closed the epic ticket file itself).
Investigation confirmed this required a genuine design decision, not a one-line wiring fix: no
existing code path was a near-miss for this — `implement-ticket.js`'s epic-tier path runs once,
before any children exist, and cannot detect completion; `create-tickets.js`'s Link phase fires at
ticket creation, the wrong lifecycle stage entirely. Of the three options considered (extend
`implement-epic.js`'s `epic_id` mode; add a re-entrant close phase to `implement-ticket.js`; a
separate close command), the first was chosen: it's the only one that reuses state
`implement-epic.js` already computes (`batchStatus`, `epicId`, `discovery.epic_ticket_path`)
instead of duplicating or inventing new infrastructure, and it makes `epic_id` mode symmetric with
the `folder`-mode cleanup step that already ships. Also settled the pre-existing DONE-vs-EPIC_SCOPED
body-status ambiguity for closed epics with live-corpus evidence (71/79 already `DONE`, corrected
after review from an initial undercount that missed epics inside per-batch `tickets/done/`
subfolders) rather than picking one arbitrarily, and confirmed the new step's unconditional
"set to DONE" instruction also self-heals the one closed epic found reading `## Status: OPEN`
(`TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`), a third drift shape distinct from
`EPIC_SCOPED`. No src/ or simulation-mechanics code touched; Parity is skip-eligible. Test coverage
for the new step is honestly disclosed as prompt-text pins only, not behavior verification — see
Test Summary.
