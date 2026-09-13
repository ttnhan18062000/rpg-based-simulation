---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [architecture, evaluation, human-review, pixel-art, security]
---

# Milestone 04 — B1 Manually Curated Advisory Reuse

## Outcome

Run the cheapest credible test of whether a very small human-approved playbook and manually selected safe
case projections improve a repeated experimental drawing task. The result is `CAP-B05-L` local signal only.
It neither passes full `CAP-B05` nor authorizes automated retrieval.

## Prerequisites

- B0 `PASS` and approved use of retained real-session evidence.
- M1 core `CAP-A01`–`CAP-A08` and `CAP-A11` **(2026-09-13, added by review)** pass; M2 is required only when the primary/non-regression outcome uses native display.
- Named reviewer and curator roles, exact candidate/active stores, authenticated promotion action, and typed guidance grammar.
- Preregistered B1 charter with affordable sample, primary outcome, non-regressions, budgets, blinding,
  randomization/counterbalancing, tie/disagreement rules, and practical-effect threshold.

## Deliverables

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `B1-W01` | Minimal typed playbook | Only a few narrow operational/drawing rules with exact hashes, scope, evidence, status, expiry, and curator approval |
| `B1-W02` | Manual case packet | Human selects a bounded set of safe projections plus contrasting failures; no automated similarity/ranking |
| `B1-W03` | Activation boundary proof | Agents/scorers cannot activate, edit, replay, or broaden a rule; post-approval validation binds exact bytes and scope |
| `B1-W04` | Controlled comparison | Same model, prompt except treatment, tools, time, token, and revision budgets across memory and no-memory conditions |
| `B1-W05` | Blind review package | Neutral randomized labels/order; initial human decision before scores; condition concealment where practical |
| `B1-W06` | Outcome report | Primary, secondary, non-regression, failures, ties, disagreements, and pre/post-score decisions reported separately |
| `B1-W07` | Investment decision | Stop, one bounded rerun, or recommend B2 planning based on `CAP-B05-L` and safeguards |

## Non-goals

- Automated retrieval, embeddings, vector databases, learned ranking, or project-wide transfer.
- Full `CAP-B05` passage or an adaptive-system claim.
- Combining outcomes into one favorable score or allowing efficiency to hide readability/reliability regression.
- Automatic rule extraction, promotion, score-based tie breaking, or production-art selection.

## Authorization boundary

Humans manually select safe case projections and approve exact typed rules. The agent receives a pinned
advisory packet but may not query the archive. The Aseprite adapter receives only the final bounded drawing
request and provenance IDs. External scores remain hidden until the initial review and have no activation authority.

## Covered capability gates

- Preliminary/local evidence: `CAP-B02` safe relevance, `B03` scope isolation, `B04` human promotion,
  `B08` score robustness, and `B09` context-path injection defense.
- Decision measure: non-gating `CAP-B05-L` only.
- Not covered: full held-out `CAP-B05`, automated retrieval, full `B06`/`B07`, or project-wide adaptation.

## Required evidence and security checks

- Exact model/provider/policy/prompt/tool versions and available stochastic controls; unavailable provenance explicit.
- Playbook/projection/corpus hashes; manually included and excluded IDs; scope and presentation order.
- All candidates, operation/revision evidence, timings, violations, failures, reviews, and disagreements.
- Attempts at approval impersonation/replay, rule mutation, unknown fields, conflicting scope, unsafe rationale,
  scorer instructions, and case-projection injection must fail end to end.
- Mechanical invalidity may reject a candidate; it cannot decide subjective readability.

## Objective exit criteria

`CAP-B05-L PASS` requires the preregistered primary practical improvement, every non-regression condition,
allowed failure rate, valid blinding/order, and all security/authority checks. Insufficient sample,
contamination, excessive disagreement, or provider instability is `INCONCLUSIVE`. Any non-regression or
authority failure is `FAIL`. Only PASS plus explicit human approval may unlock B2 planning.

## Dependencies

B1 depends on B0 and M1. It uses one narrow `ART-W01`–`ART-W03`-compatible task family chosen before
results. M2 becomes a prerequisite if native readability is primary; otherwise native claims are prohibited.

## Rollback path

Deactivate the experimental playbook snapshot, revoke case packet access, return to no-memory M1 behavior,
retain the full result including failures, and quarantine compromised evidence without rewriting history.

## Stop conditions

Stop on `FAIL` or `INCONCLUSIVE` unless a human approves one rerun for a named procedural defect. Stop if
condition blinding is impossible, budgets differ, cases contaminate the evaluation, scores anchor initial
review, or useful signal requires weakening security or non-regression criteria.

## Ticket-ready slices after authorization

Typed guidance/activation boundary; manual safe packet; preregistration; comparison runner; blind review
packaging; injection/approval suite; result and stop decision. Do not pre-scope B2 implementation tickets.
