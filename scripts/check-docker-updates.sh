#!/bin/bash
# Check for Docker image updates
# Compares local image digest with remote registry digest
# Outputs JSON with update information

set -e

# Function to get remote image digest
get_remote_digest() {
    local image="$1"
    local tag="${2:-latest}"

    # Handle different registry types
    if [[ "$image" == ghcr.io/* ]]; then
        # GitHub Container Registry
        local repo="${image#ghcr.io/}"
        curl -s "https://ghcr.io/v2/${repo}/manifests/${tag}" \
            -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
            2>/dev/null | grep -o '"digest":"[^"]*"' | head -1 | cut -d'"' -f4
    elif [[ "$image" == */* ]]; then
        # Docker Hub with namespace
        local token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${image}:pull" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        curl -s "https://registry-1.docker.io/v2/${image}/manifests/${tag}" \
            -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
            -H "Authorization: Bearer ${token}" \
            2>/dev/null | grep -o '"digest":"[^"]*"' | head -1 | cut -d'"' -f4
    else
        # Docker Hub library image
        local token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/${image}:pull" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        curl -s "https://registry-1.docker.io/v2/library/${image}/manifests/${tag}" \
            -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
            -H "Authorization: Bearer ${token}" \
            2>/dev/null | grep -o '"digest":"[^"]*"' | head -1 | cut -d'"' -f4
    fi
}

# Function to get local image digest
get_local_digest() {
    local image="$1"
    docker inspect --format='{{index .RepoDigests 0}}' "$image" 2>/dev/null | cut -d'@' -f2
}

# Function to check a single container
check_container() {
    local container="$1"
    local image=$(docker inspect --format='{{.Config.Image}}' "$container" 2>/dev/null)

    if [ -z "$image" ]; then
        return
    fi

    # Parse image and tag
    local tag="latest"
    if [[ "$image" == *:* ]]; then
        tag="${image##*:}"
        image="${image%:*}"
    fi

    local local_digest=$(get_local_digest "${image}:${tag}")
    local remote_digest=$(get_remote_digest "$image" "$tag")

    if [ -n "$local_digest" ] && [ -n "$remote_digest" ] && [ "$local_digest" != "$remote_digest" ]; then
        echo "{\"container\":\"$container\",\"image\":\"$image\",\"tag\":\"$tag\",\"local\":\"${local_digest:0:19}\",\"remote\":\"${remote_digest:0:19}\"}"
    fi
}

# Main
CONTAINERS="${1:-}"
UPDATES=()

if [ -z "$CONTAINERS" ]; then
    # Check all running containers
    CONTAINERS=$(docker ps --format '{{.Names}}')
fi

for container in $CONTAINERS; do
    result=$(check_container "$container")
    if [ -n "$result" ]; then
        UPDATES+=("$result")
    fi
done

# Output as JSON array
if [ ${#UPDATES[@]} -eq 0 ]; then
    echo "[]"
else
    echo "[$(IFS=,; echo "${UPDATES[*]}")]"
fi
