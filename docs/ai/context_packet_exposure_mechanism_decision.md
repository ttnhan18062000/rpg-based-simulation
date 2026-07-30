---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, workflows]
---

# Context Packet Exposure Mechanism Decision — TCK-20260730-CONTEXT-PACKET-EXPOSURE-DECISION

Resolves **Open Decision 6** from
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`:

> Should context packets be exposed as an MCP tool, a provider-adapter library, or both after the
> provider-neutral contract is implemented?

## 1. The precondition, checked directly

The question names its own precondition — "after the provider-neutral contract is implemented."
Both parent epics that own that contract (`TCK-20260721-PROVIDER-AGNOSTIC-EPIC`,
`TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC`) are `DONE`. But epic-level `DONE` status is
not the same claim as "the contract is implemented" — the contract's own ADR,
`docs/architecture/agent_orchestration_contract.md`, tracks five sub-decisions each with an
independent status line. Three matter here, quoted directly from that doc:

| Sub-decision | Status |
|---|---|
| Contract Representation and Format | `Proposed-pending-implementation-evidence` |
| Provider-Adapter Boundary | **`Decided`** |
| Conformance Mechanism | `Proposed-pending-implementation-evidence` |

Only one of the three — Provider-Adapter Boundary — has cleared to `Decided`. Its concrete rule,
quoted from the ADR:

> The adapters may contain provider-specific payload parsing, invocation, permissions, and hook
> registration. They may not silently redefine workflow phases, terminal statuses, gate policy, or
> artifact requirements.

So the precondition is **partially, not fully, satisfied**. This decision proceeds anyway — same
posture Open Decision 5 took toward zero real shadow-packet events — but the answer below is
framed as directional, not final, for exactly this reason.

## 2. Real precedents already in this repo

Two real, load-bearing precedents exist today and ground this decision better than reasoning from
the two option labels alone.

**MCP tool precedent — `tools/search_mcp.py`.** Exposes `search_docs`/`search_health` as MCP
tools. Its own module docstring states the transport and registration model directly:

> Transport: stdio (Claude Code spawns this as a subprocess). ... Usage (Claude Code registers via
> `.claude/settings.json`)

This is real, working, and in daily use — but it is wired Claude-specifically today. The MCP
*protocol* is provider-neutral by design (any MCP client can speak it), but this repo's one
concrete instance of it is registered only in `.claude/settings.json`; nothing registers it for
Codex.

**Provider-adapter library precedent — Phase 5's shadow-packet call site.** The one real
integration of context-packet machinery that exists today
(`TCK-20260729-SHADOW-PACKET-CALL-SITE`) is a direct in-process Python call from
`.claude/workflows/implement-ticket.js`'s Investigate phase into `tools/context_packet_assembler.py`
and friends, gated behind `SHADOW_CONTEXT_PACKET_ENABLED`. This is closer in spirit to "library"
than "MCP tool" — no subprocess, no stdio protocol, no separate server process — but it is not yet
a generalized, reusable library module with a stable public interface; it is one Claude-specific
workflow script's direct call.

Neither precedent is symmetric. Both are Claude-only in practice today.

## 3. Does Codex change the calculus?

Open Decision 6 names "after the provider-neutral contract" — implicitly, once a second provider
exists to be neutral *toward*. Checked directly:

- `docs/ai/codex_capability_matrix.md` §1 confirms Codex's `PreToolUse`/`PermissionRequest` hook
  matchers explicitly support **"MCP tool names"** as a matcher value (manual lines 9443-9454,
  quoted verbatim in that doc). This is real evidence Codex's hook framework is MCP-tool-aware —
  i.e., Codex can plausibly act as an MCP client, in principle.
- The same doc's §3 confirms this repo currently has **no `.codex/` directory** — no live Codex
  runtime presence exists here at all.
- `tickets/todos/codex-runtime-activation/` (5 tickets: epic, controlled pilot, posttool adapter,
  runtime shadow, provider-hook-policy) confirms real second-provider activation work is entirely
  unstarted.

So: Codex's hook framework can *reference* MCP tools by name, which is a positive signal for the
MCP-tool option's future viability — but there is zero live Codex execution in this repo to test
either option against. Provider parity for this decision is exactly as unverifiable today as it
was for Open Decision 5's shadow-promotion criteria, and for the identical underlying reason (only
one of two known adapters has ever gone live).

## 4. Recommendation: both, but not symmetric

**Provider-adapter library is the default/primary integration path.** It matches the ADR's one
`Decided` sub-decision (thin provider adapters translating a shared contract), it has the one real
working precedent in this repo (Phase 5's call site), and it avoids introducing a new runtime
dependency (a spawned subprocess speaking stdio MCP) for what is, in the mandatory-packet-assembly
case, an in-process step of an existing workflow run — not an interactive tool call an agent
chooses to make mid-conversation.

**MCP tool exposure is a secondary, optional interface**, layered on top of the same underlying
library — not a competing implementation of it. It fits scenarios where an agent wants to query
context-packet machinery interactively/ad hoc (mirroring how `search_docs`/`search_health` are
already exposed this way), rather than scenarios where a workflow phase mandatorily assembles a
packet as a scripted step. `tools/search_mcp.py` already establishes the pattern; a future context-
packet MCP tool would wrap the same library the adapter path calls directly, not reimplement it.

This is "both" in the same sense the source idea doc's own framing invites — not "pick one" — but
it is asymmetric: one library, one (or two, provider-agnostic) thin callers on top of it. There is
no proposal to build two independent packet-assembly implementations.

## 5. What remains open, stated plainly (not invented)

- **Not fully decided**: `Contract Representation and Format` and `Conformance Mechanism` remain
  `Proposed-pending-implementation-evidence` in the ADR. Until those clear, "the provider-neutral
  contract is implemented" — the decision's own stated precondition — is not fully true, and this
  recommendation should be re-checked against whatever those sub-decisions land on, particularly
  if the conformance mechanism ends up constraining how adapters may call shared library code.
- **Not verifiable today**: zero real Codex executions exist in this repo. Codex's hook-matcher
  awareness of "MCP tool names" is suggestive, not proof, that a Codex-side MCP client integration
  will work the same way Claude Code's does. This should be revisited once
  `tickets/todos/codex-runtime-activation/` produces at least one real live Codex run.
- **Not in scope here**: this decision does not choose *when* (which scenarios, which phases) any
  exposure mechanism gets wired into a real workflow — that remains Phase 6's job, gated by the
  56/122/6 sample-size floors Open Decision 5 already set, which are themselves still far from met
  (6 real shadow-packet events exist as of this writing).

## Resolution

Open Decision 6 is resolved directionally: **provider-adapter library as the default integration
path, MCP tool exposure as a secondary optional interface over the same library** — grounded in
the one `Decided` ADR sub-decision and the two real Claude-only precedents this repo already has.
This is not a final, unconditional answer — it is contingent on the ADR's two still-pending
sub-decisions and on real (not just hook-matcher-inferred) Codex evidence that does not exist yet.
A future ticket should re-open this specifically if either of those two gaps is filled with
evidence that contradicts the recommendation above, rather than silently assuming it still holds.
