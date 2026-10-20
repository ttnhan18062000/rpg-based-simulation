"""One lossless event-catalog run: observability FULL, kernel from the gate harness (audit_mode), and four independent counts of every event:

  listener   events handed to the kernel's listeners (extractor + push shapers + hard-law + governor events), before the recorder's mode filter
  recorder   EventRecorder.event_count_by_type: counted on every record() call BEFORE any backpressure drop or sampling
  file       lines of the run's simulation_events.jsonl by event_type (the lossless file when nothing was dropped)
  + sampling evidence: recorder events_dropped_by_mode, queue.dropped_count, in-memory dropped count, recorder mode transitions, max queue fill.

Usage: python child.py <world> <seed> <ticks> <out.json>   (cwd = a worktree; PYTHONPATH = that worktree)
"""
import json, os, shutil, sys
from collections import Counter, defaultdict
from pathlib import Path

world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.observability.config import ObservabilityConfig, ObservabilityMode
ObservabilityConfig.set_override_mode(ObservabilityMode.FULL)
from src.observability import queue as obsq
from tools.test_architecture.rpg_gate_run import build_kernel

max_fill = [0.0]
orig_push = obsq.BoundedObservabilityQueue.try_push
def push(self, ev):
    r = orig_push(self, ev)
    if self.max_size:
        max_fill[0] = max(max_fill[0], self.get_size() / self.max_size)
    return r
obsq.BoundedObservabilityQueue.try_push = push

run_id = f"evcat_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, run_id)
rec = k.event_recorder
modes_seen = set()
orig_eval = rec._obs_controller.evaluate
def ev(fill):
    m = orig_eval(fill); modes_seen.add(getattr(m, "value", str(m))); return m
rec._obs_controller.evaluate = ev

shape = defaultdict(lambda: {"n": 0, "category": Counter(), "severity": Counter(), "source": Counter(), "entity_id_none": 0, "keys": Counter(), "types": defaultdict(Counter), "example": None})
def listener(events):
    for e in events:
        s = shape[e.event_type]
        s["n"] += 1; s["category"][e.event_category] += 1; s["severity"][e.severity] += 1; s["source"][e.source_system] += 1
        if e.entity_id is None: s["entity_id_none"] += 1
        for key, val in (e.payload or {}).items():
            s["keys"][key] += 1; s["types"][key][type(val).__name__] += 1
        if s["example"] is None:
            s["example"] = {"tick": e.tick, "entity_id": e.entity_id, "message": (e.message or "")[:120], "payload": json.loads(json.dumps(e.payload, default=str))}
k._event_listeners.append(listener)
rec_by_bucket = Counter()
_orig_record = rec.record
def _rec(event):
    rec_by_bucket[event.tick // 500] += 1
    return _orig_record(event)
rec.record = _rec

for _ in range(ticks):
    k.tick_once()
stats = {
    "recorder_counts": dict(rec.event_count_by_type),
    "events_dropped_by_mode": rec._events_dropped_by_mode,
    "queue_dropped": rec.queue.dropped_count,
    "inmemory_dropped": rec.dropped_event_count,
    "modes_seen": sorted(modes_seen), "obs_mode_final": getattr(rec._obs_mode, "value", str(rec._obs_mode)),
    "max_queue_fill": round(max_fill[0], 4), "queue_max_size": rec.queue.max_size,
    "survival_counts": dict(getattr(rec, "_survival_event_counts", {}) or {}),
    "worker_alive_before_shutdown": rec._worker.is_alive(), "worker_failures": rec._worker.failure_count, "worker_health": rec._worker.health_status,
    "queue_size_at_end": rec.queue.get_size(), "queue_pushed": rec.queue.pushed_count, "recorder_by_tick_bucket": dict(rec_by_bucket),
}
k.shutdown()
run_dir = Path("data") / "runs" / run_id
file_counts = Counter(); file_by_bucket = Counter()
p = run_dir / "simulation_events.jsonl"
if p.exists():
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            _o = json.loads(line); file_counts[_o.get("event_type")] += 1; file_by_bucket[_o.get("tick", 0) // 500] += 1
        except Exception: file_counts["<unparseable>"] += 1
doc = {"world": world, "seed": seed, "ticks": ticks, "obs_mode": ObservabilityConfig.get_mode().value, "stats": stats, "file_counts": dict(file_counts), "file_by_tick_bucket": dict(file_by_bucket),
       "listener_counts": {t: s["n"] for t, s in shape.items()},
       "shape": {t: {"category": dict(s["category"]), "severity": dict(s["severity"]), "source": dict(s["source"]), "entity_id_none": s["entity_id_none"], "n": s["n"],
                     "keys": {key: {"n": n, "types": dict(s["types"][key])} for key, n in s["keys"].items()}, "example": s["example"]} for t, s in shape.items()}}
Path(out).parent.mkdir(parents=True, exist_ok=True)
Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
shutil.rmtree(run_dir, ignore_errors=True)
print("OK", world, seed, sum(file_counts.values()), "file events;", len(shape), "types")
