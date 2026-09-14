---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH
phase: done
date: 2026-09-13
tags: [cognition]
---

# TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH

## Title
`LeadState.detail` for `kind="location"` has two incompatible live conventions in production — a parseable `"x,y"` coordinate string versus free narrative text — and the mismatch throws silently, every tick, for the life of every affected lead

## Status
DONE

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

**Practical effect — corrected 2026-09-13, the original framing below undersold it.** The original
filing said only the observation-confirmation path was affected. A full sweep of every real,
non-test `.detail` read on `LeadState` found **four** real, load-bearing call sites that parse
`detail` as `"x,y"` floats to resolve a **material blocker** by navigation, not one:
`intelligence.py:408` (the one originally named), plus `intelligence.py:597`,
`src/systems/strategic_systems/redirection.py:92`, and `src/ai/goals/scorers.py:220`. All four wrap
the parse in a `try`/`except` that silently discards the failure. **So guild-granted leads never
resolved a material blocker by navigation at all** — not "never confirmed by observation." The
lead being useless for its own core purpose is the real impact, not a side mechanism being blocked.
A second, previously-undocumented convention was also found: `src/domains/information/phase.py:148`
and `src/domains/information/contradiction.py:60` compare `lead.detail == region_id` exactly — a
third format sharing `kind="location"` with the other two. See
`TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING`, filed as this investigation's own
follow-up, for the full picture and the root-cause typing question it raises.

## Scope
**Resolved 2026-09-13, after peer review of the fuller picture the investigation found** (see the
corrected "Practical effect" section above): parseable coordinates is the real majority convention
(4 load-bearing sites, not 1) and no flavour-display consumer exists to lose by dropping narrative
prose (confirmed — `state_presenter.py`'s own lead serialization never exposes `detail` at all).

- `GuildAction.visit()` (`src/town/guild.py`) now emits a parseable `"x,y"` `detail`
  (`f"{node.position[0]},{node.position[1]}"`), matching `certification/scenarios.py:485`'s own
  `"1.0,0.0"` precedent, instead of narrative text.
- `DetourSuggestionSystem._subjects_match`'s material-blocker branch
  (`src/systems/strategic_systems/detour.py:250-268`) no longer scans `detail` for a substring
  match — that only ever worked by the coincidence of narrative text containing the right word, and
  the fix that removes the narrative text removes the coincidence too. It now matches on
  `lead.subject`, the same real convention the other four material-blocker consumers already use,
  landing in this same change since it's a regression the fix itself would otherwise cause, not
  adjacent scope.
- The bare `except Exception` at `intelligence.py:435-436` is narrowed at this one site: the known
  `float()`-parse failure is now caught separately (`ValueError`/`AttributeError`), logged at
  WARNING naming the specific lead, and skips just that lead; a genuinely unexpected failure in the
  downstream confirmation/contradiction logic now gets its own distinct ERROR log
  (`exc_info=True`) rather than sharing one generic message with the known-shape case.
- The other three parse sites sharing the identical pattern (`intelligence.py:597`,
  `redirection.py:92`, `scorers.py:220`) are **not** touched — noted here as sharing the shape, left
  alone, since they stop failing once `detail` parses and the urgency that justified narrowing the
  one site actually being edited doesn't extend to sites that were never touched.
- The root-cause typing question — `detail` as one untyped `str` carrying three incompatible
  conventions, discriminated by nothing — is **filed, not built**:
  `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING`.

## Out of Scope
- Building the typed-shape fix for `LeadState.detail` — filed as its own ticket, not decided here.
- Touching `intelligence.py:597`, `redirection.py:92`, or `scorers.py:220`'s own bare exception
  handling — same shape, different urgency; noted, not fixed, in this ticket.
- `region_id`-convention consumers (`phase.py:148`, `contradiction.py:60`) — unaffected either way;
  a guild lead never matched them before this fix and still doesn't after it.
- Any change to `GuildAction.visit()`'s own lead-generation logic beyond the `detail` format itself
  (the `"iron"` → `"iron_vein"` resource-id match and the resource-id-hardcoding shape question,
  `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE`, are separate, already-filed/fixed concerns).

## Acceptance Criteria
- [x] The real convention chosen and implemented: `GuildAction.visit()` emits parseable
      coordinates, matching the real majority consumer convention and the certification precedent.
- [x] `detour.py`'s own substring-coincidence match fixed in the same change, since it's a
      regression the `detail`-format fix would otherwise cause, not separate scope.
- [x] The bare `except Exception` at the one site this ticket touches replaced with something that
      distinguishes a known-shape mismatch (visible, named, non-crashing) from a genuinely
      unexpected failure (visible, loud, non-crashing) — real test coverage for both cases.
- [x] Real test evidence: a `location` lead with parseable `detail` is confirmed normally; a
      sibling lead with non-coordinate `detail` on the same entity in the same pass is skipped,
      logged, and does not crash the pass; the `detour.py` regression this change would otherwise
      cause is covered directly.
- [x] The root-cause typing question filed as its own ticket, not built here.

## Related Tickets
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (in progress — the ticket
  whose own fix surfaced this; next in this batch's strict order)
- `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` (done, this batch —
  landed first in strict order; its fix is what made `GuildAction.visit()` produce real leads and
  surface this ticket's own defect in the first place)
- `TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING` (done, prior batch — the
  sibling "instrumentation conceals the fault" finding cited above)
- `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE` (filed alongside this one — the separate
  question of where `GuildAction.visit()`'s resource-id string should come from)
- `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING` (filed — this investigation's own
  root-cause follow-up, the typed-shape question, not built here)

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
- The fix touches three files, all in one change since `detour.py`'s own fix is a direct
  consequence of the `detail`-format change, not separate scope:
  - `src/town/guild.py` — `detail` format, `f"{node.position[0]},{node.position[1]}"`.
  - `src/systems/strategic_systems/detour.py` — `_subjects_match`'s material-blocker branch
    matches on `lead.subject == "resource_node"` instead of scanning `detail` for a substring.
  - `src/systems/strategic_systems/intelligence.py` — the coords-parse `try` split from the
    downstream confirmation/contradiction `try`, each with its own distinct, visible log.
- One pre-existing test (`tests/unit/strategic/test_phase6_strategic_cognition.py::
  test_blocker_inference_and_detour`) relied on the exact coincidental substring match this fix
  removes (`lead.subject="(5, 5)"`, `detail="Alternative resource source"`, matched only because
  `"resource"` happened to appear inside the prose). Fixed the fixture to use the real,
  intentional connection (`lead.subject="resource"`, matching the blocker's own inferred subject,
  `detail="5.0,5.0"` as a real parseable location) rather than loosening the assertion or
  softening the fix to keep the old fixture passing.
- `region_id`-convention consumers (`phase.py:148`, `contradiction.py:60`) were checked and
  confirmed unaffected either way — a guild lead's `subject` (`"iron_ore"`) was never a real
  `region_id` before or after this fix.

## Test Summary
- `tests/unit/world/test_guild_pipeline.py::test_guild_visit_leads` — extended with an assertion
  that `detail` is now a real parseable coordinate matching `node.position`.
- `tests/unit/strategic/test_detour_suggestion.py::TestSubjectsMatchMaterialBlocker` — 4 new tests:
  direct-subject match unaffected, the `resource_node` fallback still works, the fallback requires
  non-empty `detail`, and the old substring-coincidence match is confirmed gone (regression guard).
- `tests/unit/strategic/test_belief_integration.py::TestNonCoordinateLeadDetailIsSkippedNotCrashed`
  — 2 new tests: a non-coordinate `detail` lead is skipped with a WARNING (not ERROR) naming the
  lead, no crash; a coordinate `detail` sibling lead on the same entity in the same pass still
  confirms normally.
- `tests/unit/strategic/test_phase6_strategic_cognition.py::test_blocker_inference_and_detour` —
  fixed to use the real subject-match connection instead of the removed substring coincidence;
  passing.
- Regression sweep: `tests/unit/strategic/ tests/unit/world/test_guild_pipeline.py
  tests/unit/engine/test_guild_visit_phase.py tests/unit/ai/ tests/architecture/test_guild_action_dormancy.py
  tests/unit/cognition/ tests/unit/domains/information/ tests/integration/domains/information/
  tests/integration/kernel/ tests/certification/` — 691 passed, 1 skipped, 6 deselected (slow),
  no failures.

## Files Changed
- `src/town/guild.py` — parseable `detail` format.
- `src/systems/strategic_systems/detour.py` — subject-match instead of substring-scan.
- `src/systems/strategic_systems/intelligence.py` — narrowed, visible exception handling.
- `tests/unit/world/test_guild_pipeline.py`, `tests/unit/strategic/test_detour_suggestion.py`,
  `tests/unit/strategic/test_belief_integration.py`,
  `tests/unit/strategic/test_phase6_strategic_cognition.py` — new/fixed tests.
- `tickets/todos/TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING.md` — new, filed.

## Completion Summary
Fixed the real, live defect: `GuildAction.visit()` now emits a parseable coordinate, matching the
convention its own real consumers already assumed. The investigation found the impact was larger
than originally filed — four load-bearing material-blocker-resolution sites were affected, not one
observation-confirmation path — and that correction is recorded above rather than left standing.
Fixed the `detour.py` regression the format change would otherwise have caused, in the same change,
since a change that breaks something fixes it in the same change. Narrowed the bare exception at
the one site this ticket touches so a known-shape mismatch and a genuinely unexpected failure are
now visibly distinct, without removing the catch. Filed, not built, the root-cause typing question:
`LeadState.detail` is one untyped string for three incompatible real conventions, which is what made
this bug possible and will make another one possible if left as-is.
