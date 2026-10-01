export const meta = {
  name: 'probe-child',
  description: 'Zero-agent child for the nested workflow() probe',
}
let nestedInChild = 'not-attempted'
try {
  await workflow({ scriptPath: '/nonexistent/second-level.js' })
  nestedInChild = 'returned'
} catch (e) {
  nestedInChild = 'threw: ' + String(e && e.message).slice(0, 160)
}
return { child: 'ok', received_args: args, typeof_bash: typeof bash, nested_in_child: nestedInChild }
