---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Objects / Ownership / Resources / Economy (Batch 08)

**Purpose/scope.** Eighteen scenarios used to pressure-test the Objects/Material Culture,
Ownership/Possession, Resources/Production, and Economy/Exchange rule families in
`material-economy/objects-material-culture.md`, `ownership-possession.md`,
`resources-production.md`, and `economy-exchange.md`, per `tmp/world-rule-batch-8-ext-ai.md`
and its 2026-09-22 follow-up (`tmp/world-rule-batch-8-followup-ext-ai.md`). Covers all sixteen
required seed probes from the original instruction's §15, plus two further probes the
follow-up required (ME-S17, ME-S18).

Scoring uses the same vocabulary as prior batches: **covered** / **partially covered** /
**blocked** / **revealed missing rule** / **revealed contradiction**, against current
repository behavior, not the ideal design.

---

## ME-S01 — Sword changes hands

A smith creates a sword; a merchant owns it; a warrior buys it; the warrior dies; an heir
receives it.

- **Rules invoked:** OBJ-01, Inherited (ID-04, CAUSE-01, the reclassified "authoritative owner
  independent of transfer producer" entry in `ownership-possession.md`).
- **Result: partially covered.** Object identity itself is confirmed stable across ownership
  changes for a promoted `ItemInstance` (OBJ-01) — but this specific chain's *final* step
  (the warrior's death, heir receiving it) is where this batch's own most significant finding
  bites: the heirloom-transfer intent that step would rely on is confirmed rejected by
  `src/core/conservation.py`'s resolver. The sword's own identity survives every step in
  principle; whether the heir actually *receives* it in this repository's own current
  implementation does not.

## ME-S02 — Possession without ownership

A thief takes a sword; the thief possesses it; the original ownership claim remains.

- **Rules invoked:** PROP-01.
- **Result: revealed missing rule.** PROP-01 requires that a legitimate-owner/current-
  possessor mismatch be representable; checked directly, no such representation exists
  anywhere in this repository. A stolen item's `ItemStack` entry simply moves to the thief's
  own inventory — nothing marks it as taken without consent, and nothing preserves "the
  original ownership claim" as a distinct, checkable fact. This is a confirmed gap against the
  Rule's own explicit requirement, not merely an unexplored corner.

## ME-S03 — Owner without possession

A merchant owns goods; the goods are stored in a warehouse elsewhere.

- **Rules invoked:** PROP-01.
- **Result: covered.** `HomeStorageService`'s access-controlled private storage
  (`docs/mechanics/03_economic_laws.md` §6) is exactly this case, real and functioning: goods
  sit in storage physically separate from the owning entity, and only that entity may deposit
  or withdraw — ownership and current physical location are confirmed separable facts about
  the same goods.

## ME-S04 — Shared access

An organization controls a resource stock; a member may use some portion; the member does not
personally own the entire stock.

- **Rules invoked:** PROP-01.
- **Result: revealed missing rule.** `faction_{id}_gold` (`src/world/regional_sovereignty.py`)
  confirms the "organization controls a stock" half — a real, accumulating per-faction vault,
  distinct from any single member's own personal wealth. But checked directly: no individual
  member ever withdraws from or spends this vault — the "member may use some portion" half of
  the probe has no live mechanism at all. Scored as revealing a confirmed gap against PROP-01's
  own collective-ownership claim, not a rule violation (the vault's own existence is real
  evidence the claim is at least half-realized).

## ME-S05 — Resource conversion

Ore undergoes a production process and becomes a sword.

- **Rules invoked:** PROD-01, Inherited (ID-04, CAUSE-01).
- **Result: covered.** `docs/mechanics/03_economic_laws.md` §5's Crafting law destroys the
  source materials and creates the product in the same tick, jointly gated on recipe
  materials, a gold cost, and (for some recipes) a station — a real, PROD-01-compliant,
  multi-input production event with a clean identity break between input and output.

## ME-S06 — Production fails after partial cost

Materials/time are committed; the process is interrupted; some cost is already incurred; the
output is incomplete or absent.

- **Rules invoked:** Inherited (COST-03, Batch 03).
- **Result: covered — reuses Batch 03's own cost-lifecycle evidence directly.** The Atomic
  Conservation Law's own all-or-nothing rollback (`docs/mechanics/03_economic_laws.md` §1: "if
  either fails, the entire transaction is rolled back") means a *rejected* transaction never
  incurs partial cost in the first place — consistent with COST-03's own lifecycle distinction
  between committed and reversible cost, applied here as the "nothing partially commits"
  instance of that same discipline.

## ME-S07 — Scarcity emerges

Resource depletion causes local availability to fall; economic pressure changes.

- **Rules invoked:** PROD-02.
- **Result: covered.** `ResourceNodeState.remaining_charges` depleting from real harvest
  events, and `GATHER_RESOURCE` route benefit scaling down with it (Batch 06 evidence), is
  real, world-state-driven scarcity with a real downstream consequence for entity decisions.

## ME-S08 — Scarcity without price change (counter)

Scarcity increases; no market/pricing mechanism applies; scarcity exists anyway.

- **Rules invoked:** PROD-02.
- **Result: covered — and, checked directly, this is not merely permitted but this
  repository's own actual, confirmed behavior.** No producer anywhere computes
  `price_modifiers` from real depletion data — scarcity (`remaining_charges`) and price
  (`region_mod`/`building_mod`) are two entirely disconnected mechanisms in this repository
  today. Scarcity confirmed to exist and matter (route-scoring) with zero pricing-mechanism
  involvement.

## ME-S09 — Price without objective scarcity

Belief, speculation, or an institution causes a price to rise while physical supply is
unchanged.

- **Rules invoked:** EXCH-01, PROD-02.
- **Result: partially covered.** `calculate_price()`'s real multiplier chain
  (`region_mod`/`building_mod`/`type_bias`) confirms price can move independent of actual
  supply, since none of those multipliers derives from real stock levels (PROD-02's own
  finding) — but checked directly, no belief/speculation/institutional mechanism was found
  that *actively drives* a price change from an information-side cause either. The probe's
  premise (price moves for reasons other than supply) is structurally possible and, in a weak
  sense, already true (price never reads supply at all) — but no live mechanism was found that
  specifically models *belief-driven* price movement as its own causal event.

## ME-S10 — Wealth converts to capability

An entity accumulates wealth; acquires equipment/service; capability increases.

- **Rules invoked:** Inherited (PROG-07, Batch 07).
- **Result: covered.** Gold buys equipment (`BUY_UPGRADE` route family) and equipment is a
  real, confirmed capability channel (Batch 07's own PROG-01) — a real, live conversion edge,
  the cleanest of the wealth-conversion edges this batch checked.

## ME-S11 — Theft

An object is transferred without the legitimate owner's consent; possession changes; ownership/
legal/social meaning may differ. Law semantics deferred.

- **Rules invoked:** PROP-01.
- **Result: revealed missing rule — the same finding as ME-S02, traced from the transfer-event
  angle rather than the resulting-state angle.** No code path distinguishes a consensual
  transfer from a non-consensual one; both simply move an `ItemStack` entry between
  inventories identically. Law/crime/social-reaction semantics are correctly out of scope here
  (Scope Boundary, `ownership-possession.md`), but the more basic representational gap —
  marking *that* a transfer was non-consensual at all — is confirmed absent, which is a
  precondition any future Law/Crime content would need.

## ME-S12 — Wealth does not automatically mean power

An entity has wealth; no valid conversion path exists; combat/political capability is
unchanged.

- **Rules invoked:** Inherited (PROG-07, Batch 07).
- **Result: covered — and richly evidenced as this repository's own dominant pattern for
  wealth beyond equipment.** Wealth → protection (`ContractKind.PROTECTION`, confirmed DORMANT,
  only constructed in `src/certification/scenarios.py`), wealth → political influence
  (faction vaults accumulate but are never read by faction-level decisions), and wealth →
  supply-chain control (no mechanism beyond a SimQ-only scoring flag) are all confirmed
  MISSING conversion paths — wealth without equipment-buying specifically produces no combat
  or political capability change at all in this repository today.

## ME-S13 — Resource access but no ownership

An entity can harvest/use a common resource; has access; does not own the entire resource
source.

- **Rules invoked:** PROP-01.
- **Result: covered.** Any entity may harvest from a `ResourceNodeState` it can reach —
  access to interact with the node — without that entity acquiring any ownership claim over
  the node itself; the node remains a world-owned object, never transferred to a harvester.
  This is the cleanest, most unambiguous real instance of access ≠ ownership this batch found.

## ME-S14 — Ordinary object becomes relic (flagship)

An ordinary object participates in historically important events, accumulates provenance/
significance, and later entities value or react to this specific object.

- **Rules invoked:** OBJ-02, Inherited (HP-02, HP-05 — the reclassified entry originally
  drafted as OBJ-03).
- **Result: revealed missing rule enforcement — the trajectory is permitted by design but
  never realized in practice, the mirror image of Batch 07's own non-HERO-significance
  finding.** `ItemInstance`'s append-only `owner_history` is exactly the accumulating causal-
  ancestor record HP-02 requires, and the promotion mechanism (`significant=True`) is fully
  wired end-to-end — but gated `ENABLE_ITEM_INSTANCE_HISTORY` (default OFF) and, independently,
  never triggered by any production call site. No ordinary object has ever actually begun
  accumulating provenance in this repository. **Target answer, preserved from the original
  draft: YES in World Rule semantics (HP-02/HP-05 already permit it, generally, for any
  first-class subject including artifacts) — PARTIAL/unrealized in the current repository.**

## ME-S15 — Inheritance

An owner dies; property persists; a valid succession trigger fires; ownership changes.

- **Rules invoked:** Inherited (the "authoritative owner independent of transfer producer"
  entry, originally drafted as PROP-02).
- **Result: revealed contradiction — CONFLICTING, the single most significant finding in this
  batch.** `LifecycleSystem`'s heirloom-transfer logic resolves a real heir and constructs a
  real `ResourceTransferIntent(source_kind="CHEST")` — but `src/core/conservation.py`'s own
  resolver has no handler for `"CHEST"` and rejects every such intent with
  `UNKNOWN_SOURCE_KIND`. Property does persist (as a lootable `CorpseState`, open to anyone),
  and a succession trigger does fire (heir resolution), but ownership never actually changes to
  the heir specifically — the transfer is constructed and then silently discarded by the
  repository's own resolver.

## ME-S16 — Market feedback (schematic)

Scarcity changes behavior/price; production/trade changes; scarcity later changes again.

- **Rules invoked:** PROD-02, EXCH-01.
- **Result: blocked — the loop's own first link is already broken, confirmed directly rather
  than assumed.** Since price never reads real scarcity (ME-S08's own finding), the
  scarcity → price half of this feedback loop does not exist in this repository at all — there
  is no loop to trace further, only the independent scarcity → route-scoring channel (real) and
  the independent price → transaction-outcome channel (real), never connected to each other.
  Kept schematic per the batch instruction's own instruction; scored as blocked rather than
  partial, since the loop's own first causal link is confirmed absent, not merely weak.

## ME-S17 — Individuation from fungible material (added 2026-09-22 per follow-up)

A fungible quantity/stack has one portion become individually distinguished; that portion
later acquires its own history.

- **Rules invoked:** OBJ-02.
- **Result: covered by permission; MISSING by exercise — the same shape as ME-S14, checked
  from the individuation-moment angle specifically.** OBJ-02's own revised text explicitly
  requires that "any meaningful provenance the source material already carried must remain
  traceable through individuation." Checked directly: this repository's own `ItemInstance`
  schema begins `owner_history` only from the moment of individuation onward — it has no field
  for anything the source `ItemStack` carried before that moment (which node it was harvested
  from, which crafting batch produced it). Because individuation never actually occurs in
  production (`significant=True` set nowhere), this gap has never been exercised either, but
  it is real and checkable: if individuation ever fires, this repository's own current schema
  would start that object's history from a blank slate, not from whatever the source quantity's
  own provenance was.

## ME-S18 — Production with substitutable inputs (added 2026-09-22 per follow-up)

Production requires a suitable material; material A is unavailable; a declared material B is
an acceptable substitute; production remains valid.

- **Rules invoked:** PROD-01.
- **Result: covered by permission; not exercised by any real recipe.** PROD-01's own revised
  text explicitly permits a process to declare substitution semantics for a required input
  category. Checked directly: no recipe in this repository's own current content declares any
  substitute-material relationship — every recipe's `requires_items` names exact `item_id`s
  with no alternative accepted. This scenario directly challenged the old, stricter PROD-01
  formulation (which would have forbidden this trajectory outright) and confirms the revised
  Rule permits it cleanly; this repository simply has not yet authored a recipe that exercises
  the permission.

---

## Cross-batch note

ME-S15's finding (the heirloom-transfer resolver gap) is this batch's own single most
significant discovery, on par with Batch 05's ECOL-03/BODY-05, Batch 06's CONFLICTING
omniscience finding, and Batch 07's farming-counterforce gap. Classified CONFLICTING, not
MISSING, per the same distinction Batch 06/07 established: this is not an absent feature — the
code actively constructs a specific transaction that its own resolver actively rejects, a real,
live mismatch between two parts of this repository's own implementation. This does not
invalidate the Rule Catalog; the target semantics (a durable property relation has an
authoritative owner independent of whichever process caused the transfer, reclassified
2026-09-22 as Inherited rather than a new Rule) remain coherent — the Catalog successfully
exposed a real, documented implementation bug, and the 2026-09-22 follow-up review confirms
this is a repository/implementation finding to hand to implementation planning, not a World
Rule decision.

ME-S14's finding (the `ItemInstance` provenance mechanism is fully designed, wired, and never
triggered) is this batch's second most significant discovery, and is structurally identical to
Batch 07's own `Breakthrough`-granting and `combat_engagement` findings: a real mechanism,
fully wired end-to-end, that nothing in production ever switches on or exercises. **Preserved
project-level conclusion: can an ordinary object become historically significant because of
what happens to it? YES in World Rule semantics (now via History/Provenance's own HP-02/HP-05,
reclassified as Inherited rather than a new Objects-specific Rule) — PARTIAL/unrealized in the
current repository.**

ME-S12's finding (wealth → protection/political-influence/supply-chain-control all confirmed
MISSING) reconfirms, from the Economy side, the same "power conversion edges are specific,
never automatic" pattern Batch 07 established from the Combat/Fame side (PROG-07) — of the
concrete conversion chains checked across this whole Rule Catalog, wealth's own chain breaks
earliest. **Preserved project-level conclusion: wealth only becomes power through concrete
causal conversion edges — this batch confirms one real edge (equipment) and three confirmed
absent ones (protection, political influence, supply-chain control).**

ME-S17/S18 (added per the 2026-09-22 follow-up) confirm the revised OBJ-02/PROD-01 are
correctly permissive rather than over-restrictive: individuation must preserve provenance
where it occurs (OBJ-02), and substitution semantics are a process's own declared choice, not
forbidden by this Rule Catalog (PROD-01) — neither probe reveals a new gap beyond what OBJ-02/
PROD-01's own revised text already discloses.
