#!/usr/bin/env node
/**
 * Playwright render-timing harness for TCK-20260821-LIVE-MAP-PERF-VALIDATION.
 *
 * Boots a real backend (reusing tools/perf/live_map_ws_payload_measure.py's
 * own `--internal-serve` mode -- same custom entities_count / API-key-auth
 * mechanism that script already implements, not duplicated here) and a real
 * `vite` dev server, launches headless Chromium, authenticates the page's
 * REST + WebSocket traffic against the backend without touching any file
 * under frontend/src/, then imposes a requestAnimationFrame sampling loop
 * to measure wall-clock time per animation frame while the canvas is
 * visible and the live WS delta stream is driving redraws.
 *
 * Two harness-only techniques used here, neither of which edits
 * frontend/src/ or src/ (see staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/
 * investigation.md "Auth gate" and "Dev-proxy ws: true gap" sections, and
 * plan.md's Open Question 1 resolution -- both ruled in-scope):
 *
 * 1. `context.route('**\/api\/v1\/**', ...)` injects `X-API-Key` on outgoing
 *    REST calls (Playwright network interception at the page/context level).
 * 2. `context.addInitScript(...)` overrides `window.WebSocket` to redirect
 *    the connection target from the Vite dev-server origin to the real
 *    backend host:port (routing around vite.config.ts's missing `ws: true`
 *    without editing that file -- `useSimulation.ts` builds its WS URL from
 *    `window.location.host` at runtime, so a constructor-level rewrite is
 *    enough) and to append `?key=<raw>` (the query-param channel
 *    `src/api/auth.py::require_api_key_ws` supports specifically because a
 *    browser's native WebSocket() cannot set headers).
 *
 * "Render FPS" here is an IMPOSED measurement, not an observed one: a
 * repo-wide grep (frontend/src/) confirms zero requestAnimationFrame calls
 * exist anywhere in the app today (see investigation.md's "Frontend render
 * path" finding) -- useCanvas.ts's entity-drawing effect is a plain React
 * useEffect keyed on state, redrawing synchronously on every WS message,
 * with no per-frame loop of any kind. So the numbers this script produces
 * measure "wall-clock time between consecutive animation frames while the
 * canvas is visible and receiving live WS updates," not "frames per second
 * of a pre-existing render loop."
 *
 * NOT EXECUTED against a real browser in the sandbox this was authored in:
 * `npm install -D playwright && npx playwright install chromium` reached
 * npm install successfully, but the Chromium binary download failed with a
 * network-level block, not a flaky/retryable error -- `openssl s_client
 * -connect cdn.playwright.dev:443` returns a Fortinet/Fortiguard "SDNS
 * Blocked Page" certificate instead of the real CDN's, i.e. this sandbox's
 * network filter is DNS/TLS-intercepting that host outright (the same
 * category of block CLAUDE.md's CI Failure Triage section documents for
 * GitHub's results-receiver/blob-storage hosts). This matches plan.md's
 * disclosed "Known, Disclosed Gaps to Live Verification" item 3 exactly.
 * This script is a complete, ready-to-run implementation for an environment
 * where the Chromium download succeeds -- AC1 (render FPS) is reported as
 * not measurable with live data in this sandbox, per plan.md's explicit
 * instruction not to fabricate or estimate frame-timing numbers.
 *
 * Usage (once Playwright's chromium binary is installed):
 *   node frontend/perf/live_map_render_timing.mjs --entities 500 --seed 42
 */
import { chromium } from 'playwright';
import { spawn, execSync } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const VENV_PY = path.join(REPO_ROOT, '.venv', 'bin', 'python3');
const BACKEND_SCRIPT = path.join(REPO_ROOT, 'tools', 'perf', 'live_map_ws_payload_measure.py');

function parseArgs(argv) {
  const args = {
    entities: 500,
    seed: 42,
    backendPort: 8500,
    frontendPort: 5173,
    warmupMs: 5000,
    sampleTarget: 1000,
    guardFloorMb: 300,
    preflightEntitiesThreshold: 2000,
    preflightRequiredMb: 2500,
    outDir: path.join(REPO_ROOT, 'staging_artifacts', 'TCK-20260821-LIVE-MAP-PERF-VALIDATION', 'raw'),
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const val = argv[i + 1];
    if (a === '--entities') { args.entities = parseInt(val, 10); i++; }
    else if (a === '--seed') { args.seed = parseInt(val, 10); i++; }
    else if (a === '--backend-port') { args.backendPort = parseInt(val, 10); i++; }
    else if (a === '--frontend-port') { args.frontendPort = parseInt(val, 10); i++; }
    else if (a === '--warmup-ms') { args.warmupMs = parseInt(val, 10); i++; }
    else if (a === '--sample-target') { args.sampleTarget = parseInt(val, 10); i++; }
    else if (a === '--guard-floor-mb') { args.guardFloorMb = parseInt(val, 10); i++; }
    else if (a === '--preflight-entities-threshold') { args.preflightEntitiesThreshold = parseInt(val, 10); i++; }
    else if (a === '--preflight-required-mb') { args.preflightRequiredMb = parseInt(val, 10); i++; }
    else if (a === '--out-dir') { args.outDir = val; i++; }
  }
  return args;
}

function availableMb() {
  try {
    const out = execSync('free -m').toString();
    for (const line of out.split('\n')) {
      if (line.startsWith('Mem:')) {
        const parts = line.trim().split(/\s+/);
        return parseInt(parts[6], 10);
      }
    }
  } catch {
    return null;
  }
  return null;
}

async function waitForHttp(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(1000) });
      if (res.status < 500) return true;
    } catch {
      // not ready yet
    }
    await sleep(500);
  }
  return false;
}

function killTree(proc) {
  if (!proc || proc.exitCode !== null) return;
  try {
    process.kill(-proc.pid, 'SIGTERM');
  } catch {
    try { proc.kill('SIGTERM'); } catch { /* already gone */ }
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  fs.mkdirSync(args.outDir, { recursive: true });
  const resultPath = path.join(args.outDir, `render_timing_${args.entities}.json`);
  const abortedPath = path.join(args.outDir, `render_timing_${args.entities}_ABORTED.json`);

  if (args.entities >= args.preflightEntitiesThreshold) {
    const avail = availableMb();
    if (avail === null || avail < args.preflightRequiredMb) {
      const marker = {
        entities: args.entities,
        seed: args.seed,
        attempted: false,
        reason: 'pre-flight memory check failed',
        available_mb: avail,
        required_mb: args.preflightRequiredMb,
        timestamp: Date.now() / 1000,
      };
      fs.writeFileSync(abortedPath, JSON.stringify(marker, null, 2));
      console.log(
        `NOT ATTEMPTED -- pre-flight memory check failed: ${avail}MB available < `
        + `${args.preflightRequiredMb}MB required. Wrote ${abortedPath}`
      );
      return;
    }
  }

  const rawKey = `live-map-render-timing-${crypto.randomBytes(8).toString('hex')}`;
  const keyHash = crypto.createHash('sha256').update(rawKey).digest('hex');

  // --- Boot backend: reuse the payload-measurement script's own
  // --internal-serve mode instead of duplicating its monkeypatch/auth
  // wiring here. ---
  const backend = spawn(VENV_PY, [
    BACKEND_SCRIPT, '--internal-serve',
    '--entities', String(args.entities),
    '--seed', String(args.seed),
    '--port', String(args.backendPort),
    '--api-key-hash', keyHash,
  ], { cwd: REPO_ROOT, detached: true, stdio: 'ignore' });

  // --- Boot frontend dev server ---
  const frontend = spawn('npx', ['vite', '--port', String(args.frontendPort), '--strictPort'], {
    cwd: path.join(REPO_ROOT, 'frontend'),
    detached: true,
    stdio: 'ignore',
  });

  let browser = null;
  let aborted = false;
  let abortReason = null;

  try {
    const backendReady = await waitForHttp(`http://127.0.0.1:${args.backendPort}/health`, 30000);
    if (!backendReady) throw new Error('backend did not become healthy within timeout');

    const frontendReady = await waitForHttp(`http://127.0.0.1:${args.frontendPort}/`, 30000);
    if (!frontendReady) throw new Error('frontend dev server did not become ready within timeout');

    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    await context.route('**/api/v1/**', async (route) => {
      const headers = { ...route.request().headers(), 'X-API-Key': rawKey };
      await route.continue({ headers });
    });

    await context.addInitScript(
      ({ backendPort, rawKey: injectedKey }) => {
        const NativeWebSocket = window.WebSocket;
        function PatchedWebSocket(url, protocols) {
          const u = new URL(url, window.location.href);
          u.hostname = '127.0.0.1';
          u.port = String(backendPort);
          u.searchParams.set('key', injectedKey);
          return protocols === undefined
            ? new NativeWebSocket(u.toString())
            : new NativeWebSocket(u.toString(), protocols);
        }
        PatchedWebSocket.prototype = NativeWebSocket.prototype;
        PatchedWebSocket.CONNECTING = NativeWebSocket.CONNECTING;
        PatchedWebSocket.OPEN = NativeWebSocket.OPEN;
        PatchedWebSocket.CLOSING = NativeWebSocket.CLOSING;
        PatchedWebSocket.CLOSED = NativeWebSocket.CLOSED;
        window.WebSocket = PatchedWebSocket;
      },
      { backendPort: args.backendPort, rawKey }
    );

    await page.goto(`http://127.0.0.1:${args.frontendPort}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('canvas', { timeout: 30000 });

    // 100 engine warmup ticks before sampling (docs/engine/performance_contract.md
    // section 3.2's measurement protocol). tick_rate is a fixed 0.05s/tick
    // (V2EngineManager), so 100 ticks is ~5s; a fixed wall-clock warmup is
    // used rather than parsing WS tick numbers from inside the page, since
    // the frontend doesn't expose the current tick in the DOM anywhere.
    await sleep(args.warmupMs);

    // Impose a requestAnimationFrame sampling loop -- see module docstring:
    // no rAF loop exists in the app to observe.
    const samples = await page.evaluate(async (target) => {
      return await new Promise((resolve) => {
        const out = [];
        let last = performance.now();
        function tick(now) {
          out.push(now - last);
          last = now;
          if (out.length >= target) {
            resolve(out);
          } else {
            requestAnimationFrame(tick);
          }
        }
        requestAnimationFrame(tick);
      });
    }, args.sampleTarget);

    // In-flight memory guard, checked once sampling completes (page.evaluate
    // runs the whole sampling loop in one round-trip and can't be polled
    // mid-flight from here). If this trips, this run's own completed
    // samples are still recorded and valid -- it only means a subsequent,
    // larger-entity-count run should not be attempted (mirrors
    // tools/perf/live_map_ws_payload_measure.py's guard-then-report shape).
    const avail = availableMb();
    if (avail !== null && avail < args.guardFloorMb) {
      aborted = true;
      abortReason = `memory guard tripped after sampling completed: ${avail}MB available < ${args.guardFloorMb}MB floor`;
    }

    const sorted = [...samples].sort((a, b) => a - b);
    const n = sorted.length;
    const pct = (p) => sorted[Math.min(n - 1, Math.max(0, Math.round(p * (n - 1))))];
    const over = sorted.filter((v) => v > 16.6).length;

    const result = {
      entities: args.entities,
      seed: args.seed,
      attempted: true,
      aborted,
      abort_reason: abortReason,
      sample_count: n,
      warmup_ms: args.warmupMs,
      p50_ms: n ? pct(0.5) : null,
      p95_ms: n ? pct(0.95) : null,
      p99_ms: n ? pct(0.99) : null,
      min_ms: n ? sorted[0] : null,
      max_ms: n ? sorted[n - 1] : null,
      mean_ms: n ? samples.reduce((a, b) => a + b, 0) / n : null,
      pct_frames_over_16_6ms: n ? (over / n) * 100 : null,
      method:
        'harness-imposed requestAnimationFrame sampling loop (page.evaluate) while '
        + 'the canvas is visible and the live WS delta stream drives redraws -- no '
        + 'pre-existing rAF loop exists in the app to observe (see module docstring).',
    };

    fs.writeFileSync(aborted ? abortedPath : resultPath, JSON.stringify(result, null, 2));
    console.log(`Wrote ${aborted ? abortedPath : resultPath} (aborted=${aborted})`);
  } catch (err) {
    const marker = {
      entities: args.entities,
      seed: args.seed,
      attempted: true,
      aborted: true,
      abort_reason: String((err && err.stack) || err),
    };
    fs.writeFileSync(abortedPath, JSON.stringify(marker, null, 2));
    console.error(`ABORTED: ${err}`);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close().catch(() => {});
    killTree(frontend);
    killTree(backend);
  }
}

main();
