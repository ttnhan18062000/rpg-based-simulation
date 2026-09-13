---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [architecture, retrieval, evaluation, security, pixel-art]
---

# Milestone 05 — B2 Automated Bounded Retrieval

## Status and outcome

**Dormant and conditional.** If B1 shows useful local signal, test whether automated deny-by-default ranking
can preserve that benefit on a frozen uncontaminated held-out set without weakening authority or security.
This is the first milestone eligible to produce a full `CAP-B01`–`CAP-B09` adaptive-capability disposition.

## Prerequisites

- `CAP-B05-L PASS`, all B1 safeguards pass, and human authorization specifically activates B2 planning.
- Frozen development/held-out split registry, contamination audit, corpus/index hash, unblinding rule, and
  minimum practical effect approved before implementation.
- Retriever/index option decision compares deterministic metadata filtering before embeddings; dependencies,
  data handling, offline availability, and resource budgets approved.
- M1 remains independently operable without memory; M2 passes if native display is an outcome.

## Deliverables

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `B2-W01` | Retriever contract | Typed query generation, deny-by-default scope, ranking, exclusions, empty result, limits, versioning, and explanation schema |
| `B2-W02` | Frozen index and split registry | Corpus, projection schema, index/configuration, assignments, contamination, freeze, and unblinding identities are immutable and auditable |
| `B2-W03` | Bounded context renderer | Only safe projections and active typed guidance enter context; included/excluded IDs and truncation decisions recorded |
| `B2-W04` | Epoch and rollback control | Model/retriever/embedding/scorer/rubric/harness/review changes open a new epoch; earlier playbook/index can be selected |
| `B2-W05` | Retrieval quality suite | Expected relevant/excluded/empty queries and adversarial corpus achieve preregistered ranking and isolation thresholds |
| `B2-W06` | Full held-out causal comparison | Equal-budget, repeated, blinded, randomized/counterbalanced memory versus baseline run with non-regressions |
| `B2-W07` | Full threat campaign | Semantic injection and unauthorized activation tested through ingestion, projection, retrieval, context, planning, adapter, and playbook paths |
| `B2-W08` | `CAP-B01`–`CAP-B09` disposition | Every gate has setup, raw evidence, objective status, limitations, and allowed conclusion |

## Non-goals

- Mandatory embeddings or a vector database; choose the simplest retrieval that passes.
- Online self-modification, automated rule promotion, model training, autonomous curriculum, or executable skills.
- Project-wide transfer, production readiness, production assets, or final art decisions.
- Replacing direct human guidance or requiring memory for M1 operation.

## Authorization boundary

The retriever reads only approved playbook records and safe projections. It cannot read raw evidence or
write any store. The agent cannot broaden queries after seeing results outside the declared retry policy.
Only an authenticated human can activate exact typed guidance. The adapter remains memory-blind.

## Covered capability gates

Full `CAP-B01`–`CAP-B09`, including held-out `CAP-B05`. M1 `CAP-A` results remain separate and cannot be
reclassified by B2. Passing B2 proves only the named experimental scopes.

## Required evidence and security checks

- Full proposal Section 6 provenance, including model/provider, policies, prompt/query, retriever, embedding
  if any, index, rankings, inclusions/exclusions, projection, playbook, tools, scorer, harness, order, and score visibility.
- Retrieval relevance/exclusion gold set, empty-result behavior, scope-conflict fixtures, and context byte/token limits.
- Held-out contamination proof and all candidates/reviews/failures, with primary and non-regression outcomes separate.
- Injection, obfuscation, impersonation, poisoned metadata/images, approval replay, unsafe activation, stale
  epochs, rollback, quarantine, revocation, and deletion tests.
- Exact-output replay is not required under stochastic planning; provenance, retrieval, constraint application,
  and rollback must meet declared tolerances.

## Objective exit criteria

B2 `PASS` requires every `CAP-B01`–`CAP-B09` gate to pass and full held-out `CAP-B05` to meet the practical
effect without non-regression failure. Development-only success remains local evidence. A small or
contaminated sample is `INCONCLUSIVE`; any authority/security breach is `FAIL`. Passage authorizes only a
human review of whether to retain experimental B2 capability.

## Dependencies

B2 depends on M0, M1, B0, and B1; M2 only when display outcomes require it. It must not modify the Knowledge
Gateway MCP, production renderer, simulation pipeline, or agent-orchestration policy without separate owners.

## Rollback path

Disable automated retrieval, pin the last safe manual/no-memory configuration, revoke the index and context
endpoint, quarantine affected records, preserve the result, and verify M1 still operates independently.

## Stop conditions

Stop if B1 signal does not replicate, deterministic filtering suffices and more complexity adds no benefit,
held-out contamination occurs, provenance is insufficient, empty retrieval broadens unsafely, any B gate
fails, or improvement requires unequal budgets or hidden regression.

## Ticket-ready slices after activation

Split registry; deterministic retriever baseline; optional ranking comparison; bounded context renderer;
epoch/rollback; retrieval quality; held-out evaluation; threat campaign; disposition. Do not combine all
components into one ticket.
