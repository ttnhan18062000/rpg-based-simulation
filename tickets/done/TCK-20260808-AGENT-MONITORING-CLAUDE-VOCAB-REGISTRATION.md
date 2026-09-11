---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-AGENT-MONITORING-CLAUDE-VOCAB-REGISTRATION
phase: done
date: 2026-08-08
tags: [agent-monitoring, observability]
---

# TCK-20260808-AGENT-MONITORING-CLAUDE-VOCAB-REGISTRATION

## Title
`record_events.py`'s vocabulary-drift check does not recognize `"claude"` as a known agent
literal for the `implement-ticket` workflow, causing a spurious "unrecognized agent" warning on
every hand-orchestrated phase event

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` set is documented
as derived strictly by grepping `.claude/workflows/implement-ticket.js`'s own real
`pushEvent(...)`/subagent-dispatch call sites — but it already includes legitimate non-subagent
"orchestrator pseudo-agent" literals (`"implement-ticket-orchestrator"`) for cases where the
orchestrator logs an event with no delegated subagent. `"claude"` is the real, established literal
used when a session hand-orchestrates `implement-ticket.js` directly (no subagent dispatch —
e.g. after the subagent spawn cap is reached, a real, recurring, sanctioned mode this session used
throughout) — but it was never added to this set, so every such event triggers a harmless but
noisy `WARNING: unrecognized agent 'claude' for workflow 'implement-ticket'` on `record_events.py`
(confirmed non-blocking — warn-only, does not affect `cost_proxy_score`, which is driven by the
separate `agent-monitoring-index` rebuild, not this check — found and disclosed during this
session's own agent-monitoring retro review).

## Scope
1. **Investigate** (should be quick, hotfix tier): confirm `"claude"` is the only real
   hand-orchestration literal in current use (grep `agent-monitoring/events.jsonl` for other
   non-standard agent values that aren't drift/typos, to avoid registering `"claude"` while
   missing a sibling case).
2. **Implement**: add `"claude"` to `WORKFLOW_AGENTS["implement-ticket"]`, with a comment
   explaining it's a hand-orchestration literal (same category as the existing
   `"implement-ticket-orchestrator"` pseudo-agent, not a real `.claude/agents/*.md` subagent) —
   matching this file's own existing precedent and disclosure style, not silently added.

## Out of Scope
- Any change to `cost_proxy_score` computation itself, or the `agent-monitoring-index` rebuild
  cadence — this ticket is purely about the warning's own vocabulary set.
- Adding `"claude"` to other workflows' `WORKFLOW_AGENTS` sets unless Investigate finds real
  evidence it's used there too.

## Acceptance Criteria
- [ ] `WORKFLOW_AGENTS["implement-ticket"]` includes `"claude"`, with a real, evidenced rationale
      comment
- [ ] Re-running `record_events.py` with `agent="claude"` no longer prints the warning
- [ ] Scoped pytest passes (`tests/tools/test_validate_agent_monitoring.py` and any
      vocabulary-specific tests)

## Related Tickets
- None directly — found and disclosed during this session's own agent-monitoring retro review
  (`agent-monitoring/retro/RETRO-2026-W32.md`).

## Related Docs
- None requiring update — this is a code-only vocabulary-set fix, no behavior/contract change.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/vocabulary.py` (`WORKFLOW_AGENTS["implement-ticket"]`)
- `tools/agent-monitoring/record_events.py` (`warn_vocabulary_drift`, the call site that prints
  the warning)

## Assumptions / Open Questions
- Whether other hand-orchestration sessions used a different literal (e.g. a specific model name)
  instead of `"claude"` — not assumed; Investigate should grep real `events.jsonl` data before
  concluding `"claude"` is the only case needing registration.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout.

Investigated first per this ticket's own scope: queried real `events.jsonl` history for every
non-standard `agent` literal ever used on a `TCK-*` run. Found `"claude"` is by far the dominant
real hand-orchestration literal (45 occurrences), but **not the only one** — also found
`claude-fork-direct` (12), `claude-sonnet-4-6` (16), `claude-sonnet` (6), `hotfix-agent` (5),
`manual-hotfix` (3), `claude-orchestrator`/`main` (2 each), and several other one-off variants.
Registering all of them would meaningfully weaken the vocabulary-drift check's own value (it
exists to catch genuine typos/drift, not just tolerate everything ever typed) — that's a real,
separate finding (inconsistent hand-orchestration naming across sessions/time), disclosed here but
deliberately NOT expanded into this ticket's own scope; registered only `"claude"`, matching this
ticket's own explicit request and this session's own actual, current convention.

Added `"claude"` to `WORKFLOW_AGENTS["implement-ticket"]` with a rationale comment, matching the
file's own existing precedent for the `"implement-ticket-orchestrator"` pseudo-agent literal.

Real, unexpected regression found and fixed: `tests/agent_orchestration/
test_bootstrap_vocabulary_equality.py`'s own bootstrap-snapshot test failed, since it compares
`vocabulary.py`'s `WORKFLOW_AGENTS` against a separate YAML "contract" file, and that file's own
docstring explicitly warns against "fixing" a future failure by re-syncing the YAML to
`vocabulary.py`. Resolved correctly, not by re-syncing: that test already had precedent for
excluding pseudo-agent identities (`implement-ticket-orchestrator`) from its own contract
comparison — extended that same exclusion set to also cover `"claude"`, since both represent "no
real subagent was dispatched," not a real contract-declared subagent role. This is a different,
legitimate thing from the re-sync the docstring warns against.

## Test Summary
`pytest tests/tools/test_validate_agent_monitoring.py tests/agent_orchestration/
test_bootstrap_vocabulary_equality.py -q` — 29/29 pass (was 28/29 before the bootstrap-test fix).
`pytest tests/tools/ -k "agent_monitoring or vocabulary or retro" -q` — 187/187 pass. Manually
confirmed via `record_events.py --data '{"agent":"claude",...}'` that the warning no longer prints
(then removed the resulting test-probe row from `events.jsonl`, not left as durable data), and
confirmed a genuinely fake agent literal still correctly triggers `is_known_agent() == False`.

## Files Changed
- `tools/agent-monitoring/vocabulary.py` — added `"claude"` to `WORKFLOW_AGENTS["implement-ticket"]`
- `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py` — extended the existing
  pseudo-agent exclusion set to also cover `"claude"`

## Completion Summary
Real fix landed: `record_events.py` no longer prints a spurious warning for the dominant, real
hand-orchestration agent literal. Found and disclosed (but did not scope-expand into) a wider
finding — many other, much rarer non-standard agent literals exist in `events.jsonl` history,
representing inconsistent hand-orchestration naming over time, not registered here. Found and
correctly fixed an unrelated regression this change caused in a bootstrap-snapshot test, using
that test's own existing exclusion precedent rather than the re-sync approach its docstring
explicitly warns against.
