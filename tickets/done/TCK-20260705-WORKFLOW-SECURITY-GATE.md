---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-WORKFLOW-SECURITY-GATE
phase: done
date: 2026-07-05
tags: [tagging, security, workflows]
---

# TCK-20260705-WORKFLOW-SECURITY-GATE

## Title
Add a mandatory security-review gate for security-tagged tickets in implement-ticket.js

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION` (done) found that a ticket's `suggested_skills` value
(computed from `Process/Skill-signal` tags) is purely advisory today — logged in `implement-ticket.js`'s
Scope phase but never consumed by any later phase. It recommended, as a "build now" candidate, turning
the `security` tag's suggestion (`/security-review`) into a mandatory hard gate before Verify, rather
than leaving it as an easily-ignored log line — since security-relevant changes are exactly the case
where "advisory only" is the weakest guarantee.

## Scope
- Add a new gated phase to `.claude/workflows/implement-ticket.js`, inserted between Test/Parity and
  Verify, that fires **only** when `ticketInfo.suggested_skills.includes('/security-review')` (a field
  already on `TICKET_SCHEMA` since `TCK-20260705-TAG-SKILL-SUGGEST` — no new schema field needed for the
  trigger itself).
- Follow the exact structural pattern of the existing Review gate (`implement-ticket.js` lines ~319-388):
  a schema with a `verdict` enum, `pushEvent(...)`, early-return on fail with a distinct return status
  (not reusing `NEEDS_CHANGES`/`BLOCKED` — those belong to architecture-review).
- Name the new phase and its return status distinctly for monitoring/retro purposes (per this session's
  own investigation): e.g. phase `Security-Review`, agent `security-reviewer` (or reuse an existing
  agent identifier if Investigate finds a cleaner fit — see Assumptions below), failure status e.g.
  `SECURITY_BLOCKED` — never overload the existing `Review`/`NEEDS_CHANGES` names, or the two gates'
  stats will merge in `agent-monitoring/events.jsonl` and become indistinguishable in retro reports.
- A ticket with **no** `security` tag must see **zero** added latency, agent calls, or log/event
  entries — the gate must be provably inert for the non-triggering case.
- Log a visible `WARNING` (not a silent pass-through) when a ticket's `Related Code Areas` suggests
  auth/secrets/credential-adjacent paths but no `security` tag was assigned — surfacing the mis-tag risk
  rather than hiding it (per investigation's explicit recommendation).
- Update `docs/ai/workflows.md`, `docs/ai/system_overview.md` (Section 3's phase table), and
  `docs/ai/ticket-lifecycle.md` in the same session to reflect the new phase/gate — do not let this
  ticket widen the existing doc/code drift `system_overview.md` already discloses.

## Out of Scope
- Any change to the tag→skill mapping itself, or to any of the other 3 mapped tags
  (`api-design`/`debugging`/`performance`) — this ticket only builds the `security` gate.
- Auto-invoking any OTHER suggested skill (that's the separate, explicitly-**deferred** Candidate 1 from
  the investigation — do not fold it into this ticket).
- Changes to `implement-epic.js` — it delegates entirely to `implement-ticket.js` per child ticket
  (confirmed by investigation), so this gate applies epic-wide automatically with zero additional
  plumbing; do not duplicate logic there.
- Changes to `create-tickets.js`'s Structure phase or `ticket-scoper.md`'s Output contract — the
  `security` tag/skill mapping there is unchanged; this ticket only adds a consumer of the value they
  already produce.

## Acceptance Criteria
- [ ] A `security`-tagged ticket whose implementation introduces a real vulnerability → the new gate
      fires, returns a distinct structured failure status, and does NOT proceed to Verify/Finalize.
- [ ] A `security`-tagged ticket with clean code → the gate passes, run proceeds to Verify unchanged
      from today's flow (same `DONE` shape, same `stored_artifacts/` migration, same working_log row).
- [ ] A ticket with no `security` tag → zero added latency, zero added agent calls, zero new phase
      events (diff `events.jsonl` seq count before/after for an identical non-security ticket — must be
      byte-identical).
- [ ] `agent-monitoring/events.jsonl` gets a distinctly-named phase entry for the new gate, separable
      from the existing `Review` (architecture) phase in retro reports.
- [ ] A ticket whose `Related Code Areas` suggests auth/secrets/credential paths but has no `security`
      tag produces a visible `WARNING` log line (not a silent pass-through).
- [ ] `docs/ai/workflows.md`, `docs/ai/system_overview.md`, and `docs/ai/ticket-lifecycle.md` are updated
      to reflect the new phase/gate in the same session.

## Related Tickets
- TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION (recommended this as "build now", Candidate 2)
- TCK-20260705-TAG-SKILL-SUGGEST (shipped the `suggested_skills` field this gate's trigger reuses)
- TCK-20260705-WORKFLOW-PARITY-SKIP (sibling ticket, same investigation, independent — no shared code path)

## Related Docs
- stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md (Candidate 2's full
  trigger/change/feasibility/risk assessment)
- docs/ai/workflows.md, docs/ai/system_overview.md, docs/ai/ticket-lifecycle.md (index targets)
- docs/ai/README.md (Design Principles — "Hard gates", to validate the new gate's design against)

## Related Stored Artifacts
None yet — staging artifacts to be created under
`staging_artifacts/TCK-20260705-WORKFLOW-SECURITY-GATE/` when implementation begins.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- .claude/agents/architecture-reviewer.md (reference — the gate pattern to mirror)
- docs/ai/workflows.md
- docs/ai/system_overview.md
- docs/ai/ticket-lifecycle.md

## Assumptions / Open Questions
- Whether the new gate needs a dedicated new `.claude/agents/security-reviewer.md` role file (mirroring
  `architecture-reviewer.md`'s pattern exactly), or can be implemented as an inline agent-call prompt
  within `implement-ticket.js` referencing the existing built-in `/security-review` skill's guidance
  without a new agent file — left for Investigate/Plan to decide with evidence, not assumed here.
- Whether the mis-tag `WARNING` heuristic (matching `Related Code Areas` against an auth/secrets/
  credential keyword list) should reuse `tools/registry_query.py`'s seed-vocabulary substring-match
  pattern or needs its own small keyword list — left for Plan.

## Implementation Notes
- Created `.claude/agents/security-reviewer.md`, mirroring `architecture-reviewer.md`'s structure
  (Registry Lookup → checklist → Output). Checklist covers injection, unsafe deserialization, path
  traversal, subprocess/command injection, secrets-in-code, and raw-domain-model API exposure — the
  last item cross-references `architecture-reviewer.md`'s API-boundary rule by name instead of
  duplicating it. Output verdict enum (`APPROVED`/`NEEDS_CHANGES`/`BLOCKED`) matches
  `SECURITY_REVIEW_SCHEMA` exactly.
- Added `meta.phases` row for `Security-Review` in `.claude/workflows/implement-ticket.js` (after
  `Parity`, before `Verify`). Left the top-of-file `description` string unchanged — it is already a
  short summary, not an exhaustive phase enumeration.
- Added the conditional Security-Review gate to `implement-ticket.js`, inserted structurally between
  Parity's `pushEvent` and `phase('Verify')`, **outside** the `if (tier !== 'hotfix')` block so it fires
  for hotfix/standard/epic-child tickets alike. Trigger condition:
  `(ticketInfo.tags && ticketInfo.tags.includes('security')) || (ticketInfo.suggested_skills &&
  ticketInfo.suggested_skills.includes('/security-review'))` — `tags` (required, ground truth) is
  checked first, with `suggested_skills` (derived, optional) as a secondary/redundant check, per
  architecture-review finding #6. On `NEEDS_CHANGES`/`BLOCKED`, the workflow returns `SECURITY_BLOCKED`
  and does not proceed to Verify/Finalize. No `else` branch exists on the gate's `if`.
- Promoted `tags` to a **required** field on `TICKET_SCHEMA` (was absent entirely before). Added
  optional `mistag_warning: boolean` to the same schema, with a code comment noting it is a 4th place
  in this file independently computing tag-related logic (alongside the existing triple-copy
  `suggested_skills` mapping) and that it is NOT mirrored in `ticket-scoper.md` (out of scope for this
  ticket to touch that file).
- Computed `tags` and `mistag_warning` inline in **both** Scope-phase prompt branches:
  - "Load existing ticket" branch: Step 3a reads the ticket's frontmatter `tags` verbatim; Step 3b
    checks `Related Code Areas` against the keyword list (`credential`, `secret`, `password`,
    `api_key`, `private_key`, `.env`, `oauth`, `jwt` — deliberately excluding bare `auth`, `cert`,
    `key`, `token`, `session` to avoid colliding with this codebase's `AuthoritativeState`/
    `authoritative_pipeline`/`certification`/`LabSessionStore` vocabulary).
  - "Create new ticket" branch: identical keyword list and logic added inline (Step 8) — computed by
    `implement-ticket.js`'s own prompt text against the just-drafted ticket, not delegated to
    `ticket-scoper.md`.
  - `mistag_warning` is surfaced via `log(...)` only (never `pushEvent`) at the Scope phase, right
    after the existing `suggested_skills` log block — zero added monitoring events for the
    non-triggering case.
- Updated `docs/ai/workflows.md` (Phases table + Return values table), `docs/ai/system_overview.md`
  (Section 3's phase-count prose, describing Security-Review as "a 10th, conditional phase", plus the
  gate/return-status vocabulary list), and `docs/ai/ticket-lifecycle.md` (Overview ASCII diagram, new
  `### Security-Review` subsection between Parity and Verify, Failure Recovery Reference table). Ran
  `make knowledge-index-update` after the doc edits (6 files re-embedded).
- Did not touch `.claude/agents/ticket-scoper.md`, `.claude/workflows/create-tickets.js`,
  `.claude/workflows/implement-epic.js`, or `tools/registry_query.py` — all confirmed untouched via
  `git diff --stat`.
- One minor wording deviation from the plan recorded in `staging_artifacts/.../plan.md`'s new
  Deviations section: the "Create new ticket" branch's Return-line text uses `false if none` for
  `mistag_warning` instead of the plan's literal `[] if none`, since the field is schema-typed boolean.

## Test Summary
Manual verification pass (Step 5 of plan.md / test_plan.md) — no automated test harness exists for
`.claude/workflows/*.js` (confirmed zero hits searching `tests/`/`tools/` for `implement-ticket` or
`workflows/*.js`; precedent: `TCK-20260607-MON-CAPTURE`'s Test Summary).

1. `node -c .claude/workflows/implement-ticket.js` → exit 0. **PASS**
2. Grep-verified the new gate's `if` block: `phase('Security-Review')`, `agent(...)`, and both
   `pushEvent(...)` calls are the only reachable code inside it; the block sits between line 571
   (Parity's `pushEvent`) and `phase('Verify')` (line 633). Trigger checks `ticketInfo.tags.includes
   ('security')` OR `ticketInfo.suggested_skills.includes('/security-review')` — both halves present.
   **PASS**
3. Grepped for an `else` on the new `if` — none found (the only `} else {` in the file, at line 421, is
   the pre-existing hotfix-tier branch, unrelated). Grepped for any `pushEvent` referencing
   `mistag_warning` — none found. **PASS**
4. `grep -n "status: '"` and `grep -n "pushEvent('"` across the whole file — `SECURITY_BLOCKED` and
   `'Security-Review'` do not collide with any of the file's other 7 status values or 9 phase labels.
   **PASS**
5. Mis-tag WARNING heuristic checked against the keyword-match logic: positive control
   (`src/api/auth/credentials.py`, no `security` tag) → fires; negative controls
   (`src/engine/authoritative_pipeline.md`, `src/certification/harness.py`) → do not fire; security tag
   present suppresses the warning even on a matching path. **PASS** (4/4 cases correct)
6. `make knowledge-index-update` run after Step 4's doc edits — completed (6 files re-embedded, 1883
   from cache, 0 deleted). **PASS**
7. `python3 -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_registry_query.py -v`
   → 67 passed, 0 failed. **PASS** (confirms `tools/registry_query.py` untouched and doc frontmatter
   intact)

All 7 checks: **PASS**.

## Files Changed
- `.claude/agents/security-reviewer.md` (new)
- `.claude/workflows/implement-ticket.js`
- `docs/ai/workflows.md`
- `docs/ai/system_overview.md`
- `docs/ai/ticket-lifecycle.md`

## Completion Summary
Added a mandatory Security-Review gate to `implement-ticket.js`, firing when a ticket's frontmatter
`tags` include `security` (required, ground-truth) or its derived `suggested_skills` includes
`/security-review` — a new `.claude/agents/security-reviewer.md` reviews the actual implemented diff
for injection, unsafe deserialization, path traversal, subprocess/command injection, secrets-in-code,
and raw-domain-model API exposure, returning `SECURITY_BLOCKED` on failure before Verify/Finalize can
run. A non-triggering ticket sees zero added latency, agent calls, or monitoring events. Also added a
`mistag_warning` heuristic (log-only, never a monitoring event) that flags when a ticket's Related Code
Areas suggests auth/secrets/credential paths but no `security` tag was assigned, using a
collision-safe keyword list that deliberately excludes `auth`/`cert`/`key`/`token`/`session` (all of
which collide catastrophically with this codebase's own `AuthoritativeState`/`certification`/
`LabSessionStore` vocabulary, confirmed via direct grep before finalizing the list).

The plan went through 4 architecture-review rounds before approval: the first caught that the gate's
original trigger depended solely on the optional, LLM-derived `suggested_skills` field with no
deterministic backstop — undermining the ticket's own "mandatory not advisory" goal — fixed by
promoting `tags` to a required schema field and using it as the primary ground-truth half of the
trigger condition. The next two rounds caught a resulting sweep of 7 stale prose locations still
describing the old single-condition trigger, and then a template-literal escaping regression
introduced while fixing that prose. All three were caught and corrected before implementation began.

Updated `docs/ai/workflows.md`, `docs/ai/system_overview.md`, and `docs/ai/ticket-lifecycle.md` to
document the new gate consistently with the dual-trigger design. No `src/` code, simulation behavior,
or parity ledger entry was touched — this is pure agent-tooling/workflow-orchestration change, applying
to every future ticket that runs through `implement-ticket`/`implement-epic` from this point forward.
