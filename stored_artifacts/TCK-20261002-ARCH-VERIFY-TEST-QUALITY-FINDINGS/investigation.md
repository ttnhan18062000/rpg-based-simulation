---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS
artifact_type: investigation
phase: done
date: 2026-10-02
tags: [agent-monitoring, workflows]
---

# Investigation

## Verified facts (against origin/main 78ea7c465)
- `ARCH_VERIFY_SCHEMA` (`.claude/workflows/implement-ticket.js` ~1097): `required: [verdict, violations, summary]`; properties verdict, violations, summary, ts, verified_by. Extra keys are not forbidden.
- The Architecture-Verify prompt's Return list names only verdict/violations/summary/verified_by. Not to be edited (test-architecture rule).
- `archVerify` is read for verdict/violations/summary only. The event is `pushEvent(phase, agent, status, summary, ts, toolCallCount, reasonCode)` -> `{seq, phase, agent, status, summary<=200, ts, tool_call_count, reason_code}`. `writeMonitoring` passes `JSON.stringify(events)` to a monitoring agent that adds four id keys and calls `record_events.py`.
- `record_events.validate_record` only requires {run_id, seq, ts, phase, agent, summary, status}; extra keys pass through to the shard verbatim (`records[i] = {**record, ...}`).
- `record_hand_orchestrated_closure.build_records` rebuilds each event from a fixed key list (phase, agent, status, summary, ts) and DROPS everything else. The hand-orchestrated path is what test-architecture's run 1 used, so the field must be carried there too.
- Skill path: two SKILL.md copies. `.claude/skills/implement-ticket/SKILL.md` (84 lines) is current; `.agents/skills/implement-ticket/SKILL.md` (81 lines, has frontmatter) is older (lacks the verdict-strictness, null-ts, native-run-backstop paragraphs and the mechanism-registry advisory). Neither says how to word an agent's output format.

## Carry-through options
- (a) optional event field: list survives verbatim; no new write path; one row per phase unchanged (`agent_count = events.length` stays right). Cost: validator allowance + schema.md + closure-tool carry. Chosen.
- (b) extra event row: doubles the phase's rows, shifts seq/agent_count semantics, and consumers (retro, anomaly validator, done-checker monitoring check) would see a phantom agent. Rejected.
- (c) side file: a new write path with its own failure and location convention, invisible to the events consumers. Rejected.

## Risks
- Review finding (test-architecture-implementer): the reviewer's definition (`architecture-reviewer.md:123`) says only "a list", and on the skill path the schema is not shown to the agent, so items may be objects. Dropping non-strings would make a transformed or lost list indistinguishable from a clean review. Resolution: carry every item (non-strings as JSON text), wrap a non-array reply, record the non-verbatim count in `test_quality_findings_normalized`.
- The monitoring agent embeds the events JSON in a single-quoted shell argument; a `'` in a finding would break it (same pre-existing risk as `summary`). Mitigation: replace `'` with the typographic apostrophe in the JS before pushing the field.
- On the native path the monitoring agent must echo the extra field; it already echoes unknown keys today. Not provable without a real run (needs user opt-in), so it is tested at the record_events boundary instead.
- Helper parses JS: brace matching must skip strings; pinned against the real file.
