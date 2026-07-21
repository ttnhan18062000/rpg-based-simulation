---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# Discovery-Epic Gate-Closure Summary — Provider-Agnostic Agent Orchestration

For: Codex review

Source plan: [idea_provider_agnostic_agent_orchestration.md](idea_provider_agnostic_agent_orchestration.md), "Approval model and exit gate" (lines 124-145)

Parent epic: `tickets/inprogress/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md` (still `OPEN` — this doc is the basis for closing it)

## Purpose

All 5 child tickets of `TCK-20260721-PROVIDER-AGNOSTIC-EPIC` are now `DONE` (moved to `tickets/done/provider-agnostic-discovery/`). Per the source plan's exit gate: *"Only after those five outputs are reviewed and approved may a follow-on implementation epic be created."* This doc summarizes what each output actually decided, against the plan's own exit-gate wording, and asks Codex to confirm or object before the human owner signs off and the epic ticket is closed.

**Nothing here is a request to start implementation.** No provider-runtime ticket exists or is proposed by this doc.

## The 5 Required Outputs — Status

### 1. `.agents/` disposition report and approved active-location map

**Ticket:** `TCK-20260721-AGENTS-DIR-DISPOSITION` → **Doc:** `docs/ai/agents_dir_disposition.md`

**Corrected following Codex's gate-closure review** (`idea_provider_agnostic_agent_orchestration_discovery_gate_closure_response_codex.md`, "Blocking correction — Output 1's Codex location"); the summary below reflects the corrected framing landed by `TCK-20260721-AGENTS-DISPOSITION-FIX`, not the doc's original (wrong) text.

- Every `.agents/` path classified: `archive-retire` or `retain-and-migrate` (no `replace` cases found), at subdirectory granularity.
- **Two provider-native delivery surfaces, not one shared location:** Claude's surface is `.claude/` (`CLAUDE.md` + `.claude/workflows/*.js` + `.claude/skills/` + `.claude/agents/*.md`) — already active. Codex's surface is a root `AGENTS.md` (durable instructions) + `.agents/skills/` (repository skills), per the official Codex manual, verified in `docs/ai/codex_capability_matrix.md`. Root `AGENTS.md` and a reviewed/generated Codex skill catalog are absent from this repo today. But the legacy `.agents/skills/` tree is **currently auto-discoverable by Codex** — it holds 18 `SKILL.md` files today, and per the manual's cwd-to-repo-root scan behavior a live Codex session would find and could load them — while remaining unapproved/stale and not the provider-agnostic workflow source; it stays classified per the unchanged per-path table (`archive-retire` or `retain-and-migrate`), not re-enabled or "un-archived" as a Codex surface by this correction. No Codex project workflow or pilot is authorized while that legacy tree remains discoverable without an explicit containment decision, and the first Codex-delivery implementation ticket must quarantine/archive it or atomically replace it with the contract-generated catalog before enabling root `AGENTS.md` or project Codex configuration. The eventual single semantic authority for both surfaces is the shared `agent-orchestration/` contract (Output #2, Source Ownership decision — Decided, contract directory not yet built).
- Within the Claude surface, `.agents/` is fully superseded except two named carve-outs, both explicitly deferred to a future ticket, not executed here:
  - `.agents/rules/engine_contracts.md` (224 lines) — holds prescriptive per-subsystem update rules `CLAUDE.md`'s condensed table lacks.
  - 6 `.agents/skills/` dirs (`clean-code`, `codebase-search`, `code-review`, `create-skill`, `receiving-code-review`, `requesting-code-review`) — no `.claude/skills/` equivalent exists yet.
- **`WorkflowRegistry` determination** (`src/lab/registry.py`): dead/unwired code today — zero production call sites (confirmed by grep + graphify BFS), and `TCK-20260524-LAB-GUARDRAILS` explicitly proposed wiring it in, then shipped a plain-dict parameter instead. Left in place, unmodified, as inert-but-tested utility code. Whether its YAML-frontmatter-to-Pydantic parsing pattern is reusable for the shared contract (Output #2 below) is **not decided here** — that's for the implementation epic.

**Gap carried forward:** the 2 retain-and-migrate carve-outs are classified, not migrated. An implementation epic that assumes `.agents/` is fully gone yet would be wrong. Separately, this correction fixed a contradiction between Outputs 1 and 4 (Output 1 previously misclassified `.claude/` as a Codex-discovered location); no Codex delivery subtree exists yet, and generating one is future implementation-epic work gated behind the shared contract.

### 2. Contract-format ADR (representation, source ownership, versioning, provider-adapter boundary, conformance strategy)

**Ticket:** `TCK-20260721-ORCHESTRATION-CONTRACT-ADR` → **Doc:** `docs/architecture/agent_orchestration_contract.md`

Five separately labeled decisions, each carrying a status tag:

| Decision | Status | Summary |
|---|---|---|
| Contract Representation/Format | **Decided** | YAML for reviewable definitions + generated Python validation, per the source plan's initial recommendation. |
| Source Ownership | **Decided** | New repo-root `agent-orchestration/` directory, explicitly "a source specification, not a second implementation." |
| Versioning | Proposed-pending-implementation-evidence | A `version` field on the contract, aligned with existing `workflow_version`/`hook_schema_version` naming already used in the monitoring-writer decision — thin, not fleshed out. |
| Provider-Adapter Boundary | **Decided** | `.claude/` and `.codex/` each translate the shared contract into provider-native config; adapters may not silently redefine workflow phases, terminal statuses, gate policy, or artifact requirements. |
| Conformance Mechanism | Proposed-pending-implementation-evidence | Only "add contract conformance tests for both provider adapters" from the source plan — the least-specified of the 5. |

- **Execution identity is explicitly a consumed input, not decided here** — the ADR quotes Output #3's execution_id decision verbatim and states it may specify how the contract represents that identity, but does not choose its format or ownership independently. Verified byte-for-byte against the source doc during Architecture-Verify.
- ADR follows the two real precedent docs' shape (`simulation_watchdog.md`, `performance_optimization.md` — frontmatter + unnumbered title + Status/Context/Decision/Rationale/Trade-offs/Consequences), not the unused numbered `ADR-XXX` template. Registered in `docs/REGISTRY.yaml`, linked from this plan doc's own Related Material section.

**Gap carried forward:** 2 of 5 decisions are `Proposed-pending-implementation-evidence`, not `Decided` (corrected per Codex's review — Contract Representation/Format and Source Ownership are `Decided`, not pending). Conformance Mechanism in particular has almost no shape yet — an implementation epic should treat that as its own open design question, not an assumed given.

### 3. Execution-identity and monitoring-writer ADR, backed by portability and concurrent-write test evidence

**Ticket:** `TCK-20260721-MONITORING-WRITER-DECISION` → **Doc:** `docs/ai/monitoring_writer_decision.md`

- **Execution identity, Decided:** `execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"` (immutable per-execution key). `run_id` retained as the human-readable reference field. `ticket_id` promoted to an explicit stable cross-run join key, since the same ticket can now run under both providers.
- **Writer design comparison:** 3 candidates scored against POSIX+Windows portability, malformed-partial-line rejection, append-only preservation, and safe two-writer concurrency. Recommended: a lock-file protocol using `os.O_CREAT | os.O_EXCL` with bounded retry and stale-lock recovery.
- **Supported-platform set, honestly scoped:** `{Linux}`. This machine and this repo's CI (`.github/workflows/test.yml`, `ubuntu-latest`-only) have no Windows or macOS runner, no `wine`, no Windows Docker host. Per the source plan's own "every supported development platform" wording and its escape-valve clause, **Windows and macOS are explicitly marked NOT APPROVED / BLOCKED (no evidence)** rather than silently omitted or assumed compatible. Linux itself has real evidence: a 200-invocation concurrent-writer stress test (`tests/tools/test_monitoring_writer_lockfile_candidate.py`, committed, passing) using a non-POSIX-locking mechanism, satisfying the plan's "at least one non-POSIX-locking mechanism" requirement.

**Gap carried forward — the most consequential one in this batch:** the writer design has zero portability evidence beyond Linux. If Codex's own execution environment is not Linux, or if any target deployment includes Windows/macOS, the implementation epic cannot assume the recommended design works there without first gathering that evidence — this is a real, named blocker, not a formality.

### 4. Codex capability matrix, verified from current official documentation and provider fixture experiments

**Ticket:** `TCK-20260721-CODEX-CAPABILITY-MATRIX` → **Doc:** `docs/ai/codex_capability_matrix.md`

- All 10 previously-claimed Codex lifecycle hook events — `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop`, `SessionStart`, `SubagentStart` — individually marked **VERIFIED**, with field-table text excerpted directly into the durable doc from a locally cached official Codex manual (the cache itself is not durable, so the doc does not merely cite the cache path).
- **Fixture-experiment evidence, distinct from documentation citation:** `codex features list` run against a live, authenticated Codex CLI in this environment reports `hooks: stable, true` — codified as a re-runnable, committed diagnostic test (`tests/tools/test_codex_capability_diagnostics.py`), not a one-off claim.
- A deeper stdin-payload-capture fixture experiment (actually triggering a hook and inspecting its real payload shape) was investigated but **deliberately deferred**, not executed — `codex features list`'s enabled/stable signal was judged sufficient to satisfy this output's literal AC wording, but it is not the same strength of evidence as a captured real payload.

**Gap carried forward:** hook *existence* is verified; hook *payload shape* under real invocation is not yet captured. An implementation epic building the actual Codex adapter should not assume the payload shape without that deeper experiment, or should schedule it as an early implementation-epic task.

### 5. Replay-fixture specification and proof that the first Codex slice can run without editing tickets, invoking production hooks, or appending monitoring records

**Ticket:** `TCK-20260721-CODEX-REPLAY-PROOF` → **Doc:** `docs/ai/replay_fixture_spec.md` + `tools/agent_replay/`

This output proves a replay runner for the deterministic Scope→Review slice was built and tested — it does **not** prove a real Codex adapter has executed that slice. A real Codex-side replay invocation is future implementation-epic work (Phase 4 of Codex's own `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`).

- **Scope decision:** "replay the implement-ticket slice" was interpreted as the narrow, deterministic Scope→Investigate→Plan→Review portion of `implement-ticket.js` — not the full agent-driven workflow, since the 10 LLM-driven `agent()` calls cannot be literally replayed without a live model. The replay runner imports and calls the real `tools/gate_checks/*.py` functions the live orchestrator uses (read-only), and hand-mirrors the small amount of inline branch logic that has no existing gate-check module — the same accepted pattern as `implement-ticket.js`'s own `classifyChecklistFailure`, which is "kept in sync by hand" with its Python counterpart.
- **One real, checked-in fixture set**, derived read-only from this same discovery batch's own `TCK-20260721-ORCHESTRATION-CONTRACT-ADR` run (`tickets/done/`, `stored_artifacts/`, and the real `agent-monitoring/events.jsonl`/`runs.jsonl` seq 1-4 entries) — not synthetic data.
- **Unconditional hook prohibition, verified by process-level (not output-diffing) evidence:** the runner never imports, subprocesses, or `importlib.import_module`s `record_run.py`, `record_events.py`, `post_tool_hook.py`, or `pre_tool_hook.py`, under any condition. This is enforced by a committed AST-based static test that scans every string constant in the runner package — not just call-argument nodes — for the 4 forbidden filenames, widened during implementation beyond the original plan on an architecture-review advisory. Pure in-memory no-op functions stand in for all monitoring/hook I/O.
- **Fail-clearly enforcement:** the fixture loader raises `FixtureValidationError` naming the exact missing field on any incomplete fixture — no silent defaulting, no partial replay.
- **No-mutation proof:** a snapshot test compares real `tickets/**` and `agent-monitoring/*.jsonl` state before and after the replay run and asserts byte-for-byte no diff — against the real repo paths, not a copied tmp-dir shortcut.
- **Fixture envelope evaluated against Output #2's contract representation** (AC requirement): the spec doc states this fixture uses YAML data with a hand-written Python validator, consistent with the ADR's YAML-leaning representation decision, and explicitly notes this fixture envelope is a *different* artifact from the ADR's own future `agent-orchestration/contract.yaml` — not a premature stand-in for it.

**Gap carried forward:** this proves the *deterministic* slice of Claude's own workflow can be replayed safely — it does not yet prove anything about a *Codex* adapter actually executing that slice, since no Codex-side runner exists yet. That is squarely implementation-epic work.

## Net Assessment

All 5 outputs exist, are evidence-backed, and are internally consistent with each other (execution identity flows from Output #3 into Output #2 and Output #5 without contradiction, verified at each ticket's Architecture-Verify phase). Three carried-forward gaps are real and should shape the implementation epic's own scoping rather than be silently assumed away:

1. **Monitoring-writer portability** — Linux-only evidence; Windows/macOS explicitly blocked.
2. **Conformance mechanism** — least-specified of the ADR's 5 decisions, effectively undesigned.
3. **Codex hook payload shape** — existence verified, real payload under invocation not yet captured.

Plus one lower-priority carried-forward item: the 2 `.agents/` retain-and-migrate carve-outs are classified but not yet migrated.

## Codex review response received

Codex reviewed this summary and responded in
`idea_provider_agnostic_agent_orchestration_discovery_gate_closure_response_codex.md`
(2026-07-21). Result: Outputs 2–5 approved with their stated limitations;
Output 1 was blocked on a factual error — `docs/ai/agents_dir_disposition.md`
incorrectly named `.claude/` as a Codex-discovered location, contradicting
the same batch's own `codex_capability_matrix.md`. Two non-blocking wording
corrections were also requested against this doc (the Output 2 status table,
and Output 5's replay-vs-adapter-execution framing).

The corrections above (Output 1 rewritten under `TCK-20260721-AGENTS-DISPOSITION-FIX`,
the Output 2 status table, and the Output 5 clarifying sentence) were made
directly in response to that review. The discovery gate should now be
re-reviewed for closure given these corrections.
