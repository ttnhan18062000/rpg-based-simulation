import { useState, useEffect, useCallback, useRef } from 'react';
import {
  ChevronDown, ChevronRight, Play, Copy, Check, ExternalLink,
  Globe, FileJson, Search, X,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types for parsed OpenAPI spec
// ---------------------------------------------------------------------------

interface OpenAPISpec {
  info: { title: string; description?: string; version: string };
  paths: Record<string, Record<string, OperationDef>>;
  components?: { schemas?: Record<string, SchemaObj> };
  tags?: { name: string; description?: string }[];
}

interface OperationDef {
  operationId?: string;
  summary?: string;
  description?: string;
  tags?: string[];
  parameters?: ParamDef[];
  requestBody?: { content?: Record<string, { schema?: SchemaObj }> };
  responses?: Record<string, { description?: string; content?: Record<string, { schema?: SchemaObj }> }>;
}

interface ParamDef {
  name: string;
  in: string;
  required?: boolean;
  description?: string;
  schema?: SchemaObj;
}

interface SchemaObj {
  type?: string;
  title?: string;
  properties?: Record<string, SchemaObj>;
  items?: SchemaObj;
  required?: string[];
  enum?: (string | number)[];
  default?: unknown;
  description?: string;
  anyOf?: SchemaObj[];
  allOf?: SchemaObj[];
  $ref?: string;
  additionalProperties?: SchemaObj | boolean;
}

interface Endpoint {
  method: string;
  path: string;
  operationId: string;
  summary: string;
  description: string;
  tags: string[];
  parameters: ParamDef[];
  requestBody?: SchemaObj;
  responseSchema?: SchemaObj;
  responseDescription?: string;
}

interface TagGroup {
  name: string;
  description: string;
  endpoints: Endpoint[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const METHOD_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  get:    { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  post:   { bg: 'bg-blue-500/10',    text: 'text-blue-400',    border: 'border-blue-500/30' },
  put:    { bg: 'bg-amber-500/10',   text: 'text-amber-400',   border: 'border-amber-500/30' },
  patch:  { bg: 'bg-orange-500/10',  text: 'text-orange-400',  border: 'border-orange-500/30' },
  delete: { bg: 'bg-red-500/10',     text: 'text-red-400',     border: 'border-red-500/30' },
};

const API_BASE = '/api/v1';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resolveRef(ref: string, spec: OpenAPISpec): SchemaObj {
  const parts = ref.replace('#/', '').split('/');
  let current: unknown = spec;
  for (const p of parts) {
    current = (current as Record<string, unknown>)[p];
  }
  return (current as SchemaObj) ?? {};
}

function resolveSchema(schema: SchemaObj | undefined, spec: OpenAPISpec): SchemaObj | undefined {
  if (!schema) return undefined;
  if (schema.$ref) return resolveRef(schema.$ref, spec);
  if (schema.allOf) {
    const merged: SchemaObj = { type: 'object', properties: {}, required: [] };
    for (const s of schema.allOf) {
      const resolved = resolveSchema(s, spec);
      if (resolved?.properties) Object.assign(merged.properties!, resolved.properties);
      if (resolved?.required) merged.required!.push(...resolved.required);
    }
    return merged;
  }
  if (schema.anyOf) {
    return resolveSchema(schema.anyOf[0], spec);
  }
  return schema;
}

function parseSpec(spec: OpenAPISpec): TagGroup[] {
  const tagMap = new Map<string, TagGroup>();

  const tagDescs = new Map<string, string>();
  for (const t of spec.tags ?? []) tagDescs.set(t.name, t.description ?? '');

  for (const [path, methods] of Object.entries(spec.paths)) {
    for (const [method, op] of Object.entries(methods)) {
      if (['get', 'post', 'put', 'patch', 'delete'].indexOf(method) === -1) continue;

      const tags = op.tags?.length ? op.tags : ['Other'];
      const successResp = op.responses?.['200'] ?? op.responses?.['201'];
      let responseSchema: SchemaObj | undefined;
      if (successResp?.content) {
        const json = successResp.content['application/json'];
        responseSchema = json?.schema ? resolveSchema(json.schema, spec) : undefined;
      }

      let requestBody: SchemaObj | undefined;
      if (op.requestBody?.content) {
        const json = op.requestBody.content['application/json'];
        requestBody = json?.schema ? resolveSchema(json.schema, spec) : undefined;
      }

      const endpoint: Endpoint = {
        method,
        path,
        operationId: op.operationId ?? `${method}_${path}`,
        summary: op.summary ?? '',
        description: op.description ?? '',
        tags,
        parameters: op.parameters ?? [],
        requestBody,
        responseSchema,
        responseDescription: successResp?.description,
      };

      for (const tag of tags) {
        if (!tagMap.has(tag)) {
          tagMap.set(tag, { name: tag, description: tagDescs.get(tag) ?? '', endpoints: [] });
        }
        tagMap.get(tag)!.endpoints.push(endpoint);
      }
    }
  }

  return Array.from(tagMap.values());
}

function schemaToTypeString(schema: SchemaObj | undefined, spec: OpenAPISpec, depth = 0): string {
  if (!schema) return 'unknown';
  const resolved = resolveSchema(schema, spec);
  if (!resolved) return 'unknown';

  if (resolved.enum) return resolved.enum.map(v => JSON.stringify(v)).join(' | ');

  switch (resolved.type) {
    case 'string': return 'string';
    case 'integer':
    case 'number': return 'number';
    case 'boolean': return 'boolean';
    case 'array': {
      const itemType = schemaToTypeString(resolved.items, spec, depth);
      return `${itemType}[]`;
    }
    case 'object': {
      if (!resolved.properties || depth > 2) return 'object';
      const indent = '  '.repeat(depth + 1);
      const closing = '  '.repeat(depth);
      const props = Object.entries(resolved.properties).map(([k, v]) => {
        const opt = resolved.required?.includes(k) ? '' : '?';
        return `${indent}${k}${opt}: ${schemaToTypeString(v, spec, depth + 1)}`;
      });
      return `{\n${props.join('\n')}\n${closing}}`;
    }
    default:
      if (resolved.properties) {
        if (depth > 2) return 'object';
        const indent = '  '.repeat(depth + 1);
        const closing = '  '.repeat(depth);
        const props = Object.entries(resolved.properties).map(([k, v]) => {
          const opt = resolved.required?.includes(k) ? '' : '?';
          return `${indent}${k}${opt}: ${schemaToTypeString(v, spec, depth + 1)}`;
        });
        return `{\n${props.join('\n')}\n${closing}}`;
      }
      return resolved.title ?? 'unknown';
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MethodBadge({ method }: { method: string }) {
  const colors = METHOD_COLORS[method] ?? METHOD_COLORS.get;
  return (
    <span className={`inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${colors.bg} ${colors.text} border ${colors.border}`}>
      {method}
    </span>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button onClick={handleCopy} className="p-1 rounded hover:bg-bg-tertiary text-text-secondary hover:text-text-primary transition-colors" title="Copy">
      {copied ? <Check className="w-3.5 h-3.5 text-accent-green" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
}

function SchemaBlock({ schema, spec, label }: { schema: SchemaObj; spec: OpenAPISpec; label: string }) {
  const typeStr = schemaToTypeString(schema, spec);
  return (
    <div className="mt-2">
      <div className="text-[10px] uppercase tracking-wider text-text-secondary mb-1 font-semibold">{label}</div>
      <div className="relative">
        <pre className="bg-bg-primary border border-border rounded-lg p-3 text-[11px] text-text-primary overflow-x-auto max-h-60 overflow-y-auto leading-relaxed">
          {typeStr}
        </pre>
        <div className="absolute top-1.5 right-1.5">
          <CopyButton text={typeStr} />
        </div>
      </div>
    </div>
  );
}

function ParameterTable({ params }: { params: ParamDef[] }) {
  if (params.length === 0) return null;
  return (
    <div className="mt-3">
      <div className="text-[10px] uppercase tracking-wider text-text-secondary mb-1.5 font-semibold">Parameters</div>
      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="bg-bg-primary">
              <th className="text-left px-3 py-1.5 text-text-secondary font-medium">Name</th>
              <th className="text-left px-3 py-1.5 text-text-secondary font-medium">In</th>
              <th className="text-left px-3 py-1.5 text-text-secondary font-medium">Type</th>
              <th className="text-left px-3 py-1.5 text-text-secondary font-medium">Required</th>
            </tr>
          </thead>
          <tbody>
            {params.map((p, i) => (
              <tr key={i} className="border-t border-border/50">
                <td className="px-3 py-1.5 font-mono text-accent-blue">{p.name}</td>
                <td className="px-3 py-1.5 text-text-secondary">{p.in}</td>
                <td className="px-3 py-1.5 text-accent-purple font-mono">{p.schema?.type ?? 'string'}</td>
                <td className="px-3 py-1.5">{p.required ? <span className="text-accent-red">yes</span> : <span className="text-text-secondary">no</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TryItPanel({ endpoint }: { endpoint: Endpoint }) {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<{ status: number; body: string; time: number } | null>(null);
  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [bodyValue, setBodyValue] = useState('');

  const execute = useCallback(async () => {
    setLoading(true);
    setResponse(null);

    let url = API_BASE + endpoint.path;
    for (const p of endpoint.parameters.filter(p => p.in === 'path')) {
      url = url.replace(`{${p.name}}`, paramValues[p.name] ?? '');
    }

    const queryParams = endpoint.parameters.filter(p => p.in === 'query');
    if (queryParams.length > 0) {
      const qs = queryParams
        .filter(p => paramValues[p.name])
        .map(p => `${p.name}=${encodeURIComponent(paramValues[p.name])}`)
        .join('&');
      if (qs) url += `?${qs}`;
    }

    const opts: RequestInit = { method: endpoint.method.toUpperCase() };
    if (bodyValue && ['post', 'put', 'patch'].includes(endpoint.method)) {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = bodyValue;
    }

    const start = performance.now();
    try {
      const res = await fetch(url, opts);
      const text = await res.text();
      const time = Math.round(performance.now() - start);
      let formatted = text;
      try { formatted = JSON.stringify(JSON.parse(text), null, 2); } catch { /* not json */ }
      setResponse({ status: res.status, body: formatted, time });
    } catch (err) {
      setResponse({ status: 0, body: String(err), time: Math.round(performance.now() - start) });
    } finally {
      setLoading(false);
    }
  }, [endpoint, paramValues, bodyValue]);

  const statusColor = response
    ? response.status >= 200 && response.status < 300 ? 'text-accent-green'
    : response.status >= 400 ? 'text-accent-red' : 'text-accent-yellow'
    : '';

  return (
    <div className="mt-3 border border-border rounded-lg overflow-hidden">
      <div className="bg-bg-primary px-3 py-2 flex items-center justify-between border-b border-border">
        <span className="text-[10px] uppercase tracking-wider text-text-secondary font-semibold">Try It Out</span>
        <button
          onClick={execute}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1 rounded-md text-[11px] font-semibold bg-accent-blue/20 text-accent-blue hover:bg-accent-blue/30 border border-accent-blue/30 transition-colors disabled:opacity-50"
        >
          <Play className="w-3 h-3" />
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>

      {endpoint.parameters.length > 0 && (
        <div className="px-3 py-2 space-y-1.5 border-b border-border/50">
          {endpoint.parameters.map((p, i) => (
            <div key={i} className="flex items-center gap-2">
              <label className="text-[11px] text-text-secondary w-28 shrink-0 font-mono">{p.name}</label>
              <input
                type="text"
                placeholder={p.schema?.default !== undefined ? String(p.schema.default) : p.schema?.type ?? ''}
                value={paramValues[p.name] ?? ''}
                onChange={(e) => setParamValues(prev => ({ ...prev, [p.name]: e.target.value }))}
                className="flex-1 bg-bg-primary border border-border rounded px-2 py-1 text-[11px] text-text-primary placeholder-text-secondary/50 focus:outline-none focus:border-accent-blue/50"
              />
            </div>
          ))}
        </div>
      )}

      {endpoint.requestBody && (
        <div className="px-3 py-2 border-b border-border/50">
          <div className="text-[10px] text-text-secondary mb-1">Request Body (JSON)</div>
          <textarea
            value={bodyValue}
            onChange={(e) => setBodyValue(e.target.value)}
            rows={4}
            className="w-full bg-bg-primary border border-border rounded px-2 py-1.5 text-[11px] text-text-primary font-mono focus:outline-none focus:border-accent-blue/50 resize-y"
            placeholder="{}"
          />
        </div>
      )}

      {response && (
        <div className="px-3 py-2">
          <div className="flex items-center gap-3 mb-1.5">
            <span className={`text-[11px] font-bold ${statusColor}`}>
              {response.status === 0 ? 'Error' : `${response.status}`}
            </span>
            <span className="text-[10px] text-text-secondary">{response.time}ms</span>
            <div className="ml-auto">
              <CopyButton text={response.body} />
            </div>
          </div>
          <pre className="bg-bg-primary border border-border rounded-lg p-3 text-[11px] text-text-primary overflow-x-auto max-h-80 overflow-y-auto leading-relaxed font-mono">
            {response.body}
          </pre>
        </div>
      )}
    </div>
  );
}

function EndpointCard({ ep, spec }: { ep: Endpoint; spec: OpenAPISpec }) {
  const [expanded, setExpanded] = useState(false);
  const [tryIt, setTryIt] = useState(false);
  const colors = METHOD_COLORS[ep.method] ?? METHOD_COLORS.get;

  return (
    <div className={`border rounded-lg overflow-hidden transition-colors ${expanded ? colors.border : 'border-border/50'} ${expanded ? colors.bg : 'hover:border-border'}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-bg-tertiary/30"
      >
        {expanded ? <ChevronDown className="w-3.5 h-3.5 text-text-secondary shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-text-secondary shrink-0" />}
        <MethodBadge method={ep.method} />
        <span className="text-[12px] font-mono text-text-primary font-medium">{ep.path}</span>
        <span className="text-[11px] text-text-secondary ml-2 truncate flex-1">{ep.summary || ep.description}</span>
      </button>

      {expanded && (
        <div className="px-4 pb-3 border-t border-border/30">
          {ep.description && (
            <p className="text-[11px] text-text-secondary mt-2 leading-relaxed">{ep.description}</p>
          )}

          <ParameterTable params={ep.parameters} />

          {ep.requestBody && <SchemaBlock schema={ep.requestBody} spec={spec} label="Request Body" />}
          {ep.responseSchema && <SchemaBlock schema={ep.responseSchema} spec={spec} label="Response (200)" />}

          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={() => setTryIt(!tryIt)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-semibold transition-colors border ${
                tryIt
                  ? 'bg-accent-blue/20 text-accent-blue border-accent-blue/30'
                  : 'bg-bg-tertiary text-text-secondary border-border hover:text-text-primary hover:border-border'
              }`}
            >
              <Play className="w-3 h-3" />
              Try It
            </button>
          </div>

          {tryIt && <TryItPanel endpoint={ep} />}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function ApiDocsPage() {
  const [spec, setSpec] = useState<OpenAPISpec | null>(null);
  const [tagGroups, setTagGroups] = useState<TagGroup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    fetch('/openapi.json')
      .then(r => r.json())
      .then((data: OpenAPISpec) => {
        setSpec(data);
        const groups = parseSpec(data);
        setTagGroups(groups);
        if (groups.length > 0) setActiveTag(groups[0].name);
      })
      .catch(err => setError(String(err)));
  }, []);

  const scrollToTag = useCallback((tag: string) => {
    setActiveTag(tag);
    sectionRefs.current[tag]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  const filteredGroups = tagGroups.map(g => ({
    ...g,
    endpoints: g.endpoints.filter(ep =>
      !searchQuery ||
      ep.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ep.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ep.operationId.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter(g => g.endpoints.length > 0);

  const totalEndpoints = tagGroups.reduce((s, g) => s + g.endpoints.length, 0);

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="text-accent-red text-lg font-semibold mb-2">Failed to load API spec</div>
          <div className="text-text-secondary text-sm">{error}</div>
        </div>
      </div>
    );
  }

  if (!spec) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex items-center gap-3 text-text-secondary">
          <div className="w-5 h-5 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
          Loading API specification...
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 min-h-0 overflow-hidden">
      {/* Left sidebar — tag navigation */}
      <aside className="w-56 shrink-0 bg-bg-secondary border-r border-border flex flex-col">
        <div className="p-3 border-b border-border">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="w-4 h-4 text-accent-blue" />
            <span className="text-[12px] font-semibold text-text-primary">API Reference</span>
          </div>
          <div className="text-[10px] text-text-secondary">
            v{spec.info.version} &middot; {totalEndpoints} endpoints
          </div>
        </div>

        {/* Search */}
        <div className="p-2 border-b border-border">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-secondary" />
            <input
              type="text"
              placeholder="Search endpoints..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-bg-primary border border-border rounded-md pl-7 pr-7 py-1.5 text-[11px] text-text-primary placeholder-text-secondary/50 focus:outline-none focus:border-accent-blue/50"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Tag links */}
        <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {filteredGroups.map(g => (
            <button
              key={g.name}
              onClick={() => scrollToTag(g.name)}
              className={`w-full text-left px-2.5 py-1.5 rounded-md text-[11px] transition-colors flex items-center justify-between ${
                activeTag === g.name
                  ? 'bg-accent-blue/15 text-accent-blue font-semibold'
                  : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
              }`}
            >
              <span>{g.name}</span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                activeTag === g.name ? 'bg-accent-blue/20 text-accent-blue' : 'bg-bg-tertiary text-text-secondary'
              }`}>{g.endpoints.length}</span>
            </button>
          ))}
        </nav>

        {/* External docs link */}
        <div className="p-2 border-t border-border">
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[11px] text-text-secondary hover:bg-bg-tertiary hover:text-text-primary transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Swagger UI
          </a>
          <a
            href="/redoc"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[11px] text-text-secondary hover:bg-bg-tertiary hover:text-text-primary transition-colors"
          >
            <FileJson className="w-3.5 h-3.5" />
            ReDoc
          </a>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {/* Hero */}
        <div className="px-8 pt-6 pb-4 border-b border-border bg-bg-secondary/50">
          <h1 className="text-xl font-bold text-text-primary mb-1">{spec.info.title}</h1>
          {spec.info.description && (
            <p className="text-[13px] text-text-secondary max-w-2xl">{spec.info.description}</p>
          )}
          <div className="flex items-center gap-4 mt-3">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold bg-accent-green/10 text-accent-green border border-accent-green/20">
              Base URL: {API_BASE}
            </span>
            <span className="text-[10px] text-text-secondary">
              OpenAPI {spec.info.version}
            </span>
          </div>
        </div>

        {/* Endpoint groups */}
        <div className="px-8 py-4 space-y-8">
          {filteredGroups.map(group => (
            <section
              key={group.name}
              ref={el => { sectionRefs.current[group.name] = el as HTMLDivElement | null; }}
              className="scroll-mt-4"
            >
              <div className="flex items-center gap-3 mb-3">
                <h2 className="text-sm font-bold text-text-primary">{group.name}</h2>
                <div className="flex-1 border-t border-border/50" />
                <span className="text-[10px] text-text-secondary">{group.endpoints.length} endpoint{group.endpoints.length !== 1 ? 's' : ''}</span>
              </div>
              {group.description && (
                <p className="text-[11px] text-text-secondary mb-3">{group.description}</p>
              )}
              <div className="space-y-2">
                {group.endpoints.map((ep, i) => (
                  <EndpointCard key={`${ep.method}-${ep.path}-${i}`} ep={ep} spec={spec} />
                ))}
              </div>
            </section>
          ))}

          {filteredGroups.length === 0 && (
            <div className="text-center py-12 text-text-secondary text-sm">
              No endpoints match "{searchQuery}"
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
