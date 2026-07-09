---
status: active
layer: ai
authority: P1
audience: developer
tags: [audit, agent-infrastructure, observability]
---

# Agent Infrastructure Audit — 2026-07-03

A scored, evidence-based review of the AI agent orchestration layer that runs this repository's development and simulation-research lifecycle: subagents, workflows, hooks, gates, and observability. See [README.md](README.md), [agents.md](agents.md), [workflows.md](workflows.md), and [skills.md](skills.md) for the system this audit reviews.

**Scope:** static review of `.claude/`, `docs/ai/`, `docs/agent-monitoring/`, `CLAUDE.md`, `.github/workflows/`, and `Makefile`. No live workflow run was observed during this audit; the rating is a single reviewer's judgment call, not a benchmark against other projects.

## Overall score: 8.0 / 10 — Mature, gated, not yet deterministic

The orchestration layer is unusually disciplined for a solo-maintained repo: single-responsibility subagents, hard gates with resumable failure states, and harness-level hooks that enforce process rather than trusting a prompt to remember it. The ceiling below 9 is that several of the most consequential gates are themselves LLM judgment calls, and a couple of stated gaps (cost telemetry, hook bypass) are acknowledged but unresolved.

| Category | Score | Weight |
|---|---|---|
| Architecture & separation of concerns | 9.0 | 20% |
| Governance & enforcement | 8.0 | 15% |
| Traceability & observability | 8.0 | 15% |
| Automation coverage | 8.0 | 15% |
| Resilience & failure handling | 7.0 | 15% |
| Documentation & knowledge management | 8.5 | 10% |
| Determinism of judged gates | 6.5 | 10% |

Weighted mean → **8.0 / 10**.

---

## Strengths

**Genuine separation of concerns, not a single mega-prompt.** 11 subagents in `.claude/agents/*.md` each own exactly one pipeline responsibility (`ticket-scoper` never writes code, `implementer` never scopes). 8 orchestration scripts in `.claude/workflows/*.js` compose them with explicit phase tables rather than ad-hoc prompting.

**Hard gates with resumable failure states.** `implement-ticket` returns one of seven structured statuses (`CONFLICTS_DETECTED`, `NEEDS_CHANGES`, `BLOCKED`, `TESTS_FAILED`, `DOD_BLOCKED`, `DONE`, …) and every failure carries a `ticket_id` that lets a re-run skip completed phases. This is pipeline discipline most side projects skip.

**Enforcement lives in the harness, not in hope.** `PreToolUse`/`PostToolUse` hooks in `.claude/settings.json` fire on every tool call — logging to `tools.jsonl` unconditionally, and injecting a reminder before a grep-shaped Bash command or an investigation-shaped Agent call runs. Process rules from `CLAUDE.md` are backed by shell, not just instructed in a system prompt.

**Traceability chain is closed, end to end.** Ticket → staging artifacts → done, appended to `working_log.csv`, cross-checked against an 8-file parity ledger where P0 entries require a passing `test_path`, indexed in a 912-entry `docs/REGISTRY.yaml`. Nothing durable is asserted without a place to point at.

**Human-in-the-loop preserved where it matters.** `propose-simulation-enhancements` explicitly never auto-applies a patch. `update-knowledge-store` has a five-point approval gate (no `HIGH_RISK` proposal proceeds without an explicit marker) before anything is written to the long-term knowledge graph.

---

## Risks & gaps

**Hooks nudge; they don't block.** *(enforcement)* The context-scan hook only injects `additionalContext` when a Bash command matches a keyword case statement (`grep|rg|find|fd|ack|ag`). It's a reminder, not a gate — a reformulated command or a determined skip passes through with no record that the rule was bypassed.

**Monitoring failure is designed to fail silently.** *(enforcement)* The hard rule "monitoring write failure must never fail the workflow" is a sound resilience call, but it means the audit trail's own completeness is unguaranteed — a hook that fails leaves no trace that it failed.

**No cost or token telemetry, acknowledged in the docs.** *(observability)* `docs/agent-monitoring/README.md` states outright that token counts can't be captured — the workflow's `agent()` call never receives `input_tokens`/`output_tokens` from the runtime. With 11 agents fanning out per ticket, there is no governance signal on spend.

**The gates that matter most are LLM judgment, not static analysis.** *(determinism)* `architecture-reviewer`, `done-checker`, `mechanics-auditor`, and `parity-updater` are all agents rendering a verdict, not code running an assertion. The one confirmed deterministic backstop is the `make lane-architecture` static guard target — its coverage relative to what the LLM gates judge is not documented.

**Skill catalog shows signs of not being curated for this repo.** *(maintenance)* `.claude/skills/` mixes project-tuned shortcuts (`implement-ticket`, `create-tickets`) with generic skills — `frontend-design`, `api-design-principles` — with no obvious surface in an RPG simulation backend. Unclear if these are active or vestigial.

**Rollback path for knowledge-store writes is described, not verified.** *(unverified)* `update-knowledge-store` is documented as producing "an audit log JSON — what was included, excluded, approved, and how to revert." This review did not find or execute an actual revert procedure to confirm it works. *(Closed by TCK-20260704-LABKNOWLEDGE-REVERT: `RevertSimulationKnowledgeWorkflow` now implements and tests this path — see `docs/ai/workflows.md`'s `update-knowledge-store` section.)*

---

## Recommendations

Ordered by leverage — cheapest fix with the most trust gained comes first.

1. **Log hook near-misses, not just hook fires.** When the grep-pattern hook doesn't match a command that arguably should have triggered it, that's exactly the signal needed to know the advisory approach is or isn't working. *(Closed by TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING — resolved via hard-blocking the two named cases directly rather than near-miss logging; see `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`'s "Enforcement: nudge vs. block" section.)*
2. **Add a cost proxy to `tools.jsonl`.** Even a rough per-call estimate (agent count × phase) closes the one gap the project's own docs already flag.
3. **Write down what `lane-architecture` actually covers.** Turn the LLM/static split from implicit to an explicit, reviewable boundary — so gaps in the judged gates are a known quantity. *(Closed by TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING — see `docs/ai/workflows.md`'s lane-architecture coverage-boundary note.)*
4. **Prune or scope the skill catalog.** Confirm which of the 14 skills have ever fired against this codebase; retire the rest so the catalog reflects what's actually maintained.
5. **Exercise the knowledge-store revert path once, for real.** A documented rollback that has never run is a hypothesis, not a safety net. *(Closed by TCK-20260704-LABKNOWLEDGE-REVERT — see pointer at L59.)*

---

## Inventory reviewed

| Component | Count | Location |
|---|---|---|
| Subagents | 11 | `.claude/agents/*.md` |
| Orchestration workflows | 10 files / 8 documented | `.claude/workflows/*.js` |
| Project skills | 14 | `.claude/skills/*/SKILL.md` |
| Harness hooks | 4 | `.claude/settings.json` → `hooks` |
| Parity ledger files | 8 | `docs/parity_ledger/*.yaml` |
| Mechanics Bible chapters | 6 | `docs/mechanics/` |
| Doc registry entries | 912 | `docs/REGISTRY.yaml` |
| CI workflows | 2 | `.github/workflows/` |
