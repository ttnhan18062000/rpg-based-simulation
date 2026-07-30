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

This document defines a **controlled vocabulary of categories and canonical-form rules**. Until
`TCK-20260706-TAG-REGISTRY-DATA`, that vocabulary was deliberately open-ended — categories and
canonical-form rules only, not a closed list of every valid tag. It is now backed by a concrete,
append-only data file, `registries/tag_registry.jsonl` (managed by `tools/tag_registry.py`),
which **is** an enumeration: every tag used on a ticket/artifact created on or after the
enforcement cutoff must be registered there first. See [Tag Registry](#tag-registry) below for why
and how. A clean vocabulary is a prerequisite for tags becoming an actual routing signal later
(skill suggestion, gate routing, retro grouping); this document does not build any of that
consumption logic itself. Each future scenario below names which category its routing logic would
eventually read:

| Scenario | Category it reads |
|---|---|
| 1. Tag-driven skill suggestion | Process/Skill-signal |
| 2. Tag-driven gate routing | Process/Skill-signal |
| 3. Cross-cutting discovery beyond `layer` | Subsystem/Topic |
| 4. Retro/analytics grouping | Subsystem/Topic (primary), Process/Skill-signal (skill-specific gate failures) |
| 5. Automatable skill-catalog health check | Process/Skill-signal — built: `tools/tag_skill_mapping_check.py` (extraction/comparison logic), run via `tests/tools/test_tag_skill_mapping_check.py` (`python3 -m pytest tests/tools/test_tag_skill_mapping_check.py -q`) |

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

### Meta-Process

Tags about the ticket/agent-workflow process itself, not about simulation gameplay, an engine
subsystem, a skill gate, or a change's nature — e.g. `workflows`, `agent-monitoring`,
`documentation`, `tagging`, `investigation`, `retro`, `frontmatter`. Added alongside the tag
registry (`TCK-20260706-TAG-REGISTRY-DATA`): seeding the registry from the live corpus found the
large majority of in-use tags were exactly this kind of tag — evidence that they were never a bad
fit for the original 4 categories, they were simply a 5th, undocumented one. Note that `layer: ai`
in this repo also means this domain (`docs/ai/` is the Claude agent-orchestration system, not
gameplay AI/cognition — that lives under `strategy`/`cognition` instead), so an `ai` tag is
Meta-Process, not Subsystem/Topic.

**Disambiguation rule** (Meta-Process vs. Subsystem/Topic): if the tag names something a player or
the simulation engine would recognize (a gameplay subsystem, an engine capability), it is
Subsystem/Topic. If it names something only a developer or agent working *on* the ticket/tooling
system would recognize, it is Meta-Process. For example, `resource-registry` (a gameplay system)
is Subsystem/Topic, while `registry` (referring to `docs/REGISTRY.yaml` tooling) is Meta-Process.

## Forbidden Tags

`p0`, `p1`, `p2` (any case: `P0`, `P1`, `P2`) are never valid tags. This information already lives
in the ticket's dedicated `## Priority` field — a tag duplicating it is pure redundancy, not a
taxonomy gap to fill.

**Open question, not decided here:** the same redundancy argument may apply to `bug` (registered
today as Meta-Process, `TCK-20260706-TAG-REGISTRY-DATA` seed) and other tags naming a ticket's
`## Type` value (`feature`, `refactor`, `chore`, `repair`) — that field already exists for exactly
this purpose. Flagged for a future decision rather than forbidden unilaterally here, since
forbidding it retroactively would fail the 3 existing tickets already using it.

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
groups). Do not use it to pre-enumerate every subsystem tag. 1273 pre-registry tags include a
large amount of legitimately one-off, ticket-specific detail that was never evidence of a missing
category — the same principle now applies to the registry: a tag not yet registered is not
necessarily wrong, it may just not have been needed yet (see [Tag Registry](#tag-registry)).

## Tag Registry

`registries/tag_registry.jsonl` is the machine-readable, **append-only** enumeration of every
tag a ticket/artifact is allowed to use, going forward. Each line is one JSON object, one tag,
registered exactly once:

```json
{"tag": "faction", "category": "subsystem-topic", "added_date": "2026-07-06", "note": "..."}
```

**Why a registry, not just canonical-form rules:** canonical-form rules alone (lowercase,
hyphenated, no known synonym) cannot catch a *new* near-duplicate of an existing tag's *meaning*
(e.g. `calibrate` alongside the already-registered `calibration`) — both are perfectly canonical
form, just two different words for the same thing. A registry that must be checked against (not
just pattern-matched) is what closes that gap.

**Append-only, by design:** `tools/tag_registry.py`'s CLI has no `update` or `delete` command — the
only way to change what a tag means is to stop using it and register a different one; the file
itself, plus its own git history, is the changelog (no separate changelog file to keep in sync by
hand). Registering a tag that already exists is rejected.

**How to register a new tag:**

```bash
python3 tools/tag_registry.py add <tag> --category <category> --note "why this tag exists"
python3 tools/tag_registry.py list   # see everything currently registered
```

`<category>` must be one of `subsystem-topic`, `process-skill-signal`, `quality-attribute`,
`meta-process` (`phase-milestone` is deliberately not addable this way — see below). `<tag>` must
already be in canonical form; the tool rejects the same violations `validate_frontmatter.py` would.

**`phase-N` tags are exempt from registration:** `phase-5`, `phase-12`, etc. are recognized
automatically by pattern (`^phase-\d+$`) rather than requiring every phase number to be registered
individually — registering an open-ended, ever-growing numeric series one value at a time would
defeat the point of an append-only file staying small and readable.

See `docs/guides/ticket_tagging.md` for a walkthrough of when and how to add a tag in practice, and
`tools/tag_report.py` (`docs/guides/ticket_reporting.md`) for a usage-frequency report over
whatever is currently registered.

## Enforcement

Enforcement is **forward-only** from `2026-07-04`: `tools/validate_frontmatter.py` only applies
tag checks to tickets/artifacts whose `ticket_id` embeds a date (`TCK-YYYYMMDD-...`) on or after
this date. Tickets and artifacts predating this taxonomy are intentionally not backfilled or
re-validated, so a whole-directory validation run does not newly fail on historical tags.

For tickets/artifacts within scope, two checks now apply, in order: canonical form (as above), then
**registry membership** — `validate_frontmatter.py` loads `registries/tag_registry.jsonl` and
rejects any canonical-form tag that isn't registered there (except `phase-N` tags, always allowed).
This is a **hard allowlist**: a genuinely new tag must be registered via `tools/tag_registry.py add`
before it can be used on any ticket/artifact. Confirmed to introduce zero new regressions against
the existing corpus: seeding the registry from every tag already in use across the 27 (at the time)
post-cutoff tickets, then re-running `validate_frontmatter.py tickets/done`, produced the identical
185-violation count as the unmodified tree — the only 2 tag-related failures already existed before
the registry (a non-canonical `simulation_quality` usage, unrelated to registration).

Violations are a hard rejection (exit 1), the same severity as every other frontmatter field
(`status`, `layer`, `authority`, `audience`, `phase`, `artifact_type`) — not a separate warn-only
path.

This taxonomy applies to `ticket` and `artifact` content types only. `doc`-type frontmatter's
`tags` field remains free-form and unvalidated (see `docs/guidelines/frontmatter_schema.md`) — the
registry does not apply there either.
