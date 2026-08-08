---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP
phase: open
date: 2026-08-07
tags: [agent-monitoring, process-improvement]
---

# TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP

## Title
Both of this week's search-before-grep compliance failures are sibling tickets from the same
epic, same Investigate-phase sequence position — investigate whether the epic's own Investigate
prompt (not two unrelated agent lapses) is the real cause

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Found during a 2026-08-07 agent-monitoring retro (`agent-monitoring/retro/RETRO-2026-W32.md`
Notes §4). This week's Tool Safety Audit shows search-before-grep compliance at 75% (6/8 real
Investigate-phase `(run_id, seq)` pairs). Drilled into `compute_tool_safety_metrics()`'s own
`per_pair_compliance` detail (not rendered per-pair in the report by default) to find exactly
which 2 pairs failed: **`TCK-20260702-OBSISO-TRACE-ASYNC::2`** and
**`TCK-20260702-OBSISO-BROKER-CONFIG::2`** — both sibling child tickets under the same `OBSISO`
epic, and both at the exact same Investigate-phase `seq` position (`2`). Two failures sharing both
the same epic AND the same sequence position is a stronger signal than 2 independent tickets
failing at arbitrary points — it reads as a real, systemic gap specific to how this epic's own
Investigate phase was prompted/scoped (e.g. a shared investigation-kickoff template that both
child tickets inherited, which happened to grep before searching), not two unrelated one-off
agent lapses.

CLAUDE.md's Hard Rules are explicit and repeated: "Do not run grep, find, raw file reads... before
first calling `search_docs` (MCP) and `graphify query`." This is a real compliance gap against a
documented hard rule, not a soft preference.

## Scope
1. **Investigate** (mandatory before Plan):
   - Read both tickets' own `investigation.md` (`stored_artifacts/TCK-20260702-OBSISO-TRACE-ASYNC/`,
     `stored_artifacts/TCK-20260702-OBSISO-BROKER-CONFIG/`) and their Investigate-phase tool-call
     sequence directly from `agent-monitoring/tools.jsonl` (filtered to
     `(run_id, seq) in {(TCK-20260702-OBSISO-TRACE-ASYNC, 2), (TCK-20260702-OBSISO-BROKER-CONFIG, 2)}`)
     to see the exact tool-call order that triggered the grep-before-search violation.
   - Check whether both tickets share a common parent (an epic ticket, a shared
     `investigation.md` template, or a shared Investigate-phase prompt text) that could explain
     the shared failure mode.
   - Check whether other `OBSISO` epic child tickets (if any exist beyond these two) also show
     this pattern, or whether it's isolated to exactly these two.
2. **Plan**: if a shared root cause is found (e.g. a stale/incomplete Investigate-phase prompt
   template used specifically for this epic, or a broader gap in how `investigator` agent prompts
   are constructed for epic child tickets), design the fix.
3. **Implement**: apply the fix if the investigation supports one; otherwise document the finding
   as "isolated, no shared cause found" and close without a code change.

## Out of Scope
- Re-running or re-investigating the 2 already-closed `OBSISO` tickets' own substantive work — this
  ticket is about the PROCESS gap (why search-before-grep was skipped), not their actual
  deliverables, which are already DONE and presumably correct regardless of the tool-order lapse.
- Any change to `compute_tool_safety_metrics()`'s own detection logic — it correctly identified
  the gap; nothing about the detector itself needs fixing here (contrast with the sibling ticket
  `TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE`, which IS about a detector-logic gap).

## Acceptance Criteria
- [ ] `investigation.md` identifies the exact tool-call sequence for both failing pairs and
      confirms or refutes a shared root cause
- [ ] If a shared cause is found: a concrete fix to the relevant prompt/template/skill instruction
- [ ] If no shared cause is found: an honest "isolated, no pattern" conclusion, not a forced fix
- [ ] Scoped pytest run passes (if any code/prompt change is made)

## Related Tickets
- TCK-20260702-OBSISO-TRACE-ASYNC, TCK-20260702-OBSISO-BROKER-CONFIG (the 2 runs under
  investigation — both DONE)
- TCK-20260803-RETRO-TOOL-SAFETY-AUDIT (built the search-before-grep compliance detector this
  finding relies on)

## Related Docs
- CLAUDE.md's "Context Scan (Mandatory)" and Hard Rules sections (the rule that was violated)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-OBSISO-TRACE-ASYNC/investigation.md`
- `stored_artifacts/TCK-20260702-OBSISO-BROKER-CONFIG/investigation.md`

## Related Code Areas
- `.claude/skills/implement-ticket/SKILL.md` (Investigate phase instructions)
- `.claude/agents/investigator.md` (if this repo has a dedicated investigator agent prompt file)

## Assumptions / Open Questions
- Whether these 2 tickets even share a formal "epic" parent ticket, or just a common naming
  prefix (`OBSISO`) without a real `implement-epic` relationship — not assumed; Investigate must
  confirm the actual relationship before concluding there's a shared template/prompt to fix.

## Implementation Notes
Subagent spawn cap (200/200) reached before this ticket started — Investigate/Implement/Verify
performed directly.

Confirmed both flagged pairs share a real parent epic (`obs-isolation/TCK-20260702-OBSISO-EPIC.md`)
and a tightly-coupled subsystem — but ruled out a "broken shared template" in the narrow sense:
their own `search_docs`/`graphify` calls DID happen, just during Scope (seq 1) rather than
Investigate (seq 2), because Scope-phase research already substantially covered their shared
observability-subsystem topic. The sibling epic child that wasn't flagged (`ISOLATION-PROOF`)
targeted a topically distinct concern (perf/benchmark methodology) that Scope's research hadn't
covered, so its own Investigate phase made a fresh search call.

Investigated and ruled out a false lead: an `Agent` tool row with `input_summary` text reading
"Plan TCK-..." while correctly tagged `phase: Investigate` looked initially like a seq/phase
misattribution bug, but direct comparison of `tools.jsonl`'s own `phase` field against
`events.jsonl` (using `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT` as a control) confirmed full
consistency — it's a cosmetic `description`-text mismatch on one Agent dispatch with zero effect
on the compliance computation (which never inspects Agent-row summaries).

Real root cause: `.claude/agents/investigator.md` had zero mention of `search_docs`/`graphify`/the
search-before-grep hard rule anywhere in its own persistent definition (confirmed via direct read)
— it relied entirely on CLAUDE.md's global instruction being followed implicitly, which this
evidence shows isn't reliable once Scope-phase research already feels like it covered the topic.
Added an explicit instruction to `investigator.md`'s `## Inputs` section: even when Scope/epic-level
research already exists, Investigate must still make its own scoped search_docs/graphify call
before any grep. Matches the same pattern already applied for the sidecar-write gap earlier this
session (`TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`) — state hard rules explicitly
in the specific agent's own definition, not just globally.

## Test Summary
`tests/tools/test_workflow_meta_conformance.py` — 23 passed, 1 xfailed (pre-existing, unrelated;
regression guard only, this ticket doesn't touch phase/workflow structure).
`run_static_precheck` — all 7 script-checkable DoD conditions PASS.

## Files Changed
- `.claude/agents/investigator.md` (added explicit search-before-grep instruction to `## Inputs`)

## Completion Summary
Confirmed a real, shared, evidenced cause across both flagged pairs — not a coincidence, and not a
broken template per se, but a genuine gap in the investigator agent's own persistent definition
that let Scope-phase research-reuse silently substitute for Investigate's own required search pass.
Fixed at the source (the agent definition itself) rather than the detector or the two historical
tickets (already DONE, not re-litigated per this ticket's own Out of Scope). Investigated and ruled
out one false lead (a seq/phase misattribution hypothesis) before committing to the real cause,
rather than reporting the first plausible-looking anomaly.
