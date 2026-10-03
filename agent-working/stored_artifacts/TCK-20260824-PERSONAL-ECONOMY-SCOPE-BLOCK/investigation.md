---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK
artifact_type: investigation
tags: [economy, cognition]
---

# Investigation — TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK

## Search-tooling note (read first)

Both required Context Scan tools were attempted before any grep/file read, per the Hard Rule:
- `mcp__knowledge-search__search_docs(query="Personal Economy Material Ambition MotivationModel values ValuePreferenceProfile foundation ticket")` returned `{"error": "index not found", "action": "run make knowledge-index"}`.
- Fallback `python3 tools/knowledge_search.py query "Personal Economy Material Ambition MotivationModel values" --top-k 5` returned `knowledge index not found — run make knowledge-index`.
Both are a known pre-existing environment gap this session (index never built), not something this
ticket caused or is scoped to fix. `graphify query "MotivationModel values ValuePreferenceProfile
MotivationBiasService compute_bias_multiplier"` succeeded and returned 123 nodes (BFS depth=2),
confirming `MotivationModel` (cognition.py:440), `ValuePreferenceProfile` (cognition.py:383), and
`MotivationBiasService` (service.py:14) as the primary code targets, plus their existing test nodes
(`test_phase14_bias_service.py`, `test_motivation_bias_culture.py`, `test_phase14_motivation_models.py`,
`test_phase18_cognition_hierarchy_e2e.py`, `test_phase14_motivation_doctrine_scenarios.py`) — all
subsequent grep/read steps targeted exactly these nodes.

## Current Behavior

### ValuePreferenceProfile — all 7 fields default to 0.5 (ticket's claim CONFIRMED)

`src/core/cognition.py:382-402`:

```python
@dataclass(frozen=True, slots=True)
class ValuePreferenceProfile:
    """Value scales (greed, pride, curiosity, caution)."""
    survival: float = 0.5
    reward: float = 0.5
    knowledge: float = 0.5
    loyalty: float = 0.5
    pride: float = 0.5
    curiosity: float = 0.5
    caution: float = 0.5
```

All 7 fields (`survival`, `reward`, `knowledge`, `loyalty`, `pride`, `curiosity`, `caution`) default
to `0.5`. The ticket's claim is verified exactly as stated — no discrepancy found.

`MotivationModel` (`src/core/cognition.py:440-444`) holds `values: ValuePreferenceProfile =
field(default_factory=ValuePreferenceProfile)` (line 443).

### MotivationBiasService.compute_bias_multiplier — delta formula shape confirmed

`src/domains/motivation/service.py:14-72`. The relevant block, `service.py:49-63`:

```python
values = motivation.values
for tag in tags_list:
    if tag in ("recovery", "flee", "caution"):
        multiplier += (values.survival - 0.5) * 0.5
    elif tag in ("cooperation", "help", "party"):
        multiplier -= (values.pride - 0.5) * 0.5
    elif tag in ("exploration", "research", "intel", "knowledge"):
        multiplier += (values.curiosity - 0.5) * 0.5
    elif tag in ("gold", "chest", "loot", "reward"):
        multiplier += (values.reward - 0.5) * 0.5
```

Confirmed `(values.X - 0.5)` delta shape exactly as the ticket states, for 4 of the 7 fields
(`survival`, `pride`, `curiosity`, `reward`). **Additional finding not in the ticket's own prose**:
3 of the 7 `ValuePreferenceProfile` fields — `knowledge`, `loyalty`, `caution` — are never read
anywhere in `compute_bias_multiplier` at all (confirmed by grep: no `values.knowledge`,
`values.loyalty`, or `values.caution` reference exists in `src/`). These three fields are currently
fully inert regardless of the dead-on-arrival defaults issue — a second, narrower dead-code fact
worth carrying into the eventual foundation ticket's scope, since populating them would still do
nothing until `compute_bias_multiplier` is also extended to read them.

### Production construction sites — ZERO non-default values anywhere in src/

Grep of `MotivationModel(` and `ValuePreferenceProfile(` across the whole `src/` tree:

```
$ grep -rn "MotivationModel(" src/
$ grep -rn "ValuePreferenceProfile(" src/
```

Both return **zero matches** in `src/`. The only production construction of the containing
`CognitionModel` is `src/core/builder.py:111`:

```python
self._cognition = CognitionModel()
```

Zero-argument construction, which recursively default-factories `MotivationModel()` →
`ValuePreferenceProfile()` → every field `0.5`. This is the single entity-construction path found
in production code (confirmed via `graphify query`'s node list and `grep -rn "CognitionModel(" src/`
— only one hit, at `builder.py:111`).

Every non-default construction site found anywhere in the repository is in `tests/`, none in `src/`:

- `tests/unit/domains/motivation/test_phase14_bias_service.py:24-28` — `ValuePreferenceProfile(...)` then `MotivationModel(values=values)`
- `tests/unit/domains/motivation/test_phase14_motivation_models.py:19` — `ValuePreferenceProfile()` (default, unused for this claim)
- `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py:18-19` — `ValuePreferenceProfile(survival=0.8)`, `MotivationModel(doctrine=doctrine, values=values)`
- `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py:20,35` — `ValuePreferenceProfile(survival=0.6, reward=0.8, pride=0.7)` and `ValuePreferenceProfile(survival=0.8, reward=0.4, pride=0.3)`
- `tests/unit/motivation/test_motivation_bias_culture.py:17` — `MotivationModel(doctrine=doctrine)` (values left at default; only doctrine is non-default here)

**Mathematical consequence**: since every production entity's `motivation.values` fields are all
exactly `0.5`, `(values.X - 0.5)` evaluates to `0.0` for all 4 consumed fields, for every entity, on
every call, in every real run. The Value Preference Profile branch of `compute_bias_multiplier`
(lines 55-63) is therefore always a no-op multiplier contribution (`+= 0.0` / `-= 0.0`) in production.
Only the Doctrine branch (lines 43-47, driven by `preferred_route_tags`/`avoided_route_tags`, which
ARE populated with non-default values via `DoctrineResolver`/content) and the optional Cultural
overlay branch (lines 65-70, transient, never touches `ValuePreferenceProfile`) produce non-zero
multiplier effects today. This independently confirms the ticket's dead-on-arrival claim with
concrete file:line evidence rather than trusting the ticket's own prose.

### No foundation ticket exists for populating MotivationModel.values

Grep across `tickets/`, `docs/`, `stored_artifacts/` for `MotivationModel.values` /
`ValuePreferenceProfile` turned up 15 files. None is a foundation ticket to populate
`ValuePreferenceProfile` above defaults in production call sites. What exists instead:

- `tickets/done/TCK-20260619-E62C-MOTIVATION-OVERLAY.md` + `stored_artifacts/TCK-20260619-E62C-MOTIVATION-OVERLAY/investigation.md` — added the *transient* cultural overlay (`CulturalBiasApplicator`) that adds an additive delta on top of `compute_bias_multiplier`'s result; explicitly does **not** write to `ValuePreferenceProfile`/`MotivationModel` (see `src/domains/culture/applicator.py:7-8`: "It does not modify ValuePreferenceProfile or MotivationModel on the entity."). Its own investigation.md (line 13) only enumerates 4 of the 7 `ValuePreferenceProfile` fields (`survival, reward, pride, curiosity`), consistent with only having looked at the fields the bias service reads — it does not surface the dead-defaults problem as a blocker.
- `tickets/done/TCK-20260619-E62-CULTURE-DRIFT.md` + its stored investigation — same culture-overlay work, references `ValuePreferenceProfile` only as the attach point for the transient overlay, again not as a defaults-population effort.
- `tickets/done/TCK-20260529-COG-PHASE14-MOTIVATION.md` — original Phase 14 ticket that introduced `MotivationModel`/`ValuePreferenceProfile`/`MotivationBiasService`; defined the schema and defaults, not a population effort.
- `tickets/done/TCK-20260610-MOTIVATION-PRESSURE-RESOLVER.md` — adds `MotivationPressureResolver` consuming `need_profile`/`drive_profile` from catalog data; a different mechanism (needs/drives, not `ValuePreferenceProfile`), does not touch `values`.
- `tickets/done/TCK-20260628-E52F-TRAUMA-MOTIVATION.md` — wires regional `trauma_score` into `DANGER` `ConcernState` injection; also a different mechanism, not `ValuePreferenceProfile`.
- `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md:115-119,132-133,148` — Idea 24 (Personal Economy & Material Ambition) is the *origin* of this exact blocker; explicitly states the foundation ticket "is not part of this epic" and its Open Questions (line 148) leave unresolved whether the blocker gets its own ticket inside or outside the epic.
- `docs/plans/rpg_design_roadmap/rpg_direction_alignment_audit.md`, `docs/archive/entity-enhance/entity_enhance_phase11_18.md`, `docs/archive/core/entity_base.md`, `docs/brainstorm/rpg_feature_atlas.html`, `docs/parity_ledger/world_dynamics.yaml` — background/history mentions of the `MotivationModel`/`ValuePreferenceProfile` schema, none scope a population effort.
- `tickets/todos/embedding-latent-cognition/TCK-20260822-CULTURE-CROSS-REGION-CONVERGENCE.md` — explicitly requires the cultural overlay to *stay* transient and NOT be baked into durable `MotivationModel`/`ValuePreferenceProfile` state; not a population effort, and actually reinforces that the overlay pattern is deliberately kept separate from the durable defaults.

**Conclusion: confirmed — no foundation ticket for `MotivationModel.values` exists anywhere in
`tickets/`, `docs/`, or `stored_artifacts/`.** This ticket's Related Tickets section is accurate.

### Duplicate ticket file (anti-drift hazard, not this ticket's to fix)

`tickets/todos/m1-quick-wins/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` and
`tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` are byte-identical (`diff` returns
no output). Per the Workflow Rule's "After Work" step ("If the ticket originated in a
`tickets/todos/{folder}/` subfolder: Delete the source file from the subfolder"), the `todos/`
duplicate must be deleted at Finalize once this ticket closes — flagged here so it isn't missed
(a known recurring gap pattern in this repo per prior hand-orchestration feedback).

## Mechanics / Engine Constraints

`docs/mechanics/04_strategic_cognition.md` currently has **zero** references to `MotivationModel`,
`ValuePreferenceProfile`, or `MotivationBiasService` (confirmed by grep — no matches). The Motivation
sub-model exists in code (`src/core/cognition.py`) and is owned per
`docs/architecture/cognition_domain_ownership.md:18` (`MotivationModel` → `cognition.motivation` →
`src/domains/motivation/`), but the Mechanics Bible chapter that should document its laws does not
cover it at all today. This is a pre-existing documentation gap independent of this ticket — this
scope-only ticket does not change any behavior, so it does not trigger the Authoritative Mechanics
Rule's "if logic changes, update the doc" obligation. The gap is relevant context for whichever
future foundation ticket populates `ValuePreferenceProfile`: that ticket's own Docs Requiring Update
will need to add a Motivation/values section to `04_strategic_cognition.md` for the first time,
since none exists to update today.

## Docs Requiring Update

None. This ticket is scope-only and BLOCKED: it makes no behavior change, adds no code, and its own
Acceptance Criteria are entirely about ticket-body content (scoping the target design, naming the
blocking dependency, recording the verified dead-on-arrival fact, setting Status to BLOCKED). No
`docs/` path needs to change for *this* ticket's own closure.

The following docs were checked and are explicitly NOT required to change for this ticket:

The `docs/mechanics/04_strategic_cognition.md` chapter (path: `docs/mechanics/04_strategic_cognition.md`)
is not required to change now — see Mechanics / Engine Constraints above. It has no existing
Motivation/values coverage to update, and this ticket adds no new behavior for it to describe; that
obligation belongs to the future foundation ticket once `ValuePreferenceProfile` is actually
populated (the ticket's own Conditional/Deferred AC already states this explicitly).

The `docs/architecture/cognition_domain_ownership.md` doc (path:
`docs/architecture/cognition_domain_ownership.md`) already correctly lists `MotivationModel` →
`src/domains/motivation/` ownership and needs no change — this ticket does not alter ownership.

The `docs/parity_ledger/strategic_cognition.yaml` and `docs/parity_ledger/world_dynamics.yaml`
files (checked for any `MotivationModel`/`ValuePreferenceProfile`/`MotivationBiasService` entries —
see Parity Ledger Overlap below) are not required to change: the one relevant entry found
(`WORLD-CULT-002`) is about the transient cultural overlay staying non-durable, which remains true
and unaffected by this ticket, and no entry exists yet for the dead-on-arrival `ValuePreferenceProfile`
defaults themselves — creating that entry is also deferred to the eventual foundation ticket, which
is the one that would actually change the `status`/`v2_evidence` a ledger entry tracks.

The `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md` epic doc (path:
`docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md`) already documents this exact blocker at
Idea 24 (lines 115-119, 132-133, 148) and does not need editing by this ticket — this ticket's job is
to exist as the epic's own Open Question (line 148) anticipated, not to rewrite the epic doc.

## Parity Ledger Overlap

- `WORLD-CULT-002` (`docs/parity_ledger/world_dynamics.yaml:1196-1210`), status `verified`,
  priority `P1`: "Cultural bias overlay is transient ... it never writes to entity durable state
  (MotivationModel, ValuePreferenceProfile, EntityState)." This entry is about the E62C overlay
  staying non-durable, not about the `ValuePreferenceProfile` defaults themselves — it remains
  accurate and unaffected by this ticket. Not P0, no action required.
- No parity ledger entry anywhere (`strategic_cognition.yaml`, `world_dynamics.yaml`, or any other
  subsystem file) currently tracks the dead-on-arrival state of `ValuePreferenceProfile` defaults or
  the fact that `compute_bias_multiplier`'s Value Preference branch is a permanent no-op in
  production. Creating that entry belongs to the future foundation ticket (it is the one that would
  change ledger `status`/`v2_evidence`, per the Authoritative Mechanics Rule), not to this scope-only
  ticket.

## Prior Work

- `stored_artifacts/TCK-20260619-E62C-MOTIVATION-OVERLAY/` (investigation.md, plan.md, test_plan.md)
  — added the transient `CulturalBiasApplicator` overlay on top of `compute_bias_multiplier`'s
  result. Confirms the same 4-field subset of `ValuePreferenceProfile` this investigation found
  actually consumed (`survival, reward, pride, curiosity`), and confirms the overlay pattern
  (stateless service, additive bounded delta, computed per-call, never written to durable state) —
  directly reusable as a design precedent for the Target Design Sketch below.
- `stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/` — same E62 initiative; documents
  `ValuePreferenceProfile` as "the" attach point for value-scale overlays region-wide.
- `tickets/done/TCK-20260529-COG-PHASE14-MOTIVATION.md` — original schema-defining ticket for
  `MotivationModel`/`ValuePreferenceProfile`/`MotivationBiasService`; establishes the 0.5-default
  convention this ticket's dead-on-arrival claim depends on.
- No prior investigation anywhere already documents the dead-on-arrival fact with file:line
  evidence — this is the first artifact in the repo to do so at this level of detail (the E62C
  investigation came close by listing 4 of the 7 field names, but did not flag the zero-production-
  construction-sites fact or state the mathematical no-op consequence).

## Risks and Open Questions

- **Open, blocking**: the M1 epic doc itself (line 148) leaves unresolved whether the future
  foundation ticket for `MotivationModel.values` belongs inside this epic or a different
  milestone/epic. This ticket does not resolve that question (correctly, per its own Out of Scope)
  — flagging again here so it is not silently dropped. Whoever files the foundation ticket needs to
  make that milestone/epic placement call.
- **Risk if unblocked prematurely**: if a future session starts implementing the Personal Economy
  axis directly against `ValuePreferenceProfile` without first landing the foundation ticket, the
  new axis would join the same dead-on-arrival state — populated in the dataclass but never
  constructed with non-default values in `src/core/builder.py`'s single production entity-
  construction path, producing another permanently-zero delta. The Conditional/Deferred ACs in the
  ticket already guard against this by requiring the foundation ticket to land first.
- **Scope-narrowing risk**: 3 of 7 `ValuePreferenceProfile` fields (`knowledge`, `loyalty`,
  `caution`) are inert in `compute_bias_multiplier` today independent of the defaults problem (never
  read at all). If the foundation ticket populates only `values` construction but not
  `compute_bias_multiplier`'s field coverage, a Personal Economy axis mapped onto one of those three
  unread fields would still produce zero effect after the foundation ticket lands. The Target Design
  Sketch below explicitly recommends against reusing an unread field for this reason.
- No open question blocks *this* ticket's own scope-only closure — the two open items above are
  scoped to the eventual foundation/implementation tickets, not to this one.

## Anti-Drift Hazards

- Do not let a future session "helpfully" start wiring `values` construction into
  `src/core/builder.py` under this ticket — that is explicitly Out of Scope (foundation-ticket
  territory) and this ticket's own AC requires zero `src/` changes while BLOCKED.
- Do not let the Target Design Sketch below be read as authorization to design the
  content-schema/emergent-derivation mechanism for populating `MotivationModel.values` broadly —
  that belongs to the separate foundation ticket per this ticket's own Out of Scope. The sketch here
  is narrowly for how the Personal Economy axis itself would attach and be weighted *once* that
  foundation exists, not how the foundation populates values generally.
- The `tickets/todos/m1-quick-wins/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` duplicate (see
  Current Behavior above) must be deleted at Finalize per the Workflow Rule — don't let it linger as
  a stale skeleton after this ticket moves to `tickets/done/`.
- Don't conflate this ticket's dead-on-arrival finding with the *doctrine* branch
  (`preferred_route_tags`/`avoided_route_tags`, `service.py:41-47`) or the *cultural overlay* branch
  (`service.py:65-70`) of `compute_bias_multiplier` — both of those are populated/live today and are
  explicitly out of scope for the dead-on-arrival claim, which is scoped only to the
  `ValuePreferenceProfile` branch (lines 49-63).

## Target Design Sketch for Personal Economy & Material Ambition axis

This sketch documents intent only — no code, and it does not start until the not-yet-existing
`MotivationModel.values` foundation ticket has landed and `ValuePreferenceProfile` is populated with
non-default values in production call sites (per this ticket's Conditional/Deferred ACs).

**What the axis represents**: a per-entity scalar (`0.0`–`1.0`, same convention as the existing 7
fields, default `0.5` = neutral) capturing how strongly an entity values personal material
accumulation and economic self-advancement as an end in itself — distinct from `reward` (which today
reads as generic loot/gold/chest desirability) by being about durable *possession and status*
(property, stockpiled goods, market position) rather than momentary route-tag gain. Framed this way
it should be added as a genuinely new 8th field (e.g. `material_ambition: float = 0.5`) rather than
overloaded onto the existing `reward` field, to avoid silently changing `reward`'s established
semantics and its existing consumer in `compute_bias_multiplier` line 62-63.

**How the value would be derived/weighted** (once the foundation ticket's population mechanism
exists): the foundation ticket is expected to define *how* `ValuePreferenceProfile` fields get
populated above 0.5 in production (content-schema-driven, emergent-derivation, or another mechanism
— explicitly not decided here, per Out of Scope). Whatever that mechanism is, `material_ambition`
should be a consumer of it like the other 6 fields, not a special case — e.g. if the foundation
ticket derives `survival`/`curiosity`/etc. from a content-schema seed value plus emergent drift, the
same pipeline should seed `material_ambition` rather than inventing a parallel derivation path.

**What inputs it would read**: candidates for eventual derivation inputs (for the *foundation*
ticket to decide, not this one) include entity class/archetype seed data (a merchant-leaning
archetype starting higher), accumulated wealth/inventory value over time (an emergent feedback loop
mirroring the E52F trauma→motivation pattern at `tickets/done/TCK-20260628-E52F-TRAUMA-MOTIVATION.md`,
where a durable world signal feeds into a `ConcernState`/motivation-adjacent value), or doctrine
content tags. This sketch does not pick one — it only asserts that whichever input the foundation
ticket chooses, `material_ambition` should be wired the same way as the other fields, not bespoke.

**How `compute_bias_multiplier` would consume it**: following the exact existing pattern at
`service.py:49-63` (one new `elif` branch, same `(values.material_ambition - 0.5) * WEIGHT` delta
shape, same tag-bucket structure) rather than a structural rewrite:

```
elif tag in ("property", "stockpile", "market", "invest", "hoard"):
    multiplier += (values.material_ambition - 0.5) * 0.5
```

The exact tag vocabulary (`property`, `stockpile`, `market`, `invest`, `hoard` above are illustrative,
not final) and the `0.5` weight coefficient (matching the existing 4 branches' coefficient) would be
finalized in the real implementation ticket's plan.md, informed by whatever economy-domain route
tags already exist in `src/systems/` (not audited here — out of this scope-only ticket's
investigation). The optional `culture_values` overlay branch (lines 65-70) is a separate, transient
mechanism (`CulturalBiasApplicator`) and is not the attach point for this axis — `material_ambition`
belongs in the durable `ValuePreferenceProfile` branch, consistent with the ticket's own framing of
it as a `MotivationModel.values` axis, not a cultural overlay.

**Explicit non-goal of this sketch**: it does not specify the content-schema/emergent-derivation
population mechanism itself (per Out of Scope) — only how the axis, once populated by whatever
mechanism the foundation ticket builds, would be named, defaulted, and consumed by
`compute_bias_multiplier`, matching the existing 4-field pattern exactly so the eventual
implementation ticket has a concrete, low-risk shape to follow rather than reinventing the branch
structure.
