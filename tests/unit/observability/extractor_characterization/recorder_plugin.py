"""pytest plugin that records what EventExtractor.extract emits, for the characterization tests.

It wraps EventExtractor.extract. For every call a test makes, it evaluates the call once per CONFIG (default flags, each rollback flag off
alone, all four off under two modes), restoring the extractor's run-scoped caches between evaluations, and records the events as canonical
lines. The call the test itself sees is its own, unchanged: the wrapper returns the as-built evaluation, so test assertions are unaffected.

Run it as ``python -m pytest -p tests.unit.observability.extractor_characterization.recorder_plugin <modules>`` with
``EXTRACTOR_RECORD_OUT`` set to the file to write. See test_event_extractor_characterization.py.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from typing import Any

from src.observability.config import ObservabilityMode
from src.observability.divergence_episode import DivergenceEpisodes
from src.observability.event_extractor import EventExtractor

FLAGS = (
    "ENABLE_PUSH_EVENT_SHAPERS",
    "ENABLE_PUSH_EVENT_SHAPERS_PHASE2",
    "ENABLE_PUSH_EVENT_SHAPERS_QUEST",
    "ENABLE_PUSH_EVENT_SHAPERS_AGENCY",
)
# name -> (feature_flags override, or None to leave the state as built; mode override, or None to keep the caller's)
CONFIGS: dict[str, tuple[dict[str, str] | None, ObservabilityMode | None]] = {
    "as_built": (None, None),
    "default_flags": ({}, None),
    **{f"off_{flag}": ({flag: "OFF"}, None) for flag in FLAGS},
    "all_off_light": ({flag: "OFF" for flag in FLAGS}, ObservabilityMode.LIGHT),
    "all_off_normal": ({flag: "OFF" for flag in FLAGS}, ObservabilityMode.NORMAL),
}

_STATE_NAMES = (
    "_seen_routing_families", "_last_xp_tick", "_emitted_plateau", "_emitted_stale_leads", "_emitted_social_memory",
    "_emitted_contract_milestones", "_last_capability_growth_tick", "_emitted_capability_stalled",
)


def snapshot() -> tuple[Any, ...]:
    return tuple(copy.deepcopy(getattr(EventExtractor, name)) for name in _STATE_NAMES) + (copy.deepcopy(DivergenceEpisodes._diverged),)


def restore(snap: tuple[Any, ...]) -> None:
    for name, saved in zip(_STATE_NAMES, snap):
        current = getattr(EventExtractor, name)
        current.clear()
        if isinstance(current, dict):
            current.update(copy.deepcopy(saved))
        else:
            current.update(saved)
    DivergenceEpisodes._diverged.clear()
    DivergenceEpisodes._diverged.update(snap[-1])


_ADDRESS = re.compile(r"(id='\d+'|0x[0-9a-fA-F]+)")


def _plain(value: Any) -> Any:
    """JSON-safe, address-free form of a payload value (a mock or object reprs with its type, never its id)."""
    if isinstance(value, str):
        return _ADDRESS.sub("<addr>", value)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_plain(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, (str, int)) and type(value).__module__ != "unittest.mock":
        return f"{type(value).__name__}.{enum_value}"
    return f"<{type(value).__name__}>"


def canonical(event: Any) -> str:
    """One event as a canonical JSON line. ``timestamp``, ``created_at`` and ``event_id`` are wall-clock or random, so they are left out."""
    data = event.model_dump() if hasattr(event, "model_dump") else dict(vars(event))
    for volatile in ("timestamp", "created_at", "event_id"):
        data.pop(volatile, None)
    return json.dumps(_plain(data), sort_keys=True, separators=(",", ":"))


def _evaluate(original, prior, current, update, mode, flags, mode_override):
    previous = getattr(prior, "feature_flags", None)
    swapped = flags is not None
    if swapped:
        try:
            object.__setattr__(prior, "feature_flags", dict(flags))
        except (AttributeError, TypeError):
            swapped = False
    try:
        return original(prior, current, update, mode_override if mode_override is not None else mode)
    finally:
        if swapped:
            object.__setattr__(prior, "feature_flags", previous)


def digest_row(row: dict[str, Any]) -> dict[str, Any]:
    """The committed form of a row: per config, the event count and a SHA-256 prefix over the ordered canonical lines."""
    return {
        "test": row["test"], "call": row["call"], "mode": row["mode"],
        "results": {name: [len(lines), hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]] for name, lines in sorted(row["results"].items())},
    }


class _Recorder:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.node = ""
        self.call_index = 0

    def pytest_runtest_setup(self, item):
        self.node = item.nodeid
        self.call_index = 0
        EventExtractor.reset_run_state()

    def pytest_runtest_teardown(self, item):
        EventExtractor.reset_run_state()

    def pytest_sessionstart(self, session):
        self._original = EventExtractor.extract
        recorder = self

        def wrapped(prior, current, update, mode=ObservabilityMode.LIGHT):
            snap = snapshot()
            results: dict[str, list[str]] = {}
            for name, (flags, mode_override) in CONFIGS.items():
                if name == "as_built":
                    continue
                restore(snap)
                try:
                    events = _evaluate(recorder._original, prior, current, update, mode, flags, mode_override)
                    results[name] = [canonical(e) for e in events]
                except Exception as exc:  # a config the test's fixture cannot satisfy is part of the pinned behavior
                    results[name] = [f"RAISES {type(exc).__name__}"]
            restore(snap)
            actual = recorder._original(prior, current, update, mode)
            results["as_built"] = [canonical(e) for e in actual]
            recorder.rows.append({"test": recorder.node, "call": recorder.call_index, "mode": str(getattr(mode, "value", mode)), "results": results})
            recorder.call_index += 1
            return actual

        EventExtractor.extract = staticmethod(wrapped)

    def pytest_sessionfinish(self, session):
        EventExtractor.extract = staticmethod(self._original)
        rows = sorted(self.rows, key=lambda r: (r["test"], r["call"]))
        with open(os.environ["EXTRACTOR_RECORD_OUT"], "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(digest_row(row), sort_keys=True, separators=(",", ":")) + "\n")
        full = os.environ.get("EXTRACTOR_RECORD_FULL")
        if full:  # every event line, for diffing two commits; far too large to commit
            with open(full, "w", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def pytest_configure(config):
    config.pluginmanager.register(_Recorder(), "extractor-recorder")
