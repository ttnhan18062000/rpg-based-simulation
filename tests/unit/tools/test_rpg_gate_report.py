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
    base = dict(worlds=("w",), seeds=SEEDS, ticks=100, stale_after_days=30, k=2.0, floors={"O1": 1.0}, oracles={"V1": "docs/mechanics/02_combat_laws.md"})
    base.update(over)
    return GateConfig(**base)


def _outcome_row(values, rid="O1", **extra):
    return {"id": rid, "class": "outcome", "scope": "run", "group": "*", "value": None, **extra}


def _seed_doc(seed, *, value=10.0, violations=0, status="ok", o_id="O1", examples=()):
    if status != "ok":
        return {"schema": "rpg-gate-metrics/v1", "status": status, "world": "w", "seed": seed, "metrics": [], "error": "boom"}
    return {"schema": "rpg-gate-metrics/v1", "status": "ok", "world": "w", "seed": seed, "metrics": [
        {"id": o_id, "class": "outcome", "scope": "run", "group": "*", "value": value},
        {"id": "V1", "class": "validity", "scope": "run", "group": "*", "violations": violations, "examples": list(examples)},
    ]}


def _pooled_doc(violations=0, status="ok", value=None):
    metrics = [{"id": "V7", "class": "validity", "scope": "pooled", "group": "wolves", "violations": violations, "examples": ["e"]}]
    if value is not None:
        metrics.append({"id": "O9", "class": "outcome", "scope": "pooled", "group": "*", "value": value})
    return {"schema": "rpg-gate-metrics/v1", "status": status, "world": "w", "metrics": metrics if status == "ok" else [], "error": "x"}


def _docs(values=(10, 10, 10, 10, 10), **kw):
    docs = {("w", s): _seed_doc(s, value=v, **kw) for s, v in zip(SEEDS, values)}
    docs[("w", None)] = _pooled_doc()
    return docs


def _baseline(version, values=(10, 10, 10, 10, 10), milestone="M1", pooled=None):
    rows = [{"id": "O1", "class": "outcome", "scope": "run", "world": "w", "group": "*", "per_seed": {str(s): v for s, v in zip(SEEDS, values)}, "mean": sum(values) / 5, "se": 0.1}]
    if pooled is not None:
        rows.append({"id": "O9", "class": "outcome", "scope": "pooled", "world": "w", "group": "*", "value": pooled})
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
    assert fail["oracle"] == "docs/mechanics/02_combat_laws.md"
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
        docs[("w", s)]["metrics"].append({"id": "O1", "class": "outcome", "scope": "run", "group": "g", "key": "STARVATION", "tick": 100, "value": 10.5})
    refs = _refs()
    refs.last["metrics"].append({"id": "O1", "class": "outcome", "scope": "run", "world": "w", "group": "g", "key": "STARVATION", "tick": 100, "per_seed": {str(s): 10 for s in SEEDS}, "mean": 10, "se": 0})
    keyed = [f for f in _build(docs, refs=refs)["findings"] if f.get("key") == "STARVATION"]
    assert len(keyed) == 1 and keyed[0]["state"] == "pass" and keyed[0]["refs"][0]["floor"] == 1.0


def test_a_pooled_outcome_drifts_on_the_floor_alone():
    docs = _docs()
    docs[("w", None)] = _pooled_doc(value=5.0)
    config = _config(floors={"O1": 1.0, "O9": 2.0})
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


def test_outcome_judgement_without_k_is_an_error_not_a_guess():
    with pytest.raises(ValueError, match="no k"):
        _build(_docs(), config=_config(k=None))


def test_cli_writes_json_and_markdown_and_fails_on_red_only_when_asked(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    cfg = tmp_path / "config.yaml"
    cfg.write_text("worlds: [w]\nseeds: [1, 2]\nticks: 10\nstale_after_days: 30\nk: 2\noracles: {V1: oracle-x}\n")
    for seed in (1, 2):
        (docs / f"w__s{seed}.json").write_text(json.dumps(_seed_doc(seed, violations=1)))
    (docs / "w__pooled.json").write_text(json.dumps(_pooled_doc()))
    known = tmp_path / "known.yaml"
    known.write_text("known: []\n")
    args = ["--config", str(cfg), "--docs", str(docs), "--baselines", str(tmp_path / "none"), "--known", str(known),
            "--out-json", str(tmp_path / "r.json"), "--out-md", str(tmp_path / "r.md"), "--metrics-module", "tests.helpers.rpg_gate_stub_metrics", "--no-rerun"]
    assert rep.main(args) == 0
    assert rep.main([*args, "--fail-on-red"]) == 1
    assert json.loads((tmp_path / "r.json").read_text())["verdict"] == "red" and "oracle: oracle-x" in (tmp_path / "r.md").read_text()
