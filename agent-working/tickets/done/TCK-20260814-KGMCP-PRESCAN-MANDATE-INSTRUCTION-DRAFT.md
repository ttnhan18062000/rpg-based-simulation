---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT
phase: done
date: 2026-08-14
tags: [ai, claude-md, process-improvement]
---

# TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT

## Title
Draft (do not activate) the agent-instruction change replacing the blanket search-before-grep
pre-scan mandate with a cheapest-reliable-source/ambient-utility rule, explicitly sequenced against
the pre-scan hardening ticket

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §2.1 and §20 (Phase 0's final bullet) call for
drafting a generated-agent-instruction change that replaces `CLAUDE.md`'s current blanket "call
`search_docs` + `graphify query` before grep/raw reads" mandate with an ambient-utility,
cheapest-reliable-source policy — explicitly **not activated before review**.

This directly touches the same instruction surface that
`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` (sibling epic `agent-tooling-integrity-hardening`,
OPEN as of this ticket's creation) is actively hardening: that ticket is closing a real compliance
gap where hand-orchestrated (`agent=claude`) Investigate-phase work skips the mandate entirely (3
confirmed post-fix violations in the 14-day audit window). Drafting a relaxation of the same rule
whose enforcement is mid-repair is not unsafe by itself — the proposal already requires the draft
stay inert until separately activated — but the two tickets must not proceed in ignorance of each
other, and `TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC`'s Assumptions/Open Questions flags this
sequencing as unresolved.

## Scope
- **Investigate (mandatory before Plan):** check the real current status of
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`. Record whether it has landed, and if so,
  whether a follow-up retro window has confirmed its fix holds (per that ticket's own Acceptance
  Criteria, which defers long-term compliance proof to
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation section).
- Based on that finding, choose one of:
  - if the hardening fix has landed and held through a retro window: draft the relaxation with
    explicit non-regression wording that preserves the now-hardened entry point's callout;
  - if the hardening fix has not yet landed or not yet held: draft the relaxation anyway (Phase 0 is
    contract-drafting, not activation) but explicitly record in this ticket that activation must
    wait for the hardening ticket's retro-confirmed fix, and do not treat this ticket as unblocking
    activation on its own.
- Draft the replacement instruction language per §2.1's substance: the gateway (and, generally,
  `rg`/Graphify/Context Search direct calls) is an ambient, phase-agnostic repository utility, not a
  mandatory workflow phase, gate, or Definition-of-Done item; ticket ID/workflow/phase/changed-paths/
  agent-role/run-ID metadata are optional ranking hints only; agents should use the cheapest reliable
  source (a direct `rg` lookup or Graphify query remains preferable when it safely answers the
  question with less work).
- Store the draft as a reviewable artifact (e.g. in this ticket's stored artifacts or a docs/ai/
  proposal doc), explicitly marked not-yet-applied to `CLAUDE.md`.
- Do **not** edit the live `CLAUDE.md` Context Scan section, the Proactive Tool Use table, or any
  agent `.md` file's search-before-grep callout as part of this ticket.

## Out of Scope
- Activating the drafted instruction change (editing live `CLAUDE.md` or `.claude/agents/*.md`) —
  a separate, later ticket per the proposal's own maturity gate.
- Any change to `.claude/agents/investigator.md` (already fixed and verified,
  `TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`) or to
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s own fix — this ticket only drafts a future
  policy change, it does not touch that ticket's in-flight work.
- Resolving §24's other 5 open decisions — only the sequencing of this specific instruction draft.

## Acceptance Criteria
- [x] `investigation.md` records the real, current status of
      `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` (and, if relevant,
      `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation data), not an assumption.
- [x] The drafted instruction text exists as a reviewable artifact, explicitly labeled not-yet-
      activated, and is not applied to any live `CLAUDE.md` or `.claude/agents/*.md` file.
- [x] The draft or this ticket's notes explicitly state the activation precondition relative to the
      hardening ticket's status found during Investigate.
- [x] No `CLAUDE.md` or `.claude/agents/*.md` diff appears in this ticket's `Files Changed` other
      than the new draft-artifact location itself.

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent)
- TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (OPEN; hardens the exact mandate this ticket
  drafts a relaxation of — check status before Plan)
- TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (OPEN; its correlation section is the
  evidence source for whether the hardening fix is holding)
- TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP (DONE; predecessor fix this ticket must not
  regress)
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (sibling epic; parent of the tickets above)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §2.1, §20
- `CLAUDE.md` (§Context Scan, §Proactive Tool Use — reference only, not modified by this ticket)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `CLAUDE.md` (reference only — not modified)
- `.claude/agents/investigator.md` (reference only — not modified)

## Assumptions / Open Questions
- Whether the drafted instruction change should be scoped narrower than §2.1's full ambient-utility
  language (e.g. carve out an explicit exception preserving the hardened `agent=claude`
  hand-orchestration entry point) or left general with an activation precondition — not decided
  here; Investigate's finding on the hardening ticket's status should drive this choice.

## Implementation Notes
Implemented exactly the plan's 3 ordered steps, in order, following
`staging_artifacts/TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT/plan.md` verbatim.

1. **Draft artifact** — created `docs/ai/claude_md_prescan_mandate_relaxation_draft.md`, following
   the `docs/ai/codex_posttool_adapter_real_command_proposal.md` frontmatter/boilerplate shape
   (`status: active`, `layer: ai`, `authority: P2`, `audience: agent`,
   `tags: [ai, claude-md, process-improvement]`). Contains: an opening "for human review only" /
   "not activated" / "not applied" / "does not itself" disclaimer; an Activation Precondition
   section citing `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` and
   `agent-monitoring/retro/RETRO-LAST14D.md`'s own `## Notes` finding that the compliance signal is
   currently pending, not satisfied; the full §2.1 ambient-utility/cheapest-reliable-source
   replacement text (source: `docs/plans/knowledge-gateway-mcp-proposal.md:93-117`); a
   Non-Regression Cross-Reference checklist naming all 3 live instruction surfaces (`CLAUDE.md`'s
   Context Scan section, `CLAUDE.md`'s Proactive Tool Use table, and
   `.claude/skills/implement-ticket/SKILL.md`'s Step 2 callout) without editing any of them; and a
   closing "What This Draft Does Not Do" paragraph.
2. **Proposal doc annotation** — appended a "**Done (drafted; not activated)**" annotation to
   `docs/plans/knowledge-gateway-mcp-proposal.md` §20's final Phase 0 bullet (the pre-scan-mandate
   drafting bullet), matching the exact in-line annotation style already used by every other Phase 0
   bullet in that list (e.g. the redaction/retention bullet's "Drafted / pending ratification").
3. **Regression-guard test file** — created `tests/docs/test_prescan_mandate_instruction_draft.py`
   with all 5 tests from `test_plan.md`, following `tests/docs/test_redaction_retention_policy_doc.py`'s
   plain `Path.read_text()` pattern. `test_draft_does_not_modify_claude_md_or_agent_md_files` uses
   `subprocess.run(["git", "diff", "--stat", "HEAD", "--", "CLAUDE.md", ".claude/agents/*.md"], ...)`
   with real pathspecs (never an empty pathspec) and asserts empty stdout.
   `test_draft_preserves_investigator_and_skill_callouts_verbatim` scopes its SKILL.md assertion to
   the `"2. **Investigate**"` .. `"3. **Plan**"` region, modeled directly on
   `tests/tools/test_skill_investigate_search_before_grep.py::_investigate_step_text()`.

**Deviation from plan (minor, self-corrected during Implement):** the first draft of the
`## Activation Precondition` prose used a mid-line Markdown bold break (`**optional ranking\nhints**`
wrapped across a line boundary), which caused
`test_draft_covers_required_ambient_utility_substance` to fail on the `"optional ranking hints"`
fragment (a literal newline inside the phrase broke the substring match). Fixed by rejoining the
phrase onto one line; no other content changed. This is a wording/formatting fix only, not a
substance deviation from the plan, so no `plan.md` "Deviations" section was needed.

Verified directly (not just via the test) that `git diff --stat HEAD -- CLAUDE.md
.claude/agents/*.md .claude/skills/*.md` produces zero output — the ticket's own core safety
property.

## Test Summary
```
.venv/bin/python3 -m pytest tests/docs/test_prescan_mandate_instruction_draft.py -v
```
5 passed, 0 failed:
`test_draft_instruction_change_artifact_exists_and_is_labeled_not_activated`,
`test_draft_records_activation_precondition_against_hardening_ticket`,
`test_draft_preserves_investigator_and_skill_callouts_verbatim`,
`test_draft_does_not_modify_claude_md_or_agent_md_files`,
`test_draft_covers_required_ambient_utility_substance`.

Regression-surface files re-run and confirmed still passing unmodified (proving this ticket did not
silently touch what they pin):
```
.venv/bin/python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -v   # 6 passed
.venv/bin/python3 -m pytest tests/tools/test_skill_investigate_search_before_grep.py -v   # 2 passed
```

## Files Changed
- `docs/ai/claude_md_prescan_mandate_relaxation_draft.md` (new)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (edited — §20 Phase 0 bullet annotation only,
  lines 1117-1118 region)
- `tests/docs/test_prescan_mandate_instruction_draft.py` (new)
- `staging_artifacts/TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT/investigation.md`
  (Docs Requiring Update bullet corrected post-Implement to record the real
  `docs/ai/claude_md_prescan_mandate_relaxation_draft.md` path Plan chose, replacing the
  pre-Implement placeholder path — fixed a real `docs_to_update_coverage` static-check failure at
  Verify)

No `CLAUDE.md` file, no `.claude/agents/*.md` file, and no `.claude/skills/*.md` file was created,
edited, or deleted by this ticket — confirmed both by the new test and by a direct
`git diff --stat HEAD -- CLAUDE.md .claude/agents/*.md .claude/skills/*.md` (empty output).

## Completion Summary
Drafted, but did not activate, the CLAUDE.md pre-scan-mandate relaxation instruction text called
for by `docs/plans/knowledge-gateway-mcp-proposal.md` §2.1/§20 Phase 0, as a new inert artifact at
`docs/ai/claude_md_prescan_mandate_relaxation_draft.md`. The draft states an explicit Activation
Precondition (gated on `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s compliance fix being
retro-confirmed, currently pending per `agent-monitoring/retro/RETRO-LAST14D.md`), covers the full
§2.1 ambient-utility/cheapest-reliable-source substance, and cross-references all 3 live instruction
surfaces without editing any of them. The proposal doc's corresponding Phase 0 bullet was annotated
"Done (drafted; not activated)" citing this ticket. A new 5-test regression-guard file
(`tests/docs/test_prescan_mandate_instruction_draft.py`) enforces the draft's required content and,
as its highest-priority check, that `CLAUDE.md` and `.claude/agents/*.md` remain byte-unchanged by
this ticket — verified both by that test and by a direct manual `git diff --stat` check.
