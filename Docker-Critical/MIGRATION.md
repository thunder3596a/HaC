# Migration Guide: TrueNAS to Home Assistant

This guide covers migrating Docker-Critical services from TrueNAS (`/mnt/Apps/`) to Home Assistant (`/opt/Docker-Critical/`).

## Pre-Migration Checklist

- [ ] Ensure Home Assistant has sufficient disk space
- [ ] SSH access configured between hosts
- [ ] Stop all running services on TrueNAS (optional, for data consistency)
- [ ] Backup critical data before migration

## Service Mapping

| Service | Old Path (TrueNAS) | New Path (Home Assistant) |
|---------|-------------------|---------------------------|
| Authelia | `/mnt/Apps/Authelia` | `/opt/Docker-Critical/Authelia` |
| Traefik | `/mnt/Apps/traefik` | `/opt/Docker-Critical/traefik` |
| SMTP Relay | `/mnt/Apps/SMTPRelay` | `/opt/Docker-Critical/SMTPRelay` |
| Omada | `/mnt/Apps/Omada` | `/opt/Docker-Critical/Omada` |
| KaraKeep | `/mnt/Apps/KaraKeep` | `/opt/Docker-Critical/KaraKeep` |
| HomeBox | `/mnt/Apps/homebox` | `/opt/Docker-Critical/homebox` |
| Kiwix | `/mnt/Apps/kiwix` | `/opt/Docker-Critical/kiwix` |
| NetBox | `/mnt/Apps/NetBox` | `/opt/Docker-Critical/NetBox` |
| Norish | `/mnt/Apps/norish` + `/mnt/Apps/Norish` | `/opt/Docker-Critical/norish` + `/opt/Docker-Critical/Norish` |
| Forgejo | `/mnt/Apps/git` | `/opt/Docker-Critical/git` |

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

For each service, run on Home Assistant:

```bash
SERVICE_NAME="Authelia"  # Change as needed
sudo mkdir -p "/opt/Docker-Critical/${SERVICE_NAME}"
sudo rsync -avz --progress runner@truenas01:/mnt/Apps/${SERVICE_NAME}/ /opt/Docker-Critical/${SERVICE_NAME}/
```

### Method 3: Pull from TrueNAS

Run this on TrueNAS to push data to Home Assistant:

```bash
#!/bin/bash
TARGET_HOST="homeassistant"  # Update with actual hostname/IP
TARGET_USER="user"           # Update with actual user

for SERVICE in Authelia traefik SMTPRelay Omada KaraKeep homebox kiwix NetBox norish Norish git; do
    echo "Migrating ${SERVICE}..."
    ssh ${TARGET_USER}@${TARGET_HOST} "sudo mkdir -p '/opt/Docker-Critical/${SERVICE}'"
    rsync -avz --progress \
        "/mnt/Apps/${SERVICE}/" \
        "${TARGET_USER}@${TARGET_HOST}:/tmp/${SERVICE}/"
    ssh ${TARGET_USER}@${TARGET_HOST} "sudo mv /tmp/${SERVICE}/* '/opt/Docker-Critical/${SERVICE}/' && sudo rmdir /tmp/${SERVICE}"
done
```

## Post-Migration Steps

### 1. Verify Data Migration

On Home Assistant:
```bash
# Check all directories exist and have content
ls -lah /opt/Docker-Critical/

# Verify specific services
du -sh /opt/Docker-Critical/*
```

### 2. Fix Ownership/Permissions

```bash
# Set ownership to user 568:568 (standard for linuxserver images)
sudo chown -R 568:568 /opt/Docker-Critical/*

# Specific permission fixes
sudo chmod 600 /opt/Docker-Critical/traefik/acme.json
sudo chmod 755 /opt/Docker-Critical/Authelia/config
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
sudo chown -R 568:568 /opt/Docker-Critical/
sudo chmod -R 755 /opt/Docker-Critical/
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
