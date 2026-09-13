# Plan — TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH

## Chosen fix (peer-reviewed, see investigation.md)
1. `src/town/guild.py` — `GuildAction.visit()`'s `detail` becomes
   `f"{node.position[0]},{node.position[1]}"`, matching the certification precedent's format.
2. `src/systems/strategic_systems/detour.py` — `_subjects_match`'s material-blocker branch matches
   on `lead.subject == "resource_node"` instead of `blocker.subject in lead.detail`. Rides in this
   ticket: it's a regression the `detail`-format change would cause, not separate scope.
3. `src/systems/strategic_systems/intelligence.py` — split the one `try`/`except Exception` into
   two: a narrow `except (ValueError, AttributeError)` around just the coords parse (WARNING,
   names the lead, `continue`s past it), and a separate `except Exception` around the downstream
   confirmation/contradiction logic (ERROR, `exc_info=True`) for genuinely unexpected failures.
   Only this one site — the other three sharing the pattern are noted, not touched.
4. File `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING` for the root-cause typing
   question. Not built.

## What this does NOT do
- Does not redesign `LeadState.detail` into a typed/discriminated shape.
- Does not touch the `region_id`-convention consumers (unaffected either way).
- Does not touch the other three parse sites sharing `intelligence.py:435-436`'s old shape.

## Steps
1. Implement the three code changes above.
2. Write test coverage:
   - `guild.py`: `detail` is a real parseable coordinate matching `node.position`.
   - `detour.py`: `_subjects_match` unit tests — direct match unaffected, `resource_node` fallback
     preserved (with and without empty `detail`), and an explicit regression guard proving the old
     substring-coincidence match no longer fires.
   - `intelligence.py`: a non-coordinate `detail` lead is skipped with a WARNING naming the lead,
     no crash; a coordinate-`detail` sibling lead in the same pass still confirms normally.
3. Find and fix any pre-existing test relying on the substring-match coincidence being removed —
   found one (`test_phase6_strategic_cognition.py::test_blocker_inference_and_detour`), fixed the
   fixture to use the real subject-match connection rather than loosening the assertion.
4. Regression sweep across strategic/guild/ai/cognition/information/kernel/certification test
   areas.
5. Update ticket, close, record hand-orchestrated monitoring, commit.
