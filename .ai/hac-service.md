# HaC (Homelab-as-Code) Service Creation Guide

Instructions for creating, deploying, and maintaining Docker services in the HaC infrastructure. This document is the authoritative reference for any AI assistant working on this project.

---

## Architecture Overview

- **Two deployment hosts:**
  - `hac-critical` — Mission-critical services (home automation, auth, networking, git, automation)
  - `hac-noncritical` — Non-essential services (media, AI, tools)
- **GitOps via Forgejo:** All services deploy automatically via Forgejo CI/CD workflows triggered on push to `main`
- **Reverse proxy:** Two Traefik instances (one per host), SSL via Cloudflare DNS-01 ACME, per-subdomain certificates
- **Auth:** Authelia SSO with OIDC, available as Traefik middleware (`authelia@docker`)

---

## Repository Layout

```
HaC/
├── .forgejo/workflows/          # One workflow per service
├── Docker-Critical/             # Services on hac-critical
│   ├── Auth/                    # Authelia, LLDAP
│   ├── Finance/                 # Finance tools
│   ├── Home/                    # Home automation & household apps
│   │   ├── Cooking/norish.yml
│   │   ├── HomeAssistant/homeassistant.yml
│   │   ├── KaraKeep/karakeep.yml
│   │   ├── NetBox/netbox.yml
│   │   └── ...
│   ├── Management/              # Forgejo, HomeBox
│   ├── Networking/              # Traefik, Omada, Cloudflared, Mail
│   └── Tools/                   # InfluxDB, N8N, Kiwix, DockerSocketProxy
├── Docker-NonCritical/          # Services on hac-noncritical
│   ├── Automation/              # AI, ComfyUI, PriceTracker
│   ├── Media/                   # Plex, *arr stack, Books, Immich
│   ├── Networking/              # Traefik, Torrent/VPN
│   ├── Security/                # Crowdsec
│   └── Tools/                   # IT-Tools, SearXNG, Stirling-PDF, MCPGateway
└── scripts/                     # Utility scripts
```

### Where to place a new service

Choose the host based on criticality:

| If the service is... | Place it under | Runs on |
|---|---|---|
| Required for home to function (HA, auth, DNS) | `Docker-Critical/<Category>/` | `docker-critical` |
| Nice-to-have (media, tools, AI) | `Docker-NonCritical/<Category>/` | `docker-noncritical` |

Choose the category subdirectory based on function:

| Category | Use for |
|---|---|
| `Home/` | Household apps (recipes, bookmarks, inventory, home automation) |
| `Media/` | Entertainment (streaming, *arr stack, books, photos) |
| `Tools/` | Utility services (PDF tools, search, monitoring, dev tools) |
| `Networking/` | Proxy, VPN, mail, network management |
| `Auth/` | Authentication and identity |
| `Management/` | Git, inventory, infrastructure management |
| `Automation/` | AI, workflow automation, bots |
| `Security/` | IDS, monitoring, threat detection |
| `Finance/` | Financial tools |

Each service gets its own subdirectory: `Docker-Critical/Home/MyService/myservice.yml`

---

## Compose File Conventions

### Skeleton — Simple Service (no database)

```yaml
services:
  myservice:
    image: author/myservice:latest
    container_name: myservice
    restart: unless-stopped
    networks:
      - toolsproxy                    # See "Network Selection" below
    environment:
      - PUID=${PUID:-568}            # Only for linuxserver.io images
      - PGID=${PGID:-568}
      - TZ=${TZ:-America/Chicago}
    volumes:
      - /srv/myservice/config:/config # See "Storage" below
    labels:
      # Traefik routing
      - traefik.enable=true
      - traefik.http.routers.myservice.entrypoints=websecure
      - traefik.http.routers.myservice.rule=Host(`myservice.${DOMAIN_NAME}`)
      - traefik.http.routers.myservice.service=myservice
      - traefik.http.routers.myservice.tls.certresolver=${CERTRESOLVER:-cloudflare}
      - traefik.http.routers.myservice.tls.domains[0].main=myservice.${DOMAIN_NAME}
      - traefik.http.services.myservice.loadbalancer.server.port=8080
      # Authelia protection (add ONLY if service needs SSO gating)
      # - traefik.http.routers.myservice.middlewares=authelia@docker
      # Watchtower auto-updates
      - com.centurylinklabs.watchtower.enable=true
      # Home Assistant monitoring
      - ha.monitor=true
      - ha.category=tools           # Match the category: home, media, tools, networking, auth, etc.
      - ha.compose-file=Docker-Critical/Tools/MyService/myservice.yml  # Full path from repo root
      - ha.service-name=myservice   # Must match the service key in this file

networks:
  toolsproxy:
    external: true
```

### Skeleton — Service with PostgreSQL + Redis

```yaml
services:
  myservice:
    image: author/myservice:latest
    container_name: myservice
    restart: unless-stopped
    networks:
      - homeproxy
    environment:
      - DATABASE_URL=postgres://${POSTGRES_USER:-postgres}:${MYSERVICE_DB_PASSWORD}@myservice-db:5432/myservice
      - REDIS_URL=redis://myservice-redis:6379
      - TZ=${TZ:-America/Chicago}
    volumes:
      - /srv/myservice/app/data:/app/data
    depends_on:
      - myservice-db
      - myservice-redis
    labels:
      - traefik.enable=true
      - traefik.http.routers.myservice.entrypoints=websecure
      - traefik.http.routers.myservice.rule=Host(`myservice.${DOMAIN_NAME}`)
      - traefik.http.routers.myservice.service=myservice
      - traefik.http.routers.myservice.tls.certresolver=${CERTRESOLVER:-cloudflare}
      - traefik.http.routers.myservice.tls.domains[0].main=myservice.${DOMAIN_NAME}
      - traefik.http.services.myservice.loadbalancer.server.port=3000
      - traefik.http.routers.myservice.middlewares=authelia@docker
      - com.centurylinklabs.watchtower.enable=true
      - ha.monitor=true
      - ha.category=home
      - ha.compose-file=Docker-Critical/Home/MyService/myservice.yml
      - ha.service-name=myservice

  myservice-db:
    image: postgres:17-alpine
    container_name: myservice-db
    restart: unless-stopped
    networks:
      - homeproxy
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${MYSERVICE_DB_PASSWORD}
      - POSTGRES_DB=myservice
    volumes:
      - /srv/myservice/postgres:/var/lib/postgresql/data
    labels:
      - ha.monitor=true
      - ha.category=home
      - ha.compose-file=Docker-Critical/Home/MyService/myservice.yml
      - ha.service-name=myservice-db

  myservice-redis:
    image: redis:8-alpine
    container_name: myservice-redis
    restart: unless-stopped
    networks:
      - homeproxy
    volumes:
      - /srv/myservice/redis:/data
    labels:
      - ha.monitor=true
      - ha.category=home
      - ha.compose-file=Docker-Critical/Home/MyService/myservice.yml
      - ha.service-name=myservice-redis

networks:
  homeproxy:
    external: true
```

---

## Hard Rules

1. **No `version` key** — Docker Compose v2 does not use it
2. **No inline network creation** — All networks are `external: true` (pre-created on the host)
3. **No hardcoded secrets** — Use `${VAR_NAME}` placeholders; values come from Forgejo variables/secrets
4. **No `.env` files** — Environment is injected by Forgejo workflows, never committed
5. **No `:latest` without Watchtower** — If using `:latest`, add the Watchtower label for auto-updates
6. **Absolute volume paths only** — Always `/srv/...`, never `./data`
7. **`restart: unless-stopped`** for all services (exception: `restart: always` only if the app requires it for internal restart functionality)
8. **Every container gets `ha.*` labels** — Even databases and sidecars. This is how Home Assistant monitors container health
9. **One compose file per logical service** — Tightly coupled stacks (app + db + cache) share a file. Independent services get their own
10. **`container_name` is required** — Every service must have an explicit `container_name`

---

## Network Selection

The network determines which Traefik instance routes to the service and provides logical isolation.

### Critical host networks (Docker-Critical)

| Network | Use for | Example services |
|---|---|---|
| `homeproxy` | Home automation and household apps | Home Assistant, Norish, KaraKeep, NetBox, HomeBox |
| `toolsproxy` | Infrastructure and utility services | InfluxDB, N8N, Kiwix, DockerSocketProxy |
| `gitproxy` | Git infrastructure | Forgejo |
| `authnet` | Authentication services (privileged) | Authelia, LLDAP |

### Non-critical host networks (Docker-NonCritical)

| Network | Use for | Example services |
|---|---|---|
| `mediaproxy` | Media streaming and management | Plex, Radarr, Sonarr, Overseerr |
| `toolsproxy` | Utility services | IT-Tools, Stirling-PDF, SearXNG |
| `torrentproxy` | VPN-tunneled download services | Gluetun, qBittorrent, NZBGet |
| `aiproxy` | AI and ML services | Ollama, Open WebUI, ComfyUI |
| `secproxy` | Security monitoring | Crowdsec |

### Network rules

- A service connects to exactly **one** proxy network (the one matching its category)
- Internal-only services (databases, caches, sidecars) join the **same network** as their parent service — they do NOT get Traefik labels
- Traefik itself joins **all** networks on its host so it can route to every service
- The `proxy` network (generic name) exists on critical host only, used alongside toolsproxy by Traefik

---

## Traefik Labels

Every HTTP-exposed service needs these labels. Replace `myservice` with the router/service name (use lowercase, no hyphens in the router name).

### Required labels

```yaml
labels:
  - traefik.enable=true
  - traefik.http.routers.myservice.entrypoints=websecure
  - traefik.http.routers.myservice.rule=Host(`myservice.${DOMAIN_NAME}`)
  - traefik.http.routers.myservice.service=myservice
  - traefik.http.routers.myservice.tls.certresolver=${CERTRESOLVER:-cloudflare}
  - traefik.http.routers.myservice.tls.domains[0].main=myservice.${DOMAIN_NAME}
  - traefik.http.services.myservice.loadbalancer.server.port=<CONTAINER_PORT>
```

### Optional labels

```yaml
# Protect with Authelia SSO (add for admin/sensitive UIs)
- traefik.http.routers.myservice.middlewares=authelia@docker

# Explicit TLS enable (some services need this explicitly)
- traefik.http.routers.myservice.tls=true

# Force a specific Docker network for routing (needed when service is on multiple networks)
- traefik.docker.network=torrentproxy
```

### Subdomain conventions

- Use short, memorable subdomains: `norish`, `plex`, `netbox`, `kara`, `chat`
- Infrastructure dashboards use host-prefixed names: `hac-critical-traefik`, `hac-noncritical-traefik`
- Admin UIs for shared services: `ldapadmin`, `omada`
- All subdomains are under `${DOMAIN_NAME}`

### Router name rules

- Router name = service name, all lowercase
- No hyphens in router names (use `ittools` not `it-tools`)
- When a single container serves multiple UIs (e.g., Gluetun hosting qBittorrent), define multiple routers on the same container with different names and ports

---

## Home Assistant Monitoring Labels

Every container (including databases and sidecars) must have these labels:

```yaml
labels:
  - ha.monitor=true
  - ha.category=<category>                          # home, media, tools, networking, auth, etc.
  - ha.compose-file=<full-path-from-repo-root>.yml  # e.g., Docker-Critical/Home/Cooking/norish.yml
  - ha.service-name=<service-key>                   # Must match the key under `services:` in the compose file
```

The `ha.category` values used across the project:

| Category | Services |
|---|---|
| `home` | Norish, KaraKeep, HomeBox, Home Assistant, Music Assistant |
| `media` | Plex, Radarr, Sonarr, Lidarr, Readarr, Overseerr, Books |
| `tools` | IT-Tools, Stirling-PDF, SearXNG, InfluxDB, N8N, Kiwix |
| `networking` | Traefik, Gluetun, qBittorrent, NZBGet, Omada, Cloudflared, SMTP |
| `auth` | Authelia, LLDAP |

---

## Storage Layout

### Critical host (`hac-critical`)

```
/srv/                        # NVMe #1 — critical configs, databases, high-IO
├── <service>/config         # App configuration
├── <service>/postgres       # PostgreSQL data (bind mount to /var/lib/postgresql/data)
├── <service>/redis          # Redis data (bind mount to /data)
└── <service>/app/           # App-specific data (uploads, cache, etc.)

/mnt/nvme-appdata/           # NVMe #2 — appdata, search indexes, AI models
├── netbox/                  # NetBox app + Postgres + Redis
├── homebox/                 # HomeBox data
└── karakeep/                # KaraKeep data + Meilisearch indexes

/mnt/hdd/                    # HDD — bulk storage, logs, archives
├── logs/<service>           # Service logs
├── kiwix/zim                # Offline content archives
└── backups/                 # Cold backups
```

### Non-critical host (`hac-noncritical`)

```
/srv/                        # Service configs and data
├── plex/config
├── gluetun/config
├── qbittorrent/config
└── <service>/config

/mnt/data/                   # Shared media storage
├── media/movies
├── media/tv
├── media/music
├── torrents
└── usenet
```

### Storage selection rules

| Data type | Location | Why |
|---|---|---|
| Config files, small databases | `/srv/<service>/` | Fast NVMe, survives container recreation |
| Search indexes, large app data (critical host) | `/mnt/nvme-appdata/<service>/` | Separate NVMe for IO isolation |
| Bulk content, logs, archives | `/mnt/hdd/` | HDD is fine for sequential/cold access |
| Media files (non-critical host) | `/mnt/data/media/` | Shared storage for Plex/*arr stack |

---

## Deployment Workflow

Every service needs a Forgejo workflow file at `.forgejo/workflows/deploy-<service>.yml`.

### Skeleton — Simple Deploy (no checksum gating)

For services where a force-recreate on every push is acceptable (lightweight, fast to restart):

```yaml
name: Deploy <ServiceName>

on:
  push:
    branches:
      - main
    paths:
      - "Docker-Critical/Category/ServiceDir/**"    # Trigger on service file changes
      - ".forgejo/workflows/deploy-<service>.yml"    # Trigger on workflow changes
  workflow_dispatch:                                  # Allow manual trigger

jobs:
  deploy:
    runs-on: docker-critical                          # or docker-noncritical

    defaults:
      run:
        shell: sh

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Deploy <ServiceName>
        working-directory: "./Docker-Critical/Category/ServiceDir"
        env:
          TZ: ${{ vars.TZ }}
          DOMAIN_NAME: ${{ vars.DOMAIN_NAME }}
          CERTRESOLVER: ${{ vars.CERTRESOLVER }}
          # Add service-specific vars/secrets as needed
        run: |
          docker compose -p <project-name> -f <service>.yml up -d --force-recreate
```

### Skeleton — Deploy with Checksum Gating

For services where unnecessary restarts should be avoided (databases, stateful services):

```yaml
name: Deploy <ServiceName>

on:
  push:
    branches:
      - main
    paths:
      - "Docker-Critical/Category/ServiceDir/**"
      - ".forgejo/workflows/deploy-<service>.yml"
  workflow_dispatch:

jobs:
  deploy:
    runs-on: docker-critical

    defaults:
      run:
        shell: sh

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Verify compose file exists
        run: |
          ls -l "./Docker-Critical/Category/ServiceDir/<service>.yml"

      - name: Compare image and config
        working-directory: "./Docker-Critical/Category/ServiceDir"
        env:
          DOMAIN_NAME: ${{ vars.DOMAIN_NAME }}
          CERTRESOLVER: ${{ vars.CERTRESOLVER }}
          TZ: ${{ vars.TZ }}
          # Add service-specific secrets
          MYSERVICE_DB_PASSWORD: ${{ secrets.MYSERVICE_DB_PASSWORD }}
        run: |
          # Extract defined image
          defined_image=$(grep -m1 'image:' <service>.yml | awk '{print $2}')

          # Extract running image
          running_image=$(docker inspect -f '{{.Config.Image}}' <container-name> 2>/dev/null || echo "none")

          # Compute checksum of compose file
          checksum=$(sha256sum <service>.yml | awk '{print $1}')
          old=$(cat .<service>_checksum 2>/dev/null || echo "")

          echo "Defined: $defined_image"
          echo "Running: $running_image"
          echo "Checksum: $checksum vs $old"

          if [ "$defined_image" != "$running_image" ] || [ "$checksum" != "$old" ]; then
            echo "Redeploying <ServiceName>"

            # Clean stop
            docker compose -p <project-name> -f <service>.yml down --remove-orphans || true
            docker rm -f <container-name> 2>/dev/null || true

            # Deploy
            docker compose -p <project-name> -f <service>.yml up -d --force-recreate

            # Save checksum
            echo "$checksum" > .<service>_checksum
          else
            echo "No redeploy needed"
          fi
```

### Workflow conventions

1. **Runner selection:** `runs-on: docker-critical` or `runs-on: docker-noncritical` — must match where the service lives
2. **Path triggers:** Always include both the service directory (`**`) and the workflow file itself
3. **`workflow_dispatch`:** Always include for manual triggering
4. **Project name (`-p`):** Use a short, consistent name (usually the service name). This groups containers in Docker
5. **Shell:** `shell: sh` in defaults (use `shell: bash` only if you need bash-specific features like arrays)
6. **Environment:** Pass all `${VAR}` placeholders used in the compose file as `env:` in the workflow step. Use `${{ vars.X }}` for non-sensitive values, `${{ secrets.X }}` for sensitive ones

### Forgejo variables vs secrets

| Type | Syntax | Use for |
|---|---|---|
| **Variables** | `${{ vars.DOMAIN_NAME }}` | Domain, timezone, ports, non-sensitive config |
| **Secrets** | `${{ secrets.DB_PASSWORD }}` | Passwords, API tokens, keys |

Common variables available: `DOMAIN_NAME`, `CERTRESOLVER`, `TZ`, `PUID`, `PGID`, `POSTGRES_USER`, `POSTGRES_DB`, `LETS_ENCRYPT_EMAIL`, `CLOUDFLARE_EMAIL`, `DNS_SERVER`, `HA_HOST_IP`, `HA_URL`

---

## Checklist: Adding a New Service

1. **Decide host:** Critical or non-critical?
2. **Decide category:** Home, Media, Tools, Networking, etc.
3. **Create directory:** `Docker-<Host>/<Category>/<ServiceName>/`
4. **Write compose file:** `<servicename>.yml` following the skeletons above
   - Pick the correct network for the category
   - Add all Traefik labels with correct subdomain and port
   - Add all `ha.*` monitoring labels to every container
   - Add Watchtower label if using `:latest`
   - Use `/srv/<service>/` for storage
   - Use `${VAR}` for all configuration values
5. **Create workflow:** `.forgejo/workflows/deploy-<servicename>.yml`
   - Set correct runner (`docker-critical` or `docker-noncritical`)
   - Set path triggers to the service directory
   - Pass all required env vars from Forgejo variables/secrets
   - Use checksum gating for stateful services
6. **Register secrets/variables:** Add any new `${VAR}` values to Forgejo repository settings
7. **Ensure network exists:** The external network must be pre-created on the target host (`docker network create <name>`)
8. **Test locally:** `docker compose -f <service>.yml config` to validate syntax
9. **Commit and push to `main`** — workflow triggers automatically

---

## Health Checks

Add health checks to stateful and critical services. Common patterns:

### HTTP health check (most web services)

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:<PORT>/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

### PostgreSQL

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -d ${DB_NAME} -U ${DB_USER}"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Redis / Valkey

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 30s
  timeout: 10s
  retries: 3
```

Services with long startup times (ML models, media scanners) should use a longer `start_period` (e.g., `60s` or `90s`).

---

## Resource Limits

Optional but recommended for lightweight/utility services to prevent resource hogging:

```yaml
deploy:
  resources:
    limits:
      memory: 256M
      cpus: '1.0'
    reservations:
      memory: 64M
      cpus: '0.1'
```

Guidelines:

- Small tools (IT-Tools, Stirling-PDF): 256M-1G limit
- Databases: 512M-2G limit depending on dataset size
- Media/AI services: typically no limits (need full resources)

---

## Special Networking Modes

### Host networking

For services that need mDNS discovery, Bluetooth, or direct LAN access:

```yaml
network_mode: host
```

Used by: Home Assistant, Avahi, Matter Server, Music Assistant

When using `network_mode: host`, the service does NOT join any proxy network. Traefik routes to it via IP:

```yaml
# On the Traefik service, route to host-networked service by IP
- traefik.http.services.homeassistant.loadbalancer.server.url=http://${HA_HOST_IP}:8123
```

### VPN-tunneled services (network_mode: service)

Services that must route all traffic through a VPN container:

```yaml
qbittorrent:
  network_mode: service:gluetun
  depends_on:
    gluetun:
      condition: service_healthy
```

The VPN container (Gluetun) exposes ports for all tunneled services. Traefik labels for tunneled services go on the VPN container, not the service itself.

---

## Capabilities and Security

### Only add capabilities when required

```yaml
# VPN containers
cap_add:
  - NET_ADMIN
devices:
  - /dev/net/tun:/dev/net/tun

# Home automation with hardware access
cap_add:
  - NET_ADMIN
  - NET_RAW
  - NET_BROADCAST
```

### Security hardening for download/network services

```yaml
security_opt:
  - no-new-privileges:true
```

### Device passthrough (USB, SDR, Bluetooth)

```yaml
devices:
  - /dev/bus/usb:/dev/bus/usb
  - /dev/rfkill:/dev/rfkill
```

Only use `privileged: true` as a last resort (currently only Home Assistant requires it).

---

## Anti-Patterns

- Creating `.env` files in the repo (use Forgejo secrets)
- Using `docker-compose` (v1) instead of `docker compose` (v2)
- Mixing unrelated services in one compose file
- Using relative volume paths (`./data:/data`)
- Forgetting `ha.*` labels on database/sidecar containers
- Using `bridge` or default networks instead of external proxy networks
- Hardcoding domain names instead of `${DOMAIN_NAME}`
- Deploying critical services to the non-critical runner (or vice versa)
- SSH-ing to hosts for manual deploys instead of using Forgejo workflows
- Omitting `container_name` (makes monitoring and checksum gating unreliable)
- Adding `privileged: true` or `cap_add` without justification
- Exposing ports directly when Traefik routing is sufficient
