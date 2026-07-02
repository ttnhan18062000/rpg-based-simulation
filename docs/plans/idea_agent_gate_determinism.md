---
status: idea
layer: ai
authority: P2
audience: developer
maturity: idea
date: 2026-07-03
tags: [idea, agent-infrastructure, determinism, gates, enforcement, observability]
---

# Idea: Deterministic Gate Substrate for Agent Workflows

> **Maturity: IDEA** — Not scheduled. Raised directly from [`docs/ai/agent_infrastructure_audit.md`](../ai/agent_infrastructure_audit.md) (2026-07-03 score: 8.0/10, lowest category "Determinism of judged gates" at 6.5). Consider before scaling agent-workflow autonomy further (e.g. CI-triggered `implement-ticket` runs).

---

## Problem

The `implement-ticket` pipeline is structurally sound — 9 phases, hard gates, resumable failure states (see [`docs/ai/workflows.md`](../ai/workflows.md)) — but the gates that actually decide whether work is safe to land are pure LLM judgment with almost no deterministic backstop:

1. **`architecture-reviewer`** renders `APPROVED` / `NEEDS_CHANGES` / `BLOCKED` by reading a plan and reasoning about durable-state rules, API boundaries, and Mechanics Bible compliance — no static check confirms the verdict.
2. **`done-checker`** verifies all 11 Definition-of-Done conditions by reading files and judging — several of these (working_log.csv entry exists, staging artifacts exist, `data/runs/` cleaned) are trivially machine-checkable but aren't machine-checked.
3. **`parity-updater`** and **`mechanics-auditor`** both assert that `docs/parity_ledger/*.yaml` is consistent with `src/`, but nothing cross-references "files touched in this diff" against "parity entries updated in this diff."
4. The one confirmed deterministic backstop, `make lane-architecture` ("static architecture guards, no simulation, no catalog load"), has undocumented coverage relative to what these four agents judge — so nobody can say which fraction of the gate is actually verified versus vibes-checked.

Compounding this: the hooks meant to enforce process (`.claude/settings.json` `PreToolUse`/`PostToolUse`) only ever inject `additionalContext` — a reminder, never a block — and the hard rule "monitoring write failure must never fail the workflow" means a hook that silently breaks leaves no trace that it broke. The combined effect: **every gate in the pipeline can currently be talked past by a confident-but-wrong agent, and the harness has no way to tell you it happened.**

This matters more as agent autonomy scales. A human skimming a `NEEDS_CHANGES` verdict today catches most misjudgments informally. That safety net disappears the moment these workflows run less-supervised (batched `implement-epic` runs, or any future CI-triggered agent run) — at which point an LLM-only gate is not really a gate.

---

## Idea

Give each LLM-judged gate a companion **deterministic verifier** that runs first and produces a machine-checkable `PASS` / `FAIL` / `UNKNOWN`, then require the agent's verdict to explain any disagreement rather than silently overriding it.

### Where it helps

| Gate agent | Deterministic check (new) | What stays LLM-judged |
|---|---|---|
| `architecture-reviewer` | AST scan for direct durable-state mutation outside `src/engine/authoritative_pipeline*`; grep-scoped check for raw domain objects returned from `src/api/`; regex check for known "meaning smuggled into `reason`/`metadata` string" patterns | Whether the *design* is sound — strategic/tactical boundary, whether an abstraction is premature |
| `done-checker` | Script-verifiable subset of the 11 DoD conditions: `working_log.csv` has a new row, `staging_artifacts/{id}/` has all three files, `data/runs/` and `reports/release_proof/` are empty, ticket file exists in `tickets/inprogress/` | "No material gap is left unstated" — irreducibly a judgment call |
| `parity-updater` | Git-diff cross-reference: every `src/` file touched in the commit that maps to a `docs/parity_ledger/*.yaml` subsystem must have a corresponding entry touched in the same commit | Whether the chosen `status` (`verified`/`divergent`) is the correct one |
| `mechanics-auditor` | For any `PARITY` verdict, confirm the cited `test_path` exists **and is green in this run** — not just present in the ledger | Whether an `UNDOCUMENTED` implementation is actually intended behavior |

### Verdict provenance

Extend each gate's return value with a `verified_by` field, e.g. `verified_by: ["static:no_raw_domain_return", "static:parity_diff_match", "llm"]`. This makes "passed because a human-legible rule was true" distinguishable from "passed because an LLM said so" — and gives `done-checker` (and any future audit) a real signal instead of re-deriving it from scratch each time.

### Enforcement: nudge vs. block

Not every hook should escalate — over-blocking exploratory work is its own failure mode. Split by stakes:

- **Stays advisory** (current `additionalContext` nudge): the context-scan reminder before grep/find — low stakes, high false-positive risk from keyword matching.
- **Escalates to a hard block**: finalizing a ticket without a corresponding `agent-monitoring` write; committing a `src/` change in a parity-ledger-tracked subsystem with no matching ledger touch. These are the two cases the audit flagged as *silently* unenforced today, and both have unambiguous, cheap-to-check preconditions.

---

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `make lane-architecture` | Becomes the home for the new static verifiers, or a documented sibling — either way, its coverage should be written down explicitly against the four gates above, closing Recommendation 3 of the audit |
| `agent-monitoring/tools.jsonl` / hooks | The hard-block escalation is a `PreToolUse`/`PostToolUse` hook change, not a new subsystem — reuses the existing hook plumbing in `.claude/settings.json` |
| `docs/parity_ledger/*.yaml` schema | `parity-updater`'s diff cross-reference needs a stable mapping from `src/` path → subsystem YAML file; this may already be implicit in how `parity-updater` scopes its reads and just needs to be made explicit and scriptable |
| `docs/ai/agent_infrastructure_audit.md` | Recommendations 1 ("log hook near-misses") and 3 ("write down what `lane-architecture` covers") are subsumed by this idea rather than being separate small fixes |

---

## Open Questions

- Do static verifier failures hard-block immediately, or downgrade to the same `NEEDS_CHANGES`/`BLOCKED` path the LLM verdict already uses — so there's one failure vocabulary, not two?
- Where do the static checks live — a new `tools/gate_checks/` module, or folded into the existing `lane-architecture` test lane? The latter keeps one deterministic-check surface instead of two.
- How is the static layer itself kept honest — is there a test asserting 1:1 coverage between what this doc claims is checked and what's actually implemented, so this doesn't become the next undocumented gap?
- Should token/cost telemetry (the other acknowledged gap in the audit — `agent-monitoring` cannot see `input_tokens`/`output_tokens`) ride along with this effort, since both are "make the invisible parts of a gate visible," or is that a separate, smaller idea?

---

*Raised: 2026-07-03, directly from the agent infrastructure audit. Deferred pending a decision on where static verifiers should live relative to `lane-architecture`.*
