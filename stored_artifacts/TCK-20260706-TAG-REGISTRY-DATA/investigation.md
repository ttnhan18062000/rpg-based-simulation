---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260706-TAG-REGISTRY-DATA
artifact_type: investigation
tags: [tagging, taxonomy, reporting]
---

# Investigation — TCK-20260706-TAG-REGISTRY-DATA

## Request

Follow-up to `TCK-20260706-TAG-REPORT-TOOL`/`TCK-20260706-TICKET-REPORTING-GUIDE`. User noted that
`tag_report.py`'s live output showed most tags as `unclassified` (heuristic categorization only
covered a hardcoded example list per category) and asked for:

1. A machine-readable "total available tag data" file (JSON-ish, processing-first not
   human-readability-first).
2. That data avoids near-duplicate-meaning tags (`calibrate` vs `calibration`).
3. Tags can only be **added**, never updated/deleted, with a changelog.
4. Ticket tagging validation should use that data file.
5. Category itself should also be managed as data if needed, since most tags are `unclassified`
   today.
6. Explicit instruction: **ask before deciding** on the ambiguous points.

## Clarifying decisions (asked via AskUserQuestion, all 4 recommended options chosen)

1. **Enforcement: hard allowlist.** `validate_frontmatter.py` now rejects any non-`phase-N` tag not
   present in the registry, not just a soft/advisory lookup.
2. **Add mechanism: dedicated CLI.** `tools/tag_registry.py add <tag> --category <cat> --note
   "..."` is the only sanctioned way to register a tag.
3. **Bootstrapping: seed now, categorized.** The registry is seeded from every tag in use across
   the (at-investigation-time) 27 post-taxonomy tickets, each assigned a category for review.
4. **5th category: yes.** `meta-process`, for tags about the ticket/agent-workflow process itself.

## Current behavior (before this ticket)

- `tools/validate_frontmatter.py`'s `_check_tags()` only checked: forbidden priority tags
  (`p0`/`p1`/`p2`), canonical form (lowercase/hyphenated), known non-canonical synonyms
  (`TAG_SYNONYM_MAP`). It never checked whether a tag's *meaning* already existed under a different
  spelling — two canonical-form tags with the same intent (`calibrate` vs `calibration`) would both
  pass silently.
- `tools/tag_report.py`'s `categorize_tag()` matched against 3 small hardcoded example sets
  (`PROCESS_SKILL_TAGS` = 4 tags, `QUALITY_ATTRIBUTE_EXAMPLE_TAGS` = 4 tags,
  `registry_query.SEED_TAGS` = 10 tags) — anything else fell through to `unclassified`. Live run
  before this ticket: 32 of 36 unique tags (89%) were `unclassified`.
- No durable, machine-readable single source of truth existed for "which tags are known to exist
  and what do they mean" — only prose examples in `tag_taxonomy.md`.

## Evidence gathered for category assignment

Grepped `tickets/done/*.md` for each ambiguous live tag's actual usage context before assigning a
category, rather than guessing from the tag name alone (`grep -l "^tags:.*\btag\b" tickets/done/*.md`
then reading each matching ticket's `## Title`):

- `rollback`, `audit-trail`, `knowledge-store` — all trace to "Add a real revert mechanism for
  `UpdateSimulationKnowledgeWorkflow`" and "Fix hardcoded fake timestamps in
  `UpdateSimulationKnowledgeWorkflow`" — agent-tooling revert/audit capability, not a gameplay or
  world rollback. Classified `meta-process`, not `subsystem-topic`/`quality-attribute` as an
  uninvestigated guess would have placed them.
- `stasis`, `resource-registry`, `agency`, `ecology` — confirmed via ticket titles as genuine
  gameplay/SimQ concepts (economic/behavioral stasis, `ResourceRegistry` crash fix, SimQ Agency
  pillar, world/resource ecology regeneration). Classified `subsystem-topic`.
- `root-cause` — traces to "Investigate and harden against run_id/event join mismatches" —
  investigation *methodology*, not a named skill gate (`debugging` already exists as
  `process-skill-signal` for that). Classified `meta-process`.
- `ai` — **important correction to an initial assumption.** Grepping its usages
  (`docs/ai/workflows.md`'s stale-phase-list fix, gate-check tickets for architecture-reviewer/
  parity-updater/done-checker/mechanics-auditor, "Write a single consolidated technical overview
  document for the AI agent system") confirmed that in this repo, `layer: ai` and an `ai` tag refer
  to the **Claude agent-orchestration system** (`docs/ai/*`), not gameplay AI/cognition — that
  concept is tracked separately under `strategy` layer / `cognition` tag. Classified `meta-process`,
  reversing an initial guess of `subsystem-topic`.
- `data-quality`, `determinism`, `schema`, `calibration` — grepped and confirmed: `data-quality`
  traces exclusively to agent-monitoring/reporting-pipeline fixes (`generate_retro.py`,
  `validate.py`, `working_log.csv`) → `meta-process`. `determinism` spans many engine/kernel
  hardening tickets, closely matching `tag_taxonomy.md`'s own "Hardened"/"Enforced" divergence-class
  language → `quality-attribute`. `schema` and `calibration` were already named as explicit
  `tag_taxonomy.md` worked examples → `quality-attribute`, honored as-is.

Final seed: 8 `subsystem-topic`, 3 `quality-attribute`, 1 `process-skill-signal`, 25 `meta-process`
(24 identified during investigation + `reporting`, discovered missing only after re-running
`tag_report.py` post-seed — see Implementation Notes) = 37 tags total, all traced to real ticket
evidence, none invented speculatively.

## Existing code reused (no duplicated logic)

- `tools/validate_frontmatter.py`'s `extract_frontmatter`, canonical-form logic (previously inline
  in `_check_tags`, now extracted).
- `tools/generate_registry.py`'s same-package `sys.path.insert` + `from X import Y` pattern for
  cross-module imports within `tools/` (not a real installed package).
- Precedent from `TCK-20260705-TAG-REGISTRY-QUERY`: same import style, same "read-only reference,
  no dependency in the reverse direction" discipline used to avoid an import cycle here (see
  plan.md's Import Direction Decision).

## Risk assessment before implementation

Turning `validate_frontmatter.py`'s tag check into a hard allowlist is the highest-risk part of
this ticket — it changes a hard-fail CI/workflow gate. Mitigation planned and executed (see
test_plan.md and the ticket's Test Summary): seed the registry from *every* tag actually in use
across post-cutoff tickets before flipping enforcement on, then diff a full
`validate_frontmatter.py tickets/done` run against an unmodified-tree baseline (via `git stash`) to
confirm the violation count is identical.
