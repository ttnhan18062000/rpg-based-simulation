"""The testing half of running paired arms on GitHub-hosted runners (``.github/workflows/paired-arms.yml``).

TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (T2 of ``docs/plans/architecture/faster_feature_testing_draft_tickets.md``). ``tools/rpg_measure/paired.py`` is rpg's and is not
changed here. This module only (a) plans the (world, seed) matrix, (b) runs ONE arm of one (world, seed) through paired's own ``prepare_tree`` / ``result_path`` /
``run_one`` (so the unchanged ``arm_child.py``, ``PYTHONHASHSEED=0`` and the cache key ``<sha12>-<child hash>-<ticks>`` are paired's, never copied), recording the
arm's wall time and peak RSS, (c) records the runner identity beside every result, and (d) assembles the downloaded artifacts into one paired cache directory, refusing to
mix runners that differ in Python version or OS. paired.py's collected-results option (rpg's) then does the comparison.

Layout of one job's artifact (``paired-arms-<step>-<world>-s<seed>[-self]``), the paired cache layout plus one testing file beside each result (the contract rpg-planner
fixed on 2026-10-26 for ``paired.py --collected``)::

    results/<sha12>-<child hash8>-<ticks>[-repeat]/<world>_<seed>.json         paired's own arm document
    results/<sha12>-<child hash8>-<ticks>[-repeat]/<world>_<seed>.cost.json    {"wall_seconds", "peak_rss_mb" | null, "runner": {name, image, cpu_model, nproc, mem_total_mb, python, os}}

``<child hash8>`` is the hash of ``arm_child.py`` in the TOOL checkout that runs paired (the dispatched ref), not of the base or new tree, so every matrix job and
the aggregate job check out the same ref. A ``pair`` job runs the base and the new arm; a ``self`` job (a ``-self`` artifact) runs the base arm and then its ``-repeat``.

Identity rule (PERF-D2 / DET-PORT-0): the base and new arms of one (world, seed) come from the same job, and the assembled set is refused when its jobs differ in
Python version or OS. An off-host result is never compared with a local one except in the ticket's one-time byte-equality proof.

CLI::

    python -m tools.test_architecture.paired_arms plan --worlds a,b --seeds 42,43 --self-check seed42|full|off      # matrix JSON for GITHUB_OUTPUT
    python -m tools.test_architecture.paired_arms run-arm --repo . --sha SHA --arm base|new|self --world W --seed S --ticks T --cache DIR [--repeat]
    python -m tools.test_architecture.paired_arms assemble --in DIR --out DIR --base SHA40 --new SHA40               # exit 2 and the refusal on stderr
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import resource
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

IDENTITY_FIELDS = ("name", "image", "cpu_model", "nproc", "mem_total_mb", "python", "os")
COMPARED_ACROSS_JOBS = ("python", "os")  # an assembled set whose jobs differ in these is not compared
COMPARED_WITHIN_KEY = ("python", "os", "image")  # the arms of one (world, seed) must agree on these (paired.py refuses too)
WORLDS = ("frontier_living_world", "urban_political", "crowded_frontier")  # = tools.rpg_measure.paired.WORLDS; a test pins the equality
TERRAIN_WORLD = "highland_traverse"
SELF_CHECKS = ("seed42", "full", "off")
KINDS = ("pair", "self")
ARMS = ("base", "new", "self")
_NAME = re.compile(r"^[A-Za-z0-9_]+$")
SELF_CHECK_SEED = 42
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class ArmsRefused(ValueError):
    """The planned or assembled set cannot be compared; the message says why."""


def _csv(value: str, what: str) -> List[str]:
    items = [part.strip() for part in value.split(",") if part.strip()]
    if not items:
        raise ArmsRefused(f"{what}: at least one value is required")
    return items


def step_slug(step: str) -> str:
    """The step label made safe for an artifact name (letters, digits, ``.``, ``_``, ``-``); never empty."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", step).strip("-")
    return slug or "step"


def plan_matrix(worlds: str, seeds: str, self_check: str) -> Dict[str, Any]:
    """``{"include": [...], "terrain": bool}``: a ``pair`` entry per (world, seed), plus ``self`` entries (the base arm and its repeat, on one runner) per ``self_check``:
    seed 42 of every world for ``seed42`` (as ``paired.py`` expects, whatever ``seeds`` holds), every (world, seed) for ``full``.

    ``paired.py`` derives its worlds from its own constants (``WORLDS``, plus the terrain world with ``--terrain``), so ``worlds`` must be exactly that set."""
    if self_check not in SELF_CHECKS:
        raise ArmsRefused(f"self_check must be one of {SELF_CHECKS}, got {self_check!r}")
    world_list = _csv(worlds, "worlds")
    bad = [w for w in world_list if not _NAME.match(w)]
    if bad:
        raise ArmsRefused(f"worlds: not a world name (letters, digits, underscore): {bad}")
    if set(world_list) not in (set(WORLDS), set(WORLDS) | {TERRAIN_WORLD}) or len(set(world_list)) != len(world_list):
        raise ArmsRefused(f"worlds must be exactly paired.py's {list(WORLDS)}, optionally plus {TERRAIN_WORLD!r} (its --terrain), got {world_list}")
    try:
        seed_list = [int(x) for x in _csv(seeds, "seeds")]
    except ValueError:
        raise ArmsRefused(f"seeds: not integers: {seeds!r}") from None
    include = [{"world": w, "seed": x, "kind": "pair"} for w in world_list for x in seed_list]
    if self_check == "full":
        include += [{"world": w, "seed": x, "kind": "self"} for w in world_list for x in seed_list]
    elif self_check == "seed42":
        include += [{"world": w, "seed": SELF_CHECK_SEED, "kind": "self"} for w in world_list]
    return {"include": include, "terrain": TERRAIN_WORLD in world_list}


def _read_os_release() -> str:
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return platform.platform()


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def _mem_total_mb() -> Optional[int]:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def runner_identity(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    """A description of the runner, written beside every result. It describes the machine; it does not pin one (the CPU model varies between runners)."""
    env = os.environ if env is None else env
    image = "-".join(part for part in (env.get("ImageOS"), env.get("ImageVersion")) if part)
    return {
        "name": env.get("RUNNER_NAME") or "unknown",
        "image": image or "unknown",
        "cpu_model": _cpu_model(),
        "nproc": os.cpu_count() or 1,
        "mem_total_mb": _mem_total_mb(),
        "python": platform.python_version(),
        "os": _read_os_release(),
    }


def run_arm(repo: Path, sha: str, arm: str, world: str, seed: int, ticks: int, cache: Path, *, repeat: bool = False) -> Dict[str, Any]:
    """Run (or find in the cache) one arm of one (world, seed) through paired's own functions; write ``<world>_<seed>.cost.json`` beside the document and return it.
    ``arm`` only labels the console line and is validated; the cost file holds what ``paired.py --collected`` reads."""
    if arm not in ARMS:
        raise ArmsRefused(f"arm must be one of {ARMS}, got {arm!r}")
    from tools.rpg_measure import paired  # rpg's module, imported (never copied) so the cache key and the child call are paired's

    full_sha, tree = paired.prepare_tree(repo, sha, cache)
    out = paired.result_path(cache, full_sha, ticks, world, seed, repeat)
    out.parent.mkdir(parents=True, exist_ok=True)
    cached = out.exists() and not repeat  # a cached arm costs nothing here; its cost file is still written so the result has an identity
    wall = 0.0
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    if not cached:
        if out.exists():
            out.unlink()
        started = time.monotonic()
        paired.run_one(tree, world, seed, ticks, out)
        wall = time.monotonic() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss  # KiB on Linux; the largest child so far in THIS process, which runs one arm
    cost = {"wall_seconds": round(wall, 3), "peak_rss_mb": None if cached or after <= 0 else round(max(after, before) / 1024, 1), "runner": runner_identity()}
    out.with_name(out.name[: -len(".json")] + ".cost.json").write_text(json.dumps(cost, sort_keys=True) + "\n", encoding="utf-8")
    return cost


def _check_sha(name: str, value: str) -> str:
    if not _SHA40.match(value):
        raise ArmsRefused(f"{name} must be a full 40-character lowercase hex commit sha, got {value!r}")
    return value


def assemble(src: Path, out: Path, *, base: str, new: str) -> Dict[str, Any]:
    """Merge the downloaded job artifacts under ``src`` (one directory each) into one paired cache directory ``out``; refuse mixed runners or missing arms.

    Refuses when a result has no ``cost.json`` with a full ``runner`` record; when the jobs differ in Python version or OS; when the arms of one (world, seed)
    differ in Python version, OS or image; when two jobs wrote the same file with different bytes (for a self-check job that is the base arm not reproducing);
    or when a ``pair`` job (a directory without the ``-self`` suffix) lacks either the base or the new arm of its (world, seed) from that same job.
    Returns ``{"jobs": {name: [runner...]}, "arms": [cost...]}`` and writes it to ``out/identities.json``."""
    base12, new12 = _check_sha("--base", base)[:12], _check_sha("--new", new)[:12]
    jobs = sorted(p for p in Path(src).iterdir() if p.is_dir())
    if not jobs:
        raise ArmsRefused(f"{src}: no job artifacts to assemble")
    runners: Dict[str, Dict[str, Any]] = {}  # job -> its (first) runner record
    by_key: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}  # "<world>_<seed>" -> [(result dir, runner)]
    arms: List[Dict[str, Any]] = []
    for job in jobs:
        have_in_job: Dict[str, set] = {}  # stem -> {sha12 of the non-repeat dirs}
        for cost_path in sorted(job.glob("results/*/*.cost.json")):
            try:
                cost = json.loads(cost_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise ArmsRefused(f"{job.name}/{cost_path.relative_to(job)}: unreadable ({exc.__class__.__name__})") from None
            runner = cost.get("runner")
            missing = [f for f in IDENTITY_FIELDS if not isinstance(runner, dict) or f not in runner]
            if missing:
                raise ArmsRefused(f"{job.name}/{cost_path.relative_to(job)}: no runner record with {missing}; every result carries its runner identity")
            stem = cost_path.name[: -len(".cost.json")]
            directory = cost_path.parent.name
            runners.setdefault(job.name, runner)
            by_key.setdefault(stem, []).append((f"{job.name}:{directory}", runner))
            if not directory.endswith("-repeat"):
                have_in_job.setdefault(stem, set()).add(directory[:12])
            arms.append({"job": job.name, "result": f"{directory}/{stem}", **cost})
        if not job.name.endswith("-self") and not any({base12, new12} <= shas for shas in have_in_job.values()):
            raise ArmsRefused(f"{job.name}: a pair job needs both the base ({base12}) and the new ({new12}) arm of its (world, seed) from that same job, found {sorted(have_in_job)}")
    if not runners:
        raise ArmsRefused(f"{src}: no result carries a cost.json")
    for field in COMPARED_ACROSS_JOBS:
        values: Dict[str, List[str]] = {}
        for name, runner in runners.items():
            values.setdefault(str(runner[field]), []).append(name)
        if len(values) > 1:
            detail = "; ".join(f"{value!r}: {', '.join(names)}" for value, names in sorted(values.items()))
            raise ArmsRefused(f"the jobs ran on different {field} values ({detail}); arms from runners that differ in Python version or OS are not compared")
    for stem, entries in sorted(by_key.items()):
        for field in COMPARED_WITHIN_KEY:
            if len({str(r[field]) for _d, r in entries}) > 1:
                raise ArmsRefused(f"{stem}: its arms ran on different {field} values ({'; '.join(f'{d}: {r[field]!r}' for d, r in entries)})")
    for job in jobs:
        for path in sorted(job.glob("results/*/*")):
            target = Path(out) / path.relative_to(job)
            if target.exists() and not path.name.endswith(".cost.json") and target.read_bytes() != path.read_bytes():
                raise ArmsRefused(f"{path.relative_to(job)}: two jobs wrote different bytes to the same result file (a self-check arm that does not reproduce?)")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not (target.exists() and path.name.endswith(".cost.json")):  # the first cost file of a shared result stays; a later job's identical result adds none
                shutil.copyfile(path, target)
    Path(out).mkdir(parents=True, exist_ok=True)
    summary = {"jobs": runners, "arms": arms}
    (Path(out) / "identities.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--worlds", required=True)
    plan.add_argument("--seeds", required=True)
    plan.add_argument("--self-check", default="seed42")
    plan.add_argument("--step", default="step", help="the step label; printed as an artifact-safe slug")
    arm = sub.add_parser("run-arm")
    arm.add_argument("--repo", type=Path, default=Path("."))
    arm.add_argument("--sha", required=True)
    arm.add_argument("--arm", required=True)
    arm.add_argument("--world", required=True)
    arm.add_argument("--seed", type=int, required=True)
    arm.add_argument("--ticks", type=int, required=True)
    arm.add_argument("--cache", type=Path, required=True)
    arm.add_argument("--repeat", action="store_true")
    asm = sub.add_parser("assemble")
    asm.add_argument("--in", dest="src", type=Path, required=True)
    asm.add_argument("--out", type=Path, required=True)
    asm.add_argument("--base", required=True, help="the full 40-hex base sha")
    asm.add_argument("--new", required=True, help="the full 40-hex new sha")
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            planned = plan_matrix(args.worlds, args.seeds, args.self_check)
            print("matrix=" + json.dumps({"include": planned["include"]}, separators=(",", ":")))
            print("terrain=" + ("true" if planned["terrain"] else "false"))
            print("slug=" + step_slug(args.step))
        elif args.command == "run-arm":
            cost = run_arm(args.repo, args.sha, args.arm, args.world, args.seed, args.ticks, args.cache, repeat=args.repeat)
            print(f"{args.arm} {args.world} seed {args.seed}: {'cached' if cost['cached'] else str(cost['wall_seconds']) + 's'}")
        else:
            summary = assemble(args.src, args.out, base=args.base, new=args.new)
            print(f"assembled {len(summary['jobs'])} job(s), {len(summary['arms'])} arm run(s) into {args.out}")
    except ArmsRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
