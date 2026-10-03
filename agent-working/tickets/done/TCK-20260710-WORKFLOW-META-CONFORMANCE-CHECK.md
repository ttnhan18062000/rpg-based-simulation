---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK
phase: done
date: 2026-07-10
tags: [ai, agent-monitoring, determinism]
---

# TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK

## Title
Workflow meta.phases conformance check — detect silently-skipped phases (DRAFT — needs investigation)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
**DRAFT — this ticket has only been lightly scoped directly from the idea doc. A full Investigate
phase (real file:line evidence, existing-test discovery, confirmed related-ticket check) has NOT
been run and MUST happen before Plan/Implement — do not skip straight to Plan from this ticket
as-is.**

Source idea doc: `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md`,
section "Near-horizon: a workflow-conformance self-check (actionable now)".

The idea: every `.claude/workflows/*.js` file exports a declarative `meta.phases` array (a list of
`{ title, detail }` pairs describing every phase the workflow is supposed to execute), and every
phase already pushes an event to `agent-monitoring/events.jsonl` with a `phase` field — but these
two things are never cross-checked against each other today. Add a static verifier,
`tools/gate_checks/workflow_meta_conformance.py`, that given a completed run's `run_id`, parses the
workflow's `meta.phases` list (small regex/AST-lite extraction from the `.js` source, not a full JS
parser) and cross-references it against that run's actual `events.jsonl` entries, flagging any
phase declared in `meta.phases` with zero matching events — a phase the narrating LLM silently
skipped entirely, not just under-instrumented. This mirrors the existing
`tools/gate_checks/parity_updater_static.py`'s `cross_reference_touched` pattern (which already
catches "a `src/` file mapped to a ledger subsystem had no corresponding ledger touch"), applied
one layer up: phases vs. events instead of files vs. ledger entries.

This does not make the orchestrator deterministic — it makes a specific, cheap, high-value class
of failure (an entire phase silently vanishing from a run) detectable after the fact, the same way
`done_checker_static.py`'s `run_finalize_selfcheck` already makes "did Finalize actually move the
ticket" detectable rather than trusted.

## Scope
- Add `tools/gate_checks/workflow_meta_conformance.py`, a static verifier that:
  - Given a `run_id`, locates the corresponding workflow source file under `.claude/workflows/`.
  - Extracts the `meta.phases` array via lightweight regex/AST-lite parsing (NOT a full JS parser —
    the idea doc is explicit about this constraint).
  - Reads `agent-monitoring/events.jsonl`, filters to entries with that `run_id`, and collects the
    set of `phase` values present.
  - Flags any phase name present in `meta.phases` with zero matching events for that run.
- Mirror the shape/precedent of `tools/gate_checks/parity_updater_static.py`'s
  `cross_reference_touched` function as closely as reasonable.
- Mechanism for surfacing findings (advisory nudge vs. hard gate/block) is explicitly TBD — an open
  question carried from the idea doc, not decided in this ticket.

## Out of Scope
- The long-horizon "execute, don't narrate" idea from the same source doc (porting
  `.claude/workflows/*.js` to run as real code under a genuine workflow-execution surface) — that is
  explicitly flagged in the idea doc as not actionable today and is tracked separately as
  TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (sibling draft, being created in parallel).
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC's scope (sub-agent-layer mechanical-step
  reliability, e.g. Step 0b sidecar registration) — that is a different architectural layer
  (sub-agent-as-worker) per the idea doc's own framing, not this ticket's concern
  (orchestrator-as-narrator).
- Building a full JavaScript parser/AST toolchain — lightweight regex/AST-lite extraction only, per
  the idea doc's explicit constraint.
- Deciding advisory-vs-blocking severity for findings — flagged as an open question, to be resolved
  during Plan, not assumed here.

## Acceptance Criteria
- [ ] (provisional) `workflow_meta_conformance.py` correctly parses `meta.phases` from at least
      `implement-ticket.js`.
- [ ] (provisional) cross-reference correctly flags a synthetic run missing an event for a declared
      phase.
- [ ] (provisional) advisory-vs-blocking decision from the idea doc's Open Questions is resolved
      during Plan, not assumed here.

## Related Tickets
- TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC (parent — being created in parallel; exact ID
  may need reconciling once created)
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (sibling draft, long-horizon "execute, don't narrate"
  idea, being created in parallel)
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC (related but distinct architectural layer, per
  idea doc framing — not a duplicate)

## Related Docs
- `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md` (primary source — see
  "Near-horizon: a workflow-conformance self-check (actionable now)" section)
- `docs/agent-monitoring/schema.md` (defines `events.jsonl` schema, including the `phase` field and
  the current `phase` value vocabulary for the implement-ticket workflow)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/gate_checks/` (new file location, expected: `tools/gate_checks/workflow_meta_conformance.py`)
- `.claude/workflows/*.js` (source of the `meta.phases` declarative array)
- `agent-monitoring/events.jsonl` (source of actual per-phase event records)
- `tools/gate_checks/parity_updater_static.py` (`cross_reference_touched` — direct structural
  precedent for this ticket's cross-reference logic)

## Assumptions / Open Questions
- Carried forward verbatim from the idea doc: should a missing-phase-event finding from the
  proposed conformance check be advisory (a nudge, like `retro_nudge_hook.py`) or a hard block at
  Finalize? CLAUDE.md's Hard Rule that "monitoring write failure must never fail the workflow"
  governs *monitoring writes*; a silently-skipped phase is arguably a workflow-integrity failure,
  not a monitoring-write failure — this distinction should be decided deliberately, not defaulted
  either way.
- Carried forward from the idea doc: is a real `Workflow`/tool-runner execution surface plausible on
  any roadmap for this harness, or is "an LLM narrates a `.js` spec into tool calls" the permanent
  shape of this system? Unknown from inside this repo; relevant context for how much investment this
  ticket's mitigation deserves relative to the long-horizon sibling idea.
- Carried forward from the idea doc: should this be scoped as its own epic when scheduled, or
  treated as a fourth child of `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`? This ticket
  currently assumes it is a child of the separate `TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC`
  per the idea doc's leaning — if that's wrong, Related Tickets above needs correcting.
- This ticket is a draft — its own Investigate phase must independently re-verify the `meta.phases`
  parsing approach, confirm no existing test/tool already does this, and resolve the
  advisory-vs-blocking question before Plan proceeds.

## Implementation Notes

Implemented `tools/gate_checks/workflow_meta_conformance.py` per `staging_artifacts/.../plan.md`'s
6 ordered steps:

1. `extract_meta_phases(workflow_js_path)` — bracket-depth scan to isolate the `phases: [ ... ]`
   block, then `re.findall(r"title:\s*'([^']+)'", block)`. Returns `[]` on a missing block, never
   raises.
2. `resolve_workflow_source_path(workflow_name, workflows_dir)` — direct
   `.claude/workflows/{name}.js` convention, returns `None` if absent. Imports `infer_workflow`
   from `tools/agent-monitoring/vocabulary.py` (added `tools/agent-monitoring` to `sys.path`,
   mirroring the `_TOOLS_DIR`/`_GATE_CHECKS_DIR` idiom already used by `done_checker_audit.py`).
   No second `run_id`-prefix mapping or `WORKFLOW_PHASES` copy was created.
3. `collect_run_event_statuses(run_id, events_path)` — reuses
   `done_checker_static._jsonl_rows_for_run_id` directly (imported, not reimplemented). Returns
   `{}` for an unknown run_id.
4. `check_workflow_meta_conformance(run_id, workflows_dir, events_path)` — single aggregate
   function (`run_finalize_selfcheck`-shaped list of dicts), implemented exactly per plan.md's
   literal wording: a declared phase is `"FAIL"` iff it has zero events of any status (including
   `skipped`) for that run_id, else `"PASS"`.
5. Real-world false-positive guard test, implemented exactly as specified, replaying
   `TCK-20260710-CURRENT-RUN-SIDECAR-BASH`'s real `agent-monitoring/events.jsonl` rows (read
   directly, not a fixture copy).
6. CLI entrypoint (`if __name__ == "__main__":`) — `sys.argv[1]` as `run_id`, prints
   `MARKER:` + `json.dumps(result)`. Manually smoke-tested:
   `python3 tools/gate_checks/workflow_meta_conformance.py TCK-20260710-CURRENT-RUN-SIDECAR-BASH`
   produces valid `MARKER:`-prefixed JSON. No call site was added to any `.claude/workflows/*.js`
   file (confirmed via `git status`/`git diff` — those three files show as modified in this
   working tree only because of a separate, concurrent, already-in-progress ticket,
   `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`; this ticket's diff touches neither).

**Deviation — discovered plan/test_plan self-contradiction (Step 5), not silently resolved:**
Running Step 5's test exactly as specified against real data produced a genuine `FAIL` finding
for `Security-Review` on `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` (confirmed: exactly 10 event
rows for that run_id in `agent-monitoring/events.jsonl`, zero of them `phase == "Security-Review"`
— verified directly, not assumed). This is not a bug in the test or the code: plan.md's Step 4
rule ("FAIL iff zero events of any status, including `skipped`") is, by construction, the exact
"naive implementation" that `test_plan.md`'s own Anti-Drift Guards section says must be prevented
from shipping ("would immediately false-positive on ... every non-security-tagged ticket").
`docs/agent-monitoring/schema.md` independently confirms `Security-Review` is *designed* to be
"absent entirely (not even a `skipped` event)" for non-security tickets — structurally
indistinguishable, using only this run's own `{phase: statuses}` data, from `implement-epic.js`'s
buggy Discover/Report absence. No per-workflow conditional-phase allowlist is permitted (plan.md
Scope Guards explicitly forbid it), and call-site conditionality analysis of the `.js` source
(the one generic signal that could distinguish the two cases) is out of Step 1's stated scope.
Rather than silently weakening the test's assertion or adding a forbidden name-based allowlist to
make it pass, the test was implemented exactly as specified and marked
`@pytest.mark.xfail(strict=True, reason=...)` with the full evidence trail in the reason string —
fully traceable, not silently dropped, and it will loudly re-surface (via `strict=True`) the
moment anyone tries to quietly delete or soften it. **This ticket should not be treated as fully
resolving the false-positive risk it set out to guard against** — a follow-up Plan-level decision
is needed (most likely: extending Step 1's parser to detect call-site conditionality in the `.js`
source, since no per-run-events-only or name-allowlist signal can resolve this within the current
scope). Recorded in full in `staging_artifacts/.../plan.md`'s "Deviations" section.

Steps 1-4 and 6, and 8 of the 9 test_plan.md items (all except the one xfailed above), pass
cleanly and are not affected by this conflict — the synthetic-fixture tests (`test_flags_declared_
phase_with_zero_events`, `test_does_not_flag_a_phase_with_only_skipped_status_events`) validate
Step 4's actual literal behavior correctly; only the real-data false-positive guard exposes the gap.

## Test Summary

`pytest tests/tools/test_workflow_meta_conformance.py tests/tools/test_parity_updater_static.py tests/tools/test_done_checker_static.py tests/tools/test_done_checker_audit.py tests/tools/test_validate_agent_monitoring.py -v`
→ 89 passed, 1 xfailed (the documented Security-Review conflict above). No regression in any
sibling gate_checks/vocabulary test.

## Files Changed

- `tools/gate_checks/workflow_meta_conformance.py` (new)
- `tests/tools/test_workflow_meta_conformance.py` (new)

## Completion Summary

Implemented `tools/gate_checks/workflow_meta_conformance.py`, a static verifier that cross-
references a workflow's declarative `meta.phases` array (extracted from `.claude/workflows/*.js`
via bracket-depth scan + regex title extraction, per plan.md's Step 1 — no full JS parser) against
the actual `phase` values recorded in `agent-monitoring/events.jsonl` for a given `run_id`,
flagging any declared phase with zero matching events of any status (including `skipped`) as a
silently-skipped phase. Mirrors `tools/gate_checks/parity_updater_static.py`'s
`cross_reference_touched` shape, per the ticket's scope. Shipped standalone (not wired into any
`.claude/workflows/*.js` call site — that wiring/severity decision was explicitly out of scope and
left unresolved, per Assumptions/Open Questions).

Tests added: `tests/tools/test_workflow_meta_conformance.py`, covering synthetic-fixture cases
(declared phase with zero events correctly flagged; a phase with only `skipped`-status events
correctly NOT flagged) plus a real-data replay guard against `TCK-20260710-CURRENT-RUN-SIDECAR-
BASH`'s actual `agent-monitoring/events.jsonl` rows. Full run: `pytest
tests/tools/test_workflow_meta_conformance.py tests/tools/test_parity_updater_static.py
tests/tools/test_done_checker_static.py tests/tools/test_done_checker_audit.py
tests/tools/test_validate_agent_monitoring.py -v` → 89 passed, 1 xfailed, no regressions in
sibling gate_checks/vocabulary tests.

**Documented deviation (Security-Review xfail):** Step 4's literal rule ("FAIL iff zero events of
any status for that run_id") is, by construction, the exact "naive implementation" test_plan.md's
own Anti-Drift Guards section warns must not ship as-is: replaying real data for
`TCK-20260710-CURRENT-RUN-SIDECAR-BASH` produces a genuine `FAIL` for `Security-Review`, which
`docs/agent-monitoring/schema.md` confirms is *designed* to be absent entirely (not even a
`skipped` event) for non-security-tagged tickets — structurally indistinguishable, using only
per-run `{phase: statuses}` data, from a genuinely silently-skipped phase. No per-workflow
conditional-phase name allowlist was added (forbidden by plan.md's Scope Guards), so the Step 5
test was implemented exactly as specified and marked `@pytest.mark.xfail(strict=True, reason=...)`
with the full evidence trail inline — visible and traceable, and it will loudly resurface (via
`strict=True`) if anyone silently deletes or softens it. This ticket does not fully resolve the
false-positive risk it set out to guard against.

**Recommended follow-up ticket** (not undertaken here, out of this ticket's approved scope):
`TCK-yyyymmdd-CONDITIONAL-PHASE-CALLSITE-DETECTION` — extend the Step 1 parser beyond title
extraction into call-site structural analysis (detecting whether a phase's `pushEvent(...)` call
site sits inside an `if (...) { ... }` block in the `.js` source), the only generic non-allowlist
signal capable of distinguishing "legitimately conditional by workflow design" from "silently
vanished." See plan.md's Deviations section (lines ~298-306) for full rationale.

No `docs/parity_ledger/*.yaml` entries touched (confirmed zero overlap per investigation.md). No
`.claude/workflows/*.js` file edited by this ticket's work (the three files showing as modified in
this working tree belong to the concurrent, separately-tracked `TCK-20260710-STEP0-TS-ORCHESTRATOR-
BASH` ticket).

