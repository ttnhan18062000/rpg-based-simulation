---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260826-PARITY-FACTION-CANONICAL-SCAN
artifact_type: investigation
tags: [ai, workflows, faction, determinism]
---

# Investigation — TCK-20260826-PARITY-FACTION-CANONICAL-SCAN

## Current Behavior

**`tools/parity_ledger_scan.py`** (71 lines, read in full):
- `CANONICAL_LEDGER_FILES` (lines 32-41) is an 8-element tuple: `substrate.yaml`,
  `combat_movement.yaml`, `strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`,
  `social_narrative.yaml`, `world_dynamics.yaml`, `infrastructure.yaml`. `faction.yaml` is not a
  member — confirmed directly.
- `find_p0_intersection(files_changed, ledger_dir=...)` (lines 44-70) iterates only
  `CANONICAL_LEDGER_FILES`, loading each shard, filtering to `priority == "P0"` entries, and
  substring-matching `v2_evidence` against `files_changed`. `faction.yaml` is structurally never
  read by this function today.
- Module docstring (lines 1-19) states the exclusion rationale verbatim: "`faction.yaml` is
  excluded — not one of the 8, and has 0 P0 entries today". This premise is now false (see Parity
  Ledger Overlap below) — `docs/parity_ledger/faction.yaml`'s `FAC-013` entry (line 309) is
  `priority: P0`.

**`tools/gate_checks/parity_updater_static.py`** (204 lines, read in full): imports
`CANONICAL_LEDGER_FILES` from `parity_ledger_scan` (line 42) and uses it, unmodified, in three
functions:
- `derive_mapping` (lines 51-73) — builds `{src_path: {ledger_filenames}}` from every
  `v2_evidence` citation across `CANONICAL_LEDGER_FILES`. Any `src/*.py` path cited only in
  `faction.yaml`'s `v2_evidence` (e.g. `src/observability/event_extractor.py`, `src/engine/
  military_conflict.py`, `src/domains/faction/*.py`) is invisible to this mapping today.
- `expected_subsystems_for_files` (lines 76-90) and `cross_reference_touched` (lines 93-131) both
  consume `derive_mapping`'s output, so they inherit the same gap: a `src/` file whose only real
  parity coverage lives in `faction.yaml` is reported as `None`/`"NA"` — "no v2_evidence citation
  found in any canonical ledger file" — even when `faction.yaml` genuinely documents it.
- `next_available_id` (lines 134-163) takes an explicit `shard_filename` argument (not defaulted
  from `CANONICAL_LEDGER_FILES`) — confirmed unaffected by the tuple either way; already usable
  with `shard_filename="faction.yaml"` today (ticket's AC #7 correctly anticipates this).
- `search_existing_entries` (lines 166-203) *does* default-scan `CANONICAL_LEDGER_FILES` when
  `shard_filename` is omitted (line 175: `shards = [shard_filename] if shard_filename else
  CANONICAL_LEDGER_FILES`) — this call also inherits the fix automatically, matching the ticket's
  claim. It already accepts an explicit `shard_filename="faction.yaml"` override today too.

**`tools/gate_checks/mechanics_auditor_static.py`** (262 lines, read in full): imports
`CANONICAL_LEDGER_FILES` (line 30) and `expected_subsystems_for_files` from
`parity_updater_static` (line 31). Two functions are affected:
- `find_entry(entry_id, ledger_dir=...)` (lines 131-151) iterates `CANONICAL_LEDGER_FILES` only —
  today, `verify_entry_test_path`/`verify_entries`/`audit_verified_by_claims` all fail closed
  (`"entry {id} not found in any canonical ledger file"`) for any `faction.yaml` entry ID, e.g.
  `FAC-013`. Once the tuple fix lands, `find_entry` picks up `faction.yaml` automatically — no
  code change needed in this file, matching the ticket's claim that this cascades by import.
- `candidate_ledger_files_for_module` (lines 186-195) is a pass-through of
  `expected_subsystems_for_files` — inherits the same fix by the same chain.

**`docs/parity_ledger/faction.yaml`** (read in full, 439 lines, 15 entries: `FAC-001` through
`FAC-014` plus `FACTION-TENSION-001`). All 15 entries conform to `schema.json`'s required-field
and enum rules (checked field-by-field: `id` matches `^[A-Z]+-[0-9]{3}$` for every entry including
`FACTION-TENSION-001`; `status`/`priority`/`proof_type` values are all within the schema's
enums; every `verified`-status entry has non-null `v2_evidence` and `test_path` as the schema's
conditional `allOf` rule requires). No shard-specific parsing quirk found that would break
`next_available_id`'s max-numeric-suffix logic (`FAC-` prefix, 3-digit zero-padded suffixes,
highest is `FAC-014` → next available would correctly compute `FAC-015`) or
`search_existing_entries`'s substring scan.

**`.claude/workflows/implement-ticket.js`** (confirmed at line 1264): the Parity-phase agent
prompt string reads exactly:
```
Update docs/parity_ledger/ entries (files: substrate.yaml, combat_movement.yaml, strategic_cognition.yaml, town_resource.yaml, progression.yaml, social_narrative.yaml, world_dynamics.yaml, infrastructure.yaml).
```
— the same 8 filenames, hardcoded as prose, independent of the Python-side tuple. Two more
hardcoded `8` literals exist nearby in test fixtures (see Anti-Drift Hazards) that are NOT wired
to this string or to `CANONICAL_LEDGER_FILES` and would NOT auto-correct.

## Mechanics / Engine Constraints

This ticket does not touch simulation mechanics (`docs/mechanics/`) or engine contracts
(`docs/engine/`) — it is entirely meta-tooling around the parity-ledger governance layer itself.
The operative constraint is CLAUDE.md's own Authoritative Mechanics Rule / parity-ledger schema
rule: **"`P0` entries require a passing `test_path`"** — reflected mechanically in
`docs/parity_ledger/schema.json`'s conditional `allOf` block (lines 68-78: `priority == "P0"` →
`test_path` required) and in the intent of `find_p0_intersection` itself (module docstring:
"protecting a P0 entry from silently going stale"). `FAC-013` already satisfies the schema
(`test_path` is set, line 340-342) — the gap this ticket fixes is not a schema violation, it's
that the *tooling meant to guard P0 entries from going stale* cannot see this specific P0 entry at
all. No mechanics-law change is implied by fixing the tuple.

## Docs Requiring Update

None.

Four doc locations were checked directly for stale "canonical eight"/file-list prose that this fix
would invalidate, and none were found to require an update. `docs/parity_ledger/README.md` was
read in full (19 lines): it describes the ledger's role as sole authoritative tracking mechanism
and points to `tools/parity_ledger_writer.py`/`tools/parity_index.py`, but contains no file-list or
"8 canonical"/"canonical eight" language at all, so nothing there becomes stale. The three docs
`TCK-20260705-WORKFLOW-PARITY-SKIP` itself updated when it built the original 8-file skip logic —
`docs/ai/workflows.md`, `docs/ai/system_overview.md`, and `docs/ai/ticket-lifecycle.md` — were
grepped directly for "canonical", "eight", and the literal filename list; none contain it.
`docs/ai/system_overview.md` line 15's phrase "eight or more separate files" is an unrelated
sentence about doc-reading order, not the parity-ledger file count, confirmed by reading the
surrounding context rather than trusting the grep hit alone.

`docs/parity_ledger/faction.yaml` itself is explicitly Out of Scope per the ticket ("Renumbering,
editing, or re-verifying the content of any existing `faction.yaml` entry") — its content is
correct as-is and needs no edit; only the tooling that reads it changes.

## Parity Ledger Overlap

- **`FAC-013`** (`docs/parity_ledger/faction.yaml`, status `verified`, **priority `P0`**) — the
  entry motivating this ticket. `v2_evidence` cites `src/observability/event_extractor.py`.
  `test_path` is set (`tests/unit/observability/test_event_shapers_economy_faction.py`). This is
  the entry the ticket's AC #2 (`find_p0_intersection(["<FAC-013 evidence substring>"],
  ledger_dir="docs/parity_ledger")` should return a hit including `("faction.yaml", "FAC-013",
  ...)`) is written against — confirmed live: `"src/observability/event_extractor.py"` is a valid
  substring for that AC's test.
- `FAC-001` through `FAC-012`, `FAC-014`, `FACTION-TENSION-001` — all `status: verified`, priority
  P1/P2 (no other P0 entries in the shard, confirmed by reading every entry). These become visible
  to `derive_mapping`/`expected_subsystems_for_files`/`search_existing_entries` once the fix
  lands, but are irrelevant to `find_p0_intersection`'s P0-only filter either way.
- No other parity-ledger shard (`substrate.yaml`, `combat_movement.yaml`,
  `strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`, `social_narrative.yaml`,
  `world_dynamics.yaml`, `infrastructure.yaml`) is affected by this ticket's scope — they are
  already canonical and already scanned.
- This ticket makes no content change to any parity-ledger entry — it is a pure tooling fix, so no
  entry's `status`/`v2_evidence` needs updating as part of this work.

## Prior Work

- **`TCK-20260705-WORKFLOW-PARITY-SKIP`** (done, read in full) — built `find_p0_intersection` /
  `CANONICAL_LEDGER_FILES` as part of a Parity-phase skip-eligibility safeguard. Its own
  Implementation Notes confirm the 8-file scope was inherited from "the 8 canonical parity-ledger
  files" as a design given, not a `faction.yaml`-specific exclusion decision — the ticket's test
  file (`tests/tools/test_parity_ledger_scan.py`) explicitly names "canonical-8-only scan
  confirmation excluding `faction.yaml`" as one of its 3 original tests. Confirmed this ticket's
  fix does not reintroduce anything that ticket was solving: that ticket's actual safety property
  (skip the Parity agent call only when both `files_changed` has no `src/` path AND
  `behavior_changed` is false, checked against **post-Implement** signals, never Scope-time
  guesses) is entirely orthogonal to which files `find_p0_intersection` scans — widening the scan
  to include `faction.yaml` only strengthens that ticket's own stated goal ("protecting a P0 entry
  from silently going stale").
- **`TCK-20260731-PARITY-INDEX-IMPORTER`** / **`TCK-20260731-PARITY-INDEX-BASELINE`** — built the
  newer SQLite-backed `tools/parity_index.py`, confirmed (via `grep`) to already glob all 9 shards
  independent of `CANONICAL_LEDGER_FILES`. Its own comment even labels the legacy tuple "frozen
  8-file compatibility list" (`tools/parity_index_baseline.py` line 7) — this ticket does not
  touch that side, per its own Out of Scope.
- **`TCK-20260731-PARITY-IMPACT-PROOF`** (inferred from `tests/tools/test_parity_index.py`'s
  `TestEquivalenceFixtures`/`TestAllShardsCoverage` classes and
  `tests/tools/test_gate_a_readpath_review.py`'s corpus/adjudication machinery, both citing this
  ticket ID in comments) — this is the most consequential prior-work finding of this
  investigation; see Risks and Open Questions below. It built a large "Gate A" comparison corpus
  between the legacy tools and the new SQLite index, and its adjudication text
  (`_Adjudications.FACTION_EXCLUSION`, `test_gate_a_readpath_review.py` lines 339-344) states as
  established fact: *"faction.yaml is not a member of `CANONICAL_LEDGER_FILES`... both legacy
  surfaces are structurally blind to every `faction.yaml` entry regardless of priority."* This
  sentence becomes factually stale the moment this ticket's fix lands.

## Risks and Open Questions

- **Real gap in the ticket's own Scope enumeration — additional pinning tests exist beyond the 3
  files it names.** The ticket's Scope section says "Update every existing test that currently
  asserts the old exclusion as correct behavior" and explicitly calls out tests in
  `test_parity_ledger_scan.py`, `test_parity_index_baseline.py`, and `test_parity_index.py` ("Any
  other test in these three files..."). Direct reads found **two more tests, in two files not
  covered by that "these three files" audit instruction**, that also pin the old exclusion and
  will break once `faction.yaml` is added to `CANONICAL_LEDGER_FILES`:
  - `tests/tools/test_parity_updater_static.py::test_excludes_faction_yaml` (lines 90-99) —
    writes a `faction.yaml` fixture, calls `derive_mapping`, and asserts
    `"src/factions/diplomacy.py" not in mapping`. Once the tuple includes `faction.yaml`, this
    path WILL be in the mapping — the assertion inverts and the test fails.
  - `tests/tools/test_parity_index.py::TestEquivalenceFixtures::test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`
    (lines 1029-1063) — this one IS in one of the ticket's named files, but the ticket names only
    the class/one assertion; the same test body also asserts
    `"src/factions/diplomacy.py" not in legacy_mapping` (line 1050, via `derive_mapping`, not just
    `find_p0_intersection`) — this half of the test breaks too, even though the
    `find_p0_intersection` half (line 1048, `legacy_hits == []`) will *still* pass post-fix for an
    unrelated reason (the fixture entry's priority is `P1`, so `find_p0_intersection`'s P0-only
    filter excludes it regardless of which files are scanned) — the comment "Legacy exclusion:
    both comparison targets never see faction.yaml at all" becomes half-false and must be
    rewritten, not just re-verified.

    Both of these are real, currently-passing tests that pin the exact behavior this ticket
    inverts. This is not a hypothetical — it was found by reading the test bodies directly, not
    inferred. The Plan phase must add both to its file-audit list; the ticket's AC checklist item
    "no test in the repo still asserts... equivalent exclusion behavior" is not satisfiable without
    touching these two.

- **`tests/tools/test_parity_index_baseline.py::test_manifest_records_legacy_eight_shard_faction_gap`**
  (lines 84-87, in a file the ticket DOES name) is not called out individually in the ticket's
  Scope bullets (which name only `test_faction_fixture_matches_live_legacy_scan_output` and
  `test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture` from this
  file) but must also change: it asserts `manifest["excluded_from_legacy_scan"] == ["faction.yaml"]`.
  `tools/parity_index_baseline.py` line 146-147 computes that field as
  `sorted({shard["filename"] for shard in shards} - set(CANONICAL_LEDGER_FILES))` — once
  `faction.yaml` is added to the tuple, this becomes `[]` automatically (no code change needed in
  `parity_index_baseline.py` itself, consistent with the ticket's Out of Scope), but the test's
  hardcoded expected value must flip to `== []`.

- **`tests/tools/test_gate_a_readpath_review.py`'s `FACTION_EXCLUSION` adjudication text (lines
  339-344) becomes factually stale prose, but appears NOT to break any assertion** — traced this
  carefully since the ticket's AC pytest command includes this file. The adjudication is applied
  unconditionally for case `FAC-012` (line 392-393, no conditional gate), and every assertion that
  reads case `FAC-012`'s computed values compares against `_computed_index_impact_ids` (the new
  SQLite index's `impact()` output, which already includes `faction.yaml` independent of this
  ticket) rather than the legacy `find_p0_intersection`/`derive_mapping` outputs directly — so
  `recall`/`missing`/`discrepancy_adjudication`-presence assertions are unaffected by this fix.
  Two more hardcoded `8` literals exist in this same file (`"shards_scanned_legacy": 8` at line
  292, asserted at line 563; `"shards_scanned_legacy_total": 8 * len(corpus["real_cases"])` at
  line 456) — both are hardcoded integers, not derived from `CANONICAL_LEDGER_FILES`, so they
  stay internally self-consistent (test still passes) but become semantically wrong (claims 8
  shards scanned when the fix makes it 9). **Open question for Plan**: whether to leave this file
  untouched (ticket's Out of Scope doesn't explicitly cover it, and no test literally fails) or to
  do a minimal prose/literal correction since it is included in the ticket's own AC #6 pytest
  command and its adjudication text now describes a false premise as fact. Recommend flagging this
  to the ticket requester/Plan rather than assuming either answer — it's a real but non-blocking
  staleness, not a test failure, and the ticket's Out of Scope section is silent on it specifically
  (it only excludes `tools/parity_index.py`/`tools/parity_index_baseline.py` logic changes, not
  this test file's prose).

- **No other non-canonical `*.yaml` shard exists.** Confirmed via `ls docs/parity_ledger/*.yaml`:
  exactly `combat_movement.yaml, faction.yaml, infrastructure.yaml, progression.yaml,
  social_narrative.yaml, strategic_cognition.yaml, substrate.yaml, town_resource.yaml,
  world_dynamics.yaml` — the canonical 8 plus `faction.yaml` only. Ticket's assumption confirmed
  correct.

## Anti-Drift Hazards

- `implement-ticket.js` line 1264's hardcoded file-list prose is not the only hardcoded `8` in the
  repo tied to this concept — `test_gate_a_readpath_review.py` lines 292 and 456 (see Risks above)
  are two more, but they are self-referential literals inside that test file's own fixture-result
  construction, not read from `CANONICAL_LEDGER_FILES`. Do not assume fixing the Python tuple and
  the JS prompt string closes every hardcoded "8" in the repo — it does not, and this specific
  file's copies are arguably out of this ticket's scope (see Risks).
- `derive_mapping`'s `_SRC_PATH_RE` only ever extracts `src/*.py` paths from `v2_evidence` — a
  `tools/*.py` or `.claude/*.js` path cited in `faction.yaml`'s `v2_evidence` (none currently
  exist, checked) would still never appear in the mapping even after this fix. Do not scope-creep
  into "fix derive_mapping's path-prefix restriction" — that is a separate, pre-existing,
  previously-documented gap (`test_gate_a_readpath_review.py`'s `SRC_ONLY_SCOPE` adjudication)
  unrelated to the canonical-file-list gap this ticket fixes.
- `find_entry` in `mechanics_auditor_static.py` returns the *first* canonical file containing a
  matching `id` — if a future ID collision ever existed between `faction.yaml` and another shard
  (none exists today; every `FAC-*`/`FACTION-TENSION-*` ID is unique across all 9 shards, spot
  checked), the scan order (`faction.yaml` position within the now-9-element tuple) would
  determine which shard "wins." Do not silently reorder `CANONICAL_LEDGER_FILES` beyond appending
  `faction.yaml` — the ticket doesn't ask for a specific position, but appending (not inserting)
  is the lowest-risk choice since it preserves every existing index-order assumption in the 3
  consuming modules for the first 8 elements.
- `search_existing_entries` and `next_available_id` both already accept `shard_filename="faction.yaml"`
  today and are explicitly Out of Scope for code changes — do not "fix" them; only their
  *default*-scan behavior (no `shard_filename` given) changes, automatically, once the tuple is
  fixed.
