---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260709-REGISTRY-DRIFT-CHECK-GATE
artifact_type: investigation
tags: [testing, observability]
---

# Investigation — TCK-20260709-REGISTRY-DRIFT-CHECK-GATE

## Current Behavior

**`tools/generate_registry.py` has no dry-run/diff mode today — every invocation writes to disk.**

- `generate_registry(root: Path, output: Path) -> int` (`tools/generate_registry.py:408-443`) is the
  single entry point. It: (1) `collect_docs(root)` (line 179) — walks `docs/`, skipping
  `_SKIP_DOC_SUBDIRS = {"archive", "parity_ledger", "scenarios", "entity"}` (line 35); (2)
  `collect_tickets(root)` (line 239) — walks `tickets/done/*.md` flat, joining
  `stored_artifacts/{ticket_id}/*.md` via `join_artifact_files` (line 98); (3) `sort_entries()`
  (line 312) — docs first (P0→P2, then path), tickets second (date descending, then path); (4)
  `_normalise_entry_for_output()` (line 390) per entry; (5) strips `None` `last_verified` fields
  (lines 419-421); (6) **unconditionally** opens `output` for write and calls `_dump_yaml()` (lines
  430-432); (7) prints a summary (line 435); (8) returns `1` if `doc_errors` is non-empty (missing
  doc frontmatter), else `0` (lines 437-443).
- **Computation and writing are NOT already separated.** Steps 1-5 (compute `output_entries`) and
  steps 6-7 (write + print) sit in the same function body with no natural seam already exposed as a
  separate callable — a `--check` mode must either factor out a `compute_registry_entries(root) ->
  (list[dict], list[str])` helper (recommended: minimal, testable) or branch inside
  `generate_registry()` itself before the `output.open("w")` call at line 431.
- **Critical, previously-unflagged hazard: the header embeds a live UTC timestamp.**
  `header = f"...\n# Generated: {ts}\n"` where `ts = datetime.now(timezone.utc).strftime(...)`
  (lines 423-428). A byte-for-byte diff of the freshly-generated text against the on-disk file will
  **always** show a one-line difference (the timestamp) even when every entry is identical — this
  would make a naive `--check` implementation permanently non-zero-exit, defeating the ticket's own
  purpose. Confirmed live: the on-disk `docs/REGISTRY.yaml` header currently reads
  `# Generated: 2026-07-09T07:09:47Z` (from this session's `TCK-20260709-REGISTRY-REGEN-ON-CLOSE`
  Finalize run) — re-running `generate_registry()` now would produce a different timestamp
  immediately. **The diff must compare parsed entry lists (`yaml.safe_load` on-disk vs. in-memory
  `output_entries`), not raw file text including the header.** This is the single most important
  design constraint for this ticket and is not mentioned in the ticket body.
- `main()` (line 446) wires `--root` and `--output` args only; no `--check` flag exists. `sys.exit`
  is called on `generate_registry()`'s return value (line 467).
- The only invocation site today is `Makefile:233-234` (`docs-registry` target, unconditional
  `python3 tools/generate_registry.py`) plus, as of the sibling ticket closed earlier this session
  (`TCK-20260709-REGISTRY-REGEN-ON-CLOSE`), `tools/gate_checks/done_checker_static.py`'s
  `check_registry_entry_regenerated()` (calls `generate_registry()` directly, non-`--check`, always
  writes). Neither is `--check` mode — both are the "prevention" write path this ticket's "backstop"
  is explicitly independent of.
- **PyYAML is a hard dependency** (`requirements.txt:31`, `PyYAML==6.0.2`; confirmed importable in
  this environment) — `_HAS_PYYAML` (line 112-128) will always be `True` in CI/dev, so the
  stdlib-only fallback serializer (lines 130-171) is dead code in practice but must not be broken by
  any change (it's exercised implicitly whenever `_dump_yaml` is called and PyYAML is absent —
  no test currently forces that path, confirmed by grep: no `monkeypatch` of `_HAS_PYYAML` in
  `tests/tools/test_generate_registry.py`).
- **No `--check`/dry-run convention exists elsewhere in `tools/`** to copy. Checked
  `validate_frontmatter.py` (validates only, no write, no diff — always read-only, so it had no
  need for a check/write distinction) and `tag_registry.py` (append-only writer, no dry-run flag).
  The closest exit-code-differentiation precedent in this repo is `tools/evaluate_simq.py`, which
  uses `sys.exit(2)` for a distinct failure class (anchor file missing / bad JSON / comparison
  errors) alongside implicit `sys.exit(0)` success — i.e., **`sys.exit(2)` for a different-meaning
  failure than `sys.exit(1)` already has a precedent in this repo**, supporting exit code `2` for
  "drift detected" as distinguishable from `1` ("doc frontmatter missing").
- **Subprocess end-to-end CLI testing has a direct precedent**: `tests/tools/test_add_frontmatter_tickets.py`
  (`TestValidateFrontmatterAcceptsOutput`, lines 337-417) runs
  `subprocess.run([sys.executable, str(TOOLS_DIR / "validate_frontmatter.py"), ...], capture_output=True,
  text=True)` and asserts on `result.returncode`. New `--check` tests should follow this exact shape
  (`subprocess.run([sys.executable, str(GENERATE_REGISTRY_PATH), "--root", str(tmp_path), "--output",
  str(fixture_registry), "--check"], ...)`) rather than in-process argparse mocking, since `main()`
  itself is what needs exercising for an end-to-end CLI contract test.
- **CI has no job touching `docs/REGISTRY.yaml` at all today.** `.github/workflows/test.yml` defines
  9 jobs. The relevant candidates named in the ticket:
  - `arch-docs` (lines 145-160): `pytest tests/architecture tests/docs tests/integrity tests/static
    tests/refactor -m "not slow"`. `tests/tools/` is **not** in this job's path list.
  - `api-tools` (lines 112-128): `pytest tests/api tests/cli tests/tools tests/logging tests/engine
    tests/observability -m "not slow"`. **`tests/tools/` IS in this job** — `test_generate_registry.py`
    already runs here today. This is the natural home if the `--check` gate is implemented *as a
    pytest test* (e.g. `test_registry_matches_live_tree` in `tests/tools/test_generate_registry.py`
    itself, using `subprocess.run(... "--check" ...)` against the real repo root) — no `.yml` edit
    needed at all, since `pytest tests/tools` already runs in `api-tools`.
  - Alternatively, a **dedicated `run:` step** (not pytest) in either job, e.g.
    `python3 tools/generate_registry.py --check`, would need an explicit new step added to the
    `.yml` file (AC's literal wording: "Wire a CI job/step ... that runs `generate_registry.py
    --check`").
  Both satisfy the AC's "e.g. ... arch-docs job, or a dedicated step" wording; **which of the two
  is the Plan's call — flagged as an open question below**, but there is a clear technical case that
  reusing `api-tools`'s existing `pytest tests/tools` invocation (a new test function, zero `.yml`
  diff) is lower-risk than adding a bespoke `run:` step to `arch-docs` for a file that job doesn't
  otherwise touch.

## Mechanics / Engine Constraints

None. `generate_registry.py` and its tests are workflow/doc tooling — no `docs/mechanics/` or
`docs/engine/` contract applies. `INFRA-183` (below) explicitly tags this tool
`support_boundary: "Doc tooling only — no simulation behavior involved."` — the same boundary
applies to this ticket's `--check` addition.

## Parity Ledger Overlap

Two existing entries in `docs/parity_ledger/infrastructure.yaml`, both `status: verified`,
`priority: P2` (neither is P0 — no mandatory passing-`test_path` gate, but `v2_evidence`/`test_path`
should stay accurate):

- **`INFRA-183`** (lines 1900-1913): describes `generate_registry.py`'s **output shape** ("flat
  index of all frontmatter-tagged docs and closed tickets..."). `test_path:
  tests/tools/test_generate_registry.py`. This ticket adds new tests to that exact file and a new
  CLI flag to that exact tool, but does not change the *shape* of what gets written in default
  (non-`--check`) mode — `INFRA-183`'s `text` likely stays accurate as-is; its `v2_evidence` may
  warrant a one-line addendum noting the new `--check` flag exists, at the Parity phase's
  discretion (same pattern as `INFRA-263`'s relationship to `INFRA-183` — read below).
- **`INFRA-263`** (lines 3711-3736, added this session by `TCK-20260709-REGISTRY-REGEN-ON-CLOSE`'s
  Parity phase): describes the **prevention** mechanism — `check_registry_entry_regenerated()`
  auto-regenerating (and writing) `docs/REGISTRY.yaml` at every ticket close. Its own text explicitly
  scopes itself to "invocation timing (auto-run at close, not just available to run manually)" and
  states it "does not touch, extend, or duplicate INFRA-183." This ticket's `--check` gate is a
  **third, distinct** guarantee — a CI backstop that fires independently of whether the Finalize
  hook ran at all (per this ticket's own Request Summary: "independent of and complementary to the
  prevention hook") — so it does not naturally belong inside `INFRA-263`'s text either.

**Recommendation for the Parity phase: add a new entry, `INFRA-264`** (next sequential ID —
confirmed `INFRA-263` is currently the highest-numbered entry in the file, via
`grep -oP "id: INFRA-\d+" | sort | tail`), following the exact "companion, not edit" precedent
`INFRA-263` itself set relative to `INFRA-183`. Draft `text`: "CI drift-detection backstop —
`generate_registry.py --check` regenerates the registry in-memory and diffs against the checked-in
`docs/REGISTRY.yaml`, failing the CI job on mismatch, independent of whether the Finalize-phase
auto-regen (INFRA-263) ran or succeeded." `v2_evidence` should cite the new CLI flag plus the CI job
name/step actually chosen at Implement. `test_path` should cite the new `--check` test(s) added to
`tests/tools/test_generate_registry.py`. This is a recommendation, not a mandate — final
add/no-add judgment belongs to the `parity-updater` agent at Parity phase, consistent with how
`INFRA-263` itself was a Parity-phase judgment call, not an Implement-phase one.

**Flag: no P0 entries touched or affected.**

## Prior Work

- **`TCK-20260709-REGISTRY-REGEN-ON-CLOSE`** (`tickets/done/`, this session — sibling ticket in the
  same batch): implemented the **prevention** half (auto-regen + write at Finalize). Its own
  investigation.md explicitly named this ticket as the separately-scoped **backstop** half and its
  Out of Scope explicitly excludes "Adding the --check/CI drift-detection gate." Its Implementation
  Notes confirm the actual functions/files touched: `check_registry_entry_regenerated()` added to
  `tools/gate_checks/done_checker_static.py` (between `check_monitoring_write_recorded` and
  `run_finalize_selfcheck`), wired as `run_finalize_selfcheck`'s 4th tuple element, `generate_registry.py`
  itself **left untouched** by that ticket (confirmed: `tests/tools/test_generate_registry.py`
  unchanged by that ticket's diff — still 41 tests, matching this investigation's own local run).
  This confirms `generate_registry.py`'s current state (as read above) is exactly as that ticket's
  investigation described it — no drift between that investigation and this one.
- **`TCK-20260606-DOCSITE-REGISTRY`**: original ticket that created `generate_registry.py` and
  `docs/REGISTRY.yaml` (912-entry baseline at the time). Established the docs-first/tickets-second
  sort order and the `Makefile` `docs-registry` target this ticket must not modify.
- **`TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER`**: fixed the repo-wide doc-frontmatter gap that
  used to make `generate_registry.py` exit 1 unconditionally; relevant because a `--check` gate run
  against the live tree today will inherit whatever the current frontmatter-completeness state is —
  confirmed clean by this investigation's own `test_registry_exits_zero_on_real_docs_tree` run
  (still passes, rc=0, no doc errors currently).
  `TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL` and `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`
  (named as Out of Scope in this ticket) are the ongoing continuation of that cleanup — this ticket
  must not touch either.
- **`TCK-20260705-TAG-REGISTRY-QUERY`**: added `tools/registry_query.py` (seed-vocabulary tag
  matcher over `docs/REGISTRY.yaml` entries) — read for this investigation's own "Finding Prior
  Work" step per the Investigator role's instructions. Confirms `registry_query.py` has no
  relationship to write/check semantics — it's a pure read-side consumer of the registry's *content*,
  unaffected by how that content gets generated or verified. No overlap with this ticket's scope
  beyond being listed in Related Code Areas (informational only — no `--check`-relevant logic there).
- No stored investigation exists specifically for a `--check`/dry-run CLI convention anywhere in
  this repo's tooling — confirmed via both the `search_docs` and `graphify query` results returned
  at the start of this investigation (neither surfaced a prior `--check`/diff-mode design for any
  `tools/*.py` script), and via direct reads of `validate_frontmatter.py`/`tag_registry.py`. This is
  a genuinely new convention, as the ticket's own Assumptions section already flags.

## Risks and Open Questions

1. **Header-timestamp false-positive (see Current Behavior) is the top implementation risk.** Any
   `--check` implementation that diffs raw file text (including the `# Generated: <ts>` header line)
   will report drift on every run, defeating the gate. **Must** compare parsed entry lists
   (`yaml.safe_load(on_disk_text)` vs. in-memory `output_entries`), not raw text. Flagging for
   Plan/Implement — not optional.
2. **CI wiring placement is genuinely open, not fully resolved by the ticket text.** The ticket says
   "e.g. ... arch-docs job, or a dedicated step" — both a pytest-based approach (new test function in
   `tests/tools/test_generate_registry.py`, reusing the existing `api-tools` job's `pytest
   tests/tools` invocation, zero `.yml` diff) and a bespoke `run:` step (either job, requires a
   `.yml` edit) satisfy the AC's literal wording. The pytest-based approach is lower-risk (reuses an
   already-passing CI lane, no new job/step to keep in sync) but the ticket names `arch-docs`
   specifically as the example. **This is a Plan-time decision, not an Implement-time one** — the
   AC's "readable diff/summary on mismatch" requirement is satisfiable either way (a failing pytest
   assertion can print the diff via its failure message; a bespoke step prints to CI log directly).
3. **Exit code for "drift detected" must be chosen and documented.** No existing `--check`
   convention to copy; `tools/evaluate_simq.py`'s `sys.exit(2)` for a distinct failure class is the
   closest local precedent (see Current Behavior). Recommend exit code `2` for drift-detected,
   keeping `1` reserved for the pre-existing "doc missing frontmatter" meaning — this satisfies the
   AC's "distinguishable... same code with different stderr framing, or a separate documented code"
   requirement via the "separate documented code" branch. Must be documented in the module docstring
   (lines 12-13 currently only document `0`/`1`).
4. **Interaction between `--check` and pre-existing doc-frontmatter errors is unspecified by the
   ticket.** If `doc_errors` is non-empty *and* `--check` is passed, should the tool report the
   frontmatter error (exit 1, existing meaning) or attempt the diff anyway? Recommend: frontmatter
   errors short-circuit before the diff step (same as today's non-`--check` path) and keep exit `1`
   — a repo with un-computable entries cannot produce a meaningful diff. This should be an explicit
   test case, not an assumption baked in silently.
5. **Missing on-disk output file in `--check` mode is unspecified.** If `docs/REGISTRY.yaml` doesn't
   exist at all (e.g. a fresh checkout misconfiguration, or a differently-pathed `--output` in a
   test fixture), should `--check` report drift (file doesn't match "expected" content, i.e.
   everything is "added") or error out separately? Recommend: treat as drift (exit 2), since "file
   absent" is a valid, diffable "before" state (empty list) — avoids a third exit-code meaning.
6. **`--check` and PyYAML fallback path.** The stdlib-only `_dump_yaml` fallback (used only if
   PyYAML is absent) produces YAML text but has no corresponding *parser* in this module — parsing
   the on-disk file for diff purposes must use `yaml.safe_load`, which requires PyYAML regardless of
   which serializer wrote the file. Since PyYAML is a hard `requirements.txt` dependency, this is
   very unlikely to matter in practice, but `--check`'s parse step should not silently assume
   `_HAS_PYYAML` without an explicit guard/error message, since the write path already tolerates its
   absence.

## Anti-Drift Hazards

- **Do not let `--check` mode write to disk under any code path** — this is the AC's explicit,
  testable requirement ("writing no file in --check mode"). Any refactor that hoists the
  `output.open("w")` call must keep it strictly conditional on `not check`.
- **Do not regress the ~35+ existing tests that call `generate_registry(tmp_path, output)`
  positionally** expecting a real write and `rc == 0`/`rc == 1` semantics unchanged. Adding a `check:
  bool = False` keyword-only parameter (default `False`) preserves every existing call site
  unmodified — do not reorder existing positional parameters, do not change the default write
  behavior.
- **Do not diff raw file text including the header timestamp line** (Risk #1) — this is the single
  most likely way this ticket ships broken (an always-red or always-green gate that doesn't actually
  detect drift).
- **Do not touch `_SKIP_DOC_SUBDIRS`, `collect_docs`, `collect_tickets`, `sort_entries`, or any other
  entry-computation internals** — this ticket is additive (a new flag plus a new comparison branch),
  not a rewrite. Mirrors the sibling ticket's identical guardrail.
- **Do not modify the `docs-registry` Makefile target's existing meaning** (`python3
  tools/generate_registry.py`, unconditional write) — if a `docs-registry-check` convenience target
  is added, it must be a *new* target, not a change to the existing one.
- **Do not conflate this ticket's CI gate with `check_registry_entry_regenerated()`'s Finalize-time
  write-and-verify** (`TCK-20260709-REGISTRY-REGEN-ON-CLOSE`, already done) — they are deliberately
  independent mechanisms (prevention vs. backstop) per both tickets' own Request Summary/Scope text;
  do not merge them into one code path or one parity ledger entry.
- **Do not hardcode or assert a specific entry count** anywhere in new tests (against
  `docs/REGISTRY.yaml`'s real content) — `TCK-20260709-REGISTRY-COUNT-STALE-DOCS` (this session)
  explicitly removed a hardcoded "912 entries" claim for exactly this reason; the real tree's entry
  count is expected to keep changing.
