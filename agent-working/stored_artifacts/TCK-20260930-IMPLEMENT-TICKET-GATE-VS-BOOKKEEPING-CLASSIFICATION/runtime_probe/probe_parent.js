export const meta = {
  name: 'probe-runtime-globals',
  description: 'Zero-agent probe: which globals does the native Workflow runtime expose (shell? nested workflow()?)',
}
const names = ['bash', 'sh', 'exec', 'execSync', 'spawn', 'runCommand', 'shell', 'require', 'process', 'Bun', 'Deno', 'fetch', 'fs', 'child_process', 'globalThis', 'workflow', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget']
const types = {}
for (const n of names) {
  try { types[n] = typeof eval(n) } catch (e) { types[n] = 'ReferenceError' }
}
let globalKeys = null
try { globalKeys = Object.getOwnPropertyNames(globalThis).filter(k => !/^[A-Z]/.test(k)).slice(0, 80) } catch (e) { globalKeys = 'threw: ' + String(e && e.message).slice(0, 100) }
let nested = null
try {
  nested = await workflow({ scriptPath: args.child_path }, { from: 'parent' })
} catch (e) {
  nested = { threw: String(e && e.message).slice(0, 200) }
}
return { types, globalKeys, nested }
