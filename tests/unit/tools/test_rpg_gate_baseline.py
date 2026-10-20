"""TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS: schema, dual reference, staleness and the cited, immutable re-baseline."""
from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

import pytest

from tools.test_architecture import rpg_gate_baseline as rgb

NOW = dt.datetime(2026, 10, 11, tzinfo=dt.timezone.utc)
REAL_DIR = Path(__file__).resolve().parents[3] / rgb.DEFAULT_DIR


def _config(**over) -> rgb.GateConfig:
    base = dict(
        worlds=("w",), seeds=(1, 2), ticks=5000, stale_after_days=30,
        stop_lines=(rgb.StopLine("R1", "O2.*", "*", None, 10),),
    )
    base.update(over)
    return rgb.GateConfig(**base)


RULING = {"ref": "memo-61", "date": "2026-10-11"}


def _candidate(deaths=3.0, violations=0, milestone="M1", pooled=0.4) -> dict:
    return {
        "milestone": milestone,
        "provenance": {"commit_sha": "abc", "harness_hash": "h1", "worlds": ["w"], "seeds": [1, 2], "ticks": 5000},
        "metrics": [
            {"id": "O2.deaths", "class": "outcome", "scope": "run", "world": "w", "group": "guards", "key": "STARVATION", "tick": 5000,
             "per_seed": {"1": deaths, "2": deaths}, "mean": deaths, "se": 0.5},
            {"id": "O9.share", "class": "outcome", "scope": "pooled", "world": "w", "group": "*", "value": pooled},
            {"id": "V1", "class": "validity", "scope": "run", "world": "w", "group": "*", "per_seed": {"1": violations, "2": 0}, "violations": violations},
        ],
    }


def _write_v1(directory: Path, **kw) -> Path:
    return rgb.rebaseline(_candidate(**kw), _config(), directory, pr=None, cites=["TCK-metric-set-v1"], now=NOW)


def _rebase(directory: Path, **kw):
    args = dict(pr="#9", divergence_id="DIV-1")
    args.update(kw.pop("cite", {}))
    return rgb.rebaseline(_candidate(**kw), _config(), directory, now=NOW, **args)


# ---- schema and lint

def test_first_baseline_is_written_valid_with_defaulted_times(tmp_path):
    path = _write_v1(tmp_path)
    doc = json.loads(path.read_text())
    assert path.name == "rpg_gate_v1.json" and doc["rebaseline"] is None
    assert doc["provenance"]["recorded_at"] == "2026-10-11T00:00:00Z"
    assert doc["provenance"]["stale_after"] == "2026-11-10T00:00:00Z"
    assert rgb.lint_dir(tmp_path) == []


def test_lint_flags_each_schema_break():
    doc = json.loads(json.dumps({**_candidate(), "schema": rgb.SCHEMA, "version": 1, "rebaseline": None,
                                 "provenance": {**_candidate()["provenance"], "cites": ["t"], "recorded_at": "2026-10-11T00:00:00Z", "stale_after": "2026-11-10T00:00:00Z"}}))
    assert rgb.lint_baseline(doc, "rpg_gate_v1.json") == []
    bad = copy.deepcopy(doc)
    bad["schema"] = "x"
    bad["provenance"]["stale_after"] = "2026-10-01T00:00:00Z"
    del bad["provenance"]["harness_hash"]
    bad["metrics"][0]["se"] = -1
    bad["metrics"][2]["violations"] = 5  # a baseline holds validity at 0
    bad["metrics"].append(copy.deepcopy(bad["metrics"][1]))
    problems = " | ".join(rgb.lint_baseline(bad, "rpg_gate_v2.json"))
    for expected in ("schema must be", "missing harness_hash", "does not match version 1", "se is negative", "0 violations", "duplicate row"):
        assert expected in problems


def test_lint_dir_rejects_a_version_gap_and_bad_json(tmp_path):
    _write_v1(tmp_path)
    (tmp_path / "rpg_gate_v3.json").write_text(json.dumps(json.loads((tmp_path / "rpg_gate_v1.json").read_text()) | {"version": 3}))
    (tmp_path / "rpg_gate_v4.json").write_text("{")
    problems = rgb.lint_dir(tmp_path)
    assert any("without a gap" in p for p in problems) and any("invalid JSON" in p for p in problems)


def test_every_checked_in_baseline_lints_clean():
    assert rgb.lint_dir(REAL_DIR) == []


# ---- dual reference

def test_references_are_the_last_and_the_first_of_the_current_milestone(tmp_path):
    _write_v1(tmp_path, milestone="M1")
    _rebase(tmp_path, deaths=4.0, milestone="M1")
    _rebase(tmp_path, deaths=5.0, milestone="M2")
    _rebase(tmp_path, deaths=6.0, milestone="M2")
    refs = rgb.resolve_references(rgb.load_baselines(tmp_path))
    assert (refs.last["version"], refs.milestone_first["version"]) == (4, 3)


def test_a_single_baseline_is_both_references_and_none_means_no_data(tmp_path):
    assert rgb.resolve_references(rgb.load_baselines(tmp_path)) is None
    _write_v1(tmp_path)
    refs = rgb.resolve_references(rgb.load_baselines(tmp_path))
    assert refs.last is refs.milestone_first or refs.last == refs.milestone_first


def test_load_refuses_an_invalid_file_rather_than_skipping_it(tmp_path):
    _write_v1(tmp_path)
    (tmp_path / "rpg_gate_v2.json").write_text(json.dumps({"schema": rgb.SCHEMA, "version": 2}))
    with pytest.raises(rgb.BaselineError):
        rgb.load_baselines(tmp_path)


# ---- staleness

@pytest.fixture
def v1(tmp_path):
    _write_v1(tmp_path)
    return rgb.load_baselines(tmp_path)[0]


def test_a_current_baseline_is_not_stale(v1):
    assert not rgb.staleness(v1, NOW, "h1", _config()).stale


def test_stale_by_date(v1):
    result = rgb.staleness(v1, NOW + dt.timedelta(days=30), "h1", _config())
    assert result.stale and "past stale_after" in result.reasons[0]


def test_stale_by_harness_hash_and_an_unknown_hash_is_also_stale(v1):
    assert "harness hash differs" in rgb.staleness(v1, NOW, "h2", _config()).reasons[0]
    assert "unknown" in rgb.staleness(v1, NOW, None, _config()).reasons[0]


@pytest.mark.parametrize("over,word", [({"worlds": ("w", "x")}, "worlds"), ({"seeds": (1, 2, 3)}, "seeds"), ({"ticks": 6000}, "ticks")])
def test_stale_by_config(v1, over, word):
    result = rgb.staleness(v1, NOW, "h1", _config(**over))
    assert result.stale and any(r.startswith(word) for r in result.reasons)


def test_staleness_collects_every_reason(v1):
    assert len(rgb.staleness(v1, NOW + dt.timedelta(days=40), "h2", _config(ticks=1)).reasons) == 3


# ---- re-baseline

def test_refused_without_a_citation(tmp_path):
    _write_v1(tmp_path)
    with pytest.raises(rgb.RebaselineRefused, match="divergence id"):
        rgb.rebaseline(_candidate(deaths=4.0), _config(), tmp_path, pr="#9", now=NOW)
    with pytest.raises(rgb.RebaselineRefused, match="PR"):
        rgb.rebaseline(_candidate(deaths=4.0), _config(), tmp_path, pr=None, divergence_id="DIV-1", now=NOW)
    assert [p.name for p in tmp_path.glob("*.json")] == ["rpg_gate_v1.json"]


def test_refused_past_a_stop_line_without_a_ruling_and_accepted_with_one(tmp_path):
    _write_v1(tmp_path)
    with pytest.raises(rgb.RebaselineRefused, match=r"stop line\(s\) \['R1'\]"):
        _rebase(tmp_path, deaths=11.0)
    path = _rebase(tmp_path, deaths=11.0, cite={"owner_ruling": RULING})
    record = json.loads(path.read_text())["rebaseline"]
    assert record["stop_lines_crossed"] == ["R1"] and record["owner_ruling"] == RULING


def test_an_undecided_world_semantic_change_needs_a_ruling_too(tmp_path):
    _write_v1(tmp_path)
    with pytest.raises(rgb.RebaselineRefused, match="undecided"):
        _rebase(tmp_path, cite={"undecided_world_semantic_change": True})


def test_a_memo_row_alone_is_a_citation(tmp_path):
    _write_v1(tmp_path)
    path = _rebase(tmp_path, deaths=4.0, cite={"divergence_id": None, "memo_row": "memo-54"})
    assert json.loads(path.read_text())["rebaseline"]["memo_row"] == "memo-54"


def test_accepted_rebaseline_writes_a_new_file_and_leaves_the_old_bytes_alone(tmp_path):
    first = _write_v1(tmp_path)
    before = first.read_bytes()
    second = _rebase(tmp_path, deaths=4.0)
    assert second.name == "rpg_gate_v2.json" and first.read_bytes() == before
    record = json.loads(second.read_text())["rebaseline"]
    assert record["previous_version"] == 1 and record["pr"] == "#9"
    assert record["changes"] == [{"row": "O2.deaths:run:w:guards:STARVATION:5000", "before": 3.0, "after": 4.0}]
    assert rgb.lint_dir(tmp_path) == []


def test_existing_target_is_never_overwritten(tmp_path, monkeypatch):
    _write_v1(tmp_path)
    monkeypatch.setattr(rgb, "load_baselines", lambda d: [])  # a stale view that would pick version 1 again
    with pytest.raises(FileExistsError):
        _write_v1(tmp_path)


def test_changes_include_rows_that_appear_or_disappear():
    a = _candidate()["metrics"]
    b = a[:2] + [{"id": "V9", "class": "validity", "scope": "run", "world": "w", "group": "*", "violations": 2}]
    assert rgb.changes_between(a, b) == [
        {"row": "V1:run:w:*", "before": 0, "after": None},
        {"row": "V9:run:w:*", "before": None, "after": 2},
    ]


def test_stop_line_bounds_and_patterns():
    rows = _candidate(deaths=2.0)["metrics"]
    low = [rgb.StopLine("R2", "O2.*", "guards", 3, None)]
    assert rgb.stop_lines_crossed(rows, low) == ["R2"]
    assert rgb.stop_lines_crossed(rows, [rgb.StopLine("R2", "O2.*", "wolves", 3, None)]) == []  # another group
    assert rgb.stop_lines_crossed(rows, [rgb.StopLine("R3", "V*", "*", None, 0)]) == []  # at the bound is inside


def test_load_config_and_cli(tmp_path, capsys):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("worlds: [w]\nseeds: [1, 2]\nticks: 5000\nstale_after_days: 30\nstop_lines:\n  - {name: R1, metric: 'O2.*', max: 10}\n")
    assert rgb.load_config(cfg) == _config()
    cand = tmp_path / "cand.json"
    cand.write_text(json.dumps(_candidate()))
    out = tmp_path / "baselines"
    assert rgb.main(["rebaseline", "--candidate", str(cand), "--config", str(cfg), "--dir", str(out), "--cite", "TCK-metric-set-v1"]) == 0
    assert rgb.main(["rebaseline", "--candidate", str(cand), "--config", str(cfg), "--dir", str(out)]) == 2  # no citation
    assert "REFUSED" in capsys.readouterr().err
    assert rgb.main(["lint", "--dir", str(out)]) == 0
    cfg.write_text("worlds: [w]\n")
    with pytest.raises(rgb.BaselineError):
        rgb.load_config(cfg)


# ---- review round: validity is absolute, cites, scope, structured ruling, order, duplicates

def test_a_validity_fail_can_not_be_recorded_even_with_a_ruling(tmp_path):
    with pytest.raises(rgb.BaselineError, match="0 violations"):
        rgb.rebaseline(_candidate(violations=2), _config(), tmp_path, pr=None, cites=["t"], now=NOW)
    _write_v1(tmp_path)
    with pytest.raises(rgb.BaselineError, match="rpg_gate_known"):
        _rebase(tmp_path, violations=2, cite={"owner_ruling": RULING})
    assert [p.name for p in tmp_path.glob("*.json")] == ["rpg_gate_v1.json"]


def test_cites_are_required_on_every_version_and_must_hold_the_pr_and_a_citation(tmp_path):
    with pytest.raises(rgb.RebaselineRefused, match="cite"):
        rgb.rebaseline(_candidate(), _config(), tmp_path, pr=None, now=NOW)
    path = _write_v1(tmp_path)
    doc = json.loads(path.read_text())
    assert doc["provenance"]["cites"] == ["TCK-metric-set-v1"]
    second = json.loads(_rebase(tmp_path, deaths=4.0).read_text())
    assert second["provenance"]["cites"] == ["#9", "DIV-1"]
    doc["provenance"]["cites"] = []
    assert any("cites" in p for p in rgb.lint_baseline(doc, "rpg_gate_v1.json"))
    del doc["provenance"]["cites"]
    assert any("missing cites" in p for p in rgb.lint_baseline(doc, "rpg_gate_v1.json"))
    second["provenance"]["cites"] = ["#9"]
    assert any("divergence id or memo row" in p for p in rgb.lint_baseline(second, "rpg_gate_v2.json"))


def test_scope_is_required_and_a_pooled_row_has_a_value_and_no_per_seed():
    rows = _candidate()["metrics"]
    problems = rgb._lint_metrics([{**rows[1], "per_seed": {"1": 1}}, {**rows[0], "scope": "weekly"}, {k: v for k, v in rows[2].items() if k != "scope"}])
    joined = " | ".join(problems)
    assert "no per_seed" in joined and "scope must be one of" in joined and "missing scope" in joined
    assert rgb.row_value(rows[0]) == 3.0 and rgb.row_value(rows[1]) == 0.4  # run mean; pooled value
    assert rgb.stop_lines_crossed(rows, [rgb.StopLine("P", "O9.*", "*", None, 0.3)]) == ["P"]


def test_owner_ruling_must_be_structured_with_an_iso_date(tmp_path):
    _write_v1(tmp_path)
    for bad in ({"ref": "memo-61"}, {"ref": "memo-61", "date": "yesterday"}, "free text"):
        with pytest.raises(rgb.RebaselineRefused, match="owner_ruling"):
            _rebase(tmp_path, deaths=11.0, cite={"owner_ruling": bad})
    doc = json.loads(_rebase(tmp_path, deaths=11.0, cite={"owner_ruling": RULING}).read_text())
    doc["rebaseline"]["owner_ruling"] = "free text"
    assert any("not free text" in p for p in rgb.lint_baseline(doc, "rpg_gate_v2.json"))


def test_staleness_ignores_the_order_of_worlds_and_seeds(tmp_path):
    cfg = _config(worlds=("w", "x"), seeds=(2, 1))
    cand = _candidate()
    cand["provenance"] = {**cand["provenance"], "worlds": ["x", "w"], "seeds": [1, 2]}
    rgb.rebaseline(cand, cfg, tmp_path, pr=None, cites=["t"], now=NOW)
    assert not rgb.staleness(rgb.load_baselines(tmp_path)[0], NOW, "h1", cfg).stale


def test_config_rejects_a_duplicate_seed_or_world(tmp_path):
    cfg = tmp_path / "c.yaml"
    for body in ("worlds: [w]\nseeds: [1, 1]\n", "worlds: [w, w]\nseeds: [1]\n"):
        cfg.write_text(body + "ticks: 1\nstale_after_days: 1\n")
        with pytest.raises(rgb.BaselineError, match="duplicate"):
            rgb.load_config(cfg)


def test_stop_lines_apply_to_outcome_rows_only():
    rows = _candidate()["metrics"]  # includes a validity row at 0
    assert rgb.stop_lines_crossed(rows, [rgb.StopLine("ALL", "*", "*", 1, None)]) == ["ALL"]  # the pooled outcome row (0.4) is below 1
    only_validity = [r for r in rows if r["class"] == "validity"]
    assert rgb.stop_lines_crossed(only_validity, [rgb.StopLine("ALL", "*", "*", 1, None)]) == []


def test_the_first_baseline_past_a_stop_line_needs_a_ruling_too(tmp_path):
    cfg = _config()
    with pytest.raises(rgb.RebaselineRefused, match="owner_ruling"):
        rgb.rebaseline(_candidate(deaths=11.0), cfg, tmp_path, pr=None, cites=["t"], now=NOW)
    with pytest.raises(rgb.RebaselineRefused, match="undecided"):
        rgb.rebaseline(_candidate(), cfg, tmp_path, pr=None, cites=["t"], undecided_world_semantic_change=True, now=NOW)
    path = rgb.rebaseline(_candidate(deaths=11.0), cfg, tmp_path, pr=None, cites=["t"], owner_ruling=RULING, now=NOW)
    assert json.loads(path.read_text())["owner_ruling"] == RULING and rgb.lint_dir(tmp_path) == []


def test_a_v1_ruling_records_the_lines_it_covers(tmp_path):
    path = rgb.rebaseline(_candidate(deaths=11.0), _config(), tmp_path / "b", pr=None, cites=["t"], owner_ruling=RULING, now=NOW)
    assert json.loads(path.read_text())["stop_lines_crossed"] == ["R1"]


# ---- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK: required_validity in the config

def _cfg_text(extra):
    return "worlds: [w]\nseeds: [1, 2]\nticks: 5000\nstale_after_days: 30\n" + extra


def test_required_validity_loads_as_a_level_mapping_and_defaults_to_empty(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_cfg_text(""))
    assert rgb.load_config(cfg).required_validity == {}
    cfg.write_text(_cfg_text("required_validity: {run: [V1, V8], pooled: [V7]}\n"))
    loaded = rgb.load_config(cfg)
    assert loaded.required_validity == {"run": ("V1", "V8"), "pooled": ("V7",)}
    assert loaded.required_at("run") == ("V1", "V8") and loaded.required_at("pooled") == ("V7",)
    cfg.write_text(_cfg_text("required_validity: {run: [V1], pooled: [V1]}\n"))  # an id may be required at both levels
    assert rgb.load_config(cfg).required_at("pooled") == ("V1",)
    cfg.write_text(_cfg_text("required_validity: {run: [V1]}\n"))
    assert rgb.load_config(cfg).required_at("pooled") == ()


@pytest.mark.parametrize("text, match", [
    ("required_validity: [V1, V8]\n", "plain list is refused"),
    ("required_validity: V8\n", "must map a level"),
    ("required_validity: {seed: [V1]}\n", "unknown level"),
    ("required_validity: {run: [V1], world: [V2]}\n", "unknown level"),
    ("required_validity: {run: V8}\n", "must be a list"),
    ("required_validity: {run: [V8, V8]}\n", "duplicate"),
    ("required_validity: {pooled: [V7, V7]}\n", "duplicate"),
    ("required_validity: {run: [O1]}\n", r"V<n>"),
    ("required_validity: {run: [V]}\n", r"V<n>"),
    ("required_validity: {pooled: [8]}\n", r"V<n>"),
])
def test_a_malformed_required_validity_is_refused(tmp_path, text, match):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_cfg_text(text))
    with pytest.raises(rgb.BaselineError, match=match):
        rgb.load_config(cfg)


def test_the_committed_gate_config_requires_v7_pooled_and_the_rest_per_run():
    from pathlib import Path

    loaded = rgb.load_config(Path(__file__).resolve().parents[3] / "tests" / "simulation_quality" / "rpg_gate" / "config.yaml")
    assert loaded.required_validity == {"run": ("V1", "V2", "V3", "V4", "V5", "V6", "V8"), "pooled": ("V7",)}


def test_rebaseline_carries_undefined_rows_and_the_lint_checks_them(tmp_path):
    candidate = _candidate()
    candidate["undefined_rows"] = [{"row": "O8:pooled:w:*", "reason": "empty_denominator"}]
    path = rgb.rebaseline(candidate, _config(), tmp_path, pr=None, cites=["TCK-metric-set-v1"], now=NOW)
    assert json.loads(path.read_text())["undefined_rows"] == candidate["undefined_rows"] and rgb.lint_dir(tmp_path) == []
    doc = json.loads(path.read_text())
    doc["undefined_rows"] = [{"row": "O9.share:pooled:w:*", "reason": "empty_denominator"}, {"row": "x"}, "bad"]
    problems = rgb.lint_baseline(doc, filename="rpg_gate_v1.json")
    assert problems == ["undefined_rows[0]: O9.share:pooled:w:* is listed as undefined but is still in metrics", "undefined_rows[1]: missing reason", "undefined_rows[2]: not an object"]
