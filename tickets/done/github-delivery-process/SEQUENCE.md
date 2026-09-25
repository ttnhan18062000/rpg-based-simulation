# Implementation Sequence — github-delivery-process

Tickets must be implemented in this order. `implement-epic` reads this file to override alphabetical
order. `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` is the epic-tier parent and is not implemented
directly — it tracks the six below.

## Order

1. TCK-20260924-DELIVERY-STATUS-TOOL  (no deps in this batch)  — DONE 2026-09-24 (ed95e92d4)
1b. TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE  (depends on: TCK-20260924-DELIVERY-STATUS-TOOL)
2. TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES  (no deps in this batch)
3. TCK-20260924-DELIVERY-PR-RENDERER  (depends on: TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES)
4. TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY  (depends on: TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES)
5. TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER  (depends on: TCK-20260924-DELIVERY-STATUS-TOOL)
6. TCK-20260924-DELIVERY-COST-MEASUREMENT  (depends on: TCK-20260924-DELIVERY-STATUS-TOOL)

## Why This Order Matters

**The status tool runs first, ahead of the contract and templates. This deliberately inverts the
original request's ordering**, which asked for templates first. Three reasons, all from the plan's own
evidence:

- It carries the **largest measured cost**. 16.9 `gh` calls per PR with ~86% of them pure observation
  (plan §1.1) is the biggest single number in the epic; the templates gap (§1.3) and the 28%
  subject-traceability gap (§1.4) are both smaller, and §1.4 is explicitly assessed as moderate rather
  than a broken audit trail.
- It carries the **most incident-backed logic**. Plan §3.7's five verdicts encode four incidents that
  each already cost real time — the absent-run branch, the TLS block reading as green, step conclusions
  surviving a log block, and the partial-log-fetch trap. Those are currently defended only by an agent
  remembering a paragraph.
- It **depends on nothing**, and running it first means ticket 6 has a real before/after to measure.

Ticket 2 also has no intra-batch dependency, so 1 and 2 could technically run in parallel or swapped.
The order above is a priority statement, not a hard constraint — but 2 must not be reordered *after* 3
or 4, which consume its template spec.

Tickets 3 and 4 both depend on 2: ticket 3 consumes the machine-readable template spec (so the renderer
and the human template cannot disagree), and ticket 4 advises against the contract ticket 2 defines.
They are independent of each other and may run in either order.

Ticket 5 depends on 1: it classifies a `FAILING`/`ABSENT` payload that the status tool produces, and is
explicitly forbidden from fetching that state itself.

Ticket 6 runs last and depends on 1 at minimum, because it measures whether the epic actually reduced
`gh` calls per PR. Running it before the tools it measures would record a "before" number twice.

## Ticket 1b — added after ticket 1 closed

`TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE` was filed on 2026-09-24 during review of ticket
1's output. `pr_status.py`'s docstring claims non-target workflows are out of scope; the code filters
runs on `head_sha` alone, so every workflow's runs vote on the verdict. The defect is **latent** —
`deploy-docs.yml` is `workflow_dispatch:`-only today — but the docstring is false now, the two-workflow
test case is missing now, and ticket 5 builds a classifier directly on this payload. It runs before
ticket 5 for that reason; it does not block ticket 2, which shares no code with it.

This is a correction to ticket 1's output, not a re-opening of any settled decision below.

## One non-child ticket riding this branch

`TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE` (`tickets/todos/`, filed 2026-09-24)
is **not** a child of this epic — it belongs to agent-monitoring's own data model, not the delivery
lane, same reasoning as the vocabulary check below. But per the user's explicit instruction its
implementation lands on this same `github-delivery-process-epic` branch rather than opening a second
PR, and it **must not start before `TCK-20260924-DELIVERY-COST-MEASUREMENT` (ticket 6) lands** —
both touch `tools/agent-monitoring/`.

So the effective branch order is 1 → 1b → 2 → {3, 4, 5} → 6 → the shard ticket. It is listed here
only so the ordering constraint is visible to whoever sequences the next dispatch; it does not make
the ticket an epic child, and the epic is complete without it.

## Two settled decisions this batch must not re-open

Both were decided at scoping and are recorded in plan §7. A child ticket finding them inconvenient
should report that, not revisit them.

- **Advisory everywhere. Nothing blocks.** No commit-lint, no PR-shape gate, no CI job asserting that
  commit subjects name a real ticket — the last of these was the one genuine candidate and was
  declined. Every check this batch ships prints and exits zero, including on its own internal errors.
- **Ticket IDs go in the PR body's `Closes:` block, never in the PR title** (plan §3.5).

## Note on the vocabulary check

`TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK` was scoped in the same review as this epic and
is deliberately **not** a child of it. It is standard-tier, lives in `tickets/inprogress/`, and belongs
to a different subsystem — monitoring vocabulary, not the delivery lane. It shares no code with any
ticket here and has no ordering relationship to them.

It was scoped as hotfix-tier and raised to standard during verification, when its scope widened from
agent literals alone to both literal positions plus registering the 29 unregistered literals the
reconciliation found. Per CLAUDE.md Tier Routing, a new tool plus a 29-entry registry expansion is a
new feature, not a minimal targeted change.
