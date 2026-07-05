---
status: active
layer: guidelines
authority: P2
audience: developer
tags: [tagging, taxonomy, skills]
---

# Ticket Tagging — a Practical Guide

`tags` on a ticket or artifact are a controlled vocabulary, not free text — they exist so tools and
agents can route on them later instead of relying on prose.

## The 4 Categories

| Category | What it names | Example |
|---|---|---|
| Subsystem/Topic | A subject-matter area the ticket touches | `faction` |
| Phase/Milestone | A numbered phase or milestone | `phase-5` |
| Process/Skill-signal | A tag whose canonical spelling matches an existing skill/process gate 1:1 | `debugging` |
| Quality-attribute | The nature of a change, not tied to a specific skill | `hardening` |

## Skill Suggestions From Tags

`Process/Skill-signal` tags now trigger a `suggested_skills` note at ticket-scoping time — produced
by `ticket-scoper` for single tickets and by `create-tickets.js`'s Structure phase for
batch-created tickets. This complements `CLAUDE.md`'s file-path-based auto-invoke triggers, which
fire *during* editing, with a signal that fires *before* implementation work starts.

| Tag | Suggested skill |
|---|---|
| `api-design` | `/api-design-principles` |
| `debugging` | `/debugging-strategies` — unless `Related Code Areas` includes a path under `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, or `src/core/registries.py`, in which case suggest `Agent(subagent_type: "world-debugger")` instead |
| `performance` | `/python-performance-optimization` |
| `security` | `/security-review` (this mapping is the first place this route is codified anywhere in the repo — there is no `CLAUDE.md` auto-invoke row for it) |

If none of a ticket's tags match this table, `suggested_skills` is an empty array. The suggestion is
a note for the orchestrating session or a human to act on — it does not itself invoke anything.

See [`docs/guidelines/tag_taxonomy.md`](../guidelines/tag_taxonomy.md) for the full formal rules:
canonical-form requirements, forbidden tags, and the complete (non-closed) category definitions.
