"""The only place that names the agent-working roots.

TCK-20261003-AGENT-WORKING-ROOT-MOVE: ``tickets/``, ``stored_artifacts/``, ``staging_artifacts/``,
``agent-monitoring/``, ``agent-orchestration/``, ``pilot_requests/`` and ``reviews/`` (plus three generated
index folders) are being moved under one ``agent-working/`` root. Live code never spells these names; it
imports the constants below and joins them onto a repository root::

    from tools.agent_working_paths import TICKETS
    done_dir = repo_root / TICKETS / "done"

Every constant is a *relative* ``Path`` (relative to the repository root). ``tools/agent-monitoring/`` (the
tool scripts) is a different folder from ``AGENT_MONITORING`` (the data) and is not covered here.

Prefix-only layout: each moved path is its old path with ``AGENT_WORKING_ROOT`` in front. Before the move
(history, older commits) ``AGENT_WORKING_ROOT`` was ``.`` and every constant equalled its old value.

Closed history is frozen and keeps citing pre-move paths; ``resolve_legacy_citation`` maps such a citation to
the live location.
"""

from __future__ import annotations

from pathlib import Path

#: Folder that holds all agent-working state (``Path(".")`` before the move).
AGENT_WORKING_ROOT = Path("agent-working")

TICKETS = AGENT_WORKING_ROOT / "tickets"
STORED_ARTIFACTS = AGENT_WORKING_ROOT / "stored_artifacts"
STAGING_ARTIFACTS = AGENT_WORKING_ROOT / "staging_artifacts"
AGENT_MONITORING = AGENT_WORKING_ROOT / "agent-monitoring"
AGENT_ORCHESTRATION = AGENT_WORKING_ROOT / "agent-orchestration"
PILOT_REQUESTS = AGENT_WORKING_ROOT / "pilot_requests"
REVIEWS = AGENT_WORKING_ROOT / "reviews"

#: Generated, untracked index folders.
INDEX_ROOT = AGENT_WORKING_ROOT / ".index"
AGENT_MONITORING_INDEX = INDEX_ROOT / "agent-monitoring-index"
KNOWLEDGE_INDEX = INDEX_ROOT / "knowledge-index"
PARITY_INDEX = INDEX_ROOT / "parity-index"

#: Pre-move names of the seven moved roots, for citation resolution and the guard test only.
LEGACY_ROOT_NAMES = (
    "tickets",
    "stored_artifacts",
    "staging_artifacts",
    "agent-monitoring",
    "agent-orchestration",
    "pilot_requests",
    "reviews",
)

#: Pre-move names of the generated index folders.
LEGACY_INDEX_NAMES = ("agent-monitoring-index", "knowledge-index", "parity-index")


def posix(path: Path) -> str:
    """Forward-slash form of a relative constant, for building glob patterns and message text."""
    return path.as_posix()


def resolve_legacy_citation(citation: str) -> str:
    """Map a pre-move citation (``tickets/done/X.md``) to its live path.

    A citation that does not start with a legacy root, or that already carries the new prefix, is
    returned unchanged. Pure string mapping; it does not touch the filesystem.
    """
    text = citation.removeprefix("./")
    prefix = posix(AGENT_WORKING_ROOT)
    if prefix != "." and (text == prefix or text.startswith(prefix + "/")):
        return citation
    head = text.split("/", 1)[0]
    if head in LEGACY_ROOT_NAMES:
        return posix(AGENT_WORKING_ROOT / text)
    if head in LEGACY_INDEX_NAMES:
        return posix(INDEX_ROOT / text)
    return citation
