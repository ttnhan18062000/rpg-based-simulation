"""Shared helpers for the profiling toolkit (profile_tick, profile_diff, flag_attribution).

Pure functions for headers, statistics, folded-stack parsing and diffing, and attribution arithmetic
live here and import nothing from ``src`` at module level, so they are testable without the engine
or a profiler binary. The functions that build and run a kernel import the engine lazily.

Everything produced by these tools is diagnostic evidence about where time goes. It is labeled
PROVISIONAL on every output: it is not a baseline or a capacity claim, and the roadmap's RPG-core
stability entry gate forbids using a measurement as evidence before it is lifted.

Ticket: TCK-20261003-PERF-PROFILING-TOOLKIT.
"""
from __future__ import annotations

import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = Path("reports/perf")  # already git-ignored (reports/*); nothing generated is committed

PROVISIONAL_LINE = (
    "PROVISIONAL: diagnostic evidence about where time goes, not a baseline or a capacity claim "
    "(RPG-core stability entry gate not yet lifted)."
)

METROPOLIS_WARNING = (
    "WARNING: the 'metropolis' scenario is known defective: build_metropolis_state() stacks entities "
    "on the same tile by construction (TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION). "
    "Treat its numbers as unreliable."
)

# Install hints, named in the missing-binary message.
INSTALL_HINTS = {
    "py-spy": 'uv sync --group perf   (the opt-in `perf` dependency group in pyproject.toml)',
    "memray": 'uv sync --group profiling   (memray is in the opt-in `profiling` group)',
}

# Metric counters recorded per tick as the "processed work" context for a profile.
WORK_COUNTER_KEYS = ("phase_runs", "phase_skips", "raw_entity_updates", "compacted_entity_updates")


# --------------------------------------------------------------------------- header

def git_commit(root: Path = REPO_ROOT) -> str:
    try:
        head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain", "--", "src"], text=True,
                                        stderr=subprocess.DEVNULL).strip()
        return head + (" (src has uncommitted changes)" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def header_fields(scenario: str, entities: int, seed: int, warmup: int, ticks: int,
                  commit: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> "OrderedDict[str, Any]":
    fields: "OrderedDict[str, Any]" = OrderedDict()
    fields["commit"] = commit if commit is not None else git_commit()
    fields["scenario"] = scenario
    fields["entities"] = entities
    fields["seed"] = seed
    fields["warmup_ticks"] = warmup
    fields["measured_ticks"] = ticks
    fields["python"] = platform.python_version()
    fields["host_cores"] = os.cpu_count()
    for key, value in (extra or {}).items():
        fields[key] = value
    return fields


def header_lines(fields: Dict[str, Any], title: str) -> List[str]:
    """Header as plain lines (no comment marker)."""
    lines = [title, PROVISIONAL_LINE]
    lines += [f"{k}: {v}" for k, v in fields.items()]
    if fields.get("scenario") == "metropolis":
        lines.append(METROPOLIS_WARNING)
    return lines


def comment_header(fields: Dict[str, Any], title: str) -> str:
    return "\n".join(f"# {line}" for line in header_lines(fields, title)) + "\n"


def markdown_header(fields: Dict[str, Any], title: str) -> str:
    lines = header_lines(fields, title)
    out = [f"# {lines[0]}", "", f"> **{lines[1]}**", ""]
    out += [f"- {line}" for line in lines[2:]]
    return "\n".join(out) + "\n"


def parse_comment_header(text: str) -> Dict[str, str]:
    """``key: value`` pairs from the leading ``#`` lines of a folded-stack file."""
    found: Dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        body = line[1:].strip()
        if ":" in body and not body.startswith("PROVISIONAL") and not body.startswith("WARNING"):
            key, _, value = body.partition(":")
            found[key.strip()] = value.strip()
    return found


# --------------------------------------------------------------------------- statistics

def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def p95(values: Sequence[float]) -> float:
    """Nearest-rank 95th percentile (deterministic, no interpolation)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(0.95 * len(ordered)))
    return ordered[rank - 1]


def spread(values: Sequence[float]) -> Dict[str, float]:
    """Run-to-run spread of a per-repetition statistic."""
    if not values:
        return {"min": 0.0, "max": 0.0, "range": 0.0}
    lo, hi = min(values), max(values)
    return {"min": lo, "max": hi, "range": hi - lo}


def phase_table(per_tick_costs: Sequence[Dict[str, float]], tick_wall_ms: Sequence[float]) -> List[Dict[str, Any]]:
    """Per-phase mean and p95 ms per tick and share of the mean tick wall time.

    Phases come from ``kernel._phase_costs``. Some entries are sub-phases of a larger one, so shares
    do not sum to 100%: they are shares of the whole tick, not a partition.
    """
    tick_mean = mean(tick_wall_ms)
    names: List[str] = []
    for costs in per_tick_costs:
        for name in costs:
            if name not in names:
                names.append(name)
    rows = []
    for name in names:
        series = [c.get(name, 0.0) for c in per_tick_costs]
        m = mean(series)
        rows.append({
            "phase": name,
            "mean_ms": m,
            "p95_ms": p95(series),
            "share_of_tick": (m / tick_mean) if tick_mean else 0.0,
        })
    rows.sort(key=lambda r: (-r["mean_ms"], r["phase"]))
    return rows


# --------------------------------------------------------------------------- folded stacks

def parse_folded(text: str) -> "OrderedDict[str, int]":
    """``frame;frame;frame count`` lines into {stack: samples}. ``#`` lines and blanks are skipped."""
    stacks: "OrderedDict[str, int]" = OrderedDict()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        stack, _, count = line.rpartition(" ")
        if not stack:
            continue
        try:
            n = int(count)
        except ValueError:
            continue
        stacks[stack] = stacks.get(stack, 0) + n
    return stacks


def filter_stacks(stacks: Dict[str, int], marker: str) -> "tuple[OrderedDict[str, int], int, int]":
    """Keep stacks that contain ``marker`` in some frame; return (kept, kept_samples, total_samples)."""
    kept: "OrderedDict[str, int]" = OrderedDict()
    for stack, n in stacks.items():
        if marker in stack:
            kept[stack] = n
    return kept, sum(kept.values()), sum(stacks.values())


def render_folded(stacks: Dict[str, int]) -> str:
    return "".join(f"{stack} {n}\n" for stack, n in sorted(stacks.items()))


def folded_to_speedscope(stacks: Dict[str, int], name: str, header: Optional[List[str]] = None) -> Dict[str, Any]:
    """A speedscope 'sampled' profile built from folded stacks (one sample per unit of weight)."""
    frames: List[Dict[str, str]] = []
    index: Dict[str, int] = {}

    def frame_id(label: str) -> int:
        if label not in index:
            index[label] = len(frames)
            frames.append({"name": label})
        return index[label]

    samples: List[List[int]] = []
    weights: List[int] = []
    for stack, n in sorted(stacks.items()):
        samples.append([frame_id(f) for f in stack.split(";")])
        weights.append(n)
    doc: Dict[str, Any] = {
        "$schema": "https://www.speedscope.app/file-format-schema.json",
        "name": name,
        "exporter": "tools/perf/profile_tick.py (folded stacks from py-spy)",
        "activeProfileIndex": 0,
        "shared": {"frames": frames},
        "profiles": [{
            "type": "sampled",
            "name": name,
            "unit": "none",
            "startValue": 0,
            "endValue": sum(weights),
            "samples": samples,
            "weights": weights,
        }],
    }
    if header:
        doc["_header"] = header
    return doc


def normalize_frame(frame: str) -> str:
    """Drop the executing line from ``name (file:line)`` so one function is one frame.

    Lambdas keep their line: that line is what identifies a pipeline phase.
    """
    m = re.match(r"^(.*) \((.*?):(\d+)\)$", frame)
    if not m or m.group(1) == "<lambda>":
        return frame
    return f"{m.group(1)} ({m.group(2)})"


def frame_shares(stacks: Dict[str, int]) -> Dict[str, Dict[str, float]]:
    """Per frame: inclusive and self share of all samples.

    Inclusive counts a stack once per distinct frame it contains (recursion is not double counted).
    """
    total = sum(stacks.values())
    inclusive: Dict[str, int] = {}
    own: Dict[str, int] = {}
    for stack, n in stacks.items():
        frames = [normalize_frame(f) for f in stack.split(";")]
        for f in set(frames):
            inclusive[f] = inclusive.get(f, 0) + n
        own[frames[-1]] = own.get(frames[-1], 0) + n
    return {
        f: {"inclusive": inclusive[f] / total if total else 0.0, "self": own.get(f, 0) / total if total else 0.0}
        for f in inclusive
    }


def is_phase_frame(frame: str) -> bool:
    """A frame that names a kernel phase or a pipeline phase lambda."""
    name = frame.split(" (", 1)[0]
    if name.startswith("_phase_"):
        return True
    return name == "<lambda>" and "pipeline.py" in frame


def diff_shares(old: Dict[str, int], new: Dict[str, int], top: int = 15) -> Dict[str, Any]:
    """Largest changes in sample share between two folded profiles, for functions and for phases."""
    a, b = frame_shares(old), frame_shares(new)
    rows = []
    for frame in sorted(set(a) | set(b)):
        sa = a.get(frame, {"inclusive": 0.0, "self": 0.0})
        sb = b.get(frame, {"inclusive": 0.0, "self": 0.0})
        rows.append({
            "frame": frame,
            "phase": is_phase_frame(frame),
            "old_inclusive": sa["inclusive"], "new_inclusive": sb["inclusive"],
            "delta_inclusive": sb["inclusive"] - sa["inclusive"],
            "old_self": sa["self"], "new_self": sb["self"],
            "delta_self": sb["self"] - sa["self"],
        })

    def pick(subset: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
        ordered = sorted(subset, key=lambda r: (-r[key], r["frame"]))
        grew = [r for r in ordered if r[key] > 0][:top]
        shrank = [r for r in reversed(ordered) if r[key] < 0][:top]
        return {"grew": grew, "shrank": shrank}

    return {
        "old_samples": sum(old.values()),
        "new_samples": sum(new.values()),
        "functions_self": pick([r for r in rows if not r["phase"]], "delta_self"),
        "functions_inclusive": pick([r for r in rows if not r["phase"]], "delta_inclusive"),
        "phases_inclusive": pick([r for r in rows if r["phase"]], "delta_inclusive"),
    }


# --------------------------------------------------------------------------- attribution arithmetic

def attribute_flag(off_runs: Sequence[Dict[str, Any]], on_runs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Flag-off versus flag-on per-phase attribution from K repetitions of each.

    Each run is ``{"tick_wall_ms": [..], "per_tick_costs": [{phase: ms}], "events": {type: n}}``.
    Per phase: mean ms per tick for each state (mean of per-run means), the delta, the share of the
    total tick delta that phase accounts for, and the run-to-run spread of the per-run means.
    A phase's share can be negative or above 100% when others move the other way.
    """
    def per_run_means(runs: Sequence[Dict[str, Any]]) -> Dict[str, List[float]]:
        out: Dict[str, List[float]] = {}
        names: List[str] = []
        for run in runs:
            for costs in run["per_tick_costs"]:
                for n in costs:
                    if n not in names:
                        names.append(n)
        for n in names:
            out[n] = [mean([c.get(n, 0.0) for c in run["per_tick_costs"]]) for run in runs]
        out["<tick wall>"] = [mean(run["tick_wall_ms"]) for run in runs]
        return out

    off, on = per_run_means(off_runs), per_run_means(on_runs)
    total_delta = mean(on["<tick wall>"]) - mean(off["<tick wall>"])
    rows = []
    for name in sorted(set(off) | set(on)):
        a, b = off.get(name, [0.0] * len(off_runs)), on.get(name, [0.0] * len(on_runs))
        delta = mean(b) - mean(a)
        rows.append({
            "phase": name,
            "off_mean_ms": mean(a), "on_mean_ms": mean(b), "delta_ms": delta,
            "share_of_total_delta": (delta / total_delta) if total_delta else 0.0,
            "off_spread_ms": spread(a), "on_spread_ms": spread(b),
        })
    wall = [r for r in rows if r["phase"] == "<tick wall>"]
    phases = sorted((r for r in rows if r["phase"] != "<tick wall>"), key=lambda r: (-abs(r["delta_ms"]), r["phase"]))

    def event_totals(runs: Sequence[Dict[str, Any]]) -> Dict[str, float]:
        types: List[str] = []
        for run in runs:
            for t in run["events"]:
                if t not in types:
                    types.append(t)
        return {t: mean([run["events"].get(t, 0) for run in runs]) for t in sorted(types)}

    return {
        "repetitions": {"off": len(off_runs), "on": len(on_runs)},
        "tick_wall": wall[0] if wall else None,
        "total_delta_ms": total_delta,
        "phases": phases,
        "events_off": event_totals(off_runs),
        "events_on": event_totals(on_runs),
    }


# --------------------------------------------------------------------------- profiler binaries

def find_binary(name: str, explicit: Optional[str] = None) -> Optional[str]:
    """Path to a profiler binary: ``--<name>`` option, then ``$PY_SPY`` / ``$MEMRAY``, then PATH."""
    if explicit:
        return explicit if Path(explicit).exists() else None
    env = os.environ.get(name.upper().replace("-", "_"))
    if env and Path(env).exists():
        return env
    return shutil.which(name)


def missing_binary_message(name: str) -> str:
    return (f"{name} was not found. Install it with:\n  {INSTALL_HINTS.get(name, 'pip install ' + name)}\n"
            f"or pass its path explicitly. No substitute profiler is used.")


# --------------------------------------------------------------------------- child run (imports the engine lazily)

def build_state(scenario: str, entities: int):
    """Build the scenario state the way tools/perf/profile_engine.py does."""
    from src.perf.scenarios import SCENARIO_BUILDERS
    builder = SCENARIO_BUILDERS[scenario]
    if scenario == "resource":
        return builder(entity_count=int(entities * 0.7), node_count=int(entities * 0.3))
    if scenario == "combat":
        side = max(1, entities // 2)
        return builder(team_a_count=side, team_b_count=side)
    return builder(entity_count=entities)


def apply_flag_override(state: Any, flag: str, mode: str) -> "tuple[Any, Dict[str, str]]":
    """Force one feature flag ON or OFF for this process only; nothing tracked is modified.

    Two mechanisms read flags, so both are set. ``state.feature_flags`` is read directly by some
    consumers and merged by the kernel at construction: the state is frozen, so a NEW state is built
    with ``dataclasses.replace`` and returned (the original is not written through the freeze).
    ``FeatureFlagManager`` is built fresh with defaults every tick in
    ``AuthoritativeApplyPipeline.refine`` and cannot be given overrides, so its ``get_flag_mode`` is
    wrapped in this process only; that wrap is the documented measurement aid.

    Returns ``(new_state, what each mechanism reports)``.
    """
    import dataclasses

    from src.domains.optimization import feature_flags as ff

    if mode not in ("ON", "OFF"):
        raise ValueError(f"flag mode must be ON or OFF, got {mode!r}")
    if flag not in ff.FeatureFlagManager().get_all_flags():
        raise ValueError(f"unknown feature flag {flag!r}")
    target = ff.FeatureMode(mode)
    original = ff.FeatureFlagManager.get_flag_mode

    def patched(self, name: str):  # type: ignore[no-untyped-def]
        return target if name == flag else original(self, name)

    ff.FeatureFlagManager.get_flag_mode = patched  # type: ignore[method-assign]
    flags = dict(getattr(state, "feature_flags", None) or {})
    flags[flag] = mode
    new_state = dataclasses.replace(state, feature_flags=flags)
    return new_state, {"manager": ff.FeatureFlagManager().get_flag_mode(flag).value,
                       "state": str(new_state.feature_flags[flag])}


PROFILE_NAMES = ("PROD_SMALL", "PROD_DEFAULT", "PROD_LARGE", "PROD_STRESS")


def run_scenario_ticks(scenario: str, entities: int, seed: int, warmup: int, ticks: int,
                       flag: Optional[str] = None, flag_mode: Optional[str] = None,
                       profile_name: str = "PROD_LARGE") -> Dict[str, Any]:
    """Run warmup plus measured ticks in this process and return per-tick data.

    The measured loop is ``_measured_ticks``; profile_tick filters sampled stacks to ones that contain
    that frame so setup and import time are excluded from the profile.
    """
    from src.config import profiles as profiles_module
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG

    state = build_state(scenario, entities)
    override = None
    if flag and flag_mode:
        state, override = apply_flag_override(state, flag, flag_mode)
    kernel = Kernel(getattr(profiles_module, profile_name), state, DeterministicRNG(seed),
                    flags={"no_replay": True, "no_frame_pacing": True, "audit_mode": False})
    events: Dict[str, int] = {}
    tick_events = [0]

    def listener(batch: Any) -> None:
        for ev in batch:
            kind = str(getattr(ev, "event_type", None) or getattr(ev, "type", None) or type(ev).__name__)
            events[kind] = events.get(kind, 0) + 1
            tick_events[0] += 1

    kernel._event_listeners.append(listener)  # public-by-convention hook used by tests; see the guide
    try:
        for _ in range(warmup):
            kernel.tick_once()
        events.clear()
        data = _measured_ticks(kernel, ticks, tick_events)
    finally:
        kernel.shutdown()
    data["events"] = dict(sorted(events.items()))
    data["flag_override"] = override
    return data


def _measured_ticks(kernel: Any, ticks: int, tick_events: List[int]) -> Dict[str, Any]:
    import time
    per_tick: List[Dict[str, Any]] = []
    for _ in range(ticks):
        tick_events[0] = 0
        t0 = time.perf_counter_ns()
        kernel.tick_once()
        wall = (time.perf_counter_ns() - t0) / 1e6
        per_tick.append({
            "wall_ms": wall,
            "costs": {k: float(v) for k, v in dict(kernel._phase_costs).items()},  # private; as profile_engine does
            "mode": kernel.status.current_mode.name,
            "work": {k: kernel._metrics.get(k) for k in WORK_COUNTER_KEYS if k in kernel._metrics},
            "events": tick_events[0],
        })
    return {"ticks": per_tick}


def summarize_ticks(data: Dict[str, Any]) -> Dict[str, Any]:
    ticks = data["ticks"]
    modes: List[str] = []
    for t in ticks:
        if not modes or modes[-1] != t["mode"]:
            modes.append(t["mode"])
    work_keys = sorted({k for t in ticks for k in t["work"]})
    return {
        "tick_wall_ms": [t["wall_ms"] for t in ticks],
        "per_tick_costs": [t["costs"] for t in ticks],
        "runtime_mode_sequence": modes,
        "work_mean_per_tick": {k: mean([t["work"].get(k) or 0 for t in ticks]) for k in work_keys},
        "events": data.get("events", {}),
        "flag_override": data.get("flag_override"),
    }


def stamp_html(path: Path, lines: List[str]) -> None:
    """Add the PROVISIONAL header to a generated HTML file: a comment at the top and a visible banner."""
    text = path.read_text(encoding="utf-8")
    comment = "<!--\n" + "\n".join(line.replace("--", "- -") for line in lines) + "\n-->\n"
    banner = ("<div style=\"background:#fff3cd;color:#664d03;padding:8px 12px;font:14px sans-serif;"
              "border-bottom:1px solid #ffecb5\"><b>" + lines[1].replace("<", "&lt;") + "</b></div>")
    idx = text.find("<body")
    if idx != -1:
        close = text.find(">", idx)
        text = text[: close + 1] + banner + text[close + 1:]
    doctype_end = text.find(">") + 1 if text.lstrip().lower().startswith("<!doctype") else 0
    path.write_text(text[:doctype_end] + "\n" + comment + text[doctype_end:], encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_repo_on_path() -> None:
    """Make ``src`` importable when a tool is run as a script."""
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
