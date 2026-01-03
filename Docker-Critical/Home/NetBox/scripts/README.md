# NetBox Sync Scripts - Setup Guide

## Overview
These scripts sync infrastructure data from TrueNAS Scale and OPNsense into NetBox automatically.

## What Gets Synced

### TrueNAS Scale (`sync_truenas.py`)
- Device information
- Storage pools (name, status, capacity, usage)
- Network interfaces (name, MAC, MTU, IP addresses)
- Virtual machines (name, vCPUs, memory, status)

### OPNsense (`sync_opnsense.py`)
- Device information
- Network interfaces (name, MAC, IP, status)
- VLANs (ID, name/description)
- Firewall rule count (summary)
- Static routes

### Omada Controller (`sync_omada.py`)
- Access points (name, model, MAC, IP, status, clients)
- Switches (name, model, MAC, IP, status, port count)
- Gateways/routers (name, model, MAC, IP, status)
- Management interfaces with IPs

### Docker (`sync_docker.py`)
- Docker host device
- Containers as virtual machines (with status, resources, networks)
- Container networks (as prefixes)
- Container interfaces and IP addresses
- Volume information (in host device comments)

## Setup Instructions

### 1. Create API Tokens

**TrueNAS Scale:**
1. Login to TrueNAS web UI
2. Go to: System Settings → API Keys
3. Click "Add" and create a new key with read-only permissions
4. Copy the generated API key

**OPNsense:**
1. Login to OPNsense web UI
2. Go to: System → Access → Users
3. Edit your user → API Keys → Add
4. Generate a new API key pair
5. Copy both the Key and Secret

**Omada Controller:**
1. Login to Omada Controller web UI
2. Go to: Settings → Administrator
3. Create a new admin account or use existing one
4. Note the username and password (API uses standard login credentials)

**NetBox:**
1. Login to NetBox
2. Go to: Admin → Users → Your User → API Tokens
3. Create a new token with write permissions
4. Copy the token

### 2. Set Environment Variables in Forgejo

Add these to your Forgejo repository Variables/Secrets:

**Variables:**
- `TRUENAS_URL` = `https://truenas01.u-acres.com`
- `OPNSENSE_URL` = `https://opnsense.u-acres.com` (adjust to your firewall's URL)
- `OMADA_URL` = `https://omada.u-acres.com` (adjust to your Omada controller URL)
- `OMADA_SITE_NAME` = `Default` (or your site name in Omada)
- `DOCKER_HOST` = `truenas01` (name of your Docker host)
- `DOCKER_SITE` = `homelab` (NetBox site name for Docker resources)
- `VERIFY_SSL` = `false` (or `true` if you have valid certs)

**Secrets:**
- `TRUENAS_API_KEY` = (your TrueNAS API key)
- `OPNSENSE_API_KEY` = (your OPNsense API key)
- `OPNSENSE_API_SECRET` = (your OPNsense API secret)
- `OMADA_USERNAME` = (your Omada Controller username)
- `OMADA_PASSWORD` = (your Omada Controller password)
- `NETBOX_API_TOKEN` = (your NetBox API token)

### 3. Update NetBox Compose File

Add the environment variables to the netbox service in `netbox.yml`:

```yaml
environment:
  # ... existing vars ...
  
  # Sync script configuration
  TRUENAS_URL: ${TRUENAS_URL}
  TRUENAS_API_KEY: ${TRUENAS_API_KEY}
  OPNSENSE_URL: ${OPNSENSE_URL}
  OPNSENSE_API_KEY: ${OPNSENSE_API_KEY}
  OPNSENSE_API_SECRET: ${OPNSENSE_API_SECRET}
  OMADA_URL: ${OMADA_URL}
  OMADA_USERNAME: ${OMADA_USERNAME}
  OMADA_PASSWORD: ${OMADA_PASSWORD}
  OMADA_SITE_NAME: ${OMADA_SITE_NAME}
  DOCKER_HOST: ${DOCKER_HOST}
  DOCKER_SITE: ${DOCKER_SITE}
  NETBOX_TOKEN: ${NETBOX_API_TOKEN}
  VERIFY_SSL: ${VERIFY_SSL}
```

### 4. Create Custom Fields in NetBox

Login to NetBox and create these custom fields:

**For Device (dcim.device):**
1. Go to: Customization → Custom Fields → Add
2. Create field:
   - Name: `storage_pools`
   - Type: Text
   - Content Types: dcim > device
3. Create field:
   - Name: `firewall_rule_count`
   - Type: Integer
   - Content Types: dcim > device

**For Virtual Machine (virtualization.virtualmachine) - Optional:**
1. Create field:
   - Name: `container_id`
   - Type: Text
   - Content Types: virtualization > virtual machine
2. Create field:
   - Name: `image`
   - Type: Text
   - Content Types: virtualization > virtual machine

### 5. Run Sync Scripts

**Manual execution (inside container):**
```bash
docker exec -it netbox /opt/netbox/netbox/scripts/run_sync.sh
```

**Individual scripts:**
```bash
# TrueNAS only
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_truenas.py

# OPNsense only
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_opnsense.py

# Omada only
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_omada.py

# Docker only
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_docker.py
```

### 6. Schedule Automatic Sync (Optional)

Add a cron job to the NetBox container or use NetBox's built-in job scheduling:

**Option A: Container cron (add to custom-entrypoint.sh)**
```bash
# Add cron job for hourly sync
echo "0 * * * * /opt/netbox/netbox/scripts/run_sync.sh" | crontab -
```

**Option B: External cron on TrueNAS host**
```bash
# Run every 6 hours
0 */6 * * * docker exec netbox /opt/netbox/netbox/scripts/run_sync.sh
```

## Troubleshooting

**Check logs:**
```bash
docker exec -it netbox cat /opt/netbox/logs/sync_truenas.log
docker exec -it netbox cat /opt/netbox/logs/sync_opnsense.log
docker exec -it netbox cat /opt/netbox/logs/sync_omada.log
docker exec -it netbox cat /opt/netbox/logs/sync_docker.log
```

**Common issues:**
- **SSL errors:** Set `VERIFY_SSL=false` if using self-signed certs
- **API authentication failed:** Verify API keys/secrets are correct
- **Missing objects:** Ensure NetBox has required sites/manufacturers created
- **Permission denied:** Ensure NetBox API token has write permissions

## Next Steps

After first sync, check NetBox web UI:
- Devices → Should see `truenas01`, `opnsense`, and Omada devices (APs, switches, gateways)
- IPAM → IP Addresses → Should see synced IPs from all sources
- IPAM → VLANs → Should see OPNsense VLANs
- IPAM → Prefixes → Should see Docker networks
- Virtualization → Virtual Machines → Should see TrueNAS VMs and Docker containers
- Virtualization → Clusters → Should see Docker cluster

Customize the scripts as needed for your specific infrastructure!
