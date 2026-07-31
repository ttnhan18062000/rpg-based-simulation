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

Tags are now a **hard allowlist**, backed by `registries/tag_registry.jsonl`
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

## Registering a New Category

The 5 categories table above is backed by its own append-only registry,
`registries/tag_category_registry.jsonl`, also managed by `tools/tag_registry.py`. If a genuinely
new category is ever needed (rare — the taxonomy is meant to stay small and stable):

```bash
python3 tools/tag_registry.py add-category <category> --note "why this category exists"
```

Same refusal behavior as `add`: a non-canonical or already-registered category is rejected. See
`docs/guidelines/tag_taxonomy.md`'s Tag Registry section for what each of the current 4 addable
categories means and why `phase-milestone` (the 5th row in the table above) is intentionally never
registered here — it stays pattern-recognized (`phase-N`), not registry-backed.

## Skill Suggestions From Tags

`Process/Skill-signal` tags now trigger a `suggested_skills` note at ticket-scoping time — produced
by `ticket-scoper` for single tickets and by `create-tickets.js`'s Structure phase for
batch-created tickets. This complements `CLAUDE.md`'s file-path-based auto-invoke triggers, which
fire *during* editing, with a signal that fires *before* implementation work starts.

Both paths follow the same full 5-category taxonomy for tag assignment, not just the
Process/Skill-signal category that feeds `suggested_skills` — `create-tickets.js`'s Structure phase
assigns a Subsystem/Topic (or Phase/Milestone, Quality-attribute, Meta-Process) tag whenever a
concern's investigated `files_found`/domain clearly supports one, the same way `ticket-scoper` does
for single tickets. Neither path assigns a tag it can't ground in evidence.

The mapping is defined once, in `tools/tag_registry.py`'s `get_skill_mapping()` (registry rows'
optional `triggers_skill` field, merged with a small disclosed legacy fallback for the 4 tags
registered before this field existed). Run `python3 tools/tag_registry.py skill-mapping` to see the
live mapping as JSON — this doc does not maintain its own copy; edit `tag_registry.py` (or register
a new tag with `--triggers-skill`) to change or extend it.

If none of a ticket's tags match, `suggested_skills` is an empty array. The suggestion is a note for
the orchestrating session or a human to act on — it does not itself invoke anything.

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

## Relevance and Drift Checks (Advisory Only)

Registration (`tag_registry.py`) and canonical-form checks (`validate_frontmatter.py`) both verify
that a tag exists and is spelled correctly — neither checks whether an assigned tag actually
*describes* the ticket it's on. Two lightweight, advisory-only mechanisms close that gap. Both are
distinct from `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s corpus-wide sweep, which answers a different
question (is a tag validly formed and registered across the historic corpus) — these answer "does
this tag actually fit."

**Relevance self-check, at tag-assignment time.** When tags are assigned — by `ticket-scoper` for
single-ticket scoping, or by `create-tickets.js`'s Structure phase for batch creation — the same
agent turn also self-assesses whether each assigned tag's registered note/category plausibly
matches the ticket's own title, scope, and `related_code_areas`/`files_found`. The result is a
`tag_relevance_flags` list: one `"<tag>: <one-line reason>"` string per tag that doesn't clearly
fit, or an empty list if every tag fits. It is surfaced via a log line only (`Tag relevance flags:
...`) — it never rejects a tag, never blocks ticket creation, and is never passed to a `pushEvent`
status or reason code.

**Drift check, at Finalize time.** `tools/gate_checks/done_checker_static.py::check_tag_drift()`
runs during the Finalize phase of `implement-ticket.js`, after `writeMonitoring('DONE')` and outside
`run_finalize_selfcheck`'s blocking checks. It derives candidate tags from the closing ticket's own
`Files Changed`/`Related Code Areas` body text (via `registry_query.py::candidate_tags_from_text()`)
and compares them against the ticket's declared `tags:` frontmatter. A candidate tag missing from
`tags:` produces a `FLAGGED` result with the candidate tag(s) named in the evidence; otherwise the
result is `CLEAN`. This mechanism uses `CLEAN`/`FLAGGED` — never `PASS`/`FAIL`/`NA` — specifically
so no downstream blocking-status consumer can misread it as a Definition-of-Done condition. A
`FLAGGED` result never changes the ticket's `DONE` status and never auto-adds or auto-removes a tag
— it is a log-only `WARNING` for human follow-up.
