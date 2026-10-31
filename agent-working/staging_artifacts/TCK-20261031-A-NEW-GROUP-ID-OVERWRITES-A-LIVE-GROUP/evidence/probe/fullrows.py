"""Scratch: the kernel_scenario recording with full canonical event lines per (call, config) instead of digests. Usage: fullrows.py <world> <seed> <ticks> <out.jsonl>"""
import sys, json
sys.path.insert(0, ".")
import tests.unit.observability.extractor_characterization.kernel_scenario as ks
ks.digest_row = lambda r: r
rows = ks.record_kernel_run(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
with open(sys.argv[4], "w") as fh:
    for r in rows: fh.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")
print(len(rows), "rows")
