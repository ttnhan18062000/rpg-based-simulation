---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Roadmap — Completing the Simulation Semantic Control Plane Design

**Purpose.** [architecture.md](architecture.md), [agent_operating_model.md](agent_operating_model.md),
and [rollout_plan.md](rollout_plan.md) state the model and the perpetual operating philosophy
(Stage D of the rollout plan never ends — mapping coverage grows for as long as tickets keep
touching RPG-core domains). This roadmap is narrower and **bounded**: it sequences the specific
work needed to take the design from "written" to "proven infrastructure a ticket can actually
build on," matching the scope discipline `docs/world_rules/roadmap.md` already used for the Rule
Catalog itself (that roadmap stops at "Catalog frozen," not at "every Rule is implemented"). This
roadmap stops at **M4** — a second slice proves the model generalizes and a real cross-domain view
exists. Everything past that is Stage D/E/F of `rollout_plan.md`: ongoing maintenance, not a
completion target.

**Status (2026-09-23).** Design fully written (`architecture.md`, `agent_operating_model.md`,
`rollout_plan.md`). No milestone below has started. No ticket has been opened for any of them yet
— per this project's own Workflow Rule, opening `tickets/inprogress/{ticket_id}.md` is the first
step of actually starting M0, not something this roadmap does on its own.

**What this roadmap deliberately leaves open**, per `rollout_plan.md`'s own Stage A discipline —
do not design the final ontology up front: the exact mapping file's path, field names, and
serialization format are **M0's own deliverable**, not decided here. What *is* fixed here is the
sequence and each milestone's exit criteria.

---

## M0 — Schema and validator (gated on nothing)

**Goal.** Turn `architecture.md` §3's deliberately-deferred mapping shape into a real, validated
file, the same way `registries/mechanisms.yaml` itself started.

**Deliverables — three separate schemas, not one malformed row shape:**
1. **Rule↔Mechanism mapping edges.** Each entry: `rule_id`, `mechanism_id`, `edge_type` — exactly
   one of `REALIZES` / `PARTIALLY_REALIZES` / `CONSTRAINED_BY` — plus an evidence citation and a
   date. These three edge types, and only these three, connect a Rule to a Mechanism.
2. **Mechanism→Mechanism causal edges.** A separate schema: `producer_mechanism_id`,
   `consumer_mechanism_id`, plus evidence/date. Store one directed fact
   ("A produces input for B"); the inverse ("B consumes the result of A") is a generated view, not
   a second hand-authored row — the same "don't store what traversal can compute" discipline
   `depends_on`'s own dependent-count already follows. **This is a distinct relation from
   `depends_on`, and must not be folded into it or into the Rule↔Mechanism schema above** — mixing
   a Rule-to-Mechanism edge and a Mechanism-to-Mechanism edge into one `edge_type` enum on one row
   shape (an earlier draft of this roadmap did exactly this) produces rows where half the declared
   values don't have a real `rule_id` to attach to. Keep the two schemas separate.
3. **Rule-level realization classification.** A third, separate record per Rule: its own aggregate
   `SUPPORTED`/`PARTIAL`/`CONFLICTING`/`MISSING`/`INERT-OFF`/`UNKNOWN` verdict, with evidence and a
   review date. **Never inferred mechanically from the edge list above** — a Rule can have several
   mapped mechanisms in different relations while its own realization is a human judgment call
   (`architecture.md` §3/§4). Storing only the edges and trying to derive this classification from
   them would repeat the exact "derive a relation that isn't actually mechanical" mistake this
   design already rejected once for the Mechanism Registry's own `system` tier.

**Also required:**
- A validator (mirroring `tools/mechanism_registry/registry.py::validate()`) enforcing at least:
  every `rule_id` resolves to a real Rule ID under `docs/world_rules/` (parsed, not hand-checked —
  **verified for this roadmap: zero duplicate Rule IDs exist across all 172 IDs today**, so a bare
  Rule ID is already a safe foreign key with no migration needed first), every `mechanism_id`
  resolves to `registries/mechanisms.yaml`, `edge_type` in schema (1) is one of the three declared
  values, `edge_type` in schema (2) is well-formed producer/consumer, no duplicate
  `(rule_id, mechanism_id, edge_type)` triple in (1), no duplicate directed pair in (2).
- Proof the validator actually rejects bad input — deliberately broken fixtures, per this repo's
  own established CI-wiring discipline (`TCK-20260920-MECHANISM-REGISTRY-CI-WIRING`: every
  blocking check was proven to fail on deliberately broken input, not just pass on clean input).

**Exit criteria.** All three schemas exist and are validated; validator passes on empty/seed data
and is proven to fail on at least one deliberately-invalid fixture per invariant. Schema documented
in `architecture.md` §3 in place of its current "deliberately undecided" note.

**Explicitly not in scope for M0.** No real mapping entries yet — this is infrastructure only, the
same sequencing `mechanisms.yaml` itself followed (schema and validator before the 93 real rows).

---

## M1 — First operational slice: Territory / Control (gated on M0)

**Goal.** Execute `rollout_plan.md` Stage B for real, using M0's validator against real data for
the first time.

**Deliverables:**
- Real mapping entries for every `TERR-0N` Rule in
  `docs/world_rules/places-culture/territory-control.md` against their actual mechanisms —
  verify the candidate set (`regional_sovereignty`, `regional_trauma`, and any `RegionState`/
  `city`-adjacent mechanism) against the live registry at execution time; `rollout_plan.md`'s own
  candidate list is a starting hint, not a fixed answer.
- Each entry cites real evidence — a code path, a Rule's own already-written repository-evidence
  prose (e.g. `TERR-01`'s `owner_faction_id` finding), or both. No entry without a citation.
- The first domain management view (`architecture.md` §8's six axes) generated for Territory only.
- A written note of every schema friction point hit — feeds one bounded revision of M0's schema if
  needed. This is the one place a schema revision is expected and budgeted for; it is not expected
  to recur at M3.

**Exit criteria.** Territory's mapping is populated and passes M0's validator with zero manual
overrides of a reported violation. Every one of the six management-view axes has an explicit,
evidenced state — including `UNKNOWN` where no suitable evidence currently exists (e.g. "Observed
Outcome: `UNKNOWN` — no runtime evidence currently exists" is a legitimate, complete answer, not a
gap to close before M1 can exit). **The requirement is an explicit state per axis, not working
instrumentation per axis** — silent absence (an axis simply not rendered) is the actual failure
condition, not the presence of `UNKNOWN`.

---

## M2 — Drift detection (gated on M1 — needs real mappings to check drift against)

**Status: SHIPPED** 2026-09-24 (`TCK-20260924-M2-MAPPING-DRIFT-DETECTION`).

**Goal.** Execute `rollout_plan.md` Stage C's detector, scoped to what M1 just created.

**Deliverables (shipped):**
- A report-only detector, `tools/semantic_control_plane/mapping_drift_check.py` (mirroring
  `mechanism_registry_changed_code_check.py`'s own pure-core/git-wrapper/CLI philosophy), catching
  two of the three named drift classes: (1) an `implemented_by` path cited by a mapped mechanism
  changed since the mapping entry was last reviewed; (3) a mapped mechanism's `verified.verdict`
  changed since the mapping was last reviewed, recovered from `registries/mechanisms.yaml`'s own
  git history pinned to the commit that last touched `registries/rule_mechanism_edges.yaml` on or
  before the row's date. Drift class (2) — rename/removal/split/merge with a resolvable ID — is
  consciously descoped as its own detector code: no lineage field exists anywhere in the schema,
  and the one real precedent case is undetectable short of duplicating the changed-code check's own
  whole-entry-diff approach on a new axis, for a scenario that has not occurred once among M1's
  five mapped mechanisms. See `stored_artifacts/TCK-20260924-M2-MAPPING-DRIFT-DETECTION/
  investigation.md`'s "Risks and Open Questions" for the full reasoning. (Plain rename/removal is
  already a hard validator failure today via `registry.py::validate_rule_mechanism_edges()`'s
  unresolved-id check, independent of this milestone.)
- Wired via `make semantic-control-plane-drift-check`. No CI wiring at this milestone, per plan
  (Territory alone is a handful of entries).
- Proof each implemented drift class fires on a deliberately-stale fixture
  (`tests/unit/tools/test_semantic_control_plane_drift_detector.py`).

**Exit criteria.** Running the detector against Territory's live mapping reports "clean" today
(confirmed: `make semantic-control-plane-drift-check` → 0 cited-code findings, 0 verdict findings,
2026-09-24), and reports a specific violation when a fixture mapping is deliberately made stale
(covered by the fixture tests above).

---

## M3 — Existing-finding ingestion (ongoing stream, not a bounded gate — starts after M0, runs in parallel with everything after)

**Goal.** Execute `rollout_plan.md` Stage C's "ingest, don't launder" step across the frozen
Catalog. **Corrected scope**: this is a permanent, incremental ingestion process
(`docs/world_rules/review-exports/*.md`'s "Implementation Candidates — Non-Binding" sections get
triaged as domains are touched, the same way `implemented_by` coverage itself grew — 76 of 93
populated organically, never backfilled in one pass), **not a bounded, full-catalog prerequisite
that must finish before M4 can start.** Gating M4 on all 12+ batches being triaged would turn this
rollout into a full-catalog migration project — exactly what `rollout_plan.md`'s own Stage D
philosophy and `architecture.md` §7's `UNKNOWN`-is-permanent discipline already argue against.

**Process (established once, then repeats forever, same as Stage D):**
- For each named finding touched by current work: re-verify against the current registry/code
  state (never trust the prose as already-current fact —
  `mechanism_identity_and_change_taxonomy.md` §4's own precedent for re-checking an earlier
  unevidenced claim applies here too) and either promote it to a real mapping entry (through M0's
  validator) or record explicitly why it stays `UNKNOWN`.
- Track lightweight metrics if convenient (candidate findings reviewed / promoted / rejected /
  stale), but never make "100% of candidates ingested" a milestone exit criterion for anything.

**M3's own minimum bar, so it isn't purely open-ended from day one:** before M4 begins, triage the
Implementation Candidates sections specifically for **Territory/Control and Combat/Conflict** —
the two domains M1 and M4 actually need. The rest of the Catalog remains `UNKNOWN` until later
tickets or a targeted sweep touches it, exactly per Stage D.

**Exit criteria.** There is no "M3 complete" state — this stream is permanent (like Stage D). The
gate M4 actually depends on is narrower and lives in M4's own gating clause below.

---

## M4 — Second slice and first cross-domain view (gated on M1, M2, and M3's Territory+Combat-scoped triage only — not full-catalog M3)

**Goal.** Prove the model generalizes past Territory's own idiosyncrasies (a domain whose defining
finding is a *conflict*, `CONFLICTING`) by running it against a second domain, then produce the
first real multi-domain management view (`rollout_plan.md` Stage E, pulled forward here because a
*second* slice is this roadmap's own generalization test, not Stage D's ongoing organic growth).

**Chosen second domain: Combat / Conflict**
(`docs/world_rules/capability-progression/conflict-combat.md`). **Corrected 2026-09-23** — an
earlier version of this section cited a stale rollup snapshot (71.4%/71.4% vs. 35.5%/26.9%
baseline) and framed Combat as an expected "clean, mostly-`SUPPORTED`" contrast to Territory. Both
claims were checked against this repo's own live data (an independent peer review caught this) and
neither holds:
- **The rollup is live-computed and drifts** (`docs/brainstorm/mechanism_system_rollup_view.md`
  is regenerated from the registry, never a fixed number — cite it as "run
  `make mechanism-system-rollup-view` and read the current `combat` row," never a hardcoded
  percentage that will go stale again the next time the registry changes).
- **Combat is not actually uniform, and one of its two known instabilities is still live.** Checked
  directly in `registries/mechanisms.yaml`: of combat's 8 mechanisms, `tactical_decision` is
  `state: done` but `verified.verdict: contradicted` (its ATTACK-intent branch doesn't actually
  fire in real corpus play), `status_effects` is `state: orphan`, and `skill_unlocks` is
  `state: partial`. The `tactical_decision` finding is settled *as fact* — closed investigation
  `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`, nothing for M4 to wait on
  reporting — but the *behavior* it found is not settled: the ticket's own closing line states the
  strategic layer's dispatch gate never derives a `DEFEAT_ENEMY` objective from the winning goal,
  and explicitly leaves "whether this should change" as "a design question for the user," not
  resolved by that ticket. If that design question is ever resolved, `tactical_decision`'s verdict
  can move. Separately, a genuinely open, paused ticket,
  `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`, sits in this same territory and could
  also change combat's real numbers if it resumes. **Neither of these is a hard gate on M4** — both
  are named here so M4 re-checks the live registry state (including `tactical_decision`'s own
  current verdict, not just the numbers cited anywhere in this document) immediately before
  finalizing its mapping, rather than treating `contradicted` as permanent.

**Combat is kept as the second domain anyway** — not because it's expected to be clean, but
because it is *mixed*: some mechanisms cleanly `SUPPORTED`, at least one (`tactical_decision`)
likely to map `CONFLICTING` or `PARTIAL` against whatever Rule covers actually-attacking, at least
one `orphan`. A domain in a mixed real state is arguably a *better* generalization test than a
uniform one — it exercises the full classification vocabulary in one slice rather than mostly one
value, which a genuinely "clean" domain would not have done.

**Deliverables:**
- Real mapping entries for Combat/Conflict's Rules against real mechanisms (`combat_resolution`,
  `tactical_decision`, and others — verify against the live registry at execution time, not
  against any state described in this document).
- Both domains' management views combined into the first real cross-domain view
  (`architecture.md` §8), with `mapped`/`unmapped` and `verified`/`unverified` counts shown
  alongside any classification breakdown, per the pre-filtered-sample lesson already on record
  (`TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`).
- A short written comparison of what the two views actually show.

**Success condition, stated precisely to avoid biasing the result:** the model must faithfully
represent whatever the real evidence shows for each domain, and two structurally different domains
must be representable without distorting either into the same shape. **This is not**: "Territory
must come out looking bad and Combat must come out looking clean." If Combat's real mapping turns
up meaningful `PARTIAL`, `CONFLICTING`, or `UNKNOWN` results — which the known `tactical_decision`/
`status_effects`/`skill_unlocks` evidence above already makes likely — those are recorded as-is,
named up front as expected rather than treated as a surprise, and never smoothed over or used as
grounds to adjust the classification model to manufacture a cleaner contrast.

**Exit criteria.** Two domains mapped, validated, and rendered in one combined view; the comparison
recorded honestly, whatever it actually shows.

---

## Past M4 — not this roadmap's job

Once M4 closes, the design is proven, not finished-forever — `rollout_plan.md` Stage D (organic
per-ticket expansion), Stage E (broader management baseline as more domains accumulate coverage),
and Stage F (Context Compiler, only once real query patterns exist) continue indefinitely. This
roadmap does not track them; `rollout_plan.md` already does, and re-stating a perpetual stage as a
"milestone" with an exit criterion would misrepresent it as something that finishes.

## Related

- [architecture.md](architecture.md), [agent_operating_model.md](agent_operating_model.md),
  [rollout_plan.md](rollout_plan.md) — the design this roadmap sequences into concrete milestones.
- `docs/world_rules/roadmap.md` — the sibling roadmap this one's own scope discipline (stop at
  "proven," not "everything implemented") is modeled on.
- `docs/plans/mechanism_registry_initiative.md`, `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` — the
  validator-proof-on-broken-input discipline M0 and M2 both reuse.

---

## Appendix — Standalone context for a reviewer not opening the referenced files

Everything above cites other documents, registries, and tickets by name without restating their
content, on the assumption the reader has them open. This appendix removes that assumption. It
summarizes only what is needed to read M0–M4 above and judge whether the sequencing makes sense —
it is not a substitute for the referenced files if you're going to do the actual work.

### A. The two things this project is connecting

**The World Rule Catalog** (`docs/world_rules/`) is a frozen, 172-rule specification of what the
simulated game world is *supposed to mean* — not how it's coded. Example: one rule states that a
territory's "claim" (an assertion of right), "control" (who actually governs it), "jurisdiction,"
"ownership," "occupation," and "cultural association" are six distinct facts that must never be
silently collapsed into one — a kingdom can validly *claim* land a rival *occupies*, without that
being an error state. Rules are grouped into ~40 topic files (Territory/Control, Combat/Conflict,
Knowledge, Economy, etc.) and were drafted in 12 sequential batches, each independently reviewed
and marked PASS before the next began. It is "frozen" the way a ratified constitution is frozen:
changing a rule after freeze requires a deliberate, documented decision, not a routine edit.

**The Mechanism Registry** (`registries/mechanisms.yaml`) is a separate, 93-row catalog of what
*code* actually exists in the simulation, independent of what it's supposed to mean. Each row (a
"mechanism," e.g. `combat_resolution`, `regional_sovereignty`) records:
- `state` — one of exactly six values: `done`, `partial`, `gap`, `orphan` (code exists, nothing
  calls it), `gated` (exists behind a feature flag), `skeleton` (stub only). **This is a different
  axis from the Rule Catalog's own classification below — a mechanism can be `state: done` (the
  code is real and correct) while still failing to satisfy what a Rule requires.**
- `implemented_by` — the actual source file/class/method, checked against disk (a deleted file
  fails validation the day it's deleted).
- `verified` — whether anyone has actually *observed* the mechanism working at runtime (as opposed
  to just existing), and by what instrument: `code_trace` (weakest — proves the code is reachable,
  proves nothing about whether it ever actually runs), `scenario`, `corpus_run`, or `census`
  (all runtime evidence). This distinction exists because of a real incident: a combat-judgment
  mechanism was correctly marked "implemented" and turned out to have zero real effect across
  every tested condition — the code ran, and did nothing.
- `depends_on` — a narrow, hand-authored list meaning only "cannot produce a meaningful result
  without this other mechanism already having run." Deliberately does not mean call order, which
  system it belongs to, or containment.

**The gap this roadmap exists to close, confirmed by directly searching both**: as of this
roadmap's writing, **zero** of the 172 Rules cite a mechanism id, and **zero** of the 93 mechanisms
cite a Rule id. The two catalogs have never been cross-referenced. M0–M4 build and prove the first
real connective layer between them.

### B. Vocabulary used above without re-defining it every time

- **Rule ↔ Mechanism mapping edge** — a recorded fact of the shape "Rule X relates to Mechanism Y,
  in this specific way." Exactly three relationship types, and these three only ever connect a
  Rule to a Mechanism:
  - `REALIZES` — this mechanism is a real implementation of what the Rule requires.
  - `PARTIALLY_REALIZES` — implements only part of what the Rule covers.
  - `CONSTRAINED_BY` — the Rule bounds this mechanism's allowed behavior without being its main
    implementation.
- **Mechanism → Mechanism causal edge** — a *separate* kind of fact, connecting two mechanisms to
  each other, not a Rule to a mechanism: `PRODUCES_INPUT_FOR` (one directed edge, hand-authored;
  its inverse, "consumes the result of," is generated automatically rather than also hand-authored,
  the same "don't store what can be computed" rule `depends_on`'s own dependent-count already
  follows). M0's job is to decide the exact file/schema for both of these, kept as two separate
  structures rather than one mixed row shape.
- **Rule-level realization classification** — a *third*, separate kind of record: one classification
  per Rule (see next bullet), not per edge. A Rule can have several mapped mechanisms in different
  relations while its own realization classification remains a single, separately-recorded human
  judgment call — never mechanically inferred by counting or combining its edges.
- **Realization classification** — a separate, already-established vocabulary (reused here, not
  invented for this roadmap) describing whether a Rule's real-world requirement is actually met by
  the code today: `SUPPORTED`, `PARTIAL`, `CONFLICTING` (code exists and actively does the *wrong*
  thing relative to the Rule — the worst case, worse than simply missing), `MISSING` (investigated,
  confirmed absent), `INERT-OFF` (exists but behind a disabled flag), or `UNKNOWN`.
- **`UNKNOWN` vs. `MISSING`** — not interchangeable. `MISSING` means someone investigated and
  confirmed the capability is genuinely absent. `UNKNOWN` means nobody has checked yet. Given
  172 × 93 possible pairings, the overwhelming majority will sit at `UNKNOWN` for a long time by
  design — this is treated as a correct, permanent, expected state throughout this roadmap, not a
  gap to be embarrassed about or rushed to eliminate.
- **"Gated on"** — a milestone cannot start until the milestone(s) it's gated on have met their
  exit criteria. **"Exit criteria"** — the specific, checkable condition that ends a milestone; not
  a vague sense of "good enough."
- **`docs/world_rules/roadmap.md`** — the equivalent sequencing document for the World Rule Catalog
  itself (the 12 batches mentioned in §A above). Cited here purely as a precedent for scope
  discipline: that roadmap declares victory at "the Catalog is fully drafted and reviewed," not at
  "every rule has been implemented in code" — this roadmap copies that same stopping-point logic
  for M4 rather than trying to plan all the way to full implementation.

### C. What `rollout_plan.md`'s "Stage A–F" (cited throughout M0–M4) actually are

A separate document lays out the long-run, never-ending operating model this roadmap's milestones
plug into. Brief summary, since M0–M4 reference specific stages by letter:
- **Stage A** — decide the minimum data shape needed (no final schema yet) → this is M0.
- **Stage B** — the first real slice of actual mapping data, Territory/Control → this is M1.
- **Stage C** — start drift detection, and separately, ingest existing prose findings → split here
  into M2 (detection) and M3 (ingestion) because they have different gating needs.
- **Stage D** — ongoing, perpetual: every future ticket that touches a mapped domain
  opportunistically updates/validates its mapping as part of normal work, forever. Not a milestone
  because it never finishes.
- **Stage E** — a management view spanning many domains once enough of them have real coverage →
  pulled forward partially into M4 (the first *two*-domain view) as this roadmap's own
  generalization test, ahead of Stage E's fuller, later, organically-grown version.
- **Stage F** — a future tool that lets an agent ask one query and get back a compact, relevant
  packet of Rules/mechanisms/evidence, built only after real usage shows what such queries look
  like. Explicitly not started by this roadmap.

### D. The specific past incidents cited as precedent, summarized

- **`TCK-20260920-MECHANISM-REGISTRY-CI-WIRING`** — when the Mechanism Registry's own automated
  checks were wired into CI, each one was deliberately tested against *deliberately broken* input
  first, to prove it actually catches the problem it claims to catch, not just that it passes on
  already-correct data. M0 and M2 both require the same proof for their own new validators/
  detectors.
- **`TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`** — a batch of 20 mechanisms was
  checked and reported a 100% pass rate, which looked like strong evidence until it was pointed
  out that all 20 had been pre-selected specifically *because* they already had prior evidence of
  working — the population was rigged to pass before any checking happened. M4 cites this to
  justify always showing raw mapped/unmapped and verified/unverified counts next to any percentage,
  never a percentage alone.
- **`mechanism_identity_and_change_taxonomy.md` §4** — while re-checking mechanism identity
  questions, an earlier claim of "these two things are the same, no separate implementation
  exists" turned out to be based on an incomplete search and was wrong. M3 cites this as the reason
  existing prose findings must be re-verified against current reality before being trusted as fact,
  not simply copied forward.
- **Why Combat/Conflict is M4's second domain (corrected 2026-09-23)** — an earlier version of this
  appendix cited a stale rollup snapshot and framed Combat as an expected "clean" contrast to
  Territory's `CONFLICTING` result. An independent peer review checked this against live data and
  found it wrong on both counts: the rollup is regenerated from the registry and had already moved
  past the cited numbers, and Combat itself is not uniform — `tactical_decision` is
  `verified.verdict: contradicted`, `status_effects` is `orphan`, `skill_unlocks` is `partial`
  (all three checked directly in `registries/mechanisms.yaml`). Combat is kept as the second domain
  anyway, but for a different, more honest reason: it's a *mixed* domain — some mechanisms cleanly
  supported, at least one likely `CONFLICTING`/`PARTIAL` — which exercises more of the
  classification vocabulary in one slice than a uniformly "clean" domain would have. See M4's own
  text for the full correction.

### E. One project convention referenced without explanation

This repository requires opening a formal ticket (`tickets/inprogress/{ticket_id}.md`) before
starting most units of work, including M0. This roadmap does not open that ticket itself — it is
scoping the work, not starting it.
