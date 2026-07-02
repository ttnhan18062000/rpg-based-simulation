#!/usr/bin/env python3
"""
graphify_to_html.py — Convert graphify graph.json → self-contained interactive HTML.

Libraries used (embedded from node_modules, no internet required):
  - sigma.js v3   (WebGL graph renderer)
  - graphology    (graph data structure)

Usage:
    python3 tools/graphify_to_html.py [INPUT] [-o OUTPUT] [--top-communities N]

Defaults:
    INPUT  = graphify-out/graph.json
    OUTPUT = graphify-out/interactive_graph.html
"""
import json
import math
import random
import argparse
from pathlib import Path
from collections import defaultdict, Counter

PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ab",
    "#a0cbe8", "#ffbe7d", "#ff9d9a", "#86bcb6", "#8cd17d",
    "#f1ce63", "#d4a6c8", "#fabfd2", "#d7b5a6", "#79706e",
]
OTHER_COLOR  = "#3a3a58"
DEFAULT_TOP_N = 20

# Paths relative to project root (where this script is run from)
SIGMA_JS      = Path("node_modules/sigma/dist/sigma.min.js")
GRAPHOLOGY_JS = Path("node_modules/graphology/dist/graphology.umd.min.js")


def assign_cluster_positions(nodes_out, community_counts, top_comm_set):
    """Assign initial (x, y) positions grouped by community to give sigma a good start."""
    comm_nodes: dict = defaultdict(list)
    for n in nodes_out:
        comm_nodes[n["comm"]].append(n)

    sorted_comms = [c for c, _ in community_counts.most_common()]
    n_comms = len(sorted_comms)
    RADIUS = max(800, math.sqrt(len(nodes_out)) * 10)

    comm_pos = {}
    for i, comm in enumerate(sorted_comms):
        angle = 2 * math.pi * i / n_comms
        r = RADIUS * (0.35 if comm in top_comm_set else 0.9)
        comm_pos[comm] = (r * math.cos(angle), r * math.sin(angle))

    rng = random.Random(42)
    for n in nodes_out:
        cx, cy = comm_pos.get(n["comm"], (0.0, 0.0))
        spread = max(30.0, math.sqrt(len(comm_nodes[n["comm"]])) * 14)
        n["x"] = cx + rng.uniform(-spread, spread)
        n["y"] = cy + rng.uniform(-spread, spread)


def main():
    parser = argparse.ArgumentParser(
        description="Convert graphify graph.json → self-contained interactive HTML"
    )
    parser.add_argument("input", nargs="?", default="graphify-out/graph.json")
    parser.add_argument("-o", "--output", default="graphify-out/interactive_graph.html")
    parser.add_argument("--top-communities", type=int, default=DEFAULT_TOP_N,
                        help=f"Communities to colour-code (default: {DEFAULT_TOP_N})")
    args = parser.parse_args()

    print(f"Loading {args.input} …")
    with open(args.input, encoding="utf-8") as f:
        g = json.load(f)

    all_nodes = g["nodes"]
    all_links = g["links"]
    print(f"  {len(all_nodes):,} nodes  {len(all_links):,} links")

    # Degree
    degrees: defaultdict = defaultdict(int)
    for lnk in all_links:
        degrees[lnk["source"]] += 1
        degrees[lnk["target"]] += 1

    # Community colours
    community_counts: Counter = Counter(n.get("community", 0) for n in all_nodes)
    top_comms = [c for c, _ in community_counts.most_common(args.top_communities)]
    top_comm_set = set(top_comms)
    comm_color = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(top_comms)}

    # Slim nodes — these become graphology node attributes too
    nodes_out = []
    for n in all_nodes:
        comm = n.get("community", 0)
        deg  = degrees.get(n["id"], 0)
        nodes_out.append({
            "id":    n["id"],
            "label": n.get("label", n["id"]),
            "color": comm_color.get(comm, OTHER_COLOR),
            "size":  round(max(2.0, math.log2(deg + 2) * 2.5), 2),
            "comm":  comm,
            "ftype": n.get("file_type", "code"),
            "deg":   deg,
            "sf":    n.get("source_file", ""),
            # x/y filled in below
        })

    assign_cluster_positions(nodes_out, community_counts, top_comm_set)

    # Slim links
    node_id_set = {n["id"] for n in all_nodes}
    links_out = []
    for lnk in all_links:
        s, t = lnk["source"], lnk["target"]
        if s in node_id_set and t in node_id_set:
            links_out.append({"s": s, "t": t, "r": lnk.get("relation", "")})

    # Legend
    community_info = [
        {"id": c, "color": comm_color[c], "count": community_counts[c], "label": f"Comm {c}"}
        for c in top_comms
    ]
    other_count = sum(v for c, v in community_counts.items() if c not in top_comm_set)
    if other_count:
        community_info.append({"id": -1, "color": OTHER_COLOR, "count": other_count, "label": "Other"})

    ftype_counts = Counter(n.get("file_type", "code") for n in all_nodes).most_common()
    rel_counts   = Counter(lnk.get("relation", "") for lnk in all_links).most_common(25)

    stats = {
        "nodes":       len(nodes_out),
        "links":       len(links_out),
        "communities": len(community_counts),
        "top_n":       args.top_communities,
    }

    # Embed JS libraries
    print("Reading local libraries …")
    sigma_js      = SIGMA_JS.read_text(encoding="utf-8")
    graphology_js = GRAPHOLOGY_JS.read_text(encoding="utf-8")

    data_block = (
        f"const NODES = {json.dumps(nodes_out, separators=(',',':'))};\n"
        f"const LINKS = {json.dumps(links_out, separators=(',',':'))};\n"
        f"const COMMUNITY_INFO = {json.dumps(community_info)};\n"
        f"const FTYPE_COUNTS   = {json.dumps(dict(ftype_counts))};\n"
        f"const REL_COUNTS     = {json.dumps(dict(rel_counts))};\n"
        f"const OTHER_COLOR    = {json.dumps(OTHER_COLOR)};\n"
        f"const STATS          = {json.dumps(stats)};\n"
    )

    print("Generating HTML …")
    html = (
        HTML_TEMPLATE
        .replace("/* __GRAPHOLOGY__ */", graphology_js)
        .replace("/* __SIGMA__ */",      sigma_js)
        .replace("/* __DATA__ */",       data_block)
    )

    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    mb = out.stat().st_size / 1024 / 1024
    print(f"Written → {out}  ({mb:.1f} MB)")
    print(f"Open:  xdg-open {out.resolve()}")


# ---------------------------------------------------------------------------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Knowledge Graph — Interactive Viewer</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:        #0d0d1a;
  --surface:   #141428;
  --border:    #23233d;
  --accent:    #4e79a7;
  --text:      #dde0ec;
  --muted:     #6b6b8a;
  --hover-bg:  #1c1c34;
  --sidebar-w: 288px;
}
html, body { height: 100%; overflow: hidden; background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; }

/* ── Layout ── */
#layout { display: flex; height: 100vh; overflow: hidden; }
#sidebar { width: var(--sidebar-w); min-width: var(--sidebar-w); flex-shrink: 0;
  background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden; z-index: 10; }
#graph-wrap { flex: 1; overflow: hidden; position: relative; min-width: 0; }
#sigma-container { width: 100%; height: 100%; }

/* ── Sidebar header ── */
#sidebar-header { padding: 12px 14px 10px; border-bottom: 1px solid var(--border); background: #0f0f22; flex-shrink: 0; }
#sidebar-header h1 { font-size: 14px; font-weight: 600; letter-spacing: 0.03em; }
#stats-mini { margin-top: 5px; color: var(--muted); font-size: 11px; line-height: 1.7; }

/* ── Search ── */
#search-wrap { padding: 10px 12px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
#search { width: 100%; background: var(--bg); border: 1px solid var(--border);
  color: var(--text); padding: 7px 10px; border-radius: 6px; font-size: 12px;
  outline: none; transition: border-color 0.15s; }
#search:focus { border-color: var(--accent); }
#search-results { max-height: 150px; overflow-y: auto; margin-top: 5px; display: none; }
.sr-item { display: flex; align-items: center; gap: 6px; padding: 4px 6px;
  cursor: pointer; border-radius: 4px; font-size: 11px;
  white-space: nowrap; overflow: hidden; }
.sr-item:hover { background: var(--hover-bg); }
.sr-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.sr-name { flex: 1; overflow: hidden; text-overflow: ellipsis; }
.sr-deg { color: var(--muted); font-size: 10px; flex-shrink: 0; }

/* ── Controls ── */
#controls { display: flex; gap: 5px; padding: 8px 12px;
  border-bottom: 1px solid var(--border); flex-shrink: 0; flex-wrap: wrap; }
.ctrl-btn { flex: 1; min-width: 64px; padding: 5px 6px; border-radius: 5px; cursor: pointer;
  border: 1px solid var(--border); background: var(--bg); color: var(--text);
  font-size: 11px; font-weight: 500; transition: all 0.14s; text-align: center; }
.ctrl-btn:hover { border-color: var(--accent); color: var(--accent); }
.ctrl-btn.on { background: var(--accent); border-color: var(--accent); color: #fff; }

/* ── Scrollable body ── */
#scroll-body { flex: 1; overflow-y: auto; min-height: 0; }
#scroll-body::-webkit-scrollbar { width: 5px; }
#scroll-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Sections ── */
.section { padding: 10px 12px; border-bottom: 1px solid var(--border); }
.sec-title { font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--muted); margin-bottom: 7px;
  display: flex; justify-content: space-between; align-items: center; }
.sec-title a { font-weight: 400; cursor: pointer; color: var(--accent);
  text-transform: none; letter-spacing: 0; font-size: 10px; text-decoration: none; }

/* ── Filter rows ── */
.filter-row { display: flex; align-items: center; gap: 6px; padding: 3px 4px;
  border-radius: 4px; cursor: pointer; user-select: none; }
.filter-row:hover { background: var(--hover-bg); }
.filter-row input[type=checkbox] { accent-color: var(--accent); cursor: pointer; flex-shrink: 0; }
.filter-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; }
.filter-count { color: var(--muted); font-size: 10px; flex-shrink: 0; }
.c-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }

/* ── Info panel ── */
#info-content { line-height: 1.75; font-size: 12px; }
.field { margin-bottom: 2px; }
.field b { color: var(--text); }
.field span { color: var(--muted); word-break: break-all; }
.empty { color: var(--muted); font-style: italic; }
#nbr-section { margin-top: 8px; }
.nbr-title { font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.07em; color: var(--muted); margin: 4px 0; }
.nbr-row { display: flex; align-items: center; gap: 5px; padding: 2px 4px;
  border-radius: 3px; cursor: pointer; font-size: 11px; }
.nbr-row:hover { background: var(--hover-bg); }
.nbr-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nbr-rel { color: var(--muted); font-size: 10px; flex-shrink: 0; }

/* ── Tooltip overlay ── */
#tip { position: absolute; pointer-events: none; background: #171730ee;
  border: 1px solid var(--border); border-radius: 6px; padding: 7px 10px;
  font-size: 11px; line-height: 1.55; max-width: 300px; z-index: 200;
  display: none; backdrop-filter: blur(3px); }

/* sigma cursor */
.sigma-mouse { cursor: default; }
</style>
</head>
<body>
<div id="layout">

  <div id="sidebar">
    <div id="sidebar-header">
      <h1>Knowledge Graph</h1>
      <div id="stats-mini"></div>
    </div>

    <div id="search-wrap">
      <input type="text" id="search" placeholder="Search nodes…" autocomplete="off" spellcheck="false">
      <div id="search-results"></div>
    </div>

    <div id="controls">
      <button class="ctrl-btn" id="btn-zoom-fit">⊙ Fit</button>
      <button class="ctrl-btn" id="btn-zoom-in">＋</button>
      <button class="ctrl-btn" id="btn-zoom-out">－</button>
      <button class="ctrl-btn" id="btn-clear">✕ Clear</button>
    </div>

    <div id="scroll-body">

      <div class="section" id="info-panel">
        <div class="sec-title">Selected Node</div>
        <div id="info-content"><span class="empty">Click a node to inspect</span></div>
        <div id="nbr-section" style="display:none">
          <div class="nbr-title" id="nbr-count"></div>
          <div id="nbr-list"></div>
        </div>
      </div>

      <div class="section">
        <div class="sec-title">File Type <a onclick="setAll('ftype',true)">all</a></div>
        <div id="ftype-list"></div>
      </div>

      <div class="section">
        <div class="sec-title">Relation <a onclick="setAll('rel',true)">all</a></div>
        <div id="rel-list" style="max-height:200px;overflow-y:auto"></div>
      </div>

      <div class="section">
        <div class="sec-title">Communities <a onclick="setAll('comm',true)">all</a></div>
        <div id="comm-list" style="max-height:300px;overflow-y:auto"></div>
      </div>

    </div>
  </div>

  <div id="graph-wrap">
    <div id="sigma-container"></div>
  </div>

</div>
<div id="tip"></div>

<script>/* __GRAPHOLOGY__ */</script>
<script>/* __SIGMA__ */</script>
<script>
/* __DATA__ */

// ── Node lookup & colour helpers ──────────────────────────────────────────────
const commColorMap = new Map(COMMUNITY_INFO.map(c => [c.id, c.color]));
const nodeDataMap  = new Map(NODES.map(n => [n.id, n]));

function getNodeColor(n) {
  return commColorMap.get(n.comm) ?? OTHER_COLOR;
}

// ── Filter state ──────────────────────────────────────────────────────────────
const activeFtypes = new Set(Object.keys(FTYPE_COUNTS));
const activeRels   = new Set(Object.keys(REL_COUNTS));
const activeComms  = new Set(COMMUNITY_INFO.map(c => c.id));   // includes -1 for "Other"

function isNodeVisible(n) {
  if (!activeFtypes.has(n.ftype)) return false;
  const inTop = commColorMap.has(n.comm) && n.comm !== -1;
  const commKey = inTop ? n.comm : -1;
  return activeComms.has(commKey);
}

function isEdgeVisible(l) {
  if (!activeRels.has(l.r)) return false;
  const sn = nodeDataMap.get(l.s);
  const tn = nodeDataMap.get(l.t);
  return sn && tn && isNodeVisible(sn) && isNodeVisible(tn);
}

// ── Highlight state ────────────────────────────────────────────────────────────
let highlightedNodes = new Set();   // node ids
let highlightedEdges = new Set();   // edge keys
let selectedNodeId   = null;

// ── Build graphology graph ────────────────────────────────────────────────────
const graph = new graphology.MultiDirectedGraph();

for (const n of NODES) {
  graph.addNode(n.id, {
    x:     n.x,
    y:     -n.y,          // flip Y so cluster layout looks natural
    size:  n.size,
    color: getNodeColor(n),
    label: n.label,
  });
}

for (const l of LINKS) {
  try {
    graph.addDirectedEdge(l.s, l.t, { relation: l.r });
  } catch (_) {}          // skip if either node missing
}

// Build edge lookup by (source, target) for neighbour panel
const edgesByNode = new Map();   // nodeId → [{edgeKey, other, rel, dir}]
graph.forEachEdge((eKey, attrs, src, tgt) => {
  if (!edgesByNode.has(src)) edgesByNode.set(src, []);
  if (!edgesByNode.has(tgt)) edgesByNode.set(tgt, []);
  edgesByNode.get(src).push({ eKey, other: tgt, rel: attrs.relation, dir: 'out' });
  edgesByNode.get(tgt).push({ eKey, other: src, rel: attrs.relation, dir: 'in'  });
});

// ── Sigma renderer ────────────────────────────────────────────────────────────
const container = document.getElementById('sigma-container');

const renderer = new Sigma(graph, container, {
  renderEdgeLabels:  false,
  labelFont:         '"Segoe UI", Roboto, sans-serif',
  labelSize:         11,
  labelColor:        { color: '#c8ccdc' },
  labelRenderedSizeThreshold: 6,
  defaultEdgeColor:  'rgba(120,120,180,0.07)',
  defaultEdgeType:   'line',
  edgeReducer(edge, data) {
    const src = graph.source(edge);
    const tgt = graph.target(edge);
    const sn  = nodeDataMap.get(src);
    const tn  = nodeDataMap.get(tgt);
    const lnk = { s: src, t: tgt, r: data.relation };

    if (!isEdgeVisible(lnk)) return { ...data, hidden: true };

    if (highlightedEdges.size > 0) {
      if (highlightedEdges.has(edge)) {
        return { ...data, color: 'rgba(180,190,255,0.75)', size: 1.5, hidden: false };
      }
      return { ...data, color: 'rgba(120,120,180,0.02)', hidden: false };
    }
    return { ...data, hidden: false };
  },
  nodeReducer(node, data) {
    const n = nodeDataMap.get(node);
    if (!n || !isNodeVisible(n)) return { ...data, hidden: true };

    if (highlightedNodes.size > 0) {
      if (highlightedNodes.has(node)) {
        return { ...data, hidden: false, highlighted: node === selectedNodeId };
      }
      return { ...data, color: '#1e1e30', label: null, hidden: false, size: Math.max(1, data.size * 0.5) };
    }
    return { ...data, hidden: false };
  },
});

// ── Camera controls ────────────────────────────────────────────────────────────
document.getElementById('btn-zoom-fit').onclick  = () => renderer.getCamera().animatedReset();
document.getElementById('btn-zoom-in').onclick   = () => renderer.getCamera().animatedZoom({ duration: 200 });
document.getElementById('btn-zoom-out').onclick  = () => renderer.getCamera().animatedUnzoom({ duration: 200 });
document.getElementById('btn-clear').onclick     = clearSelection;

// ── Node hover ────────────────────────────────────────────────────────────────
const tip = document.getElementById('tip');

renderer.on('enterNode', ({ node }) => {
  const n = nodeDataMap.get(node);
  if (!n) return;
  tip.innerHTML =
    `<b>${esc(n.label)}</b><br>` +
    `<span style="color:#8888aa">${n.ftype} · comm ${n.comm} · deg ${n.deg}</span><br>` +
    `<span style="color:#5555aa;font-size:10px">${esc(n.sf)}</span>`;
  tip.style.display = 'block';
  container.style.cursor = 'pointer';
});

renderer.on('leaveNode', () => {
  tip.style.display = 'none';
  container.style.cursor = 'default';
});

container.addEventListener('mousemove', e => {
  const r  = container.getBoundingClientRect();
  let tx   = e.clientX - r.left + 14;
  let ty   = e.clientY - r.top  + 12;
  if (tx + 310 > r.width)  tx = e.clientX - r.left - 320;
  if (ty + 100 > r.height) ty = e.clientY - r.top  - 80;
  tip.style.left = tx + 'px';
  tip.style.top  = ty + 'px';
});

// ── Node click ────────────────────────────────────────────────────────────────
function selectNode(nodeId) {
  selectedNodeId = nodeId;
  const edges    = edgesByNode.get(nodeId) ?? [];
  highlightedNodes = new Set([nodeId, ...edges.map(e => e.other)]);
  highlightedEdges = new Set(edges.map(e => e.eKey));
  renderer.refresh();
  renderInfoPanel(nodeId, edges);
  // Animate camera to node using graph-space coords
  const attrs = graph.getNodeAttributes(nodeId);
  renderer.getCamera().animate(
    { x: attrs.x, y: attrs.y, ratio: 0.25 },
    { duration: 400 }
  );
}

renderer.on('clickNode', ({ node }) => selectNode(node));
renderer.on('clickStage', () => clearSelection());

function clearSelection() {
  selectedNodeId   = null;
  highlightedNodes = new Set();
  highlightedEdges = new Set();
  renderer.refresh();
  document.getElementById('info-content').innerHTML = '<span class="empty">Click a node to inspect</span>';
  document.getElementById('nbr-section').style.display = 'none';
}

function renderInfoPanel(nodeId, edges) {
  const n     = nodeDataMap.get(nodeId);
  const color = getNodeColor(n);
  document.getElementById('info-content').innerHTML =
    `<div class="field"><b>Label</b> <span>${esc(n.label)}</span></div>` +
    `<div class="field"><b>Type</b> <span>${esc(n.ftype)}</span></div>` +
    `<div class="field"><b>Community</b> <span>${n.comm} <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color};vertical-align:middle;margin-left:3px"></span></span></div>` +
    `<div class="field"><b>Degree</b> <span>${n.deg}</span></div>` +
    `<div class="field"><b>File</b> <span style="font-size:11px">${esc(n.sf)}</span></div>`;

  const nbrsec = document.getElementById('nbr-section');
  if (!edges.length) { nbrsec.style.display = 'none'; return; }
  nbrsec.style.display = 'block';

  const out = edges.filter(e => e.dir === 'out');
  const inn = edges.filter(e => e.dir === 'in');
  document.getElementById('nbr-count').textContent =
    `Connections (${out.length} out · ${inn.length} in)`;

  const makeRows = (list, arrow) =>
    list.slice(0, 25).map(e => {
      const on = nodeDataMap.get(e.other);
      if (!on) return '';
      const oc = getNodeColor(on);
      return `<div class="nbr-row" onclick="jumpTo('${escAttr(e.other)}')">` +
        `<div class="c-dot" style="background:${oc}"></div>` +
        `<span class="nbr-name">${esc(on.label)}</span>` +
        `<span class="nbr-rel">${arrow} ${esc(e.rel)}</span></div>`;
    }).join('');

  document.getElementById('nbr-list').innerHTML =
    (out.length ? `<div class="nbr-title">Outgoing (${out.length})</div>` + makeRows(out, '→') : '') +
    (inn.length ? `<div class="nbr-title">Incoming (${inn.length})</div>` + makeRows(inn, '←') : '') +
    (edges.length > 50 ? `<div style="color:var(--muted);font-size:10px;padding:4px">… ${edges.length - 50} more</div>` : '');
}

window.jumpTo = function(id) {
  selectNode(id);
};

// ── Search ────────────────────────────────────────────────────────────────────
const searchInput   = document.getElementById('search');
const searchResults = document.getElementById('search-results');
let   searchTimer   = null;

searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(doSearch, 120);
});
document.addEventListener('click', e => {
  if (!e.target.closest('#search-wrap')) searchResults.style.display = 'none';
});

function doSearch() {
  const q = searchInput.value.trim().toLowerCase();
  if (!q) { searchResults.style.display = 'none'; clearHighlight(); return; }

  const hits = NODES.filter(n => n.label.toLowerCase().includes(q)).slice(0, 30);
  highlightedNodes = hits.length ? new Set(hits.map(n => n.id)) : new Set();
  highlightedEdges = new Set();
  renderer.refresh();

  if (!hits.length) {
    searchResults.innerHTML = '<div style="padding:5px 8px;color:var(--muted);font-size:11px">No results</div>';
    searchResults.style.display = 'block';
    return;
  }
  searchResults.innerHTML = hits.map(n => {
    const c = getNodeColor(n);
    return `<div class="sr-item" onclick="jumpToSearch('${escAttr(n.id)}')">` +
      `<div class="sr-dot" style="background:${c}"></div>` +
      `<span class="sr-name">${esc(n.label)}</span>` +
      `<span class="sr-deg">${n.deg}</span></div>`;
  }).join('');
  searchResults.style.display = 'block';
}

window.jumpToSearch = function(id) {
  searchResults.style.display = 'none';
  selectNode(id);
};

function clearHighlight() {
  highlightedNodes = new Set();
  highlightedEdges = new Set();
  renderer.refresh();
}

// ── Stats ─────────────────────────────────────────────────────────────────────
document.getElementById('stats-mini').innerHTML =
  `${STATS.nodes.toLocaleString()} nodes · ${STATS.links.toLocaleString()} links<br>` +
  `${STATS.communities.toLocaleString()} communities`;

// ── Build filter UI ────────────────────────────────────────────────────────────
function filterRow(group, key, label, count, color) {
  const el = document.createElement('label');
  el.className = 'filter-row';
  el.innerHTML =
    `<input type="checkbox" checked data-g="${group}" data-k="${escAttr(key)}">` +
    (color ? `<div class="c-dot" style="background:${color}"></div>` : '') +
    `<span class="filter-label">${esc(label)}</span>` +
    `<span class="filter-count">${Number(count).toLocaleString()}</span>`;
  return el;
}

const ftypeEl = document.getElementById('ftype-list');
for (const [ft, cnt] of Object.entries(FTYPE_COUNTS))
  ftypeEl.appendChild(filterRow('ftype', ft, ft, cnt, null));

const relEl = document.getElementById('rel-list');
for (const [rel, cnt] of Object.entries(REL_COUNTS))
  relEl.appendChild(filterRow('rel', rel, rel, cnt, null));

const commEl = document.getElementById('comm-list');
for (const c of COMMUNITY_INFO)
  commEl.appendChild(filterRow('comm', String(c.id), c.label, c.count, c.color));

// ── Filter change handler ─────────────────────────────────────────────────────
document.addEventListener('change', e => {
  const cb = e.target;
  if (!cb.matches('input[type=checkbox][data-g]')) return;
  const g = cb.dataset.g, k = cb.dataset.k;
  const toggle = (set, key) => cb.checked ? set.add(key) : set.delete(key);
  if (g === 'ftype') toggle(activeFtypes, k);
  if (g === 'rel')   toggle(activeRels,   k);
  if (g === 'comm')  toggle(activeComms,  isNaN(k) ? k : Number(k));
  renderer.refresh();
});

window.setAll = function(group, on) {
  const cbs = document.querySelectorAll(`input[data-g="${group}"]`);
  cbs.forEach(cb => {
    cb.checked = on;
    const k = cb.dataset.k;
    if (group === 'ftype') on ? activeFtypes.add(k)           : activeFtypes.delete(k);
    if (group === 'rel')   on ? activeRels.add(k)             : activeRels.delete(k);
    if (group === 'comm')  on ? activeComms.add(isNaN(k) ? k : Number(k))
                               : activeComms.delete(isNaN(k) ? k : Number(k));
  });
  renderer.refresh();
};

// ── Utilities ─────────────────────────────────────────────────────────────────
function esc(s)     { return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function escAttr(s) { return String(s??'').replace(/'/g,"\\'"); }
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
