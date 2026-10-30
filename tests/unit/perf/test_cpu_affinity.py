from __future__ import annotations

import pytest

from src.perf import cpu_affinity as ca
from src.perf.benchmark_record import collect_runtime


@pytest.mark.parametrize(
    "cpus, text",
    [({4, 5}, "4-5"), (set(range(6)), "0-5"), ({0, 2, 3}, "0,2-3"), ({3}, "3"), ({5, 4, 0}, "0,4-5"), (set(), ""), ({0, 1, 3, 4, 5}, "0-1,3-5")],
)
def test_ranges_are_canonical_and_sorted(cpus, text) -> None:
    assert ca.format_cpu_ranges(cpus) == text


def test_collect_reads_the_injected_affinity() -> None:
    assert ca.collect_cpu_affinity(lambda pid: {5, 4}) == "4-5"


def test_collect_is_unknown_where_the_platform_cannot_say() -> None:
    def refuse(pid):
        raise OSError("no")

    assert ca.collect_cpu_affinity(refuse) == ca.UNKNOWN
    assert ca.collect_cpu_affinity(lambda pid: set()) == ca.UNKNOWN


def test_collect_runtime_records_the_live_affinity_and_leaves_host_fields_alone() -> None:
    runtime = collect_runtime()
    assert runtime.cpu_affinity == ca.collect_cpu_affinity()
    assert runtime.cpu_affinity != ca.UNKNOWN
