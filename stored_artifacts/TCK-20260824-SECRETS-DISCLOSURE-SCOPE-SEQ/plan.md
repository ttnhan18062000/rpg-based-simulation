---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ
artifact_type: plan
tags: [information, feature-flags]
---

# Implementation Plan — TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ

## Summary

This ticket's own Scope section is explicit: "Land scope/design artifacts only." No `src/` file
is created, modified, or deleted by this plan. All six steps below write prose into the ticket
body's own required sections (`## Implementation Notes`, `## Test Summary`, `## Files Changed`,
`## Completion Summary`, and an append-only update to `## Assumptions / Open Questions`) — the
same single file, `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md`. This is
chosen as the single primary location (rather than appending to `investigation.md`) because
`investigation.md` carries `status: historical` / `artifact_type: investigation` and already
records a complete, closed investigation of current-state code; mixing a forward-looking,
non-binding design proposal into that file would blur "what the codebase does today" with "what a
future ticket might build," which is exactly the kind of drift the investigation's own Anti-Drift
Hazards section warns against. `Implementation Notes` is the ticket-format section designed to
hold exactly this kind of narrative record. The plan produces: (1)-(2) two citation-backed
confirmations that the ticket's sequencing premise still holds; (3) a non-binding schema/routing
design sketch satisfying the Scope section's design-artifact requirement; (4)-(5) two explicit
factual statements required by AC3 and AC4; (6) closing out the ticket's remaining required
sections. No test is added or run, per `test_plan.md`'s finding that there is no regression
surface. No `docs/`, `config/`, or `src/` path is touched by any step.

## Steps

### Step 1 — Confirm C1 status and record it in Implementation Notes
**Files:** `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md` (`## Implementation Notes`)
**Change:** Add a paragraph stating: `ENABLE_BELIEF_ASSIMILATION` is `FeatureMode.ON`
(`src/domains/optimization/feature_flags.py:37`, confirmed by direct read per
`investigation.md`'s "Current Behavior" section); `TCK-20260824-ROLLOUT-FLAG-DECISIONS` (C1) is in
`tickets/done/TCK-20260824-ROLLOUT-FLAG-DECISIONS.md`; `docs/guidelines/intentional_divergences.md`'s
DEV-003 entry (~line 1445) records this decision as rationale class **Stabilized**, status
**ACTIVE**. Also state, citing `src/engine/pipeline.py:173`, that `InformationBeliefPhase.apply()`
remains invoked via `run_phase("information_belief", ..., "ENABLE_BELIEF_ASSIMILATION")` — i.e.
the flag being ON does not make the phase unconditional; it is a real gate that is currently
open, not removed. Conclude explicitly: this satisfies AC1's and Out of Scope's "confirmed live"
condition for *sequencing* purposes, but does not authorize this ticket itself to implement —
this ticket's own Scope section's unqualified "design/scope artifacts only" instruction controls
regardless of flag state.
**Do NOT touch:** `src/domains/optimization/feature_flags.py`, `src/engine/pipeline.py`,
`docs/guidelines/intentional_divergences.md` — cited, not edited. Do not edit `## Related
Tickets` (C1 is already listed there as a blocking dependency — see Step 6 verification note) or
`SEQUENCE.md` (already places this ticket strictly after C1 at
`tickets/todos/m1-quick-wins/SEQUENCE.md` line 13 — confirmed present, no edit needed).
**Verify:** `test_plan.md`'s Scope guard (`git diff --stat` confined to
`tickets/inprogress/`/`staging_artifacts/` paths) and its read-only spot-check command
(`grep -n '"ENABLE_BELIEF_ASSIMILATION"' src/domains/optimization/feature_flags.py`).

### Step 2 — Confirm LEAD-CONTRADICTION-WIRING does not force re-evaluation
**Files:** `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md` (`## Implementation Notes`)
**Change:** Add a paragraph, citing: `src/engine/pipeline.py:356` (a new, always-on, no-flag
`run_phase("lead_contradiction", ...)` call added by the sibling ticket); the excluding docstring
in `src/engine/pipeline_phases/lead_contradiction.py` lines 60-64 ("CONCEPT contradiction is
observation-shaped ... routed through `BeliefContradictionService.detect()` instead" — i.e. this
always-on phase explicitly does not cover `concept`/`information` lead kinds);
`src/domains/information/bridge.py:40` (`ObservationBeliefBridge.process_observation()` now calls
the real `BeliefContradictionService.detect()`); and `src/engine/pipeline.py:173` again
(`InformationBeliefPhase.apply()`, which contains this wiring, remains flag-gated, not bypassed).
State the conclusion explicitly: `TCK-20260824-LEAD-CONTRADICTION-WIRING` built a structurally
separate, orthogonal always-on system for non-concept lead kinds while leaving
`BeliefContradictionService`/`InformationBeliefPhase` flag-gated exactly as before — it did **not**
take Out of Scope's named re-evaluation trigger (idea 12's flag-free alternative path). This
ticket's sequencing premise (blocked on C1, not superseded by an always-on bypass) holds
unchanged.
**Do NOT touch:** `src/engine/pipeline.py`, `src/engine/pipeline_phases/lead_contradiction.py`,
`src/domains/information/bridge.py` — citation only, no code edits, no re-opening of the already
`tickets/done/` `LEAD-CONTRADICTION-WIRING` ticket or its `stored_artifacts/`.
**Verify:** Same Scope guard as Step 1.

### Step 3 — Write the schema-extension / selective-disclosure design sketch (non-binding)
**Files:** `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md` (new subsection under
`## Implementation Notes`, e.g. `### Design Sketch (non-binding, for a future implementation
ticket)`)
**Change:** Write prose (plain description and/or illustrative pseudocode in a fenced block
clearly labeled as non-executing sketch material, not a diff) covering:
- A proposed `confidence_tier` concept and a proposed `secrecy_level` field, described as
  additions in the same additive-dataclass-field pattern `TCK-20260824-RELATIONSHIP-ROLE-FIELD`
  already used for `SocialBond` (per `investigation.md`'s Prior Work section) — described as
  living alongside `InformationSourceProfile` (`src/domains/information/schema.py`, read per
  `investigation.md`'s Current Behavior section: fields today are `accuracy`, `freshness`,
  `bias`, `cost_gold` — no secrecy/confidence-tier field exists) and/or `SourceTrustEntry`
  (`src/core/strategic.py:341-346`: `entity_id`, `trust: float = 0.5`, `interactions: int = 0`,
  `last_outcome: Optional[str]` — no such field exists there either).
- An explicit composition statement: the new "confidence tier" concept must compose with, not
  duplicate, the existing `LeadCertainty` enum (`PRECISE`/`APPROXIMATE`/`VAGUE`/`EXHAUSTED`,
  `src/core/strategic.py:34-39`) and `NormalizedInformationResponse.certainty: float` — per
  `investigation.md`'s Mechanics/Engine Constraints and Risks sections, this is a named
  schema-collision risk that any real future design must resolve before implementation.
- A selective-disclosure routing sketch: a prose description of a gate inside
  `InformationQueryRouter.route()` (`src/domains/information/router.py:22-106`, which today ranks
  by `expected_certainty = accuracy * trust_score` at line 87 and returns top-3 candidates with no
  disclosure gate) that would use `secrecy_level` against the requester's trust/relationship
  standing to exclude or redact candidates.
- An explicit carry-forward of the investigation's live-traffic caveat: Branch A's
  query/response cycle is still `urban_political`-only per `docs/audits/D19_domain_phase_inventory.md`
  §3 (PP-04 row), and Branch B only ever routes one "first unknown" per actor per tick
  (`src/domains/information/phase.py:87-107`) — a future design must not assume broad live query
  volume exists yet outside that one profile.
- A one-line explicit disclaimer at the top of the subsection: "This subsection is a non-binding
  design sketch for a future implementation ticket. No `src/` file is created or modified by this
  ticket."
**Do NOT touch:** `src/domains/information/schema.py`, `src/domains/information/router.py`,
`src/domains/information/trust.py`, `src/core/strategic.py` — no new `.py` file anywhere, no
pseudocode presented as an applied diff.
**Verify:** `test_plan.md`'s Scope guard (`git diff --stat`); manual read confirming the fenced
sketch block is clearly labeled illustrative and no `src/` path appears in the diff.

### Step 4 — State the DECEPTIVE_DETECTED delta-reuse decision (AC3)
**Files:** `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md` (`## Implementation Notes`)
**Change:** Add an explicit statement: any future `DECEPTIVE_DETECTED` wiring **reuses the
existing `-0.25` delta via the existing `"DECEPTIVE_DETECTED"` outcome branch already in
`src/domains/information/trust.py:49-50`** (`SourceTrustUpdateService.update()`) — no new writer
is needed, because the branch already exists and is semantically correct for the deceptive-source
case; it is currently just uncalled (`grep -rn "DECEPTIVE_DETECTED" src/ tests/` returns exactly
one hit, the branch definition itself, per `investigation.md`'s Current Behavior section — zero
production or test callers). Immediately follow with the explicit caveat from
`investigation.md`'s Risks and Open Questions section: the `-0.25` value itself is unvalidated
(zero callers, zero balance-measurement history ever run against it) — a future implementation
ticket must treat it as a placeholder needing balance validation, not a proven constant, even
though the branch/delta itself is the one being reused rather than replaced with a new writer.
**Do NOT touch:** `src/domains/information/trust.py` — the reuse decision is stated in prose
only; no new outcome branch is added, no caller is wired, `SourceTrustUpdateService.update()`
remains uncalled after this ticket.
**Verify:** Scope guard, plus the Acceptance Criteria Map cross-check below (AC3 wording match).

### Step 5 — State the SocialBond.sentiment / SourceTrustEntry structural-separation finding (AC4)
**Files:** `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md` (`## Implementation Notes`)
**Change:** Add an explicit statement, citing: `SocialBond.sentiment`
(`src/core/models/social.py:14-20`: `float`, `-1.0` to `1.0`, "Bias/Liking"), living in
`SocialComponent.bonds: Dict[int, SocialBond]` (`src/core/models/social.py:32-43`) — a **Social**
domain relationship/affection ledger — versus `SourceTrustEntry`/`StrategicComponent.source_trust`
(`src/core/strategic.py:341-346,393`: `float trust` `0.0`-`1.0`, "Trust score for a specific
information source") — a **Strategic Cognition** domain information-source-reliability ledger.
State the conclusion in the ticket's own AC4 wording: these are **structurally separate ledgers
with no shared implementation** — different component (`SocialComponent` vs
`StrategicComponent`), different dataclass, different semantics, no cross-reference or shared
update path between the two files. Cite corroborating evidence: `TCK-20260824-AFFECTION-CONTRACT-
GATE` (still `OPEN`, `tickets/todos/m1-quick-wins/`) already independently excludes "idea 25's
separate trust ledger (PP-04-adjacent)" from its own scope, treating the two ledgers as separate
concerns. State explicitly, as a forward-looking constraint: any future secrecy/disclosure design
must not reach into `SocialBond.sentiment`.
**Do NOT touch:** `src/core/models/social.py`, `src/core/strategic.py` — citation only, no field
added to either dataclass by this ticket.
**Verify:** Scope guard, plus the Acceptance Criteria Map cross-check below (AC4 wording match).

### Step 6 — Close out remaining ticket sections
**Files:** `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md` (`## Test Summary`,
`## Files Changed`, `## Completion Summary`, and an append-only update to `## Assumptions / Open
Questions`)
**Change:**
- `## Test Summary`: "N/A — no code changes. Per `test_plan.md`'s Regression Surface finding, no
  `src/` file is created, modified, or deleted by this ticket, so no regression surface exists to
  protect. No pytest command was run."
- `## Files Changed`: list only `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md`,
  `staging_artifacts/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ/investigation.md`,
  `staging_artifacts/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ/test_plan.md`,
  `staging_artifacts/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ/plan.md` (this plan) — no `src/`,
  no `docs/`, no `config/` entries.
- `## Completion Summary`: one paragraph confirming all four ACs are met by Steps 1-5 above, the
  scope-only nature of the deliverable was preserved throughout, and that any real implementation
  requires a new, separate, not-yet-created future ticket.
- `## Assumptions / Open Questions`: append (do not delete existing bullets) a resolution note
  for the two items `investigation.md` actually resolved — the "what does system live mean"
  question (resolved: real non-compile-time-seed per-tick writers now exist for the
  contradiction-detection slice, per `investigation.md`'s "System Live" resolution section) and
  the idea-12-path re-evaluation trigger (resolved: not taken, per Step 2 above). Leave the
  `DECEPTIVE_DETECTED` reuse-vs-new-writer product-calibration question and the `layer: strategy`
  registry note exactly as they are — `investigation.md`'s own Risks section is explicit that the
  calibration question is a human/product decision this ticket's AC only requires *stating*
  (done in Step 4), not resolving further.
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets`,
`## Related Docs`, `## Related Code Areas` — all already correct from the Scope phase; this step
only appends to `## Assumptions / Open Questions`, never rewrites or deletes its existing content.
**Verify:** `done-checker`'s `frontmatter_valid` condition; final read-through cross-checking
each AC's literal wording against what Steps 1-6 actually wrote (see Acceptance Criteria Map
below).

## Scope Guards

- No `src/` file of any kind is created, modified, or deleted — not
  `src/domains/information/schema.py`, `router.py`, `trust.py`, `contradiction.py`, `phase.py`,
  `bridge.py`, `assimilation.py`, not `src/core/strategic.py`, not `src/core/models/social.py`,
  not `src/engine/pipeline.py` or `src/engine/pipeline_phases/lead_contradiction.py`, not
  `src/domains/optimization/feature_flags.py`.
- No new `docs/mechanics/` or `docs/engine/` authoritative doc, and no edit to
  `docs/mechanics/04_strategic_cognition.md` — those are reserved for already-shipped, certified
  behavior; this ticket ships no behavior. (Confirmed correct in `investigation.md`'s "Docs
  Requiring Update" section: **None**.)
- No `docs/parity_ledger/` entry is added or edited (no `STRAT-###` row for
  `DECEPTIVE_DETECTED`/secrecy — a `P0`/`P1` entry needs a passing `test_path`, which cannot exist
  for undesigned code).
- No feature-flag change — `ENABLE_BELIEF_ASSIMILATION` is read/cited only, never modified.
- No test file is added, modified, or run — `test_plan.md` explicitly documents there is nothing
  to test.
- `SEQUENCE.md` (`tickets/todos/m1-quick-wins/SEQUENCE.md`) is not edited — already correctly
  places this ticket strictly after C1 (confirmed at line 13 of that file).
- `investigation.md` and `test_plan.md` are not edited by this plan's steps — they are already
  complete, historical records of the Investigate/Test-Plan phases; this plan's design sketch
  (Step 3) is deliberately placed in the ticket body instead, per the Summary's rationale.
- Before editing the ticket file, run `git status` first (per this repo's PR Lifecycle rule) to
  confirm no concurrent session has an in-flight edit to the same file, since the working
  directory can be shared across concurrent sessions.

## Dependency Map

All six steps write to the same single file (the ticket body) but touch disjoint sections, so
none has a hard ordering dependency on another's *content* — however, Step 6 should run last
since it summarizes/closes out sections that depend on Steps 1-5 having been written first (its
`## Completion Summary` references "Steps 1-5 above" and its `## Assumptions / Open Questions`
resolution note depends on Steps 1 and 2's findings being already recorded). Steps 1-5 may be
done in any order relative to each other; the order given (1→5) simply follows the ticket's own
AC ordering for readability. No step depends on any `src/`, `docs/`, or `config/` file changing —
none of those change in this plan.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — scope limited to design/plan artifacts; no implementation until C1 confirmed live | Step 1 (confirms + documents C1 live status), Step 3 (design sketch stays non-binding prose), all Scope Guards | `test_plan.md` Scope guard: `git diff --stat` confined to ticket/staging_artifacts paths |
| AC2 — Related Tickets names C1 as blocking dependency; SEQUENCE.md places this strictly after it | Already satisfied pre-plan (ticket `## Related Tickets` line already names `TCK-20260824-ROLLOUT-FLAG-DECISIONS`; `tickets/todos/m1-quick-wins/SEQUENCE.md` line 13 already places this ticket after it, `depends on:` noted) — Step 1 confirms/documents this, does not create it | `test_plan.md` Scope guard; manual confirmation both files already contain the required text (read, not edited) |
| AC3 — DECEPTIVE_DETECTED wiring states delta-reuse vs. new-writer decision | Step 4 | `test_plan.md` Scope guard; Acceptance Criteria Map cross-check (wording match confirmed above) |
| AC4 — ticket documents SocialBond.sentiment / SourceTrustEntry structural separation | Step 5 | `test_plan.md` Scope guard; Acceptance Criteria Map cross-check (wording match confirmed above) |

## Anti-Drift Notes

- Do not read Step 1's "C1 confirmed live" finding as license to begin real implementation in
  this ticket — `investigation.md`'s own Anti-Drift Hazards section warns against exactly this
  misreading. The literal Scope-section wording ("Land scope/design artifacts only") controls
  regardless of flag state.
- Do not let Step 3's design sketch collide with `LeadCertainty`
  (`src/core/strategic.py:34-39`) or `NormalizedInformationResponse.certainty` — the sketch must
  state composition, not duplication, per the schema-collision risk `investigation.md` flags.
- Do not let Step 3's design sketch reach into `SocialBond.sentiment` — Step 5's own finding
  (AC4) is that this must stay a separate ledger; a design sketch that quietly reuses
  `SocialBond.sentiment` as a secrecy signal would directly contradict what Step 5 documents in
  the same ticket.
- Do not treat `LeadContradictionSystem`'s always-on state-scan phase
  (`src/engine/pipeline_phases/lead_contradiction.py`) as a place a future secrecy/disclosure
  design could hook into — its own docstring explicitly excludes `concept`/`information` lead
  kinds (Step 2's citation).
- Do not silently upgrade `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-073` entry
  (`legacy_verified`, `test_path: null`) — out of scope for this ticket per the Scope Guards
  above; flagged for a future implementation ticket only.
- Do not delete or rewrite any existing bullet in `## Assumptions / Open Questions` when doing
  Step 6 — append the resolution notes only, preserving the full decision trail.

## Unresolved Questions

None. `investigation.md`'s own Risks and Open Questions section states no open question blocks
this ticket's own scope-only deliverable — the one item still genuinely open (whether a future
`DECEPTIVE_DETECTED` wiring reuses the `-0.25` delta or needs a differently-calibrated new writer)
is a human/product calibration decision that this ticket's AC3 only requires *stating*, which
Step 4 does; it does not require this ticket to decide the calibration question itself, so it is
not a blocker for this plan.
