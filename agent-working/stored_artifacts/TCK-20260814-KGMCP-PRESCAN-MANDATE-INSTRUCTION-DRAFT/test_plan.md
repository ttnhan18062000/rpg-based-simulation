---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT
artifact_type: test_plan
tags: [ai, claude-md, process-improvement]
---

# Test Plan — TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT

## What "test" means for this ticket
This ticket produces zero `src/`/`tools/` code and no runtime behavior change — its Scope explicitly
excludes activating anything. The precedent this repo already uses for exactly this artifact shape is
`tests/docs/test_redaction_retention_policy_doc.py` (covering
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`, this epic's own sibling
ticket, `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`): plain `Path.read_text()` string/heading
assertions against the drafted doc, never a runtime/behavioral test, plus one `ast`-based guard that
proves a *different, live* file was not touched. This ticket's tests follow that same shape, adapted
to the two-file target this ticket actually has (the new draft artifact, plus the three live
instruction files it must not touch).

## Regression Surface
No existing test exercises code this ticket changes, because this ticket changes no code. The
regression surface is therefore about proving non-regression of the **live instruction files**, not
re-running unrelated suites. Existing tests that must keep passing unmodified (their content proves
this ticket did not silently touch what they pin):

- `tests/tools/test_skill_investigate_search_before_grep.py` (unit) — pins the phase-scoped
  search-before-grep callout inside `.claude/skills/implement-ticket/SKILL.md` step 2, added by
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`. This ticket must not cause this file to fail —
  a failure here would mean `SKILL.md`'s callout was accidentally touched, which is explicitly
  Out of Scope.
- `tests/docs/test_redaction_retention_policy_doc.py` (unit / doc-structure, integration group) —
  the sibling epic-child doc-structure precedent this ticket's own new test mirrors. Not touched by
  this ticket, but its passing confirms the pattern this ticket's test follows is still valid
  against its own doc.
- Any existing `.claude/agents/investigator.md` structural test, if one exists (none was found by
  direct grep of `tests/` for `investigator.md` at investigation time — flag for the test-scoper/
  implementer to re-confirm at Test phase, since a new one could have landed between Investigate and
  Implement) — must keep passing if one is discovered, since the callout it pins is explicitly Out
  of Scope for this ticket.

Category: doc/architecture-guard (static text-assertion tests), not unit-in-the-behavioral sense,
not integration, not arena-combat (not applicable to this domain).

## New Tests Required

- **`test_draft_instruction_change_artifact_exists_and_is_labeled_not_activated`**
  Category: architecture guard (doc-structure).
  Verifies: the new draft artifact file (path decided by Plan, e.g.
  `docs/ai/claude_md_prescan_mandate_relaxation_draft.md` or a `staging_artifacts/`→
  `stored_artifacts/` path) exists and contains an explicit, early "for human review only" /
  "not yet activated" / "not applied to any live `CLAUDE.md` or `.claude/agents/*.md` file"
  disclaimer — mirroring the exact boilerplate opening `docs/ai/codex_posttool_adapter_real_command_
  proposal.md` and `redaction_retention_policy.md` §11 both use, so the assertion should check for
  the disclaimer's substance (three required phrase fragments: "for human review only" or
  equivalent, "not activated" or "not applied", and "does not itself" — matching
  `test_policy_doc_explicitly_flags_ratification_pending`'s precedent of asserting distinct,
  individually matchable phrase fragments rather than one long string).
  Where it lives: `tests/docs/test_prescan_mandate_instruction_draft.py` (new file, following
  `tests/docs/test_redaction_retention_policy_doc.py`'s naming and directory convention).

- **`test_draft_records_activation_precondition_against_hardening_ticket`**
  Category: architecture guard (doc-structure).
  Verifies: the draft (or this ticket's own `Implementation Notes`/`Assumptions` — Plan decides
  which) explicitly names `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` and states the
  activation precondition found by Investigate (fix landed, not yet retro-confirmed by
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation section) — i.e., asserts the
  literal ticket ID string plus a phrase indicating activation is gated on a future retro
  confirmation, not asserted as already satisfied.
  Where it lives: same new file as above.

- **`test_draft_preserves_investigator_and_skill_callouts_verbatim`**
  Category: architecture guard (non-regression, `ast`/text-based, mirrors
  `test_sqlite_defaults_not_silently_implemented`'s "prove a different file was not touched"
  pattern).
  Verifies: `.claude/agents/investigator.md` still contains its search-before-grep callout
  (`mcp__knowledge-search__search_docs`, `graphify query`, "does not substitute" or equivalent) and
  `.claude/skills/implement-ticket/SKILL.md` still contains its Step 2 phase-scoped sentence
  (`"Step 0's one-time upfront call does not substitute for this phase-scoped call"`) — both
  checked via plain `Path.read_text()` substring assertions, run *after* this ticket's Implement
  phase, to catch any accidental edit to either live file. This is the direct enforcement of this
  ticket's 4th Acceptance Criterion ("No `CLAUDE.md` or `.claude/agents/*.md` diff appears in this
  ticket's `Files Changed`").
  Where it lives: same new file as above.

- **`test_draft_does_not_modify_claude_md_or_agent_md_files`**
  Category: architecture guard (`git diff`-based or file-hash-based, not content-based).
  Verifies: `CLAUDE.md` and every `.claude/agents/*.md` file are byte-identical to their pre-ticket
  committed state — the strongest possible form of the same non-regression guarantee, complementary
  to the text-substring test above (that one catches content drift even if the file were touched and
  restored to equivalent-but-differently-worded text; this one catches any diff at all, including
  formatting-only changes). Should compare against `git show HEAD:<path>` (or an equivalent
  known-good baseline) rather than a hardcoded string copy, so it does not need updating every time
  unrelated content in those files changes for other reasons.
  Where it lives: same new file as above, or `tests/tools/test_workflow_meta_conformance.py` if Plan
  judges it fits that file's existing conformance-guard scope better — Plan's call, not decided here.

- **`test_draft_covers_required_ambient_utility_substance`**
  Category: architecture guard (doc-structure, content-coverage).
  Verifies: the draft text contains the load-bearing substance items from proposal §2.1 — "ambient
  utility" / same category as `rg`/git history/Graphify/Context Search framing, the "optional
  ranking hints" framing for ticket ID/workflow/phase/changed-paths/agent-role/run-ID, "not itself a
  workflow phase, gate, Definition-of-Done item, or mandatory ticket step" (or a close paraphrase),
  and the cheapest-reliable-source examples (`rg` for exact text check, Graphify directly for
  focused code-reference, Context Search directly for focused document lookup) — each asserted as a
  distinct, individually matchable phrase fragment, not one giant string, per this repo's existing
  convention (`test_redaction_retention_policy_doc_exists_and_has_required_sections`'s
  `never_cache_items` list is the direct precedent for this assertion shape).
  Where it lives: same new file as above.

## Scoped Pytest Commands
```
.venv/bin/python3 -m pytest tests/docs/test_prescan_mandate_instruction_draft.py -v
.venv/bin/python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -v
.venv/bin/python3 -m pytest tests/tools/test_skill_investigate_search_before_grep.py -v
```
Never `pytest tests/` — scoped to the doc-structure/architecture-guard domain this ticket actually
touches (`tests/docs/`) plus the two specific regression-surface files named above.

## Anti-Drift Test Guards
- The `test_draft_does_not_modify_claude_md_or_agent_md_files` test is the direct, mechanical
  enforcement of this ticket's 4th Acceptance Criterion and should be treated as the single
  highest-priority test in this plan — it is what would catch a well-intentioned implementer
  "just fixing" the live files instead of only drafting.
- `test_draft_preserves_investigator_and_skill_callouts_verbatim` guards specifically against the
  scope-creep failure mode this investigation flagged as a real risk: a draft that only checks
  non-regression against `CLAUDE.md`'s two named sections while silently contradicting
  `.claude/skills/implement-ticket/SKILL.md`'s phase-scoped callout (the un-named-in-ticket 5th
  instruction surface found during Investigate).
- `test_draft_records_activation_precondition_against_hardening_ticket` guards against the draft
  silently dropping or softening the "not yet retro-confirmed" finding — e.g. an implementer
  drafting language that reads as if the hardening fix is already fully proven, which the real
  `RETRO-LAST14D.md` data does not yet support.
- No test in this plan should ever import or execute the drafted instruction text as if it were
  active configuration — every assertion is `Path.read_text()` substring/heading matching only,
  consistent with `tests/docs/test_redaction_retention_policy_doc.py`'s explicit doc-structure-only
  framing (its own module docstring: "assert doc *structure* ... never runtime behavior").
