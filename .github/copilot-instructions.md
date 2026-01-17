# Copilot Instructions for Docker Homelab

This file guides AI coding agents through this homelab's architecture, deployment patterns, and conventions.

## Quick Context

- **Hosts:**
  - **docker-critical** (Debian) - Mission-critical services (Home Assistant, Authelia, Forgejo, Traefik)
  - **docker-noncritical** (Debian) - Non-essential services (media stack, AI, automation)
  - **truenas01** - NFS/SMB storage server only (no Docker)
- **Git:** Forgejo (self-hosted Git server + Actions runners on each Docker host)
- **Deployments:** GitOps via Forgejo workflows (no persistent repo clone on host)
- **Secrets:** Forgejo repository variables/secrets only (no `.env` files)
- **Reverse Proxy:** Traefik with Cloudflare DNS-01 ACME (one instance per Docker host)
- **Storage:**
  - **docker-critical:** `/srv` (NVMe #1) for configs/databases, `/mnt/nvme-appdata` (NVMe #2) for appdata/search, `/mnt/hdd` for bulk/logs
  - **docker-noncritical:** `/srv` for service configs, `/mnt/data` for media/downloads
  - **truenas01:** NFS/SMB shares mounted on Docker hosts

## Architecture

### Service Organization
- **`Docker-Critical/`** — Mission-critical services on docker-critical host
  - `Home/HomeAssistant/` — Home automation hub + ESPHome
  - `Home/RTL-SDR/` — Software-defined radio for sensors
  - `Home/MusicAssistant/` — Multi-room audio server
  - `Home/NetBox/` — Network documentation
  - `Home/Cooking/` — Norish recipe app
  - `Home/KaraKeep/` — Media library management
  - `Management/Git - Forgejo/` — Forgejo server + Postgres
  - `Management/HomeBox/` — Household inventory
  - `Networking/Proxy/` — Traefik reverse proxy
  - `Networking/Omada/` — Network controller
  - `Networking/Mail/` — SMTP relay (Postfix)
  - `Auth/` — Authelia SSO
  - `Tools/InfluxDB/` — Time-series database
- **`Docker-NonCritical/`** — Non-essential services on docker-noncritical host
  - `Media/*/` — Media stack (radarr, sonarr, lidarr, prowlarr, readarr, overseerr, flaresolverr, profilarr, dispatcharr, plex)
  - `Networking/Torrent/` — qBittorrent + Gluetun VPN + NZBGet
  - `Networking/Proxy/` — Traefik reverse proxy (non-critical instance)
  - `Automation/AI/` — Ollama, Open WebUI
  - `Automation/` — ComfyUI, Watchtower, Price Tracker
  - `Security/Crowdsec/` — Threat detection

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
**docker-critical:**
- App config: `/srv/<service>/` (e.g., `/srv/homeassistant`, `/srv/traefik`, `/srv/git`)
- Appdata tier: `/mnt/nvme-appdata/<service>/` (e.g., `/mnt/nvme-appdata/netbox`, `/mnt/nvme-appdata/karakeep`)
- Bulk storage: `/mnt/hdd/` (logs, archives, ZIM files)

**docker-noncritical:**
- App config: `/srv/<service>/config/` (e.g., `/srv/radarr/config`, `/srv/qbittorrent/config`)
- Media/downloads: `/mnt/data/` (e.g., `/mnt/data/torrents`, `/mnt/data/usenet`)
- Shared media: NFS mounts from truenas01 (e.g., `/mnt/Pool01/data` for Plex, *arr apps)

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
      - PUID=${PUID}
      - PGID=${PGID}
      - TZ=${TZ}
      - VAR_NAME=${VAR_NAME}
    labels:
      - traefik.enable=true
      - traefik.http.routers.myservice.entrypoints=websecure
      - traefik.http.routers.myservice.rule=Host(`myservice.${DOMAIN_NAME}`)
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
- **Runner labels:**
  - `runs-on: docker-critical` for critical services (Home Assistant, Authelia, Traefik-Critical, Forgejo, etc.)
  - `runs-on: docker-noncritical` for non-critical services (media stack, AI, automation)
  - Must match runner's registered labels on each host
- **Checkout:** always v4 (`actions/checkout@v4`)
- **Project scoping:** `-p <service-name>` prevents cross-stack impacts (e.g., `docker compose -p postfix -f /tmp/Postfix.yml`)
- **Environment vars:** exported to remote SSH session (e.g., `VAR1=$VAR1 docker compose ...`)
- **Checksum gate:** avoid redeploys if config unchanged (efficiency + idempotence)
- **scp + ssh:** workflows run locally on runner; compose file copied to `/tmp/`, executed there
- **Host-specific paths:** Ensure volume paths match the target host's storage layout

## Common Patterns

### Adding a Service to Media Network (docker-noncritical)
Create `Docker-NonCritical/Media/<ServiceName>/<service>.yml`:
```yaml
services:
  <service>:
    image: <image>
    container_name: <service>
    restart: unless-stopped
    networks: [mediaproxy]
    environment: [PUID=568, PGID=568, TZ=America/Chicago]
    labels: [traefik.enable=true, com.centurylinklabs.watchtower.enable=true, ...]
    volumes: [/srv/<service>/config:/config, /mnt/Pool01/data:/data]
    security_opt: [no-new-privileges:true]
networks:
  mediaproxy: {external: true}
```
Then create `.forgejo/workflows/deploy-<service>.yml` with `runs-on: docker-noncritical`.

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
Read `.continue/rules/Context.md` in the workspace root for:
- Multi-host infrastructure (docker-critical, docker-noncritical, truenas01)
- Full list of Forgejo variables/secrets
- Network definitions
- Host storage layouts (per-host)
- CI/CD runner details (one per Docker host)

## DO's and DON'Ts

✅ **DO**
- Place each service in its own `<service>.yml` file under `Docker-Critical/` or `Docker-NonCritical/`
- Use external networks (defined once per host, reused)
- Reference all secrets/vars via `${VAR}` placeholders
- Create Forgejo workflows with checksum gating and correct runner labels (`docker-critical` or `docker-noncritical`)
- Mount persistent data to host-specific paths:
  - **docker-critical:** `/srv/<service>/`, `/mnt/nvme-appdata/<service>/`, or `/mnt/hdd/`
  - **docker-noncritical:** `/srv/<service>/config/`, `/mnt/data/`
- Use Traefik labels for routing and ACME
- Test compose files locally before commit
- Document custom env vars in service READMEs
- Include `security_opt: [no-new-privileges:true]` and `restart: unless-stopped`

❌ **DON'T**
- Create `.env` files (breaks GitOps; use Forgejo secrets instead)
- Hardcode domain names, passwords, or IPs (use placeholders)
- Inline network creation (external or pre-created only)
- Mix multiple services in one compose file (except tightly coupled stacks like Norish+DB)
- Deploy critical services to docker-noncritical (will lose home automation)
- Deploy non-critical services to docker-critical (wastes resources)
- Use `:latest` tags without understanding update implications
- SSH directly to Docker hosts for deployments (always use Forgejo workflows)
- Assume both hosts have identical storage paths

## File Structure Reference
```
docker/
├── .forgejo/workflows/          # CI/CD workflows (one per service)
│   ├── deploy-<service>.yml     # Specifies runner: docker-critical or docker-noncritical
│   └── ...
├── .github/copilot-instructions.md  # This file
├── Docker-Critical/             # Critical services (docker-critical host)
│   ├── Home/                    # Home services (HA, Music, NetBox, Norish, KaraKeep)
│   ├── Management/              # Infrastructure (Forgejo, HomeBox)
│   ├── Networking/              # Proxy, Omada, Mail
│   ├── Auth/                    # Authelia SSO
│   └── Tools/                   # InfluxDB
├── Docker-NonCritical/          # Non-critical services (docker-noncritical host)
│   ├── Media/                   # Media stack (*arr apps, Plex, Overseerr, etc.)
│   ├── Networking/              # Torrent/VPN (qBittorrent, Gluetun, NZBGet), Proxy
│   ├── Automation/              # AI (Ollama, WebUI, ComfyUI), Watchtower, Price Tracker
│   └── Security/                # Crowdsec
└── README.md
```

## Next Steps for Agents
1. Read `.continue/rules/Context.md` in the workspace root for full infrastructure knowledge
2. Determine which host the service belongs on (critical vs non-critical)
3. Inspect existing workflows (`.forgejo/workflows/deploy-*.yml`) for runner label examples
4. For new services:
   - Create compose file in appropriate `Docker-Critical/` or `Docker-NonCritical/` folder
   - Create workflow with correct `runs-on:` label
   - Use host-appropriate storage paths
5. Always validate YAML syntax and network existence before committing
6. Test locally first; use `workflow_dispatch` for manual trigger during development
