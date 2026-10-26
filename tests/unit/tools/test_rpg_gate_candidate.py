"""TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS: harness documents -> candidate -> v1 -> the report passes; each refusal; owned fails omitted."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from tools.test_architecture import rpg_gate_baseline as base
from tools.test_architecture import rpg_gate_candidate as cand
from tools.test_architecture import rpg_gate_report as rep

TODAY = dt.date(2026, 10, 11)
SEEDS = (1, 2, 3)
SHA, HASH = "abc123", "hash1"
KNOWN_SHA = "a" * 64
MAIN_CI_ENV = {"GITHUB_RUN_ID": "39799337778", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main"}
ORACLE = "docs/mechanics/02_combat_laws.md"


def _config(**over) -> base.GateConfig:
    args = dict(worlds=("w",), seeds=SEEDS, ticks=100, stale_after_days=30)
    args.update(over)
    return base.GateConfig(**args)


def _seed_doc(seed, *, v3=0, sha=SHA, hhash=HASH, ticks=100, k=2.0, floor=1.0, value=None, floor_rel=None):
    return {"schema": "rpg-gate-metrics/v1", "status": "ok", "world": "w", "seed": seed, "ticks": ticks, "sha": sha, "harness_hash": hhash, "metrics": [
        {"id": "O1", "class": "outcome", "scope": "run", "group": "*", "key": "DEATHS", "tick": 100, "value": 10.0 + seed if value is None else value, "k": k, "floor": floor, **({"floor_rel": floor_rel} if floor_rel is not None else {})},
        {"id": "V1", "class": "validity", "scope": "run", "group": "*", "violations": 0, "examples": [], "oracle": ORACLE},
        {"id": "V3", "class": "validity", "scope": "run", "group": "wolves", "violations": v3, "examples": ["x"] if v3 else [], "oracle": ORACLE},
    ]}


def _pooled_doc(*, v3=0, sha=SHA, hhash=HASH):
    return {"schema": "rpg-gate-metrics/v1", "status": "ok", "world": "w", "ticks": 100, "sha": sha, "harness_hash": hhash, "metrics": [
        {"id": "V3", "class": "validity", "scope": "pooled", "group": "wolves", "violations": v3, "examples": [], "oracle": ORACLE},
        {"id": "O9", "class": "outcome", "scope": "pooled", "group": "*", "value": 0.4, "floor": 0.1},
    ]}


def _write(directory: Path, docs=None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    docs = docs if docs is not None else {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}
    for (world, seed), doc in docs.items():
        (directory / (f"{world}__s{seed}.json" if seed is not None else f"{world}__pooled.json")).write_text(json.dumps(doc, sort_keys=True))
    return directory


def _entry(match="V3:wolves", ticket="TCK-OWN", expires="2026-12-31"):
    return {"match": match, "ticket": ticket, "owner": "rpg", "added_on": "2026-10-01", "expires_on": expires, "state": "fail"}


def _report(*findings, skipped=(), sha=SHA):
    return {"schema": "rpg-gate-report/v1", "sha": sha, "harness_hash": HASH, "findings": list(findings), "rerun": {"performed": True, "not_performed_budget": [list(p) for p in skipped]}}


def _build(directory, known=(), **kw):
    kw.setdefault("known_file_sha256", KNOWN_SHA)
    kw.setdefault("env", MAIN_CI_ENV)  # a main CI run, so the candidate can become a baseline; the tests that need no CI pass env={}
    return cand.build_candidate(directory, kw.pop("config", _config()), list(known), kw.pop("report", _report()), today=TODAY, **kw)


# ---- the round trip

def test_documents_to_candidate_to_v1_to_an_all_pass_report(tmp_path):
    docs_dir = _write(tmp_path / "docs")
    candidate = _build(docs_dir, milestone="M0")
    out = tmp_path / "candidate.json"
    out.write_text(cand.dump_candidate(candidate))
    baselines = tmp_path / "baselines"
    target = base.rebaseline(json.loads(out.read_text()), _config(), baselines, pr=None, cites=["TCK-METRIC-SET"], now=dt.datetime(2026, 10, 11, tzinfo=dt.timezone.utc))
    assert target.name == "rpg_gate_v1.json" and base.lint_dir(baselines) == []
    refs = base.resolve_references(base.load_baselines(baselines))
    docs = rep.load_documents(docs_dir, _config())
    findings = rep.evaluate(docs, _config(), refs, {}, HASH)
    assert findings and {f["state"] for f in findings} == {rep.PASS}
    # both references are v1 itself
    assert refs.last is refs.milestone_first or refs.last["version"] == refs.milestone_first["version"] == 1


def test_candidate_rows_carry_the_statistics_and_thresholds(tmp_path):
    candidate = _build(_write(tmp_path / "docs"), milestone="M0", commit_sha=SHA)
    assert candidate["provenance"] == {"commit_sha": SHA, "harness_hash": HASH, "worlds": ["w"], "seeds": [1, 2, 3], "ticks": 100,
                                    "known_file_sha256": KNOWN_SHA, "ci": {"run_id": "39799337778", "run_attempt": "1", "event_name": "workflow_dispatch", "ref": "refs/heads/main"}}
    rows = {(r["id"], r["scope"]): r for r in candidate["metrics"]}
    o1 = rows[("O1", "run")]
    assert o1["per_seed"] == {"1": 11.0, "2": 12.0, "3": 13.0} and o1["mean"] == 12.0 and o1["se"] == pytest.approx(1 / 3 ** 0.5)
    assert (o1["k"], o1["floor"], o1["key"], o1["tick"]) == (2.0, 1.0, "DEATHS", 100)
    assert rows[("O9", "pooled")]["value"] == 0.4 and rows[("O9", "pooled")]["floor"] == 0.1 and "per_seed" not in rows[("O9", "pooled")]
    assert rows[("V1", "run")]["violations"] == 0 and rows[("V1", "run")]["oracle"] == ORACLE and rows[("V1", "run")]["per_seed"] == {"1": 0, "2": 0, "3": 0}
    assert rows[("V3", "pooled")]["violations"] == 0
    assert "version" not in candidate and "rebaseline" not in candidate and "omitted_validity" not in candidate


def test_the_same_inputs_give_a_byte_identical_candidate(tmp_path):
    a = cand.dump_candidate(_build(_write(tmp_path / "a"), milestone="M0"))
    b = cand.dump_candidate(_build(_write(tmp_path / "b"), milestone="M0"))
    assert a == b


# ---- refusals

def _refused(directory, match, known=(), **kw):
    with pytest.raises(cand.CandidateRefused, match=match):
        _build(directory, known, **kw)


def test_a_no_data_document_refuses_naming_the_document_and_reason(tmp_path):
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}
    docs[("w", 2)] = {"status": "no-data", "reason": "run_error", "world": "w", "seed": 2, "metrics": [], "error": "boom"}
    _refused(_write(tmp_path / "d", docs), r"w__s2\.json: no-data \(run_error\)")


def test_a_missing_or_unexpected_document_is_a_matrix_mismatch(tmp_path):
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}
    del docs[("w", 3)]
    _refused(_write(tmp_path / "missing", docs), r"w__s3\.json is missing")
    full = _write(tmp_path / "extra")
    (full / "w__s9.json").write_text(json.dumps(_seed_doc(9)))
    _refused(full, r"w__s9\.json is not a \(world, seed\)")


def test_sha_and_harness_hash_must_agree(tmp_path):
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}
    docs[("w", 2)] = _seed_doc(2, sha="other")
    _refused(_write(tmp_path / "sha", docs), "disagree on the commit sha")
    docs[("w", 2)] = _seed_doc(2, hhash="other")
    _refused(_write(tmp_path / "hash", docs), "disagree on the harness hash")
    _refused(_write(tmp_path / "ok"), "not the requested commit", commit_sha="zzz")


def test_ticks_must_equal_the_config(tmp_path):
    docs = {**{("w", s): _seed_doc(s, ticks=50) for s in SEEDS}, ("w", None): _pooled_doc()}
    _refused(_write(tmp_path / "d", docs), r"ran 50 ticks, the config says 100")


def test_fewer_than_two_seeds_refuses(tmp_path):
    _refused(_write(tmp_path / "d", {("w", 1): _seed_doc(1), ("w", None): _pooled_doc()}), "at least 2", config=_config(seeds=(1,)))


def test_a_threshold_mismatch_across_documents_refuses(tmp_path):
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}
    docs[("w", 3)] = _seed_doc(3, floor=5.0)
    _refused(_write(tmp_path / "d", docs), "threshold mismatch for O1")


def test_an_outcome_row_without_k_or_floor_refuses(tmp_path):
    docs = {**{("w", s): _seed_doc(s, k=None) for s in SEEDS}, ("w", None): _pooled_doc()}
    _refused(_write(tmp_path / "d", docs), "no numeric k and floor")


def test_a_row_absent_from_one_seed_refuses(tmp_path):
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}
    docs[("w", 2)]["metrics"] = [m for m in docs[("w", 2)]["metrics"] if m["id"] != "O1"]
    _refused(_write(tmp_path / "d", docs), r"O1 \(group \*\) is absent from seed\(s\) \[2\]")


def test_a_keyed_row_absent_from_one_seed_refuses_with_the_row_set_text(tmp_path):
    """The row set is declared by the module and nothing is imputed (TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED): a keyed count row a seed omits is a refusal."""
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}
    for seed in SEEDS:
        docs[("w", seed)]["metrics"].append({"id": "O4", "class": "outcome", "scope": "run", "group": "meat", "key": "eaten", "tick": 100, "value": 2.0, "k": 2.0, "floor": 1.0})
    docs[("w", 3)]["metrics"] = [m for m in docs[("w", 3)]["metrics"] if m["id"] != "O4"]
    _refused(_write(tmp_path / "d", docs), r"row O4 \(group meat\) is absent from seed\(s\) \[3\]; every seed must report the same rows")


# ---- validity fails: owned ones are omitted and recorded, others refuse

def _failing(v3=2):
    return {**{("w", s): _seed_doc(s, v3=v3 if s == 2 else 0) for s in SEEDS}, ("w", None): _pooled_doc(v3=v3)}


def test_an_owned_validity_fail_is_omitted_and_recorded(tmp_path):
    candidate = _build(_write(tmp_path / "d", _failing()), [_entry()], milestone="M0")
    assert not [r for r in candidate["metrics"] if r["id"] == "V3"]
    assert candidate["omitted_validity"] == [
        {"row": "V3:pooled:w:wolves", "known_match": "V3:wolves", "ticket": "TCK-OWN"},
        {"row": "V3:run:w:wolves", "known_match": "V3:wolves", "ticket": "TCK-OWN"},
    ]
    baselines = tmp_path / "b"
    base.rebaseline(candidate, _config(), baselines, pr=None, cites=["TCK-METRIC-SET"], known=[_entry()], today=TODAY)
    written = json.loads((baselines / "rpg_gate_v1.json").read_text())
    assert written["omitted_validity"] == candidate["omitted_validity"] and base.lint_dir(baselines) == []


def test_an_unowned_or_expired_or_wrong_state_validity_fail_refuses(tmp_path):
    docs = _write(tmp_path / "d", _failing())
    _refused(docs, r"w__s2\.json: validity row V3 has 2 violation\(s\) and no owner", [])
    _refused(docs, "expired on 2026-10-01", [_entry(expires="2026-10-01")])
    _refused(docs, "no owner", [{**_entry(), "state": "drift"}])
    _refused(docs, "no owner", [_entry(match="V4")])


def test_the_lint_rejects_an_omitted_row_that_is_still_in_metrics(tmp_path):
    candidate = _build(_write(tmp_path / "d"), milestone="M0")
    doc = {"schema": base.SCHEMA, "version": 1, "milestone": "M0", "rebaseline": None,
           "provenance": {**candidate["provenance"], "recorded_at": "2026-10-11T00:00:00Z", "stale_after": "2026-11-10T00:00:00Z", "cites": ["T"]},
           "metrics": candidate["metrics"], "omitted_validity": [{"row": "V1:run:w:*", "known_match": "V1", "ticket": "TCK-X"}]}
    assert any("still in metrics" in p for p in base.lint_baseline(doc))
    doc["omitted_validity"] = [{"row": "V3:run:w:wolves", "known_match": "V3"}]
    assert any("missing ticket" in p for p in base.lint_baseline(doc))
    doc["omitted_validity"] = [{"row": "V4:run:w:wolves", "known_match": "V4", "ticket": "TCK-X"}]
    assert base.lint_baseline(doc) == []


# ---- evidence-only and the CLIs

def test_an_evidence_only_candidate_cannot_become_a_baseline(tmp_path):
    candidate = _build(_write(tmp_path / "d"), milestone="M0", evidence_only=True)
    assert candidate["evidence_only"] is True
    with pytest.raises(base.RebaselineRefused, match="evidence only"):
        base.rebaseline(candidate, _config(), tmp_path / "b", pr=None, cites=["T"])


# ---- the CI run and the known file are recorded (TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE)

def test_a_candidate_records_the_ci_run_and_the_known_file_hash(tmp_path):
    prov = _build(_write(tmp_path / "d"))["provenance"]
    assert prov["known_file_sha256"] == KNOWN_SHA
    assert prov["ci"] == {"run_id": "39799337778", "run_attempt": "1", "event_name": "workflow_dispatch", "ref": "refs/heads/main"}


@pytest.mark.parametrize("env", [{}, {"GITHUB_RUN_ID": "1"}, {**MAIN_CI_ENV, "GITHUB_REF": ""}, {k: v for k, v in MAIN_CI_ENV.items() if k != "GITHUB_EVENT_NAME"}])
def test_ci_is_null_unless_all_four_run_variables_are_set(tmp_path, env):
    assert _build(_write(tmp_path / "d"), env=env)["provenance"]["ci"] is None


def test_a_candidate_with_no_ci_run_or_off_main_cannot_become_a_baseline(tmp_path):
    for env, match in (({}, "no CI run"), ({**MAIN_CI_ENV, "GITHUB_REF": "refs/heads/some-branch"}, "not refs/heads/main")):
        candidate = _build(_write(tmp_path / "d"), env=env)
        with pytest.raises(base.RebaselineRefused, match=match):
            base.rebaseline(candidate, _config(), tmp_path / "b", pr=None, cites=["T"])
    assert not (tmp_path / "b").exists()
    assert base.rebaseline(_build(_write(tmp_path / "d"), milestone="M1"), _config(), tmp_path / "b", pr=None, cites=["T"]).name == "rpg_gate_v1.json"


def test_the_cli_records_the_sha256_of_the_known_file_bytes_and_the_run_from_the_environment(tmp_path, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_text("worlds: [w]\nseeds: [1, 2, 3]\nticks: 100\nstale_after_days: 30\n")
    known = tmp_path / "known.yaml"
    known.write_text("known: []\n# exact bytes, comment included\n")
    report = tmp_path / "report.json"
    report.write_text(json.dumps(_report()))
    args = ["--report", str(report), "--config", str(config), "--docs", str(_write(tmp_path / "ok")), "--known", str(known)]
    for var in MAIN_CI_ENV:
        monkeypatch.delenv(var, raising=False)
    local = tmp_path / "local.json"
    assert cand.main([*args, "--out", str(local)]) == 0
    prov = json.loads(local.read_text())["provenance"]
    assert prov["known_file_sha256"] == hashlib.sha256(known.read_bytes()).hexdigest() and prov["ci"] is None
    for var, value in MAIN_CI_ENV.items():
        monkeypatch.setenv(var, value)
    ci_out = tmp_path / "ci.json"
    assert cand.main([*args, "--out", str(ci_out)]) == 0
    assert json.loads(ci_out.read_text())["provenance"]["ci"]["run_id"] == "39799337778"


def test_the_cli_writes_the_file_or_refuses_without_writing(tmp_path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text("worlds: [w]\nseeds: [1, 2, 3]\nticks: 100\nstale_after_days: 30\n")
    known = tmp_path / "known.yaml"
    known.write_text("known: []\n")
    out = tmp_path / "out" / "candidate.json"
    report = tmp_path / "report.json"
    report.write_text(json.dumps(_report()))
    args = ["--report", str(report), "--config", str(config), "--docs", str(_write(tmp_path / "ok")), "--known", str(known), "--out", str(out), "--milestone", "M0"]
    assert cand.main(args) == 0 and json.loads(out.read_text())["milestone"] == "M0"
    out.unlink()
    bad = ["--report", str(report), "--config", str(config), "--docs", str(_write(tmp_path / "bad", _failing())), "--known", str(known), "--out", str(out)]
    assert cand.main(bad) == 2 and not out.exists()
    assert "REFUSED:" in capsys.readouterr().err


def test_rebaseline_cli_takes_the_milestone(tmp_path):
    candidate = _build(_write(tmp_path / "d"))  # the workflow's candidate has no milestone
    assert "milestone" not in candidate
    with pytest.raises(base.BaselineError, match="missing milestone"):
        base.rebaseline(candidate, _config(), tmp_path / "b1", pr=None, cites=["T"])
    target = base.rebaseline(candidate, _config(), tmp_path / "b2", pr=None, cites=["T"], milestone="M0")
    assert json.loads(target.read_text())["milestone"] == "M0"


# ---- the report must stand behind the run

def test_an_unstable_finding_refuses_naming_the_metric(tmp_path):
    unstable = {"world": "w", "id": "O1", "group": "*", "state": "unstable"}
    _refused(_write(tmp_path / "d"), r"unstable finding.*w/O1", report=_report(unstable))


def test_a_rerun_cut_by_the_budget_refuses_naming_the_unconfirmed_metrics(tmp_path):
    drift = {"world": "w", "id": "O1", "group": "*", "state": "drift"}
    _refused(_write(tmp_path / "d"), r"not performed \(budget\).*w/O1", report=_report(drift, skipped=[("w", 2)]))


def test_a_confirmed_first_pass_drift_or_fail_is_accepted(tmp_path):
    findings = [{"world": "w", "id": "O1", "group": "*", "state": "drift"}, {"world": "w", "id": "V3", "group": "wolves", "state": "fail"}]
    assert _build(_write(tmp_path / "d"), report=_report(*findings), milestone="M0")["metrics"]


def test_a_report_from_other_documents_refuses(tmp_path):
    _refused(_write(tmp_path / "d"), "the report is from sha", report=_report(sha="other"))
    _refused(_write(tmp_path / "e"), "not an rpg-gate-report/v1", report={"findings": []})


# ---- rebaseline re-checks the owners of omitted rows

def test_rebaseline_rechecks_each_omitted_owner_against_the_current_registry(tmp_path):
    candidate = _build(_write(tmp_path / "d", _failing()), [_entry()], milestone="M0")
    kw = dict(pr=None, cites=["T"])
    with pytest.raises(base.RebaselineRefused, match="--known"):
        base.rebaseline(candidate, _config(), tmp_path / "b0", **kw)
    with pytest.raises(base.RebaselineRefused, match="no longer a state: fail entry"):
        base.rebaseline(candidate, _config(), tmp_path / "b1", known=[], **kw)
    with pytest.raises(base.RebaselineRefused, match="expired on 2026-10-01"):
        base.rebaseline(candidate, _config(), tmp_path / "b2", known=[_entry(expires="2026-10-01")], today=TODAY, **kw)
    assert base.rebaseline(candidate, _config(), tmp_path / "b3", known=[_entry()], today=TODAY, **kw).exists()


# ---- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK: the candidate refuses while a required validity row is missing

def _without(docs, row_id):
    return {k: {**d, "metrics": [m for m in d["metrics"] if m["id"] != row_id]} for k, d in docs.items()}


def _full(directory):
    return {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}


def test_a_required_validity_row_present_everywhere_does_not_refuse(tmp_path):
    candidate = _build(_write(tmp_path / "d"), config=_config(required_validity={"run": ("V3",), "pooled": ("V3",)}))
    assert "omitted_validity" not in candidate


def test_a_missing_required_validity_row_refuses_without_an_owner(tmp_path):
    docs = _write(tmp_path / "d", _without(_full(tmp_path), "V3"))
    _refused(docs, "required validity row V3 is missing and has no owner", config=_config(required_validity={"run": ("V3",), "pooled": ("V3",)}))


def test_a_missing_required_row_is_accepted_when_an_owned_fail_covers_it_and_is_listed(tmp_path):
    docs = _write(tmp_path / "d", _without(_full(tmp_path), "V3"))
    known = [_entry(match="V3", ticket="TCK-OWN-V3")]
    candidate = _build(docs, known, config=_config(required_validity={"run": ("V3",), "pooled": ("V3",)}), milestone="M0")
    assert candidate["omitted_validity"] == [{"row": "V3:pooled:w:*", "known_match": "V3", "ticket": "TCK-OWN-V3"}, {"row": "V3:run:w:*", "known_match": "V3", "ticket": "TCK-OWN-V3"}]  # one per level
    assert not [r for r in candidate["metrics"] if r["id"] == "V3"]
    baselines = tmp_path / "b"
    base.rebaseline(candidate, _config(required_validity={"run": ("V3",), "pooled": ("V3",)}), baselines, pr=None, cites=["TCK-METRIC-SET"], known=known, today=TODAY)
    assert base.lint_dir(baselines) == []


def test_an_expired_or_wrong_state_owner_does_not_cover_a_missing_required_row(tmp_path):
    docs = _write(tmp_path / "d", _without(_full(tmp_path), "V3"))
    cfg = _config(required_validity={"run": ("V3",), "pooled": ("V3",)})
    _refused(docs, "expired", [_entry(match="V3", expires="2026-10-01")], config=cfg)
    _refused(docs, "no owner", [{**_entry(match="V3"), "state": "flaky"}], config=cfg)


def test_a_row_missing_from_only_the_pooled_document_refuses_too(tmp_path):
    docs = _full(tmp_path)
    docs[("w", None)] = {**docs[("w", None)], "metrics": [m for m in docs[("w", None)]["metrics"] if m["id"] != "V3"]}
    _refused(_write(tmp_path / "d", docs), r"w__pooled\.json: required validity row V3 is missing", config=_config(required_validity={"run": ("V3",), "pooled": ("V3",)}))


def _with_stub_v8(mode):
    from tests.helpers import rpg_gate_stub_metrics as stub

    docs = _full(None)
    return {k: {**d, "metrics": [*d["metrics"], *({**r, "scope": "pooled" if k[1] is None else "run"} for r in stub.v8_rows(mode))]} for k, d in docs.items()}


def test_the_stub_v8_row_clean_is_recorded_and_violating_needs_an_owner(tmp_path):
    cfg = _config(required_validity={"run": ("V8",), "pooled": ("V8",)})
    candidate = _build(_write(tmp_path / "ok", _with_stub_v8("clean")), config=cfg)
    assert [r["id"] for r in candidate["metrics"] if r["id"] == "V8"]
    _refused(_write(tmp_path / "bad", _with_stub_v8("violations")), "validity row V8 has 1 violation", config=cfg)
    _refused(_write(tmp_path / "gone", _with_stub_v8("absent")), "required validity row V8 is missing", config=cfg)
    owned = _build(_write(tmp_path / "own", _with_stub_v8("violations")), [_entry(match="V8", ticket="TCK-RPG-V8")], config=cfg)
    assert [o["known_match"] for o in owned["omitted_validity"]] and not [r for r in owned["metrics"] if r["id"] == "V8"]


# ---- TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL: a row is required at the level it is judged at

PER_LEVEL = {"run": ("V1", "V3"), "pooled": ("V3",)}  # the fixture's seed documents carry V1 and V3, its pooled document only V3 (no V1)


def _drop(doc, rid):
    return {**doc, "metrics": [m for m in doc["metrics"] if m["id"] != rid]}


def test_a_pooled_document_without_a_run_only_row_and_seed_documents_without_a_pooled_only_row_do_not_refuse(tmp_path):
    docs = _full(tmp_path)
    docs = {k: (_drop(d, "V3") if k[1] is not None else d) for k, d in docs.items()}  # seeds lack V3, which is required at the pooled level only
    candidate = _build(_write(tmp_path / "d", docs), config=_config(required_validity={"run": ("V1",), "pooled": ("V3",)}))
    assert "omitted_validity" not in candidate


def test_dropping_a_run_row_from_one_seed_refuses_and_an_owner_lists_it_as_run_level(tmp_path):
    docs = _full(tmp_path)
    docs[("w", 2)] = _drop(docs[("w", 2)], "V3")
    cfg = _config(required_validity={"run": ("V3",), "pooled": ()})
    _refused(_write(tmp_path / "d", docs), r"w__s2\.json: required validity row V3 is missing and has no owner", config=cfg)
    candidate = _build(_write(tmp_path / "o", docs), [_entry(match="V3", ticket="TCK-OWN-V3")], config=cfg)
    assert candidate["omitted_validity"] == [{"row": "V3:run:w:*", "known_match": "V3", "ticket": "TCK-OWN-V3"}]


def test_dropping_a_pooled_row_refuses_and_an_owner_lists_it_as_pooled_level(tmp_path):
    docs = _full(tmp_path)
    docs[("w", None)] = _drop(docs[("w", None)], "V3")
    cfg = _config(required_validity={"run": (), "pooled": ("V3",)})
    _refused(_write(tmp_path / "d", docs), r"w__pooled\.json: required validity row V3 is missing and has no owner", config=cfg)
    candidate = _build(_write(tmp_path / "o", docs), [_entry(match="V3", ticket="TCK-OWN-V3")], config=cfg)
    assert candidate["omitted_validity"] == [{"row": "V3:pooled:w:*", "known_match": "V3", "ticket": "TCK-OWN-V3"}]


def test_a_pooled_only_row_is_not_asked_of_the_seed_documents(tmp_path):
    cfg = _config(required_validity={"run": ("V1",), "pooled": ("V7",)})
    _refused(_write(tmp_path / "d"), r"w__pooled\.json: required validity row V7 is missing", config=cfg)  # only the pooled document is asked for V7


def test_floors_may_differ_between_worlds_but_not_between_the_seeds_of_one(tmp_path):
    two = _config(worlds=("w", "x"))

    def world(name, floor_by_seed):
        out = {(name, s): {**_seed_doc(s, floor=floor_by_seed[s]), "world": name} for s in SEEDS}
        out[(name, None)] = {**_pooled_doc(), "world": name}
        return out

    same_per_world = {**world("w", {1: 1.0, 2: 1.0, 3: 1.0}), **world("x", {1: 3.0, 2: 3.0, 3: 3.0})}
    assert "metrics" in _build(_write(tmp_path / "ok", same_per_world), config=two)
    drift = {**world("w", {1: 1.0, 2: 1.0, 3: 1.0}), **world("x", {1: 3.0, 2: 3.1, 3: 3.0})}
    _refused(_write(tmp_path / "bad", drift), r"threshold mismatch for O1 in x", config=two)


def test_the_candidate_records_its_own_thresholds():
    """TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD AC5: a new baseline carries the candidate's k and floor, not any reference's."""
    docs = {**{("w", s): _seed_doc(s, k=3.5, floor=7.0) for s in SEEDS}, ("w", None): _pooled_doc()}
    candidate = _build(_write(Path(__import__("tempfile").mkdtemp()) / "d", docs))
    row = next(r for r in candidate["metrics"] if r["id"] == "O1")
    assert (row["k"], row["floor"]) == (3.5, 7.0)
    pooled = next(r for r in candidate["metrics"] if r["id"] == "O9")
    assert pooled["floor"] == 0.1


def _pooled_with_share(**row):
    doc = _pooled_doc()
    doc["metrics"].append({"id": "O8", "class": "outcome", "scope": "pooled", "group": "*", "floor": 0.1, **row})
    return doc


def test_an_empty_denominator_share_is_left_out_and_listed_not_refused(tmp_path):
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_with_share(value=None, reason="empty_denominator")}
    candidate = _build(_write(tmp_path / "d", docs), ())
    assert candidate["undefined_rows"] == [{"row": "O8:pooled:w:*", "reason": "empty_denominator"}]
    assert not [m for m in candidate["metrics"] if m["id"] == "O8"]


def test_a_null_pooled_share_without_the_reason_still_refuses(tmp_path):
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_with_share(value=None)}
    _refused(_write(tmp_path / "d", docs), "pooled outcome row O8 has no numeric value")


# ---- a relative floor (TCK-20261020-RPG-GATE-CANDIDATE-RECORDS-A-RELATIVE-FLOOR)

def _o1(candidate):
    return next(m for m in candidate["metrics"] if m["id"] == "O1" and m["scope"] == "run")


def _rel_docs(values, **kw):
    return {**{("w", s): _seed_doc(s, value=v, floor=3.0, floor_rel=0.10, **kw) for s, v in zip(SEEDS, values)}, ("w", None): _pooled_doc()}


def test_the_candidate_records_the_relative_floor_with_its_two_parts(tmp_path):
    row = _o1(_build(_write(tmp_path / "a", _rel_docs([40.0, 50.0, 60.0])), ()))
    assert (row["floor"], row["floor_base"], row["floor_rel"]) == (5.0, 3.0, 0.10)
    small = _o1(_build(_write(tmp_path / "b", _rel_docs([5.0, 5.0, 5.0])), ()))
    assert (small["floor"], small["floor_base"], small["floor_rel"]) == (3.0, 3.0, 0.10)


def test_a_row_without_floor_rel_records_only_floor(tmp_path):
    row = _o1(_build(_write(tmp_path / "a"), ()))
    assert "floor_rel" not in row and "floor_base" not in row


def test_floor_rel_outside_zero_to_one_or_not_a_number_refuses(tmp_path):
    for bad in (0, -0.1, 1.5, "0.1", True):
        docs = {**{("w", s): _seed_doc(s, floor_rel=0.1) for s in SEEDS}, ("w", None): _pooled_doc()}
        for s in SEEDS:
            docs[("w", s)]["metrics"][0]["floor_rel"] = bad
        _refused(_write(tmp_path / f"d{bad!r}", docs), "floor_rel .* must be a number in")


def test_a_pooled_row_with_floor_rel_refuses(tmp_path):
    docs = {**{("w", s): _seed_doc(s) for s in SEEDS}, ("w", None): _pooled_doc()}
    docs[("w", None)]["metrics"][1]["floor_rel"] = 0.1
    _refused(_write(tmp_path / "d", docs), "pooled outcome row O9 carries floor_rel")


def test_floor_rel_must_agree_across_the_documents_of_a_world(tmp_path):
    docs = _rel_docs([40.0, 50.0, 60.0])
    docs[("w", 2)]["metrics"][0]["floor_rel"] = 0.2
    _refused(_write(tmp_path / "d", docs), "threshold mismatch for O1")


# ---- TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED: scoped entries in the candidate

def _scoped_v3(cases, ticket="TCK-S"):
    return {**_entry(match="V3:wolves", ticket=ticket), "cases": cases}


def _v3_docs(by_seed, pooled_v3=0):
    """Seed documents with V3 fails given as {seed: [entity ids]} (violations == len(ids))."""
    docs = {("w", s): _seed_doc(s) for s in SEEDS}
    for seed, ids in by_seed.items():
        row = next(m for m in docs[("w", seed)]["metrics"] if m["id"] == "V3")
        row["violations"], row["examples"] = len(ids), [{"entity_id": i} for i in ids]
    docs[("w", None)] = _pooled_doc(v3=pooled_v3)
    return docs


def test_a_scoped_entry_omits_exactly_its_covered_fail(tmp_path):
    known = [_scoped_v3([{"world": "w", "seed": 2, "entity_id": 28}])]
    candidate = _build(_write(tmp_path / "d", _v3_docs({2: [28]})), known, milestone="M0")
    assert not [r for r in candidate["metrics"] if r["id"] == "V3" and r["scope"] == "run"]
    assert {"row": "V3:run:w:wolves", "known_match": "V3:wolves", "ticket": "TCK-S"} in candidate["omitted_validity"]


def test_a_fail_on_an_uncovered_seed_or_entity_refuses_the_candidate(tmp_path):
    known = [_scoped_v3([{"world": "w", "seed": 2, "entity_id": 28}])]
    _refused(_write(tmp_path / "a", _v3_docs({2: [28], 3: [28]})), r"w__s3\.json: validity row V3 has 1 violation\(s\) and no owner", known)
    _refused(_write(tmp_path / "b", _v3_docs({2: [28, 29]})), r"w__s2\.json: validity row V3 has 2 violation\(s\) and no owner", known)


def test_a_pooled_fail_is_not_owned_by_a_scoped_entry(tmp_path):
    known = [_scoped_v3([{"world": "w", "seed": 2, "entity_id": 28}])]
    _refused(_write(tmp_path / "p", _v3_docs({2: [28]}, pooled_v3=1)), r"w__pooled\.json: validity row V3 has 1 violation\(s\) and no owner", known)


def test_a_missing_required_row_is_not_owned_by_a_scoped_entry(tmp_path):
    cfg = _config(required_validity={"run": ("V3",), "pooled": ()})
    docs = _v3_docs({})
    for doc in docs.values():
        doc["metrics"] = [m for m in doc["metrics"] if m["id"] != "V3"]
    _refused(_write(tmp_path / "m", docs), "required validity row V3 is missing", [_scoped_v3([{"world": "w", "seed": 2}])], config=cfg)


def test_two_scoped_owners_of_one_row_are_both_recorded_so_each_expiry_is_rechecked(tmp_path):
    first = _scoped_v3([{"world": "w", "seed": 2, "entity_id": 28}], ticket="TCK-A")
    second = _scoped_v3([{"world": "w", "seed": 3, "entity_id": 38}], ticket="TCK-B")
    docs = _v3_docs({2: [28], 3: [38]})
    candidate = _build(_write(tmp_path / "d", docs), [first, second], milestone="M0")
    run_rows = [(o["row"], o["ticket"]) for o in candidate["omitted_validity"] if ":run:" in o["row"]]
    assert run_rows == [("V3:run:w:wolves", "TCK-A"), ("V3:run:w:wolves", "TCK-B")]
    with pytest.raises(base.RebaselineRefused, match="expired"):
        base.rebaseline(candidate, _config(), tmp_path / "b", pr=None, cites=["TCK-METRIC-SET"], known=[first, {**second, "expires_on": "2026-10-01"}], today=TODAY)
