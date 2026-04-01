#!/bin/bash
# Axiom Esports Database Setup Script
# Applies migrations and seeds the database

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESET=false
DRY_RUN=false
ONLY_MIGRATIONS=false
ONLY_SEED=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset) RESET=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --only-migrations) ONLY_MIGRATIONS=true; shift ;;
        --only-seed) ONLY_SEED=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo -e "${CYAN}==================================${NC}"
echo -e "${CYAN}Axiom Esports Database Setup${NC}"
echo -e "${CYAN}==================================${NC}"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${GRAY}Loading environment from .env${NC}"
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Determine database connection
DATABASE_URL="${DATABASE_URL:-}"
if [ -z "$DATABASE_URL" ]; then
    HOST="${POSTGRES_HOST:-localhost}"
    PORT="${POSTGRES_PORT:-5432}"
    DB="${POSTGRES_DB:-axiom_esports}"
    USER="${POSTGRES_USER:-axiom}"
    PASS="${POSTGRES_PASSWORD:-changeme}"
    DATABASE_URL="postgresql://${USER}:${PASS}@${HOST}:${PORT}/${DB}"
fi

# Mask password for display
DISPLAY_URL=$(echo "$DATABASE_URL" | sed 's/:\/\/[^@]*@/:\/\/***@/')
echo -e "${GRAY}Database: $DISPLAY_URL${NC}"

# Wait for database to be ready
wait_for_db() {
    local timeout=60
    echo -e "${YELLOW}Waiting for database...${NC}" -n
    for i in $(seq 1 $timeout); do
        if pg_isready -d "$DATABASE_URL" > /dev/null 2>&1; then
            echo -e " ${GREEN}READY${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo -e " ${RED}TIMEOUT${NC}"
    return 1
}

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}Warning: psql not found. Migrations must be applied manually.${NC}"
fi

# Run migrations
if [ "$ONLY_SEED" = false ]; then
    echo -e "\n${YELLOW}Applying migrations...${NC}"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${CYAN}[DRY RUN] Would apply migrations:${NC}"
        for f in "$SCRIPT_DIR"/migrations/*.sql; do
            echo -e "  ${GRAY}- $(basename "$f")${NC}"
        done
    elif command -v psql &> /dev/null; then
        if ! wait_for_db; then
            echo -e "${RED}Database not available${NC}"
            exit 1
        fi
        
        for f in "$SCRIPT_DIR"/migrations/*.sql; do
            echo -n -e "  ${GRAY}Applying $(basename "$f")...${NC}"
            if psql "$DATABASE_URL" -f "$f" > /dev/null 2>&1; then
                echo -e " ${GREEN}OK${NC}"
            else
                echo -e " ${RED}FAILED${NC}"
                exit 1
            fi
        done
        echo -e "${GREEN}Migrations complete${NC}"
    else
        echo -e "${YELLOW}Skipping migrations (psql not available)${NC}"
    fi
fi

# Run seeder
if [ "$ONLY_MIGRATIONS" = false ]; then
    echo -e "\n${YELLOW}Seeding database...${NC}"
    
    SEED_SCRIPT="$SCRIPT_DIR/seed_data/seed_database.py"
    
    if [ ! -f "$SEED_SCRIPT" ]; then
        echo -e "${RED}Seed script not found: $SEED_SCRIPT${NC}"
        exit 1
    fi
    
    ARGS=()
    [ "$RESET" = true ] && ARGS+=("--reset")
    [ "$DRY_RUN" = true ] && ARGS+=("--dry-run")
    
    if python3 "$SEED_SCRIPT" "${ARGS[@]}"; then
        echo -e "${GREEN}Seeding complete${NC}"
    else
        echo -e "${RED}Seeding failed${NC}"
        exit 1
    fi
fi

# Verify
echo -e "\n${YELLOW}Verifying database...${NC}"
if command -v psql &> /dev/null; then
    psql "$DATABASE_URL" -c "
SELECT 'player_performance' as table_name, count(*) as count FROM player_performance
UNION ALL
SELECT 'web_data_store', count(*) FROM web_data_store WHERE data_type = 'match_summary'
UNION ALL
SELECT 'sator_events', count(*) FROM sator_events
UNION ALL
SELECT 'arepo_markers', count(*) FROM arepo_markers;" 2>/dev/null || true
fi

echo -e "\n${GREEN}Setup complete!${NC}"
