# NetBox Sync Configuration Guide

Complete reference for all environment variables, secrets, and custom fields required for NetBox sync scripts to function properly.

## Table of Contents
- [Environment Variables (Forgejo Repository Variables)](#environment-variables)
- [Secrets (Forgejo Repository Secrets)](#secrets)
- [Custom Fields](#custom-fields)
- [Setup Instructions](#setup-instructions)

---

## Environment Variables

Add these to your **Forgejo Repository Settings → Variables** (plaintext):

### Core Configuration
| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `DOMAIN_NAME` | - | Primary domain for Traefik routing | `example.com` |
| `NETBOX_ALLOWED_HOSTS` | - | Comma-separated hosts NetBox accepts | `netbox.example.com,192.168.1.100` |
| `NETBOX_DB_NAME` | - | PostgreSQL database name | `netbox` |
| `NETBOX_DB_USER` | - | PostgreSQL database user | `netbox` |
| `NETBOX_DB_HOST` | - | PostgreSQL host (usually `netbox-postgres`) | `netbox-postgres` |
| `NETBOX_DB_PASSWORD` | - | **See SECRETS** | - |
| `NETBOX_REDIS_HOST` | - | Redis host (usually `netbox-redis`) | `netbox-redis` |
| `NETBOX_METRICS_ENABLED` | `false` | Enable Prometheus metrics | `true` or `false` |
| `VERIFY_SSL` | `false` | Verify SSL certificates for external APIs | `false` for self-signed, `true` for production |

### Email Configuration
| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `NETBOX_EMAIL_FROM` | - | Sender email address | `netbox@example.com` |
| `NETBOX_EMAIL_SERVER` | - | SMTP server hostname | `mail.example.com` |
| `NETBOX_EMAIL_PORT` | - | SMTP server port | `587` |

### TrueNAS Scale Sync
| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `TRUENAS_URL` | `https://truenas01.example.com` | TrueNAS web UI URL | `https://truenas01.example.com` |

### OPNsense Sync
| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `OPNSENSE_URL` | `https://opnsense.example.com` | OPNsense web UI URL | `https://opnsense.example.com` |

### Omada Controller Sync
| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `OMADA_URL` | `https://omada.example.com` | Omada Controller web UI URL | `https://omada.example.com` |
| `OMADA_SITE_NAME` | `Default` | Name of site in Omada Controller | `Default` or `Home-Lab` |

### Docker Sync
| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `DOCKER_HOST` | `truenas01` | Docker host name (for NetBox records) | `truenas01` |
| `DOCKER_SITE` | `homelab` | NetBox site for Docker resources | `homelab` |

---

## Secrets

Add these to your **Forgejo Repository Settings → Secrets** (encrypted):

### NetBox API
| Secret | Required | Description |
|--------|----------|-------------|
| `NETBOX_API_TOKEN` | ✓ | NetBox API token for sync script authentication |
| `NETBOX_SECRET_KEY` | ✓ | Django secret key (random 50+ char string) |
| `NETBOX_DB_PASSWORD` | ✓ | PostgreSQL password |

### Email/SMTP
| Secret | Required | Description |
|--------|----------|-------------|
| `SMTP_USERNAME` | ✓ | SMTP username for email notifications |
| `SMTP_PASSWORD` | ✓ | SMTP password |

### TrueNAS Scale
| Secret | Required | Description |
|--------|----------|-------------|
| `TRUENAS_API_KEY` | ✓ | TrueNAS API key (from System → API Keys) |

### OPNsense
| Secret | Required | Description |
|--------|----------|-------------|
| `OPNSENSE_API_KEY` | ✓ | OPNsense API key (from System → Access → Users) |
| `OPNSENSE_API_SECRET` | ✓ | OPNsense API secret (paired with API key) |

### Omada Controller
| Secret | Required | Description |
|--------|----------|-------------|
| `OMADA_USERNAME` | ✓ | Omada Controller admin username |
| `OMADA_PASSWORD` | ✓ | Omada Controller admin password |

---

## Custom Fields

Custom fields extend NetBox models with additional metadata. Create these in **NetBox Admin → Customization → Custom Fields**.

### Device Custom Fields (`dcim.device`)

These fields store infrastructure data synced from external sources.

#### Field 1: Storage Pools (TrueNAS)
```
Name:              storage_pools
Label:             Storage Pools
Type:              Long text
Description:       Storage pool information from TrueNAS (JSON formatted)
Content Types:     dcim > device
Weight:            100
Default:           (leave blank)
Required:          ☐ (unchecked)
Filter Logic:      Loose
Visibility:        Always
Editable:          No
Group:             Infrastructure Metadata
```

**Purpose:** Stores TrueNAS pool information (capacity, usage, status)

#### Field 2: Firewall Rules Count (OPNsense)
```
Name:              firewall_rules_count
Label:             Firewall Rules
Type:              Integer
Description:       Number of active firewall rules on OPNsense
Content Types:     dcim > device
Weight:            110
Default:           0
Required:          ☐ (unchecked)
Minimum Value:     0
Maximum Value:     (leave blank)
Filter Logic:      Loose
Visibility:        Always
Editable:          No
Group:             Infrastructure Metadata
```

**Purpose:** Quick reference for firewall rule count

#### Field 3: Sync Source
```
Name:              sync_source
Label:             Sync Source
Type:              Selection
Description:       Source system that provided this device data
Content Types:     dcim > device
Weight:            120
Choices:           TrueNAS, OPNsense, Omada, Manual
Required:          ☐ (unchecked)
Filter Logic:      Exact
Visibility:        Always
Editable:          No
Group:             Infrastructure Metadata
```

**Purpose:** Track origin of synced device data

#### Field 4: Last Sync Time
```
Name:              last_sync_time
Label:             Last Sync Time
Type:              Date & time
Description:       Timestamp of last successful sync
Content Types:     dcim > device
Weight:            130
Default:           (leave blank)
Required:          ☐ (unchecked)
Filter Logic:      Loose
Visibility:        Always
Editable:          No
Group:             Infrastructure Metadata
```

**Purpose:** Track when device was last synced

---

### Virtual Machine Custom Fields (`virtualization.virtualmachine`)

These fields store Docker container metadata.

#### Field 1: Container ID
```
Name:              container_id
Label:             Container ID
Type:              Text
Description:       Docker container ID (short form)
Content Types:     virtualization > virtual machine
Weight:            100
Default:           (leave blank)
Required:          ☐ (unchecked)
Filter Logic:      Exact
Visibility:        Always
Editable:          No
Group:             Container Metadata
```

**Purpose:** Map NetBox VMs back to Docker container IDs

#### Field 2: Container Image
```
Name:              container_image
Label:             Container Image
Type:              Text
Description:       Docker image name and tag (e.g., nginx:latest)
Content Types:     virtualization > virtual machine
Weight:            110
Default:           (leave blank)
Required:          ☐ (unchecked)
Filter Logic:      Loose
Visibility:        Always
Editable:          No
Group:             Container Metadata
```

**Purpose:** Track which image runs each container

#### Field 3: Container Status
```
Name:              container_status
Label:             Container Status
Type:              Selection
Description:       Current Docker container status
Content Types:     virtualization > virtual machine
Weight:            120
Choices:           running, exited, paused, restarting, created, offline
Required:          ☐ (unchecked)
Filter Logic:      Exact
Visibility:        Always
Editable:          No
Group:             Container Metadata
```

**Purpose:** Detailed container state tracking

---

### Interface Custom Fields (`dcim.interface`, `virtualization.vminterface`)

Optional: Track interface source data.

#### Field 1: MAC Address Source
```
Name:              mac_source
Label:             MAC Source
Type:              Selection
Description:       Source that provided this MAC address
Content Types:     dcim > interface, virtualization > vm interface
Weight:            100
Choices:           OPNsense, Omada, Docker, TrueNAS, Manual
Required:          ☐ (unchecked)
Filter Logic:      Exact
Visibility:        If Set
Editable:          No
Group:             Sync Metadata
```

---

### Network/Prefix Custom Fields (`ipam.prefix`)

Optional: Track Docker network metadata.

#### Field 1: Network Driver
```
Name:              network_driver
Label:             Network Driver
Type:              Text
Description:       Docker network driver type
Content Types:     ipam > prefix
Weight:            100
Default:           (leave blank)
Required:          ☐ (unchecked)
Filter Logic:      Exact
Visibility:        If Set
Editable:          No
Group:             Container Metadata
```

**Purpose:** Track bridge, overlay, macvlan, etc.

#### Field 2: Network Scope
```
Name:              network_scope
Label:             Network Scope
Type:              Selection
Description:       Docker network visibility scope
Content Types:     ipam > prefix
Weight:            110
Choices:           local, swarm, global
Required:          ☐ (unchecked)
Filter Logic:      Exact
Visibility:        If Set
Editable:          No
Group:             Container Metadata
```

---

## Setup Instructions

### 1. Create Forgejo Variables

**Navigate to:** Repository Settings → Variables

Add all variables from the [Environment Variables](#environment-variables) section.

**Example:**
```
DOMAIN_NAME=example.com
TRUENAS_URL=https://truenas01.example.com
VERIFY_SSL=false
```

### 2. Create Forgejo Secrets

**Navigate to:** Repository Settings → Secrets

Add all secrets from the [Secrets](#secrets) section.

**Important:** Secrets are encrypted and only revealed during workflow execution.

### 3. Generate Required API Keys

#### NetBox API Token
1. Login to NetBox web UI
2. Navigate to: **Admin → Users → [Your User] → API Tokens**
3. Click **Add**
4. Create token with description "NetBox Sync Scripts"
5. Copy the token and save as `NETBOX_API_TOKEN` secret

#### TrueNAS API Key
1. Login to TrueNAS Scale web UI
2. Navigate to: **System Settings → API Keys**
3. Click **Add**
4. Description: "NetBox Sync"
5. Copy the key and save as `TRUENAS_API_KEY` secret

#### OPNsense API Credentials
1. Login to OPNsense web UI
2. Navigate to: **System → Access → Users**
3. Click your user → **API Keys**
4. Click **Add**
5. Copy **Key** → `OPNSENSE_API_KEY` secret
6. Copy **Secret** → `OPNSENSE_API_SECRET` secret

#### Omada Controller Credentials
1. Use your Omada admin username → `OMADA_USERNAME` secret
2. Use your Omada admin password → `OMADA_PASSWORD` secret

### 4. Create Custom Fields in NetBox

**Navigate to:** Customization → Custom Fields → Add

Create each custom field listed in the [Custom Fields](#custom-fields) section.

**Best Practices:**
- Set `Editable: No` for synced fields (prevents manual overwrites)
- Use `Visibility: If Set` for optional fields
- Group related fields with `Group` parameter
- Use meaningful descriptions for filtering/searching

### 5. Deploy NetBox

Trigger the Forgejo workflow:
```bash
# Push changes to trigger automatic deployment
git push origin main

# Or manually trigger via Forgejo web UI
# Repository → Actions → Deploy NetBox → Run workflow
```

### 6. Test Sync Scripts

**Run all syncs:**
```bash
docker exec -it netbox /opt/netbox/netbox/scripts/run_sync.sh
```

**Run individual syncs:**
```bash
# TrueNAS
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_truenas.py

# OPNsense
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_opnsense.py

# Omada
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_omada.py

# Docker
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_docker.py
```

**Check logs:**
```bash
docker exec -it netbox cat /opt/netbox/logs/sync_truenas.log
docker exec -it netbox cat /opt/netbox/logs/sync_opnsense.log
docker exec -it netbox cat /opt/netbox/logs/sync_omada.log
docker exec -it netbox cat /opt/netbox/logs/sync_docker.log
```

### 7. Schedule Automatic Syncs

Add to TrueNAS cron or use external scheduler:

```bash
# Run every 6 hours
0 */6 * * * docker exec netbox /opt/netbox/netbox/scripts/run_sync.sh >> /mnt/Apps/NetBox/logs/cron_sync.log 2>&1
```

---

## Validation Checklist

- [ ] All Forgejo Variables set (see table above)
- [ ] All Forgejo Secrets configured (encrypted)
- [ ] NetBox API token generated and stored
- [ ] TrueNAS API key generated and stored
- [ ] OPNsense API credentials generated and stored
- [ ] Omada Controller credentials stored
- [ ] SMTP credentials configured
- [ ] All custom fields created in NetBox
- [ ] Custom field groups assigned correctly
- [ ] Sync scripts tested individually
- [ ] Logs reviewed for errors
- [ ] Cron job scheduled (optional)

---

## Troubleshooting

### API Authentication Failures

**Error:** `Error fetching devices: 401 Unauthorized`

**Solution:**
1. Verify API credentials are correct
2. Check API token hasn't expired
3. Ensure user has required permissions
4. Check API key/secret pairs match

### SSL Certificate Errors

**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution:**
```bash
# Temporarily disable SSL verification
VERIFY_SSL=false docker exec netbox /opt/netbox/netbox/scripts/run_sync.sh

# Then set VERIFY_SSL=false in Forgejo Variables
```

### Missing Custom Fields

**Error:** `Custom field 'storage_pools' does not exist`

**Solution:**
1. Create custom field in NetBox UI (see [Custom Fields](#custom-fields))
2. Ensure field name matches exactly (snake_case)
3. Check field is assigned to correct content type

### Network Connectivity

**Error:** `Connection refused` or `Name resolution failed`

**Solution:**
1. Verify URLs are correct in Forgejo Variables
2. Check firewall rules allow outbound connections
3. Test DNS resolution: `nslookup truenas01.example.com`
4. Test API connectivity: `curl -k https://opnsense.example.com/api/core/system/status`

---

## Reference: Field Types

| Type | Use Case | Example |
|------|----------|---------|
| **Text** | Single-line data, IDs | Container ID, IP address |
| **Long text** | Multi-line data, JSON | Storage pool details, comments |
| **Integer** | Numeric counters | Rule count, port number |
| **Decimal** | Precise numbers | CPU count (2.5 cores) |
| **Boolean** | Yes/No | Is encrypted, Is monitored |
| **Date** | Point-in-time reference | Warranty expiration |
| **Date & time** | Timestamp tracking | Last sync, deployment time |
| **URL** | Hyperlinks | Controller web UI link |
| **JSON** | Structured metadata | Complex configurations |
| **Selection** | Predefined choices | Status, source system |
| **Multiple selection** | Multiple predefined choices | Tags, supported protocols |

---

## Additional Resources

- [NetBox Custom Fields Documentation](https://netboxlabs.com/docs/netbox/en/stable/customization/custom-fields/)
- [NetBox REST API Guide](https://netboxlabs.com/docs/netbox/en/stable/api/overview/)
- [PyNetBox Library](https://github.com/netbox-community/pynetbox)
