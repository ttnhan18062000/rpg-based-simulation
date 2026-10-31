"""The active-writer slot module must not pull in the cognition package (OFF-mode import isolation)."""
import subprocess
import sys

_PROBE = (
    "import sys\n"
    "import src.observability.active_decision_trace as m\n"
    "import src.ai.goals.adventure_scorer\n"
    "bad = sorted(n for n in sys.modules if n.startswith('src.observability.cognition') or n == 'src.observability.queue')\n"
    "print(','.join(bad))\n"
)


def test_slot_module_and_scorer_import_no_cognition_or_queue_modules():
    out = subprocess.run([sys.executable, "-c", _PROBE], capture_output=True, text=True, check=True).stdout.strip()
    assert out == "", f"loaded: {out}"


def test_writer_module_reexports_the_same_slot():
    from src.observability import active_decision_trace as slot
    from src.observability.cognition import decision_trace_writer as w

    assert w.get_active_writer is slot.get_active_writer
    assert w.set_active_writer is slot.set_active_writer
