"""Stratified sample manifest builder for the filtered replay eval pilot
(TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, Step 1).

Selects 20-40 tickets from `tickets/done/*.md` (top-level `TCK-*.md` files only, excluding
tracking subfolders), stratified by `## Tier` (hotfix/standard/epic), frontmatter `layer:`, and
a success/failure outcome derived from `agent-monitoring/data/*/runs.jsonl`'s `final_status`
field. Splits the selection into dev/validation/holdout (~60/20/20) and persists the result as a
real, re-loadable YAML file — never held only as a local variable, per this ticket's Scope item 1.

Reads `agent-monitoring/data/*/runs.jsonl` via
`tools/agent_replay_codex/monitoring_shards.py::source_paths()` (sharding-aware, matches the real
`agent-monitoring/data/<week>/<source>.jsonl` layout including the `unknown-week` fallback
bucket) — never the four forbidden `tools/agent-monitoring/` scripts named in
`docs/ai/replay_fixture_spec.md`'s unconditional containment law.

All counts are re-derived live at call time, never hardcoded — the corpus grows between sessions
(see this ticket's own investigation.md Current Behavior §6).
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay_codex.monitoring_shards import source_paths  # noqa: E402
from generate_registry import _strip_frontmatter, parse_body_section  # noqa: E402
from validate_frontmatter import extract_frontmatter  # noqa: E402

_GATE_FAILURE_STATUSES = frozenset(
    {
        "DOD_BLOCKED",
        "NEEDS_HUMAN_INPUT",
        "NEEDS_CHANGES",
        "CONFLICTS_DETECTED",
        "TESTS_FAILED",
        "TAGS_NOT_REGISTERED",
        "DOC_STALENESS_BLOCKED",
        "GATE_FAIL",
        "PARITY_INCOMPLETE",
        "ANCHORS_STILL_FAILING",
    }
)

_DEFAULT_SEED = 20260907
_SPLIT_RATIOS = {"dev": 0.6, "validation": 0.2, "holdout": 0.2}


@dataclass(frozen=True)
class SampledTicket:
    ticket_id: str
    tier: str
    layer: str
    outcome_stratum: str
    split: str


@dataclass(frozen=True)
class SampleManifest:
    generated_at: str
    corpus_size: int
    tier_breakdown: dict = field(default_factory=dict)
    sample_size: int = 0
    tickets: list = field(default_factory=list)  # list[SampledTicket]


def enumerate_done_tickets(done_dir: Path) -> list[Path]:
    """Top-level `TCK-*.md` files directly under `done_dir` — excludes tracking subfolders
    (e.g. `tickets/done/m1-quick-wins/`), matching investigation.md Current Behavior §6's
    methodology."""
    return sorted(p for p in done_dir.glob("TCK-*.md") if p.is_file())


def _read_tier_layer(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(text) or {}
    layer = str(frontmatter.get("layer") or "misc")
    body = _strip_frontmatter(text)
    tier = parse_body_section(body, "Tier").strip() or "unlabeled"
    return tier, layer


def _load_run_outcomes(monitoring_root: Path) -> dict:
    """`{run_id: final_status}` read across every `runs.jsonl` shard (read-only)."""
    outcomes: dict[str, str] = {}
    for path in source_paths(monitoring_root, "runs.jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                run_id = record.get("run_id")
                final_status = record.get("final_status")
                if run_id and final_status:
                    outcomes[run_id] = final_status
    return outcomes


def _outcome_stratum(ticket_id: str, outcomes: dict) -> str:
    status = outcomes.get(ticket_id)
    if status is None:
        return "unknown"
    return "failure" if status in _GATE_FAILURE_STATUSES else "success"


def build_sample_manifest(
    done_dir: Path,
    monitoring_root: Path,
    sample_size_range: tuple[int, int] = (20, 40),
    seed: int = _DEFAULT_SEED,
) -> SampleManifest:
    """Build a stratified sample manifest. `sample_size_range` is a hard bound — the returned
    manifest's `sample_size` is always within `[sample_size_range[0], sample_size_range[1]]`
    whenever the corpus has at least `sample_size_range[0]` tickets, per the Scope Guards' "hard-
    bound to the 20-40 range" requirement."""
    min_size, max_size = sample_size_range
    ticket_paths = enumerate_done_tickets(done_dir)
    outcomes = _load_run_outcomes(monitoring_root)
    rng = random.Random(seed)

    strata: dict[tuple, list[str]] = {}
    tier_breakdown: dict[str, int] = {}
    for path in ticket_paths:
        ticket_id = path.stem
        tier, layer = _read_tier_layer(path)
        outcome = _outcome_stratum(ticket_id, outcomes)
        tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1
        strata.setdefault((tier, layer, outcome), []).append(ticket_id)

    total_tickets = len(ticket_paths)
    target = (min_size + max_size) // 2

    picked: list[tuple[str, tuple]] = []
    for key in sorted(strata.keys()):
        cell = strata[key]
        proportion = len(cell) / total_tickets if total_tickets else 0
        n = min(len(cell), max(0, round(proportion * target)))
        chosen = sorted(rng.sample(cell, n)) if 0 < n < len(cell) else (sorted(cell) if n >= len(cell) else [])
        for ticket_id in chosen:
            picked.append((ticket_id, key))

    if len(picked) > max_size:
        picked = sorted(rng.sample(picked, max_size))
    elif len(picked) < min_size and total_tickets:
        used = {ticket_id for ticket_id, _ in picked}
        pool = [(tid, key) for key, cell in strata.items() for tid in cell if tid not in used]
        rng.shuffle(pool)
        for ticket_id, key in pool:
            if len(picked) >= min_size:
                break
            picked.append((ticket_id, key))
        picked.sort()

    picked.sort(key=lambda pair: pair[0])

    n = len(picked)
    dev_count = round(n * _SPLIT_RATIOS["dev"])
    validation_count = round(n * _SPLIT_RATIOS["validation"])
    holdout_count = n - dev_count - validation_count
    splits = ["dev"] * dev_count + ["validation"] * validation_count + ["holdout"] * holdout_count
    rng.shuffle(splits)

    tickets = [
        SampledTicket(ticket_id=tid, tier=key[0], layer=key[1], outcome_stratum=key[2], split=split)
        for (tid, key), split in zip(picked, splits)
    ]

    return SampleManifest(
        generated_at=datetime.now(timezone.utc).isoformat(),
        corpus_size=total_tickets,
        tier_breakdown=tier_breakdown,
        sample_size=len(tickets),
        tickets=tickets,
    )


def manifest_to_dict(manifest: SampleManifest) -> dict:
    return {
        "generated_at": manifest.generated_at,
        "corpus_size": manifest.corpus_size,
        "tier_breakdown": manifest.tier_breakdown,
        "sample_size": manifest.sample_size,
        "tickets": [asdict(t) for t in manifest.tickets],
    }


def write_manifest(manifest: SampleManifest, output_path: Path) -> Path:
    """Persists `manifest` to a real file on disk — the durable artifact Scope item 1 requires."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(manifest_to_dict(manifest), sort_keys=False), encoding="utf-8"
    )
    return output_path


def load_manifest(path: Path) -> SampleManifest:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    tickets = [SampledTicket(**t) for t in raw.get("tickets", [])]
    return SampleManifest(
        generated_at=raw["generated_at"],
        corpus_size=raw["corpus_size"],
        tier_breakdown=raw.get("tier_breakdown", {}),
        sample_size=raw["sample_size"],
        tickets=tickets,
    )
