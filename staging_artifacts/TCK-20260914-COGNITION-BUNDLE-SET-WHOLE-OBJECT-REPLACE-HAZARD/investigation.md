# Investigation — TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD

## Re-verified writer enumeration (2026-09-14, post-#190/#191 merge)

Re-ran the enumeration grep the ticket itself asked to be re-verified before acting on it:
`grep -rn '"cognition_bundle_set"\]\s*=\|cognition_bundle_set=' src/`. The 9 real writer sites and
1 dormant-but-structurally-identical site from the ticket's own table are unchanged — no new
writer has been added since the ticket was filed. Verdicts stand as recorded.

## The real `CognitionModel` schema (`src/core/cognition.py`)

`CognitionModel` is a deep, purely-declarative tree: 6 top-level fields (`subjective`, `memory`,
`motivation`, `commitment`, `relationships`, `role_model`), each itself a `@dataclass(frozen=True,
slots=True)` container of further nested dataclasses. `memory` alone has 6 sub-fields (`experience`,
`causal`, `spatial`, `habit`, `combat`, `social`), several of which (`causal.entries`,
`combat.opponent_stats`, `spatial.visited_regions`) are themselves `Mapping`/`Tuple` collections
that individual writers mutate at the *entry* level, not the whole-container level. **No dataclass
in this file defines a `merge()` method today** — this is a pure data schema, unlike `src/core/
updates.py`'s own `EntityUpdate` sub-components (`CombatUpdate`, `SocialUpdate`, etc.), which do
each implement `.merge()`.

This matters directly for evaluating Option 1.

## Option 1 — per-subfield merge on `CognitionModel`

**What it would actually require**: not a single `CognitionModel.merge()` method, but a full,
correct `.merge()` on every dataclass in the file, recursively, because the real collision surface
goes past the top level. Two concrete cases proven by the real writer set itself:

- `combat_actions.py` (Step 5a) and `combat_engagement/phase.py` (passive observation) can both
  write to the **same** `memory.combat.opponent_stats` dict for the **same entity** in the **same
  tick**, for **different `subject_key`s** (an entity resolves a real fight via `execute_attack()`
  and is *also* the nearest evaluator/witness for a different hostile in `CombatEngagementPhase`'s
  own per-actor loop). A `memory`-level or even `CombatMemory`-level "replace" would still lose one
  write; only merging `opponent_stats` at the **dict-key** level is actually correct here.
- `memory_update` (this ticket's own first-action fix, above) and any future writer could
  legitimately touch two *different* leaves under the same `MemoryModel` (`causal` vs. `combat`) in
  the same tick — a `CognitionModel`-level "replace whichever changed" is too coarse; `MemoryModel`
  itself needs to merge its own 6 sub-fields independently.

So a **correct** Option 1 needs recursive merge logic at every level down to individual dict-key/
tuple-append granularity for `causal.entries` (append/cap), `combat.opponent_stats` (dict union with
salience-eviction poking through), `spatial.visited_regions` (dict union), etc. — not a generic
"prefer the changed field" reflection helper, because "changed" isn't well-defined for a field two
writers touch with genuinely different intents (e.g., two different dict keys). This is a real,
ongoing engineering surface (~15+ dataclasses today, each needing its own correct merge semantics
matching what its own collection type means), and every future field addition needs a matching
merge case — the exact cost the ticket named as Option 1's price, now sized against the real schema
rather than estimated.

**Verdict: correct, but expensive and slow-changing.** It is the only option that makes a *dict-key-
level* collision (the `opponent_stats` case above) structurally safe without any writer discipline
at all. It is also the option most likely to itself contain a bug on day one (getting tuple-append
vs. tuple-replace semantics right per field, for a schema this deep, is easy to get subtly wrong)
and the hardest to keep correct as the schema grows — schema growth here is not slow: this file has
gained 3 new leaf types in the last month alone for combat_engagement, role_model, and lineage
features.

## Option 2 — mandatory typed write helper

**What it would look like against the real schema**: a single function, e.g.
`src/core/cognition_write.py::read_through_cognition(entity_id, fallback_cognition, entity_updates,
tick_update)`, generalizing the `_read_through_cognition()` helper already built and tested in
`src/domains/combat_engagement/phase.py` for this exact hazard. Every real writer already follows
the identical three-step lookup (this phase's own local `entity_updates`, then the tick's
accumulated `tick_update`, then the entity snapshot) — 6 of today's 9 writers already hand-wrote
this exact sequence independently. Centralizing it is a pure extraction, not new design.

This does **not** solve the `opponent_stats` dict-key-collision case above by itself — reading
through gets a writer the *up-to-date* `CognitionModel` to build its patch from, but two writers in
the *same* phase call building from the *same* read-through result would still need to merge their
own dict writes explicitly (as `combat_engagement/phase.py`'s own witnessed-combat code already
does, manually, via `store_opponent_model()`'s upsert). What it *does* fully solve is the actual
observed failure mode: an entity's cognition write from **phase N** silently erasing **phase N-1**'s
own write for the same entity, which is the concrete bug this ticket exists because of.

**Verdict: cheap, addresses the actual observed failure class, does not touch `merge()`'s own
semantics (lower blast radius), but relies on adoption** — a future writer that skips the helper and
reads `entity.cognition` directly is exactly as unsafe as today.

## Option 3 — architecture/corpus test guardrail

Checked feasibility directly: an AST-walk test (matching the existing style of
`tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer`, which already
walks every file under `tools/` for a similar single-writer invariant) can detect a `.cognition`
attribute access on a name that also appears in a `cognition_bundle_set=` keyword argument within
the same function, outside an allow-listed helper module. This is mechanically feasible and cheap.

**Verdict: real, but a backstop, not a fix.** It converts "a future writer silently gets this
wrong" into "a future writer's PR fails CI with a clear message" — which is the correct role for a
guardrail, but it presupposes Option 2 (or something like it) exists as the "correct path" the test
is steering people toward. A guardrail with no sanctioned alternative to point to just produces a
failing test with no clear fix.

## Recommendation: Option 2 + Option 3 together, not Option 1

The ticket's own peer-supplied argument for the structural options ("5-of-6 convention adoption and
it still lost data — the failure mode is not knowing a pattern is needed, which only a type or the
merge logic can surface") is real evidence, but it argues for **a single, mandatory, discoverable
entry point being enforced** — not specifically for Option 1's much larger recursive-merge surface.
Option 2 (the helper) + Option 3 (an architecture test making the helper the only reachable path)
delivers the same "a future writer can't discover the unsafe path first" property the peer's
argument calls for, at a small fraction of Option 1's engineering and ongoing-maintenance cost, and
without touching `EntityUpdate.merge()`'s existing, already-tested semantics for every *other* field.

Option 1 would still be worth doing **only if** a real, live instance of the dict-key-collision case
(two writers touching different keys of the same nested dict, e.g. `opponent_stats`, in the same
tick) is ever observed causing an actual data-loss bug — that specific failure mode is not fixed by
Option 2 alone. No such instance has been observed; `combat_engagement/phase.py`'s own witnessed-
combat code already handles its own internal case of this manually and correctly (`_merge_
observation_into_updates()`'s own upsert-by-key logic). Recommend treating Option 1 as a documented,
deferred escalation path if that specific failure mode is ever actually observed, not building it
speculatively now.

`src/engine/patches.py::CognitionPatch.merge()` reproduces the same whole-object-replace pattern but
remains genuinely dead (confirmed again: still only ever applied to a single already-fully-merged
`EntityUpdate`, never merging two `CognitionPatch` objects against each other in the current call
graph) — Option 2 does not touch it, and it needs no fix under this recommendation since it is not a
live collision site. Worth a one-line comment at its own definition noting the dormant duplication,
so a future reader investigating a `CognitionPatch`-level bug isn't surprised to find the same shape
twice.

## First action (not conditional on the above, per the ticket's own scope) — DONE

`src/domains/memory/phase.py::MemoryUpdatePhase.apply()` now reads through any `cognition_bundle_set`
an earlier phase already staged this same tick before building its own `CognitionModel`, matching
the pattern the other 5 already-safe writers use. New regression test:
`tests/unit/domains/memory/test_memory_update_phase_apply.py::
test_memory_update_reads_through_an_earlier_same_tick_cognition_write`. This closes the one
remaining "safe only by ordering" writer from the enumeration, independent of the Option 2/3
decision above.
