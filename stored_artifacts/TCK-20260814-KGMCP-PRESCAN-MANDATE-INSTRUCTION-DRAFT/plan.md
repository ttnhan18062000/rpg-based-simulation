---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT
artifact_type: plan
tags: [ai, claude-md, process-improvement]
---

# Implementation Plan — TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT

## Summary

This ticket produces exactly one new prose artifact — `docs/ai/claude_md_prescan_mandate_relaxation_draft.md`
— that drafts, but explicitly does not activate, the replacement instruction text from proposal
§2.1 (ambient-utility / cheapest-reliable-source policy) that would eventually replace CLAUDE.md's
current blanket "search_docs + graphify before grep" mandate. Per Investigate's finding, the
dependency ticket (`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`) has **landed** but its
compliance fix has **not yet been retro-confirmed** (`agent-monitoring/retro/RETRO-LAST14D.md`,
regenerated 2026-08-15T02:24, states no hand-orchestrated Investigate-phase run has recurred since
the fix shipped) — this selects the ticket's Scope's second branch: draft the general §2.1 language
now, but attach an explicit, unambiguous activation precondition rather than a narrower carve-out.

Three ordered steps: (1) write the draft artifact, cross-referencing all three live instruction
surfaces that carry the mandate today (`CLAUDE.md`'s Context Scan section, `CLAUDE.md`'s Proactive
Tool Use table, and `.claude/skills/implement-ticket/SKILL.md`'s Step 0/Step 2 phase-scoped
callout — not just the two `CLAUDE.md` sections named in the ticket's own Related Docs) without
editing any of them; (2) annotate `docs/plans/knowledge-gateway-mcp-proposal.md` §20's final Phase 0
bullet (lines 1117-1118) as done-with-caveat, matching the annotation pattern already present on
every other Phase 0 bullet in that same list; (3) add one new doc-structure test file,
`tests/docs/test_prescan_mandate_instruction_draft.py`, whose five tests enforce the draft's
required content and — the single highest-priority test in this plan — that zero bytes of
`CLAUDE.md` or any `.claude/agents/*.md` file changed as a result of this ticket. No `src/`,
`tools/`, or runtime code is touched; no Mechanics Bible chapter, engine contract, or parity ledger
entry is implicated (confirmed by direct precedent in Investigate's Parity Ledger Overlap section).

## Design Decision — `docs/ai/` over `docs/engine/contracts/knowledge_gateway_mcp/`

Investigate's Prior Work section (lines 131-167) identifies two existing "drafted, not yet applied"
artifact locations in this repo and found they serve genuinely different purposes:

- `docs/engine/contracts/knowledge_gateway_mcp/` houses **system-behavior specs** — §-numbered
  contracts defining formulas, schemas, and operational limits that a *future implementation
  ticket* will wire into code (e.g. `redaction_retention_policy.md`'s SQLite limits, redaction
  regex rules, token-counting formula). This epic's own `TCK-20260814-KGMCP-CONTRACT-SCHEMAS`,
  `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`, and `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`
  all placed their deliverables here because each defines behavior for code that will exist later.
- `docs/ai/` houses **agent-orchestration / instruction-prose drafts** — the three
  `codex_posttool_adapter_*` documents, each opening with identical boilerplate (verified directly,
  `docs/ai/codex_posttool_adapter_real_command_proposal.md:9-17`): *"This document is **for human
  review only**. Nothing in this repository parses it as TOML, ... and no code in this repository
  implements or executes what it describes."* These are proposed changes to what an agent process
  is told to do, not to what code does.

This ticket's deliverable is **CLAUDE.md replacement wording** — agent-instruction prose, not a
system-behavior contract and not a hook/command config. It is categorically the `docs/ai/` shape.
Placing it under `docs/engine/contracts/knowledge_gateway_mcp/` would misfile it alongside sibling
docs that define code-facing schemas/formulas, and would invite a future implementer to treat it as
something "Phase 1+" wires into `tools/`, which it explicitly is not (per Investigate's Risks note:
the gateway itself does not exist yet, so no code implements or executes this draft either way).
`docs/ai/` is also the only location with an established "for human review only" boilerplate this
draft can reuse verbatim rather than inventing new not-yet-activated phrasing from scratch.

Chosen path: **`docs/ai/claude_md_prescan_mandate_relaxation_draft.md`** (the name Investigate
recommended and the test plan's own examples assume).

## Steps

### Step 1 — Write the draft instruction-relaxation artifact
**Files:** `docs/ai/claude_md_prescan_mandate_relaxation_draft.md` (new file)

**Change:** Create the file with this structure. Frontmatter must mirror the shape confirmed at
`docs/ai/codex_posttool_adapter_real_command_proposal.md:1-7` (`status: active`, `layer: ai`,
`authority: P2`, `audience: agent`, `tags: [ai, claude-md, process-improvement]` — reusing this
ticket's own already-registered tags rather than introducing new ones).

1. **Opening disclaimer** (first paragraph, not buried later — per Investigate's Anti-Drift
   Hazards). Reuse the exact boilerplate pattern confirmed at
   `docs/ai/codex_posttool_adapter_real_command_proposal.md:11-17`, adapted to this draft's subject:
   state plainly that this document is for human review only, that nothing in this repository
   parses or executes it, and that it does not itself decide or imply activation. Must contain, as
   distinct matchable fragments (per `test_plan.md`'s
   `test_draft_instruction_change_artifact_exists_and_is_labeled_not_activated`): a "for human
   review only" (or equivalent) fragment, a "not activated" / "not applied" fragment, and a "does
   not itself" fragment (mirroring `redaction_retention_policy.md`'s own ratification-pending
   phrasing, confirmed verbatim by reading
   `tests/docs/test_redaction_retention_policy_doc.py:141-146`: `"drafted, not ratified"`,
   `"may not begin until"`, `"does not itself decide or imply approval"` — adapt the verb from
   "ratified/approval" to "activated/activation" for this draft's own subject).

2. **Activation Precondition section.** State explicitly, by literal ticket ID string, that
   activation is gated on `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s compliance fix being
   retro-confirmed by `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation section,
   and that this precondition is **currently pending, not satisfied** — cite
   `agent-monitoring/retro/RETRO-LAST14D.md`'s own finding (Investigate confirmed this file's `##
   Notes` section states verbatim that "no hand-orchestrated Investigate-phase run has occurred
   since the fix shipped, so there is no real data yet confirming compliance improved"). Do not
   recompute or restate the correlation numbers — cite the retro report as the source, per
   Investigate's Anti-Drift Hazards ("do not duplicate a second correlation/compliance metric").

3. **Proposed Replacement Instruction Text section.** Draft the full §2.1 ambient-utility substance
   (per this ticket's Scope — general text, not narrowed; see Anti-Drift Notes below for why), citing
   `docs/plans/knowledge-gateway-mcp-proposal.md:93-117` as source. Must include, as distinct
   matchable fragments (per `test_draft_covers_required_ambient_utility_substance`):
   - "ambient utility" framing placing the gateway/direct tools in the same category as `rg`, git
     history, Graphify, and Context Search (source: proposal.md:95-97);
   - the "optional ranking hints" framing for ticket ID/workflow/phase/changed-paths/agent-role/
     run ID (source: proposal.md:99-100);
   - a "not itself a workflow phase, gate, Definition-of-Done item, or mandatory ticket step" clause
     or close paraphrase (source: proposal.md:101-102);
   - the three cheapest-reliable-source bypass examples verbatim: `rg` for a simple exact text
     check, Graphify directly for a focused code-reference or dependency question, Context Search
     directly for a focused document lookup (source: proposal.md:107-109).

4. **Non-Regression Cross-Reference section (checklist format).** Explicitly name and quote/
   paraphrase all **three** live instruction surfaces that carry today's mandate, so a future
   activation ticket has a complete, non-partial checklist — not just the two surfaces this
   ticket's own Related Docs names:
   - `CLAUDE.md`'s `## Context Scan (Mandatory)` section (confirmed present at `CLAUDE.md:29-40`,
     the numbered 4-step `search_docs` → `graphify query` → fallback → check ordering, "Never
     start with grep");
   - `CLAUDE.md`'s `## Proactive Tool Use` table, "Any investigation" row (confirmed present at
     `CLAUDE.md:320-321`, Step 1/Step 2/Step 3 ordering, "never skip it");
   - `.claude/skills/implement-ticket/SKILL.md`'s Step 2 ("Investigate") phase-scoped callout
     (confirmed present at `SKILL.md:58`, the sentence beginning "Search-before-grep is
     phase-scoped, not satisfied by Step 0" through "the exact violation this instruction exists to
     prevent (`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`)") — this is the un-named-in-ticket
     5th surface Investigate flagged as a gap; it is the literal, currently-hardened mechanism
     whose compliance is the pending signal this entire draft is conditioned on, so omitting it here
     would defeat the ticket's own sequencing purpose.
   For each of the three, state plainly that this draft references it for a future activation
   ticket's use and does **not** edit it now.

5. **Closing "What this draft does not do" paragraph.** State explicitly: this document does not
   modify `CLAUDE.md`, any `.claude/agents/*.md` file, or `.claude/skills/implement-ticket/SKILL.md`;
   activation requires a separate, later ticket; and this document does not itself unblock or close
   the pending compliance signal it describes.

**Do NOT touch:** `CLAUDE.md`, any file under `.claude/agents/`, or
`.claude/skills/implement-ticket/SKILL.md`. This step only ever writes the one new file above.

**Verify:** `test_draft_instruction_change_artifact_exists_and_is_labeled_not_activated`,
`test_draft_records_activation_precondition_against_hardening_ticket`,
`test_draft_covers_required_ambient_utility_substance` (all three from
`tests/docs/test_prescan_mandate_instruction_draft.py`, added in Step 3).

### Step 2 — Annotate the proposal doc's Phase 0 bullet as complete-with-caveat
**Files:** `docs/plans/knowledge-gateway-mcp-proposal.md`

**Change:** §20's final Phase 0 bullet reads verbatim, confirmed at
`docs/plans/knowledge-gateway-mcp-proposal.md:1117-1118`:
> "Draft the generated-agent-instruction change replacing the blanket pre-scan mandate with the
> cheapest-reliable-source and ambient-utility rule; do not activate it before review."

This is the last unannotated bullet in the Phase 0 list — every other bullet in that same list
(lines 1050-1116) already carries a **Done** or **Drafted / pending ratification** annotation citing
the ticket that closed it (e.g. line 1101-1105's redaction/retention bullet: `"**Drafted / pending
ratification** (`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`) — see ... §11 ... the artifact is
drafted, not ratified; §24 item 1 remains an open reviewer decision this ticket does not
self-resolve."`). This ticket's own Related Docs did not name this file at all, and 3 of this
epic's 4 prior sibling tickets already missed this exact edit (per the parent agent's explicit
instruction) — do not repeat that omission.

Append an annotation to this bullet, in the same in-line style as the existing annotations,
reading (substance, not necessarily verbatim):
> "**Done (drafted; not activated)** (`TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT`) — see
> `docs/ai/claude_md_prescan_mandate_relaxation_draft.md`: drafted replacement instruction text
> covering §2.1's ambient-utility/cheapest-reliable-source substance, cross-referencing all 3 live
> instruction surfaces (CLAUDE.md's Context Scan section, CLAUDE.md's Proactive Tool Use table,
> and `.claude/skills/implement-ticket/SKILL.md`'s Step 2 callout) without editing any of them.
> Activation is explicitly gated on `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s compliance
> fix being retro-confirmed by `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation
> section — pending as of this ticket; this ticket does not itself activate or unblock activation."

Use "Done (drafted; not activated)" rather than a bare "**Done**" — a bare "Done" would misleadingly
imply the same completion class as the fully-implemented bullets above it (e.g. line 1051's frozen
schemas), which contradicts this ticket's own Out of Scope. This mirrors the precedent already set
by the redaction/retention bullet's own "Drafted / pending ratification" (not bare "Done") label for
the same reason.

**Do NOT touch:** Any other bullet or section in this proposal doc. Only the one bullet at
lines 1117-1118 gets an annotation appended.

**Verify:** No automated test covers this file's content (it is a plan/proposal doc, not a
contract with a structural test); verify manually by re-reading the edited bullet before Finalize,
and ensure `docs/plans/knowledge-gateway-mcp-proposal.md` appears in this ticket's `Files Changed`
section (the exact omission class that hit 3 of 4 prior siblings).

### Step 3 — Add the regression-guard test file
**Files:** `tests/docs/test_prescan_mandate_instruction_draft.py` (new file)

**Change:** Create the file following `tests/docs/test_redaction_retention_policy_doc.py`'s exact
pattern (confirmed by direct read: plain `Path.read_text()` string/heading assertions, an `ast`
import only where needed, module docstring stating "assert doc structure ... never runtime
behavior"). Implement the five tests from `test_plan.md`, all in this one file:

1. `test_draft_instruction_change_artifact_exists_and_is_labeled_not_activated` — asserts
   `docs/ai/claude_md_prescan_mandate_relaxation_draft.md` exists and its text contains the three
   distinct disclaimer fragments from Step 1.1.
2. `test_draft_records_activation_precondition_against_hardening_ticket` — asserts the draft's text
   contains the literal string `"TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP"` plus a phrase
   indicating the precondition is pending, not satisfied (e.g. assert both a "retro-confirmed" or
   "retro" fragment and a "pending" fragment are present — do not assert a phrase implying the
   precondition is already met).
3. `test_draft_preserves_investigator_and_skill_callouts_verbatim` — reads
   `.claude/agents/investigator.md` and asserts it still contains `"mcp__knowledge-search__search_docs"`,
   `"graphify"`, and `"does not substitute"` (confirmed live text at `investigator.md:12-16`, exact
   phrase "does not substitute for Investigate's own search-before-grep pass"); separately reads
   `.claude/skills/implement-ticket/SKILL.md` and asserts it still contains
   `"Step 0's one-time upfront call does not substitute for this phase-scoped call"` (confirmed
   live text at `SKILL.md:58`). Model both region-scoping and assertion style directly on
   `tests/tools/test_skill_investigate_search_before_grep.py`'s `_investigate_step_text()` helper
   (bound assertions to the `"2. **Investigate**"` .. `"3. **Plan**"` region) rather than a bare
   whole-file substring search, so a future edit elsewhere in `SKILL.md` cannot cause a false pass.
4. `test_draft_does_not_modify_claude_md_or_agent_md_files` — the single highest-priority test in
   this plan. Use `git diff --stat HEAD -- CLAUDE.md .claude/agents/*.md` (via `subprocess.run`,
   `cwd=_REPO_ROOT`) and assert empty output — i.e. the working tree has zero uncommitted diff
   against the last commit for these paths. **Anti-drift note:** this is a within-this-ticket's
   Test-phase check (run after Implement, before this ticket's own commit), not a permanent
   "these files may never change, by any future ticket, forever" pin — `tests/tools/
   test_agent_monitoring_manifest.py:142-158` documents exactly this failure mode for an earlier,
   similarly-broad writer guard (`test_writer_files_are_byte_unchanged_by_this_ticket`), which had
   to be removed once a later ticket's *approved* scope legitimately required touching the files it
   protected. If a future ticket's approved scope legitimately needs to edit `CLAUDE.md` or a
   `.claude/agents/*.md` file, narrowing or removing this specific test is that future ticket's own
   scoped responsibility — not evidence this test was wrong to add now.
5. `test_draft_covers_required_ambient_utility_substance` — asserts the draft's text contains each
   of the four distinct fragments listed in Step 1.3, as individually matchable strings (mirroring
   `test_redaction_retention_policy_doc_exists_and_has_required_sections`'s `never_cache_items` list
   shape, confirmed at `tests/docs/test_redaction_retention_policy_doc.py:51-60`).

**Other writers to these read targets (enumerated, per Fact-Verification Requirement #2):** this
test file only *reads* `docs/ai/claude_md_prescan_mandate_relaxation_draft.md` (written solely by
Step 1 of this ticket — no other writer), `CLAUDE.md` (written by many past/future tickets across
the repo's history, none of which run concurrently with this one), `.claude/agents/investigator.md`
(last written by `TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`, DONE, no concurrent writer),
and `.claude/skills/implement-ticket/SKILL.md` (last written by
`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`, DONE, no concurrent writer). This ticket's own
Implement phase is the only writer active during this ticket's session, and per Step 1/Step 2's
"Do NOT touch" guards, it must not write to any of the three live files. No race, no double-count,
no ordering hazard: this is a read-only test against files this ticket does not modify, run once
at Test-phase.

**Do NOT touch:** Any existing test file. This step only adds one new file.

**Verify:**
```
.venv/bin/python3 -m pytest tests/docs/test_prescan_mandate_instruction_draft.py -v
.venv/bin/python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -v
.venv/bin/python3 -m pytest tests/tools/test_skill_investigate_search_before_grep.py -v
```
(the latter two are the regression-surface files from `test_plan.md` — must keep passing unmodified,
proving this ticket did not silently touch what they pin).

## Scope Guards

- **Do not edit `CLAUDE.md`** — neither the Hard Rules bullet (line 24), the Context Scan section
  (lines 29-40), nor the Proactive Tool Use table (lines 320-321). Referenced and quoted only.
- **Do not edit any file under `.claude/agents/`**, specifically `.claude/agents/investigator.md`
  (lines 12-16) — the predecessor fix (`TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`) this
  ticket must not regress.
- **Do not edit `.claude/skills/implement-ticket/SKILL.md`**, specifically the Step 2 phase-scoped
  callout at line 58 — the exact mechanism `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` built,
  whose compliance is this ticket's own load-bearing "pending, not yet retro-confirmed" finding.
  This surface is not named in the ticket's own Related Docs/Related Code Areas but is in scope for
  this guard per Investigate's explicit flag.
- **Do not activate anything.** No live instruction file changes what agents are told to do as a
  result of this ticket. The draft is inert prose only.
- **Do not fabricate or recompute compliance data.** Cite `agent-monitoring/retro/RETRO-LAST14D.md`
  as the source for the "pending, not yet retro-confirmed" claim; never recompute a parallel
  correlation number.
- **Do not narrow §2.1's substance without flagging it.** This plan chose to draft the *general*
  §2.1 ambient-utility text (not a hand-crafted carve-out preserving only the hardened
  hand-orchestration entry point) — see Anti-Drift Notes below for why this is not left as an
  open question.
- **Do not resolve §24's other open decisions.** Only this specific instruction draft's sequencing
  is in scope.
- **Do not touch `docs/engine/contracts/knowledge_gateway_mcp/`** — the Design Decision above
  explicitly rejects that location for this ticket's deliverable; no file in that directory should
  be created or modified by this ticket.

## Dependency Map

- Step 1 (draft artifact) has no dependency on Step 2 or Step 3 — it can be written first,
  independently verified against Step 3's tests once Step 3 exists.
- Step 2 (proposal doc annotation) depends on Step 1 only insofar as its annotation text cites
  Step 1's file path — write Step 1 first so the path is real, but Step 2 makes no other file
  dependency.
- Step 3 (test file) depends on Step 1's file existing (tests 1/2/5 read it) and on Step 1/Step 2
  having made zero edits to the three live instruction files (test 3/4 assert this). Step 3 should
  therefore run last, after Step 1 and Step 2 are both complete, even though its own file write is
  independent of Step 2's content.

Recommended implementation order: Step 1 → Step 2 → Step 3.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `investigation.md` records the real, current status of `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` (and the tracking ticket's correlation data), not an assumption | Already satisfied by the Investigate phase (see `investigation.md` "Status of..." sections) — no Plan/Implement step required | N/A (satisfied pre-Plan; no test needed, it is a document-content fact already recorded) |
| The drafted instruction text exists as a reviewable artifact, explicitly labeled not-yet-activated, and is not applied to any live `CLAUDE.md` or `.claude/agents/*.md` file | Step 1 (creation), Step 3 (regression guard) | `test_draft_instruction_change_artifact_exists_and_is_labeled_not_activated`, `test_draft_does_not_modify_claude_md_or_agent_md_files` |
| The draft or this ticket's notes explicitly state the activation precondition relative to the hardening ticket's status found during Investigate | Step 1 (Activation Precondition section) | `test_draft_records_activation_precondition_against_hardening_ticket` |
| No `CLAUDE.md` or `.claude/agents/*.md` diff appears in this ticket's `Files Changed` other than the new draft-artifact location itself | Step 1, Step 2, Step 3 (all constrained by Scope Guards; Step 3 adds the mechanical proof) | `test_draft_does_not_modify_claude_md_or_agent_md_files`, `test_draft_preserves_investigator_and_skill_callouts_verbatim` |

## Anti-Drift Notes

- **The un-named 5th surface is the load-bearing one.** The ticket's own Related Docs names only
  `CLAUDE.md`'s Context Scan and Proactive Tool Use sections, but Investigate confirmed
  `.claude/skills/implement-ticket/SKILL.md`'s Step 2 callout (`SKILL.md:58`) is the literal,
  currently-hardened mechanism whose compliance this entire ticket's sequencing logic depends on.
  Step 1.4 and Step 3's test 3 both explicitly cover it — do not treat the ticket's own Related Docs
  list as the complete non-regression surface.
- **General §2.1 text, not a narrower carve-out — this is a made decision, not an open question.**
  Investigate flagged this as a judgment call for Plan (Risks and Open Questions, 2nd bullet). This
  plan resolves it: draft the full §2.1 ambient-utility substance with an explicit activation
  precondition attached, rather than hand-authoring a narrower exception clause the proposal text
  itself never asked for. This also matches `test_plan.md`'s own
  `test_draft_covers_required_ambient_utility_substance`, which was already written assuming full
  §2.1 substance — choosing a narrower carve-out instead would contradict the already-approved test
  plan, so this is not left as an Unresolved Question requiring a separate decision before
  Implement.
- **The gateway does not exist yet — do not let the draft imply otherwise.** Per Investigate's Risks
  section, no `knowledge_context`/`knowledge_status` MCP tool exists in `tools/` yet (only Phase 0 is
  complete). The draft's Proposed Replacement Instruction Text must preserve proposal.md:115-117's
  own framing ("current repository instructions remain in force; merely implementing the MCP does
  not silently override them") rather than softening it into present-tense availability.
  §2.1's own bypass guidance (`rg`/Graphify/Context Search direct calls) is real and callable today,
  independent of the not-yet-built gateway — the draft may describe that part as available now.
  Only the gateway itself is not yet callable.
- **The `test_agent_monitoring_manifest.py` precedent (lines 142-158) is a direct warning, already
  applied above in Step 3.4:** a broad "these files must never change, forever" guard was previously
  removed once legitimate future scope required touching the files it protected. This plan's
  regression-guard test is intentionally scoped to *this ticket's own diff*, not an eternal
  prohibition — a future ticket with genuine, approved scope to edit `CLAUDE.md` or
  `.claude/agents/*.md` must narrow/remove this specific test as part of its own scope, not treat
  its existence as unconditional.
- **This ticket cannot manufacture the pending compliance signal.** Do not let Implement (or any
  later phase) treat this ticket as having resolved or advanced
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s pending retro-confirmation — it can only move
  when a real hand-orchestrated Investigate-phase run recurs naturally and a future retro window
  picks it up.
- **Files Changed must include the proposal-doc edit.** 3 of this epic's 4 prior sibling tickets
  omitted their own `docs/plans/knowledge-gateway-mcp-proposal.md` §20 edit from their `Files
  Changed` section. Step 2's edit to that file must be listed explicitly at Finalize.
