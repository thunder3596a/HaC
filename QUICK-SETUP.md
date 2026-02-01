# Quick Setup Checklist

## What You Need to Do

### 1. Get Your Forgejo API Token

1. Go to: https://git.example.com/user/settings/applications
2. Click "Generate New Token"
3. Token name: `docker-workflows`
4. Select permissions:
   - ✅ `repository` (read/write)
   - ✅ `actions` (read/write)
5. Click "Generate Token"
6. **Copy the token** (you'll only see it once!)

### 2. Add Forgejo Secrets

Go to: https://git.example.com/your-username/docker/settings/actions/secrets

Click "Add Secret" for each of these:

#### Required - Fill These In:

| Secret Name | Where to Get It | Example |
|------------|----------------|---------|
| `FORGEJO_TOKEN` | Token from step 1 (NO "token " prefix) | `abc123def456...` |
| `forgejo_token` | Same token WITH "token " prefix | `token abc123def456...` |
| `CLOUDFLARE_DNS_API_TOKEN` | Cloudflare Dashboard → API Tokens | `xxx` |
| `CLOUDFLARE_ZONE_API_TOKEN` | Cloudflare Dashboard → API Tokens | `xxx` |
| `HOMEASSISTANT_MARIADB_ROOT_PASSWORD` | Your MariaDB root password | From your setup |
| `HOMEASSISTANT_MARIADB_PASSWORD` | Your MariaDB HA user password | From your setup |
| `HA_LONG_LIVED_TOKEN` | HA → Profile → Long-Lived Tokens | `eyJhb...` |

#### Already Have Values - Copy from HA secrets.yaml:

| Secret Name | Value (from HA secrets.yaml) |
|------------|------------------------------|
| `forgejo_workflow_url_critical` | `https://git.example.com/api/v1/repos/your-username/docker/actions/workflows/check-updates-critical.yml/dispatches` |
| `forgejo_workflow_url_noncritical` | `https://git.example.com/api/v1/repos/your-username/docker/actions/workflows/check-updates-noncritical.yml/dispatches` |
| `forgejo_workflow_url_apply_critical` | `https://git.example.com/api/v1/repos/your-username/docker/actions/workflows/apply-updates-critical.yml/dispatches` |
| `forgejo_workflow_url_apply_noncritical` | `https://git.example.com/api/v1/repos/your-username/docker/actions/workflows/apply-updates-noncritical.yml/dispatches` |

### 3. Add Forgejo Variables

Go to: https://git.example.com/your-username/docker/settings/actions/variables

Click "Add Variable" for each of these:

| Variable Name | Value |
|--------------|-------|
| `DOMAIN_NAME` | `example.com` |
| `TZ` | `America/Chicago` |
| `CERTRESOLVER` | `cloudflare` |
| `HA_URL` | `https://ha.example.com` |
| `CLOUDFLARE_EMAIL` | Your Cloudflare email |
| `LETS_ENCRYPT_EMAIL` | Your Let's Encrypt email |

### 4. Copy Script to Home Assistant

```bash
# On your Home Assistant host
cd /path/to/this/repo
cp scripts/get-docker-containers.sh /srv/homeassistant/config/
chmod +x /srv/homeassistant/config/get-docker-containers.sh
```

### 5. Restart Home Assistant

```bash
# In Home Assistant
Developer Tools → YAML → Restart
```

### 6. Test the Workflow

1. Go to: https://git.example.com/your-username/docker/actions
2. Find "Apply Updates - Docker Critical"
3. Click "Run workflow"
4. Watch the output - should see "Registered: container-name → compose-file"

## Common Issues

### "could not read Username" error
- **Fix**: Make sure you added `FORGEJO_TOKEN` secret (without "token " prefix)
- The workflow now uses this for git checkout

### "Secret X not defined" error
- **Fix**: Add the missing secret in step 2 above

### Workflow succeeds but containers don't update
- **Fix**: Make sure labels are added to compose files
- Verify with: `docker inspect container-name | grep ha.monitor`

### Home Assistant sensors show "unknown"
- **Fix**: Make sure script is copied and executable
- Test manually: `/config/get-docker-containers.sh http://YOUR_DOCKER_HOST_IP:2375`

## Next Steps After Setup

1. Add labels to remaining compose files (see DOCKER-MONITORING-SETUP.md)
2. Import docker-dashboard.yaml to Home Assistant
3. Test container updates via dashboard buttons

## Need Help?

See the detailed guides:
- [DOCKER-MONITORING-SETUP.md](DOCKER-MONITORING-SETUP.md) - Complete technical setup
- [FORGEJO-VARIABLES-SETUP.md](FORGEJO-VARIABLES-SETUP.md) - Detailed variable documentation
- [forgejo-config-template.yml](forgejo-config-template.yml) - Template with all values
