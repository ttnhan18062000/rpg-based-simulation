---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP
artifact_type: plan
tags: [ai, agent-monitoring, process-improvement]
---

# Implementation Plan — TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP

## Summary

`investigation.md` confirmed the real gap is not hotfix-tier routing (all 3 flagged runs are
`tier:standard`; hotfix has no Investigate-phase event at all — `implement-ticket.js:722`) but
whole-pipeline hand-orchestration: the top-level Claude session executed `.claude/skills/implement-ticket/SKILL.md`'s
numbered pipeline steps directly instead of dispatching `Agent(subagent_type: ...)` calls, and
`SKILL.md`'s own numbered step 2 ("Investigate", `SKILL.md:58`) carries no search-before-grep
instruction of its own — only Step 0 ("Context search", `SKILL.md:51-55`) does, and Step 0 fires
once, upfront, before Scope, not per-phase. This plan closes that gap the same way
`TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP` closed the equivalent gap in
`.claude/agents/investigator.md:12-20`: add a self-contained, phase-scoped, non-optional
search-before-grep instruction directly inside step 2's own text block in `SKILL.md`, add a
regression test that the instruction lands in that specific bounded block (not merely somewhere in
the file, and not merely as a "see Step 0" pointer), and add a short doc section to
`docs/guides/agent_monitoring.md` recording the fix, mirroring the existing "Sidecar Reminder Hook"
section's structure and cross-reference style. No `src/` code, Mechanics Bible chapter, engine
contract, or parity ledger entry is touched — this is agent-orchestration instruction text only.

## Steps

### Step 1 — Add a phase-scoped search-before-grep callout to SKILL.md's Investigate step

**Files:** `.claude/skills/implement-ticket/SKILL.md`

**Change:** Verified by direct read (`SKILL.md:49-59`): the "Pipeline (standard tier)" section's
step 2 currently reads, in full:

```
2. **Investigate** — produce `investigation.md` and `test_plan.md` (skipped for hotfix). At the
   end of this phase, also run the shadow context-packet call site (`implement-ticket.js:560-588`):
   ... This step is skipped whenever Investigate itself is skipped (hotfix tier).
```

Step 0 ("Context search", `SKILL.md:51-55`) is confirmed to be a single upfront call before Scope
(`Raw file reads and grep are follow-up steps only — use paths from steps 1–2 first`, `SKILL.md:55`)
with no per-phase repeat instruction anywhere else in the file — grepped the file's full text (read
in full above, lines 1-78) and confirmed no other `search_docs`/`graphify` mention exists outside
Step 0.

Append a new sentence to the end of step 2's existing text block (after "...skipped (hotfix
tier)."), before the numbering moves to step 3 ("Plan", `SKILL.md:59`). Do not touch the existing
step 2 sentences (the shadow-context-packet instruction) — only append. Suggested text (the
implementer may adjust wording, but it must preserve every semantic element listed below):

> **Search-before-grep is phase-scoped, not satisfied by Step 0:** before performing any Read or
> grep-flavored Bash work for this phase — including, and especially, when Investigate is being
> performed directly by the orchestrating session rather than via
> `Agent(subagent_type: "investigator")` dispatch — call `mcp__knowledge-search__search_docs` with
> this ticket's own topic and run `graphify query "<ticket title>"` again, even though Step 0
> already ran once at the very start of the ticket. Step 0's one-time upfront call does not
> substitute for this phase-scoped call; treating "Step 0 already searched" as license to skip
> straight to grep/Read here is the exact violation this instruction exists to prevent
> (`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`).

Required semantic elements (so Step 2 of this plan can assert on them regardless of exact wording
chosen):
1. Names both tools by their real identifiers: `mcp__knowledge-search__search_docs` and `graphify`.
2. States explicitly that Step 0 does not substitute / is not sufficient on its own.
3. Is self-contained — a reader executing step 2 in isolation gets the full instruction without
   needing to re-read Step 0 (no bare "see Step 0 above" phrasing).
4. Lands inside step 2's own text block, between the "2. **Investigate**" marker and the
   "3. **Plan**" marker — not in Step 0, not in a document-wide preamble, not in the Notes section.

**Do NOT touch:**
- The literal string `2. **Investigate**` (the bolded phase-title heading) — must remain byte-for-byte
  present, because `tools/gate_checks/workflow_meta_conformance.py::check_skill_doc_covers_meta_phases`
  (verified via `tests/tools/test_workflow_meta_conformance.py:322-328`,
  `test_check_covers_real_implement_ticket_skill_md`, which currently asserts zero FAIL findings and
  exactly 12 phases matched) locates this phase by regex-matching the bolded title text. Breaking
  or renaming it fails that test and the Finalize-tail `check_workflow_meta_conformance` advisory.
- The existing shadow-context-packet sentence within step 2 (`SKILL.md:58`, the
  `implement-ticket.js:560-588` reference) — append after it, do not reword or remove it.
- Step 0 (`SKILL.md:51-55`) — per investigation.md's Anti-Drift Hazards, adding the callout only to
  Step 0 and calling it done is explicitly the failure mode already ruled insufficient (all 3
  flagged runs presumably had Step 0 fire once and still skipped straight to grep at Investigate).
  Step 0's own text must not be edited by this ticket.
- Steps 3 through 13 (Plan through Finalize) and the "Hotfix tier skips..." paragraph
  (`SKILL.md:71`) — out of scope; this ticket's Out of Scope section explicitly excludes redesigning
  hotfix-tier's pipeline stages.
- `.claude/agents/investigator.md` — explicitly out of scope per the ticket; its own fix
  (`TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`) is verified working and must not be re-touched
  or "harmonized."
- `.claude/workflows/implement-ticket.js` — the JS is the authoritative source of phase names/order;
  this ticket only adds prose to the translation-aid `SKILL.md`, and must not touch the JS's
  hotfix-tier branch (`implement-ticket.js:721-722`) or any other JS logic.

**Other readers of this file (no concurrent writers):** `SKILL.md` is a single Markdown file edited
by a human/agent session, never written concurrently by another pipeline phase or background
process. The only other code that *reads* it is
`tools/gate_checks/workflow_meta_conformance.py::check_skill_doc_covers_meta_phases` (a read-only
regex scan, run at Finalize and as a pytest test) and any future hand-orchestrating session that
reads it live at Investigate time — both are satisfied as long as the phase-title heading string is
preserved (addressed above) and the new sentence is additive, not a restructuring of the file's
existing step numbering or table.

**Verify:** `test_skill_investigate_step_has_search_before_grep_callout` and
`test_skill_investigate_callout_survives_step0_removal_check` (Step 2 below), plus unmodified pass
of `tests/tools/test_workflow_meta_conformance.py` and
`tests/tools/test_current_run_sidecar_orchestrator.py` (regression surface, per test_plan.md).

---

### Step 2 — Add the regression test for the callout

**Files:** new file `tests/tools/test_skill_investigate_search_before_grep.py`

**Change:** test_plan.md offers a choice between extending
`tests/tools/test_current_run_sidecar_orchestrator.py` or creating a new file, deferring to the
implementer "if it does not make that file's own docstring/scope claim inaccurate." Verified by
direct read (`tests/tools/test_current_run_sidecar_orchestrator.py:1-8`): that file's own docstring
states it covers "Static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js`
and `docs/agent-monitoring/schema.md`" and its only two path constants are `_WORKFLOW_PATH` and
`_SCHEMA_DOC_PATH` — neither points at `.claude/skills/`. Adding a `SKILL.md`-reading test to that
file would make its own docstring inaccurate. Decision: create a new file instead, following the
same `Path.read_text()` raw-text-assertion pattern (no JS/Markdown test runner exists for
`.claude/skills/*.md`, matching the established convention).

Implement two tests:

1. `test_skill_investigate_step_has_search_before_grep_callout`:
   - Read `.claude/skills/implement-ticket/SKILL.md` via `Path.read_text()`.
   - Locate the bounded region between the literal marker `"2. **Investigate**"` and the literal
     marker `"3. **Plan**"` (`str.index()` on both markers, slice between them) — mirrors the
     bounding technique test_plan.md specifies, so a fix that only touches Step 0 cannot false-pass.
   - Assert `"mcp__knowledge-search__search_docs"` appears in the bounded region.
   - Assert `"graphify"` appears in the bounded region.
   - Assert a phrase indicating Step 0 is insufficient on its own appears in the bounded region
     (e.g. assert `"does not substitute"` or equivalent language actually used in Step 1's final
     wording — the implementer must keep this assertion in sync with whatever exact phrase Step 1
     lands on, since Step 1 explicitly allows wording flexibility).

2. `test_skill_investigate_callout_survives_step0_removal_check`:
   - Same bounded region as above.
   - Assert the region does NOT contain a bare cross-reference-only phrase such as `"see Step 0"`
     with no accompanying instruction verbs — i.e. assert that `"search_docs"` and `"graphify"`
     both appear textually inside the bounded region itself (already covered by test 1), and
     additionally assert the region is self-contained by checking it does not consist of only a
     pointer sentence (e.g. assert the bounded region's length exceeds a minimal threshold, or
     assert it contains an imperative verb like `"call"` alongside the tool names) — the intent is
     a defense-in-depth guard against a future edit weakening the callout back into a pointer,
     not a new independent semantic check.

**Do NOT touch:** `tests/tools/test_current_run_sidecar_orchestrator.py`,
`tests/tools/test_workflow_meta_conformance.py`, `tests/tools/test_concern_investigator_agent_definition.py`,
`tests/tools/test_generate_retro.py` — all four are regression surface per test_plan.md and must
keep passing unmodified (no edits to their assertions or scope).

**Other writers of this resource:** none — this is a brand-new test file; no other phase or agent
writes to it.

**Verify:**
```
.venv/bin/python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py \
  tests/tools/test_workflow_meta_conformance.py tests/tools/test_generate_retro.py \
  tests/tools/test_skill_investigate_search_before_grep.py -v
```
All must pass, including the two new tests and the three unmodified regression files.

---

### Step 3 — Document the fix in docs/guides/agent_monitoring.md

**Files:** `docs/guides/agent_monitoring.md`

**Change:** Verified by direct read (`docs/guides/agent_monitoring.md:194-213`): the existing
"Sidecar Reminder Hook" section (added by `TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`)
sits between the "Epic Staleness Check" section and "Makefile Targets" (`docs/guides/agent_monitoring.md:216`),
and follows a consistent structure: what the gap was, why it recurs under hand-orchestration, the
concrete fix, and any automated backstop (there, a `PreToolUse` hook). Also verified: the "Tool
Safety Audit" retro-report row (`docs/guides/agent_monitoring.md:70`) already documents the
search-before-grep compliance *metric* this fix improves compliance with, but does not itself
describe the `SKILL.md` fix.

Insert a new section titled `## Investigate-Step Search-Before-Grep Callout` immediately after the
"Sidecar Reminder Hook" section and before the `---` separator preceding "## Makefile Targets"
(i.e. insert right after line 213's closing content, before line 214's `---`/216's heading). Content
must cover, mirroring the Sidecar Reminder Hook section's own style:
- What the gap was: hand-orchestrated sessions performing Investigate-phase work directly (not via
  `Agent(subagent_type: "investigator")`) had no phase-scoped search-before-grep instruction —
  `SKILL.md`'s Step 0 fires once, upfront, and does not repeat per phase.
- The fix: `SKILL.md`'s own numbered step 2 ("Investigate") now carries an explicit, non-optional,
  self-contained search-before-grep instruction (cite `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`),
  mirroring the equivalent fix already made to `.claude/agents/investigator.md` for the
  agent-dispatched path (cite `TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`).
- Cross-reference the Tool Safety Audit row (line 70) as the metric a reader should check to confirm
  the fix holds over time, and note that proving long-term compliance is the responsibility of the
  sibling ticket `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`, not this section itself.

**Do NOT touch:** The "Tool Safety Audit" row's existing description of
`compute_tool_safety_metrics()`'s detection logic (`docs/guides/agent_monitoring.md:70`) — at most
add one short cross-reference sentence pointing to the new section; do not alter its existing
content describing the metric itself. Do not touch `tools/agent-monitoring/generate_retro.py` or
any other detector code — this is a docs-only addition. Do not touch the "Sidecar Reminder Hook"
section's own text.

**Other writers of this resource:** none concurrent — this is a single Markdown file, edited
directly. The only other consumer is `done-checker`'s static `check_docs_to_update_coverage`
(`tools/gate_checks/done_checker_static.py`), which at Verify time checks whether
`docs/guides/agent_monitoring.md` was actually touched, matching `investigation.md`'s "Docs
Requiring Update" bullet — a read-only consumer, not a writer, so no interaction/race to reconcile.

**Verify:** No dedicated new test required — test_plan.md explicitly defers this to the existing
Verify-phase static check (`check_docs_to_update_coverage`) rather than duplicating it as a
hand-written test. Manually confirm the new section reads correctly and the doc's frontmatter
(if any date/tags fields exist) is left otherwise unmodified.

## Scope Guards

- Do not touch `.claude/agents/investigator.md` under any circumstance — its fix is verified
  working and is explicitly out of scope.
- Do not touch `.claude/workflows/implement-ticket.js`, including its hotfix-tier short-circuit at
  `implement-ticket.js:721-722` (`pushEvent('Investigate', 'investigator', 'skipped', ...)`) — this
  ticket's own investigation ruled out hotfix-tier routing as the mechanism; no redesign of
  hotfix-tier's pipeline stages is in scope.
- Do not modify `tools/agent-monitoring/generate_retro.py` or `compute_tool_safety_metrics()`'s
  detection logic (`INFRA-315`) — this ticket fixes the entry-point instruction, not the compliance
  detector.
- Do not add the callout only to Step 0 (`SKILL.md:51-55`) — it must land specifically inside step
  2's own text block, per the investigation's Anti-Drift Hazards.
- Do not attempt to force real `Agent(subagent_type: ...)` dispatch for every phase, or otherwise
  fix the broader "why wasn't any subagent spawned at all in these 3 runs" question — that is a
  separate, broader compliance gap this ticket's Scope does not ask to solve.
- Do not touch `.claude/skills/create-tickets/SKILL.md` or any other skill file — stay inside
  `implement-ticket/SKILL.md`. `create-tickets/SKILL.md`'s own drift gap is tracked by a distinct
  ticket (`TCK-20260804-CREATE-TICKETS-SKILL-SYNC`).
- Do not re-run or re-litigate the 3 already-closed flagged tickets — this ticket is forward-looking
  only.
- Do not touch any `docs/parity_ledger/*.yaml` file or any `docs/mechanics/`/`docs/engine/` file —
  investigation.md confirmed zero applicable citations; this is agent-orchestration tooling only.

## Dependency Map

- Step 1 has no dependencies — it is the first and only functional change (the instruction text
  itself).
- Step 2 depends on Step 1: the new tests assert on the specific wording Step 1 lands on (the
  required semantic elements are fixed, but the exact phrase for the "Step 0 does not substitute"
  assertion must match). Implement Step 1 first, then write Step 2's assertions against the actual
  final text.
- Step 3 is independent of Step 2 (no shared file or test dependency) but should reference the
  final wording chosen in Step 1 for accuracy. It may be implemented in parallel with Step 2, but
  should not be finalized until Step 1's exact wording is locked in.
- Recommended execution order: Step 1 → Step 2 → Step 3 (sequential is simplest and avoids any
  wording-sync rework, even though Step 3 is not strictly blocked by Step 2).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `investigation.md` identifies the real, confirmed dispatch mechanism for `agent=claude` Investigate-phase work, sourced from `.claude/workflows/implement-ticket.js` (or equivalent) and real `events.jsonl` records — not assumed. | Already satisfied by the existing `investigation.md` artifact (prior phase output) — no implementation step in this plan produces this; it is a precondition this plan builds on. | N/A (artifact-review, not a test) |
| An explicit search-before-grep callout exists at that entry point. | Step 1 (adds the callout to `SKILL.md` step 2) | `test_skill_investigate_step_has_search_before_grep_callout`, `test_skill_investigate_callout_survives_step0_removal_check` (Step 2) |
| `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (sibling epic child) can measure whether this fix holds in the next retro window — this ticket does not itself need to prove long-term compliance, only that the callout is real and reachable. | Step 1 (callout is real, in the file hand-orchestrating sessions actually read) + Step 3 (doc records the fix for future auditors, cross-referencing the Tool Safety Audit metric the sibling ticket will use) | No test proves "holds over time" within this ticket (by design, per test_plan.md and investigation.md); reachability is verified structurally by Step 2's tests confirming the callout is present in the live `SKILL.md` file, not a fixture copy |

## Anti-Drift Notes

- The single most important hazard, called out explicitly in `investigation.md`'s Anti-Drift
  Hazards: **do not add the callout only to Step 0 and call it done.** Step 0 already exists and
  demonstrably did not prevent the 3 flagged violations. The fix must be phase-scoped, landing
  inside step 2's own text block — Step 2's tests are bounded specifically to guard against this
  regression.
- Do not conflate this fix with forcing real subagent dispatch. `SKILL.md`'s translation table
  (`SKILL.md:35`, "Spawn `Agent(subagent_type: "name", ...)`") already correctly instructs this;
  the fact that the 3 flagged runs didn't follow it at all is a separate, broader gap this ticket
  does not attempt to solve.
- Preserve the exact bolded phase-title strings (`2. **Investigate**`, `3. **Plan**`, and all
  others) — `check_skill_doc_covers_meta_phases` regex-matches on these; a reworded or restructured
  heading silently fails that check even if the new instruction text itself is fine.
- The investigation's one open question — whether the exact per-run trigger across the 3 flagged
  tickets is subagent spawn-cap exhaustion (as the disclosed
  `TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP` precedent showed) or a more general
  no-subagent-dispatch operating pattern — is explicitly judged by `investigation.md` as **not
  blocking**: the fix target (the missing instruction at `SKILL.md` step 2) is identical either way.
  This plan treats it as a resolved non-blocker, left for a future retro to characterize further,
  not as an Unresolved Question requiring a decision before implementation.
- All open items from `investigation.md` are either already resolved (hotfix-tier hypothesis ruled
  out; entry point confirmed as `SKILL.md`) or explicitly judged non-blocking by the investigation
  itself (the per-run trigger-cause question, addressed above). Implementation may proceed directly
  from this plan — no `## Unresolved Questions` section is included since there is nothing to flag
  for human review.
