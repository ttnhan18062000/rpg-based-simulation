---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE
phase: done
date: 2026-07-18
tags: [documentation, claude-md]
---

# TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE

## Title
Update agent-facing docs/rules to describe the new canonical Tier/Layer/Status/Priority mechanism

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The user explicitly asked: "remember to update related agent's settings
like skills/rules/workflows/etc." Once TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM,
TCK-20260718-LAYER-REGISTRY-CONVERSION, and TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL
land, several places that currently describe Tier/Layer/Priority/Status
informally, incompletely, or not at all need to be brought up to date — both
so future agent sessions understand the real mechanism (not just tribal
knowledge in a closed ticket's Implementation Notes) and so the Layer-vs-Tag
distinction the user asked about is documented somewhere durable, not just
explained once in conversation.

**Amended mid-epic**: the Layer-vs-Tag contrast changed shape partway
through this epic. `Layer` was originally going to stay a hardcoded Python
enum (`LAYER_VALUES` in `validate_frontmatter.py`), contrasted against
`Tag`'s open, registry-backed taxonomy — i.e. "hardcoded enum vs. open
registry." The user then explicitly asked for `Layer` to also become
registry-backed (`TCK-20260718-LAYER-REGISTRY-CONVERSION`:
`docs/guidelines/layer_registry.jsonl` + `tools/layer_registry.py`,
structurally mirroring `tag_registry.py`). So the real, final contrast this
ticket must document is no longer "enum vs. registry" — **both `Tier`
(remains a small, code-level enum — no registry, low cardinality, unlikely
to grow) and `Layer`/`Tag` (both registry-file-backed, append-only,
CLI-managed) exist**, and the meaningful axis distinguishing `Layer` from
`Tag` is **cardinality and curation, not mechanism**: `Layer` is
single-value-per-ticket and curated (no category split — it IS the
subsystem-topic dimension), `Tag` is multi-value-per-ticket and
categorized into 4 taxonomy types. Do not describe the old "hardcoded enum
vs. open registry" framing anywhere in this ticket's output — it is now
inaccurate.

## Scope
- Investigate which `.claude/agents/*.md` role files actually need updates
  (a preliminary grep found `done-checker.md`, `ticket-scoper.md`,
  `concern-investigator.md`, `architecture-reviewer.md`,
  `parity-updater.md`, `simulation-analyst.md` all mention tier/priority
  somewhere — investigate whether each one's existing mention is already
  accurate/generic enough to not need a change, versus one that would give
  wrong guidance now that Tier/Priority are hard-validated; only touch the
  ones that actually need it, do not reflexively edit all six).
- Update `tools/validate_frontmatter.py`'s module docstring/header comment
  if it currently implies it is the only source of ticket-field validation
  (it validates frontmatter only; body-section Tier/Priority/Status
  validation now lives in the new module from
  TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM — the docstring should make this
  split clear so a future reader doesn't assume one module owns everything).
- Consider whether `docs/guidelines/` needs a new short doc (parallel to
  `docs/guidelines/tag_taxonomy.md`) explaining the Tier/Layer/Status/
  Priority canonical-value system and the real, final Layer-vs-Tag
  distinction (cardinality/curation, not mechanism — both are now
  registry-backed; see Request Summary's amendment) — investigate whether
  this is worth a new file or better folded into an existing doc (e.g.
  `docs/guidelines/design_patterns.md` or `CLAUDE.md` itself); do not create
  a new doc file reflexively if an existing one is a better, less
  fragmenting home.
- Confirm `CLAUDE.md`'s new Layer-registry paragraph (added by
  TCK-20260718-LAYER-REGISTRY-CONVERSION, mirroring the existing
  Tags-allowlist paragraph) reads well alongside that existing Tags
  paragraph — investigate whether the two paragraphs should be merged into
  one "registry-backed fields" explanation or are clearer kept separate;
  this ticket should not redo TCK-20260718-LAYER-REGISTRY-CONVERSION's own
  writing, only polish/verify the result reads coherently once both
  paragraphs exist side by side.
- Confirm `CLAUDE.md`'s Ticket Format Priority-line fix from
  TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM actually landed (this ticket
  should not re-do that fix, only verify it and handle anything that ticket
  didn't cover).

## Out of Scope
- Any code change — this ticket is documentation-only.
- Re-litigating the enum/validation design itself (already decided and
  implemented by the two prerequisite tickets).

## Acceptance Criteria
- [ ] Every `.claude/agents/*.md` file that gave now-inaccurate guidance
      about Tier/Priority (e.g. implying they're unvalidated free text) is
      corrected; files whose existing mention needed no change are left
      alone, with the investigation's reasoning for each documented in this
      ticket's Implementation Notes.
- [ ] `tools/validate_frontmatter.py`'s docstring accurately describes its
      own scope (frontmatter fields only) relative to the new body-section
      check module.
- [ ] A decision (create new doc / extend existing doc / neither needed) is
      made and documented for the Layer-vs-Tag explanatory doc question,
      with reasoning.
- [ ] `CLAUDE.md`'s Priority line is confirmed correct (`P0 | P1 | P2 | P3`).

## Related Tickets
- Parent epic: TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC
- Depends on: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM,
  TCK-20260718-LAYER-REGISTRY-CONVERSION,
  TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL

## Related Docs
- CLAUDE.md
- tools/validate_frontmatter.py
- docs/guidelines/tag_taxonomy.md
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/agents/done-checker.md
- .claude/agents/ticket-scoper.md
- .claude/agents/concern-investigator.md
- .claude/agents/architecture-reviewer.md
- .claude/agents/parity-updater.md
- .claude/agents/simulation-analyst.md
- tools/validate_frontmatter.py
- CLAUDE.md

## Assumptions / Open Questions
- Whether a new `docs/guidelines/` doc is warranted vs. folding into an
  existing one — left for this ticket's own investigation to decide.

## Implementation Notes

Same execution-context deviation as the rest of this epic (no Agent tool
access — self-flagged per established precedent). This is the final ticket
in the epic, so its own job is largely verifying and correcting what the
prior 4 left behind — see investigation.md for the full per-file
reasoning on what needed a change vs. what was investigated and correctly
left alone.

Fixed: `done-checker.md`'s static-check mapping table (missing the 6th
`ticket_field_values_valid` condition) and checklist #3's own text;
`ticket-scoper.md`'s Priority guidance (missing P3) and Layer guidance (no
registry mention); 3 `.claude/workflows/*.js` files' identical stale
`LAYER_VALUES in tools/validate_frontmatter.py` placeholder text
(`create-tickets.js`, `simq-audit.js`, `implement-ticket.js` — verified
`node --check` clean after each edit); both dashboard docs' "statuses is
the one exception" language, now describing the real final state (4 of 5
facets canonical, only `tags` corpus-derived) instead of 2 separate stale
single-facet callouts.

Investigated and correctly left alone: `parity-updater.md`'s `priority: P0
| P1 | P2` (confirmed via a direct scan of `infrastructure.yaml` —
`Counter({'P0': 178, 'P1': 82, 'P2': 23})`, zero P3s — this is genuinely a
different P0-P2 scale, the parity ledger entry's own priority field, not
ticket-body Priority); `architecture-reviewer.md`/`simulation-analyst.md`
(no enum claim at all in their tier/priority mentions);
`concern-investigator.md`'s narrower `tier_recommendation`
(hotfix/standard only, by design — this agent never recommends epic
directly) and its `priority_hint` (a hint field feeding
`create-tickets.js`'s own Structure-phase mapping, not itself validated
against `PRIORITY_VALUES` — left untouched to avoid unrelated coupling,
noted as a candidate for a future, separately-scoped ticket if ever
warranted); `tools/validate_frontmatter.py`'s docstring (already correctly
scoped to "YAML frontmatter," never claimed to own body-section
validation).

Layer-vs-Tag doc decision: **no new `docs/guidelines/` file created** —
folded into `CLAUDE.md`, which `TCK-20260718-LAYER-REGISTRY-CONVERSION`
already extended with a full explanatory paragraph. A new standalone doc
would either duplicate that content or fragment the single most-read
instruction file into two cross-referenced places.

Final completeness check: grepped `.claude/` and `docs/` for both stale
patterns (`LAYER_VALUES in tools/validate_frontmatter`, and non-P3 `P0 |
P1 | P2`) — zero remaining stale `LAYER_VALUES` references; the only
remaining `P0 | P1 | P2` hits are the 3 already-confirmed-correct
parity-ledger-scale references.

## Test Summary

- `python3 -m pytest tests/tools/test_done_checker_static.py
  tests/tools/test_ticket_field_values.py tests/tools/test_layer_registry.py
  tests/tools/test_validate_frontmatter.py -q` — 164/164 passing (this
  ticket touches no code, this is a pure regression guard).
- `node --check` on all 3 edited `.claude/workflows/*.js` files — all
  syntactically valid.
- `python3 tools/validate_frontmatter.py --content-type doc
  docs/observability/agent_ops_dashboard_contract.md` /
  `docs/guides/agent_ops_dashboard.md` — both `OK: no violations`.
- Completeness grep (see Implementation Notes) — 0 remaining stale
  references of either pattern.

## Files Changed
- .claude/agents/done-checker.md (static-check mapping table +
  checklist #3 text)
- .claude/agents/ticket-scoper.md (Priority/Layer guidance, frontmatter
  template placeholder)
- .claude/workflows/create-tickets.js (stale layer placeholder text)
- .claude/workflows/simq-audit.js (stale layer placeholder text)
- .claude/workflows/implement-ticket.js (stale layer placeholder text)
- docs/observability/agent_ops_dashboard_contract.md (facets paragraph
  rewritten for the final canonical state)
- docs/guides/agent_ops_dashboard.md (facets paragraph rewritten for the
  final canonical state)

## Completion Summary
All acceptance criteria met: every `.claude/agents/*.md` file that gave
now-inaccurate guidance was corrected (2 of 6), the other 4 investigated
and confirmed correct as-is with reasoning documented; the 3
`.claude/workflows/*.js` files sharing the same stale Layer text
(explicitly covered by the user's "workflows" mention) were also fixed;
`validate_frontmatter.py`'s docstring confirmed already-accurate;
Layer-vs-Tag documentation decision made (fold into CLAUDE.md, no new
file) and already executed by the prerequisite ticket;
`CLAUDE.md`'s Priority line confirmed correct. This closes out the epic —
all 5 child tickets (TIER-PRIORITY-CANONICAL-ENUM, TIER-PRIORITY-CORPUS-
CLEANUP, LAYER-REGISTRY-CONVERSION, DASHBOARD-FACETS-FULLY-CANONICAL, and
this one) are now DONE.
