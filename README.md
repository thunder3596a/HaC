# Homelab-as-Code (HaC)

> **GitHub Mirror:** [github.com/thunder3596a/HaC](https://github.com/thunder3596a/HaC) — automatically synced from Forgejo via `mirror-to-github.yml`

Complete infrastructure-as-code for a self-hosted home automation and media center, organized into critical and non-critical services with automated deployment via Forgejo CI/CD. HaC stands for "Homelab-as-Code."

## Architecture Overview

### Deployment Model

- **Git-based:** Configuration managed through Forgejo (self-hosted Git server)
- **Infrastructure as Code:** All services defined via Docker Compose
- **Automated Deployments:** Forgejo workflows trigger on file changes
- **Multi-Host:** Two hosts — critical (home automation) and non-critical (media/tools)

### Network Structure

- **homeproxy:** Home services and automation (internal only)
- **mediaproxy:** Entertainment and media services
- **toolsproxy:** Backend utilities and infrastructure
- **torrentproxy:** Torrent/VPN services
- **aiproxy:** LLM and AI services
- **secproxy:** Security and monitoring
- **gitproxy:** Git infrastructure
- **authnet:** Privileged authentication services (LDAP, OAuth)

### Reverse Proxy

- **Traefik:** Two instances (critical and non-critical)
  - SSL termination via Let's Encrypt with Cloudflare DNS-01 challenge
  - Individual per-subdomain certificates
  - Automatic service discovery via Docker labels

---

## Repository Structure

```
HaC/
├── .forgejo/workflows/          # Deployment automation (Forgejo Actions)
├── Docker-Critical/             # Mission-critical services (hac-critical host)
├── Docker-NonCritical/          # Non-essential services (hac-noncritical host)
├── docs/                        # Supplemental documentation and guides
├── scripts/                     # Utility scripts
└── README.md                    # This file
```

---

## HaC-Critical Services

Services running on **hac-critical** (critical host).

**Storage layout on hac-critical:**

- `/srv` (NVMe #1) for critical configs and high-IO databases
- `/mnt/nvme-appdata` (NVMe #2) for appdata/search/AI tiers (NetBox, HomeBox, KaraKeep Meili, etc.)
- `/mnt/hdd` for backups/logs/archives (e.g., ZIM files, service logs)

### Authentication & Access Control

- **Authelia** (`Auth/Authelia.yml`) - SSO and authentication
  - PostgreSQL backend for session storage
  - LLDAP for LDAP/Active Directory simulation
  - Traefik middleware integration for protected services

### Networking & Proxy

- **Traefik** (`Networking/Proxy/proxy.yml`) - Reverse proxy and load balancer
  - HTTP/HTTPS with individual SSL certificates per domain
  - Dashboard at `hac-critical-traefik.${DOMAIN_NAME}`
  - Service discovery and routing

- **Omada Controller** (`Networking/Omada/omada.yml`) - TP-Link network management
  - WiFi and network device management
  - Dashboard at `omada.${DOMAIN_NAME}`

- **Postfix SMTP Relay** (`Networking/Mail/Postfix.yml`) - Email delivery
  - Relays outbound mail for internal services
  - Credentials via Forgejo secrets

- **Cloudflared** (`Networking/Cloudflared/cloudflared.yml`) - Cloudflare Tunnel
  - Secure external access without port forwarding
  - Automatic DNS and certificate management

### Home Automation Core

- **Home Assistant** (`Home/HomeAssistant/homeassistant.yml`) - Home automation hub
  - Core automation and smart home control
  - Dashboard at `ha.${DOMAIN_NAME}`

- **ESPHome** (`Home/HomeAssistant/homeassistant.yml`) - IoT device management
  - Firmware compilation for ESP8266/ESP32 devices
  - Dashboard at `esphome.${DOMAIN_NAME}`
  - Device-to-Home Assistant integration

- **RTL-SDR** (`Home/RTL-SDR/rtl-sdr.yml`) - Software-defined radio receiver
  - 433 MHz and 915 MHz frequency monitoring
  - MQTT integration with Home Assistant
  - Weather station and sensor data decoding
  - Config: `/srv/rtl-sdr/`

- **Govee2MQTT** (`Home/Govee2MQTT/govee2mqtt.yml`) - Govee device MQTT bridge
  - Integrates Govee lights and sensors with Home Assistant
  - MQTT-based control and monitoring

- **NUT (Network UPS Tools)** (`Home/NUT/nut.yml`) - UPS monitoring
  - Battery backup monitoring and management
  - Automatic shutdown coordination

- **Whisper** (`Home/Whisper/whisper.yml`) - Speech recognition
  - Local speech-to-text processing
  - Privacy-focused voice assistant integration

### Infrastructure Services

- **Forgejo** (`Management/Git - Forgejo/git.yml`) - Self-hosted Git server
  - Repository hosting and Git service
  - CI/CD Actions runners
  - Dashboard at `git.${DOMAIN_NAME}`
  - PostgreSQL backend

- **NetBox** (`Home/NetBox/netbox.yml`) - Network documentation
  - IP address management (IPAM)
  - Device and network inventory
  - Custom theming via sage-green theme
  - PostgreSQL + Redis backends
  - Dashboard at `netbox.${DOMAIN_NAME}`

### Data & Monitoring

- **InfluxDB** (`Tools/InfluxDB/influxdb.yml`) - Time-series database
  - Stores metrics and sensor data from Home Assistant
  - Historical data archival and analysis
  - Flux query language for complex aggregations
  - Dashboard at `influx.${DOMAIN_NAME}`

- **Docker Socket Proxy** (`Tools/DockerSocketProxy/docker-socket-proxy.yml`) - Secure Docker API access
  - Restricts Docker socket access for Traefik and monitoring
  - Security layer for Docker daemon

- **N8N** (`Tools/N8N/n8n.yml`) - Workflow automation
  - No-code automation platform
  - Integration with external APIs and services
  - Dashboard at `n8n.${DOMAIN_NAME}`

### Home Services

- **Norish** (`Home/Cooking/norish.yml`) - Recipe manager
  - Recipe collection and meal planning
  - Web page recipe clipping with headless Chrome
  - OIDC authentication via Authelia
  - PostgreSQL + Redis backends
  - Dashboard at `norish.${DOMAIN_NAME}`

- **KaraKeep** (`Home/KaraKeep/karakeep.yml`) - Bookmark manager
  - Save and organize bookmarks and links
  - Web page archiving and screenshots
  - Meilisearch integration for full-text search
  - Dashboard at `kara.${DOMAIN_NAME}`

- **Music Assistant** (`Home/MusicAssistant/musicassistant.yml`) - Music server and player management
  - Unified music library from multiple providers (Spotify, Plex, Jellyfin, local files)
  - Multi-player support (Sonos, AirPlay, Google Cast, DLNA, etc.)
  - Local audio file streaming with quality selection
  - Host network mode for mDNS/player discovery
  - Dashboard at `music.${DOMAIN_NAME}`

- **Vikunja** (`Home/Vikunja/vikunja.yml`) - Task management
  - Self-hosted task hub (Todoist/Trello alternative)
  - CalDAV support for iOS Reminders sync
  - PostgreSQL backend
  - MCP server for Claude Code integration
  - Dashboard at `tasks.${DOMAIN_NAME}`

- **HomeBox** (`Management/HomeBox/homebox.yml`) - Home inventory management
  - Track household items and their locations
  - Asset management and organization
  - Dashboard at `homebox.${DOMAIN_NAME}`

- **Kiwix** (`Tools/Kiwix/kiwix.yml`) - Offline Wikipedia mirror
  - Wikipedia and documentation archives
  - Read-only ZIM file mount
  - Dashboard at `wikipedia.${DOMAIN_NAME}`

- **Doomsday Library** (`Home/Doomsday/library.yml`) - Offline content library
  - Additional offline content archives
  - Kiwix-serve for ZIM files
  - Dashboard at `library.${DOMAIN_NAME}`

---

## HaC-NonCritical Services

Services running on **hac-noncritical** (non-critical host). Can restart without affecting home automation.

**Storage layout on hac-noncritical:**

- Per-service persistent data directories (local to host)

### Networking, Proxy & VPN

- **Traefik** (`Networking/Proxy/proxy.yml`) - Non-critical reverse proxy
  - Dashboard at `hac-noncritical-traefik.${DOMAIN_NAME}`

- **Gluetun** (via `Networking/Torrent/torrent.yml`) - VPN/proxy container
  - Network namespace for torrent services
  - Supports multiple VPN providers

### Media Stack (Entertainment)

#### Request & Discovery

- **Overseerr** (`Media/overseerr/overseerr.yml`) - Media request platform
  - User-friendly movie/TV show requests
  - Integrates with Radarr/Sonarr

#### Indexing & Search

- **Prowlarr** (`Media/prowlarr/prowlarr.yml`) - Torrent indexer manager
  - Torrent site management and search
  - Unified interface for Radarr/Sonarr

- **Profilarr** (`Media/profilarr/profilarr.yml`) - Profile management
  - Radarr/Sonarr quality profile sync

#### Media Download & Organization

- **Radarr** (`Media/radarr/radarr.yml`) - Movie management
  - Automated movie downloads
  - Library organization and monitoring

- **Sonarr** (`Media/Sonarr/sonarr.yml`) - TV show management
  - Episode tracking and downloading
  - Season monitoring

- **Lidarr** (`Media/lidarr/lidarr.yml`) - Music management
  - Music library automation
  - Artist and album monitoring

- **Readarr** (`Media/readarr/readarr.yml`) - Book management
  - eBook and audiobook tracking

#### Download Clients

- **qBittorrent** (via `Networking/Torrent/torrent.yml`) - Torrent client
  - Download management
  - Behind Gluetun VPN tunnel

- **NZBGet** (via `Networking/Torrent/torrent.yml`) - Usenet client
  - Usenet download support

#### Utilities

- **FlareSolverr** (`Media/flaresolverr/flaresolverr.yml`) - CloudFlare bypass
  - Resolves CloudFlare-protected indexer sites
  - API for Radarr/Sonarr integration

- **Dispatcharr** (`Media/Dispatcharr/dispatcharr.yml`) - Notification router
  - Routes Radarr/Sonarr notifications

### Photos & Media

- **Immich** (`Media/Immich/immich.yml`) - Photo and video management
  - Self-hosted Google Photos alternative
  - Machine learning for facial recognition and search
  - PostgreSQL (with pgvecto.rs) + Valkey backends
  - Dashboard at `media.${DOMAIN_NAME}`

### Books & Audiobooks

- **Audiobookshelf** (`Media/Books/ebook.yml`) - Audiobook and podcast server
  - Self-hosted audiobook streaming
  - Podcast management
  - Dashboard at `audiobooks.${DOMAIN_NAME}`

- **Kavita** (`Media/Books/ebook.yml`) - eBook and comic reader
  - Digital library for books, comics, manga
  - Web-based reader interface
  - Dashboard at `kavita.${DOMAIN_NAME}`

### Media Center

- **Plex** (`Media/Plex/plex.yml`) - Media streaming server
  - Movies, TV shows, music streaming
  - Dashboard at `plex.${DOMAIN_NAME}`
  - Mounts media from `/mnt/Pool01/data/`

### Automation & AI

- **Open WebUI** (`Automation/AI/openwebui.yml`) - LLM interface
  - Chat interface for Ollama
  - Dashboard at `chat.${DOMAIN_NAME}`

- **Price Tracker** (`Automation/pricetracker.yml`) - eCommerce monitoring
  - Price tracking and alerts

### Tools

- **IT-Tools** (`Tools/IT-Tools/it-tools.yml`) - Developer utilities
  - Collection of handy developer tools
  - Dashboard at `it-tools.${DOMAIN_NAME}`

- **SearXNG** (`Tools/SearX/searx.yml`) - Privacy-focused metasearch
  - Self-hosted search engine
  - Aggregates results from multiple sources
  - Dashboard at `search.${DOMAIN_NAME}`

- **Stirling-PDF** (`Tools/Stirling-PDF/stirling-pdf.yml`) - PDF toolkit
  - PDF manipulation and conversion
  - Merge, split, compress, OCR
  - Dashboard at `pdf.${DOMAIN_NAME}`

- **MCP Gateway** (`Tools/MCPGateway/mcpgateway.yml`) - Model Context Protocol hub
  - Central gateway for MCP servers
  - Integrations: Home Assistant, OPNsense, NetBox, n8n, Omada, HomeBox, Vikunja
  - Dashboard at `mcp.${DOMAIN_NAME}`

- **Docker Socket Proxy** (`Tools/DockerSocketProxy/docker-socket-proxy.yml`) - Secure Docker API access
  - Non-critical instance for Traefik and monitoring

### Security

- **Crowdsec** (`Security/Crowdsec/crowdsec.yml`) - Threat detection
  - IDS/crowdsourced security
  - Log analysis and blocking

- **Wazuh** (`Security/security.yaml`) - SIEM and threat detection
  - Wazuh Manager, Indexer (OpenSearch), and Dashboard
  - Agent-based endpoint monitoring
  - Syslog ingestion and log analysis
  - 30-day index retention via ISM policy
  - Dashboard at `wazuh.${DOMAIN_NAME}`

---

## Deployment

### Deployment Hosts

All services deploy via Forgejo CI/CD workflows in `.forgejo/workflows/`. Workflows select the appropriate runner based on service location:

**Critical services** → `runs-on: docker-critical`
**Non-critical services** → `runs-on: docker-noncritical`

| Service | Workflow | Host | Trigger |
| --------- | ---------- | ------------- | ----------------------------------------- |
| Authelia | `deploy-authelia.yml` | hac-critical | Push to `Docker-Critical/Auth/**` |
| Traefik (Critical) | `deploy-traefik-critical.yml` | hac-critical | Push to `Docker-Critical/Networking/Proxy/**` |
| Traefik (NonCritical) | `deploy-traefik-noncritical.yml` | hac-noncritical | Push to `Docker-NonCritical/Networking/Proxy/**` |
| Home Assistant | `deploy-homeassistant.yml` | hac-critical | Push to `Docker-Critical/Home/HomeAssistant/**` |
| ESPHome | (included in HA) | hac-critical | Push to `Docker-Critical/Home/HomeAssistant/**` |
| RTL-SDR | `deploy-rtl-sdr.yml` | hac-critical | Push to `Docker-Critical/Home/RTL-SDR/**` |
| Music Assistant | `deploy-musicassistant.yml` | hac-critical | Push to `Docker-Critical/Home/MusicAssistant/**` |
| Govee2MQTT | `deploy-govee2mqtt.yml` | hac-critical | Push to `Docker-Critical/Home/Govee2MQTT/**` |
| NUT | `deploy-nut.yml` | hac-critical | Push to `Docker-Critical/Home/NUT/**` |
| Whisper | `deploy-whisper.yml` | hac-critical | Push to `Docker-Critical/Home/Whisper/**` |
| InfluxDB | `deploy-influxdb.yml` | hac-critical | Push to `Docker-Critical/Tools/InfluxDB/**` |
| N8N | `deploy-n8n.yml` | hac-critical | Push to `Docker-Critical/Tools/N8N/**` |
| NetBox | `deploy-netbox.yml` | hac-critical | Push to `Docker-Critical/Home/NetBox/**` |
| Norish | `deploy-norish.yml` | hac-critical | Push to `Docker-Critical/Home/Cooking/**` |
| KaraKeep | `deploy-karakeep.yml` | hac-critical | Push to `Docker-Critical/Home/KaraKeep/**` |
| HomeBox | `deploy-homebox.yml` | hac-critical | Push to `Docker-Critical/Management/HomeBox/**` |
| Vikunja | `deploy-vikunja.yml` | hac-critical | Push to `Docker-Critical/Home/Vikunja/**` |
| Kiwix | `deploy-kiwix.yml` | hac-critical | Push to `Docker-Critical/Tools/Kiwix/**` |
| Forgejo | `deploy-forgejo.yml` | hac-critical | Push to `Docker-Critical/Management/Git*/**` |
| Omada | `deploy-omada.yml` | hac-critical | Push to `Docker-Critical/Networking/Omada/**` |
| SMTP Relay | `deploy-smtprelay.yml` | hac-critical | Push to `Docker-Critical/Networking/Mail/**` |
| Cloudflared | `deploy-cloudflared.yml` | hac-critical | Push to `Docker-Critical/Networking/Cloudflared/**` |
| Docker Socket Proxy (Critical) | `deploy-docker-socket-proxy-critical.yml` | hac-critical | Push to `Docker-Critical/Tools/DockerSocketProxy/**` |
| Plex | `deploy-plex.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/Plex/**` |
| Immich | `deploy-immich.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/Immich/**` |
| Radarr | `deploy-radarr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/radarr/**` |
| Sonarr | `deploy-sonarr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/Sonarr/**` |
| Lidarr | `deploy-lidarr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/lidarr/**` |
| Readarr | `deploy-readarr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/readarr/**` |
| Overseerr | `deploy-overseerr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/overseerr/**` |
| Prowlarr | `deploy-prowlarr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/prowlarr/**` |
| Profilarr | `deploy-profilarr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/profilarr/**` |
| Dispatcharr | `deploy-dispatcharr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/Dispatcharr/**` |
| FlareSolverr | `deploy-flaresolverr.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/flaresolverr/**` |
| Books (ebook) | `deploy-ebook.yml` | hac-noncritical | Push to `Docker-NonCritical/Media/Books/**` |
| Torrent Stack | `deploy-torrent.yml` | hac-noncritical | Push to `Docker-NonCritical/Networking/Torrent/**` |
| Open WebUI | `deploy-openwebui-noncritical.yml` | hac-noncritical | Push to `Docker-NonCritical/Automation/AI/**` |
| IT-Tools | `deploy-it-tools.yml` | hac-noncritical | Push to `Docker-NonCritical/Tools/IT-Tools/**` |
| SearXNG | `deploy-searx.yml` | hac-noncritical | Push to `Docker-NonCritical/Tools/SearX/**` |
| Stirling-PDF | `deploy-stirling-pdf.yml` | hac-noncritical | Push to `Docker-NonCritical/Tools/Stirling-PDF/**` |
| MCP Gateway | `deploy-mcpgateway.yml` | hac-noncritical | Push to `Docker-NonCritical/Tools/MCPGateway/**` |
| Docker Socket Proxy (NC) | `deploy-docker-socket-proxy-noncritical.yml` | hac-noncritical | Push to `Docker-NonCritical/Tools/DockerSocketProxy/**` |
| Wazuh | `deploy-wazuh.yml` | hac-noncritical | Push to `Docker-NonCritical/Security/**` |
| CrowdSec | (via Wazuh workflow or manual) | hac-noncritical | Push to `Docker-NonCritical/Security/Crowdsec/**` |

**Maintenance workflows:**

| Workflow | Purpose |
| ----------------------- | -------------------------------------------- |
| `check-updates-critical.yml` | Check for container image updates (critical) |
| `check-updates-noncritical.yml` | Check for container image updates (non-critical) |
| `apply-updates-critical.yml` | Apply container image updates (critical) |
| `apply-updates-noncritical.yml` | Apply container image updates (non-critical) |
| `mirror-to-github.yml` | Mirror repository to GitHub |

### Required Forgejo Variables

> See [docs/forgejo-variables.md](docs/forgejo-variables.md) for full details and troubleshooting.

Global variables (set in repository settings):

- `DOMAIN_NAME` - Primary domain (e.g., `example.com`)
- `CERTRESOLVER` - Certificate resolver (default: `cloudflare`)
- `PUID` / `PGID` - User/group IDs for linuxserver images (default: `568`)
- `TZ` - Timezone (default: `America/Chicago`)
- `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER` - MQTT broker details
- `POSTGRES_USER`, `POSTGRES_DB` - PostgreSQL defaults
- `OLLAMA_BASE_URL` - Ollama LLM server URL
- `INFERENCE_*` - Model selection for KaraKeep AI features
- `INFLUXDB_ADMIN_USER` - InfluxDB admin username (default: `admin`)

### Required Forgejo Secrets

Encrypted secrets (set in repository settings):

- `CLOUDFLARE_EMAIL`, `CLOUDFLARE_DNS_API_TOKEN` - Cloudflare DNS for ACME
- `CLOUDFLARE_ZONE_API_TOKEN` - Zone API token
- `LETS_ENCRYPT_EMAIL` - Let's Encrypt contact
- `AUTHELIA_DB_PASSWORD` - Authelia PostgreSQL password
- `GIT_DB_PASSWORD` - Forgejo PostgreSQL password
- `NETBOX_DB_PASSWORD`, `NETBOX_SECRET_KEY` - NetBox secrets
- `PLEX_CLAIM` - Plex initial setup token
- `MQTT_PASSWORD` - MQTT broker password
- `PROFILARR_PAT` - Profilarr API token
- `SMTP_*` - SMTP relay credentials
- `INFLUXDB_ADMIN_PASSWORD` - InfluxDB admin password
- `IMMICH_DB_PASSWORD` - Immich PostgreSQL password
- `WAZUH_INDEXER_PASSWORD` - Wazuh OpenSearch password
- `WAZUH_API_PASSWORD` - Wazuh API password
- `VIKUNJA_DB_PASSWORD` - Vikunja PostgreSQL password
- `VIKUNJA_JWT_SECRET` - Vikunja JWT signing secret
- `VIKUNJA_API_TOKEN` - Vikunja API token (for MCP + N8N integrations)

---

## Data Locations

### Critical Services

Persistent data on primary host (tiered):

```
/srv/                      # NVMe #1 (critical + high IO)
├── authelia/              # SSO database and config
├── traefik/               # Reverse proxy config and ACME certs
├── homeassistant/         # HA config and automations
├── avahi/                 # mDNS reflection config
├── esphome/               # ESPHome device configs
├── rtl-sdr/               # RTL-SDR config and decoded data
├── music-assistant/       # Music Assistant data
├── influxdb/              # Time-series database and config
├── norish/                # Recipe database (app + DB + redis)
├── smtp-relay/            # Postfix spool
├── omada/                 # Controller data
├── vikunja/               # Vikunja files + Postgres
└── git/                   # Forgejo repositories, data + Postgres

/mnt/nvme-appdata/         # NVMe #2 (appdata/search/AI)
├── netbox/                # IPAM app, Postgres, Redis, theme
├── homebox/               # HomeBox data/config
└── karakeep/              # KaraKeep data + Meilisearch

/mnt/hdd/                  # HDD (bulk/logs/archives)
├── logs/omada             # Omada logs
├── logs/smtp-relay        # Postfix logs
├── kiwix/zim              # Kiwix ZIM archives
└── backups/               # Cold backups/archives
```

### Non-Critical Services

Persistent data on docker-noncritical:

```
/srv/                      # High IO services
├── immich/                # Immich Postgres + ML model cache
├── openwebui_data/        # Open WebUI data
└── wazuh/                 # Wazuh indexer data + dashboard config

/mnt/data/                 # NFS/shared storage
├── family/upload/         # Immich photo uploads
├── family/external/       # Immich external libraries
└── wazuh/archives/        # Wazuh log archives

/var/lib/docker/volumes/   # Docker-managed volumes
[per-service mounts]       # Absolute paths per compose file
```

### Media (Shared Storage)

```
/mnt/Pool01/data/media/
├── movies/               # Radarr downloads
├── tv/                   # Sonarr downloads
├── music/                # Lidarr downloads
└── books/                # Readarr downloads
```

---

## Migration

See [MIGRATION.md](Docker-Critical/MIGRATION.md) for detailed instructions on migrating services from TrueNAS to Home Assistant.

**Quick start:**

```bash
# Run migration script
ssh user@homeassistant
chmod +x migrate-to-homeassistant.sh
sudo ./migrate-to-homeassistant.sh
```

---

## Development & Customization

### Adding a New Service

1. **Create compose file** in appropriate folder:

   ```yaml
   Docker-Critical/Home/MyService/myservice.yml
   ```

2. **Define service** with:
   - Network specification (homeproxy, mediaproxy, etc.)
   - Environment variables (use `${VAR}` placeholders)
   - Traefik labels for routing
   - Volume mounts with absolute paths
   - Health checks

3. **Create deployment workflow** in `.forgejo/workflows/`:

   ```yaml
   name: Deploy MyService
   on:
     push:
       paths:
         - "Docker-Critical/Home/MyService/**"
         - ".forgejo/workflows/deploy-myservice.yml"
   ```

4. **Test locally**:

   ```bash
   docker compose -p myservice -f myservice.yml up -d
   ```

5. **Commit and push** - workflow triggers automatically

### Modifying Existing Service

- Edit the `.yml` file
- Update workflow if paths change
- Commit to main branch
- Workflow automatically redeploys with checksum validation

### Configuration Best Practices

- Never hardcode secrets (use `${SECRET_NAME}`)
- Use external networks (no inline network creation)
- Set `restart: unless-stopped` policy
- Include health checks for critical services
- Traefik labels always for HTTP services
- Watchtower label `com.centurylinklabs.watchtower.enable=true` for auto-updates
- HA monitoring labels (`ha.monitor`, `ha.category`, `ha.compose-file`, `ha.service-name`) for Home Assistant tracking — see [docs/docker-monitoring.md](docs/docker-monitoring.md)

---

## Service Dependencies

```
Traefik (Critical)
├── Authelia (authentication provider)
├── Omada (network dashboard)
├── Home Assistant (home automation hub)
│   ├── ESPHome (device management)
│   ├── RTL-SDR (wireless sensors)
│   └── Govee2MQTT (Govee devices)
├── InfluxDB (metrics and historical data)
├── Music Assistant (music server and players)
├── NetBox (infrastructure docs)
├── Norish (recipes)
├── KaraKeep (bookmarks)
├── HomeBox (inventory)
├── Vikunja (task management)
└── Forgejo (git/CI)

Traefik (NonCritical)
├── Plex (media streaming)
├── Immich (photo management)
├── Radarr/Sonarr/etc (media management)
├── Overseerr (media requests)
├── Open WebUI (LLM chat)
├── Wazuh (SIEM)
├── MCP Gateway (MCP hub)
└── Tools (IT-Tools, SearXNG, Stirling-PDF)
```

---

## Security Notes

- **Split Horizon DNS:** Not needed - Unbound on OpnSense provides local DNS overrides
- **External Access:** Via Cloudflare Tunnel to avoid port forwarding
- **Authentication:** Authelia protects sensitive services
- **ACME:** Individual certificates per subdomain (no wildcard)
- **SSH:** Via Tailscale network for secure access
- **SIEM:** Wazuh for endpoint monitoring and log analysis

---

## Troubleshooting

### Service won't start

```bash
# Check logs
docker logs <container-name>

# Verify compose file
docker compose -f <service>.yml config

# Check network exists
docker network ls | grep proxy
```

### Traefik routing issues

```bash
# Check router config
docker logs traefik | grep router

# Verify service labels
docker inspect <service> | grep traefik
```

### Permissions errors

```bash
# Verify ownership
ls -la /srv/<service>/

# Fix permissions
sudo chown -R 568:568 /srv/<service>/
```

---

## License & Attribution

Personal home automation infrastructure. Configuration patterns based on best practices for self-hosted services.

---

**Last Updated:** February 24, 2026
**Maintainer:** Nicholas Underwood
