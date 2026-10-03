---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-BASELINE-METRICS
artifact_type: test_plan
tags: [agent-monitoring, observability]
---

# Test Plan — TCK-20260728-RETRIEVAL-BASELINE-METRICS

## Regression Surface

This ticket adds a new module and must not touch any existing one — every test below must pass
**unmodified** before and after this ticket's changes land.

**Unit — `tools/agent-monitoring/` pure-function modules:**
- `tests/tools/test_agent_monitoring_legacy_reader.py` (240 lines) — `classify_provenance()` and
  its 6 runs-shapes + tools/events null-gap rules. This ticket's new tool imports
  `classify_provenance` read-only; this suite proves that import didn't change its behavior.
- `tests/tools/test_agent_monitoring_manifest.py` (158 lines) — `build_manifest()`,
  reproducibility, streaming-only guard, zero-mutation integration test. Direct sibling precedent
  for this ticket's own tool; must stay green as proof the precedent pattern itself is undisturbed.
- `tests/tools/test_validate_agent_monitoring.py` (448 lines) — `_record_is_complete()`,
  `compute_drift_report()`, `compute_tool_count_drift_report()`,
  `compute_multi_invocation_collision_report()`, vocabulary single-source guard.
- `tests/tools/test_cost_proxy.py` (57 lines) — `compute_cost_proxy_score()` formula.
- `tests/tools/test_generate_retro.py` (1,014 lines) — `compute_retro_metrics()`,
  `_resolve_status`, `_is_gate_fail`, `_normalize_phase`/`_normalize_agent`, outlier flagging, tag
  breakdown, reason-code aggregation, spend proxy. The single largest regression surface this
  ticket's own reuse touches (`_load_runs_and_events`, `_resolve_status`, `_is_gate_fail` are all
  candidates for direct import).

**Integration — writer/consent boundary (adjacent, must not regress even though untouched):**
- `tests/tools/test_monitoring_writer.py`, `test_monitoring_writer_single_source.py`,
  `test_monitoring_writer_lockfile_candidate.py` — prove `writer.py` remains the sole append path;
  this ticket's tool must never call any of these writers.
- `tests/agent_replay_codex/` + `tests/agent_codex_pilot_guardrails/` (61 passed / 5 consent-gated
  skipped per `TCK-20260728-PHASE0-PREREQ-CONFIRMATION`'s confirmed baseline) — not directly touched
  by this ticket, but its `baseline_manifest_gate.py` imports `manifest.py`'s
  `capture_lines`/`assert_prefix_preserved` via `importlib.util.spec_from_file_location`; if this
  ticket's plan phase decides to extend `manifest.py` itself (it should not — see Anti-Drift Test
  Guards) this suite would be the tripwire.

**Zero-mutation precedent to mirror:**
- `tests/agent_replay/test_no_mutation_snapshot.py` — the dirty-tree-aware pre/post hash-snapshot
  pattern this ticket's own zero-mutation test must copy, scoped to
  `agent-monitoring/*.jsonl` only.

## New Tests Required

Per acceptance criteria (AC1-AC5 from `tickets/inprogress/TCK-20260728-RETRIEVAL-BASELINE-METRICS.md`):

**AC1 — context-tokens explicitly marked 'unavailable'**
- `test_baseline_report_context_tokens_marked_unavailable` — unit. Asserts the report's context-token
  field/section is a literal `"unavailable"` string (not `0`, not `null`, not omitted), and that the
  report's own text cites `docs/agent-monitoring/schema.md`'s "What is not recorded" section (e.g. by
  file path substring) as the source of that determination. Location:
  `tests/tools/test_<new_module>.py` (new file, e.g. `test_retrieval_baseline_metrics.py` — exact
  name is a Plan-phase decision).

**AC2 — follow-up-search-count marked not_yet_instrumented OR derived with cited computation**
- `test_baseline_report_search_count_is_marked_or_derived_never_silent` — unit. Asserts the report's
  search-count field is either the literal string `"not_yet_instrumented"` or a numeric value
  accompanied by an explicit citation string naming the field(s) it was computed from (e.g.
  `tool_call_count`, per the Plan-phase's chosen derivation — see investigation.md Risk #2). Must
  never be a bare number with no accompanying derivation text.
- `test_baseline_report_search_count_derivation_matches_stated_fields` — unit, only if the Plan phase
  chooses a derived (not `not_yet_instrumented`) approach: given a small synthetic `events`/`tools`
  fixture, assert the reported count numerically equals what the stated computation actually
  produces — proves the citation isn't decorative.

**AC3 — phase-duration gap-aware or visibly flagged as pause-contaminated**
- `test_baseline_report_flags_duration_as_pause_contaminated_when_no_gap_aware_view_exists` — unit.
  Given `duration_utils.py` does not exist (confirmed in investigation.md), asserts every
  duration-bearing row/section in the report carries an explicit contamination-flag marker string
  (e.g. `"pause-contaminated"` or equivalent), never presenting `duration_s` unqualified.
- `test_baseline_report_would_prefer_gap_aware_view_if_available` — unit, forward-looking guard:
  monkeypatches/imports a stub `duration_utils`-shaped callable (or asserts via `importlib.util.find_spec`
  that the module is absent today) so that if `idea_agent_monitoring_active_duration.md` is
  implemented later, this test starts failing loudly (module now exists but report still only
  flags-contaminated instead of using it) rather than silently drifting out of date. This is the
  explicit "the caveat itself has an expiry condition" guard the ticket's Out-of-Scope note implies.

**AC4 — test/gate outcome and review-rework derived only from existing fields, documented as proxy**
- `test_baseline_report_gate_outcome_uses_final_status_and_reason_code_only` — unit. Given a
  synthetic `runs`/`events` fixture, asserts the report's gate-outcome section is computed purely
  from `final_status`/`reason_code`/Review-Architecture-Verify `status` transitions (reusing
  `_resolve_status`/`_is_gate_fail`-equivalent logic, imported not reimplemented) and carries an
  explicit "derived proxy, not fabricated" disclosure string.
- `test_baseline_report_review_rework_proxy_requires_multi_record_same_run_id` — unit. Synthetic
  fixture: one `run_id` with two `runs.jsonl`-shaped records (`NEEDS_CHANGES` then later `DONE`);
  asserts this is flagged as rework. A second `run_id` with only a single terminal-non-DONE record
  and no later record must NOT be flagged as rework (proves the proxy doesn't conflate "failed and
  abandoned" with "failed and reworked").
- `test_baseline_report_review_rework_proxy_ignores_reason_code_alone` — unit, anti-drift-shaped:
  asserts a run with `reason_code` populated but only ever one terminal record is not counted as
  "reworked" — guards against the exact hazard named in investigation.md ("do not fabricate a
  review-rework count from `reason_code_breakdown` alone").

**AC5 — zero mutation of `agent-monitoring/*.jsonl`**
- `test_baseline_report_tool_causes_zero_diff_on_real_corpus` — integration, mirrors
  `tests/agent_replay/test_no_mutation_snapshot.py` and
  `test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff`:
  dirty-tree-aware pre/post `git status --porcelain -- agent-monitoring/` snapshot (or SHA-256
  content-hash fallback if the tree is already dirty) around a real invocation of the new tool
  against the live corpus.
- `test_baseline_report_tool_never_imports_writer_module` — unit/static, `ast`-based source scan of
  the new module (mirrors `test_agent_monitoring_manifest.py`'s streaming-guard style): asserts no
  `import` of `tools/agent-monitoring/writer.py`, `record_run.py`, `record_events.py`, or
  `post_tool_hook.py`, and no call to `open(..., "w")`/`open(..., "a")` anywhere in its source.

**Reuse-not-reimplement guards (explicit ticket requirement, not tied to a single AC letter):**
- `test_baseline_report_reuses_classify_provenance_not_reimplemented` — unit, mirrors
  `test_tag_breakdown_uses_registry_categorize_tag_not_reimplemented_lookup`'s style in
  `test_generate_retro.py`: asserts the new module's source imports `classify_provenance` from
  `tools/agent-monitoring/legacy_reader.py` (via `ast`/source-text check) rather than containing its
  own inline shape-classification `if`/`elif` chain.
- `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader` — unit: asserts the new module
  either imports `generate_retro.py`'s `_load_runs_and_events` (or an equivalently-shaped
  index-with-fallback helper) rather than calling `sqlite3.connect()` or `path.read_text()` directly
  in its own top-level data-loading code.

## Scoped Pytest Commands

```bash
# New module's own tests (once named/created by Plan/Implement)
pytest tests/tools/test_retrieval_baseline_metrics.py -v   # exact filename per Plan-phase decision

# Full regression surface for the modules this ticket reuses/reads
pytest tests/tools/test_agent_monitoring_legacy_reader.py \
       tests/tools/test_agent_monitoring_manifest.py \
       tests/tools/test_validate_agent_monitoring.py \
       tests/tools/test_cost_proxy.py \
       tests/tools/test_generate_retro.py -v

# Adjacent writer/consent boundary — confirm untouched
pytest tests/tools/test_monitoring_writer.py \
       tests/tools/test_monitoring_writer_single_source.py \
       tests/tools/test_monitoring_writer_lockfile_candidate.py -v

# Zero-mutation precedent this ticket's own integration test mirrors
pytest tests/agent_replay/test_no_mutation_snapshot.py -v
```

Never run `pytest tests/` for this ticket — scope stays inside `tests/tools/` (agent-monitoring
tooling) plus the one zero-mutation precedent file in `tests/agent_replay/`.

## Anti-Drift Test Guards

- **Reuse-not-reimplement static checks** (listed above under "Reuse-not-reimplement guards") are
  the primary anti-drift mechanism for this ticket's core requirement — the ticket explicitly names
  `legacy_reader.py`'s pattern as "not reimplemented," so a test that only checks *output* equality
  would miss a silent reimplementation that happens to produce the same numbers today but drifts
  the next time a 7th legacy shape is discovered (`classify_provenance` would gain a new rule;
  a reimplemented copy would not).
- **Gate-outcome/rework fabrication guard** (`test_baseline_report_review_rework_proxy_ignores_reason_code_alone`)
  — directly protects against the single most likely silent-scope-creep failure mode: quietly
  treating an existing coarse signal (`reason_code_breakdown`) as if it answered a question
  (`was this ticket reworked?`) it was never designed to answer.
- **Duration-caveat expiry guard** (`test_baseline_report_would_prefer_gap_aware_view_if_available`)
  — protects against this ticket's read-only baseline report silently becoming stale/wrong the
  moment `idea_agent_monitoring_active_duration.md` ships a real `duration_utils.py`, without anyone
  updating this ticket's own report tool.
- **Zero-mutation integration test** (`test_baseline_report_tool_causes_zero_diff_on_real_corpus`) —
  protects the hard repo-wide invariant ("append-only, never rewritten") that every prior
  agent-monitoring tooling ticket in this lineage
  (`TCK-20260721-BASELINE-MONITORING-MANIFEST`, `TCK-20260713-MONITORING-*-INDEX-MIGRATE`) has
  independently re-verified rather than assumed.
- **AC-marker-string presence tests** (AC1/AC2/AC3/AC4's first test each) — protect against the
  report silently degrading from "explicitly marked unavailable/derived-with-citation/flagged" to
  "silently omitted" in a future edit; each test asserts the literal marker string is present, not
  just that *some* value renders, so a future refactor that drops the caveat text (while leaving a
  numeric field in place) fails loudly instead of passing on output-shape alone.
- **No-writer-import static guard** (`test_baseline_report_tool_never_imports_writer_module`) —
  protects the CLAUDE.md-level invariant that this is a strictly read-only reporting tool, catching
  an accidental future edit that starts importing `writer.py` (e.g. to "helpfully" persist the
  baseline snapshot back into `agent-monitoring/`) before it ships.
