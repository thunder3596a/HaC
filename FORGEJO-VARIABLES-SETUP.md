# Forgejo Variables Setup

This document lists the variables and secrets that need to be configured in Forgejo for the Docker update workflows.

## Repository Variables

Go to: Repository Settings → Actions → Variables

Add the following variables:

| Variable Name | Description | Example Value |
|--------------|-------------|---------------|
| `DOMAIN_NAME` | Your domain name | `example.com` |
| `CERTRESOLVER` | Traefik cert resolver | `cloudflare` |
| `TZ` | Timezone | `America/Chicago` |
| `CLOUDFLARE_EMAIL` | Cloudflare account email | `user@example.com` |
| `LETS_ENCRYPT_EMAIL` | Let's Encrypt email | `user@example.com` |
| `HA_URL` | Home Assistant URL | `https://ha.example.com` |
| `WAZUH_VERSION` | Wazuh version (optional) | `4.14.3` |
| `WAZUH_INDEXER_USERNAME` | Wazuh indexer admin username (optional) | `admin` |
| `WAZUH_API_USERNAME` | Wazuh API username (optional) | `wazuh-wui` |

## Repository Secrets

Go to: Repository Settings → Actions → Secrets

Add the following secrets:

| Secret Name | Description | Where to Get It |
|------------|-------------|-----------------|
| `HOMEASSISTANT_MARIADB_ROOT_PASSWORD` | MariaDB root password | Your database config |
| `HOMEASSISTANT_MARIADB_PASSWORD` | MariaDB HA user password | Your database config |
| `CLOUDFLARE_DNS_API_TOKEN` | Cloudflare DNS API token | Cloudflare Dashboard → API Tokens |
| `CLOUDFLARE_ZONE_API_TOKEN` | Cloudflare Zone API token | Cloudflare Dashboard → API Tokens |
| `HA_LONG_LIVED_TOKEN` | Home Assistant long-lived token | HA → Profile → Long-Lived Access Tokens |
| `forgejo_token` | Forgejo API token with "token " prefix | Forgejo → Settings → Applications |
| `forgejo_workflow_url_critical` | Critical workflow dispatch URL | See below |
| `forgejo_workflow_url_noncritical` | NonCritical workflow dispatch URL | See below |
| `forgejo_workflow_url_apply_critical` | Apply updates critical URL | See below |
| `forgejo_workflow_url_apply_noncritical` | Apply updates noncritical URL | See below |
| `WAZUH_INDEXER_PASSWORD` | Wazuh indexer admin password | Generate strong password |
| `WAZUH_API_PASSWORD` | Wazuh API password (used for dashboard login) | Generate strong password |

## Forgejo Workflow URLs

Format: `https://YOUR_FORGEJO_URL/api/v1/repos/OWNER/REPO/actions/workflows/WORKFLOW_FILE/dispatches`

Examples:
```
forgejo_workflow_url_critical:
https://git.example.com/api/v1/repos/username/HaC/actions/workflows/check-updates-critical.yml/dispatches

forgejo_workflow_url_apply_critical:
https://git.example.com/api/v1/repos/username/HaC/actions/workflows/apply-updates-critical.yml/dispatches
```

## Forgejo Token Format

**Important:** The token must include the "token " prefix:

```yaml
forgejo_token: "token YOUR_API_TOKEN_HERE"
```

To create a Forgejo token:
1. Go to Forgejo → Settings → Applications
2. Create new token with repository and workflow permissions
3. Copy the token
4. In Home Assistant secrets.yaml, add: `forgejo_token: "token YOUR_COPIED_TOKEN"`

## Docker Socket Access

The workflows need access to the Docker socket. This is configured in the runner, not in variables.

If using Docker socket proxy:
- No special configuration needed
- Workflows use `http://localhost:2375`

If using direct socket mount:
- Ensure the runner has access to `/var/run/docker.sock`
- Mount it in the runner container configuration

## Security Notes

1. **Never commit these values to git** - they're in .gitignore
2. **Use separate tokens** for different purposes (Cloudflare DNS vs Zone)
3. **Rotate tokens periodically** for security
4. **Use read-only tokens** where possible (e.g., HA notifications)
5. **Restrict token scopes** to only what's needed

## Testing Variables

After adding variables, test with:

```bash
# In Forgejo Actions runner
echo $DOMAIN_NAME
echo $TZ
echo $CLOUDFLARE_EMAIL
```

Secrets won't be visible but will be available to workflows.

## Troubleshooting

### "Variable not found" errors
- Check variable name spelling (case-sensitive)
- Ensure variables are set at repository level, not user level
- Restart workflow after adding variables

### "Invalid token" errors
- Verify token has "token " prefix
- Check token hasn't expired
- Ensure token has correct permissions

### "Cannot connect to Docker"
- Verify runner has Docker socket access
- Check `http://localhost:2375/containers/json` works
- Review runner logs for connection errors
