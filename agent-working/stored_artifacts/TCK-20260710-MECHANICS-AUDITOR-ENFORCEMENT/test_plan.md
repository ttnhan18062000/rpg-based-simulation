---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT
artifact_type: test_plan
tags: [ai, workflows, determinism, agent-monitoring]
---

# Test Plan — TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT

## Regression Surface

All 3 must keep passing unmodified (baseline confirmed this session: 73 passed, 2.68s):

**Unit — gate-check modules (direct dependency chain: any new function in `mechanics_auditor_static.py`
imports from / sits alongside these):**
- `tests/tools/test_mechanics_auditor_static.py` (16 tests — the module this ticket extends)
- `tests/tools/test_parity_updater_static.py` (imported by `mechanics_auditor_static.py` for
  `expected_subsystems_for_files`; must not regress)
- `tests/tools/test_done_checker_static.py` (sibling gate-check module, same `tools/gate_checks/`
  package; no direct import relationship but same package `__init__.py` — confirm it stays empty)

**Integration — workflow orchestration (only relevant if design (a), a new `implement-ticket.js`
call site, is chosen at Plan time; otherwise this group is unaffected and serves as a negative-control
regression check that nothing was accidentally wired in):**
- `tests/tools/test_current_run_sidecar_orchestrator.py` (11 tests — asserts `writeSidecar()`
  precedes every covered `agent()` call; a new mechanics-auditor call site, if added, would need a
  corresponding sidecar-adjacency assertion added here or in a new file, not a silent gap)
- `tests/tools/test_step0_ts_orchestrator.py` (6 tests — asserts `captureTs()` precedes every
  covered `agent()` call; same adjacency requirement as above if design (a) is chosen)
- `tests/tools/test_workflow_meta_conformance.py` (structural conformance checks on the workflow
  files; must not regress regardless of which design is chosen)

**Docs (no automated test, verify by grep per the prior ticket's own precedent):** re-grep
`docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`,
`docs/ai/skills.md` for `mechanics-auditor` post-change — confirm every existing mention (5 files,
confirmed this session) remains accurate and no stale claim ("no orchestrator-side enforcement...
compliance depends entirely on the agent actually running the script and citing it honestly") survives
unedited if the ticket's resolution changes that fact.

## New Tests Required

Per AC #1 (design explicitly resolved, documented) — no automated test possible for a written-decision
AC; verified by investigation.md/plan.md prose review only, not a test.

Per AC #2 (if a call site/wrapper is added, static check computed before agent renders verdict) and
AC #3 (verified_by self-report cross-checked post-hoc against orchestrator-computed result) — assuming
the investigation's recommended design (b), a standalone post-hoc audit function added to
`tools/gate_checks/mechanics_auditor_static.py`:

1. **`test_audit_detects_falsely_cited_static_pass`**
   Category: unit (coverage-honesty — must prove detection of a real violation, not just a happy path,
   per this test file's own existing header convention: "every check function below has at least one
   fixture proving it catches a real violation it claims to catch, not just that it runs on the happy
   path")
   Verifies: given a fixture ledger entry whose `test_path` cites a genuinely failing test, and a
   simulated agent output row claiming `verified_by: ["static:mechanics_auditor_static", "llm"]` with
   no FAIL caveat disclosed in `Finding`, the new audit function flags this row as a mismatch/dishonest
   claim (recomputed static result contradicts what the row's `verified_by`/`Finding` implies).
   Location: `tests/tools/test_mechanics_auditor_static.py`

2. **`test_audit_detects_step_0_skipped_on_verified_status_entry`**
   Category: unit (coverage-honesty)
   Verifies: given a fixture ledger entry with `status: verified` (Step 0 is mandatory per the agent's
   own prompt for this branch), and a simulated agent output row with `verified_by: ["llm"]` only (no
   static-check tag at all), the audit function flags this as a "Step 0 skipped" case — this is the
   literal AC #4 scenario ("a new test demonstrates the enforcement mechanism actually detects a case
   where Step 0 was skipped or falsely cited").
   Location: `tests/tools/test_mechanics_auditor_static.py`

3. **`test_audit_passes_honest_llm_only_claim_on_non_verified_status_entry`**
   Category: unit (negative control — prevents over-triggering)
   Verifies: given a fixture ledger entry with `status: missing` or `status: divergent` (Step 0 is
   never mandated for these branches per `.claude/agents/mechanics-auditor.md`'s own prompt), a
   simulated row with `verified_by: ["llm"]` only does **not** get flagged — the audit must not punish
   an honest, correctly-scoped `["llm"]`-only claim outside the `verified`-status branch.
   Location: `tests/tools/test_mechanics_auditor_static.py`

4. **`test_audit_passes_honest_static_pass_claim`**
   Category: unit (happy path)
   Verifies: given a fixture `verified`-status entry whose `test_path` cites a genuinely passing test,
   and a row honestly claiming `verified_by: ["static:mechanics_auditor_static", "llm"]` with no
   contradicting caveat, the audit returns a clean/no-violation result.
   Location: `tests/tools/test_mechanics_auditor_static.py`

5. **`test_audit_scoped_by_row_not_whole_ledger`**
   Category: unit (anti-drift lock-in, mirrors existing `test_scoped_by_entry_id_not_whole_ledger`
   convention in this same file)
   Verifies: the audit function only evaluates rows explicitly passed to it — a ledger entry not
   present in the agent's own output rows is never independently surfaced as a violation (no bulk
   sweep). Reuses the existing 3-entry ledger fixture pattern (`A-001`/`A-002`/`A-003`) from
   `test_scoped_by_entry_id_not_whole_ledger`.
   Location: `tests/tools/test_mechanics_auditor_static.py`

6. **`test_audit_never_overrides_agent_status_classification`**
   Category: unit (anti-drift — repeats the non-override principle `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`
   already locked in for the per-entry Step 0 check; this ticket's new post-hoc audit must inherit the
   same constraint)
   Verifies: the audit function's return shape carries a distinct field (e.g. `"honesty_status"` or
   equivalent, name TBD at Plan time) that is never named `"status"`/`"Status"` and is documented as
   never intended to overwrite or relabel the agent's own `PARITY`/`DIVERGENT`/`MISSING`/`UNDOCUMENTED`
   classification — asserted by inspecting the returned dict's keys, not just its values.
   Location: `tests/tools/test_mechanics_auditor_static.py`

**If design (a) (a new `implement-ticket.js` call site) is chosen instead at Plan/Review time**, add
the JS-side adjacency assertions mirroring the sibling files' existing convention (e.g.
`test_mechanics_auditor_bash_precedes_agent_call` in a new or existing
`tests/tools/test_current_run_sidecar_orchestrator.py`-style file) — not detailed further here since
the investigation's recommendation is design (b); the planner must add this section explicitly if
overriding that recommendation.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_mechanics_auditor_static.py -v
python3 -m pytest tests/tools/test_mechanics_auditor_static.py tests/tools/test_parity_updater_static.py tests/tools/test_done_checker_static.py -v
```

If design (a) is chosen (JS call site added), additionally:
```
python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_step0_ts_orchestrator.py tests/tools/test_workflow_meta_conformance.py -v
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **Non-override lock-in** (`test_audit_never_overrides_agent_status_classification`, above): guards
  against the exact mistake `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s architecture review round 1
  already caught once (a static FAIL force-relabeling `PARITY` to `DIVERGENT`/`MISSING`). Any future
  change that makes the new audit function's output field double as a `Status` override would fail
  this test.
- **No-bulk-sweep lock-in** (`test_audit_scoped_by_row_not_whole_ledger`, above): guards against a
  future "helpful" refactor that has the audit function accept a ledger file/directory instead of an
  explicit row list — would silently reintroduce the 82%-of-entries-have-no-test_path wall-of-FAILs
  problem this codebase's existing design discipline already avoids everywhere else in this module.
- **Branch-scoping guard** (`test_audit_passes_honest_llm_only_claim_on_non_verified_status_entry`,
  above): guards against over-eager enforcement flagging `missing`/`divergent`-branch rows that were
  never required to cite Step 0 in the first place — prevents this ticket's fix from becoming a new
  source of false positives against otherwise-correct agent behavior.
- **Call-site-absence negative control**: re-run `grep -n "mechanics-auditor\|mechanics_auditor"
  .claude/workflows/implement-ticket.js` as part of Verify if design (b) is the final choice — must
  still return zero matches, confirming the prior ruling was not silently overturned by accident
  during implementation.
- **Docs-drift guard**: grep all 5 files that currently mention `mechanics-auditor`'s enforcement gap
  (`.claude/agents/mechanics-auditor.md`, `docs/ai/agents.md`, `docs/ai/workflows.md`,
  `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`) for the literal phrase "no
  orchestrator-side enforcement" post-implementation — if the chosen design actually closes (or
  partially closes) that gap, this stale claim must be updated in the same session (Authoritative
  Mechanics Rule's "Consistency"/CLAUDE.md's Parity discipline extended to agent-infra self-documentation),
  not left contradicting the new code.
