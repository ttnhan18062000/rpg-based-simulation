#!/usr/bin/env python3
"""Where does a feature flag's cost go? Run a scenario with the flag OFF and ON, K times each.

For a named feature flag, runs the scenario from the same seed with the flag forced OFF and forced
ON (K repetitions each, interleaved so slow drift hits both), each run in its own child process
without any profiler attached, and prints per-phase mean ms per tick for each state, the delta, each
phase's share of the total tick delta, the run-to-run spread of the per-run means, and the event
counts for both states. This reproduces the 2026-09-14 ENABLE_COMBAT_ENGAGEMENT study as one command.

    python3 tools/perf/flag_attribution.py --flag ENABLE_COMBAT_ENGAGEMENT --scenario combat --entities 100

The flag is forced inside the child process only (``state.feature_flags`` plus a process-local wrap of
``FeatureFlagManager.get_flag_mode``); no tracked file is modified. Output is PROVISIONAL diagnostic
evidence, not a baseline: one sandbox, small entity counts, a handful of repetitions.

Ticket: TCK-20261003-PERF-PROFILING-TOOLKIT.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.perf import _profiling_common as common  # noqa: E402

PROFILE_TICK = Path(__file__).resolve().parent / "profile_tick.py"


def run_once(args: argparse.Namespace, mode: str, workdir: Path, index: int) -> Dict[str, Any]:
    out = workdir / f"{mode.lower()}_{index}.json"
    cmd = [sys.executable, str(PROFILE_TICK), "--child", "--scenario", args.scenario, "--entities", str(args.entities),
           "--seed", str(args.seed), "--warmup", str(args.warmup), "--ticks", str(args.ticks),
           "--profile", args.profile, "--flag", args.flag, "--flag-mode", mode, "--out-json", str(out)]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0 or not out.exists():
        raise RuntimeError(f"run flag={mode} #{index} failed (exit {done.returncode}):\n{done.stderr[-2000:]}")
    return common.summarize_ticks(json.loads(out.read_text(encoding="utf-8")))


def distinct_sequences(runs: List[Dict[str, Any]]) -> List[List[str]]:
    seen: List[List[str]] = []
    for run in runs:
        if run["runtime_mode_sequence"] not in seen:
            seen.append(run["runtime_mode_sequence"])
    return seen


def render_markdown(result: Dict[str, Any], fields: Dict[str, Any], flag: str, overrides: Dict[str, Any]) -> str:
    out = [common.markdown_header(fields, f"Feature flag attribution: {flag}")]
    out.append(f"- repetitions: {result['repetitions']['off']} off, {result['repetitions']['on']} on (interleaved)")
    out.append(f"- flag as seen inside the runs: {overrides}")
    modes = result.get("modes", {})
    if modes:
        out.append(f"- RuntimeMode sequences seen across repetitions: off {modes.get('off')}, on {modes.get('on')}")
        if any(seq != ["NORMAL"] for seq in modes.get("off", []) + modes.get("on", [])):
            out.append("- WARNING: a run left RuntimeMode NORMAL. Cadence, LOD and scan policy change with the mode, "
                       "so the delta mixes the flag's cost with a mode change.")
    wall = result["tick_wall"]
    out.append("")
    out.append("Share of total delta is each phase's delta divided by the tick wall-time delta; it can be negative "
               "or exceed 100% when other phases move the other way, and sub-phases overlap their parent.")
    out.append("")
    out.append("| Phase | Off mean ms | On mean ms | Delta ms | Share of total delta | Off range ms | On range ms |")
    out.append("|---|---|---|---|---|---|---|")
    if wall:
        out.append(f"| **(tick wall time)** | {wall['off_mean_ms']:.3f} | {wall['on_mean_ms']:.3f} | {wall['delta_ms']:+.3f} | "
                   f"100.0% | {wall['off_spread_ms']['range']:.3f} | {wall['on_spread_ms']['range']:.3f} |")
    for r in result["phases"]:
        if abs(r["delta_ms"]) < 0.0005 and r["off_mean_ms"] < 0.0005 and r["on_mean_ms"] < 0.0005:
            continue
        out.append(f"| {r['phase']} | {r['off_mean_ms']:.3f} | {r['on_mean_ms']:.3f} | {r['delta_ms']:+.3f} | "
                   f"{r['share_of_total_delta'] * 100:.1f}% | {r['off_spread_ms']['range']:.3f} | {r['on_spread_ms']['range']:.3f} |")
    out.append("")
    out.append("## Events (mean per run over the measured ticks)")
    out.append("")
    out.append("| Event type | Off | On |")
    out.append("|---|---|---|")
    types = sorted(set(result["events_off"]) | set(result["events_on"]))
    out.append(f"| **(all)** | {sum(result['events_off'].values()):.1f} | {sum(result['events_on'].values()):.1f} |")
    for t in types:
        out.append(f"| {t} | {result['events_off'].get(t, 0):.1f} | {result['events_on'].get(t, 0):.1f} |")
    return "\n".join(out) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--flag", required=True, help="feature flag name, for example ENABLE_COMBAT_ENGAGEMENT")
    parser.add_argument("--scenario", default="combat", choices=["idle", "movement", "resource", "combat", "strategic",
                                                                  "mixed", "metropolis"])
    parser.add_argument("--entities", type=int, default=100, help="entity count (keep small; this runs the kernel)")
    parser.add_argument("--ticks", type=int, default=15, help="measured ticks per run")
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--reps", type=int, default=3, help="repetitions per state (K)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--profile", choices=common.PROFILE_NAMES, default="PROD_LARGE",
                        help="RuntimeProfile; a larger tick budget keeps the governor in NORMAL longer")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--out-dir", default=None, help=f"also write the result here (default {common.OUT_ROOT}/flag_attribution)")
    args = parser.parse_args(argv)

    if args.scenario == "metropolis":
        print(common.METROPOLIS_WARNING, file=sys.stderr)
    if args.reps < 1:
        parser.error("--reps must be at least 1")

    off_runs: List[Dict[str, Any]] = []
    on_runs: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        try:
            for i in range(args.reps):  # interleaved: off, on, off, on, ...
                off_runs.append(run_once(args, "OFF", work, i))
                on_runs.append(run_once(args, "ON", work, i))
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    result = common.attribute_flag(off_runs, on_runs)
    result["modes"] = {"off": distinct_sequences(off_runs), "on": distinct_sequences(on_runs)}
    overrides = {"off": off_runs[0]["flag_override"], "on": on_runs[0]["flag_override"]}
    fields = common.header_fields(args.scenario, args.entities, args.seed, args.warmup, args.ticks,
                                  extra={"profile": args.profile, "flag": args.flag, "repetitions_per_state": args.reps,
                                        "profiler": "none attached"})
    text = (json.dumps({"header": common.header_lines(fields, f"Feature flag attribution: {args.flag}"),
                        "flag_as_seen": overrides, **result}, indent=2, ensure_ascii=False) + "\n"
            if args.format == "json" else render_markdown(result, fields, args.flag, overrides))
    out_dir = Path(args.out_dir) if args.out_dir else common.OUT_ROOT / "flag_attribution"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{args.flag}_{args.scenario}_{args.entities}_s{args.seed}.{args.format}"
    path.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    print(f"\nwritten: {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
