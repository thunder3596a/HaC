# Wazuh Stack Setup Guide

## Overview

This Wazuh stack has been simplified to use **Traefik for SSL termination** and disable internal SSL requirements. No manual certificate generation needed!

## Architecture

- **wazuh.indexer** - OpenSearch-based indexer for storing security events
- **wazuh.manager** - Main Wazuh manager for agent management and security analysis
- **wazuh.dashboard** - Web UI accessible via Traefik at `https://wazuh.${DOMAIN_NAME}`

## Forgejo Variables

Go to: Repository Settings → Actions → Variables

### Required Variables
| Variable Name | Description | Recommended Value |
|--------------|-------------|-------------------|
| `DOMAIN_NAME` | Your domain name | Already configured |
| `CERTRESOLVER` | Traefik cert resolver | Already configured (typically `cloudflare`) |

### Optional Variables
| Variable Name | Description | Default Value |
|--------------|-------------|---------------|
| `WAZUH_VERSION` | Wazuh version to deploy | `4.14.3` |
| `WAZUH_INDEXER_USERNAME` | Indexer admin username | `admin` |
| `WAZUH_API_USERNAME` | Wazuh API username | `wazuh-wui` |

## Forgejo Secrets

Go to: Repository Settings → Actions → Secrets

Add the following secrets (use strong, unique passwords):

| Secret Name | Description | Notes |
|------------|-------------|-------|
| `WAZUH_INDEXER_PASSWORD` | Password for the indexer admin user | Min 8 characters, use strong password |
| `WAZUH_API_PASSWORD` | Password for Wazuh API access | Min 8 characters, use strong password |

**Note:** `WAZUH_DASHBOARD_PASSWORD` is NOT needed - the dashboard uses the API password.

## What Changed from the Old Config?

✅ **Simplified:**
- ❌ No SSL certificates to generate
- ❌ No config files required
- ❌ No complex internal SSL setup
- ✅ Traefik handles all SSL (using your existing Let's Encrypt setup)
- ✅ HTTP used for internal Docker network communication (secure by default)
- ✅ Auto-updates via Watchtower
- ✅ Resource limits added
- ✅ Updated to latest stable version (4.14.3)

## Deployment

### Option 1: Automatic Deployment (Recommended)

A Forgejo workflow is configured to automatically deploy when you push changes:
- **Workflow:** `.forgejo/workflows/deploy-wazuh.yml`
- **Triggers:**
  - Push to `main` branch affecting `Docker-NonCritical/Security/**`
  - Manual workflow dispatch

To manually trigger deployment:
1. Go to Forgejo → Actions → Workflows
2. Select "Deploy Wazuh"
3. Click "Run workflow"

### Option 2: Manual Deployment

```bash
cd Docker-NonCritical/Security
docker-compose -f security.yaml up -d
```

**Note:** You'll need to export the required environment variables first if deploying manually.

## Access

- **Dashboard URL:** `https://wazuh.${DOMAIN_NAME}`
- **Username:** Value of `WAZUH_API_USERNAME` (default: `wazuh-wui`)
- **Password:** Value of `WAZUH_API_PASSWORD`

## Agent Communication Ports

The following ports are exposed for Wazuh agent communication:
- **1514** - Wazuh agent communication
- **1515** - Wazuh agent enrollment
- **514/udp** - Syslog
- **55000** - Wazuh API (also used by dashboard)

## Resource Requirements

- **wazuh.indexer**: 1-2GB RAM, 0.5-2 CPU cores
- **wazuh.manager**: 512MB-2GB RAM, 0.5-2 CPU cores
- **wazuh.dashboard**: 256MB-1GB RAM, 0.25-1 CPU cores

**Total:** ~2-5GB RAM recommended

## Troubleshooting

### Dashboard shows "Wazuh API is not reachable"
- Wait 2-3 minutes after startup for all services to initialize
- Check that wazuh.manager is running: `docker ps | grep wazuh-manager`
- Check manager logs: `docker logs wazuh-manager`

### "Authentication failed" on login
- Verify `WAZUH_API_PASSWORD` secret is set correctly in Forgejo
- Default username is `wazuh-wui` (unless you changed `WAZUH_API_USERNAME`)

### Indexer fails to start
- Check available memory: `docker stats`
- Indexer requires at least 1GB RAM
- Check logs: `docker logs wazuh-indexer`

### SSL Certificate Issues
- Traefik handles SSL automatically
- Ensure `CERTRESOLVER` variable is set correctly
- Check Traefik logs for certificate generation issues

## Next Steps

After deployment:
1. Log in to the dashboard at `https://wazuh.${DOMAIN_NAME}`
2. Deploy Wazuh agents to systems you want to monitor
3. Configure security rules and alerts
4. Integrate with your SIEM or notification systems

## Documentation

- [Wazuh Documentation](https://documentation.wazuh.com/current/)
- [Wazuh Docker Deployment](https://documentation.wazuh.com/current/deployment-options/docker/wazuh-container.html)
- [Latest Release Notes (4.14.3)](https://documentation.wazuh.com/current/release-notes/release-4-14-3.html)
