# Copilot Instructions for Docker Homelab

This file guides AI coding agents through this homelab's architecture, deployment patterns, and conventions.

## Quick Context

- **Host:** TrueNAS Scale (`truenas01`) running Docker
- **Git:** Forgejo (self-hosted Git server + Actions runner)
- **Deployments:** GitOps via Forgejo workflows (no persistent repo clone on host)
- **Secrets:** Forgejo repository variables/secrets only (no `.env` files)
- **Reverse Proxy:** Traefik with Cloudflare DNS-01 ACME
- **Storage:** `/mnt/Apps/<Service>` for persistent data; `/mnt/Pool01/data` for media

## Architecture

### Service Organization
- **`docker/Media/*/*.yml`** — Per-service media stacks (radarr, sonarr, lidarr, prowlarr, readarr, overseerr, flaresolverr, profilarr, dispatcharr)
- **`docker/Networking/*`** — Proxy (Traefik), torrent (qbittorrent + gluetun + nzbget)
- **`docker/Security/Auth/`** — Authelia authentication
- **`docker/Tools/Mail/`** — SMTP relay (Postfix)
- **`docker/Tools/Git - Forgejo/`** — Forgejo server + Postgres
- **`docker/Tools/Git - Forgejo Runner/`** — Self-hosted Actions runner
- **`docker/Home/*`** — Homelab services (Kiwix library, Norish recipe app, KaraKeep)
- **`docker/Automation/*`** — AI/compute (Ollama, Open WebUI, ComfyUI)

### Networks
Services are scoped to logical networks (external, created by Traefik or defined per-stack):
- `homeproxy` — Home services (Norish, Homebox, Kiwix)
- `mediaproxy` — Media services (Radarr, Sonarr, Overseerr, Dispatcharr)
- `toolsproxy` — Backend tools (Forgejo, utilities)
- `torrentproxy` — Torrent/VPN (qBittorrent, Gluetun, NZBGet)
- `aiproxy` — LLM services (Ollama, Open WebUI)
- `secproxy` — Security (Authelia, Wazuh)
- `gitproxy` — Git/CI (Forgejo, runner)
- `authnet` — Privileged auth-only network (LDAP, OAuth)

### Data Paths
- App config: `/mnt/Apps/<ServiceName>` (e.g., `/mnt/Apps/Sonarr`, `/mnt/Apps/Forgejo`)
- Media: `/mnt/Pool01/data` (radarr, sonarr, lidarr mounts)

## Compose File Patterns

### Minimal Service Example
```yaml
services:
  myservice:
    image: ghcr.io/org/service:latest
    container_name: myservice
    restart: unless-stopped
    networks:
      - toolsproxy
    environment:
      - PUID=568
      - PGID=568
      - TZ=America/Chicago
      - VAR_NAME=${VAR_NAME}
    labels:
      - traefik.enable=true
      - traefik.http.routers.myservice.entrypoints=websecure
      - traefik.http.routers.myservice.rule=Host(`myservice.u-acres.com`)
      - traefik.http.routers.myservice.service=myservice
      - traefik.http.services.myservice.loadbalancer.server.port=8080
      - com.centurylinklabs.watchtower.enable=true
    volumes:
      - /mnt/Apps/myservice:/config
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  toolsproxy:
    external: true
```

### Key Conventions
1. **No `version` key** (Docker Compose v2; key is ignored/warns)
2. **PUID=568, PGID=568** for linuxserver images (consistent host user)
3. **TZ=America/Chicago** (project timezone)
4. **All environment vars as `${VAR_NAME}`** (never hardcoded secrets)
5. **Traefik labels** for every exposed service
6. **Watchtower label** to enable auto-updates
7. **External networks** (never create networks inline unless multi-service)
8. **Project naming:** compose deploy uses `-p <service-name>`

## Forgejo Workflow Patterns

### Deployment Workflow Template
```yaml
name: Deploy <Service>

on:
  push:
    branches:
      - main
    paths:
      - "<path>/<service>.yml"
      - ".forgejo/workflows/deploy-<service>.yml"
  workflow_dispatch:

jobs:
  deploy:
    runs-on: truenas01  # self-hosted runner label
    defaults:
      run:
        shell: sh

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Verify compose file exists
        run: ls -l ./<path>/<service>.yml

      - name: Compare image and config
        working-directory: ./<path>
        env:
          VAR1: ${{ vars.VAR1 }}
          SECRET1: ${{ secrets.SECRET1 }}
        run: |
          # Check if image or config changed; redeploy if needed
          defined_image=$(grep -m1 'image:' <service>.yml | awk '{print $2}')
          running_image=$(docker inspect -f '{{.Config.Image}}' <container-name> 2>/dev/null || echo "none")
          checksum=$(sha256sum <service>.yml | awk '{print $1}')
          old=$(cat .<service>_checksum 2>/dev/null || echo "")

          if [ "$defined_image" != "$running_image" ] || [ "$checksum" != "$old" ]; then
            echo "Redeploying..."
            scp <service>.yml runner@truenas01:/tmp/<service>.yml
            ssh runner@truenas01 "docker rm -f <container-name> || true"
            ssh runner@truenas01 "docker compose -p <project-name> -f /tmp/<service>.yml down --remove-orphans || true"
            ssh runner@truenas01 "VAR1=$VAR1 SECRET1=$SECRET1 docker compose -p <project-name> -f /tmp/<service>.yml up -d --force-recreate"
            echo "$checksum" > .<service>_checksum
          fi
```

### Critical Workflow Details
- **Runner label:** `runs-on: truenas01` (must match runner's registered labels)
- **Checkout:** always v4 (`actions/checkout@v4`)
- **Project scoping:** `-p <service-name>` prevents cross-stack impacts (e.g., `docker compose -p postfix -f /tmp/Postfix.yml`)
- **Environment vars:** exported to remote SSH session (e.g., `VAR1=$VAR1 docker compose ...`)
- **Checksum gate:** avoid redeploys if config unchanged (efficiency + idempotence)
- **scp + ssh:** workflows run locally on runner; compose file copied to `/tmp/`, executed there

## Common Patterns

### Adding a Service to Media Network
Create `docker/Media/<ServiceName>/<service>.yml`:
```yaml
services:
  <service>:
    image: <image>
    container_name: <service>
    networks: [mediaproxy]
    environment: [PUID=568, PGID=568, TZ=America/Chicago]
    labels: [traefik.enable=true, ...]  # as above
    volumes: [/mnt/Apps/<Service>:/config, /mnt/Pool01/data:/data]
networks:
  mediaproxy: {external: true}
```
Then create `.forgejo/workflows/deploy-<service>.yml` following the template above.

### Secrets in Forgejo
Repository Settings → Variables (plaintext) or Secrets (encrypted):
- **Variables:** `DOMAIN_NAME=u-acres.com`, `PUID=568`, `TZ=America/Chicago`
- **Secrets:** `GIT_DB_PASSWORD`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `CLOUDFLARE_DNS_API_TOKEN`, etc.

Access in workflows via `${{ vars.VAR_NAME }}` or `${{ secrets.SECRET_NAME }}`.

### Traefik Middleware (Authelia)
Add middleware reference for protected services:
```yaml
labels:
  - traefik.http.routers.<service>.middlewares=authelia@docker
```
(Authelia auto-injects auth via Traefik middleware)

### Health Checks
Prefer HTTP-based or process checks for container health:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"] 
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

## Context Discovery
Read `Context.md` in the repo root for:
- Physical infrastructure (OpnSense router, TrueNAS interfaces)
- Full list of Forgejo variables/secrets
- Network definitions
- Host storage layout
- CI/CD runner details

## DO's and DON'Ts

✅ **DO**
- Place each service in its own `<service>.yml` file
- Use external networks (defined once, reused)
- Reference all secrets/vars via `${VAR}` placeholders
- Create Forgejo workflows with checksum gating (idempotent)
- Mount persistent data to `/mnt/Apps/<Service>`
- Use Traefik labels for routing and ACME
- Test compose files locally before commit
- Document custom env vars in service READMEs

❌ **DON'T**
- Create `.env` files (breaks GitOps; use Forgejo secrets instead)
- Hardcode domain names, passwords, or IPs (use placeholders)
- Inline network creation (external or pre-created only)
- Mix multiple services in one compose file (except tightly coupled stacks like Norish+DB)
- Forget `restart: unless-stopped` or similar policy
- Use `:latest` tags without understanding update implications
- SSH directly to `truenas01` for deployments (always use Forgejo workflows)

## File Structure Reference
```
docker/
├── .forgejo/workflows/          # CI/CD workflows
│   ├── deploy-<service>.yml
│   └── ...
├── Context.md                   # Infrastructure & secrets reference
├── Automation/                  # AI/compute services
├── Home/                        # Home services
├── Media/                       # Per-service media stacks
├── Networking/                  # Proxy, torrent, VPN
├── Security/                    # Auth, monitoring
├── Tools/                       # Utilities, Git, Mail
└── README.md
```

## Next Steps for Agents
1. Read `Context.md` for full infrastructure knowledge
2. Inspect `.forgejo/workflows/deploy-karakeep.yml` or `deploy-norish.yml` as working examples
3. For new services: create compose file, then workflow from template above
4. Always validate YAML syntax and network existence before committing
5. Test locally first; use `workflow_dispatch` for manual trigger during development
