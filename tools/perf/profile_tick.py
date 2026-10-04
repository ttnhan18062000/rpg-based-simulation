#!/usr/bin/env python3
"""Sampling profile of a named scenario's ticks, with the per-phase tick context beside it.

Builds a scenario from ``src/perf/scenarios.py::SCENARIO_BUILDERS`` at a given entity count and
seed, runs warmup plus N measured ticks in a child process under ``py-spy record`` (the tool
launches the child itself, so no elevated privilege is needed), and writes under ``reports/perf/``:

- ``profile.folded``           folded stacks of the measured ticks only
- ``profile.speedscope.json``  the same samples as a speedscope profile
- ``phases.md`` / ``phases.json``  mean and p95 ms per tick and share of tick per phase, the
  RuntimeMode sequence and the processed-work counters, so a profile is never shown without context

``--memory`` runs the same child under ``memray`` and writes its flame graph instead of sampling.
Every output carries the PROVISIONAL header. This is diagnostic evidence, not a baseline.

    python3 tools/perf/profile_tick.py --scenario mixed --entities 200 --ticks 30

Ticket: TCK-20261003-PERF-PROFILING-TOOLKIT.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.perf import _profiling_common as common  # noqa: E402

SCRIPT = Path(__file__).resolve()
MEASURED_MARKER = "_measured_ticks"
DEFAULT_RATE_HZ = 250


def _scenario_choices() -> List[str]:
    # Static list so --help and the missing-binary path work without importing the engine.
    return ["idle", "movement", "resource", "combat", "strategic", "mixed", "metropolis"]


def child_command(args: argparse.Namespace, out_json: Path) -> List[str]:
    cmd = [sys.executable, str(SCRIPT), "--child", "--scenario", args.scenario, "--entities", str(args.entities),
           "--seed", str(args.seed), "--warmup", str(args.warmup), "--ticks", str(args.ticks),
           "--out-json", str(out_json)]
    cmd += ["--profile", args.profile]
    if args.flag and args.flag_mode:
        cmd += ["--flag", args.flag, "--flag-mode", args.flag_mode]
    return cmd


def render_phase_report(fields, summary, phase_rows, sampling_note: str) -> str:
    out = [common.markdown_header(fields, "Per-phase tick context for a profile")]
    out.append(f"- runtime mode sequence: {' -> '.join(summary['runtime_mode_sequence']) or 'n/a'}")
    work = ", ".join(f"{k}={v:.1f}" for k, v in summary["work_mean_per_tick"].items()) or "n/a"
    out.append(f"- processed work (mean per tick): {work}")
    out.append(f"- events (measured ticks): {sum(summary['events'].values())}")
    out.append(f"- sampling: {sampling_note}")
    if summary["runtime_mode_sequence"] != ["NORMAL"]:
        out.append("- WARNING: the RuntimeMode left NORMAL during the measured ticks. Cadence, LOD and scan policy "
                   "change with the mode, so this profile describes a degraded run, not the NORMAL-mode cost.")
    out.append("")
    out.append("Shares are of the mean tick wall time. Some phases are sub-phases of another, so shares do not sum to 100%.")
    out.append("")
    out.append("| Phase | Mean ms/tick | p95 ms/tick | Share of tick |")
    out.append("|---|---|---|---|")
    wall = summary["tick_wall_ms"]
    out.append(f"| (tick wall time) | {common.mean(wall):.3f} | {common.p95(wall):.3f} | 100.0% |")
    for r in phase_rows:
        out.append(f"| {r['phase']} | {r['mean_ms']:.3f} | {r['p95_ms']:.3f} | {r['share_of_tick'] * 100:.1f}% |")
    return "\n".join(out) + "\n"


def run_child(args: argparse.Namespace) -> int:
    common.load_repo_on_path()
    data = common.run_scenario_ticks(args.scenario, args.entities, args.seed, args.warmup, args.ticks,
                                     flag=args.flag, flag_mode=args.flag_mode, profile_name=args.profile)
    common.write_json(Path(args.out_json), data)
    return 0


def run_parent(args: argparse.Namespace) -> int:
    tool = "memray" if args.memory else "py-spy"
    binary = common.find_binary(tool, args.memray if args.memory else args.py_spy)
    if binary is None:
        print(common.missing_binary_message(tool), file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir) if args.out_dir else common.OUT_ROOT / f"{args.scenario}_{args.entities}_s{args.seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    child_json = out_dir / "child_ticks.json"
    child = child_command(args, child_json)
    fields = common.header_fields(args.scenario, args.entities, args.seed, args.warmup, args.ticks,
                                  extra={"profile": args.profile, "tool": tool,
                                                      "sample_rate_hz": None if args.memory else args.rate})

    if args.memory:
        bin_path = out_dir / "memray.bin"
        run = subprocess.run([binary, "run", "--force", "-o", str(bin_path), *child[1:]],
                             capture_output=True, text=True)
        if run.returncode != 0:
            print(f"memray run failed (exit {run.returncode}):\n{run.stderr[-2000:]}", file=sys.stderr)
            return 1
        html = out_dir / "memray_flamegraph.html"
        flame = subprocess.run([binary, "flamegraph", "--force", "-o", str(html), str(bin_path)],
                               capture_output=True, text=True)
        if flame.returncode != 0:
            print(f"memray flamegraph failed (exit {flame.returncode}):\n{flame.stderr[-2000:]}", file=sys.stderr)
            return 1
        header = common.header_lines(fields, "Memray allocation flame graph")
        common.stamp_html(html, header)
        # The binary capture cannot carry a header, so a sidecar states what it is.
        sidecar = out_dir / "memray.bin.provisional.txt"
        sidecar.write_text(common.comment_header(fields, "Memray capture (binary; read with memray)"), encoding="utf-8")
        sampling_note = "memray allocation tracking (no CPU sampling in this run)"
        written = [str(html), str(bin_path), str(sidecar)]
    else:
        raw = out_dir / "profile.raw.folded"
        run = subprocess.run([binary, "record", "-f", "raw", "-r", str(args.rate), *([] if args.blocking else ["--nonblocking"]),
                              "-o", str(raw), "--", *child],
                             capture_output=True, text=True)
        if not raw.exists() or raw.stat().st_size == 0:
            print(f"py-spy produced no samples (exit {run.returncode}).\nstdout:\n{run.stdout[-1500:]}\n"
                  f"stderr:\n{run.stderr[-1500:]}", file=sys.stderr)
            return 1
        stacks = common.parse_folded(raw.read_text(encoding="utf-8"))
        kept, kept_n, total_n = common.filter_stacks(stacks, MEASURED_MARKER)
        raw.unlink()
        if not kept:
            print("No sampled stack contained the measured-ticks frame; raise --ticks or --rate. "
                  f"Total samples: {total_n}.", file=sys.stderr)
            return 1
        header = common.header_lines(fields, "Folded stacks of the measured ticks (py-spy)")
        folded_path = out_dir / "profile.folded"
        folded_path.write_text(common.comment_header(fields, "Folded stacks of the measured ticks (py-spy)")
                               + common.render_folded(kept), encoding="utf-8")
        ss_path = out_dir / "profile.speedscope.json"
        common.write_json(ss_path, common.folded_to_speedscope(
            kept, f"{args.scenario} {args.entities} entities (PROVISIONAL)", header))
        sampling_note = (f"py-spy at {args.rate} Hz{'' if args.blocking else ' (nonblocking)'}, {kept_n} of "
                         f"{total_n} samples kept (stacks inside `{MEASURED_MARKER}`; setup and warmup dropped). "
                         "The sampler still slows the process, so absolute ms here are inflated; use shares, and "
                         "flag_attribution.py for unprofiled timings")
        written = [str(folded_path), str(ss_path)]

    if not child_json.exists():
        print("The child run wrote no tick data; see the profiler output above.", file=sys.stderr)
        return 1
    summary = common.summarize_ticks(json.loads(child_json.read_text(encoding="utf-8")))
    rows = common.phase_table(summary["per_tick_costs"], summary["tick_wall_ms"])
    md_path, js_path = out_dir / "phases.md", out_dir / "phases.json"
    md_path.write_text(render_phase_report(fields, summary, rows, sampling_note), encoding="utf-8")
    common.write_json(js_path, {"header": list(common.header_lines(fields, "Per-phase tick context")),
                                "summary": summary, "phases": rows})
    child_json.unlink()
    for p in written + [str(md_path), str(js_path)]:
        print(p)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scenario", choices=_scenario_choices(), default="mixed")
    parser.add_argument("--entities", type=int, default=200, help="entity count (keep small; this runs the kernel)")
    parser.add_argument("--ticks", type=int, default=30, help="measured ticks")
    parser.add_argument("--warmup", type=int, default=3, help="warmup ticks before measuring")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--profile", choices=common.PROFILE_NAMES, default="PROD_LARGE",
                        help="RuntimeProfile; a larger tick budget keeps the governor in NORMAL longer")
    parser.add_argument("--rate", type=int, default=DEFAULT_RATE_HZ, help="py-spy sample rate in Hz")
    parser.add_argument("--blocking", action="store_true",
                        help="let py-spy pause the process at every sample (consistent stacks, but in this sandbox it "
                             "slowed a tick roughly eightfold); the default is py-spy --nonblocking")
    parser.add_argument("--memory", action="store_true", help="run under memray instead of sampling with py-spy")
    parser.add_argument("--py-spy", dest="py_spy", default=None, help="path to the py-spy binary")
    parser.add_argument("--memray", default=None, help="path to the memray binary")
    parser.add_argument("--out-dir", default=None, help=f"output directory (default {common.OUT_ROOT}/<scenario>_<n>_s<seed>)")
    parser.add_argument("--flag", default=None, help="force a feature flag for this run only (used by flag_attribution)")
    parser.add_argument("--flag-mode", choices=("ON", "OFF"), default=None)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--out-json", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.child:
        if not args.out_json:
            parser.error("--child requires --out-json")
        return run_child(args)
    return run_parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
