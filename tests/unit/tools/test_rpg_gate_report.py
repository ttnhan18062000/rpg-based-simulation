"""TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN: every state from fixture documents, both references, k*SE AND floor, ownership, rerun."""
from __future__ import annotations

import datetime as dt
import json

import pytest

from tools.test_architecture import known_reds
from tools.test_architecture import rpg_gate_report as rep
from tools.test_architecture.rpg_gate_baseline import GateConfig, References

TODAY = dt.date(2026, 10, 11)
SEEDS = (1, 2, 3, 4, 5)


def _config(**over) -> GateConfig:
    base = dict(worlds=("w",), seeds=SEEDS, ticks=100, stale_after_days=30)
    base.update(over)
    return GateConfig(**base)


ORACLE = "docs/mechanics/02_combat_laws.md"


def _seed_doc(seed, *, value=10.0, violations=0, status="ok", o_id="O1", examples=(), k=2.0, floor=1.0, reason="run_error", oracle=ORACLE):
    if status != "ok":
        return {"schema": "rpg-gate-metrics/v1", "status": status, "reason": reason, "world": "w", "seed": seed, "metrics": [], "error": "KeyError: boom"}
    outcome = {"id": o_id, "class": "outcome", "scope": "run", "group": "*", "value": value}
    if k is not None:
        outcome["k"] = k
    if floor is not None:
        outcome["floor"] = floor
    return {"schema": "rpg-gate-metrics/v1", "status": "ok", "harness_hash": "h", "world": "w", "seed": seed, "metrics": [
        outcome,
        {"id": "V1", "class": "validity", "scope": "run", "group": "*", "violations": violations, "examples": list(examples), "oracle": oracle},
    ]}


def _pooled_doc(violations=0, status="ok", value=None, floor=2.0):
    metrics = [{"id": "V7", "class": "validity", "scope": "pooled", "group": "wolves", "violations": violations, "examples": ["e"], "oracle": ORACLE}]
    if value is not None:
        metrics.append({"id": "O9", "class": "outcome", "scope": "pooled", "group": "*", "value": value, **({"floor": floor} if floor is not None else {})})
    return {"schema": "rpg-gate-metrics/v1", "status": status, "harness_hash": "h", "reason": "metric_error", "world": "w", "metrics": metrics if status == "ok" else [], "error": "x"}


def _docs(values=(10, 10, 10, 10, 10), **kw):
    docs = {("w", s): _seed_doc(s, value=v, **kw) for s, v in zip(SEEDS, values)}
    docs[("w", None)] = _pooled_doc()
    return docs


def _baseline(version, values=(10, 10, 10, 10, 10), milestone="M1", pooled=None, k=2.0, floor=1.0, pooled_floor=2.0):
    """A recorded baseline carries each outcome row's own k and floor by contract (rpg_gate_baseline_format.md), which the report now judges it with: they default to the
    thresholds the fixture documents carry, so a test that does not care about them reads as before. Pass ``k=None`` / ``floor=None`` for a baseline that lacks them."""
    thresholds = {name: v for name, v in (("k", k), ("floor", floor)) if v is not None}
    rows = [{"id": "O1", "class": "outcome", "scope": "run", "world": "w", "group": "*", "per_seed": {str(s): v for s, v in zip(SEEDS, values)}, "mean": sum(values) / 5, "se": 0.1, **thresholds}]
    if pooled is not None:
        rows.append({"id": "O9", "class": "outcome", "scope": "pooled", "world": "w", "group": "*", "value": pooled, **({"floor": pooled_floor} if pooled_floor is not None else {})})
    return {"version": version, "milestone": milestone, "metrics": rows}


def _refs(last=None, first=None):
    last = last or _baseline(2)
    return References(last=last, milestone_first=first or last)


def _states(report):
    return {(rep.metric_test_id(f), f.get("seed"), f["scope"]): f["state"] for f in report["findings"]}


def _build(docs, refs=None, reasons=None, known=(), rerun=None, config=None):
    return rep.build_report(config or _config(), docs, refs if refs is not None else _refs(), reasons or {}, list(known), TODAY, sha="abc", harness_hash="h", rerun=rerun)


def _entry(match, state, ticket="TCK-1", expires="2026-12-31"):
    return {"match": match, "ticket": ticket, "owner": "rpg", "added_on": "2026-10-01", "expires_on": expires, "state": state}


# ---- pass and fail (validity)

def test_everything_in_band_is_pass_and_green():
    report = _build(_docs())
    assert report["verdict"] == "green" and set(_states(report).values()) == {"pass"}
    assert report["counts"]["pass"] == len(report["findings"])


def test_validity_fail_is_exact_per_seed_with_five_examples_and_the_config_oracle():
    docs = _docs()
    docs[("w", 3)] = _seed_doc(3, violations=7, examples=list("abcdefg"))
    report = _build(docs)
    fail = next(f for f in report["findings"] if f["state"] == "fail" and f["scope"] == "run")
    assert fail["seed"] == 3 and fail["violations"] == 7 and fail["examples"] == list("abcde")
    assert fail["oracle"] == ORACLE
    assert _states(report)[("V1", 4, "run")] == "pass"  # the other seeds are judged on their own


def test_a_pooled_validity_fail_is_judged_per_world():
    docs = _docs()
    docs[("w", None)] = _pooled_doc(violations=2)
    report = _build(docs)
    assert _states(report)[("V7:wolves", None, "pooled")] == "fail"


# ---- drift: both references, k*SE AND floor

def test_drift_needs_both_over_k_se_and_over_the_floor():
    # diffs 2,3,2,3,2: mean 2.4, se 0.245 -> over k*se (0.49) and over the floor (1.0): drift
    assert _states(_build(_docs((12, 13, 12, 13, 12))))[("O1", None, "run")] == "drift"
    # diffs 0.5 each: se 0 -> over k*se but under the floor 1.0: pass
    assert _states(_build(_docs((10.5,) * 5)))[("O1", None, "run")] == "pass"
    # mean 1.5 over the floor, but noisy: diffs 1,3,0,3,0.5 -> mean 1.5, se ~0.58, k*se 1.17 -> still drift; make it noisier
    noisy = _build(_docs((11, 15, 5, 17, 9.5)))  # diffs 1,5,-5,7,-0.5: mean 1.5, se ~2.2, k*se 4.4: inside SE though over the floor
    assert _states(noisy)[("O1", None, "run")] == "pass"


def test_both_references_are_reported_and_drift_against_either_is_drift():
    last = _baseline(3, (12,) * 5, milestone="M2")
    first = _baseline(1, (10,) * 5, milestone="M2")
    report = _build(_docs((12.0, 12.0, 12.0, 12.0, 12.0)), refs=References(last=last, milestone_first=first))
    finding = next(f for f in report["findings"] if f["id"] == "O1")
    by_ref = {r["ref"]: r for r in finding["refs"]}
    assert by_ref["last"]["state"] == "pass" and by_ref["milestone-first"]["state"] == "drift" and finding["state"] == "drift"
    assert [r["ref"] for r in report["references"]] == ["last", "milestone-first"]


def test_floor_keyed_by_id_applies_to_every_key_and_tick():
    docs = _docs((10,) * 5)
    for s in SEEDS:
        docs[("w", s)]["metrics"].append({"id": "O1", "class": "outcome", "scope": "run", "group": "g", "key": "STARVATION", "tick": 100, "value": 10.5, "k": 2.0, "floor": 1.0})
    refs = _refs()
    refs.last["metrics"].append({"id": "O1", "class": "outcome", "scope": "run", "world": "w", "group": "g", "key": "STARVATION", "tick": 100, "per_seed": {str(s): 10 for s in SEEDS}, "mean": 10, "se": 0, "k": 2.0, "floor": 1.0})  # a recorded baseline row carries its thresholds
    keyed = [f for f in _build(docs, refs=refs)["findings"] if f.get("key") == "STARVATION"]
    assert len(keyed) == 1 and keyed[0]["state"] == "pass" and keyed[0]["refs"][0]["floor"] == 1.0


def test_a_pooled_outcome_drifts_on_the_floor_alone():
    docs = _docs()
    docs[("w", None)] = _pooled_doc(value=5.0)
    config = _config()
    over = _build(docs, refs=_refs(_baseline(2, pooled=2.0)), config=config)
    assert _states(over)[("O9", None, "pooled")] == "drift"
    under = _build(docs, refs=_refs(_baseline(2, pooled=4.0)), config=config)
    assert _states(under)[("O9", None, "pooled")] == "pass"


# ---- stale, no-data

def test_a_stale_reference_gives_stale_never_pass_and_validity_is_unaffected():
    report = _build(_docs(), reasons={2: ["past stale_after"]})
    states = _states(report)
    assert states[("O1", None, "run")] == "stale" and states[("V1", 1, "run")] == "pass"
    assert report["references"][0]["stale"] == ["past stale_after"] and report["verdict"] == "green"


def test_a_stale_reference_does_not_hide_drift_against_the_other_one():
    last = _baseline(3, (10,) * 5, milestone="M2")
    first = _baseline(1, (10,) * 5, milestone="M2")
    report = _build(_docs((15,) * 5), refs=References(last=last, milestone_first=first), reasons={3: ["x"]})
    assert _states(report)[("O1", None, "run")] == "drift"


def test_no_baseline_and_missing_row_and_too_few_seeds_are_no_data():
    none = rep.build_report(_config(), _docs(), None, {}, [], TODAY)
    assert _states(none)[("O1", None, "run")] == "no-data"
    refs = _refs(_baseline(2))
    refs.last["metrics"] = []
    assert _states(_build(_docs(), refs=refs))[("O1", None, "run")] == "no-data"
    sparse = _baseline(2)
    sparse["metrics"][0]["per_seed"] = {"1": 10}
    assert _states(_build(_docs(), refs=_refs(sparse)))[("O1", None, "run")] == "no-data"


def test_a_no_data_seed_passes_through_and_stops_outcome_judgement_for_the_world():
    docs = _docs()
    docs[("w", 2)] = _seed_doc(2, status="no-data")
    report = _build(docs)
    states = _states(report)
    assert states[("*", 2, "run")] == "no-data" and ("O1", None, "run") not in states
    assert report["counts"]["pass"] > 0 and report["verdict"] == "green"
    missing = _docs()
    del missing[("w", 3)]
    assert _states(_build(missing))[("*", 3, "run")] == "no-data"
    pooled_gone = _docs()
    pooled_gone[("w", None)] = _pooled_doc(status="no-data")
    assert _states(_build(pooled_gone))[("*", None, "pooled")] == "no-data"


# ---- ownership and verdict

def test_unowned_fail_is_red_owned_is_known_and_expired_is_red():
    docs = _docs()
    docs[("w", 1)] = _seed_doc(1, violations=1)
    assert _build(docs)["verdict"] == "red"
    owned = _build(docs, known=[_entry("V1", "fail")])
    assert owned["verdict"] == "green" and next(f for f in owned["findings"] if f["state"] == "fail")["ownership"] == "known"
    expired = _build(docs, known=[_entry("V1", "fail", expires="2026-10-01")])
    assert expired["verdict"] == "red" and "expired" in expired["reasons"][0]


def test_a_drift_entry_does_not_own_a_fail_and_a_fail_entry_does_not_trace_a_drift():
    docs = _docs((15,) * 5)
    docs[("w", 1)] = _seed_doc(1, value=15, violations=1)
    report = _build(docs, known=[_entry("V1", "drift"), _entry("O1", "fail")])
    by = {f["id"]: f for f in report["findings"] if f["state"] in ("fail", "drift")}
    assert by["V1"]["ownership"] == "unowned" and by["O1"]["ownership"] == "needs-trace-ticket" and report["verdict"] == "red"


def test_drift_is_never_red_and_a_traced_drift_shows_its_ticket():
    plain = _build(_docs((15,) * 5))
    assert plain["verdict"] == "green" and next(f for f in plain["findings"] if f["state"] == "drift")["ownership"] == "needs-trace-ticket"
    traced = _build(_docs((15,) * 5), known=[_entry("O1", "drift", ticket="TCK-TRACE")])
    assert next(f for f in traced["findings"] if f["state"] == "drift")["ticket"] == "TCK-TRACE"


def test_group_ids_match_the_registry_as_metric_colon_group():
    docs = _docs()
    docs[("w", None)] = _pooled_doc(violations=1)
    assert _build(docs, known=[_entry("V7:wolves", "fail")])["verdict"] == "green"
    assert _build(docs, known=[_entry("V7:foxes", "fail")])["verdict"] == "red"


def test_stale_known_entries_are_listed():
    report = _build(_docs(), known=[_entry("V1", "fail"), _entry("O1", "drift")])
    assert report["stale_known_entries"] == {"fail": ["V1"], "drift": ["O1"]}


def test_the_registry_requires_a_state_when_entries_have_one():
    entries = [_entry("V1", "fail")]
    for call in (lambda: known_reds.owner_of("V1", entries), lambda: known_reds.classify({"V1": ""}, entries, TODAY), lambda: known_reds.stale_mappings({}, entries)):
        with pytest.raises(ValueError, match="state"):
            call()
    assert known_reds.owner_of("V1", [{"match": "V1", "ticket": "t", "owner": "o", "added_on": "2026-01-01", "expires_on": "2026-12-31", "kind": "flaky"}])


# ---- same-SHA rerun

def test_a_rerun_that_disagrees_marks_unstable_and_routes_to_test_infrastructure():
    docs = _docs()
    docs[("w", 1)] = _seed_doc(1, violations=1)
    calls = []

    def rerun(pairs):
        calls.append(list(pairs))
        return {("w", 1): _seed_doc(1, violations=0)}

    report = _build(docs, rerun=rerun)
    unstable = next(f for f in report["findings"] if f["state"] == "unstable")
    assert unstable["route"] == "test-infrastructure" and unstable["first_state"] == "fail" and unstable["rerun_state"] == "pass"
    assert calls == [[("w", 1)]] and report["verdict"] == "red" and report["rerun"]["performed"]


def test_a_rerun_that_agrees_keeps_the_state_and_a_drift_reruns_every_seed_of_its_world():
    calls = []

    def rerun(pairs):
        calls.append(list(pairs))
        return _docs((15,) * 5)

    report = _build(_docs((15,) * 5), rerun=rerun)
    assert _states(report)[("O1", None, "run")] == "drift" and len(calls) == 1 and len(calls[0]) == 5 and report["verdict"] == "green"


def test_a_drift_that_vanishes_on_rerun_is_unstable_and_makes_the_job_red():
    report = _build(_docs((15,) * 5), rerun=lambda pairs: _docs((10,) * 5))
    assert _states(report)[("O1", None, "run")] == "unstable" and report["verdict"] == "red"


def test_no_rerun_when_nothing_failed_or_drifted():
    report = _build(_docs(), rerun=lambda pairs: pytest.fail("must not rerun"))
    assert report["rerun"] == {"performed": False}


# ---- output

def test_markdown_shows_states_references_examples_and_oracle():
    docs = _docs((15,) * 5)
    docs[("w", 1)] = _seed_doc(1, value=15, violations=2, examples=["x"])
    md = rep.render_markdown(_build(docs))
    for needle in ("RED", "fail", "drift", "oracle: docs/mechanics/02_combat_laws.md", "vs last v2", "needs-trace-ticket", "unowned"):
        assert needle in md
    assert "Every metric passes." in rep.render_markdown(_build(_docs()))
    json.dumps(_build(docs))  # the report is JSON-serialisable


def test_a_missing_k_or_floor_is_a_contract_error_reported_as_no_data_never_a_made_up_threshold():
    for kw, word in (({"k": None}, "k"), ({"floor": None}, "floor")):
        report = _build({**_docs(), **{("w", s): _seed_doc(s, **kw) for s in SEEDS}})
        f = next(f for f in report["findings"] if f["id"] == "O1")
        assert f["state"] == "no-data" and f["reason"] == "contract_error" and word in f["detail"] and "contract error" in f["detail"]
    pooled = _docs()
    pooled[("w", None)] = _pooled_doc(value=5.0, floor=None)
    f = next(f for f in _build(pooled, refs=_refs(_baseline(2, pooled=2.0)))["findings"] if f["id"] == "O9")
    assert f["state"] == "no-data" and "floor" in f["detail"]


def test_rows_of_one_metric_that_disagree_on_k_floor_or_oracle_are_mixed_module_versions():
    for kw in ({"k": 3.0}, {"floor": 2.0}, {"oracle": "other"}):
        docs = _docs()
        docs[("w", 2)] = _seed_doc(2, **kw)
        report = _build(docs)
        mixed = [f for f in report["findings"] if f.get("reason") == "contract_error"]
        assert mixed and all(f["state"] == "no-data" and f["detail"] == "mixed metric module versions" for f in mixed)
        assert not any(f["state"] in ("drift", "fail") for f in mixed)


def test_the_judged_seed_count_is_shown_on_each_outcome_result():
    report = _build(_docs((12, 13, 12, 13, 12)))
    f = next(f for f in report["findings"] if f["id"] == "O1")
    assert all(r["n"] == 5 and r["of"] == 5 for r in f["refs"]) and "judged on 5/5 seeds" in rep.render_markdown(report)
    sparse = _baseline(2)
    sparse["metrics"][0]["per_seed"] = {"1": 10, "2": 10, "3": 10}
    report = _build(_docs(), refs=_refs(sparse))
    assert "judged on 3/5 seeds" in rep.render_markdown({**report, "findings": [{**f, "state": "drift"} for f in report["findings"] if f["id"] == "O1"]})
    assert next(f for f in report["findings"] if f["id"] == "O1")["refs"][0]["n"] == 3


def test_no_data_reasons_are_split_and_a_run_error_is_prominent_but_not_red():
    docs = _docs()
    docs[("w", 1)] = _seed_doc(1, status="no-data", reason="run_error")
    docs[("w", 2)] = _seed_doc(2, status="no-data", reason="metric_error")
    del docs[("w", 3)]
    report = _build(docs)
    assert report["no_data_reasons"]["run_error"] == 1 and report["no_data_reasons"]["metric_error"] == 1 and report["no_data_reasons"]["harness_error"] == 1
    assert report["run_errors"] == [{"world": "w", "seed": 1, "error": "KeyError: boom"}]
    md = rep.render_markdown(report)
    assert "RUN ERRORS (1)" in md and "rpg defect" in md and report["verdict"] == "green"


def test_validity_is_still_judged_from_the_seeds_that_have_data():
    docs = _docs()
    docs[("w", 1)] = _seed_doc(1, status="no-data")
    docs[("w", 2)] = _seed_doc(2, violations=3)
    report = _build(docs)
    assert _states(report)[("V1", 2, "run")] == "fail" and _states(report)[("V1", 3, "run")] == "pass" and ("V1", 1, "run") not in _states(report)


def test_cli_writes_json_and_markdown_and_fails_on_red_only_when_asked(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    cfg = tmp_path / "config.yaml"
    cfg.write_text("worlds: [w]\nseeds: [1, 2]\nticks: 10\nstale_after_days: 30\n")
    from tools.test_architecture import rpg_gate_harness

    current = rpg_gate_harness.harness_hash(cfg, metrics_module="tests.helpers.rpg_gate_stub_metrics")  # the documents must come from the current harness
    for seed in (1, 2):
        (docs / f"w__s{seed}.json").write_text(json.dumps({**_seed_doc(seed, violations=1, oracle="oracle-x"), "harness_hash": current}))
    (docs / "w__pooled.json").write_text(json.dumps({**_pooled_doc(), "metrics": [], "harness_hash": current}))
    known = tmp_path / "known.yaml"
    known.write_text("known: []\n")
    args = ["--config", str(cfg), "--docs", str(docs), "--baselines", str(tmp_path / "none"), "--known", str(known),
            "--out-json", str(tmp_path / "r.json"), "--out-md", str(tmp_path / "r.md"), "--metrics-module", "tests.helpers.rpg_gate_stub_metrics", "--no-rerun"]
    assert rep.main(args) == 0
    assert rep.main([*args, "--fail-on-red"]) == 1
    assert json.loads((tmp_path / "r.json").read_text())["verdict"] == "red" and "oracle: oracle-x" in (tmp_path / "r.md").read_text()


def _contract(report, rid):
    return [f for f in report["findings"] if f["id"] == rid and f.get("reason") == "contract_error"]


def test_a_validity_row_without_a_count_or_an_oracle_is_a_contract_error_not_a_pass():
    for edit, word in ((lambda row: row.pop("violations"), "violations"), (lambda row: row.update(violations="3"), "violations"), (lambda row: row.pop("oracle"), "oracle")):
        docs = _docs()
        for s in SEEDS:
            docs[("w", s)] = _seed_doc(s)
            edit(docs[("w", s)]["metrics"][1])
        found = _contract(_build(docs), "V1")
        assert found and all(f["state"] == "no-data" and word in f["detail"] for f in found)


def test_an_outcome_row_without_a_value_or_mean_is_a_contract_error_not_a_crash():
    docs = _docs()
    for s in SEEDS:
        docs[("w", s)] = _seed_doc(s)
        del docs[("w", s)]["metrics"][0]["value"]
    found = _contract(_build(docs), "O1")
    assert found and found[0]["state"] == "no-data" and "value" in found[0]["detail"]
    pooled = _docs()
    pooled[("w", None)] = _pooled_doc(value=5.0)
    del pooled[("w", None)]["metrics"][1]["value"]
    assert _contract(_build(pooled, refs=_refs(_baseline(2, pooled=2.0))), "O9")


def test_documents_from_another_harness_version_are_no_data():
    docs = _docs()
    docs[("w", 2)] = {**_seed_doc(2), "harness_hash": "other"}
    report = _build(docs)  # current harness hash is "h": the odd document is the stale one
    assert next(f for f in report["findings"] if f.get("seed") == 2)["detail"] == "documents from another harness version"
    assert _states(report)[("V1", 1, "run")] == "pass"
    all_old = {k: {**d, "harness_hash": "old"} for k, d in _docs().items()}
    assert {f["detail"] for f in _build(all_old)["findings"] if f["state"] == "no-data"} == {"documents from another harness version"}
    disagree = rep.build_report(_config(), docs, _refs(), {}, [], TODAY, harness_hash="")  # no current hash known: disagreement alone is enough
    assert all(f["state"] == "no-data" for f in disagree["findings"])


# ---- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK: a required validity row the metric module leaves out is no-data, never a pass

def _docs_with_pooled_v1():
    docs = _docs()
    docs[("w", None)] = {**docs[("w", None)], "metrics": [*docs[("w", None)]["metrics"], {"id": "V1", "class": "validity", "scope": "pooled", "group": "*", "violations": 0, "examples": [], "oracle": ORACLE}]}
    return docs


def _missing_required(report):
    return [f for f in report["findings"] if f.get("required_missing")]


def test_a_required_validity_row_that_every_document_has_adds_nothing():
    report = _build(_docs_with_pooled_v1(), config=_config(required_validity={"run": ("V1",), "pooled": ("V1",)}))
    assert _missing_required(report) == []


def test_a_required_validity_row_missing_is_no_data_contract_error_in_every_document():
    report = _build(_docs_with_pooled_v1(), config=_config(required_validity={"run": ("V1", "V8"), "pooled": ("V1", "V8")}))
    missing = _missing_required(report)
    assert len(missing) == len(SEEDS) + 1  # each seed document and the pooled one
    assert all(f["state"] == "no-data" and f["reason"] == "contract_error" and f["id"] == "V8" and f["class"] == "validity" for f in missing)
    assert all(f["detail"] == "required validity row V8 missing" for f in missing)
    assert {f.get("seed") for f in missing} == {*SEEDS, None}
    assert report["no_data_reasons"]["contract_error"] >= len(missing)
    assert report["verdict"] != "red"  # advisory: no-data never turns the job red by itself


def test_the_markdown_lists_the_missing_required_row_prominently():
    text = rep.render_markdown(_build(_docs(), config=_config(required_validity={"run": ("V8",), "pooled": ("V8",)})))
    assert "Required validity row(s) missing: V8" in text and "no-data" in text and "required validity row V8 missing" in text


def test_a_required_row_missing_in_one_seed_only_is_named_for_that_seed():
    docs = _docs_with_pooled_v1()
    docs[("w", 3)] = {**docs[("w", 3)], "metrics": [m for m in docs[("w", 3)]["metrics"] if m["id"] != "V1"]}
    missing = _missing_required(_build(docs, config=_config(required_validity={"run": ("V1",), "pooled": ("V1",)})))
    assert [(f["id"], f.get("seed")) for f in missing] == [("V1", 3)]


def _v8_docs(mode):
    from tests.helpers import rpg_gate_stub_metrics as stub

    docs = _docs_with_pooled_v1()
    for key, doc in docs.items():
        docs[key] = {**doc, "metrics": [*doc["metrics"], *({**r, "scope": "pooled" if key[1] is None else "run"} for r in stub.v8_rows(mode))]}
    return docs


@pytest.mark.parametrize("mode, expected", [("clean", "pass"), ("violations", "fail")])
def test_the_stub_v8_row_is_judged_absolutely(mode, expected):
    report = _build(_v8_docs(mode), config=_config(required_validity={"run": ("V8",), "pooled": ("V8",)}))
    states = {f["state"] for f in report["findings"] if f["id"] == "V8"}
    assert states == {expected} and _missing_required(report) == []
    if mode == "violations":
        assert any(f["examples"][0]["check"] == "unsourced" and f["examples"][0]["entity_id"] == 91 for f in report["findings"] if f["id"] == "V8")


def test_a_module_without_the_required_v8_row_is_no_data_not_a_pass():
    report = _build(_v8_docs("absent"), config=_config(required_validity={"run": ("V8",), "pooled": ("V8",)}))
    assert {f["state"] for f in _missing_required(report)} == {"no-data"} and not [f for f in report["findings"] if f["id"] == "V8" and f["state"] == "pass"]


# ---- TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL: a row is required at the level it is judged at

PER_LEVEL = {"run": ("V1",), "pooled": ("V7",)}  # _docs_with_pooled_v1 carries V1 in every seed document and V7 in the pooled one, as rpg's module does


def test_a_seed_document_without_a_pooled_only_row_and_a_pooled_document_without_a_run_only_row_are_not_missing():
    docs = _docs()  # seed documents have V1 and no V7; the pooled document has V7 and no V1
    assert _missing_required(_build(docs, config=_config(required_validity=PER_LEVEL))) == []


def test_the_plain_list_semantics_would_have_flagged_it_and_the_per_level_config_does_not():
    docs = _docs()
    both = _config(required_validity={"run": ("V1", "V7"), "pooled": ("V1", "V7")})
    assert len(_missing_required(_build(docs, config=both))) == len(SEEDS) + 1  # V7 in every seed, V1 in the pooled one
    assert _missing_required(_build(docs, config=_config(required_validity=PER_LEVEL))) == []


def test_dropping_a_run_row_from_one_seed_gives_exactly_one_contract_error_for_that_seed():
    docs = _docs()
    docs[("w", 4)] = {**docs[("w", 4)], "metrics": [m for m in docs[("w", 4)]["metrics"] if m["id"] != "V1"]}
    report = _build(docs, config=_config(required_validity=PER_LEVEL))
    missing = _missing_required(report)
    assert [(f["id"], f.get("seed"), f["scope"], f["state"], f["reason"]) for f in missing] == [("V1", 4, "run", "no-data", "contract_error")]


def test_dropping_the_pooled_row_gives_exactly_one_pooled_contract_error():
    docs = _docs()
    docs[("w", None)] = {**docs[("w", None)], "metrics": []}
    missing = _missing_required(_build(docs, config=_config(required_validity=PER_LEVEL)))
    assert [(f["id"], f.get("seed"), f["scope"], f["state"], f["reason"]) for f in missing] == [("V7", None, "pooled", "no-data", "contract_error")]


def _world_docs(world, floor_by_seed):
    docs = {(world, s): {**_seed_doc(s, floor=floor_by_seed[s]), "world": world} for s in SEEDS}
    docs[(world, None)] = {**_pooled_doc(), "world": world}
    return docs


def _mixed(report):
    return [f for f in report["findings"] if f.get("detail") == "mixed metric module versions"]


def test_two_worlds_with_different_floors_for_one_row_are_not_mixed_versions():
    flat = lambda v: {s: v for s in SEEDS}
    docs = {**_world_docs("w", flat(1.0)), **_world_docs("x", flat(3.0))}
    assert _mixed(_build(docs, config=_config(worlds=("w", "x")))) == []


def test_two_seeds_of_one_world_with_different_floors_are_still_mixed_versions():
    flat = lambda v: {s: v for s in SEEDS}
    docs = {**_world_docs("w", flat(1.0)), **_world_docs("x", {**flat(3.0), 2: 3.1})}
    mixed = _mixed(_build(docs, config=_config(worlds=("w", "x"))))
    assert mixed and {f["world"] for f in mixed} == {"x"}


# ---- TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD: each reference is judged with its own recorded k and floor

def _ref(finding, label="last"):
    return next(r for r in finding["refs"] if r["ref"] == label)


def _o1(report):
    return next(f for f in report["findings"] if f["id"] == "O1" and f["scope"] == "run")


def _o9(report):
    return next(f for f in report["findings"] if f["id"] == "O9")


def test_a_run_row_is_judged_on_the_reference_floor_and_reports_the_moved_threshold():
    # diffs 5 +/- noise: over k*se, over the reference floor 3.0, under the candidate's floor 9.0. The candidate's floor must not rescue it.
    docs = _docs((15, 15.1, 14.9, 15.1, 14.9), floor=9.0)
    finding = _o1(_build(docs, refs=_refs(_baseline(2, floor=3.0))))
    ref = _ref(finding)
    assert finding["state"] == "drift" and ref["state"] == "drift" and ref["floor"] == 3.0
    assert ref["threshold_moved"] == {"floor": {"candidate": 9.0, "reference": 3.0}}


def test_the_same_thresholds_report_no_move():
    ref = _ref(_o1(_build(_docs((15,) * 5), refs=_refs(_baseline(2)))))
    assert "threshold_moved" not in ref


def test_a_pooled_row_is_judged_on_the_reference_floor_and_reports_the_moved_threshold():
    docs = _docs()
    docs[("w", None)] = _pooled_doc(value=9.0, floor=9.0)  # diff 5.0 from the reference's 4.0
    finding = _o9(_build(docs, refs=_refs(_baseline(2, pooled=4.0, pooled_floor=3.0))))
    ref = _ref(finding)
    assert ref["state"] == "drift" and ref["floor"] == 3.0 and ref["threshold_moved"] == {"floor": {"candidate": 9.0, "reference": 3.0}}


def test_last_and_milestone_first_are_each_judged_on_their_own_floor():
    docs = _docs((15, 15.1, 14.9, 15.1, 14.9))
    finding = _o1(_build(docs, refs=_refs(_baseline(3, floor=3.0, milestone="M2"), _baseline(1, floor=9.0, milestone="M2"))))
    assert (_ref(finding)["state"], _ref(finding, "milestone-first")["state"]) == ("drift", "pass")
    assert (_ref(finding)["floor"], _ref(finding, "milestone-first")["floor"]) == (3.0, 9.0)


@pytest.mark.parametrize("lacks", [{"floor": None}, {"k": None}])
def test_a_reference_row_without_a_recorded_threshold_is_no_data_for_that_reference_only(lacks):
    docs = _docs((15, 15.1, 14.9, 15.1, 14.9), floor=0.5)  # falling back to the candidate's floor 0.5 would read as drift
    finding = _o1(_build(docs, refs=_refs(_baseline(3, **lacks, milestone="M2"), _baseline(1, milestone="M2"))))
    bare = _ref(finding)
    assert bare["state"] == "no-data" and bare["reason"] == "contract_error" and bare["detail"] == "reference row has no recorded threshold" and "floor" not in bare
    assert _ref(finding, "milestone-first")["state"] == "drift"  # the other reference is judged as usual


def test_a_pooled_reference_without_a_floor_is_no_data_not_a_fallback():
    docs = _docs()
    docs[("w", None)] = _pooled_doc(value=99.0, floor=2.0)
    ref = _ref(_o9(_build(docs, refs=_refs(_baseline(2, pooled=4.0, pooled_floor=None)))))
    assert ref["state"] == "no-data" and ref["reason"] == "contract_error"


def test_two_documents_of_one_world_with_different_floors_are_still_a_contract_error():
    docs = _docs()
    docs[("w", 2)] = _seed_doc(2, floor=9.0)
    report = _build(docs, refs=_refs(_baseline(2)))
    assert [f for f in report["findings"] if f.get("detail") == "mixed metric module versions"]


def _with_oracle(row_oracle=None, base_oracle=None):
    docs = _docs()
    docs = {k: {**d, "metrics": [{**m, **({"oracle": row_oracle} if row_oracle and m["id"] == "O1" else {})} for m in d["metrics"]]} for k, d in docs.items()}
    base = _baseline(2)
    if base_oracle:
        base["metrics"][0]["oracle"] = base_oracle
    return _ref(_o1(_build(docs, refs=_refs(base))))


def test_an_oracle_present_on_one_side_only_is_a_move_and_on_neither_is_not():
    assert _with_oracle("docs/a.md", None)["threshold_moved"] == {"oracle": {"candidate": "docs/a.md", "reference": None}}
    assert _with_oracle(None, "docs/b.md")["threshold_moved"] == {"oracle": {"candidate": None, "reference": "docs/b.md"}}
    assert "threshold_moved" not in _with_oracle()
    assert "threshold_moved" not in _with_oracle("docs/a.md", "docs/a.md")


def test_the_markdown_shows_the_moved_threshold_without_changing_the_state():
    docs = _docs((15, 15.1, 14.9, 15.1, 14.9), floor=9.0)
    report = _build(docs, refs=_refs(_baseline(2, floor=3.0)))
    text = rep.render_markdown(report)
    assert "threshold moved: floor 3.0 -> 9.0" in text and _o1(report)["state"] == "drift"


def test_a_missing_reference_threshold_is_named_in_the_markdown_and_counted_in_the_tally():
    docs = _docs((15, 15.1, 14.9, 15.1, 14.9), floor=0.5)
    both_bare = _build(docs, refs=_refs(_baseline(3, floor=None, milestone="M2"), _baseline(1, floor=None, milestone="M2")))
    finding = _o1(both_bare)
    assert finding["state"] == "no-data" and finding["reason"] == "contract_error" and finding["detail"] == "reference row has no recorded threshold"
    assert both_bare["no_data_reasons"]["contract_error"] >= 1
    text = rep.render_markdown(both_bare)
    assert text.count("[contract_error] reference row has no recorded threshold") >= 2  # named for each reference, not repeated for the finding
    assert "vs last v3: no-data" in text and "vs milestone-first v1: no-data" in text


def test_one_bare_reference_beside_a_drifting_one_keeps_the_drift_state_and_still_names_the_cause():
    docs = _docs((15, 15.1, 14.9, 15.1, 14.9), floor=0.5)
    report = _build(docs, refs=_refs(_baseline(3, floor=None, milestone="M2"), _baseline(1, milestone="M2")))
    finding = _o1(report)
    assert finding["state"] == "drift" and "reason" not in finding
    assert "[contract_error] reference row has no recorded threshold" in rep.render_markdown(report)


def test_the_no_row_in_the_baseline_detail_is_shown_for_its_reference():
    base = _baseline(2)
    base["metrics"] = [m for m in base["metrics"] if m["id"] != "O1"]
    assert "no row for this metric in the baseline" in rep.render_markdown(_build(_docs(), refs=_refs(base)))


def _keyed(seed, value, key="starved"):
    return {"id": "O2", "class": "outcome", "scope": "run", "group": "wolves", "key": key, "tick": 100, "value": value, "k": 2.0, "floor": 1.0}


def _with_keyed(docs, rows_by_seed):
    for seed, rows in rows_by_seed.items():
        docs[("w", seed)]["metrics"] = [m for m in docs[("w", seed)]["metrics"] if m["id"] != "O2"] + rows
    return docs


def _absent(report):
    return [f for f in report["findings"] if "absent from seed" in f.get("detail", "")]


def test_a_keyed_row_absent_from_some_seeds_is_one_contract_error_never_read_as_zero():
    rows = {s: [_keyed(s, 3.0), _keyed(s, 1.0, "killed")] for s in SEEDS}
    rows[2], rows[4] = [_keyed(2, 3.0)], [_keyed(4, 3.0)]
    report = _build(_with_keyed(_docs(), rows))
    (found,) = _absent(report)
    assert (found["id"], found["key"], found["state"], found["reason"]) == ("O2", "killed", "no-data", "contract_error")
    assert found["detail"] == "row absent from seed(s) [2, 4]; every seed reports the same rows"
    assert [f["state"] for f in report["findings"] if f["id"] == "O2" and f["key"] == "killed"] == ["no-data"]  # the key is not judged on the seeds that have it
    assert report["no_data_reasons"]["contract_error"] == 1
    markdown = rep.render_markdown(report)
    assert "row absent from seed(s) [2, 4]; every seed reports the same rows" in markdown and "contract_error: 1" in markdown  # the tally line names it


def test_no_row_set_error_when_every_seed_carries_the_same_keyed_rows():
    report = _build(_with_keyed(_docs(), {s: [_keyed(s, 3.0 + s)] for s in SEEDS}))
    assert _absent(report) == [] and report["no_data_reasons"]["contract_error"] == 0


def test_a_row_every_seed_lacks_is_not_a_row_set_error():
    assert _absent(_build(_with_keyed(_docs(), {s: [] for s in SEEDS}))) == []


def test_a_validity_row_the_config_does_not_require_is_judged_on_the_row_set_too_but_a_required_one_is_reported_per_seed_only():
    docs = _docs()
    docs[("w", 3)]["metrics"] = [m for m in docs[("w", 3)]["metrics"] if m["id"] != "V1"]
    report = _build(docs)
    assert len(_absent(report)) == 1 and _absent(report)[0]["id"] == "V1"
    required = _build(docs, config=_config(required_validity={"run": ("V1",)}))
    assert _absent(required) == [] and [f for f in required["findings"] if f.get("required_missing")]


# ---- shares: an undefined pooled share (TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED, scope 5)

def _share_docs(**row):
    docs = _docs()
    docs[("w", None)] = _pooled_doc()
    docs[("w", None)]["metrics"].append({"id": "O9", "class": "outcome", "scope": "pooled", "group": "*", "floor": 0.1, **row})
    return docs


def test_an_empty_denominator_share_is_no_data_empty_denominator_not_a_contract_error():
    report = _build(_share_docs(value=None, reason="empty_denominator"), refs=_refs(_baseline(2, pooled=0.4)))
    (found,) = [f for f in report["findings"] if f["id"] == "O9"]
    assert (found["state"], found["reason"]) == ("no-data", "empty_denominator")
    assert report["no_data_reasons"]["empty_denominator"] == 1 and report["no_data_reasons"]["contract_error"] == 0
    assert report["verdict"] == "green" and "empty_denominator" in rep.render_markdown(report)


def test_a_null_pooled_share_without_that_reason_stays_a_contract_error():
    for extra in ({}, {"reason": "other"}):
        report = _build(_share_docs(value=None, **extra), refs=_refs(_baseline(2, pooled=0.4)))
        (found,) = [f for f in report["findings"] if f["id"] == "O9"]
        assert (found["state"], found["reason"]) == ("no-data", "contract_error"), extra


def test_a_defined_share_against_a_baseline_where_it_was_undefined_has_no_reference_never_drift():
    base = _baseline(2)
    base["undefined_rows"] = [{"row": "O9:pooled:w:*", "reason": "empty_denominator"}]
    report = _build(_share_docs(value=0.9), refs=_refs(base))
    (found,) = [f for f in report["findings"] if f["id"] == "O9"]
    assert found["state"] == "no-data" and "reason" not in found
    assert {r["detail"] for r in found["refs"]} == {"no reference (undefined at baseline)"}
    assert "no reference (undefined at baseline)" in rep.render_markdown(report)
