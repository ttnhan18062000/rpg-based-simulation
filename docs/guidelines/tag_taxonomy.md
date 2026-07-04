---
status: active
layer: guidelines
authority: P1
audience: developer
---

# Tag Taxonomy

## Purpose

`tags` on ticket and artifact frontmatter have always been free text. A corpus review across
1001 tickets in `docs/REGISTRY.yaml` found 1273 distinct tags, 57.3% of them used exactly once,
plus at least 19 confirmed format-duplicate groups (`p0`/`P0`, `phase-5`/`phase5`,
`simulation_quality`/`simulation-quality`, etc.).

This document defines a **controlled vocabulary of categories and canonical-form rules** — not a
frozen enumeration of every valid tag. A clean vocabulary is a prerequisite for tags becoming an
actual routing signal later (skill suggestion, gate routing, retro grouping); this document does
not build any of that consumption logic itself. Each future scenario below names which category
its routing logic would eventually read:

| Scenario | Category it reads |
|---|---|
| 1. Tag-driven skill suggestion | Process/Skill-signal |
| 2. Tag-driven gate routing | Process/Skill-signal |
| 3. Cross-cutting discovery beyond `layer` | Subsystem/Topic |
| 4. Retro/analytics grouping | Subsystem/Topic (primary), Process/Skill-signal (skill-specific gate failures) |
| 5. Automatable skill-catalog health check | Process/Skill-signal |

## Categories

### Subsystem/Topic

Names a subject-matter area a ticket or artifact touches: `combat`, `economy`, `cognition`,
`faction`, `resource`, `social`, `content`, `world`, `engine`, `strategy`, ...

Canonical form: lowercase, hyphen-separated, no underscores.

This is a deliberately finer-grained, sometimes cross-cutting complement to `layer`'s 19-value
enum, not a duplicate of it. `layer` is coarse by design — a topic like `faction` genuinely spans
the `ai`, `systems`, and `social` layers, and `layer`-only search can't find "everything about
factions" in one query the way a clean `faction` tag can.

### Phase/Milestone

Marks a ticket/artifact as belonging to a numbered phase or milestone. Canonical format is
`phase-N` (e.g. `phase-5`), never `phaseN`.

### Process/Skill-signal

Tags whose canonical spelling matches an existing or clearly nameable skill/process gate 1:1 —
e.g. `api-design`, `performance`, `debugging`, `security`. This category exists specifically to
serve future scenarios 1-2 (tag-driven skill suggestion, tag-driven gate routing): its canonical
tag names are chosen to line up with the skill/process they would eventually trigger, so a later
routing table is a lookup, not a re-mapping exercise.

### Quality-attribute

Cross-cutting characterizations of a change's *nature*, not tied to a specific skill or process —
e.g. `hardening`, `calibration`, `schema`, `audit`. This category models on `CLAUDE.md`'s
Intentional Divergences rationale classes (`Hardened`/`Enforced`/`Unified`/`Stabilized`/`Bounded`/
`Bug Fix`/`Intentional Gameplay Change`).

**Disambiguation rule** (Process/Skill-signal vs. Quality-attribute): a tag belongs in
Process/Skill-signal only if it names an existing or clearly nameable skill/process gate 1:1;
otherwise, if it characterizes the nature of a change, it is Quality-attribute. For example,
`hardening` describes *how* a change was made (Quality-attribute), while `security` names the
`security-review` skill (Process/Skill-signal).

## Forbidden Tags

`p0`, `p1`, `p2` (any case: `P0`, `P1`, `P2`) are never valid tags. This information already lives
in the ticket's dedicated `## Priority` field — a tag duplicating it is pure redundancy, not a
taxonomy gap to fill.

## Canonical-Form Rules

- Lowercase only — no uppercase characters (`Combat` → `combat`).
- Hyphen-separated — no underscores (`simulation_quality` → `simulation-quality`).
- Phase tags use `phase-N`, never `phaseN` (`phase5` → `phase-5`).
- The following run-together compounds and abbreviations have no separator character for the
  general rule above to normalize mechanically, so they are listed explicitly:

| Non-canonical | Canonical |
|---|---|
| `obs` | `observability` |
| `cog` | `cognition` |
| `sim` | `simulation` |
| `worldmodules` | `world-modules` |
| `selfmodel` | `self-model` |
| `datamodel` | `data-model` |
| `worldspec` | `world-spec` |

This list is intentionally small and evidence-based (derived from confirmed corpus duplicate
groups). Do not use it to pre-enumerate every subsystem tag — the taxonomy defines categories and
canonical-form rules, not a closed list of every valid tag. 1273 existing tags include a large
amount of legitimately one-off, ticket-specific detail that is not evidence of a missing category.

## Enforcement

Enforcement is **forward-only** from `2026-07-04`: `tools/validate_frontmatter.py` only applies
tag checks to tickets/artifacts whose `ticket_id` embeds a date (`TCK-YYYYMMDD-...`) on or after
this date. Tickets and artifacts predating this taxonomy are intentionally not backfilled or
re-validated, so a whole-directory validation run does not newly fail on historical tags.

Violations are a hard rejection (exit 1), the same severity as every other frontmatter field
(`status`, `layer`, `authority`, `audience`, `phase`, `artifact_type`) — not a separate warn-only
path.

This taxonomy applies to `ticket` and `artifact` content types only. `doc`-type frontmatter's
`tags` field remains free-form and unvalidated (see `docs/guidelines/frontmatter_schema.md`).
