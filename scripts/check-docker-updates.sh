#!/bin/bash
# Check for Docker image updates
# Compares local image digest with remote registry digest
# Outputs JSON with update information

set -e

# Function to get remote image digest using Docker-Content-Digest header
# This is more reliable than parsing manifest JSON
get_remote_digest() {
    local image="$1"
    local tag="${2:-latest}"
    local digest=""

    # Accept both single-arch and multi-arch manifests
    local accept_header="Accept: application/vnd.docker.distribution.manifest.v2+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.index.v1+json, application/vnd.oci.image.manifest.v1+json"

    # Handle different registry types
    if [[ "$image" == ghcr.io/* ]]; then
        # GitHub Container Registry - get token first (works for public images)
        local repo="${image#ghcr.io/}"
        local token=$(curl -s "https://ghcr.io/token?service=ghcr.io&scope=repository:${repo}:pull" 2>/dev/null | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$token" ]; then
            digest=$(curl -sI "https://ghcr.io/v2/${repo}/manifests/${tag}" \
                -H "$accept_header" \
                -H "Authorization: Bearer ${token}" \
                2>/dev/null | grep -i "docker-content-digest:" | tr -d '\r' | awk '{print $2}')
        fi
    elif [[ "$image" == */* ]]; then
        # Docker Hub with namespace
        local token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${image}:pull" 2>/dev/null | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$token" ]; then
            digest=$(curl -sI "https://registry-1.docker.io/v2/${image}/manifests/${tag}" \
                -H "$accept_header" \
                -H "Authorization: Bearer ${token}" \
                2>/dev/null | grep -i "docker-content-digest:" | tr -d '\r' | awk '{print $2}')
        fi
    else
        # Docker Hub library image
        local token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/${image}:pull" 2>/dev/null | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$token" ]; then
            digest=$(curl -sI "https://registry-1.docker.io/v2/library/${image}/manifests/${tag}" \
                -H "$accept_header" \
                -H "Authorization: Bearer ${token}" \
                2>/dev/null | grep -i "docker-content-digest:" | tr -d '\r' | awk '{print $2}')
        fi
    fi

    echo "$digest"
}

# Function to get local image digest from container
get_local_digest() {
    local container="$1"
    # Get the image ID from the container, then get the RepoDigests from that image
    local image_id=$(docker inspect --format='{{.Image}}' "$container" 2>/dev/null)
    if [ -n "$image_id" ]; then
        # Try to get RepoDigests (may be empty for locally built images)
        local digest=$(docker inspect --format='{{range .RepoDigests}}{{.}}{{"\n"}}{{end}}' "$image_id" 2>/dev/null | head -1 | cut -d'@' -f2)
        echo "$digest"
    fi
}

# Function to check a single container
check_container() {
    local container="$1"
    local full_image=$(docker inspect --format='{{.Config.Image}}' "$container" 2>/dev/null)

    if [ -z "$full_image" ]; then
        return 1
    fi

    # Parse image and tag
    local image="$full_image"
    local tag="latest"
    if [[ "$full_image" == *:* ]]; then
        tag="${full_image##*:}"
        image="${full_image%:*}"
    fi

    local local_digest=$(get_local_digest "$container")
    local remote_digest=$(get_remote_digest "$image" "$tag")

    # Debug output to stderr (won't affect JSON output)
    >&2 echo "Checking $container: image=$image:$tag local=${local_digest:0:19}... remote=${remote_digest:0:19}..."

    if [ -n "$local_digest" ] && [ -n "$remote_digest" ] && [ "$local_digest" != "$remote_digest" ]; then
        # Output single JSON object (not array) - caller will build array
        echo "{\"container\":\"$container\",\"image\":\"$image\",\"tag\":\"$tag\",\"local\":\"${local_digest:0:19}\",\"remote\":\"${remote_digest:0:19}\"}"
        return 0
    fi
    return 1
}

# Main
CONTAINER="${1:-}"

if [ -z "$CONTAINER" ]; then
    # Check all running containers and output combined array
    UPDATES=()
    for c in $(docker ps --format '{{.Names}}'); do
        result=$(check_container "$c" 2>/dev/null)
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
else
    # Check single container - output just the JSON object or empty string
    result=$(check_container "$CONTAINER")
    if [ -n "$result" ]; then
        echo "$result"
    fi
fi
