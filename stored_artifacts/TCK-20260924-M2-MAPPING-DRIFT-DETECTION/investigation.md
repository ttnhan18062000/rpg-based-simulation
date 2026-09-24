---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M2-MAPPING-DRIFT-DETECTION
artifact_type: investigation
tags: [architecture, schema, registry]
---

# Investigation — TCK-20260924-M2-MAPPING-DRIFT-DETECTION

## Current Behavior

**No detector for the semantic control plane's own mapping exists today.** `tools/semantic_control_plane/`
currently holds exactly three modules: `registry.py` (schema validators), `rule_catalog.py`
(`scan_rule_ids()`), and `generate_territory_control_view.py` (the six-axis management view). None
of the three checks for drift — they only validate structure and render current state.

**`tools/semantic_control_plane/registry.py`** (`registry.py:116-152`,
`validate_rule_mechanism_edges()`) already rejects an unresolved `rule_id` or `mechanism_id` on
every row — confirmed by direct read: `errors.append(...)` fires whenever `rule_id not in
known_rule_ids` or `mechanism_id not in known_mechanism_ids` (`registry.py:138-143`). This means a
plain rename or removal of a mapped Rule or mechanism is **already a hard validator failure today**,
not silent drift — the ticket's own scope note is correct, verified against the real code, not just
taken on report.

**`registries/mechanisms.yaml`** carries **no lineage/history field of any kind.** Direct grep for
`split_from|merged_into|successor|predecessor|lineage|renamed_from` across the file returns zero
hits (one unrelated comment mentioning "split" in prose, `mechanisms.yaml:2392`, not a field). Split
and merge history lives only in prose inside `docs/plans/mechanism_identity_and_change_taxonomy.md`
(§5/§6/§8) and in `verified.note` free text on individual entries — never in a structured,
machine-readable field. This is the concrete fact that answers the ticket's own open question #2
below.

**M1's live mapping data** (`registries/rule_mechanism_edges.yaml:30-112`,
`registries/rule_classifications.yaml:31-92`) — every row's `date`/`review_date` is `"2026-09-24"`
(today). Five mechanisms are cited across the four TERR rows: `regional_sovereignty`,
`betrayal_siege_war`, `city` (via `rule_mechanism_edges.yaml`), plus the four TERR rule ids
themselves in `rule_classifications.yaml`. `registries/mechanism_causal_edges.yaml:39` is `edges:
[]` — zero rows, confirmed by direct read, so there is nothing for a causal-edge drift check to run
against yet (not itself an M2 gap; M1's own header records this as a deliberate zero-rows outcome).

**`tools/mechanism_registry/registry.py::MechanismRegistry`** (`registry.py:157-205`) is the read
surface M2 must reuse for the mechanism side: `get_verification(mechanism_id)` returns the live
`verified` block or `None` (`registry.py:200-205`); `parse_implemented_by_entry(entry)`
(`registry.py:101-108`) splits an `implemented_by` string into `(path, symbol_or_None)` — exactly
the helper the ticket's own Scope says to reuse, never re-parse.

**`tools/mechanism_registry/mechanism_registry_changed_code_check.py`** (full file read) is the
named structural precedent, confirmed line-for-line:
- Three-entry-point split: `check_drift(old_data, new_data, changed_files)` (pure core,
  `:87-102`), `check_drift_from_git(base_ref, head_ref)` (git wrapper via `git diff --name-only` +
  `git show <ref>:<path>`, `:148-154`), `check_drift_for_ticket(ticket_id, base_ref)` (close-time
  wrapper, `:205-214`).
- **This tool's own axis is a two-ref diff** (`--base`/`--head`, defaulting to `origin/main`/`HEAD`,
  `:217-228`) — it answers "did this diff change cited code," a fundamentally different question
  from M2's "has cited code changed since this row's own recorded date." Confirmed by direct read
  of `get_changed_files()` (`:133-135`, `git diff --name-only {base}...{head}`) and
  `load_registry_at_ref()` (`:138-145`, reads a specific ref or `WORKTREE`). **M2 must not copy this
  shape** — the ticket's own Scope warning is correct and independently confirmed here: there is no
  `base_ref`/`head_ref` pair in M2's problem, only one fixed point (today) and one per-row recorded
  date, so the git plumbing needed is `git log --before=<date>` / `git show <sha>:<path>`, not `git
  diff <ref>...<ref>`.
- Report-only convention confirmed: `main()` always `return 0` (`:251`), and the module docstring
  states this explicitly (`:30-34`). Never wired into CI; invoked via `make
  mechanism-registry-changed-code-check` and the close-time `--ticket-id` flag.
- `_uncommitted_changed_files()` via `git status --porcelain` (`:157-170`) — not directly reusable
  for M2 (M2 has no "ticket's own changed files" concept; it diffs cited paths' own git history
  against a stored row date, not a ticket's changed-file set), but establishes the repo's existing
  pattern for reading working-tree state alongside committed history when a check must not fail
  open just because it ran pre-commit.

**Git history check (ticket's own open question #1, resolved directly, not assumed):**
`git log --format='%H %ad %s' --date=short -- registries/mechanisms.yaml` shows the file's most
recent commit is `741b117de` on `2026-09-24` — the same single squash-merge commit
(`Simulation Semantic Control Plane: M0 schema/validator foundation + status-vocabulary
reconciliation (#241)`) that introduced `registries/rule_mechanism_edges.yaml` and
`registries/rule_classifications.yaml` in the first place (both files have exactly one commit in
their own `git log`, also `741b117de`). **There is a commit on `registries/mechanisms.yaml` on or
before every M1 row's `date`/`review_date` (`"2026-09-24"`)** — the assumption holds, resolvable
today via `git log --before="2026-09-24 23:59:59" --format=%H -- registries/mechanisms.yaml` (or
equivalent) followed by `git show <sha>:registries/mechanisms.yaml`. No blocker found; no schema
change is needed to recover the review-time verdict.

**Real residual risk on this same axis, not previously called out**: because `741b117de` and every
M1 row share the *same calendar date* (`2026-09-24`), `git log --before=<date> 23:59:59` will
resolve to `741b117de` itself today — correct only because no *later* commit on the same day has
touched `mechanisms.yaml` yet. The ticket's own "not blocking" open question (date-only, no time
component) is the same risk restated: if a second commit touching `mechanisms.yaml` lands later
today, "the commit on/before the row's date" becomes ambiguous between the two, and the conservative
reading (a same-day code change counts as "changed since review") the ticket already recommends
resolves it correctly *for drift class 1* (cited-file dates), but for drift class 3's own git-history
recovery of `mechanisms.yaml` itself, the same-day case needs an explicit tie-break: recovering the
verdict **as of the specific commit that introduced the row** (`741b117de`, known and pinnable, not
merely "some commit on 2026-09-24") is safer than a bare date-string comparison once same-day
commits are possible. Flagged for the implementer as a design detail, not a blocker — the ticket's
existing "pick the conservative reading, state it in a test" instruction already covers the general
case; this note narrows it for class 3 specifically.

**Split/merge mechanical-signal check (ticket's own open question #2, resolved directly):** no
lineage field exists (confirmed above). The one real precedent for a kept-ID split
(`action_pacing_readiness`, `mechanism_identity_and_change_taxonomy.md` §5) moved `state` from
`partial` → `done` and trimmed its `verified` block's own scope, while the *id itself* was
unchanged — a case the validator's unresolved-id check cannot see, and that neither M2 drift class 1
(implemented_by path change) nor class 3 (verdict change, as scoped by this ticket) is guaranteed to
catch either, since a split can preserve both `implemented_by` and `verdict` while still narrowing
what the id actually describes. **No mechanical signal exists in the current schema to detect this
shape short of comparing a full entry snapshot against a stored review-time baseline** — which is
exactly what `mechanism_registry_changed_code_check.py`'s own `old_mechs.get(mid) == mech` whole-
entry-equality check (`:100`) already does, on its own two-ref-diff axis, for a different purpose.
Building a second, per-row-date-scoped whole-entry-diff specifically for class 2 would duplicate that
existing tool's own approach against a different comparison basis, for a scenario that has not
occurred even once among the five mechanisms M1 actually mapped (`regional_sovereignty`,
`betrayal_siege_war`, `city`, plus the two implicitly-referenced ones with zero causal-edge rows).
**This supports descoping class 2 as its own detector code**, per the ticket's own named candidate —
see Risks and Open Questions and the recommended AC disposition below.

**Test-directory location — contradicts the ticket's own Scope line, verified directly.** The
ticket's Scope states tests should live under `tests/tools/`. Confirmed by directory listing:
`tests/tools/` exists but holds only `fixtures/`, `memory_probe.py`, `perf_assertions.py`, and
`__init__.py` — no `test_*.py` files, and it is not where any semantic-control-plane test lives.
The real, established home is `tests/unit/tools/` — `test_semantic_control_plane_schema.py` (M0's own
test module) and `test_mechanism_registry_changed_code_check.py` (the named structural precedent)
both live there, alongside `test_territory_control_view.py` and `test_mechanism_registry.py`. **The
new M2 test module belongs in `tests/unit/tools/`, not `tests/tools/`** — flagged as a direct
correction to the ticket's own pre-investigation, not a new decision.

**Makefile precedent** (`Makefile:349-382`, direct read): every generated-view/detector target in
this family follows `<subject>-<verb>` naming with a `##`-prefixed one-line help comment
(`territory-control-view`, `mechanism-registry-changed-code-check`). No `semantic-control-plane-*`
prefix exists yet — `territory-control-view` is the only current `tools/semantic_control_plane/`
target and does not use that prefix. The ticket's own suggested name,
`semantic-control-plane-drift-check`, is consistent with the family's naming shape and does not
collide with any existing target (confirmed by `grep -c "^semantic-control-plane-drift-check:"
Makefile` returning 0 before this ticket).

## Mechanics / Engine Constraints

This ticket builds a report-only tooling detector, not simulation behavior — no `docs/mechanics/`
chapter or `docs/engine/` contract governs its shape directly, the same conclusion both M0's and
M1's own investigations reached for this same tool family (`stored_artifacts/TCK-20260923-M0-
SCHEMA-VALIDATOR-FOUNDATION/investigation.md`'s "Mechanics / Engine Constraints" section; M1's own
section citing `architecture.md` §3/§4/§7/§8 and `docs/plans/status_axis_model.md`). The real
constraints are architectural, already covered above and reused here without change:
- `architecture.md` §7 — `UNKNOWN` is permanent; the detector must never treat an unmapped
  Rule/mechanism as an error, only report drift on rows that actually exist.
- `architecture.md` §3/§4 — the detector must never derive or write a `rule_classifications.yaml`
  classification value; it only reports that a row's own recorded evidence may be stale, leaving the
  human re-review judgment untouched (mirrors `mechanism_registry_changed_code_check.py`'s own
  restraint, "surfaces 'mapping review required', does not determine new semantic truth on its
  own" — `rollout_plan.md` Stage C, quoted verbatim).
- `docs/plans/status_axis_model.md` — any status word the detector's own output prints (e.g. citing
  a `verified.verdict` value) must be one of the four already-enforced axis vocabularies (`VALID_
  STATES`, `VALID_VERDICTS`, `VALID_RULE_CLASSIFICATIONS`), never a minted term. The detector's own
  *report* prose (e.g. "STALE", "CLEAN", "DRIFT FOUND") is not itself one of the four axes and is
  not constrained by this rule — only values it *echoes back* from the registries are.

## Docs Requiring Update

- `docs/plans/simulation_semantic_control_plane/roadmap.md`: M2's own goal/deliverables/exit-criteria
  section (lines 109-125) must move from an unstarted milestone description to reflect the shipped
  detector — the real `make` target name, which drift classes actually shipped as code versus were
  consciously descoped with a reason (class 2, if the recommendation above is adopted), and
  confirmation that running it against Territory's live mapping reports the exit criterion's own
  "clean today" (or, if not clean, the real finding and its disposition, per the ticket's own Out of
  Scope instruction not to silently re-review the row to force a clean report).

Two further doc-shaped items were genuinely considered, not silently skipped:

The epic ticket's own milestone-disposition table (`tickets/inprogress/TCK-20260923-SEMANTIC-
CONTROL-PLANE-EPIC.md`, the M2 row currently reading "**SCOPED** 2026-09-24, dispatched to
`rpg-implementer`") is real, required work per this ticket's own AC, but is **not** a `docs/` path —
it is a ticket file under `tickets/inprogress/`, outside `check_docs_to_update_coverage`'s own regex
scope (`^-\s+\`(docs/...)\``). It is listed here in prose, not as a Format-1 bullet, because a
bullet for a non-`docs/` path would not parse against that check and the path itself does not start
with `docs/` — the implementer/doc-updater must still update it as part of closing this ticket, it
is simply not the kind of path this section's machine-parsed format covers.

`docs/plans/simulation_semantic_control_plane/rollout_plan.md`'s own Stage C section (already
describing the detector's philosophy in the abstract, not tied to any milestone's completion state)
was considered because it names the same three drift classes `roadmap.md` M2 does. It is not
required to change for this ticket: Stage C's own text already accurately describes the
detector's intended shape and philosophy without asserting whether it exists yet — the same reasoning
M0's and M1's own investigations already applied to this exact document (neither touched it, for the
same "describes the design, not milestone completion state" reason). `docs/plans/status_axis_model.md`
was also considered, since the detector echoes axis-B vocabulary in its output — it is not required
to change: this ticket reuses the existing four-axis vocabulary without adding a new value, term, or
binding, so nothing in that doc's own content becomes stale.

`docs/plans/simulation_semantic_control_plane/architecture.md` is not required to change: M2 adds a
detector over already-decided schemas (§3) and does not revise the mapping shape, the classification
rule, or the six management-view axes (§8) — nothing in §§1-9 becomes inaccurate by this ticket's own
scope.

## Parity Ledger Overlap

None required. Searched all nine `docs/parity_ledger/*.yaml` files for `TERR-0|regional_sovereignty|
betrayal_siege_war|owner_faction_id` — three incidental hits beyond the already-known `FAC-010`:
`world_dynamics.yaml:1388-1392` (an unrelated `SOVEREIGNTY-EVENTS` entry about `WorldEvent` emission
on ownership change, not the TERR mapping) and `infrastructure.yaml:8709-8713` (an unrelated
`_set`-suffix-convention citation). Neither overlaps this ticket's scope. `FAC-010`
(`docs/parity_ledger/faction.yaml:227-242`, `status: verified`, `priority: P1`) is cited as evidence
inside `registries/rule_mechanism_edges.yaml`'s own TERR-01/TERR-03 rows (M1's work, already landed)
but this ticket does not alter `FAC-010`, does not change any `src/` behavior, and does not touch any
parity-tracked simulation path — it is a read-only detector over already-committed registry data. No
P0 entry is touched.

## Prior Work

- `stored_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/` — built the three schemas and
  `tools/semantic_control_plane/registry.py` this detector reads; its own investigation established
  the "new sibling package, not folded into `tools/mechanism_registry/`" precedent this ticket's own
  module placement (`tools/semantic_control_plane/`) already follows.
- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/` — produced the five live
  mapping rows this detector checks drift against; its own investigation independently confirmed the
  `FactionInfluenceService` binding for `regional_sovereignty` and the FAC-010 second-desync finding,
  both directly relevant context for reading the mapping rows' own evidence prose without
  re-deriving it.
- `tools/mechanism_registry/mechanism_registry_changed_code_check.py` +
  `tests/unit/tools/test_mechanism_registry_changed_code_check.py` — the named structural precedent
  for the pure-core/git-wrapper split, the report-only/always-exit-0 convention, and the
  disposable-temp-git-repo test pattern for planted-fixture proof (`_init_temp_repo`/`_commit`/
  `_in_temp_repo` helpers, `:182-210`), directly reusable for M2's own planted-drift fixture tests.
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — the split/merge vocabulary and the one
  real kept-ID split precedent (`action_pacing_readiness`, §5) this investigation's class-2 finding
  is built on.
- `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` — source of the prove-it-fails-on-a-deliberately-
  broken-fixture discipline this ticket's own AC requires per drift class.

## Risks and Open Questions

- **Open, implementer's call (per ticket): does drift class 2 justify its own code?** This
  investigation found **no mechanical signal** in the current schema for a split/merge that keeps a
  resolvable ID — no lineage field exists anywhere in `registries/mechanisms.yaml`, and the one real
  precedent case (`action_pacing_readiness`) is only detectable by a full-entry snapshot diff against
  a stored review-time baseline, which would duplicate `mechanism_registry_changed_code_check.py`'s
  own whole-entry-equality approach on a different (per-row-date, not two-ref) axis, for a case that
  has not occurred once among M1's five mapped mechanisms. **Recommendation: descope class 2 as its
  own detector code**, with this investigation's finding as the written reason, satisfying the
  ticket's own AC ("or any one consciously descoped with a written reason... class 2's overlap with
  the existing validator is the expected candidate"). This is a recommendation for the
  planner/implementer to confirm, not a decision this investigation finalizes unilaterally.
- **Same-day git-history ambiguity for drift class 3** (new finding, detailed above under Current
  Behavior): today, every M1 row and `mechanisms.yaml`'s own last commit share the same calendar date
  (`2026-09-24`), so "the commit on/before the row's date" is unambiguous only because no second
  commit has touched `mechanisms.yaml` today yet. Recommend the implementer pin the review-time
  commit explicitly where possible (the commit that introduced the row, `741b117de` for all of M1)
  rather than re-deriving "the commit on or before this date" freshly every run, or at minimum make
  the same-day tie-break rule explicit and tested (which commit wins when two share a date — first or
  last chronologically on that day).
- **Whether the detector should also echo `state` drift, not just `verified.verdict`** — the
  `action_pacing_readiness` split moved `state` (`partial` → `done`) without necessarily moving
  `verdict`. The ticket's own Scope explicitly bounds class 3 to `verified.verdict` only; this
  investigation does not recommend widening that scope (would blur class 3 into a second entry-diff
  check, the same duplication concern raised for class 2 above), but flags it as a residual blind
  spot the implementer/reviewer should be aware of, not silently assume is covered.
- **Test-directory correction** (detailed above): the ticket's own Scope names `tests/tools/`; the
  real, established location is `tests/unit/tools/`. Not itself risky, but must be caught before
  Implement writes to the wrong directory.

## Anti-Drift Hazards

- **Do not copy `mechanism_registry_changed_code_check.py`'s `--base`/`--head` two-ref-diff shape.**
  The ticket's own Scope and this investigation both independently confirm M2's axis is a per-row
  date comparison, not a ref diff — copying the shape would silently answer a different question
  ("did this branch change cited code" instead of "has cited code changed since this row's own
  review").
- **Do not let the detector write, correct, or suggest a `rule_classifications.yaml` value.** Same
  "declared, not derived" rule M0/M1 already enforce by omission — a drift detector that also
  auto-corrects the very thing it's flagging as stale would reintroduce the mechanical-derivation
  failure `architecture.md` §3/§4 already rejects once for this design.
  `test_no_function_derives_classification_from_edges` (`tests/unit/tools/
  test_semantic_control_plane_schema.py:387-400`) already guards the edge-to-classification path;
  a drift-detector-to-classification path would be the same failure shape from a new direction and
  should be guarded the same way if any such helper is ever tempted.
- **Do not add a `reviewed_mechanism_verdict` (or similar) field to `rule_mechanism_edges.yaml`/
  `rule_classifications.yaml`** unless the git-history-recovery approach is proven unworkable in
  Implement — the ticket's own Scope already states this and this investigation's own git-log check
  (above) confirms the git-history path is viable today, so the schema-migration fallback should not
  be reached for by default.
- **Do not make this detector block anything.** Exit 0 unconditionally, same as
  `mechanism_registry_changed_code_check.py`'s own `main()` (`:251`, "Always 0 -- this check never
  fails the build") and every other detector in this corpus — no CI wiring, no ratchet, per this
  ticket's own explicit Out of Scope.
- **Do not write the new test module to `tests/tools/`.** Use `tests/unit/tools/`, matching every
  real sibling test file in this family (see Current Behavior's test-directory correction above).
