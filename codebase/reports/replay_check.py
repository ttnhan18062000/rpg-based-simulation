#!/usr/bin/env python3
"""`make replay-check` — a one-command reviewer demo of the determinism claim.

Runs the simulation CLI twice with the same seed under the Canonical signal contract
(`RPG_SIGNAL_CONTRACT=canonical`) and compares the two `Final State Hash:` lines. It is a
short-run measurement, not a proof; the guide `docs/guides/reviewer_replay_check.md` says what
it does and does not show, and `docs/engine/deterministic_execution.md` ("What runs today") is
the contract it is read against.

Exit codes: 0 the hashes match, 1 they differ, 2 a run crashed, timed out or printed no hash.
`--live` is opt-in: it repeats the pair on the default LIVE contract, which is expected to
differ today (known gap, #585), and its result never changes the exit code.

Each run writes a `data/runs/<run_id>` directory. The CLI does not print the run id on stdout,
but the id embeds the child process id (`run_<epoch>_<n>_<pid>_<hex>`), so this module removes
exactly the directories whose pid is one of its own children. It never diffs the directory
(other sessions write there at the same time).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

SIGNAL_CONTRACT_ENV = "RPG_SIGNAL_CONTRACT"
CANONICAL_CONTRACT = "canonical"
DEFAULT_SEED = 42
DEFAULT_TICKS = 300
DEFAULT_TIMEOUT_S = 300.0
LIVE_LABEL = "expected to differ today (known gap, #585)"

EXIT_MATCH = 0
EXIT_DIFFER = 1
EXIT_COULD_NOT_RUN = 2

REPO_ROOT = Path(__file__).resolve().parents[2]
_HASH_LINE = re.compile(r"^Final State Hash:[ \t]*(\S+)[ \t]*$", re.MULTILINE)
_RUN_DIR = re.compile(r"^run_\d+_\d+_(\d+)_[0-9a-f]+$")

CommandBuilder = Callable[[int, int], list[str]]


@dataclass(frozen=True)
class RunResult:
    """One CLI run: the parsed hash, or the reason there is none."""

    final_hash: str | None
    error: str | None = None


def default_command(seed: int, ticks: int) -> list[str]:
    """Return the simulation CLI command line for one run."""
    return [
        sys.executable,
        "-m",
        "src",
        "cli",
        "--seed",
        str(seed),
        "--ticks",
        str(ticks),
    ]


def parse_final_hash(output: str) -> str | None:
    """Return the value of the last `Final State Hash:` line in `output`, or None."""
    found = _HASH_LINE.findall(output)
    return found[-1] if found else None


def own_run_dirs(runs_root: Path, pid: int) -> list[Path]:
    """Return the `run_*` directories under `runs_root` created by process `pid`."""
    if not runs_root.is_dir():
        return []
    matches = (_RUN_DIR.match(p.name) for p in runs_root.iterdir() if p.is_dir())
    return [
        runs_root / m.string
        for m in matches
        if m is not None and int(m.group(1)) == pid
    ]


def run_once(
    command: Sequence[str],
    env: dict[str, str],
    repo_root: Path,
    timeout_s: float,
) -> RunResult:
    """Run `command` once from `repo_root`, parse its hash, and remove only its own run dirs."""
    proc = subprocess.Popen(
        list(command),
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        stdout, _ = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        result = RunResult(None, f"timed out after {timeout_s:g}s")
    else:
        final_hash = parse_final_hash(stdout)
        if proc.returncode != 0:
            result = RunResult(final_hash, f"exited with status {proc.returncode}")
        elif final_hash is None:
            result = RunResult(None, "no 'Final State Hash:' line in the output")
        else:
            result = RunResult(final_hash)
    for run_dir in own_run_dirs(repo_root / "data" / "runs", proc.pid):
        shutil.rmtree(run_dir, ignore_errors=True)
    return result


def _run_pair(
    label: str,
    contract_env: str | None,
    args: argparse.Namespace,
    command_builder: CommandBuilder,
    repo_root: Path,
) -> tuple[list[RunResult], str]:
    """Run the CLI twice under one contract and print each hash. Return results and the verdict."""
    env = dict(os.environ)
    env.pop(SIGNAL_CONTRACT_ENV, None)
    if contract_env is not None:
        env[SIGNAL_CONTRACT_ENV] = contract_env
    print(f"{label} (seed={args.seed}, ticks={args.ticks})")
    results: list[RunResult] = []
    for index in (1, 2):
        result = run_once(
            command_builder(args.seed, args.ticks), env, repo_root, args.timeout
        )
        shown = result.final_hash or "(none)"
        suffix = f"  [{result.error}]" if result.error else ""
        print(f"  run {index}: {shown}{suffix}")
        results.append(result)
    if any(r.error or r.final_hash is None for r in results):
        return results, "COULD NOT RUN"
    return results, "MATCH" if results[0].final_hash == results[
        1
    ].final_hash else "DIFFER"


def main(
    argv: Sequence[str] | None = None,
    command_builder: CommandBuilder = default_command,
    repo_root: Path = REPO_ROOT,
) -> int:
    """Run the replay check and return the process exit code."""
    parser = argparse.ArgumentParser(
        prog="python3 -m codebase.reports.replay_check",
        description="Run the same seed twice under the Canonical signal contract and compare the final state hashes.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--ticks", type=int, default=DEFAULT_TICKS)
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help="seconds allowed per run",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="also run the pair on the default LIVE contract (informational; never changes the exit code)",
    )
    args = parser.parse_args(argv)

    _, verdict = _run_pair(
        f"canonical contract ({SIGNAL_CONTRACT_ENV}={CANONICAL_CONTRACT})",
        CANONICAL_CONTRACT,
        args,
        command_builder,
        repo_root,
    )
    print(verdict)
    if args.live:
        print()
        _, live_verdict = _run_pair(
            f"live contract (default, opt-in): {LIVE_LABEL}",
            None,
            args,
            command_builder,
            repo_root,
        )
        print(f"{live_verdict}  [informational, does not change the exit code]")
    return {"MATCH": EXIT_MATCH, "DIFFER": EXIT_DIFFER}.get(verdict, EXIT_COULD_NOT_RUN)


if __name__ == "__main__":
    sys.exit(main())
