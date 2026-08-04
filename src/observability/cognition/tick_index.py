"""
src/observability/cognition/tick_index.py
───────────────────────────────────────────────────────────────────────────────
Decision Trace Tick-Index Sidecar — Epic 2.2B.

Maintains a `decision_trace_index.json` sidecar alongside `decision_trace.jsonl`
mapping tick → first byte offset for that tick. Enables O(1) random-access reads
by tick without scanning the full JSONL file.

Lifecycle:
- `append_entry()` is called from `DecisionTraceWriter`'s async drain worker
  callback (`_write_entry_to_file`), once per queued entry actually written to
  decision_trace.jsonl — not synchronously from `write_trace()`. Crash-safe up
  to the worker's drain cadence: any crash leaves the index valid for all
  entries drained (written) so far.
- `rebuild()` is called from `DecisionTraceWriter.close()` to produce a clean,
  complete index at run end.
- `lookup()` is used by the REST API (E22C) to byte-seek directly to a tick.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, List

logger = logging.getLogger(__name__)


class DecisionTraceIndex:
    """Maintains a tick→byte_offset sidecar for decision_trace.jsonl."""

    def __init__(self, run_dir: str) -> None:
        self._trace_path = os.path.join(run_dir, "decision_trace.jsonl")
        self._index_path = os.path.join(run_dir, "decision_trace_index.json")
        self._index: Dict[int, int] = {}  # tick → first byte offset for that tick

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def append_entry(self, tick: int, offset: int) -> None:
        """
        Incrementally add a tick→offset entry (non-fatal).

        Only the FIRST occurrence of a tick is recorded — subsequent entities
        on the same tick are contiguous in the file and will be traversed by
        `lookup()` until the tick changes.

        Called from `DecisionTraceWriter`'s async drain worker
        (`_write_entry_to_file`) after each queued entry is written to
        decision_trace.jsonl, so the sidecar is kept valid after every
        drained write — at the worker's drain cadence, not synchronously per
        hot-path `write_trace()` call.
        """
        if tick in self._index:
            return  # already recorded the first offset for this tick
        try:
            self._index[tick] = offset
            self._flush()
        except Exception:
            logger.exception("DecisionTraceIndex.append_entry failed (non-fatal)")

    def rebuild(self) -> None:
        """
        Scan decision_trace.jsonl and rebuild the full index from scratch.

        Called from `DecisionTraceWriter.close()` to guarantee a clean,
        complete sidecar at run end regardless of any incremental errors.
        Non-fatal: any I/O or parse error is logged and ignored.
        """
        if not os.path.exists(self._trace_path):
            return
        try:
            new_index: Dict[int, int] = {}
            with open(self._trace_path, "r", encoding="utf-8") as f:
                while True:
                    offset = f.tell()
                    line = f.readline()
                    if not line:
                        break
                    try:
                        entry = json.loads(line)
                        tick = int(entry["tick"])
                        if tick not in new_index:
                            new_index[tick] = offset
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            self._index = new_index
            self._flush()
        except Exception:
            logger.exception("DecisionTraceIndex.rebuild failed (non-fatal)")

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def lookup(self, tick: int) -> List[dict]:
        """
        Return all entries for a given tick via byte-seek (O(1) seek + O(k) read).

        Loads the index from disk if not already in memory. Returns an empty
        list if the tick is not present in the index. Reads forward from the
        seek position until the tick changes (entries are contiguous by tick).
        """
        if not self._index:
            self._load()
        offset = self._index.get(tick)
        if offset is None:
            return []
        results: List[dict] = []
        try:
            with open(self._trace_path, "r", encoding="utf-8") as f:
                f.seek(offset)
                while True:
                    line = f.readline()
                    if not line:
                        break
                    try:
                        entry = json.loads(line)
                        if int(entry["tick"]) != tick:
                            break  # past this tick's entries
                        results.append(entry)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        break
        except Exception:
            logger.exception("DecisionTraceIndex.lookup failed (non-fatal)")
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flush(self) -> None:
        """Serialize the in-memory index to disk (string keys, int values)."""
        serialized = {str(k): v for k, v in self._index.items()}
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f)

    def _load(self) -> None:
        """Load the index from disk (converts string keys back to int)."""
        if not os.path.exists(self._index_path):
            return
        try:
            with open(self._index_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._index = {int(k): int(v) for k, v in raw.items()}
        except Exception:
            logger.exception("DecisionTraceIndex._load failed (non-fatal); index stays empty")
