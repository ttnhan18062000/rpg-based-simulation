---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION
artifact_type: test_plan
tags: [investigation, ai, workflows, tagging]
---

# Test Plan — TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION

This ticket implements no code — it produces recommendations only (see `investigation.md`). This
document is therefore forward-looking: a verification checklist for whichever candidate tuning(s) a
future implementation ticket actually builds, keyed to the 4 candidates assessed in `investigation.md`'s
Risks and Open Questions section.

## Regression Surface (existing behavior that must not break)

Any future tuning ticket touching `.claude/workflows/implement-ticket.js` or `implement-epic.js` must
re-verify, at minimum:

- A `hotfix`-tier ticket still skips Investigate/Plan/Review exactly as today (`tier === 'epic'` and
  `tier !== 'hotfix'` branches at `implement-ticket.js:218` and `:242` must remain unchanged in shape).
- A ticket with **zero** `Process/Skill-signal` tags still produces `suggested_skills: []` and zero
  extra phases/gates/log lines — the no-tag path must be provably identical to current behavior.
- `implement-epic.js`'s batch loop still stops on the first non-`DONE` child result and still reports
  `results`/`stopped_at`/`remaining` correctly — no new tuning should change this orchestration contract.
- `agent-monitoring/events.jsonl` and `runs.jsonl` still get a write attempt for every run, including
  when a new gate/skip fires (CLAUDE.md Hard Rule: monitoring write is mandatory, failure non-fatal).

## New Tests Required (per candidate, if built)

### Candidate 2 — mandatory `/security-review` gate for `security`-tagged tickets

- A `security`-tagged ticket whose implementation introduces a real vulnerability → the new gate fires,
  the run returns a structured failure status (mirroring `NEEDS_CHANGES`/`BLOCKED`'s shape), and the
  ticket does NOT proceed to Verify/Finalize.
- A `security`-tagged ticket with clean code → the gate passes, and the run proceeds to Verify unchanged
  from today's flow (same final `DONE` shape, same `stored_artifacts/` migration, same working_log row).
- A ticket with **no** `security` tag → zero added latency, zero added agent calls, zero new phase
  events — prove the gate is fully inert for the non-triggering case (diff `events.jsonl` seq count
  before/after the tuning for an identical non-security ticket).
- `agent-monitoring/events.jsonl` gets a distinctly-named phase entry (e.g. `Security-Review`) for the
  new gate so retro reports (`/agent-monitoring-retro`) can distinguish it from the existing `Review`
  (architecture) phase.
- `docs/ai/workflows.md`, `docs/ai/system_overview.md` (Section 3 phase table), and
  `docs/ai/ticket-lifecycle.md` are updated in the same session to reflect the new phase — verify via a
  grep/diff that the phase count and gate vocabulary (`CONFLICTS_DETECTED`, `NEEDS_CHANGES`, ...) in
  those docs match the new `.js` file exactly, closing rather than widening the doc/code drift
  `system_overview.md` Section 6 already flags.

### Candidate 3 — skip Parity when `implementation.files_changed` has no `src/` paths and `behavior_changed` is false

- A genuinely docs-only ticket (`files_changed` = only `docs/*.md`/`tickets/*.md`,
  `behavior_changed: false`) → Parity's `agent()` call is skipped entirely; a `pushEvent(..., 'skipped',
  ...)` is recorded; `events.jsonl` reflects a `skipped` status for the Parity phase seq.
- A **scope-drift** case — a ticket originally scoped as docs-only (Related Code Areas has no `src/`
  entries) whose Implement phase actually DOES touch `src/` (i.e. `files_changed` includes a `src/`
  path even though Related Code Areas didn't predict it) → Parity must still run fully. This is the
  single most important regression test: it directly verifies the gate reads `implementation.files_changed`
  (post-Implement, authoritative) and never `Related Code Areas` (pre-Implement guess), per
  `investigation.md`'s explicit safety condition.
- A ticket where `files_changed` has no `src/` paths but `implementation.behavior_changed` is
  (surprisingly) `true` — e.g. a config/data file change with real behavioral effect — must NOT skip
  Parity; the two signals must both agree before skipping (logical AND of "no src/ path" and "no
  behavior_changed"), not either alone.
- No P0 parity ledger entry ever goes stale as a result of a skip — add an explicit check (or assert in
  the test) that none of the changed files intersects any P0 entry's `v2_evidence` path before allowing
  the skip to fire.

### Candidate 4 — Test-phase skip for docs-only tickets

**Reject as stated per `investigation.md`** — do not build the general "no `src/` ⇒ skip Test" form.
If a narrower `files_changed.length === 0` variant is ever proposed instead, its test plan must include:
- A regression test using the exact `files_changed` list from `tickets/done/TCK-20260705-AI-AGENT-OVERVIEW-DOC.md`
  (a real docs-only ticket that legitimately required and passed a `tests/tools/test_validate_frontmatter.py`
  run) to prove that ticket's Test phase is **not** caught by the narrower skip predicate — i.e. the
  regression test must fail loudly if someone widens the predicate back to "no `src/`" instead of "zero
  files changed".

### Candidate 1 — auto-invoke suggested skill during Implement

Deferred per `investigation.md` — no test plan authored until a JS-callable skill-invocation primitive
exists. When that groundwork lands, the test plan must at minimum cover:
- A `performance`-tagged ticket's Implement phase output includes evidence the suggested skill's
  guidance was actually applied (not just referenced) — e.g. profiling data or a documented
  before/after benchmark in `implementation_summary`.
- The architecture-reviewer's `plan.md` review, for a ticket that will trigger auto-invocation, explicitly
  lists the auto-invoked step as part of the approved plan — closing the "gate never saw the expanded
  scope" gap identified in `investigation.md`'s Candidate 1 risk assessment.
- Token/tool-call cost delta (via `agent-monitoring/tools.jsonl` `tool_call_count`) is measured for a
  matched pair of tagged vs. untagged tickets of otherwise similar scope, to make the auto-invoke's real
  cost visible before deciding whether to keep it on by default.

## Scoped Pytest Commands (for whichever candidate is implemented)

There is no Python test suite for `.claude/workflows/*.js` or `.claude/agents/*.md` today (these are
prompt-orchestration files, not `src/`-testable Python). A future implementation ticket's test plan
should instead rely on:
- Manual/scripted dry-runs of `implement-ticket` against a throwaway ticket fixture (one per triggering
  condition: security-tagged, docs-only, scope-drift, no-tag baseline).
- `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` if the tuning adds any new frontmatter
  field (e.g. exposing raw `tags` on `TICKET_SCHEMA` the way `suggested_skills` was added) — run this to
  confirm no accidental frontmatter-schema regression.
- `tools/agent-monitoring/validate.py` to confirm working-log/run-record correspondence still holds after
  any new phase or skip is introduced.

## Anti-Drift Test Guards

- Any new gate/skip must be provably **inert** for tickets that don't match its trigger — the standard
  regression check for every candidate above is "diff the full `events.jsonl` sequence for an identical
  non-triggering ticket before and after the change; it must be byte-identical."
- Any new skip (Candidates 3/4) must always be tested against the **scope-drift** case (Scope-time guess
  disagreeing with Implement-time reality) — this is the single hazard `investigation.md` calls out
  repeatedly, and it is the one test case a future implementer is most likely to skip under time pressure.
- Any new gate (Candidate 2) must be tested for **both** directions of tag-assignment error (false
  positive: gate fires needlessly on a non-security ticket someone mistagged; false negative: gate never
  fires on a security-relevant ticket that was never tagged) — and the false-negative case must produce a
  visible `WARNING` per `investigation.md`'s recommendation, not a silent pass-through.
