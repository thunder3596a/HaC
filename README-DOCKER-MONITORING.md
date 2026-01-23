# Label-Based Docker Container Monitoring System

## Quick Overview

This system provides **automatic, scalable Docker container monitoring** through Home Assistant using Docker labels. No hardcoded lists - just add labels to your compose files.

## Key Features

✅ **Zero Hardcoding** - No IPs or container names in code
✅ **Auto-Discovery** - Containers discovered via Docker labels
✅ **Secure** - All sensitive values in Forgejo variables/secrets
✅ **Scalable** - Add containers by just adding 4 labels
✅ **Dashboard** - Live status display with quick actions
✅ **Workflow Integration** - Update workflows read labels dynamically

## How to Use

### To Monitor a New Container

Add these 4 labels to your compose file:

```yaml
services:
  myapp:
    image: myapp:latest
    container_name: my-container
    labels:
      - ha.monitor=true
      - ha.category=tools
      - ha.compose-file=Docker-Critical/Tools/MyApp/myapp.yml
      - ha.service-name=myapp
```

Then restart: `docker compose up -d`

That's it! The container will automatically:
- Appear in Home Assistant sensors
- Show on the dashboard
- Be available for updates via workflows

## Documentation

- **[DOCKER-MONITORING-SETUP.md](DOCKER-MONITORING-SETUP.md)** - Complete technical setup guide
- **[FORGEJO-VARIABLES-SETUP.md](FORGEJO-VARIABLES-SETUP.md)** - Variables and secrets configuration
- **[../homeassistant/SETUP-DOCKER-MONITORING.md](../homeassistant/SETUP-DOCKER-MONITORING.md)** - Home Assistant configuration

## Files

### Docker Repository
- `scripts/get-docker-containers.sh` - Query Docker API for labeled containers
- `scripts/generate-container-sensors.py` - Generate HA sensor configs
- `scripts/add-labels-to-compose.sh` - Helper to add labels
- `.forgejo/workflows/apply-updates-critical.yml` - Update workflow (label-based)

### Home Assistant Repository
- `configuration.yaml` - Command line sensors for Docker
- `docker-dashboard.yaml` - Status dashboard with live updates
- `SETUP-DOCKER-MONITORING.md` - Setup instructions

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

## Security

- ❌ No private IPs in code
- ❌ No credentials in repository
- ✅ All secrets in Forgejo variables
- ✅ IPs passed via environment/secrets
- ✅ Tokens properly formatted and scoped

## Label Reference

| Label | Required | Purpose | Example |
|-------|----------|---------|---------|
| `ha.monitor` | Yes | Enable monitoring | `true` |
| `ha.category` | Yes | Dashboard grouping | `home`, `networking`, `tools` |
| `ha.compose-file` | Yes | Path to compose file | `Docker-Critical/Home/App/app.yml` |
| `ha.service-name` | Yes | Service name in compose | `myservice` |

## Status

### Completed
- ✅ Label-based architecture implemented
- ✅ Scripts created and documented
- ✅ Home Assistant sensors configured
- ✅ Dashboard created
- ✅ Workflow updated for label discovery
- ✅ Documentation written
- ✅ Security hardening (no IPs/creds in code)

### Next Steps
1. Add Forgejo variables (see FORGEJO-VARIABLES-SETUP.md)
2. Copy script to Home Assistant
3. Add labels to remaining compose files
4. Import dashboard to Home Assistant
5. Test workflows

## Benefits

**Before (Hardcoded):**
- Add container → Update workflow maps → Update sensors → Update dashboard
- IPs and credentials in code
- Error-prone manual tracking

**After (Label-Based):**
- Add container → Add 4 labels → Restart container
- Everything auto-discovered
- Secure, scalable, maintainable

## Support

Issues or questions:
- Check the documentation in this directory
- Review troubleshooting sections in setup guides
- Verify Forgejo variables are set correctly
- Test scripts manually to isolate issues

