---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP
artifact_type: investigation
tags: [testing, bug]
---

# Investigation — TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP

## Current Behavior

A fresh local run confirms the lane's real state as of 2026-08-17:

```
tests/tools/test_gate_a_readpath_review.py        3 failed, 6 passed, 7 errors
tests/tools/test_context_kind_priority_decision.py       1 failed (of 11)
tests/tools/test_exact_lookup_convention_decision.py     2 failed (of 12)
tests/tools/test_stored_artifact_kind_decision.py        1 failed (of 11)
tests/tools/test_entity_event_ledger.py                  1 failed
tests/tools/test_search_mcp.py::TestMcpJson::test_command_is_python3   1 failed
```

The ticket's own count ("23 failed + 7 errors of 2272 collected") was the full `tests/tools -m
"not slow"` lane total; this investigation re-verified each of the 8 groups individually rather
than re-deriving the aggregate. One correction to the ticket's own group-4 description: it reads
"2 direct failures + 5 cascading errors" — the real, freshly measured split is **3 failed + 7
errors** (`TestCorpusIntegrity` has 2 direct-load tests, but `TestAdjudication::
test_gate_a_no_phase2_synthetic_fixture_relabeled_as_ticket_derived_corpus` also calls
`_load_corpus()` directly, outside the `gate_a_full_run` fixture, making it a 3rd direct failure
rather than an 8th cascading error). This does not change the fix, only the exact test count.

### Group 1 — 2 KGMCP real-gateway tests over/at the fast-lane budget

`tests/conftest.py:60-88` enforces a per-test wall-clock budget; `--resource-budget` defaults to
`medium` = 60s (`:62-88`). Measured directly with `--resource-budget off --durations=10`:

- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py::test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`
  (line 375) — **40.94s** alone (whole file: 44.55s, 17 tests, all other tests <3s each).
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py::test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`
  (line 667) — **60.98s** alone (whole file: 69.86s, 31 tests). A secondary contributor in the
  same file, `test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip`, takes 7.29s
  and `test_branch_partition_live_direct_call_against_a_real_current_row` takes 1.48s — both real
  live-gateway round trips, but comfortably inside budget on their own.

This refines the ticket's own framing ("mark both `@pytest.mark.slow`") to a precise,
minimal fix: only the two identically-named `test_zero_mutation_of_agent_monitoring_and_
manifest_across_full_run` functions (one per file) are the actual budget-busting real-gateway
calls. Marking only those two, not the whole module, keeps the other 16 (phase2) / 30 (phase3)
already-fast tests in the `api-tools` fast lane, per CLAUDE.md's Testing Rule ("scope to the
domain"). `phase2` currently has no `import pytest`; `phase3` already does (line 57).

`pyproject.toml:67-69` already registers both `slow` and `extra_slow` markers — no new marker
registration needed.

**CI/CD coverage check (ticket's own explicit ask):** `.github/workflows/test.yml`'s `api-tools`
job (lines 111-128) runs `pytest tests/api tests/cli tests/tools tests/logging tests/engine
tests/observability -m "not slow" --tb=short -q` — this is the real `-m "not slow"` fast lane the
ticket describes. The `slow` job (lines 208-241) runs `pytest tests/ -m "slow or extra_slow"
--resource-budget large --tb=short -q --ignore=tests/unit/worldassembly/test_corpus_diversity.py`
— `pytest tests/` is the whole tree, recursively, so `tests/tools/` **is** already covered by the
`slow` job today. **No CI/CD gap exists** — marking the 2 functions `@pytest.mark.slow` moves them
into a lane that already runs them (at `--resource-budget large` = 600s, comfortably above their
41s/61s real cost), it does not silently drop them from CI. No change to `.github/workflows/
test.yml` is required for coverage; only the 2 `@pytest.mark.slow` decorators are needed.

### Group 2 — `content_usage_matrix.md` frontmatter gap

**Resolved: this file is script-generated, not hand-maintained.**
`tests/unit/content/test_content_usage_matrix.py::test_generate_and_save_report` (lines 111-120)
calls `generate_matrix_report()` (imported from `src/content/matrix.py`) and unconditionally
**writes its return value to `docs/mechanics/content_usage_matrix.md` on every test run**
(`output_path.write_text(report, ...)`, line 118). This runs as part of the `unit-core-world` CI
job (`tests/unit/content` is in that job's path list, `.github/workflows/test.yml:35`) — so any
hand-edited frontmatter added directly to the `.md` file would be silently overwritten the next
time this unit test suite runs, locally or in CI.

Root cause: `generate_matrix_report()` (`src/content/matrix.py:715-737`) builds its `lines` list
starting directly with `"# Content Usage Matrix Report"` (line 718) — no frontmatter block is ever
prepended. The fix must go in this function, not the `.md` file directly.

No `Makefile` target or `tools/` script references `content_usage_matrix.md` as a write target;
`src/content/repository.py:150` and `tests/unit/content/test_content_usage_matrix.py` are the only
other references, both read-side (a comment and the generating test itself).

Frontmatter shape (per `docs/guidelines/frontmatter_schema.md:42-55` and
`tools/validate_frontmatter.py:44-58`): required fields `status`, `layer`, `authority`,
`audience`; `last_verified` is required only when `status: authoritative`. Since this doc is
regenerated by an automated test run (no human curates a `last_verified` date), `status: active`
is the correct choice — avoids a `last_verified` field nobody maintains — matching the precedent
at `docs/simulation_quality/eval_matrix_results.md:1-5` (`status: active`, no `last_verified`).
`layer: mechanics` is registered (`registries/layer_registry.jsonl:1`). Recommended block:

```yaml
---
status: active
layer: mechanics
authority: P1
audience: developer
---
```

### Group 3 — 3 stale frozen-content-hash guards

All 3 use the identical `hashlib.sha256(path.read_bytes()).hexdigest()` pattern against a
hardcoded `_EXPECTED_TOOLS_HASHES` dict, one entry per protected `tools/*.py` file, explicitly
documented in each file's own header comment as "a one-off scope guard for this ticket, not a
durable invariant... a future ticket... should update (or remove) the corresponding constant."
Confirmed via direct pytest run which single dict entry in each file is now stale:

- `tests/tools/test_context_kind_priority_decision.py:31-33` — stale entry:
  `"tools/parity_index.py"`. The other 3 entries (`context_packet_assembler.py`,
  `hybrid_retrieval.py`, `generate_registry.py`) still match; leave them.
- `tests/tools/test_exact_lookup_convention_decision.py:37-39` — stale entry:
  `"tools/parity_index.py"` (same file, same reason: `tools/parity_index.py` has legitimately
  changed via unrelated later work, e.g. `TCK-20260731-PARITY-READPATH-GATE`/
  `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`). Other 3 entries still match.
- `tests/tools/test_stored_artifact_kind_decision.py:27-29` — stale entry:
  `"tools/generate_registry.py"`. Other 3 entries (`validate_frontmatter.py`,
  `context_packet_assembler.py`, `hybrid_retrieval.py`) still match.

Fix (matching the established precedent this session already applied 3x to KGMCP's own sibling
tickets, e.g. `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py:105-113`'s own
narrowing comments): remove each stale dict entry, with a one-line disclosure comment citing this
ticket and stating the entry was removed because the named file legitimately changed via unrelated
later work, confirmed by `git log` showing this session's 2 tickets never touched it.

### Group 4 — `gate_a_corpus.json`/`gate_a_results.json` provenance (open question 1, resolved)

**Exhaustive search performed, per the ticket's explicit ask:**

1. `git log --all --oneline --since="2026-07-30" --until="2026-08-02"` — no commit around the
   `TCK-20260731-PARITY-READPATH-GATE` era references gate_a, corpus, or results under any
   filename. `git log --all --oneline --grep="gate_a" -i` — zero hits. `git log --all
   --diff-filter=A --name-only -- staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/` — zero
   hits (the staging directory itself was never committed at any point; only its final
   `investigation.md`/`plan.md`/`test_plan.md` were added, directly under `stored_artifacts/`, at
   the Finalize commit). `find` for `gate_a_corpus*`/`gate_a_results*` anywhere in the working
   tree — zero hits.
2. `tools/parity_index.py` has no `gate_a`-specific regeneration logic — its only public API is
   `build()`/`entry()`/`impact()`/`health()` (lines 530, 550, 599, 661), all generic, none aware of
   this specific corpus shape.
3. `stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/{investigation,plan}.md` — grepped for
   `gate_a`, `corpus.json`, and every real case ID (`WORLD-076`, `INFRA-299`, `FAC-012`) — zero
   hits. No sibling ticket holds an equivalent or overlapping corpus.

**Conclusion: unrecoverable, confirmed exhaustively — not just "not found by one grep."** The 6
real cases' *metadata* (`case_id`, `commit_sha`, `entry_id`, `changed_path_query`,
`expected_obligation_ids`) is technically re-derivable from `docs/ai/parity_readpath_gate_a_
decision.md` §2.1's own table, since `canonical_fragment_hash` is a pure, reproducible function of
git-pinned content (`_fragment_hash()`, test file lines 75-82). But the 3 synthetic edge cases
(`SYN-P0PAIR-001`, `SYN-MULTISHARD-001`, `SYN-MALFORMED-001`) were **hand-authored fixture
entries** — their exact field values were never disclosed anywhere, only their *shape* and
*adjudicated outcome* (decision doc §2.2, §6.3). Reconstructing them now, with full knowledge of
what `docs/ai/parity_readpath_gate_a_decision.md` §6.3 already says they proved (e.g. the
three-way malformed-shard divergence), is definitionally hindsight-informed — exactly the
"retroactively re-freezing already-computed results" risk the ticket's own Out of Scope section
forbids, and the corpus's own `plan.md` Decision 2 methodology ("frozen before any result was
computed") exists specifically to prevent. Even a real-cases-only partial reconstruction would
fail `TestCorpusIntegrity::test_gate_a_corpus_cases_have_pinned_source_and_expected_set`'s
`len(corpus["synthetic_edge_cases"]) >= 3` assertion, and would have to reuse the exact case IDs
(`FAC-012`, `INFRA-296`, etc.) the test module's `_Adjudications` class hardcodes by literal
string (lines 373-394) to avoid breaking those tests differently — i.e. any regenerated corpus
would only be a corpus reverse-engineered to fit this file's own hardcoded expectations, not an
independent freeze. **Honest disclosure is the correct resolution, matching the ticket's own
stated preference.**

**Fix design — skip, not delete, with disclosure:**

Confirmed which of the file's test classes depend on `_CORPUS_PATH`/`_load_corpus()` (directly, or
transitively via the `gate_a_full_run` fixture) vs. which do not:

| Class | Depends on corpus? | Current state | Action |
|---|---|---|---|
| `TestNoMutation` (1 test) | No — only reads `_protected_files()` | passes today | **Untouched** |
| `TestCorpusIntegrity` (2 tests) | Yes — direct `_load_corpus()` call | fails (F) | Skip |
| `TestLegacyCapture` (1 test) | Yes — via `gate_a_full_run` fixture | errors (E) | Skip |
| `TestIndexCapture` (2 tests) | Yes — via fixture | errors (E) | Skip |
| `TestAdjudication` (3 tests) | 2 via fixture, 1 direct (`test_gate_a_no_phase2_synthetic_fixture_relabeled_as_ticket_derived_corpus`, line 520, calls `_load_corpus()` directly, not fixture-gated) | 2 error, 1 fails | Skip all 3 |
| `TestMetrics` (2 tests) | Yes — via fixture | errors (E) | Skip |
| `TestDecisionDocIntegrity` (5 tests) | No — only reads `_DECISION_DOC_PATH` | passes today | **Untouched** |

Implementation: add `_CORPUS_AVAILABLE = _CORPUS_PATH.exists()` and a shared, dated skip-reason
string near the top of `test_gate_a_readpath_review.py`, citing
`TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP` and the exhaustive-search finding above.
Apply `@pytest.mark.skipif(not _CORPUS_AVAILABLE, reason=_SKIP_REASON)` to `TestCorpusIntegrity`
and to `TestAdjudication::test_gate_a_no_phase2_synthetic_fixture_relabeled_as_ticket_derived_
corpus`. Add `if not _CORPUS_AVAILABLE: pytest.skip(_SKIP_REASON)` as the first line of the
`gate_a_full_run` fixture (module-scoped, line 229) so every test that consumes it (`TestLegacy
Capture`, `TestIndexCapture`, the other 2 `TestAdjudication` tests, `TestMetrics`) reports as
skipped rather than erroring. `TestNoMutation` and `TestDecisionDocIntegrity` are left completely
unedited. This is a genuine, disclosed skip for a real missing input, not a loosened assertion —
consistent with CLAUDE.md's "never edit an artifact to make a gate pass" rule, since nothing here
is being made to silently pass.

### Group 5 — `test_epic_staleness_check.py`'s stale `obs-isolation` fixture (open question 2 [ticket numbering: 3], resolved)

`tickets/todos/` today contains exactly one folder, `codex-runtime-activation/` (plus one loose
ticket file, `TCK-20260731-CODEX-EXECUTION-IDENTITY-TAG-SWEEP.md`, not epic-shaped). Checked
whether `codex-runtime-activation/` is a valid "genuinely never-started" substitute:

- `SEQUENCE.md` lists 6 tickets: `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`,
  `TCK-20260730-CLAUDE-EXECUTION-IDENTITY`, `TCK-20260730-PROVIDER-HOOK-POLICY`,
  `TCK-20260730-CODEX-POSTTOOL-ADAPTER`, `TCK-20260730-CODEX-RUNTIME-SHADOW`,
  `TCK-20260730-CODEX-CONTROLLED-PILOT`.
- Only `TCK-20260730-CODEX-CONTROLLED-PILOT.md` still physically lives in the folder — the other 5
  tickets already completed and moved to `tickets/done/`. `tickets/working_log.csv` confirms
  `TCK-20260730-CODEX-RUNTIME-SHADOW` closed **2026-07-31**.
- Traced `tools/agent-monitoring/epic_staleness_check.py`'s actual logic:
  `discover_candidate_epics()` (lines 129-198) would discover this folder in `mode="folder"` (has
  `SEQUENCE.md`, no epic-tier ticket file remaining in the folder, so
  `epic_id = "FOLDER-tickets-todos-codex-runtime-activation"`), with `child_ids` pulled from
  `SEQUENCE.md`'s text. `resolve_child_activity()` would find `TCK-20260730-CODEX-RUNTIME-SHADOW`'s
  2026-07-31 `working_log.csv` row as `most_recent_activity`. `is_epic_stale()` (line 251) returns
  `True` whenever `(now - most_recent_activity) > window_days` (`DEFAULT_STALENESS_WINDOW_DAYS = 5`,
  line 38) — with today (2026-08-17) minus 2026-07-31 being 17 days, this folder **would actually
  be flagged STALE right now**, not never-started. It has real, non-zero child activity — the
  opposite of the semantic the test needs to prove (an epic with **zero** child activity ever is
  correctly classified never-started). It is disqualified, not a usable substitute.
- No other `tickets/todos/` folder exists today. `tickets/backlogs/` is a different location type
  the epic-staleness checker's `discover_candidate_epics()` never scans (only `inprogress_dir` and
  `todos_dir` are read, per its signature), so an epic parked there would not even be discovered by
  the function under test — irrelevant regardless of its own activity state.

**Conclusion: no live repo path exists today that is genuinely "zero child activity ever."**
Per the ticket's own fallback instruction, this test must move to a synthetic `tmp_path` fixture.

Note: the *unit-level* proof of this exact semantic already exists and already passes today —
`test_does_not_flag_never_started_epic(tmp_path)` (lines 216-236) exercises `is_epic_stale()` /
`is_epic_never_started()` directly against a synthetic epic with zero activity. What is missing is
only the *end-to-end integration* proof (`compute_stale_epics_report()`/`find_stale_epics()`'s
full real-file-reading pipeline, including the report-string "Informational:" section split) and
the no-mutation guard, both of which currently depend on the real, now-gone `REAL_OBSISO_DIR`.

### Group 6 — stale epic ticket path in `test_exact_lookup_convention_decision.py`

`_EPIC_TICKET_PATH` (`tests/tools/test_exact_lookup_convention_decision.py:28-30`) points to
`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`. Confirmed via `find`: the
real file now lives at `tickets/backlogs/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` — a 3rd
ticket-location type distinct from `done/`/`todos/`, consistent with this epic remaining open
(per its own working-log history) but deprioritized out of active `inprogress/`. Fix: update the
path constant's `"inprogress"` segment to `"backlogs"`.

### Group 7 — `.mcp.json` `command` assertion (`test_search_mcp.py`)

Confirmed the full real, intentional chain, not just the literal value:
- `.mcp.json`'s `knowledge-search` server: `"command": "bash"`, `"args": ["tools/start_search_mcp.sh"]`.
- `tools/start_search_mcp.sh` (read in full): tries `.venv/bin/python3`, then a hardcoded
  `vboxuser` venv path, then falls back to `command -v python3`, and `exec`s whichever is found
  running `search_mcp.py`. This is `TCK-20260624-FIX-TOOLS-SERVER`'s documented portability fix
  (`tickets/working_log.csv` row), shipped and intentional — the wrapper script itself is what
  invokes python3, not `.mcp.json`'s own top-level `command` field.

`tests/tools/test_search_mcp.py::TestMcpJson::test_command_is_python3` (lines 55-58) is the stale
artifact — it asserts `entry["command"] == "python3"` directly, never accounting for the wrapper
indirection.

**Additional confirmed finding beyond the ticket's own named scope for this group:** running the
full `TestMcpJson` class directly (`pytest tests/tools/test_search_mcp.py::TestMcpJson -v`) shows
**2 failures, not 1** — `test_args_point_to_search_mcp` (lines 60-64) also fails today, for the
same root cause: it asserts `entry["args"][0].endswith("search_mcp.py")`, but the real, intentional
`args[0]` is `"tools/start_search_mcp.sh"` (the wrapper), which does not end in `search_mcp.py`.
The ticket's own group 7 only names `test_command_is_python3`; this second failure is the same
stale-reference class and squarely inside this group's own `Related Code Areas` listing
(`tests/tools/test_search_mcp.py` named whole-file, not by test). Both must be fixed together.

Fix: rewrite both assertions to the real contract:
- `test_command_is_python3` → assert `entry["command"] == "bash"`.
- `test_args_point_to_search_mcp` → assert `entry["args"][0] == "tools/start_search_mcp.sh"` (the
  wrapper script path, not `search_mcp.py` directly).
- Add one new assertion (either as a 3rd test or appended to one of the two above) that
  `tools/start_search_mcp.sh`'s own text invokes `python3` — e.g. `"python3" in (_REPO_ROOT /
  "tools" / "start_search_mcp.sh").read_text()` — so the full chain (`.mcp.json` → wrapper → real
  interpreter) is proven end-to-end, not just one hop of it.

### Group 8 — `ENTITY-003` evidence citation (`test_entity_event_ledger.py`)

Ran the failing test directly; the real root cause is **more precise** than the ticket's own
framing ("cites evidence path `event_extractor.py` (bare filename)"). `docs/event_ledger/
entity.yaml:30`'s `ENTITY-003.evidence` string **already** leads with the fully-qualified
`"src/observability/event_extractor.py (multiple sites); ..."` — that leading citation is correct.
The actual bug is a **second, incidental bare mention deep in the descriptive prose**, in the
sentence `"...combat_hard_law_violation remains event_extractor.py-only, not shaper-migrated."`
`test_entity_ledger_evidence_citations_are_real_files`'s regex-extraction branch (triggered because
the *first* token already matches `src/observability/event_extractor.py`, test file line 37) runs
`re.findall(r"[\w./]+\.py", evidence)` against the **whole** evidence string, and this regex
incidentally captures the bare `"event_extractor.py"` substring out of `"event_extractor.py-only"`
(word-character boundary stops the match right before the `-`) — a real filename-shaped substring
that is not itself a path citation, just a possessive/adjectival mention. `Path("event_extractor.py").exists()`
correctly fails since no such file exists at repo root. Fix: prefix that second mention with the
real path too — `"combat_hard_law_violation remains event_extractor.py-only"` →
`"combat_hard_law_violation remains src/observability/event_extractor.py-only"` — in
`docs/event_ledger/entity.yaml:30`, so every `.py`-shaped regex match in the string resolves to a
real, existing path. This is the same outcome the ticket describes (correct the citation to the
real path) with the precise mechanism identified.

## Mechanics / Engine Constraints

None of the 8 groups touch simulation mechanics (`docs/mechanics/`) or engine contracts
(`docs/engine/`) behavior — this is entirely a `tests/tools` infrastructure/documentation
correctness sweep. `docs/mechanics/content_usage_matrix.md` (Group 2) is a supporting content-
resolution reference cited in CLAUDE.md's Mechanics Bible table, not one of the 6 numbered/
Certified chapters — its frontmatter gap does not affect any formula/law parity claim.

## Docs Requiring Update

- `docs/mechanics/content_usage_matrix.md`: frontmatter gap fixed at the generator
  (`src/content/matrix.py::generate_matrix_report()`), which is what actually produces this file's
  content on every relevant test run — the `.md` file itself is a build artifact, not hand-edited.
- `docs/event_ledger/entity.yaml`: `ENTITY-003`'s evidence string corrected so its second
  `event_extractor.py` mention carries the real `src/observability/` prefix (Group 8).

**Post-Implement update (Verify phase, 2026-08-17):** the actual Implement-time scope for both
items above ended up wider than this list originally named, per the loop-stops-at-first-failure
guard shape disclosed in `plan.md`'s Deviations section:
- `docs/event_ledger/entity.yaml`: 3 additional malformed evidence citations beyond `ENTITY-003`
  were found and fixed the same way — `ENTITY-007` (same bare `event_extractor.py`-only pattern),
  `ENTITY-014` (bare `evolution.py` → `src/engine/evolution.py`), and `ENTITY-015` (a 3-file
  citation malformed as one concatenated path → 3 properly comma-separated real paths under
  `src/engine/`). All 4 citations independently re-verified against the real filesystem at Verify
  time; every cited path exists.
- `docs/REGISTRY.yaml` also required regeneration as a direct consequence of the
  `content_usage_matrix.md` frontmatter fix (it became newly-registrable), per CLAUDE.md's
  unconditional-regeneration-on-doc-change convention — not itself a hand-edited doc, but flagged
  here since it wasn't named in this section's original list.

No `docs/parity_ledger/*.yaml` entry, Mechanics Bible chapter, or engine contract needs updating —
none of the 8 groups change simulation behavior, only test/doc infrastructure correctness.

## Parity Ledger Overlap

None. No parity ledger entry references any of the 8 affected test files or the 2 doc paths above.

## Prior Work

- `stored_artifacts/TCK-20260710-EPIC-STALENESS-CHECK/` and
  `stored_artifacts/TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK/` — original authoring intent for
  `tools/agent-monitoring/epic_staleness_check.py` and its test suite; confirms Decision 5's
  "never flag zero-activity epics stale" rule and that `TCK-20260702-OBSISO-EPIC` was chosen at
  authoring time specifically as "the repo's real live proof of the never-started case" (module
  docstring, lines 7-12) — precisely the shape that no longer exists live, motivating the synthetic
  fixture recommendation here.
- `stored_artifacts/TCK-20260731-PARITY-READPATH-GATE/{investigation,plan,test_plan}.md` — full
  original design of the gate_a corpus/results mechanism; confirms the corpus was always meant to
  live only in `staging_artifacts/` (never `stored_artifacts/`) and was never listed as a
  Finalize-migrated artifact, explaining why it has zero git history.
- `docs/ai/parity_readpath_gate_a_decision.md` — the GO decision doc; its own §6 Limitations
  sections were cross-checked against the corpus provenance question and found unrelated (they
  discuss retrieval-surface gaps, not corpus custody).
- This session's 3 prior KGMCP tickets (`TCK-20260815-KGMCP-P4-PARITY-ADAPTER`,
  `TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`, and one earlier) already
  established the "narrow a stale frozen-hash dict entry, with a disclosure comment" precedent
  this ticket's Group 3 fix reuses verbatim (see
  `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py:102-113`'s own comment block).

## Risks and Open Questions

All 3 of the ticket's own flagged open questions are resolved above (Groups 2, 4, 5) with no
remaining blocking unknowns. One additional real failure was found beyond the ticket's own named
scope (Group 7's `test_args_point_to_search_mcp`, folded into that group's fix above) — the
ticket's "23 failed + 7 errors" aggregate was a point-in-time count from a prior session; this
investigation re-verified every group against the current tree rather than trusting that count,
per CLAUDE.md's Investigate-phase discipline, and found the total real failure count today is one
higher than named (still fully covered by the 8 groups' fixes, no 9th group needed). Residual,
non-blocking item for Implement:

- Group 1: confirm at Implement time that adding `@pytest.mark.slow` to only the 2 identified
  functions (not whole modules) is sufficient — i.e., that the remaining tests in each file stay
  under budget together with the rest of the `api-tools` job's full command
  (`tests/api tests/cli tests/tools tests/logging tests/engine tests/observability`), not just in
  isolation as measured here.

## Anti-Drift Hazards

- **Group 3/Group 4**: do not remove or weaken any *other* dict entry beyond the one confirmed
  stale per file — each remaining entry still correctly protects real Out-of-Scope files for those
  historical decision-document-only tickets.
- **Group 4**: do not, under any framing, author new `SYN-*` synthetic fixture content to "restore"
  the corpus — this is the one thing the ticket's Out of Scope section explicitly forbids, and it
  is very tempting since the test module's own hardcoded IDs (`SYN-P0PAIR-001` etc.) make a
  plausible-looking reconstruction easy to fabricate. The skip-with-disclosure design above is the
  only acceptable resolution.
- **Group 5**: do not repurpose `codex-runtime-activation/` as the new fixture target — confirmed
  above it has real activity and would misrepresent the "never-started" semantic; use a synthetic
  `tmp_path` fixture only.
- **Group 7**: verify the *whole* chain (`.mcp.json` → wrapper script → real python3 invocation),
  not just the top-level `command` field — a shallow fix that only flips the literal string without
  reading `tools/start_search_mcp.sh` would miss `test_args_point_to_search_mcp`'s own now-stale
  assumption (see Risks above).
- **Group 8**: do not remove the `src/observability/event_extractor.py (multiple sites)` correct
  leading citation while fixing the second bare mention — both need to stay valid.
- **General**: every fix in this ticket must be a correction to a real, confirmed stale reference —
  never a loosened assertion. This investigation re-ran every failing test directly rather than
  trusting the ticket's own prior description, per CLAUDE.md's Investigate-phase search-and-verify
  discipline.
