---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH
phase: open
date: 2026-09-13
tags: [cognition]
---

# TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH

## Title
`LeadState.detail` for `kind="location"` has two incompatible live conventions in production — a parseable `"x,y"` coordinate string versus free narrative text — and the mismatch throws silently, every tick, for the life of every affected lead

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while fixing `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`'s own
`GuildAction.visit()` string-mismatch bug (`"iron"` → `"iron_vein"`). That fix made
`GuildAction.visit()` produce real `LeadState(kind="location", ...)` leads for the first time ever
in a live corpus run — and doing so immediately surfaced a **third, previously-invisible defect**
that could never collide with anything before, because this lead-producing path had never actually
produced a lead until that fix landed.

`src/systems/strategic_systems/intelligence.py:406-436`'s belief-confirmation loop processes every
`lead.kind == "location"` lead an entity holds by doing `tuple(map(float, lead.detail.split(',')))`
— it assumes `detail` is a parseable `"x,y"` coordinate string. Confirmed this convention is real
and used elsewhere: `src/certification/scenarios.py:485` constructs exactly this shape
(`detail="1.0,0.0"`). But `GuildAction.visit()` (`src/town/guild.py:41`) constructs its own
`kind="location"` leads with `detail=f"Rumors of iron near {node.position}"` — free narrative text,
not parseable coordinates. Confirmed via a real 300-tick instrumented run against
`frontier_living_world`: after the iron/iron_vein fix, every tick, for every entity holding one of
these guild-granted leads, the belief-confirmation loop's `float()` call throws
`could not convert string to float: 'Rumors of iron near (48.0'` — repeated identically, every
tick, for the entire lifetime of the lead.

**The failure is silently swallowed, and that concealment is itself part of the defect, not
incidental to it.** The `try`/`except Exception` at `intelligence.py:435-436` catches this and logs
`logger.error(f"Failed to check belief lead outcome: {ex}")` — no crash, no test failure, nothing
that would ever surface this to anyone not reading logs line-by-line. A mechanism that throws every
tick for the life of every affected lead and is swallowed into a log line is a mechanism that
cannot fail visibly — the same family as the `IntentTrace` recording `SUCCESS` for a no-op
(`TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING`, this same batch): the
instrumentation actively conceals the fault rather than surfacing it.

**Practical effect, checked and disclosed rather than assumed**: these leads still land in
`entity.strategic.leads` and are genuinely readable by any consumer that reads that field directly
(confirmed for `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`'s own purposes —
see that ticket for the explicit check). Only this one specific observation-based
confirmation/contradiction path is affected: a guild-granted lead can never be marked
`tested=True`/`test_outcome` via direct-observation confirmation, because the code that would do
that crashes (caught) before it can act, every time it's attempted.

## Scope
- Determine which convention is actually correct for `kind="location"` leads: parseable
  coordinates (matching `intelligence.py`'s own consumer and the certification fixture's
  precedent), free narrative text (matching `GuildAction.visit()`'s own current shape and
  presumably intended for player/log readability), or a redesign that separates a
  machine-readable field from a human-readable one so neither producer has to compromise. This is
  a real design question — not resolved here.
- Whichever convention is chosen, fix the actual mismatch: either `GuildAction.visit()` emits
  parseable `detail`, or `intelligence.py`'s belief-confirmation loop is changed to not assume a
  single free-form string encodes coordinates directly (e.g. reading a real position field instead
  of parsing prose).
- **Do not leave the bare `except Exception: logger.error(...)` as-is once the mismatch is fixed.**
  Whoever picks this up should replace it with something that can't silently swallow a *different*,
  genuinely unexpected failure the same way this one has been hidden — narrow the caught exception
  type, or handle the known-shape mismatch explicitly rather than catching broadly around it.
- Real test evidence that a `location` lead, regardless of which producer created it, can be
  processed by the belief-confirmation loop without throwing.

## Out of Scope
- Any change to `GuildAction.visit()`'s own lead-generation logic beyond the `detail` format
  itself (already fixed separately: the `"iron"` → `"iron_vein"` resource-id match, and the
  resource-id-hardcoding shape question, `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE`).
- Auditing every other `kind="location"` lead producer for the same mismatch as part of this
  ticket's own fix — `src/domains/information/normalizer.py`, `src/world/providers/information.py`,
  and `src/systems/strategic_systems/belief.py`'s two producers take `detail` as a caller-supplied
  parameter rather than hardcoding it, so their own conformance depends on their own callers;
  worth a note in Implementation Notes if this ticket's own investigation finds a second live
  mismatch, but not a mandate to sweep all of them now.

## Acceptance Criteria
- [ ] A real design decision on the correct `detail` convention for `kind="location"` leads,
      brought to peer/user review before implementation.
- [ ] The mismatch fixed per that decision — either producer or consumer side, not both patched
      independently in a way that reintroduces the same class of drift.
- [ ] The bare `except Exception` replaced with something that cannot silently conceal a
      genuinely unexpected failure the same way this one was hidden.
- [ ] Real test evidence: a `location` lead from each real production producer processes through
      the belief-confirmation loop without throwing.
- [ ] No implementation without the design decision above.

## Related Tickets
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (in progress — the ticket
  whose own fix surfaced this)
- `TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING` (done, this batch — the
  sibling "instrumentation conceals the fault" finding cited above)
- `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE` (filed alongside this one — the separate
  question of where `GuildAction.visit()`'s resource-id string should come from)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/systems/strategic_systems/intelligence.py:406-436` (the belief-confirmation loop's
  `float()` parse and its bare `except Exception`)
- `src/town/guild.py:41` (`GuildAction.visit()`'s own `detail=f"Rumors of iron near {node.position}"`)
- `src/certification/scenarios.py:485` (the parseable-coordinate convention's own real precedent)
- `src/core/strategic.py:276-288` (`LeadState`, the shared type both conventions live under)

## Assumptions / Open Questions
- Which convention is authoritative is the central, deliberately-unresolved question this ticket
  exists to answer — not assumed here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
