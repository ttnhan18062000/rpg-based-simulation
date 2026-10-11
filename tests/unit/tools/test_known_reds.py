"""TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE: the shared known-reds module (match, shadowing, expiry, stale mapping, both kinds)."""

from __future__ import annotations

import datetime as dt
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


def test_the_real_gate_registry_exists_is_empty_and_lints_clean():
    assert GATE_FILE.exists()
    assert kr.load_known_reds(GATE_FILE, RPG_GATE_SPEC) == []
    assert kr.lint_file(GATE_FILE, RPG_GATE_SPEC) == []


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
