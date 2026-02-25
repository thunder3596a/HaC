# Docker Container Monitoring with Home Assistant

This document describes the label-based, scalable Docker container monitoring system.

## Overview

This system uses Docker labels to automatically discover and monitor containers. No hardcoded lists to maintain — just add labels to your compose files.

## How It Works

### 1. Docker Labels

Each container you want to monitor needs these labels in its compose file:

```yaml
labels:
  - ha.monitor=true                    # Enable monitoring
  - ha.category=home                   # Category for grouping (home, networking, auth, etc.)
  - ha.compose-file=Docker-Critical/Home/HomeAssistant/homeassistant.yml
  - ha.service-name=homeassistant      # The actual service name in compose
```

### 2. Home Assistant Sensors

Two command_line sensors query the Docker API and filter for containers with `ha.monitor=true`:

- `sensor.docker_critical_containers_json` - Monitors critical Docker host
- `sensor.docker_noncritical_containers_json` - Monitors noncritical Docker host

These sensors:
- Show the count of monitored containers as their state
- Store full container details (name, status, image, category, etc.) as JSON attributes
- Update every 60 seconds

### 3. Forgejo Workflow

The [apply-updates-critical.yml](../.forgejo/workflows/apply-updates-critical.yml) workflow:
- Queries the Docker API for containers with `ha.monitor=true`
- Dynamically builds the COMPOSE_MAP and SERVICE_MAP from labels
- No hardcoded container lists needed

### 4. Dashboard

The `docker-dashboard.yaml` (in the Home Assistant repo) provides:
- Live status tables for both hosts
- Container names, status, images, and categories
- Quick action buttons to trigger updates

## Adding a New Container

To add a new container to monitoring:

1. Add the four `ha.*` labels to your compose file
2. Restart the container: `docker compose up -d`
3. That's it! It will automatically appear in Home Assistant sensors, the dashboard, and update workflows.

Example:

```yaml
services:
  myservice:
    image: myimage:latest
    container_name: my-container
    labels:
      - ha.monitor=true
      - ha.category=tools
      - ha.compose-file=Docker-Critical/Tools/MyService/myservice.yml
      - ha.service-name=myservice
```

## Label Reference

| Label | Required | Purpose | Example |
|-------|----------|---------|---------|
| `ha.monitor` | Yes | Enable monitoring | `true` |
| `ha.category` | Yes | Dashboard grouping | `home`, `networking`, `tools` |
| `ha.compose-file` | Yes | Path to compose file from repo root | `Docker-Critical/Home/App/app.yml` |
| `ha.service-name` | Yes | Service name in compose (may differ from container name) | `myservice` |

## Architecture

```
Docker Compose Files
    ↓ (labels: ha.monitor, ha.category, ha.compose-file, ha.service-name)
    ↓
Docker API (queries for ha.monitor=true)
    ↓
Home Assistant Sensors (store as JSON attributes)
    ↓
Dashboard (displays live status)
    ↓
Forgejo Workflows (update containers via labels)
```

## Before / After

**Before (Hardcoded):**
- Add container → Update workflow maps → Update sensors → Update dashboard
- IPs and credentials in code
- Error-prone manual tracking

**After (Label-Based):**
- Add container → Add 4 labels → Restart container
- Everything auto-discovered
- Secure, scalable, maintainable

## Files

### HaC Repository
- `scripts/get-docker-containers.sh` — Query Docker API for labeled containers
- `scripts/generate-container-sensors.py` — Generate HA sensor configs
- `scripts/add-labels-to-compose.sh` — Helper to add labels
- `.forgejo/workflows/apply-updates-critical.yml` — Update workflow (label-based)

### Home Assistant Repository
- `configuration.yaml` — Command line sensors for Docker
- `docker-dashboard.yaml` — Status dashboard with live updates

## Next Steps

1. **Configure Forgejo Variables** — see [forgejo-variables.md](forgejo-variables.md) for complete list
2. **Copy script to Home Assistant:**
   ```bash
   cp scripts/get-docker-containers.sh /srv/homeassistant/config/
   chmod +x /srv/homeassistant/config/get-docker-containers.sh
   ```
3. **Add labels to remaining compose files** — review all compose files in `Docker-Critical/` and `Docker-NonCritical/`, restart containers after
4. **Import dashboard in Home Assistant** — Settings → Dashboards → add YAML mode, paste `docker-dashboard.yaml` content
5. **Test the workflow** — trigger from Forgejo Actions, watch for "Registered:" messages

## Troubleshooting

### Container not appearing in Home Assistant

1. Verify labels are present:
   ```bash
   docker inspect container-name | jq '.Config.Labels'
   ```

2. Check if sensor is updating:
   - Go to Developer Tools → States
   - Find `sensor.docker_critical_containers_json`
   - Check the `containers` attribute

3. Verify the script works:
   ```bash
   /config/get-docker-containers.sh http://DOCKER_HOST_IP:2375
   ```

### Workflow not finding containers

1. Check workflow logs for "Registered:" messages
2. Verify `jq` is installed on the runner
3. Confirm Docker API is accessible from the runner
