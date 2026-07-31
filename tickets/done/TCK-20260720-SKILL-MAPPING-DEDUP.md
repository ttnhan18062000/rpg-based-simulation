---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-SKILL-MAPPING-DEDUP
phase: open
date: 2026-07-20
tags: [tagging, workflows, skills]
---

# TCK-20260720-SKILL-MAPPING-DEDUP

## Title
Deduplicate the 4-copy process-skill-signal-to-skill mapping table into a single source

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
The Process/Skill-signal-tag to suggested_skills table is manually duplicated across ticket-scoper.md, ticket_tagging.md, implement-ticket.js, and create-tickets.js, with a drift-detector (tools/tag_skill_mapping_check.py) that itself has a hardcoded 5th copy (KNOWN_TAGS) and previously declared dedup out of scope by design — a decision this work reopens. Preferred approach (to be confirmed/refined during Investigate) is to encode the mapping as a triggers_skill-style field directly on each process-skill-signal tag's row in tag_registry.jsonl rather than a new 5th registry file, with all 4 current copies reading from that one place. Investigate should decide whether the drift-detector becomes unnecessary or shrinks to checking that consumers read the live source.

## Scope
- resolve the append-only-vs-existing-rows conflict during this ticket's own Investigate/Plan phases and encode the target-skill mapping as a single source (preferred: a triggers_skill-style field on each process-skill-signal tag's row)
- update all 4 consumers (ticket-scoper.md, ticket_tagging.md, implement-ticket.js, create-tickets.js) to read from the single source
- explicitly decide and implement the fate of tag_skill_mapping_check.py (remove vs repurpose)
- rewrite docs/guides/ticket_tagging.md's "Skill Suggestions From Tags" section to describe the single-source mechanism instead of documenting a 4th independently-maintained copy of the table
- update docs/ai/agents.md's ticket-scoper section if the single-source mechanism changes how suggested_skills is computed from what that section currently describes (added by TCK-20260705-TAG-SKILL-SUGGEST)

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- pre-deciding which of the 3 candidate schema-conflict resolutions to use — that decision belongs to this ticket's own Investigate/Plan phases, not to this synthesis

## Acceptance Criteria
- [x] changing a tag's target skill in exactly ONE stored location changes what all 4 consumers actually compute/emit — verified by editing the single source and confirming all 4 outputs reflect the change with zero other file edits
- [x] the debugging tag's conditional target (default /debugging-strategies vs the world-debugger carve-out for world-path tickets) is preserved losslessly, not flattened to a plain string that drops the branch
- [x] tag_skill_mapping_check.py's fate is explicitly decided and implemented — either removed with its 10 tests retired/migrated, or repurposed into a check that each of the 4 consumers reads the live source rather than embedding a literal copy — not left as dead code comparing copies that no longer independently exist
- [x] tag_registry.jsonl's append-only/no-update invariant is either preserved by the schema-change design, or the invariant break is explicitly justified and recorded
- [x] during this ticket's own Investigate/Plan phase, one of the 3 candidate resolutions to the append-only-vs-existing-rows conflict (or an explicitly justified 4th option) is chosen and documented — not mandated in advance by this ticket's Scope
- [x] docs/guides/ticket_tagging.md's "Skill Suggestions From Tags" section describes the single source, not a 4th hand-maintained copy of the mapping table
- [x] docs/ai/agents.md's ticket-scoper section is reviewed and updated if its description of suggested_skills computation no longer matches the new single-source mechanism

## Related Tickets
- TCK-20260705-TAG-SKILL-SUGGEST
- TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK
- TCK-20260718-LAYER-REGISTRY-CONVERSION
- TCK-20260720-TAG-REGISTRY-RELOCATE

## Related Docs
- docs/guidelines/tag_registry.jsonl
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md
- docs/ai/agents.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/tag_skill_mapping_check.py
- tests/tools/test_tag_skill_mapping_check.py
- tools/tag_registry.py
- tests/tools/test_tag_registry.py
- .claude/agents/ticket-scoper.md
- docs/guides/ticket_tagging.md
- .claude/workflows/implement-ticket.js
- .claude/workflows/create-tickets.js

## Assumptions / Open Questions
- candidate resolution (a): widen add_tag()'s schema going forward only — new rows get the triggers_skill field, old rows stay without it and are read via a fallback
- candidate resolution (b): do a one-time explicitly-authorized rewrite of the 4 existing tag_registry.jsonl lines, breaking the append-only invariant, requiring explicit sign-off
- candidate resolution (c): store the mapping in a different location entirely, not on tag_registry.jsonl rows
- the 4 consumers span 3 different execution contexts requiring different read mechanisms: the 2 Node.js workflow files have a working precedent (python3 -c subprocess call + stdout JSON marker, already used at implement-ticket.js:313-314 and create-tickets.js:578-579); ticket-scoper.md is an LLM-interpreted agent prompt with no code execution; ticket_tagging.md is a pure human-read doc with no binding mechanism today
- if dedup succeeds, tag_skill_mapping_check.py's entire premise (pairwise-comparing independently-maintained texts) becomes moot, but its 3 parser functions and 10 tests encode real format-specific knowledge — delete-vs-shrink is explicitly undecided
- no prior ticket has reopened TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK's explicit out-of-scope decision — this is genuine, undone work
- layer assigned as `ai` (Claude agent/orchestration tooling) per docs/guidelines/layer_registry.jsonl — this work is entirely about agent/workflow tooling infrastructure, not gameplay cognition

## Implementation Notes

Followed `plan.md`'s 12 steps in order, implementing the chosen hybrid-(a)+(c) resolution.

- **Steps 1-2 (`tools/tag_registry.py`):** `add_tag()` gained an optional `triggers_skill: dict | None = None`
  parameter, written into the entry only when given — zero behavior change for every existing caller
  (confirmed by `test_add_tag_without_triggers_skill_omits_field`). Added the module-level
  `_LEGACY_SKILL_TRIGGERS` dict, disclosed in a comment directly above it, covering exactly the 4
  existing `process-skill-signal` rows (`api-design`, `debugging`, `performance`, `security`), each
  structured as `{skill, carveout_agent, carveout_paths, carveout_excluded_paths}` — the `debugging`
  entry preserves the full carve-out (agent `world-debugger`, 5 carve-out paths, and the
  `src/worldgeneration/` exclusion) as structured data, not a flattened string.
- **Step 3:** Added `get_skill_mapping(root=None)` — merges each registry row's own `triggers_skill`
  field (when present) with `_LEGACY_SKILL_TRIGGERS` as fallback. This is the one function every
  consumer ultimately depends on.
- **Step 4:** Added a `skill-mapping` CLI subcommand (`python3 tools/tag_registry.py skill-mapping`)
  printing `get_skill_mapping()`'s result as plain JSON (no marker prefix — consumed directly by an
  agent's own Bash tool call, not orchestrator-parsed).
- **Steps 5-8 (consumer rewrites):** Replaced the embedded table/arrow-list in
  `.claude/agents/ticket-scoper.md` (Output-contract item 5), `.claude/workflows/implement-ticket.js`
  (existing-ticket branch's Step 3 — the "new ticket" branch already delegated to ticket-scoper.md and
  needed no change), `.claude/workflows/create-tickets.js` (Structure phase's `suggested_skills` block),
  and `docs/guides/ticket_tagging.md` (Skill Suggestions From Tags section) with an instruction to run
  `python3 tools/tag_registry.py skill-mapping` and read its JSON, preserving the carve-out's full
  `(skill, carveout_agent, carveout_paths, carveout_excluded_paths)` structure in every replacement's
  wording. No literal table/arrow-list text remains in any of the 4 files.
- **Step 9:** Reviewed `docs/ai/agents.md:44` — confirmed (per the plan's own pre-check) that its
  generic phrasing ("skill/agent invocations mapped from the ticket's `Process/Skill-signal` tags")
  does not name the old 4-copy mechanism and remains accurate under the new single-source design. No
  edit made.
- **Step 10:** Repurposed `tools/tag_skill_mapping_check.py` in place. Removed the 3 format-specific
  parsers (`extract_pairs_markdown`, `extract_pairs_js_escaped`, `extract_pairs_arrow_list`),
  `normalize_target`, the anchor/regex constants, and `check_tag_skill_mapping_consistency` — all dead
  once Steps 5-8 landed (no consumer embeds a parseable table anymore). Replaced with `KNOWN_TAGS`
  derived live from `tag_registry.get_skill_mapping().keys()` (fixing the module's own previously
  disclosed staleness limitation) and a new `check_consumers_reference_live_source(root=None)` that
  asserts each of the 4 consumer files (a) references the live mechanism (substring match on
  `skill-mapping`/`get_skill_mapping`) and (b) does not re-embed a literal table (heuristic: 3+ known
  tag names formatted as table-row/arrow-list-shaped text within the file). Rewrote
  `tests/tools/test_tag_skill_mapping_check.py`: retired all 10 old tests (named individually in a
  top-of-file comment block, not silently deleted) and added 5 new tests, including one that injects a
  reintroduced table into a tmp copy of a consumer file and asserts the check actually catches it (the
  anti-drift "must be able to fail" guard), and one confirming the check tolerates a couple of
  in-context tag mentions (e.g. inline examples in prose) without false-flagging them as a table.
- **Step 11:** Updated `docs/guidelines/tag_taxonomy.md`'s Scenario 5 row to describe
  `check_consumers_reference_live_source` instead of the old extraction/comparison framing.
- **Step 12:** Full regression run — see Test Summary.

No deviations from `plan.md`'s 12 implementation steps were needed for the code itself.

**Follow-up fix (post-implementation, found by the real Test phase's full regression run):**
`tests/tools/test_create_tickets_tag_scope.py::test_process_skill_signal_mapping_table_still_present_unchanged`
failed. That test belonged to the earlier, separate TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX
ticket and asserted the literal old embedded skill-mapping table
(`"api-design  -> /api-design-principles"`, `"Do not invent mappings for tags outside this 4-entry
table"`) was still present verbatim in `create-tickets.js` — a premise this ticket's Step 7 (and its
already-approved architecture review) intentionally invalidated by replacing that table with a
live-lookup instruction pointing at `tag_registry.py`'s `get_skill_mapping()` / `skill-mapping` CLI
subcommand. Before touching the test, independently re-read the current
`.claude/workflows/create-tickets.js` (lines ~503-514) and confirmed: the old table's literal
strings are genuinely absent, and the new live-lookup reference
(`python3 tools/tag_registry.py skill-mapping`, plus the guardrail sentence "Do not invent mappings
for tags outside this live mapping's keys.") is genuinely present and correct. Renamed the stale
test to `test_skill_mapping_references_live_source_not_embedded_table` and rewrote its assertions
to check the new reality (old strings absent, new reference present) instead of weakening or
deleting it. `create-tickets.js` itself required no change — it was already correct from the
original implementation. No other test in that file was touched. Full file re-run:
`python3 -m pytest tests/tools/test_create_tickets_tag_scope.py -v` — 5 passed, 0 failed. See
`staging_artifacts/TCK-20260720-SKILL-MAPPING-DEDUP/plan.md`'s new "Deviations" section for the same
record.

## Test Summary

`python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_tag_report.py tests/tools/test_validate_frontmatter.py -q`

Result: **173 passed**, 0 failed. Includes: all 21 pre-existing `test_tag_registry.py` tests
unmodified (`test_add_tag_rejects_duplicate_tag` and `test_add_tag_is_append_only_existing_entries_unchanged`
in particular — confirms AC4, the append-only invariant was never touched), 9 new
`test_tag_registry.py` tests from Steps 1-3, 5 new `test_tag_skill_mapping_check.py` tests from Step
10 (replacing the 10 retired ones), and all `test_agent_ops_dashboard_ingest.py` /
`test_tag_report.py` / `test_validate_frontmatter.py` tests confirming the additive `triggers_skill`
field and new `get_skill_mapping()`/CLI subcommand don't break either downstream consumer.

Also manually verified: `python3 tools/tag_registry.py skill-mapping` prints valid JSON for all 4
known tags with the debugging carve-out intact; `check_consumers_reference_live_source()` returns
`[]` against the real, just-edited 4 consumer files.

## Files Changed

- `tools/tag_registry.py` — `add_tag(triggers_skill=...)`, `_LEGACY_SKILL_TRIGGERS`, `get_skill_mapping()`, `skill-mapping` CLI subcommand
- `tests/tools/test_tag_registry.py` — 9 new tests (triggers_skill write/omit, legacy fallback shape, get_skill_mapping)
- `tools/tag_skill_mapping_check.py` — repurposed: removed parsers/normalize_target/consistency-check, added live-derived `KNOWN_TAGS` and `check_consumers_reference_live_source()`
- `tests/tools/test_tag_skill_mapping_check.py` — retired 10 old tests (documented in a top-of-file comment), added 5 new tests
- `.claude/agents/ticket-scoper.md` — Output-contract item 5 rewritten to point at the live CLI command
- `.claude/workflows/implement-ticket.js` — existing-ticket branch's Step 3 delegates to the Output contract instead of embedding a table
- `.claude/workflows/create-tickets.js` — Structure phase's `suggested_skills` block rewritten to point at the live CLI command
- `docs/guides/ticket_tagging.md` — "Skill Suggestions From Tags" section rewritten to describe the single source
- `docs/guidelines/tag_taxonomy.md` — Scenario 5 row updated to describe the repurposed checker
- `tests/tools/test_create_tickets_tag_scope.py` — follow-up fix (Test phase caught this): renamed/rewrote `test_process_skill_signal_mapping_table_still_present_unchanged` to `test_skill_mapping_references_live_source_not_embedded_table`, asserting the old embedded table is absent and the new live-lookup reference is present, instead of asserting the old table still exists

## Completion Summary

Collapsed the 5 hand-maintained copies of the `Process/Skill-signal` tag -> skill mapping
(`ticket-scoper.md`, `ticket_tagging.md`, `implement-ticket.js`, `create-tickets.js`, and
`tag_skill_mapping_check.py`'s own `KNOWN_TAGS`) into one executable source: `tag_registry.py`'s new
`get_skill_mapping()`, which merges a forward-only `triggers_skill` field on registry rows with a
small, explicitly disclosed `_LEGACY_SKILL_TRIGGERS` fallback for the 4 already-registered tags —
preserving the registry's append-only invariant with zero changes to `add_tag()`'s existing
duplicate-rejection behavior or its tests. All 4 consumer files now read this single source live
(via a new `skill-mapping` CLI subcommand for the 3 LLM-prompt consumers, and directly via
`docs/guides/ticket_tagging.md`'s prose pointer for the one human doc), with the `debugging` tag's
conditional carve-out (default skill vs. `world-debugger` agent + path set + exclusion) preserved
losslessly as structured data throughout. `tag_skill_mapping_check.py` was repurposed from a
pairwise-comparator of independently-maintained texts (whose premise no longer exists) into a static
regression guard confirming each consumer references the live source and none re-embed a table,
resolving its own previously-disclosed `KNOWN_TAGS` staleness limitation as a side effect. All 7
acceptance criteria are satisfied; the full scoped regression suite (173 tests across
`test_tag_registry.py`, `test_tag_skill_mapping_check.py`, `test_agent_ops_dashboard_ingest.py`,
`test_tag_report.py`, `test_validate_frontmatter.py`) passes.
