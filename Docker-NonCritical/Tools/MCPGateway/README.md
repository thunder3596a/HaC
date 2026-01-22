# MCP Gateway Stack

A comprehensive Model Context Protocol (MCP) gateway implementation for integrating local LLMs (via Ollama) with various services in your homelab infrastructure.

## Overview

This stack provides a centralized MCP gateway powered by IBM's ContextForge, along with MCP servers for:

- **Home Assistant** - Smart home automation and control
- **n8n** - Workflow automation management
- **TP-Link Omada** - Network management (APs, switches, gateways)
- **OPNsense** - Firewall and router management
- **NetBox** - Infrastructure documentation and IPAM
- **HomeBox** - Inventory management

## Architecture

```
Local LLM (Ollama)
       ↓
MCP Gateway (ContextForge)
       ↓
  ┌────┴────┬────────┬──────────┬──────────┬─────────┬──────────┐
  ↓         ↓        ↓          ↓          ↓         ↓          ↓
Home     n8n     Omada    OPNsense    NetBox   HomeBox
Assistant
```

The MCP Gateway acts as a central hub that:
- Federates all MCP servers into a single endpoint
- Provides authentication and rate limiting
- Offers observability and monitoring
- Converts between different MCP transport protocols
- Includes an admin UI for management

## Prerequisites

1. **Running Services**: Ensure all target services are running and accessible:
   - Home Assistant
   - n8n
   - TP-Link Omada Controller
   - OPNsense
   - NetBox
   - HomeBox

2. **API Access**: Generate API tokens/credentials for each service

3. **Docker Network**: Ensure the `aiproxy` network exists (for connecting to Ollama)

## Setup

### 1. Create Environment File

Copy the example environment file and fill in your credentials:

```bash
cd Docker-NonCritical/Tools/MCPGateway
cp .env.example .env
```

Edit `.env` and configure:

- **MCP Gateway Database**: Set secure passwords for MariaDB
- **Home Assistant**: URL and long-lived access token
- **n8n**: URL and API key
- **Omada**: Controller URL, username, password, and site ID
- **OPNsense**: URL, API key, and API secret
- **NetBox**: URL and API token
- **HomeBox**: URL and API token

### 2. Create Data Directories

```bash
sudo mkdir -p /srv/mcp-gateway/{config,mariadb,redis}
sudo chown -R $(id -u):$(id -g) /srv/mcp-gateway
```

### 3. Start the Stack

```bash
docker compose up -d
```

### 4. Verify Services

Check that all containers are running:

```bash
docker compose ps
```

Access the MCP Gateway admin UI:
- Local: http://localhost:3000
- External: https://mcp.u-acres.com (via Traefik)

## MCP Server Capabilities

### Home Assistant MCP Server

Tools for controlling your smart home:
- Control lights, switches, and other devices
- Query sensor states
- Trigger automations
- Manage scenes

### n8n MCP Server

Workflow automation management:
- List workflows
- Get workflow details
- Activate/deactivate workflows
- Execute workflows
- View execution history

### TP-Link Omada MCP Server

Network infrastructure management:
- List sites, devices, and clients
- Get device information and statistics
- Reboot devices
- Block/unblock clients
- View SSIDs and network health

### OPNsense MCP Server

Firewall and router management:
- View firewall rules
- Monitor interfaces and traffic
- Manage aliases and port forwards
- Check system status
- View logs

### NetBox MCP Server

Infrastructure documentation (read-only):
- Query devices and IP addresses
- View sites, racks, and circuits
- Check VLAN and prefix information
- Retrieve cable connections

### HomeBox MCP Server

Inventory management:
- List and search items
- Create/update/delete items
- Manage locations and labels
- Track quantities and details

## Connecting Local LLMs

### Ollama Integration

To connect your local Ollama models to the MCP gateway:

1. Ensure Ollama is on the `aiproxy` network (it should be based on your existing setup)

2. Configure your LLM client to use the MCP gateway:

```json
{
  "mcpServers": {
    "homelab": {
      "url": "http://mcp-gateway:3000",
      "transport": "sse"
    }
  }
}
```

### Using with Continue.dev or Similar

For VS Code extensions like Continue:

```json
{
  "models": [
    {
      "title": "Ollama with MCP",
      "provider": "ollama",
      "model": "llama3.1:latest",
      "apiBase": "http://ollama:11434"
    }
  ],
  "experimental": {
    "modelContextProtocol": true,
    "mcpServers": {
      "homelab": {
        "url": "http://mcp-gateway:3000"
      }
    }
  }
}
```

## Security Considerations

1. **API Tokens**: Store all tokens securely in the `.env` file
2. **Network Isolation**: MCP servers are on a private `mcpnet` bridge network
3. **SSL/TLS**: Use HTTPS for all service connections when possible
4. **Rate Limiting**: MCP Gateway provides built-in rate limiting
5. **Authentication**: Gateway can enforce authentication policies

## Troubleshooting

### MCP Server Not Connecting

Check container logs:
```bash
docker compose logs <service-name>
```

### Authentication Failures

Verify your API tokens/credentials in the `.env` file match your service configurations.

### Network Issues

Ensure all services are accessible from the Docker host:
```bash
curl -k https://your-service-url/api
```

### Database Connection Issues

Check MariaDB container logs:
```bash
docker compose logs mariadb
```

## Updating

To update all services:

```bash
docker compose pull
docker compose up -d
```

Note: Watchtower is configured to auto-update most containers except custom-built MCP servers.

## Custom MCP Server Development

The custom MCP servers (n8n, Omada, HomeBox) are located in `./mcp-servers/` and can be modified as needed. After making changes:

```bash
docker compose build <service-name>
docker compose up -d <service-name>
```

## Resources

- [MCP Gateway Documentation](https://ibm.github.io/mcp-context-forge/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [Home Assistant MCP Server](https://github.com/tevonsb/homeassistant-mcp)
- [OPNsense MCP Server](https://github.com/Pixelworlds/opnsense-mcp-server)
- [NetBox MCP Server](https://github.com/netboxlabs/netbox-mcp-server)

## License

This configuration is provided as-is for personal homelab use.
