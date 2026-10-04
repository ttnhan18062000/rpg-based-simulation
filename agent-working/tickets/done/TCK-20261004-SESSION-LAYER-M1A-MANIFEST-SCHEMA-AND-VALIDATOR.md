---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1A-MANIFEST-SCHEMA-AND-VALIDATOR
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M1A-MANIFEST-SCHEMA-AND-VALIDATOR

## Title
Session-layer M1a: role manifest, authority file and validator (nine seats)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create `registries/session_roles.yaml` and `registries/session_authority.yaml` with the nine seats of plan section 3 (two `unstaffed`), a typed loader and a validator, so the session layer has one validated source of truth that M2 onward consume.

Child of `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (milestone M1). Hold rule met: M-1 merged (#289) and M0 recorded ADJUST (#307).

## Scope
- `registries/session_roles.yaml`: roles in the five-part shape of plan section 4 (identity, responsibility, capability, placement, handover) plus a `worktrees:` resource section with exactly one `writer` per worktree. Nine seats: `{rpg,agent-working,testing}-{designer,planner,implementer}`. `legacy_session_name` records today's holder. `seat_status: staffed|unstaffed` (`agent-working-planner` and `testing-designer` unstaffed, named holder recorded in the entry, not in runtime state).
- `registries/session_authority.yaml`: per-role `needs_user` and dated `grants`, governing-file class.
- Typed loader in `tools/sessions/` (read-only; decision logic reads state, never mutates it).
- Validator (CLI plus importable): every `owns` glob resolves to files; no two roles own a path without a stated split; every role has a handover path and a worktree; every `routes` target is a real role; `session_name` unique; every worktree declares one `writer` and that role has the `implementer` function. Reports, never blocks, per-role complexity (override count, unique routes, authority exceptions).
- Staleness: an entry citing a deleted path, ticket or role is reported (reuse the planning-doc staleness sweep).
- Wire the validator into the existing registry validation entry point / CI the way `layer_registry.py` and `tag_registry.py` are.

## Out of Scope
- Launcher, binding record, SessionStart hook (M2). Guardrail hook and permission rules (M5). Generated agent files (M1c). Prose templates (M1b). `settings.json` changes of any kind.

## Acceptance Criteria
1. Both registry files exist with the nine seats; the validator passes on them and fails, with a named reason, on a fixture for each rule above (glob matches nothing, overlapping ownership, missing handover, unknown route target, duplicate session name, worktree with no or two writers, writer that is not an implementer).
2. Complexity report is printed and does not change the exit code.
3. `session_authority.yaml` is covered by the governing-file rule: a test or validator check proves a hook/CI-visible marker, and the ticket records that the owner confirmed the literal diff (plan section 10).
4. Loader returns typed records; no raw dict leaks past the module boundary; a test proves it does not write.
5. M0 findings applied: `seat` resolution does not depend on `agent_type` alone (M0o); nothing in the schema stores liveness (derivable, M0q).
6. Registry-validation wiring runs in CI; scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (parent), `TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE` (done)
- M1b, M1c and M1d depend on this ticket.

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 3, 4, 5, 10, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0 record; ADJUST 5, 6.1, 10)
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`
- `agent-working/stored_artifacts/TCK-20261004-SESSION-LAYER-M1A-MANIFEST-SCHEMA-AND-VALIDATOR/` (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- `registries/` (new files), `tools/sessions/` (new), `tests/tools/` (new tests), CI registry validation entry.

## Assumptions / Open Questions
- Open decision 3 (may a seat start unstaffed with a named holder): drafted as allowed; the owner may veto, which changes only `seat_status` rules.
- Owner must confirm the literal diff of `session_authority.yaml` before merge.
- `owns` globs for each role are copied from plan section 4 and the current handover notes; the validator will flag any that no longer resolve, which is expected to surface real staleness.

## Implementation Notes
Nine seats (two unstaffed with a named interim holder), a loader returning frozen dataclasses only, and a validator with nine rule ids plus a report-only complexity table. Wiring: there is no central registry-validation entry point in this repo (layer/tag registries are enforced through validate_frontmatter and tests), so the validator is wired the same way: a CI test validates the real files. The staleness sweep `tools/gate_checks/planning_doc_staleness_check.py` was not reused: it compares planning docs to done tickets, a different subject; the manifest instead reports a cited ticket id that no ticket file carries. Governing-file marker: `governing_file: true` plus a GOVERNING FILE header, checked by the validator and a test. The owner confirmed the literal content of `registries/session_authority.yaml` on 2026-10-04 (AskUserQuestion in the agent-working-implementer terminal), including the dated push/open_pr grant for agent-working-implementer. M0: no liveness field and no `agent_type` field exist in the schema (tested). Not exercised: a worktree with two writers is unrepresentable (the field holds one id; a list is rejected by test).

## Test Summary
tests/tools/test_session_roster.py (24 tests): Registry files, typed loader and validator; each rule has a fixture that trips it plus a positive control; the real registry validates (this is the CI wiring: tests/tools is a CI lane). Also run: the 11 other test files that scan `.claude/agents` (72 passed), and tests/docs.

## Files Changed
- `registries/session_roles.yaml`
- `registries/session_authority.yaml`
- `tools/sessions/__init__.py`
- `tools/sessions/roster.py`
- `tools/sessions/validate.py`
- `tests/tools/test_session_roster.py`

## Completion Summary
Done. Registry files, typed loader and validator; each rule has a fixture that trips it plus a positive control; the real registry validates (this is the CI wiring: tests/tools is a CI lane).