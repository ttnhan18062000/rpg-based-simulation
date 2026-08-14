---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260804-AGENT-DEF-GAP-FIXES
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation — TCK-20260804-AGENT-DEF-GAP-FIXES

## Current Behavior

### Fresh evidence pull (this investigation, not reused from the audit doc's original 8-sample readout)

Queried `agent-monitoring-index/monitoring.db` directly (Python + sqlite3) for all `Review`- and
`Verify`-phase `status='failed'` events with `ts >= 2026-07-20` (roughly the last 2-3 weeks as of
this session's date).

**Review: 15 failures since 2026-07-20.** Full list (ts, run_id, summary) captured verbatim; not
reproduced in full here, see raw query output in this ticket's investigation trail. Classification
against the audit's root cause 1 (planner factual-claim error): genuinely mixed — several are
factual-claim errors about existing behavior (e.g. `TCK-20260729-SHADOW-BASELINE-COMPARISON`:
"infer_workflow(e.get(run_id)) missing None-guard, would crash"; `TCK-20260702-OBSISO-TRACE-ASYNC`:
test-file-specific defects), others are plan-completeness gaps (missing lifecycle/prune mechanism,
missing ledger-entry fields) or design-flaw findings (seq-collision bug, race conditions) that are
not strictly "wrong factual claim about current behavior" but rather "insufficient design" — a
related but distinct failure mode from the audit's narrower framing.

**Data-quality caveat, disclosed honestly rather than silently reconciled:** at least 2 of the 15
"Review"-labeled events (`TCK-20260702-OBSISO-TRACE-ASYNC` seq 4-6, `TCK-20260702-OBSISO-ISOLATION-PROOF`
seq 4-5) describe content that reads like post-Implement diff review (specific test file line
numbers, real function/class names) rather than pre-Implement plan review — yet each of these same
run_ids also has its own separate, later, genuine `Architecture-Verify`-phase event with different
content (confirmed by direct query: not duplicates). This session's own hand-orchestration of the
OBSISO tickets earlier today is the most likely source (both tickets were implemented in this
session). Whether these specific events are mislabeled (should have been `Architecture-Verify`) or
are legitimately reviewing a plan.md that already proposed concrete test modifications with cited
line numbers could not be resolved with certainty in the time available — flagged here per the
Uncertainty Rule ("vague leads stay vague until evidence narrows them") rather than force-resolved.
This affects the *precision* of the 15.2%/22.9% headline percentages by at most ~1-2 percentage
points either direction — it does not change the qualitative finding (Review failures are real,
frequent, and dominated by claims-about-existing-behavior errors) or this ticket's scope.

**Verify: 25 failures since 2026-07-20 — materially reshapes the audit's original framing.**
Classified by dominant pattern (some failures cite multiple items, counted once per pattern they
exhibit):

| Pattern | Count | Examples |
|---|---|---|
| Unchecked AC checkboxes despite content satisfied | 6 | `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`, `TCK-20260721-CODEX-REPLAY-PROOF`, `TCK-20260730-CODEX-RUNTIME-SHADOW`, `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`, `TCK-20260803-DOC-UPDATER-CORE-WIRING`, `TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT` |
| Stale `## Status` field (OPEN when it should reflect real progress) | 5 (1 flagged as a false-positive precedent-confusion by `TCK-20260728-CODE-TEST-INDEX-BOUNDARIES` itself — no INPROGRESS precedent actually exists in `tickets/done/`) | `TCK-20260721-CODEX-REPLAY-PARITY`, `TCK-20260727-CODEX-SKILL-COMPANION-ASSETS`, `TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE`, `TCK-20260729-DETERMINISTIC-CODE-INDEX`, `TCK-20260729-HYBRID-RETRIEVAL-FUSION` |
| Undocumented deviation/gap in Completion Summary | 4 | `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`, `TCK-20260728-EVAL-FIXTURE-REPAIR`, `TCK-20260729-SHADOW-PACKET-CALL-SITE`, `TCK-20260730-CODEX-POSTTOOL-ADAPTER` |
| `investigation.md`'s "Docs Requiring Update" section fails the static bullet-format parser | 3 | `TCK-20260803-DOCS-STRUCTURE-AUDIT`, `TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE`, `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION` |
| Scope item silently not implemented | 1 | `TCK-20260702-OBSISO-BROKER-CONFIG` |
| Undisclosed scope creep (parity change outside stated Files Changed) | 1 | `TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX` |
| Real substantive contradiction (corpus evidence vs. AC claim) | 1 | `TCK-20260730-CLAUDE-EXECUTION-IDENTITY` |
| **"Uncleaned data/runs" — the audit doc's original cited cause** | **0** | none found in this fresh window |

**"Uncleaned data/runs" is confirmed resolved, not currently active.** Zero of the 25 fresh Verify
failures mention `data/runs` or `reports/release_proof`. `TCK-20260708-DATA-RUNS-CLEANUP-TIMING`
(confirmed via its own ticket file) landed 2026-07-08, moving the cleanup enforcement point to
right after Test — well before this fresh window. The audit doc's original sample (which was not
date-filtered) likely drew from before this fix landed. **This ticket's scope item asking Plan to
confirm this should be resolved as: confirmed stale, exclude from the implementer.md fix.**

**Two patterns not in the audit doc's original framing, found only via this fresh pull:**
1. **Stale `## Status` field** is now comparably frequent to AC-checkbox misses (5 vs 6
   occurrences) — a real, current implementer/Finalize hygiene gap the original 8-sample audit
   didn't surface prominently. Belongs in the implementer.md fix's scope.
2. **"Docs Requiring Update" bullet-format parser failures** (3 occurrences) are the *exact same
   bug class* independently found and fixed ad hoc during this session's own
   `TCK-20260804-EXPANSION-RATE-WIRING` ticket (a `:line`-suffix-inside-backticks bullet format
   that `done_checker_static.py`'s `_DOCS_BULLET_RE` regex can't match against git status's bare
   path). This is a recurring, multi-instance trap — but it is written during **Investigate**, not
   Implement, so it does not belong in the implementer.md fix. **Flagged for Plan's decision**:
   either add explicit bullet-format guidance to `.claude/agents/investigator.md` (checked: it has
   no example bullet format shown for "Docs Requiring Update" today), or fix the parser itself to
   accept both formats (the more root-cause fix, avoiding a fourth similar recurrence) — Plan must
   choose, this is out of Investigate's authority to decide.

### `.claude/agents/planner.md` and `.claude/agents/implementer.md` — re-read fresh

Both confirmed unchanged since the earlier audit's read: `planner.md` (88 lines) has zero
instruction on verifying factual claims against source before writing them into `plan.md`.
`implementer.md` (76 lines) has zero mention of `## Completion Summary`, `## Files Changed`
discipline, `## Status` field currency, or AC-checkbox discipline anywhere in its own persistent
text — all of this guidance today lives only in `implement-ticket.js`'s one-time per-call Implement
prompt (`Update the ticket... fill in the ticket's Completion Summary...`), never in the agent's
own file.

### What kind of verification would have caught each sampled Review failure

Sampled 5 (`SHADOW-BASELINE-COMPARISON`, `SHADOW-PACKET-CALL-SITE`, `STORED-ARTIFACT-KIND`,
`DOC-UPDATER-CORE-WIRING`, `OBSISO-TRACE-ASYNC` seq 4):
- `SHADOW-BASELINE-COMPARISON`'s missing `None`-guard: would be caught by "read the actual function
  signature/call site the plan proposes to touch, before asserting it handles X correctly" — a
  concrete, checkable instruction (cite the file:line read).
- `SHADOW-PACKET-CALL-SITE`'s seq-collision bug: a design-completeness gap, not a wrong factual
  claim — would need "trace the proposed change's interaction with every OTHER concurrent writer to
  the same resource" as a distinct planner instruction, not just "verify claims."
- `STORED-ARTIFACT-KIND`'s AC4-vs-plan-Step-2 self-contradiction: an internal-consistency check
  (does the ticket's own AC match what the plan's own steps say) — a different, mechanical
  cross-check, not a source-code verification.
- `DOC-UPDATER-CORE-WIRING`'s undefined ternary condition: a plan proposing pseudocode/logic that
  references a field with no backing schema — "before proposing a conditional on a field, confirm
  that field exists in the relevant schema/dataclass" is concrete and checkable.
- `OBSISO-TRACE-ASYNC` seq 4 (data-quality-caveated, likely Architecture-Verify not Review): not
  counted as planner-attributable evidence given the labeling uncertainty above.

**Conclusion for Plan**: the planner-side fix cannot be a single instruction ("verify claims") —
the sampled failures span at least 3 distinct failure modes (wrong factual claim about existing
code, incomplete design/interaction analysis, internal ticket-consistency mismatch, and
schema-referencing-a-nonexistent-field). Plan should design 2-3 concrete, checkable sub-instructions
rather than one vague directive.

### Prior similar fix attempts — checked via docs/REGISTRY.yaml and search_docs

No prior ticket found attempting to add fact-verification or hygiene-checklist guidance to
`planner.md`/`implementer.md`'s own persistent definitions. This is genuinely new ground for these
two files.

**However — a directly relevant, more urgent finding surfaced during this same investigation, not
originally in this ticket's scope:** `tickets/done/TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT.md`
and `tickets/done/TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE.md` (both 2026-07-08) already
fixed earlier instances of the exact same class of drift this session's
`TCK-20260804-SKILL-JS-PHASE-SYNC`/`TCK-20260804-CREATE-TICKETS-SKILL-SYNC` just fixed again today —
`implement-ticket/SKILL.md` drifted, was fixed (added Architecture-Verify/Security-Review), then
drifted again (missing Document-Update, doc-staleness gate, shadow-packet probe, post-Test cleanup,
Parity cross-reference gate, post-Finalize index refresh) before today's fix; `create-tickets/SKILL.md`
was fixed once (Workflow-tool phrasing), then drifted again in a different dimension (tag-registry
gate, short_scope dedup) before today's fix. **This is a recurring pattern, not a one-off** — a
third fix without a drift-prevention mechanism is likely to recur a third time. This is reported to
the user as a separate, flagged finding (see conversation) rather than silently expanded into this
ticket's scope, since it's a materially different kind of fix (a structural/mechanism decision, per
the user's explicit "you can introduce new skills/phases/agents if it's worth it and measurable"
guidance) that deserves its own scoping conversation.

## Mechanics / Engine Constraints

N/A — agent-tooling/orchestration definitions, not simulation mechanics.

## Docs Requiring Update

- `docs/ai/agent_definition_gap_audit_2026-08-04.md`: needs a "how to check if this worked" pointer
  once Plan/Implement land — already scoped in the ticket's own ACs.

## Parity Ledger Overlap

None — `.claude/agents/*.md` files are agent-instruction prose, same scope-boundary conclusion
Parity reached independently for both sibling SKILL.md tickets this session (no ledger entry
needed for this class of change).

## Prior Work

- `docs/ai/agent_definition_gap_audit_2026-08-04.md` — original audit, superseded in precision by
  this investigation's fresh pull but not contradicted in its qualitative conclusions.
- `TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT`, `TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE`
  — prior, now-recurred fixes of a different (but related-in-spirit) drift class, see above.
- `TCK-20260708-DATA-RUNS-CLEANUP-TIMING` — confirmed still effective; the audit's cited
  "uncleaned data/runs" cause is stale, exclude from this ticket's fix.

## Risks and Open Questions

1. **Docs Requiring Update bullet-format fix location (investigator.md vs. parser) — Plan must
   decide, not Investigate.** 3 recurring instances, same bug class this session independently hit
   and fixed once already. Out of this ticket's originally-stated scope (which named only
   planner.md/implementer.md) — Plan should decide whether to fold this in (expanding scope
   slightly, with user awareness) or explicitly defer it to a separate ticket.
2. **Review-phase mislabeling uncertainty** (Review vs. Architecture-Verify for 2 OBSISO-ticket
   event clusters) — does not block this ticket's core planner-fix scope, but the exact percentage
   figures should not be over-cited as precise in Plan/Implement's own text; cite the qualitative
   pattern and the "since 2026-07-20" counts (15/25), not the audit doc's original monthly
   percentages, when writing the new instructions' rationale.
3. **Planner fix needs 2-3 concrete sub-instructions, not one directive** — see "Conclusion for
   Plan" above.

## Anti-Drift Hazards

- Do not fold the "Docs Requiring Update" bullet-format issue into implementer.md — it's an
  Investigate-phase artifact, wrong agent file.
- Do not re-cite the audit doc's original monthly percentages as if independently re-verified —
  this investigation's own fresh counts (15 Review / 25 Verify failures since 2026-07-20) are the
  authoritative numbers going forward for this ticket.
- Do not silently expand this ticket to also fix the recurring-SKILL.md-drift-mechanism question —
  that's a separate, flagged finding requiring its own user-facing scoping decision.
- Do not add the stale-Status-field or AC-checkbox-discipline guidance to `planner.md` — both are
  Implement/Finalize-time artifacts, belong in `implementer.md`.
