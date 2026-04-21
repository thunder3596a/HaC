# HaC — Copilot Context

## Assistant Policy

- Approved assistants right now: GitHub Copilot and Microsoft Copilot.
- Strategic direction: move toward fully local Ollama-only operation.
- Do not introduce, require, or depend on Claude or any other AI assistant tooling.

## Documentation

All setup guides and configuration references are in **Outline** at `https://docs.u-acres.com`.
When working on this repo, consult Outline for patterns and context before suggesting changes.

Key docs:

- [Service Creation Guide](https://docs.u-acres.com/doc/service-creation-guide-4UODNqOvPN) — compose skeletons, hard rules, network selection, deployment workflow patterns
- [Forgejo Variables Reference](https://docs.u-acres.com/doc/forgejo-variables-reference-nvgshbtzQK) — all required variables and secrets
- [Docker Container Monitoring](https://docs.u-acres.com/doc/docker-container-monitoring-LGL1OrDfm8) — `ha.*` label system
- [Overview & Architecture](https://docs.u-acres.com/doc/overview-architecture-cNdSRv2VKa) — full service list and host layout

## What This Repo Is

Infrastructure-as-code for a self-hosted homelab. Every service is a Docker Compose file deployed automatically via Forgejo CI/CD on push to `main`.

Two hosts:
- **hac-critical** (`docker-critical` runner) — Home automation, auth, networking, core infra
- **hac-noncritical** (`docker-noncritical` runner) — Media, tools, security, AI

## Hard Rules for Compose Files

1. No `version:` key (Compose v2)
2. `restart: unless-stopped` on every service
3. No hardcoded secrets — use `${VAR_NAME}` — values come from Forgejo vars/secrets
4. No `.env` files committed
5. External networks only — `external: true`, never create inline
6. Absolute volume paths only — `/srv/...`, never `./data`
7. Every container (including databases and sidecars) must have `ha.*` monitoring labels AND `container_name`

## Required Labels on Every Container

```yaml
labels:
  - ha.monitor=true
  - ha.category=<home|media|tools|networking|auth|automation|security>
  - ha.compose-file=Docker-Critical/Category/Service/service.yml  # full path from repo root
  - ha.service-name=<key under services: in this file>
```

Do not add `com.centurylinklabs.watchtower.*` labels. Image updates are managed by Forgejo update workflows.

## Traefik Labels (every HTTP service)

```yaml
labels:
  - traefik.enable=true
  - traefik.http.routers.myservice.entrypoints=websecure
  - traefik.http.routers.myservice.rule=Host(`myservice.${DOMAIN_NAME}`)
  - traefik.http.routers.myservice.service=myservice
  - traefik.http.routers.myservice.tls.certresolver=${CERTRESOLVER:-cloudflare}
  - traefik.http.routers.myservice.tls.domains[0].main=myservice.${DOMAIN_NAME}
  - traefik.http.services.myservice.loadbalancer.server.port=<PORT>
  # Optional SSO:
  - traefik.http.routers.myservice.middlewares=authentik@docker
```

Router name rules: all lowercase, no hyphens (`ittools` not `it-tools`).

## Networks

**hac-critical:** `homeproxy`, `toolsproxy`, `gitproxy`, `authnet`
**hac-noncritical:** `mediaproxy`, `toolsproxy`, `torrentproxy`, `aiproxy`, `secproxy`, `mcpnet`

Each service connects to exactly one proxy network matching its category.
Internal services (DBs, caches) join the same network as their parent — no Traefik labels.

## Deployment Workflow Pattern

```yaml
name: Deploy MyService
on:
  push:
    branches: [main]
    paths:
      - "Docker-Critical/Category/ServiceDir/**"
      - ".forgejo/workflows/deploy-myservice.yml"
  workflow_dispatch:
jobs:
  deploy:
    runs-on: docker-critical   # or docker-noncritical
    defaults:
      run:
        shell: sh
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        working-directory: "./Docker-Critical/Category/ServiceDir"
        env:
          TZ: ${{ vars.TZ }}
          DOMAIN_NAME: ${{ vars.DOMAIN_NAME }}
          CERTRESOLVER: ${{ vars.CERTRESOLVER }}
          MY_SECRET: ${{ secrets.MY_SECRET }}
        run: |
          docker compose -p myservice -f myservice.yml up -d --force-recreate
```

## Storage

- `/srv/<service>/` — NVMe, fast (configs, databases)
- `/mnt/hdd/` — HDD (logs, archives, ZIM files) — hac-critical only
- `/mnt/Pool01/data/media/` — Shared media (movies, tv, music, books)
- `/mnt/data/` — NFS (Immich photos, Wazuh archives) — hac-noncritical

## Key Variables Available in Workflows

`DOMAIN_NAME`, `CERTRESOLVER`, `PUID` (568), `PGID` (568), `TZ` (America/Chicago), `HA_URL` (`http://localhost:8123`), `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER`, `POSTGRES_USER`, `POSTGRES_DB`, `OLLAMA_BASE_URL`, `VIKUNJA_URL`, `N8N_URL`, `HOMEBOX_URL`

## Anti-Patterns to Avoid

- `.env` files in the repo
- `docker-compose` (v1) — use `docker compose` (v2)
- Relative volume paths (`./data:/data`)
- Missing `ha.*` labels on DB/sidecar containers
- Default bridge networks instead of external proxy networks
- Hardcoded domain names instead of `${DOMAIN_NAME}`
- Manual SSH deploys instead of Forgejo workflows
- `find /srv` on docker-critical (hangs on overlay mounts)

## Issue Tracking

- Track all planned work, defects, and security findings in Forgejo Issues.
- Create or update a Forgejo issue before making non-trivial changes.
- For big efforts and net-new features, create a Forgejo Project before implementation begins.
- If Forgejo Projects are unavailable for the repo, create an epic issue and treat it as the project tracker.
- Link all child issues/tasks to the project (or epic fallback) and execute work against those linked items.
- Use epics with linked child issues for multi-step work.
- Keep issue acceptance criteria and status aligned with delivered changes.
- If an issue is fully fixed, close it in Forgejo in the same work session.
- Before closing, add a completion note summarizing root cause, changes made, and verification results.
- Fill relevant issue fields before close (at minimum: assignee, status/state, and any available labels/milestone that apply).
- Do not mirror issues to GitHub or split tracking across Forgejo and GitHub.
- For new work, always plan the task first and execute against the tracked Forgejo issue.
