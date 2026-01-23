# Docker Container Monitoring with Home Assistant

This document describes the label-based, scalable Docker container monitoring system.

## Overview

This system uses Docker labels to automatically discover and monitor containers. No hardcoded lists to maintain - just add labels to your compose files.

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

The [apply-updates-critical.yml](.forgejo/workflows/apply-updates-critical.yml) workflow now:
- Queries the Docker API for containers with `ha.monitor=true`
- Dynamically builds the COMPOSE_MAP and SERVICE_MAP from labels
- No hardcoded container lists needed!

### 4. Dashboard

The [docker-dashboard.yaml](../homeassistant/docker-dashboard.yaml) provides:
- Live status tables for both hosts
- Container names, status, images, and categories
- Quick action buttons to trigger updates

## Adding a New Container

To add a new container to monitoring:

1. Add the four `ha.*` labels to your compose file
2. Restart the container: `docker compose up -d`
3. That's it! It will automatically appear in:
   - Home Assistant sensors
   - The dashboard
   - Update workflows

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

### ha.monitor
**Required:** `true`
**Purpose:** Enables this container for Home Assistant monitoring

### ha.category
**Required:** string
**Purpose:** Groups containers in dashboard
**Examples:** `home`, `networking`, `auth`, `tools`, `media`, `management`

### ha.compose-file
**Required:** relative path
**Purpose:** Path to compose file from repo root
**Example:** `Docker-Critical/Home/HomeAssistant/homeassistant.yml`

### ha.service-name
**Required:** string
**Purpose:** The service name in the compose file (may differ from container name)
**Example:** For container `homeassistant-db`, service name is `mariadb`

## Files Modified

### Docker Repository
- Added labels to compose files:
  - [Docker-Critical/Home/HomeAssistant/homeassistant.yml](Docker-Critical/Home/HomeAssistant/homeassistant.yml)
  - [Docker-Critical/Networking/Proxy/proxy.yml](Docker-Critical/Networking/Proxy/proxy.yml)
  - (Add labels to remaining compose files as needed)

- [scripts/get-docker-containers.sh](scripts/get-docker-containers.sh) - Fetches container data from Docker API
- [.forgejo/workflows/apply-updates-critical.yml](.forgejo/workflows/apply-updates-critical.yml) - Updated to use labels

### Home Assistant Repository
- Updated [configuration.yaml](../homeassistant/configuration.yaml):
  - Added command_line sensors for Docker API
  - Sensors store container data as JSON attributes

- Created [docker-dashboard.yaml](../homeassistant/docker-dashboard.yaml):
  - Markdown tables showing all monitored containers
  - Status indicators and quick actions

## Next Steps

1. **Configure Forgejo Variables:**
   - See [FORGEJO-VARIABLES-SETUP.md](FORGEJO-VARIABLES-SETUP.md) for complete list
   - Add all required variables and secrets in Forgejo Repository Settings
   - This ensures no private IPs or credentials are in the code

2. **Copy the script to Home Assistant:**
   ```bash
   cp scripts/get-docker-containers.sh /srv/homeassistant/config/
   chmod +x /srv/homeassistant/config/get-docker-containers.sh
   ```

3. **Add labels to remaining compose files:**
   - Review all compose files in Docker-Critical/ and Docker-NonCritical/
   - Add the four `ha.*` labels to each container you want to monitor
   - Restart containers: `docker compose up -d`

3. **Import the dashboard in Home Assistant:**
   - Go to Settings → Dashboards
   - Create new dashboard or edit existing
   - Add yaml mode and paste content from docker-dashboard.yaml

4. **Test the workflow:**
   - Trigger the workflow from Forgejo Actions
   - Watch the output to see label-based discovery
   - Verify containers update correctly

## Benefits

- **Scalable:** Add containers by just adding labels
- **Maintainable:** Single source of truth (the compose files)
- **Flexible:** Easy to add new categories or metadata
- **Automatic:** Workflows discover containers dynamically
- **Organized:** Dashboard groups by category

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
2. Verify jq is installed on runner
3. Confirm Docker API is accessible from runner

