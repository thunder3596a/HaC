# NetBox Sync Quick Reference

## ⚡ Required Forgejo Variables (Plaintext)

```
DOMAIN_NAME=u-acres.com
NETBOX_ALLOWED_HOSTS=netbox.u-acres.com,192.168.1.100
NETBOX_DB_NAME=netbox
NETBOX_DB_USER=netbox
NETBOX_DB_HOST=netbox-postgres
NETBOX_REDIS_HOST=netbox-redis
NETBOX_METRICS_ENABLED=false
NETBOX_EMAIL_FROM=netbox@u-acres.com
NETBOX_EMAIL_SERVER=mail.u-acres.com
NETBOX_EMAIL_PORT=587
TRUENAS_URL=https://truenas01.u-acres.com
OPNSENSE_URL=https://opnsense.u-acres.com
OMADA_URL=https://omada.u-acres.com
OMADA_SITE_NAME=Default
DOCKER_HOST=truenas01
DOCKER_SITE=homelab
VERIFY_SSL=false
```

## 🔐 Required Forgejo Secrets (Encrypted)

```
NETBOX_SECRET_KEY=<random 50+ char string>
NETBOX_DB_PASSWORD=<strong password>
NETBOX_API_TOKEN=<from NetBox Admin → Users → API Tokens>
SMTP_USERNAME=<email account>
SMTP_PASSWORD=<email password>
TRUENAS_API_KEY=<from TrueNAS System Settings → API Keys>
OPNSENSE_API_KEY=<from OPNsense System → Access → Users>
OPNSENSE_API_SECRET=<paired with API Key>
OMADA_USERNAME=<Omada admin username>
OMADA_PASSWORD=<Omada admin password>
```

## 📋 Required NetBox Custom Fields

### Device Fields (`dcim.device`)

| Name | Type | Description | Group |
|------|------|-------------|-------|
| `storage_pools` | Long Text | TrueNAS pool data (JSON) | Infrastructure Metadata |
| `firewall_rules_count` | Integer | OPNsense firewall rule count | Infrastructure Metadata |
| `sync_source` | Selection | Data source (TrueNAS/OPNsense/Omada/Manual) | Infrastructure Metadata |
| `last_sync_time` | Date & Time | Last sync timestamp | Infrastructure Metadata |

**Selection Choices for `sync_source`:** TrueNAS, OPNsense, Omada, Manual

---

### Virtual Machine Fields (`virtualization.virtualmachine`)

| Name | Type | Description | Group |
|------|------|-------------|-------|
| `container_id` | Text | Docker container ID (short) | Container Metadata |
| `container_image` | Text | Docker image:tag | Container Metadata |
| `container_status` | Selection | Container state | Container Metadata |

**Selection Choices for `container_status`:** running, exited, paused, restarting, created, offline

---

### Interface Fields (`dcim.interface`, `virtualization.vminterface`)

| Name | Type | Description | Group |
|------|------|-------------|-------|
| `mac_source` | Selection | MAC provider (OPNsense/Omada/Docker/TrueNAS/Manual) | Sync Metadata |

---

### Prefix Fields (`ipam.prefix`)

| Name | Type | Description | Group |
|------|------|-------------|-------|
| `network_driver` | Text | Docker driver type | Container Metadata |
| `network_scope` | Selection | Docker scope (local/swarm/global) | Container Metadata |

---

## 🔧 Custom Field Settings (Best Practices)

All sync-populated fields should use:
- **Visibility:** Always
- **Editable:** No (prevents manual overwrites)
- **Filter Logic:** Loose (or Exact for selections)
- **Required:** Unchecked

Optional fields use:
- **Visibility:** If Set (only show when populated)
- **Editable:** No

---

## 📍 Custom Field Content Types

Match fields to these content types exactly:

**Device:** `dcim > device`
**Virtual Machine:** `virtualization > virtual machine`
**Interface:** `dcim > interface`
**VM Interface:** `virtualization > vm interface`
**Prefix:** `ipam > prefix`

---

## 🚀 Testing

```bash
# Test all syncs
docker exec -it netbox /opt/netbox/netbox/scripts/run_sync.sh

# Test individual sync
docker exec -it netbox python3 /opt/netbox/netbox/scripts/sync_omada.py

# Check logs
docker exec -it netbox tail -f /opt/netbox/logs/sync_*.log
```

---

## ✅ Pre-Deployment Checklist

- [ ] All Variables set in Forgejo (18 items)
- [ ] All Secrets created in Forgejo (10 items)
- [ ] API keys/tokens generated from external systems
- [ ] All custom fields created in NetBox (9 fields)
- [ ] Custom field groups assigned
- [ ] Sync scripts tested
- [ ] Logs reviewed without errors
- [ ] Cron job scheduled (optional)

---

## 📚 Additional Docs

See `CONFIGURATION.md` for:
- Detailed field descriptions
- Step-by-step setup instructions
- Troubleshooting guide
- API key generation procedures
