# Forgejo Secrets & Variables Restoration Guide

After the Forgejo v13→v14 migration, all repository secrets and variables were lost. This directory contains scripts to help restore them.

## Quick Start

### 1. Scan Workflows
```bash
cd restore-secrets
bash scan-workflows.sh
```
This generates `required-secrets.txt` (59 secrets) and `required-vars.txt` (56 variables).

### 2. Find Your Values

**Option A: Check running containers on hosts**
```bash
# SSH to docker-critical
ssh docker-critical

# Check container environment variables
docker inspect homeassistant | grep -A 50 Env
docker inspect forgejo | grep -A 50 Env
docker inspect authelia | grep -A 50 Env

# Check for .env files
find /srv/docker -name ".env" -o -name "*.env"
```

**Option B: Check local development environment**
```bash
# Search for .env files in HaC repo
find ../Docker-* -name ".env" -o -name "*.env"

# Check git history (if values were committed)
git log --all --full-history -- "*.env"
```

**Option C: Check backups**
- TrueNAS backups of /srv/docker directories
- Home Assistant snapshots (may contain MQTT credentials)
- Database dumps (postgres, mariadb)

### 3. Fill in Template
```bash
cp secrets-values.env.template secrets-values.env
nano secrets-values.env  # Fill in your actual values
```

### 4. Create Forgejo Access Token
1. Go to https://git.u-acres.com/user/settings/applications
2. Generate new token with `repo` and `admin:repo_hook` scopes
3. Export it:
```bash
export FORGEJO_TOKEN="your-token-here"
```

### 5. Run Restoration Script
```bash
bash restore-forgejo-secrets.sh secrets-values.env
```

The script will:
- ✅ Add secrets via API to /settings/secrets
- ✅ Add variables via API to /settings/variables
- ⚠️ Skip any that have empty values
- ❌ Report any API errors

### 6. Verify
Check the web UI:
- https://git.u-acres.com/nicholas/HaC/settings/secrets
- https://git.u-acres.com/nicholas/HaC/settings/variables

Then trigger a test workflow:
- https://git.u-acres.com/nicholas/HaC/actions

## Priority Order

If you can't find all 115 values immediately, prioritize these for core infrastructure:

### Critical (Core infrastructure - must restore first)
1. `DOMAIN_NAME` - u-acres.com
2. `CERTRESOLVER` - cloudflare
3. `TZ` - America/Chicago
4. `GIT_DB_PASSWORD` - For Forgejo itself
5. `POSTGRES_USER` / `POSTGRES_DB` - git / git
6. `CLOUDFLARE_DNS_API_TOKEN` - For Traefik cert generation
7. `CLOUDFLARE_ZONE_API_TOKEN` - For DNS updates

### High Priority (Auth & monitoring)
8. `AUTHELIA_*` secrets (5 total) - SSO won't work without these
9. `LLDAP_*` secrets (3 total) - User directory backend
10. `HA_LONG_LIVED_TOKEN` - Home Assistant integration
11. `HA_URL` / `HA_HOST_IP` - For HA monitoring

### Medium Priority (Services)
12. Database passwords (9 total: *_DB_PASSWORD)
13. `PLEX_CLAIM` - Media server
14. `MQTT_*` (4 vars) - IoT integrations
15. NetBox configuration (13 secrets/vars)

### Low Priority (Optional features)
16. Govee integration (5 secrets)
17. VPN/OpenVPN (3 secrets)
18. Wazuh security (5 secrets)
19. AI/ML services (5 vars)

## Finding Specific Values

### Database Passwords
Check running postgres containers:
```bash
# On docker-critical
docker exec -it git-db env | grep POSTGRES
docker exec -it authelia-db env | grep POSTGRES
docker exec -it vikunja-db env | grep POSTGRES
```

### Authelia Secrets
Check Authelia config:
```bash
cat /srv/docker/Docker-Critical/Auth/authelia-config/configuration.yml
cat /srv/authelia/config/configuration.yml
```

### Home Assistant Token
Generate a new Long-Lived Access Token:
1. Go to https://ha.u-acres.com/profile
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Copy and add as `HA_LONG_LIVED_TOKEN`

### Plex Claim Token
Get a new claim token (valid for 4 minutes):
```bash
# Visit https://www.plex.tv/claim/
# Copy the token and immediately deploy
```

## Troubleshooting

### "HTTP 401" when running script
- Check your `FORGEJO_TOKEN` is valid
- Regenerate token with proper scopes (repo, admin:repo_hook)

### "HTTP 404" when running script
- Verify repo owner/name: nicholas/HaC
- Check if Forgejo is accessible: curl https://git.u-acres.com

### Workflows still failing after restoration
- Check workflow logs: https://git.u-acres.com/nicholas/HaC/actions
- Look for specific missing variable error
- Add that secret/variable manually via web UI

### Can't find a specific value
- Leave it empty in secrets-values.env (script will skip it)
- Generate a new random value for secrets (uuid, openssl rand -hex 32)
- Redeploy the affected service after adding the value

## Manual Addition (Web UI)

If you prefer to add secrets/variables manually:

1. Go to https://git.u-acres.com/nicholas/HaC/settings/secrets
2. Click "Add Secret"
3. Enter Name (e.g., `GIT_DB_PASSWORD`) and Value
4. Click "Add Secret"
5. Repeat for each secret

Same process for variables at:
https://git.u-acres.com/nicholas/HaC/settings/variables

## Files in This Directory

- `scan-workflows.sh` - Extracts secrets/vars from workflow files
- `restore-forgejo-secrets.sh` - Batch adds via API
- `secrets-values.env.template` - Template to fill in
- `required-secrets.txt` - Generated list of 59 secrets
- `required-vars.txt` - Generated list of 56 variables
- `README.md` - This file

## Security Notes

- **NEVER commit `secrets-values.env` to git**
- It's already in `.gitignore`
- After restoration, delete the file: `rm secrets-values.env`
- Store credentials in a password manager (Vaultwarden, Bitwarden)
- Rotate any secrets that may have been compromised

## Next Steps After Restoration

1. Monitor workflow queue: https://git.u-acres.com/nicholas/HaC/actions
2. Check runner logs on hosts:
   ```bash
   # docker-critical
   sudo journalctl -u act_runner -f

   # docker-noncritical
   sudo journalctl -u act_runner -f
   ```
3. Manually trigger any failed workflows
4. Verify critical services are deployed correctly:
   - Forgejo (obviously working if you're reading this)
   - Authelia SSO
   - Home Assistant
   - Traefik proxies
   - Plex media
