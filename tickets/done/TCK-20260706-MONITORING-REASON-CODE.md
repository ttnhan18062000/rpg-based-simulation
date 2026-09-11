---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260706-MONITORING-REASON-CODE
phase: done
date: 2026-07-06
tags: [agent-monitoring, tagging, reporting]
---

# TCK-20260706-MONITORING-REASON-CODE

## Title
Add a `reason_code` field to agent-monitoring events.jsonl to disambiguate DOD_BLOCKED sub-causes

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Follow-up to the tag-registry work (`TCK-20260706-TAG-REGISTRY-DATA`). User asked whether there's
enough trace data to troubleshoot the new tagging + tag-based-skill-selection features after
running for 3 days, then suggested durable tracing similar to `agent-monitoring` for
"agent-related steps (tags, tasks, workflows, etc.)". Investigation found the real gap:
`agent-monitoring/events.jsonl`'s `summary` field is capped at "verdict + item count" for the
`Verify` phase, so a `DOD_BLOCKED` event cannot be distinguished, after the fact, between a
tag-registry rejection, a missing test, incomplete staging artifacts, or any other DoD condition
failure — `final_status`/`phase` already disambiguate every *other* gate outcome
(`CONFLICTS_DETECTED`, `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`/`BLOCKED`, `TESTS_FAILED`,
`SECURITY_BLOCKED`) 1:1 to a single specific phase and meaning — `DOD_BLOCKED` is the one
catch-all bucket hiding multiple distinct sub-causes. User confirmed the fix should extend the
existing `agent-monitoring` schema (not build a separate new tracing subsystem).

## Scope
- **`tools/gate_checks/done_checker_static.py`**: new pure function `classify_checklist_failure(checklist: list[dict]) -> str | None` —
  scans a `done-checker` checklist (the same `[{"condition","status","evidence"}, ...]` shape
  `run_static_precheck` already returns and the `done-checker` agent already transcribes into
  `doneCheck.checklist`) for the first `FAIL` entry: returns `"tag_registry_rejection"` if its
  `evidence` contains the tag-registry rejection substring (`"is not in the tag registry"`, the
  exact wording `validate_frontmatter.py`'s `_check_tags` already emits), `"dod_condition_failed"`
  for any other `FAIL`, or `None` if everything is `PASS`/`NA`.
- **`.claude/workflows/implement-ticket.js`**:
  - `pushEvent` gains an optional `reasonCode` parameter (nullable, default `null`), included in
    the pushed event object as `reason_code`.
  - After `doneCheck` returns with `verdict !== 'READY_TO_CLOSE'`, call
    `classify_checklist_failure(doneCheck.checklist)` via `bash()` (mirroring the existing
    Architecture-Verify Step-0 `bash()` + marker-prefixed-JSON pattern already used for
    `run_architecture_checks`), and pass the result as `reason_code` to the `Verify`/`failed`
    `pushEvent` call.
  - No other `pushEvent` call site changes — every other gate status already disambiguates via
    `phase`/`final_status` alone; adding `reason_code` there would be redundant, not new
    information (confirmed during investigation, not assumed).
- **`docs/agent-monitoring/schema.md`**: document the new `reason_code` field on `events.jsonl` —
  nullable, only populated today for `Verify`/`failed` events, two known values, explicitly *not*
  a closed enum (mirrors the tag-taxonomy category precedent: extensible, evidence-driven, not
  pre-enumerated).
- **`tools/agent-monitoring/generate_retro.py`**: aggregate `reason_code` occurrences for
  `done-checker`'s `failed` events into the retro report, so the field is actually consumed by the
  tool meant to answer "how did this run" after a few days, not just written and never read.
- **Tests**: `tests/tools/test_done_checker_static.py` gains coverage for
  `classify_checklist_failure` (tag-registry case, generic-DoD-failure case, all-pass case, mixed
  checklist where a later entry is the failing one).

## Out of Scope
- Retrofitting `reason_code` onto any other phase's `pushEvent` call — no evidenced gap there
  today (see Request Summary); would be speculative, not evidence-driven.
- Any change to `create-tickets.js` — it has no `Verify`/`done-checker` phase, so this specific
  gap doesn't apply to that workflow; its own event schema is untouched.
- Tracking whether `suggested_skills` (tag-based skill selection) was actually acted on — flagged
  in the prior exploratory discussion as a separate, bigger question (would need the orchestrating
  session to self-report), not decided or built here.
- Any change to `tools/agent-monitoring/validate.py` — confirmed it does not enforce a closed
  field set, so the new optional field needs no accommodation there.

## Acceptance Criteria
- [ ] `classify_checklist_failure` exists, pure, tested (4+ cases).
- [ ] A `Verify`-phase `DOD_BLOCKED` run caused by an unregistered tag produces an `events.jsonl`
      record with `reason_code: "tag_registry_rejection"`.
- [ ] A `Verify`-phase `DOD_BLOCKED` run caused by any other DoD failure produces
      `reason_code: "dod_condition_failed"`.
- [ ] Every other phase's pushed events still have `reason_code: null` (unchanged, confirmed not a
      regression — old records without the field remain valid, matching the `tool_call_count`
      nullable-for-old-records precedent).
- [ ] `docs/agent-monitoring/schema.md` documents the field.
- [ ] `generate_retro.py`'s report includes a reason-code breakdown when any exist in the input data.
- [ ] All new/updated tests pass; existing `test_done_checker_static.py`,
      `test_generate_registry.py`-adjacent monitoring test suites show no regressions.

## Related Tickets
- TCK-20260706-TAG-REGISTRY-DATA (the feature whose troubleshooting need motivated this ticket)
- TCK-20260705-GATE-DET-DONE-CHECKER (built `done_checker_static.py` and its checklist shape this
  ticket reuses)

## Related Docs
- docs/agent-monitoring/schema.md
- docs/guides/agent_monitoring.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- .claude/workflows/implement-ticket.js (Verify phase, `pushEvent` definition)
- tools/agent-monitoring/generate_retro.py

## Assumptions / Open Questions
- Assumed the tag-registry-rejection substring (`"is not in the tag registry"`) is stable enough
  to match against — it's defined once in `tools/tag_registry.py`'s `_check_tags`-facing error
  message (via `validate_frontmatter.py`'s `_check_tags`) and not duplicated elsewhere, so a
  wording change there would need this classifier updated too; documented as a coupling, not
  hidden.
- This ticket cannot be exercised end-to-end via `implement-ticket` on itself (same
  bootstrapping limitation noted in `TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER`'s
  self-reference note) — verified via the pure-function unit tests plus manual trace of the JS
  call-site wiring instead.

## Implementation Notes
Implemented per plan.md with one deliberate deviation from the original design, discovered during
implementation (not assumed upfront):

1. **`tools/gate_checks/done_checker_static.py`**: added `classify_checklist_failure(checklist)` —
   pure function, scans for the first `FAIL` entry, returns `"tag_registry_rejection"` if its
   `evidence` contains `"is not in the tag registry"`, else `"dod_condition_failed"`, else `None`.
2. **Deviation from plan.md's original design:** the plan called for invoking this Python function
   from `implement-ticket.js` via `bash()` (mirroring the Architecture-Verify precedent). While
   implementing, re-reading the existing `p0ScanOutput` bash-call code in that same file surfaced
   an explicit, already-documented warning: embedding a JSON blob directly into a
   `python3 -c "..."` string corrupts the script when the JSON's own quotes collide with the
   shell's, causing the check to "silently fail open." `doneCheck.checklist`'s `evidence` strings
   are exactly this kind of unsafe payload — they can contain quotes and backticks (copied
   verbatim from `validate_frontmatter.py`'s own error messages, which themselves quote tag names
   and a full backtick-wrapped shell command). Rather than risk that same failure mode (or
   introduce an unprecedented heredoc/base64 pattern into this file with no existing example to
   validate against), the fix is a small (~10-line) JS mirror of the exact same logic,
   `classifyChecklistFailure`, invoked directly with no subprocess. The Python function remains as
   the tested reference implementation (5 pytest cases) the JS mirror must match, and stays
   directly reusable by any future offline tooling. Both copies are commented to note they must be
   kept in sync by hand — the same accepted tradeoff already precedented in this repo
   (`tag_taxonomy.md`'s `registry_query.py` `SEED_TAGS` note).
3. **`.claude/workflows/implement-ticket.js`**: `pushEvent` gained an optional 7th `reasonCode`
   param (defaults to `null`, included as `reason_code`); only the `Verify`/`failed` call site
   passes one (via the new `classifyChecklistFailure`). All 11 other `pushEvent` call sites
   untouched — confirmed via grep that none needed a new reason code (every other gate status
   already disambiguates 1:1 via `phase`/`final_status`). Verified `node --check` passes on the
   edited file (no local JS test harness exists in this repo for workflow scripts — disclosed, not
   hidden).
4. **`docs/agent-monitoring/schema.md`**: documented the new field, its nullability, and the 2
   known values, with an explicit "why only Verify" rationale and a "not a closed enum" note.
5. **`tools/agent-monitoring/generate_retro.py`**: added a "DOD_BLOCKED Reason Codes" section,
   rendered only when at least one event carries a non-null `reason_code` (confirmed via a live
   `--all` run against the real 502-run/2130-event corpus: report generated successfully, section
   correctly omitted since no run has exercised the new code path yet).

## Test Summary
- `pytest tests/tools/test_done_checker_static.py tests/tools/test_done_checker_audit.py -v` →
  42 passed (5 new `classify_checklist_failure` tests + 37 pre-existing, all passing).
- New `tests/tools/test_generate_retro.py` (first test file for this previously-untested script,
  scoped only to the changed behavior) → 3 passed.
- Full `pytest tests/tools/ -q --ignore=tests/tools/test_knowledge_search.py` → 487 passed, 2
  failed (the same 2 pre-existing, unrelated `test_search_mcp.py` failures disclosed in this
  session's earlier tickets — confirmed via `git stash` in that earlier work, not re-verified here
  since nothing in this ticket touches `.mcp.json`/`search_mcp.py`).
- `node --check .claude/workflows/implement-ticket.js` → syntax OK.
- `python3 tools/agent-monitoring/generate_retro.py --all` → ran cleanly against the live
  502-run/2130-event corpus; new section correctly absent (no `reason_code` data exists yet, since
  no run has gone through the Verify phase since this ticket landed).

## Files Changed
- `tools/gate_checks/done_checker_static.py` (new `classify_checklist_failure` function)
- `.claude/workflows/implement-ticket.js` (`pushEvent` gains `reason_code`; new
  `classifyChecklistFailure` helper; Verify-phase failure call site wired)
- `docs/agent-monitoring/schema.md` (new field documented)
- `tools/agent-monitoring/generate_retro.py` (new reason-code aggregation section)
- `tests/tools/test_done_checker_static.py` (5 new tests)
- `tests/tools/test_generate_retro.py` (new, 3 tests)
- `agent-monitoring/retro/RETRO-ALL.md`, `agent-monitoring/retro/index.md` (regenerated by the
  manual verification run — real tool output, not test residue)
- `tickets/inprogress/TCK-20260706-MONITORING-REASON-CODE.md` → `tickets/done/...`
- `staging_artifacts/TCK-20260706-MONITORING-REASON-CODE/` → `stored_artifacts/...`

## Completion Summary
Extended `agent-monitoring/events.jsonl` with an optional `reason_code` field to close the one
concrete trace gap found while evaluating whether the tag-registry/skill-suggestion features would
be troubleshootable after a few days of runs: `DOD_BLOCKED` was the sole gate status collapsing
multiple distinct DoD causes into one value (every other gate status already disambiguates 1:1 via
`phase`/`final_status`). A new pure, tested Python classifier
(`classify_checklist_failure`) defines the intended behavior; a hand-synced JS mirror
(`classifyChecklistFailure`) is what `implement-ticket.js` actually calls, after discovering
mid-implementation that piping the checklist's arbitrary evidence text through `bash()` would risk
the exact shell-quote-corruption failure mode this same file already warns about elsewhere — a
real design correction made during implementation, not assumed at planning time.
`generate_retro.py` now surfaces a reason-code breakdown when present, so the field is actually
consumed by the tool meant to answer "how did the last few days go," not just written and left
unread. No other phase's events were touched — confirmed, not assumed, that no other gate status
has this same catch-all problem today. Explicitly deferred: retrofitting `reason_code` elsewhere,
and tracking whether tag-based skill suggestions are actually acted on (a separate, bigger
question, raised but not decided in the prior exploratory discussion).
