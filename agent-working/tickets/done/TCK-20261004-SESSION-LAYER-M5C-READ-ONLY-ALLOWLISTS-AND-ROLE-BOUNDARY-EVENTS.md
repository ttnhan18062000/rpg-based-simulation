---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS

## Title
Session-layer M5c: read-only role allowlists and advisory `role_boundary` events

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Use the free hard boundary (a `--agent` tool allowlist makes pure review roles read-only, verified M0b: it applies to the main session and persists across resume) and add the advisory semantic boundaries: warn and log a `role_boundary` monitoring event, never block.

Child of `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY`. **Hold rule: do not activate before M2a-M2b are merged** (this ticket consumes the binding record and role-state directory) and M0 results (done). Every `settings.json` or hook edit needs the owner's confirmation of the literal diff, and a settings-shape test search first (grep `tests/` for the pinned hook shape).

## Scope
- Decide which roles are pure review (candidate: seats whose function is reviewer only, per the manifest); set their `tools` allowlist in `registries/session_roles.yaml` and regenerate `session-<role>.md` (M1c). Check that the allowlist still lets them read and message.
- `role_boundary` event: emitted (advisory) by the M5b hook path or a separate PostToolUse/UserPromptSubmit helper when a role edits a path outside its `owns` (per `route.py`, M3a) or sends a dispatch-class message from a role not in the receiver's `accepts_dispatch_from`. Event carries role, session id, class, path or target, never message content. Writes via the existing monitoring recorder; write failure never fails anything.
- Warn text goes to the session once per path class per session (no spam).
- Retire criteria recorded in the ticket: harden only what recurs after a measured window (target four weeks of retro data); hardening is its own ticket (M7).

## Out of Scope
- Any deny or ask on semantic boundaries; hardening decisions (M7); new vocabulary for the `agent` field (`role_boundary` events use their own field set, never `agent`).

## Acceptance Criteria
1. Allowlisted roles cannot Edit or Write (probe with a positive control that an unlisted role can); they can still Read and SendMessage.
2. An edit outside `owns` produces exactly one advisory warning and one event per path class per session; an edit inside `owns` produces none.
3. The event validates against the monitoring schema and does not touch the `vocabulary_drift` ratchet (test).
4. Event write failure is swallowed (fault-injection test).
5. Owner confirmed the literal diff for any `settings.json` or hook edit; scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY` (parent), M2b, M3a, M5b; feeds M6a and M7

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 9.0, 10, 11, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0n: exit 2 or JSON deny blocks; exit 1 and unparseable output fail open)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Related Code Areas
- `registries/session_roles.yaml` (`tools`), `.claude/agents/session-*.md` (generated), `tools/sessions/`, monitoring recorder, tests.

## Assumptions / Open Questions
- Which seats are pure review is an owner decision. Every seat today has a `may_write` grant, so no seat qualifies and no allowlist is set; the mechanism is verified (M0b) and rendered by the generator. Open question for the owner: should any review-only seat exist? Proceeded with the events regardless.

## Implementation Notes
Drafted by `agent-working-design` 2026-10-04; activated and implemented by `agent-working-implementer` 2026-10-05. Retire criteria: harden only what recurs after a measured window (M7, four weeks after M6a).

## Test Summary
`tests/tools/test_session_boundary.py` (new) plus `test_session_guard.py`, `test_settings_json_hooks_wiring.py` pass (74); the session, claim, write-path, monitoring and schema tool suites pass (692 passed, 3 skipped). Covered: edit inside, outside, unowned, split and outside-worktree paths; the `may_write: ["**"]` non-exemption; message-class mismatch with accepted and unaccepted senders; one warning and one event per path class per session; event field set with no `agent`; own file so the `events` vocabulary ratchet never sees it; swallowed event-write and state-write failures; through the guard, only `additionalContext` and never a permission decision, authority decisions unchanged. Not run: a live fresh-session probe of the hook (settings take effect only in a fresh session) and of a real allowlisted seat (none exists).

## Files Changed
- tools/sessions/boundary.py
- tools/sessions/guard.py
- tests/tools/test_session_boundary.py
- tests/tools/test_session_guard.py
- .claude/settings.json
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/session_layer_working_process.md

## Completion Summary
Advisory `role_boundary` events are implemented: an edit that crosses another domain's claim and a dispatch-class message to a role that does not accept the sender each warn once per session and log one event to `role_boundary.jsonl`, never denying. The guard matcher gained `SendMessage` (owner confirmed the literal diff). Part (b): M0b verified that a `--agent` tool allowlist applies to the main session and the generator already renders it, but every seat has a `may_write` grant so none is set; whether a review-only seat should exist is an owner decision. Of the four plan-named boundary types, wrong-owner and neighbouring-domain editing are one `edit_outside_owns` kind (routed paths included), message-class is `message_class_mismatch`; "unusual route" and handoff formatting are not separate events and stay for the measured window.
