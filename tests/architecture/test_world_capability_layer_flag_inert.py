"""
Architecture guard for TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION's naming-proximity check.

ENABLE_WORLD_CAPABILITY_LAYER gates nothing today: no WorldCapabilityLayer class or module
exists anywhere in src/ at all (unlike ENABLE_ADVENTURE_ROUTING, which used to gate a real,
now-deleted phase -- see test_adventure_routing_flag_inert.py). The flag's only non-registration
references are a test-scaffold pressure_signals dict entry in src/testing/scenario_runner.py
(maps to nothing, since no phase names this flag in a run_phase(..., feature_flag=...) call)
and calibrate_simq.py's/test_scenario_feature_flag_defaults.py's own known-flag allowlists --
neither is a gating call site.

This test pins that inertness so a future real wiring of ENABLE_WORLD_CAPABILITY_LAYER fails
loudly here, forcing re-examination of this ticket's own "no combination interaction possible
with ENABLE_WORLD_EMERGENCE" resolution instead of the claim silently going stale.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

_LIVE_GATING_PATTERNS = (
    'is_enabled("ENABLE_WORLD_CAPABILITY_LAYER")',
    "is_enabled('ENABLE_WORLD_CAPABILITY_LAYER')",
    'get_flag_mode("ENABLE_WORLD_CAPABILITY_LAYER")',
    "get_flag_mode('ENABLE_WORLD_CAPABILITY_LAYER')",
    'feature_flag="ENABLE_WORLD_CAPABILITY_LAYER"',
    "feature_flag='ENABLE_WORLD_CAPABILITY_LAYER'",
)

# The flag's own registration -- default OFF, not a gating call site.
_EXEMPT_PATH = SRC_ROOT / "domains" / "optimization" / "feature_flags.py"


def test_enable_world_capability_layer_has_no_live_gating_call_site():
    offenders = []
    for path in SRC_ROOT.rglob("*.py"):
        if path == _EXEMPT_PATH:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in _LIVE_GATING_PATTERNS:
            if pattern in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {pattern!r}")

    assert not offenders, (
        "ENABLE_WORLD_CAPABILITY_LAYER has a live gating call site outside "
        "feature_flags.py's own registration -- this reopens the "
        "ENABLE_WORLD_EMERGENCE + ENABLE_WORLD_CAPABILITY_LAYER combination question "
        "(TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION) and requires re-examining this "
        "ticket's own static-inertness resolution:\n" + "\n".join(offenders)
    )
