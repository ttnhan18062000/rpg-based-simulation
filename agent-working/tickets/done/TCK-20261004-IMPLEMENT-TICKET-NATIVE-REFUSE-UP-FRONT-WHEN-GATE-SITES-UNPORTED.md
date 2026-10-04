---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-IMPLEMENT-TICKET-NATIVE-REFUSE-UP-FRONT-WHEN-GATE-SITES-UNPORTED
phase: done
date: 2026-10-04
tags: [ai, process-improvement]
---

# TCK-20261004-IMPLEMENT-TICKET-NATIVE-REFUSE-UP-FRONT-WHEN-GATE-SITES-UNPORTED

## Title
A native `implement-ticket` run must refuse at start, not crash after Scope, while legacy `bash()` gate sites are unported

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Reported by `test-architecture-reviewer`, relayed from `rpg-implementer` (2026-10-04): native run `wf_ca51b3b4-356` for `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` (standard tier) died with `ReferenceError: bash is not defined` at the first legacy gate site (`tagCheckOutput`, `bash(` near `.claude/workflows/implement-ticket.js` line 594 on `origin/main`) after Scope. Six agents ran, about 277k tokens, none reached Implement.

Verified from `origin/main` (`bec0b2b85`): `legacyBash = typeof bash === 'function' ? bash : null` (line 44) and the only native precondition (lines 107-115) checks `args.start_ts` and `args.execution_id_suffix`. Nothing refuses when `legacyBash` is null and the run will reach an unported `bash(` site. Bare `bash(` calls remain at lines 594, 846, 1083, 1401, 1465, 1519, 1610, 1611, 1956 and others. Epic tier returns before the gates (line 659), so it is unaffected. This is the known deferral (`implement-ticket-native-port` SEQUENCE items 4-5, deferred by the owner on 2026-10-01); the defect is the failure mode, not the gap.

## Scope
- After the existing native args check, when `!legacyBash`: if the run's tier is known (`args.tier`) and is not `epic`, return a terminal status (for example `NATIVE_GATE_SITES_UNPORTED`) before any agent is dispatched, with a message naming the deferral and the legacy runtime as the path. If the tier is not given in args, refuse the same way: the tier is only known after Scope, which is exactly what costs tokens.
- Keep the legacy runtime unchanged. Remove or narrow the refusal as each gate site is ported (a single constant listing the unported sites, so the port tickets delete their entry; refusal lifts when the list is empty).
- Register the new status in the terminal-status contract and the sampler classification (the `WORKFLOW_ERROR` work added six more; follow that shape), and record a run entry for the refusal like other terminal statuses, best-effort.

## Out of Scope
- Porting any gate site, running the `Workflow` tool (needs the owner's opt-in), changing the native input-sites check.

## Acceptance Criteria
1. A native run (simulated by `legacyBash = null`) with `tier: standard` or `hotfix`, or with no tier, returns the new status with zero agent dispatches (positive control: the same input today reaches Scope; assert on a call counter).
2. `tier: epic` natively proceeds as before; the legacy runtime is unaffected (existing tests green).
3. The unported-site list is a single constant; a test asserts it equals the set of bare `bash(` call sites outside `shOmit`/`sh` helpers, so a newly added bare `bash(` fails the test until listed (and a ported site must be removed).
4. The status appears in the terminal-status contract and sampler classification; the refusal run entry is written best-effort and a write failure never changes the status.
5. Scoped tests (`tests/tools` workflow/implement-ticket tests) green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT` (epic; deferred children NATIVE-PORT-ATTESTED-GATE-SITES and NATIVE-PORT-SMALL-TICKET-NATIVE-RUN), `TCK-20260930-NATIVE-PORT-INPUT-SITES`, the `WORKFLOW_ERROR` ticket (#300)

## Related Docs
- `.claude/workflows/implement-ticket.js` header comments (lines 33-44)

## Related Stored Artifacts
- none

## Related Code Areas
- `.claude/workflows/implement-ticket.js`, the terminal-status and sampler tests

## Assumptions / Open Questions
- The line numbers are from `origin/main` `bec0b2b85` and shift as edits land; match on the code, not the number.
- If the owner wants native runs to be attempted anyway (for the data), the refusal could be an opt-in override arg; drafted without one.
- A `.claude/workflows/` edit is not a governing-file edit under CLAUDE.md, but confirm with the owner if the implementer treats it as one.

## Implementation Notes
Draft by `agent-working-design`, 2026-10-04, from a relayed report; the code facts above were read on `origin/main`. Implemented 2026-10-04 (hand-orchestrated). `NATIVE_UNPORTED_GATE_SITES` (9 variable names) sits beside `sh`/`shOmit` in `implement-ticket.js`; after the native args check a non-epic or unspecified-tier native run returns `NATIVE_GATE_SITES_UNPORTED` before Scope. Epic tier and the legacy runtime are untouched.

**Deviation from the draft, to review:** AC1 says "zero agent dispatches" and the Scope says the refusal also records a run entry. Natively `sh()` dispatches an agent per command, so the two cannot both hold literally. Implemented: zero *pipeline* agents (asserted by label), plus two best-effort recorder dispatches (one event, one run row, `agent_count` 0), the same pre-Scope fallback shape `recordWorkflowError` and `SCOPE_AGENT_FAILED` already use, because CLAUDE.md requires every run to leave a run entry. If the owner prefers no recording (like `INVALID_ARGS`), delete the `try` block and the recorder tests.

Contract registration: the new raw `record_run.py --data` line is picked up by the extractor as a `bypass` status, so `terminal-statuses.yaml` and the regenerated `rendered/claude-adapter.yaml` list it (18 statuses), the sampler's gate-failure set includes it, and `docs/agent-monitoring/schema.md` documents it. Pinned counts (17 -> 18) updated in four tests.

## Test Summary
`tests/tools/test_implement_ticket_native_refusal.py` (9): refusal for standard, hotfix and no tier with zero pipeline agents; positive control (list emptied -> Scope reached); epic native proceeds; legacy unaffected; run row and event written; recorder failure never changes the status; list equals the real bare call sites. Contract, adapter, sampler and workflow-shape suites: 168 + 168 pass.

## Files Changed
- `.claude/workflows/implement-ticket.js`, `tools/agent_replay/sampler.py`
- `agent-working/agent-orchestration/terminal-statuses.yaml`, `agent-working/agent-orchestration/rendered/claude-adapter.yaml`, `docs/agent-monitoring/schema.md`
- `tests/tools/test_implement_ticket_native_refusal.py` (new); pinned counts in `tests/agent_orchestration/test_contract_structure.py`, `tests/agent_orchestration_claude_adapter/test_generator_containment.py`, `test_terminal_status_schema.py`, `test_terminal_status_extractor.py`

## Completion Summary
Done; closed in PR #316. The refusal lifts automatically when the port tickets empty the list.
