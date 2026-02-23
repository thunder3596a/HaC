#!/bin/bash

# Setup Forgejo runner for docker-noncritical
set -e

RUNNER_DIR="/srv/forgejo-runner-noncritical"
INSTANCE_URL="https://git.u-acres.com"
REGISTRATION_TOKEN="KCrVPIyYkF_ibCnaeyfP-7XJm9B5GqZRWy7NbbODtGG"
RUNNER_NAME="docker-noncritical"
RUNNER_LABELS="docker-noncritical:host"

echo "[1/4] Creating runner directory..."
mkdir -p "$RUNNER_DIR"
chmod 755 "$RUNNER_DIR"

echo "[2/4] Registering runner with Forgejo..."
docker run --rm --entrypoint "" --network host \
  -v "$RUNNER_DIR":/data \
  gitea/act_runner:latest \
  sh -c "cd /data && act_runner register --no-interactive --instance $INSTANCE_URL --token $REGISTRATION_TOKEN --name $RUNNER_NAME --labels $RUNNER_LABELS"

echo "[3/4] Verifying .runner file..."
if [ -f "$RUNNER_DIR/.runner" ]; then
  echo "✓ Runner configuration created successfully"
  cat "$RUNNER_DIR/.runner" | head -10
else
  echo "✗ Runner configuration not found!"
  exit 1
fi

echo "[4/4] Building custom runner image with Node.js..."
cd /srv/forgejo-runner-noncritical
docker build -t forgejo-runner-noncritical:latest -f Dockerfile . 2>&1 | tail -5

echo ""
echo "✓ Setup complete! Starting daemon..."
docker run -d --name forgejo-runner-noncritical \
  --restart unless-stopped \
  --network host \
  -v "$RUNNER_DIR":/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  forgejo-runner-noncritical:latest

sleep 2
echo "✓ Runner started. Checking status..."
docker logs --tail 10 forgejo-runner-noncritical

echo ""
echo "✓ docker-noncritical runner deployment complete!"
