"""MCP tool that packages a drawing revision for intake. Importing this module registers it on the shared server.

It is the ONLY link from the drawing tools to the store, and it writes nothing outside the experiment workspace: no adopt,
build, release, revoke or gc tool exists on this server.
"""

from __future__ import annotations

from visual_assets.drawing import handoff
from visual_assets.drawing.server.app import call, mcp


@mcp.tool()
def export_handoff(
    name: str,
    revision: str,
    licence_state: str = "UNREVIEWED",
    licence_evidence_ref: str = "UNAVAILABLE",
    brief_id: str = "UNAVAILABLE",
    review_evidence_ref: str = "NOT_APPLICABLE",
    limitations: list[str] | None = None,
) -> dict:
    """Package one exact revision (r0001 style, required) as a candidate handoff directory in the experiment workspace:
    package.json, the source's exact bytes and a preview. It is a candidate, NOT an adoption: a human decides later.
    licence_state: UNREVIEWED|CLEARED|RESTRICTED|WITHDRAWN. The *_ref values are short text or UNAVAILABLE/NOT_APPLICABLE."""
    return call(
        handoff.build_handoff, name, revision, licence_state=licence_state, licence_evidence_ref=licence_evidence_ref,
        brief_id=brief_id, review_evidence_ref=review_evidence_ref, limitations=limitations,
    )
