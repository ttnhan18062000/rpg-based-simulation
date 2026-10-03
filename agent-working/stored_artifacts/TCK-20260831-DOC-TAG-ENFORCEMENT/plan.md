---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260831-DOC-TAG-ENFORCEMENT
artifact_type: plan
tags: [frontmatter, tagging, taxonomy, documentation, schema]
---

# Implementation Plan — TCK-20260831-DOC-TAG-ENFORCEMENT

## Summary

This plan extends `tools/validate_frontmatter.py`'s tag hard-allowlist to `doc`-type frontmatter
without retrofitting the existing 397-doc corpus. It introduces a new, doc-only opt-in boolean
field, `tags_enforced: true`, as the cutover signal (Decision 2), computed independently of
`_check_tags`'s existing `ticket_id`-based scope logic (Decision 1: extract the content-type-
agnostic canonical-form/registry-membership loop into a shared private helper, leave `_check_tags`'s
external signature and ticket/artifact behavior byte-for-byte unchanged, add a new thin
`_check_doc_tags` wrapper that calls the same helper). No bulk backfill of the 234 unregistered doc
tags is performed (Decision 3: pure forward-only grandfathering, mirroring the ticket-side
precedent exactly — zero existing doc carries the new field, so zero existing doc is newly
rejected). The layer allowlist check requires no code change at all — it is already fully wired
(`_validate_doc` already calls `_check_enum(..., "layer", LAYER_VALUES)`) — so this plan "ships" it
by adding a regression-pinning test against the one real violation found in investigation
(`docs/simulation/domains/social_memory_contract.md`, `layer: social`) without touching that file's
content, since choosing between registering a new permanent `social` layer or remapping it to an
existing one is an irreversible registry decision this ticket does not need to make to satisfy its
own acceptance criteria (Decision 4).

## Decisions (per this ticket's own Assumptions/Open Questions — decided here, not left open)

### Decision 1 — `_check_tags` generalization shape: extract a shared core, do not change `_check_tags`'s signature or behavior

**Chosen:** Add a new private helper, `_tag_membership_errors(filepath: str, tags: list, registry:
dict | None) -> list[str]`, containing exactly the two-stage loop currently inside `_check_tags`
(`tools/validate_frontmatter.py:172-181`, confirmed by direct read in this session: `for tag in
tags: violation = canonical_form_violation(tag); ... elif registry is not None and not
is_tag_registered(tag, registry): ...`). `_check_tags(filepath, fm, registry=None)` keeps its exact
current signature and ticket_id-based scope derivation (`tools/validate_frontmatter.py:156-170`)
and internally calls `_tag_membership_errors` for its own tag list — this is a pure refactor with
zero external behavior change. A new `_check_doc_tags(filepath, fm, registry=None)` computes its
own in-scope decision from the new `tags_enforced` field (Decision 2) and, if in-scope, also calls
`_tag_membership_errors`.

**Why this over the investigation's alternative (a caller-supplied `in_scope` parameter added
directly to `_check_tags`):** either shape satisfies "don't reimplement `canonical_form_violation`/
`is_tag_registered`" (this ticket's Out of Scope). Leaving `_check_tags`'s signature and internal
ticket_id logic completely untouched — rather than adding a new parameter/branch to it — is the
smaller, more reversible change: `_validate_ticket` (`tools/validate_frontmatter.py:204`) and
`_validate_artifact` (`:218`) keep calling `_check_tags(filepath, fm, registry)` exactly as today,
so there is structurally zero risk of an accidental behavior change on the ticket/artifact path from
this refactor — the existing 7 `TestTagRegistryEnforcement` tests exercise `_check_tags` end-to-end
and act as a byte-for-byte regression guard with no changes needed to those tests themselves.

### Decision 2 — Cutover mechanism: new opt-in boolean field `tags_enforced`

**Chosen:** A new, optional `doc`-frontmatter field, `tags_enforced: true`. When absent, `false`, or
any falsy/missing value, `_check_doc_tags` returns `[]` (exempt — this is every doc in the corpus
today, since no doc anywhere carries this field). When present and truthy, tag checks apply exactly
as they do for in-scope tickets/artifacts.

**Why a boolean over the ticket-side's date-embedded pattern:** the ticket-side mechanism embeds a
date in `ticket_id` because `ticket_id` already exists for an unrelated reason (identifying the
ticket) and a *global* forward-only date cutoff naturally falls out of it. Docs have no equivalent
naturally-occurring identifier. Investigation's option (a) (evaluated as "High" feasibility,
`investigation.md` "Risks and Open Questions" table) frames a boolean as one valid shape of the
"opt-in marker field" family. A plain boolean is chosen over a second date field because: (1) it is
a strict per-file opt-in, not a global forward-only rollout, so there is no meaningful "date" to
encode — a doc author (or a future ticket) marks a specific file in-scope when it's ready; (2) it
avoids a second, redundant date-comparison code path next to `_ticket_id_effective_date` for a
mechanism that is conceptually "on/off," not "before/after a cutoff"; (3) it keeps the doc-side
grandfathering trivially provable — "does this key exist and is it truthy" — which is exactly what
`test_doc_missing_cutover_field_defaults_to_exempt` and
`test_doc_predating_cutover_signal_not_newly_rejected` (test_plan.md) need to assert.

**Why not (b) git blame/log:** investigation.md rules this out directly — no precedent in this
codebase for a frontmatter-scoped git-history check, `-L` line-range tracking breaks across
renames/squashes, and it adds a new git-subprocess dependency `validate_frontmatter.py` does not
have today (it is pure text-parsing). Rejected.

**Why not (c) path-scoped rollout alone:** trivial to add but coarse-grained — it grandfathers or
enforces whole directories, not individual files, so it cannot alone satisfy AC #3's per-file
grandfathering requirement. Not used as the primary mechanism. (Nothing prevents a *future* ticket
from combining it with `tags_enforced` — e.g., opting a whole directory in by editing each file's
frontmatter — but that bulk edit is exactly the kind of retrofit Decision 3 defers.)

**Why not (d) `last_verified`:** already conclusively ruled out by the ticket itself and confirmed
by investigation.md's direct measurement (75/397 doc entries, not a universal signal) and semantic
mismatch (freshness vs. tag-scope). Rejected.

### Decision 3 — Retrofit strategy: pure forward-only grandfathering, no bulk backfill

**Chosen:** No tag is registered into `registries/tag_registry.jsonl` and no doc's frontmatter is
edited to add `tags_enforced` as part of this ticket. Every one of the 397 existing doc entries
lacks the new field by construction, so every existing doc is automatically exempt — 0 new
violations against the current corpus (confirmed reasoning: `_check_doc_tags` returns `[]` whenever
`tags_enforced` is falsy/absent, which is unconditionally true for the current corpus today).

**Why over a bulk backfill pass:** this ticket's own Out of Scope explicitly excludes "Actually
performing a bulk backfill/registration of the ~1310 currently-unregistered doc tags" — pure
forward-only grandfathering is the only strategy consistent with that constraint, and it is also the
smaller, safer, fully reversible option (an opt-in field that no file yet carries cannot break
anything on landing). The 9 high-frequency unregistered tags investigation.md flags as legitimate
registration candidates (`idea`×28, `contract`×16, `agent-infrastructure`×12, `roadmap`×8,
`domains`×8, `pipeline`×5, `planning`×5, `guide`×5, `scoring`×4) and the 3 canonical-form violations
(`Any`, `worldmodules`, `simulation_quality`) are **not** touched by this plan — they remain
candidates for a future, separately-scoped backfill ticket, exactly as this ticket's Out of Scope
already anticipates. No doc file's tags are edited by this plan.

### Decision 4 — Layer check: ship as already-complete; do not fix the one known violation

**Chosen:** No code change to the layer-enum check (`_check_enum(filepath, fm, "layer",
LAYER_VALUES)` inside `_validate_doc`, `tools/validate_frontmatter.py:194`) — it is already fully
wired and already runs whenever `_validate_doc` runs. This plan adds one regression-pinning test
(`test_invalid_layer_doc_fixture_still_rejected`, per test_plan.md) against the real fixture
`docs/simulation/domains/social_memory_contract.md` (`layer: social`, not in the 20-value
`LAYER_VALUES` registry) to make the pre-existing violation a documented, deliberate fact rather
than a silent latent one. **This plan does not edit that file's `layer:` value** — choosing between
registering a new, permanent `social` layer (`registries/layer_registry.jsonl` is append-only,
confirmed in `tools/layer_registry.py`'s design per investigation.md) versus remapping the file to
an existing layer (`strategy` or `simulation`) is a content decision outside this ticket's scope
(extending the *validator*, not curating the *corpus*), and no Acceptance Criterion requires the fix
— AC #6 only requires the post-change violation count be "bounded, understood," which a single
already-flagged, already-tested violation satisfies. Fixing this file is left as a one-line follow-up
for whoever owns `docs/simulation/domains/social_memory_contract.md`'s content.

## Steps

### Step 1 — Extract `_tag_membership_errors` from `_check_tags`

**Files:** `tools/validate_frontmatter.py`

**Change:** Add a new private function `_tag_membership_errors(filepath: str, tags: list, registry:
dict | None = None) -> list[str]` containing exactly the loop body currently inside `_check_tags`
(read directly in this session, `tools/validate_frontmatter.py:172-181`):
```python
def _tag_membership_errors(filepath: str, tags: list, registry: dict | None = None) -> list[str]:
    errors = []
    for tag in tags:
        violation = canonical_form_violation(tag)
        if violation:
            errors.append(f"{filepath}: tags: {violation}")
            continue
        if registry is not None and not is_tag_registered(tag, registry):
            errors.append(
                f"{filepath}: tags: {tag!r} is not in the tag registry — register it first via "
                f"`python3 tools/tag_registry.py add {tag} --category <category> "
                f'--note "..."`'
            )
    return errors
```
Rewrite `_check_tags` to call it after computing `embedded_date` and the early-return, i.e. replace
its existing inline loop with `return _tag_membership_errors(filepath, tags, registry)`. `_check_tags`'s
signature, docstring, and the `embedded_date is None or embedded_date <
TAG_TAXONOMY_EFFECTIVE_DATE` early-exempt branch (`tools/validate_frontmatter.py:156-170`) are
otherwise untouched.

**Other writers to this file:** `tools/validate_frontmatter.py` has no other concurrent writer within
this ticket's steps — Steps 1–3 are sequential edits to the same file within one implementation
session, not concurrent processes. No other ticket or background process modifies this file (single-
file, single-session change).

**Do NOT touch:** `_ticket_id_effective_date`, `_TICKET_ID_DATE_PATTERN`, `TAG_TAXONOMY_EFFECTIVE_DATE`,
`_check_enum`, `_validate_ticket`, `_validate_artifact`, `_validate_archive`, `_VALIDATORS`,
`validate_file`/`validate_directory`, `main()` — none of these change in this step.

**Verify:** Full unmodified re-run of `tests/tools/test_validate_frontmatter.py::TestTagRegistryEnforcement`
(all 7 tests) and `TestEnumAntiDrift::test_tag_taxonomy_effective_date` — must pass with zero
changes to those test files, proving the refactor is behavior-preserving for tickets/artifacts.

### Step 2 — Add `_check_doc_tags` with the `tags_enforced` cutover signal

**Files:** `tools/validate_frontmatter.py`

**Change:** Add a new private function:
```python
def _check_doc_tags(filepath: str, fm: dict, registry: dict | None = None) -> list[str]:
    """Validate doc tags: canonical form + registry membership, only for docs opted in via
    `tags_enforced: true`. Every doc lacking this field (the entire corpus as of this ticket) is
    exempt/grandfathered — see docs/guidelines/tag_taxonomy.md's Enforcement section."""
    tags = fm.get("tags")
    if not tags:
        return []
    if not fm.get("tags_enforced"):
        return []
    return _tag_membership_errors(filepath, tags, registry)
```
Place it directly after `_check_tags` (before `_validate_doc`), mirroring the file's existing
top-to-bottom ordering (generic checks, then per-content-type validators).

**Other writers to this file:** same as Step 1 — no concurrent writer; sequential edit within this
ticket's own implementation pass.

**Do NOT touch:** `_check_tags` itself (already finalized in Step 1), `is_phase_milestone_tag`
exemption logic inside `_tag_membership_errors`/`canonical_form_violation` (in `tag_registry.py`,
not touched at all by this ticket per Out of Scope).

**Verify:** New `TestDocTagEnforcement` tests (test_plan.md): `test_doc_registered_tag_accepted`,
`test_doc_unregistered_tag_rejected`, `test_doc_non_canonical_tag_rejected`,
`test_doc_phase_milestone_tag_exempt_from_registration`,
`test_doc_missing_cutover_field_defaults_to_exempt` — all against `_check_doc_tags` called directly
(unit-level, no `_validate_doc` wiring needed yet — that's Step 3).

### Step 3 — Wire `_validate_doc()` to call `_check_doc_tags`

**Files:** `tools/validate_frontmatter.py`

**Change:** In `_validate_doc(filepath, fm, registry=None)` (`tools/validate_frontmatter.py:188-199`
as read in this session), add one line before `return errors`:
```python
errors += _check_doc_tags(filepath, fm, registry)
```
This is the actual fix for the ticket's named code gap ("`_validate_doc` does not call
`_check_tags` anywhere" — investigation.md "Current Behavior") — but calling the new
`_check_doc_tags`, not the ticket_id-scoped `_check_tags`, per Decision 1/2 above. This is the one
line that must NOT be a naive `_check_tags(filepath, fm, registry)` call (investigation.md's named
failure mode: that exact call is a permanent silent no-op for every doc because no doc frontmatter
carries `ticket_id`).

**Other writers to `_validate_doc`:** `_VALIDATORS = {"doc": _validate_doc, ...}`
(`tools/validate_frontmatter.py:245`) is the only place `_validate_doc` is referenced/dispatched to;
`validate_file`/`validate_directory` call it only via that dispatch table. Per investigation.md's
consumer sweep, the only caller of `validate_file`/`validate_directory` anywhere in the repo is
`tools/gate_checks/done_checker_static.py` (`validate_file(ticket_path, registry=registry)` at line
272, and `validate_directory(staging_dir, content_type_override="artifact", registry=registry)` at
line 282) — both calls are hardcoded to `ticket`/`artifact` content types and never resolve to
`doc`, so this wiring change cannot affect `done_checker_static.py`'s behavior. No other consumer
calls the doc path. Confirmed no concurrent writer to this function during implementation.

**Do NOT touch:** the four required-field checks, the four `_check_enum` calls, or the
`last_verified`-when-`authoritative` conditional already inside `_validate_doc` — none of those
change.

**Verify:** `test_validate_doc_no_longer_silently_skips_tags` (the primary anti-no-op guard — an
in-scope doc fixture with a definitely-unregistered tag and empty registry must produce a non-empty,
`tags`-mentioning error list) and `test_doc_predating_cutover_signal_not_newly_rejected` (a real
pre-existing doc fixture, e.g. `docs/world/assembly_contract.md`, lacking `tags_enforced`, must
still validate to `[]` on its `tags:`-prefixed errors). Also re-run `TestDocContentType`'s existing
`test_doc_tags_optional_present`/`test_doc_tags_optional_absent` unmodified — both must keep
passing, now because `_check_doc_tags` correctly resolves them as out-of-scope (no
`tags_enforced`), not because the check is absent.

### Step 4 — Pin the one known real doc-layer violation with a regression test

**Files:** `tests/tools/test_validate_frontmatter.py`

**Change:** Add `test_invalid_layer_doc_fixture_still_rejected` (test_plan.md), asserting
`validate_file(Path("docs/simulation/domains/social_memory_contract.md"))` contains an error
matching `layer: invalid value 'social'`. Place it in `TestDocContentType` (extends the existing
group, per test_plan.md's stated placement — this is a layer-only assertion, not a new tag-check
class). No production code changes in this step — the layer enum check already exists and already
runs (`_check_enum(filepath, fm, "layer", LAYER_VALUES)` at `tools/validate_frontmatter.py:194`,
confirmed unchanged by Steps 1–3).

**Other writers to `docs/simulation/domains/social_memory_contract.md`:** none from this ticket — its
`layer: social` value is read-only in this step, per Decision 4. No other in-flight ticket in this
worktree touches this file (confirmed no reference to it outside investigation.md/test_plan.md/this
plan).

**Do NOT touch:** `docs/simulation/domains/social_memory_contract.md`'s frontmatter content itself —
no edit to its `layer:` value. Do not register a new `social` layer in
`registries/layer_registry.jsonl`.

**Verify:** the new test itself, run once added.

### Step 5 — Update `docs/guidelines/tag_taxonomy.md`'s Enforcement section

**Files:** `docs/guidelines/tag_taxonomy.md`

**Change:** Replace the final paragraph of the "Enforcement" section (read in full this session,
lines ~195-224; the exact sentence to remove: "This taxonomy applies to `ticket` and `artifact`
content types only. `doc`-type frontmatter's `tags` field remains free-form and unvalidated (see
`docs/guidelines/frontmatter_schema.md`) — the registry does not apply there either.") with text
describing the actual new scope: `doc`-type frontmatter's `tags` field is now checked (canonical
form + registry membership) **only for docs that opt in** via `tags_enforced: true` in their
frontmatter; any doc lacking that field (the entire corpus as of this ticket) remains free-form and
unvalidated, matching pre-ticket behavior exactly. State explicitly that this is an opt-in
per-file mechanism, not a forward-only date cutoff like the ticket/artifact side, and that no
existing doc has been retrofitted or bulk-registered.

**Other writers to this file:** none identified — no other in-flight ticket references
`tag_taxonomy.md`.

**Do NOT touch:** the "Canonical-Form Rules," "Categories," or earlier "Enforcement" paragraphs
(the `2026-07-04` ticket/artifact forward-only description) — those remain accurate and unchanged.

**Verify:** manual read-through; no automated test asserts prose content, but
`test_check_tags_ticket_scope_unaffected_by_doc_generalization` indirectly confirms the described
ticket/artifact behavior still matches what this doc continues to say.

### Step 6 — Update `docs/guidelines/frontmatter_schema.md`'s `doc` schema table

**Files:** `docs/guidelines/frontmatter_schema.md`

**Change:** In the `doc` content-type table (read this session, lines 46-53), change the `tags` row
from `| tags | no | list of strings | free-form |` to describe the new conditional enforcement
(e.g. `| tags | no | list of strings | free-form unless \`tags_enforced: true\` — see
tag_taxonomy.md |`), and add a new row: `| tags_enforced | no | boolean | opt-in tag-enforcement
marker, default false/absent |`. Optionally (cheap, same file/section, flagged by investigation.md
as pre-existing unrelated staleness, not new scope) also add the missing `frontend` value to the
`LAYER_VALUES` "Enum Reference" list (investigation.md: 19 listed vs. 20 real registered values,
already covered by an existing passing test `test_enum_values_layer`) — this is optional cleanup,
not required by any Acceptance Criterion; do it only if it does not risk the step's own scope or
review time.

**Other writers to this file:** none identified.

**Do NOT touch:** the `ticket`/`artifact`/`archive` schema tables in this same file, or any other
section besides the `doc` table (and, if done, the `LAYER_VALUES` enum reference list).

**Verify:** manual read-through; no automated test asserts this file's prose, but keep the doc
internally consistent with Step 5.

### Step 7 — Update parity ledger entry `INFRA-180`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Update entry `id: INFRA-180` (read in full this session, lines 1897-1909). Current
`text` ends: "...On ticket/artifact content types, tags additionally carry controlled-vocabulary
enforcement per docs/guidelines/tag_taxonomy.md — forbidden p0/p1/p2 tags and canonical-
synonym/format rejection — applied forward-only from 2026-07-04 so historical tickets are not newly
rejected." Append/amend to state doc-type frontmatter now also carries the same controlled-
vocabulary checks, gated on the new opt-in `tags_enforced: true` field rather than a date cutoff,
with the existing corpus fully grandfathered (no doc currently carries the field). Update
`v2_evidence` to add `_check_doc_tags`/`_tag_membership_errors` and the new
`TestDocTagEnforcement`/`test_invalid_layer_doc_fixture_still_rejected` test additions to the
existing evidence list (`tools/validate_frontmatter.py + docs/guidelines/frontmatter_schema.md +
docs/guidelines/tag_taxonomy.md + tests/tools/test_validate_frontmatter.py` — same four files,
evidence description just needs the doc-scope addition named). Keep `status: verified` (the behavior
described remains fully implemented and tested, just broader in scope) and `priority: P2` unchanged.

**Other writers to `docs/parity_ledger/infrastructure.yaml`:** this is a shared, actively-written
multi-entry YAML file — other tickets add/update *other* `id:` entries in the same file over time
(e.g. `INFRA-263`, `INFRA-282`, `INFRA-306` are all visible in the current file, added by unrelated
prior tickets). This step touches only the `INFRA-180` entry's `text`/`v2_evidence` fields — no
other entry is read or modified. Per this project's own established incident precedent (full-file
raw-YAML rewrites via ad-hoc scripts/Edit have caused real corruption on this file before), **this
step must use `tools/parity_ledger_writer.py` (or dispatch to the `parity-updater` agent, which
uses that same sanctioned, schema-validating tool) to apply the edit — never a raw `Edit` tool call
or a hand-written YAML dump** that rewrites the whole file.

**Do NOT touch:** any other `id:` entry in `infrastructure.yaml`, or any other parity ledger file
(`substrate.yaml`, `combat_movement.yaml`, etc. — investigation.md confirms none reference this
subsystem).

**Verify:** no dedicated pytest test for parity ledger prose; confirm via
`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` (file
still parses) and a manual diff review showing only the `INFRA-180` entry changed.

### Step 8 — Real-corpus verification run (Acceptance Criterion #6)

**Files:** none changed; this is a verification-only step, executed at Test/Verify phase, not
Implement.

**Change:** Run `python3 tools/validate_frontmatter.py docs/` against the full corpus after Steps
1–7 land. Expected result, per Decision 3 (pure grandfathering, no doc carries `tags_enforced`) and
Decision 4 (layer check unchanged): **0 new tag violations**, **exactly 1 layer violation**
(`docs/simulation/domains/social_memory_contract.md`, `layer: social` — pre-existing, not newly
introduced by this ticket, per Step 4's pinning test). Record this exact composition (0 tag / 1
layer, with the one layer violation named and attributed as pre-existing) in the ticket's `Test
Summary` at close, satisfying AC #6's "bounded, understood violation count" requirement without
asserting a hardcoded count inside any pytest test (per test_plan.md's Anti-Drift Test Guards —
`TCK-20260720-TAG-CORPUS-REPAIR-SWEEP` precedent against live-corpus count assertions in tests).

**Other writers:** none — read-only verification command.

**Do NOT touch:** do not "fix" the 1 layer violation as part of this step just because the count is
now visible (see Decision 4) — recording it is sufficient.

**Verify:** the command's own exit code and output text, compared manually against the expected
composition above; not a pytest assertion.

## Scope Guards

Explicit list of things this plan must not touch (from the ticket's Out of Scope, investigation.md's
Anti-Drift Hazards, and this plan's own Decisions):

- No bulk registration of any of the 234 currently-unregistered doc tags into
  `registries/tag_registry.jsonl` (Decision 3; ticket Out of Scope).
- No bulk assignment/correction of `layer:` values across the doc corpus beyond the single
  pinning test in Step 4 (Decision 4; ticket Out of Scope).
- No edit to `docs/simulation/domains/social_memory_contract.md`'s frontmatter content (Decision 4).
- No new registration in `registries/layer_registry.jsonl` (no new `social` layer added).
- No fix to the 3 canonical-form violations (`Any`, `worldmodules`, `simulation_quality`) found in
  the doc corpus — they remain grandfathered like every other existing doc tag (Decision 3).
- No change to `_check_tags`'s external signature, its `ticket_id`-based scope derivation, or any
  `_validate_ticket`/`_validate_artifact` call site (Decision 1; investigation.md Anti-Drift
  Hazards).
- No change to `canonical_form_violation()`, `is_tag_registered()`, `load_registry()`, `add_tag()`
  in `tools/tag_registry.py`, or `layer_values()`/`is_layer_registered()` in
  `tools/layer_registry.py` (ticket Out of Scope — single source of truth, call only, never
  reimplement).
- No wiring of `validate_frontmatter.py` into any CI workflow (`.github/workflows/*.yml`) — confirmed
  still unreferenced anywhere in CI (ticket Out of Scope).
- No change to `tools/generate_registry.py`'s `collect_docs`/`collect_tickets` projections
  (ticket Out of Scope).
- No change to `tools/tag_corpus_sweep.py` or `tools/tag_report.py`'s existing ticket/artifact-scoped
  corpus walk (test_plan.md Regression Surface; those tools' own scope guards from
  `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP` remain in force).
- No raw `Edit`/hand-written full-file YAML rewrite of `docs/parity_ledger/infrastructure.yaml` —
  Step 7 must go through `tools/parity_ledger_writer.py` or the `parity-updater` agent.
- Per the doc-updater's own standing boundary, `docs/parity_ledger/`, `docs/audits/`,
  `docs/archive/`, `docs/scenarios/`, and `docs/entity/` are not touched by this plan except the one
  explicit, in-scope `INFRA-180` edit in Step 7 (which is itself inside `docs/parity_ledger/` but is
  a named, required Acceptance Criterion, not incidental drift).

## Dependency Map

- Step 1 → Step 2 (Step 2's `_check_doc_tags` calls `_tag_membership_errors`, which Step 1 creates).
- Step 2 → Step 3 (Step 3 wires `_check_doc_tags` into `_validate_doc`; cannot wire a function that
  doesn't exist yet).
- Step 4 is independent of Steps 1–3 (pure test addition against already-existing layer-check code)
  and can be done in parallel with them, but is listed after Step 3 for narrative flow.
- Steps 5, 6, 7 (doc/parity updates) depend on Steps 1–3 being finalized (their prose describes the
  final `tags_enforced` field name and behavior) but do not depend on each other and can be done in
  any order or in parallel with each other.
- Step 8 depends on all of Steps 1–7 being complete (it verifies the final state of the corpus run).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: plan.md documents a decided cutover mechanism and retrofit strategy before implementation | This document's "Decisions" section (Decisions 1–4) | N/A — documentation artifact, reviewed at Plan-phase gate |
| AC2: `_validate_doc()` calls `_check_tags()` or an equivalent doc-appropriate variant; unregistered in-scope tag hard-rejects | Steps 1, 2, 3 | `test_validate_doc_no_longer_silently_skips_tags`, `test_doc_unregistered_tag_rejected` |
| AC3: a doc predating/outside the cutover signal is not newly rejected (grandfathering, verified against a real fixture) | Steps 2, 3 | `test_doc_predating_cutover_signal_not_newly_rejected`, `test_doc_missing_cutover_field_defaults_to_exempt` |
| AC4: `tag_taxonomy.md`'s Enforcement section no longer states doc tags are unconditionally exempt; states the actual new scope | Step 5 | manual read-through (no automated prose test) |
| AC5: `infrastructure.yaml` `INFRA-180`'s `status`/`v2_evidence` reflect the new doc-enforcement behavior | Step 7 | YAML-parses check + manual diff review |
| AC6: new/updated tests cover registered-tag-passes, unregistered-tag-rejects, non-canonical-rejects, grandfathered-doc-unaffected | Steps 2, 3, 4 | `TestDocTagEnforcement`'s full new test set (test_plan.md), `test_invalid_layer_doc_fixture_still_rejected` |
| AC7: `python3 tools/validate_frontmatter.py docs/` produces a bounded, understood violation count, recorded in Test Summary | Step 8 | manual run + `Test Summary` entry at ticket close |

## Anti-Drift Notes

- **The single most important hazard this plan guards against**: investigation.md's named failure
  mode — a naive, unmodified `_check_tags(filepath, fm, registry)` call added inside `_validate_doc`
  is a *permanent, silent no-op* for every doc, because no doc frontmatter carries `ticket_id`, so
  `_ticket_id_effective_date(fm.get("ticket_id"))` is always `None` and `_check_tags`'s exemption
  branch is always true. This plan avoids that shape entirely by routing docs through a separate
  `_check_doc_tags` function with its own, doc-appropriate scope signal (`tags_enforced`), not
  through `_check_tags` at all. `test_validate_doc_no_longer_silently_skips_tags` is the concrete
  test that would fail against the naive implementation and must pass against this plan's actual
  one.
- **Do not let `_check_tags`'s refactor (Step 1) change ticket/artifact behavior.** All 7
  `TestTagRegistryEnforcement` tests and `test_tag_taxonomy_effective_date` must pass unmodified —
  any diff to those test files during implementation is itself a signal something went wrong in
  Step 1, since the refactor is designed to be behavior-preserving by construction (same inputs,
  same code path, just relocated into a shared helper). No other frontmatter field (`status`,
  `layer`, `authority`, `audience`) is touched by this ticket.
- **`last_verified` and `tags_enforced` are two distinct fields answering two distinct questions**
  (content freshness vs. tag-enforcement opt-in) — do not conflate them, do not reuse
  `last_verified` as a proxy for the new cutover signal anywhere in implementation, per
  investigation.md's explicit warning.
- **Canonical-form violations found in the live corpus (`Any`, `worldmodules`,
  `simulation_quality`) and high-frequency unregistered tags (`idea`, `contract`,
  `agent-infrastructure`, etc.) are evidence for a future, separately-scoped backfill ticket** — do
  not fold their fix into this ticket's commits, even opportunistically, per Decision 3 and the
  ticket's own Out of Scope.
- **The one known invalid doc layer (`social_memory_contract.md`) is a deliberately-left-open,
  documented, tested pre-existing condition, not a bug in this ticket's own change** — a future
  session fixing that file's `layer:` value will need to deliberately update
  `test_invalid_layer_doc_fixture_still_rejected`, which is the intended, visible signal (per
  investigation.md's Anti-Drift Hazards) rather than a silent pass-to-fail-to-pass flip.
- **No test in this plan may assert an exact violation count against the live `docs/` corpus** —
  Step 8's real-corpus run is a manual/Test-Summary-recorded verification, not a pytest assertion,
  per test_plan.md's explicit anti-drift guard mirroring `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s
  precedent (corpus counts grow over time and would make a hardcoded assertion flaky by design).

## Deviations (recorded during Implement)

- **Step 8's actual real-corpus run surfaced more total violations than this plan's estimate,
  but the tag-side result matched exactly.** This plan's Step 8 estimate ("0 new tag violations,
  exactly 1 layer violation") was scoped to `docs/REGISTRY.yaml`'s curated 397 `type: doc`
  entries (investigation.md's denominator). Running `python3 tools/validate_frontmatter.py docs/`
  directly against the raw `docs/` tree (851 `.md` files — a superset investigation.md did not
  separately re-measure, since no CI or prior tool run had ever invoked the validator
  comprehensively against `docs/` before this ticket) produced **355 total violations**, broken
  down as: 161 `status` (mostly `docs/archive/**`'s pre-existing missing/invalid values), 150
  `original_date` (all `docs/archive/**`, the archive content-type's own pre-existing required
  field), 22 `frontmatter` (files with no frontmatter block at all, mostly
  `docs/brainstorm/codex/**`), 19 `layer` (18 pre-existing `docs/archive/legacy_agents_skills_
  20260722/*/SKILL.md` missing-layer archive files + the 1 known
  `social_memory_contract.md` doc-layer violation this plan already predicted and pinned), 3
  `last_verified`, and **0 `tags`** — confirming the tag-side prediction exactly (no doc anywhere
  carries `tags_enforced`, so zero new tag violations, as designed).
- **None of the extra 336 violations (355 total minus the 19 already-accounted-for layer
  violations) are caused by, or touch code paths modified by, this ticket.** `status`,
  `original_date`, and `frontmatter`-block-presence checks are all pre-existing code
  (`_validate_archive`, `extract_frontmatter`) untouched by Steps 1-3, and `layer` enum-checking
  for `archive`/`doc` content types (`_check_enum(..., "layer", LAYER_VALUES)`) is also untouched.
  They are latent, already-existing corpus issues that were simply never surfaced before because
  no prior tool run ever validated the full raw `docs/` tree end-to-end (confirmed by
  investigation.md's "no CI workflow invokes `validate_frontmatter.py`" finding) — not a
  regression introduced by this ticket's tag-enforcement change. Per Step 8's own instruction and
  this plan's Scope Guards, none of these pre-existing violations were fixed as part of this
  ticket; AC #6's "bounded, understood violation count" is satisfied by having the exact breakdown
  above, not by the specific number matching the narrower pre-Implement estimate.
- No other deviation from this plan's Steps 1-7 occurred; all code and doc changes match the
  literal shapes specified above.
