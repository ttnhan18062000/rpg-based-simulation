"""Perf known-debt ledger: the second user of the shared known-reds module (PERF-M2-T05b).

A perf lane (a benchmark scenario) that is already red has an owner, a ticket and an expiry, so a regression inside it is still
reported instead of hidden. The rules (owner, ticket, ``added_on``/``expires_on``, ``kind``, first-match ownership, shadowing) are the
shared ones in ``tools.test_architecture.known_reds``; this module only declares perf's :data:`PERF_DEBT_SPEC` and the one extension field.

``match`` is an ``fnmatch`` pattern on the scenario id. ``expected_signature`` (optional) says what the lane is known to report, so a
different outcome in the same lane is new drift and not the known debt. Its format is ``<STATE>:<check>``:

* ``STATE`` is a non-pass ``OutcomeState`` name: ``REGRESSION``, ``INCONCLUSIVE`` or ``NOT_APPLICABLE``;
* ``check`` is the ``compare()`` check that produced it: one of :data:`CHECKS`.

A signature outside that vocabulary is a lint problem, not a pattern that silently never matches.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from tools.test_architecture.known_reds import REQUIRED_ENTRY_FIELDS, RegistrySpec, lint_file, lint_known_reds, load_known_reds

LEDGER_PATH = Path(__file__).resolve().parents[2] / "docs" / "performance" / "known_debt_ledger.yaml"

SIGNATURE_STATES = ("REGRESSION", "INCONCLUSIVE", "NOT_APPLICABLE")
#: The ``compare()`` checks in ``src/perf/benchmark_record.py`` (without the ``_check_`` prefix), in the order they run.
CHECKS = ("schema", "each_side", "blocking_fields", "hash_scheme", "mode_sequences", "latency")

PERF_DEBT_SPEC = RegistrySpec(
    "perf_debt",
    "known_debt",
    REQUIRED_ENTRY_FIELDS,
    kinds=("broken", "flaky"),
    optional_fields=("expected_signature", "note"),
    strict_fields=True,
)


def signature_problem(signature: object) -> Optional[str]:
    """Why ``signature`` is not ``<STATE>:<check>`` in the closed vocabulary, or ``None`` when it is."""
    if not isinstance(signature, str) or signature.count(":") != 1:
        return f"expected_signature must be '<STATE>:<check>', got {signature!r}"
    state, check = signature.split(":")
    if state not in SIGNATURE_STATES:
        return f"expected_signature state must be one of {SIGNATURE_STATES}, got {state!r}"
    if check not in CHECKS:
        return f"expected_signature check must be one of {CHECKS}, got {check!r}"
    return None


def signature_problems(entries: Sequence[dict]) -> List[str]:
    """One problem per entry whose ``expected_signature`` is not in the format."""
    return [
        f"{entry.get('match', '?')}: {problem}"
        for entry in entries
        if "expected_signature" in entry
        for problem in [signature_problem(entry["expected_signature"])]
        if problem
    ]


def lint_ledger_entries(entries: Sequence[dict]) -> List[str]:
    """The shared lint plus the signature format."""
    return lint_known_reds(entries, PERF_DEBT_SPEC) + signature_problems(entries)


def lint_ledger(path: Path = LEDGER_PATH) -> List[str]:
    """Lint the ledger file: the shared structure lint (it also reports a missing file), then the signatures."""
    return lint_file(path, PERF_DEBT_SPEC) + signature_problems(load_known_reds(path, PERF_DEBT_SPEC))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Lint the perf known-debt ledger.")
    parser.add_argument("--path", type=Path, default=LEDGER_PATH)
    args = parser.parse_args(argv)
    problems = lint_ledger(args.path)
    for problem in problems:
        print(f"LEDGER: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
