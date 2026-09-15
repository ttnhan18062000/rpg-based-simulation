# Investigation — TCK-20260915-MONITORING-ANOMALY-VALIDATOR

Scoped LAST per the epic's own explicit instruction, encoding tickets 1-7's confirmed causes
rather than this ticket's own original hypotheses.

## Mapping the ticket's own 6 candidate checks to sibling-ticket reality

| Candidate check | Disposition |
|---|---|
| Duplicate run records | Already built: `duplicate_run_record_check.py` (ticket 1). Reused directly. |
| `seq` uniqueness/contiguity | Already built: `event_seq_integrity_check.py` (ticket 4). Reused directly. |
| `tool_call_count` vs `tools.jsonl` | Already built: `tool_call_count_mismatch_check.py` (ticket 3). Reused directly. |
| `ts` shape, `unknown-week` rows | Already built: `monitoring_integrity_backlog_check.py` items 4/5 (ticket 7). Reused via its own `find_unusable_ts_records`/`count_unknown_week_rows` helpers directly — NOT item 2 (missing run record), which is a presence check (`validate.py`'s own domain), not a coherence check (this ticket's domain). |
| Vocabulary conformance (agents/tiers) | **Not yet built anywhere — investigated fresh, see below.** |
| working_log 6-column schema | **Already fully FIXED** by ticket 7 (writer safe forward, 9 historical rows repaired, structurally protected by a sole-writer test). A genuinely-achieved, guarded zero does not need a new ratchet entry. |

## Vocabulary conformance — the ticket's own example numbers were all wrong

The ticket's Scope cited three specific examples as "non-canonical agents": `orchestrator` (144),
`concern-investigator` (6), `context-packet-wrapper` (1). Re-measuring `validate.py`'s own
`compute_drift_report` machinery against the real corpus found:

- `orchestrator`: 401 occurrences at first measurement, 501 confirmed independently minutes later
  by the peer session that originally scoped this candidate (corpus still growing during this
  epic's own work) — not 144. Spans 2026-06-22 through (at least) 2026-09-12, distributed across
  every real pipeline phase (Finalize, Scope, Test, Implement, Parity, Verify) at hundreds of
  occurrences each. This is `vocabulary.py`'s own already-documented "orchestrator itself logging
  an event with no delegated subagent" category (the same reason `"claude"` was registered) —
  simply not yet added under that exact literal.
- `context-packet-wrapper`: 59, not 1. A named constant (`tools/retrieval_events.py:305`,
  `AGENT_PACKET = "context-packet-wrapper"`), read by `implement-ticket.js:607`/`:632`, and its
  `seq <= 0` shadow rows are already documented as intentional
  (`docs/agent-monitoring/schema.md`'s `seq` field row, `TCK-20260729-SHADOW-PACKET-CALL-SITE`).
- `concern-investigator`: a real, currently-registered subagent (`.claude/agents/concern-investigator.md`
  exists, `create-tickets.js` references it) simply missing from `vocabulary.py`'s
  `WORKFLOW_AGENTS["create-tickets"]` set.

Further investigation (not named in the ticket, found by direct corpus query) surfaced 3 more
instances of the identical "real mechanism, missing from the registry" pattern:

- `implement-ticket` (138) and `implement-epic` (16) as agent literals under their own
  same-named workflow — the workflow's own name used as a self-referential "the orchestrator of
  this workflow did it directly" label.
- `write-sequence` (5) — `create-tickets.js`'s real Write-phase `writeSidecar`/`pushEvent` label
  (`create-tickets.js:844`, `:856`; also named in `docs/agent-monitoring/schema.md`'s own
  `tool_call_count` field row as one of create-tickets' 4 real computed call sites).

All 6 were registered in `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS`, each with a
comment documenting what it is and how it was confirmed, matching that file's own existing
standard (`"confirmed by grepping every pushEvent(...) call site"`).

**The genuine residual after registering all 6**: 162 agent-literal occurrences (verified as
historical, not an active writer — the largest identifiable sub-clusters, model-name-as-agent-identity
and alternate-role-naming, stop entirely in 2026-07 with nothing since) and 2 tier-literal
occurrences (`epic_batch`/`epic-batch`, real typo-variants of the canonical `"epic"` tier — too
rare and too clearly wrong-spelling to register as canonical). This residual IS ratcheted.

**Separately noted, not ratcheted**: 258 events have no `agent` field at all (a field-absence, not
a wrong-literal — a different check shape than this drift computation covers). Confirmed
historical (185 in 2026-06, 19 in 2026-07) and partially overlapping with
`monitoring_integrity_backlog_check.py`'s own item-4 unusable-ts ratchet (54 of the 258 also have
no parseable `ts`). Documented in the validator module's own docstring rather than silently
dropped, per this epic's own "accept-and-document is legitimate, silent-drop is not" standard.

## Why the peer's own candidate-check framing was corrected, not blindly implemented

The peer session that scoped this ticket independently re-derived the same three example numbers
and found them all wrong too (its own message: "This is the fourth premise of mine you have
corrected in this epic... concern-investigator is in the agent roster I carry in context, and
vocabulary.py already documented the orchestrator-pseudo-agent category I was calling drift").
This is the exact "vague leads stay vague until evidence narrows them" discipline this repo's own
Uncertainty Rule names, applied at the ticket-scoping level, not just the implementation level —
consistent with every other ticket in this epic.
