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

- `memory_update` (this ticket's own first-action fix, above) and any future writer could
  legitimately touch two *different* leaves under the same `MemoryModel` (`causal` vs. `combat`) in
  the same tick — a `CognitionModel`-level "replace whichever changed" is too coarse; `MemoryModel`
  itself needs to merge its own 6 sub-fields independently.

**Correction, verified empirically rather than assumed** (peer review caught this before it shipped
as a claim): an earlier draft of this investigation additionally claimed `combat_actions.py` (Step
5a) and `combat_engagement/phase.py` (passive observation) writing *different keys* of the same
`memory.combat.opponent_stats` dict for the same entity in the same tick was a case Option 2
(read-through alone) could not handle, and that Option 1 would be needed for it. **That claim was
wrong, and disproven with a real pipeline run**, not just re-reasoned: constructed a real 3-entity
scenario (`AuthoritativeApplyPipeline.refine()`, a real `ATTACK` task through `action_routing` +
a real nearest-hostile evaluation through `combat_engagement`'s own main loop, same tick, same
attacker) and confirmed the attacker's own final `opponent_stats` contains **both** keys
(`entity.2` from the real combat resolution, `entity.3` from the passive evaluation) —
`_read_through_cognition()` alone, unmodified, handles this correctly. The reason: `action_routing`
and `combat_engagement` are not separate accumulators — pipeline.py threads one `update`/`tick_update`
StateUpdate linearly through every phase in sequence, so `combat_actions.py`'s own write (staged
during `action_routing`, which runs earlier) is already present in the very `tick_update` that
`combat_engagement`'s own `_read_through_cognition()` checks. Writer B's read-through sees writer
A's already-merged dict entry and adds its own key on top; whole-object replace of that *combined*
result is then correct, because there was only ever one write in flight for that entity at
`combat_engagement`'s own read point, not two competing ones.
**This narrows Option 1's justification, not just its estimated cost**: the one concrete
dict-key-collision case in today's writer set is not a real gap in Option 2 — it was already
correctly covered by the read-through pattern once traced through the real pipeline rather than
assumed from the writer table alone. Option 1 would still be needed only for a hypothetically
different failure shape — two writers staging into *genuinely separate* accumulators that never
converge before either one's own read-through point (not observed in any real writer today; the
pipeline's own single-accumulator design makes this hard to construct by accident).

So the actual remaining engineering cost of a *correct* Option 1 is: recursive merge logic at every
level of the tree, needed only to protect against writers that might one day exist outside the
pipeline's own single-accumulator discipline — a real, ongoing engineering surface (~15+ dataclasses
today, each needing its own correct merge semantics matching what its own collection type means),
solving a failure mode that has not been observed and that the pipeline's own architecture already
makes hard to construct.

**Verdict: correct in principle, but solves a hypothetical failure mode the real pipeline's own
single-accumulator design already prevents in every writer observed today.** It is also the option
most likely to itself contain a bug on day one (getting tuple-append vs. tuple-replace semantics
right per field, for a schema this deep, is easy to get subtly wrong) and the hardest to keep
correct as the schema grows — schema growth here is not slow: this file has gained 3 new leaf types
in the last month alone for combat_engagement, role_model, and lineage features.

## Option 2 — mandatory typed write helper

**What it would look like against the real schema**: a single function, e.g.
`src/core/cognition_write.py::read_through_cognition(entity_id, fallback_cognition, entity_updates,
tick_update)`, generalizing the `_read_through_cognition()` helper already built and tested in
`src/domains/combat_engagement/phase.py` for this exact hazard. Every real writer already follows
the identical three-step lookup (this phase's own local `entity_updates`, then the tick's
accumulated `tick_update`, then the entity snapshot) — 6 of today's 9 writers already hand-wrote
this exact sequence independently. Centralizing it is a pure extraction, not new design.

Verified directly (see the correction above) that this pattern, applied consistently, **does**
correctly handle same-tick, same-entity, different-dict-key writes across two different pipeline
phases — not just the "phase N replaces phase N-1's entire write" failure mode this ticket was
originally filed for, but the narrower key-level collision too, as a consequence of the pipeline's
own single-accumulator threading rather than anything the helper itself has to reason about.

**Verdict: cheap, addresses the actual observed failure class (and, verified, the dict-key-collision
class too), does not touch `merge()`'s own semantics (lower blast radius), but relies on adoption**
— a future writer that skips the helper and reads `entity.cognition` directly is exactly as unsafe
as today.

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

**Revised, per peer's own framing of this exact question**: earlier drafts of this section treated
Option 1 as a documented, deferred escalation path in case the dict-key-collision case (two writers
touching different keys of the same nested dict, e.g. `opponent_stats`, in the same tick) was ever
observed causing real data loss. That framing is now retired, not just softened. The empirical check
above (a real pipeline run, not reasoning about the writer table) confirmed both writers stage into
the *same* accumulated `update`/`tick_update` object, so `_read_through_cognition()` already covers
this case today — there is no gap for Option 1 to stand ready for. Per the peer's own logic: "if
[Option 2 already covers it], Option 1 isn't a deferred escalation path — it's unnecessary, and the
ticket should say so rather than leaving a speculative escalation on the books." Recording that here
rather than carrying forward a speculative escalation path for a failure mode that isn't real given
how this pipeline is actually built. `combat_engagement/phase.py`'s own witnessed-combat code
additionally handles its own internal same-phase case of this manually and correctly (`_merge_
observation_into_updates()`'s own upsert-by-key logic), for what it's worth as a second, independent
data point — but the pipeline-level architecture is the reason Option 1 is unnecessary, not this one
call site alone.

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
