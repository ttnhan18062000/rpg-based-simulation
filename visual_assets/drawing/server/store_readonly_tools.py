"""Read-only MCP tools onto the asset store, plus `submit_candidate`. Importing this module registers them on the shared server.

Every result names the store root it used (`store_root`: checkout name, branch, whether it is a linked worktree and whether it came from `VISUAL_ASSETS_CHECKOUT`), so a wrong root is visible.

An agent can hand a candidate to intake and look at the store. It cannot adopt, revoke, build, release, delete or activate anything: those are human decisions
(or later steps) with no tool here, and the boundary test lets this server import only the store layers listed in `SERVER_STORE_ALLOWED`. The only thing
`submit_candidate` writes is the gitignored quarantine; `store_list` and `store_show` write nothing and return shaped summaries, never raw files or absolute paths.
"""

from __future__ import annotations

from datetime import datetime, timezone

from visual_assets.drawing import handoff
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.server.app import mcp
from visual_assets.store import config as store_config
from visual_assets.store import intake as intake_api
from visual_assets.store import readmodel
from visual_assets.store import lock as store_lock
from visual_assets.store.errors import StoreError


def _now() -> str:
    """This entry point (like the CLI) reads the clock; the store library never does."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe(fn, *args, **kwargs):
    """Run a store or drawing function, turning a coded refusal into a tool error carrying its (path-free) message."""
    try:
        return fn(*args, **kwargs)
    except (AdapterError, StoreError) as exc:
        raise ValueError(str(exc)) from None


def _submit(handoff_id: str) -> dict:
    directory = handoff.handoff_directory(handoff_id)
    created_at = _now()
    with store_lock.store_write_lock("submit candidate", started_at=created_at):  # ADR D24: intake writes the quarantine
        result = intake_api.intake(directory, created_at=created_at)
    return {
        "handoff_id": handoff_id,
        "intake_id": result.intake_id,
        "candidate_id": result.candidate_id,
        "verdict": result.verdict.value,
        "findings": [{"code": f.code.value, "detail": f.detail} for f in result.findings],
        "store_root": store_config.describe_root(),
        "note": "Staged in the local quarantine only. A PASSED candidate still needs a human to review and adopt it; no tool here can.",
    }


@mcp.tool()
def submit_candidate(handoff_id: str) -> dict:
    """Run store intake on a handoff written by `export_handoff` (give its handoff_id, not a path and not the candidate id). Returns the verdict and findings.
    Writes only the local quarantine. It is NOT an adoption: a human decides later."""
    return _safe(_submit, handoff_id)


@mcp.tool()
def store_list(kind: str, limit: int = readmodel.DEFAULT_LIMIT) -> dict:
    """Bounded listing, read-only. kind: intake | source | artifact | release (release candidates only; nothing is active). limit 1-200."""
    return {**_safe(readmodel.list_items, kind, limit), "store_root": store_config.describe_root()}


@mcp.tool()
def store_show(kind: str, id: str) -> dict:
    """One record as a shaped summary, read-only. kind/id: intake `in-...`; source `<source_asset_id>/<rNNNN>`; artifact `<artifact_id>`;
    release `<catalog_id>/<rc-NNNN>`. Statements by a producer are labelled as claims."""
    return {**_safe(readmodel.show_item, kind, id), "store_root": store_config.describe_root()}
