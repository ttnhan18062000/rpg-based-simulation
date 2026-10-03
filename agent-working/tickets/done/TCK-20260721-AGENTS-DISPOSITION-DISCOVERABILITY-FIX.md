---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX
phase: done
date: 2026-07-21
tags: [ai, workflows, process-improvement]
---

# TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX

## Title
Correct the "Neither Codex surface exists in this repo yet" wording gap in `docs/ai/agents_dir_disposition.md` and its closure-summary doc — legacy `.agents/skills/` is currently Codex-discoverable

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`docs/ai/agents_dir_disposition.md`'s "Approved active location" section (paragraph beginning "Neither Codex surface exists in this repo yet...", currently line 41) was already corrected once by `TCK-20260721-AGENTS-DISPOSITION-FIX` to separate the two provider surfaces. Codex's follow-up review (`docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_corrections_response_codex.md`, "Required final correction — legacy skills are currently discoverable") found a further gap in that same paragraph: it conflates (a) whether a reviewed/generated Codex delivery subtree exists (correctly: it doesn't) with (b) whether the currently-present `.agents/skills/` content is actually discoverable by a real Codex session today (it is). Verified directly: `.agents/skills/` contains 18 `SKILL.md` files right now (`find .agents/skills -name SKILL.md | wc -l` → 18), and per the Codex manual behavior already cited in `docs/ai/codex_capability_matrix.md` (§5), Codex scans `.agents/skills` from cwd up to the repo root — so a live Codex session pointed at this repo would discover and could load this stale, unreviewed content today. The doc's current wording implies zero live risk when there is an unaddressed containment gap. The same "neither...exists yet" framing was inherited into `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md`'s Output 1 summary (currently line 32: "Neither `AGENTS.md` nor a reviewed/generated Codex-delivery `.agents/skills/` subtree exists in this repo yet...") and needs the same correction.

## Scope
- Revise the "Approved active location" section of `docs/ai/agents_dir_disposition.md` — specifically the paragraph currently starting "Neither Codex surface exists in this repo yet..." (line 41) — to state all 4 points from Codex's exact specification:
  1. Root `AGENTS.md` and a reviewed/generated Codex skill catalog are absent (already correct; keep it).
  2. The legacy `.agents/skills/` tree is **currently auto-discoverable by Codex** (a real Codex session scanning this repo would find its 18 `SKILL.md` files today) but is unapproved/stale and must not be treated as the provider-agnostic workflow source.
  3. No Codex project workflow/pilot is authorized while that legacy tree remains discoverable without an explicit containment decision.
  4. The first Codex-delivery implementation ticket must quarantine/archive the legacy tree or atomically replace it with the contract-generated catalog before enabling root `AGENTS.md` or project Codex configuration.
- Propagate the same 4-point correction into `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md`'s Output 1 summary (line 32, the same "neither...exists yet" framing inherited from the prior fix), keeping the rest of that Output 1 bullet block (carve-outs, `WorkflowRegistry` determination, "Gap carried forward" line) internally consistent with the revised wording.
- Preserve the existing correct content in both docs that this fix does not touch: the two-provider-surface split, the per-path classification table, the eventual-shared-contract statement, and the "must not be read as un-archiving" caveat — all of that remains accurate and unchanged.

## Out of Scope
- Does not delete, quarantine, or archive the legacy `.agents/skills/` tree itself — per Codex's own explicit statement, this is a documentation and sequencing correction only. Actually containing the tree is future implementation-epic work, gated behind an explicit containment decision that this ticket *names as a precondition*, not executed here.
- Does not create a root `AGENTS.md` file or any `.codex/` project configuration.
- Does not touch the per-path classification table (lines 15-32 of `docs/ai/agents_dir_disposition.md`) — no individual `.agents/skills/*` or `.agents/rules/*` entry's classification changes.
- Does not touch `docs/ai/codex_capability_matrix.md` — its §5 citation of the Codex `.agents/skills` scan-from-cwd-to-root behavior is the evidentiary source for this fix and remains accurate as-is; no change needed there.
- Does not attempt to close the parent epic (`tickets/inprogress/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md`) — per Codex's response, closure follows only after this correction lands and is reviewed; that is a separate follow-up ticket.
- Does not modify any other section of either target doc (WorkflowRegistry determination, Test-pairing note, "What this doc does not do", the closure doc's Outputs 2-5 sections) beyond the Output 1 paragraph named above.

## Acceptance Criteria
1. `docs/ai/agents_dir_disposition.md`'s "Approved active location" section states, in place of the current "Neither Codex surface exists in this repo yet" paragraph, all 4 points verbatim in substance: (a) root `AGENTS.md`/reviewed catalog absent, (b) `.agents/skills/` is currently auto-discoverable by Codex today despite being unapproved/stale, (c) no Codex project workflow/pilot is authorized while it remains discoverable without an explicit containment decision, (d) the first Codex-delivery implementation ticket must quarantine/archive or atomically replace the legacy tree before enabling root `AGENTS.md` or project Codex configuration.
2. The revised paragraph does not claim "zero" Codex-side risk or discoverability — it explicitly names the live discoverability of the 18 `SKILL.md` files under `.agents/skills/` as a current, unaddressed condition, not merely a future non-issue.
3. `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md`'s Output 1 section (line 32 and immediate context) reflects the same 4-point correction, consistent with the revised disposition doc.
4. The per-path classification table in `docs/ai/agents_dir_disposition.md` (lines 15-32) is byte-identical to its pre-fix state.
5. `docs/ai/codex_capability_matrix.md` is unmodified — diff confirms zero changes.
6. No file under `.agents/` is deleted, moved, or modified by this ticket — `git status`/`git diff` shows zero changes under `.agents/`.
7. `python3 tools/validate_frontmatter.py docs/ai/agents_dir_disposition.md` and the equivalent check on the closure-summary doc both pass.
8. `make knowledge-index-update` is run after the doc edits (both files are under `docs/`).

## Related Tickets
- `tickets/done/TCK-20260721-AGENTS-DIR-DISPOSITION.md` — original ticket that produced `docs/ai/agents_dir_disposition.md`; context/predecessor, not a conflict.
- `tickets/done/TCK-20260721-AGENTS-DISPOSITION-FIX.md` — the prior correction this ticket follows up on (fixed the "one shared location" claim; this ticket fixes the separate "neither exists yet" discoverability gap in the same paragraph). Context/predecessor, not a conflict.
- `tickets/inprogress/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md` — parent discovery epic, still `OPEN`, blocked on this exact correction per Codex's gate-closure review response; not modified or closed by this ticket.

## Related Docs
- `docs/ai/agents_dir_disposition.md` — primary doc being corrected (target paragraph currently at line 41).
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md` — secondary doc being corrected (Output 1 section, currently line 32).
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_corrections_response_codex.md` — "Required final correction — legacy skills are currently discoverable" section; the exact 4-point specification this ticket implements.
- `docs/ai/codex_capability_matrix.md` — §5, VERIFIED source of the Codex `.agents/skills` cwd-to-repo-root scan behavior cited as evidence; not modified.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/investigation.md` — prior investigation behind the doc now being corrected; not modified.

## Related Code Areas
- None — documentation-only correction. No `src/` or `tests/` files are in scope. `.agents/skills/` itself is read-only evidence (file count verification), not modified.

## Assumptions / Open Questions
- Assumes the 18-file count for `.agents/skills/*/SKILL.md` (verified via `find .agents/skills -name SKILL.md | wc -l` during scoping) is stable enough to cite as a point-in-time fact in the doc; if a future ticket changes the count before this lands, the exact number should be re-verified at implementation time rather than assumed unchanged.
- Assumes `layer: ai` and tags `[ai, workflows, process-improvement]` remain correct, matching both predecessor tickets and the docs being edited — confirmed registered via `tools/layer_registry.py list` and `tools/tag_registry.py list`.
- Assumes "explicit containment decision" (point 3 of Codex's spec) does not need to be made or named as a specific mechanism by this ticket — only referenced as a precondition that gates future Codex pilot/workflow authorization. If Codex's review expects this ticket to also specify *what* the containment decision looks like (rather than just stating one is required), that would expand this ticket's scope beyond a wording fix.
- Assumes closing the parent epic remains out of scope and is a separate follow-up, consistent with the prior fix ticket's same assumption and Codex's response treating this correction as a precondition to approval, not the approval act itself.

## Implementation Notes
Verified the 18-file count directly (`find .agents/skills -name SKILL.md | wc -l` → 18) before editing.

Rewrote the target paragraph in `docs/ai/agents_dir_disposition.md`'s "Approved active location" section (previously starting "Neither Codex surface exists in this repo yet") to state all 4 points from Codex's spec verbatim in substance: (1) root `AGENTS.md`/reviewed catalog absent (kept, was already correct), (2) the legacy `.agents/skills/` tree is currently auto-discoverable by Codex today (18 `SKILL.md` files, cwd-to-repo-root scan per `docs/ai/codex_capability_matrix.md` §5) despite being unapproved/stale, (3) no Codex project workflow/pilot is authorized while it remains discoverable without an explicit containment decision, (4) the first Codex-delivery implementation ticket must quarantine/archive or atomically replace the legacy tree before enabling root `AGENTS.md` or project Codex configuration. Kept the existing "must not be read as un-archiving" caveat and appended an explicit closing sentence stating this is a documentation/sequencing correction, not an instruction to delete the tree during discovery — matching Codex's own final sentence in the corrections-response doc.

Propagated the same 4-point correction into `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md`'s Output 1 bullet (previously line 32, the "Neither `AGENTS.md` nor a reviewed/generated Codex-delivery `.agents/skills/` subtree exists..." sentence), inserting the same 4 points inline while preserving the rest of the bullet (two-provider-surface split, shared-contract sentence) and leaving the "Gap carried forward" line and the rest of the doc (Outputs 2-5, per-path table, WorkflowRegistry determination, Test-pairing note, "What this doc does not do") untouched.

No `.agents/` file was touched (`git status --short .agents/` empty). `docs/ai/codex_capability_matrix.md` was not modified (only read for citation). The per-path classification table (lines 15-32 of the disposition doc) is unchanged — confirmed by re-reading it post-edit.

Both edited docs are untracked (`??`) in this working tree (part of the same uncommitted discovery batch), so `git diff` against HEAD shows nothing for them; verified the actual edits by re-reading file content and grepping the classification table instead.

Ran `python3 tools/validate_frontmatter.py` on each file individually (the script only accepts one `path` positional argument, not multiple) — both passed. Ran `make knowledge-index-update` after the doc edits (6 files changed/re-embedded, including both edited docs).

Deviation from ticket's implicit assumption: AC 7 as literally worded ("both pass") was executed as two separate single-file invocations rather than one combined command, since the script's CLI does not accept multiple paths — behavior and outcome are identical (OK: 1 file(s) checked — no violations, for each).

Deviation discovered during Test phase (post-Implement): the scoped pytest run initially returned 1 failure — `tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`, caused by `docs/REGISTRY.yaml` being out of sync with 2 unrelated docs (`idea_provider_agnostic_agent_orchestration_discovery_gate_closure_corrections_claude.md` and its Codex response) that predate this ticket and were never part of its own edits. Since Finalize would regenerate `docs/REGISTRY.yaml` unconditionally anyway (CLAUDE.md's standing rule), the registry was regenerated immediately via `python3 tools/generate_registry.py --output docs/REGISTRY.yaml` rather than leaving a known-to-self-heal failure blocking the Test gate. The full scoped suite was re-run afterward and passed 133/133. `docs/REGISTRY.yaml` is accordingly added to this ticket's own Files Changed below, even though its content changes (adding the 2 unrelated docs' entries) are not semantically part of this ticket's scope — the regeneration action itself is.

## Test Summary
Documentation-only change; no `src/`/`tests/` code touched. Verification performed:
- `find .agents/skills -name SKILL.md | wc -l` → 18 (fact-check for the cited count).
- `python3 tools/validate_frontmatter.py docs/ai/agents_dir_disposition.md` → OK, no violations.
- `python3 tools/validate_frontmatter.py docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md` → OK, no violations.
- `git status --short .agents/ docs/ai/codex_capability_matrix.md` → confirms zero changes under `.agents/` and `codex_capability_matrix.md` untouched.
- Manual re-read of both edited docs confirms the per-path classification table, WorkflowRegistry determination, Test-pairing note, and "What this doc does not do" sections are byte-identical to their pre-edit state (not touched by any Edit call).
- Scoped pytest run: `.venv/bin/python3 -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py -v`. First run: 132 passed, 1 failed (`test_check_flag_detects_no_drift_against_real_registry`, pre-existing `docs/REGISTRY.yaml` drift unrelated to this ticket's edits — see Implementation Notes). After regenerating `docs/REGISTRY.yaml`, re-run: **133 passed, 0 failed.**

## Files Changed
- `docs/ai/agents_dir_disposition.md` — rewrote the "Neither Codex surface exists in this repo yet" paragraph in "Approved active location".
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md` — rewrote the corresponding sentence in Output 1's bullet.
- `tickets/inprogress/TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX.md` — this ticket, status/notes update.
- `docs/REGISTRY.yaml` — regenerated mid-Test-phase to resolve a pre-existing drift failure (2 unrelated docs from earlier in this session were missing from the registry); not a content change caused by this ticket's own doc edits, but the regeneration action itself is this ticket's own change.

## Completion Summary
All 8 Acceptance Criteria are satisfied: the disposition doc's "Approved active location" paragraph now states all 4 points — root `AGENTS.md`/reviewed catalog absent, `.agents/skills/` currently auto-discoverable by Codex today, no Codex project workflow/pilot authorized while it stays discoverable without a containment decision, and the first Codex-delivery ticket must quarantine/archive or atomically replace it before enabling root `AGENTS.md`/project Codex config (AC1); the paragraph explicitly names the live discoverability of the 18 `SKILL.md` files as a current, unaddressed condition rather than a future non-issue (AC2); the closure-summary doc's Output 1 bullet carries the same 4-point correction (AC3); the per-path classification table is byte-identical to its pre-fix state (AC4); `codex_capability_matrix.md` is unmodified (AC5); `git status --short .agents/` shows zero changes (AC6); `validate_frontmatter.py` passes on both edited docs, run individually since the script takes one path at a time (AC7); `make knowledge-index-update` was run after the doc edits (AC8). Nothing under `.agents/` was touched, and this is a pure documentation/sequencing correction with no runtime behavior change.
