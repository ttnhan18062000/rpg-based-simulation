---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-IMPACT-PROOF
artifact_type: investigation
tags: [ai, observability, process-improvement, testing]
---

# Investigation — TCK-20260731-PARITY-IMPACT-PROOF

## Current Behavior

### `tools/parity_index.py` (read in full, 482 lines) — Phase 1 importer, confirmed no read-CLI exists

Directly verified (grep, not assumed): the only `argparse` subparser registered is `build`
(`main()`, line 465-471: `subparsers.add_parser("build", ...)`). There is no `impact`, `entry`,
`search`, or `health` subcommand and no equivalently-named top-level function in the module —
`grep -n "add_parser\|def entry\|def health\|def impact"` returns only the `build` parser
registration and the module docstring's prose reference to "Phase-2 impact query view" (line 34).
**This confirms the ticket's premise: this Phase-2 ticket must build the `impact`/`entry`/`health`
surface fresh; nothing pre-exists to extend.**

Tables/columns this ticket's read functions must query (all populated by `build()`, `_build_into()`
line 356-412):
- `entries` (line 139-155): `id` (PK), `shard`, `subsystem`, `entry_order`, `text`, `status`,
  `priority`, `legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`, `divergence_note`,
  `support_boundary`, `canonical_fragment_hash`.
- `code_refs` / `test_refs` / `constraint_refs` / `ticket_refs` (line 157-168, `_REF_TABLES`):
  `(id, entry_id, path, relation, source_field)`. `relation` is currently always `None` or
  `"declared"` (only `test_refs` rows inserted directly from `test_path` get `relation="declared"`,
  `_populate_ref_tables` line 258; all regex-matched rows get `relation=None`, line 270/272/274/279)
  — **an `impact` query's "selection reason" cannot rely on a populated `relation` column alone**;
  it must be synthesized from which table matched and `source_field`, not read as a pre-existing
  reason string.
- `entry_health` (line 171-177, materialized table): `(entry_id, finding_type, detail)`, finding
  types `missing_test_path`, `missing_v2_evidence`, `legacy_unstructured`, `absent_file`
  (`_populate_entry_health`, line 282-319). This is the direct data source for the `health`
  subcommand — no new classification logic is needed, only a query/formatting layer, per the
  ticket's own Scope ("classify malformed/missing/legacy-unstructured inputs through health output
  ... without inventing a relationship").
- `entry_fts` (only when `fts5_available`, line 178-181, populated line 322-329): standalone FTS5
  virtual table, discovery-only per `v1_decisions_phase0.md`. `impact`/`entry`/`health` must never
  depend on this table's existence — Phase 1's own `test_fts5_forced_unavailable_falls_back_to_exact_lookup`
  already proves exact lookups work without it, and this ticket's Scope excludes `search`/FTS
  entirely (the idea doc's CLI sketch includes `parity-index search`, but the ticket's own quoted
  CLI spec and Scope text list only `impact`, `entry`, `health` — `search` stays out of this ticket).
- `ledger_generation`: one row per build, `(schema_version, importer_version, built_at,
  source_manifest_hash, shard_manifest_json, shard_count, entry_count, fts5_available)`. Read-only
  metadata source for e.g. a `health` summary header; not itself queried by path/entry/test.

Existing helper functions directly reusable (do not reimplement): `serialize_manifest` (imported
from `tools/parity_index_baseline.py`, line 56) is already the JSON-output convention this ticket's
new subcommands must reuse for machine-readable output (`sort_keys=True, indent=2,
ensure_ascii=True` + trailing newline, per `v1_decisions_phase0.md`'s "Output convention" section).
`_REPO_ROOT` (line 52) is already computed and is the correct base for any path-existence check an
`impact`/`health` query needs (mirroring `_populate_entry_health`'s own `absent_file` check, line
316: `(_REPO_ROOT / path).exists()`).

### `tools/parity_ledger_scan.py::find_p0_intersection` (read in full, 59 lines) — legacy comparison target #1

`find_p0_intersection(files_changed, ledger_dir="docs/parity_ledger")` (line 36-59): iterates only
`CANONICAL_LEDGER_FILES` (8-file tuple, line 24-33, excludes `faction.yaml`), filters to
`priority == "P0"` only (line 51 — **not** all-priority), does a raw Python substring check
(`changed_path in evidence`, line 57) against `v2_evidence` only (never `legacy_evidence` or
`text`), and returns a flat list of `(filename, entry_id, changed_path)` triples with **no
dedup, no ordering guarantee, and no explicit "no match" record** — an empty list is
indistinguishable between "checked and found nothing" and "nothing to check." This is the P0-
substring behavior the ticket's equivalence corpus must capture as legacy comparison evidence,
labeling the new index's all-priority, ANY-field (`v2_evidence`/`legacy_evidence`/`text`),
regex-anchored (not substring) behavior as an intentional, documented difference.

`tests/tools/test_parity_ledger_scan.py` (3 tests, confirmed passing): `test_only_scans_canonical_eight_not_faction`
is the direct fixture proof of the faction-exclusion behavior this ticket's faction evidence case
must contrast against.

### `tools/gate_checks/parity_updater_static.py::cross_reference_touched` (read in full, 120 lines) — legacy comparison target #2

`derive_mapping` (line 39-61) builds `{src_path: {ledger_filenames}}` from a regex
(`_SRC_PATH_RE = re.compile(r"src/[\w\-./]+\.py")`, line 36) applied to `v2_evidence` only, scanning
only `CANONICAL_LEDGER_FILES` (imported **by identity** from `parity_ledger_scan`, line 34 — the
sibling test `test_reuses_canonical_ledger_files_constant` enforces `is`, not `==`). A path cited in
2+ canonical files accumulates all of them into a `set` (line 60) — this is the "ANY-of multi-shard
semantics" the ticket's AC #2 requires the equivalence fixtures to cover, directly proven today by
`test_derive_mapping_handles_multi_subsystem_file` and `test_any_of_candidate_subsystems_touched_clears_flag`.
`derive_mapping` silently `continue`s past a YAML parse failure (line 55-56, bare
`except Exception: continue`) — this is the "malformed-input treatment" difference the ticket's AC
#2 names: the legacy tool **silently skips** a malformed shard and keeps going, while
`tools/parity_index.py`'s importer **aborts the whole build** on the same condition
(`ShardParseError`, Phase 1 Decision 2). This is a real, load-bearing behavioral divergence to
document explicitly, not something to reconcile or "fix" in either direction.

`expected_subsystems_for_files` (line 64-78) restricts to `src/` paths only (non-`src/` silently
dropped from the returned dict, line 74-75) and returns `None` (never omits the key) for an
unmapped `src/` path — this "explicit `None`/NA, never silent omission" behavior is exactly the
"explicit unknown/no-match" requirement this ticket's AC #1 imposes on the new `impact`/`entry`
output, so the new index's behavior here should match the legacy tool's intent even though its
data source differs.

`cross_reference_touched` (line 81-119) returns one of three statuses per `src/` path: `NA` (no
citation found anywhere in canonical files), `PASS` (ANY-of-candidates touched), `FAIL` (mapped but
none touched) — status semantics keyed off git-diff-shaped `touched_ledger_files` input, not
directly comparable to a static "what does entry X's index-derived impact set look like" query.
The equivalence proof needs to translate this PASS/FAIL/NA vocabulary into the new index's terms
(e.g., "does the new index's `code_refs` table produce the same `{src_path: {candidate filenames}}`
mapping as `derive_mapping`, restricted to the same P1+ scope", since `derive_mapping` has no
priority filter at all — it maps every entry regardless of priority, a further intentional
difference from `find_p0_intersection`'s P0-only scope that AC #2 explicitly calls out
("P0-substring versus all-priority behavior") as two *separate* legacy behaviors to reconcile
against, not one).

`tests/tools/test_parity_updater_static.py` (10 tests, confirmed passing): `test_excludes_faction_yaml`
is the second direct fixture proof of faction-exclusion this ticket's faction evidence case must
contrast against; `test_derive_mapping_skips_malformed_yaml_file` is the fixture proof of the
silent-skip malformed-YAML behavior noted above.

### Phase-0 baseline manifest — corpus facts the equivalence fixtures must be built consistently with

`stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/baseline_manifest.json` (read in full):
9 shards, 1,945 entries, 0 duplicate IDs, `excluded_from_legacy_scan: ["faction.yaml"]`,
`missing_evidence_health.missing_test_path_count: 1347`, `missing_v2_evidence_count: 0`,
`priority_counts_total: {P0: 1661, P1: 218, P2: 66}`. `faction.yaml` itself: 13 entries, all
`status: verified`, `priority_counts: {P1: 11, P2: 2}` — **zero P0 entries**, confirming the
ticket's own scope language ("faction's zero-P0/legacy exclusion status") directly against live
data, not an assumption. This ticket's equivalence corpus does not need to reconstruct all 1,945
live entries — it needs small, synthetic, `tmp_path`-isolated fixtures (mirroring Phase 1's own
`_make_corpus`/`_full_nine_shard_corpus` pattern in `tests/tools/test_parity_index.py`) that
reproduce the *shape* of the legacy tools' documented behaviors (P0-only, all-priority, ANY-of,
malformed-input, faction-exclusion) — consistent with Phase 1's own test-fixture precedent, not a
live-corpus replay.

### `v1_decisions_phase0.md` — binding boundary this ticket must respect

"Path-only links" section (read in full): "V1 resolves structured references... to path-level only.
No Graphify symbol resolution is used or depended on in v1." This directly constrains AC's
"no symbol-coverage claim is permitted" language — the `impact`/`entry` output schema must never
claim or imply a symbol-level match; any `--symbol` CLI flag named in the idea doc's CLI sketch
(`parity-index impact --changed-path … [--symbol …] [--test …]`) can, at most, be accepted as an
input filter applied against path-level data (e.g. treating a symbol argument as inert/no-op or as
an explicit "not supported at v1" response) — it must never silently degrade into fabricating a
symbol match from a path match.

### Idea doc's CLI sketch and Phase 2 Delivery Sequence — the ticket's own literal spec

`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md`,
"Read path and context integration" section (line 199-253, read in full):
```text
parity-index build [--check]
parity-index impact --changed-path … [--symbol …] [--test …]
parity-index entry ENTRY-ID
parity-index search --query … --filters …
parity-index health [--subsystem …] [--priority P0]
```
The ticket's own Scope/Related-Docs text quotes only `impact`, `entry`, `health` from this list —
`search` (FTS-backed) and `build --check` are not named in this ticket's Scope and are **not**
implemented here (consistent with the ticket's Out-of-Scope: "semantic search"). "Delivery
sequence: Phase 2" (line 391-398, read in full): "Implement exact `impact`, `entry`, and `health`
APIs/CLI output. Compare index results to current `parity_ledger_scan` and `parity_updater_static`
behavior on a versioned fixture set; document every intentional improvement/difference, including
all-shard coverage. Keep the existing workflow gates unchanged; this is a read-only shadow selection
source." This directly confirms: (a) this ticket's scope is bounded to `impact`/`entry`/`health`
only, matching the ticket body; (b) no gate wiring — matching Out of Scope; (c) the comparison must
be against **both** named legacy functions, not one.

## Mechanics / Engine Constraints

None. Consistent with both Phase 0 and Phase 1's own findings, reconfirmed directly here: this is
agent-infrastructure/tooling work (`tools/`, a read-only query layer over a local derived SQLite
index) — no `docs/mechanics/` chapter or `docs/engine/` contract governs parity-ledger tooling. The
only binding constraints are `docs/parity_ledger/schema.json`'s known duplicate-`"if"`-key parsing
gap (inherited unchanged from Phase 1 — `health` output must continue to reflect the schema's
*documented intent*, not what `json.loads` mechanically enforces) and every decision recorded in
`v1_decisions_phase0.md`, which this ticket must follow without reopening (see Path-only links
above).

## Parity Ledger Overlap

This ticket implements no `src/` simulation behavior — it is meta/tooling work about the ledger's
own read tooling, not a behavior the ledger tracks. Consistent with both Phase 0 and Phase 1's own
findings, independently reconfirmed here (`grep -rl "PARITY-INDEX\|PARITY-IMPACT\|parity_index"
docs/parity_ledger/` returns zero matches): **no parity-ledger entry's `status`/`v2_evidence` needs
to change as a result of this ticket, and no new entry is required.**

The same three informational-only precedent entries Phase 1 found remain the closest prior art
(unchanged, re-confirmed present): `INFRA-289`, `INFRA-290`, `INFRA-291`
(`docs/parity_ledger/infrastructure.yaml`, lines 5710/5779/5859) — each documents a
`tools/agent-monitoring/*.py` module's migration onto a derived SQLite index, the same
precedent-shape as this ticket's `impact`/`entry`/`health` read functions querying
`parity-index/parity.db` instead of scanning YAML/JSONL directly. None require edits; none
document `tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`, or
`tools/parity_index.py`/`tools/parity_index_baseline.py` themselves, consistent with this tool
family's established precedent of shipping without a parity-ledger entry. No P0 entries are at
risk (no `src/` change, no `v2_evidence` touched, no gate behavior changed per Out of Scope).

## Prior Work

- **`stored_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/`** (plan.md, investigation.md, test_plan.md
  — read in full) — the direct Phase-1 predecessor this ticket builds on. Its plan.md's Decisions
  1-3 (FTS5 test seam, duplicate-ID/malformed-shard abort semantics, `entry_fts` naming) are settled
  and this ticket must not reopen them. Its Deviations section records a **user-decision precedent**
  (2026-08-02) for handling a cross-ticket test-assertion collision by narrowing the older test to
  check a historical commit diff rather than live state — directly relevant precedent for this
  ticket's own anticipated collision with `test_importer_does_not_implement_impact_or_entry_or_health_cli`
  (see Risks below), though the resolution shape will differ since that guard's whole purpose is to
  gate exactly what this ticket must now build.
- **`stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/`** (baseline_manifest.json — read in full)
  — Phase-0 corpus facts (see Current Behavior above), the comparison-evidence anchor for the
  equivalence fixture corpus's shape (not a literal live-corpus replay).
- **`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md`** (read in
  full) — binding architecture decisions this ticket inherits without reopening: path-level-only
  references, the 9-table/view schema shape, CLI/module ownership (flat `tools/parity_index.py`, no
  new package).
- **`INFRA-289`/`INFRA-290`/`INFRA-291`** (`docs/parity_ledger/infrastructure.yaml`) — precedent
  shape for "read path migrates from linear scan to derived-index query, body/signature of the
  underlying logic unchanged, comparison test proves byte-identical or documents the narrow
  divergence" — directly the shape of proof this ticket's equivalence corpus must produce for
  `find_p0_intersection`/`cross_reference_touched`.
- **`tests/tools/test_parity_index.py`** (Phase 1's own suite, read in full, 8 test-class groups, 15
  tests, confirmed 44/44 passing today combined with the other three parity test files) — the
  established fixture idiom (`_load_module()` by path, `_make_corpus`/`_full_nine_shard_corpus`,
  `_entry()` builder) this ticket's new equivalence tests should extend rather than reinvent.

## Risks and Open Questions

1. **Direct collision with Phase 1's own anti-drift guard test — requires an explicit decision, not
   an assumption.** `tests/tools/test_parity_index.py::TestArchitectureGuards::
   test_importer_does_not_implement_impact_or_entry_or_health_cli` (line 480-496) currently asserts,
   as a hard invariant: no `add_parser("impact"`, `add_parser("entry"`, or `add_parser("health"` in
   `tools/parity_index.py`'s source, and neither `"impact"` nor `"entry"` appears anywhere in the
   module's `--help` output. This ticket's entire scope is to add exactly those three subcommands.
   Building them **will** break this test as written — this is not a bug to route around, but a
   test whose invariant was correctly scoped to Phase 1 and is now obsolete by design, per Phase 1's
   own plan.md Scope Guards ("Do not build `impact`, `entry`, `search`, or `health` CLI subcommands
   (Phase 2 — TCK-20260731-PARITY-IMPACT-PROOF)") and the idea doc's own Phase 2 Delivery Sequence
   naming exactly these three. **This is flagged as an open question for Plan to resolve explicitly,
   not assumed:** the correct fix is very likely to narrow this specific test to (a) keep asserting
   `search` is never implemented (genuinely still out of scope) and (b) either remove or invert the
   `impact`/`entry`/`health` assertions now that Phase 2 authorizes them — mirroring the Phase-1
   Deviations precedent of narrowing an obsolete-by-design cross-phase test rather than leaving a
   contradiction in place. This must not be treated as "editing a test to dodge a gate" (which the
   project's Hard Rules forbid) — the underlying invariant genuinely changed because this ticket is
   the one that was always destined to add this CLI surface, per the Phase-1 plan's own explicit,
   named forward reference to this ticket ID.
2. **`relation` column is not a ready-made "selection reason."** `_populate_ref_tables` (line
   240-279) leaves `relation` as `NULL` for every regex-matched ref-table row and `"declared"` only
   for the direct `test_path`-sourced row. AC #1's "selection reasons" requirement cannot be
   satisfied by reading `relation` alone — the `impact` query must synthesize a reason string from
   `(table, source_field, relation)` (e.g. "code_refs match via v2_evidence text scan" vs. "test_refs
   declared via test_path field"). This is a design requirement for Plan to size, not a blocker.
3. **AC #2's "P0-substring versus all-priority" and "ANY-of multi-shard" are two independently
   testable legacy behaviors from two different functions, not one comparison.** `find_p0_intersection`
   is P0-only against `v2_evidence` alone with no multi-shard semantics of its own (it just iterates
   shards independently); `cross_reference_touched`'s ANY-of semantics is `derive_mapping`'s
   accumulation of *all* canonical files a path is cited in, at *all* priorities. The equivalence
   fixture corpus needs at least two independent comparison cases (one against each legacy function)
   plus the malformed-input and faction cases — four distinct comparison dimensions total, not a
   single blended fixture. Flagged so Plan sizes this as ≥4 fixture scenarios, not 1.
4. **The idea doc's CLI sketch includes `--symbol` on `impact`, but v1 has no symbol data at all.**
   `code_refs`/`test_refs`/etc. carry only `path`; there is no symbol column anywhere in the Phase-1
   schema. A `--symbol` flag, if implemented, can only ever be a documented no-op/unsupported input
   at v1 (never silently accepted as if it narrowed results) — consistent with the "no
   symbol-coverage claim is permitted" language in both this ticket's Scope and
   `v1_decisions_phase0.md`. Plan must decide explicitly whether to accept-and-ignore-with-warning,
   or reject `--symbol` outright as an unimplemented flag — either is defensible, but silently
   accepting it without a documented no-op behavior would violate the "no symbol-coverage claim"
   constraint.
5. **No pre-existing `impact`/`entry`/`health` implementation or partial CLI branch exists** —
   confirmed via direct grep of `tools/parity_index.py` (only `build` subparser present, module
   docstring's own line 34 documents `impact_candidates` as "intentionally not built here"). Pure
   greenfield addition to an existing module; no conflicting partial implementation to reconcile.
6. **`search` (FTS-backed) is named in the idea doc's CLI sketch but is not in this ticket's Scope
   text** — confirmed consistent, not a gap: the ticket's own Scope/AC text names only `impact`,
   `entry`, `health`, and Out of Scope explicitly excludes "semantic search." The Phase-1 guard
   test's `add_parser("search"` assertion should remain intact and unmodified by this ticket (see
   Risk #1 — only the `impact`/`entry`/`health` assertions in that same test need revisiting).

## Anti-Drift Hazards

- **Do not modify `tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`, or
  either legacy tool's own test file** (`tests/tools/test_parity_ledger_scan.py`,
  `tests/tools/test_parity_updater_static.py`, 13 tests total). This ticket's own Scope requires
  their outputs as unmodified comparison evidence — any edit to the functions under comparison
  would invalidate the equivalence proof itself.
- **Do not wire `impact`/`entry`/`health` into any live workflow gate, agent prompt, or
  `.claude/workflows/implement-ticket.js` phase.** Explicitly Out of Scope; this ticket's own
  Related Docs "Phase-specific selection policy" table marks Parity-phase gate replacement as
  requiring "equivalence evidence" first — this ticket *produces* that evidence, it does not consume
  it to flip the gate.
- **Do not implement `search` or any FTS-backed query surface**, even though `entry_fts` already
  exists from Phase 1 and would make a `search` subcommand technically easy to add. Out of Scope per
  the ticket's own text ("semantic search" excluded) — resist scope creep here specifically because
  the underlying table is already present and "while we're in here" pressure is real.
- **Do not silently fabricate a symbol-level claim** via the `--symbol` flag named in the idea doc's
  CLI sketch. `v1_decisions_phase0.md`'s "Path-only links" decision is binding; any `--symbol`
  handling must be an explicit documented no-op/unsupported response, never a heuristic path-to-symbol
  guess.
- **Do not treat `test_importer_does_not_implement_impact_or_entry_or_health_cli`'s existing
  assertions as untouchable.** Per Risk #1, narrowing/updating this specific test's `impact`/`entry`/
  `health` assertions (while preserving its `search`-forbidden assertion) is the correct, anticipated
  outcome of this ticket per Phase 1's own forward reference — not a gate-gaming shortcut. Plan must
  state this explicitly rather than leaving an implementer to discover the contradiction mid-build
  and improvise.
- **Do not invent a relationship or repair a health finding while building the `health`
  subcommand.** Per the ticket's own Scope line ("without inventing a relationship or changing a
  source/legacy tool"), `health` output is a read/format layer over the existing `entry_health`
  table — it must never write back to `entries`, `docs/parity_ledger/*.yaml`, or synthesize a finding
  type Phase 1 didn't already classify.
- **Do not run the equivalence proof against the live 1,945-entry corpus as the primary test
  substrate.** Follow Phase 1's own precedent: small, synthetic, `tmp_path`-isolated fixtures that
  reproduce the legacy tools' documented behavior shapes (P0-only, all-priority, ANY-of, malformed,
  faction-exclusion) are the testable unit; the live corpus is comparison-evidence context, not a
  fixture to hard-code assertions against (Phase 0/1 baseline drift is expected and must not be
  treated as a bug when the live entry count changes between now and implementation).
