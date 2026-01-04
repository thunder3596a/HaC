# Migration Guide: TrueNAS to Home Assistant

This guide covers migrating Docker-Critical services from TrueNAS (`/mnt/Apps/`) to the Debian 12 critical host using the new storage layout:

- SSD (`/srv`) for all critical services: Home Assistant, databases, MQTT, Zigbee/Z-Wave, Traefik, Authelia, Forgejo, NetBox, HomeBox, KaraKeep
- HDD (`/mnt/hdd`) for backups, logs, and large archives (Kiwix ZIM files)

## Storage Layout

Your hardware consists of:
- **512GB SSD** mounted at `/srv` — All critical services, databases, and persistent data
- **1TB HDD** mounted at `/mnt/hdd` — Logs, backups, and large archives (e.g., Kiwix ZIM files)

All Docker-Critical services are consolidated on the SSD for performance.

## Service Mapping

| Service | Old Path (TrueNAS) | New Path (Critical Host) | Storage Tier |
|---------|-------------------|---------------------------|--------------|
| Home Assistant | `/mnt/Apps/homeassistant` | `/srv/homeassistant/config` | SSD |
| Avahi | `/mnt/Apps/avahi` | `/srv/avahi` | SSD |
| ESPHome | `/mnt/Apps/esphome` | `/srv/esphome` | SSD |
| RTL-SDR | `/mnt/Apps/rtl-sdr` | `/srv/rtl-sdr` | SSD |
| Music Assistant | `/mnt/Apps/music-assistant` | `/srv/music-assistant` | SSD |
| InfluxDB | `/mnt/Apps/influxdb` | `/srv/influxdb` | SSD |
| Authelia | `/mnt/Apps/Authelia` | `/srv/authelia` | SSD |
| Traefik | `/mnt/Apps/traefik` | `/srv/traefik` | SSD |
| SMTP Relay | `/mnt/Apps/SMTPRelay` | `/srv/smtp-relay` (spool) + `/mnt/hdd/logs/smtp-relay` (logs) | SSD/HDD |
| Omada | `/mnt/Apps/Omada` | `/srv/omada` (data) + `/mnt/hdd/logs/omada` (logs) | SSD/HDD |
| Norish | `/mnt/Apps/norish` + `/mnt/Apps/Norish` | `/srv/norish` | SSD |
| Forgejo | `/mnt/Apps/git` | `/srv/git` | SSD |
| NetBox | `/mnt/Apps/NetBox` | `/srv/netbox` | SSD |
| HomeBox | `/mnt/Apps/homebox` | `/srv/homebox` | SSD |
| KaraKeep | `/mnt/Apps/KaraKeep` | `/srv/karakeep` | SSD |
| Kiwix | `/mnt/Apps/kiwix` | `/mnt/hdd/kiwix` | HDD |

## Migration Methods

### Method 1: Automated Script (Recommended)

1. Copy `migrate-to-homeassistant.sh` to Home Assistant:
   ```bash
   scp migrate-to-homeassistant.sh user@homeassistant:/tmp/
   ```

2. SSH to Home Assistant and run:
   ```bash
   ssh user@homeassistant
   chmod +x /tmp/migrate-to-homeassistant.sh
   sudo /tmp/migrate-to-homeassistant.sh
   ```

### Method 2: Manual Service-by-Service

For each service, run on the Debian host (choose the target path from the table above):

```bash
SERVICE_NAME="Authelia"  # Change as needed
TARGET_PATH="/srv/authelia"  # Example target on NVMe #1; adjust per service mapping
sudo mkdir -p "${TARGET_PATH}"
sudo rsync -avz --progress runner@truenas01:/mnt/Apps/${SERVICE_NAME}/ "${TARGET_PATH}/"
```

### Method 3: Pull from TrueNAS

Run this on TrueNAS to push data to Home Assistant:

```bash
#!/bin/bash
TARGET_HOST="homeassistant"  # Update with actual hostname/IP
TARGET_USER="user"           # Update with actual user

declare -A TARGET_PATHS=(
    [Authelia]="/srv/authelia"
    [traefik]="/srv/traefik"
    [SMTPRelay]="/srv/smtp-relay"
    [Omada]="/srv/omada"
    [KaraKeep]="/mnt/nvme-appdata/karakeep"
    [homebox]="/mnt/nvme-appdata/homebox"
    [kiwix]="/mnt/hdd/kiwix/zim"
    [NetBox]="/mnt/nvme-appdata/netbox"
    [norish]="/srv/norish"
    [Norish]="/srv/norish"   # case variant
    [git]="/srv/git"
)

for SERVICE in "${!TARGET_PATHS[@]}"; do
    TARGET_PATH=${TARGET_PATHS[$SERVICE]}
    echo "Migrating ${SERVICE} -> ${TARGET_PATH}"
    ssh ${TARGET_USER}@${TARGET_HOST} "sudo mkdir -p '${TARGET_PATH}'"
    rsync -avz --progress \
        "/mnt/Apps/${SERVICE}/" \
        "${TARGET_USER}@${TARGET_HOST}:${TARGET_PATH}/"
done
```

## Post-Migration Steps

### 1. Verify Data Migration

On the Debian host:
```bash
# Check all directories exist and have content
ls -lah /srv /mnt/hdd

# Verify specific services
du -sh /srv/* /mnt/hdd/*
```

### 2. Fix Ownership/Permissions

```bash
# Set ownership to user 568:568 (standard for linuxserver images)
sudo chown -R 568:568 /srv/*

# Specific permission fixes
sudo chmod 600 /srv/traefik/acme.json
sudo chmod 755 /srv/authelia/config
```

### 3. Update Workflows

The workflows have already been updated to reference the new paths. Verify:
- `.forgejo/workflows/deploy-*.yml` files point to `Docker-Critical/` paths
- Workflow runners are configured for the correct host

### 4. Deploy Services

Deploy services one by one via Forgejo workflows:

```bash
# Example order (dependencies first)
1. Traefik (networking layer)
2. Authelia (authentication)
3. SMTP Relay (email)
4. Database-backed services (Forgejo, NetBox, Norish)
5. Standalone services (KaraKeep, HomeBox, Kiwix, Omada)
```

### 5. Test Each Service

After deployment, verify:
- [ ] Service starts successfully
- [ ] Data is accessible
- [ ] Authentication works (if applicable)
- [ ] Traefik routing works
- [ ] SSL certificates are valid

### 6. Update DNS/Routing (if needed)

If Home Assistant has a different IP than TrueNAS:
- Update DNS records
- Update reverse proxy rules
- Update firewall rules

## Rollback Plan

If migration fails:

1. Keep original data on TrueNAS untouched until fully verified
2. To rollback, simply redeploy services on TrueNAS using old compose files
3. Restore DNS/routing to TrueNAS

## Cleanup (After Successful Migration)

Once everything is verified working on Home Assistant:

```bash
# On TrueNAS (BE CAREFUL!)
# Archive old data before deletion
sudo tar -czf /mnt/backup/docker-critical-backup-$(date +%Y%m%d).tar.gz /mnt/Apps/

# Remove old data (only after 100% verification)
# sudo rm -rf /mnt/Apps/Authelia
# sudo rm -rf /mnt/Apps/traefik
# ... etc
```

## Troubleshooting

### Permission Denied Errors
```bash
sudo chown -R 568:568 /srv/ /mnt/nvme-appdata/
sudo chmod -R 755 /srv/
```

### Database Won't Start
- Check postgres data directory permissions
- Verify data isn't corrupted
- Check logs: `docker logs <container-name>`

### Missing Data
- Verify rsync completed successfully
- Check source and target paths match
- Look for hidden files: `ls -la`

### Network Issues
- Ensure SSH keys are set up
- Test connectivity: `ssh runner@truenas01`
- Check firewall rules

## Verification Checklist

- [ ] All directories migrated
- [ ] File counts match source
- [ ] Disk space sufficient
- [ ] Permissions correct
- [ ] Services deploy successfully
- [ ] Web interfaces accessible
- [ ] Data appears correct
- [ ] Backups taken
- [ ] Old data archived
