---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-STATUS-VOCABULARY-RECONCILIATION
artifact_type: plan
tags: [architecture, schema, taxonomy, registry, documentation]
---

# Implementation Plan — TCK-20260923-STATUS-VOCABULARY-RECONCILIATION

## Summary

This is a documentation/vocabulary-contract ticket, not a code-behavior change. It creates one new
doc, `docs/plans/status_axis_model.md`, that states the four-axis model, the cross-axis binding
table, both homograph decisions, and the STARVED/REACH-LIMITED registry-representation decision —
then adds a one-line pointer to that doc at each of the four existing vocabulary homes named by
AC 5, plus one optional fifth pointer the investigation recommends but AC 5 does not require. It
closes with two verification steps: an automated cross-reference proof (permanent test, since AC 5
should stay true forever) and a one-time `git diff` check that no mechanism row's `state`/`verdict`
changed (not a permanent test, since future tickets legitimately change those values often and a
hardcoded 93-row snapshot would become a maintenance tax unrelated to this ticket's own scope). No
`src/` code changes. No M0 schema changes beyond an optional docstring line.

**Corrections made during planning, verified by direct read, that supersede investigation.md's own
citations:** investigation.md cited `docs/world_rules/roadmap.md` lines 171–177 as the source of
the `INERT-OFF` definition quote ("`knowledge_model` has no decision consumer, INERT/OFF;
`PerceptionUpdatePhase` has zero production call sites, INERT/OFF") and as the source of `MISSING`'s
"investigated, evidenced absence" definition. Neither string exists at those lines in
`roadmap.md` (confirmed: `grep -n "decision consumer\|production call sites" docs/world_rules/
roadmap.md` returns zero hits at 171-177; that range is actually about History/Provenance drafting,
unrelated content). The real sources, confirmed by direct read:
- The `INERT-OFF` quote is at `docs/world_rules/README.md:172` (and restated at
  `docs/world_rules/review-exports/knowledge-agency-batch-06-review.md:264,290,292`).
- The `MISSING`/`UNKNOWN` distinction ("`MISSING` is an investigated, evidenced absence; `UNKNOWN`
  is simply 'not yet looked at.'") is at `docs/plans/simulation_semantic_control_plane/
  architecture.md:189-190` — inside the very file this ticket is already cross-referencing, which is
  a better citation than `roadmap.md` would have been anyway.
- `roadmap.md:581` ("object provenance is **PARTIAL/INERT-OFF**, not MISSING") is correctly cited
  and confirmed real.
Step 1 below directs the implementer to cite the corrected locations, not investigation.md's
original line numbers.

## Steps

### Step 1 — Author the axis-model doc
**Files:** `docs/plans/status_axis_model.md` (new file)
**Change:** Create the doc with frontmatter matching the sibling-doc pattern confirmed at
`docs/plans/mechanism_registry_initiative.md:1-6` and `docs/plans/simulation_semantic_control_plane/
architecture.md:1-6` (`status: active`, `layer: architecture`, `authority: P1`, `audience: agent`,
`tags: [architecture, documentation, schema]`). Body must contain, in this order:

1. **Axis table** — exactly four rows, one per axis, each stating: the question it answers, its
   canonical vocabulary, its home file, and its enforcement/data status. Source every claim from
   investigation.md's Current Behavior section (already file:line verified there) rather than
   re-deriving:
   - Axis A (implementation completeness): `state` — `done|partial|gap|orphan|gated|skeleton` —
     `registries/mechanisms.yaml:71`, enforced by `VALID_STATES`
     (`tools/mechanism_registry/registry.py:139`) — **enforced, 93 real rows**.
   - Axis B (evidentiary verification): `verified.verdict` — `observed|contradicted|inconclusive`
     paired with `instrument` — same file, `VALID_VERDICTS` (`registry.py:149`) — **enforced**, no
     independent rollup view (only per-row + `mechanism_verification_view.md`).
   - Axis C (runtime reach/liveness): compass §10 —
     `MISSING|DESIGNED|EXPERIMENTAL|OFF|DORMANT|STARVED|REACH-LIMITED|LIVE|DEPRECATED|REPLACED` —
     `docs/brainstorm/core_rpg_design_direction.md:472` — **aspirational prose, unenforced, 0
     mechanism rows carry a §10 value** (confirmed by investigation's grep sweep); only `STARVED`
     (line 475) and `REACH-LIMITED` (line 476) have a real one-line definition — the other eight are
     undefined anywhere in the repo.
   - Axis D (Rule-semantic realization): control-plane Rule realization —
     `SUPPORTED|PARTIAL|CONFLICTING|MISSING|INERT-OFF|UNKNOWN` —
     `docs/plans/simulation_semantic_control_plane/architecture.md:125`, enforced by
     `VALID_RULE_CLASSIFICATIONS` (`tools/semantic_control_plane/registry.py:58-60`) — **enforced,
     0 populated rows today** (M1's job, not this ticket's).
   State explicitly, per the ticket's own "Not assumed" clause: Axes A and B are the load-bearing
   reference (93 real rows); Axis D is enforced but empty; Axis C is the least authoritative —
   aspirational prose with no enforcement and no data. Do not present all four as co-equal.

2. **Binding table** — one row per cross-axis pair with a real or claimed relationship, each
   labelled `equivalence` / `implication` / `correlation` / `no defined relationship`, with a one-
   line rationale citing evidence. Required rows (do not omit any; AC 2 requires undefined pairs be
   listed, not silently dropped):
   - `MISSING` (C) × `MISSING` (D) → **correlation, not equivalence**. Different granularity
     (mechanism vs. Rule) and different evidentiary bar (C's is undefined/no bar stated; D's carries
     an explicit "investigated" requirement per `architecture.md:189-190`, corrected citation above).
   - `OFF` (C) × `INERT-OFF` (D) → **equivalence in intent, non-identical evidentiary rigor**.
     `INERT-OFF` carries a real, repeatedly-applied definition (`docs/world_rules/README.md:172`;
     `roadmap.md:581`: "code exists, wired in some sense, zero real production effect, often
     feature-gated"); `OFF` is undefined in prose beyond its list position but reads the same way in
     plain English. When both apply to the same mechanism/Rule pair, prefer citing `INERT-OFF`'s
     evidence. Do not rename either value (see Scope Guards / AC 8).
   - `partial` (A) × `PARTIAL` (D) → **correlation, not equivalence**, same reasoning pattern as the
     `MISSING` pair above: mechanism-level completeness judgment vs. Rule-level semantic judgment: a
     Rule mapped to `partial`-state mechanisms is more likely itself `PARTIAL`, but the converse does
     not hold and axis A's `partial` is never a mechanical determinant of axis D's `PARTIAL`
     (`architecture.md:119-136` already makes exactly this argument for the shape generally — reuse
     it, do not re-derive).
   - `gated` (A) × `OFF` (C) → **correlation**. `gated` means "code exists, reachable, but sits
     behind a currently-default-off condition" — confirmed by two real registry rows:
     `registries/mechanisms.yaml:747` (`temporal_pressure`, gated behind `ENABLE_MEMORY_UPDATE`
     default OFF) and `:754-758` (a reproduction-path mechanism, "gated behind
     `ENABLE_REPRODUCTION_HUMANOID_PATH` (default OFF, feature_flags.py), which is what `gated`
     means"). This is evidence-suggestive of `OFF` on the runtime axis but not an implication: `gated`
     states a structural fact (a gate exists) without stating whether that gate is open in the
     profile being asked about, so a `gated` mechanism could be `LIVE` in a profile where its flag is
     on.
   - `orphan` (A) × `DORMANT` (C) → **no defined relationship**. `DORMANT` has zero prose definition
     anywhere in `core_rpg_design_direction.md` (confirmed by investigation's grep sweep — 8 of 10
     §10 values are undefined). Do not force a mapping to `orphan` on inference alone; record as
     undefined until `DORMANT` gets a real one-line definition, matching the treatment already given
     to `skeleton` below.
   - `skeleton` (A) × [no §10 counterpart] → **no defined relationship**. Confirmed: `skeleton` is
     never mentioned in `core_rpg_design_direction.md` (grep, zero hits); it is a purely
     registry-internal implementation-completeness notion (scaffold before `gap`/`partial`/`done`).
   - `STARVED`/`REACH-LIMITED` (C) × `verified.verdict: contradicted` + `instrument` a runtime value
     (B) → **correlation**. A STARVED/REACH-LIMITED case is one plausible cause of a `contradicted`
     runtime verdict, but `contradicted` alone does not distinguish "conditions almost never occur"
     from "the logic is outright broken" — this is exactly why Step 1 item 4 below records a
     prose-note convention rather than adding a field.

3. **Homograph decisions** (AC 3) — restate the two resolutions above as explicit, separately
   labelled decisions with rationale (`MISSING`×2: keep both words, correlation only;
   `OFF`/`INERT-OFF`: keep both words, equivalence-in-intent, do not rename, citing AC 8's
   out-of-scope-unless-charged-to-M1 constraint as the reason renaming was rejected).

4. **STARVED/REACH-LIMITED registry-representation decision** (AC 4) — record: **no new registry
   field is added.** Reproduce (summarized, citing investigation.md's Risks and Open Questions
   section as the source of the completed 12-question walkthrough — do not re-run the admission test
   from scratch) the §11 admission-test application against a hypothetical `reach` field, concluding
   it fails admission on Q4 (no current consumer) and Q12 (duplicates `verified.note`, which already
   carries the full story — see `registries/mechanisms.yaml:186-225`'s `tactical_decision` row).
   Record the lighter-weight alternative as the actual decision: a **documented convention** that
   when `verified.verdict: contradicted` is paired with a runtime `instrument`, the `note` field
   should name which of STARVED / REACH-LIMITED / genuinely-broken applies, in prose. State
   explicitly: **this is a convention, not a new YAML key — AC 6's "if a registry field is added,
   validate() enforces it" is therefore not triggered.** (This resolves the open risk investigation.md
   flagged as needing a planner decision rather than assuming it either way.)

5. **§10 enforcement-status statement** — state plainly: confirmed unenforced, 0 mechanism rows
   carry a §10 value, only 2 of 10 values defined in prose, positioned as the least authoritative of
   the four axes per item 1 above.

**Do NOT touch:** any mechanism row's `state` or `verified` block (evidence only, cited not edited);
`docs/parity_ledger/*.yaml` (zero overlap, confirmed no reference to any of the four vocabularies);
`docs/guidelines/tag_taxonomy.md` (cited as structural precedent only).
**Verify:** manual read-through against AC 1–4 text; `test_status_axis_model_doc_exists` in Step 7's
new test file (file exists, is non-empty, contains the four-axis table and both homograph decisions
by keyword check).

### Step 2 — Cross-reference in `registries/mechanisms.yaml` header
**Files:** `registries/mechanisms.yaml`
**Change:** Insert one new comment line after line 99 (blank `#` line following "...instrument
finding the claimed behavior doesn't actually happen.") and before line 100
(`# Validate with: make mechanism-registry-validate...`), reading approximately:
`# For how this file's state/verified axes relate to the compass's §10 runtime-status vocabulary`
`# and the control plane's Rule realization vocabulary, see docs/plans/status_axis_model.md.`
This mirrors the existing precedent at line 22 (`# See docs/plans/mechanism_registry_initiative.md
for the full design rationale...`), so the style is already established in this exact file.
**Other writers to this file:** none. `registries/mechanisms.yaml` is explicitly "the single
hand-authored source" (its own header, line 1) — confirmed by `grep -rl mechanisms.yaml tools/
Makefile`: every hit (`generate_mechanism_*.py`, `mechanism_atlas_regenerate.py`,
`mechanism_capabilities_regenerate.py`, `mechanism_*_check.py`, `registry.py`,
`system_registry.py`) reads this file to produce a *different* output (charts, views, HTML,
validation errors) — none of them opens `mechanisms.yaml` for writing. `tickets/inprogress/`
currently contains only this ticket and `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md` (epic-tier,
tracks children only, does not itself edit files) — no concurrent ticket is editing this file's
header right now.
**Do NOT touch:** any line below `layers:` (line 109 onward — the actual mechanism rows); the
`# THREE AXES` containment/execution-order/functional-dependency block (lines 32-40, an unrelated
axis system about `depends_on`, not to be confused with this ticket's status axes).
**Verify:** `pytest tests/unit/tools/test_mechanism_registry.py::test_real_registry_passes_validation
tests/unit/tools/test_mechanism_registry.py::test_real_registry_has_no_duplicate_keys -q` (a comment
edit must not break `yaml.safe_load()` parsing or trip `check_duplicate_keys()`).

### Step 3 — Cross-reference in `tools/mechanism_registry/registry.py` docstring
**Files:** `tools/mechanism_registry/registry.py`
**Change:** Insert one new paragraph in the module docstring after line 48
("...`validate()`'s own body -- see its own docstring for why.") and before line 49/50 (`Usage:`),
reading approximately: "See `docs/plans/status_axis_model.md` for how this module's `VALID_STATES`/
`VALID_VERDICTS` axes relate to the compass's §10 runtime-status vocabulary and the semantic
control plane's Rule realization vocabulary — the same shape, three deliberately separate axes,
never conflated." This is the AC 5 "registry validator's own docstring" home, verified by direct
read of the docstring boundaries (module docstring closes at line 53).
**Other writers to this file:** none identified — this is a hand-maintained source file, not
generated. No other in-flight ticket touches it (same `tickets/inprogress/` check as Step 2).
**Do NOT touch:** `VALID_STATES` (line 139), `VALID_VERDICTS` (line 149), `_REQUIRED_VERIFIED_FIELDS`
(line 150), `STATIC_INSTRUMENTS`/`RUNTIME_INSTRUMENTS`/`VALID_INSTRUMENTS`, or any function body —
docstring-only edit.
**Verify:** `pytest tests/unit/tools/test_mechanism_registry.py -q` (full file, confirms the
docstring edit didn't break import or any existing assertion against docstring content).

### Step 4 — Cross-reference + aspirational-status note in `core_rpg_design_direction.md` §10
**Files:** `docs/brainstorm/core_rpg_design_direction.md`
**Change:** Insert new text after line 476 (the REACH-LIMITED bullet) and before line 478 (the
blank line preceding "and, at the system level..."), stating two things: (a) a cross-reference —
"See `docs/plans/status_axis_model.md` for how this vocabulary relates to the Mechanism Registry's
`state`/`verified.verdict` axes and the semantic control plane's Rule realization axis." (b) the
unenforced-status note — "This vocabulary is aspirational prose, not an enforced enum: no validator
checks it and no mechanism row currently carries a §10 value (only `STARVED` and `REACH-LIMITED`
above have a real one-line definition; the other eight values are undefined here or anywhere else
in the repo)." Both additions are prose only; the `MISSING · DESIGNED · ... · REPLACED` code block
(line 472) itself is unchanged — no value added, removed, or renamed.
**Other writers to this file:** hand-authored brainstorm doc; no generator writes to it. Check
`tickets/inprogress/` (same as Step 2) — no concurrent ticket is editing §10 right now.
**Do NOT touch:** §11 (lines 486-507, the admission test itself — Step 1 cites it, does not modify
it); the code block at line 472 (the ten-value list itself must stay exactly as-is — no renaming,
no reordering, no addition/removal of values, since that would be inventing new ontology ahead of
data, which `rollout_plan.md` Stage A and this ticket's Out of Scope both forbid).
**Verify:** manual diff review (doc-only file, no automated parser); Step 7's new test asserts the
literal string `status_axis_model.md` appears somewhere in this file.

### Step 5 — Cross-reference in `architecture.md` §3/§4
**Files:** `docs/plans/simulation_semantic_control_plane/architecture.md`
**Change:** Insert one new paragraph after line 143 (end of §4, "...not because a three-value enum
is aesthetically cleaner.") and before line 145 (`## 5. Delivery truth reuses two existing
mechanisms...`), reading approximately: "See `docs/plans/status_axis_model.md` for the full
cross-axis binding table between this Rule realization vocabulary, the Mechanism Registry's `state`/
`verified.verdict` axes, and the compass's §10 runtime-status vocabulary — including the `MISSING`
and `OFF`/`INERT-OFF` homograph decisions this section's own values are party to." This satisfies AC
5's literal "architecture.md §3/§4" requirement by placing the pointer at the boundary of both
sections it names.
**Other writers to this file:** hand-authored plan doc, part of the active M0/M1 initiative but no
M1 ticket exists yet in `tickets/inprogress/` or `tickets/todos/` (confirmed by directory listing —
only `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md` and this ticket are in-flight) — no concurrent
writer to this file today.
**Do NOT touch:** `VALID_RULE_CLASSIFICATIONS`'s six-value list at line 125 (the code block itself);
§7 ("Unknown is permanent," lines 178-196, cited as evidence not edited); §9's non-goals (lines
221-243).
**Verify:** manual diff review; Step 7's new test asserts the literal string `status_axis_model.md`
appears in this file.

### Step 6 — (Optional, not required by any AC) Cross-reference in `tools/semantic_control_plane/registry.py` docstring
**Files:** `tools/semantic_control_plane/registry.py`
**Change:** Insert one line in the module docstring (after the existing "Mirrors
`tools/mechanism_registry/registry.py`'s own `validate(data)`..." paragraph, before `Usage:`, lines
9-20 area) pointing to `docs/plans/status_axis_model.md`, mirroring Step 3's style. This is
investigation.md's recommendation as a nice-to-have completeness pointer alongside
`VALID_RULE_CLASSIFICATIONS` (line 58-60) — AC 5 names only "the registry validator's own
docstring" (singular, satisfied by Step 3) and "architecture.md §3/§4" (satisfied by Step 5), so
this step is optional polish, not an AC-mapped requirement. Skip it if time-constrained; it does not
block any acceptance criterion.
**Other writers to this file:** none — hand-maintained, no concurrent ticket in flight (M0's own
ticket already landed and closed; M1 does not exist yet).
**Do NOT touch:** `VALID_RULE_CLASSIFICATIONS` (line 58-60), `VALID_RULE_MECHANISM_EDGE_TYPES`
(line 55-57), any `validate_*()` function body — docstring-only, and this is the file AC 8 most
directly protects, so treat any change here as maximally sensitive.
**Verify:** `pytest tests/unit/tools/test_semantic_control_plane_schema.py -q` (full file, confirms
`VALID_RULE_CLASSIFICATIONS` unchanged and no import/collection error from the docstring edit).

### Step 7 — Automated cross-reference proof (AC 5)
**Files:** `tests/unit/tools/test_status_axis_model_cross_references.py` (new file)
**Change:** Write a small, permanent pytest module (this guard should stay true forever, unlike the
one-time AC 7 check in Step 8) that:
- asserts `docs/plans/status_axis_model.md` exists and is non-empty;
- asserts the literal substring `status_axis_model.md` appears in each of the four AC-5-required
  homes: `registries/mechanisms.yaml`, `docs/brainstorm/core_rpg_design_direction.md`,
  `docs/plans/simulation_semantic_control_plane/architecture.md`, and
  `tools/mechanism_registry/registry.py`.
Read each target file with plain `open(path).read()` and `in` — no YAML/AST parsing needed, these
are all plain-text or docstring searches. Use `REPO_ROOT = Path(__file__).resolve().parents[3]` as
already established at `tests/unit/tools/test_mechanism_registry.py:29`, for path consistency with
the existing suite.
**Do NOT touch:** any other test file; do not fold this into `test_mechanism_registry.py` even
though that file already has the `registry_data` fixture pattern — this check spans files outside
the mechanism registry's own domain (it also reads `core_rpg_design_direction.md` and
`architecture.md`), so a dedicated small module keeps the mechanism-registry suite's own scope
clean, matching the test_plan's own suggested naming.
**Verify:** `pytest tests/unit/tools/test_status_axis_model_cross_references.py -q` — must fail if
run before Steps 1-5 are complete (sanity-check this by running it once mid-implementation, after
Step 1 but before Step 2, to confirm it actually catches a missing cross-reference rather than
trivially passing).

### Step 8 — AC 7 regression proof: zero mechanism row reclassification
**Files:** none changed; verification-only step.
**Change:** None. This step runs `git diff registries/mechanisms.yaml` (against the commit this
ticket started from) and confirms every changed line falls within the header comment block (lines
1-108) or the two Step-2-inserted lines specifically — i.e., zero changed lines below `layers:`
(line 109) that would represent a mechanism row. Practically: `git diff registries/mechanisms.yaml
| grep -E '^\+|^-' | grep -v '^\+\+\+\|^---'` and manually confirm every hunk is inside the header
range. This is a **one-time check, not a permanent pytest test** — the test_plan.md explicitly left
this as the planner's call, and a hardcoded 93-row snapshot test would break on every legitimate
future ticket that corrects a mechanism's `state` or `verdict` (this happens routinely — see the
several `TCK-2026091*`/`TCK-2026092*` state-correction precedents cited throughout
`mechanisms.yaml`'s own rows), which is a maintenance cost unrelated to this ticket's own scope and
would falsely implicate future unrelated tickets in an "AC 7 violation" they don't actually commit.
**Other writers to this file:** same as Step 2 — none, hand-authored only.
**Do NOT touch:** nothing to touch; this step is read-only verification.
**Verify:** the `git diff` command above, run once at the end of implementation, output pasted into
the ticket's Completion Summary as evidence.

### Step 9 — Final scoped test run + AC 8 confirmation
**Files:** none changed; verification-only step.
**Change:** None. Run the full scoped pytest command set from `test_plan.md`:
```
python3 -m pytest tests/unit/tools/test_mechanism_registry.py -q
python3 -m pytest tests/unit/tools/test_semantic_control_plane_schema.py -q
python3 -m pytest tests/unit/tools/test_status_axis_model_cross_references.py -q
```
Then confirm AC 8: `git diff --stat registries/rule_classifications.yaml
registries/rule_mechanism_edges.yaml registries/mechanism_causal_edges.yaml` must show no output
(these M0 data files are untouched by this ticket); `git diff tools/semantic_control_plane/
registry.py` must show either no output (if Step 6 was skipped) or a docstring-only diff with
`VALID_RULE_CLASSIFICATIONS`/`VALID_RULE_MECHANISM_EDGE_TYPES` unchanged (if Step 6 was done) — the
existing `test_semantic_control_plane_schema.py` suite passing unchanged is itself evidence of this,
since it directly asserts those frozensets' exact value sets.
**Verify:** all three pytest commands green; both `git diff` checks confirm no M0 schema/data
change.

## Scope Guards

- Never change any mechanism row's `state` or `verified.verdict` value in `registries/mechanisms.yaml`
  (AC 7). Header-comment lines only.
- Never touch `registries/rule_classifications.yaml`, `registries/rule_mechanism_edges.yaml`, or
  `registries/mechanism_causal_edges.yaml` — M0's own (currently empty) data files; populating them
  is M1's job, explicitly out of scope.
- Never modify `VALID_RULE_CLASSIFICATIONS` or `VALID_RULE_MECHANISM_EDGE_TYPES` in
  `tools/semantic_control_plane/registry.py` (AC 8) — docstring-only edit if Step 6 is done at all.
- Never modify `VALID_STATES`, `VALID_VERDICTS`, `VALID_INSTRUMENTS`, or
  `_REQUIRED_VERIFIED_FIELDS` in `tools/mechanism_registry/registry.py`.
- Never rename `MISSING` (either axis) or `OFF`/`INERT-OFF` (either axis) — both homograph decisions
  are "keep both words," not "rename to disambiguate."
- Never add a new YAML key/field to any mechanism row — the STARVED/REACH-LIMITED decision is a
  prose-note convention, not a schema field; if a future implementer is tempted to add a `reach`
  field anyway, that is a scope violation of this plan's own Step 1 item 4 decision.
- Never touch `docs/parity_ledger/*.yaml` — zero overlap, confirmed by investigation's grep across
  all eight subsystem files.
- Never touch `docs/guidelines/tag_taxonomy.md` — cited as structural precedent only.
- Never resolve or touch the `tactical_decision` mechanism's own row content, or the open design
  question of whether the strategic dispatch gate should derive `DEFEAT_ENEMY` — cited as evidence
  only throughout Step 1.
- Never merge the four vocabularies into one enum — the ticket's Out of Scope and this plan's own
  Step 1 item 1 both treat this as the wrong answer, not a fallback if reconciliation feels
  laborious.
- No CI wiring of any kind — report-only per Out of Scope.
- Do not widen the ten-value §10 list itself (line 472 of `core_rpg_design_direction.md`) — no
  value added, removed, or renamed, even though eight of them are undefined prose today; defining
  them is a separate, future ticket, not this one's job.

## Dependency Map

- Step 1 (author the doc) must complete before Steps 2, 3, 4, 5, 6 (all cross-reference edits point
  at a doc that must exist first) and before Step 7 (the cross-reference test needs real content to
  check against, and needs a real path to assert).
- Steps 2, 3, 4, 5, 6 are mutually independent — different files, no shared editing order required.
  Steps 2 and 3 both touch the Mechanism Registry's "home" (data file vs. code docstring) but are
  physically separate files with no conflict.
- Step 7 depends on Steps 1-5 being complete (it asserts all four required cross-references exist);
  Step 6 is optional and not asserted by Step 7 (AC 5 does not require it).
- Step 8 depends on all edits (Steps 1-6) being complete — it is the final diff check across the
  whole change set.
- Step 9 depends on Steps 7 and 8 both passing — it is the final full-suite run and AC 8 close-out.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| 1. Axis model document (how many axes, question each answers, canonical vocabulary) | Step 1 (item 1) | Manual read-through; Step 7 doc-exists assertion |
| 2. Binding table covering every cross-axis pair, undefined pairs explicitly listed | Step 1 (item 2) | Manual read-through against the 7 required rows listed in Step 1 |
| 3. Both homograph collisions have a recorded decision + rationale | Step 1 (items 2, 3) | Manual read-through |
| 4. STARVED/REACH-LIMITED registry-representation decision, §11 test applied if a field is added | Step 1 (item 4) | Manual read-through; no field added, so no validator test is required |
| 5. All four homes cross-reference the axis model | Steps 2, 3, 4, 5 | Step 7 — `test_status_axis_model_cross_references.py` |
| 6. If a field is added, `validate()` enforces it and rejects a broken fixture | Step 1 (item 4) decides no field is added — AC 6 not triggered | N/A (explicitly not triggered; recorded as a decision, not skipped silently) |
| 7. Zero mechanism `state`/`verdict` changes | Steps 2-6 (scope discipline) | Step 8 — `git diff` check |
| 8. M0 schema unchanged, or change charged to M1's allowance | Step 6 (optional, docstring-only) + Scope Guards | Step 9 — `git diff --stat` on M0 data files + full `test_semantic_control_plane_schema.py` pass |

## Anti-Drift Notes

- **"Reconcile" must not drift into "merge."** Step 1 item 1 explicitly ranks the four axes rather
  than collapsing them; if an implementer finds the binding table "messy" and is tempted to simplify
  by merging two axes, that is exactly the drift the ticket's Out of Scope forbids.
- **Cross-reference, never duplicate.** Steps 2-6 insert one-line pointers, not restatements of the
  axis model's content. A cross-reference edit that grows past ~3 lines is duplicating content that
  belongs only in `status_axis_model.md`.
- **The most tempting scope-creep vector in this entire ticket is "fixing" `tactical_decision`'s row
  while writing the STARVED discussion** (Step 1 item 4) — the investigation explicitly flags this,
  and Step 8's `git diff` check exists specifically to catch it if it happens anyway.
- **Do not treat §10 as load-bearing merely because it's newer.** Step 1 item 5 and the axis-table
  ranking in item 1 both position it as the least authoritative axis — an implementer should resist
  any urge to "upgrade" §10's status while writing about it, since only Axes A, B, and D have real
  enforcement/data behind them.
- **The `MISSING`×2 and `OFF`/`INERT-OFF` homograph decisions are "keep both words," never
  "rename."** Renaming Axis D's enum values would touch `tools/semantic_control_plane/
  registry.py::VALID_RULE_CLASSIFICATIONS`, which is exactly the M0-schema-widening AC 8 forbids
  unless explicitly charged to M1's one bounded revision — which this ticket does not do.
- **The citation correction in this plan's Summary is itself load-bearing**: when Step 1 is
  implemented, use the corrected file:line citations (`docs/world_rules/README.md:172`,
  `architecture.md:189-190`) rather than investigation.md's original (`roadmap.md:171-177`), which
  do not exist at those lines.

## Deviations

- **Step 8 (AC 7 verification)** was implemented as a small deterministic script (parses
  `git diff registries/mechanisms.yaml`'s hunk headers via regex, fails loudly if any changed line
  falls at/after the pre-edit `layers:` boundary, line 109) rather than the plan's originally
  described "`git diff | grep -E '^\+|^-' | grep -v '^\+\+\+\|^---'` and manually confirm every hunk
  is inside the header range." This was done per an architecture-review suggestion surfaced at
  Implement time (non-blocking, not required by any AC): a scripted check is not eyeballed prose and
  fails loudly rather than relying on a human read of grep output. The plan's own reasoning for why
  this is a one-time check rather than a permanent pytest test (a hardcoded 93-row baseline would
  break on every legitimate future `state`/`verdict` correction) still holds and was preserved — the
  script was run once, ad hoc, from the session scratchpad, and was not committed to the repo as a
  permanent artifact. Manual `git diff` review was also performed as a cross-check, per the original
  plan text, and agreed with the script's result.
- No other deviations. Steps 1-7 and 9 were implemented exactly as specified.

## Unresolved Questions

None. Every item investigation.md's Risks and Open Questions section left open (axis-model doc
location, §10 enforcement status, `skeleton`'s non-relationship, both homograph resolutions, and the
STARVED/REACH-LIMITED field decision, including the "does the prose-convention count as a field for
AC 6" sub-question) has a concrete decision recorded in Step 1 above, grounded in investigation.md's
own evidence plus this plan's own additional binding-table resolutions for the `partial`/`PARTIAL`,
`gated`/`OFF`, and `orphan`/`DORMANT` pairs the ticket's Request Summary flagged but investigation.md
did not individually resolve (needed for AC 2's "every cross-axis pair" completeness, using the same
evidentiary method investigation.md already applied successfully to the two AC-3-required
homographs).
