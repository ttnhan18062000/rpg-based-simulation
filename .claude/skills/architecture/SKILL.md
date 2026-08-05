---
name: architecture
description: "Architectural decision-making framework. Requirements analysis, trade-off evaluation, ADR documentation. Use when making architecture decisions or analyzing system design."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Architecture Decision Framework

> "Requirements drive architecture. Trade-offs inform decisions. ADRs capture rationale."

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

| File | Description | When to Read |
|------|-------------|--------------|
| `context-discovery.md` | Questions to ask, project classification | Starting architecture design |
| `trade-off-analysis.md` | ADR templates, trade-off framework | Documenting decisions |
| `pattern-selection.md` | Decision trees, anti-patterns | Choosing patterns |
| `examples.md` | MVP, SaaS, Enterprise examples | Reference implementations |
| `patterns-reference.md` | Quick lookup for patterns | Pattern comparison |

---

## 🔗 Related Skills

| Skill / Resource | Use For |
|-------|---------|
| `architecture-reviewer` agent | The real, gated mechanism in this repo that validates a plan (pre-Implement) or a diff (post-Implement Architecture-Verify) against durable-state, API-boundary, registry, and Mechanics Bible rules — this skill's soft ADR-writing guidance complements, but does not replace, that hard gate. |
| `docs/architecture/` | Where this repo's real ADR-shaped design docs live — the same location the `brainstorming` skill's spec-writing flow (`docs/architecture/YYYY-MM-DD-<topic>-design.md`) targets. |
| `api-design-principles` skill | REST/GraphQL API design patterns (this repo, adjacent skill). |
| CLAUDE.md "Architecture Rule" | This repo's own durable-state/API-boundary/strategic-tactical/uncertainty rules — the authoritative source, not this skill's generic patterns, whenever the two disagree. |

---

## Core Principle

**"Simplicity is the ultimate sophistication."**

- Start simple
- Add complexity ONLY when proven necessary
- You can always add patterns later
- Removing complexity is MUCH harder than adding it

---

## Validation Checklist

Before finalizing architecture:

- [ ] Requirements clearly understood
- [ ] Constraints identified
- [ ] Each decision has trade-off analysis
- [ ] Simpler alternatives considered
- [ ] ADRs written for significant decisions
- [ ] Team expertise matches chosen patterns

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.
