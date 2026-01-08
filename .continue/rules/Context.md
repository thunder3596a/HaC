# Copilot Instructions for Home-Lab Workspace

This file guides AI coding agents across this multi-project workspace: Docker homelab infrastructure, PriceTracker application, Home Assistant configuration, and Forgejo MCP server.

## Workspace Overview

Four independent projects sharing infrastructure:

| Project | Location | Purpose | Tech Stack |
|---------|----------|---------|-----------|
| **Docker** | `./docker/` | Infrastructure & services | Docker Compose, Forgejo CI/CD |
| **PriceTracker** | `./pricetracker/` | Price monitoring & purchasing strategy | Node.js + React, PostgreSQL, Redis |
| **Home Assistant** | `./Home Assistant/homeassistant/` | Home automation & IoT | YAML config, custom components |
| **Forgejo MCP** | `./Local Development/AI/forgejo-mcp/` | Git-based AI integration | Go, MCP protocol |

---

## 🐳 Docker Homelab

**Existing instructions:** See [docker/.github/copilot-instructions.md](../docker/.github/copilot-instructions.md) for detailed patterns.

### Key Context
- **Architecture:** Multi-host Docker deployment (TrueNAS is NAS only)
  - **docker-critical** (192.168.19.51, `docker-critical.u-acres.com`) — Mission-critical services (Home Assistant, Authelia, Traefik, Forgejo)
  - **docker-noncritical** (192.168.19.52, `docker-noncritical.u-acres.com`) — Non-essential services (media, AI, automations)
- **Deployment:** GitOps via Forgejo workflows (no persistent clone, uses scp + ssh to `/tmp/` on respective hosts)
- **Reverse Proxy:** Two Traefik instances (one per host) with Cloudflare DNS-01 ACME
- **Storage:** 
  - **Critical:** `/srv` (NVMe #1) for configs/databases, `/mnt/nvme-appdata` (NVMe #2) for appdata/search
  - **NonCritical:** Local storage per host
- **Networks:** Logical scopes (homeproxy, mediaproxy, toolsproxy, torrentproxy, aiproxy, secproxy, gitproxy, authnet)

### Compose File Essentials
- No `version` key (Docker Compose v2)
- PUID=568, PGID=568, TZ=America/Chicago for linuxserver images
- All secrets/vars as `${VAR_NAME}` (via Forgejo variables/secrets, never hardcoded)
- Traefik labels for every exposed service
- External networks only (pre-created)
- `restart: unless-stopped` + Watchtower labels

### Service Organization
- **Critical services** in `Docker-Critical/` (Home Assistant, Authelia, Traefik, Forgejo, Omada, RTL-SDR, NetBox, etc.)
- **Non-critical services** in `Docker-NonCritical/` (Media stack, Automation, AI services, etc.)
- Each service in its own `<service>.yml` file
- Per-service Forgejo workflows with checksum-gating and appropriate runner selection:
  - `runs-on: docker-critical` for critical services
  - `runs-on: docker-noncritical` for non-critical services

---

## 💰 PriceTracker

### Architecture
- **Frontend:** React 18 + Vite + TailwindCSS (sage-green theme)
- **Backend:** Node.js 20 + Express + TypeScript
- **Database:** PostgreSQL 14+
- **Cache:** Redis 6+
- **Auth:** OIDC + Authelia with PKCE + refresh token rotation
- **Push Notifications:** APNs for iOS
- **Price Scraping:** Node-cron background jobs + Playwright for dynamic content

### Project Structure
```
backend/
├── src/
│   ├── api/routes/          # Express routes
│   ├── services/            # Business logic (price scraping, purchasing strategies)
│   ├── repositories/        # Database access layer
│   ├── middleware/          # Auth, validation, error handling
│   ├── jobs/                # Background jobs (price monitors)
│   ├── config/              # Configuration (OIDC, APNs, etc.)
│   └── types/               # TypeScript interfaces
├── migrations/              # Database migrations
└── tests/                   # Unit & integration tests

frontend/
├── src/
│   ├── components/          # Reusable UI components
│   ├── pages/               # Page-level components
│   ├── services/            # API clients (Zustand + React Query)
│   ├── store/               # Zustand state stores
│   ├── styles/              # TailwindCSS + custom theme (sage-green)
│   └── types/               # TypeScript types
└── Dockerfile               # Multi-stage build
```

### Key Patterns
- **Zod validation** for all API inputs
- **React Query** for server state; **Zustand** for client state
- **TypeScript strict mode** throughout
- **Two purchasing strategies:** Opportunistic Buying & Bulk Purchase Optimization
- **Multi-user collaboration:** Owner/Editor/Viewer permissions
- **Quantity-aware cost tracking** at project and group levels

### Development Workflow
```bash
# Setup
cp .env.example .env
docker-compose -f docker-compose.dev.yml up -d

# Migrate & seed
docker-compose -f docker-compose.dev.yml exec api npm run migrate
docker-compose -f docker-compose.dev.yml exec api npm run seed

# Dev servers
npm run dev  # Both frontend and backend with hot-reload
```

### Build & Testing
```bash
# Lint & type-check
npm run lint      # ESLint
npm run format    # Prettier
npm run type-check

# Tests
npm run test               # Unit tests
npm run test:integration   # Integration tests
```

### Deployment
- Docker Compose production setup with Traefik labels
- Authelia OIDC middleware for API protection
- Build args for `VITE_API_URL` passed at image build time
- Internal network (`pricetracker-internal`) for db/cache; external `toolsproxy` for proxy access
- PostgreSQL persisted to `/mnt/Apps/PriceTracker/postgres`
- Redis persisted to `/mnt/Apps/PriceTracker/redis`

### Critical Files
- [backend/src/config/index.ts](../pricetracker/backend/src/config/index.ts) — Configuration loading
- [backend/src/services/](../pricetracker/backend/src/services/) — Price scraping & purchasing logic
- [frontend/src/services/api.ts](../pricetracker/frontend/src/services/) — API client
- [PURCHASING_STRATEGIES.md](../pricetracker/PURCHASING_STRATEGIES.md) — Algorithm documentation

---

## 🏠 Home Assistant

### Configuration Structure
YAML-based home automation config with custom components, blueprints, and integrations.

### Key Files
- `configuration.yaml` — Main entry point, includes other YAML files
- `automations.yaml` — Automation rules
- `scripts.yaml` — Custom script definitions
- `groups.yaml` — Entity grouping
- `fans.yaml`, `lights.yaml`, `mqtt.yaml`, `sensors.yaml` — Domain-specific configs
- `custom_components/` — Third-party integrations
- `custom_zha_quirks/` — ZigBee device quirks
- `node-red/` — Node-RED automations (if enabled)
- `esphome/` — ESPHome device configs (if integrated)

### Architecture Patterns
- **MQTT:** Central communication hub for integrations
- **ZigBee:** Zigbee2MQTT or ZHA for device control
- **Custom Components:** Extend with community packages
- **Blueprints:** Reusable automation/script templates
- **Addons:** Home Assistant add-ons in `addons_config/` and auto-scripts in `addons_autoscripts/`
- **Secrets:** Use Home Assistant secrets file (not in repo)

### Development Workflow
- Edit YAML configs locally
- Use Home Assistant dev container or Docker instance for testing
- Test automations/scripts in UI before commit
- Custom components go in `custom_components/` and are version-controlled

### Integration Points
- **Authelia:** For UI authentication (external reverse proxy)
- **MQTT Broker:** Central message hub
- **ESPHome:** For custom hardware devices
- **Third-party APIs:** Weather, calendar, voice, notifications

---

## 🔗 Forgejo MCP Server

MCP (Model Context Protocol) server enabling AI assistants to interact with Forgejo (self-hosted Git).

### Architecture
```
main.go
  → cmd/cmd.go              (CLI parsing, flags)
  → operation/operation.go  (Tool registration)
  → operation/{domain}/     (Tool implementations)
  → pkg/forgejo/            (Forgejo API client wrapper)
  → pkg/to/                 (Response formatting)
  → pkg/params/             (Shared parameter descriptions)
```

### Building & Running
```bash
make build              # Outputs ./forgejo-mcp binary
make vendor             # Tidy Go modules

# stdio mode (for MCP clients)
./forgejo-mcp --transport stdio --url https://forgejo.example.org --token <token>

# SSE mode (HTTP-based clients)
./forgejo-mcp --transport sse --url https://forgejo.example.org --token <token> --sse-port 8080
```

### Adding a New Tool
1. **Define tool** in `operation/{domain}/{feature}.go`:
   ```go
   var MyTool = mcp.NewTool(
	   "tool_name",
	   mcp.WithDescription("Description"),
	   mcp.WithString("param", mcp.Required()),
   )
   ```

2. **Implement handler:**
   ```go
   func MyToolFn(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	   param, _ := req.Params.Arguments["param"].(string)
	   result, _, err := forgejo.Client().SomeMethod(param)
	   if err != nil {
		   return to.ErrorResult(fmt.Errorf("failed: %v", err))
	   }
	   return to.TextResult(result)
   }
   ```

3. **Register in domain's RegisterTool()** function
4. **Import & call** in `operation/operation.go`

### Key Dependencies
- `codeberg.org/mvdkleijn/forgejo-sdk/forgejo/v2` — Forgejo API client
- `github.com/mark3labs/mcp-go` — MCP protocol

### Domain Organization
- `operation/issue/` — Issue management (create, update, list, close)
- `operation/pull/` — Pull request operations
- `operation/repo/` — Repository operations (list, info)
- `operation/search/` — Code search, repo search
- `operation/user/` — User operations
- `operation/version/` — Server version info

### Blocked Features
See `docs/plans/`:
- Wiki support (blocked on forgejo-sdk)
- Projects/Kanban (blocked on Gitea 1.26.0)

---

## 🔄 Cross-Project Integration

### Forgejo as Central Git Hub
- **Docker configs** deployed via Forgejo workflows
- **PriceTracker** source code hosted on Forgejo
- **Forgejo MCP** allows AI to interact with all repos
- **Home Assistant** configs can be versioned on Forgejo (with secrets management)

### Secrets Management Strategy
- **Docker:** Forgejo repository variables (plaintext) and secrets (encrypted)
- **PriceTracker:** `.env` from Forgejo secrets (locally for dev, injected via Docker)
- **Home Assistant:** Native Home Assistant secrets file (excluded from repo)
- **Forgejo MCP:** Access token as environment variable or command-line flag

### CI/CD Workflow Pattern
```yaml
name: Deploy <Service>
on:
  push:
	paths:
	  - "Docker-Critical|NonCritical/<service>.yml"  # Determines runner
jobs:
  deploy:
	runs-on: docker-critical  # or docker-noncritical (must match Forgejo runner labels)
	steps:
	  - uses: actions/checkout@v4
	  - name: Compare & redeploy
		run: |
		  # Checksum gating to avoid unnecessary redeploys
		  old_checksum=$(cat .<service>_checksum 2>/dev/null || echo "")
		  new_checksum=$(sha256sum <service>.yml | awk '{print $1}')
		  [ "$old_checksum" = "$new_checksum" ] && exit 0
		  # Deploy logic here
		  echo "$new_checksum" > .<service>_checksum
```

---

## 🛠️ Common Tasks

### Adding a New Docker Service
1. **Determine tier:** Is it mission-critical (HA, Auth, Traefik) or non-critical?
2. Create `docker/Docker-Critical/NewService/newservice.yml` or `docker/Docker-NonCritical/NewService/newservice.yml`
3. Use external network (e.g., `toolsproxy`) pre-created on target host
4. Add Traefik labels pointing to appropriate Traefik instance (`traefik.http.routers.<service>.rule=Host(...)`)
5. Create `.forgejo/workflows/deploy-newservice.yml` with runner selection (`runs-on: docker-critical` or `docker-noncritical`) and checksum gating
6. Test YAML syntax locally: `docker-compose config -f Docker-Critical|NonCritical/NewService/newservice.yml`
7. Verify networks exist on target host before deploying

### Adding an API Endpoint in PriceTracker
1. Create route file in `backend/src/api/routes/<feature>.ts`
2. Import and register in `backend/src/index.ts`
3. Define Zod schema in `backend/src/types/`
4. Implement service logic in `backend/src/services/`
5. Add middleware (auth, validation) via `express-async-errors`
6. Write tests in `backend/tests/`

### Adding a Home Assistant Automation
1. Create YAML in `automations.yaml` or separate file and include
2. Use entity IDs from `configuration.yaml`
3. Test in UI → Developer Tools → Automation
4. Reference blueprints from `blueprints/` if reusable
5. Commit changes (secrets excluded)

### Exposing a Forgejo Tool to MCP
1. Design tool in `operation/{domain}/feature.go`
2. Implement handler with error handling
3. Use `pkg/to.TextResult()` or `pkg/to.ErrorResult()`
4. Register and test via MCP client
5. Document in `docs/tools.md`

---

## 📋 DO's and DON'Ts

✅ **DO**
- Reference configuration via `${VAR}` in Docker files (Forgejo will interpolate)
- Select correct runner in Forgejo workflows (`docker-critical` or `docker-noncritical`)
- Use Zod for schema validation in PriceTracker backend
- Group related Docker services with shared networks per host
- Test compose files locally before committing
- Keep migrations reversible (PriceTracker database)
- Use TypeScript strict mode in all TS projects
- Pin versions in Go `go.mod` (Forgejo MCP)
- Commit Home Assistant YAML but never commit secrets
- Monitor service health on both hosts via Traefik dashboards

❌ **DON'T**
- Hardcode secrets in compose files or source code
- Create `.env` files in Docker project (use Forgejo secrets)
- Mix multiple independent services in one compose file (exceptions: tightly coupled stacks)
- Use `:latest` tags in production without understanding implications
- Deploy critical services to docker-noncritical runner (will lose home automation)
- SSH directly to docker hosts for deployments (always use Forgejo workflows)
- Commit Home Assistant `.storage/` or database files
- Use relative paths in Docker volumes (always absolute)
- Forget to add Watchtower labels for auto-updating services
- Implement Forgejo tools without error handling
- Assume both Docker hosts have identical storage paths

---

## 🚀 Next Steps for Agents

1. **Understand the homelab architecture:** Read [docker/README.md](../docker/README.md) and [docker/Context.md](../docker/Context.md)
2. **For Docker work:** Refer to [docker/.github/copilot-instructions.md](../docker/.github/copilot-instructions.md) for compose patterns
3. **For PriceTracker development:**
   - Backend: Start with [backend/src/config/index.ts](../pricetracker/backend/src/config/index.ts)
   - Frontend: Understand store structure in [frontend/src/store/](../pricetracker/frontend/src/store/)
   - Reference [SETUP.md](../pricetracker/SETUP.md) for local development
4. **For Home Assistant:** Edit YAML, test in UI, commit (exclude secrets)
5. **For Forgejo MCP:** Use `make build`, test locally with `--transport stdio`, reference existing tools in `operation/`

---

## 📚 Key Documentation Files

- [docker/README.md](../docker/README.md) — Docker infrastructure overview
- [docker/Context.md](../docker/Context.md) — Detailed infrastructure reference (secrets, networks, storage)
- [pricetracker/README.md](../pricetracker/README.md) — PriceTracker overview
- [pricetracker/SETUP.md](../pricetracker/SETUP.md) — Development setup guide
- [pricetracker/DEPLOYMENT.md](../pricetracker/DEPLOYMENT.md) — Production deployment
- [pricetracker/API.md](../pricetracker/API.md) — API endpoint documentation
- [pricetracker/PURCHASING_STRATEGIES.md](../pricetracker/PURCHASING_STRATEGIES.md) — Algorithm details
- [Local Development/AI/forgejo-mcp/README.md](../Local%20Development/AI/forgejo-mcp/README.md) — Forgejo MCP docs
