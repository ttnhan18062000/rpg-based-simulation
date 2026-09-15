---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-PRIORITY-DERIVATION
artifact_type: investigation
tags: [architecture, documentation, schema]
---

# Investigation — TCK-20260915-MECHANISM-PRIORITY-DERIVATION

## Current Behavior

`docs/brainstorm/mechanisms.yaml` (75 mechanisms, `verified` block added by
`TCK-20260915-MECHANISM-VERIFICATION-AXIS`) has no priority derivation and no generated charts.
`tools/mechanism_registry.py`'s `MechanismRegistry.dependents_of()` already computes direct
dependents by traversal (built by the Foundation ticket) — this ticket's own scope needs
*transitive* dependents (see decision below), which is a new computation, not a rename of the
existing one. `docs/brainstorm/rpg_simulation_wiring_map.html` has 3 hand-authored mermaid
diagrams with hand-maintained `classDef live`/`classDef bug`/`classDef gated`/`classDef proposed`
state-color assignments.

## Real Finding: this ticket's own reframing (peer review, following T2's own seed)

T2's own 6-verdict seed produced the epic's first real finding: 69 of 75 mechanisms have never
been verified, and only 1 has *runtime* verification. Per peer review, this ticket is reframed
around that finding's own natural consequence: a priority ranking over all 75 mechanisms is mildly
interesting; a priority ranking over the **69 unverified** mechanisms answers the real question —
*which one do we verify next?* Concretely: the priority-derivation function and its primary
generated view should surface unverified mechanisms first, ordered by `rank × dependents`, since a
hub mechanism nobody has verified is the highest-value next target (more depends on it, so it is
where an unverified mechanism is most expensive if it turns out wrong).

## Decision: transitive dependent-count, confirmed against real data

Computed both direct and transitive dependent-count against the real 75-mechanism graph (direct
DFS/BFS traversal for transitive, since the graph is confirmed acyclic by Foundation's own
validator — a DAG guarantees termination):

| id | direct | transitive |
|---|---|---|
| `action_pacing_readiness` | 7 | 23 |
| `tactical_decision` | 2 | 14 |
| `combat_engagement` | 1 | 13 |
| `combat_resolution` | 3 | 12 |
| `betrayal_siege_war` | 3 | 11 |
| `cognition_capacity_fatigue` | 2 | 9 |
| `trauma` | 1 | 8 |
| `perception` | 1 | 8 |
| `regional_trauma_hazards_sovereignty` | 5 | 8 |

**Hub count is identical either way — 26 mechanisms have `direct > 0`, and the same 26 have
`transitive > 0`.** Peer's own concern (that transitive counting might collapse the 26 hubs into a
handful of "super-hubs") did not materialize — every mechanism with any transitive dependents also
has at least one direct dependent, by definition, so the set doesn't shrink.

**But the ranking is meaningfully different, not just scaled.** `combat_engagement` (1 direct
dependent) and `tactical_decision` (2 direct) both rank far higher transitively (13/14) than their
direct counts alone would suggest, because their own dependents (`combat_resolution`) are
themselves hubs with many further dependents. `regional_trauma_hazards_sovereignty` (5 direct, the
2nd-highest direct count in the whole graph) ranks comparatively lower transitively (8) — its
direct dependents are mostly leaves with few further dependents of their own.

**Decided: transitive** (peer confirmed). Matches the stated intent ("how much breaks if this is
wrong") on real data — direct count would badly undercount blast radius for exactly the mechanism
(`combat_engagement`) where getting the priority wrong matters most: 1 direct dependent would rank
the project's single most-verified, most-central mechanism near the bottom, while 13 transitive
dependents correctly reflects its real centrality.

## Reframing per peer review: priority over the 69 unverified, not all 75

The primary generated view is a priority ranking over the **69 currently-unverified** mechanisms
(the direct consequence of T2's own seed finding — 69 of 75 mechanisms have no recorded verdict),
not an abstract ranking over the full 75. The real question this answers: *which unverified
mechanism should be verified next?* The 26-hubs/49-leaves shape from T2 works in this view's favor
— a hub mechanism nobody has verified is the highest-value next target, since more depends on it.

## Real Finding: the `entity` layer alone exceeds the readability threshold

| layer | mechanism count |
|---|---|
| entity | 43 |
| world | 12 |
| faction | 11 |
| region | 7 |
| group | 2 |

The `entity` layer alone has 43 mechanisms — already past the ~40-node mermaid readability rule of
thumb by itself, before any dependency edges are even drawn. Acceptance Criteria #5's "a view that
would [exceed the threshold] must fail or paginate rather than emit an unreadable diagram" is a
real, immediately-hit case for the single most common view type (single-layer), not a rare edge
case to handle defensively. Pagination is built for this real case (see plan.md).

**But per peer review, pagination is the safety net, not the recommendation.** If a slice is
unreadable at its natural size, that itself is evidence the slice isn't answering a question
anyone actually has — for `entity` specifically, the useful views are the unverified-priority
ranking, top-N by dependents, and ancestors-of-X, all naturally bounded regardless of layer size.
Whole-layer-`entity` is not built as this ticket's flagship view; it exists (with pagination) for
completeness, not as the primary way anyone is expected to read the `entity` layer.

## Real Finding: mermaid rendering has no embedded script or committed image

Grepped `docs/brainstorm/rpg_simulation_wiring_map.html` for any `<script` tag: **none exist,
anywhere in the file.** The three `<pre class="mermaid">` blocks are rendered by nothing embedded
in the document itself — no client-side mermaid.js include, no committed static image as a
fallback.

**Followed up per peer's own suggestion**: checked whether `make docs-serve`/`make docs-build`
(this repo's real Docusaurus-based doc pipeline) renders these files before concluding anything.
It does not: `website/docusaurus.config.js`'s docs plugin has a `path`/`exclude` config for
`docs/brainstorm/` content (`brainstorm/**` is not excluded), but Docusaurus's classic docs plugin
only globs `**/*.{md,mdx}` by default and this repo's config has no `include:` override — `.html`
files are never picked up as doc pages at all, and `docs/brainstorm/*.html` is not under
`website/static/` either, so there is no passthrough path copying it into the built site verbatim.
No `@docusaurus/theme-mermaid` (or equivalent) plugin is configured either. **Net conclusion: these
diagrams likely have never rendered for anyone viewing them through this repo's own real
documentation infrastructure** — a genuine, separate defect, not folded into this ticket (per
peer's own instruction). Filed `TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS`.

This does not block this ticket's own new generated views, which are built with their own
rendering-path assumption stated explicitly rather than inherited silently from the wiring map's
own (apparently broken) one — see plan.md.

**`BT` vs `TB` subgraph layout — attempted a real empirical test, could not complete it visually.**
Published a test artifact (3 mermaid diagrams: the wiring map's own `TB`-with-subgraph-lanes
pattern reproduced, the identical structure re-rendered as `BT`, and a larger BT test closer to a
real mechanism-dependency slice) specifically to check this directly rather than assume. **This
session has no way to visually inspect a rendered artifact's own output** — publishing succeeds,
but there is no available tool to view the resulting image. Proceeding on general Mermaid
engine reasoning instead: `BT` is computed by the same dagre-based layout engine as `TB`, simply
inverted — there is no documented Mermaid limitation specific to subgraph-lane layout under `BT`
versus `TB`; the known Mermaid subgraph pitfall is direction *overrides inside* a subgraph
conflicting with the parent direction, which applies identically regardless of whether the parent
is `TB` or `BT`. This is reasoning from general engine behavior, explicitly not a visual
confirmation — peer independently confirmed they also cannot visually inspect a rendered artifact
(same tool limitation), and is surfacing the artifact link to the user for an optional ten-second
look. **Implemented as a parameter, not a literal**, per peer's own suggestion: the generator's
direction defaults to `BT` but is a config value, so reversing it later is a one-line config
change, not a code edit — treated as cheaply reversible, not a hard blocker on shipping this
ticket.

## Scope Item 3, Resolved (peer review): the ticket's own wording overstated its intent

**"Replace the wiring map's hand-authored charts with generated ones"** — investigated the wiring
map's own 3 existing diagrams directly before assuming what "replace" means:
- **Layer Model** (line 275): CONTAINMENT (`ENT ==> GRP`, "Faction contains Entities").
- **Entity Operating Loop** (line 447): TICK EXECUTION ORDER (`PER --> SELF --> BEL`, what happens
  before what within one tick).
- **Entity Lifecycle Arc** (line 606): STATE TRANSITIONS (`AL --> WD`, a per-entity lifecycle
  state machine, not a mechanism-dependency graph at all).

None of these three diagram *types* is a dependency graph — the registry's own `depends_on` field,
and the priority-derivation charts this ticket builds from it, represent a fourth, different axis.
The design doc's own Finding 3 ("Containment is not dependency... Only the latter drives priority")
already establishes this.

**Confirmed by peer: the ticket's own verb was wrong, not this reading.** The ticket's parenthetical
— "(its `classDef live`/`classDef bug` assignments)" — was the actual intent; "replace... charts"
was not. Replacing the three diagrams with dependency charts would destroy real information.
**Settled:**
- The three existing diagrams stay, topology untouched.
- Only the `classDef` state coloring derives from the registry's `state` field at generation time
  (a small transform: `state` → mermaid `classDef` name) — this alone is the fifth hand-maintained
  state surface being removed.
- The dependency/priority charts are a new, additive artifact serving a different question
  (verification targeting), not a replacement for any of the three.

**The generalization worth recording, per peer's explicit request — this is what stops the epic
from over-reaching, and will matter again at T4:** this investigation has now identified **four
distinct axes over the same mechanism node set** — containment (Layer Model), execution order
(Entity Operating Loop), lifecycle transitions (Entity Lifecycle Arc), and dependency (the
registry's own `depends_on`, built by Foundation, consumed by this ticket). The mechanism registry
captures exactly **one** of these four. It does not supersede the other three, and it should not —
a future attempt to make the registry "the single source of truth for the graph" (collapsing all
four axes into one) should be refused on this basis, the same way this ticket refused to collapse
containment/execution-order/lifecycle into dependency just because one file happened to hold all
four kinds of information. Each axis answers a genuinely different question and none of the other
three is expressible in terms of `depends_on`.

## Step 3's own measured result: the epic's second measured finding, not just infrastructure

Systematically compared every one of the 24 mechanism-mapped nodes in the Entity Operating Loop
diagram against the real registry `state` before touching anything (see Step 3 in plan.md for the
full per-node table). **4 of 24 (17%) were wrong.** Combined with Foundation's own two stale atlas
badges, this is the second time this epic has *measured* the disagreement problem it exists to
solve in a real artifact, rather than asserting it in the abstract. `combat_engagement` is the
sharpest instance: the diagram still read "GATED OFF by default" the day after Foundation's own
work in this same session had already confirmed it went live-by-default (2026-09-14) — stale text,
not just a stale color, fixed as both.

**Real cost worth recording, per peer review, not just the fix's own benefit.** Until this fix,
five artifacts disagreed — and the disagreement, however unreliable, was itself a signal:
`commitment_betrayal`'s own cross-document disagreement (Foundation's Judgment Call 6) was findable
*because* two documents said different things about it. Resolving it in the registry's favor here
removes that accidental signal. **Consolidation concentrates risk**, not just noise: if the
registry is right, five-way disagreement was pure overhead eliminated cleanly; if the registry is
ever wrong on some mechanism, everything downstream of it (this diagram included, after this fix)
is now uniformly wrong with no disagreement left to surface it. This is not an argument against
consolidating — the old disagreement signal was accidental and nobody was actually monitoring it —
but it is the reason the verification axis (T2) matters *more* after this fix, not less: it is the
deliberate replacement for the accidental safety this ticket's own consolidation just removed. The
69-unverified figure (T2's own finding) is the honest statement of how much of the registry is
currently unchecked against reality — worth keeping visible precisely because five-source
disagreement no longer is.

## Prior Work

- `staging_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/`,
  `staging_artifacts/TCK-20260915-MECHANISM-VERIFICATION-AXIS/` — this ticket's own two
  dependencies; extends both rather than building from scratch.
- `docs/plans/mechanism_registry_initiative.md` §3 (chart generation) and §4 (open questions) —
  the plan doc this ticket's own Related Docs section cites; §4's questions 1-2 are this
  investigation's own subject.

## Docs Requiring Update

- `docs/brainstorm/rpg_simulation_wiring_map.html` — pending the scope-3 confirmation above: at
  minimum, the 3 existing diagrams' `classDef` state-color assignments should derive from the
  registry rather than stay hand-maintained. New generated view files (location decided in
  plan.md) are new docs, not updates to existing ones.

## Parity Ledger Overlap

None. No logic/mechanics change.

## Assumptions / Open Questions

1. **Scope item 3's real meaning** — flagged above, pending peer confirmation.
2. **BT rendering** — reasoning-based decision, not visually confirmed; flagged as cheaply
   reversible.
3. Per the ticket's own Assumption #2 (multiply vs primary-sort-key): resolved by the ticket's own
   stated formula (`priority = rank × dependents`) — a multiply, not a two-key sort. Checked
   against the real data: this does let a heavily-depended-on faction/world mechanism outrank a
   leaf entity mechanism (e.g., `betrayal_siege_war`, faction rank 3 × 11 transitive dependents =
   33, could outrank a rank-1 entity leaf with a handful of dependents) — this is the ticket's own
   explicit design intent ("may be correct or may violate the bottom-up rule... check against a
   known-correct ordering"), not an accident; recorded as intentional rather than re-litigated.
