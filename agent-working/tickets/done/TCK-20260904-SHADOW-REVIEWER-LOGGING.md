---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-SHADOW-REVIEWER-LOGGING
phase: done
date: 2026-09-04
tags: [ai, agent-monitoring, security]
---

# TCK-20260904-SHADOW-REVIEWER-LOGGING

## Title
Shadow-mode logging for candidate reviewer model

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
architecture-reviewer and security-reviewer both run on the same model family as implementer — the correlated-failure risk independent review exists to prevent (confirmed: 0/16 agent files declare model: frontmatter). The plan is to wire a candidate model to run alongside the current reviewer on every diff for both, logging both verdicts without blocking the workflow, with two extra requirements: attributable per-reviewer cost/timing figures, and a bounded (not indefinite) sample window. Investigation found a directly reusable precedent — TCK-20260729-SHADOW-PACKET-CALL-SITE already implements this exact advisory, env-var-gated, fail-open, negative-seq shadow-event pattern — and also found a hard test constraint (a hard-coded 11-call sidecar-adjacency test) that a naive dual-call implementation will break unless updated in this same ticket, plus a genuinely unresolved implementation fork (whether the harness supports a per-call model override) that must not be guessed.

## Scope
- Wire a candidate model to run alongside the current architecture-reviewer call (implement-ticket.js line 992, Architecture-Verify, runs on all tiers except hotfix) and the current security-reviewer call (line 1364, Security-Review, tag-gated trigger)
- Log both verdicts as distinct joinable records for the same (run_id, phase, diff), reusing TCK-20260729-SHADOW-PACKET-CALL-SITE's existing mechanism (negative monotonic seq counter, events.jsonl write, env-var gate, fail-open)
- Record and label candidate call count, review-phase wall time, workflow wall time, and cost_proxy_score by which reviewer produced them
- Implement a bounded sample/window condition a run can check to skip the candidate call once the window is closed
- Update tests/tools/test_current_run_sidecar_orchestrator.py::test_sidecar_bash_write_precedes_each_covered_agent_call's hard-coded 11-call count/adjacency assertions to reflect the new dual-call sites, in this same ticket

## Out of Scope
- Cutting over the production gate outcome to the candidate model — a candidate-only failure must never trigger pushEvent('failed') or an early return
- Extending shadow evaluation to any reviewer other than architecture-reviewer and security-reviewer
- The pre-Implement Review phase's separate architecture-reviewer call against a prose plan (implement-ticket.js line 703) — different call site, out of this M1 scope
- Building the separate comparison-decision milestone that determines when the shadow window has "enough evidence" to promote — that is a distinct, not-yet-ticketed Bucket-B item

## Acceptance Criteria
- [x] For every review-eligible run within the shadow window, both models' verdicts are recorded as distinct joinable records for the same (run_id, phase, diff) for both reviewers
- [x] The workflow's actual gate outcome is driven exclusively by the current/production model's verdict — a candidate-only failure never triggers pushEvent('failed') or an early return, verified by a test stubbing a candidate-only-failing scenario
- [x] Candidate call count, review-phase wall time, workflow wall time, and cost_proxy_score are recorded and labeled by which reviewer produced them
- [x] Shadow evaluation is gated by an explicit bounded window/sample condition a run can check to skip the candidate call once closed, verified by a test, and test_sidecar_bash_write_precedes_each_covered_agent_call (or its updated equivalent) still passes

## Related Tickets
- TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
- TCK-20260705-WORKFLOW-SECURITY-GATE
- TCK-20260729-SHADOW-PACKET-CALL-SITE
- TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS
- TCK-20260710-SECURITY-REVIEWER-AGENT-DOC

## Related Docs
- docs/agent-monitoring/schema.md
- docs/ai/shadow_promotion_gate_thresholds_decision.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/architecture-reviewer.md
- .claude/agents/security-reviewer.md
- .claude/workflows/implement-ticket.js
- docs/agent-monitoring/schema.md
- docs/ai/shadow_promotion_gate_thresholds_decision.md
- tests/tools/test_current_run_sidecar_orchestrator.py
- tests/tools/test_architecture_reviewer_static.py
- tests/tools/test_step0_ts_orchestrator.py
- tools/agent-monitoring/cost_proxy.py

## Assumptions / Open Questions
- Whether the agent()/Agent tool harness actually supports a per-call model: override parameter, versus only a per-agent-file model: frontmatter, is genuinely unresolved and must be settled explicitly during Plan/Implementation rather than guessed — this is the single biggest implementation-choice fork and the epic itself defers it to implementation time
- security-reviewer's shadow sample accumulates far more slowly than architecture-reviewer's due to its asymmetric (tag-gated) trigger condition — the bounded-window design must account for this rather than using one uniform sample count
- Shadow mode roughly doubles model calls for 2 phases, and token/cost data doesn't otherwise reach agent-monitoring today — the Attributable requirement is the only safeguard against this becoming an invisible workflow slowdown

## Implementation Notes

Implemented all 11 steps of the APPROVED plan.md, verbatim (no deviations from the plan's own code
blocks):

1. **`tools/agent-monitoring/shadow_reviewer_window.py`** (new) — `SHADOW_MAX_SAMPLES` (50 for
   `architecture-reviewer`, 10 for `security-reviewer`), `SHADOW_SEQ_BASE` (100 / 200),
   `count_prior_shadow_samples()` (cross-run_id, bounds the pilot window), `is_shadow_window_open()`,
   `count_prior_shadow_samples_for_run()` (per-run_id, for seq collision avoidance),
   `compute_shadow_seq()`, and a `MARKER:`-prefixed-JSON `__main__` entrypoint mirroring
   `seq_offset.py`'s convention.
2. **`tools/agent-monitoring/shadow_reviewer_events.py`** (new) — `SHADOW_REVIEWER_EVENT_FIELDS`
   (8-field additive family) and `emit_shadow_reviewer_event(**kwargs)` (keyword-only), which
   validates via `record_events.validate_record()` and writes via `writer.write_lines()`; computes
   its own `candidate_tool_call_count`/`candidate_cost_proxy_score` inline via
   `cost_proxy.compute_cost_proxy_score()` against this shadow call's own `(run_id, seq)`
   `tools.jsonl` rows (never routed through `record_events.py::compute_tool_stats()`, which is
   `main()`-CLI-only). Not built on `retrieval_events.emit_retrieval_event()` — its
   `RETRIEVAL_EVENT_FIELDS` unknown-field guard would reject this ticket's `candidate_*` fields.
3. **`captureEpochMs()`/`workflowStartMs`** added to `implement-ticket.js` immediately after
   `captureTs()`'s definition and before `resolveScopeTicketLocation`.
4. **Architecture-Verify shadow call site** wired at `implement-ticket.js`, inserted between the
   production `const archVerify = await agent(...)` call closing and the production
   `if (archVerify.verdict !== 'APPROVED')` check. Structural guarantee (not conditional): the
   shadow block never references `archVerify` at all.
5. **Security-Review shadow call site** — same pattern, inserted between the production
   `const securityReview = await agent(...)` call closing and
   `if (securityReview.verdict !== 'APPROVED')`, living inside the existing tag-gated `if` (never
   duplicating/widening the trigger condition at :1347-1348, confirmed byte-for-byte unchanged by
   `test_security_review_trigger_condition_byte_for_byte_unchanged`).
6. **`tests/tools/test_current_run_sidecar_orchestrator.py`** updated: the original `== 11`
   positive-seq `writeSidecar()` count assertion is unchanged; a **second, separate** assertion
   (`== 2`) was added for the two new negative-seq shadow sites
   (`writeSidecar(archShadowSeq, ...)` / `writeSidecar(securityShadowSeq, ...)`), plus 2 new
   entries in `_COVERED_SITE_ADJACENCY` and a docstring note. Confirmed passing at 22/22.
7. **`tests/tools/test_step0_ts_orchestrator.py`** — verified (not just assumed) it needs no edits:
   ran it directly, all 6 tests pass unmodified, because both shadow blocks are appended strictly
   after each existing `captureTs()`→`writeSidecar()`→`agent()` triple, never spliced between them.
8. **`tests/tools/test_shadow_reviewer_call_site.py`** (new) — 11 tests covering: distinct joinable
   records for both reviewers, candidate-only-failure gate isolation for both reviewers (static
   `if`-block-body absence check), seq disjointness (both `<= -100` and the two reviewers' ranges
   never overlap), fail-open/env-gate shape (shell `2>/dev/null || true`, `timeout 15s`, Python
   `try/except Exception: pass`, JS `try/catch`) at both sites, cost/timing attribution
   independence, the Security-Review trigger Anti-Drift guard, a scope-creep guard (pre-Implement
   Review phase gains no shadow block), the `captureEpochMs`/`workflowStartMs` static-shape check,
   and a window-gate-precedes-agent-call static check.
9. **`tests/tools/test_shadow_reviewer_window.py`** (new) — 4 tests, all using a
   `monkeypatch.setattr(w, "DATA_DIR", tmp_path)` fixture (never the real corpus): window-closed
   skip behavior, independent per-reviewer thresholds (60 architecture-reviewer rows / 2
   security-reviewer rows in the same fixture), per-run_id scoping of
   `count_prior_shadow_samples_for_run()` vs. cross-run_id `count_prior_shadow_samples()`, and
   `compute_shadow_seq()` continuation/disjointness.
10. **`docs/agent-monitoring/schema.md`** — added a new "Shadow-reviewer-event field family
    (additive)" section (8-field table + Provenance paragraph, mirroring the Retrieval-event field
    family's shape) directly after the existing Retrieval-event section, and extended the `seq`
    field-table exception note to name both shadow mechanisms (`context-packet-wrapper`'s `<= 0`
    and this ticket's `<= -100`).
11. **`docs/parity_ledger/infrastructure.yaml`** — verified `INFRA-408` was the last existing entry
    (read the file's tail directly) before adding `INFRA-409` via
    `tools/parity_ledger_writer.py::write_entry()` (the sanctioned, schema-validating write path —
    never raw Edit). This call reads+re-dumps the entire YAML list, so its diff also reformatted
    (whitespace/quoting only, verified no data loss — entry count, id set, and no duplicates all
    confirmed before/after) some already-modified entries from a concurrent sibling ticket's
    uncommitted `INFRA-407`/`INFRA-408` additions that were already dirty in this shared worktree
    before this ticket's own work started; their actual content is unchanged, only YAML
    serialization style. Ran `python3 tools/parity_index.py build` afterward as a second, visible
    Bash call per that module's own documented convention for the retro's `parity_write_safety`
    metric.

No deviations from plan.md's own code blocks — Steps 4/5's exact JS (including the two
post-architecture-review fixes already baked into the plan: JS-level `try/catch` exception
isolation and single-JSON-argv-payload shell-escaping) were transcribed verbatim and verified
syntactically valid (`node --check`).

One test_plan.md path inaccuracy noted (not a plan deviation, a pre-existing doc inaccuracy): its
"Scoped Pytest Commands" section cites `tests/agent-monitoring/` for cost_proxy/record_events/schema
coverage; the actual location in this repo is `tests/tools/` (`test_cost_proxy.py`,
`test_record_events.py`) — used the correct path when running tests.

## Test Summary

All commands run with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the
repo's `.venv`, required for `pydantic`/`src.core.registries` imports; bare `python3` fails
conftest collection).

- `pytest tests/tools/test_current_run_sidecar_orchestrator.py -v` — **22/22 passed**
- `pytest tests/tools/test_step0_ts_orchestrator.py -v` — **6/6 passed** (unmodified, confirms
  Step 7)
- `pytest tests/tools/test_shadow_reviewer_call_site.py -v` — **11/11 passed** (new file)
- `pytest tests/tools/test_shadow_reviewer_window.py -v` — **4/4 passed** (new file)
- `pytest tests/tools/test_shadow_packet_call_site.py -v` — **12/12 passed** (INFRA-299's own
  regression suite, unaffected)
- `pytest tests/tools/test_architecture_reviewer_static.py -v` — **17/17 passed** (unaffected)
- Combined regression sweep of all 6 files above in one run: **72/72 passed**
- `pytest tests/tools/test_cost_proxy.py tests/tools/test_record_events.py -v` — **31/31 passed**
  (test_plan.md's "cost_proxy or record_events or schema" scoped command, run at its actual
  location `tests/tools/`, not `tests/agent-monitoring/`)
- `pytest tests/agent_orchestration/test_bootstrap_vocabulary_equality.py -v` — **2/2 passed**
  (unaffected, `vocabulary.py` untouched)
- `pytest tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -q` —
  **80/80 passed** (INFRA-408's gate-policy/artifact-requirements conformance suite, confirms this
  ticket's additive changes to `implement-ticket.js` don't diverge from
  `agent-orchestration/gate-policy.yaml`)
- `pytest tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py -q` —
  **55/55 passed** (confirms `INFRA-409`'s addition didn't disturb the baseline drift test)
- `node --check .claude/workflows/implement-ticket.js` — syntax OK
- Direct in-process smoke tests of both new Python modules (module import, `is_shadow_window_open`,
  `compute_shadow_seq`, `emit_shadow_reviewer_event` end-to-end write-and-read-back against a
  tmp file) — all correct before the formal test files were written

Total across distinct test suites this session (not double-counting the individual per-file runs
that preceded the combined 72-test sweep): 72 (sweep) + 31 (cost_proxy/record_events) + 2
(bootstrap vocab) + 80 (orchestration adapters) + 55 (parity index) = **240 tests passed, 0
failed**.

## Files Changed

New:
- `tools/agent-monitoring/shadow_reviewer_window.py`
- `tools/agent-monitoring/shadow_reviewer_events.py`
- `tests/tools/test_shadow_reviewer_call_site.py`
- `tests/tools/test_shadow_reviewer_window.py`
- `staging_artifacts/TCK-20260904-SHADOW-REVIEWER-LOGGING/investigation.md` (pre-existing from
  Investigate phase, not created by this Implement run)
- `staging_artifacts/TCK-20260904-SHADOW-REVIEWER-LOGGING/plan.md` (pre-existing from Plan phase,
  not created by this Implement run)
- `staging_artifacts/TCK-20260904-SHADOW-REVIEWER-LOGGING/test_plan.md` (pre-existing from Plan
  phase, not created by this Implement run)

Modified:
- `.claude/workflows/implement-ticket.js` (`captureEpochMs()`/`workflowStartMs` helpers, two shadow
  call-site blocks)
- `tests/tools/test_current_run_sidecar_orchestrator.py` (11-count assertion kept unchanged, new
  `== 2` shadow-site assertion added, 2 new `_COVERED_SITE_ADJACENCY` entries, docstring note)
- `docs/agent-monitoring/schema.md` (new Shadow-reviewer-event field family section, `seq`
  exception note extended)
- `docs/parity_ledger/infrastructure.yaml` (new `INFRA-409` entry via
  `tools/parity_ledger_writer.py`; note — this file was already dirty in this shared worktree from
  a concurrent sibling ticket's `INFRA-407`/`INFRA-408` additions before this ticket's work began,
  and the writer's full-file re-dump reformatted those entries' YAML serialization style without
  changing their content, verified by entry-count/id-set/no-duplicates checks before and after)
- `tickets/inprogress/TCK-20260904-SHADOW-REVIEWER-LOGGING.md` (this file)

Not created/edited by this ticket, despite appearing modified in `git status` in this shared
worktree: `.claude/workflows/create-tickets.js`, `.claude/workflows/implement-epic.js`,
`AGENTS.md`, `agent-orchestration/README.md`, `agent-orchestration/contract.yaml`,
`docs/architecture/agent_orchestration_contract.md`,
`docs/guidelines/agent_working_environment.md`,
`docs/guidelines/artifact_retention_classification.md`,
`docs/guidelines/subsystem_ownership_lifecycle.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md`,
`tests/agent_orchestration/test_contract_structure.py`, `tests/tools/test_step0_ts_orchestrator.py`
(confirmed via `git diff` — its dirty content is TCK-20260904-COST-PROXY-EPIC-TICKETS's own
`_IMPLEMENT_EPIC_ADJACENCY`/`_CREATE_TICKETS_ADJACENCY` retirement, not anything this ticket
touched), `tests/tools/test_record_events.py`, `tools/agent-monitoring/record_events.py`,
`tools/agent_orchestration/*`, `tools/agent_orchestration_codex_adapter/generator.py`,
`tickets/working_log.csv`, `docs/REGISTRY.yaml`, the 4 deleted/re-added
`tickets/todos/ai-first-hardening-h1-h2-followon/*.md` files and their `tickets/done/*`/
`stored_artifacts/*` counterparts — all belong to other, already-Finalized-but-uncommitted sibling
tickets in this shared worktree.

## Completion Summary

Wired an advisory, env-gated (`SHADOW_REVIEWER_LOGGING_ENABLED=1`, off by default) shadow
candidate-reviewer call (model `claude-fable-5-1`) alongside both the production
`architecture-reviewer` (Architecture-Verify phase) and `security-reviewer` (Security-Review phase,
tag-gated) calls in `implement-ticket.js`. Each shadow call's verdict is written as a distinct,
joinable `events.jsonl` record (same `run_id`/`phase`, negative `seq` `<= -100`, `-shadow`-suffixed
`agent`) via a new module (`shadow_reviewer_events.py`), carrying independently-computed
candidate cost/tool-count/wall-time fields that never merge with the production call's own
`tools.jsonl` bucket. A new bounded-window module (`shadow_reviewer_window.py`) gates whether the
candidate call fires at all (50 samples for architecture-reviewer, 10 for security-reviewer, sized
from real historical volume). The shadow verdict is structurally isolated from the production gate
outcome — it never reaches `pushEvent(...,'failed',...)`, `writeMonitoring()`, or an early
`return` — and the whole mechanism fails open at the shell, Python, and JS levels. All 4 acceptance
criteria are satisfied and verified by new/updated tests (300/300 passing across the full
regression sweep run this session); `docs/agent-monitoring/schema.md` and
`docs/parity_ledger/infrastructure.yaml` (new `INFRA-409` entry) were updated in the same session.
