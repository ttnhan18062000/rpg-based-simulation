---
status: active
layer: ai
authority: P1
audience: developer
date: 2026-07-29
tags: [ai, codex, workflows, hooks, agent-monitoring, provider-agnostic]
---

# Codex Runtime Status and Activation Plan

## Purpose and scope

This is the current operational status tracker for Codex in this repository.
It distinguishes the completed provider-agnostic **foundation** from a future
live Codex **runtime activation**. It is not authorization to enable a hook,
write monitoring data, invoke paid Codex work, or run a live pilot.

The completed provider-agnostic initiative delivered shared semantics, safe
Codex guidance, direct-experiment evidence, replay proof, and pilot guardrails.
It intentionally did not activate Codex as a production workflow provider.

## Status summary

| Pillar | Current status | Production readiness |
|---|---|---|
| Semantic workflow contract | Implemented and validated | Ready as canonical source |
| Guidance and skills | Implemented; 16 skills plus 18 declared companion assets | Ready for instruction discovery |
| Claude live workflow conformance | Implemented and tested | Active Claude baseline |
| Codex runtime workflow | Replay-only; no `implement-ticket` runtime | Not active |
| Codex hooks | Payload captured; project config intentionally hook-free | Not active |
| Shared monitoring writer/schema | Implemented and tested | Capability ready, no Codex call site |
| Execution identity | Schema supported, not supplied by real Claude/Codex writes | Not operational |
| Codex replay/shadow parity | Real, consent-gated proof for Scope→Review fixture | Proven for limited replay only |
| Pilot safety/rollback | Implemented and tested | Ready to gate, not authorize, a pilot |
| Dashboard/provider analysis | Reader support implemented | No real provider-attributed traffic yet |

## Pillar tracker

### 1. Canonical semantics

**Implemented**

- `agent-orchestration/` is the canonical source for the `implement-ticket`
  first vertical slice: workflow, roles, terminal statuses, skills, monitoring
  fields, normalized hook vocabulary, and reviewed divergences.
- The contract validator is deterministic, network-free, and write-guarded.
- Claude conformance tests compare the live workflow's phase and status
  vocabulary to the contract.

**Verification already available**

- `tests/agent_orchestration/`
- `tests/agent_orchestration_claude_adapter/`

**Remaining work**

None for the current first-slice semantic model. Any new runtime behavior must
extend the contract first rather than add provider-local semantics.

### 2. Guidance and skill packages

**Implemented**

- Root `AGENTS.md` is generated from the contract.
- `.agents/skills/` contains the 16 contract-declared Codex skills.
- The legacy 18-skill tree is archived outside Codex discovery.
- `skills.yaml` declares 18 curated companion assets for four skills; the
  generator copies them byte-identically, preserves nested paths, and rejects
  traversal/missing-source cases.

**Verification already available**

- `tests/agent_orchestration_codex_adapter/` validates frontmatter/body
  traceability, companion-asset byte identity, reference resolution, archive
  fidelity, and generation write guards.

**Remaining work**

Keep companion assets contract-declared. Do not copy arbitrary `.claude/skills/`
contents automatically; add a declared asset and reference-resolution coverage
when a shared skill gains a new dependency.

### 3. Codex project configuration and hooks

**Implemented**

- `.codex/config.toml` is committed as a comment-only, hook-free project
  marker.
- A direct isolated experiment captured a real `PostToolUse` payload and the
  working Codex TOML registration shape.
- Codex has more available lifecycle events than the contract currently
  normalizes; the contract intentionally records only the two events wired on
  the Claude side (`PreToolUse`, `PostToolUse`).

**Current behavior**

- No Codex hook command runs in this repository.
- Normal Codex tool use does not append monitoring data or trigger a production
  writer.

**Activation prerequisites**

1. Record a provider hook-surface policy separating **available**,
   **normalized**, and **enabled** events per provider.
2. Choose the minimal first enabled event: `PostToolUse` only, unless new
   contract evidence justifies another event.
3. Define the hook command's failure behavior, timeout, output redaction, and
   out-of-band diagnostics.
4. Obtain explicit, contemporaneous human approval before any real config with
   hook registration is created or executed.

**Exit verification**

- Scratch experiment first; never test a hook-bearing config in the repository.
- Captured stdin payload validates against the documented fixture schema.
- Project config diff is reviewed and contains only the approved event/command.
- Failure injection proves hook failure does not block the workflow.
- Rollback restores the hook-free config and leaves the monitoring corpus
  prefix unchanged.

### 4. Runtime workflow orchestration

**Implemented**

- Claude retains the active `.claude/workflows/implement-ticket.js` workflow.
- Codex has contract guidance and replay tooling, not a live native
  `implement-ticket` executor.
- The real replay adapter proves Scope→Investigate→Plan→Review fixture behavior
  can match the provider-neutral runner under a consent gate.

**Not implemented**

- No Codex runtime maps a real ticket to the complete phase/gate/artifact
  lifecycle.
- No automatic ticket ownership, phase event emission, artifact validation, or
  finalization exists for live Codex work.

**Activation plan**

1. Specify a minimal Codex runtime adapter from the canonical workflow contract.
2. Limit the first live slice to one low-risk ticket and explicitly supported
   phases; do not imply all Claude workflow features are available.
3. Make phase transitions and required artifacts machine-checkable before
   enabling writes.
4. Preserve Claude as the default/only production executor until shadow-mode
   evidence and pilot approval succeed.

**Exit verification**

- Contract fixture parity for phases, final status, gate result, and artifacts.
- Process-level containment proof: no unexpected ticket, hook, or monitoring
  mutation.
- Human-reviewed intentional-divergence entry for every permitted mismatch.

### 5. Monitoring schema, writer, and execution identity

**Implemented**

- The shared Linux append-only writer, locking/recovery coverage, additive
  schema, legacy normalization, and provider-aware dashboard ingestion exist.
- New records can carry `provider`, `execution_id`, and `ticket_id`.
- Reader/dashboard behavior labels legacy records rather than dropping them.

**Current limitation**

- Real Claude workflow records do not currently supply `provider` or
  `execution_id`; Codex has no active writer at all.
- Concurrent-provider detection is therefore tested with fixtures but has no
  real provider-attributed traffic to evaluate.

**Activation plan**

1. File a narrow execution-identity activation ticket before relying on pilot
   concurrency protection.
2. Update the Claude current-run sidecar/workflow to create a validated
   `provider="claude"` execution identity for new records.
3. Add the equivalent Codex identity only when the live adapter and hook/writer
   boundary are approved.
4. Keep all historical JSONL immutable; new identity fields are additive only.

**Exit verification**

- One controlled Claude execution produces coherent `provider`,
  `execution_id`, `ticket_id`, and `run_id` records across all relevant JSONL
  sources.
- Legacy parsing/queries remain green.
- The dashboard groups/filter records by provider and labels legacy-unknown
  records correctly.
- Baseline prefix comparison proves no historical record changed.

### 6. Replay, shadow comparison, and pilot guardrails

**Implemented**

- `tools/agent_replay_codex/` has a strict live-consent gate, isolated scratch
  execution, no-diff containment, hook-free config guard, and replay/shadow
  comparison tooling.
- `tools/agent_codex_pilot_guardrails/` provides pilot request validation,
  independent human sign-off, candidate/concurrent-claim rejection, evidenced
  enabled-surface checks, baseline comparison, and scratch-only rollback.

**Boundary**

These mechanisms are readiness tooling. They do not select a live ticket, grant
sign-off, enable a hook, or execute a pilot.

**Pilot entry criteria**

- Runtime adapter and execution identity activation are complete.
- Hook policy and minimal hook configuration have passed isolated verification.
- A human owner supplies a specific ticket, rollback plan, and contemporaneous
  pilot sign-off.
- The candidate is low risk and not concurrently claimed.

**Pilot exit criteria**

- Pre/post monitoring baseline preserves every pre-existing line.
- The provider-attributed run is visible in monitoring and dashboard readers.
- Rollback is tested by one configuration/flag action and produces zero
  unintended ticket or monitoring changes.
- The result is reviewed before expanding scope.

## Recommended activation sequence

```text
Execution identity (Claude first)
        ↓
Hook-surface policy + isolated Codex PostToolUse verification
        ↓
Minimal Codex runtime adapter + shadow parity
        ↓
Single human-approved pilot with monitoring/rollback gates
        ↓
Review evidence, then decide whether to expand
```

## Required decision record for every activation step

For each new runtime-enabling ticket, record:

- owner and explicit scope;
- contract version and provider adapter version;
- enabled hook events and writer functions;
- consent/sign-off evidence for any paid or live Codex invocation;
- pre/post monitoring manifest or prefix comparison;
- replay/shadow/pilot test commands and outcomes;
- rollback command and observed result;
- intentional divergences or an explicit zero-divergence result.

## Baseline verification commands

Use scoped suites; do not run a live Codex invocation merely to refresh this
tracker.

```bash
.venv/bin/python3 -m pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -v
.venv/bin/python3 -m pytest tests/agent_replay_codex/ tests/agent_codex_pilot_guardrails/ -v
```

The contract suite currently has one separately tracked stale staging-artifact
path failure (`TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH`). It must remain
distinguished from activation regressions until repaired.

## Related sources

- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`
- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_claude.md`
- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_response_codex.md`
- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/skill_companion_assets_fix_verification_claude.md`
- `agent-orchestration/README.md`
- `docs/ai/codex_capability_matrix.md`
