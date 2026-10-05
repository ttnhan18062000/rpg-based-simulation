---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT

## Title
Session-layer M6a: `session_role` on monitoring records, headline-metric categories and the batch-latency triplet

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The minimum measurement M7's review needs: resolved `session_role` on monitoring runs and events (separate from `agent`), the headline metric (manual orchestration actions per completed batch, by category), and three batch latencies derived from existing PR and ticket artifacts.

Child of `TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW`. **Hold rule: do not activate before M2a-M2b are merged** (this ticket consumes the binding record and role-state directory) and M0 results (done). Every `settings.json` or hook edit needs the owner's confirmation of the literal diff, and a settings-shape test search first (grep `tests/` for the pinned hook shape).

## Scope
- `session_role` field on monitoring runs and events, read from the per-session binding record (M2b) via the per-session `current_run.<session_id>` sidecar, never the shared sidecar (cross-session contamination ticket); value `unresolved` when no binding exists. Schema doc updated; the field never shares `agent`.
- Headline metric: categories role reminder, routing correction, manual wake, worktree correction, boundary reminder, handover recovery. Tagging method decided from M0j (the prompt-submit hook payload): sample from `UserPromptSubmit`, or fall back to a one-line owner-side tally per batch recorded in the retro. Genuine owner decisions, design feedback and new requirements are not counted.
- Batch latency: implementation latency (dispatch to PR green), finalization latency (PR green to finalized), cycle time (dispatch to finalized), derived from PR, ticket and monitoring artifacts with no batch registry. A reporter in the retro tooling prints the three numbers and states what an unavailable timestamp means (`unknown`, never zero).
- Add the measures to the existing retro report; no new report.

## Out of Scope
- Analytics beyond the headline metric and latencies (M6b), the roster check (M6b), any change to the `agent` vocabulary or its ratchet.

## Acceptance Criteria
1. A monitoring event written in a bound session carries the right `session_role`; in an unbound session it carries `unresolved`; two concurrent sessions never swap roles (test with two sidecars).
2. Schema validation and the `vocabulary_drift` ratchet are unaffected (existing tests green).
3. The tagging method is chosen and recorded with its evidence; a fixture batch produces category counts that exclude decisions and requirements.
4. The latency reporter handles a missing timestamp as `unknown` and reproduces a hand-computed value for one real finished batch (cited).
5. Scoped tests green; docs, schema doc and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW` (parent), M2b (binding), M5 (events), M7 consumes this

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 9.0, 10, 11, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0n: exit 2 or JSON deny blocks; exit 1 and unparseable output fail open)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Related Code Areas
- monitoring recorders under `tools/agent-monitoring/`, schema docs under `docs/agent-monitoring/`, retro tooling, tests.

## Assumptions / Open Questions
- Data from a first four weeks only becomes useful after M2 ships; this ticket can land the field early so data accumulates.

## Implementation Notes
Drafted by `agent-working-design` 2026-10-04; activated and implemented by `agent-working-implementer` 2026-10-05. M6b and M7 are not started (M7 is time-gated four weeks after this).

## Test Summary
`tests/tools/test_session_layer_measures.py` (new, 39) passes with the settings-wiring, session-guard and session-boundary suites. Covered: two concurrent sessions never swap `session_role`; an unbound session or no session id is `unresolved`; the shared `current_run` is never read; `record_run.py` and `record_events.py` write `session_role` and leave `agent` and validation unchanged; the tagger fixture (ten repeated-instruction prompts tagged, decisions, feedback, questions, requirements and long prompts untagged) and the category counts; the hook records no prompt text and never raises; the tally is validated; latency reproduces the hand-computed value for merged PR 346 (implementation 2506 s, finalization 187 s, cycle 2693 s) and is `unknown` for a missing timestamp, unmerged PR, red or unfinished check or negative span; the retro section renders and is omitted unless supplied; the wired hook passes outside a repo and with the script missing. Not run: a live fresh-session probe of the new `UserPromptSubmit` hook (settings take effect in a fresh session).

## Files Changed
- tools/agent-monitoring/session_role.py
- tools/agent-monitoring/manual_actions.py
- tools/agent-monitoring/batch_latency.py
- tools/agent-monitoring/session_layer_report.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- tools/agent-monitoring/generate_retro.py
- .claude/settings.json
- docs/agent-monitoring/schema.md
- tests/tools/test_session_layer_measures.py

## Completion Summary
`session_role` (resolved by session id from the binding record, `unresolved` otherwise, separate from `agent`) is stamped on runs and events. Tagging method chosen from M0j (`UserPromptSubmit` carries the prompt): a conservative phrase sampler wired as a new `UserPromptSubmit` hook (owner confirmed the literal diff; records category only, never the prompt) plus an owner-side `tally` command as the authoritative channel. The three batch latencies are derived on demand from PR data with no registry and `unknown` for anything unavailable; reproduced by hand for PR 346. The retro report gained one `Session-Layer Measures` section. Limits stated: dispatch is proxied by the batch's first commit unless given (the dispatch message leaves no repo artifact); finalization is merge, because closing the ticket happens inside the PR; the sampler under-counts by design; `tools` rows are not stamped; the secondary retro measures (misroutes, bounces, idle stall, `/clear` count) are not part of this ticket.
