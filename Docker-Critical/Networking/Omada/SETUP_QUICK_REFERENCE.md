# Omada Controller Setup Quick Reference

## ⚡ Required Forgejo Variables (Plaintext)

```
DOMAIN_NAME=u-acres.com
TZ=America/Chicago
```

## 🔐 Required Forgejo Secrets (Encrypted)

For NetBox integration (if using NetBox sync):
```
OMADA_USERNAME=<your Omada admin username>
OMADA_PASSWORD=<your Omada admin password>
```

## 📦 Service Details

- **Container Name:** `omada-controller`
- **Image:** `mbentley/omada-controller:latest`
- **Web UI:** https://omada.u-acres.com
- **Default Ports:**
  - Management HTTPS: 8043
  - Portal HTTPS: 8843
  - Management HTTP: 8088 (redirects to HTTPS)
  - Portal HTTP: 8088

## 📁 Persistent Storage

- **Data:** `/mnt/Apps/Omada/data`
- **Logs:** `/mnt/Apps/Omada/logs`

## 🌐 Network

- **Network:** `toolsproxy` (external)
- **Traefik Route:** `omada.u-acres.com`

## 🚀 Deployment

### Via Forgejo Workflow (Recommended)
```bash
# Push changes to trigger deployment
git add Tools/Omada/omada.yml .forgejo/workflows/deploy-omada.yml
git commit -m "Deploy Omada Controller"
git push origin main

# Or trigger manually via Forgejo UI:
# Repository → Actions → Deploy Omada Controller → Run Workflow
```

### Manual Deployment (Not Recommended)
```bash
# SSH to truenas01
ssh runner@truenas01

# Create data directories
mkdir -p /mnt/Apps/Omada/data /mnt/Apps/Omada/logs

# Deploy
cd /tmp
DOMAIN_NAME=u-acres.com TZ=America/Chicago docker compose -p omada -f omada.yml up -d
```

## 🔧 Initial Setup

1. Access https://omada.u-acres.com
2. Follow the setup wizard:
   - Set controller name
   - Create admin account (use these credentials for `OMADA_USERNAME` and `OMADA_PASSWORD` secrets if using NetBox sync)
   - Configure cloud access (optional)
   - Set wireless network settings

3. Add your Omada devices:
   - Ensure devices are on the same network or have L3 discovery enabled
   - Devices should auto-discover the controller
   - Adopt devices from the pending list

## 📋 Pre-Deployment Checklist

- [ ] `DOMAIN_NAME` variable set in Forgejo
- [ ] `TZ` variable set in Forgejo (America/Chicago)
- [ ] `/mnt/Apps/Omada` directory exists on truenas01
- [ ] `toolsproxy` network exists
- [ ] Traefik is running and configured
- [ ] DNS record for `omada.u-acres.com` points to Traefik
- [ ] Workflow file pushed to `.forgejo/workflows/deploy-omada.yml`

## 🔍 Troubleshooting

### Check Container Status
```bash
ssh runner@truenas01
docker ps --filter name=omada-controller
docker logs omada-controller
```

### Check Health
```bash
docker inspect omada-controller | grep -A 10 Health
```

### Access Container Shell
```bash
docker exec -it omada-controller /bin/bash
```

### Reset Controller (Caution!)
```bash
# This will delete all configuration
ssh runner@truenas01
docker compose -p omada -f /tmp/omada.yml down -v
rm -rf /mnt/Apps/Omada/data/*
docker compose -p omada -f /tmp/omada.yml up -d
```

## 🔗 Integration

### NetBox Sync
If you're using the NetBox sync scripts (as seen in [NetBox SETUP_QUICK_REFERENCE.md](../Home/NetBox/SETUP_QUICK_REFERENCE.md)), ensure you set:

- `OMADA_URL` = `https://omada.u-acres.com`
- `OMADA_USERNAME` = admin username (secret)
- `OMADA_PASSWORD` = admin password (secret)
- `OMADA_SITE_NAME` = `Default` (or your site name)

## 📚 Additional Resources

- [Official Omada Controller Documentation](https://www.tp-link.com/us/support/download/omada-software-controller/)
- [mbentley/omada-controller Docker Image](https://hub.docker.com/r/mbentley/omada-controller)
- [Omada SDN API Documentation](https://www.tp-link.com/us/omada-sdn/controller-api/)

## ⚙️ Configuration Notes

- The controller runs on HTTPS by default (port 8043)
- SSL certificates are managed by Traefik
- MongoDB is embedded in the container
- First-time setup requires web UI access
- Controller ID is generated on first run and stored in `/mnt/Apps/Omada/data`
