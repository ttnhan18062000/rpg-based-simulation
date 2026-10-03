---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX
phase: done
date: 2026-07-20
tags: [tagging, workflows]
---

# TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX

## Title
Fix create-tickets.js's Structure phase over-restricting tags to Process/Skill-signal only, on a stale citation

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
User noticed a real inconsistency while reviewing 4 tickets just batch-created by `/create-tickets`
(the `progress-timeline` folder): all 4 came out with either an empty `tags: []` or only a single
`api-design` tag, while sibling tickets covering the exact same subsystem (e.g.
`TCK-20260718-STATS-TAB-FRONTEND`: `[dashboard]`, `TCK-20260719-AGENT-ROLE-GLOSSARY`:
`[dashboard, observability]`) carry real Subsystem/Topic tags. Root cause traced directly:
`.claude/workflows/create-tickets.js`'s Structure-phase prompt (~line 503-506) explicitly instructs
"Do NOT assign Subsystem/Topic, Phase/Milestone, or Quality-attribute tags ... deferred to a
separate ticket, TCK-20260705-TAG-REGISTRY-QUERY" — restricting batch-created tickets to only the
Process/Skill-signal category (`api-design`/`debugging`/`performance`/`security`). But
`TCK-20260705-TAG-REGISTRY-QUERY` (read in full: `tickets/done/TCK-20260705-TAG-REGISTRY-QUERY.md`)
is not about tag assignment at all — its actual scope was extending `docs/REGISTRY.yaml`'s
*prior-work search* to filter by tags (`tools/registry_query.py`). The citation does not justify
the restriction it's attached to; it appears to be a stale or mistaken reference left in the
workflow code, not a real, still-open deferral. Meanwhile `.claude/agents/ticket-scoper.md` — the
agent used both for single-ticket scoping and (nominally) for `create-tickets.js`'s own Write
phase — has no such restriction; its own tags instruction just says to follow
`docs/guidelines/tag_taxonomy.md`'s full 5-category taxonomy. This means the two ticket-creation
code paths in this repo (batch via `create-tickets.js`'s Structure phase vs. single-ticket via
`ticket-scoper`) currently encode two different, contradictory tagging policies for the same kind
of ticket.

## Scope
- In `.claude/workflows/create-tickets.js`'s Structure-phase prompt (the `tags:` rules block, current
  lines ~503-506), remove the incorrect citation of `TCK-20260705-TAG-REGISTRY-QUERY` and the
  blanket "Do NOT assign Subsystem/Topic, Phase/Milestone, or Quality-attribute tags" instruction.
- Replace it with guidance consistent with `ticket-scoper.md`'s own tags instruction and
  `docs/guidelines/tag_taxonomy.md`'s full 5-category model: the Structure-phase synthesis agent
  should be allowed (not required) to assign Subsystem/Topic tags when a concern's investigated
  `files_found`/domain clearly indicates one (e.g. `dashboard-frontend/`/`src/api/agent_ops_dashboard/`
  → `dashboard`; `agent-monitoring/*.jsonl` involvement → `observability`), mirroring how
  `ticket-scoper` already does this for single tickets, while keeping the existing
  Process/Skill-signal mapping table (`api-design`/`debugging`/`performance`/`security` →
  `suggested_skills`) exactly as-is.
- Decide (during Investigate) whether Phase/Milestone and Quality-attribute tags should also be
  back in scope for Structure, or whether Subsystem/Topic alone closes the gap that actually caused
  this — do not over-scope the fix beyond what the evidence supports.
- Update `docs/guides/ticket_tagging.md` and/or `docs/guidelines/tag_taxonomy.md` if either
  currently implies (or fails to clarify) that batch-created tickets follow a narrower tagging
  policy than single-ticket ones — the two paths should be documented as following the same policy
  once this is fixed.

## Out of Scope
- Retroactively re-tagging the full ticket corpus for prior batches created under the old
  restricted behavior — this ticket fixes the workflow going forward only.
- The 4 `progress-timeline` tickets this bug was found on already had their tags manually
  corrected in the same session this bug was found (`dashboard`, `observability`, and (for the API
  ticket) `agent-monitoring` added) — not re-touched by this ticket.
- Any change to the Process/Skill-signal → `suggested_skills` mapping table itself (`api-design`,
  `debugging`, `performance`, `security`) — that logic is correct and unaffected.
- Any change to `ticket-scoper.md`'s own (already-correct) tags instruction.

## Acceptance Criteria
- [ ] `.claude/workflows/create-tickets.js`'s Structure-phase prompt no longer cites
      `TCK-20260705-TAG-REGISTRY-QUERY` as justification for restricting tags to Process/Skill-signal
      only.
- [ ] Running `/create-tickets` on a proposal whose concerns clearly belong to a registered
      Subsystem/Topic tag (e.g. a dashboard-frontend/agent-monitoring proposal, matching this
      ticket's own originating case) produces tickets with that Subsystem/Topic tag populated, not
      an empty or Process/Skill-signal-only `tags` array.
- [ ] The existing Process/Skill-signal → `suggested_skills` behavior (verified by
      `TCK-20260705-TAG-SKILL-SUGGEST`'s acceptance criteria) is unchanged and still passes.
- [ ] `docs/guides/ticket_tagging.md` and/or `docs/guidelines/tag_taxonomy.md` accurately describe
      one consistent tagging policy across both `create-tickets.js` (batch) and `ticket-scoper`
      (single-ticket) paths.

## Related Tickets
- TCK-20260705-TAG-SKILL-SUGGEST (introduced the Process/Skill-signal → suggested_skills mapping this fix preserves)
- TCK-20260705-TAG-REGISTRY-QUERY (the ticket incorrectly cited as justification — actually about REGISTRY.yaml search, unrelated to tag assignment scope)
- TCK-20260704-TAG-TAXONOMY (defined the full 5-category taxonomy this fix realigns Structure phase with)
- TCK-20260720-BULK-RUN-TIMELINE, TCK-20260720-ECHARTS-PHASE-PALETTE, TCK-20260720-PROGRESS-TIMELINE-VIEW, TCK-20260720-TIMELINE-RANGE-CONTROL (the 4 tickets whose under-tagging surfaced this bug; manually corrected already, not blocked on this fix)

## Related Docs
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/create-tickets.js
- .claude/agents/ticket-scoper.md
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md

## Assumptions / Open Questions
- Assumes the fix should bring `create-tickets.js` up to `ticket-scoper.md`'s existing (already
  full-taxonomy) behavior, rather than the reverse (further restricting `ticket-scoper.md`) — this
  matches the taxonomy docs' own stated intent (5 categories, not 1) and the observed pattern that
  richly-tagged tickets in the corpus are the norm, not the exception.
- Open question for Investigate: whether the original author of the Structure-phase restriction had
  an unstated reason (e.g. avoiding low-confidence tag guesses in a fully-automated batch pipeline
  with no human in the loop per-ticket) that should be preserved as a narrower guardrail (e.g.
  "only assign a Subsystem/Topic tag when investigation evidence is unambiguous") rather than
  removing the restriction outright.

## Implementation Notes
- `.claude/workflows/create-tickets.js`:
  - `TASK_SCHEMA.properties.tags.description` (was line 373): removed the "limited to Process/Skill-signal detection... deferred to TCK-20260705-TAG-REGISTRY-QUERY" text; now points at `docs/guidelines/tag_taxonomy.md`'s full 5-category model, matching the schema description style already used elsewhere in the file.
  - Structure-phase `tags:` prompt rule block (was lines 503-506): removed the stale `TCK-20260705-TAG-REGISTRY-QUERY` citation and the blanket "Do NOT assign Subsystem/Topic, Phase/Milestone, or Quality-attribute tags" instruction. Replaced with guidance that (a) follows the full 5-category taxonomy, mirroring `ticket-scoper.md`'s own instruction, (b) keeps the existing Process/Skill-signal closed-list-of-4 rule verbatim (unchanged, per Out of Scope), and (c) adds an explicit evidence guardrail — only assign a Subsystem/Topic (or Phase/Milestone/Quality-attribute/Meta-Process) tag when the concern's investigated `files_found`/domain clearly supports it (with the ticket's own `dashboard` / `observability` examples inlined), never guessed from the title alone. This resolves the Assumptions/Open Questions item: rather than a blanket re-open, the fix carries forward a narrower "evidence-grounded" guardrail so a fully-automated batch pipeline doesn't emit low-confidence tag guesses.
  - `suggested_skills` mapping table (lines ~508-517) and its 4-tag closed list were left untouched, per Out of Scope.
- `docs/guides/ticket_tagging.md`: added a paragraph after the `suggested_skills` intro clarifying that both `create-tickets.js` (batch) and `ticket-scoper` (single-ticket) now follow the same full 5-category taxonomy for tag assignment, not just the Process/Skill-signal slice that feeds `suggested_skills` — closing the gap where the doc described the shared `suggested_skills` behavior but never stated the two paths' tag-assignment scope was otherwise identical.
- `docs/guidelines/tag_taxonomy.md` was checked and contains no reference to `create-tickets.js`, batch tickets, or the stale deferral — left unmodified (no inaccuracy to fix there).
- Verified no other reference to `TCK-20260705-TAG-REGISTRY-QUERY` or the "Do NOT assign" restriction remains anywhere in `.claude/workflows/create-tickets.js` or `.claude/agents/`.

## Test Summary
- `node --check .claude/workflows/create-tickets.js` — passes (no syntax errors introduced).
- `python3 -m pytest tests/tools/test_tag_skill_mapping_check.py -q` — 10 passed (Process/Skill-signal → `suggested_skills` mapping, AC 3, unaffected).
- `python3 tools/tag_skill_mapping_check.py` — exit 0 (markdown table in `ticket_tagging.md` and JS-escaped table in `create-tickets.js` still consistent).
- `python3 -m pytest tests/tools/test_workflow_meta_conformance.py -q` — 14 passed, 1 xfailed (pre-existing xfail, unrelated).
- New: `tests/tools/test_create_tickets_tag_scope.py` (added during Verify remediation, 5 tests) — reads the live `.claude/workflows/create-tickets.js` source and asserts: the stale `TCK-20260705-TAG-REGISTRY-QUERY` citation is gone, the blanket "Do NOT assign Subsystem/Topic" restriction is gone, the full-5-category `tag_taxonomy.md` guidance is present, the evidence guardrail (`files_found` / "Do not guess a tag from the title alone if files_found doesn't support it") is present, and the untouched Process/Skill-signal 4-entry mapping table is still intact. Confirmed as a real regression guard (not a tautology) by checking the assertions against the ticket's own quoted pre-fix text, which fails them. `python3 -m pytest tests/tools/test_create_tickets_tag_scope.py -q` — 5 passed.

## Files Changed
- `.claude/workflows/create-tickets.js`
- `docs/guides/ticket_tagging.md`
- `tests/tools/test_create_tickets_tag_scope.py` (new, added during Verify remediation)

## Completion Summary
Removed the stale `TCK-20260705-TAG-REGISTRY-QUERY` citation and the blanket Process/Skill-signal-only tag restriction from `create-tickets.js`'s Structure phase (schema description + prompt rule), replacing it with full-5-category guidance mirroring `ticket-scoper.md`, gated by an explicit evidence guardrail (only assign Subsystem/Topic/etc. when investigated `files_found`/domain clearly supports it) so automated batch runs don't emit low-confidence guesses. Clarified in `docs/guides/ticket_tagging.md` that batch and single-ticket paths now follow one consistent tagging policy. Process/Skill-signal → `suggested_skills` mapping was left untouched and its tests still pass. Verify's Definition-of-Done gate initially failed for missing test coverage on the new guardrail text/behavior; remediated by adding `tests/tools/test_create_tickets_tag_scope.py`, which directly asserts the stale citation and blanket restriction are absent and the new evidence-guardrail guidance is present in the live workflow file.
