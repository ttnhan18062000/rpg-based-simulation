---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260826-PARITY-FACTION-CANONICAL-SCAN
artifact_type: plan
tags: [ai, workflows, faction, determinism]
---

# Implementation Plan — TCK-20260826-PARITY-FACTION-CANONICAL-SCAN

## Summary

Append `"faction.yaml"` to the single-source-of-truth `CANONICAL_LEDGER_FILES` tuple in
`tools/parity_ledger_scan.py` (confirmed at `tools/parity_ledger_scan.py:32-41`, an 8-tuple), which
by import automatically fixes `tools/gate_checks/parity_updater_static.py`'s `derive_mapping`
(`:51`), `expected_subsystems_for_files` (`:76`), `cross_reference_touched` (`:93`) and
`tools/gate_checks/mechanics_auditor_static.py`'s `find_entry`/`candidate_ledger_files_for_module`
— no code changes needed in either gate-checks file. Update the matching hardcoded prose in
`.claude/workflows/implement-ticket.js:1264`. Then rewrite the seven existing tests confirmed (by
direct read this session) to pin the old exclusion as correct behavior — one more than the
ticket's own Scope bullets name (`test_parity_updater_static.py::test_excludes_faction_yaml`,
confirmed at lines 90-99) and one more than that
(`test_parity_index_baseline.py::test_manifest_records_legacy_eight_shard_faction_gap`, confirmed
at lines 84-86) — plus add two new positive-coverage tests the ticket's ACs require (real `FAC-013`
P0 intersection; a static-prose guard on the `implement-ticket.js` string). Finally, correct the
now-factually-false `FACTION_EXCLUSION` adjudication string in
`tests/tools/test_gate_a_readpath_review.py` (confirmed at lines 339-344) — a design call made in
this plan (see Anti-Drift Notes) since it's cheap, self-referential (no other file duplicates the
string), and prevents a test file from asserting a now-false "fact" about the tooling it audits.
The two hardcoded `shards_scanned_legacy: 8` integer literals in that same file (lines 292, 456,
563) are deliberately left untouched — a separate, lower-value, higher-touch-count cleanup outside
this ticket's core fix, noted as a future micro-follow-up rather than silently left broken (it
isn't broken; it's a proxy metric that becomes cosmetically stale, not incorrect in any way a test
enforces as true today).

## Steps

### Step 1 — Add `faction.yaml` to `CANONICAL_LEDGER_FILES` and correct the module's stale docstrings
**Files:** `tools/parity_ledger_scan.py`
**Change:** Append `"faction.yaml"` as the 9th element of the `CANONICAL_LEDGER_FILES` tuple
(confirmed at `tools/parity_ledger_scan.py:32-41` — currently an 8-tuple ending
`"infrastructure.yaml",`). Append, do not insert or reorder — `mechanics_auditor_static.py`'s
`find_entry` (confirmed at `tools/gate_checks/mechanics_auditor_static.py:131-151`, per
investigation.md) returns the first canonical file containing a matching entry `id`; appending
preserves scan order for the existing 8 files and avoids any risk of changing which shard "wins" a
future ID collision (none exists today, confirmed by investigation). Also correct two now-false
prose spots in the same file: the module docstring (confirmed at `tools/parity_ledger_scan.py:7-9`,
"Scans only the 8 canonical parity-ledger files... `faction.yaml` is excluded — not one of the 8,
and has 0 P0 entries today") and `find_p0_intersection`'s own docstring (confirmed at
`tools/parity_ledger_scan.py:49`, "Only scans CANONICAL_LEDGER_FILES — never `faction.yaml`...").
Rewrite both to state the tuple now has 9 members including `faction.yaml`, and drop the "0 P0
entries" claim (now false — `FAC-013` is P0, confirmed in investigation.md's Parity Ledger Overlap
section).
**Do NOT touch:** `find_p0_intersection`'s function body/control flow (lines 44-70) — it already
iterates `CANONICAL_LEDGER_FILES` generically; no logic change is needed, only the tuple's
contents. Do not touch `tools/parity_index.py` or `tools/parity_index_baseline.py` (ticket's
explicit Out of Scope) — `parity_index_baseline.py:146-147`'s `excluded_from_legacy_scan` field
(`sorted({shard["filename"] for shard in shards} - set(CANONICAL_LEDGER_FILES))`, confirmed by
direct read) recomputes to `[]` automatically once this step lands, with zero code change there.
**Verify:** `pytest tests/tools/test_parity_ledger_scan.py::test_reuses_canonical_ledger_files_constant`
(note: this specific test actually lives in `test_parity_updater_static.py`, see Step 5's Verify)
is not the check for this step — this step's own correctness is proven by Steps 3 and 4's tests
passing, since editing the tuple with no rewritten tests would leave Step 3 failing.

### Step 2 — Update the Parity-phase prompt string in `implement-ticket.js`
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** At the line confirmed at `.claude/workflows/implement-ticket.js:1264`, change:
`Update docs/parity_ledger/ entries (files: substrate.yaml, combat_movement.yaml,
strategic_cognition.yaml, town_resource.yaml, progression.yaml, social_narrative.yaml,
world_dynamics.yaml, infrastructure.yaml).`
to append `, faction.yaml` before the closing paren, listing all 9 files. This is a plain prose
string inside a template literal (confirmed by direct read — the line sits inside the
`implementation.behavior_changed ? \`Update docs/parity_ledger/...\`` conditional block) with no
other code around it referencing the file count, so this is a pure string edit.
**Do NOT touch:** The surrounding rules block (`behavior matches Mechanics Bible → status=verified
...`, confirmed immediately below the file-list line) — those rules are unrelated to which files
are listed and already apply generically to any target file including `faction.yaml`. Do not touch
`expectedSubsystemsOutput` / `nextIdOutput` template variables on the lines above (confirmed at the
same read) — they are computed by `parity_updater_static.py` functions that already inherit the fix
by import (Step 1), no JS-side change needed for them.
**Verify:** New static-prose test from Step 10 (`"faction.yaml" in` the prompt string content).

### Step 3 — Rewrite `test_parity_ledger_scan.py::test_only_scans_canonical_eight_not_faction`
**Files:** `tests/tools/test_parity_ledger_scan.py`
**Change:** Confirmed at lines 52-62: the test currently writes a synthetic `faction.yaml` P0
fixture, calls `find_p0_intersection`, and asserts `hits == []` and
`"faction.yaml" not in CANONICAL_LEDGER_FILES`. Invert both assertions: after Step 1,
`find_p0_intersection(["src/factions/diplomacy.py"], ledger_dir=str(tmp_path))` against that same
fixture must return `[("faction.yaml", "FAC-001", "src/factions/diplomacy.py")]`, and
`"faction.yaml" in CANONICAL_LEDGER_FILES` must be true. Rename the test to
`test_scans_canonical_nine_including_faction` (old name asserts a now-false premise; keeping the
old name with inverted body would be misleading to future readers, matching the project's
naming-for-behavior convention).
**Do NOT touch:** The other three tests in this file
(`test_detects_p0_intersection_via_synthetic_fixture`, confirmed lines 23-34;
`test_no_intersection_for_representative_docs_only_change`, lines 37-40;
`test_find_p0_intersection_malformed_shard_raises_labeled_error_not_crash`, lines 43-49) — all
three are unaffected by the tuple's contents and must keep passing unmodified per test_plan.md's
Regression Surface.
**Verify:** `pytest tests/tools/test_parity_ledger_scan.py -v` — all 4 tests pass (3 unmodified + 1
rewritten).

### Step 4 — Add a positive-control test against the real `FAC-013` P0 entry (ticket AC #2)
**Files:** `tests/tools/test_parity_ledger_scan.py`
**Change:** Add a new test exercising the real ledger (not a synthetic fixture), mirroring the
existing negative-control pattern in `test_no_intersection_for_representative_docs_only_change`
(lines 37-40) but as a positive control:
```python
def test_detects_real_fac013_p0_intersection():
    hits = find_p0_intersection(
        ["src/observability/event_extractor.py"], ledger_dir="docs/parity_ledger"
    )
    assert ("faction.yaml", "FAC-013", "src/observability/event_extractor.py") in hits
```
Use `in hits` rather than `hits == [...]` in case another canonical shard's P0 entry also happens
to cite a substring of that same path (avoids a brittle exact-list assertion for a real,
non-synthetic ledger that can grow independently of this ticket). `FAC-013`'s `v2_evidence` citing
`src/observability/event_extractor.py` and its `P0` priority are both confirmed directly in
investigation.md's Parity Ledger Overlap section (`docs/parity_ledger/faction.yaml`, entry at line
~309-342, `status: verified`, `test_path` set).
**Do NOT touch:** Do not assert an exact `hits == [...]` list against the live ledger — the real
`docs/parity_ledger` directory is mutable by other tickets over time (unlike a `tmp_path` fixture),
so an exact-list assertion here would be a hidden coupling to the ledger's current total P0 count,
which is out of this ticket's control.
**Verify:** `pytest tests/tools/test_parity_ledger_scan.py::test_detects_real_fac013_p0_intersection -v`.

### Step 5 — Rewrite `test_parity_updater_static.py::test_excludes_faction_yaml`
**Files:** `tests/tools/test_parity_updater_static.py`
**Change:** Confirmed at lines 90-99: the test writes a synthetic `faction.yaml` fixture (`FAC-001`,
P1, `v2_evidence: "src/factions/diplomacy.py"`), calls `derive_mapping(tmp_path)`, and asserts
`"src/factions/diplomacy.py" not in mapping`. Invert to
`mapping["src/factions/diplomacy.py"] == {"faction.yaml"}` (matching the existing sibling test's
assertion shape at lines 86-87, `mapping["src/town/harvest.py"] == {"town_resource.yaml"}`). Rename
to `test_includes_faction_yaml`. `derive_mapping`'s signature is confirmed unchanged at
`tools/gate_checks/parity_updater_static.py:51` (`derive_mapping(ledger_dir: "Path | str" =
"docs/parity_ledger") -> dict`) — this step touches only the test, no production code.
**Do NOT touch:** `test_reuses_canonical_ledger_files_constant` (confirmed lines 102-105, identity
check `CANONICAL_LEDGER_FILES is SCAN_CANONICAL_LEDGER_FILES`) — must keep passing unmodified; it
is the anti-drift guard against a future fix that defines a second, parallel tuple instead of
appending to the one shared source of truth. Do not touch any `derive_mapping` /
`expected_subsystems_for_files` / `cross_reference_touched` / `next_available_id` /
`search_existing_entries` test below line 110 in this file — all must keep passing unmodified per
test_plan.md's Regression Surface (this also verifies ticket AC #7 — `next_available_id` and
`search_existing_entries` continue to work unchanged).
**Verify:** `pytest tests/tools/test_parity_updater_static.py -v` — full file green.

### Step 6 — Add `expected_subsystems_for_files` real-ledger coverage test (ticket AC #3)
**Files:** `tests/tools/test_parity_updater_static.py`
**Change:** Add a new test proving the real (non-synthetic) ledger case:
```python
def test_expected_subsystems_includes_faction_for_real_ledger_path():
    result = expected_subsystems_for_files(
        ["src/observability/event_extractor.py"], ledger_dir="docs/parity_ledger"
    )
    assert result["src/observability/event_extractor.py"] is not None
    assert "faction.yaml" in result["src/observability/event_extractor.py"]
```
`expected_subsystems_for_files`'s signature is confirmed at
`tools/gate_checks/parity_updater_static.py:76` (`expected_subsystems_for_files(files_changed,
ledger_dir="docs/parity_ledger") -> dict`). Before Step 1, this path returns `None` for that key
(no canonical-file citation found); after Step 1, `faction.yaml`'s `FAC-013` citation makes it
non-`None` and includes `"faction.yaml"` in the candidate list. This is the same real `src/` path
used in Step 4, keeping the two positive-control tests correlated to the same investigated evidence
rather than inventing a second unverified path.
**Do NOT touch:** Do not assert an exact list value (e.g. `== ["faction.yaml"]`) — if another
canonical shard also happens to cite this path in the future, an exact-list assertion would be a
false failure unrelated to this ticket's fix; `in` membership is the correct check here, matching
Step 4's reasoning.
**Verify:** `pytest tests/tools/test_parity_updater_static.py::test_expected_subsystems_includes_faction_for_real_ledger_path -v`.

### Step 7 — Rewrite the three affected tests in `test_parity_index_baseline.py`
**Files:** `tests/tools/test_parity_index_baseline.py`
**Change:** Three tests confirmed by direct read:
1. `test_manifest_records_legacy_eight_shard_faction_gap` (confirmed lines 84-86): asserts
   `manifest["excluded_from_legacy_scan"] == ["faction.yaml"]`. Change to `== []` and rename to
   `test_manifest_records_no_legacy_shard_gap`. No production-code change needed —
   `parity_index_baseline.py:146-147`'s `excluded_from_legacy_scan` field is computed as
   `sorted({shard["filename"] for shard in shards} - set(CANONICAL_LEDGER_FILES))` (confirmed by
   direct read), which resolves to `[]` automatically once Step 1 lands.
2. `test_faction_fixture_matches_live_legacy_scan_output` (confirmed lines 144-147): asserts
   `find_p0_intersection(["src/factions/diplomacy.py"], ledger_dir=str(FIXTURES_DIR /
   "faction_case")) == []`. Read the fixture file
   `tests/tools/fixtures/parity_index_baseline/faction_case/faction.yaml` first to confirm its
   entry's `id`/`priority` before writing the new expected-hit tuple (the ticket's Scope names this
   fixture but investigation did not cite its exact contents — confirm before asserting the exact
   tuple value, do not guess the entry `id`). Invert `== []` to the real expected hit list once
   confirmed. Do not rename unless the fixture's data makes the old name factually wrong (name
   describes matching legacy-vs-live behavior, which still holds after inversion — likely no rename
   needed here, only the asserted value).
3. `test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture` (confirmed
   lines 169-177): asserts `"faction.yaml" in filenames` (manifest shard list — stays true,
   untouched) AND `find_p0_intersection(...) == []` AND `"faction.yaml" not in
   CANONICAL_LEDGER_FILES` (both now false). Flip the `hits` assertion to match sub-step 2's
   confirmed real value and flip `not in` to `in`. Rename to
   `test_faction_yaml_included_in_manifest_shard_list_and_legacy_fixture` (drop "but_excluded" — no
   longer true).
**Do NOT touch:** Every other test in this file — manifest determinism/coverage, source-hash,
entry-count-drift, no-mutation guard, missing-`test_path` count, unmapped/multi-shard/malformed-yaml
fixture tests, V1 decision-doc completeness, anti-scope-creep guards (per test_plan.md's Regression
Surface, all must keep passing unmodified). Do not touch
`tests/tools/fixtures/parity_index_baseline/faction_case/faction.yaml` itself — only the test
assertions that read it change, not the fixture data (ticket's Out of Scope: no ledger-content
edits).
**Verify:** `pytest tests/tools/test_parity_index_baseline.py -v` — full file green.

### Step 8 — Partially rewrite `test_parity_index.py`'s legacy-exclusion equivalence test
**Files:** `tests/tools/test_parity_index.py`
**Change:** Confirmed at lines 1029-1063
(`TestEquivalenceFixtures::test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`).
The test builds a synthetic corpus with a `faction.yaml` entry `FAC-801` (priority `P1`,
`v2_evidence` citing `src/factions/diplomacy.py`). Two assertions on the "legacy" half (lines
1045-1050):
- `legacy_hits = find_p0_intersection(["src/factions/diplomacy.py"], ledger_dir=...)` then
  `assert legacy_hits == []` (line 1048) — **leave this assertion as-is**; it stays `[]` after Step
  1, but now because `FAC-801`'s priority is `P1` (P0-only filter excludes it), not because
  `faction.yaml` is unscanned. Update the inline comment above it (currently "Legacy exclusion:
  both comparison targets never see faction.yaml at all", line 1044) to state the real reason it
  still returns `[]` post-fix, since the old comment becomes half-false.
- `legacy_mapping = derive_mapping(...)` then `assert "src/factions/diplomacy.py" not in
  legacy_mapping` (line 1050) — **invert this one**: after Step 1, `derive_mapping` now includes
  this path (keyed to `{"faction.yaml"}`), so change to
  `assert legacy_mapping["src/factions/diplomacy.py"] == {"faction.yaml"}`.
Leave the "new index" half (lines 1052-1063: `_pi.build`, `_pi.entry`, `_pi.impact` assertions)
completely unchanged — confirmed unaffected, `tools/parity_index.py` is Out of Scope and was
already `faction.yaml`-inclusive before this ticket. Consider renaming the test to
`test_faction_evidence_case_present_in_both_legacy_and_new_index` since "despite_legacy_exclusion"
no longer describes reality.
**Do NOT touch:** `TestAllShardsCoverage::test_impact_and_entry_cover_all_nine_shards_including_faction`
or any other `_pi.*` (SQLite index) test in this file — all must keep passing byte-for-byte
unmodified, per test_plan.md's explicit Anti-Drift Test Guard (regression proof that
`tools/parity_index.py` itself was not touched).
**Verify:** `pytest tests/tools/test_parity_index.py -v` — full file green, including the untouched
`TestAllShardsCoverage` class.

### Step 9 — Correct the stale `FACTION_EXCLUSION` adjudication prose in `test_gate_a_readpath_review.py`
**Files:** `tests/tools/test_gate_a_readpath_review.py`
**Change:** Design call (see Anti-Drift Notes for rationale): update the `FACTION_EXCLUSION` string
constant confirmed at lines 339-344 — currently states as fact "faction.yaml is not a member of
CANONICAL_LEDGER_FILES (tools/parity_ledger_scan.py:24-33) -- both legacy surfaces are structurally
blind to every faction.yaml entry regardless of priority" — which becomes false once Step 1 lands.
Rewrite the string to describe the corrected state, e.g.: "faction.yaml was historically excluded
from CANONICAL_LEDGER_FILES (fixed by TCK-20260826-PARITY-FACTION-CANONICAL-SCAN); legacy surfaces
now see faction.yaml like any other canonical shard; impact() included faction.yaml even before
that fix." Confirmed via `grep -n "FACTION_EXCLUSION" tests/tools/test_gate_a_readpath_review.py`
that this constant is referenced exactly once elsewhere (line 393, `self.FACTION_EXCLUSION`,
inside `apply()`'s per-case adjudication assignment for case `FAC-012`) — a single self-referential
attribute, so editing its string value requires no other file or line to change in lockstep. Do not
rename the `FACTION_EXCLUSION` class attribute itself — renaming has no test benefit (nothing
outside this file references the name) and only adds unnecessary diff surface.
**Do NOT touch:** The two `"shards_scanned_legacy": 8` integer literals (confirmed at lines 292 and
456) or their matching assertion (line 563,
`record["analyst_effort_proxy"]["shards_scanned_legacy"] == 8`) — deliberately left as a separate,
lower-value cleanup (see Anti-Drift Notes). Do not touch any other adjudication constant in this
class (`P0_ONLY_FILTER`, `SRC_ONLY_SCOPE`, `DOT_CLAUDE_PREFIX_GAP`, `MALFORMED_SHARD_THREE_WAY`,
`ANY_OF_MULTI_SHARD`) or the `apply()` method's case-routing logic — none reference
`CANONICAL_LEDGER_FILES`'s contents and none become stale from this fix.
**Verify:** `pytest tests/tools/test_gate_a_readpath_review.py -v` — full file green (no assertion
was failing before this step and none is expected to fail after; this step is a prose-accuracy fix,
confirmed by investigation to have zero assertion-level impact).

### Step 10 — Add a static-prose guard test on `implement-ticket.js`'s Parity-phase file list (ticket AC #4)
**Files:** new file `tests/tools/test_parity_prompt_ledger_file_list.py`
**Change:** Confirmed by search (`grep -rl "implement-ticket.js" tests/tools/` and a direct grep for
the file-list prose string) that no existing test file asserts against this specific prompt string
today. Add a new, narrowly-scoped test that reads `.claude/workflows/implement-ticket.js` as text
and asserts the Parity-phase file-list line contains all 9 canonical filenames including
`faction.yaml`, e.g.:
```python
from pathlib import Path

_JS_PATH = Path(__file__).parent.parent.parent / ".claude" / "workflows" / "implement-ticket.js"


def test_parity_phase_prompt_lists_all_nine_canonical_files():
    source = _JS_PATH.read_text()
    assert "Update docs/parity_ledger/ entries (files:" in source
    for filename in (
        "substrate.yaml", "combat_movement.yaml", "strategic_cognition.yaml",
        "town_resource.yaml", "progression.yaml", "social_narrative.yaml",
        "world_dynamics.yaml", "infrastructure.yaml", "faction.yaml",
    ):
        assert filename in source
```
This mirrors the existing pattern of other `tests/tools/test_*_wiring.py` files that assert against
`implement-ticket.js`'s static text content (e.g. `test_document_update_phase_wiring.py`,
`test_doc_staleness_gate_wiring.py`, confirmed present in the directory listing) rather than
executing the JS file.
**Do NOT touch:** Any existing `tests/tools/test_*wiring*.py` file — this is a new, separate file,
not an addition to an existing one, since none of the existing wiring tests cover this specific
prompt string (confirmed by grep).
**Verify:** `pytest tests/tools/test_parity_prompt_ledger_file_list.py -v`.

## Scope Guards

- Do not modify `tools/parity_index.py` or `tools/parity_index_baseline.py` logic — both already
  scan all 9 shards independent of `CANONICAL_LEDGER_FILES` (ticket's explicit Out of Scope).
  `parity_index_baseline.py`'s `excluded_from_legacy_scan` computation is read-only reused, not
  edited, in Step 7.
- Do not edit, renumber, or re-verify any entry in `docs/parity_ledger/faction.yaml`, including
  `FAC-013`'s `P0` status or `v2_evidence` — ticket's explicit Out of Scope. This plan only changes
  tooling that reads the ledger, never the ledger's content.
- Do not add any other non-canonical `*.yaml` file under `docs/parity_ledger/` to
  `CANONICAL_LEDGER_FILES` — confirmed via `ls docs/parity_ledger/*.yaml` that `faction.yaml` is the
  only non-canonical shard present today.
- Do not build a merge-conflict guard or ID-collision CI check for `docs/parity_ledger/*.yaml` —
  that is `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`'s scope, a separate backlog ticket.
- Do not modify `next_available_id` or `search_existing_entries`'s function bodies in
  `tools/gate_checks/parity_updater_static.py` — both already accept an explicit `shard_filename`
  override and need no code change; only their *default*-scan behavior changes automatically via
  the Step 1 tuple edit.
- Do not reorder `CANONICAL_LEDGER_FILES` — append `faction.yaml` as the 9th element only (Step 1
  rationale: preserves `find_entry`'s first-match-wins scan order for the existing 8 files).
- Do not touch the two `shards_scanned_legacy: 8` integer literals or their matching assertion in
  `tests/tools/test_gate_a_readpath_review.py` (lines 292, 456, 563) — deliberately deferred, see
  Anti-Drift Notes.
- Do not touch `derive_mapping`'s `_SRC_PATH_RE` path-prefix restriction (only matches `src/*.py`) —
  a separate, pre-existing, previously-documented gap unrelated to this ticket's file-set fix.
- Never run `pytest tests/` in full — this ticket's blast radius is fully contained within
  `tests/tools/` (per test_plan.md).

## Dependency Map

- Step 1 (tuple + docstring fix) must land before Steps 3, 4, 5, 6, 7, 8 — every rewritten/new test
  in those steps asserts against post-fix behavior and will fail (or fail to demonstrate anything
  meaningful) if run against the pre-fix tuple.
- Step 2 (JS prompt string) is independent of Step 1 — can be done in either order relative to it —
  but must land before Step 10 (its verifying test).
- Steps 3 and 4 both touch `test_parity_ledger_scan.py` — independent of each other (different
  tests) but naturally sequenced together since they're in the same file.
- Steps 5 and 6 both touch `test_parity_updater_static.py` — independent of each other, same file.
- Step 7's three sub-changes are independent of each other but share one file
  (`test_parity_index_baseline.py`); sub-step 2 requires reading the `faction_case` fixture file
  first (see Step 7's Change text) before its exact assertion value can be written.
- Step 8 is independent of Steps 3-7 (different file) but depends on Step 1 like all test-rewrite
  steps.
- Step 9 is independent of every other step — a self-contained prose edit in a file whose
  assertions are already unaffected by Step 1 (confirmed by investigation).
- Step 10 depends only on Step 2 (verifies its output), not on Step 1.
- All steps are otherwise safely reorderable/parallelizable except the Step 1 → {3,4,5,6,7,8}
  ordering constraint above.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `"faction.yaml" in CANONICAL_LEDGER_FILES` is true | Step 1 | Step 3's rewritten test; Step 5's `test_reuses_canonical_ledger_files_constant` (unmodified, confirms single source of truth) |
| `find_p0_intersection` returns real `FAC-013` hit | Step 1 | Step 4's `test_detects_real_fac013_p0_intersection` |
| `expected_subsystems_for_files`/`derive_mapping` include `faction.yaml` for `src/` paths | Step 1 | Step 5's rewritten `test_includes_faction_yaml`; Step 6's `test_expected_subsystems_includes_faction_for_real_ledger_path` |
| `implement-ticket.js` Parity-phase prompt lists `faction.yaml` alongside the other 8 | Step 2 | Step 10's `test_parity_phase_prompt_lists_all_nine_canonical_files` |
| All pre-existing tests asserting old exclusion are updated/removed | Steps 3, 5, 7, 8 (Step 9 as a design-call bonus, not itself an exclusion assertion) | Full scoped pytest run (see below) — no remaining `"faction.yaml" not in CANONICAL_LEDGER_FILES` or equivalent assertion anywhere in the repo |
| `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py tests/tools/test_gate_a_readpath_review.py` passes | Steps 1-9 collectively | Direct run of that exact command as final verification |
| `next_available_id`/`search_existing_entries` continue to work unchanged | (no step changes them — Out of Scope) | Unmodified tests below line 110 in `test_parity_updater_static.py`, confirmed passing per Step 5's Do NOT touch |

## Anti-Drift Notes

- **Design call on `test_gate_a_readpath_review.py`'s stale prose (Step 9): fix it.** Investigation
  confirmed no assertion in that file breaks either way — the `FACTION_EXCLUSION` string is applied
  unconditionally to case `FAC-012` and every downstream assertion compares against
  `_computed_index_impact_ids` (the SQLite index's `impact()` output, already `faction.yaml`-
  inclusive independent of this ticket), not against the string's content or against
  `find_p0_intersection`/`derive_mapping` directly. Given that, the fix is genuinely optional from a
  pure "does the AC #6 pytest command pass" standpoint. This plan chooses to fix it anyway because:
  (1) it is a single self-referential string constant (confirmed via grep — referenced exactly once
  elsewhere in the file), so the edit carries no lockstep-update risk; (2) the string is literally
  named `FACTION_EXCLUSION` and asserted into a test corpus's adjudication record as an
  "established fact" about the tooling this exact ticket changes — leaving it would mean a test
  file governing readpath-parity claims about `CANONICAL_LEDGER_FILES` asserts something false
  about `CANONICAL_LEDGER_FILES` the moment this ticket merges, which is the kind of undocumented
  staleness CLAUDE.md's traceability discipline exists to prevent; (3) the ticket's own AC #6
  explicitly includes this file in its pytest command, signaling the requester considers it in-scope
  for verification, even though the ticket's Out of Scope section is silent on prose edits within it.
  The two `shards_scanned_legacy: 8` integer literals are deliberately NOT touched in the same step
  — they require a 3-location lockstep edit (lines 292, 456, and the assertion at 563) for a
  cosmetic proxy-metric correction with no "asserts a false fact" character (the field is already
  labeled `analyst_effort_proxy`, signaling it's an approximation, not a factual claim), so the
  cost/benefit tips the other way. If this bothers a future reader, it's a two-minute standalone
  hotfix ticket, not worth folding into this one.
- **`derive_mapping`'s `_SRC_PATH_RE` restriction is out of scope and must not be touched.** It only
  ever extracts `src/*.py` paths from `v2_evidence`; a `tools/*.py` or `.claude/*.js` path cited in
  `faction.yaml`'s `v2_evidence` (none currently exist, confirmed by investigation) would still
  never appear in the mapping even after this fix. This is a separate, pre-existing,
  previously-documented gap (`test_gate_a_readpath_review.py`'s `SRC_ONLY_SCOPE` adjudication,
  confirmed present at a different location in the same file) — do not scope-creep into fixing it.
- **Append-only tuple discipline.** `find_entry` in `mechanics_auditor_static.py` (confirmed lines
  131-151 per investigation) returns the first canonical file containing a matching entry `id`.
  Appending `faction.yaml` (not inserting elsewhere) preserves every existing index-order assumption
  for the first 8 elements. No ID collision exists today between `faction.yaml` and any other shard
  (spot-checked by investigation), but the append-only rule is the correct general discipline
  regardless.
- **`search_existing_entries`/`next_available_id` are Out of Scope for code changes.** Both already
  accept `shard_filename="faction.yaml"` explicitly today; only their *default*-scan behavior (no
  `shard_filename` given) changes automatically once Step 1 lands. Confirm via the unmodified tests
  below line 110 in `test_parity_updater_static.py`, do not add new code paths to either function.
- **Exact-list vs. membership assertions against the real ledger.** Steps 4 and 6 deliberately use
  `in` / non-`None` membership checks rather than exact-list equality when asserting against the
  live `docs/parity_ledger` directory (not a `tmp_path` fixture), since that directory can grow new
  P0 entries from unrelated future tickets — an exact-list assertion there would create a hidden,
  unintended coupling. Exact-list/exact-set assertions remain correct and are used for all
  `tmp_path`-fixture-based tests (Steps 3, 5, 7 sub-step 2), which are fully controlled by the test
  itself.

## Deviations

Implemented as written — all 10 steps landed exactly as planned, with one addition:

- **Added Step 11 (not in this plan's original 10 steps)**: the Implement-phase task carried an
  advisory note from Plan-review, applied because it was cheap and worthwhile: add a small positive
  test asserting `mechanics_auditor_static.find_entry("FAC-013", ledger_dir="docs/parity_ledger")`
  now returns `(entry, "faction.yaml")` instead of `(None, None)`, mirroring this plan's Step 4/6
  real-ledger pattern for the other two functions (`find_p0_intersection`,
  `expected_subsystems_for_files`) that consume `CANONICAL_LEDGER_FILES` by import.
  `find_entry` — the third consumer, in `tools/gate_checks/mechanics_auditor_static.py` — had no
  dedicated real-ledger positive-control test anywhere in Steps 1-10, which was a genuine coverage
  gap this plan itself did not catch. Added
  `test_find_entry_locates_real_fac013_in_faction_yaml` to
  `tests/tools/test_mechanics_auditor_static.py`. No other deviation from this plan occurred; every
  file listed in Steps 1-10's "Files" lines was touched exactly as described, and no file outside
  that set (plus this one addition) was modified.
