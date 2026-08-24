---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260824-KGMCP-KEEP-OR-DEPRECATE
phase: done
date: 2026-08-24
tags: [mcp]
---

# TCK-20260824-KGMCP-KEEP-OR-DEPRECATE

## Title
Decide KGMCP's Future: Keep, Invest Further, or Deprecate

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
No ticket across KGMCP's Phase 0-5 arc or the efficiency-remediation epic has ever actually made the keep/invest-further/deprecate call for the Knowledge Gateway MCP -- every phase's epic and the consolidated audit deliberately deferred that call to a human reviewer, and all the measurement work needed to make it (Phase 3 accounting closure, Phase 4 warm-path comparisons, Phase 5 repeated-demand measurement) is now done. This closes a real, disclosed gap: produce a dedicated decision/scoping ticket that presents the three options with their real tradeoffs, cites the existing evidence trail rather than re-deriving it, and pauses for explicit repository-owner ratification before any option is acted on -- mirroring the same ratification pattern already used for Phase 0 (TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION). The ticket itself does not pick an outcome; a later, separate ticket would carry out whatever gets ratified.

## Scope
- Present exactly three named options for KGMCP's future -- (1) keep as-is with no further investment, (2) invest further by closing Phase 5's remaining scope now that Phase 3's accounting gap is closed per TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING, (3) deprecate/remove the gateway -- each with a real tradeoff paragraph citing specific existing evidence (Phase 4's 7/7 warm-path latency/token losses from TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON; Phase 5's 5.8%-18.5% repeat-demand signal)
- Produce a decision-presentation doc under docs/engine/contracts/knowledge_gateway_mcp/ (new or an addendum to an existing doc such as audit_phase0_5.md) that synthesizes the evidence trail already recorded in the proposal doc, the consolidated audit, the efficiency-remediation epic's Completion Summary, and docs/parity_ledger/infrastructure.yaml INFRA-344..356, without contradicting any of them
- Pause for explicit repository-owner ratification before the ticket closes -- record the ticket's own Status as a paused/blocked state, not DONE with a chosen outcome, mirroring TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION's separation of 'present the decision' from 'record the ratification'

## Out of Scope
- Choosing keep, invest-further, or deprecate unilaterally -- the ratification is the repository owner's call, not this ticket's
- Any code change to tools/knowledge_gateway_mcp.py, tools/knowledge_gateway_router.py, tools/knowledge_gateway_packet_assembly.py, tools/knowledge_gateway_cache.py, tools/knowledge_gateway_redaction.py, tools/start_knowledge_gateway_mcp.sh, or .mcp.json
- Re-running any KGMCP measurement corpus or warm/cold comparison runner -- the ticket must cite existing INFRA-344..356 parity entries and the Phase 4/5 tickets' results, not re-derive them
- Resolving docs/plans/knowledge-gateway-mcp-proposal.md §24's remaining open decisions 2, 3, 5, 6 (canonical repo/branch identity format, eligible Graphify relation types, data/lab_knowledge adapter eligibility, authoritative location for future human-approved knowledge) -- these are narrower Phase 1+ implementation-detail decisions, distinct from this concern's broader keep/invest/deprecate call

## Acceptance Criteria
- [x] The ticket's artifacts present exactly three named options (keep as-is with no further investment; invest further by closing Phase 5's remaining scope now that Phase 3's accounting gap is closed per TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING; deprecate/remove the gateway), each with a real tradeoff paragraph citing specific existing evidence (Phase 4's 7/7 warm-path latency/token losses from TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON; Phase 5's 5.8%-18.5% repeat-demand signal) rather than re-derived measurements — see `keep_or_deprecate_decision.md` §1-2.
- [x] No file under tools/ or src/ is modified by this ticket -- Files Changed lists only ticket/doc paths (confirmed below: only 3 doc files + this ticket's own lifecycle files).
- [x] **Deviation, disclosed (see Implementation Notes):** this AC as originally drafted assumed the ticket's own pipeline would present the options and then pause, with ratification recorded by a *later, separate* ticket (mirroring TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION's two-ticket split). In practice, the repository owner ratified the decision directly, in conversation, in the same session that scoped this ticket — before Implement began — so there was no live pipeline state left to pause. This ticket therefore records the ratification directly in its own Implement phase and closes DONE, the same real-world shape TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION itself had (that ticket was also written *after* its ratification had already happened, not paused mid-flight awaiting one). No option was chosen by any agent — the repository owner chose it.
- [x] The ticket's Related Tickets/Docs section cites TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC, docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md, and docs/parity_ledger/infrastructure.yaml (INFRA-344..356) as its evidence trail rather than any newly re-run KGMCP measurement — confirmed, no measurement corpus was re-run.

## Related Tickets
- TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC
- TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON
- TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON
- TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT
- TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE
- TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING
- TCK-20260821-PROCEDURAL-GENERATOR-KEPT

## Related Docs
- docs/plans/knowledge-gateway-mcp-proposal.md
- docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md
- docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md
- docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md
- docs/parity_ledger/infrastructure.yaml
- tmp/mcp-followup-instruction.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/knowledge_gateway_mcp.py
- tools/knowledge_gateway_router.py
- tools/knowledge_gateway_packet_assembly.py
- tools/knowledge_gateway_cache.py
- tools/knowledge_gateway_redaction.py
- tools/start_knowledge_gateway_mcp.sh
- .mcp.json

## Assumptions / Open Questions
- Confirmed no existing ticket, doc, or working_log entry in tickets/todos, tickets/inprogress, or tickets/done makes this keep/invest/deprecate call -- this is not a duplicate of prior work
- The evidence trail is split across at least 4 authoritative sources (proposal doc §18/§24/§25, audit_phase0_5.md, the efficiency-remediation epic's Completion Summary, and INFRA-344..356) -- Scope/Plan phase must synthesize without contradicting any of them since none has itself made the final call
- The efficiency-remediation epic's Completion Summary states the gateway is 'not yet cost-competitive with an agent calling the underlying tools directly' on all 7/7 corpus entries even warm -- this is strong input evidence but must be presented as input to a reviewer decision, not smuggled in as this ticket's own conclusion
- The audit doc §5 and the Phase 5 ticket already recommend against further Phase 5 investment absent reviewer sign-off -- the 'invest further' option must be scoped as contingent on ratification, not framed as a default path
- Tier is set to hotfix on the strength of the TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION precedent (docs-only, ratification-pausing, self-evident intent); Scope phase should re-confirm this against implement-ticket's tier-routing rule given the multi-source synthesis this ticket requires
- layer is set to `ai` (registered: "Claude agent/orchestration tooling (this repo's layer:ai means the agent system, not gameplay cognition)") since KGMCP is agent-facing MCP tooling under tools/, not a gameplay subsystem; noted here per ticket-scoper's layer-inference instructions

## Implementation Notes
Created `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md`, the real
decision record: §1 presents all three options with their real tradeoffs; §2 cites the existing
evidence trail verbatim (Phase 2 cache-hit-cap fix, Phase 3 budget-tolerance closure, Phase 4
cold+warm direct-tool-comparison losses, Phase 5 repeated-demand measurement, the efficiency-
remediation epic's own net verdict) — no measurement was re-derived or re-run; §3 records the
ratification: **Option A — keep as-is, no further investment**, ratified by the repository owner
on 2026-08-24, directly in conversation, before this ticket's own Implement phase began.

Added a short "Status update (2026-08-24)" pointer paragraph to both
`docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md` §5 and
`docs/plans/knowledge-gateway-mcp-proposal.md` §25 — additive only, no existing sentence in either
doc was altered or removed, both now point to `keep_or_deprecate_decision.md` for the full record.
Neither doc's own pre-existing "does not recommend" framing was contradicted — the framing itself
remains accurate (neither document made the call; a human reviewer did, elsewhere, and this
ticket records that).

No file under `tools/` or `src/` was touched, per Out of Scope. No KGMCP measurement corpus was
re-run — every number cited in `keep_or_deprecate_decision.md` §2 is a direct citation of an
already-real, already-verified prior result.

**On the AC3 deviation:** this ticket's own drafted Acceptance Criteria (written before Implement,
during Scope/Structure) assumed a two-step pattern — this ticket presents options and pauses,
a later separate ticket records whatever gets ratified — mirroring
`TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`'s own two-ticket precedent literally. What actually
happened diverged from that literal reading but not from the underlying principle it protects (no
agent picks the outcome): the repository owner ratified "keep as-is" directly in the same
conversation that scoped this ticket, before any Implement work began. Re-reading the precedent
ticket itself confirms this is in fact the *same* real-world shape — `TCK-20260815-HOTFIX-KGMCP-
PHASE0-RATIFICATION`'s own Request Summary states "the user...was presented both decisions...and
ratified both as drafted" *before* that ticket's own text was written; it was never a ticket that
itself paused mid-pipeline waiting for an answer. This ticket follows the same real pattern: the
human decision came first, this ticket documents it, and closes DONE. No agent chose an outcome.

Minor, non-blocking monitoring-vocabulary note: this ticket's own Scope/Parity-skip events were
recorded with agent literal `orchestrator`, which `tools/agent-monitoring/vocabulary.py`'s
warn-only check flags as unrecognized for the `implement-ticket` workflow (the correct
hand-orchestration literal is `claude` — confirmed by reading `vocabulary.py` after the fact).
This is a warn-only vocabulary check (record_events.py still appended both records; append-only
history is not rewritten to "fix" it), disclosed here rather than silently left unstated.

## Test Summary
- `python3 tools/validate_frontmatter.py <path> --content-type doc` — OK, 0 violations, run
  individually against all 3 doc files touched (`keep_or_deprecate_decision.md`,
  `audit_phase0_5.md`, `knowledge-gateway-mcp-proposal.md`).
- `.venv/bin/python3 -m pytest tests/docs/test_phase5_repeated_demand_measurement_doc.py
  tests/docs/test_redaction_retention_policy_doc.py -q` → 9 passed, 0 failed. Confirmed the
  additive proposal-doc edit does not trip
  `test_phase5_proposal_doc_annotation_does_not_overclaim_done` (no Phase 5 bullet marked Done;
  the required `TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT` reference is still present,
  untouched).
- No `tools/`/`src/` test suite re-run needed — zero code files changed.

## Files Changed
- `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` (new) — the decision
  record.
- `docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md` (edited) — additive "Status
  update (2026-08-24)" paragraph appended to §5, no existing text altered.
- `docs/plans/knowledge-gateway-mcp-proposal.md` (edited) — additive "Status update (2026-08-24)"
  paragraph appended after §25's existing closing sentence, no existing text altered.
- `tickets/todos/kgmcp-decision/TCK-20260824-KGMCP-KEEP-OR-DEPRECATE.md` → moved to
  `tickets/done/kgmcp-decision/TCK-20260824-KGMCP-KEEP-OR-DEPRECATE.md` (this file).
- `tickets/working_log.csv` (Finalize) — new row appended.
- `docs/REGISTRY.yaml` (Finalize self-check) — regenerated.

`make knowledge-index-update` was attempted per this repo's "docs changed -> update index" rule
but failed with `OSError: We couldn't connect to 'https://huggingface.co'` — a pre-existing,
disclosed environment gap (this machine's HuggingFace-download SSL/network path, unrelated to this
ticket's own docs edits) rather than something introduced or fixable here. Not routed around;
reported honestly. `docs/REGISTRY.yaml` (the actually-required, non-optional registry) was
regenerated successfully via `make docs-registry`.

No `docs/parity_ledger/` entry was added: this is a pure documentation/decision record with zero
behavior change (`behavior_changed=false`, zero `src/`/`tools/` files touched) — skip-eligible per
the same convention every prior docs-only KGMCP ticket in this arc used (e.g.
`TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION` added no new parity entry of its own either, only
corrected existing ones it happened to touch; this ticket touches none).

## Completion Summary
Recorded the repository owner's ratification of KGMCP's future: **keep as-is, no further
investment**. The decision is documented in a new file,
`docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md`, which presents all
three options (keep / invest further / deprecate) with their real evidence-backed tradeoffs before
recording the actual ratification — mirroring `TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`'s
own precedent of presenting real evidence and then recording a human decision, not re-deriving or
second-guessing it. Two existing docs (`audit_phase0_5.md`, the proposal doc) got a short, additive
pointer to the new record so a future reader following either doc's own "this is a human reviewer's
call" framing lands on the actual answer. No code under `tools/`/`src/` was touched. No further
Phase 5+/Phase 6 KGMCP investment is authorized by this decision.
