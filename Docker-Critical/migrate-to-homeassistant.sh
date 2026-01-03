#!/bin/bash
# Migration script to move Docker-Critical services from TrueNAS to Home Assistant
# Run this on the Home Assistant host

set -e  # Exit on error

# Configuration
SOURCE_HOST="truenas01"
SOURCE_USER="runner"
SOURCE_BASE="/mnt/Apps"
TARGET_BASE="/opt/Docker-Critical"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Docker-Critical Data Migration ===${NC}"
echo "Source: ${SOURCE_USER}@${SOURCE_HOST}:${SOURCE_BASE}"
echo "Target: ${TARGET_BASE}"
echo ""

# Create base directory
echo -e "${YELLOW}Creating base directory...${NC}"
sudo mkdir -p "${TARGET_BASE}"

# Function to migrate a service
migrate_service() {
    local service_name=$1
    local source_path="${SOURCE_USER}@${SOURCE_HOST}:${SOURCE_BASE}/${service_name}"
    local target_path="${TARGET_BASE}/${service_name}"
    
    echo -e "${YELLOW}Migrating ${service_name}...${NC}"
    
    # Create target directory
    sudo mkdir -p "${target_path}"
    
    # Rsync data from source to target
    sudo rsync -avz --progress \
        -e "ssh -o StrictHostKeyChecking=no" \
        "${source_path}/" \
        "${target_path}/"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${service_name} migrated successfully${NC}"
    else
        echo -e "${RED}✗ ${service_name} migration failed${NC}"
        return 1
    fi
}

# Migrate all services
echo -e "${GREEN}Starting service migrations...${NC}\n"

# Auth services
migrate_service "Authelia"

# Networking services
migrate_service "traefik"
migrate_service "SMTPRelay"
migrate_service "Omada"

# Home services
migrate_service "KaraKeep"
migrate_service "homebox"
migrate_service "kiwix"
migrate_service "NetBox"
migrate_service "norish"
migrate_service "Norish"  # Case difference

# Management services
migrate_service "git"

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
