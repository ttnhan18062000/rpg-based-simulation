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
underlying ticket data. Today there are three pillars built: tag-usage reporting, ticket-corpus
statistics (velocity, tier/type/priority/layer distribution, artifact completeness), and the
legacy corpus tag/category repair sweep (a full-corpus, no-date-cutoff violation report). The
structure below leaves room for more.

---

## Pillar 1: Tag Usage Reporting

**Tool:** [`tools/tag_report.py`](../../tools/tag_report.py)

### What it does

Counts how many completed tickets (`tickets/done/`) use each tag, and classifies each tag into
one of the 5 categories defined in
[`docs/guidelines/tag_taxonomy.md`](../guidelines/tag_taxonomy.md) (Subsystem/Topic,
Phase/Milestone, Process/Skill-signal, Quality-attribute, Meta-Process) by looking it up in
[`registries/tag_registry.jsonl`](../../registries/tag_registry.jsonl) — the append-only,
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
| *(registry lookup)* | Every other tag: whatever `category` field the matching entry in `registries/tag_registry.jsonl` carries — `subsystem-topic`, `process-skill-signal`, `quality-attribute`, or `meta-process` |
| `unclassified` | The tag isn't a phase tag and isn't in the registry — a data-integrity signal worth investigating (how did an unregistered tag get past `validate_frontmatter.py`'s hard allowlist?), not an expected steady state |

### Legacy / historical context

The taxonomy is very young — it did not exist before 2026-07-04, and the registry is younger still
(`TCK-20260706-TAG-REGISTRY-DATA`) — so on any given day, most `tickets/done/` files will be
skipped as pre-taxonomy. That is not a script bug; it reflects how recently the controlled
vocabulary was introduced. Numbers to keep in mind, all **dated snapshots that will shift** as more
post-cutoff tickets accumulate:

- **Pre-taxonomy corpus** (from `tag_taxonomy.md`'s original review, ticket `TCK-20260704-TAG-TAXONOMY`): 1001 tickets, 1273 distinct tags, 57.3% used exactly once, at least 19 confirmed format-duplicate groups (e.g. `p0`/`P0`, `phase-5`/`phase5`).
- **Live snapshot as of 2026-07-06** (`python3 tools/tag_report.py`): 1046 `.md` files scanned under `tickets/done/` → 1002 skipped as pre-taxonomy/legacy `ticket_id`, 12 skipped as `SEQUENCE.md`, 3 skipped as no-frontmatter → **29 tickets included**, spanning **37 unique tags**, all 37 now registered and classified (0 `unclassified`) after the registry was seeded from this exact live tag list. At the time, the tool's non-canonical diagnostic still caught 2 real historical-leakage cases the registry didn't fix by itself — `simulation_quality` (underscore form) — with retagging explicitly deferred as out of scope for the registry ticket.
- **`TCK-20260719-TAG-COLLISION-DEDUP`** (2026-07-19) closed that gap and 7 siblings found via a fresh full-corpus scan (`tickets/{done,inprogress,todos}/` + `stored_artifacts/`, not just `tickets/done/`): every literal-spelling duplicate of an already-meaningful tag — `simulation_quality`→`simulation-quality` (223 occurrences total once fully consolidated), `grand_strategy`→`grand-strategy`, `feature_flag`/`feature-flag`→`feature-flags`, `dungeon_crawl`→`dungeon-crawl`, `grade_thresholds`→`grade-thresholds` — was renamed to its canonical form (registering 3 previously-unregistered canonical forms in the process), and every forbidden `p0`/`p1`/`p2`-as-a-tag occurrence (duplicating the ticket's own dedicated `## Priority` field) was removed outright, per `docs/guidelines/tag_taxonomy.md`'s own "Forbidden Tags" policy. Fixed regardless of ticket date — a one-line `tags:` edit carries none of the structural-retrofit risk that otherwise motivates leaving pre-taxonomy tickets untouched. A fresh corpus-wide re-scan post-fix confirms zero remaining collision groups.

Use `python3 tools/tag_report.py --list-skipped` to see the actual skipped file paths if you need
to inspect the pre-taxonomy corpus directly (e.g. to spot more duplicate-group candidates for a
future taxonomy cleanup) — the tool does not aggregate tag counts for skipped tickets itself,
since that corpus was never governed by any vocabulary to begin with.

---

## Pillar 2: Ticket Corpus Statistics

**Tool:** [`tools/ticket_stats_report.py`](../../tools/ticket_stats_report.py)

### What it does

Covers four reporting angles over `tickets/done/` in one tool: ticket velocity/throughput (closed
tickets per day and per ISO-week, from `tickets/working_log.csv`), tier/type/priority distribution
(counts per canonical value, plus a non-canonical marker for anything outside
`tools/ticket_field_values.py`'s `TIER_VALUES`/`PRIORITY_VALUES`), layer distribution (counts per
value in `registries/layer_registry.jsonl`, same non-canonical marker), and artifact
completeness (for `standard`/`epic` tickets only, per this project's own hotfix-exemption: does
`stored_artifacts/{ticket_id}/` exist with all 3 required files — `investigation.md`, `plan.md`,
`test_plan.md`). Built by `TCK-20260718-TICKET-CORPUS-REPORT`, mirroring `tools/tag_report.py`'s
own shape (computation/rendering split, `--json` flag, dedicated test file, `make` target) —
that module is the direct precedent.

`docs/REGISTRY.yaml` is **not** a sufficient data source for this pillar by itself — its ticket
entries carry no `layer`, no `priority`, and no body `## Status`, confirmed directly during that
ticket's investigation — so this tool parses ticket files the same way
`tools/ticket_field_values.py`/the Agent Ops Dashboard's `ingest.py` already do, reusing
`validate_frontmatter.py::extract_frontmatter` and `generate_registry.py::parse_body_section`
rather than reimplementing either.

This pillar's numbers are also exposed as a typed JSON API route,
`GET /api/stats/tickets` (`TicketCorpusStats`), consumed by the Agent Ops Dashboard's Stats tab —
see [`docs/guides/agent_ops_dashboard.md`](agent_ops_dashboard.md#stats) and
[`docs/observability/agent_ops_dashboard_contract.md`](../observability/agent_ops_dashboard_contract.md).
The CLI and the API route compute from the exact same functions (`compute_velocity`,
`compute_distribution`, `compute_artifact_completeness`), so their numbers are always identical for
the same corpus state.

### Quick start

```bash
python3 tools/ticket_stats_report.py                                   # stdout summary
python3 tools/ticket_stats_report.py --json reports/ticket_stats.json  # write a structured report to disk

make ticket-stats-report                                                # same as the plain stdout form
make ticket-stats-report ARGS="--json reports/ticket_stats_report.json"
```

**Live snapshot as of 2026-07-18** (dated, will shift as the corpus grows): 1179 files scanned
under `tickets/done/`, 24 skipped as `SEQUENCE.md` → **1155 tickets included**. Tier: 931
`standard`, 103 `hotfix`, 81 non-canonical `unknown`, 40 `epic`. Priority: 798 `P1`, 237 `P2`, 71
non-canonical `unknown`, 25 `P0`, 24 `P3`. Layer: 19 distinct values, topped by `misc` (321) and
`engine` (206). Artifact completeness (`standard`/`epic` only): 624/971 complete.

### Technical detail

Scoped to `tickets/done/` only, matching `tag_report.py`'s own scope choice — the same
`SEQUENCE.md`-skip rule applies (folder index files are never counted as tickets). Velocity groups
`tickets/working_log.csv` rows by calendar day and by ISO-week (via
`tools/agent-monitoring/generate_retro.py::iso_week`, reused not reimplemented), tolerating
unparseable rows by counting and skipping them rather than crashing. Distribution counts use
`Counter`s over the three body-section fields (tier, ticket_type, priority) plus the frontmatter
`layer` field, cross-referenced against the canonical value sets so an out-of-registry value shows
as `unknown`/non-canonical instead of silently miscounting. Artifact completeness only checks
`standard`/`epic` tickets, since `hotfix` tickets are explicitly exempt from staging artifacts per
this project's own workflow rule (`CLAUDE.md`'s "Hotfix: No staging artifacts required").

---

## Pillar 3: Legacy Corpus Tag/Category Repair Sweep

**Tool:** [`tools/tag_corpus_sweep.py`](../../tools/tag_corpus_sweep.py)

### What it does

Both pillars above only ever look at `tickets/done/`, and Pillar 1's tag-usage report is further
narrowed to tickets whose `ticket_id` embeds a date on or after the tag taxonomy's effective date
(`TAG_TAXONOMY_EFFECTIVE_DATE`, 2026-07-04) — enforcement of the controlled vocabulary is
deliberately forward-only, per the taxonomy's own "no backfill of history" decision. That leaves a
large historic gap never checked by anything: everything predating the cutoff, plus
`tickets/inprogress/`, `tickets/todos/`, and `stored_artifacts/`, none of which Pillar 1 or 2 ever
walks.

This is a **report-only, no-date-cutoff** sweep across all four corpus roots —
`tickets/done/**`, `tickets/inprogress/**`, `tickets/todos/**`, and `stored_artifacts/**/*.md` —
built for `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`. Contrast this explicitly with Pillar 1: Pillar
1's `tag_report.py` skips any ticket whose `ticket_id` predates the taxonomy cutoff; this sweep
applies no such date gate anywhere — a 2026-01-01 ticket is checked exactly the same as one from
today. For every tag found in every file's `tags:` frontmatter list, it emits one `(file, tag,
issue)` row per applicable violation:

| Issue | Fires when |
|---|---|
| `unregistered` | The tag is not in [`registries/tag_registry.jsonl`](../../registries/tag_registry.jsonl) and is not a canonical `phase-N` tag |
| `invalid_category` | The tag **is** registered, but its recorded `category` is not one of the currently valid values in [`registries/tag_category_registry.jsonl`](../../registries/tag_category_registry.jsonl) — drift protection for a hand-edited registry or a category later deprecated, not something the live corpus is expected to trigger today (registries are append-only, so no category can currently become invalid after a tag was registered under it) |
| `non_canonical_form` | `canonical_form_violation(tag)` is not `None` (uppercase, underscore, forbidden priority tag, known non-canonical synonym) |

`unregistered` and `invalid_category` are mutually exclusive per tag — `invalid_category` only
fires for a tag with a literal registry entry, a strictly narrower condition than "registered at
all" (which also covers phase-N tags that have no registry entry to check a category against).
`non_canonical_form` is fully independent of the other two and can combine with either, so a tag
with multiple issues produces multiple rows for the same `(file, tag)` pair.

It never writes to any file it scans — there is no `--fix` flag, and no code path in this tool
ever calls `Path.write_text` against anything under `tickets/` or `stored_artifacts/`. Deciding
what to do with a finding (retag, register, or fix a legacy file) is left to a human or a
follow-up ticket.

### Quick start

```bash
python3 tools/tag_corpus_sweep.py                                    # stdout summary + row table
python3 tools/tag_corpus_sweep.py --json reports/tag_corpus_sweep.json  # write a structured report to disk
```

### Technical detail

The corpus walk (`collect_sweep_files`) and per-file classification (`tag_issues`,
`sweep_file_rows`) live in `tools/tag_report.py`, alongside Pillar 1's own functions, so both
reuse `tools/validate_frontmatter.py::extract_frontmatter` as the sole frontmatter parser (no
second parser) and the same `SEQUENCE.md`-skip convention — but `collect_sweep_files` applies
**only** that one skip rule (unlike `collect_completed_tickets`'s four), and `sweep_file_rows`
tolerates a missing frontmatter block, a missing `tags:` key, or unparseable frontmatter by
returning zero rows rather than crashing or skipping-and-counting. `tools/tag_corpus_sweep.py`
itself is a separate module holding only the orchestration (`run_sweep`) and CLI/output layer
(`print_report`, `build_json_report`, `main`) — it does not import, call, or modify Pillar 1's own
`main()`/`--json`/`--show-tickets`/`--list-skipped` CLI wiring, which stays scoped to its
narrower, already-shipped `tickets/done/`-only report.

**Live snapshot as of 2026-07-31** (dated, will shift as the corpus grows and as findings are
addressed): 4145 files scanned across all four roots, 37 skipped as `SEQUENCE.md`. 7832 violation
rows found: 7002 `unregistered`, 830 `non_canonical_form`, 0 `invalid_category` (expected — see
the table above).

---

## Related docs

- [`docs/guidelines/tag_taxonomy.md`](../guidelines/tag_taxonomy.md) — the controlled vocabulary this report classifies against
- [`docs/guides/ticket_tagging.md`](ticket_tagging.md) — practical tagging guide, skill-suggestion table
- [`docs/guides/simulation_quality.md`](simulation_quality.md) — the "pillars" framing this guide's structure borrows
