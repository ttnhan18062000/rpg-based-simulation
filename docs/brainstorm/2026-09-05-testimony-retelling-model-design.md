---
status: active
layer: strategy
authority: P2
audience: agent
tags: [strategy, content]
---

# Testimony/Retelling Model — Design for Idea 62 (and, Later, 63)

**Source:** Deliverable #1 of `docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md`
("A testimony/retelling model — how a recorded event's *represented* content diverges from its
*ground-truth* content as it propagates through retellings, distinct from both Chronicle... and
`BeliefEntry`/`KnowledgeFact`"), flagged there as P2/larger-scope, "may need its own dedicated
proposal the way the temporal calendar did." This is that proposal — a design, not an
implementation. No `src/` file is touched by this doc.

## The real gap, confirmed via direct code read (not assumed)

Three real, live mechanisms exist today, and **none of them bridges "Chronicle recorded this event"
to "an entity now believes a drifted version of it":**

1. **Chronicle has no persisted record class at all.** `ChronicleCompiler.compile()`
   (`src/domains/chronicle/compiler.py:39-88`) is a pure `hierarchy -> (markdown_str, json_dict)`
   render — it reads `campaign_state.narrative_ledger`, groups it via `ChronicleGrouper`, and writes
   `Chronicle.md`/`chronicle.json` as a side effect. There is no `ChronicleRecord` class anywhere in
   `src/` — idea 62's own atlas schema entry (`ChronicleRecord.fidelity`,
   `docs/brainstorm/rpg_expected_schemas.html#schema-62`) names a class that does not exist; it would
   have to be invented, not extended.
2. **`BeliefEntry` already has a decay mechanism, but it decays *confidence*, not *content*.**
   `src/systems/strategic_systems/belief.py`: `BeliefEntry.certainty: float` (0.0-1.0),
   `BeliefCycleSystem.decay_stale_beliefs()` (`belief.py:42-60`) reduces `certainty` based on
   `current_tick - lead.discovered_tick`. This is a real, live, already-shipped decay mechanism —
   but it never touches `BeliefEntry.claim: str`, the actual believed content. A belief with
   `certainty=0.1` and a belief with `certainty=0.9` can carry the *identical* `claim` string. This
   is a genuinely different axis from what idea 62 describes ("a personally-witnessed battle becomes
   a simplified story, then a distorted myth" — the *content* changes, not just the confidence in
   it).
3. **`BeliefEntry.source="rumor"` is fed a caller-supplied string, not derived from Chronicle.**
   `BeliefCycleSystem.process_rumor()` (`belief.py:83-114`) takes `rumor_detail: str` as a parameter
   — whatever the caller already decided to say. Nothing in `src/` today calls `process_rumor()`
   (or anything else) seeded from Chronicle's own recorded events. An entity cannot currently form a
   belief *about a historical Chronicle event* at all, accurate or distorted — there is no path from
   "this happened, Chronicle recorded it" to "this entity now believes something about it."

This confirms the Legacy/Memory proposal's own framing was correct, not merely asserted: the
mechanism this axis needs really doesn't exist anywhere, across three different components that
would each plausibly have carried it.

## Proposed shape: a `TestimonyDeriver`, sibling to `CultureDeriver`/`FameDeriver`

Per the axis proposal's own accepted principle ("Chronicle remains downstream... it renders
recorded events, it does not decide what a future generation currently believes about them"),
fidelity/distortion should **not** be bolted onto Chronicle's own rendering path (that would make
Chronicle stop being a pure downstream renderer, reversing an already-confirmed architectural
decision). Instead, mirror the same 3-layer pattern already established twice this session
(`CultureDeriver` for region-scale culture, `FameDeriver` for entity-scale fame,
`docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md`):

- **Deriver**: `TestimonyDeriver.derive(hierarchy, current_episode) -> Dict[str, float]` — keyed by
  `entry.entry_id` (the existing deterministic dedup key,
  `"{episode}:{tick}:{event_type}:{subject_id}"`, `src/domains/campaigns/state.py:237`), not a new
  key scheme. Computes a `fidelity` value per recorded event as a function of episode-distance:
  `fidelity = decay_fn(current_episode - entry.episode)`. No new event-scoring — reuses
  `entry.significance`/`entry.event_type` only to decide which events are even eligible for
  testimony-tracking (a `calamity` or `entity_death` is worth retelling; a routine
  `faction_shift` may not be), the same "which events feed this axis" judgment call idea 57's own
  doc had to make and disclosed rather than silently resolved.
- **Model**: a small frozen record, `TestimonyRecord(entry_id: str, fidelity: float,
  generations_removed: int)` — deliberately NOT named `ChronicleRecord`, since it is not a Chronicle
  output; it is a derived-downstream fact about one, matching the "Chronicle stays downstream"
  principle by construction, not just by convention.
- **Consumer, not exporter/importer**: unlike `CultureDeriver`/`FameDeriver`, this one has no
  natural CarryForward — `fidelity` is a pure function of episode-distance, recomputable on demand
  rather than needing persistence across episodes (nothing about it depends on prior-episode state
  beyond the ledger itself, which is already durable). The real integration point is **at belief
  formation**: when something (a future ticket's own "hearing a story" mechanic — out of this doc's
  scope, see Open Questions) causes an entity to form a `BeliefEntry` about a historical Chronicle
  event, it should seed `BeliefEntry.certainty` from `TestimonyDeriver`'s `fidelity` value for that
  event instead of a hardcoded constant, and set `source="legend"` (a new, 4th `source` value,
  alongside the existing `"observation"`/`"rumor"`/`"deduction"`) so downstream consumers can tell a
  living memory from an inherited one.

## The real open question this doc does not resolve: content distortion, not just confidence

`fidelity` as scoped above only degrades *how confident* a belief is (extending `BeliefEntry`'s
existing certainty-decay pattern to a new source, at Chronicle-event granularity) — it does **not**
by itself make the *claim string* simplify or distort, which is idea 62's more literal framing ("a
personally-witnessed battle becomes a simplified story, then a distorted myth"). Actually mutating
`claim` text is a real content-generation problem (how do you mechanically "simplify" a sentence?),
not an aggregation-shape problem like the rest of this doc — **explicitly out of scope here**,
flagged as idea 62's own remaining design work rather than invented. A defensible middle ground
worth naming, not resolving: `fidelity` alone (no text mutation) may already be sufficient for
idea 62's actual gameplay hook — if idea 63 ("Belief Grows Around Real History") only needs to know
*how reliable* a legend is to decide whether an institution forms around it, content-string
mutation may never be load-bearing at all. Whoever tickets idea 62 should re-check this against
idea 63's real needs before building text-distortion logic speculatively.

## Second open question: tick-scale decay vs. episode-scale distance, an unresolved unit mismatch

`BeliefCycleSystem.decay_stale_beliefs()` operates on **ticks** (`current_tick -
lead.discovered_tick`, `stale_threshold: int = 50`); `NarrativeLedgerEntry`/`CultureDeriver`/
`FameDeriver` all operate on **episodes**. Campaign episodes are not fixed-length in ticks (each
`EpisodeSummary` runs to its own natural stopping point). A `TestimonyDeriver` producing an
episode-distance-based `fidelity` value, consumed by a tick-based `BeliefEntry` decay system, needs
an explicit conversion rule this doc does not invent — e.g. "N episodes removed maps to floor
certainty of X" is a real design/balance decision (same caution the atlas gives idea 34's own
unanchored numeric thresholds), not something to guess at here.

## What this doc does not resolve (idea 62/63's own remaining scope)

- The actual `decay_fn(generations_removed) -> fidelity` curve — a real numeric/design decision, no
  existing anchor (matches the "free judgment, same caution as idea 34" pattern the schemas doc
  already applies elsewhere).
- Which event types are eligible for testimony-tracking at all (see the Deriver section above) —
  disclosed as an open judgment call, not resolved.
- The actual "hearing a story" trigger mechanic that would call into `TestimonyDeriver` and form a
  `"legend"`-sourced `BeliefEntry` — likely a Perception-system consumer, mirroring idea 57's own
  `discoverable_via: Perception system reference` pattern, but not designed here.
- Whether content-string distortion (vs. confidence-only decay) is actually load-bearing for idea 63
  — flagged above as worth re-checking before building, not assumed either way.

## References

- `docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md` (parent proposal, deliverable #1)
- `docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md` (the sibling-deriver
  pattern this doc reuses)
- `docs/brainstorm/rpg_expected_schemas.html#schema-62` (idea 62's own frozen schema — read-only, not edited)
- `src/domains/chronicle/compiler.py`, `src/domains/campaigns/state.py` (`NarrativeLedgerEntry`)
- `src/systems/strategic_systems/belief.py` (`BeliefEntry`, `BeliefCycleSystem`)
