---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP
phase: done
date: 2026-08-10
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP

## Title
Close the search-before-grep gap for Investigate-phase work that never spawns the `investigator`
subagent

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP` added an explicit search-before-grep callout to
`.claude/agents/investigator.md` (commit `9d9ed87db7a`, 2026-08-08 12:55 UTC), root-causing the
original gap as "an instruction living only in global `CLAUDE.md` context, with no explicit
callout in the specific agent's own definition, gets skipped under real task pressure." The fix
worked exactly where it was applied: recomputing `compute_tool_safety_metrics` over the 14-day
window post-commit shows **zero** `investigator`-agent Investigate-phase violations.

But 3 post-fix violations remain in the same window, and **all 3 are `agent=claude`**, not
`investigator`:

| run_id::seq | first tool ts (UTC) |
|---|---|
| `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD::2` | 2026-08-08T15:30:09 |
| `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION::2` | 2026-08-08T19:04:19 |
| `TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE::2` | 2026-08-09T05:07:49 |

Direct inspection of `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION::2`'s full
tool sequence in `agent-monitoring/tools.jsonl` confirms: 100+ tool calls, straight into
`Read`/`grep`-flavored `Bash`, zero `mcp__knowledge-search__search_docs` or `graphify` call
anywhere in the phase, later hand-editing `docs/parity_ledger/combat_movement.yaml` and
`substrate.yaml` directly. This is Investigate-phase work done directly by the top-level
orchestrating session (`agent=claude`) rather than delegated to the `investigator` subagent — the
identical failure mode the epic-gap ticket already proved, just recurring in a path that
`investigator.md`'s fix structurally cannot reach.

## Scope
- **Investigate (mandatory before Plan):** Determine exactly which real entry point drives this
  `agent=claude` Investigate-phase work — hotfix-tier pipeline routing (per CLAUDE.md's Tier
  Routing table: `hotfix | Scope → Implement → Test → Parity → Verify → Finalize`, which has no
  explicit Investigate phase name at all — confirm whether these 3 runs are actually hotfix-tier,
  or a different hand-orchestration path), or something else. Do not assume; find the real
  dispatch mechanism in `.claude/workflows/implement-ticket.js` or wherever `agent=claude` phase
  labeling originates.
- Add an explicit, non-optional search-before-grep callout at that confirmed real entry point,
  mirroring `investigator.md`'s fix in substance (not necessarily verbatim — the entry point may
  be a workflow prompt template, not an agent `.md` file).
- If the entry point turns out to be "no dedicated instruction surface exists at all for this
  path" (i.e. it's genuinely just the top-level session with only `CLAUDE.md` to rely on), decide
  and document how a per-task-relevant reminder gets surfaced there without hand-rolling a new
  agent definition for a case that may not warrant one.

## Out of Scope
- Any change to `.claude/agents/investigator.md` itself — that fix is verified working; this
  ticket covers a different, non-overlapping path.
- Re-running or re-litigating the 3 already-affected tickets above — they are already closed/done;
  this is forward-looking.
- Redesigning hotfix-tier's pipeline stages — only the search-before-grep instruction gap within
  whatever the real dispatch mechanism is.

## Acceptance Criteria
- [x] `investigation.md` identifies the real, confirmed dispatch mechanism for `agent=claude`
      Investigate-phase work, sourced from `.claude/workflows/implement-ticket.js` (or equivalent)
      and real `events.jsonl` records — not assumed.
- [x] An explicit search-before-grep callout exists at that entry point.
- [x] `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (sibling epic child) can measure
      whether this fix holds in the next retro window — this ticket does not itself need to prove
      long-term compliance, only that the callout is real and reachable.

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP (DONE; predecessor fix, same root-cause class,
  different entry point)
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP (DONE; same shape — hand-orchestration
  bypassing an agent-specific instruction)

## Related Docs
None yet — Investigate phase must confirm the real dispatch mechanism before any doc gets touched.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `.claude/agents/investigator.md` (reference only — not modified by this ticket)
- `agent-monitoring/tools.jsonl`, `agent-monitoring/events.jsonl`

## Assumptions / Open Questions
- Whether all 3 flagged runs share the same dispatch mechanism, or are 3 unrelated hand-orchestration
  shapes that happen to look similar — not assumed; Investigate must confirm before Plan, following
  the same honest-verdict discipline `TCK-20260807-DOC-UPDATER-FIRST-ATTEMPT-BLOCKED-RATE` used
  ("if 3 genuinely unrelated causes are found, that is a valid, honest terminal state").

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP/plan.md`
exactly, in the plan's recommended order (Step 1 → Step 2 → Step 3), with no deviations:

- **Step 1** — Appended a new sentence to the end of step 2 ("Investigate")'s existing text block
  in `.claude/skills/implement-ticket/SKILL.md` (line 58), after the shadow-context-packet
  sentence and before the numbering moves to step 3 ("Plan"). The new sentence: names both tools
  by their real identifiers (`mcp__knowledge-search__search_docs`, `graphify`); states explicitly
  ("Step 0's one-time upfront call does not substitute for this phase-scoped call") that Step 0 is
  not sufficient on its own; is self-contained (no bare "see Step 0" pointer); and cites this
  ticket ID. The literal strings `2. **Investigate**` and `3. **Plan**` were preserved
  byte-for-byte, and the existing shadow-context-packet sentence and Step 0's own text were left
  untouched, per the plan's Do NOT touch list.
- **Step 2** — Created `tests/tools/test_skill_investigate_search_before_grep.py` with two tests,
  following the raw-text `Path.read_text()` pattern used by
  `tests/tools/test_current_run_sidecar_orchestrator.py` (a new file was warranted rather than
  extending that file, since its own docstring scopes it to `implement-ticket.js` and
  `schema.md` only, not `.claude/skills/`). Both tests bound their assertions to the region
  between the literal markers `"2. **Investigate**"` and `"3. **Plan**"` so a fix landing only in
  Step 0 cannot false-pass:
  - `test_skill_investigate_step_has_search_before_grep_callout` — asserts
    `mcp__knowledge-search__search_docs`, `graphify`, and the phrase `"does not substitute"` all
    appear in the bounded region.
  - `test_skill_investigate_callout_survives_step0_removal_check` — asserts the region contains
    an imperative verb (`"call"`) alongside the tool names, does not contain a bare `"see step
    0"` pointer, and exceeds a minimal length threshold (200 chars) as a defense-in-depth guard
    against a future edit weakening the callout back into a pointer.
- **Step 3** — Added a new `## Investigate-Step Search-Before-Grep Callout` section to
  `docs/guides/agent_monitoring.md`, inserted immediately after the "Sidecar Reminder Hook"
  section and before the `## Makefile Targets` separator, mirroring the Sidecar Reminder Hook
  section's structure (what the gap was, the fix, and a pointer to the relevant metric). Also
  added one short cross-reference sentence to the end of the existing "Tool Safety Audit" table
  row (line 70) pointing to the new section, without altering that row's existing description of
  `compute_tool_safety_metrics()`'s own detection logic.

Verification: ran the plan's specified command —
`pytest tests/tools/test_current_run_sidecar_orchestrator.py
tests/tools/test_workflow_meta_conformance.py tests/tools/test_generate_retro.py
tests/tools/test_skill_investigate_search_before_grep.py -v` — 146 passed, 1 xfailed, 0 failed.
This confirms the two new tests pass and all three named regression-surface files
(`test_current_run_sidecar_orchestrator.py`, `test_workflow_meta_conformance.py`, including its
`check_skill_doc_covers_meta_phases` phase-heading conformance test, and `test_generate_retro.py`)
remain unaffected.

No `src/` code, Mechanics Bible chapter, engine contract, or parity ledger entry was touched —
consistent with `investigation.md`'s "Mechanics / Engine Constraints" and "Parity Ledger Overlap"
sections (both "None applicable"). `.claude/agents/investigator.md` and
`.claude/workflows/implement-ticket.js` were not touched, per the plan's Scope Guards.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py
tests/tools/test_workflow_meta_conformance.py tests/tools/test_generate_retro.py
tests/tools/test_skill_investigate_search_before_grep.py -v` → 146 passed, 1 xfailed, 1 warning
(pre-existing, unrelated `SyntaxWarning` in `done_checker_static.py`), 0 failed. Both new tests
(`test_skill_investigate_step_has_search_before_grep_callout`,
`test_skill_investigate_callout_survives_step0_removal_check`) pass, and the three named
regression-surface test files pass unmodified. Parity cross-reference gate: vacuous pass (no
`src/` paths in this ticket's Files Changed).

## Files Changed
- `.claude/skills/implement-ticket/SKILL.md` (modified — appended search-before-grep callout to
  step 2's text block)
- `tests/tools/test_skill_investigate_search_before_grep.py` (new — regression tests for the
  callout)
- `docs/guides/agent_monitoring.md` (modified — new "Investigate-Step Search-Before-Grep
  Callout" section, plus a one-sentence cross-reference addition to the existing "Tool Safety
  Audit" table row)

## Completion Summary
Closed the search-before-grep gap for hand-orchestrated Investigate-phase work that never spawns
the `investigator` subagent. `investigation.md` confirmed the real mechanism was not hotfix-tier
routing but whole-pipeline hand-orchestration: the top-level Claude session executing
`.claude/skills/implement-ticket/SKILL.md`'s numbered steps directly, whose step 2 ("Investigate")
carried no search-before-grep instruction of its own (only the one-time, upfront Step 0 did).
Added an explicit, self-contained, non-optional search-before-grep instruction directly inside
step 2's own text block in `SKILL.md`, mirroring the equivalent fix already applied to
`.claude/agents/investigator.md` for the agent-dispatched path
(`TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`). Backed the fix with two bounded-region
regression tests in a new `tests/tools/test_skill_investigate_search_before_grep.py` and
documented the fix in a new `docs/guides/agent_monitoring.md` section, cross-referenced from the
existing "Tool Safety Audit" row. No `src/` code, mechanics, engine-contract, or parity-ledger
changes were required or made.
