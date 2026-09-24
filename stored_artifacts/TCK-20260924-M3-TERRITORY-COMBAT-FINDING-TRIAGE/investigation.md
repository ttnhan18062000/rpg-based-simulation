---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE
artifact_type: investigation
tags: [architecture, schema, registry, combat]
---

# Investigation — TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE

## Context Scan performed

`mcp__knowledge-search__search_docs("Territory Control Combat Conflict finding triage semantic
control plane")` returned real, relevant hits (the ticket's own Assumption #5 that the index is
missing in this worktree did **not** reproduce — the MCP tool answered normally; noted, not
treated as a defect either way). `graphify query "territory control combat conflict semantic
control plane mapping"` matched on the literal string "control" (UI `ControlPanel.tsx` nodes) and
returned nothing topically useful for this ticket — the graph's community structure for this
specific cross-doc triage question is not informative; direct reads of the named source docs and
registries carried the actual investigation, as expected for a doc-triage ticket rather than a
code-relationship one.

## Current Behavior

**Registries (read directly, `registries/{rule_mechanism_edges,rule_classifications,
mechanisms}.yaml`):** M1 already populated real edges/classifications for **all four** `TERR-0N`
Rules — TERR-01 (CONFLICTING), TERR-02 (PARTIAL), TERR-03 (CONFLICTING), TERR-05 (PARTIAL) — each
citing `regional_sovereignty`, `betrayal_siege_war`, and/or `city` with real code evidence, dated
`2026-09-24`. `registries/mechanism_causal_edges.yaml` is `edges: []` (zero rows). **No Combat rule
ID appears anywhere in either edges or classifications file** — confirmed by direct read, zero
`CONFLICT-*` rows. `python3 tools/semantic_control_plane/registry.py` → `OK: rule_mechanism_edges.yaml,
mechanism_causal_edges.yaml, rule_classifications.yaml valid` (run today). `make
semantic-control-plane-drift-check` → `0 cited-code drift finding(s), 0 verdict drift finding(s)`
(run today) — M2's exit criterion still holds after re-running it now, not merely cited from its
own investigation.

**`registries/mechanisms.yaml`** (read directly): `combat_resolution` (`state: done`),
`tactical_decision` (`state: done`, `verified.verdict: contradicted`, ATTACK-branch dormant in
corpus play, root-caused and closed by `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`),
`combat_engagement` (`state: done`, `verified.verdict: observed`, evidence: "posture gate moved
attacks 1960 -> 837", with a 2026-09-23 card-desc addendum explicitly correcting an older "nothing
downstream consumes this" claim as stale).

**`src/domains/optimization/feature_flags.py`** (read directly, line 32): `"ENABLE_COMBAT_ENGAGEMENT":
FeatureMode.ON` — **this is the live default**, not OFF. Confirmed via `git log` this was flipped by
`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (merged 2026-09-14, commit `#190`), which the same
file's own comment describes as landing "after the full tests/integration/ regression run." Confirmed
wired into the real tick pipeline: `src/engine/pipeline.py:320`,
`run_phase("combat_engagement", update, lambda u: u.merge(CombatEngagementPhase.apply(...)),
"ENABLE_COMBAT_ENGAGEMENT")`. **This directly contradicts** `conflict-combat.md`'s own prose
("gated behind `ENABLE_COMBAT_ENGAGEMENT`, default OFF, never run in a real corpus profile") and
`capability-progression-batch-07-review.md`'s Repository Finding #2 ("INERT/OFF ... never runs in
production ... default OFF") — both docs carry `last_verified: "2026-09-23"`, nine days *after* the
flag was flipped ON. See "Risks and Open Questions" below; this is the single most load-bearing,
surprising re-verification result in this investigation.

**`src/engine/tactical.py:174-202`** (read directly): confirms both cited claims exactly as
described in the prose. (1) The permissive fallback: lines 198-202,
`try: if not _gate.can_perceive(...).perceived: continue / except Exception: pass  # Gate failure →
permissive fallback` — a gate failure fails open, matching the doc's own characterization
word-for-word. (2) The perception gate genuinely runs before any neighbor becomes hostile-eligible:
`_gate.can_perceive(entity, get_entity_signals(n), {"distance": ...})` is called inside the
per-neighbor loop before the `hostiles.append(n)` branch. Both claims: **CONFIRMED, current, live.**

**`src/world/displacement.py`** (read directly, header + `DisplacementService`): confirmed a
calamity-driven (idea 65, "Named Refugee Threads") population-relocation mechanism, gated on
`RegionState.calamity_intensity >= 0.6`, structurally unrelated to any combat-defeat outcome.
Confirms finding #12's "naming near-collision, not semantic overlap" verdict exactly as claimed.

**Closed/paused tickets (Related Tickets, record-only per ticket's own instruction):**
`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION.md` confirmed present in
`tickets/done/` (closed). `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md` confirmed present
in `tickets/todos/` (not started — "paused" is an approximately accurate plain-English description of
an unopened todos-folder ticket; it does not carry `## Status: BLOCKED` since it was never moved to
`tickets/inprogress/`). `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION` has **no standalone ticket
file anywhere** (`tickets/{inprogress,done,todos}/`) — confirmed by repo-wide grep; it exists only as
a named forward-reference inside `registries/rule_mechanism_edges.yaml`'s own header comment and
inside the closed `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE.md`. Per this ticket's own explicit
instruction, not re-derived or re-filed — noted as-is for Plan.

## Territory/Control findings

### T1 — `territory-control.md` § Implementation Candidates — Non-Binding (1 candidate)
**Claim:** a `TerritorialRelation`-shaped typed record (claimant/controller/kind/since-tick) could
replace/supplement the single `owner_faction_id` field; explicitly `DEFERRED — no commitment in
Rule Catalog phase`.
**Re-verified today:** this is a forward-looking design proposal, not a statement about current
Rule↔Mechanism reality — there is no mechanism in `registries/mechanisms.yaml` implementing a
`TerritorialRelation` record (grep confirms zero hits for that string anywhere under `src/` or
`registries/`). M1's own TERR-01/TERR-03 classifications (CONFLICTING) already fully capture the
*current-state* gap this candidate is proposing to fix.
**Read on disposition:** **not a control-plane fact** — it is a proposed future mechanism, not an
existing Rule-Mechanism relationship. Nothing to promote; the gap it responds to is already recorded
as CONFLICTING in `rule_classifications.yaml`.

### T2 — `places-territory-batch-11a-review.md` § Implementation Candidates — Non-Binding (L311)
**Claim:** identical text to T1 (the review export regenerates from the canonical file, per its own
"generated, non-authoritative" header).
**Re-verified today:** confirmed byte-for-byte equivalent content to T1 by direct comparison; this
review-export file explicitly states it is "never edited directly as the fix for a review finding."
**Read on disposition:** same as T1 — **not a control-plane fact**, and should be triaged as one
finding with two citations, not duplicated as a separate row, when the triage log is written.

### T3 — `territory-control.md` § Open questions carried forward, item 1
**Claim:** "Does Territory need its own authoritative relation model ... or can it remain a derived
projection over existing Region/Place/Faction facts?" — explicitly "Not decided here."
**Re-verified today:** an open design question with no registry-checkable current-state claim to
verify against. No mechanism or Rule-classification answers this question today.
**Read on disposition:** **stays UNKNOWN** — genuinely undecided design question, not a fact this
ticket's re-verification process can resolve either way.

### T4 — `territory-control.md` § Open questions carried forward, item 2
**Claim:** "Whether `owner_faction_id`'s own assignment ever traces to a real causal basis ... was
not exhaustively confirmed."
**Re-verified today:** partially superseded by M1's own TERR-02 classification (`PARTIAL`), which
*does* now cite a real, exhaustively-traced causal-basis mechanism
(`FactionInfluenceService.process_influence_shift()`, `src/world/influence.py:33-71`, gated on a
combat-death-evidence threshold) alongside two confirmed gaps (world-gen-time bare assignment; a
real +-50 vs +-100 threshold mismatch between two governing docs, not just two code paths). Directly
read `rule_classifications.yaml`'s TERR-02 row today to confirm this evidence is current and dated
`2026-09-24`.
**Read on disposition:** **already covered by M1's existing TERR-02 row** — the open question this
prose poses is now answered (partially) by real evidence already on file. No new row needed; Plan may
choose to note in the triage log that this open question is resolved-partial by the existing TERR-02
classification rather than truly open.

### T5 — `places-territory-batch-11a-review.md` § Repository Findings (L247) — **scope-guard
finding, same shape as the batch-07 warning but for Territory, not flagged by the ticket itself**
This review file's Repository Findings section is **not Territory-only** — it covers Batch 11A's
three families (Places, Settlements, Territory/Control) under one numbered list (items 1-10), exactly
the same "one review export, several rule families" shape the ticket explicitly warned about for
`capability-progression-batch-07-review.md`. The ticket's own Scope table did not carry an equivalent
warning for this source, so I verified the split myself by re-reading every item against which family
it actually names:
- **Item 1** (CONFLICTING — `owner_faction_id` control/sovereignty conflation + contested-claim
  divergence) → **Territory** (TERR-01/TERR-03). **Already covered**, word-for-word, by M1's existing
  TERR-01/TERR-03 classification rows (re-read `rule_classifications.yaml` today to confirm).
- **Item 2** (MISSING — no cultural-association/residence field) → **Territory** (TERR-01). Re-read
  `src/core/state.py`'s `PlaceState`/`RegionState` fields (via the existing M1 edge evidence, itself
  citing `src/core/state.py:344-383`) — confirmed no such field exists. **Not separately captured**
  in TERR-01's classification evidence text today (that text discusses only the control/sovereignty
  overload, not the residence/cultural-association absence as its own sub-finding). Since the schema
  allows exactly one classification row per Rule ID and TERR-01 already has one (CONFLICTING), this
  cannot become a second row — it can only be folded into TERR-01's existing evidence text, which is
  an edit, not a new promotion. Flagged for Plan's own call rather than assumed.
- **Item 3** (MISSING — no significance/historical-meaning field on `PlaceState`) → **Places**
  (PLACE-02), **not Territory. Out of scope.**
- **Item 4** (MISSING — no `place_id` retirement/re-founding mechanism) → **Places/Settlements**
  (PT-S02/PT-S05), **not Territory. Out of scope.**
- **Item 5** (MISSING — no settlement transformation mechanism beyond CITY→RUIN) → **Settlements**
  (SETT-03), **not Territory. Out of scope.**
- **Item 6** (MISSING — no settlement growth/decline causal mechanism) → **Settlements** (SETT-02),
  **not Territory. Out of scope.**
- **Item 7** (MISSING — no migration mechanism of any kind) → **Settlements**, **not Territory. Out
  of scope.**
- **Item 8** (MISSING — no territorial-claim-vs-control causal-basis mechanism confirmed) →
  **Territory** (TERR-02). **Already covered** by M1's existing TERR-02 `PARTIAL` row (same finding
  as T4 above, cross-referenced from a different source document).
- **Item 9** (UNKNOWN — whether `PlaceState.scale` is mutated at runtime) → **Settlements**
  (SETT-02/PT-S13), **not Territory. Out of scope.**
- **Item 10** (notable — "settlement" collapsed into `PlaceKind.CITY`, not its own durable-state
  class) → **Settlements**, **not Territory. Out of scope.**

**Read on disposition:** of this source's 10 numbered findings, only **items 1, 2, and 8** are
Territory-scoped and in this ticket's scope; the other seven (3-7, 9, 10) are Places/Settlements and
out of scope for the same reason the ticket already excludes batch-07's progression/learning findings.
Items 1 and 8 are **already covered** by M1's existing rows. Item 2 is a **real gap in the existing
TERR-01 evidence's own itemization** (the sub-fact isn't textually present, though the aggregate
CONFLICTING classification is still directionally correct) — Plan should decide whether to amend
TERR-01's evidence text (not a new row) or record this explicitly in the triage log as "covered by
TERR-01's aggregate classification, sub-fact not separately itemized in evidence text."

## Combat/Conflict findings

### C1 — `conflict-combat.md` § Repository Findings (L179, 4 findings)
1. **SUPPORTED** — perception-gated targeting, `TacticalDecisionSystem`/`PerceptionGate`. Re-verified
   today directly against `src/engine/tactical.py:181,199` (see Current Behavior above) —
   **CONFIRMED, current, matches prose exactly.**
2. **INERT/OFF** — `combat_engagement` domain "never runs in production", `ENABLE_COMBAT_ENGAGEMENT`
   default OFF; plus the `try/except Exception: pass` fail-open note. Re-verified today: the
   fail-open note is **confirmed, current** (same code, same file). **The INERT/OFF/default-OFF
   claim is STALE, contradicted by live state** — see the "Current Behavior" section above:
   `ENABLE_COMBAT_ENGAGEMENT` is `FeatureMode.ON` by default (flipped 2026-09-14, ten days before
   this doc's own `last_verified: "2026-09-23"` date) and `registries/mechanisms.yaml`'s own
   `combat_engagement` entry already carries real runtime evidence (`verified.verdict: observed`,
   corpus posture-gate effect measured). This finding needs to be triaged as **two separable
   sub-claims**: the fail-open robustness gap (still true) and the INERT/OFF characterization (now
   false).
3. **MISSING** — no surrender/capture/forced-displacement combat outcome. Re-verified today:
   `src/engine/combat.py`'s `outcome_kind` values and `src/engine/movement.py`'s `FLED` property
   confirm the six/seven-value vocabulary the doc itself already cites; no surrender/capture/
   displacement value exists among them (spot-checked, not exhaustively re-enumerated beyond
   confirming no new outcome kind was added since the doc's own last_verified date). **CONFIRMED,
   current.**
4. **MISSING** — no non-combat Conflict superclass/contest-resolution mechanism named as such.
   Re-verified today: this is explicitly framed by the doc itself as consistent with a stated Scope
   Boundary, not a gap needing a fix — no registry check applies. **CONFIRMED as an out-of-model
   scope statement, current.**

### C2 — `conflict-combat.md` § Open questions carried forward (L213, 4 items)
1. Whether `ENABLE_COMBAT_ENGAGEMENT` should be turned on — **already moot**: re-verified today, it
   already was turned on, 2026-09-14, by `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`. This open
   question is **stale/resolved-by-event**, not still open.
2. Whether the `try/except Exception: pass` fallback should fail closed — re-verified: still an open,
   real, unresolved implementation question; the code is unchanged (confirmed above). **Still genuinely
   open**, real.
3. Whether surrender/capture/forced-displacement should become real outcomes — still open, no new
   mechanism exists (see C1.3). **Still genuinely open.**
4. Whether a dedicated non-combat Conflict-resolution mechanism should be built — still open, no
   registry-checkable state change. **Still genuinely open.**
**Read on disposition:** items 2-4 stay **UNKNOWN** (real open design questions, this ticket does not
decide them per its own Out of Scope). Item 1 should be recorded in the triage log as **resolved by
event, evidence dated 2026-09-14** rather than left reading as still-open — a case of prose going
stale in the opposite direction (an open question the world already answered, not a stale factual
claim).

### C3 — `capability-progression-batch-07-review.md` § Repository Findings (L269, 12 numbered)
**Resolved in/out split, verified directly against each finding's own content (not trusted from the
ticket's own first-read guess):**

| # | Finding | Family | In/Out | Notes |
|---|---|---|---|---|
| 1 | SUPPORTED — perception-gated targeting | Combat | **IN** | matches ticket's guess |
| 2 | INERT/OFF — `combat_engagement` domain, `ENABLE_COMBAT_ENGAGEMENT` default OFF | Combat | **IN** | matches ticket's guess; **STALE**, see C1.2 above — same contradiction |
| 3 | INERT/OFF — `BreakthroughService` granting path never invoked | Progression | **OUT** | not named in ticket's guess; breakthroughs are a Capability/Progression mechanism (`PROG-*` family), not Combat |
| 4 | MISSING — no counterforce against combat-XP farming | Progression | **OUT** | matches ticket's guess |
| 5 | MISSING — `TRAIN_SKILL` unreachable | Learning/Progression | **OUT** | matches ticket's guess |
| 6 | MISSING — no capability-improving mechanism for most lived-experience categories | Learning/Progression | **OUT** | matches ticket's guess |
| 7 | MISSING — no surrender/capture/forced-displacement outcome | Combat | **IN** | matches ticket's guess; duplicate of C1.3, same finding cross-cited from two sources |
| 8 | MISSING — no fame-to-followers conversion edge | Progression (PROG-07, power conversion) | **OUT** | not named in ticket's guess; lives in `capability-progression.md`'s own PROG-07, not `conflict-combat.md` |
| 9 | MISSING — no mechanism recognizes non-HERO individual's growing significance (CP-S15) | Progression | **OUT** | not named in ticket's guess; progression/history-significance family |
| 10 | Success-only progression is a repository fact, not a Rule requirement | Learning | **OUT** | matches ticket's guess |
| 11 | Doc/implementation mismatch — `max_xp_per_tick` claimed, no such symbol exists | Progression (`docs/engine/supported_progression_surface_phase5.md`) | **OUT** | matches ticket's guess; re-verified directly (see below) |
| 12 | Naming near-collision — `src/world/displacement.py` unrelated to combat outcomes | Combat/Conflict (explicitly framed as clarifying finding #7 above) | **IN** | matches ticket's guess |

**Resolved in-scope set: {1, 2, 7, 12}.** This **matches** the ticket's own first-read guess for the
items it named, but the ticket's guess was **incomplete**: it never classified findings 3, 8, and 9
at all (only stated 4, 5, 6, 10, 11 as out-of-scope, silently omitting 3/8/9 from either list). All
three resolve cleanly to **out-of-scope/Progression** on inspection — no ambiguity found, but this is
a real gap in the ticket's own pre-Investigate scoping that a less careful pass could have missed
outright (the exact risk the ticket itself calls out: "getting it wrong in the permissive direction
turns this ticket into the full-catalog sweep the roadmap explicitly rejects" — under-counting
in-scope findings isn't that failure mode, but silently *skipping* 3/8/9 entirely without triaging
them as anything would have been an AC1 violation: "every finding in every source" was not met).

**Finding 11 re-verified directly today**, per the ticket's own explicit instruction: grepped
`max_xp_per_tick` across `src/` — zero hits, confirmed absent. This finding is **Progression-scoped**
(the doc it's about, `docs/engine/supported_progression_surface_phase5.md`, is a progression-surface
contract, not a Combat one) — **out of scope for this ticket**, consistent with the ticket's own
"if it's not Combat/Territory it's out of scope, just note that" instruction. Noted, not triaged
further.

## Docs Requiring Update

No doc requires a content change as a *direct deliverable of this Investigate phase* — this phase
produces evidence only, per the ticket's own instruction not to write the triage log, registry rows,
or doc/code changes yet. The following are flagged for **Plan/Implement** to actually execute, and
are recorded here as Format-1 bullets because the underlying facts investigated above make each one
a real, not merely considered, requirement of this ticket's own Acceptance Criteria:

- `docs/world_rules/capability-progression/conflict-combat.md`: the "INERT/OFF ... default OFF,
  never run in a real corpus profile" characterization of `combat_engagement`/`ENABLE_COMBAT_ENGAGEMENT`
  is confirmed stale against live state (flag is `ON` by default since 2026-09-14; the mechanism
  registry's own `combat_engagement` entry already shows real observed effect). This ticket's own Out
  of Scope forbids *fixing the underlying gap this finding names* but does not forbid correcting a
  factual staleness discovered during re-verification — Plan must decide whether correcting this
  doc's own prose falls inside or outside this ticket's scope (the ticket's Out-of-Scope list names
  "fixing any gap a finding names," which is a different thing from "the finding's own factual
  premise is now wrong"); if Plan judges it out of scope for this ticket specifically, this bullet
  should be resolved per the Conditional-Bullet convention with "Resolved during implementation,
  condition not met" rather than silently dropped.
- `docs/plans/simulation_semantic_control_plane/roadmap.md`: AC7 requires the M3 section to record
  that the narrow Territory+Combat bar is met, without marking M3 "complete."
- `tickets/inprogress/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md`: AC8 requires the M3 row of the
  epic's own milestone-disposition table to be updated. Not a `docs/` path — noted here in prose per
  the same convention `TCK-20260924-M2-MAPPING-DRIFT-DETECTION/investigation.md` already used for
  this identical situation (a required non-`docs/` update, outside `check_docs_to_update_coverage`'s
  own regex).

The following were considered and are **not** required to change, stated in prose (Format 2), per
this ticket's own explicit Out-of-Scope boundary against fixing gaps a finding names:
`docs/plans/simulation_semantic_control_plane/{architecture,rollout_plan,agent_operating_model}.md`
are not required to change — this ticket adds no new schema, edge type, or classification vocabulary
value; it only ingests existing findings using the schema M0 already defined.
`docs/engine/supported_progression_surface_phase5.md`'s `max_xp_per_tick` claim, though confirmed
stale during this investigation, is out of this ticket's own domain scope (Progression, not
Territory/Combat) — its correction belongs to a future Progression-domain triage pass, not this one.

## Parity Ledger Overlap

Searched all nine `docs/parity_ledger/*.yaml` files for `TERR-0|CONFLICT-0|owner_faction_id|
regional_sovereignty|combat_engagement|ENABLE_COMBAT_ENGAGEMENT`. `docs/parity_ledger/faction.yaml`
carries `FAC-010` (status: `verified`, priority: `P1`), already cited as evidence inside M1's own
`rule_mechanism_edges.yaml` TERR-01/TERR-03 rows — this ticket does not alter `FAC-010`. No parity
ledger entry references `ENABLE_COMBAT_ENGAGEMENT`, `combat_engagement`, or any `CONFLICT-0N` Rule ID
directly — this ticket's Combat findings have no parity-ledger overlap to flag beyond the pre-existing
`FAC-010` citation already recorded by M1. No P0 entry is newly touched by this ticket's own scope.

## Prior Work

- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/` — the source of all four TERR
  rows already on file; re-read (via the live registry files, not the stored artifact itself, per
  this ticket's own re-verify-don't-trust-prose discipline) to confirm every Territory finding in
  scope here is already substantially covered.
- `stored_artifacts/TCK-20260924-M2-MAPPING-DRIFT-DETECTION/investigation.md` — establishes the
  `tests/unit/tools/` (not `tests/tools/`) location correction independently confirmed again here, and
  the precedent for citing a required-but-non-`docs/`-path update (the epic's own milestone table) in
  prose rather than a Format-1 bullet.
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §4 — the explicit precedent this ticket is
  built on; not independently re-read line-by-line this session beyond the roadmap's own citation of
  it, since its content (re-verify prose, don't launder it forward) is already the operating principle
  applied throughout this investigation rather than a separate fact to check.

## Risks and Open Questions

1. **The `ENABLE_COMBAT_ENGAGEMENT` staleness is the single biggest open question for Plan.** Both
   Combat source docs (`conflict-combat.md`, `capability-progression-batch-07-review.md`) characterize
   this as INERT/OFF as of their own `last_verified: "2026-09-23"` date, but the flag has been `ON` by
   default since 2026-09-14 and the mechanism registry already shows real runtime effect. This ticket's
   own scope is triage (recording a disposition with re-verified evidence), and its Out of Scope
   explicitly forbids "turning `ENABLE_COMBAT_ENGAGEMENT` on, or any other feature-flag flip" — that
   flip already happened, independently of this ticket, before this ticket was even opened. What
   remains open for Plan: does the triage log record this finding as **CONFLICTING** (the doc claims
   OFF; the flag is ON — an active documentation/reality mismatch, arguably the Combat-domain
   equivalent of Territory's own CONFLICTING pattern) or as **PROMOTE-AT-M4 with corrected evidence**
   (M4 will need to know the flag state is ON, not OFF, when it writes Combat's real mapping rows)? I
   recommend the latter framing in the triage log (record accurately re-verified evidence for M4 to
   consume) while separately flagging the doc staleness for a documentation correction, but this is a
   judgment call for Plan, not settled here.
2. **TERR-01's evidence-text sub-itemization gap (item 2, Territory § T5)** — whether Plan edits the
   existing TERR-01 classification row's evidence text to explicitly itemize the residence/
   cultural-association MISSING sub-fact, or records this in the triage log as "covered by TERR-01's
   aggregate CONFLICTING verdict, sub-fact not independently itemized," is an open editorial call, not
   resolved by this investigation.
3. **Batch-07-review's own in-scope/out-of-scope split was incomplete in the ticket, not merely
   unverified** — findings 3, 8, 9 were never mentioned by either list in the ticket's own first-read
   guess. This investigation resolved all three to out-of-scope with no real ambiguity, so it does not
   block Plan, but it is worth the dispatching session's attention as a process observation: a "verify
   the split yourself" instruction that is silently incomplete (omits items rather than mis-classifying
   them) is a subtler failure mode than a wrong classification, and would not have been caught by a
   pass that only checked the named items against their own claimed family.
4. **`places-territory-batch-11a-review.md`'s Repository Findings section mixing three rule families**
   (T5 above) was not flagged by the ticket's own Scope table the way the batch-07 case explicitly was
   — this is a second instance of the same "triage by content, not section name" hazard the ticket
   named for Combat, discovered independently for Territory during this investigation. Worth the
   dispatching session confirming this reading is correct before Plan proceeds, since it changes what
   "every finding in every source" (AC1) actually enumerates for this source from 10 items to 3.

## Anti-Drift Hazards

- **Do not write any Combat mapping rows to `registries/rule_mechanism_edges.yaml` or
  `rule_classifications.yaml`.** Zero exist today (confirmed); creating them is M4's own named
  deliverable per the ticket's own asymmetry rule. Territory rows already fully exist for TERR-01/02/
  03/05 — do not duplicate or overwrite them; if Plan decides T5's item-2 sub-fact warrants a change,
  that is an edit to existing evidence text, not a new row.
  `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` (paused) is a genuinely adjacent, real ticket
  that could move Combat's own numbers later — do not act on it or treat its existence as grounds to
  pre-empt M4's Combat mapping work now.
- **Do not silently upgrade `UNKNOWN` to `MISSING`** anywhere in the triage log — several findings
  above (T3, C2 items 2-4) are genuinely open design questions this ticket's own Out of Scope forbids
  deciding, and must land on `UNKNOWN`, not a false `MISSING`.
- **Do not "fix" the `ENABLE_COMBAT_ENGAGEMENT` doc staleness by re-flipping the flag or by silently
  rewriting the World Rule docs' prose as part of this ticket's own triage-log write** — the flag
  change already happened independently (a fact to record, per AC2's "re-verified today" requirement),
  and any doc correction is a separate, explicitly-flagged Docs Requiring Update item for Plan/
  Implement to decide the scope of, not something to fold silently into the triage log entry itself.
- **Do not re-derive or re-file `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION`** — confirmed it has
  no standalone ticket file; the ticket's own instruction is explicit that this triage must not touch
  it.
