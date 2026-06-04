# AI Tooling — Overview

This project uses **Claude Code** with a structured set of subagents, multi-agent workflows, and skills to automate the full development and simulation lifecycle.

## Three Layers

| Layer | Location | Purpose | How to invoke |
|---|---|---|---|
| **Agents** | `.claude/agents/*.md` | Focused subagent for one role in a task | Spawned automatically by workflows, or via `Agent(subagent_type: "name")` |
| **Workflows** | `.claude/workflows/*.js` | Multi-agent orchestration across many steps | `Workflow({ name: "workflow-name", args: {...} })` or `/workflow-name` |
| **Skills** | `.claude/skills/*/SKILL.md` + built-in | Slash commands for specific task patterns | `/skill-name` in the prompt |

---

## Quick Reference

### When to use a workflow vs. an agent vs. a skill

**Use a workflow** when the task spans multiple phases (scope → implement → test → close). Workflows carry state across agents and handle gates and failures automatically.

**Use an agent directly** when you need one focused task in the middle of a conversation — e.g., "check if this plan violates architecture rules" or "update the parity ledger for this change."

**Use a skill** for a well-defined single-session pattern that doesn't require multi-agent orchestration — e.g., `/graphify`, `/code-review`, `/implement-ticket` (which is a skill that triggers the workflow).

---

## Document Index

| Document | Contents |
|---|---|
| [agents.md](agents.md) | All 11 subagents — role, inputs, outputs, when to invoke |
| [workflows.md](workflows.md) | All 8 workflows — phases, args, return values, when to use |
| [skills.md](skills.md) | Project skills and built-in Claude Code skills |
| [ticket-lifecycle.md](ticket-lifecycle.md) | Complete development flow from request to closed ticket |

---

## Design Principles

**Separation of concerns.** Each agent owns one responsibility. The `implementer` never creates tickets; the `ticket-scoper` never writes code.

**Hard gates.** Workflows stop and return a structured failure when a gate fails (architecture review rejected, tests fail, DoD blocked). The user resolves the issue and resumes with `ticket_id`.

**Resumability.** The `implement-ticket` workflow accepts `ticket_id` to skip phases already completed. This makes re-runs after a gate failure cheap.

**Parity discipline.** Any behavior change flows through `parity-updater` before the ticket closes. P0 parity entries require a passing `test_path` — the workflow enforces this.

**No silent scope creep.** The `planner` maps every step to a specific acceptance criterion. The `done-checker` verifies scope match before the ticket moves to `done/`.
