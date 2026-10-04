---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1C-GENERATED-SESSION-AGENT-FILES
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M1C-GENERATED-SESSION-AGENT-FILES

## Title
Session-layer M1c: generate `session-<role>.md` agent files, with a roster-spawn probe and a drift check

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Generate `.claude/agents/session-<role>.md` from the manifest and templates, add a drift check to the validator, and resolve the M0d finding that these files enter every plain session's Agent-tool roster.

Child of `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (milestone M1). Hold rule met: M-1 merged (#289) and M0 recorded ADJUST (#307).

## Scope
- Generator `tools/sessions/generate_agents.py` (deterministic: same manifest gives byte-identical files).
- Each file carries a description that says launcher-only, never spawn; the tool allowlist for read-only roles (the free hard boundary of plan section 10).
- Drift check in the M1a validator: regeneration differs from the committed files -> fail.
- Probe (recorded as `.jsonl` evidence): in a plain `claude -p` session in a scratch repo carrying the generated files, give a task a roster agent could plausibly take and show the model does not spawn a `session-*` agent; positive control: an agent with an inviting description does get spawned. If the probe fails, move generation to a location or inline definition that stays out of the roster and record why.
- Decide and record the location (M0d allowed a separate directory).

## Out of Scope
- Launcher (M2), `settings.json` or hook changes, role-conditional hooks (M5).

## Acceptance Criteria
1. Generator is deterministic (test: run twice, identical bytes) and produces nine files, or the recorded alternative location.
2. Drift check fails on a hand-edited generated file (fixture) and passes on a fresh generation.
3. Spawn probe evidence recorded with its positive control, harness version stated; result decides the location, documented in the ticket.
4. Read-only roles' allowlists exclude Bash, Edit and Write (verified against M0b: the allowlist applies to the main session).
5. Scoped tests green; `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (parent), `TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE` (done)
- Depends on M1a and M1b. Resolves M0 item d.

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 3, 4, 5, 10, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0 record; ADJUST 5, 6.1, 10)
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`
- `agent-working/stored_artifacts/TCK-20261004-SESSION-LAYER-M1C-GENERATED-SESSION-AGENT-FILES/` (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- `tools/sessions/` (new), `.claude/agents/` (generated), `tests/tools/`.

## Assumptions / Open Questions
- Whether `.claude/agents/` edits count as governing-file class: they live under `.claude/`; treat the generated files as derived artifacts guarded by the drift check, and ask the owner if any `settings.json` edit turns out to be needed (none is planned).
- Probe needs Claude Code live calls (cheap, haiku, scratch repo); no owner opt-in beyond the ticket.

## Implementation Notes
Decision: generated files stay in `.claude/agents/` (a separate location would break `--agent`, which resolves names there) with a launcher-only description. Spawn probe (Claude Code 2.1.288, `claude -p --model haiku --setting-sources project`, scratch repos, evidence in `evidence/spawn_probe.jsonl`): with the nine session files present the roster listed all of them (M0d confirmed on 2.1.288) and the model made 0 Agent-tool spawns in 3 runs on tasks a session role could plausibly take; positive control: a repo with an inviting `doc-helper` agent spawned it in 1 of 2 runs. Limits: one model (haiku), 3 trials, no proof for other models; the probe shows no spawn, not that spawning is impossible. If a spawn is ever observed, move generation inline or to a path outside the roster and re-probe. No seat has a tool allowlist today (designers write drafts, planners write tickets, and review roles need `gh` through Bash), so AC4 is covered by the generator emitting an allowlist verbatim and a test that any manifest allowlist excludes Bash, Edit and Write; the first read-only seat is an M2 or later decision.

## Test Summary
tests/tools/test_session_agent_generator.py (9 tests): Deterministic generator, drift check wired into the validator, spawn probe with positive control. Also run: the 11 other test files that scan `.claude/agents` (72 passed), and tests/docs.

## Files Changed
- `tools/sessions/generate_agents.py`
- `.claude/agents/session-*.md (9 generated)`
- `tests/tools/test_session_agent_generator.py`
- `agent-working/stored_artifacts/TCK-20261004-SESSION-LAYER-M1C-GENERATED-SESSION-AGENT-FILES/evidence/`

## Completion Summary
Done. Deterministic generator, drift check wired into the validator, spawn probe with positive control.