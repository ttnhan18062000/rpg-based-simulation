---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER
artifact_type: investigation
tags: [process-improvement, workflows, create-tickets, ticket-scoper]
---

# Investigation — TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER

## Gap 1 claims, independently re-verified against this branch (based on `origin/main` `4512eae30`)

| Check site | Re-verified | Evidence |
|---|---|---|
| `concern-investigator.md` Step 3 | CONFIRMED | Lines 84-93: `grep -i "<keyword>" tickets/working_log.csv` only — no `tickets/todos/` or `tickets/inprogress/` scan anywhere in the file. |
| `implement-ticket.js` Scope, existing-ticket path | CONFIRMED | The prompt text sets `conflicts=(["ticket file not found for ${ticketId}"] if ticket_path is empty, else [])` — for a ticket that IS found (the normal case), `conflicts` is unconditionally `[]`. A `related_context` field already exists on the same output contract ("any non-blocking informational findings ... [] if none") — the right landing spot for scanner hits, no schema change needed on this path. |
| `implement-ticket.js` Scope, new-ticket path | CONFIRMED | Step 1: "Scan tickets/ (inprogress/, done/, and backlogs/) for overlapping scope or prior attempts." `todos/` is absent from that list, exactly as claimed. |

`search_docs`/`knowledge_search.py`'s scope (docs + closed tickets/working_log.csv only) is
confirmed by inspection and correctly placed in Out of Scope — rebuilt only on doc changes, so
indexing open tickets would introduce the same kind of staleness this ticket exists to remove.

## B0 / PERCEPTION-UPDATE overlap (AC1 fixture)

No `B0` ticket file exists anywhere in this repo (`git log --all --oneline | grep -i B0` matches
only an unrelated commit subject substring; no `tickets/**/*B0*` file). Confirms the ticket's own
fallback instruction applies: build a fixture.

`tickets/todos/TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED.md` is real, on this branch
now (copied from `origin/main`, unmodified by this ticket). Its real `## Related Code Areas`:
```
src/domains/perception/phase.py::PerceptionUpdatePhase
src/domains/perception/filter.py::PerceptionFilterService
src/domains/perception/salience.py::WorldSignal
src/systems/strategic_systems/intelligence.py (the SpatialQueryService.nearby_entities() bypass)
src/world/perception/gate.py::PerceptionGate
src/engine/pipeline.py
src/engine/tactical.py
```
and its Title starts "Design decision needed: which of three perception-shaped things in this
codebase is meant to be the real one?".

The AC1 fixture (`tests/fixtures/open_ticket_overlap/B0-PERCEPTION-UPDATE-WAVE-FIXTURE.md`, built
for this ticket, cited here as its source) reconstructs a plausible rpg-feature-planning wave
ticket that would genuinely have overlapped the real one: a `## Related Code Areas` entry citing
`src/domains/perception/phase.py` verbatim (the strongest, most deterministic signal — an exact
path match) plus a title/summary sharing distinctive terms (`perception`, `PerceptionModel`,
`strategic cognition`) with the real ticket, without copying its prose. This is a reconstruction,
not the real B0 text (unavailable — it lives only in the planning session's own uncommitted work,
not this branch or main).

## Existing canonical parsing to reuse

`tools/generate_registry.py::parse_body_section(body, section)` and
`parse_related_code_areas(section_text)` (path-citation extraction: backtick-quoted token first,
falling back to a path-shaped bare bullet line) are both already the sanctioned parser — used
directly by `tools/epic_folder_status.py` (the precedent this ticket cites) and
`tools/ticket_field_values.py`. No hand-rolled regex needed for either title/summary/code-area
extraction.

`tools/epic_folder_status.py` is the direct style precedent for the new tool: a pure `get_*()`
function returning a plain dict/list, a thin `main()`/argparse wrapper, prints one JSON object,
always exits 0 (a report, never a gate) — this ticket's scanner follows the identical shape.

## Term-overlap signal design

No existing "distinctive term overlap" helper exists anywhere in `tools/` to reuse (checked:
nothing in `tools/generate_registry.py`, `tools/knowledge_search.py`, or `tools/ticket_field_values.py`
does token-set overlap on ticket prose). Designed fresh: lowercase, alphanumeric-token split,
drop tokens under 5 characters and a small stopword list, compare as sets, hit when the
intersection has >= 2 shared distinctive terms. Threshold chosen per the ticket's own Assumptions
guidance ("prefer false positives to misses, since the output is advisory") — loose enough to
catch real overlaps like the B0 fixture, proven not to fire on an unrelated control ticket (AC2).

## Wiring points, exact locations for Scope item 2

- `concern-investigator.md` Step 3 (lines 84-93): add the scanner call alongside the existing
  `working_log.csv` grep, same "up to 3 matching" framing.
- `implement-ticket.js` Scope existing-ticket prompt (~line 155, the `related_context=` output
  field instruction): mention the scanner call before that line, and to put hits there.
- `implement-ticket.js` Scope new-ticket prompt, Step 1 (~line 171): add "and `tickets/todos/`
  (via the overlap scanner)" to the existing tickets/ scan list.

## Prompt-text pin test precedent (AC4)

`tests/tools/test_finalize_working_log_uses_helper_pin.py` (cited in `epic_folder_status.py`'s own
docstring) is the existing pattern for "assert specific text appears in a workflow's prompt
string" — read its structure before writing this ticket's own pin tests in the same style.
