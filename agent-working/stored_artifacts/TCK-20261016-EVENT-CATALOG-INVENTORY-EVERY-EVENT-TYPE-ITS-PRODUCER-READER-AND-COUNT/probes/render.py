import json, sys, collections
from pathlib import Path
SCR = Path(sys.argv[1]); T = sys.argv[2]; OUTMD = Path(sys.argv[3])
d = json.load(open(SCR / "catalog.json")); rows = d["rows"]; ev = d["evidence"]; sc = d["scorer_types"]
W = ["frontier_living_world", "urban_political", "crowded_frontier"]
def cell(x): return str(x).replace("|", "/").replace("\n", " ")
L = []
A = L.append
A(f"---\nstatus: historical\nlayer: observability\nauthority: P2\naudience: agent\nartifact_type: report\nticket_id: {T}\ndate: 2026-10-16\ntags: []\n---\n")
A("# Event catalog inventory (read-only, owner decision 80 (i))\n")
measured = [t for t, r in rows.items() if r["total"]]
A(f"Base `4de05711f`. {len(rows)} event types: {len(measured)} measured in the runs, {len(rows) - len(measured)} with a producer in `src/` that never fired in {len(ev)} runs (3 worlds x seeds 42-46 x 5000 ticks). Counts are per world, summed over the 5 seeds (`F` frontier_living_world, `U` urban_political, `C` crowded_frontier); per-seed counts are in `event_counts_per_seed.tsv`.\n")
cr = rows.get("combat_resolved", {}).get("counts", {})
A("## 0. What matters most (details below)\n")
A("1. **The event file is lossy once 5000 CRITICAL events have accumulated** (section 1). `biological_state_changed` is CRITICAL, so in FULL mode from about tick 3300 the file and the SimQ feed lose every INFO and WARNING event, including the shutdown tally events the rpg gate reads (`rpg_gate_ledger_tally`, `death_ledger_tally`, `starvation_channel_tally`: present only in the three crowded_frontier runs that stayed under 5000). The gate is safe today only because LIGHT mode does not emit `biological_state_changed` (it is mode-gated).")
A(f"2. **`combat_resolved` is emitted** ({cr.get('frontier_living_world')} / {cr.get('urban_political')} / {cr.get('crowded_frontier')} in F / U / C); the 'known never emitted' list should not carry it. Truly without a producer: `attrition_threshold_crossed` and `camp_constructed`. `project_*` types are reachable only through the translation of `StrategicProjectChanged` / `StrategicDetourCreated` (the table shows what fired).")
A("3. **Alert events never reach SimQ or the file**: `GOLD_HOARDING`, `INFLATION_SPIRAL` and the other economy alerts go to the kernel's listeners only.")
A("4. **Events built in authoritative code and dropped**: `belief_contradiction` and `lead_contradiction_resolved` are built in the refine pass and discarded at `pipeline.py:526` (the extractor re-derives them from the state diff); `leadership_changed`, `betrayal_desertion`, `clan_member_left` and `clan_succession` are buffered on class attributes that no production code reads (section 3c).")
A("5. **Zero `InvariantViolation` events** in 15 runs: no hard-law violation fired.")
A("6. **Economy events never fire in these three worlds**: `gold_sink_fired`, `trade_executed`, `shop_transaction`, `item_crafted` and `quest_reward_dispensed` are all 0 (section 3a), although the Economy pillar listens to them.")
A("7. Counts are FULL observability mode with default feature flags; the default LIGHT mode emits fewer types (mode gates are listed per type).\n")
A("## 1. How nothing was sampled\n")
A("- Observability mode FULL (`ObservabilityConfig.set_override_mode(FULL)` before the kernel is built), kernel from `rpg_gate_run.build_kernel` (audit_mode, pinned governor), PYTHONHASHSEED=0, `tools`-free child `child.py` (kept in `probes/`).")
A("- Four independent counts of every event per run: (R) `EventRecorder.event_count_by_type`, incremented on every `record()` call BEFORE any DEGRADED/PRESSURE drop or 1-in-N sampling; (L) a kernel listener, which sees every extracted, push-shaper, hard-law and governor event, and the alert events that never reach the recorder; (F) the lines of the run's `simulation_events.jsonl`; and the per-type max of the three is the reported count. Channel letters per type are in the table.")
A("- Sampling evidence per run (below): recorder mode transitions seen, `events_dropped_by_mode`, `queue.dropped_count`, in-memory drops and the highest queue fill. The counts are lossless because the recorder stayed NORMAL in every run, nothing was dropped by mode or queue, and R is taken before any filter (see the finding below about the file itself).\n")
A("| world | seed | modes seen | dropped by mode | queue dropped | max queue fill | sum R (recorder) | sum F (file) | F / R | sum L (listener) | file stops keeping events from tick | CRITICAL events |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
for e in ev: A(f"| {e[0]} | {e[1]} | {','.join(e[4])} | {e[2]} | {e[3]} | {e[5]} | {e[8]} | {e[9]} | {e[9] / e[8]:.2f} | {e[10]} | {e[11] if e[11] is not None else ('n/a (old child)' if e[9] < 0.97 * e[8] else '-')} | {e[12]} |")
A("""
**The event file is NOT lossless at 5000 ticks, so the counts do not come from it.** In 12 of the 15 runs `simulation_events.jsonl` holds fewer lines than the recorder counted (F / R down to 0.58), although the recorder stayed in NORMAL, `events_dropped_by_mode` and `queue.dropped_count` are 0, the drain worker is alive and healthy, and the queue is empty at the end. Cause (read from `event_recorder.py` `record()`): the in-memory buffer holds 5000 events; when it is full, `record()` evicts the oldest event of the lowest severity below CRITICAL, and when everything in it is CRITICAL it drops the incoming non-critical event and returns BEFORE the queue push. `biological_state_changed` is emitted at severity CRITICAL (14,083 in urban_political seed 42), so once 5000 of them have accumulated (around tick 3300 in that run) every later INFO and WARNING event is dropped from the file and from the SimQ feed (`quality_fn` is fed from the same queue); only the CRITICAL ones still get through. `dropped_event_count` is the counter that shows it (242,360 in that run); the 'file stops keeping events from tick' column is where the file's per-500-tick count falls below 90% of the recorder's. This is a read-only finding for the designer; nothing here was changed.

The count used in the table is the per-type maximum of R, L and F: R is incremented on every `record()` call before any filter, L sees every event handed to the kernel's listeners, and F is shown only as a cross-check. The 3 extra file lines per run are the three shutdown tally events, which are written outside `record()`.
""")
A("\nSimQ note: the SimQ hub is built only when `build_feed_from_env()` returns a feed, so the runs have no hub; the SimQ column is static (scorer `EVENT_TYPES` after `quality_hub._translate`, whose payload-conditional translators map to the outputs listed in the table).\n")

A("## 2. Catalog\n")
A("Producer tags: `EventExtractor` = `event_extractor.py` (the rollback path, live when a push-shaper flag is off); `event_shapers` = the push shapers (live default, `ENABLE_PUSH_EVENT_SHAPERS` ON). Gates are the enclosing conditions that mention a mode or flag. 'free dict' = the payload is a literal dict, not a typed record.\n")
A("| event type | producer (file:line) | derived from | payload shape (key:types, '?' = not on every event) | category / severity | SimQ pillar read | F / U / C | ch |\n|---|---|---|---|---|---|---|---|")
for t in sorted(rows, key=lambda x: (rows[x]["category"], x)):
    r = rows[t]
    prod = "<br>".join(r["sites"][:4]) + (f"<br>+{len(r['sites']) - 4} more" if len(r["sites"]) > 4 else "") if r["sites"] else "(none in src)"
    gate = ("<br>gate: " + "; ".join(r["gates"][:2])) if r["gates"] else ""
    A(f"| `{t}` | {cell(prod)}{cell(gate)} | {cell(r['derived'])} | {cell(r['payload'][:300])} | {cell(r['category'])} / {cell(r['severity'])} | {cell(', '.join(r['simq']) or '-')} | {r['counts'][W[0]]} / {r['counts'][W[1]]} / {r['counts'][W[2]]} | {r['chan'] or '-'} |")

A("\n## 3. Flags\n")
reach = set()
import importlib
def ct(t, rows=rows):
    return rows[t]["simq_types"] if "simq_types" in rows[t] else None
A("### 3a. Types a SimQ pillar listens for that are NEVER emitted\n")
emitted_contract = d.get("emitted_contract", {})
never = d["never_emitted"]; dormant = d["producer_never_fired"]
A("No producer in `src/` at all (after `quality_hub._translate`):\n")
for c, ps in sorted(never.items()): A(f"- `{c}` ({', '.join(ps)})")
A("\nA producer exists in `src/` but the type did not fire once in the measured runs (conditional or dormant; the table shows the gate):\n")
for c, info in sorted(dormant.items()): A(f"- `{c}` -> pillar {info['pillars']}; produced by {info['via']} ({info['sites']})")
A("\n### 3b. Emitted types nobody reads\n")
A("No SimQ pillar reads the type (directly or after translation). 'other readers' = files outside the producers that mention the type string.\n")
A("| event type | measured F / U / C | other readers in src |\n|---|---|---|")
for t, r in sorted(d["unread"].items()): A(f"| `{t}` | {r['f']} / {r['u']} / {r['c']} | {cell(', '.join(r['readers'][:4]) or 'none')} |")
A("\n### 3c. Events built in authoritative code\n")
A("Producers outside `src/observability/` (code that runs in the tick pipeline or beside it, not the read-side extractor/shapers):\n")
A("| event type | producer | where it goes | measured F / U / C |\n|---|---|---|---|")
for t, r in sorted(d["authoritative"].items()): A(f"| `{t}` | {cell('<br>'.join(r['sites']))} | {cell(r['goes'])} | {r['f']} / {r['u']} / {r['c']} |")
A("\n### 3d. SimQ-motivated seeds\n")
A("Producers whose source carries a SimQ/SQ ticket reference nearby. 'D33 candidate?' = the content fiction (something that happens in the world) might justify the event on its own, apart from scoring.\n")
A("| seed (ticket) | what it seeds or enables | events it feeds (measured F / U / C) | D33 candidate? | why |\n|---|---|---|---|---|")
for sd in d["simq_seeds"]:
    ev = "<br>".join(f"`{e}` " + (" / ".join(str(x) for x in c) if c[0] is not None else "(no such type)") for e, c in sd["counts"].items())
    A(f"| {cell(sd['ticket'])} | {cell(sd['what'])} | {ev} | {cell(sd['d33'])} | {cell(sd['why'])} |")
Path(OUTMD).write_text("\n".join(L) + "\n", encoding="utf-8")
# per-seed tsv
tsv = ["type\tworld\t" + "\t".join(str(s) for s in range(42, 47))]
for t, r in sorted(d["per_seed"].items()):
    for w in W: tsv.append(f"{t}\t{w}\t" + "\t".join(str(r.get(w, {}).get(str(s), 0)) for s in range(42, 47)))
Path(OUTMD).with_name("event_counts_per_seed.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
print("wrote", OUTMD, len(L), "lines")
