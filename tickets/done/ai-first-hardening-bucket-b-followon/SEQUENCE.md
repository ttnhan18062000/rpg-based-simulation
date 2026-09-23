# Implementation Sequence — ai-first-hardening-bucket-b-followon

tracking_doc: docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md

All three tickets are independent of each other — no ordering requirement. `implement-epic` would
implement them in any order; listed here alphabetically for reference only.

## Order

1. TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON — the only ticket that touches code
   (`.claude/workflows/implement-ticket.js`'s shadow-reviewer env-var default) and the epic ticket
   itself (refreshing its stale Bucket B/C gate descriptions).
2. TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC — Bucket-C item 18, a spec document
   only (no `.claude/agents/*.md` edits).
3. TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC — Bucket-C item 19, a spec document only
   (no `cost_proxy.py` changes).

## Why These Are Independent

Item 13's eval pilot (`TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`, done) unblocked Bucket-C items
18/19/20 per `bucket_c_future_options.md`'s own sequencing rule — none of the three tickets here
depend on each other's output. Ticket 1's epic refresh documents that all six Bucket-A/B gating
tickets are now done; tickets 2 and 3 each independently consume that same already-cleared
prerequisite to write their own Experiment Specification, following the six-section shape
(`Hypothesis`/`Baseline`/`Method`/`Metrics`/`Exit`/`Kill`) `agent_evaluation_foundation_experiment.md`
already established for item 13.

## Scope Boundaries Carried From the Batch Brief

- Item 20 (full eval platform) stays untouched — pilot evidence alone doesn't justify building it
  yet, per the source proposal's own warning.
- Item 21 (Codex pilot) stays in `tickets/backlogs/` per prior user decision — not part of this
  batch.
- Item 17 (secret-hook escalation) is not in this batch — the hook is advisory-only and no
  false-positive rate is recorded yet, so there is no decision to make.
