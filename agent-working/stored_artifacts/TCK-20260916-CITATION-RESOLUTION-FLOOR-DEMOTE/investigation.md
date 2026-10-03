# Investigation — TCK-20260916-CITATION-RESOLUTION-FLOOR-DEMOTE

## What happened

`CITATION_RESOLUTION_FLOOR` (in `tools/gate_checks/premise_staleness_check.py`) is a blocking
ratchet on the percentage of open-ticket `Related Code Areas` citations that resolve to a real
file on disk. On 2026-09-16, PR #210 closed `TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-
UNMEETABLE`, moving it from `tickets/todos/` to `tickets/done/`. That shrank the open-ticket
population from 83 to 82, which by itself moved the measured citation-resolution rate from 96.1%
to 96.0% — below the floor (still pinned at 96.1 at that commit). `API / tools / logging` failed
on `main` at `0ab68f345` as a direct result. No citation text changed; no broken reference was
introduced.

The floor was re-pinned 96.1 → 95.8 in PR #208 (by this same session, during the #208 merge
conflict resolution), with the cause honestly traced in a code comment. As with the deleted
sidecar-attribution floor before it, this is the exact same shape of defect: a ratchet whose
denominator is "currently open tickets" moves whenever a ticket closes or opens, regardless of
citation quality — an inverted signal that fires on ordinary activity, not on regression.

## Root cause

The check's population (`load_open_ticket_entries()`, everything under `tickets/todos/` and
`tickets/inprogress/`) is a live, multi-session-shared corpus that shrinks and grows continuously
as any of several concurrent Claude sessions close or open tickets. A fixed percentage floor over
that population cannot distinguish "a ticket closed" from "a citation broke."

## Precedent

`TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE`'s own Decision section (read in full
from its real commit before this ticket's implementation began) establishes the disposition for
this exact class of defect: remove the gate, keep the measurement, document why in the module so
it is not rebuilt as a threshold. This ticket applies that same precedent.
