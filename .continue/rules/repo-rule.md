---
description: Homelab context and GitOps rules for Nicholas
---

You are assisting with Nicholas's homelab, which is fully documented in `Context.md` at the root of the repo.

Always follow these rules:

- All Docker Compose files live under `/docker`
- One service per file
- No `.env` files — use `${VAR}` and assume secrets come from Forgejo
- All deployments use Forgejo workflows
- All services must join the correct Docker network as defined in `Context.md`
- Persistent data always goes under `/mnt/Apps/<Service>`
- Use GitOps-safe patterns only
- Never assume manual deployment; always generate workflow-compatible YAML
- SMTP config uses `smtp-relay:587` and app-specific senders
- Workflows run on `truenas01` with `docker` and `linux-x64` labels
- MCP server is available and should be used for repo context and file access

When generating anything, include:

1. Docker Compose file  
2. Forgejo workflow  
3. Traefik labels (if applicable)  
4. Required secrets/variables  

Always read `Context.md` before generating anything.
