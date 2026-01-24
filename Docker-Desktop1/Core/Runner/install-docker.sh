#!/bin/sh
# Install Docker CLI in Alpine-based containers
if ! command -v docker >/dev/null 2>&1; then
    echo "Installing Docker CLI..."
    apk add --no-cache docker-cli docker-cli-compose curl
fi