#!/bin/bash

# ============================================
# Automatic Database Backup Script
# Runs every 6 hours via cron
# Backs up PostgreSQL + Redis to remote server
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; exit 1; }
print_info() { echo -e "${YELLOW}ℹ${NC} $1"; }

# Load environment variables
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found at $ENV_FILE"
fi

source "$ENV_FILE"

# Check required variables
if [ -z "$BACKUP_SERVER_HOST" ]; then
    print_error "BACKUP_SERVER_HOST not set in .env"
fi

if [ -z "$BACKUP_SERVER_USER" ]; then
    print_error "BACKUP_SERVER_USER not set in .env"
fi

if [ -z "$BACKUP_SERVER_PATH" ]; then
    print_error "BACKUP_SERVER_PATH not set in .env"
fi

# Configuration
BACKUP_DIR="/srv/backups/auto"
SSH_KEY="${BACKUP_SSH_KEY:-/root/.ssh/backup_key}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="db_backup_${DATE}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

print_info "Starting automatic database backup: $BACKUP_NAME"

# ============================================
# 1. PostgreSQL Backup
# ============================================

print_info "Backing up PostgreSQL database..."

cd "$SCRIPT_DIR"

docker exec app_postgres pg_dump \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=custom \
    --blobs \
    --compress=9 \
    > "${BACKUP_DIR}/${BACKUP_NAME}_postgres.dump" 2>/dev/null

if [ $? -eq 0 ]; then
    print_success "PostgreSQL backup completed"
else
    print_error "PostgreSQL backup failed"
fi

# ============================================
# 2. Redis Backup
# ============================================

print_info "Backing up Redis data..."

# Trigger Redis BGSAVE
if [ -n "$REDIS_PASSWORD" ]; then
    docker exec app_redis redis-cli -a "$REDIS_PASSWORD" BGSAVE > /dev/null 2>&1
else
    docker exec app_redis redis-cli BGSAVE > /dev/null 2>&1
fi

# Wait for BGSAVE to complete
sleep 5

# Copy dump.rdb
docker cp app_redis:/data/dump.rdb "${BACKUP_DIR}/${BACKUP_NAME}_redis.rdb" 2>/dev/null

if [ $? -eq 0 ]; then
    print_success "Redis backup completed"
else
    print_error "Redis backup failed"
fi

# ============================================
# 3. Nginx Proxy Manager Data Backup
# ============================================

print_info "Backing up Nginx Proxy Manager data..."

docker run --rm \
    -v app_npm_data:/data \
    -v ${BACKUP_DIR}:/backup \
    alpine \
    tar czf /backup/${BACKUP_NAME}_npm_data.tar.gz -C /data . 2>/dev/null

if [ $? -eq 0 ]; then
    print_success "NPM data backup completed"
else
    print_info "NPM data backup skipped (volume may not exist)"
fi

# ============================================
# 4. Backup .env file
# ============================================

print_info "Backing up .env file..."
cp "$ENV_FILE" "${BACKUP_DIR}/${BACKUP_NAME}_env" 2>/dev/null

if [ $? -eq 0 ]; then
    print_success ".env backup completed"
fi

# ============================================
# 5. Create compressed archive
# ============================================

print_info "Creating compressed archive..."

cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" \
    "${BACKUP_NAME}_postgres.dump" \
    "${BACKUP_NAME}_redis.rdb" \
    "${BACKUP_NAME}_npm_data.tar.gz" \
    "${BACKUP_NAME}_env" 2>/dev/null

if [ $? -eq 0 ]; then
    # Remove individual files
    rm -f "${BACKUP_NAME}_postgres.dump" \
          "${BACKUP_NAME}_redis.rdb" \
          "${BACKUP_NAME}_npm_data.tar.gz" \
          "${BACKUP_NAME}_env"
    
    BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    print_success "Archive created: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
else
    print_error "Archive creation failed"
fi

# ============================================
# 6. Transfer to remote backup server
# ============================================

print_info "Transferring backup to remote server..."

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    print_error "SSH key not found: $SSH_KEY"
fi

# Transfer using rsync
rsync -avz --progress \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=30" \
    "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    "${BACKUP_SERVER_USER}@${BACKUP_SERVER_HOST}:${BACKUP_SERVER_PATH}/" 2>&1

if [ $? -eq 0 ]; then
    print_success "Backup transferred to remote server successfully"
    
    # Optional: Remove local backup after successful transfer
    if [ "${BACKUP_KEEP_LOCAL:-false}" != "true" ]; then
        rm -f "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
        print_info "Local backup removed (transferred to remote)"
    fi
else
    print_error "Backup transfer failed - keeping local copy"
fi

# ============================================
# 6. Cleanup old backups on remote server
# ============================================

print_info "Cleaning old backups on remote server (keeping last ${RETENTION_DAYS} days)..."

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    "${BACKUP_SERVER_USER}@${BACKUP_SERVER_HOST}" \
    "find ${BACKUP_SERVER_PATH} -name 'db_backup_*.tar.gz' -mtime +${RETENTION_DAYS} -delete" 2>/dev/null

if [ $? -eq 0 ]; then
    print_success "Old backups cleaned"
fi

# ============================================
# 8. Cleanup old local backups (keep only 3 days)
# ============================================

print_info "Cleaning old local backups (keeping last 3 days)..."
find "$BACKUP_DIR" -name "db_backup_*.tar.gz" -mtime +3 -delete 2>/dev/null
print_success "Local cleanup completed"

# ============================================
# 9. Log completion
# ============================================

LOG_FILE="/var/log/backup-auto.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completed: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})" >> "$LOG_FILE"

print_success "Automatic backup completed successfully!"
print_info "Backup: ${BACKUP_NAME}.tar.gz"
print_info "Remote: ${BACKUP_SERVER_USER}@${BACKUP_SERVER_HOST}:${BACKUP_SERVER_PATH}/"

exit 0
