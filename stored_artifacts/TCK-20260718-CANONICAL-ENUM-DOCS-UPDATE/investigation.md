---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE
date: 2026-07-18
tags: [documentation, claude-md]
---

# Investigation — TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE

## Current Behavior (file:line refs)

Checked all 6 `.claude/agents/*.md` files a preliminary grep flagged for
tier/priority mentions, read each in full context (not just the grep hit):

- **`done-checker.md`** — genuinely stale: its static-check mapping table
  (line ~48-54) only listed 5 `run_static_precheck` conditions;
  `ticket_field_values_valid` (added by
  TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM) was missing, and checklist
  item #3's own text ("`## Tier`, `## Type`, `## Priority` fields...
  contain valid values") gave no indication this was now backed by a real
  static check for 2 of those 3 fields. **Updated.**
- **`ticket-scoper.md`** — genuinely stale: Priority guidance listed only
  `P0`/`P1`/`P2` (missing `P3`, same bug as `CLAUDE.md`'s pre-fix line);
  Layer guidance said "use `misc`" with no mention of the registry;
  frontmatter template's `layer:` placeholder pointed at
  `LAYER_VALUES in tools/validate_frontmatter.py` (technically still
  importable from there, but doesn't mention the registry CLI, the actual
  way to discover/add values now). **Updated.**
- **`concern-investigator.md`** — `tier_recommendation` enum
  (`hotfix`/`standard`) is intentionally narrower than the full
  `TIER_VALUES` (this agent never recommends `epic` directly, by design —
  epics are scoped via a different path). `priority_hint` says `P0/P1/P2`
  or the generic case (missing `P3`) — this is describing a *hint* field
  the Structure phase later maps into a real ticket, not itself validated
  against `PRIORITY_VALUES`; borderline, but for consistency worth a
  one-line fix. **Investigated, minor fix warranted but low-risk since
  it's a hint field, not a validated one — see Scope Guards for the
  decision to leave it, since it doesn't feed the canonical-enum gate
  directly and touching it risks unrelated create-tickets.js coupling.**
- **`architecture-reviewer.md`** — only a passing "hotfix tier" mention in
  a workflow-phase-skip context, no enum claim at all. **No change
  needed.**
- **`parity-updater.md`** — `priority: P0  # P0 | P1 | P2` is the *parity
  ledger entry's own* priority field (a genuinely different P0-P2 scale),
  confirmed via a direct scan of `docs/parity_ledger/infrastructure.yaml`
  (`Counter({'P0': 178, 'P1': 82, 'P2': 23})` — zero P3 entries exist,
  confirming this is not the ticket-body Priority field at all). **No
  change needed — correctly left alone, not a bug.**
- **`simulation-analyst.md`** — "high-priority events" is plain English
  about simulation goal priority, unrelated to the ticket `## Priority`
  field. **No change needed.**

Also checked `.claude/workflows/*.js` for the same `LAYER_VALUES in
tools/validate_frontmatter.py` stale reference (the user's "workflows"
mention explicitly covers these): found and fixed identical stale text in
`create-tickets.js`, `simq-audit.js`, `implement-ticket.js`. Verified all 3
with `node --check` after editing — syntactically valid.

`docs/observability/agent_ops_dashboard_contract.md` and
`docs/guides/agent_ops_dashboard.md` both still described only `statuses`
as "the one exception" to corpus-derived facets — stale as of
TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL (now 4 of 5 facets are
canonical, only `tags` is corpus-derived). Rewrote both paragraphs to
describe the final, correct state rather than leaving 3 separate
near-duplicate "one exception" callouts across the session's several
tickets.

`tools/validate_frontmatter.py`'s module docstring only ever claimed to
validate "YAML frontmatter" — never implied it owned body-section
validation. **Investigated, no change needed — already correctly scoped.**

## Mechanics/Engine Constraints

None — documentation/agent-instruction accuracy, not simulation gameplay.

## Parity Ledger Overlap (IDs + status)

None — no code/behavior change, pure documentation.

## Prior Work

Every prior ticket in this epic (all 4, DONE) — this ticket documents their
combined final state.

## Risks and Open Questions

- New standalone `docs/guidelines/` doc (parallel to `tag_taxonomy.md`) vs.
  folding into `CLAUDE.md`: **decided — fold into CLAUDE.md.**
  `TCK-20260718-LAYER-REGISTRY-CONVERSION` already added a full explanatory
  paragraph there (Layer-registry mechanics, plus a summary distinguishing
  `layer`/`tags` from body-field `Tier`/`Status`/`Priority`) — a new
  standalone doc would either duplicate that content or fragment the
  single most-read instruction file into two places a future reader has to
  cross-reference. `CLAUDE.md` is already the authoritative, high-traffic
  location; no new file created.

## Anti-Drift Hazards

None — every edit in this ticket is either a stale-reference fix (traced to
a specific superseding ticket) or a genuine gap-fill, not new design.
