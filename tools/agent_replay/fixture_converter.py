"""Ticket + stored_artifacts -> FixtureEnvelope YAML converter for the filtered replay eval pilot
(TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, Step 2).

Models `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` — the one
existing hand-built example — reading a closed ticket's real permanent files (path references
only, never embedded copies) plus its `agent-monitoring/data/*/events.jsonl` phase records for
Scope/Investigate/Plan/Review. `Review.output.verdict`/`.violations` are reconstructed from
`events.jsonl`'s truncated `summary` field where no fuller record exists (the same disclosed
limitation the hand-built fixture already documents) — every converted fixture records a
`review_output_fidelity` field in the conversion log so this is visible per-fixture, never
smoothed over (investigation.md Risk #5).

A ticket missing `stored_artifacts/{id}/`, `investigation.md`, `plan.md`, or any of the 4
Scope/Investigate/Plan/Review phase events is NOT converted — it is excluded with a specific,
logged reason (Scope item 3), never silently dropped. Every accepted fixture is round-tripped
through the existing, unmodified `fixture_envelope.load_fixture()` before acceptance.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay_codex.monitoring_shards import source_paths  # noqa: E402
from generate_registry import _strip_frontmatter, parse_body_section  # noqa: E402
from validate_frontmatter import extract_frontmatter  # noqa: E402

from .fixture_envelope import FixtureValidationError, load_fixture

_PHASE_ORDER = ("Scope", "Investigate", "Plan", "Review")
_PHASE_AGENTS = {
    "Scope": "ticket-scoper",
    "Investigate": "investigator",
    "Plan": "planner",
    "Review": "architecture-reviewer",
}
_REVIEW_VERDICT_KEYWORDS = (
    "NEEDS_CHANGES",
    "NEEDS_HUMAN_INPUT",
    "CONFLICTS_DETECTED",
    "BLOCKED",
)


@dataclass(frozen=True)
class ConversionResult:
    ticket_id: str
    converted: bool
    fixture_path: str | None
    review_output_fidelity: str | None
    reason: str | None


def _read_events_for_ticket(monitoring_root: Path, ticket_id: str) -> list[dict]:
    """Every `events.jsonl` row across all shards whose `run_id` matches `ticket_id`, sorted by
    `seq` (read-only, never one of the four forbidden scripts)."""
    records: list[dict] = []
    for path in source_paths(monitoring_root, "events.jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("run_id") == ticket_id:
                    records.append(record)
    records.sort(key=lambda r: r.get("seq", 0))
    return records


def _reconstruct_review_verdict(summary: str) -> str:
    """Best-effort reconstruction from a 200-char-capped events.jsonl summary — never a verbatim
    record of the real REVIEW_SCHEMA JSON (see docs/ai/replay_fixture_spec.md)."""
    normalized = (summary or "").strip().upper()
    if normalized.startswith("APPROVED"):
        return "APPROVED"
    for keyword in _REVIEW_VERDICT_KEYWORDS:
        if keyword in normalized:
            return keyword
    return "APPROVED"


def convert_ticket_to_fixture(
    ticket_id: str,
    ticket_path: Path,
    stored_artifacts_dir: Path,
    monitoring_root: Path,
    output_dir: Path,
) -> ConversionResult:
    """Convert one closed ticket into a FixtureEnvelope YAML under `output_dir`, or return a
    `ConversionResult` with `converted=False` and a specific `reason` if it cannot be converted."""
    if not ticket_path.exists():
        return ConversionResult(ticket_id, False, None, None, f"missing ticket file {ticket_path}")

    if not stored_artifacts_dir.is_dir():
        return ConversionResult(
            ticket_id, False, None, None, f"missing stored_artifacts/{ticket_id}/"
        )

    investigation_path = stored_artifacts_dir / "investigation.md"
    plan_path = stored_artifacts_dir / "plan.md"
    if not investigation_path.exists():
        return ConversionResult(
            ticket_id, False, None, None, f"missing stored_artifacts/{ticket_id}/investigation.md"
        )
    if not plan_path.exists():
        return ConversionResult(
            ticket_id, False, None, None, f"missing stored_artifacts/{ticket_id}/plan.md"
        )

    events = _read_events_for_ticket(monitoring_root, ticket_id)
    events_by_phase: dict[str, dict] = {}
    for record in events:
        phase = record.get("phase")
        if phase in _PHASE_ORDER and phase not in events_by_phase:
            events_by_phase[phase] = record

    missing_phases = [p for p in _PHASE_ORDER if p not in events_by_phase]
    if missing_phases:
        return ConversionResult(
            ticket_id,
            False,
            None,
            None,
            f"missing events.jsonl phase record(s) for {missing_phases} — no Scope/Investigate/"
            "Plan/Review phase transitions recorded (common for hotfix-tier tickets, whose "
            "pipeline has no Investigate/Plan/Review phase at all)",
        )

    ticket_text = ticket_path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(ticket_text) or {}
    tags = list(frontmatter.get("tags") or [])
    body = _strip_frontmatter(ticket_text)
    tier = parse_body_section(body, "Tier").strip() or "standard"

    scope_event = events_by_phase["Scope"]
    investigate_event = events_by_phase["Investigate"]
    plan_event = events_by_phase["Plan"]
    review_event = events_by_phase["Review"]

    review_summary = review_event.get("summary", "")
    verdict = _reconstruct_review_verdict(review_summary)
    review_output_fidelity = "reconstructed_from_truncated_summary"

    seqs = [r.get("seq") for r in events_by_phase.values() if r.get("seq") is not None]
    seq_range = [min(seqs), max(seqs)] if seqs else [0, 0]

    fixture_dict = {
        "version": 1,
        "source": {
            "ticket_id": ticket_id,
            "ticket_path": str(ticket_path),
            "stored_artifacts_dir": str(stored_artifacts_dir).rstrip("/") + "/",
            "events_run_id": ticket_id,
            "events_seq_range": seq_range,
            "final_status": "DONE",
            "tier": tier,
        },
        "phases": [
            {
                "phase": "Scope",
                "agent": scope_event.get("agent") or _PHASE_AGENTS["Scope"],
                "input": {"tags": tags, "conflicts": []},
                "output": {
                    "status": scope_event.get("status", "ok"),
                    "summary": scope_event.get("summary", ""),
                    "ts": scope_event.get("ts", ""),
                },
                "transition": "ok",
            },
            {
                "phase": "Investigate",
                "agent": investigate_event.get("agent") or _PHASE_AGENTS["Investigate"],
                "input": {},
                "output": {
                    "status": investigate_event.get("status", "ok"),
                    "summary": investigate_event.get("summary", ""),
                    "ts": investigate_event.get("ts", ""),
                },
                "transition": "ok",
            },
            {
                "phase": "Plan",
                "agent": plan_event.get("agent") or _PHASE_AGENTS["Plan"],
                "input": {"plan_path": str(plan_path)},
                "output": {
                    "status": plan_event.get("status", "ok"),
                    "summary": plan_event.get("summary", ""),
                    "ts": plan_event.get("ts", ""),
                },
                "transition": "ok",
            },
            {
                "phase": "Review",
                "agent": review_event.get("agent") or _PHASE_AGENTS["Review"],
                "input": {
                    "plan_path": str(plan_path),
                    "investigation_path": str(investigation_path),
                },
                "output": {
                    "verdict": verdict,
                    "violations": [],
                    "status": review_event.get("status", "ok"),
                    "summary": review_summary,
                    "ts": review_event.get("ts", ""),
                },
                "transition": verdict,
            },
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = output_dir / f"{ticket_id}.yaml"
    header = (
        f"# Bulk-converted replay fixture for {ticket_id}"
        f" (TCK-20260907-FILTERED-REPLAY-EVAL-PILOT tools/agent_replay/fixture_converter.py).\n"
        f"# Review.output.verdict/.violations RECONSTRUCTED from a truncated events.jsonl summary"
        f" — see docs/ai/replay_fixture_spec.md and this ticket's conversion_log.yaml"
        f" (review_output_fidelity={review_output_fidelity!r}).\n"
    )
    fixture_path.write_text(
        header + yaml.safe_dump(fixture_dict, sort_keys=False), encoding="utf-8"
    )

    try:
        load_fixture(fixture_path)
    except FixtureValidationError as exc:
        fixture_path.unlink(missing_ok=True)
        return ConversionResult(
            ticket_id, False, None, None, f"generated fixture failed load_fixture validation: {exc}"
        )

    return ConversionResult(ticket_id, True, str(fixture_path), review_output_fidelity, None)


def convert_sample(
    ticket_ids: list[str],
    done_dir: Path,
    stored_artifacts_root: Path,
    monitoring_root: Path,
    output_dir: Path,
) -> list[ConversionResult]:
    results = []
    for ticket_id in ticket_ids:
        ticket_path = done_dir / f"{ticket_id}.md"
        stored_artifacts_dir = stored_artifacts_root / ticket_id
        results.append(
            convert_ticket_to_fixture(
                ticket_id, ticket_path, stored_artifacts_dir, monitoring_root, output_dir
            )
        )
    return results


def write_conversion_log(results: list[ConversionResult], output_path: Path) -> Path:
    records = [asdict(r) for r in results]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump({"conversions": records}, sort_keys=False), encoding="utf-8"
    )
    return output_path
