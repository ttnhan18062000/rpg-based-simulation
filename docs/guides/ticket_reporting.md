---
status: active
layer: guidelines
authority: P2
audience: developer
tags: [tagging, reporting, guide]
---

# Ticket Reporting — Getting Started Guide

This guide covers reporting tools that read `tickets/`, `docs/REGISTRY.yaml`, and
`tickets/working_log.csv` to answer questions about the ticket corpus itself (not about a
simulation run — see [`simulation_quality.md`](simulation_quality.md) for that). Like SimQ's
scoring surface, this is organized as **pillars** — independent reporting angles over the same
underlying ticket data. Today there is exactly one pillar built: tag-usage reporting. The
structure below leaves room for more.

---

## Pillar 1: Tag Usage Reporting

**Tool:** [`tools/tag_report.py`](../../tools/tag_report.py)

### What it does

Counts how many completed tickets (`tickets/done/`) use each tag, and classifies each tag into
one of the 5 categories defined in
[`docs/guidelines/tag_taxonomy.md`](../guidelines/tag_taxonomy.md) (Subsystem/Topic,
Phase/Milestone, Process/Skill-signal, Quality-attribute, Meta-Process) by looking it up in
[`docs/guidelines/tag_registry.jsonl`](../guidelines/tag_registry.jsonl) — the append-only,
machine-readable tag data file `tools/tag_registry.py` manages (`TCK-20260706-TAG-REGISTRY-DATA`).
A tag only shows as `unclassified` if it somehow isn't registered, which should be rare going
forward: `validate_frontmatter.py`'s hard allowlist rejects an unregistered tag at commit time. It
also flags non-canonical tag usage (uppercase, underscores, forbidden priority tags, known
non-canonical synonyms) among the tickets it counts, as a data-quality diagnostic.

### Quick start

```bash
python3 tools/tag_report.py                                  # stdout summary + tag table
python3 tools/tag_report.py --show-tickets                   # also list ticket IDs per tag
python3 tools/tag_report.py --list-skipped                   # list which files were skipped, and why
python3 tools/tag_report.py --json reports/tag_report.json    # write a structured report to disk

make tag-report                                               # same as the plain stdout form
make tag-report ARGS="--json reports/tag_report.json"
```

### Technical detail

The tool walks `tickets/done/` recursively (it does pick up the small number of ticket files that
live directly under `tickets/done/{folder}/` subfolders, not just the flat top level) and applies
3 skip rules, in order, before a ticket's tags are counted:

| Order | Skip reason | Condition |
|---|---|---|
| 1 | `sequence_index_file` | The file is `SEQUENCE.md` — a folder index, not a ticket |
| 2 | `no_frontmatter_legacy_format` / `unparseable_frontmatter` | No YAML frontmatter block, or it fails to parse |
| 3 | `pre_taxonomy_or_legacy_ticket_id` | `ticket_id` is missing/unparseable, or its embedded `TCK-YYYYMMDD-...` date is before the taxonomy's effective date (`2026-07-04`, see `tag_taxonomy.md`'s Enforcement section) |
| 4 | `no_tags` | `tags` is missing or an empty list |

This mirrors `tools/validate_frontmatter.py`'s own enforcement cutoff exactly (imported, not
reimplemented), so "included in this report" always means the same thing as "subject to taxonomy
enforcement" — there is one definition of "too old to count," not two.

Tag classification (`categorize_tag(tag, registry)`):

| Category | Rule |
|---|---|
| `phase-milestone` | Matches `^phase-\d+$` — recognized by pattern, never looked up (see `tag_taxonomy.md`'s Tag Registry section for why phase tags aren't individually registered) |
| *(registry lookup)* | Every other tag: whatever `category` field the matching entry in `docs/guidelines/tag_registry.jsonl` carries — `subsystem-topic`, `process-skill-signal`, `quality-attribute`, or `meta-process` |
| `unclassified` | The tag isn't a phase tag and isn't in the registry — a data-integrity signal worth investigating (how did an unregistered tag get past `validate_frontmatter.py`'s hard allowlist?), not an expected steady state |

### Legacy / historical context

The taxonomy is very young — it did not exist before 2026-07-04, and the registry is younger still
(`TCK-20260706-TAG-REGISTRY-DATA`) — so on any given day, most `tickets/done/` files will be
skipped as pre-taxonomy. That is not a script bug; it reflects how recently the controlled
vocabulary was introduced. Numbers to keep in mind, all **dated snapshots that will shift** as more
post-cutoff tickets accumulate:

- **Pre-taxonomy corpus** (from `tag_taxonomy.md`'s original review, ticket `TCK-20260704-TAG-TAXONOMY`): 1001 tickets, 1273 distinct tags, 57.3% used exactly once, at least 19 confirmed format-duplicate groups (e.g. `p0`/`P0`, `phase-5`/`phase5`).
- **Live snapshot as of 2026-07-06** (`python3 tools/tag_report.py`): 1046 `.md` files scanned under `tickets/done/` → 1002 skipped as pre-taxonomy/legacy `ticket_id`, 12 skipped as `SEQUENCE.md`, 3 skipped as no-frontmatter → **29 tickets included**, spanning **37 unique tags**, all 37 now registered and classified (0 `unclassified`) after the registry was seeded from this exact live tag list. The tool's non-canonical diagnostic still catches 2 real historical-leakage cases the registry doesn't fix by itself: `simulation_quality` (underscore form) used on 2 tickets — the canonical `simulation-quality` is registered as the correct replacement, but retagging those 2 tickets is out of scope for the registry ticket, same as it was for the original tag-report ticket.

Use `python3 tools/tag_report.py --list-skipped` to see the actual skipped file paths if you need
to inspect the pre-taxonomy corpus directly (e.g. to spot more duplicate-group candidates for a
future taxonomy cleanup) — the tool does not aggregate tag counts for skipped tickets itself,
since that corpus was never governed by any vocabulary to begin with.

---

## Other candidate pillars (not built)

Documented here only to explain why this guide is structured as "pillars" rather than a single
flat tool doc — none of the below are scoped, promised, or in progress:

- **Ticket velocity / throughput** — derived from `tickets/working_log.csv` timestamps (tickets
  closed per day/week, by tier or layer).
- **Tier / type / priority distribution** — how many `hotfix` vs `standard` vs `epic` tickets,
  bug vs feature vs refactor, P0/P1/P2 mix, over time.
- **Layer distribution** — cross-tab of `layer` against tier/type, using the same
  `docs/REGISTRY.yaml` data source `tools/registry_query.py` already reads.
- **Artifact completeness** — how many `standard`/`epic` tickets have a matching
  `stored_artifacts/{ticket_id}/` folder with all 3 required files, vs. gaps.

If one of these is ever wanted, it likely belongs as a new `tools/*_report.py` script following
the same pattern as `tools/tag_report.py` (reuse `validate_frontmatter.py`/`generate_registry.py`
parsing, dedicated test file, `make` target) — not folded into `tag_report.py` itself.

---

## Related docs

- [`docs/guidelines/tag_taxonomy.md`](../guidelines/tag_taxonomy.md) — the controlled vocabulary this report classifies against
- [`docs/guides/ticket_tagging.md`](ticket_tagging.md) — practical tagging guide, skill-suggestion table
- [`docs/guides/simulation_quality.md`](simulation_quality.md) — the "pillars" framing this guide's structure borrows
