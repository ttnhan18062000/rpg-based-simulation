"""TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE: the shared known-reds module (match, shadowing, expiry, stale mapping, both kinds)."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

from tools.test_architecture import known_reds as kr
from tools.test_architecture.known_reds import GATE_STATES, RPG_GATE_SPEC, SLOW_SPEC

TODAY = dt.date(2026, 10, 9)
ARCH = Path(kr.__file__).parent
SLOW_FILE = ARCH / "slow_known_reds.yaml"
GATE_FILE = ARCH / "rpg_gate_known.yaml"


def _slow(match, expires="2026-12-01", kind="broken", **extra):
    return {"match": match, "ticket": "TCK-X", "owner": "someone", "added_on": "2026-10-01", "expires_on": expires, "kind": kind, **extra}


def _gate(match, state="fail", expires="2026-12-01", **extra):
    return {"match": match, "ticket": "TCK-X", "owner": "someone", "added_on": "2026-10-01", "expires_on": expires, "state": state, **extra}


# --- both real registry files lint clean (the lint runs in the tools lane with the rest of tests/unit/tools) ---


def test_the_real_slow_registry_lints_clean():
    assert kr.lint_file(SLOW_FILE, SLOW_SPEC) == []


def test_the_real_gate_registry_lints_clean_and_every_entry_is_owned():
    """Every entry has a live owner ticket (todos/ or inprogress/; a done ticket means the entry is stale and must be retired), a match of the right shape
    for its state, and an expiry within 90 days of when it was added. No exact entry is pinned: the registry is data."""
    assert GATE_FILE.exists()
    assert kr.lint_file(GATE_FILE, RPG_GATE_SPEC) == []
    tickets = ARCH.parents[1] / "agent-working" / "tickets"
    validity_id = re.compile(r"^V\d+(:.+)?$")
    for entry in kr.load_known_reds(GATE_FILE, RPG_GATE_SPEC):
        name = f"{entry['match']} ({entry['ticket']})"
        live = [tickets / folder / f"{entry['ticket']}.md" for folder in ("todos", "inprogress")]
        in_done = (tickets / "done" / f"{entry['ticket']}.md").exists()
        assert not in_done, f"{name}: the owning ticket is done, so the entry is stale and must be retired"
        assert any(path.exists() or any(path.parent.glob(f"**/{path.name}")) for path in live), f"{name}: no such ticket under todos/ or inprogress/"
        if entry["state"] == "fail":
            assert validity_id.match(entry["match"]) and "*" not in entry["match"].split(":")[0], f"{name}: a fail entry matches a validity id (V<n> or V<n>:<group>), never a wildcard"
        else:
            assert not validity_id.match(entry["match"]), f"{name}: a drift entry must not match a validity id"
        added = dt.date.fromisoformat(str(entry["added_on"]))
        assert dt.date.fromisoformat(str(entry["expires_on"])) <= added + dt.timedelta(days=90), f"{name}: expires more than 90 days after it was added"


def test_lint_file_reports_a_missing_file_a_wrong_top_key_and_a_non_list(tmp_path):
    assert "file not found" in kr.lint_file(tmp_path / "nope.yaml", SLOW_SPEC)[0]
    wrong = tmp_path / "wrong.yaml"
    wrong.write_text("known: []\n", encoding="utf-8")
    assert "expected a mapping with a list under 'known_reds'" in kr.lint_file(wrong, SLOW_SPEC)[0]
    not_list = tmp_path / "notlist.yaml"
    not_list.write_text("known: {a: 1}\n", encoding="utf-8")
    assert kr.lint_file(not_list, RPG_GATE_SPEC)


# --- matching ---


def test_first_matching_entry_wins():
    known = [_slow("tests.a.test_x*", kind="flaky"), _slow("tests.a*")]
    assert kr.owner_of("tests.a.test_x::t", known)["kind"] == "flaky"
    assert kr.owner_of("tests.a.test_y::t", known)["kind"] == "broken"
    assert kr.owner_of("tests.b::t", known) is None


def test_a_metric_pattern_matches_the_id_with_and_without_a_group():
    known = [_gate("combat.win_rate:*", "drift"), _gate("combat.win_rate")]
    assert kr.owner_of("combat.win_rate:goblin", known, "drift") is known[0]
    assert kr.owner_of("combat.win_rate", known, "fail") is known[1]
    assert kr.owner_of("combat.win_rate:goblin", known, "fail") is None  # the fail entry has no group pattern


def test_the_same_metric_can_be_owned_separately_in_fail_and_drift():
    known = [_gate("m.a*", "fail"), _gate("m.a*", "drift")]
    assert kr.owner_of("m.a1", known, "fail") is known[0]
    assert kr.owner_of("m.a1", known, "drift") is known[1]
    assert kr.lint_known_reds(known, RPG_GATE_SPEC) == []  # different states never shadow each other


# --- shadowing ---


def test_a_catch_all_before_a_narrower_entry_is_shadowing():
    problems = kr.lint_known_reds([_slow("tests.*"), _slow("tests.a.test_x*")], SLOW_SPEC)
    assert any("shadowed by the earlier entry 'tests.*'" in p for p in problems)


def test_a_catch_all_after_the_narrower_entry_is_fine():
    assert kr.lint_known_reds([_slow("tests.a.test_x*"), _slow("tests.*")], SLOW_SPEC) == []


def test_shadowing_is_per_state_but_still_caught_within_a_state():
    problems = kr.lint_known_reds([_gate("m.*", "drift"), _gate("m.a*", "drift")], RPG_GATE_SPEC)
    assert any("shadowed" in p for p in problems)
    assert kr.lint_known_reds([_gate("m.*", "fail"), _gate("m.a*", "drift")], RPG_GATE_SPEC) == []


# --- expiry and classification ---


def test_expiry_is_strictly_before_today():
    assert kr.is_expired(_slow("a", expires="2026-10-08"), TODAY) is True
    assert kr.is_expired(_slow("a", expires="2026-10-09"), TODAY) is False
    assert kr.days_to_expiry(_slow("a", expires="2026-10-12"), TODAY) == 3


def test_classify_splits_unowned_and_expired_and_respects_state():
    known = [_gate("m.owned*", "fail"), _gate("m.old*", "fail", expires="2026-10-01"), _gate("m.drifty*", "drift")]
    failing = {"m.owned1": "x", "m.old1": "x", "m.unknown": "x", "m.drifty1": "x"}
    unowned, expired = kr.classify(failing, known, TODAY, "fail")
    assert unowned == ["m.drifty1", "m.unknown"] and expired == ["m.old1"]
    unowned, expired = kr.classify({"m.drifty1": "x"}, known, TODAY, "drift")
    assert unowned == [] and expired == []


def test_classify_without_state_is_the_slow_behaviour():
    known = [_slow("tests.a*"), _slow("tests.b*", expires="2026-10-01")]
    assert kr.classify({"tests.a::t": "s", "tests.b::t": "s", "tests.c::t": "s"}, known, TODAY) == (["tests.c::t"], ["tests.b::t"])


# --- stale mappings ---


def test_stale_mappings_lists_entries_matching_nothing_failing():
    known = [_slow("tests.a*"), _slow("tests.gone*")]
    assert kr.stale_mappings({"tests.a::t": "s"}, known) == [known[1]]


def test_stale_mappings_by_state_judges_an_entry_only_against_its_own_state():
    known = [_gate("m.a*", "fail"), _gate("m.b*", "drift")]
    assert kr.stale_mappings({"m.a1": "x"}, known, "fail") == []
    assert kr.stale_mappings({"m.a1": "x"}, known, "drift") == [known[1]]
    assert set(kr.entries_by_state(known)) == set(GATE_STATES)


# --- both registry kinds: required fields, kinds and states, strictness, extensions ---


@pytest.mark.parametrize("field", ["match", "ticket", "owner", "added_on", "expires_on", "kind"])
def test_slow_entries_require_every_field(field):
    entry = _slow("tests.a*")
    del entry[field]
    assert f"missing {field}" in " ".join(kr.lint_known_reds([entry], SLOW_SPEC))


@pytest.mark.parametrize("field", ["match", "ticket", "owner", "added_on", "expires_on", "state"])
def test_gate_entries_require_every_field_and_no_kind(field):
    entry = _gate("m.a*")
    del entry[field]
    assert f"missing {field}" in " ".join(kr.lint_known_reds([entry], RPG_GATE_SPEC))
    assert kr.lint_known_reds([_gate("m.a*")], RPG_GATE_SPEC) == []  # no `kind` needed


def test_gate_state_must_be_fail_or_drift_and_slow_kind_must_be_broken_or_flaky():
    assert "state must be one of ('fail', 'drift')" in " ".join(kr.lint_known_reds([_gate("m.a*", "warn")], RPG_GATE_SPEC))
    assert "kind must be one of ('broken', 'flaky')" in " ".join(kr.lint_known_reds([_slow("tests.a*", kind="odd")], SLOW_SPEC))


@pytest.mark.parametrize("spec,make", [(SLOW_SPEC, _slow), (RPG_GATE_SPEC, _gate)])
def test_dates_expiry_order_and_brackets_are_linted_for_both_kinds(spec, make):
    assert "not an ISO date" in " ".join(kr.lint_known_reds([make("a*", expires="soon")], spec))
    assert "expires_on is before added_on" in " ".join(kr.lint_known_reds([make("a*", expires="2026-09-01")], spec))
    assert "character class" in " ".join(kr.lint_known_reds([make("a[1]")], spec))


def test_the_gate_registry_rejects_unknown_fields_but_the_slow_one_tolerates_them():
    assert "unknown field 'expected_signature'" in " ".join(kr.lint_known_reds([_gate("m.a*", expected_signature="x")], RPG_GATE_SPEC))
    assert kr.lint_known_reds([_slow("tests.a*", whatever="x")], SLOW_SPEC) == []


def test_a_registry_can_declare_an_extension_field_without_touching_the_rules():
    perf = kr.RegistrySpec("perf_debt", "ledger", kr.REQUIRED_ENTRY_FIELDS, kinds=kr.KINDS, optional_fields=("expected_signature",), strict_fields=True)
    assert kr.lint_known_reds([_slow("tests.perf*", expected_signature="x")], perf) == []
    assert "unknown field 'other'" in " ".join(kr.lint_known_reds([_slow("tests.perf*", other="x")], perf))


def test_load_known_reds_handles_missing_none_and_empty(tmp_path):
    assert kr.load_known_reds(None) == [] and kr.load_known_reds(tmp_path / "nope.yaml") == []
    empty = tmp_path / "e.yaml"
    empty.write_text("", encoding="utf-8")
    assert kr.load_known_reds(empty) == []
    none_list = tmp_path / "n.yaml"
    none_list.write_text("known_reds:\n", encoding="utf-8")
    assert kr.load_known_reds(none_list) == []


def test_the_slow_report_still_exposes_the_names_it_used_to_define():
    from tools.test_architecture import slow_regression_report as srr

    for name in ("load_known_reds", "lint_known_reds", "shadowed_entries", "owner_of", "is_expired", "days_to_expiry", "classify", "stale_mappings", "REQUIRED_ENTRY_FIELDS", "KINDS"):
        assert getattr(srr, name) is getattr(kr, name)


# --- TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED: scoped entries (`cases`) ---


def _scoped(cases, match="V3", **extra):
    return _gate(match, "fail", cases=cases, **extra)


def _v3(world, seed, *ids, violations=None, scope="run"):
    """A V3 fail finding as the gate report carries it."""
    examples = [{"entity_id": i, "kind": "starved", "tick": 100} for i in ids]
    finding = {"id": "V3", "group": "*", "scope": scope, "world": world, "state": "fail", "violations": len(examples) if violations is None else violations, "examples": examples}
    if scope == "run":
        finding["seed"] = seed
    return finding


N14 = {"world": "urban_political", "seed": 44, "entity_id": 28}
N15A = {"world": "crowded_frontier", "seed": 46, "entity_id": 38}
N15B = {"world": "frontier_living_world", "seed": 44, "entity_id": 2}


def _v1_registry():
    return [_scoped([N14], ticket="TCK-N14"), _scoped([N15A, N15B], ticket="TCK-N15")]


def _owner(finding, known=None):
    entry = kr.owner_of_finding("V3", finding, known if known is not None else _v1_registry(), state="fail")
    return entry["ticket"] if entry else None


def test_a_scoped_entry_owns_exactly_its_cases_and_scoped_entries_share_a_match():
    assert _owner(_v3("urban_political", 44, 28)) == "TCK-N14"
    assert _owner(_v3("crowded_frontier", 46, 38)) == "TCK-N15"
    assert _owner(_v3("frontier_living_world", 44, 2)) == "TCK-N15"


def test_a_fourth_fail_on_an_uncovered_world_and_seed_is_unowned():
    assert _owner(_v3("urban_political", 45, 28)) is None
    assert _owner(_v3("crowded_frontier", 47, 38)) is None
    assert _owner(_v3("new_world", 44, 2)) is None


def test_a_new_entity_on_a_covered_world_and_seed_is_unowned():
    assert _owner(_v3("urban_political", 44, 28, 29)) is None
    assert _owner(_v3("urban_political", 44, 29)) is None


def test_violations_above_the_examples_cap_is_unowned():
    assert _owner(_v3("urban_political", 44, 28, violations=6)) is None


def test_an_example_without_an_entity_id_is_unverifiable_so_unowned():
    finding = _v3("urban_political", 44, 28)
    finding["examples"] = [{"kind": "starved"}]
    assert _owner(finding) is None
    finding["examples"] = []
    finding["violations"] = 0
    assert _owner(finding) is None


def test_a_pooled_fail_is_never_owned_by_a_scoped_entry():
    assert _owner(_v3("urban_political", None, 28, scope="pooled")) is None


def test_a_case_without_entity_id_owns_every_fail_of_that_world_and_seed():
    known = [_scoped([{"world": "w", "seed": 1}])]
    assert _owner(_v3("w", 1, 5, 6, violations=9), known) == "TCK-X"
    assert _owner(_v3("w", 2, 5), known) is None


def test_an_unscoped_entry_after_scoped_ones_owns_what_they_do_not():
    known = [*_v1_registry(), _gate("V3", "fail", ticket="TCK-ALL")]
    assert _owner(_v3("anywhere", 1, 7), known) == "TCK-ALL"
    assert _owner(_v3("urban_political", 44, 28), known) == "TCK-N14"


def test_the_string_lookups_never_see_a_scoped_entry():
    known = _v1_registry()
    assert kr.owner_of("V3", known, "fail") is None
    assert kr.classify({"V3": ""}, known, TODAY, "fail") == (["V3"], [])
    assert kr.stale_mappings({}, known, "fail") == []


def test_stale_cases_names_each_case_that_no_longer_fails():
    ident = lambda f: f["id"]  # noqa: E731
    assert kr.stale_cases([_v3("urban_political", 44, 28)], _v1_registry(), ident) == [
        "V3 crowded_frontier/46/38", "V3 frontier_living_world/44/2"]
    assert kr.stale_cases([_v3("urban_political", 44, 99)], _v1_registry(), ident)[0] == "V3 urban_political/44/28"
    assert kr.stale_cases([], [_scoped([{"world": "w", "seed": 1}])], ident) == ["V3 w/1"]


def test_the_lint_accepts_the_v1_registry():
    assert kr.lint_known_reds(_v1_registry(), RPG_GATE_SPEC) == []


def test_the_lint_rejects_overlapping_cases_across_and_within_entries():
    across = kr.lint_known_reds([_scoped([N14]), _scoped([{**N14}], ticket="TCK-Y")], RPG_GATE_SPEC)
    assert any("overlaps" in p for p in across)
    within = kr.lint_known_reds([_scoped([N14, {"world": "urban_political", "seed": 44}])], RPG_GATE_SPEC)
    assert any("overlaps" in p for p in within)
    assert not [p for p in kr.lint_known_reds([_scoped([N14, {**N14, "entity_id": 29}])], RPG_GATE_SPEC) if "overlaps" in p]


def test_the_lint_rejects_an_unscoped_entry_before_a_scoped_one_but_not_the_reverse():
    assert any("shadowed" in p for p in kr.lint_known_reds([_gate("V3", "fail"), _scoped([N14])], RPG_GATE_SPEC))
    assert kr.lint_known_reds([_scoped([N14]), _gate("V3", "fail", ticket="TCK-Y")], RPG_GATE_SPEC) == []


@pytest.mark.parametrize(
    "cases, fragment",
    [
        ([], "non-empty list"),
        ("x", "non-empty list"),
        (["x"], "not a mapping"),
        ([{"seed": 1}], "world is required"),
        ([{"world": "w"}], "seed is required"),
        ([{"world": "w", "seed": "1"}], "seed is required"),
        ([{"world": "w", "seed": True}], "seed is required"),
        ([{"world": "w", "seed": 1, "extra": 1}], "unknown key"),
        ([{"world": "w", "seed": 1, "entity_id": None}], "entity_id"),
    ],
)
def test_the_lint_rejects_an_empty_or_malformed_case(cases, fragment):
    assert any(fragment in p for p in kr.lint_known_reds([_scoped(cases)], RPG_GATE_SPEC))


def test_a_drift_entry_with_cases_is_a_lint_error():
    assert any("only on a state: fail" in p for p in kr.lint_known_reds([_gate("O1", "drift", cases=[N14])], RPG_GATE_SPEC))


def test_the_slow_registry_rejects_cases():
    problems = kr.lint_known_reds([_slow("tests.a*", cases=[{"world": "w", "seed": 1}])], SLOW_SPEC)
    assert any("cases is not allowed in the slow registry" in p for p in problems)
