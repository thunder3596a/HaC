# Home-Lab Docker Configuration

Complete Docker infrastructure for a self-hosted home automation and media center, organized into critical and non-critical services with automated deployment via Forgejo CI/CD.

## Architecture Overview

### Deployment Model
- **Git-based:** Configuration managed through Forgejo (self-hosted Git server)
- **Infrastructure as Code:** All services defined via Docker Compose
- **Automated Deployments:** Forgejo workflows trigger on file changes
- **Multi-Host:** Critical services on main home automation host, non-critical services distributed

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
docker/
├── .forgejo/workflows/          # Deployment automation (Forgejo Actions)
├── Docker-Critical/             # Mission-critical services
├── Docker-NonCritical/          # Non-essential services
├── Tools/                       # Utility configurations
├── MIGRATION.md                 # TrueNAS → Home Assistant migration guide
└── README.md                    # This file
```

---

## Docker-Critical Services

Services running on **docker-critical** (critical host).

**Storage layout on docker-critical:**
- `/srv` (NVMe #1) for critical configs and high-IO databases
- `/mnt/nvme-appdata` (NVMe #2) for appdata/search/AI tiers (NetBox, HomeBox, KaraKeep Meili, etc.)
- `/mnt/hdd` for backups/logs/archives (e.g., ZIM files, service logs)

### Authentication & Access Control
- **Authelia** (`authelia.yml`) - SSO and authentication
  - PostgreSQL backend for session storage
  - LLDAP for LDAP/Active Directory simulation
  - Traefik middleware integration for protected services

### Networking & Proxy
- **Traefik** (`proxy.yml`) - Reverse proxy and load balancer
  - HTTP/HTTPS with individual SSL certificates per domain
  - Dashboard at `docker-critical-traefik.${DOMAIN_NAME}`
  - Service discovery and routing
  
- **Omada Controller** (`omada.yml`) - TP-Link network management
  - WiFi and network device management
  - Dashboard at `omada.${DOMAIN_NAME}`

- **Postfix SMTP Relay** (`Postfix.yml`) - Email delivery
  - Relays outbound mail for internal services
  - Credentials via Forgejo secrets

- **Cloudflared** (`Cloudflared/cloudflared.yml`) - Cloudflare Tunnel
  - Secure external access without port forwarding
  - Automatic DNS and certificate management

### Home Automation Core
- **Home Assistant** (`HomeAssistant/homeassistant.yml`) - Home automation hub
  - Core automation and smart home control
  - Dashboard at `ha.${DOMAIN_NAME}`
  
- **ESPHome** (`HomeAssistant/homeassistant.yml`) - IoT device management
  - Firmware compilation for ESP8266/ESP32 devices
  - Dashboard at `esphome.${DOMAIN_NAME}`
  - Device-to-Home Assistant integration
  
- **RTL-SDR** (`RTL-SDR/rtl-sdr.yml`) - Software-defined radio receiver
  - 433 MHz and 915 MHz frequency monitoring
  - MQTT integration with Home Assistant
  - Weather station and sensor data decoding
  - Config: `/srv/rtl-sdr/`

- **Govee2MQTT** (`Govee2MQTT/govee2mqtt.yml`) - Govee device MQTT bridge
  - Integrates Govee lights and sensors with Home Assistant
  - MQTT-based control and monitoring
  
- **NUT (Network UPS Tools)** (`NUT/nut.yml`) - UPS monitoring
  - Battery backup monitoring and management
  - Automatic shutdown coordination
  
- **Whisper** (`Whisper/whisper.yml`) - Speech recognition
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
- **Kiwix** (`Tools/Kiwix/kiwix.yml`) - Offline content library
  - Wikipedia and documentation mirrors
  - Read-only media mount
  - Dashboard at `kiwix.${DOMAIN_NAME}`

- **KaraKeep** (`Home/KaraKeep/karakeep.yml`) - Media library management
  - Video collection organization
  - Meilisearch integration for full-text search
  - Dashboard at `kara.${DOMAIN_NAME}`

- **Music Assistant** (`Home/MusicAssistant/musicassistant.yml`) - Music server and player management
  - Unified music library from multiple providers (Spotify, Plex, Jellyfin, local files)
  - Multi-player support (Sonos, AirPlay, Google Cast, DLNA, etc.)
  - Local audio file streaming with quality selection
  - Host network mode for mDNS/player discovery
  - Dashboard at `music.${DOMAIN_NAME}`

### Finance
- **Actual Budget** (`Finance/finance.yml`) - Personal finance management
  - Budget tracking and expense management
  - Bank synchronization and reporting
  - Dashboard at `budget.${DOMAIN_NAME}`
  - Meilisearch integration for full-text search
  - Dashboard at `kara.${DOMAIN_NAME}`

- **Music Assistant** (`Home/MusicAssistant/musicassistant.yml`) - Music server and player management
  - Unified music library from multiple providers (Spotify, Plex, Jellyfin, local files)
  - Multi-player support (Sonos, AirPlay, Google Cast, DLNA, etc.)
  - Local audio file streaming with quality selection
  - Host network mode for mDNS/player discovery
  - Dashboard at `music.${DOMAIN_NAME}`

---

## Docker-NonCritical Services

Services running on **docker-noncritical** (non-critical host). Can restart without affecting home automation.

**Storage layout on docker-noncritical:**
- Per-service persistent data directories (local to host)

### Networking & Proxy
- **Traefik** (`Networking/Proxy/proxy.yml`) - Non-critical reverse proxy
  - Dashboard at `docker-noncritical-traefik.${DOMAIN_NAME}`

- **Gluetun** (via `torrent.yml`) - VPN/proxy container
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

### Media Center
- **Plex** (`Media/Plex/plex.yml`) - Media streaming server
  - Movies, TV shows, music streaming
  - Dashboard at `plex.${DOMAIN_NAME}`
  - Mounts media from `/mnt/Pool01/data/`

### Automation & Tools
- **Watchtower** (`Automation/watchtower.yml`) - Container image updates
  - Automatic Docker image updates
  - Selective service control via labels

- **ComfyUI** (`Automation/comfy.yaml`) - Stable Diffusion UI
  - Image generation interface
  - GPU acceleration support

- **Ollama** (`Automation/AI/ai.yml`) - Local LLM server
  - Run local language models
  - OpenAI-compatible API

- **Open WebUI** (`Automation/AI/aiportal.yml`) - LLM interface
  - Chat interface for Ollama

- **Price Tracker** (`Automation/pricetracker.yml`) - eCommerce monitoring
  - Price tracking and alerts

### Security
- **Crowdsec** (`Security/Crowdsec/crowdsec.yml`) - Threat detection
  - IDS/crowdsourced security
  - Log analysis and blocking

---

## Deployment

### Deployment Hosts

All services deploy via Forgejo CI/CD workflows in `.forgejo/workflows/`. Workflows select the appropriate runner based on service location:

**Critical services** → `runs-on: docker-critical`
**Non-critical services** → `runs-on: docker-noncritical`

| Service | Workflow | Host | Trigger |
|---------|----------|------|---------|
| Authelia | `deploy-authelia.yml` | docker-critical | Push to `Docker-Critical/Auth/**` |
| Traefik (Critical) | `deploy-traefik-critical.yml` | docker-critical | Push to `Docker-Critical/Networking/Proxy/**` |
| Traefik (NonCritical) | `deploy-traefik-noncritical.yml` | docker-noncritical | Push to `Docker-NonCritical/Networking/Proxy/**` |
| Home Assistant | `deploy-homeassistant.yml` | docker-critical | Push to `Docker-Critical/Home/HomeAssistant/**` |
| ESPHome | (included in HA) | docker-critical | Push to `Docker-Critical/Home/HomeAssistant/**` |
| RTL-SDR | `deploy-rtl-sdr.yml` | docker-critical | Push to `Docker-Critical/Home/RTL-SDR/**` |
| Music Assistant | `deploy-musicassistant.yml` | docker-critical | Push to `Docker-Critical/Home/MusicAssistant/**` |
| InfluxDB | `deploy-influxdb.yml` | docker-critical | Push to `Docker-Critical/Tools/InfluxDB/**` |
| NetBox | `deploy-netbox.yml` | docker-critical | Push to `Docker-Critical/Home/NetBox/**` |
| Norish | `deploy-norish.yml` | docker-critical | Push to `Docker-Critical/Home/Cooking/**` |
| Forgejo | `deploy-forgejo.yml` | docker-critical | Push to `Docker-Critical/Management/Git*/**` |
| Omada | `deploy-omada.yml` | docker-critical | Push to `Docker-Critical/Networking/Omada/**` |
| SMTP Relay | `deploy-smtprelay.yml` | docker-critical | Push to `Docker-Critical/Networking/Mail/**` |
| Plex | `deploy-plex.yml` | docker-noncritical | Push to `Docker-NonCritical/Media/Plex/**` |
| Radarr/Sonarr/etc | `deploy-*.yml` | docker-noncritical | Push to `Docker-NonCritical/Media/**` |
| Profilarr | `deploy-profilarr.yml` | docker-noncritical | Push to `Docker-NonCritical/Media/profilarr/**` |

### Required Forgejo Variables
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

---

## Data Locations

### Critical Services
Persistent data on primary host (tiered):
```
/srv/                      # NVMe #1 (critical + high IO)
├── authelia/              # SSO database and config
├── traefik/               # Reverse proxy config and ACME certs
├── git/                   # Forgejo repositories and config
├── homeassistant/         # HA config and automations
├── avahi/                 # mDNS reflection config
├── esphome/               # ESPHome device configs
├── rtl-sdr/               # RTL-SDR config and decoded data
├── music-assistant/       # Music Assistant data
├── influxdb/              # Time-series database and config
├── norish/                # Recipe database (app + DB + redis)
├── smtp-relay/            # Postfix spool
├── omada/                 # Controller data
└── git/                   # Forgejo data + Postgres

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
/var/lib/docker/volumes/   # Docker-managed volumes
/srv/ (optional)           # For higher IO services if available
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

---

## Service Dependencies

```
Traefik (Critical)
├── Authelia (authentication provider)
├── Omada (network dashboard)
├── Home Assistant (home automation hub)
│   ├── ESPHome (device management)
│   └── RTL-SDR (wireless sensors)
├── InfluxDB (metrics and historical data)
├── Music Assistant (music server and players)
├── NetBox (infrastructure docs)
├── Norish (recipes)
├── KaraKeep (media library)
└── Forgejo (git/CI)

Traefik (NonCritical)
├── Plex (media streaming)
├── Radarr/Sonarr/etc (media management)
├── Overseerr (media requests)
├── Ollama/WebUI (LLM services)
└── Others
```

---

## Security Notes

- **Split Horizon DNS:** Not needed - Unbound on OpnSense provides local DNS overrides
- **External Access:** Via Cloudflare Tunnel to avoid port forwarding
- **Authentication:** Authelia protects sensitive services
- **ACME:** Individual certificates per subdomain (no wildcard)
- **SSH:** Via Tailscale network for secure access

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


---

## License & Attribution
**Maintainer:** Nicholas Underwood
Personal home automation infrastructure. Configuration patterns based on best practices for self-hosted services.

---

**Last Updated:** January 31, 2026  
**Maintainer:** Nicholas Underwood
