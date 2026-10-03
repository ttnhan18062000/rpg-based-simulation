---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M2-MAPPING-DRIFT-DETECTION
artifact_type: test_plan
tags: [architecture, schema, registry]
---

# Test Plan — TCK-20260924-M2-MAPPING-DRIFT-DETECTION

## Regression Surface

Existing tests that must keep passing (none are expected to change behavior — this ticket adds a
new, read-only module and a new `make` target; it does not modify any existing registry, validator,
or generated view):

**Unit — semantic control plane / mechanism registry:**
- `tests/unit/tools/test_semantic_control_plane_schema.py` — the three M0 schema validators
  (`validate_rule_mechanism_edges`, `validate_mechanism_causal_edges`, `validate_rule_classifications`,
  `check_duplicate_keys`, `validate_all`), including `test_documented_cli_invocation_actually_runs`
  (subprocess) and `test_all_three_schemas_pass_on_real_seed_data` (must still pass unmodified —
  M2 must not alter any committed registry file, per the ticket's own AC).
- `tests/unit/tools/test_territory_control_view.py` — the M1 six-axis Territory view generator;
  must remain unaffected since M2 only reads `rule_mechanism_edges.yaml`/`rule_classifications.yaml`,
  never writes them.
- `tests/unit/tools/test_mechanism_registry.py` — `MechanismRegistry`, `validate()`,
  `parse_implemented_by_entry`, `symbol_defined_in_file` — the read surface M2's own detector reuses;
  must stay green since M2 imports these functions without modification.
- `tests/unit/tools/test_mechanism_registry_changed_code_check.py` — the structural precedent this
  ticket's own module mirrors (pure-core/git-wrapper split, report-only exit-0 convention, planted-
  fixture test pattern). Not touched by this ticket, but its passing state confirms the precedent
  pattern still behaves as documented before M2 mirrors it.

**Integration:**
- Any `tests/unit/tools/conftest.py`-scoped autouse fixtures (e.g. `_empty_system_registry_by_default`)
  must continue to apply cleanly to the new test module the same way they already apply to
  `test_mechanism_registry.py` and `test_semantic_control_plane_schema.py`.

No `arena-combat` or simulation-behavior regression surface applies — this ticket touches no `src/`
code and no simulation-behavior path.

## New Tests Required

Per acceptance criteria, in `tests/unit/tools/test_semantic_control_plane_drift_detector.py` (new
file — **not** `tests/tools/`, correcting the ticket's own Scope line; see investigation.md's
Current Behavior section for the verified reason):

1. **`test_pure_core_takes_no_git_dependency`**
   - Category: architecture guard
   - Verifies: the pure-core drift-check function(s) accept only already-loaded dicts/data
     structures and a comparison date/reference — no `subprocess`, no `git` invocation, importable
     and callable with zero filesystem/git access beyond the passed-in arguments. Mirrors
     `mechanism_registry_changed_code_check.py`'s own `check_drift(old_data, new_data,
     changed_files)` purity, confirmed by that module's own docstring (`:14-18`, "No git dependency,
     no subprocess -- this is what the tests exercise directly").
   - Where: `tests/unit/tools/test_semantic_control_plane_drift_detector.py`

2. **`test_drift_class_1_fires_on_planted_stale_citation`**
   - Category: unit (deliberately-broken-fixture proof, per `TCK-20260920-MECHANISM-REGISTRY-
     CI-WIRING`'s own discipline and this ticket's own AC)
   - Verifies: given a synthetic mapped mechanism whose `implemented_by`-cited file's last-commit
     date is *after* the mapping row's own recorded `date`, the detector reports drift for that row.
     A fixture with the cited file's last-commit date *on or before* the row's date must NOT report
     drift (positive + negative control, mirroring `test_negative_control_flags_code_changed...` /
     `test_positive_control_does_not_flag...` pattern in the mechanism-registry precedent).
   - Where: same file. Likely needs a disposable temp git repo (`tmp_path`/`monkeypatch`, mirroring
     `_init_temp_repo`/`_commit`/`_in_temp_repo` from `test_mechanism_registry_changed_code_check.py:
     182-210`) so real commit dates can be planted deterministically.

3. **`test_drift_class_1_silent_when_cited_file_unchanged_since_review`**
   - Category: unit (clean-data control)
   - Verifies: a mapping row whose cited file's last commit predates the row's own `date` produces
     no finding — proves the detector isn't unconditionally firing.
   - Where: same file.

4. **`test_drift_class_3_fires_on_planted_verdict_change`**
   - Category: unit (deliberately-broken-fixture proof)
   - Verifies: given a planted git history where `registries/mechanisms.yaml` at the commit on/before
     a row's `review_date` shows one `verified.verdict` for the mapped mechanism, and the live/current
     registry shows a different `verified.verdict` for the same id, the detector reports drift for
     that row, naming the old and new verdict values (both drawn from `VALID_VERDICTS`, per the
     status-vocabulary AC).
   - Where: same file, same disposable-temp-git-repo pattern, with two commits touching
     `registries/mechanisms.yaml`.

5. **`test_drift_class_3_silent_when_verdict_unchanged_since_review`**
   - Category: unit (clean-data control)
   - Verifies: no finding when the recovered review-time verdict equals the current verdict.
   - Where: same file.

6. **`test_drift_class_3_review_time_recovery_uses_commit_not_bare_date_string`** (only if the
   implementer adopts investigation.md's same-day-pinning recommendation; otherwise substitute with
   a test asserting the chosen same-day tie-break rule explicitly, per the ticket's own "state it in
   a test" instruction for the date-interpretation open question)
   - Category: unit (edge case / regression-prone path)
   - Verifies: when two commits touch `registries/mechanisms.yaml` on the exact same calendar date as
     a row's own `date`/`review_date`, the detector resolves review-time state deterministically
     (documenting which one wins), not by an unstated implicit rule.
   - Where: same file.

7. **`test_drift_class_2_descope_documented_or_signal_absent`** (only if class 2 is descoped per
   investigation.md's recommendation — otherwise substitute with `test_drift_class_2_fires_on_planted_
   split_signal` proving whatever mechanical signal the implementer actually built)
   - Category: architecture guard
   - Verifies: if descoped, this is not a runtime test but a documentation check — the ticket's own
     Completion Summary / investigation.md must record the written reason (AC requires this, not a
     test). If NOT descoped (implementer finds a signal this investigation missed), this test must
     prove the detector fires on a deliberately-planted split/merge fixture the same way classes 1
     and 3 do — no clean-only test is acceptable per the ticket's own AC.
   - Where: same file (only if class 2 ships code) or noted as N/A with a pointer to the ticket's own
     Completion Summary disposition.

8. **`test_report_only_exits_zero_with_findings_present`**
   - Category: unit (report-only contract, explicitly required by AC)
   - Verifies: `main()` (or equivalent CLI entry point) returns 0 even when one or more of the
     planted-drift fixtures above produce findings — mirrors
     `test_main_always_exits_zero`/`test_ticket_id_cli_path_never_fails_even_with_findings` from the
     mechanism-registry precedent.
   - Where: same file.

9. **`test_make_target_runs_clean`**
   - Category: integration
   - Verifies: `make <the chosen target name, e.g. semantic-control-plane-drift-check>` runs via
     `subprocess.run(["make", "<target>"], cwd=REPO_ROOT, ...)` and exits 0 against the real
     committed registries — mirrors `test_make_target_runs_clean` in the mechanism-registry precedent
     exactly (`tests/unit/tools/test_mechanism_registry_changed_code_check.py:153-159`).
   - Where: same file.

10. **`test_registries_still_validate_clean_after_running_detector`**
    - Category: architecture guard (explicit AC: "M2 must not alter the committed mapping files")
    - Verifies: running the detector against the real committed registries, then re-running
      `tools/semantic_control_plane/registry.py`'s own `validate_all()` (or the documented CLI
      invocation via subprocess, mirroring `test_documented_cli_invocation_actually_runs`), still
      returns zero errors — proves the detector is read-only in practice, not just by code
      inspection.
    - Where: same file.

11. **`test_detector_status_words_resolve_to_status_axis_model_vocabulary`**
    - Category: architecture guard (explicit AC: "Every status word in the output resolves to
      `docs/plans/status_axis_model.md`'s vocabulary — do not mint new ones")
    - Verifies: every echoed registry value in the detector's own report output (e.g. an old/new
      `verified.verdict` pair) is a member of `VALID_VERDICTS`/`VALID_STATES`/
      `VALID_RULE_CLASSIFICATIONS` as appropriate — never a term invented for the report itself
      (report-level words like "STALE"/"CLEAN"/"DRIFT" are the detector's own prose, not axis
      vocabulary, and are out of this test's scope per investigation.md's own reading of the AC).
    - Where: same file.

12. **`test_live_run_against_territory_mapping_reports_or_records_finding`**
    - Category: integration (explicit AC: "Running it against M1's live Territory mapping produces a
      report")
    - Verifies: the git-backed wrapper, run against the real committed `registries/
      rule_mechanism_edges.yaml`/`rule_classifications.yaml`/`registries/mechanisms.yaml`, completes
      without error and produces a report (finding count, even if zero). This is the same-day
      case noted in investigation.md — a "clean today" result is expected and acceptable per the
      ticket's own exit criterion, but the test must actually run the real path, not assert on a
      mocked one, so a real finding (if any) is caught rather than assumed away.
    - Where: same file.

## Scoped Pytest Commands

```
python3 -m pytest tests/unit/tools/test_semantic_control_plane_drift_detector.py -v
python3 -m pytest tests/unit/tools/ -k "semantic_control_plane or mechanism_registry" -v
```

The second command re-runs the full regression surface named above (schema validators, territory
view, mechanism registry, changed-code-check precedent) alongside the new module in one scoped pass —
never `pytest tests/`.

## Anti-Drift Test Guards

- **`test_registries_still_validate_clean_after_running_detector`** (New Test #10) is the direct
  guard against the detector accidentally mutating `registries/*.yaml` — the exact scope-creep this
  ticket's own AC calls out by name.
- **`test_report_only_exits_zero_with_findings_present`** (New Test #8) guards against a future
  editor turning this into a blocking gate/ratchet by accident — the ticket's Out of Scope is
  explicit that this must never happen, and CI-wiring is deferred to a later milestone.
- **`test_pure_core_takes_no_git_dependency`** (New Test #1) guards against the exact shape mistake
  the ticket's own Scope warns against — silently copying `mechanism_registry_changed_code_check.py`'s
  two-ref-diff (`--base`/`--head`) axis instead of building the per-row-date axis M2 actually needs.
  A test that only checks the *output* is correct would not catch a wrong internal shape that happens
  to produce the same answer on today's clean data; this test checks the *signature*/dependency shape
  directly.
- **`test_no_function_derives_classification_from_edges`** (existing, `tests/unit/tools/
  test_semantic_control_plane_schema.py:387-400`) — re-run as part of the regression surface, not
  duplicated, but worth naming explicitly here: if the M2 detector ever grows a "suggest a new
  classification" helper, this existing test's own scanning approach is the guard that would need
  extending to also scan the new module, and the implementer should be aware of it rather than
  assume it only covers M0/M1 code.
- **`test_detector_status_words_resolve_to_status_axis_model_vocabulary`** (New Test #11) guards
  against a minted status word entering the report output silently — the exact drift the ticket's own
  AC line about `status_axis_model.md` exists to prevent.
