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

## The 5 Categories

| Category | What it names | Example |
|---|---|---|
| Subsystem/Topic | A subject-matter area the ticket touches | `faction` |
| Phase/Milestone | A numbered phase or milestone | `phase-5` |
| Process/Skill-signal | A tag whose canonical spelling matches an existing skill/process gate 1:1 | `debugging` |
| Quality-attribute | The nature of a change, not tied to a specific skill | `hardening` |
| Meta-Process | About the ticket/agent-workflow process itself, not gameplay or engine subject matter | `workflows` |

## Registering a New Tag

Tags are now a **hard allowlist**, backed by `docs/guidelines/tag_registry.jsonl`
(`tools/tag_registry.py`) — see `docs/guidelines/tag_taxonomy.md`'s Tag Registry section for the
full rationale. In practice, if you want to use a tag that isn't already registered:

```bash
python3 tools/tag_registry.py add <tag> --category <category> --note "why this tag exists"
```

`<category>` is one of `subsystem-topic`, `process-skill-signal`, `quality-attribute`,
`meta-process` (`phase-milestone` tags like `phase-5` never need registering — they're recognized
by pattern). The tool refuses a tag that's already registered (registration is append-only — you
can't rename or repurpose an existing tag, only add a new one) and refuses a non-canonical tag name
(same lowercase/hyphenated rules `validate_frontmatter.py` enforces). Run
`python3 tools/tag_registry.py list` to see everything currently registered before deciding whether
your intended tag already exists under a different spelling (e.g. `calibration` instead of
`calibrate`) — the whole point of the registry is to catch that before it duplicates.

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

## Tags as a Registry Search Filter

`Subsystem/Topic` tags are now also used as a second, cheap filter dimension when searching
`docs/REGISTRY.yaml` for prior work — alongside `layer` in `create-tickets.js`'s Investigate phase
and alongside `related_code_areas` in `investigator.md`'s "Finding Prior Work" step. Both consumers
derive candidate tags from a concern/ticket's own title and description via a plain substring match
against a fixed seed vocabulary, implemented in
[`tools/registry_query.py`](../../tools/registry_query.py). That vocabulary is the same 10
Subsystem/Topic words this guide's sibling doc
([`docs/guidelines/tag_taxonomy.md`](../guidelines/tag_taxonomy.md)) names as examples — not a
separate list.

See [`docs/guidelines/tag_taxonomy.md`](../guidelines/tag_taxonomy.md) for the full formal rules:
canonical-form requirements, forbidden tags, and the complete (non-closed) category definitions.
