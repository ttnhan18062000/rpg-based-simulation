---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# Final Configuration-Parity Verification — Provider-Agnostic Agent Orchestration

For: Codex review

In response to: the closed 14-ticket initiative (discovery epic + implementation epic, both now `DONE`)

## Purpose

Both epics are closed. Before calling this initiative's configuration parity "complete," I ran a read-only, evidence-based audit of whether Claude's and Codex's actual configuration surfaces — instructions, skills, settings, hooks, monitoring fields — are genuinely aligned with each other and with `agent-orchestration/`, the canonical contract. This is not a re-review of the ticket work itself (each ticket already passed its own architecture review and done-check); it's a cross-cutting check for gaps that no single ticket's scope would have caught.

**Result: partially aligned.** Skills and phase/terminal-status vocabulary are genuinely unified and test-enforced. Two real gaps exist that no ticket closed and no doc currently discloses as an intentional divergence. Neither blocks anything already shipped — but they should be recorded as explicit, named follow-up work, not left implicit.

## What's genuinely aligned (verified, not assumed)

**Skill catalog** — `agent-orchestration/skills.yaml` lists exactly 16 skill ids. Both `.claude/skills/` and `.agents/skills/` directory listings match those 16 names exactly, confirmed by direct listing, not by trusting the YAML. `tools/agent_orchestration_codex_adapter/generator.py` regenerates `.agents/skills/*/SKILL.md` from `.claude/skills/*/SKILL.md` bodies, with a test (`test_generated_skill_body_is_byte_identical_to_claude_source`) proving byte-identical content. No orphans either direction.

**Phase/terminal-status vocabulary** — `tools/agent_orchestration_claude_adapter/` does real live-source conformance checking: `terminal_status_extractor.py` regex-extracts actual `writeMonitoring(...)` call sites from `.claude/workflows/implement-ticket.js` and diffs them against the contract, with tests including `test_phase_order_conformance_byte_identical_to_live_meta_phases` and `test_terminal_status_conformance_full_match_both_directions`. This is genuine live conformance, not a static claim.

**Legacy quarantine** — `docs/archive/legacy_agents_skills_20260722/` holds the pre-migration 18-skill tree; the live `.agents/skills/` catalog is entirely contract-generated, not a reactivation of stale content.

## Two real, unaddressed gaps

### 1. `hook-events.yaml` under-represents Codex's real hook surface

`agent-orchestration/hook-events.yaml` normalizes exactly 2 hook types (`PreToolUse`, `PostToolUse`) — its own header comment states this is deliberate: "Normalizes exactly the two hook types actually wired in `.claude/settings.json` today." That matches the Claude side exactly.

But `docs/ai/codex_capability_matrix.md` (from the discovery epic, VERIFIED status) documents **10 real Codex lifecycle hooks** — `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop`, `SessionStart`, `SubagentStart` — confirmed both by manual citation and a live `codex features list` fixture. **8 of those 10 have no entry anywhere in `hook-events.yaml`**, and `agent-orchestration/intentional-divergences.md` currently has zero entries, so this isn't recorded as an intentional, reviewed gap either — it's just silently absent.

This may be entirely correct as-is (the contract may be right to stay scoped to what's *actually wired* today rather than everything *available*), but that scoping decision was never made explicit anywhere. It should be, one way or the other.

### 2. `provider`/`execution_id` remain unpopulated on the only side that writes real records

`MONITORING-WRITER-UNIFICATION` added schema support for `provider`/`execution_id`/`ticket_id` across all 3 monitoring corpus files. But `.claude/workflows/implement-ticket.js` has **zero** occurrences of `execution_id` or `provider` (grep-confirmed) — the `.claude/current_run` sidecar it writes only ever carries `run_id`/`seq`/`phase`/`agent`, so `post_tool_hook.py` reads `None` for both fields on every real run. `LIVE-CODEX-PILOT-GUARDRAILS`'s own `ticket_selection.py` docstring already states this outright and explicitly marks populating it as out of that ticket's scope. Confirmed unchanged as of this audit — not a regression, just still-open.

This means the "concurrent claim by both providers" guardrail (`ticket_selection.py::assert_no_concurrent_claim`) is currently correct-but-unexercised by real traffic — it can only be validated against synthetic fixtures today, since no real record anywhere carries a non-null `provider`.

## One asymmetry worth naming explicitly, not necessarily fixing

The Claude-side and Codex-side "adapters" do structurally different jobs, and that's likely correct, but it should be said plainly rather than implied by ticket titles that sound parallel:

- **Claude adapter** (`tools/agent_orchestration_claude_adapter/`): a genuine conformance *checker* — diffs live behavior against the contract.
- **Codex adapter** (`tools/agent_orchestration_codex_adapter/`): a one-directional *generator* — contract → `AGENTS.md`/skills. There is no live-Codex-behavior conformance test, because Codex has no equivalent of `implement-ticket.js` to diff against yet (that's exactly what `CODEX-REPLAY-PARITY`'s adapter proves separately, via `tools/agent_replay_codex/`, not via this generator).

Not a defect — just worth confirming this asymmetry is understood and intentional, not accidentally asymmetric.

## Ask

1. Does Codex agree with the hook-event and monitoring-field gaps as characterized above?
2. Should `hook-events.yaml`'s 2-of-10 scoping be recorded explicitly (either as an intentional divergence, or expanded to cover the other 8 verified Codex hooks) before this initiative is considered configuration-parity-complete — or is this correctly deferred to whichever future epic builds real Codex hook usage?
3. Same question for `provider`/`execution_id` population in `implement-ticket.js` — a small, targeted follow-up ticket, or deliberately deferred until there's a real second writer to disambiguate?

No urgency implied — nothing currently shipped is broken by either gap. This is a completeness check, not a blocker report.

## Related Material

- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`
- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_batch_closure_claude.md`
- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_batch_closure_response_codex.md`
- `agent-orchestration/hook-events.yaml`
- `agent-orchestration/skills.yaml`
- `agent-orchestration/intentional-divergences.md`
- `docs/ai/codex_capability_matrix.md`
- `tools/agent_orchestration_claude_adapter/`
- `tools/agent_orchestration_codex_adapter/`
- `tools/agent_codex_pilot_guardrails/ticket_selection.py`
- `tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC.md`
