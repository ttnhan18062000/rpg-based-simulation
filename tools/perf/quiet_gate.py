"""The quiet-window gate of ``rerun_baselines record`` and the in-run foreign-load check for pinned runs.

Owner's CPU split (#715, 2026-10-30): Docker on vCPUs 0-3, perf runs pinned to 4-5. A pinned run is gated on the busy fraction of its own CPUs and, as well, on the 1-minute load average (a host-wide
check, since 2026-10-30), and checked again after it ran for work that landed on its CPUs mid-run (``user.slice``
is not confined to 0-3). An unpinned run keeps the load-average rule and skips the in-run check. Every reader is injectable: the unit tests never sleep and
never read the real ``/proc``.
"""

from __future__ import annotations

import fnmatch
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.perf.cpu_affinity import allowed_cpus

#: Seconds the busy fraction and the swap counters are observed over before each run.
SAMPLE_S = 5.0
#: A pinned run starts only when every allowed CPU is below this busy fraction (percent).
MAX_PINNED_BUSY_PCT = 10.0
#: A pinned run is stopped when work that was not the run's own used this share of its allowed CPUs (fraction of ``len(allowed) * wall seconds``).
MAX_FOREIGN_SHARE = 0.10


def _user_hz() -> float:
    try:
        return float(os.sysconf("SC_CLK_TCK"))
    except (ValueError, OSError, AttributeError):
        return 100.0


USER_HZ = _user_hz()
#: A transient ``systemd-run --scope`` unit; only its own cgroup holds nothing but this run (the own-scope guard of a pinned series).
SCOPE_PATTERN = "run-*.scope"

CpuJiffies = Dict[int, Tuple[int, int]]  # cpu -> (busy, total)


class GateError(Exception):
    """A reading the gate needs cannot be taken: the series refuses rather than skip the check."""


class SwapMovedError(GateError):
    """``pswpin``/``pswpout`` moved while a pinned run was measuring: the host swapped during the run."""

    def __init__(self, pages_in: int, pages_out: int) -> None:
        super().__init__(f"swap activity during the run (pswpin +{pages_in}, pswpout +{pages_out} pages)")
        self.pages_in, self.pages_out = pages_in, pages_out


def read_cpu_jiffies(path: str = "/proc/stat") -> CpuJiffies:
    """``{cpu: (busy, total)}`` from the per-CPU lines; busy = user + nice + system + irq + softirq + steal (idle and iowait are not busy)."""
    out: CpuJiffies = {}
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 9 and parts[0].startswith("cpu") and parts[0][3:].isdigit():
                v = [int(x) for x in parts[1:9]]
                out[int(parts[0][3:])] = (v[0] + v[1] + v[2] + v[5] + v[6] + v[7], sum(v))
    except (OSError, ValueError) as exc:
        raise GateError(f"cannot read {path}: {exc}") from exc
    if not out:
        raise GateError(f"{path} has no per-CPU lines")
    return out


def read_swap_counters(path: str = "/proc/vmstat") -> Optional[Tuple[int, int]]:
    """``(pswpin, pswpout)``, or ``None`` where the file cannot be read."""
    try:
        fields = dict(line.split()[:2] for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip())
        return int(fields["pswpin"]), int(fields["pswpout"])
    except (OSError, KeyError, ValueError):
        return None


def read_own_cgroup_path(proc_cgroup: str = "/proc/self/cgroup") -> str:
    """The cgroup v2 path of this process (``/user.slice/.../run-p1-i2.scope``). Raises ``GateError`` when it cannot be read."""
    try:
        lines = Path(proc_cgroup).read_text(encoding="utf-8").splitlines()
        return next(line.split(":", 2)[2] for line in lines if line.startswith("0::"))
    except (OSError, StopIteration, IndexError) as exc:
        raise GateError(f"cannot read this process's cgroup ({proc_cgroup}): {exc}") from exc


def read_own_cgroup_usec(proc_cgroup: str = "/proc/self/cgroup", root: str = "/sys/fs/cgroup") -> int:
    """``usage_usec`` of this process's cgroup (the ``systemd-run`` scope; the measure children inherit it). Raises ``GateError`` when it cannot be read."""
    rel = read_own_cgroup_path(proc_cgroup)
    try:
        stat = (Path(root) / rel.lstrip("/") / "cpu.stat").read_text(encoding="utf-8")
        return int(next(line.split()[1] for line in stat.splitlines() if line.startswith("usage_usec ")))
    except (OSError, StopIteration, IndexError, ValueError) as exc:
        raise GateError(f"cannot read this process's cgroup CPU time ({proc_cgroup}, cpu.stat): {exc}") from exc


def pinned_cpus(jiffies: CpuJiffies, allowed: Optional[Set[int]]) -> Optional[Set[int]]:
    """The allowed CPUs when they are a strict subset of the host's; ``None`` for an unpinned process."""
    if not allowed:
        return None
    host = set(jiffies)
    return set(allowed) if set(allowed) < host else None


def busy_pct(before: CpuJiffies, after: CpuJiffies, cpus: Set[int]) -> Dict[int, float]:
    out: Dict[int, float] = {}
    for cpu in sorted(cpus):
        (b0, t0), (b1, t1) = before[cpu], after[cpu]
        out[cpu] = round(100.0 * (b1 - b0) / (t1 - t0), 1) if t1 > t0 else 0.0
    return out


def gate_read(
    base: Callable[[], Dict[str, Optional[float]]],
    sleep: Callable[[float], None] = time.sleep,
    stat: Callable[[], CpuJiffies] = read_cpu_jiffies,
    vmstat: Callable[[], Optional[Tuple[int, int]]] = read_swap_counters,
    affinity: Callable[[], Optional[Set[int]]] = allowed_cpus,
    sample_s: float = SAMPLE_S,
) -> Dict[str, Any]:
    """One gate reading: ``base`` (load and memory) plus, over ``sample_s``, the busy fraction of each allowed CPU (pinned only) and the swap-in/out delta."""
    j0, s0 = stat(), vmstat()
    sleep(sample_s)
    j1, s1 = stat(), vmstat()
    reading: Dict[str, Any] = dict(base())
    allowed = pinned_cpus(j1, affinity())
    reading["pinned"] = sorted(allowed) if allowed else None
    reading["busy_pct"] = busy_pct(j0, j1, allowed) if allowed else None
    reading["swap_io_delta"] = (s1[0] - s0[0]) + (s1[1] - s0[1]) if s0 and s1 else None
    return reading


def evaluate(reading: Dict[str, Any], max_load: float, min_available_mb: float, max_probe_ms: Optional[float] = None) -> Tuple[bool, str]:
    """``(ok, text)``; the text lists every reading and names each failed check. A reading that cannot be taken (memory, swap counters) is a failure: on this host both are always readable, so a ``None`` means something is broken."""
    load, avail, busy, swap = reading.get("loadavg_1min"), reading.get("available_mb"), reading.get("busy_pct"), reading.get("swap_io_delta")
    failed: List[str] = []
    parts = [f"loadavg1 {load}", f"available {avail} MB"]
    if busy is not None:
        parts.append("busy % of allowed CPUs " + ", ".join(f"cpu{c} {p}" for c, p in busy.items()))
        if max(busy.values()) >= MAX_PINNED_BUSY_PCT:
            failed.append(f"allowed-CPU busy >= {MAX_PINNED_BUSY_PCT:.0f} %")
    if load is None or load >= max_load:
        failed.append(f"loadavg1 >= {max_load}")
    if max_probe_ms is not None and busy is not None:  # a pinned run only; off (None) unless the caller sets a limit
        probe = reading.get("probe_ms")
        parts.append(f"host-speed probe {probe} ms")
        if probe is None:
            failed.append("host-speed probe unreadable")
        elif probe > max_probe_ms:
            failed.append(f"host-speed probe > {max_probe_ms} ms")
    if avail is None:
        failed.append("available memory unreadable")
    elif avail < min_available_mb:
        failed.append(f"available memory < {min_available_mb:.0f} MB")
    if swap is None:
        failed.append("swap counters unreadable")
    else:
        parts.append(f"swap in+out pages {swap}")
        if swap != 0:
            failed.append("swap activity (pswpin/pswpout moved)")
    text = "; ".join(parts)
    return (not failed, f"{text} [FAILED: {', '.join(failed)}]" if failed else text)


def qg_error(path: str) -> GateError:
    return GateError(f"the pinned run is not in its own transient scope (cgroup {path}; need a {SCOPE_PATTERN} unit): that cgroup's CPU time is not this run's alone, so the foreign share would be understated. Run it under `systemd-run --user --scope ...`")


class RunWatch:
    """The in-run check of one pinned run: busy jiffies of the allowed CPUs and this cgroup's CPU time at the start and the end."""

    def __init__(self, stat: Callable[[], CpuJiffies] = read_cpu_jiffies, cgroup_usec: Callable[[], int] = read_own_cgroup_usec,
                 affinity: Callable[[], Optional[Set[int]]] = allowed_cpus, clock: Callable[[], float] = time.monotonic,
                 cgroup_path: Callable[[], str] = read_own_cgroup_path, vmstat: Callable[[], Optional[Tuple[int, int]]] = read_swap_counters) -> None:
        self._stat, self._usec, self._clock, self._path, self._vmstat = stat, cgroup_usec, clock, cgroup_path, vmstat
        self.swap_delta: Optional[Tuple[int, int]] = None
        self.cpus: Optional[Set[int]] = None
        self._affinity = affinity

    def start(self) -> None:
        """Raises ``GateError`` for a pinned process whose cgroup CPU time cannot be read, or that is not in its own ``run-*.scope``: the series refuses rather than skip the check."""
        j = self._stat()
        self.cpus = pinned_cpus(j, self._affinity())
        if self.cpus is None:
            return
        path = self._path()
        if not fnmatch.fnmatchcase(path.rstrip("/").rsplit("/", 1)[-1], SCOPE_PATTERN):
            raise qg_error(path)
        self._s0 = self._vmstat()
        if self._s0 is None:
            raise GateError("swap counters unreadable (/proc/vmstat): a pinned series needs the in-run swap check")
        self._j0, self._u0, self._t0 = j, self._usec(), self._clock()

    def finish(self) -> Optional[float]:
        """Raises ``SwapMovedError`` when pswpin/pswpout moved during the run. The foreign share of the run (``None`` for an unpinned run): (busy on the allowed CPUs - own CPU time) / (len(allowed) * wall seconds), clamped at 0."""
        if self.cpus is None:
            return None
        j1, u1, t1 = self._stat(), self._usec(), self._clock()
        s1 = self._vmstat()
        if s1 is None:
            raise GateError("swap counters unreadable (/proc/vmstat) at the end of the run")
        self.swap_delta = (s1[0] - self._s0[0], s1[1] - self._s0[1])
        if self.swap_delta != (0, 0):
            raise SwapMovedError(*self.swap_delta)
        busy_s = sum(j1[c][0] - self._j0[c][0] for c in self.cpus) / USER_HZ
        own_s = (u1 - self._u0) / 1e6
        wall = max(t1 - self._t0, 1e-9)
        return round(max(0.0, (busy_s - own_s) / (len(self.cpus) * wall)), 4)
