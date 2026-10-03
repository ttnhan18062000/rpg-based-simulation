---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK
artifact_type: plan
tags: [economy, cognition]
---

# Implementation Plan — TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK

## Summary

This ticket is scope-only and BLOCKED: its "Implement" phase adds no code, only documentation
content to the ticket's own body (and, if needed, a verification-only pass over
`staging_artifacts/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK/investigation.md`, which already
contains the required content and is not expected to need edits). The approach is to transcribe
verified facts that already exist in `investigation.md` — the dead-on-arrival file:line evidence,
the "no foundation ticket exists" finding, and the Target Design Sketch — into the ticket body
itself so a future reader gets the citable evidence without having to open the investigation
artifact, then close out the standard ticket-body sections (Implementation Notes, Test Summary,
Files Changed, Completion Summary) truthfully reflecting that zero `src/`/`tests/` files changed.
No new design decisions are made in this plan; every fact below is transcribed from
`investigation.md`, which already verified it against source.

## Steps

### Step 1 — Add file:line evidence for the dead-on-arrival fact into the ticket body
**Files:** `tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` (no `src/` files)
**Change:** Add a "Dead-on-Arrival Evidence" subsection under `## Scope` (or immediately after it)
citing, transcribed verbatim from `investigation.md`'s Current Behavior section (which already
read and quoted the source at these exact locations — this step transcribes, it does not re-grep
or re-derive):
- `ValuePreferenceProfile` dataclass, `src/core/cognition.py:382-402` — all 7 fields
  (`survival`, `reward`, `knowledge`, `loyalty`, `pride`, `curiosity`, `caution`) default to `0.5`.
- `MotivationModel.values` field, `src/core/cognition.py:440-444` (specifically line 443:
  `values: ValuePreferenceProfile = field(default_factory=ValuePreferenceProfile)`).
- `MotivationBiasService.compute_bias_multiplier`, `src/domains/motivation/service.py:14-72`,
  Value-Preference-Profile delta block at lines 49-63: 4 of 7 fields consumed
  (`survival`, `pride`, `curiosity`, `reward`) via `(values.X - 0.5) * 0.5`; 3 fields
  (`knowledge`, `loyalty`, `caution`) never read anywhere in the method.
- Zero non-default production construction: `grep -rn "MotivationModel(" src/` and
  `grep -rn "ValuePreferenceProfile(" src/` both return zero matches; the sole production
  `CognitionModel` construction site is `src/core/builder.py:111`
  (`self._cognition = CognitionModel()`, zero-argument), which default-factories the whole chain
  to `0.5`.
- Mathematical consequence: `(values.X - 0.5)` evaluates to `0.0` for all 4 consumed fields, for
  every entity, on every call, in every production run — the Value Preference Profile branch of
  `compute_bias_multiplier` is a permanent no-op contribution in production.

**Do NOT touch:** `src/core/cognition.py`, `src/domains/motivation/service.py`,
`src/core/builder.py` — this is a citation transcription, not a code change. Do not alter the
existing `## Scope` bullet wording beyond appending this evidence subsection.
**Verify:** Ticket's own AC — "Ticket body states the verified dead-on-arrival fact with file:line
evidence so future readers don't re-derive it." No automated test applies (per `test_plan.md`'s
"New Tests Required: None" — this AC is documentation content, not runtime behavior).

### Step 2 — Confirm and lightly refine Related Tickets / Assumptions naming the foundation ticket as a hard blocker
**Files:** `tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` (`## Related Tickets`
lines 55-56, `## Assumptions / Open Questions` lines 70-73)
**Change:** Cross-check the existing wording against `investigation.md`'s "No foundation ticket
exists for populating MotivationModel.values" section, which searched `tickets/`, `docs/`, and
`stored_artifacts/` (15 files matched a `MotivationModel.values`/`ValuePreferenceProfile` grep;
none is a population effort — closest are `TCK-20260619-E62C-MOTIVATION-OVERLAY` and
`TCK-20260619-E62-CULTURE-DRIFT`, which explicitly keep the cultural overlay transient and
non-durable, and `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md:115-119,132-133,148`
Idea 24, which originates this exact blocker). Current ticket wording ("None. No foundation
ticket for MotivationModel.values exists yet anywhere in docs/tickets/stored_artifacts...") is
already accurate and needs no factual change; add one clarifying sentence naming the search scope
(15 files checked across `tickets/`, `docs/`, `stored_artifacts/`) so the "not yet filed" claim is
traceable to a specific search rather than asserted bare.
**Do NOT touch:** Do not invent a placeholder ticket ID for the foundation ticket — none exists.
Do not change `## Related Code Areas` or `## Related Docs` (already accurate per investigation's
"Docs Requiring Update" section, which found no doc needs to change for this ticket's own closure).
**Verify:** Ticket's own AC — "Ticket names the not-yet-existing MotivationModel.values foundation
ticket as a hard blocking dependency in Related Tickets/Assumptions."

### Step 3 — Add a condensed Target Design Sketch pointer into ticket body Implementation Notes
**Files:** `tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` (`## Implementation
Notes`, currently empty at lines 75-76)
**Change:** Add a short pointer plus condensed summary — not a full reproduction — of the Target
Design Sketch already written in full in `investigation.md` (its "Target Design Sketch for
Personal Economy & Material Ambition axis" section, lines 263-317): a new 8th field
`material_ambition: float = 0.5` on `ValuePreferenceProfile` (distinct from `reward`, which stays
generic loot/gold desirability); consumption follows the existing `elif` branch pattern at
`service.py:49-63` (`(values.material_ambition - 0.5) * 0.5` against an illustrative,
not-yet-final tag bucket); explicit non-goal restated verbatim — this sketch does not specify the
content-schema/emergent-derivation population mechanism itself, that is the foundation ticket's
job. State in the ticket that the full sketch lives in `investigation.md`, and this is a
summary/pointer only, so design authority isn't duplicated across two files with a risk of drift.
**Do NOT touch:** `staging_artifacts/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK/investigation.md`
itself — it already contains the full sketch (historical/frozen once written); this step does not
re-edit it. Do not add implementation code or pseudo-code beyond the illustrative snippet already
in `investigation.md` line 299-301. Do not commit to a final tag vocabulary or weight coefficient
— both are explicitly "illustrative, not final" per `investigation.md:303-304`.
**Verify:** Ticket's own AC — "Ticket is created and moved to a scoping-only/BLOCKED state --
documents target design, contains no implementation" (the "documents target design" half).

### Step 4 — Verify Conditional/Deferred Acceptance Criteria section stays consistent with the design sketch
**Files:** `tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` (`## Conditional /
Deferred Implementation Acceptance Criteria`, lines 50-53, already present)
**Change:** Cross-check the three existing Deferred AC checkboxes against the design-sketch
content added in Step 3. The ticket's Deferred ACs currently name the axis generically ("A
Personal Economy & Material Ambition motivation axis"); after Step 3 names the concrete field
`material_ambition` in Implementation Notes, align the first Deferred AC bullet to reference
`material_ambition` explicitly so the ACs and the design-sketch pointer use one consistent field
name (avoids a naming drift between sections that a future foundation-ticket author could
misread as two different proposals). Confirm the doc-update targets named in the third Deferred AC
(`docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`) match
`investigation.md`'s "Mechanics / Engine Constraints" finding that `04_strategic_cognition.md`
currently has zero references to `MotivationModel`/`ValuePreferenceProfile`/`MotivationBiasService`
(confirmed by grep) — the deferred AC is correctly scoped as "add a section that doesn't exist yet,"
not "update an existing section."
**Do NOT touch:** Do not add new Deferred ACs beyond the existing 3. Do not convert any Deferred AC
into a current, checkable AC — each remains conditional on the not-yet-existing foundation ticket
landing first, per the ticket's own Out of Scope.
**Verify:** Ticket's own AC — "Eventual (unblocked) implementation ACs are stated as
conditional/deferred."

### Step 5 — Confirm Status stays BLOCKED and frontmatter remains valid
**Files:** `tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` (frontmatter block
lines 1-10, `## Status` lines 17-18)
**Change:** Confirm the `## Status` body field remains `BLOCKED` (not `OPEN`/`INPROGRESS`/`DONE`)
per `tools/ticket_field_values.py`'s allowed value set, and confirm frontmatter
(`status: active`, `layer: economy`, `authority: P1`, `audience: agent`,
`tags: [economy, cognition]`) still validates — `layer: economy` and both tags are already
registry-backed and used by this ticket's own sibling investigation/test_plan artifacts, and by
precedent tickets `TCK-20260619-E62C-MOTIVATION-OVERLAY`/`TCK-20260619-E62-CULTURE-DRIFT` in the
same subsystem. This step is a verification checkpoint — no field change is expected unless Steps
1-4's edits accidentally altered frontmatter formatting, in which case restore it exactly.
**Do NOT touch:** Do not change `status: active` to `status: historical` in the ticket's own
frontmatter — that transition belongs to the eventual `tickets/done/` migration at Finalize, not
this Implement phase. The ticket stays `inprogress` with `status: active` until moved to done.
**Verify:** Definition-of-Done's "Frontmatter valid" condition, script-checked by
`done-checker`'s `frontmatter_valid` condition at Verify. No single ticket AC checkbox covers this
directly — it's a workflow-wide requirement re-confirmed here since Steps 1-4 touch the same file.

### Step 6 — Fill Implementation Notes (remainder), Test Summary, Files Changed, Completion Summary
**Files:** `tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` (bottom sections,
lines 75-85)
**Change:** Complete the standard ticket close-out sections, run last since they summarize Steps
1-5's final state:
- **Implementation Notes**: append to Step 3's design-sketch pointer a closing line: "No `src/`
  or `tests/` files were touched by this ticket; it is scope-only per its own Acceptance
  Criteria and Out of Scope."
- **Test Summary**: state, per `test_plan.md`'s "Scoped Pytest Commands" section, that no new
  tests were required (every AC in this ticket is documentation/scoping content, not runtime
  behavior — none is testable by an automated test) and that the optional sanity-check command
  (`pytest tests/unit/domains/motivation/test_phase14_bias_service.py
  tests/unit/motivation/test_motivation_bias_culture.py
  tests/unit/domains/motivation/test_phase14_motivation_models.py -v`) is not required for this
  ticket's own Definition of Done since no `src/`/`tests/` files changed; if the implementer runs
  it anyway as a sanity check, record the pass/fail result here.
- **Files Changed**: list exactly `tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md`
  and, if this plan's own edits are considered in scope for the record,
  `staging_artifacts/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK/plan.md` — no `src/` or `tests/`
  path may appear in this list.
- **Completion Summary**: 1-2 sentences — ticket scoped and blocked per its own design, the
  dead-on-arrival fact recorded with file:line citations, the foundation ticket named as a hard
  blocker, no implementation performed.

**Do NOT touch:** Do not list any `src/` or `tests/` path in Files Changed — doing so would
falsely claim a code change this ticket did not make.
**Verify:** Ticket's own ACs — "contains no implementation" and "No src/ changes are made under
this ticket while blocked." The Files Changed section is the auditable record proving the latter.

## Scope Guards

- **No `src/` file may be created, modified, or deleted under this ticket at any step.** This
  applies to every step above without exception, including Step 1's citations of `src/core/
  cognition.py`, `src/domains/motivation/service.py`, and `src/core/builder.py` — those are
  read-only citations transcribed from `investigation.md`, never edits.
- **No implementation of the Personal Economy & Material Ambition axis itself.** Step 3 documents
  intent only (field name, consumption pattern) — it does not add the `material_ambition` field to
  `ValuePreferenceProfile`, does not add a branch to `compute_bias_multiplier`, and does not touch
  any test file.
- **No designing the content-schema/emergent-derivation mechanism for populating
  `MotivationModel.values` generally.** That belongs to the separate, not-yet-scoped foundation
  ticket per this ticket's own Out of Scope. Step 3's design sketch is narrowly about how the
  Personal Economy axis would attach and be weighted *once* that foundation exists — never how the
  foundation populates values in general.
- **`staging_artifacts/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK/investigation.md` and
  `test_plan.md` are not edited by this plan's steps** unless a factual drift is discovered during
  Step 1/2 cross-checking (none is expected — both were read in full to produce this plan and are
  internally consistent with the ticket body).
- **`tickets/todos/m1-quick-wins/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md` (the byte-identical
  duplicate flagged in `investigation.md`'s "Duplicate ticket file" section) is explicitly out of
  scope for this plan's Implement phase.** Its deletion is a Finalize-phase step per the Workflow
  Rule's "After Work" section ("delete the source file from the subfolder"), not an Implement-phase
  edit, and falls outside this ticket's stated allowed file set
  (`tickets/inprogress/{ticket_id}.md` + `staging_artifacts/{ticket_id}/`).
- **`tickets/working_log.csv` and `docs/REGISTRY.yaml` are not touched by this plan.** Both are
  Finalize-phase writes (append-only log entry; automatic registry regeneration), outside this
  Implement phase's scope.

## Dependency Map

- Step 1 and Step 2 are independent of each other and of Step 3 — each edits a distinct section of
  the same file and can be done in any order.
- Step 3 is independent of Steps 1-2 but should precede Step 4, since Step 4 aligns the Deferred
  AC wording (`material_ambition` field name) to what Step 3 introduces.
- Step 4 depends on Step 3 (needs the field name Step 3 establishes).
- Step 5 is a verification checkpoint over the cumulative edits from Steps 1-4 — run it after all
  four, not before, so it catches any accidental frontmatter drift introduced along the way.
- Step 6 depends on Steps 1-5 completing, since Files Changed and Completion Summary must reflect
  the final state of the ticket body, not an intermediate one.

Suggested order: 1 → 2 → 3 → 4 → 5 → 6 (Steps 1 and 2 may be swapped or done in parallel without
consequence).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Ticket is created and moved to a scoping-only/BLOCKED state -- documents target design, contains no implementation. | Step 3 (documents target design), Step 6 (confirms no implementation via Files Changed) | No automated test — manual content review (`test_plan.md`: "New Tests Required: None") |
| Ticket names the not-yet-existing MotivationModel.values foundation ticket as a hard blocking dependency in Related Tickets/Assumptions. | Step 2 | No automated test — manual content review |
| Ticket body states the verified dead-on-arrival fact with file:line evidence so future readers don't re-derive it. | Step 1 | No automated test — manual content review; underlying code facts are covered by existing tests in `tests/unit/domains/motivation/test_phase14_bias_service.py`, `tests/unit/domains/motivation/test_phase14_motivation_models.py`, `tests/unit/motivation/test_motivation_bias_culture.py` staying green (optional sanity check, per `test_plan.md`) |
| Eventual (unblocked) implementation ACs are stated as conditional/deferred. | Step 4 | No automated test — manual content review |
| No src/ changes are made under this ticket while blocked. | Step 6 (Files Changed audit); guarded across all steps by Scope Guards | No automated test — `git diff --stat` showing zero `src/`/`tests/` paths touched is the auditable proof at Verify |

## Anti-Drift Notes

- **Do not let a future session "helpfully" start wiring `values` construction into
  `src/core/builder.py` under this ticket** — explicitly Out of Scope (foundation-ticket
  territory), and this ticket's own AC requires zero `src/` changes while BLOCKED
  (`investigation.md`, "Anti-Drift Hazards").
- **Do not conflate the dead-on-arrival finding with the doctrine branch**
  (`preferred_route_tags`/`avoided_route_tags`, `service.py:41-47`) or the **cultural overlay
  branch** (`service.py:65-70`) of `compute_bias_multiplier` — both are populated/live today and
  are out of scope for the dead-on-arrival claim, which is scoped only to the
  `ValuePreferenceProfile` branch (`service.py:49-63`).
- **The `WORLD-CULT-002` parity ledger entry** (`docs/parity_ledger/world_dynamics.yaml:1196-1210`)
  is about the transient cultural overlay staying non-durable — it is unaffected by this ticket and
  must not be edited under this ticket ID; no parity ledger entry exists yet for the
  `ValuePreferenceProfile` defaults dead-on-arrival state itself, and creating one is deferred to
  the future foundation ticket (per `investigation.md`'s "Parity Ledger Overlap" and this ticket's
  own third Deferred AC).
- **This ticket does not trigger the Authoritative Mechanics Rule's "if logic changes, update the
  doc" obligation** — it changes no behavior, so `docs/mechanics/04_strategic_cognition.md` is
  correctly left untouched (it has zero existing Motivation/values coverage to update, per
  `investigation.md`'s "Docs Requiring Update" section).
- **3 of 7 `ValuePreferenceProfile` fields (`knowledge`, `loyalty`, `caution`) are inert in
  `compute_bias_multiplier` today independent of the defaults problem** (never read at all) — the
  Target Design Sketch (Step 3) already accounts for this by recommending `material_ambition` be a
  genuinely new 8th field rather than reusing one of the three unread fields, since reusing an
  unread field would still produce zero effect even after a foundation ticket populates it.
- **No shared resource (registry, counter, log) is written by this plan's steps.** Every step
  writes only to `tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md`, a file no
  other ticket or concurrent process writes to. `tickets/working_log.csv` and
  `docs/REGISTRY.yaml` — the two genuinely shared, multi-writer resources in this workflow — are
  Finalize-phase writes outside this plan's scope, so no ordering/race/collision analysis applies
  here.

## Unresolved Questions

None. The one open item surfaced in `investigation.md`'s "Risks and Open Questions" section — the
M1 epic doc's own Idea 24 leaving unresolved whether the future `MotivationModel.values` foundation
ticket belongs inside the epic or a different milestone/epic (`docs/plans/rpg_design_roadmap/
rpg_m1_quick_wins_epic.md:148`) — is explicitly a decision for whoever files that not-yet-existing
foundation ticket, not for this ticket's own closure. This ticket's own scope (documenting the
target design, recording the dead-on-arrival evidence, naming the blocker, staying BLOCKED with no
`src/` changes) does not depend on that placement decision being resolved first.
