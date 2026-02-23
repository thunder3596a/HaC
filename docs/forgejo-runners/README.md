# Forgejo Runners Setup & Documentation

This directory contains documentation for deploying and managing Forgejo CI/CD runners on the homelab infrastructure.

## Overview

The homelab infrastructure uses two Forgejo runners for distributed CI/CD job execution:

- **docker-critical**: Runner on the critical infrastructure host (mission-critical services)
- **docker-noncritical**: Runner on the noncritical infrastructure host (media, AI, tools)

Both runners are containerized using custom Docker images that extend `gitea/act_runner:latest` with Node.js and other utilities required for GitHub Actions compatibility.

## Architecture

```
┌─────────────────────────────────────────────────┐
│       Forgejo Instance                          │
│   (git.example.com:3000 / Port 2222)            │
│                                                 │
│  ├─ Database: PostgreSQL 15 (git-db)            │
│  └─ Git Repositories: /srv/git/data             │
├─────────────────────────────────────────────────┤
│            Action Runners                       │
│                                                 │
│  Runner 2: docker-critical (ID 2)               │
│  ├─ Host: HOST_CRITICAL                         │
│  ├─ Network: host mode                          │
│  ├─ Container: forgejo-runner-critical          │
│  ├─ UUID: <REDACTED>                             │
│  ├─ Labels: docker-critical:host                │
│  └─ Storage: /srv/forgejo-runner-critical       │
│                                                 │
│  Runner 3: docker-noncritical (ID 3)            │
│  ├─ Host: HOST_NONCRITICAL                      │
│  ├─ Network: host mode                          │
│  ├─ Container: forgejo-runner-noncritical       │
│  ├─ UUID: <REDACTED>                             │
│  ├─ Labels: docker-noncritical:host             │
│  └─ Storage: /srv/forgejo-runner-noncritical    │
└─────────────────────────────────────────────────┘
```

## Runner Configuration

### Custom Docker Image

Both runners use a custom Docker image that includes:

```dockerfile
FROM gitea/act_runner:latest

# Install Node.js and dependencies
RUN apk add --no-cache \
    nodejs \
    npm \
    git \
    curl

WORKDIR /data
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["sh", "-c", "cd /data && exec act_runner daemon"]
```

**Why Node.js?** The GitHub Actions `checkout@v4` action requires Node.js to execute. By including Node.js in the runner image, workflows using standard GitHub Actions will work correctly.

### Environment & Resources

**Resource Limits:**
- Memory: 1GB limit, 256MB reservation
- CPU: 2.0 cores limit, 0.5 cores reservation

**Environment Variables:**
```yaml
GITEA_INSTANCE_URL=https://git.example.com
GITEA_RUNNER_NAME=docker-critical  # or docker-noncritical
GITEA_RUNNER_LABELS=docker-critical  # or docker-noncritical
```

**Network Mode:** Host network mode allows runners to:
- Access Docker socket directly (`/var/run/docker.sock`)
- Execute Docker commands within jobs
- Communicate with services on the host

## Deployment

### Docker-Critical Runner

The docker-critical runner is deployed via:
- **Compose File:** `Docker-Critical/Tools/Runner/runner.yml`
- **Dockerfile:** `Docker-Critical/Tools/Runner/Dockerfile`
- **Status:** ✅ Running and operational

**To redeploy docker-critical runner:**

```bash
ssh user@HOST_CRITICAL

# Stop and remove old container
docker stop forgejo-runner-critical && docker rm forgejo-runner-critical

# Rebuild image
cd /srv/runner-critical
docker build -t forgejo-runner-critical:latest -f Dockerfile .

# Start new container
docker run -d --name forgejo-runner-critical \
  --restart unless-stopped \
  --network host \
  -v /srv/forgejo-runner-critical:/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  forgejo-runner-critical:latest

# Verify
docker logs --tail 20 forgejo-runner-critical
```

### Docker-Noncritical Runner

The docker-noncritical runner is deployed via:
- **Compose File:** `Docker-NonCritical/Tools/Runner/runner.yml`
- **Dockerfile:** `Docker-NonCritical/Tools/Runner/Dockerfile`
- **Status:** ✅ Running and operational

**To redeploy docker-noncritical runner:**

The deployment script `setup-runner-noncritical.sh` handles:
1. Creating runner directory (`/srv/forgejo-runner-noncritical`)
2. Registering runner with Forgejo
3. Building custom Docker image
4. Starting daemon container

```bash
ssh user@HOST_NONCRITICAL

# Copy and run setup script (with sudo/root access)
su root
bash setup-runner-noncritical.sh

# Verify
docker ps | grep runner
docker logs --tail 20 forgejo-runner-noncritical
```

**Note:** The `setup-runner-noncritical.sh` script references a registration token. For security, this token is NOT stored in the repository. See "Runner Registration" section below.

## Runner Registration

### Generating Registration Tokens

Registration tokens are created in Forgejo's database and allow runners to authenticate on first connection.

**To generate a new registration token:**

1. **Connect to Forgejo database:**
```bash
ssh user@HOST_CRITICAL
docker exec git-db psql -U git -d git
```

2. **Insert new token** (replace with a unique value):
```sql
INSERT INTO action_runner_token (token, owner_id, repo_id, is_active, created, updated)
VALUES (
  'YOUR_UNIQUE_TOKEN_HERE',
  0,  -- owner_id (0 = instance-wide)
  0,  -- repo_id (0 = not repo-specific)
  true,  -- is_active
  extract(epoch from now()),
  extract(epoch from now())
);
```

3. **List existing tokens:**
```sql
SELECT id, token, is_active FROM action_runner_token ORDER BY id DESC;
```

4. **View registered runners:**
```sql
SELECT id, uuid, name FROM action_runner ORDER BY id DESC;
```

### Runner Registration Flow

1. **Create registration token** (database)
2. **Run registration command:**
```bash
docker run --rm --entrypoint "" --network host \
  -v /srv/forgejo-runner-HOSTNAME:/data \
  gitea/act_runner:latest \
  sh -c "cd /data && act_runner register --no-interactive \
    --instance https://git.example.com \
    --token YOUR_REGISTRATION_TOKEN \
    --name RUNNER_NAME \
    --labels RUNNER_LABELS"
```

3. **Verify .runner file created:**
```bash
cat /srv/forgejo-runner-HOSTNAME/.runner
```

The `.runner` file will contain:
- `id`: Runner ID from database
- `uuid`: Unique identifier
- `token`: Internal authentication token (auto-generated during registration)
- `address`: Forgejo instance URL
- `labels`: Runner labels for job targeting

4. **Start daemon:**
```bash
docker run -d --name forgejo-runner-HOSTNAME \
  --restart unless-stopped \
  --network host \
  -v /srv/forgejo-runner-HOSTNAME:/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  forgejo-runner-HOSTNAME:latest
```

## Workflow Configuration

Workflows can target specific runners using the `runs-on` field:

```yaml
jobs:
  deploy-critical:
    runs-on: docker-critical
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to critical
        run: docker compose up -d

  deploy-noncritical:
    runs-on: docker-noncritical
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to noncritical
        run: docker compose up -d
```

Example workflows in this repository:
- `.forgejo/workflows/deploy-plex.yml` - Runs on docker-critical
- `.forgejo/workflows/deploy-runner-critical.yml` - Manages critical runner
- `.forgejo/workflows/deploy-runner-noncritical.yml` - Manages noncritical runner

## Monitoring & Troubleshooting

### Check Runner Status

**On docker-critical:**
```bash
ssh user@HOST_CRITICAL

# View container status
docker ps | grep runner
docker stats forgejo-runner-critical

# View logs
docker logs --tail 100 forgejo-runner-critical

# Check in Forgejo admin panel
# Login as admin → Site Administration → Actions → Runners
```

**On docker-noncritical:**
```bash
ssh user@HOST_NONCRITICAL

# With root access (required)
su root

# View container status
docker ps | grep runner
docker stats forgejo-runner-noncritical

# View logs
docker logs --tail 100 forgejo-runner-noncritical
```

### Common Issues

**Issue: "Cannot find: node in PATH"**
- **Cause:** Runner image missing Node.js
- **Solution:** Rebuild image using custom Dockerfile with Node.js included

**Issue: "permission denied while trying to connect to the docker API"**
- **Cause:** User doesn't have Docker socket permissions
- **Solution:** Run Docker commands with sudo/root or add user to docker group

**Issue: "runner registration token not found"**
- **Cause:** Token was deleted or doesn't exist in database
- **Solution:** Create new registration token using the registration flow above

**Issue: Container keeps restarting**
- **Cause:** .runner file missing or invalid
- **Solution:** Check `/srv/forgejo-runner-HOSTNAME/.runner` exists and has valid JSON

### Database Queries

**View all runners:**
```sql
SELECT id, uuid, name, last_online FROM action_runner ORDER BY id;
```

**View runner tokens:**
```sql
SELECT id, token, is_active FROM action_runner_token;
```

**View runner activity:**
```sql
SELECT id, name, last_online, last_active FROM action_runner WHERE last_online > 0;
```

## Maintenance

### Updating Runner Images

When updating the base `gitea/act_runner` image or dependencies:

1. **Update Dockerfile** in `Docker-Critical/Tools/Runner/` and `Docker-NonCritical/Tools/Runner/`
2. **Rebuild images:**
   - Critical: `docker build -t forgejo-runner-critical:latest Docker-Critical/Tools/Runner/`
   - Noncritical: `docker build -t forgejo-runner-noncritical:latest Docker-NonCritical/Tools/Runner/`
3. **Restart runners:** Stop old container, start new one with rebuilt image
4. **Verify:** Check logs for successful connection to Forgejo

### Rotating Registration Tokens

1. Generate new token in database
2. Re-register runner with new token
3. Delete old token from database

### Scaling Runners

To add additional runners:

1. Create registration token
2. Create new runner directory
3. Register runner
4. Start daemon container
5. Verify in Forgejo admin panel

## Security Notes

⚠️ **Important Security Considerations:**

- **Registration tokens** are secrets and should not be committed to version control
- **.runner files** contain internal authentication tokens and should not be exposed
- **Host network mode** allows full access to Docker socket - only use with trusted runners
- **Database credentials** should be managed via environment variables or secrets
- **SSH keys** for host access should use key-based authentication

This repository uses `.gitignore` to exclude:
- `insert_token*.sql` - Registration token insertion scripts
- `.runner.json` - Example runner configuration
- `setup-runner*.sh` - Setup scripts (if they contain tokens)

## References

- [Forgejo Actions Documentation](https://docs.forgejo.org/user/actions/)
- [Gitea Act Runner](https://gitea.com/gitea/act_runner)
- [GitHub Actions Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

## Contacts & Support

For issues with:
- **Runner deployment:** Check logs with `docker logs forgejo-runner-HOSTNAME`
- **Workflow configuration:** Review `.forgejo/workflows/` examples
- **Database issues:** Access git-db container to debug SQL issues
- **Host access:** SSH to respective host with proper credentials
