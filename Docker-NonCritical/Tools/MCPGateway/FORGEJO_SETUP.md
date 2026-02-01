# Forgejo Secrets and Variables Setup for MCP Gateway

This document lists all the Forgejo secrets and variables that need to be configured for the MCP Gateway deployment.

## How to Set Up in Forgejo

1. Navigate to your repository in Forgejo
2. Go to **Settings** → **Secrets** (for sensitive data) or **Variables** (for non-sensitive data)
3. Add each secret/variable listed below

## Required Secrets

Add these to **Settings → Secrets**:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `MCP_DB_ROOT_PASSWORD` | MariaDB root password for MCP Gateway database | `super_secure_root_password_123` |
| `MCP_DB_PASSWORD` | MariaDB user password for MCP Gateway | `secure_mcpuser_password_456` |
| `HA_LONG_LIVED_TOKEN` | Home Assistant long-lived access token | `eyJ0eXAiOiJKV1QiLCJhbGc...` |
| `OPNSENSE_API_KEY` | OPNsense API key | `XZt8D3kL9mN...` |
| `OPNSENSE_API_SECRET` | OPNsense API secret | `pQw7rS2vT8y...` |
| `NETBOX_API_TOKEN` | NetBox API token | `0123456789abcdef0123456789abcdef01234567` |
| `N8N_API_KEY` | n8n API key | `n8n_api_abc123xyz...` |
| `OMADA_USERNAME` | TP-Link Omada controller username | `admin` |
| `OMADA_PASSWORD` | TP-Link Omada controller password | `your_omada_password` |
| `HOMEBOX_TOKEN` | HomeBox API token | `hb_token_xyz789...` |

## Required Variables

Add these to **Settings → Variables**:

| Variable Name | Description | Example |
|---------------|-------------|---------|
| `DOMAIN_NAME` | Your base domain name | `example.com` |
| `CERTRESOLVER` | Traefik certificate resolver | `cloudflare` |
| `HOMEASSISTANT_URL` | Home Assistant URL | `http://homeassistant:8123` |
| `OPNSENSE_URL` | OPNsense firewall URL | `https://opnsense.local` |
| `NETBOX_URL` | NetBox URL | `http://netbox:8080` |
| `N8N_URL` | n8n workflow automation URL | `http://n8n:5678` |
| `OMADA_URL` | TP-Link Omada controller URL | `https://omada.local:8043` |
| `OMADA_SITE_ID` | Omada site ID | `Default` |
| `HOMEBOX_URL` | HomeBox inventory URL | `http://homebox:7745` |

## How to Generate Required Tokens

### Home Assistant Token
1. Log in to Home Assistant
2. Click your profile (bottom left)
3. Scroll to "Long-Lived Access Tokens"
4. Click "Create Token"
5. Name it "MCP Gateway" and copy the token

### OPNsense API Key/Secret
1. Log in to OPNsense web interface
2. Go to **System → Access → Users**
3. Edit your user or create a new API user
4. Scroll to "API Keys" section
5. Click "+" to generate a new key
6. Download or copy the key and secret

### NetBox API Token
1. Log in to NetBox
2. Click your username (top right) → **API Tokens**
3. Click "Add a token"
4. Set write permissions if needed (MCP server is read-only by default)
5. Save and copy the token

### n8n API Key
1. Log in to n8n
2. Go to **Settings → API**
3. Generate a new API key
4. Copy the key

### HomeBox Token
1. Log in to HomeBox
2. Go to **Profile → API Tokens** (or similar, depending on version)
3. Generate a new token
4. Copy the token

### Omada Username/Password
Use your existing Omada controller credentials (typically admin user).

## Deployment Workflow

The Forgejo workflow (`.forgejo/workflows/deploy-mcpgateway.yml`) will automatically:

1. Trigger on changes to `Docker-NonCritical/Tools/MCPGateway/**`
2. Build custom MCP servers (n8n, Omada, HomeBox)
3. Validate all required secrets and variables are set
4. Deploy the stack using docker compose
5. Only redeploy if the image or configuration has changed

## Testing the Setup

After configuring all secrets and variables:

1. Push a change to trigger the workflow:
   ```bash
   git commit --allow-empty -m "Test MCP Gateway deployment"
   git push
   ```

2. Check the Forgejo Actions tab to see the workflow run

3. Verify deployment:
   ```bash
   docker ps | grep mcp
   ```

4. Access the MCP Gateway admin UI:
   - Local: http://your-server:3000
   - External: https://mcp.example.com (or your domain)

## Security Notes

- **Never commit secrets** to the repository - always use Forgejo secrets
- Rotate API tokens regularly
- Use read-only tokens where possible (especially for NetBox)
- Consider network isolation for sensitive MCP servers
- Review MCP gateway logs for unauthorized access attempts

## Troubleshooting

### Missing Secret Error
```
Missing required secret: HOMEASSISTANT_TOKEN
```
**Solution**: Add the missing secret in Forgejo Settings → Secrets

### Invalid Token Error in Container Logs
```
Error: Authentication failed
```
**Solution**: Regenerate the token and update the Forgejo secret

### Container Not Starting
Check logs:
```bash
docker logs mcp-homeassistant
docker logs mcp-gateway
```

### Network Connection Issues
Verify service URLs are accessible from the Docker host:
```bash
curl -k https://opnsense.local/api/
curl http://homeassistant:8123/api/
```

## Additional Resources

- [Forgejo Secrets Documentation](https://forgejo.org/docs/latest/)
- [MCP Gateway Documentation](https://ibm.github.io/mcp-context-forge/)
- [Home Assistant API](https://www.home-assistant.io/integrations/api/)
- [OPNsense API](https://docs.opnsense.org/development/api.html)
- [NetBox API](https://docs.netbox.dev/en/stable/integrations/rest-api/)
