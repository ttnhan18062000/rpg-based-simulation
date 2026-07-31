---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-RELEVANCE-VERIFY
phase: done
date: 2026-07-20
tags: [tagging, workflows]
---

# TCK-20260720-TAG-RELEVANCE-VERIFY

## Title
Add a tag-relevance verification step to catch hallucinated, wrong, or drifted tags

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Surfaced directly from this session's own experience: twice, tickets came out of `create-tickets.js`
with no Subsystem/Topic tags, and both times the correction was a human (the user) reading the
ticket and manually picking better tags. Checked `tools/validate_frontmatter.py`'s `_check_tags`
directly — it only verifies canonical form (spelling/format) and registry membership (does this
tag exist). Nothing anywhere in the pipeline verifies that an assigned tag is actually *relevant*
to what a ticket is about, and nothing revisits a ticket's tags after Scope/creation time even
when later Investigate/Plan/Implement phases reveal the ticket touches subsystems nobody
anticipated when it was tagged. This means both hallucinated tags (a plausible-sounding but wrong
tag, assigned by an LLM with no independent check) and missing tags (a ticket's actual final scope
drifts away from its declared tags during implementation) currently go completely undetected —
the only check that exists today is an attentive human noticing, which is not a reliable
mechanism.

## Scope
- A relevance-check step, following the same "second independent look" pattern this repo already
  uses for `security-reviewer`/`mechanics-auditor`, that cross-references a ticket's assigned tags
  against its title/scope/`related_code_areas` at creation time and flags an implausible tag —
  wired into both tag-assignment paths (`create-tickets.js`'s Structure phase for batch creation,
  and `ticket-scoper` for single-ticket creation).
- A drift check, run at Finalize time (or as part of `done-checker`), that re-derives candidate
  tags from a ticket's final `Files Changed`/`related_code_areas` and flags any obvious mismatch
  against its declared `tags` for human review — e.g. a ticket that ended up only touching
  `src/api/agent_ops_dashboard/` but has no `dashboard` tag.
- Document both mechanisms in `docs/guides/ticket_tagging.md`.

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- Building a fully automated tag-assignment engine — this is a verification/flagging layer over
  existing human/LLM tag assignment, not an auto-tagger.
- Retroactively re-verifying the entire historic ticket corpus for tag *relevance* —
  TCK-20260720-TAG-CORPUS-REPAIR-SWEEP already covers the full corpus, but only for
  registry-membership/canonical-form/category-validity, a deliberately different and narrower kind
  of check than relevance; this ticket does not extend that sweep's scope.
- Making either check a hard pipeline-blocking gate — both are advisory flags for human review,
  matching this repo's existing practice for soft/judgment-based signals (e.g. the existing
  `mistag_warning` heuristic in `ticket-scoper.md`/`implement-ticket.js`, which warns rather than
  blocks).

## Acceptance Criteria
- [ ] A relevance-check mechanism exists and is wired into at least one tag-assignment path
      (`create-tickets.js`'s Structure phase and/or `ticket-scoper`), flagging — not silently
      rejecting — a tag whose registered category/description doesn't plausibly match the
      ticket's title, scope, and `related_code_areas`.
- [ ] A drift-check mechanism exists that, given a ticket's final `Files Changed`/
      `related_code_areas`, flags an obvious mismatch against its declared `tags` for human
      review, without auto-adding or auto-removing any tag.
- [ ] Neither mechanism blocks or fails the ticket pipeline outright — both surface as advisory
      warnings, consistent with this repo's existing treatment of judgment-based signals.
- [ ] `docs/guides/ticket_tagging.md` documents both mechanisms: what they check, where they run,
      and that they are advisory, not enforcing.
- [ ] `docs/ai/agents.md` is updated if either mechanism is implemented as (or added to) an
      existing agent's documented behavior.

## Related Tickets
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX
- TCK-20260720-TAG-CORPUS-REPAIR-SWEEP
- TCK-20260705-TAG-SKILL-SUGGEST
- TCK-20260706-CREATE-TICKETS-TAG-CHECK
- TCK-20260720-TAG-REGISTRY-RELOCATE
- TCK-20260720-TAG-CATEGORY-REGISTRY

## Related Docs
- docs/guides/ticket_tagging.md
- docs/guidelines/tag_taxonomy.md
- docs/ai/agents.md
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/create-tickets.js
- .claude/agents/ticket-scoper.md
- tools/gate_checks/done_checker_static.py
- tools/validate_frontmatter.py
- tools/tag_registry.py
- .claude/agents/security-reviewer.md
- .claude/agents/mechanics-auditor.md

## Assumptions / Open Questions
- Precedent pattern for the relevance check: `security-reviewer` and `mechanics-auditor` both
  already implement a "second independent agent look" over another agent's output in this repo —
  whether the relevance check should be a similarly dedicated new agent, or a lighter-weight check
  folded into `ticket-scoper`'s/`create-tickets.js`'s own existing output, is an open
  implementation decision for this ticket's own Investigate/Plan phases, not decided here.
- Both mechanisms are inherently judgment-based (an LLM or heuristic assessing "does this tag fit"
  has no ground truth to check against) — false positives/negatives are expected and acceptable
  given the advisory (non-blocking) design; this is a deliberate trade-off, not an oversight.
- This ticket is related to but distinct from TCK-20260720-TAG-CORPUS-REPAIR-SWEEP: that sweep
  answers "is this tag validly formed and registered" across the whole historic corpus; this
  ticket answers "does this tag actually describe what the ticket is about" going forward — the
  two checks are complementary, not overlapping, and should not be merged into one tool.
- Layer assigned as `ai` (Claude agent/orchestration tooling) since this is entirely about the
  agent/ticket-workflow tooling, not gameplay subject matter, matching the rest of this batch's
  layer choices.

## Implementation Notes

Implemented all 7 steps of `staging_artifacts/TCK-20260720-TAG-RELEVANCE-VERIFY/plan.md` exactly
as written — no deviations.

1. `.claude/agents/ticket-scoper.md`: added Output item 6, `tag_relevance_flags` — a self-check
   list of `"<tag>: <one-line reason>"` strings for any assigned tag that doesn't plausibly fit the
   ticket's own title/scope/`related_code_areas`; empty list if all tags fit (never omitted).
2. `.claude/workflows/create-tickets.js`: added `tag_relevance_flags` to `TASK_SCHEMA.required` and
   its property definition (mirrors `suggested_skills`); added a `tag_relevance_flags:` prompt rule
   block immediately after the existing `files_found`-evidence guardrail (that guardrail's exact
   strings — `files_found`, `clearly indicates one`, the "Do not guess a tag from the title alone"
   sentence — were left untouched); added a log-only `tasksWithRelevanceFlags` orchestrator block
   mirroring the existing `tasksWithSkills` block, never touching `pushEvent`.
3. `tools/gate_checks/done_checker_static.py`: added `_extract_section_text()`, a small private
   helper that returns a ticket's `## {heading}` body text up to the next `## ` heading or EOF
   (empty string if the heading is absent) — the first function in this file to parse ticket body
   sections rather than only YAML frontmatter.
4. Same file: added `check_tag_drift(ticket_id, ticket_path=None) -> tuple[str, str]` directly after
   `check_monitoring_write_recorded()`. Reads the closing ticket's `Files Changed`/`Related Code
   Areas` body text via `_extract_section_text()`, derives candidate tags via
   `registry_query.candidate_tags_from_text()` (new import added to the existing import block), and
   compares them against the ticket's declared `tags:` frontmatter. Returns `CLEAN` if no candidates
   or all candidates are already declared, `FLAGGED` (naming the missing candidate tag(s)) otherwise.
   Deliberately NOT added to `run_finalize_selfcheck()`'s `checks` tuple — that tuple's shape (4
   entries) is unchanged, verified by a new regression test.
5. `.claude/workflows/implement-ticket.js`: added a new `bash()` block in the Finalize phase,
   positioned after `await writeMonitoring('DONE')` and the existing
   `check_monitoring_write_recorded` block, before the final `return`. Calls `check_tag_drift` via
   `python3 -c`, parses a `TAG_DRIFT_CHECK_JSON:`-prefixed marker, and on `FLAGGED` only calls
   `pushEvent(..., 'failed', ...)` and `log('WARNING: ...')` — the final `return` object's
   `status: 'DONE'` is unconditional and never references `tagDriftCheck`.
6. `docs/guides/ticket_tagging.md`: added a new "Relevance and Drift Checks (Advisory Only)" section
   documenting both mechanisms — what each checks, where each runs, and that both are advisory-only
   (never block, never auto-add/remove a tag) — and explicitly distinguishing them from
   `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s registry-membership/canonical-form sweep.
7. `docs/ai/agents.md`: confirmed this file is hand-maintained and distinct from the
   contract-generated `AGENTS.md` (`tools/agent_orchestration_codex_adapter/generator.py::
   build_agents_md()` writes only to the repo-root `AGENTS.md` and `.agents/skills/`, never to
   `docs/ai/`) — safe to hand-edit. Added one bullet to `ticket-scoper`'s existing `**Outputs:**`
   list for `tag_relevance_flags`.

Tests added: `tests/tools/test_ticket_scoper_relevance_check.py` (new — AC #1 coverage for both the
`ticket-scoper.md` instruction and the never-blocks-via-`pushEvent` guard on `create-tickets.js`),
`tests/tools/test_create_tickets_tag_scope.py` (extended with
`test_create_tickets_structure_relevance_self_check_instruction_present`, including a companion
assertion that the pre-existing evidence guardrail strings survive unmodified),
`tests/tools/test_done_checker_static.py` (extended with `check_tag_drift` unit tests — flags a
missing candidate tag, clean when tags already cover candidates, clean when no candidates are
derivable — plus a regression guard confirming `run_finalize_selfcheck`'s checklist stays exactly
the same 4 conditions), `tests/tools/test_finalize_tag_drift_wiring.py` (new — source-text guard
confirming the Finalize `bash()` block's placement and that it never conditions the final `status`).

Follow-up cross-reference (informational only, no new work here): `tickets/todos/TCK-20260731-
CODEX-EXECUTION-IDENTITY-TAG-SWEEP.md` tracks whether this ticket's `check_tag_drift` Finalize hook
and `TAG-TOUCHPOINT-CLEANUP`'s `classifyChecklistFailure` rewrite need provider/`execution_id`
coverage once `TCK-20260730-CLAUDE-EXECUTION-IDENTITY` lands. Not implemented as part of this
ticket — that ticket remains in `tickets/todos/`.

## Test Summary

Scoped suite (all files this ticket touches or must not regress) — 218 passed, 0 failed:
```
python3 -m pytest tests/tools/test_done_checker_static.py tests/tools/test_validate_frontmatter.py \
  tests/tools/test_registry_query.py tests/tools/test_tag_registry.py \
  tests/tools/test_tag_category_registry.py tests/tools/test_create_tickets_tag_scope.py \
  tests/tools/test_classify_checklist_failure_js_mirror.py \
  tests/tools/test_ticket_scoper_relevance_check.py tests/tools/test_finalize_tag_drift_wiring.py -q
```
Broader regression sweep, `python3 -m pytest tests/tools/ -q`: 1384 passed, 1 xfailed, 8 failed.
All 8 failures are pre-existing and unrelated to this ticket's scope (`.mcp.json`
command/args drift in `test_search_mcp.py`, ECharts bundle-size and `knowledge_search`
build/performance timing in `test_agent_ops_dashboard_frontend_api_surface.py`/
`test_build_index.py`/`test_knowledge_search.py`) — none touch `tag_registry.py`,
`done_checker_static.py`, `create-tickets.js`, `ticket-scoper.md`, or `implement-ticket.js`.

## Files Changed

- `.claude/agents/ticket-scoper.md`
- `.claude/workflows/create-tickets.js`
- `.claude/workflows/implement-ticket.js`
- `tools/gate_checks/done_checker_static.py`
- `docs/guides/ticket_tagging.md`
- `docs/ai/agents.md`
- `tests/tools/test_ticket_scoper_relevance_check.py` (new)
- `tests/tools/test_create_tickets_tag_scope.py`
- `tests/tools/test_done_checker_static.py`
- `tests/tools/test_finalize_tag_drift_wiring.py` (new)

## Completion Summary

Added two advisory, non-blocking tag-quality checks: a relevance self-check (`tag_relevance_flags`)
computed inline by `ticket-scoper` and `create-tickets.js`'s Structure phase at tag-assignment time,
and a drift check (`check_tag_drift()`) run at Finalize time comparing a closing ticket's declared
tags against candidates derived from its `Files Changed`/`Related Code Areas` text. Neither
mechanism blocks the pipeline, uses `PASS`/`FAIL`/`NA` vocabulary, or auto-adds/removes a tag — both
are documented in `docs/guides/ticket_tagging.md` and `docs/ai/agents.md`. All acceptance criteria
met; scoped and broader regression suites pass with only pre-existing, unrelated failures.
