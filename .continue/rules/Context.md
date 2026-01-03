# Context File for Homelab

This file documents repository structure, deployment notes and important values for quick reference.

Guidance

AI should assume:

### A. All Compose files live under `docker/`
### B. One service per file
### C. All deployments use Forgejo workflows
### D. No `.env` files — use `${VAR}`
### E. All secrets come from Forgejo
### F. All services must join correct networks
### G. Persistent data lives under `/mnt/Apps/<Service>`
### H. AI should generate:
- Compose files
- Forgejo workflows
- Traefik labels
- SMTP blocks
- Network definitions
- Volume mappings
- GitOps-safe patterns

# GitOps Model (Forgejo)

## Runner
- Self-hosted on `truenas01`
- Labels: `docker`, `linux-x64`
- Executes `docker compose` directly on host

## Deployment Model
- Repo is checked out inside runner workspace
- Workflows run `docker compose -f <file> up -d`
- No persistent clone on host
- No `.env` files — all secrets come from Forgejo

## Repo
- **Root:** `Home-Lab\docker`
- **OneDrive Path:** `c:\Users\Nicho\OneDrive\Home-Lab\docker`
- **Description:** Home-Lab docker configs and deployment.
- **Maintainer:** Nicholas

# Homelab

This document is the top-level reference for the Homelab. It includes physical infrastructure details (router and networks) and important repositories and workflows (Docker repo as a sub-item).

- **Maintainer:** Nicholas
- **Primary workspace root:** `c:\Users\Nicho\OneDrive\Home-Lab`

### Repositories
- **Docker repo (configs & deployment):** `c:\Users\Nicho\OneDrive\Home-Lab\docker`
	- Description: Docker configs and deployment files for TrueNAS Scale (`truenas01`)
	- Key files:
		- `docker/Networking/proxy.yml`
		- `docker/Networking/torrent.yml`
		- `docker/Home/Doomsday/library.yml`
		- `docker/Tools/Git - Forgejo/git.yml`
		- `.forgejo/workflows/deploy-docker.yml`
		- `docker/Media/<service>/<service>.yml` (per-service compose files)
		- `docker/Tools/Git - Forgejo Runner/runner.yml`

## Physical Infrastructure

This section records the physical network layout and the primary router appliance along with servers.

### Router: OpnSense
- **Device** HP SFF Desktop
- **Role:** OpnSense (primary router / firewall)
- **Host Name:** `fw.u-acres.com`
- **Hardware Features:** Dual SFP+
- **Services:** 'Firewall, Unbound DNS, Kea DHCP, NTOPNG, Crowdsec

### Interfaces & Addresses
- **DMZ**: None
- **WAN**: `76.156.32.86/22`
- **LAN**: `192.168.19.2/24`
- **IoT**: `192.168.101.2/24`
- **Guest**: `192.168.200.2/24`
- **Cameras**: `192.168.51.2/24`
- **Tailscale**: `100.74.172.27/32`
- **Tailscale (IPv6)**: `fd7a:115c:a1e0::5c01:ac1d/48`
- **Work**: `192.168.20.2/24`

### TRUENAS01: TrueNas Community Edition
- **Device**: HP DL360 Gen9
- **Role**: NAS, Docker Host
- **Host Name:** 'Truenas01.u-acres.com'
	- Key Files/Paths
		- '/mnt/Apps' is the path to application configuration files
		- '/mnt/Pool01/data' is the path to application data and media.

> Note: Interface addresses above are the gateway/interface addresses used by OpnSense. Adjust host allocations or DHCP static mappings as needed in OpnSense configuration.

## Environment & Runner
- **Host (for Docker deployments):** `truenas01`
- **Forgejo runner:** self-hosted runner present on `truenas01`, label `docker, linux-x64`


## Deploy (Docker repo)
- **Workflow path:** `.forgejo/workflows/deploy-docker.yml`
- **Deployment model:** runner-local — the Forgejo runner checks out the repo in the job workspace and runs `docker compose` on the runner host. No repository clone should be required on the host outside of the runner job.
- **Working Example:** `.forgejo/workflows/deploy-karakeep.yml`

## Networks used by traefik (Docker)
- `homeproxy`
	- used for home services like norish and homebox.
- `mediaproxy`
	- entertainment, media.
- `proxy`
- `toolsproxy`
	 - used for backend services.
- `torrentproxy`
	- used for anything we dont want publicly visible like torrenting, using usenet, etc.
- `aiproxy`
	- llm services
- `secproxy`
	- security tooling resides here.
- `gitproxy`
	- For git ops, forgejo networking.
- 'authnet'
	- Only for priveleged networking, LDAP, AUTH, etc.

## Secrets & env (used by workflows / Traefik)

### Environment / Config variables
- `DOMAIN_NAME`              — `u-acres.com`
- `FORGEJO_RUNNER_ADDRESS`   — `https://git.u-acres.com`
- `FORGEJO_RUNNER_INSTANCE`  — Same as above or instance URL
- `PUID` / `PGID`            — 568/568
- `TZ`                       — 'America/Chicago'
## Notes
- Timezone is America/Chicago
- Domain is u-acres.com
-- I use sub domains for each service
- Traefik labels always
