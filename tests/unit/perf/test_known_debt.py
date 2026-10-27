"""The perf known-debt ledger is a user of the shared known-reds module (TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER)."""
from __future__ import annotations

import datetime as dt

import pytest

from tools.perf import known_debt as kd
from tools.test_architecture import known_reds as kr

TODAY = dt.date(2026, 10, 12)


def _entry(match="mixed_*", expires="2026-12-01", **extra):
    return {"match": match, "ticket": "TCK-X", "owner": "perf-implementer", "added_on": "2026-10-01", "expires_on": expires, "kind": "broken", **extra}


def test_the_real_ledger_lints_clean() -> None:
    assert kd.LEDGER_PATH.exists()
    assert kd.lint_ledger() == []
    assert kd.main([]) == 0


def test_an_entry_with_a_signature_lints_clean() -> None:
    assert kd.lint_ledger_entries([_entry(expected_signature="INCONCLUSIVE:latency")]) == []


def test_the_lint_rejects_an_entry_that_expires_before_it_was_added() -> None:
    problems = kd.lint_ledger_entries([_entry(added_on="2026-11-01", expires="2026-10-01")])
    assert any("expires_on is before added_on" in p for p in problems)


def test_an_expired_entry_is_expired_for_a_failing_lane() -> None:
    entries = [_entry(expires="2026-10-01")]
    assert kr.classify({"mixed_100": "x"}, entries, TODAY) == ([], ["mixed_100"])


def test_a_shadowed_entry_is_rejected() -> None:
    problems = kd.lint_ledger_entries([_entry("mixed_*"), _entry("mixed_100")])
    assert any("shadowed" in p for p in problems)


def test_an_ownerless_entry_is_rejected() -> None:
    entry = _entry()
    del entry["owner"]
    assert any("missing owner" in p for p in kd.lint_ledger_entries([entry]))


def test_an_unknown_field_is_rejected() -> None:
    assert any("unknown field 'severity'" in p for p in kd.lint_ledger_entries([_entry(severity="high")]))


@pytest.mark.parametrize(
    "signature",
    ["INCONCLUSIVE", "PASS:latency", "INCONCLUSIVE:speed", "INCONCLUSIVE:latency:x", "inconclusive:latency", "", None, 3],
)
def test_a_malformed_signature_is_rejected(signature) -> None:
    problems = kd.lint_ledger_entries([_entry(expected_signature=signature)])
    assert any("expected_signature" in p for p in problems)


def test_every_check_name_is_a_real_compare_check() -> None:
    from src.perf import benchmark_record as br

    assert tuple(c.__name__.removeprefix("_check_") for _, c in br._CHECKS) == tuple(name for name, _ in br._CHECKS) == kd.CHECKS == br.CHECK_NAMES


def test_a_ledger_file_is_linted_through_the_main(tmp_path, capsys) -> None:
    path = tmp_path / "ledger.yaml"
    path.write_text("known_debt:\n  - match: 'mixed_*'\n    ticket: TCK-X\n    owner: o\n    added_on: '2026-10-01'\n"
                    "    expires_on: '2026-12-01'\n    kind: broken\n    expected_signature: 'PASS:latency'\n", encoding="utf-8")
    assert kd.main(["--path", str(path)]) == 1
    assert "expected_signature state" in capsys.readouterr().out
    assert kd.main(["--path", str(tmp_path / "missing.yaml")]) == 1
