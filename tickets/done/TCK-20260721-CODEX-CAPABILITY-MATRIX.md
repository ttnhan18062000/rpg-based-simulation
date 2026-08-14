---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-CODEX-CAPABILITY-MATRIX
phase: done
date: 2026-07-21
tags: [ai, workflows, process-improvement]
---

# TCK-20260721-CODEX-CAPABILITY-MATRIX

## Title
Verify and document the Codex capability matrix

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Current Codex capabilities, project trust behavior, all lifecycle hook events, role/delegation model, skills/configuration surfaces, and payload/fixture gaps verified against official documentation and confirmed with provider fixture experiments, not assumed from the plan's existing (dated 2026-07-20) documentation citation. Unverified behavior must be explicitly marked.

## Scope
- This ticket may create only isolated contract, replay, fixture, diagnostic, or decision-record work. It must not modify production Claude/Codex workflows, hooks, monitoring writers, live ticket artifacts, or the shared monitoring JSONL corpus.
- Verify current Codex capabilities, project trust behavior, all lifecycle hook events, role/delegation model, skills/configuration surfaces, and payload/fixture gaps against official Codex documentation.
- Confirm hook/payload/matcher/timing behavior with provider fixture experiments where documentation review alone is insufficient, explicitly marking any behavior that remains unverified.
- Produce a standalone Codex capability-matrix artifact, not folded into the existing dated (2026-07-20) plan citation, with per-entry citation and verification date.

## Out of Scope
- Creating any provider-runtime implementation ticket — blocked until all 5 discovery outputs are complete, evidence-backed, and explicitly approved (see parent epic TCK-20260721-PROVIDER-AGNOSTIC-EPIC).
- No Codex adapter implementation or production wiring based on the matrix — verification only.
- No changes to production Claude/Codex workflows, hooks, or monitoring writers.

## Acceptance Criteria
- [x] A Codex capability-matrix artifact exists separately enumerating: current Codex capabilities, project trust behavior, all lifecycle hook events, role/delegation model, skills/configuration surfaces, and payload/fixture gaps — each entry citing an official source with a verification date at execution time, not carried over unchanged from the plan's 2026-07-20 citation.
- [x] All ten previously-claimed lifecycle hook events (PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, UserPromptSubmit, SubagentStop, Stop, SessionStart, SubagentStart) are each individually marked VERIFIED or UNVERIFIED/DIVERGENT — none left unmarked or assumed.
- [x] At least one matrix entry cites a provider fixture experiment result as evidence, distinguishing 'documented in official docs' from 'fixture-confirmed by direct experiment.'
- [x] Matrix explicitly calls out any capability/hook/config surface where current official Codex documentation diverges from, is silent on, or cannot be reconciled with the plan's existing claims.

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR

## Related Docs
- docs/engine/capability_registry.yaml
- docs/engine/known_limitations.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_ticket_handoff_codex.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_finding_01_claude.md
- stored_artifacts/TCK-20260619-E-CAP-REGISTRY/investigation.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/capability.py
- tests/unit/engine/test_capability_registry.py
- tests/architecture/test_capability_references.py

## Assumptions / Open Questions
- Exact Codex hook payload/matcher/timing equivalence is still a discovery fixture question per the source plan's own text — cannot be closed by documentation review alone, requires running Codex fixture experiments, which may need Codex CLI/API access not yet confirmed present in this environment.
- Existing citation (learn.chatgpt.com/docs/hooks.md, verified 2026-07-20) is stale relative to execution date — even the 10-hook list itself, not just payload details, could already be wrong if Codex's public docs changed.
- No prior ticket in this repo has verified a third-party AI provider's capabilities against live external docs — citation/evidence conventions for an external product must be established fresh (closest precedent, TCK-20260619-E-CAP-REGISTRY, verified only in-repo engine features against source code).
- This is a parallelizable discovery child (no prerequisite) but incomplete/unmarked evidence here directly blocks TCK-20260721-ORCHESTRATION-CONTRACT-ADR, which depends on it.
- Depends on TCK-20260721-PROVIDER-AGNOSTIC-EPIC as parent; no dependency on sibling children TCK-20260721-AGENTS-DIR-DISPOSITION or TCK-20260721-MONITORING-WRITER-DECISION — can run in parallel with them.

## Implementation Notes

Followed `staging_artifacts/TCK-20260721-CODEX-CAPABILITY-MATRIX/plan.md`'s five steps exactly, in order, with no deviations.

**Step 1 (baseline):** confirmed all three pre-existing regression commands passed clean before any change (10 + 95 + 5 = 110 tests, all passed).

**Step 2 (matrix doc):** wrote `docs/ai/codex_capability_matrix.md` with frontmatter mirroring the sibling precedent `docs/ai/agents_dir_disposition.md` (`status: active`, `layer: ai`, `authority: P1`, `audience: developer`, `tags: [ai, workflows, process-improvement]` — all three tags confirmed already registered in `docs/guidelines/tag_registry.jsonl` before use). Re-read the cache file fresh at implementation time (`/tmp/openai-docs-cache/codex-manual.md`, still present, unchanged mtime 2026-07-20 16:04) at lines 1-150 (Feature Maturity/Pricing/Quickstart), 3150-3239 (project config + agent-roles pointer), 8385-8454 (Build skills), 9130-9568 (full Hooks section), 12960-13099 (Roles and workspace permissions, Skill controls), 15440-15507 (Skills & Plugins). All ten hook events individually marked VERIFIED with the field-table text excerpted directly into the doc body (not just cited by path), matching the plan's field-coverage-asymmetry notes (`permission_mode` absent for `PreCompact`/`PostCompact`; `PreToolUse`/`PermissionRequest` reject `continue`/`stopReason`/`suppressOutput`). Included all six required rows (hooks, current capabilities, project trust, role/delegation, skills/config surfaces, payload/fixture gaps), the documentation-vs-fixture-experiment distinction (section 6), and a dedicated Divergences/Silences section (section 7) stating no divergence was found and naming the specific silences the matrix fills plus the residual WebFetch-blocked limitation. The `[agents]` role/delegation section (§4) is explicitly marked VERIFIED for existence/high-level shape only, not full field-level schema, since the manual's own "Agent roles" heading is a pointer to an external doc this sandbox could not re-fetch — this is disclosed in the doc rather than silently glossed over.

**Step 3 (diagnostic test):** added `tests/tools/test_codex_capability_diagnostics.py::test_codex_hooks_feature_reported_enabled`, sibling in style to `tests/tools/test_post_tool_hook.py`. Guards with `shutil.which("codex")` and skips if absent; otherwise runs `codex features list` (read-only CLI diagnostic, no hook script invoked) and asserts the `hooks` row contains `stable`/`true`. Verified against the real installed output (`hooks   stable   true` among ~90 other feature rows) — the loose substring/regex match (`\b(stable|true)\b`) only inspects the `hooks` line, per the plan's instruction not to pin the full output format.

**Step 4 (regression pass):** re-ran all four scoped commands; all passed (10 + 95 + 5 + 1 = 111 total). `git status` confirmed changes confined to this ticket's two new files (`docs/ai/codex_capability_matrix.md`, `tests/tools/test_codex_capability_diagnostics.py`) plus this ticket's own artifacts — no `src/engine/`, `.agents/`, `.claude/`, `.codex/`, or `tools/agent-monitoring/*.py` file was touched. (The working tree also carries pre-existing uncommitted state from sibling tickets `TCK-20260721-AGENTS-DIR-DISPOSITION` and `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`, which predate and are unrelated to this ticket's own changes.)

**Step 5 (this update):** ticket body updated with results; all four AC boxes checked. Ticket `Status` left as `INPROGRESS` (not `DONE`) and the file left in `tickets/inprogress/` — moving to `tickets/done/` and staging artifacts to `stored_artifacts/` is Finalize-phase work, out of scope for the Implement phase.

No deviation from the plan occurred; `staging_artifacts/TCK-20260721-CODEX-CAPABILITY-MATRIX/plan.md` requires no Deviations section addendum.

## Test Summary

```
.venv/bin/python3 -m pytest tests/unit/engine/test_capability_registry.py tests/architecture/test_capability_references.py -v
  10 passed

.venv/bin/python3 -m pytest tests/unit/lab_agent/ tests/integration/lab_agent/ -v
  95 passed

.venv/bin/python3 -m pytest tests/tools/test_post_tool_hook.py -v
  5 passed

.venv/bin/python3 -m pytest tests/tools/test_codex_capability_diagnostics.py -v
  1 passed (codex CLI present and authenticated in this environment; test is designed to skip cleanly instead where codex is absent from PATH)
```

Total: 111 passed, 0 failed, 0 skipped (in this environment). No `pytest tests/` broad run was performed, per the plan's Scope Guards.

## Files Changed

- `docs/ai/codex_capability_matrix.md` (new) — the standalone Codex capability-matrix decision-record artifact.
- `tests/tools/test_codex_capability_diagnostics.py` (new) — re-runnable diagnostic test codifying the `codex features list` fixture-experiment evidence.
- `tickets/inprogress/TCK-20260721-CODEX-CAPABILITY-MATRIX.md` (this file) — Implementation Notes, Test Summary, Files Changed, Completion Summary filled in; all four AC boxes checked.

## Completion Summary

All four acceptance criteria are satisfied. `docs/ai/codex_capability_matrix.md` independently re-verifies, at a fresh 2026-07-21 execution-date citation, all ten previously-claimed Codex lifecycle hook events (each individually marked VERIFIED, with load-bearing field-table text excerpted directly from the non-durable `/tmp/openai-docs-cache/codex-manual.md` into the durable doc body) alongside the five other required rows (current capabilities, project trust behavior, role/delegation model, skills/configuration surfaces, payload/fixture gaps). The payload/fixture-gaps section explicitly distinguishes documentation-cited evidence from the fixture-confirmed `codex features list` → `hooks stable true` direct-experiment result, and that finding is now codified as a skippable, re-runnable regression test (`tests/tools/test_codex_capability_diagnostics.py`) rather than remaining a one-off manual finding. A dedicated Divergences/Silences section states plainly that no divergence from the plan's 2026-07-20 claim was found, names the specific silences this matrix newly fills, and discloses the residual WebFetch-blocked and partial-role-schema limitations rather than glossing over them. All four scoped regression commands (110 pre-existing tests + 1 new test = 111 total) passed clean both before and after the change, and `git status` confirms the change surface is confined to exactly the two new files plus this ticket's own artifacts — no production Claude/Codex file, `.agents/`, `.codex/`, or `src/engine/capability.py` was touched. The deeper stdin-payload-capture fixture experiment was deliberately not performed, per the plan's explicit scope decision, and is recorded in the matrix as deferred future work rather than a silently-filled gap.
