---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261007-EPIC-RETRO-READABILITY-AND-MONITORING-DATA-HYGIENE
phase: open
date: 2026-10-07
tags: [observability, agent-monitoring, process-improvement]
---
# TCK-20261007-EPIC-RETRO-READABILITY-AND-MONITORING-DATA-HYGIENE

## Title
Epic: make the weekly retro readable and its input data clean, from findings of the 2026-W40 deep retro

## Status
EPIC_SCOPED
## Tier
epic
## Type
chore
## Priority
P3

## Request Summary
The 2026-W40 deep retro (251 runs, 1570 events) hit five problems in the retro and its data. Duplicates were checked first:
- Hand-closure duration and cost coverage is ALREADY covered by TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST (all four children closed, time-gated to the W42 read). NOT re-filed here.
- Skip/path reason fields are covered by TCK-20261006-EPIC-TICKET-PATH-RECORD. NOT re-filed here.
- The knowledge index was not built (`search_docs` returned "index not found"), so this scan used grep over todos/done only. Treat "no duplicate found" as weaker than usual.

## Scope (children, each standard tier, order in SEQUENCE.md when filed)
1. **Retro notes do not accumulate (standard).** `## Notes` keeps every regen's addendum; W40 is 558 lines with older addenda (written at 18, 38, 61 runs) conflicting with final tables. Design: regeneration keeps hand-authored notes (current rule) but a new "Final" block is marked and earlier per-regen addenda are collapsed to a one-line history, or notes carry the run count they were written at and the generator flags notes older than the data. Do not drop hand-written notes silently (TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES).
2. **Retro Failures section (standard).** Add a section listing every non-DONE run and every `failed`/`blocked` event with its one-line summary, grouped by agent and by recurring cause. W40 needed two throwaway scripts to get this. Includes a "failed the same test across tickets" count so a recurring pre-existing test failure is visible. The known-failing-test baseline itself is an owner decision, not part of this child.
3. **Run rows missing `execution_id` (standard).** 2116 run rows across all weeks, ~900 lack `execution_id` (mostly W23-W34 pre-field; W40: 5, W41: 3, W37/W39: 1 each, 5 `unknown-week`). Decide: (a) tolerate and report as "predates", (b) find the writer that still omits it in W40/W41 and fix it. Retro dedupe key is `(run_id, execution_id, start_ts)`, so a missing id weakens it. Also here: two non-canonical tiers (`epic_batch`, `epic-batch`) and 21 rows with tier null; 3 `tools.jsonl` rows skipped by the loader; 14 tickets with 2-4 Scope events at seq 1 (resume collision). Each is a validator warning today (318 total).
4. **Retro directory ownership (standard, tiny).** `agent-working/agent-monitoring/retro/**` is not in agent-working-designer's `owns` in `registries/session_authority.yaml`, yet the retro skill tells the running session to fill `## Notes` and earlier notes were written by that role. Owner decision: add the retro dir to the designer's owns, or record that the retro notes are written by the implementer. Edit `registries/session_authority.yaml` and `session_roles.yaml` only after the decision.
5. **Hook noise (standard).** The context-search PreToolUse hook (`.claude/settings.json`) fires on every Bash call, including pure data analysis on a retro, and said nothing useful. Measure how often it fires versus how often an investigation follows, then narrow it (for example fire only when the command is grep/find/cat on `src/`/`docs/` before a search_docs call this session). Advisory only; no blocking.

## Out of Scope
- Hand-closure duration/cost (already filed). Skip/path reasons (already filed).
- Backfilling or rewriting past shards.
- Any blocking gate over monitoring data.
- Building the knowledge index (separate; `make knowledge-index`).
- Changing the Measurement Watchlist row for DELIVERY-COST-MEASUREMENT.

## Acceptance Criteria
1. Each child is closed or dropped with an owner-recorded reason.
2. The W42 retro's Notes read as one current statement, and a stale-notes warning appears when the notes are older than the data.
3. The W42 retro has a Failures section and no run needs an ad hoc script to list its failures.
4. `make agent-monitoring-validate` warning count for W40+ rows is stated before and after child 3.
5. The owner decision in child 4 is recorded in `registries/session_authority.yaml` or the retro skill.

## Related Tickets
TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST, TCK-20261006-EPIC-TICKET-PATH-RECORD, TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES, TCK-20260915-DUPLICATE-RUN-RECORDS, TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION, TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE, TCK-20261007-RETRO-FAILURES-SECTION, TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE
## Related Docs
docs/agent-monitoring/README.md, docs/agent-monitoring/schema.md, agent-working/agent-monitoring/retro/RETRO-2026-W40.md (final addendum)
## Related Code Areas
tools/agent-monitoring/generate_retro.py, tools/agent-monitoring/validate*.py, .claude/settings.json (hook), registries/session_authority.yaml
## Assumptions / Open Questions
- Counts above come from a read-only sweep on the agent-working-seat worktree (branch at f99cb0c6c) on 2026-10-07.
- `execution_id` omission by week is verified; whether W40/W41 omissions come from one writer is not.
- Child 4 decided 2026-10-07: the agent-working role owns the retro dir (`registries/session_roles.yaml`, same PR). Still open: whether child 5 sits under agent-working or the settings owner.
## Implementation Notes / Test Summary / Files Changed / Completion Summary
2026-10-08: children 1-3 are done in one batch PR: TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE, TCK-20261007-RETRO-FAILURES-SECTION, TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE, plus the planner-added TCK-20261008-VALIDATOR-WORKING-LOG-SHARDS-FALSE-POSITIVE (validator warning count: W40+ 131 of 165 before, 1 of 35 after). Child 4 (retro dir ownership: decided, the agent-working role owns it) and child 5 (hook noise) are not filed, so this epic and its folder stay in todos/ until they are closed or dropped.
