---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-WOUND-HEALING-DECISION
artifact_type: investigation
tags: [combat]
---

# Investigation — TCK-20260824-WOUND-HEALING-DECISION

## Current Behavior

**Decision context (already made by the ticket owner, not re-litigated here): Option (b) — wounds
are intentionally permanent until a Scar forms via a separate, later mechanic
(`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`, not implemented by this ticket).** This section
documents the evidence that supports declaring the current healing code dead-by-design.

### 1. `WoundService.heal_wound()` — dead code, zero production callers
`src/engine/rpg_depth.py:187-200`:
```python
@staticmethod
def heal_wound(wound) -> Tuple:
    """Heal a wound and create a scar. Returns (healed_wound, scar)."""
    # VERIFIED v2: scar_permanence_logic
    from src.core.state import WoundState, ScarState
    healed = replace(wound, healed=True, scar_created=True)
    scar = ScarState(
        id=f"scar_{wound.id}", wound_kind=wound.kind, tick_created=wound.tick_inflicted,
        atk_penalty=wound.atk_penalty * 0.3, def_penalty=wound.def_penalty * 0.3,
        speed_penalty=wound.speed_penalty * 0.3,
    )
    return healed, scar
```
Full-repo search (`grep -rn "heal_wound" src/ tests/`) found exactly six matches: the definition
itself (line 187) and five call sites, **all in `tests/unit/core/test_rpg_depth.py`**
(`TestScarPermanence.test_scar_permanence` L238, `test_scar_lesser_penalty` L247,
`test_scar_cumulative_penalties` L255-256, and `TestSkillScaling.test_effective_stats_with_scars`
L482, which uses `heal_wound()` only to manufacture a `ScarState` fixture). **Zero callers in
`src/`.** It is never invoked from `combat.py`, `patches.py`, `apply.py`, or any AI/goal producer —
nothing in the production code path ever calls it.

### 2. `MedicalService.get_diagnosis_quality()` — dead code, zero production callers
`src/engine/rpg_depth.py:272-282`:
```python
class MedicalService:
    """Wisdom-based medical diagnosis and healing quality."""

    @staticmethod
    def get_diagnosis_quality(wis: int) -> float:
        """Calculate diagnosis accuracy (0.0 to 1.0)."""
        # Linear scaling: 10 Wisdom = 50% accuracy, 20 Wisdom = 100%
        return min(1.0, wis * 0.05)
```
Full-repo search (`grep -rn "get_diagnosis_quality" src/ tests/`) found exactly **one match: the
definition itself.** Zero callers anywhere, including in tests — no unit test even exercises this
method directly. `MedicalService` is a standalone one-method class; nothing constructs or invokes
it outside its own definition.

### 3. `get_diagnosis_quality()`'s pipeline membership: belongs to a never-built healing pipeline, not a separately-dead subsystem
`MedicalService` lives in the same "Discovery and Medical Services" section of `rpg_depth.py`
(`src/engine/rpg_depth.py:259-282`, comment header `# ─── Discovery and Medical Services
──────────────────────────────── (Task 10.1, 10.2)`) alongside `DiscoveryService`
(perception-based interaction, which **is** live — see `get_discovery_threshold` consumers
elsewhere). `MedicalService.get_diagnosis_quality(wis)` returns a 0.0-1.0 accuracy score whose only
plausible consumer, by name and docstring ("diagnosis accuracy," "healing quality"), is a
Wisdom-gated healing-success/quality roll — i.e. it would feed a hypothetical `heal_wound()` call
site that decided whether/how well a heal succeeds based on the healer's WIS. No such call site was
ever built. `docs/mechanics/01_entity_anatomy.md`'s attribute table (Section 1, not Section 6)
still lists `Wisdom (WIS) | Healing quality and tactical decision-making.` — this is the only doc
reference tying WIS to "healing quality," and it describes the same never-realized pipeline.
**Conclusion: `get_diagnosis_quality()` is dead for the *same* reason `heal_wound()` is dead — it is
an unfinished half of the identical never-wired healing pipeline, not a separate medical/diagnosis
subsystem that failed for unrelated reasons.** There is no other "diagnosis" concept in the
codebase it could belong to instead.

### 4. Ambiguous "when a wound heals" phrasing — exact current text
`docs/mechanics/02_combat_laws.md:85` (end of "## 5. Wound Infliction"):
> `- Permanent Scars: when a wound heals, it has a 30% chance to leave a scar (`scar_penalty =
> wound_penalty * 0.3`).`

`docs/mechanics/01_entity_anatomy.md:169-173` (end of "## 6. Trauma: Wounds & Scars", subsection
"### Permanent Scars"):
> `When a wound is healed, it has a chance to leave a **Permanent Scar**, which carries **30%** of
> the original wound's stat penalties indefinitely.`
> ```python
> scar_penalty = wound_penalty * 0.3
> ```

Both phrasings presuppose healing happens ("when a wound heals" / "when a wound is healed") without
ever stating a trigger condition — because none exists in code. Neither doc states that wounds are
currently permanent. Note a secondary inaccuracy inherited in the same sentences, informational
only (not this ticket's AC to resolve, since it describes the *scar-formation* mechanic owned by
`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`, not the healing-trigger decision this ticket owns): the
dead `heal_wound()` code does not actually roll any probability — it unconditionally creates a scar
every time it is called with a flat 0.3x penalty multiplier — so "30% chance" (a probability) versus
"carries 30% of penalties" (a magnitude) already contradict each other in the current text,
independent of whether healing ever fires. Flagged in Risks below; left for the scar-wiring ticket
to resolve since it owns the real formula.

### 5. `WoundUpdate(wounds_heal=...)` producers — confirms zero, matches ticket's claim
`src/core/updates.py:604-621` defines `WoundUpdate`:
```python
@dataclass(frozen=True, slots=True)
class WoundUpdate:
    """New wounds and scar transitions."""
    wounds_add: List[WoundState] = field(default_factory=list)
    wounds_heal: List[str] = field(default_factory=list)  # wound IDs to heal
    scars_add: List[ScarState] = field(default_factory=list)
```
The only production constructor of `WoundUpdate` anywhere in `src/` is
`CombatResolutionSystem._get_wound_infliction()` (`src/engine/combat.py:605-617`), which
**always constructs `WoundUpdate(wounds_add=[wound])` and never populates `wounds_heal` or
`scars_add`**:
```python
wound = WoundService.create_wound(...)
return WoundUpdate(wounds_add=[wound])
```
There are four call sites of `_get_wound_infliction()` in `combat.py` (lines 194, 288, 504, 562),
all feeding the same single-purpose helper — none of them constructs `wounds_heal` or `scars_add`
either, directly or indirectly. `src/engine/patches.py:637-638` (`WoundPatch.apply`) is a pure
*consumer* — it applies `wounds_heal` IDs if present, but nothing ever populates them. This is
independent of `ENABLE_COMBAT_ENGAGEMENT`'s gate state: even with that flag on, the only live
infliction path never produces a heal, so **zero production producers exist for `wounds_heal`
regardless of gate state** — confirming the ticket's claim exactly. The single non-test-fixture
construction of `WoundUpdate(wounds_heal=[...])` in the whole repo is
`tests/unit/core/test_rpg_depth.py:600` (`test_wound_heal_through_apply`), which hand-builds the
update to test the *apply-path consumer logic* in isolation, not a production trigger.

### 6. `wound_healed` event/field — every consumer, and correction needed to COMB-296/ENTITY-018
`src/observability/event_extractor.py:292-301` is the only consumer of the `healed` flag transition
(diff-based, reactive — not a producer):
```python
prior_wounds_by_id = {w.id: w for w in prior_wounds}
for wound in entity_wounds:
    prior_wound = prior_wounds_by_id.get(wound.id)
    if prior_wound is not None and wound.healed and not prior_wound.healed:
        events.append(SimulationEvent(
            event_type="wound_healed", event_category="lifecycle", ...
        ))
```
This block only fires if `entity.combat.wounds` shows a `healed=False -> True` transition between
two ticks — which, per Finding 5, never happens through any real production path. The only test
that exercises this block, `tests/unit/observability/test_event_extractor_vitals.py:69-83`
(`test_wound_healed_fires`), hand-constructs a `healed=True` `WoundState` directly and passes it to
`EventExtractor.extract()` — it bypasses `WoundUpdate`/`patches.py`/`Kernel.tick_once()` entirely,
so it verifies the *consumer* logic only, not any production trigger.

**`docs/parity_ledger/combat_movement.yaml` COMB-296** (status: `verified`, priority: `P2`) and
**`docs/event_ledger/entity.yaml` ENTITY-018** (status: `observed`) both currently attribute
`wound_healed`'s unreachability solely to `ENABLE_COMBAT_ENGAGEMENT` being corpus-wide off
(TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY), with language implying it "will begin
firing naturally once a future ticket re-enables it" (COMB-296 `support_boundary`) / "just currently
unreachable in practice" (ENTITY-018 `notes`). This is misleading for `wound_healed` and
`scar_gained` specifically (though accurate for `wound_sustained`, which has a real live producer
gated only by the flag): even with `ENABLE_COMBAT_ENGAGEMENT` flipped on, `wound_healed` and
`scar_gained` would still never fire, because — per Finding 5 — no code anywhere constructs
`WoundUpdate(wounds_heal=...)` or `WoundUpdate(scars_add=...)`. Both entries need correcting to
state plainly that `wound_healed` (and `scar_gained`, sharing the same `wounds_heal`/`scars_add`
absence) has **zero production producers independent of the engagement gate**, per this ticket's
AC #4 ("regardless of the gate state chosen").

**Note on a distinct, unrelated `Scar` concept found during this search, to prevent confusion for
implementers:** `src/core/updates.py:902` (`StateUpdate.scars_add_or_update`) and
`src/core/state.py:176` (`LocalScarState`, "Localized world trauma at a specific coordinate") are a
**different subsystem** — regional/world calamity trauma (`docs/mechanics/05_world_evolution.md`
territory), not entity combat trauma. `LocalScarState` has real producers
(`tests/unit/world/test_consequences.py:19`) and is unrelated to this ticket's `ScarState`
(`src/core/state.py:105`, "Permanent mark from a healed wound"). Do not conflate the two when
searching for "scar" producers.

## Mechanics / Engine Constraints

- **`docs/mechanics/02_combat_laws.md` Section 5 ("Wound Infliction")** and
  **`docs/mechanics/01_entity_anatomy.md` Section 6 ("Trauma: Wounds & Scars")** are the two
  Certified Level 1 (Authoritative) chapters governing this mechanic. Per the Authoritative
  Mechanics Rule, both must state the real, decided behavior — permanence until a future
  scar-formation mechanic — not the current ambiguous "when a wound heals" phrasing.
- The **Durable State Rule**: `WoundState.healed`/`scar_created` are already typed fields on a
  proper durable-state dataclass (`src/core/state.py:90-100`) with a defined apply path
  (`WoundPatch.apply`, `src/engine/patches.py:629-640`) — the *data model* is already correct and
  does not need to change for Option (b). Only the never-reached producer/pipeline
  (`heal_wound()`, `get_diagnosis_quality()`) is affected.
- No engine contract in `docs/engine/` references wound healing directly; the 7-phase kernel loop
  and 37-phase authoritative pipeline are unaffected by this decision either way, since no phase
  currently constructs `wounds_heal`.

## Docs Requiring Update

- `docs/mechanics/02_combat_laws.md`: replace the ambiguous "when a wound heals, it has a 30%
  chance to leave a scar" phrasing (Section 5, line 85) with an explicit statement that wounds are
  permanent until a Scar forms via a separate mechanic (owned by
  TCK-20260824-TACTICAL-WOUND-SCAR-WIRING), removing the implication that healing currently occurs.
- `docs/mechanics/01_entity_anatomy.md`: replace the ambiguous "When a wound is healed, it has a
  chance to leave a Permanent Scar" phrasing (Section 6, "### Permanent Scars", lines 169-173) with
  the same explicit permanence statement.
- `docs/parity_ledger/combat_movement.yaml`: correct COMB-296's `text`/`v2_evidence`/
  `support_boundary` to state that `wound_healed`/`scar_gained` have zero production producers
  regardless of `ENABLE_COMBAT_ENGAGEMENT` gate state (not merely "gated off"), consistent with this
  ticket's AC #4.
- `docs/event_ledger/entity.yaml`: correct ENTITY-018's `notes` for the same reason — `wound_healed`
  and `scar_gained` are unreachable independent of the combat-engagement gate, unlike
  `wound_sustained` which has a real live producer once that gate is on.
- `docs/guidelines/intentional_divergences.md`: add a new `DEV-005` entry (next sequential ID after
  DEV-004) documenting the "wounds permanent until Scar" decision, `heal_wound()`/
  `get_diagnosis_quality()` disposition (removed or annotated dead-by-design — Implement phase's
  call, both are valid per ticket scope), rationale class, and verification path, per the
  Authoritative Mechanics Rule's Divergence clause and this ticket's AC #3.

The `docs/simulation_quality/event_type_coverage.md` doc (referenced only inside COMB-296's
`support_boundary` prose, not itself a Related Doc) is not required to change for this ticket: it
classifies `wound_healed` as `unscored_intentional` under Section 5's SimQ-pillar-wiring taxonomy,
which is orthogonal to whether the event has a production producer — that classification stays
correct regardless of this ticket's decision.

The `docs/mechanics/01_entity_anatomy.md` attribute table row for Wisdom ("Healing quality and
tactical decision-making", Section 1, not Section 6) is not required to change for this ticket: it
is flavor/summary text for the WIS attribute's intended future role, not a claim that healing is
currently active, and this ticket's scope is limited to Section 6's ambiguous "when a wound heals"
phrasing plus the two named parity/event-ledger entries — the attribute table row is a separate
sentence in a separate section not named in the ticket's Scope or Related Docs.

## Parity Ledger Overlap

- **COMB-296** (`docs/parity_ledger/combat_movement.yaml`, priority P2, status `verified`) — must be
  corrected per this ticket's AC #4. P2, not P0, so no new passing `test_path` is strictly required
  by the P0 rule, but the existing `test_path` (`test_wound_sustained_severity_mapping`,
  `test_wound_healed_fires`, `test_scar_gained_fires`) remains valid as consumer-logic evidence and
  should be kept, with the `v2_evidence`/`support_boundary` prose corrected rather than the
  `test_path` itself.
- **ENTITY-018** (`docs/event_ledger/entity.yaml`, status `observed`) — same correction, `notes`
  field.
- **COMB-072/073/102/103/104** and **COMB-314** — already corrected by the prior, separate,
  already-done `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING` ticket (penalty formula, not healing).
  Not in scope here; mentioned only to confirm no overlap/duplication.
- **COMB-290** — the 25% wound-infliction-threshold entry, owned by the separate, still-open
  `TCK-20260824-WOUND-THRESHOLD-DECISION`. Not touched by this ticket.
- No P0 entries are touched by this ticket's scope.

## Prior Work

- `stored_artifacts/` has no prior investigation specific to wound healing (the sibling ticket
  `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING` was `hotfix`-tier and required no staging artifacts).
- `tickets/done/TCK-20260824-WOUND-PENALTY-FORMULA-WIRING.md` (read in full) already wired the
  severity-scaled penalty formula into `combat.py::_get_wound_infliction()` and corrected the same
  two Mechanics Bible sections' penalty-formula description, but **explicitly left the "when a wound
  heals" phrasing alone** as out of scope — confirming this ticket picks up exactly the residual gap
  that ticket deferred.
- `tickets/todos/m1-quick-wins/TCK-20260824-WOUND-THRESHOLD-DECISION.md` (still open, sibling
  ticket, its own `should_inflict_wound()`/40%-threshold decision untouched here) explicitly defers
  "whether `heal_wound()` should be handled here or deferred entirely to
  TCK-20260824-WOUND-HEALING-DECISION" to this ticket — confirming this ticket, not that one, owns
  `heal_wound()`'s disposition.
- `tickets/todos/m1-quick-wins/TCK-20260824-TACTICAL-WOUND-SCAR-WIRING.md` (still open) is the
  "separate path" Option (b) defers scar formation to — but as currently scoped, that ticket only
  makes `TacticalDecisionSystem` *read* `entity.combat.wounds`/`.scars` via the existing
  `WoundService` aggregators; it does **not** itself build a new scar-formation producer. Flagged
  below as an open question, not re-litigated here.
- `docs/guidelines/intentional_divergences.md`'s most recent entry, **DEV-004**
  (`TCK-20260824-ALLOCATE-AP-BRANCH-DECISION`), is structurally the closest precedent: a
  "decide the fate of dormant/dead code" ticket with the exact same shape (Subsystem / Situation /
  Decision / Rationale / Verification / Status, plus a summary-table row). Use it as the template
  for the new DEV-005 entry.

## Risks and Open Questions

- **Open question, not blocking, flagged for the ticket owner / a future ticket rather than assumed
  here**: Option (b)'s premise is that scars form "via a different path" owned by
  `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`. As currently scoped (read above), that ticket only
  consumes existing `ScarState` data — it does not build a scar-formation producer either. Unless
  its scope changes before it lands, `ScarState` (and thus scars) will have **zero producers even
  after that ticket completes**, same as today. This does not block this ticket (which only needs
  to record the permanence decision and correct docs/dead-code annotations), but it means "wounds
  become Scars via a different path" is not yet a real, scoped end-to-end path — only a declared
  intent. Worth surfacing to the ticket owner during Plan/Implement rather than silently assuming
  it will resolve itself.
- **Removal vs. dead-by-design annotation choice is left to Implement**: the ticket's Scope says
  "remove or explicitly annotate ... as dead-by-design" — both are valid. Removing `heal_wound()`
  requires updating/removing `TestScarPermanence` (3 tests) and
  `TestSkillScaling.test_effective_stats_with_scars` (1 test, uses `heal_wound()` only to build a
  scar fixture — would need inlining a hand-built `ScarState` instead). Annotating in place avoids
  touching those 4 tests but leaves dead code discoverable-but-unused. This investigation does not
  make that call; Plan should decide based on the project's general dead-code posture (compare: DEV-004
  chose deletion for `AllocateAttributeAction` but dormancy for `execute_allocate_ap`).
- **The 30%-chance vs. 30%-magnitude phrasing contradiction** (Finding 4) is real but belongs to
  `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`'s eventual real formula, not this ticket's permanence
  decision — flagged, not fixed here, to avoid scope creep into the scar-formula ticket's territory.
- `MedicalService.get_diagnosis_quality()`'s removal (if chosen) has no test dependents at all
  (Finding 2), so it carries zero regression risk either way — simplest possible case.

## Anti-Drift Hazards

- **Do not touch `should_inflict_wound()` or `WOUND_THRESHOLD_RATIO`** (`src/engine/rpg_depth.py`) —
  owned by the separate, still-open `TCK-20260824-WOUND-THRESHOLD-DECISION`. Easy to conflate since
  both are "dead code in `rpg_depth.py`" decisions being made in the same week.
  `WoundService.create_wound()` (already live, wired by `WOUND-PENALTY-FORMULA-WIRING`) must not be
  touched either.
  - **`test_wound_heal_through_apply`** (`tests/unit/core/test_rpg_depth.py:590-603`) must **not**
  be removed even though it references `WoundUpdate(wounds_heal=...)` — it tests the *apply-path
  consumer* (`ApplyPath._apply_entity_update` / `WoundPatch.apply` in `patches.py`), which is
  correct, tested plumbing that stays regardless of this ticket's decision. Only the *producer*
  side (`heal_wound()`) is in scope for removal/annotation, not the consumer plumbing in
  `patches.py`/`updates.py`.
- **Do not conflate `ScarState` (entity combat trauma, `src/core/state.py:105`) with
  `LocalScarState` (world/regional trauma, `src/core/state.py:176`)** — both contain the word
  "scar" and both have "scars_add"-shaped fields on different `*Update` classes
  (`WoundUpdate.scars_add` vs `StateUpdate.scars_add_or_update`), but they are unrelated
  subsystems. `LocalScarState` has real producers and must not be touched by this ticket.
- **Do not silently change `wound_sustained`'s status** — it has a real production producer
  (`combat.py::_get_wound_infliction`) gated only by `ENABLE_COMBAT_ENGAGEMENT`; only
  `wound_healed`/`scar_gained` lack a producer regardless of gate state. COMB-296/ENTITY-018 cover
  all three events in one entry each — corrections must be precise about which of the three is
  actually affected, not blanket-rewritten.
- **Do not implement Option (a)** (an active healing trigger) — this has already been decided
  against by the ticket owner; this investigation exists to support Option (b) only.
