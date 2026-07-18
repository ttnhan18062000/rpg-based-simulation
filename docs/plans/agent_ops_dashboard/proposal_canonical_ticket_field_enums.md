---
status: active
layer: guidelines
authority: P2
audience: developer
maturity: proposal
date: 2026-07-18
tags: [frontmatter, data-quality, observability]
---

# Proposal: Canonical, hard-validated enums for Tier/Layer/Status/Priority — and make the dashboard's filter facets reflect them

**Maturity: PROPOSAL** — grew out of a real bug report and a follow-up design
question during today's Agent Ops Dashboard fix session. The user pointed out
that `TCK-20260718-FILTER-SELECT-DROPOUT`'s fix (a synthetic-`<option>`
injection) was a band-aid: the real problem is that the Tickets view's
Tier/Layer/Priority filter dropdowns compute their option lists from the
*currently filtered* ticket set, so selecting one filter genuinely narrows
what other filters can offer — which is not the desired UX. The user wants
these dropdowns to always show the full set of possible values, and asked
whether a closed, hard-validated enum (similar to Layer, explicitly *not*
like Tag) should exist for these ticket fields, checked as a rule at ticket
creation/processing time — plus an explanation of how Layer differs from Tag.

## Background investigation (already done, feed this to Investigate — do not redo)

The ticket body has (at least) four fields whose values are meant to be a
closed set, but only two currently have any code-level enforcement:

| Field | Location | Current values found in corpus | Enum exists? | Enforced? |
|---|---|---|---|---|
| `## Tier` | ticket body | `standard` (932), `hotfix` (103), `epic` (40) — **zero drift** | No | No |
| `layer:` | ticket **frontmatter** | 19 fixed values (`mechanics`, `engine`, `combat`, `economy`, `world`, `ai`, `misc`, ...) | Yes — `LAYER_VALUES` in `tools/validate_frontmatter.py` | **Yes** — `_check_enum()` runs as part of `validate_frontmatter.py`, invoked by `done_checker_static.py::check_frontmatter_valid` at the Verify/Finalize gate. A ticket cannot close with an invalid `layer:`. |
| `## Status` | ticket body | Fixed today via `WORKFLOW_STATUS_VALUES` (`OPEN`/`INPROGRESS`/`BLOCKED`/`DONE`/`EPIC_SCOPED`) added this session in `src/api/agent_ops_dashboard/ingest.py` — **dashboard-only**, not a ticket-creation-time gate | Yes, but **only inside the dashboard backend**, not reused by any ticket-authoring/closing tool | No — nothing stops a *new* ticket from being closed with a non-canonical body Status; this session's `STATUS-DRIFT-REPAIR`/`STATUS-SUFFIX-TRIM`/`STATUS-MULTILINE-FIX` tickets were pure historical-data cleanup, not prevention |
| `## Priority` | ticket body | `P1` (794), `P2` (240), `P0` (25), `P3` (24), **`P1: High` (2) — already drifted**, same shape as the Status bugs fixed earlier today | No | No |

Key finding to explain to the user in any response/doc: **`Layer` already is
the exact mechanism the user is describing wanting to build** — a closed,
hardcoded enum (`LAYER_VALUES`), validated as a hard gate at ticket-close
time, distinct from `Tag` (`docs/guidelines/tag_registry.jsonl` — multi-value
per ticket, categorized into 4 types per `docs/guidelines/tag_taxonomy.md`,
append-only *growable* registry, not a fixed code enum). The dashboard simply
doesn't reuse `LAYER_VALUES` for its Layer filter facet — it re-derives Layer
from the filtered corpus the same way it (correctly, for Tag) derives tags.

**Important architectural note for whoever implements this**: `LAYER_VALUES`
lives in `tools/validate_frontmatter.py` and validates a *frontmatter* field
(`extract_frontmatter`). `Tier`/`Priority`/`Status` are *body-section* fields,
parsed via a completely different code path (`tools/generate_registry.py`'s
`parse_body_section`, used by `ingest.py`, `status_drift_check.py`). Adding
hard validation for body-section Tier/Priority is **not** a drop-in reuse of
`validate_frontmatter.py`'s existing `_check_enum()` — that function only
ever sees frontmatter dict values. This needs new validation logic that reads
the body section (via `parse_body_section`) and checks it against a
canonical set, most naturally wired into the same `done_checker_static.py`
gate-check pipeline that already runs `validate_frontmatter.py` at Verify —
mirroring `status_drift_check.py`'s own existing shape (which already reads
body sections this same way, just doesn't block on it — it's a detection-only
tool today, not a closing gate).

Also worth deciding during Investigate: `WORKFLOW_STATUS_VALUES` currently
lives inside `src/api/agent_ops_dashboard/ingest.py` — a dashboard-specific
module — not a shared `tools/` location. If a new shared canonical-enums
module is created for `TIER_VALUES`/`PRIORITY_VALUES`, should
`WORKFLOW_STATUS_VALUES` (and possibly `LAYER_VALUES`) move there too, with
`ingest.py`/`validate_frontmatter.py` importing from the new single source of
truth, rather than three separate modules each defining their own slice of
the same underlying "what values can a ticket field hold" concept? This
mirrors the exact lesson `TCK-20260718-STATUS-MULTILINE-FIX` learned the hard
way (a duplicated, drifted regex second-guessing the real extraction
function) — a canonical enum that exists in more than one place risks the
same class of staleness. Make and document a clear call either way.

`CLAUDE.md`'s own Ticket Format section documents Priority as
`(P0 | P1 | P2)` — **missing P3**, which the real corpus uses 24 times. This
doc/reality mismatch should be corrected as part of whatever canonical-enum
work lands, not left stale.

## User's explicit decisions for scope (already made, do not re-ask)

- Structure this as an **epic** with child tickets, not one ticket.
- The new Tier/Priority hard validation should be added for **future ticket
  closures** (via the same gate pattern Layer already uses), **and** the
  existing closed corpus (`tickets/done/`, plus `tickets/inprogress/`,
  `tickets/todos/`) should be **fully re-scanned now** against the new
  canonical Tier/Priority enums to surface *any* drift beyond the 2 already-
  known `"P1: High"` cases — not just those 2, a full corpus check.

## Concerns for Comprehend/Investigate to turn into child tickets

1. **Canonical enum definitions + hard-validation gate.** Define
   `TIER_VALUES` (`{hotfix, standard, epic}`) and `PRIORITY_VALUES`
   (`{P0, P1, P2, P3}`) — decide the right module/location per the
   architectural note above (possibly consolidating `LAYER_VALUES` and
   `WORKFLOW_STATUS_VALUES` alongside them into one shared source of truth).
   Wire body-section Tier/Priority validation into the Finalize/Verify gate
   (`done_checker_static.py` and/or a new function alongside
   `status_drift_check.py`'s existing shape) so a ticket cannot close with a
   non-canonical Tier or Priority value going forward — mirroring exactly how
   `layer:` already blocks today. Fix `CLAUDE.md`'s Ticket Format section to
   correctly list `P3`.

2. **Full-corpus re-validation and cleanup.** Using the new canonical
   Tier/Priority checks, scan the *entire* current ticket corpus
   (`tickets/done/`, `tickets/inprogress/`, `tickets/todos/`) for any
   drift — not just the 2 known `"P1: High"` cases, everything the new check
   would flag. Fix whatever is found, following this session's established
   pattern (`STATUS-DRIFT-REPAIR`/`STATUS-SUFFIX-TRIM`/`STATUS-MULTILINE-FIX`):
   investigate each drifted value's actual meaning before blindly overwriting
   it (some may need relocated context, some may be legitimate exemptions
   like pre-TCK-naming legacy files — apply the same judgment, don't assume
   every finding is a simple typo). This ticket depends on concern 1 landing
   first (needs the real canonical values and check function to exist).

3. **Dashboard facets become canonical for Tier/Layer/Priority** (Status
   already fixed this session by `TCK-20260718-STATUS-FACET-CANONICAL`).
   `src/api/agent_ops_dashboard/ingest.py`'s `get_tickets()` should compute
   `facets["tiers"]`, `facets["layers"]`, `facets["priorities"]` from the new
   canonical enum module (reusing `LAYER_VALUES` directly for layers) instead
   of `_distinct_sorted(...)` over the filtered corpus — mirroring exactly how
   `facets["statuses"]` already works. `facets["tags"]` is correctly left
   alone (Tag is genuinely open-vocabulary/multi-value, not a closed enum —
   see the Layer-vs-Tag distinction above). Once all four single-value facets
   are fixed canonical lists, investigate whether
   `dashboard-frontend/src/views/TicketsView.tsx`'s `FilterSelect`
   synthetic-`<option>`-injection workaround (added by
   `TCK-20260718-FILTER-SELECT-DROPOUT`, closed earlier today) becomes dead
   code for Tier/Layer/Status/Priority (since the selected value will now
   always be present in the canonical `options` list) — remove it if
   genuinely unreachable, verified via a test, not just asserted. This ticket
   depends on concern 1 (needs the canonical values to exist) but not on
   concern 2 (corpus cleanup doesn't block the dashboard code change).

4. **Update related agent/doc settings.** Once the mechanism exists, update
   every place that currently documents Tier/Layer/Priority/Status informally
   or incompletely: `CLAUDE.md`'s Ticket Format section (tier/type/priority
   lines, and the missing-P3 fix from concern 1 if not already folded in
   there), any `.claude/agents/*.md` role files that reference these fields
   (check `ticket-scoper.md`, `done-checker.md`, `investigator.md`,
   `planner.md` for tier/priority/status mentions — investigate which
   actually need updates rather than touching all of them reflexively),
   `tools/validate_frontmatter.py`'s module docstring, and the dashboard's
   own `docs/observability/agent_ops_dashboard_contract.md` /
   `docs/guides/agent_ops_dashboard.md` (both already partially describe the
   Status-is-canonical exception from earlier today — extend that language to
   cover Tier/Layer/Priority too, or fold it into one unified "canonical
   facets" description rather than four near-duplicate paragraphs). Depends
   on concerns 1 and 3 (needs the real implementation to document).

## Explicitly out of scope

- Any change to how `Tag` works — its open-vocabulary, registry-governed,
  multi-value design is correct and different from Tier/Layer/Priority/Status
  by intent, not by oversight. Do not add a "closed Tag enum."
- Retrofitting the frontmatter `status`/`authority`/`audience`/`phase` fields
  — those already have their own working enums (`STATUS_VALUES`,
  `AUTHORITY_VALUES`, `AUDIENCE_VALUES`, `PHASE_VALUES` in
  `validate_frontmatter.py`) and hard validation; not part of this proposal.
- Any further UI/UX redesign of the Tickets view beyond making the four
  facets canonical — no new components, no visual redesign.
