---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON
phase: done
date: 2026-09-23
tags: [ai, agent-monitoring, governance]
---

# TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON

## Title
Shadow-reviewer collection default-on flip + AI-first hardening follow-on epic refresh

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Two parts, bundled because the second depends on the first's own evidence:

(a) `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (`tickets/todos/`, `EPIC_SCOPED`) is stale: its
Bucket B/C item list and Assumptions section describe several gating tickets as pending or
in-progress, but all six — `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`,
`TCK-20260904-SHADOW-REVIEWER-LOGGING`, `TCK-20260904-BASH-SECRET-SCAN-HOOK`,
`TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST`,
`TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING`, `TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN`
— are now in `tickets/done/`. Refresh the epic's own text to reflect that, with the done paths, so
a future reader doesn't have to re-derive it from scratch.

(b) The user approved turning shadow-reviewer collection on by default. Today
`SHADOW_REVIEWER_LOGGING_ENABLED` defaults off (`.claude/workflows/implement-ticket.js`'s two call
sites gate on strict `"1"` string equality) — real collection has produced only 3 `-shadow` events
total across all weekly shards, nowhere near the 50 architecture-reviewer / 10 security-reviewer
sample window `TCK-20260904-SHADOW-REVIEWER-LOGGING`'s own M2 decision needs
(`review_independence_epic.md`, Bucket-B item 16). Flip the default so unset means enabled, with
`SHADOW_REVIEWER_LOGGING_ENABLED=0` as the explicit opt-out — this is a JS-level default flip, not
a `.claude/settings.json` env block (that file is a governing file needing its own direct user
confirmation of literal text, which this batch does not have).

## Scope
- Update `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`'s Request Summary / Assumptions /
  Related Tickets sections to state plainly that all 6 named gating tickets are done (with their
  `tickets/done/` paths), and that item 13's eval pilot unblocked Bucket-C items 18-20 per its own
  already-recorded Related Tickets bullet. Do not re-scope the epic itself or create child tickets
  from it — this is a text-accuracy refresh only, the epic stays `EPIC_SCOPED`.
- Flip `.claude/workflows/implement-ticket.js`'s two shadow-reviewer gate call sites (Architecture-
  Verify ~line 1057, Security-Review ~line 1502) from `if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" =
  "1" ]` to a form where an unset/empty env var enables collection and `SHADOW_REVIEWER_LOGGING_ENABLED=0`
  is the explicit opt-out.
- Update the two comments referencing the old default (lines ~220, ~1049) and every doc that states
  "off by default": `docs/agent-monitoring/schema.md`'s Shadow-reviewer-event field family section,
  `docs/parity_ledger/infrastructure.yaml`'s `INFRA-409` entry (`text` and `v2_evidence`).
- Update `tests/tools/test_shadow_reviewer_call_site.py::test_shadow_reviewer_call_site_is_fail_open_and_env_gated`
  (line ~230) to assert the new gate string instead of the old one; add a test asserting the
  opt-out path (`SHADOW_REVIEWER_LOGGING_ENABLED=0` closes the gate) if no existing test already
  covers that shape.
- State plainly in this ticket (Assumptions/Open Questions or Implementation Notes) that default-on
  may still fill the 60-sample window slowly, because most ticket closures in this repo are
  hand-orchestrated and never run `implement-ticket.js`'s pipeline — a known limitation to record,
  not something to engineer around.

## Out of Scope
- Widening the bounded window (`SHADOW_MAX_SAMPLES` = 50 architecture-reviewer / 10
  security-reviewer, 60 total) — that is the existing cost cap, unrelated to the default-on
  question, and stays exactly as-is.
- Adding an env-var default via `.claude/settings.json` — explicitly rejected route per the batch
  brief; if the JS-level default route turns out not to work, this ticket stops and reports rather
  than touching `settings.json`.
- Scoping Bucket-C items 18/19/20 into Experiment Specifications — those are the two sibling
  tickets in this same batch (`TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC`,
  `TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC`) plus item 20 which stays untouched.
- Making the M2 shadow-comparison cutover decision itself (`review_independence_epic.md` M2) — this
  ticket only makes collection actually collect; the comparison/decision is separate future work
  once enough sample data exists.
- Any change to the candidate model choice (`claude-fable-5-1`), the shadow event schema, or
  `shadow_reviewer_events.py`/`shadow_reviewer_window.py`'s own logic — only the env-var default
  changes.

## Acceptance Criteria
- [x] `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`'s text accurately reflects that all 6 named
      gating tickets are done, with paths, and that item 13 unblocked items 18-20.
- [x] Both `implement-ticket.js` shadow-reviewer call sites collect by default with the env var
      unset, and stop collecting when `SHADOW_REVIEWER_LOGGING_ENABLED=0` is set explicitly.
- [x] `docs/agent-monitoring/schema.md` and `docs/parity_ledger/infrastructure.yaml`'s `INFRA-409`
      entry no longer say "off by default"; both accurately describe the new default.
- [x] `tests/tools/test_shadow_reviewer_call_site.py` passes and covers both the default-on shape
      and the explicit `=0` opt-out shape.
- [x] This ticket's own body states the known slow-fill limitation (hand-orchestrated closures
      bypass the pipeline entirely) plainly, not implied.
- [x] `## Related Tickets` links back to `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`.

## Related Tickets
- `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (`tickets/todos/`, `EPIC_SCOPED`) — the Bucket
  B/C tracking epic this ticket both refreshes (part a) and further executes on (part b, item 16's
  prerequisite).
- `TCK-20260904-SHADOW-REVIEWER-LOGGING` (done) — built the collection mechanism this ticket
  changes the default of; does not touch its schema or scoring logic.
- `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT` (done) — item 13, unblocks the epic's Bucket-C items;
  referenced in the epic refresh.
- `TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC`,
  `TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC` (this batch, `tickets/todos/`) — sibling
  tickets in the same batch, independent of this one.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/review_independence_epic.md` (M2) —
  the shadow-comparison decision this ticket's part (b) is a prerequisite for, not itself.
- `docs/agent-monitoring/schema.md` — Shadow-reviewer-event field family section.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-409` entry.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260904-SHADOW-REVIEWER-LOGGING/` — original build; background only.

## Related Code Areas
- `.claude/workflows/implement-ticket.js` — two shadow-reviewer gate call sites (~1057, ~1502) plus
  their surrounding comments (~220, ~1049).
- `tests/tools/test_shadow_reviewer_call_site.py` — static source-text assertions on the gate shape.
- `tickets/todos/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md` — epic text refresh.

## Assumptions / Open Questions
- Assumes an unset env var reads as empty string in the bash `[ ]` test used at both call sites
  (true for this repo's shell invocation pattern — confirmed by reading the existing `= "1"` form,
  which already relies on the same unset-is-empty behavior for the off-by-default case).

## Implementation Notes
Confirmed via grep that the two `implement-ticket.js` call sites (~1057, ~1502) are the ONLY places
that reference `SHADOW_REVIEWER_LOGGING_ENABLED` outside comments/docs — `shadow_reviewer_window.py`
and `shadow_reviewer_events.py` never read the env var themselves, so this ticket's diff is confined
to the orchestrator file, one test file, two docs, one parity-ledger entry, and the epic ticket.

Flipped both gate conditions from `= "1"` (opt-in, off by default) to `!= "0"` (on by default,
`SHADOW_REVIEWER_LOGGING_ENABLED=0` opts out) — an unset env var reads as empty string in bash
`[ ]`, and `"" != "0"` is true, so collection now runs unless explicitly disabled. Updated the one
comment (~1049) that stated the old truthy value literally; the other comment (~220, on the
ticket-claim-detection code) already described the gate generically and needed no change.

**Known limitation, stated plainly per this ticket's own Scope**: default-on may still fill the
60-sample window (50 architecture-reviewer / 10 security-reviewer, unchanged) slowly, because most
ticket closures in this repo are hand-orchestrated and never invoke `implement-ticket.js`'s actual
pipeline — the only code path that ever evaluates this env var. This ticket makes collection
possible when the pipeline does run; it does not change how often the pipeline runs.

Updated `docs/agent-monitoring/schema.md` and `docs/parity_ledger/infrastructure.yaml`'s `INFRA-409`
entry (via `tools/parity_ledger_writer.py::write_entry()`, never a raw YAML string-replace — full-
file rewrite risk) to state the new default; ran `python3 tools/parity_index.py build` afterward for
a visible, retro-countable index rebuild per the module's own documented convention. Confirmed the
resulting diff to `infrastructure.yaml` is minimal (9 insertions/4 deletions, only the INFRA-409
entry touched) — the writer's `yaml.safe_dump` round-trip did not reformat unrelated entries.

Refreshed `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (still `tickets/todos/`, still
`EPIC_SCOPED` — no re-scoping): corrected stale `tickets/todos/`/`tickets/inprogress/` path
annotations for items 14/15/Bucket-A (all now `tickets/done/`), updated Bucket-B items 16/17 status
(16: this ticket's part b addresses its data-starvation prerequisite; 17: knowledge-gateway gate
cleared but false-positive-rate gate still open, confirmed not part of this batch), and noted items
18/19 were scoped into Experiment Specifications by this same batch's sibling tickets.

## Test Summary
`pytest tests/tools/test_shadow_reviewer_call_site.py tests/tools/test_shadow_reviewer_window.py -v`
— 16/16 passed (12 in the call-site file including 1 updated + 1 new test, 4 in the window file,
unchanged/regression). Scoped to the domain under modification per CLAUDE.md's Testing Rule.

## Files Changed
- `.claude/workflows/implement-ticket.js` — both shadow-reviewer gate conditions flipped
  (`= "1"` → `!= "0"`) at the Architecture-Verify and Security-Review call sites; one comment
  updated to describe the new default.
- `tests/tools/test_shadow_reviewer_call_site.py` — updated the env-gated assertion to the new gate
  string; added `test_shadow_reviewer_default_on_opt_out_literal_is_zero_not_one` (polarity guard).
- `docs/agent-monitoring/schema.md` — Shadow-reviewer-event field family section updated to describe
  the new default.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-409` entry's `text`/`v2_evidence` updated via
  `tools/parity_ledger_writer.py`.
- `docs/parity_ledger.db` (or equivalent derived index path) — rebuilt by `write_entry()` in-process
  and again visibly via `python3 tools/parity_index.py build`.
- `tickets/todos/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md` — text-accuracy refresh (paths,
  Bucket-B item 16/17 status, Bucket-C item 18/19 cross-references); `EPIC_SCOPED` status unchanged.
- `tickets/todos/ai-first-hardening-bucket-b-followon/` — new folder: `SEQUENCE.md` plus this
  ticket and its two siblings (`TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC`,
  `TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC`).
- `staging_artifacts/TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON/` — new:
  `investigation.md`, `plan.md`, `test_plan.md`.
- `tickets/todos/TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON.md` — deleted (superseded by
  this file, `tickets/done/TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON.md`).

## Completion Summary
Flipped `implement-ticket.js`'s shadow-reviewer collection default from opt-in (off) to opt-out
(on), so the M2 comparison window named in `review_independence_epic.md`'s Bucket-B item 16 can
actually accumulate samples — real volume was 3 events total across all weekly shards under the old
default. Updated the one test that pinned the old gate string, added a polarity-regression guard,
and kept both docs and the parity-ledger entry describing this mechanism in sync with the new
default, per CLAUDE.md's Authoritative Mechanics Rule for parity/doc updates. Refreshed the stale
AI-first hardening follow-on epic ticket so its Bucket B/C status accurately reflects that all 6
originally-pending gating tickets are done, without re-scoping the epic itself. Stated plainly, not
engineered around: default-on alone does not guarantee the window fills quickly, since most ticket
closures in this repo bypass the pipeline entirely via hand-orchestration.
