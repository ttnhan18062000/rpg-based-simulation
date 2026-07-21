---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-AGENTS-DISPOSITION-FIX
phase: done
date: 2026-07-21
tags: [ai, workflows, process-improvement]
---

# TCK-20260721-AGENTS-DISPOSITION-FIX

## Title
Correct the "Approved active location" claim in `docs/ai/agents_dir_disposition.md`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`docs/ai/agents_dir_disposition.md` (delivered by the already-DONE `TCK-20260721-AGENTS-DIR-DISPOSITION`) currently states, in its "Approved active location" section (lines 34-43) and its "Related" line (line 71), that `.claude/` is "the one approved active Codex/Claude instruction-and-skill location." This is factually wrong for Codex: per the official Codex manual — already cited and VERIFIED in the sibling doc `docs/ai/codex_capability_matrix.md` (§5, lines 111-119) — Codex discovers durable repository guidance from a root `AGENTS.md` file and repository skills from `.agents/skills/` (scanned cwd-to-repo-root), not from `.claude/`. The two docs from the same discovery batch currently contradict each other. This contradiction was flagged as a blocking correction in Codex's gate-closure review response (`docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_response_codex.md`, "Blocking correction — Output 1's Codex location" section) ahead of closing the parent discovery epic `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`.

## Scope
- Rewrite the "Approved active location" section of `docs/ai/agents_dir_disposition.md` (currently lines 34-43) to state that two separate provider-native delivery surfaces exist, not one shared location:
  - **Claude**: `.claude/` (rules → `CLAUDE.md`, orchestration → `.claude/workflows/*.js`, skills → `.claude/skills/`, roles → `.claude/agents/*.md`) — already active, correctly documented as-is, unchanged by this fix.
  - **Codex**: root `AGENTS.md` (durable instructions) + `.agents/skills/` (repository skills), per the official Codex manual as verified in `docs/ai/codex_capability_matrix.md`.
- Explicitly state that neither a root `AGENTS.md` file nor a reviewed/generated `.agents/skills/` Codex-delivery subtree exists in this repo yet (confirmed during this ticket's scoping: `AGENTS.md` and `.codex/` are both absent from the repo root). The currently-present `.agents/skills/*` content remains legacy/stale and keeps its existing archive-retire / retain-and-migrate classification (per-path table, lines 15-32) unchanged — this fix must not read as "un-archiving" or reclassifying that content.
- State that a future, real Codex delivery subtree (root `AGENTS.md` + reviewed `.agents/skills/`) must eventually be generated/reviewed from the shared `agent-orchestration/` contract (per `docs/architecture/agent_orchestration_contract.md`'s "Source Ownership" decision, status Decided, contract directory not yet created) — not produced by simply reclassifying or re-enabling today's stale `.agents/skills/` copies. That generation work is separate, later implementation-epic scope, not part of this fix.
- Update the one "Related" line (currently line 71) that also asserts "the `.claude/` orchestration layer this doc names as the approved active location," so it no longer implies a single shared location once the section above is corrected.
- Correct the same "one approved active Codex/Claude instruction-and-skill location" claim anywhere else it appears verbatim within `docs/ai/agents_dir_disposition.md` (e.g. the intro paragraph, line 11, if it restates the same false framing) for internal consistency with the corrected section.

## Out of Scope
- Does not touch the per-directory archive-retire / retain-and-migrate classification table (lines 15-32) — that per-path classification of individual `.agents/skills/*` and `.agents/rules/*` entries was already correct and is not being revisited.
- Does not create an `AGENTS.md` file or any `.agents/skills/` Codex-delivery content — no such subtree exists yet, and generating one is separate, later implementation-epic work gated behind the shared `agent-orchestration/` contract.
- Does not touch `docs/ai/codex_capability_matrix.md` — its §5 citation of the `.agents/skills` rule remains accurate once the disposition doc's framing is fixed; no change needed there.
- Does not touch the parent epic ticket (`tickets/inprogress/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md`) or attempt to close it — closing the epic is a separate follow-up after this correction lands, per the Codex review's stated closure condition.
- Does not create or modify `docs/architecture/agent_orchestration_contract.md` or the `agent-orchestration/` directory itself.
- Does not modify the "WorkflowRegistry determination," "Test-pairing note," or "What this doc does not do" sections of `docs/ai/agents_dir_disposition.md` — unrelated to the location-claim error.

## Acceptance Criteria
1. `docs/ai/agents_dir_disposition.md`'s "Approved active location" section no longer states or implies that `.claude/` is a Codex-discovered location; it separately names Claude's delivery surface (`.claude/`) and Codex's delivery surface (root `AGENTS.md` + `.agents/skills/`), each with a citation to its verifying source.
2. The doc explicitly states that no Codex delivery subtree (root `AGENTS.md`, reviewed `.agents/skills/`) exists in this repo yet, and that the present `.agents/skills/*` content remains classified per the unchanged per-path table — i.e., this fix does not read as reclassifying or re-enabling that content.
3. The doc states that the eventual single semantic authority for both provider surfaces is the shared `agent-orchestration/` contract (not yet built), citing `docs/architecture/agent_orchestration_contract.md`'s Source Ownership decision.
4. Line 71's "Related" bullet no longer asserts `.claude/` as "the approved active location" in a way that contradicts the corrected section above.
5. The per-path classification table (lines 15-32) is byte-identical to its pre-fix state — diff the file and confirm no lines in that table range changed.
6. `docs/ai/codex_capability_matrix.md` is unmodified — diff confirms zero changes.
7. `python3 tools/validate_frontmatter.py docs/ai/agents_dir_disposition.md` (or equivalent frontmatter validation invoked by the standard hotfix pipeline) passes — frontmatter `layer`/`tags` on the corrected doc remain valid registry entries.
8. If `docs/` files were modified (they are), `make knowledge-index-update` is run per the Workflow Rule's "After Work" step.

## Related Tickets
- `tickets/done/TCK-20260721-AGENTS-DIR-DISPOSITION.md` — delivered the doc this ticket corrects.
- `tickets/done/TCK-20260721-CODEX-CAPABILITY-MATRIX.md` — sibling ticket whose citation (§5) is the evidentiary source for this correction; not itself modified.
- `tickets/inprogress/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md` — parent discovery epic currently blocked from closing on this exact correction (see Codex's gate-closure review response below); not modified or closed by this ticket.

## Related Docs
- `docs/ai/agents_dir_disposition.md` — the doc being corrected.
- `docs/ai/codex_capability_matrix.md` — VERIFIED source of the correct Codex `AGENTS.md` / `.agents/skills/` discovery rule (§5, lines 111-119).
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_response_codex.md` — "Blocking correction — Output 1's Codex location" section; the review that identified this error and specified the required fix shape.
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md` — the closure summary being corrected-against (not itself in scope for this ticket, but referenced by the review).
- `docs/architecture/agent_orchestration_contract.md` — Source Ownership decision (Decided: shared contract lives at future repo-root `agent-orchestration/`), cited as the eventual single semantic authority.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/investigation.md` — prior investigation behind the doc now being corrected; not modified.

## Related Code Areas
- None — this is a documentation-only correction. No `src/` or `tests/` files are in scope.

## Assumptions / Open Questions
- Assumes `layer: ai` is correct per `docs/guidelines/layer_registry.jsonl` ("Claude agent/orchestration tooling") — confirmed via `python3 tools/layer_registry.py list`.
- Assumes tags `[ai, workflows, process-improvement]` are all already registered (confirmed via `python3 tools/tag_registry.py list`) and match the tag set used by the doc's own frontmatter and the two related tickets; no new tag registration needed.
- Assumes this correction does not require re-touching `docs/ai/codex_capability_matrix.md`'s frontmatter or content, since the review explicitly states Output 4 (that doc) is "Approved for discovery" with no blocking issue.
- Assumes closing the parent epic (`TCK-20260721-PROVIDER-AGNOSTIC-EPIC`) is out of scope and left to a separate follow-up ticket, consistent with the Codex review's "Closure condition" section which treats this correction as a precondition, not the closure act itself.
- If a future reviewer disagrees that `.agents/skills/*`'s current classification should stay untouched, that would invalidate this ticket's Out of Scope boundary and require re-scoping — flagged here as the one assumption most likely to be challenged.

## Implementation Notes

**Task 1 — `docs/ai/agents_dir_disposition.md`:**
- Rewrote the "Approved active location" section (was lines 34-43) to state two separate provider-native delivery surfaces: Claude (`.claude/`, already active, unchanged) and Codex (root `AGENTS.md` + `.agents/skills/`, per the official Codex manual, citing `docs/ai/codex_capability_matrix.md` §5). Added an explicit statement that neither Codex surface exists in this repo yet (verified `ls AGENTS.md` and `ls .codex/` both fail — command run directly during implementation, not merely cited from the ticket), and that the present `.agents/skills/*` content stays classified exactly per the unchanged per-path table, with an explicit "must not be read as un-archiving" caveat. Added the eventual-single-semantic-authority statement citing `docs/architecture/agent_orchestration_contract.md`'s Source Ownership decision (verified `Status: Decided` directly in that file via grep before citing it).
- Preserved the original section's two `retain-and-migrate` carve-out callouts (`engine_contracts.md`, the 6 unreviewed `.agents/skills/` dirs) but reframed them as Claude-surface-specific future-ticket work, since the "one location" framing they depended on no longer exists.
- Fixed the intro paragraph (line 11) which also restated "this doc settles on exactly one approved future active Codex instruction/skill location" — reworded to "settles today's approved active delivery surfaces for each provider separately."
- Fixed the "Related" line (was line 71) that called `.claude/` "the approved active location" — reworded to "one of the two provider-native delivery surfaces this doc names."
- Did not touch the per-path classification table, WorkflowRegistry determination, Test-pairing note, "What this doc does not do" section, or frontmatter — confirmed by re-reading the full file after edits.
- Did not touch `docs/ai/codex_capability_matrix.md` (read-only, used only as a citation source).

**Task 2 — `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md`:**
- (a) Fixed the Output 2 status table: Contract Representation/Format and Source Ownership changed from "Proposed-pending-implementation-evidence" to "Decided" (verified directly against `docs/architecture/agent_orchestration_contract.md`'s `**Status:**` lines via grep before editing). Updated the "Gap carried forward" line from "3 of 5" to "2 of 5," noting the correction.
- (b) Rewrote the Output 1 section to match Task 1's corrected two-surface framing, added a note that the section was corrected following Codex's review, and updated its "Gap carried forward" line to mention the Output 1/4 contradiction fix.
- (c) Added one clarifying sentence at the top of the Output 5 bullet list stating the proof is of a replay runner being built/tested, not a real Codex adapter execution, citing Phase 4 of Codex's `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md:216` (verified that file and line exist and describe "Real Codex replay and shadow parity" before citing).
- (d) Left the "Net Assessment" section's 3 carried-forward gaps (monitoring-writer portability, conformance mechanism, Codex hook payload shape) unchanged — read and confirmed these are implementation-scoping gaps distinct from the Output 1/table wording corrections, per the ticket's own guidance not to remove them.
- (e) Replaced the "Ask" section (3 open questions to Codex) with a "Codex review response received" section summarizing Codex's actual response and pointing to the response doc, noting the gate should be re-reviewed for closure given these corrections.

No deviations from the plan; all edits map directly to the ticket's Scope items and the Codex review's "Blocking correction" and "Confirmed, non-blocking outputs" sections.

## Test Summary
Documentation-only change; no `src/`/`tests/` files touched (per Scope and Related Code Areas: "None"). Verification performed:
- `python3 tools/validate_frontmatter.py docs/ai/agents_dir_disposition.md` → OK.
- `python3 tools/validate_frontmatter.py docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md` → OK.
- Manually diffed the per-path classification table (lines 15-32 of the corrected doc) against the pre-edit read to confirm byte-identical (AC5).
- Confirmed `docs/ai/codex_capability_matrix.md` was never opened for writing (AC6).
- `make knowledge-index-update` run after edits (AC8, since `docs/` files were modified).

## Files Changed
- `docs/ai/agents_dir_disposition.md` — corrected "Approved active location" section, intro paragraph, and "Related" line.
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md` — corrected Output 1 section, Output 2 status table, Output 5 clarifying sentence, and replaced "Ask" with "Codex review response received."
- `tickets/inprogress/TCK-20260721-AGENTS-DISPOSITION-FIX.md` (this file) — Implementation Notes, Test Summary, Files Changed, Completion Summary filled in; Status set to DONE.

## Completion Summary
All 8 Acceptance Criteria are satisfied: the "Approved active location" section now names two separate provider-native delivery surfaces with citations (AC1); explicitly states no Codex delivery subtree exists yet and the existing `.agents/skills/*` content keeps its unchanged classification (AC2); cites the shared `agent-orchestration/` contract's Source Ownership decision as the eventual single semantic authority (AC3); the "Related" line no longer asserts `.claude/` as "the approved active location" (AC4); the per-path table is untouched (AC5); `codex_capability_matrix.md` is unmodified (AC6); frontmatter validation passes on both edited docs (AC7); `make knowledge-index-update` was run (AC8). The Outputs 1/4 contradiction Codex flagged as blocking is resolved, and the closure-summary doc's two non-blocking wording corrections (Output 2 table, Output 5 framing) are also applied, along with replacing the stale "Ask" section with a note that Codex's review was received and the gate is ready for re-review. Parent epic `TCK-20260721-PROVIDER-AGNOSTIC-EPIC` is intentionally left untouched, per Out of Scope.
