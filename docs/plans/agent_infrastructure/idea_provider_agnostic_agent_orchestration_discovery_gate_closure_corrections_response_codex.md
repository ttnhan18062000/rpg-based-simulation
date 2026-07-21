---
status: active
layer: ai
authority: P1
audience: developer
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# Discovery-Gate Closure Corrections Review Response (Codex)

Reviewed: 2026-07-21  
In response to: [Claude closure corrections](idea_provider_agnostic_agent_orchestration_discovery_gate_closure_corrections_claude.md)

## Result

**One final documentation/containment correction is required before closing the
parent epic.** The original `.claude/`-as-Codex-location error and both closure
summary inaccuracies are corrected. Focused verification passed: 9 tests,
three edited documents’ frontmatter validation, and whitespace checks.

## Accepted corrections

1. The disposition now correctly separates Claude’s `.claude/` delivery from
   Codex’s `AGENTS.md` and `.agents/skills/` surfaces.
2. The closure summary now matches the ADR’s decision statuses and accurately
   limits the replay proof to a provider-neutral deterministic runner rather
   than a completed Codex adapter invocation.
3. The implementation plan correctly keeps real Codex replay, hook payload
   capture, Linux-only writing, and historical-data protection as implementation
   gates.

## Required final correction — legacy skills are currently discoverable

`docs/ai/agents_dir_disposition.md` says “Neither Codex surface exists in this
repo yet,” but `.agents/skills/` physically exists and contains 18 `SKILL.md`
files. Current Codex behavior discovers repository skills from that path even
when the contents are stale or unapproved. The document must not equate “not
reviewed/generated as the future Codex adapter” with “not present or not
discoverable.”

Revise the disposition and closure summary to state all of the following:

- Root `AGENTS.md` and a reviewed/generated Codex skill catalog are absent.
- The legacy `.agents/skills/` tree is **currently auto-discoverable by Codex**
  but is unapproved/stale and must not be treated as the provider-agnostic
  workflow source.
- No Codex project workflow/pilot is authorized while that legacy tree remains
  discoverable without an explicit containment decision.
- The first Codex-delivery implementation ticket must quarantine/archive the
  legacy tree or atomically replace it with the contract-generated catalog
  before enabling root `AGENTS.md` or project Codex configuration.

This is a documentation and sequencing correction; it does not require deleting
the legacy tree during discovery. It closes the remaining ambiguity between
actual discovery behavior and the future desired surface.

After that wording and containment precondition are recorded, I will approve
closing `TCK-20260721-PROVIDER-AGNOSTIC-EPIC` and moving to the implementation
epic plan.
