---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Plan — Mechanism Tier Model (axis → system → mechanism)

> **Status, updated 2026-09-18 — the `system` tier described below was investigated and rejected;
> this doc is kept for its surviving findings, not as a live implementation plan.**
>
> `TCK-20260917-EPIC-MECHANISM-TIER-MODEL` opened with an investigation-first child,
> `TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION`, that derived candidate systems by
> hand from the real dependency graph (§2/§3 below) before any schema work began. The result: **do
> not build the `system` tier as designed, full stop** — not "proceed with changes." A
> proceed-with-changes fallback (multi-root aggregation, letting a system declare several roots) was
> considered and rejected as declared membership in disguise: hand-picking roots until a derived set
> looks right is manual curation wearing the word "derived," which reintroduces the exact
> informally-maintained-truth failure this whole registry effort exists to remove.
>
> **Root cause, stated once**: `depends_on` (§3 below) encodes *prerequisite* — this mechanism cannot
> produce a meaningful result without that one already existing. A `system` encodes *collaboration*
> — these mechanisms work together toward one recognizable capability. No traversal over the first
> relation reliably produces the second. This explains all four bad derived-system fits the
> investigation found (combat missing `tactical_decision`, progression coming out 8-of-9 combat
> mechanisms, economy bottoming out at 2 members, social swinging 4x between two roots) as one
> failure rather than four separate disappointments.
>
> **What still stands, and why this doc isn't deleted**: the §2 `mechanism` tier (already built,
> unaffected) and the naming evidence for `system` over `cluster`/`circuit` remain valid regardless.
> The axis-attachment question §2's table leaves open (does an axis attach to mechanisms or to
> systems?) is answered on independent evidence in
> `TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS`: mechanisms, not systems —
> partly *because* there is no system tier left to attach to, but also because the temporal axis
> proposal's own concerns already span three different candidate systems the investigation tried,
> which would have been awkward under system-level attachment even if the tier had shipped.
>
> Children 2–4 named in the epic below (the `system` schema, the `axis` tier, and the
> proposal-decomposition check) are **permanently undrafted, not deferred** — see the epic's own
> Completion Summary. The `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` precondition named
> throughout this doc remains real and independently valuable: derived priority
> (`generate_mechanism_priority_view.py`) runs on the same `depends_on` edges regardless of whether
> any tier above `mechanism` is ever built.

**Status, scoped 2026-09-17.** The registry records 89 mechanisms. Design proposals arrive as
*axes* — "introduce a spatial axis." Nothing connects the two, so a proposal cannot state what it
will do to the registry, and the registry cannot answer questions asked above the level of a single
node.

This plan defines the tiers between them. It owns the **model and the sequencing**; the two tickets
below own their own implementation detail and are not restated here.

---

## 1. The two questions that motivate it

**"Does combat work?"** No mechanism's verdict answers this. `combat_engagement` is
runtime-verified; `combat_resolution`, `tactical_decision`, `perception` and `trauma` are all
unverified. One node is green and the path is unknown. This question is asked constantly in planning
and is currently unanswerable from the registry.

**"How many mechanisms does this proposal introduce?"** A proposal for a new axis implies several
systems, each implying several mechanisms — some new, some extended, some merely wired or tuned.
Without a route from axis to mechanism there is no way to state that up front, and therefore no way
to check afterwards whether what landed matches what was proposed.

---

## 2. The three tiers

| Tier | What it is | Membership | Backed by |
|---|---|---|---|
| **axis** | a dimension of play — roughly a game sub-genre: spatial, temporal, knowledge-belief | **declared**, overlapping | judgement only |
| **system** | a functional grouping — combat, progression, trade | **derived** from a declared root | declared `depends_on` edges |
| **mechanism** | the existing registry node | already defined | `implemented_by`, validated against disk and symbol |

### The asymmetry is the design, and must not be forgotten

Each tier rests on weaker evidence than the one below it:

- a **mechanism** binds to real code, and a deleted module or renamed symbol fails validation
- a **system** derives from `depends_on`, so it is only as true as edges someone declared
- an **axis** has **no mechanical backing at all** — nothing in the dependency graph knows that
  movement and time-of-day belong to the same dimension of play

State this wherever axes are defined. It is acceptable when visible and dangerous when forgotten,
and forgetting it is precisely how the atlas came to be trusted for years.

---

## 3. Why systems derive and axes do not

A system is a **rooted subtree**: `combat` is the transitive ancestors of `combat_resolution`. One
declared line, membership falls out of the graph, and adding an edge updates it for free. Overlap is
natural rather than a problem — `combat_resolution` belongs to both `combat` and `progression`
because it feeds `xp_leveling`.

An axis is **not a subgraph**. A spatial axis cuts across movement, perception, combat and region;
no dependency relation expresses "these share a dimension of play." So it is hand-declared and
overlapping, with no derivation to lean on.

**Declared membership lists for systems are forbidden.** That would be another hand-maintained
surface, the failure class the registry epic spent eleven tickets removing.

---

## 4. The decomposition model

This is what the tiers are *for*:

```
axis proposal  →  which systems it touches  →  per-mechanism changes, each classified
```

The change taxonomy (Introduce, Extend, Wire, Tune, Split, Retire, Interpose) classifies at the
**mechanism** tier. Proposals arrive at the **axis** tier. Without the middle tier there is no route
between them.

Two consequences:

**It is a free quality gate on proposals.** A proposal that cannot state its registry diff is not
concrete enough to build. That costs one paragraph to test.

**It is mechanically checkable.** Declared diff versus actual diff after landing — a proposal saying
"introduces 3, extends 1" should produce exactly that. Divergence is detectable rather than
noticed.

---

## 5. Rollups report counts, never a badge

A system shows *combat — 6 mechanisms, 1 verified, 0 runtime end-to-end.* **Never a single status.**

A badge reading "combat: partial" would conceal that 5 of 6 members are unverified. The verification
axis exists so that unverified renders visibly rather than being summarised away; a summary badge
rebuilds the atlas's failure one tier higher. The base is thin enough — 26 of 89 bound, 2
runtime-verified — that abstraction would obscure that rather than expose it.

---

## 6. Sequencing

1. **`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`** — first, and it blocks the rest.
   Node boundaries are currently accidental, inherited from atlas cards and directory structure. A
   tier built on accidental boundaries propagates the accident while making it harder to see.
2. **`TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM`** — P2, blocked on the above.

Deliberately *not* blocking `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` (P1) on the
tier work. Coverage is useful independently; only the identity rules precede it, because a split
divides both a binding and a verdict.

---

## 7. Known limitations, recorded before they are discovered

**Derived membership reflects declared edges, not real traffic.** Measured 2026-09-17
(`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`): combat in the corpus worlds is reached
overwhelmingly through movement's opportunity-attack path — 181–2177 calls per 1000 ticks — while
the declared `tactical_decision → combat_resolution` route fires 0–2 times. A derived `combat` system
would describe the declared structure while the dominant real path runs elsewhere.

**`depends_on` semantics are looser in practice than stated.** The rule is *requires to exist in
order to function*. But `combat_resolution` declares both `movement` and `tactical_decision`, and
neither is obviously a prerequisite — both look like execution flow. **Derived priority is computed
from these edges**, so if some are really flow rather than dependency, the "what to fix next"
ranking measures something other than blast radius. Open in the identity-rules ticket.

**Axes cannot be validated.** See §2. There is no check to write.

---

## 8. Non-goals

- **No fourth tier.** Three is what the evidence supports.
- **No derived axes.** Not possible from the dependency graph; do not fake it with heuristics.
- **No retrofitting** every mechanism into a system or axis. Unassigned is a visible gap, not an
  error — same rule as `unverified`.
- **No rolled-up status badges.** See §5.
- **No renaming.** `system` was chosen over `cluster` (70 occurrences in `src/`, a real concept:
  statistical clustering in `observability/mining/`) and `circuit` (`short-circuit` in
  `engine/phase_graph.py`), each a *semantic* collision. `system` collides only with the directory
  `src/systems/`, and mechanisms already map across both that and `src/domains/`. Recorded so it is
  not relitigated.

---

## Related

- `docs/plans/mechanism_registry_initiative.md` — the substrate this builds on
- `docs/plans/mechanism_claims_as_tests_initiative.md` — the checking layer; this is the structural
  one
- `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`,
  `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — implementation detail lives there
