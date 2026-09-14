# Investigation — TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH

## Two checks required before picking a fix

Per explicit review instruction: check whether a flavour/narrative-display field already exists on
`LeadState` before inventing one, and check whether other consumers read `detail` as text.

**No flavour field exists.** `LeadState` (`src/core/strategic.py:274-287`) has exactly:
`id, kind, subject, detail, discovered_tick, certainty, source_entity_id, tested, test_outcome,
failure_count, suppression_until_tick`. No narrative/display field. Also confirmed nothing reads
`detail` as display prose anywhere in the codebase — `src/api/presenters/state_presenter.py`'s own
lead serialization (the only place leads reach the API) exposes `id/kind/subject/certainty/tested`
and never `detail`. So dropping the narrative text loses nothing to any real display consumer.

**More consumers exist than the ticket's own filing named.** A full grep of every real (non-test)
`.detail` read on `LeadState` found, beyond `intelligence.py:406-436`'s own parse:

| Site | Convention | Real effect |
|---|---|---|
| `intelligence.py:408` | parseable `"x,y"` | belief-confirmation loop (originally named) |
| `intelligence.py:597` | parseable `"x,y"` | material-blocker navigation resolution |
| `redirection.py:92` | parseable `"x,y"` | material-blocker navigation resolution |
| `scorers.py:220` | parseable `"x,y"` | material-blocker navigation resolution (goal scoring) |
| `phase.py:148` | exact `region_id` | belief contradiction (region-danger-seen) |
| `contradiction.py:60` | exact `region_id` | belief contradiction (region-danger-seen) |
| `detour.py:257-258` | substring scan of `detail` | material-blocker → detour target resolution |
| `lead_routing.py:59` | raw `detail` as target | `REACH_LOCATION` objective routing |

Four of these (not one) fail silently on narrative-text `detail`, all via a swallowing
`try`/`except`. `certification/scenarios.py:485`'s own fixture (`detail="1.0,0.0"`) confirms the
parseable-coordinate convention is the real, intended precedent.

## Real impact, corrected

Reported to peer with this evidence: guild-granted leads never resolved a material blocker by
navigation at all — not just "never confirmed by observation," which is what the ticket's own
original filing said. Peer's response: put the corrected impact in the ticket in place of the
original paragraph, treat `detour.py`'s substring-match as a regression this fix would itself cause
(fix it in the same change, don't split it), narrow the visibility fix only at the site being
touched (not the other three sharing the pattern), and file the typed-shape root cause as its own
ticket rather than building it now.

## Why coordinates, not a redesign

Peer's lean (parseable coordinates, since `GuildAction.visit()` already has `node.position`) is
confirmed by evidence, not just preference: 4 real load-bearing consumers assume this shape, 0 real
consumers display `detail` as prose. A full discriminated-type redesign is real, valuable future
work — filed as `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING` — but isn't required to
fix the one live defect this ticket exists to close.

## Why `detour.py` rides in this ticket

`_subjects_match`'s material-blocker branch matched via `blocker.subject in lead.detail` — a
substring scan that only worked because narrative text happened to contain the right word. Once
`GuildAction.visit()` stops producing narrative text, that coincidence is gone and detour
suggestions for guild-granted material leads silently stop working — a real regression this same
change causes, not adjacent scope. Fixed by matching on `lead.subject`, the same convention the
other four real material-blocker consumers already use; the `"resource_node"` generic fallback is
preserved.

## Why only one exception site is narrowed

`intelligence.py:435-436`'s bare `except Exception` concealed the parse failure into a single
generic log line for the life of every affected lead — "a mechanism that cannot fail visibly," the
same family as the `IntentTrace` finding this arc's earlier ticket fixed. Narrowed at this one site:
the coords-parse failure is now caught separately (`ValueError`/`AttributeError`), logged at
WARNING naming the specific lead and its raw `detail`, and skips only that lead; a genuinely
unexpected failure in the downstream confirmation/contradiction logic gets its own distinct ERROR
log with `exc_info=True`. The other three parse sites sharing the identical shape
(`intelligence.py:597`, `redirection.py:92`, `scorers.py:220`) are left untouched — they stop
failing once `detail` parses for the one real producer that was emitting bad data, so the urgency
that justified touching this one site doesn't extend to them.
