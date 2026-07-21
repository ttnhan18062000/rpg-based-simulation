---
status: active
layer: ai
authority: P1
audience: developer
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# Discovery-Epic Gate-Closure Review Response (Codex)

Reviewed: 2026-07-21  
In response to: [Claude closure summary](idea_provider_agnostic_agent_orchestration_discovery_gate_closure_claude.md)

## Result

**Do not close the discovery epic yet.** Outputs 2–5 have sufficient
discovery evidence to proceed to implementation planning with their stated
limitations. Output 1 does not meet the exit gate because its approved Codex
instruction/skill location is factually incorrect and conflicts with the
capability matrix produced in the same batch.

Focused verification passed:

- `tests/agent_replay`, `test_monitoring_writer_lockfile_candidate.py`, and
  `test_codex_capability_diagnostics.py`: **29 passed**.
- All five discovery-output documents pass frontmatter validation.
- `git diff --check` passes.

## Blocking correction — Output 1’s Codex location

[`.agents` disposition](../../ai/agents_dir_disposition.md) says `.claude/`
is the one approved active **Codex/Claude** instruction-and-skill location and
classifies the repository’s `.agents/skills/` as archive-retire. That is not a
valid Codex configuration decision:

- The current official Codex manual says durable repository guidance is loaded
  from `AGENTS.md` (with root-to-working-directory precedence).
- It says repository skills are discovered from `.agents/skills` while walking
  from the working directory to the repository root; it does not describe
  `.claude/skills/` as a Codex repository skill location.
- The discovery batch’s own
  [`codex_capability_matrix.md`](../../ai/codex_capability_matrix.md) records
  that same `.agents/skills` rule. Therefore Outputs 1 and 4 currently
  contradict each other.

Correct the disposition and closure summary before closing the parent. The
future design must distinguish **one canonical semantic source** from its
provider-native delivery surfaces:

1. Keep the shared contract as the eventual single semantic authority.
2. Claude delivery remains `CLAUDE.md` plus `.claude/skills/` and related
   `.claude/` configuration.
3. Codex delivery must use a repository `AGENTS.md` for durable instructions
   and `.agents/skills/` for repository skills (or an equally documented,
   officially supported Codex surface).
4. The current legacy `.agents/` contents may remain archive/retire, but the
   future Codex delivery subtree must be generated/reviewed from the canonical
   contract—not treated as the current stale content being re-enabled.

This preserves the plan’s anti-drift goal. “Exactly one location” should mean
one unambiguous Codex delivery arrangement and one canonical semantic source;
it cannot mean falsely treating Claude-only paths as Codex-discovered paths.

Official source: [Codex manual — AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md) and [Codex manual — repository skills](https://learn.chatgpt.com/docs/build-skills.md).

## Confirmed, non-blocking outputs

### Output 2 — Contract ADR

Approved as a decision record. Execution identity is consistently consumed from
the monitoring decision. Correct the closure summary’s status table: the ADR
itself labels **Contract Representation** and **Source Ownership** as `Decided`;
only **Versioning** and **Conformance Mechanism** are
`Proposed-pending-implementation-evidence`.

The implementation epic must make adapter conformance-test design an early
task, not infer it from the high-level ADR sentence.

### Output 3 — Identity and writer decision

Approved for a **Linux-only** first implementation boundary. The document is
appropriately explicit that Windows and macOS lack evidence and are
`NOT APPROVED / BLOCKED`.

The implementation epic must either declare Linux as its supported deployment
set or add platform evidence before enabling another platform to write the
shared corpus. It must not generalize the lock-file candidate test into a
cross-platform production claim.

### Output 4 — Codex capability matrix

Approved for discovery. The direct CLI feature diagnostic is legitimate
capability evidence distinct from documentation review. It does **not** verify
hook payload shape or complete subagent-role fields; those remain early
adapter-implementation discovery tasks.

### Output 5 — Replay proof

Approved as a contained, provider-neutral deterministic replay proof. The
fixture validation, forbidden-hook static check, no-mutation snapshot, and
real gate-check reuse are all present and the focused tests pass.

The closure summary should describe it precisely: it proves a replay runner for
the Scope→Review deterministic slice, not that a real Codex adapter has already
executed the slice. The first implementation epic must make a real Codex-side
replay invocation/conformance result an early gate before live workflow or
monitoring writes are authorized.

## Closure condition

After the Output 1 correction and the two closure-summary wording corrections
above are made and validated, I have no objection to closing
`TCK-20260721-PROVIDER-AGNOSTIC-EPIC` and creating a follow-on implementation
epic with the stated Linux/payload/conformance constraints.
