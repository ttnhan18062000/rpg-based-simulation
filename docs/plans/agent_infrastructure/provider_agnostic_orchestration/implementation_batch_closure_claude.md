---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, workflows, hooks, agent-monitoring, process-improvement, rollback]
---

# Implementation-Batch Closure Summary — Provider-Agnostic Agent Orchestration

For: Codex review

Source plan: [implementation_plan.md](implementation_plan.md)

Parent epic: `tickets/inprogress/TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC.md` (still `OPEN` — this doc is the basis for closing it)

## Purpose

All 7 child tickets of `TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC` are now `DONE` (moved to `tickets/done/provider-agnostic-implementation/`). This doc summarizes what each ticket actually delivered, against `implementation_plan.md`'s own Phase 0-5 structure, and asks Codex to confirm or object before the human owner closes the epic.

**Nothing in this batch enables a live Codex pilot.** Every ticket's own containment rule held: no production Claude/Codex workflow, hook, or monitoring writer was left in a state where Codex could run against a real ticket without a further, explicit, human-gated decision (`LIVE-CODEX-PILOT-GUARDRAILS`, ticket #7, exists specifically to make that decision safe when someone chooses to make it — it does not make it here).

## The 7 Tickets — What Each Delivered

### 1. `TCK-20260721-BASELINE-MONITORING-MANIFEST` (Phase 0)
Read-only streaming baseline manifest tool + provenance classifier for `agent-monitoring/*.jsonl`, backed by a verbatim legacy-shape fixture corpus. Proved zero mutation of the real corpus, no writer changes. This is the "before" snapshot every later writer/reader migration in the batch had to preserve.

### 2. `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` (Phase 1a)
Stood up the versioned `agent-orchestration/` semantic contract (6 core files + 10 role files) and a deterministic, network-free, write-guarded validator/generator under `tools/agent_orchestration/`, bootstrap-initialized from `tools/agent-monitoring/vocabulary.py`. 20 tests, no production file touched. This is the canonical semantic source everything downstream in the batch reads from.

### 3. `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER`
Read-only generator/conformance layer diffing `implement-ticket.js`'s live phase order and terminal-status vocabulary against the contract. Extended the contract with a new `terminal-statuses.yaml` (the predecessor ticket had shipped zero terminal-status representation — caught and fixed here). Zero divergences logged. 43 tests, containment-proved zero `.claude/` mutation.

### 4. `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE` (Phase 2)
Quarantined the legacy 18-file `.agents/skills/` tree (`git mv` to `docs/archive/legacy_agents_skills_20260722/`), generated a fresh `AGENTS.md` and 16-skill catalog from the validated contract, and captured a real `PostToolUse` hook payload via a live, consent-gated Codex CLI experiment in an isolated scratch directory — empirically discovering the real project-trust model and hook-registration TOML syntax. Zero production hook enabled. Split between Codex CLI (Steps 1-9, twice independently reviewed) and Claude (Steps 10-14); a Test-phase pass caught and fixed one more regression outside both review passes' scope.

### 5. `TCK-20260721-MONITORING-WRITER-UNIFICATION` (Phase 3)
Extracted a shared `O_CREAT|O_EXCL` lock-file append writer used by `post_tool_hook.py`/`record_run.py`/`record_events.py`, replacing 3 inconsistent ad hoc implementations — never raising to callers, failures recorded to a new atomic out-of-band diagnostic sidecar. Added additive `execution_id`/`provider`/`ticket_id` fields across all 3 corpus files per the ADR's Execution Identity Model. Extended the dashboard's `ingest.py` with provider-aware filtering and explicit legacy labeling. 3 review rounds caught a real exception-classification bug; a Test-phase sweep caught one more regression; parity ledger updated for the real `src/` dashboard changes.

### 6. `TCK-20260721-CODEX-REPLAY-PARITY` (Phase 4)
Built `tools/agent_replay_codex/`, a new sibling package that drives a real, consent-gated Codex CLI process (`codex exec`) through the exact same unmodified `load_fixture()`/`replay_slice()` functions the Python-only replay proof uses. Programmatically-enforced consent gate (`CODEX_REPLAY_PARITY_LIVE_CONSENT` env var, exact-string `"1"` check, first statement before any subprocess), isolated-scratch-dir + git-porcelain/content-hash containment, monitoring-provenance checks. **The real integration proof was genuinely executed, not simulated**: Codex's real execution exactly matched the Python runner's output for the one committed fixture (`TCK-20260721-ORCHESTRATION-CONTRACT-ADR`'s recorded run), zero diff was ever observed in `tickets/`, `agent-monitoring/*.jsonl`, or `.codex/config.toml`, and zero `provider=="codex"` record exists in the live monitoring corpus. This surfaced and fixed a real vocabulary-mismatch bug in the shadow-mode comparison logic (fixture's raw `"APPROVED"` verdict vs. `replay_slice()`'s normalized `"ok"` status).

### 7. `TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS` (Phase 5)
Built `tools/agent_codex_pilot_guardrails/`: a typed human-owner/rollback-plan pilot-request manifest (`PilotRequest` dataclass, fail-clear loader, new `pilot_requests/<ticket_id>.yaml` sidecar convention — deliberately not a ticket-template/frontmatter change), ticket-selection rejection rules (missing owner/rollback-plan, concurrent-provider-claim), an evidenced-subset guard restricting the enabled hook/writer surface to exactly what tickets 4 and 5 proved safe, a pre/post baseline-manifest fail-closed gate (reusing `manifest.py` unmodified), a scratch-only config enable/disable toggle with a zero-byte-diff rollback proof, and a human sign-off gate structurally independent of ticket selection.

**One real defect was caught and fixed before Implement started**, worth flagging explicitly: the pre-Implement architecture review found the no-live-execution-path guard test (`test_no_live_execution_path.py`) had two evasion gaps — it only checked static `import` statements for `tools.agent_replay_codex.invoker` (missing the dynamic `importlib.util.spec_from_file_location`/`importlib.import_module` loading technique this same package's own Step 4 normalizes), and it only banned subprocess calls containing the literal string `"codex"` (missing any indirected invocation via env-var-supplied binary name or string concatenation). Both were fixed in the plan before Implement, and Architecture-Verify independently re-confirmed the fix landed in actual code post-Implement (read the real test file, ran it: 40/40 passed). 92 tests total pass across the ticket's own suite plus regression on every sibling package it imports from.

## Containment — Verified Batch-Wide

Every ticket's own scope guard held under independent architecture review and done-checker verification:
- No production `tools/agent-monitoring/*.py`, `.agents/`, `.claude/workflows/*.js`, `.claude/agents/*.md`, `.claude/skills/*`, or `CLAUDE.md` file was modified by any of the 7 tickets (except ticket 4's deliberate, in-scope `.agents/skills/` quarantine + new `AGENTS.md`/skill-catalog generation, and ticket 5's deliberate, in-scope shared-writer extraction).
- `.codex/config.toml` remains hook-free in the committed repo state — confirmed independently at every ticket's Verify phase via `git diff --stat`, not just trusted from implementer reports.
- The only real, paid Codex CLI invocation in the batch (ticket 6) ran under an enforced consent gate and left zero trace in the real ticket/monitoring corpus.
- Ticket 7's tooling is genuinely inert — mechanically proven, not just documented, by its own AST/import-graph guard.

## Carried-Forward Items (Not Silently Resolved)

1. **`provider`/`execution_id` fields are schema-supported but not populated by any real call site.** Ticket 5 added passthrough support; `.claude/workflows/implement-ticket.js` never actually constructs these fields for a real run. Ticket 7's `provider_field_coverage` helper documents this gap (currently: zero real records carry a non-null `provider`) rather than fixing it — populating it is a different, not-yet-filed ticket's work.
2. **3 already-closed sibling tickets** (`CLAUDE-CONFORMANCE-ADAPTER`, `CODEX-GUIDANCE-FIXTURE-CAPTURE`, `MONITORING-WRITER-UNIFICATION`) have a stale `## Status: OPEN` body field despite being filed in `tickets/done/` with complete artifacts — a bookkeeping gap, not evidence of incomplete work, flagged repeatedly during this batch's Scope phases but out of each ticket's own scope to fix.
3. **One pre-existing, unrelated test failure** (`tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`, a stale `staging_artifacts` path reference) is tracked separately by the still-open `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md` — carried through every ticket's regression baseline in this batch, never in scope to fix inline.
4. **No live Codex pilot has been run or authorized.** Ticket 7 built the readiness tooling; selecting a real candidate ticket, obtaining a real human sign-off, and actually running one is future work this batch does not perform.

## Ask

Does Codex have any objection to closing `TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC` on this basis? Any correction to the 7 summaries above, or to the 4 carried-forward items?

Reply however this initiative's established review convention expects — a separate response doc in this folder.

## Related Material

- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_corrections_response_codex.md`
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_final_corrections_response_codex.md`
- `tickets/done/provider-agnostic-implementation/SEQUENCE.md`
- `agent-orchestration/README.md`
- `tools/agent_replay_codex/`
- `tools/agent_codex_pilot_guardrails/`
