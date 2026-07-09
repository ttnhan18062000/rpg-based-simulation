---
status: idea
layer: observability
authority: P2
audience: developer
maturity: idea
date: 2026-07-04
tags: [idea, agent-infrastructure, observability, schema, data-quality]
---

# Idea: Enforce agent-monitoring Schema at Write Time, Not Just at Read Time

> **Maturity: SCHEDULED** — tracked as `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` under
> `TCK-20260708-AGENT-INFRA-HARDENING-EPIC` (2026-07-08), sequenced first in that epic since the
> cost-observability idea depends on this one's vocabulary cleanup. Raised from a direct
> investigation of `agent-monitoring/runs.jsonl`/`events.jsonl` (2026-07-04), the same investigation
> that produced [`TCK-20260704-CREATE-TICKETS-MONITORING`](../../../tickets/done/TCK-20260704-CREATE-TICKETS-MONITORING.md)
> (now in `tickets/done/`). That ticket fixed a coverage gap (`create-tickets` wasn't recorded at
> all); this idea addresses a data-quality gap in the workflows that already are recorded. Decision
> made explicitly when this was raised: **do not backfill or rewrite the 98 historical drifted
> records** — this idea is about preventing further drift, not correcting the past.

---

## Problem

Direct analysis of the live `agent-monitoring/` data (466 runs, 1844 events) found real, measurable schema drift:

- **21% of runs (98/466) have `workflow: null`.** These are older-format records using a completely different field set (`ticket_id`/`status`/`started_at`/`completed_at`/`notes` instead of `run_id`/`final_status`/`start_ts`/`end_ts`/`summary`) — they could not have been written by the current `record_run.py`, since its `REQUIRED` check would reject a record missing the `workflow` key entirely. They must predate it or bypass it (direct file writes).
- **`events.jsonl`'s `phase` field appears in at least 8 forms for the same concept**: `Implement`, `implement`, `IMPLEMENT`, plus combined values like `Implement+Finalize` and `Investigate+Plan+Implement`.
- **`agent` field has 39 distinct values** where only 11 canonical subagent names are documented — free-text values like `claude`, `orchestrator`, `scope-agent`, `hotfix-agent`, `doc-writer` sit alongside the real ones.
- **`tier` has both `epic-batch` and `epic_batch`** as separate values for what should be one.

The important nuance: `record_run.py` and `record_events.py` **already validate** — both check a `REQUIRED` set of field names and `record_events.py` checks `status` against `VALID_STATUS = {ok, failed, blocked, skipped}`. But that validation only checks that a key is *present*, not that its value is *non-null* or drawn from a *canonical vocabulary*. A call passing `"workflow": null` or `"phase": "IMPLEMENT"` passes validation today. The enforcement exists; its coverage just stops short of the fields that actually drifted.

This matters because every retro report, every future audit, and the two sibling ideas in this folder (`idea_agent_gate_determinism.md`'s `verified_by` field, `idea_agent_cost_observability.md`'s spend-by-phase breakdown) all depend on `phase`/`agent`/`workflow` being queryable without first writing a normalization pass. Left alone, the vocabulary will keep drifting exactly the way it already has.

---

## Idea

Extend the **write-time** validators (`record_run.py`, `record_events.py`) and the **read-time** linter (`tools/agent-monitoring/validate.py`, which already parses both files for other checks) with two independent layers:

### 1. Non-null enforcement on required fields (write-time)

`REQUIRED - set(record.keys())` catches a missing key; it doesn't catch `{"workflow": null, ...}`. Add a second check: any key in `REQUIRED` whose value is `None` fails validation the same way a missing key does. Cheap, unambiguous, no vocabulary maintenance required.

### 2. Canonical vocabulary check (write-time, warn — not reject — initially)

For `phase` and `agent`, maintain a known-good set per workflow (the set this very ticket just had to enumerate for `create-tickets` in `schema.md`: `Comprehend`/`Investigate`/`Structure`/`Write`/`Link`, vs. `implement-ticket`'s `Scope`/`Investigate`/`Plan`/`Review`/`Implement`/`Test`/`Parity`/`Verify`/`Finalize`). A value outside the known set for that `workflow` doesn't get rejected — new legitimate phases/agents will appear as workflows evolve — but it gets a `WARNING: unrecognized phase 'IMPLEMENT' for workflow 'implement-ticket' (did you mean 'Implement'?)` printed to stderr at write time, so drift is visible the moment it's introduced instead of discovered months later in an audit.

### 3. Drift report (read-time, `validate.py`)

`make agent-monitoring-validate` already exists and already loads both files. Add a summary section: count of null-required-field records, a frequency table of `phase`/`agent`/`tier` values that don't match the canonical set for their `workflow`, so a maintainer sees drift accumulating in the regular validation pass rather than needing to run an ad hoc investigation (like the one that produced this idea) to notice it.

---

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `tools/agent-monitoring/record_run.py` / `record_events.py` | Add the non-null check to the existing `REQUIRED` validation branch; add the vocabulary warning as a new, non-blocking check |
| `tools/agent-monitoring/validate.py` | Extend with the drift-report summary described above |
| `docs/agent-monitoring/schema.md` | Already had to be updated with `create-tickets`'s phase list and `tier: "n/a"` as part of the sibling ticket — this idea is what stops the *next* new workflow from silently reintroducing the same kind of drift instead of documenting it |
| [`idea_agent_gate_determinism.md`](idea_agent_gate_determinism.md) | Shares the same underlying principle: make an implicit thing (which gate-check passed, which vocabulary a value belongs to) explicit and checkable, rather than trusting free text |
| [`idea_agent_cost_observability.md`](idea_agent_cost_observability.md) | A spend-by-phase breakdown is only meaningful if "phase" means one consistent thing — this idea is close to a prerequisite for that one's retro-report payoff, not just a parallel concern |

---

## Open Questions

- Should the vocabulary check ever graduate from `warn` to `reject`? Rejecting outright risks a workflow crash over a bookkeeping mismatch — the existing hard rule ("monitoring write failure must never fail the workflow") argues for keeping it a warning indefinitely, but that means it still relies on someone reading stderr.
- Should the canonical phase/agent sets live in `schema.md` (documentation, human-maintained) or in a small JSON/YAML sidecar that both the docs and the validators read from a single source of truth? Two copies is exactly the kind of drift this idea is trying to prevent elsewhere.
- Is per-`workflow` vocabulary scoping (as opposed to one global set) worth the maintenance cost, given the repo will likely add more workflows over time and each one gets its own phase names?
- Does the non-null check risk breaking any current caller that passes `null` intentionally for a genuinely-unknown value — is there a legitimate case for `"workflow": null` today that this would newly reject?

---

*Raised: 2026-07-04, directly from investigating actual runs.jsonl/events.jsonl data (not just the docs) while scoping TCK-20260704-CREATE-TICKETS-MONITORING. Deferred — historical data is explicitly left untouched per the decision made when this was raised.*
