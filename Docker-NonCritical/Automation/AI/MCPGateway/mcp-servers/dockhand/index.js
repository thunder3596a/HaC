import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

const DOCKHAND_URL = (process.env.DOCKHAND_URL || '').replace(/\/$/, '');
const DOCKHAND_USERNAME = process.env.DOCKHAND_USERNAME;
const DOCKHAND_PASSWORD = process.env.DOCKHAND_PASSWORD;

if (!DOCKHAND_URL || !DOCKHAND_USERNAME || !DOCKHAND_PASSWORD) {
  console.error('Missing required env vars: DOCKHAND_URL, DOCKHAND_USERNAME, DOCKHAND_PASSWORD');
  process.exit(1);
}

let sessionCookie = null;

async function login() {
  const res = await fetch(`${DOCKHAND_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: DOCKHAND_USERNAME, password: DOCKHAND_PASSWORD }),
  });
  if (!res.ok) throw new Error(`Dockhand login failed: ${await res.text()}`);
  const setCookie = res.headers.get('set-cookie') || '';
  const match = setCookie.match(/dockhand_session=([^;]+)/);
  if (!match) throw new Error('No session cookie in Dockhand login response');
  sessionCookie = match[1];
}

async function request(method, path, body) {
  if (!sessionCookie) await login();
  const opts = {
    method,
    headers: {
      Cookie: `dockhand_session=${sessionCookie}`,
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  };
  let res = await fetch(`${DOCKHAND_URL}${path}`, opts);
  if (res.status === 401) {
    sessionCookie = null;
    await login();
    opts.headers.Cookie = `dockhand_session=${sessionCookie}`;
    res = await fetch(`${DOCKHAND_URL}${path}`, opts);
  }
  const text = await res.text();
  try { return JSON.parse(text); } catch { return text; }
}

const TOOLS = [
  {
    name: 'list_environments',
    description: 'List all Docker environments (hosts) managed by Dockhand',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'list_containers',
    description: 'List all Docker containers across environments. Optionally filter by environmentId.',
    inputSchema: {
      type: 'object',
      properties: {
        environmentId: { type: 'string', description: 'Optional environment ID to filter by' },
      },
    },
  },
  {
    name: 'get_container',
    description: 'Get details for a specific container by ID',
    inputSchema: {
      type: 'object',
      properties: { id: { type: 'string', description: 'Container ID' } },
      required: ['id'],
    },
  },
  {
    name: 'get_container_logs',
    description: 'Get logs from a container',
    inputSchema: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Container ID' },
        tail: { type: 'number', description: 'Number of log lines to return (default 100)' },
      },
      required: ['id'],
    },
  },
  {
    name: 'restart_container',
    description: 'Restart a Docker container by ID',
    inputSchema: {
      type: 'object',
      properties: { id: { type: 'string' } },
      required: ['id'],
    },
  },
  {
    name: 'start_container',
    description: 'Start a stopped Docker container by ID',
    inputSchema: {
      type: 'object',
      properties: { id: { type: 'string' } },
      required: ['id'],
    },
  },
  {
    name: 'stop_container',
    description: 'Stop a running Docker container by ID',
    inputSchema: {
      type: 'object',
      properties: { id: { type: 'string' } },
      required: ['id'],
    },
  },
  {
    name: 'list_stacks',
    description: 'List all Docker Compose stacks managed by Dockhand',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'get_stack',
    description: 'Get details of a specific stack by name',
    inputSchema: {
      type: 'object',
      properties: { name: { type: 'string', description: 'Stack name as shown in Dockhand' } },
      required: ['name'],
    },
  },
  {
    name: 'get_stack_compose',
    description: 'Get the compose file content for a stack',
    inputSchema: {
      type: 'object',
      properties: { name: { type: 'string' } },
      required: ['name'],
    },
  },
  {
    name: 'restart_stack',
    description: 'Restart all containers in a Dockhand stack',
    inputSchema: {
      type: 'object',
      properties: { name: { type: 'string' } },
      required: ['name'],
    },
  },
  {
    name: 'start_stack',
    description: 'Start a stopped Dockhand stack',
    inputSchema: {
      type: 'object',
      properties: { name: { type: 'string' } },
      required: ['name'],
    },
  },
  {
    name: 'stop_stack',
    description: 'Stop a running Dockhand stack (docker compose down)',
    inputSchema: {
      type: 'object',
      properties: { name: { type: 'string' } },
      required: ['name'],
    },
  },
  {
    name: 'get_pending_updates',
    description: 'List containers that have available image updates',
    inputSchema: { type: 'object', properties: {} },
  },
];

async function callTool(name, args) {
  switch (name) {
    case 'list_environments':
      return request('GET', '/api/environments');
    case 'list_containers':
      return request('GET', args?.environmentId
        ? `/api/containers?environmentId=${encodeURIComponent(args.environmentId)}`
        : '/api/containers');
    case 'get_container':
      return request('GET', `/api/containers/${encodeURIComponent(args.id)}`);
    case 'get_container_logs':
      return request('GET', `/api/containers/${encodeURIComponent(args.id)}/logs?tail=${args.tail ?? 100}`);
    case 'restart_container':
      return request('POST', `/api/containers/${encodeURIComponent(args.id)}/restart`);
    case 'start_container':
      return request('POST', `/api/containers/${encodeURIComponent(args.id)}/start`);
    case 'stop_container':
      return request('POST', `/api/containers/${encodeURIComponent(args.id)}/stop`);
    case 'list_stacks':
      return request('GET', '/api/stacks');
    case 'get_stack':
      return request('GET', `/api/stacks/${encodeURIComponent(args.name)}`);
    case 'get_stack_compose':
      return request('GET', `/api/stacks/${encodeURIComponent(args.name)}/compose`);
    case 'restart_stack':
      return request('POST', `/api/stacks/${encodeURIComponent(args.name)}/restart`);
    case 'start_stack':
      return request('POST', `/api/stacks/${encodeURIComponent(args.name)}/start`);
    case 'stop_stack':
      return request('POST', `/api/stacks/${encodeURIComponent(args.name)}/down`);
    case 'get_pending_updates':
      return request('GET', '/api/containers/pending-updates');
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

const server = new Server(
  { name: 'dockhand-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;
  try {
    const data = await callTool(name, args);
    return {
      content: [{ type: 'text', text: typeof data === 'string' ? data : JSON.stringify(data, null, 2) }],
    };
  } catch (err) {
    return {
      content: [{ type: 'text', text: `Error: ${err.message}` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
