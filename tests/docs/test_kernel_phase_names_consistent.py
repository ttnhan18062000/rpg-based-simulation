from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent.parent
# "GOVERNANCE" is checked case-sensitive only: a case-insensitive check would false-
# positive on legitimate uses (docs/engine/contracts/governance_logic.md's citations,
# architecture.md's own "Phase Governance" section heading). This safely catches
# architecture.md's ALL-CAPS table entry today. "PACKETIZATION" has no legitimate use
# in any casing, so it's checked case-insensitively to also catch the Title-Case
# "Packetization" occurrences in README.md/CLAUDE.md/docs/guides/simulation.md that a
# case-sensitive-only check would miss (found during Review — see architecture-reviewer
# note on TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT's Review phase).
FORBIDDEN_PHASE_NAME_GOVERNANCE = "GOVERNANCE"  # case-sensitive
FORBIDDEN_PHASE_NAME_PACKETIZATION = "packetization"  # checked case-insensitively
REAL_PHASES = ("INIT", "SCHEDULING", "COLLECTION", "RESOLUTION", "CLEANUP",
               "ADVANCEMENT", "PERSISTENCE")

PHASE_NARRATING_DOCS = [
    "docs/engine/kernel.md",
    "docs/engine/architecture.md",
    "docs/engine/README.md",
    "docs/engine/contracts/simulation_kernel_contract.md",
    "docs/guides/simulation.md",
    "CLAUDE.md",
]

@pytest.mark.xfail(
    strict=True,
    reason=(
        "architecture.md still narrates a fabricated 6-phase GOVERNANCE/PACKETIZATION "
        "loop pending TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION (OPEN); remove this "
        "marker once that ticket and TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION "
        "(OPEN) both land and this test passes for real."
    ),
)
def test_no_fabricated_phase_names_in_kernel_docs():
    """GOVERNANCE and PACKETIZATION are not real _phase_* methods in src/engine/kernel.py.
    This exact fabricated pair independently drifted into architecture.md, README.md,
    CLAUDE.md, and docs/guides/simulation.md after being fixed once in kernel.md
    (TCK-20260619-P0-DOC-REPAIR) — TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT."""
    for rel_path in PHASE_NARRATING_DOCS:
        text = (ROOT / rel_path).read_text()
        assert FORBIDDEN_PHASE_NAME_GOVERNANCE not in text, (
            f"{rel_path} contains fabricated phase name {FORBIDDEN_PHASE_NAME_GOVERNANCE!r}"
        )
        assert FORBIDDEN_PHASE_NAME_PACKETIZATION not in text.lower(), (
            f"{rel_path} contains fabricated phase name 'packetization' (any casing)"
        )

def test_kernel_doc_states_all_seven_real_phases():
    """The canonical doc (kernel.md) must name all 7 real phases — guards against a future
    partial/stale rewrite in the other direction."""
    text = (ROOT / "docs/engine/kernel.md").read_text()
    for phase in REAL_PHASES:
        assert phase in text, f"kernel.md missing real phase name {phase!r}"
