#!/bin/bash
# Migration script to move Docker-Critical services from TrueNAS to Home Assistant
# Run this on the Home Assistant host

set -e  # Exit on error

# Configuration
SOURCE_HOST="truenas01"
SOURCE_USER="runner"
SOURCE_BASE="/mnt/Apps"

declare -A TARGET_PATHS=(
    [Authelia]="/srv/authelia"
    [traefik]="/srv/traefik"
    [SMTPRelay]="/srv/smtp-relay"
    [Omada]="/srv/omada"
    [KaraKeep]="/mnt/nvme-appdata/karakeep"
    [homebox]="/mnt/nvme-appdata/homebox"
    [kiwix]="/mnt/hdd/kiwix/zim"
    [NetBox]="/mnt/nvme-appdata/netbox"
    [norish]="/srv/norish"
    [Norish]="/srv/norish"
    [git]="/srv/git"
    [homeassistant]="/srv/homeassistant/config"
    [avahi]="/srv/avahi"
    [esphome]="/srv/esphome"
    [rtl-sdr]="/srv/rtl-sdr"
    [music-assistant]="/srv/music-assistant"
    [influxdb]="/srv/influxdb"
)

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Docker-Critical Data Migration ===${NC}"
echo "Source: ${SOURCE_USER}@${SOURCE_HOST}:${SOURCE_BASE}"
echo "Targets: /srv (critical), /mnt/nvme-appdata (appdata), /mnt/hdd (logs/archives)"
echo ""

# Function to migrate a service
echo -e "${GREEN}Starting service migrations...${NC}\n"

for service_name in "${!TARGET_PATHS[@]}"; do
    source_path="${SOURCE_USER}@${SOURCE_HOST}:${SOURCE_BASE}/${service_name}"
    target_path="${TARGET_PATHS[$service_name]}"

    echo -e "${YELLOW}Migrating ${service_name} -> ${target_path}...${NC}"
    sudo mkdir -p "${target_path}"

    sudo rsync -avz --progress \
        -e "ssh -o StrictHostKeyChecking=no" \
        "${source_path}/" \
        "${target_path}/"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${service_name} migrated successfully${NC}"
    else
        echo -e "${RED}✗ ${service_name} migration failed${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}=== Migration Summary ===${NC}"
echo "All services have been migrated to ${TARGET_BASE}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify data integrity in ${TARGET_BASE}"
echo "2. Update file ownership if needed: sudo chown -R 568:568 ${TARGET_BASE}/*"
echo "3. Deploy services using Forgejo workflows"
echo "4. Test each service after deployment"
echo "5. Once verified, you can remove old data from ${SOURCE_HOST}:${SOURCE_BASE}"
