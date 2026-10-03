---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW
artifact_type: investigation
tags: [architecture, schema, registry, combat]
---

# Investigation — TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW

## Current Behavior

### The mappable surface: 12 Rule IDs, independently re-derived

Ran the equivalent of `rule_catalog.py::scan_rule_ids()`'s heading regex
(`^## ([A-Z]{2,8}-[0-9]{2})\b`) plus a looser token scan against
`docs/world_rules/capability-progression/conflict-combat.md` and cross-checked every hit against
the real corpus:

```
grep -noE '[A-Z]{2,10}-[0-9]{2}' conflict-combat.md | sort | uniq -c
      4 AGENCY-01   3 AGENCY-02   1 AGENCY-04   4 BODY-07   1 CAP-01   5 CONFLICT-01
      5 CONFLICT-02 3 ECOL-04     3 KNOW-01     2 LIFE-01   1 LIFE-02  2 OWN-02  3 PERC-01
```

12 unique real Rule IDs (excluding `CONFLICT-02`, which is a historical/superseded citation only
— see below). **Confirmed: only `CONFLICT-01` is declared as an own-local `## CONFLICT-01 —
...` heading inside this file** (`conflict-combat.md:34`) — the scanner's regex only matches
`## <ID> —` headings, and every one of the other 11 appears in this file solely as prose citation
inside an "Inherited / Applied Foundational Rules" entry, never as its own `## <ID>` heading here.
Each of those 11 IS a real, heading-declared Rule ID elsewhere in the live corpus (confirmed by
direct grep of every batch file, one per ID):

| Rule ID | Declared at |
|---|---|
| `PERC-01` | `docs/world_rules/knowledge-agency/perception.md:31` |
| `KNOW-01` | `docs/world_rules/knowledge-agency/knowledge-information.md:34` |
| `AGENCY-01` | `docs/world_rules/knowledge-agency/agency-decision.md:32` |
| `AGENCY-02` | `docs/world_rules/knowledge-agency/agency-decision.md:62` |
| `AGENCY-04` | `docs/world_rules/knowledge-agency/agency-decision.md:169` |
| `LIFE-01` | `docs/world_rules/life-body/lifecycle.md:35` |
| `LIFE-02` | `docs/world_rules/life-body/lifecycle.md:59` |
| `BODY-07` | `docs/world_rules/life-body/body-condition.md:148` |
| `OWN-02` | `docs/world_rules/foundations/state-ownership.md:41` |
| `CAP-01` | `docs/world_rules/foundations/capability.md:30` |
| `ECOL-04` | `docs/world_rules/life-body/ecology-population.md:68` |

Because `scan_rule_ids()` resolves `rule_id` against a live scan of the **whole**
`docs/world_rules/**/*.md` corpus (`registry.py:279`, `known_rule_ids = scan_rule_ids(...)`), not
per-file, all 11 inherited-derived IDs are already valid, resolvable foreign keys for
`rule_mechanism_edges.yaml`/`rule_classifications.yaml` today — no schema gap. **The ticket's
claimed 12-ID count and exact ID list are confirmed correct**, and its framing ("only
`CONFLICT-01` is own-local; the other 11 are Inherited entries referenceable under the original
Rule ID they derive from") matches the file's real structure exactly.

**`CONFLICT-02` confirmed correctly non-live.** `grep -rn "^## CONFLICT-02\b" docs/world_rules
--include="*.md"` returns zero hits anywhere in the corpus. Its 5 occurrences in
`conflict-combat.md` are all inside historical framing ("originally drafted as CONFLICT-02",
"formerly CONFLICT-02") — never a live citation. A citation scanner using the same heading-anchored
regex as `scan_rule_ids()` (`^## ...`) will never trip on it, since none of the 5 occurrences is at
the start of a `##` heading line.

### Combat's 8 mechanisms — live state re-verified directly against `registries/mechanisms.yaml`

Parsed the YAML directly (`systems: [combat]` filter) rather than trusting any prose:

| Mechanism | `state` | `verified.instrument` | `verified.verdict` |
|---|---|---|---|
| `combat_resolution` | done | scenario | observed |
| `tactical_decision` | done | corpus_run | **contradicted** |
| `combat_engagement` | done | scenario | observed |
| `movement` | done | code_trace | observed |
| `action_pacing_readiness` | done | scenario | observed |
| `skill_unlocks` | **partial** | code_trace | observed |
| `trauma` | done | code_trace | observed |
| `status_effects` | **orphan** | code_trace | observed |

**All three of the ticket's live-check claims confirmed exactly as stated, independently
re-derived, not copied from the ticket or the triage log:**
- `tactical_decision`'s current `verified.verdict` is `contradicted` (`registries/mechanisms.yaml:189-225`)
  — unchanged since the 2026-09-19 root-cause note. `state` stays `done`.
- `status_effects`'s current `state` is `orphan` (`registries/mechanisms.yaml:1003`).
- `skill_unlocks`'s current `state` is `partial` (`registries/mechanisms.yaml:802`).

**`ENABLE_COMBAT_ENGAGEMENT` re-verified live**: `src/domains/optimization/feature_flags.py:32`
reads `"ENABLE_COMBAT_ENGAGEMENT": FeatureMode.ON` — matches the M3 triage log's correction exactly
(flipped 2026-09-14, PR #190, `1e075b807`).

**`TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` re-checked**: file still lives at
`tickets/todos/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md` (not `inprogress/`, not
`done/`) with body field `## Status` = `OPEN`. **Still paused, has not resumed.**

### Candidate mechanisms per Rule ID (evidence gathered, disposition NOT made — that is `plan.md`'s
job per the ticket's own AC1)

- **`CONFLICT-01`** — its own "Repository evidence" text (`conflict-combat.md:45-54`) cites
  `ResourceOpportunityProvider`'s reward scaling, an `AGENCY-01`-evidenced `blocker_penalty`, and
  `ECOL-04`'s regional-scarcity/migration feedback — **none of these are one of Combat's 8
  `systems: [combat]` mechanisms.** Grepping `registries/mechanisms.yaml` for
  `ResourceOpportunityProvider`/`blocker_penalty` returns zero hits (these are class/field names
  cited in doc prose, not registered `mechanism_id`s under those exact names). Plausible
  registered-mechanism candidates by subject matter: `resource_harvesting`
  (`registries/mechanisms.yaml:2489`, `systems: [economy]`, `state: orphan`) for the
  resource-contention half, and `regional_trauma` (`:1948`, `systems: [world]`) or a
  not-yet-identified Ecology mechanism for the `ECOL-04` half. **Flagging, not resolving**: this
  Rule's own real evidence points outside Combat's 8-mechanism set entirely, which the planner
  needs to know before assuming every one of the 12 IDs maps only to `systems: [combat]` rows.
- **Perception/knowledge inherited entry (`PERC-01`, `KNOW-01`, `AGENCY-01`, `AGENCY-02`)** — the
  file's own evidence (`:83-105`) cites `TacticalDecisionSystem.evaluate_entity_intent()`
  (`src/engine/tactical.py:181,199`, `tactical_decision`'s own `implemented_by`) and
  `EngagementRiskEvaluator`/`CombatPosture` (`combat_engagement`'s own domain). Strong `tactical_decision`
  candidate for all four IDs (perception-gated targeting, confirmed live); `combat_engagement` is a
  secondary candidate for the estimation/consideration half (`caution = 1.0 - bravery` in
  `EngagementRiskEvaluator`).
- **`AGENCY-04`, `CAP-01`** (capability doesn't guarantee outcome) — `conflict-combat.md:148-161`
  reuses `capability-progression.md`'s own identical entry verbatim; real candidate is whatever
  mechanism that file's own evidence already cites (out of this file's scope to re-derive — the
  ticket's own Out of Scope excludes the other two Batch 07 files). Within Combat's own 8,
  `combat_resolution` (`calculate_damage()` responding to `combat.atk`/`combat.def_stat`, per its
  own `verified.note`) is the concrete mechanism where "higher capability may still lose" is
  actually decided.
- **`LIFE-01`, `LIFE-02`** (combat outcome vocabulary) — direct, unambiguous candidate:
  `combat_resolution` (`src/engine/combat.py`'s real `outcome_kind` values:
  `KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`/`SURVIVE`/`REJECTED`), plus `movement`
  (`FLED`/`combat_escape="EVASIVE_SUCCESS"`, `src/engine/movement.py`) for the seventh
  withdrawal outcome the file's own evidence explicitly adds beyond Batch 05.
- **`BODY-07`, `OWN-02`** (Combat produces events; Life/Body owns consequence) — the file states
  this is a boundary claim, not a Combat-side implementation fact; `combat_resolution` is the
  producer-of-events side within Combat's own mechanisms, but the actual bodily-consequence owner
  is outside this file's Rule family entirely (Life/Body's own mechanisms) — a real candidate
  `CONSTRAINED_BY` edge on `combat_resolution`, not a `REALIZES` one.
- **`ECOL-04`** — see `CONFLICT-01` above; same non-Combat-mechanism candidate set.

### The shared-Rule-ID-across-domains question (Assumptions/Open Questions #2)

**Verified directly, both the validator logic and the real current registry state:**

1. `validate_rule_mechanism_edges()` (`tools/semantic_control_plane/registry.py:116-152`) keys its
   duplicate check on the **triple** `(rule_id, mechanism_id, edge_type)`
   (`registry.py:145-151`), never the pair `(rule_id, mechanism_id)`. Two edges sharing a
   `rule_id` but citing different `mechanism_id`s (e.g. `PERC-01` → `tactical_decision` from
   Combat, and some future `PERC-01` → a Perception-domain mechanism from Batch 06's own eventual
   mapping) are two distinct triples and both validate cleanly — **confirmed by direct code
   read, not by running a live test against real cross-domain data** (see next point for why no
   such data exists yet to test against for real).
2. **Correction to the ticket's own framing**: today, `grep -n "rule_id" registries/
   rule_mechanism_edges.yaml registries/rule_classifications.yaml` shows the **only** `rule_id`
   values present anywhere in either file are `TERR-01`, `TERR-02`, `TERR-03`, `TERR-05` (M1's own
   four rows). **None of `PERC-01`/`KNOW-01`/`AGENCY-01`/`AGENCY-02` (or any of the other 8 IDs)
   has an existing row today** — Batch 06's own Knowledge/Agency domain has never been run through
   this control plane. The ticket's Assumption #2 phrasing ("already mapped by Batch 06's own
   domain") is true only in the sense that Batch 06 is the Rule Catalog batch that *drafted* these
   IDs, not that the semantic-control-plane registries already carry rows for them. **When M4
   writes edges for `PERC-01`/`KNOW-01`/`AGENCY-01`/`AGENCY-02` citing `tactical_decision`/
   `combat_engagement`, those will be the FIRST rows either registry has ever carried for those
   Rule IDs** — the "two different domains' mechanisms mapped to one Rule ID" scenario the ticket
   describes as already-real is, on today's actual disk state, still prospective. This does not
   change AC1/AC2's substance (the validator genuinely does support it, per point 1 above, and no
   stop-and-report condition is triggered), but the planner should not describe it in `plan.md` as
   something that already exists on disk today.

### `generate_territory_control_view.py` — exact shape, for the extend-vs-new-file call

`tools/semantic_control_plane/generate_territory_control_view.py` (221 lines):
- Hardcodes `_TERR_RULE_IDS = ["TERR-01", "TERR-02", "TERR-03", "TERR-05"]` at module level
  (`:43`) — the Rule-ID list is not a parameter anywhere in `build_territory_view()` or `render()`;
  both close over the module constant directly.
- `build_territory_view(rule_mechanism_data, classifications_data, registry)` → returns a dict:
  `rows` (one dict per Rule ID with all six axis values), `mapped`/`unmapped` counts (based on
  whether the Rule has ≥1 edge), `verified`/`unverified` counts (based on whether any mapped
  mechanism has a runtime `verified.instrument`), and `classification_counts` (a dict over the six
  `VALID_RULE_CLASSIFICATIONS` values).
- `render(...)` → a Markdown string: banner, mapped/unmapped line, verified/unverified line,
  classification-breakdown line, then one Markdown table row per Rule ID across `_SIX_AXES`.
- `main()` → argparse CLI with `--output`/`--rule-mechanism-edges`/`--classifications`/`--check`;
  `--check` compares a fresh render against the committed file and exits 1 on mismatch (no build
  failure — this is Territory-only, no CI wiring yet, matching the ticket's Out of Scope).
- Wired via `make territory-control-view` (not read in this pass, but named consistently across
  the roadmap/M1 artifacts).

**What this means for the extend-vs-new-file decision** (left to `plan.md` per the ticket's own
Assumption #1 — reporting shape only, not deciding): extending in place would require turning
`_TERR_RULE_IDS` into a parameter (or a second constant plus a domain-keyed loop), and renaming the
module/output file/Make target away from "territory" specifically if the intent is a genuinely
domain-agnostic renderer going forward. The six-axis row-building logic itself
(`build_territory_view`'s body) has no Territory-specific logic in it beyond the hardcoded ID
list and the `_DESIGN_VALUE` constant (which cites `territory-control.md`'s own frontmatter) — so
the *shape* does generalize cleanly to a second domain; only the two Territory-specific constants
would need to become domain-keyed.

### `core_rpg_design_direction.md` §10 — run-on paragraph and the runtime-status terms actually needed

**Run-on paragraph located**: `docs/brainstorm/core_rpg_design_direction.md:478`. The pointer
sentence ("See `docs/plans/status_axis_model.md` for how this vocabulary relates to the Mechanism
Registry's `state`/`verified.verdict` axes and the semantic control plane's Rule realization
axis.") and `**Status note (2026-09-24).**` are literally concatenated on the same line/paragraph
with a single space between them and no blank line anywhere in between — confirmed by direct read,
matches the ticket's description exactly. The fix (owned by `world-rule-catalog-design`, per the
ticket's §5, but the location is confirmed here) is inserting a paragraph break (blank line)
between "...Rule realization axis." and "**Status note (2026-09-24).**".

**The 8 undefined §10 terms**: `MISSING`, `DESIGNED`, `EXPERIMENTAL`, `OFF`, `DORMANT`, `LIVE`,
`DEPRECATED`, `REPLACED` (line 472/478). Only `STARVED` and `REACH-LIMITED` (line 475-476) carry a
real one-line prose definition anywhere in the repo.

**Which terms the cross-domain view actually needs — evidence-based answer**: **none of the 8
undefined terms.** `generate_territory_control_view.py`'s six axes (`DESIGN`, `REALIZATION`,
`IMPLEMENTATION`, `VERIFICATION`, `INTEGRATION`, `OBSERVED OUTCOME`) render exclusively from Axis A
(`state`), Axis B (`verified.verdict`/`instrument`), and Axis D (`SUPPORTED`/`PARTIAL`/
`CONFLICTING`/`MISSING`/`INERT-OFF`/`UNKNOWN`) per `status_axis_model.md` §1's table — confirmed by
reading the generator's real source: zero §10/Axis-C terms appear anywhere in
`generate_territory_control_view.py`'s output-building code. Combat's own mixed real state
(`tactical_decision` `contradicted`, `status_effects` `orphan`, `skill_unlocks` `partial`) is fully
expressible using only Axes A/B/D — no new §10 term is structurally required by the generated
table. **The one place a §10 term might legitimately appear** is the ticket's own required written
comparison (§3 of Scope) if it characterizes `tactical_decision`'s situation in plain English:
`STARVED` is the one term that already has a real prose definition ("a live path whose conditions
almost never occur in real simulation") and matches `tactical_decision`'s own finding exactly —
`status_axis_model.md` §4 already calls `tactical_decision` "a textbook STARVED case." No other of
the 8 undefined terms is needed by anything this ticket's own deliverables touch. This is a report
only — no definition, pruning, or edit of the vocabulary is made here or proposed for this ticket.

## Mechanics / Engine Constraints

- `docs/plans/simulation_semantic_control_plane/architecture.md` §3 — the three-edge-type vocabulary
  (`REALIZES`/`PARTIALLY_REALIZES`/`CONSTRAINED_BY`) and the "never generate the Cartesian product"
  rule directly constrain how many/which of the 12 IDs may receive a row at all — `UNKNOWN` remains
  a fully legitimate, permanent disposition for any ID where no real relationship is found.
- `architecture.md` §4 — Rule-level realization classification is a separate, human-judgment record,
  never mechanically derived from the edge list; `tools/semantic_control_plane/registry.py`'s own
  `validate_rule_classifications()` docstring and `test_no_function_derives_classification_from_edges`
  enforce this by construction.
- `architecture.md` §7 — `UNKNOWN` is permanent; a management view must show raw mapped/unmapped and
  verified/unverified counts alongside any classification breakdown, never a percentage alone.
- `docs/plans/status_axis_model.md` §1-§4 — governs every status word this ticket may use: Axis A
  (`state`), Axis B (`verified.verdict`), Axis D (Rule classification) are all enforced and load-
  bearing; Axis C (§10 compass vocabulary) is explicitly the least authoritative and is not to be
  force-mapped onto Axis A/B values (`orphan` × `DORMANT` is explicitly "no defined relationship" —
  §2's own table forbids inferring `status_effects` is `DORMANT` just because it's `orphan`).

## Docs Requiring Update

- `docs/plans/simulation_semantic_control_plane/architecture.md`: §3 must document the
  inherited-entry citation rule (an Inherited/Applied Foundational entry is cited under the
  original Rule ID it derives from, e.g. `PERC-01`, not a new local ID) — required by the ticket's
  own Scope item 4; confirmed this sentence does not exist anywhere in the file today (checked by
  reading all of §3).
- `docs/plans/simulation_semantic_control_plane/roadmap.md`: the M4 section (and the epic's
  milestone table, tracked in the parent epic ticket, not this file) must record M4's disposition
  and state that the roadmap is complete while the mapping itself continues under Stages D/E/F —
  required by AC9. Today's M4 section still reads as an open/in-progress milestone description.
- `registries/rule_mechanism_edges.yaml`, `registries/rule_classifications.yaml`: not docs in the
  `docs/` sense but are the load-bearing data files this ticket's core deliverable writes to;
  called out here for completeness since `done-checker`'s doc-coverage regex only scans `docs/`
  paths — these are covered by the registry validator (AC2) and the test suite instead, not by the
  docs-coverage mechanism.

The `docs/brainstorm/core_rpg_design_direction.md` (path: `docs/brainstorm/core_rpg_design_direction.md`,
under `docs/`) run-on-paragraph fix is explicitly **not** this ticket's own edit per its Related
Docs framing ("`world-rule-catalog-design` asked that a parallel one-sentence addition ... ride on
`TCK-20260923-TERR01-STALE-JURISDICTION-CITATION`") — wait, that citation-rule sentence is
`architecture.md`'s job (listed above); the §10 run-on fix itself is Scope item 5's own literal
instruction ("Fix the `core_rpg_design_direction.md` §10 run-on paragraph") and IS this ticket's own
work, not deferred — see the Format 1 bullet below.

- `docs/brainstorm/core_rpg_design_direction.md`: fix the §10 run-on paragraph at line 478 (insert
  a blank line between "...Rule realization axis." and "**Status note (2026-09-24).**") — required
  directly by the ticket's own Scope item 5, first bullet. This is a formatting-only fix; content is
  unchanged, and the vocabulary itself is explicitly not edited (Out of Scope).

The `docs/world_rules/capability-progression/conflict-combat.md` file (under `docs/`) is not
required to change for this ticket: it is explicitly read-only per the ticket's Out of Scope
("Editing `docs/world_rules/` — the frozen Catalog is not changed by this track") and per Related
Docs' own "read-only" annotation.

## Parity Ledger Overlap

None of `docs/parity_ledger/*.yaml`'s entries are touched by this ticket — the Rule↔Mechanism
mapping and Rule classification schemas are a deliberately separate, sibling structure to the
parity ledger (different subsystem: parity ledger tracks doc/code semantic parity per subsystem
YAML file; this control plane tracks Rule-Catalog-to-Mechanism-Registry cross-references). Checked
`docs/parity_ledger/combat_movement.yaml` directly for any entry referencing `CONFLICT-01` or the
other 11 Rule IDs by name — no hits. No parity ledger entry requires updating as part of this
ticket.

## Prior Work

- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/` — the direct precedent this
  ticket extends: same registries, same validator, same six-axis view shape, same
  mapped/unmapped-alongside-classification discipline. Its `investigation.md`/`test_plan.md` follow
  the same frontmatter/section shape used here.
- `stored_artifacts/TCK-20260924-M2-MAPPING-DRIFT-DETECTION/` — the drift detector this ticket's
  new Combat rows will be checked against (AC5: `make semantic-control-plane-drift-check` must
  report clean after the new rows).
- `docs/plans/simulation_semantic_control_plane/finding_triage_log.md`'s own
  `TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE` section — consumed directly, not
  re-investigated, per the ticket's own instruction. Its three `PROMOTE-AT-M4` findings
  (perception-gated targeting, `ENABLE_COMBAT_ENGAGEMENT`'s corrected live state, the missing
  surrender/capture/displacement outcome) are the evidentiary basis for several of the 12 Rule
  IDs' eventual edges/classifications.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (closed) — the settled fact behind
  `tactical_decision`'s `contradicted` verdict; its own closing line explicitly leaves "whether this
  should change" as an unresolved design question, which this ticket must not resolve.

## Risks and Open Questions

1. **CONFLICT-01's own real evidence points outside Combat's 8 registered mechanisms** (see
   Current Behavior above — `ResourceOpportunityProvider`/`blocker_penalty`/`ECOL-04` feedback have
   no obvious 1:1 registered `mechanism_id` under those exact names). The planner should decide in
   `plan.md` whether `CONFLICT-01` maps to `resource_harvesting`/`regional_trauma`-adjacent
   mechanisms (crossing outside `systems: [combat]`), stays `UNKNOWN` for lack of a resolvable
   mechanism_id, or needs a short additional grep pass to identify the real registered id before
   plan.md is finalized. Not resolved here — this is a genuine open question, not an assumed
   answer.
2. **The "shared Rule ID across two domains" scenario is prospective, not already-real on disk**
   (see Current Behavior above) — the validator supports it by construction (triple-keyed
   duplicate check), but there is no existing cross-domain row to test it against today. M4's own
   Combat rows for `PERC-01`/`KNOW-01`/`AGENCY-01`/`AGENCY-02` will be the first real test of this
   path. No stop-and-report condition was found (the validator logic genuinely supports it), but
   `plan.md` should not claim this is already-observed cross-domain data.
3. **`BODY-07`/`OWN-02`'s real mechanism-side candidate is outside this Rule family's own scope**
   (Life/Body's own mechanisms own the bodily-consequence side) — `combat_resolution` is a
   plausible `CONSTRAINED_BY` or event-producer-side citation, but the planner should confirm this
   against whatever Life/Body's own domain would eventually cite, to avoid asserting a `REALIZES`
   edge that actually belongs to a mechanism outside Combat's own set.
4. Whether the `architecture.md` §3 citation-rule addition (Scope item 4) should also touch the
   Catalog's own admission-discipline section is explicitly **not** this ticket's job — confirmed
   already correctly scoped out in the ticket text (rides on
   `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION` instead). No action needed here beyond noting
   it stays correctly excluded.

## Anti-Drift Hazards

- **Do not read `CONFLICT-01`'s single heading as the domain's whole surface.** The ticket itself
  names this exact failure mode (`TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`
  precedent) — all 12 IDs must get an explicit disposition, `UNKNOWN` included, in `plan.md`.
- **Do not silently force `status_effects` (`orphan`) into `DORMANT` or `skill_unlocks` (`partial`)
  into any §10 term.** `status_axis_model.md` §2 explicitly marks `orphan × DORMANT` as "no defined
  relationship" — inferring one would misuse an unenforced, half-undefined vocabulary axis to
  describe a well-defined one.
- **Do not classify `combat_engagement`'s stale doc premise as `CONFLICTING`.** The M3 triage log's
  own disposition reasoning (`finding_triage_log.md` "Disposition reasoning" block) already settled
  this: `CONFLICTING` is a code-vs-Rule semantic-violation judgment, and what was wrong here is
  doc-vs-reality staleness, not a demonstrated Rule violation. Carry this distinction into any
  `combat_engagement`-related classification M4 writes.
- **Do not resolve `tactical_decision`'s `contradicted` verdict or resume the paused hostility
  sweep.** Both are explicitly Out of Scope; record their current state (done above) and stop.
- **Do not let the cross-domain view's Territory rows change.** `_TERR_RULE_IDS`'s existing four
  rows and their six-axis values must render identically to `stored_artifacts/
  TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE`'s own committed output — any implementation
  approach (extend vs. new generator) must reproduce Territory's existing output byte-for-byte
  before adding Combat.
- **Do not edit `docs/world_rules/capability-progression/conflict-combat.md`.** Frozen, read-only,
  confirmed by direct Out-of-Scope line and Related Docs' "read-only" annotation.
- **Do not define, prune, or edit any of the 8 undefined §10 terms** — Scope item 5's own explicit
  instruction is report-only; that decision belongs to `world-rule-catalog-design`.
